import os
from datetime import datetime
from typing import Dict, List

from src.case.enums import TranscriptionStatus
from src.case.model import TranscriptionModel
from src.case.entity import TranscriptionEntity
from src.case.repository import TranscriptionRepository
from src.case import config

os.makedirs(config.MP3_SAVE_DIR, exist_ok=True)


class TranscriptionService:
    """All business-logic lives here. Orchestrator stays dumb."""

    def __init__(self, transcription_repository: TranscriptionRepository):
        self.repo = transcription_repository

    # ---------- Creation -------------------------------------------------- #
    def create_new_transcription(self, raw: Dict) -> TranscriptionEntity:
        """
        • Accept **raw** data exactly as it comes from the API
        • Parse / normalise it here
        • Persist via the repository
        """
        parsed = self._parse_dates(raw)
        model = TranscriptionModel(
            **parsed, status=TranscriptionStatus.TRANSCRIPTION.value
        )
        return self.repo.create_transcription(model)

    # ---------- Updates --------------------------------------------------- #
    def partial_update(self, transcription_id: int, fields: Dict):
        return self.repo.update_transcription(transcription_id, fields)

    # ---------- Reads ----------------------------------------------------- #
    def get_transcriptions_list(self):
        return self.repo.get_all_transcriptions()

    def get_transcriptions_by_case_id(self, case_id: str):
        return self.repo.get_transcriptions_by_case_id(case_id)

    # ---------- Helpers --------------------------------------------------- #
    @staticmethod
    def _parse_dates(payload: Dict) -> Dict:
        """Convert ISO strings to `datetime` objects (in-place safe)."""
        out = payload.copy()
        for key in ("create_date", "update_date"):
            if key in out and isinstance(out[key], str):
                out[key] = datetime.fromisoformat(out[key])
        return out
