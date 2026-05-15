import enum

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.event_participant import ParticipantRole, MembershipStatus

class EventParticipantBase(BaseModel):
    user_id: int
    role: ParticipantRole


class EventParticipantCreate(EventParticipantBase):
    pass


class EventParticipantResponse(EventParticipantBase):
    id: int
    event_id: int
    membership_status: MembershipStatus

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class EventParticipantInvitationItem(BaseModel):
    event_id: int
    title: str
    role: ParticipantRole
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class EventSentInvitationItem(BaseModel):
    event_id: int
    event_title: str
    invitee_user_id: int
    role: ParticipantRole

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
