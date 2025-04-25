from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from src.case.enums import TranscriptionStatus
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TranscriptionEntity(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    mp3_url = Column(String, nullable=True)
    full_text = Column(Text, nullable=True)
    improved_text = Column(Text, nullable=True)
    status = Column(String, nullable=False, default=TranscriptionStatus.RECEIVED.value)
    is_deleted = Column(Boolean, default=False, nullable=False)
    create_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    update_date = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return (
            f"<TranscriptionEntity(id={self.id}, case_id='{self.case_id}', title='{self.title}', "
            f"status='{self.status}', is_deleted={self.is_deleted})>"
        )


class CaseEntity(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, nullable=False)
    status = Column(Integer, nullable=False)
    create_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CaseEntity(id='{self.id}', status='{self.status}')>"

class InfoUnitEntity(Base):
    __tablename__ = "info_units"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, nullable=False)
    transcription_id = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    language = Column(String(10), nullable=False)
    status = Column(String, default="unverified", nullable=False)

    def __repr__(self):
        return (
            f"<InfoUnitEntity(id={self.id}, case_id='{self.case_id}', transcription_id={self.transcription_id}, "
            f"text='{self.text}', language='{self.language}', status='{self.status}')>"
        )