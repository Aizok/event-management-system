from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from .config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "client_encoding": "UTF8"
    },
    pool_pre_ping=True
)

SessionLocal=sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()