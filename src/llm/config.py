import os

MAX_TOKENS = 2048
MAX_CONTEXT = 4096
NUM_THREADS = os.cpu_count() // 2
TEMPERATURE = 0.4
TOP_K = 50
TOP_P = 0.95
REPEAT_PENALTY = 1.2


###LOAD ENV FROM .ENV FILE
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

HF_MODEL_NAME = os.getenv("DOPROS_HF_MODEL_NAME")
PATH_TO_LOCAL_LLM = Path(os.getenv("DOPROS_PATH_TO_LOCAL_LLM", ""))

if not PATH_TO_LOCAL_LLM.exists():
    raise FileNotFoundError(f"Model file not found: {PATH_TO_LOCAL_LLM}")
