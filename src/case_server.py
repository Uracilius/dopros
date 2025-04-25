from fastapi import FastAPI
from enum import Enum
from datetime import datetime
import random
import string


class TranscriptionStatus(str, Enum):
    RETRIEVE = "RETRIEVE"


app = FastAPI(title="Transcription Server")


@app.get("/getTranscription")
def get_transcription():
    chance = random.random()
    if chance < 0.05:  # 5% threshold
        random_string = "".join(
            random.choices(string.ascii_uppertranscription + string.digits, k=5)
        )
        return {
            "case_number": f"CASE-{random_string}",
            "title": "Sample Transcription",
            "description": "Test transcription",
            "mp3_url": "https://example.com/sample.mp3",
            "status": TranscriptionStatus.RETRIEVE,
            "is_deleted": False,
            "create_date": datetime.utcnow(),
            "update_date": datetime.utcnow(),
        }
    else:
        return {}
