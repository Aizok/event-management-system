import enum

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional
from datetime import datetime
from ..models.notification import NotificationType, NotificationStatus

class NotificationBase(BaseModel):
    task_id: Optional[int] = Field(None, gt=0)
    event_id: Optional[int] = Field(None, gt=0)
    recipient_id: int = Field(..., gt=0)
    initiator_id: int = Field(..., gt=0)
    type: NotificationType = NotificationType.EMAIL
    title: str = Field(..., max_length=255)

    @model_validator(mode="after")
    def require_task_or_event(self):
        if self.task_id is None and self.event_id is None:
            raise ValueError("Either task_id or event_id must be set")
        return self


# Создание (Consumer)
class NotificationCreate(NotificationBase):
    message: Optional[str] = Field(None, max_length=5000)


class NotificationResponse(NotificationBase):
    id: int
    status: NotificationStatus
    message: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    updated_at: datetime
    retry_count: int
    max_retries: int

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
