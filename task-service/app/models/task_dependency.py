from sqlalchemy import String, Text, DateTime, Float, Enum as SAEnum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id: Mapped[int]=mapped_column(primary_key=True, index=True)

    # Зависимая задача, ребёнок
    task_id: Mapped[int]=mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True
    )

    # От какой зависит, родитель
    depends_on_task_id: Mapped[int]=mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"),
        index=True
    )

    task: Mapped["Task"]=relationship(
        "Task",
        foreign_keys=[task_id],
        back_populates="dependencies"
    )

    depends_on: Mapped["Task"]=relationship(
        "Task",
        foreign_keys=[depends_on_task_id],
        back_populates="dependents"
    )

    __table_args__ = (
        UniqueConstraint("task_id", "depends_on_task_id", name="uq_task_dependency"),
    )