import enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.event_participant import ParticipantRole

class EventParticipantBase(BaseModel):
    user_id: int
    role: ParticipantRole


class EventParticipantCreate(EventParticipantBase):
    pass


class EventParticipantResponse(EventParticipantBase):
    id: int
    event_id: int

    model_config = ConfigDict(from_attributes=True)
