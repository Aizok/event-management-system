import enum
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional


class GenerateRequest(BaseModel):
    description: str = Field(..., min_length=10)
    event_id: int


class TaskTiming(str, enum.Enum):
    BEFORE = "before"
    DURING = "during"
    AFTER = "after"


class TaskPriority(str, enum.Enum):
    LOW="low"
    MEDIUM="medium"
    HIGH="high"


class TaskItem(BaseModel):
    """То, что возвращает AI (сырые данные)"""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    estimated_hours: int | None = Field(default=None, ge=1, le=100)
    timing: TaskTiming = TaskTiming.BEFORE
    priority: TaskPriority = TaskPriority.MEDIUM

    @field_validator("timing", mode="before")
    @classmethod
    def normalize_timing(cls, v):
        if isinstance(v, str):
            v=v.strip().lower()
            if v in {"before", "during", "after"}:
                return TaskTiming(v)
            return TaskTiming.BEFORE
        return v

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v):
        if isinstance(v, str):
            v=v.strip().lower()
            if v in {"low", "medium", "high"}:
                return TaskPriority(v)
            return TaskPriority.MEDIUM
        return v


class ProposedTask(BaseModel):
    """Черновик задачи с датами (как payload для task-service после планирования)."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    event_id: int
    start_time: datetime
    end_time: datetime
    deadline: datetime
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee_id: Optional[int] = None

    @field_validator("priority", mode="before")
    @classmethod
    def normalize_priority(cls, v):
        if isinstance(v, str):
            v = v.strip().lower()
            if v in {"low", "medium", "high"}:
                return TaskPriority(v)
            return TaskPriority.MEDIUM
        return v


class CreatedTask(BaseModel):
    id: int
    title: str
    description: Optional[str]
    event_id: int


class GenerateResponse(BaseModel):
    event_name: str
    tasks: List[ProposedTask]
    errors: List[str] = Field(default_factory=list)


class CommitGeneratedTasksRequest(BaseModel):
    event_id: int
    tasks: List[ProposedTask] = Field(default_factory=list, max_length=30)

    @model_validator(mode="after")
    def tasks_belong_to_event(self):
        for t in self.tasks:
            if t.event_id != self.event_id:
                raise ValueError("Каждая задача должна относиться к указанному мероприятию (event_id)")
        return self


class CommitGeneratedTasksResponse(BaseModel):
    tasks: List[CreatedTask] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class TokenRole(str, enum.Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    EXECUTOR = "executor"
    VIEWER = "viewer"
    SERVICE = "service"


class TokenData(BaseModel):
    role: TokenRole
    user_id: int | None = None
    email: str | None = None
    service_name: str | None = None