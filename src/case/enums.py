from enum import Enum


class Language(Enum):
    RUSSIAN = "rus"
    KAZAKH = "kaz"


class CaseStatus(Enum):
    RETRIEVE = "Retrieving"
    RECEIVED = "Received"
    TRANSCRIPTION = "Transcription"
    ENHANCEMENT = "Enhancement"
    ANALYSIS = "Analysis"
    COMPLETED = "Completed"
    ERROR = "Error"

    @classmethod
    def list(cls):
        return [e.value for e in cls]
