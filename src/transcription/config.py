LIVE_RECORDING_CHUNK_LENGTH = 2

###LOAD ENV FROM .ENV FILE
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

TRANSCRIPTION_RESULT_PATH = Path(os.getenv("DOPROS_TRANSCRIPTION_RESULT_PATH"))
ASR_MODEL_PATH = Path(os.getenv("DOPROS_ASR_MODEL_PATH", ""))

TRANSCRIPTION_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)

if not ASR_MODEL_PATH.exists():
    raise FileNotFoundError(f"ASR Model file not found from .env: {ASR_MODEL_PATH}")