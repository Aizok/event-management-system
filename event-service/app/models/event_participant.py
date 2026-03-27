from sqlalchemy import ForeignKey, Enum as SAEnum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum

class ParticipantRole(str, enum.Enum):
    OWNER = "owner"
    ORGANIZER = "organizer"
    EXECUTOR = "executor"
    VIEWER = "viewer"

class EventParticipant(Base):
    __tablename__ = "event_participants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(index=True)

    role: Mapped[ParticipantRole] = mapped_column(SAEnum(ParticipantRole), nullable=False)

    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="participants"
    )
