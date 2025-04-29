###LOAD ENV FROM .ENV FILE
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

TRANSCRIPTION_RESULT_PATH = Path(os.getenv("DOPROS_TRANSCRIPTION_RESULT_PATH"))

TRANSCRIPTION_RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)