from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class TaskHistory(Base):
    __tablename__ = "task_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    changed_by: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    field: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)

    changed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="history"
    )