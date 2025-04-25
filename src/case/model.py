from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from src.case.enums import TranscriptionStatus
from enum import Enum

Base = declarative_base()  # Use SQLAlchemy's declarative base


class TranscriptionModel(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    mp3_url = Column(String, nullable=True)
    full_text = Column(String, nullable=True)
    improved_text = Column(String, nullable=True)
    status = Column(String, default=TranscriptionStatus.RECEIVED, nullable=False)
    is_deleted = Column(Boolean, default=False)
    create_date = Column(DateTime, default=datetime.utcnow)
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def next_transcription_status(self):
        """Advance the transcription status to the next stage."""
        status_order = [
            TranscriptionStatus.RETRIEVE.value,
            TranscriptionStatus.RECEIVED.value,
            TranscriptionStatus.TRANSCRIPTION.value,
            TranscriptionStatus.ENHANCEMENT.value,
            TranscriptionStatus.ANALYSIS.value,
            TranscriptionStatus.COMPLETED.value,
        ]

        if self.status in status_order:
            current_index = status_order.index(self.status)
            if current_index < len(status_order) - 1:
                self.status = status_order[current_index + 1]


class InfoUnitModel(Base):
    __tablename__ = "info_units"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, nullable=False)
    transcription_id = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    language = Column(String(10), nullable=False)
    status = Column(String, default="unverified", nullable=False)
