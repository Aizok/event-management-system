import enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.event import EventStatus

class EventBase(BaseModel):
    title: str=Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    location: Optional[str]=None
    budget: float = 0.0

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str]=None
    description: Optional[str]=None
    start_time: Optional[datetime]=None
    end_time: Optional[datetime]=None
    location: Optional[str] = None
    budget: Optional[float] = None
    status: Optional[EventStatus]=None

class EventResponse(EventBase):
    id: int
    status: EventStatus
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


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
