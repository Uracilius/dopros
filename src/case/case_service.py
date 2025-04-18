import os
import time
import shutil
import requests
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from repository import CaseRepository
from models import CaseModel
from entity import CaseEntity
from enums import CaseStatus
import config

os.makedirs(config.MP3_SAVE_DIR, exist_ok=True)


class CaseService:
    def __init__(self, case_repository: CaseRepository):
        self.case_repository = case_repository

    def create_new_case(self, case_model: CaseModel) -> CaseEntity:
        """Business logic before saving the case"""
        case_model.status = CaseStatus.TRANSCRIPTION.value  # Apply default logic
        return self.case_repository.create_case(case_model)

    def partial_update(self, case_id: int, updated_fields: dict):
        return self.case_repository.update_case(case_id, updated_fields)

    def get_cases_list(self):
        return self.case_repository.get_all_cases()
