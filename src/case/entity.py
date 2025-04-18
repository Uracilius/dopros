from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from enums import CaseStatus
from sqlalchemy.orm import declarative_base

Base = declarative_base()  # Keep only one instance


class CaseEntity(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(
        String, unique=True, nullable=False
    )  # Ensuring unique case identification
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    mp3_url = Column(String, nullable=True)  # Keeping audio URL for transcription cases
    status = Column(String, nullable=False, default=CaseStatus.RECEIVED.value)
    is_deleted = Column(Boolean, default=False, nullable=False)  # Soft delete flag
    create_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    update_date = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return (
            f"<CaseEntity(id={self.id}, case_number='{self.case_number}', title='{self.title}', "
            f"status='{self.status}', is_deleted={self.is_deleted})>"
        )
