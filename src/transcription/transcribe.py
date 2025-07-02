# src/transcription/transcribe.py

import os
import time
import wave
import tempfile
import threading
import logging
import warnings

from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

import pyaudio
from pydub import AudioSegment
import nemo.collections.asr as nemo_asr
from nemo.collections.asr.parts.utils.rnnt_utils import Hypothesis
import nemo.utils

from src.transcription import config
from src.transcription.doa import VoiceDirectionFinder

# Silence NeMo logging
logging.getLogger("nemo_logger").setLevel(logging.ERROR)
nemo.utils.logging.setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning)


class Transcriber:
    """Record microphone, split on speaker turn, run NeMo RNNT model."""

    _FRAME_LEN = 1024           # ~64 ms
    _SAMPLE_RATE = 16_000
    _MIN_CHUNK_MS = 400         # drop any chunk shorter than this
    _MAX_SEC_PER_CHUNK = 8      # force-flush after this many seconds
    _STABLE_READS = 2           # frames required to accept a new bucket

    def __init__(self, model_path: str = config.ASR_MODEL_PATH):
        self.vdf = VoiceDirectionFinder(bucket_size=50)
        self.stop_recording = threading.Event()
        self.model = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(
            model_path
        )
        self.executor = ThreadPoolExecutor(max_workers=2)

    def transcribe_audio(self, wav_path: str) -> str | None:
        output: List[Hypothesis] = self.model.transcribe([wav_path])
        if not output or not isinstance(output[0], Hypothesis):
            return None
        text = output[0].text.strip()
        return text or None

    def record_and_transcribe(self) -> Tuple[str, str]:
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            rate=self._SAMPLE_RATE,
            channels=1,
            input=True,
            input_device_index=1,
            frames_per_buffer=self._FRAME_LEN,
        )
        print("[Transcriber] 🎤 Recording started")

        # initial state
        frames_current: List[bytes] = []
        start_time = time.time()
        chunk_start = start_time

        # speaker-change tracking
        current_bucket = self.vdf.get_bucket(self.vdf.get_direction())
        candidate_bucket = None
        candidate_count = 0

        all_speakers_text: List[str] = []
        # clear result file
        with open(config.TRANSCRIPTION_RESULT_PATH, "w", encoding="utf-8"):
            pass

        def flush_chunk(frames: List[bytes], bucket: int):
            if not frames:
                return
            duration_ms = len(frames) * self._FRAME_LEN / self._SAMPLE_RATE * 1000
            if duration_ms < self._MIN_CHUNK_MS:
                print(f"[Transcriber] Dropping too-short chunk ({duration_ms:.1f} ms)")
                return

            # write temp WAV
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                wav_path = tmp.name
                with wave.open(wav_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(self._SAMPLE_RATE)
                    wf.writeframes(b"".join(frames))

            text = self.transcribe_audio(wav_path)
            os.unlink(wav_path)
            if not text:
                return

            speaker = self.vdf.classify_speaker(bucket)
            timestamp = time.strftime(
                "[%H:%M:%S]", time.gmtime(time.time() - start_time)
            )
            with open(config.TRANSCRIPTION_RESULT_PATH, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} {speaker}: {text}\n")
            all_speakers_text.append(text)
            print(f"{timestamp} {speaker}: {text}")

        try:
            while not self.stop_recording.is_set():
                data = stream.read(self._FRAME_LEN, exception_on_overflow=False)
                frames_current.append(data)

                doa = self.vdf.get_direction()
                doa_bucket = self.vdf.get_bucket(doa)

                if doa_bucket != current_bucket:
                    # track a potential new bucket
                    if doa_bucket == candidate_bucket:
                        candidate_count += 1
                    else:
                        candidate_bucket = doa_bucket
                        candidate_count = 1
                    print(f"[Transcriber] candidate_bucket={candidate_bucket}, count={candidate_count}")

                    # commit to new speaker
                    if candidate_count >= self._STABLE_READS:
                        print(f"[Transcriber] → flush bucket {current_bucket}")
                        flush_chunk(frames_current, current_bucket)
                        frames_current = []
                        current_bucket = candidate_bucket
                        candidate_bucket = None
                        candidate_count = 0
                        chunk_start = time.time()
                else:
                    # reset if readings go back
                    candidate_bucket = None
                    candidate_count = 0

                # force-flush long chunks
                if time.time() - chunk_start >= self._MAX_SEC_PER_CHUNK:
                    print(f"[Transcriber] Timeout flush bucket {current_bucket}")
                    flush_chunk(frames_current, current_bucket)
                    frames_current = []
                    chunk_start = time.time()

        finally:
            print("[Transcriber] 🔚 Final flush before stopping")
            flush_chunk(frames_current, current_bucket)
            stream.stop_stream()
            stream.close()
            pa.terminate()
            self.executor.shutdown(wait=False)
            self.stop_recording.set()

        # save entire recording as MP3
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        os.makedirs("audios", exist_ok=True)
        mp3_path = os.path.abspath(f"audios/transcription_{timestamp}.mp3")
        audio_segment = AudioSegment(
            data=b"".join(frames_current),
            sample_width=2,
            frame_rate=self._SAMPLE_RATE,
            channels=1,
        )
        audio_segment.export(mp3_path, format="mp3")

        print(f"[Transcriber] 🎬 Finished, MP3 at {mp3_path}")
        return "\n".join(all_speakers_text), mp3_path

    def stop(self):
        self.stop_recording.set()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Real-time transcription with DOA diarisation")
    parser.add_argument("--duration", type=float, help="Seconds to record before auto-stopping")
    args = parser.parse_args()

    t = Transcriber()
    if args.duration:
        threading.Timer(args.duration, t.stop).start()

    try:
        t.record_and_transcribe()
    except KeyboardInterrupt:
        print("[Transcriber] Interrupted, stopping…")
        t.stop()
