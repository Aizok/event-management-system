from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from .config import settings
from ..models.user import Base

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")

engine=create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db()-> Generator[Session, None, None]:
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

