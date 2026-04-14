from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

class EventType(str, Enum):
    TASK_CREATED = "TaskCreated"
    TASK_UPDATED = "TaskUpdated"
    TASK_ASSIGNED = "TaskAssigned"
    TASK_RESCHEDULED = "TaskRescheduled"
    TASK_COMPLETED = "TaskCompleted"
    EVENT_CREATED = "EventCreated"
    RESOURCE_ALLOCATED = "ResourceAllocated"
    RESOURCE_RELEASED = "ResourceReleased"


class BaseEvent(BaseModel):
    event_type: EventType
    event_id: str = Field(default_factory=lambda : str(uuid4()))
    source_service: str
    source_entity_id: Optional[int]
    timestamp: datetime=Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any]={}

class TaskCreated(BaseEvent):
    event_type: EventType=EventType.TASK_CREATED

class TaskAssigned(BaseEvent):
    event_type: EventType = EventType.TASK_ASSIGNED

class TaskUpdated(BaseEvent):
    event_type: EventType = EventType.TASK_UPDATED

class TaskRescheduled(BaseEvent):
    event_type: EventType = EventType.TASK_RESCHEDULED
