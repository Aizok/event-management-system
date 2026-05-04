import enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
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

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time < self.start_time:
            raise ValueError("end_time must be >= start_time")
        return self

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

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time is not None and self.end_time is not None and self.end_time < self.start_time:
            raise ValueError("end_time must be >= start_time")
        return self

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
