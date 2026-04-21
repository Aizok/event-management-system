from datetime import datetime
import enum

from sqlalchemy import String, Text, DateTime, Float, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class EventStatus(str, enum.Enum):
    DRAFT="draft"
    PUBLISHED="published"
    CANCELLED="cancelled"
    COMPLETED="completed"


class Event(Base):
    __tablename__="events"

    id:Mapped[int]=mapped_column(primary_key=True, index=True)
    title:Mapped[str]=mapped_column(String(255), nullable=False)
    description:Mapped[str | None]=mapped_column(Text, nullable=True)

    start_time: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False)

    location:Mapped[str |None]=mapped_column(String(255), nullable=True)
    budget:Mapped[float]=mapped_column(Float, default=0.0)

    status:Mapped[EventStatus]=mapped_column(SAEnum(EventStatus), default=EventStatus.DRAFT, nullable=False)
    owner_id:Mapped[int]=mapped_column(nullable=False)

    created_at=mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    participants: Mapped[list["EventParticipant"]]=relationship(
        "EventParticipant",
        back_populates="event",
        cascade="all, delete-orphan"
    )
