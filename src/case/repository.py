from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session, declarative_base
from enums import CaseStatus
from models import CaseModel
from entity import CaseEntity

Base = declarative_base()


class CaseRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_case_by_id(self, case_id: int) -> Optional[CaseEntity]:
        return (
            self.db_session.query(CaseEntity)
            .filter(CaseEntity.id == case_id, CaseEntity.is_deleted == False)
            .first()
        )

    def get_case_by_case_number(self, case_number: str) -> Optional[CaseEntity]:
        return (
            self.db_session.query(CaseEntity)
            .filter(
                CaseEntity.case_number == case_number, CaseEntity.is_deleted == False
            )
            .first()
        )

    def get_all_cases(self) -> List[CaseEntity]:
        return (
            self.db_session.query(CaseEntity)
            .filter(CaseEntity.is_deleted == False)
            .all()
        )

    def create_case(self, case_model: CaseModel) -> CaseEntity:
        """Takes a CaseModel (business logic), converts it to CaseEntity, and saves it."""
        new_case = CaseEntity(
            case_number=case_model.case_number,
            title=case_model.title,
            description=case_model.description,
            mp3_url=case_model.mp3_url,
            status=case_model.status,
            is_deleted=False,
            create_date=case_model.create_date,
            update_date=case_model.update_date,
        )
        self.db_session.add(new_case)
        self.db_session.commit()
        self.db_session.refresh(new_case)
        return new_case

    def update_case(self, case_id: int, updated_fields: dict):
        case_entity = (
            self.db_session.query(CaseEntity)
            .filter(CaseEntity.id == case_id, CaseEntity.is_deleted == False)
            .one_or_none()
        )
        if not case_entity:
            return None

        for field, value in updated_fields.items():
            if value is not None and hasattr(case_entity, field):
                setattr(case_entity, field, value)

        case_entity.update_date = datetime.utcnow()

        self.db_session.commit()
        return case_entity

    def soft_delete_case(self, case_id: int) -> bool:
        """Soft deletes the case by setting is_deleted = True."""
        existing_case = self.get_case_by_id(case_id)
        if not existing_case:
            return False

        existing_case.is_deleted = True
        existing_case.update_date = datetime.utcnow()

        self.db_session.commit()
        return True
