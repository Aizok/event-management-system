import enum

from pydantic import BaseModel, Field
from typing import List, Optional


class GenerateRequest(BaseModel):
    description: str = Field(..., min_length=10)
    event_id: int


class TaskItem(BaseModel):
    """То, что возвращает AI (сырые данные)"""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    estimated_hours: int | None = Field(default=None, ge=1, le=100)


class CreatedTask(BaseModel):
    id: int
    title: str
    description: Optional[str]
    estimated_hours: Optional[int]
    event_id: int


class GenerateResponse(BaseModel):
    event_name: str
    tasks: List[CreatedTask]
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