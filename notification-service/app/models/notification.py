from sqlalchemy import String, Text, DateTime, Enum as SAEnum, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from enum import Enum


class NotificationType(str, Enum):
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    event_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    recipient_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    initiator_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)

    type: Mapped[NotificationType] = mapped_column(
        SAEnum(NotificationType),
        default=NotificationType.EMAIL,
        nullable=False
    )

    status: Mapped[NotificationStatus] = mapped_column(
        SAEnum(NotificationStatus),
        default=NotificationStatus.PENDING,
        nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    sent_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
