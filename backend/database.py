# database.py — SQLModel engine + session dependency
from sqlmodel import SQLModel, Session, create_engine
from pathlib import Path
import models  # noqa: F401

DB_PATH = Path(__file__).parent / "auction.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session