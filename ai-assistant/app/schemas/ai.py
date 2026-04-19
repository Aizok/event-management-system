import enum

from pydantic import BaseModel, Field
from typing import List, Optional


class GenerateRequest(BaseModel):
    description: str = Field(..., min_length=10)
    event_id: int


class TaskItem(BaseModel):
    """То, что возвращает AI (сырые данные)"""
    title: str
    description: Optional[str] = None
    estimated_hours: Optional[int] = None


class CreatedTask(BaseModel):
    id: int
    title: str
    description: Optional[str]
    estimated_hours: Optional[int]
    event_id: int


class GenerateResponse(BaseModel):
    event_name: str
    tasks: List[CreatedTask]


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