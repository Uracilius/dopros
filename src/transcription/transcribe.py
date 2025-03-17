import torch
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
import config
import psutil

logging.getLogger("nemo_logger").setLevel(logging.ERROR)
nemo.utils.logging.setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)


class Transcriber:
    def __init__(
        self,
        model_path=config.asr_model_path,
    ):

        self.model = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(
            model_path
        )

    def transcribe_audio(self, file_path):

        output = self.model.transcribe([file_path])

        if isinstance(output, tuple) and len(output) == 2:
            processed_text = output[1]
            return processed_text[0] if processed_text else None
        if isinstance(output, list) and len(output) > 0 and isinstance(output[0], str):
            return output[0]
        return None

    def record_and_transcribe(self, chunk_length_s=config.live_recording_chunk_length):

        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024,
        )

        frames = []
        try:
            # Record audio in chunks
            for _ in range(0, int(16000 / 1024 * chunk_length_s)):
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)

            # Save chunk to a .wav
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                wav_filename = tmp_wav.name
                with wave.open(wav_filename, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(16000)
                    wf.writeframes(b"".join(frames))

            # Transcribe chunk
            transcription = self.transcribe_audio(wav_filename)

            # Save result
            if transcription:
                with open("results/transcription.txt", "a", encoding="utf-8") as f:
                    f.write(transcription + "\n")

            return transcription

        except Exception as e:
            print(f"Error during transcription: {e}")
            return None
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

    def chunk_audio(self, input_path, chunk_length_ms=10000):
        """
        Splits an audio file into chunks of chunk_length_ms (milliseconds) and saves them to /tmp.
        """
        audio = AudioSegment.from_wav(input_path)
        chunk_paths = []

        for i, start in enumerate(range(0, len(audio), chunk_length_ms)):
            chunk = audio[start : start + chunk_length_ms]
            chunk_path = f"/tmp/chunk_{i}.wav"
            chunk.export(chunk_path, format="wav")
            chunk_paths.append(chunk_path)

        return chunk_paths


def test_transcription_from_file(
    transcriber,
    input_file,
    output_file="results/transcription.txt",
    chunk_length_ms=10000,
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
    start_cpu_load = psutil.cpu_percent(interval=None)
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

    # cleanup
    for chunk in chunk_paths:
        os.remove(chunk)

    total_time = round(time.time() - start_time, 2)

    print(f"Transcription took {total_time} seconds.")
    print(f"Transcription saved to {output_file}")


if __name__ == "__main__":
    transcriber = Transcriber(
        model_path="src/transcription/transcription_model/stt_kk_ru_fastconformer_hybrid_large.nemo"
    )
    test_transcription_from_file(
        transcriber,
        input_file="src/transcription/input.wav",
        output_file="src/transcription/results/transcription.txt",
    )
