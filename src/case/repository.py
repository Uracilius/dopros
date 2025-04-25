from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session, declarative_base
from src.case.enums import TranscriptionStatus
from src.case.model import TranscriptionModel
from src.case.entity import TranscriptionEntity, CaseEntity, InfoUnitEntity


Base = declarative_base()


class TranscriptionRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_transcription_by_id(
        self, transcription_id: int
    ) -> Optional[TranscriptionEntity]:
        return (
            self.db_session.query(TranscriptionEntity)
            .filter(
                TranscriptionEntity.id == transcription_id,
                TranscriptionEntity.is_deleted == False,
            )
            .first()
        )

    def get_all_transcriptions(self) -> List[TranscriptionEntity]:
        return (
            self.db_session.query(TranscriptionEntity)
            .filter(TranscriptionEntity.is_deleted == False)
            .all()
        )

    def create_transcription(
        self, transcription_model: TranscriptionModel
    ) -> TranscriptionEntity:
        """Takes a TranscriptionModel (business logic), converts it to TranscriptionEntity, and saves it."""
        new_transcription = TranscriptionEntity(
            title=transcription_model.title,
            case_id=transcription_model.case_id,
            description=transcription_model.description,
            mp3_url=transcription_model.mp3_url,
            full_text=transcription_model.full_text,
            improved_text=transcription_model.improved_text,
            status=transcription_model.status,
            is_deleted=False,
            create_date=transcription_model.create_date,
            update_date=transcription_model.update_date,
        )
        self.db_session.add(new_transcription)
        self.db_session.commit()
        self.db_session.refresh(new_transcription)
        return new_transcription

    def update_transcription(self, transcription_id: int, updated_fields: dict):
        transcription_entity = (
            self.db_session.query(TranscriptionEntity)
            .filter(
                TranscriptionEntity.id == transcription_id,
                TranscriptionEntity.is_deleted == False,
            )
            .one_or_none()
        )
        if not transcription_entity:
            return None

        for field, value in updated_fields.items():
            if value is not None and hasattr(transcription_entity, field):
                setattr(transcription_entity, field, value)

        transcription_entity.update_date = datetime.utcnow()

        self.db_session.commit()
        return transcription_entity

    def get_transcriptions_by_case_id(self, case_id: str) -> List[TranscriptionEntity]:
        return (
            self.db_session.query(TranscriptionEntity)
            .filter(
                TranscriptionEntity.case_id == case_id,
                TranscriptionEntity.is_deleted == False,
            )
            .all()
        )

    def soft_delete_transcription(self, transcription_id: int) -> bool:
        """Soft deletes the transcription by setting is_deleted = True."""
        existing_transcription = self.get_transcription_by_id(transcription_id)
        if not existing_transcription:
            return False

        existing_transcription.is_deleted = True
        existing_transcription.update_date = datetime.utcnow()

        self.db_session.commit()
        return True


class CaseRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_case_by_id(self, case_id: str) -> Optional[CaseEntity]:
        return (
            self.db_session.query(CaseEntity).filter(CaseEntity.id == case_id).first()
        )

    def create_case(self, case_id: str, status: str) -> CaseEntity:
        new_case = CaseEntity(
            id=case_id,
            status=status,
            create_date=datetime.utcnow(),
        )
        self.db_session.add(new_case)
        self.db_session.commit()
        self.db_session.refresh(new_case)
        return new_case

    def update_case(self, case_id: str, updated_fields: dict) -> Optional[CaseEntity]:
        case_entity = self.get_case_by_id(case_id)
        if not case_entity:
            return None

        for field, value in updated_fields.items():
            if value is not None and hasattr(case_entity, field):
                setattr(case_entity, field, value)

        case_entity.update_date = datetime.utcnow()

        self.db_session.commit()
        return case_entity

    def soft_delete_case(self, case_id: str) -> bool:
        """Soft deletes the case by setting is_deleted = True."""
        existing_case = self.get_case_by_id(case_id)
        if not existing_case:
            return False

        existing_case.status = 0

        self.db_session.commit()
        return True

    def get_case_list(self) -> List[CaseEntity]:
        return self.db_session.query(CaseEntity).all()


class InfoUnitRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_info_unit_by_id(self, info_unit_id: int) -> Optional[InfoUnitEntity]:
        return (
            self.db_session.query(InfoUnitEntity)
            .filter(InfoUnitEntity.id == info_unit_id)
            .first()
        )

    def get_info_units_by_case_id(self, case_id: str) -> List[InfoUnitEntity]:
        return (
            self.db_session.query(InfoUnitEntity)
            .filter(InfoUnitEntity.case_id == case_id)
            .all()
        )

    def get_info_units_by_transcription_id(
        self, transcription_id: int
    ) -> List[InfoUnitEntity]:
        return (
            self.db_session.query(InfoUnitEntity)
            .filter(InfoUnitEntity.transcription_id == transcription_id)
            .all()
        )

    def create_info_unit(
        self,
        case_id: str,
        transcription_id: int,
        text: str,
        language: str,
        status: str = "0",
    ) -> InfoUnitEntity:
        new_info_unit = InfoUnitEntity(
            case_id=case_id,
            transcription_id=transcription_id,
            text=text,
            language=language,
            status=status,
        )
        self.db_session.add(new_info_unit)
        self.db_session.commit()
        self.db_session.refresh(new_info_unit)
        return new_info_unit

    def update_info_unit(
        self, info_unit_id: int, updated_fields: dict
    ) -> Optional[InfoUnitEntity]:
        info_unit_entity = self.get_info_unit_by_id(info_unit_id)
        if not info_unit_entity:
            return None

        for field, value in updated_fields.items():
            if value is not None and hasattr(info_unit_entity, field):
                setattr(info_unit_entity, field, value)

        self.db_session.commit()
        return info_unit_entity

    def delete_info_unit(self, info_unit_id: int) -> bool:
        info_unit_entity = self.get_info_unit_by_id(info_unit_id)
        if not info_unit_entity:
            return False

        self.db_session.delete(info_unit_entity)
        self.db_session.commit()
        return True


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

if __name__ == "__main__":

    DATABASE_URL = "sqlite:///transcriptions.db"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()

    transcription_repo = TranscriptionRepository(db_session)
    case_repo = CaseRepository(db_session)

    # Test create_case
    print("Creating a new case...")
    new_case = case_repo.create_case(case_id="CASE-001", status=1)
    print(f"Created case: {new_case}")
