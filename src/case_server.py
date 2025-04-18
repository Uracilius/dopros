from fastapi import FastAPI
from enum import Enum
from datetime import datetime
import random
import string


class CaseStatus(str, Enum):
    RETRIEVE = "RETRIEVE"


app = FastAPI(title="Case Server")


@app.get("/getCase")
def get_case():
    chance = random.random()
    if chance < 0.05:  # 5% threshold
        random_string = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        return {
            "case_number": f"CASE-{random_string}",
            "title": "Sample Case",
            "description": "Test case for transcription",
            "mp3_url": "https://example.com/sample.mp3",
            "status": CaseStatus.RETRIEVE,
            "is_deleted": False,
            "create_date": datetime.utcnow(),
            "update_date": datetime.utcnow(),
        }
    else:
        return {}
