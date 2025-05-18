# src/transcription/transcribe.py
"""
Real-time transcription with DOA-based dynamic diarisation.

Key points
----------
* One PyAudio stream; we read 1024-sample frames (≈ 64 ms at 16 kHz, 1 ch, 16 bit).
* Direction of Arrival (DOA) polled every frame.
* As soon as DOA *стабильно* смещается на другой «bucket» 3 раза подряд
  (≈ 0.2 с) – режем аудио, отправляем в ASR и помечаем «Speaker X».
* Чанки также сбрасываются, если накоплено ≥ MAX_SEC_PER_CHUNK секунд,
  чтобы длинный монолог не уходил в 30-секундный кусок.
* Минимальный размер чанка – 0.4 с: если сплит случился раньше, ждём
  добора данных.
"""

import os, time, wave, tempfile, threading, logging, warnings, statistics
from queue import Queue
from collections import deque
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


# --------------------------------------------------------------------------- #
#                              Transcriber                                    #
# --------------------------------------------------------------------------- #
class Transcriber:
    """Record microphone, split on speaker turn, run NeMo RNNT model."""

    # tune here
    _FRAME_LEN = 1024  # 64 ms @ 16 kHz
    _SAMPLE_RATE = 16_000
    _MIN_CHUNK_MS = 400  # don’t flush shorter chunks
    _MAX_SEC_PER_CHUNK = 8  # force-flush long monologues
    _STABLE_READS = 4  # DOA readings before we accept new bucket

    def __init__(self, model_path: str = config.ASR_MODEL_PATH):
        self.vdf = VoiceDirectionFinder(bucket_size=20)
        self.stop_recording = threading.Event()
        self.model = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.restore_from(
            model_path
        )
        self.executor = ThreadPoolExecutor(max_workers=2)

    # --------------------------------------------------------------------- #
    #                             ASR helper                                #
    # --------------------------------------------------------------------- #
    def transcribe_audio(self, wav_path: str) -> str | None:
        output: List[Hypothesis] = self.model.transcribe([wav_path])
        if not output or not isinstance(output[0], Hypothesis):
            return None
        text = output[0].text.strip()
        return text or None

    # --------------------------------------------------------------------- #
    #                          Main public API                              #
    # --------------------------------------------------------------------- #
    def record_and_transcribe(self) -> Tuple[str, str]:
        """Return (full_transcription_text, mp3_path)."""

        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            rate=self._SAMPLE_RATE,
            channels=1,
            input=True,
            input_device_index=1,
            frames_per_buffer=self._FRAME_LEN,
        )

        # state
        frames_current: List[bytes] = []
        speaker_bucket = self.vdf.get_bucket(self.vdf.get_direction())
        stable_reads = 0
        start_time = time.time()
        chunk_start_time = start_time
        all_speakers_text: List[str] = []

        # prepare log file
        with open(config.TRANSCRIPTION_RESULT_PATH, "w", encoding="utf-8") as f:
            f.write("")

        def flush_chunk(frames: List[bytes], bucket: int):
            """Send chunk to ASR, write to file, return transcript or None."""
            if not frames:
                return None

            duration_ms = len(frames) * self._FRAME_LEN / self._SAMPLE_RATE * 1000
            if duration_ms < self._MIN_CHUNK_MS:
                # too small – merge with next chunk
                return None

            # save wav
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
                return None

            speaker = self.vdf.classify_speaker(bucket)
            timestamp = time.strftime(
                "[%H:%M:%S]", time.gmtime(time.time() - start_time)
            )
            with open(config.TRANSCRIPTION_RESULT_PATH, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} {speaker}: {text}\n")

            all_speakers_text.append(text)
            return text

        # ----------------------------------------------------------------- #
        #                          Streaming loop                           #
        # ----------------------------------------------------------------- #
        self.stop_recording.clear()
        try:
            while not self.stop_recording.is_set():
                data = stream.read(self._FRAME_LEN, exception_on_overflow=False)
                frames_current.append(data)

                # --- DOA logic
                doa_bucket = self.vdf.get_bucket(self.vdf.get_direction())
                if doa_bucket == speaker_bucket:
                    stable_reads = min(stable_reads + 1, self._STABLE_READS)
                else:
                    stable_reads = 1  # first reading of potential new speaker

                # accept new speaker when stable
                if doa_bucket != speaker_bucket and stable_reads >= self._STABLE_READS:

                    flush_chunk(frames_current, speaker_bucket)
                    frames_current = []
                    speaker_bucket = doa_bucket
                    chunk_start_time = time.time()
                    continue

                if time.time() - chunk_start_time >= self._MAX_SEC_PER_CHUNK:
                    flush_chunk(frames_current, speaker_bucket)
                    frames_current = []
                    chunk_start_time = time.time()

        finally:
            # final flush

            flush_chunk(frames_current, speaker_bucket)
            stream.stop_stream()
            stream.close()
            pa.terminate()
            self.executor.shutdown(wait=False)
            self.stop_recording.set()

        # save full recording to mp3 (optional — iframe buffer reused)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        mp3_path = os.path.abspath(f"audios/transcription_{timestamp}.mp3")
        os.makedirs("audios", exist_ok=True)
        audio_segment = AudioSegment(
            data=b"".join(frames_current),
            sample_width=2,
            frame_rate=self._SAMPLE_RATE,
            channels=1,
        )
        audio_segment.export(mp3_path, format="mp3")

        return "\n".join(all_speakers_text), mp3_path
