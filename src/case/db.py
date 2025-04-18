from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# Import the *same* Base used by your model
from entity import Base, CaseEntity

DATABASE_URL = "sqlite:///cases.db"

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
    init_db()
