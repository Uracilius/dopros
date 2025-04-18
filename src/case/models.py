from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from enums import CaseStatus
from enum import Enum

Base = declarative_base()  # Use SQLAlchemy's declarative base


class CaseModel(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    mp3_url = Column(String, nullable=True)
    status = Column(String, default=CaseStatus.RECEIVED, nullable=False)
    is_deleted = Column(Boolean, default=False)
    create_date = Column(DateTime, default=datetime.utcnow)
    update_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def next_case_status(self):
        """Advance the case status to the next stage."""
        status_order = [
            CaseStatus.RETRIEVE.value,
            CaseStatus.RECEIVED.value,
            CaseStatus.TRANSCRIPTION.value,
            CaseStatus.ENHANCEMENT.value,
            CaseStatus.ANALYSIS.value,
            CaseStatus.COMPLETED.value,
        ]

        if self.status in status_order:
            current_index = status_order.index(self.status)
            if current_index < len(status_order) - 1:
                self.status = status_order[current_index + 1]
