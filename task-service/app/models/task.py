from sqlalchemy import String, Text, DateTime, Float, Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

import enum


class TaskStatus(str, enum.Enum):
    TODO="todo"
    IN_PROGRESS="in_progress"
    DONE="done"
    OVERDUE="overdue"


class TaskPriority(str, enum.Enum):
    LOW="low"
    MEDIUM="medium"
    HIGH="high"


class Task(Base):
    __tablename__ = "tasks"

    id:Mapped[int]=mapped_column(primary_key=True, index=True)
    title:Mapped[str]=mapped_column(String(255), nullable=False)
    description:Mapped[str | None]=mapped_column(Text, nullable=True)

    status:Mapped[TaskStatus]=mapped_column(SAEnum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority:Mapped[TaskPriority]=mapped_column(SAEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)

    created_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    start_time: Mapped[DateTime]=mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[DateTime]=mapped_column(DateTime(timezone=True), nullable=False)
    deadline:Mapped[DateTime]=mapped_column(DateTime(timezone=True), nullable=False)

    event_id: Mapped[int]=mapped_column(Integer, nullable=True, index=True)
    owner_id: Mapped[int]=mapped_column(Integer, nullable=False, index=True)
    assignee_id: Mapped[int | None]=mapped_column(Integer, nullable=True, index=True)

    dependencies: Mapped[list["TaskDependency"]]=relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan"
    )

    dependents: Mapped[list["TaskDependency"]]=relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.depends_on_task_id",
        back_populates="depends_on",
        cascade="all, delete-orphan"
    )

    history: Mapped[list["TaskHistory"]]=relationship(
        "TaskHistory",
        back_populates="task",
        cascade="all, delete-orphan"
    )
