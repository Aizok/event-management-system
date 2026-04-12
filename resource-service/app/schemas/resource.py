import enum

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from ..models.resource import AllocationStatus, ResourceType


class ResourceBase(BaseModel):
    name: str=Field(..., min_length=1, max_length=255)
    type: ResourceType
    description: Optional[str] = None
    quantity: int=Field(1, ge=1, le=1000)
    cost_per_hour: Optional[float]=Field(None, ge=0)


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    name: Optional[str]=None
    type: Optional[ResourceType]=None
    description: Optional[str] = None
    quantity: Optional[int]=Field(None, ge=1, le=1000)
    cost_per_hour: Optional[float]=Field(None, ge=0)


class ResourceResponse(ResourceBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    allocations: List["ResourceAllocationResponse"]=Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ResourceAllocationCreate(BaseModel):
    resource_id: int
    task_id: Optional[int]=None
    event_id: int
    quantity_used: int=1
    date_start: datetime
    date_end: datetime


class ResourceAllocationUpdate(BaseModel):
    resource_id: Optional[int]=None
    task_id: Optional[int]=None
    event_id: Optional[int]=None
    quantity_used: Optional[int]=Field(None, ge=1, le=1000)
    date_start: Optional[datetime]=None
    date_end: Optional[datetime]=None


class ResourceAllocationResponse(BaseModel):
    id: int
    resource_id: int
    task_id: Optional[int]
    event_id: int
    owner_id: int
    quantity_used: int
    status: AllocationStatus
    date_start: datetime
    date_end: datetime

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