from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from src.case.entity import Base, TranscriptionEntity, CaseEntity

DATABASE_URL = "sqlite:///transcriptions.db"

engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Session = scoped_session(SessionLocal)


def get_db_session():
    db = Session()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import os

    if os.path.exists("transcriptions.db"):
        os.remove("transcriptions.db")
    init_db()
