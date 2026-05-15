import enum

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from ..models.task import TaskStatus, TaskPriority


class TaskAssigneeResponse(BaseModel):
    user_id: int
    status: str
    invited_by: Optional[int] = None
    created_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class TaskAssigneeInvitationItem(BaseModel):
    task_id: int
    event_id: int
    event_title: str
    title: str
    invited_by: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TaskSentInvitationItem(BaseModel):
    task_id: int
    event_id: int
    event_title: str
    title: str
    invitee_user_id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TaskAssigneeInvite(BaseModel):
    user_id: int = Field(..., gt=0)


class TaskInvitationPreview(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    start_time: datetime
    end_time: datetime
    deadline: datetime
    event_id: int
    event_title: str

    model_config = ConfigDict(from_attributes=True)


class TaskBase(BaseModel):
    title: str=Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TaskCreate(TaskBase):
    event_id: int
    priority: TaskPriority=TaskPriority.MEDIUM
    deadline: datetime
    start_time: datetime
    end_time: datetime



class TaskUpdate(BaseModel):
    title: Optional[str]=None
    description: Optional[str]=None
    status: Optional[TaskStatus]=None
    priority: Optional[TaskPriority]=None
    deadline: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    deadline: datetime
    start_time: datetime
    end_time: datetime
    actual_start_time: Optional[datetime]
    actual_end_time: Optional[datetime]
    updated_at: Optional[datetime]
    event_id: int
    owner_id: int
    assignees: List[TaskAssigneeResponse] = Field(default_factory=list)

    is_late_start: bool = False

    model_config = ConfigDict(from_attributes=True)


class TaskBrief(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)


class TaskPage(BaseModel):
    items: List[TaskResponse]
    total: int


class TaskMetricsResponse(BaseModel):
    total: int
    overdue: int


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