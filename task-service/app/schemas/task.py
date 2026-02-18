from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.task import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    title: str=Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TaskCreate(TaskBase):
    event_id: int
    assignee_id: Optional[int] = None
    priority: TaskPriority=TaskPriority.MEDIUM
    deadline: Optional[datetime]= None


class TaskUpdate(BaseModel):
    title: Optional[str]=None
    description: Optional[str]=None
    status: Optional[TaskStatus]=None
    priority: Optional[TaskPriority]=None
    assignee_id: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    deadline: Optional[datetime]
    updated_at: Optional[datetime]
    event_id: int
    assignee_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    user_id: int
    email: Optional[str] = None
    role: Optional[str] = None