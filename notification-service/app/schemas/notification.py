from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.notification import NotificationType, NotificationStatus

class NotificationBase(BaseModel):
    task_id: int=Field(..., gt=0) # Из события TaskCreated
    recipient_id: int=Field(..., gt=0) # Из события assignee_id
    initiator_id: int=Field(..., gt=0)
    type: NotificationType=NotificationType.EMAIL
    title: str=Field(..., max_length=255)

# Создание (Consumer)
class NotificationCreate(NotificationBase):
    message: Optional[str]=Field(None, max_length=5000)


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


class TokenData(BaseModel):
    user_id: int
    email: Optional[str] = None
    role: Optional[str] = None
