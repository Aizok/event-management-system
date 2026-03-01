from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class EventType(str, Enum):
    TASK_CREATED="TaskCreated"
    TASK_UPDATED="TaskUpdated"
    TASK_COMPLETED="TaskCompleted"
    EVENT_CREATED="EventCreated"
    RESOURCE_ALLOCATED="ResourceAllocated"
    RESOURCE_RELEASED="ResourceReleased"

class BaseEvent(BaseModel):
    event_type: EventType
    event_id: Optional[int]=None
    source_service: str
    source_entity_id: Optional[int]
    timestamp: datetime=Field(default_factory=lambda: datetime.now(timezone.utc))
    data: Dict[str, Any]={}

class TaskCreated(BaseEvent):
    event_type: EventType=EventType.TASK_CREATED

class TaskUpdated(BaseEvent):
    event_type: EventType = EventType.TASK_UPDATED

class EventCreated(BaseEvent):
    event_type: EventType = EventType.EVENT_CREATED