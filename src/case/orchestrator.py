import threading
import time
from typing import Dict

import requests

from src.case import config
from src.case.db import get_db_session
from src.case.network_service import NetworkService
from src.case.transcription_service import TranscriptionService
from src.case.repository import (
    TranscriptionRepository,
    CaseRepository,
    InfoUnitRepository,
)


class Orchestrator:

    def __init__(self):
        db_session = next(get_db_session())
        transcription_repo = TranscriptionRepository(db_session)

        self.case_repo = CaseRepository(next(get_db_session()))

        self.info_unit_repo = InfoUnitRepository(next(get_db_session()))

        self.transcription_service = TranscriptionService(transcription_repo)
        self.network_service = NetworkService()

        # self.network_thread = threading.Thread(
        #     target=self.network_service.monitor_network,
        #     args=(self.transcription_service,),
        #     daemon=True,
        # )
        # self.network_thread.start()

    def fetch_transcriptions_by_case_id(self, case_id: str):
        transcriptions_list = self.transcription_service.get_transcriptions_by_case_id(
            case_id
        )
        if transcriptions_list:
            return transcriptions_list
        else:
            print(f"No transcriptions found for case ID {case_id}.")
            return []

    def create_transcription(self, data: Dict):
        entity = self.transcription_service.create_new_transcription(data)
        print(f"Transcription {entity.id} created successfully.")
        return entity

    def partial_update_transcription(self, transcription_id: int, fields: Dict):
        updated = self.transcription_service.partial_update(transcription_id, fields)
        msg = "updated successfully." if updated else "not found or update failed."
        print(f"Transcription {transcription_id} {msg}")
        return updated

    def get_case_list(self):
        return self.case_repo.get_case_list()

    def get_info_unit_list(self, case_id: str):
        return self.info_unit_repo.get_info_units_by_case_id(case_id=case_id)

    def create_info_unit(
        self, case_id: str, transcription_id: int, text: str, language: str
    ):
        entity = self.info_unit_repo.create_info_unit(
            case_id=case_id,
            transcription_id=transcription_id,
            text=text,
            language=language,
            status="0",
        )
        print(f"Info unit {entity.id} created successfully.")

    @staticmethod
    def _online(url: str) -> bool:
        try:
            return requests.get(url, timeout=3).status_code == 200
        except requests.RequestException:
            return False

    def _fetch_remote(self):
        try:
            resp = requests.get(f"{config.SERVER_API_URL}/getTranscription", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if data:
                # API returns either a list or a single object; normalise to list
                payloads = data if isinstance(data, list) else [data]
                for p in payloads:
                    self.create_transcription(p)
        except requests.RequestException as exc:
            print(f"Error fetching transcription list: {exc}")

    # --------------------------------------------------------------------- #
    # Main loop
    # --------------------------------------------------------------------- #
    # def run(self):
    #     last_fetch = 0.0
    #     while True:
    #         if self._online(config.NETWORK_CHECK_URL):
    #             if time.time() - last_fetch >= config.FETCH_INTERVAL:
    #                 self._fetch_remote()
    #                 last_fetch = time.time()
    #         time.sleep(config.CHECK_INTERVAL)


if __name__ == "__main__":
    from datetime import datetime
    from enums import TranscriptionStatus
    from entity import CaseEntity

    orchestrator = Orchestrator()

    # --- Create sample cases ---
    print("Creating sample cases...")
    session = next(get_db_session())
    case_repo = CaseRepository(session)

    case_data = [
        {"id": "CASE001", "status": "OPEN"},
        {"id": "CASE002", "status": "CLOSED"},
    ]

    for c in case_data:
        case = (
            orchestrator.case_repo.db_session.query(CaseEntity)
            .filter_by(id=c["id"])
            .first()
        )
        if not case:
            new_case = CaseEntity(
                id=c["id"], status=c["status"], create_date=datetime.utcnow()
            )
            orchestrator.case_repo.db_session.add(new_case)

    orchestrator.case_repo.db_session.commit()
    print("Cases created.\n")

    # --- Create sample transcriptions ---
    print("Creating sample transcriptions...")
    transcriptions = [
        {
            "title": "First Hearing",
            "case_id": "CASE001",
            "description": "Opening hearing session",
            "mp3_url": "http://example.com/audio1.mp3",
            "create_date": datetime.utcnow(),
            "update_date": datetime.utcnow(),
        },
        {
            "title": "Second Hearing",
            "case_id": "CASE002",
            "description": "Final argument session",
            "mp3_url": "http://example.com/audio2.mp3",
            "create_date": datetime.utcnow(),
            "update_date": datetime.utcnow(),
        },
    ]

    for t in transcriptions:
        orchestrator.create_transcription(t.copy())

    print("\nFetching all cases and transcriptions:\n")
    all_cases = orchestrator.get_case_list()
    for c in all_cases:
        print(c)

    for c in case_data:
        trans_list = orchestrator.fetch_transcriptions_by_case_id(c["id"])
        for t in trans_list:
            print(t)
