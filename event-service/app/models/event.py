from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base=declarative_base()


class EventStatus(str, enum.Enum):
    DRAFT="draft"
    PUBLISHED="published"
    CANCELLED="cancelled"
    COMPLETED="completed"


class Event(Base):
    __tablename__="events"

    id=Column(Integer, primary_key=True, index=True)
    title=Column(String(255), nullable=False)
    description=Column(Text, nullable=False)

    start_date=Column(DateTime(timezone=True), nullable=False)
    end_date=Column(DateTime(timezone=True), nullable=False)

    location=Column(String(255), nullable=True)
    budget=Column(Float, default=0.0)

    status=Column(SQLEnum(EventStatus), default=EventStatus.DRAFT, nullable=False)
    owner_id=Column(Integer, nullable=False)

    created_at=Column(DateTime(timezone=True), server_default=func.now())
    updated_at=Column(DateTime(timezone=True), onupdate=func.now())