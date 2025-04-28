import nemo.collections.asr as nemo_asr
import pyaudio
import wave
import tempfile
import logging
import nemo.utils
import warnings
from pydub import AudioSegment
import os
import time
from src.transcription import config
from nemo.collections.asr.parts.utils.rnnt_utils import Hypothesis
import threading
from queue import Queue

logging.getLogger("nemo_logger").setLevel(logging.ERROR)
nemo.utils.logging.setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)


class Transcriber:
    def __init__(
        self,
        model_path=config.ASR_MODEL_PATH,
    ):
        self.stop_recording = threading.Event()
        self.model = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(
            model_path
        )

    def transcribe_audio(self, file_path: str) -> str | None:
        output: list[Hypothesis] = self.model.transcribe([file_path])

        if not output or not isinstance(output[0], Hypothesis):
            print(f">> Unexpected transcription output for {file_path}: {output}")
            return None

        best_hypothesis: Hypothesis = output[0]

        if best_hypothesis.text and best_hypothesis.text.strip():
            print(f">> Accepted transcription: {best_hypothesis.text.strip()}")
            return best_hypothesis.text.strip()
        else:
            print(
                f">> Model returns a trnascription but has empty text: {best_hypothesis}"
            )
            return None

    def record_and_transcribe(
        self, chunk_length_s=config.LIVE_RECORDING_CHUNK_LENGTH, overlap_s=1
    ):
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            rate=16000,
            channels=1,
            input=True,
            input_device_index=2,
            frames_per_buffer=1024,
        )

        audio_queue = Queue()
        self.stop_recording.clear()
        final_mp3_path = None
        full_transcription = []

        with open(config.TRANSCRIPTION_RESULT_PATH, "w", encoding="utf-8") as f:
            f.write("")

        def recorder():
            frames = []
            max_frames = int(16000 / 1024 * chunk_length_s)
            overlap_frames = int(16000 / 1024 * overlap_s)

            while not self.stop_recording.is_set():
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)

                if len(frames) >= max_frames:
                    audio_queue.put(frames.copy())
                    frames = frames[-overlap_frames:]

            stream.stop_stream()
            stream.close()
            p.terminate()

        record_thread = threading.Thread(target=recorder)
        record_thread.start()

        try:
            while not self.stop_recording.is_set() or not audio_queue.empty():
                try:
                    frames = audio_queue.get(timeout=0.5)
                except:
                    continue

                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".wav"
                ) as tmp_wav:
                    wav_filename = tmp_wav.name
                    with wave.open(wav_filename, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                        wf.setframerate(16000)
                        wf.writeframes(b"".join(frames))

                transcription = self.transcribe_audio(wav_filename)

                if transcription:
                    full_transcription.append(transcription)

                    # NEW: write to result file incrementally
                    with open(
                        config.TRANSCRIPTION_RESULT_PATH, "a", encoding="utf-8"
                    ) as f:
                        f.write(transcription + "\n")

                os.unlink(wav_filename)

        finally:
            self.stop_recording.set()
            record_thread.join()

        # Save full audio as MP3
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        final_mp3_path = os.path.abspath(f"audios/transcription_{timestamp}.mp3")
        os.makedirs("audios", exist_ok=True)
        audio_segment = AudioSegment(
            data=b"".join(frames), sample_width=2, frame_rate=16000, channels=1
        )
        audio_segment.export(final_mp3_path, format="mp3")

        return "\n".join(full_transcription), final_mp3_path

    def chunk_audio(self, input_path, chunk_length_ms=10000):
        """
        Splits an audio file into chunks of chunk_length_ms (milliseconds) and saves them to /tmp.
        """
        audio = AudioSegment.from_wav(input_path)
        chunk_paths = []

        for i, start in enumerate(range(0, len(audio), chunk_length_ms)):
            chunk = audio[start : start + chunk_length_ms]
            chunk_path = os.path.join(tempfile.gettempdir(), f"chunk_{i}.wav")

            chunk.export(chunk_path, format="wav")
            chunk_paths.append(chunk_path)

        return chunk_paths


def test_transcription_from_file(
    transcriber: Transcriber,
    input_file,
    output_file="results/transcription.txt",
    chunk_length_ms=20000,
):
    """
    for model testing
    """
    start_time = time.time()

    # try:
    #     with open("/sys/class/thermal/thermal_zone0/temp", "r") as temp_file:
    #         raw_temp = temp_file.read().strip()
    #     system_temp_c = float(raw_temp) / 1000.0
    # except Exception:
    #     system_temp_c = -1
    chunk_paths = transcriber.chunk_audio(input_file, chunk_length_ms)
    total_chunks = len(chunk_paths)
    print(f"Number of chunks to process: {total_chunks}")

    total_audio_ms = len(AudioSegment.from_wav(input_file))
    total_audio_sec = round(total_audio_ms / 1000, 2)
    print(f"Total audio length: {total_audio_sec} seconds")

    with open(output_file, "w", encoding="utf-8") as f:
        for i, chunk_path in enumerate(chunk_paths, 1):
            transcription = transcriber.transcribe_audio(chunk_path)
            if transcription:
                f.write(transcription + "\n")
                print(f"Chunk {i}/{total_chunks} transcription: {transcription}")
            else:
                print(f"Chunk {i}/{total_chunks} had no transcription.")

    for chunk in chunk_paths:
        os.remove(chunk)

    total_time = round(time.time() - start_time, 2)

    print(f"Transcription took {total_time} seconds.")
    print(f"Transcription saved to {output_file}")


if __name__ == "__main__":
    transcriber = Transcriber(model_path=config.ASR_MODEL_PATH)

    test_transcription_from_file(
        transcriber,
        input_file="src/transcription/dopros1.wav",
        output_file="src/transcription/results/transcription.txt",
    )
