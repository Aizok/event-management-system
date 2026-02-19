from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.resource import ResourceStatus, ResourceType

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

    model_config = ConfigDict(from_attributes=True)


class ResourceAllocationCreate(BaseModel):
    resource_id: int
    task_id: Optional[int]=None
    event_id: Optional[int]=None
    quantity_used: int=1
    date_start: datetime
    date_end: datetime


class ResourceAllocationResponse(BaseModel):
    id: int
    resource_id: int
    task_id: Optional[int]
    event_id: Optional[int]
    quantity_used: int
    status: ResourceStatus
    date_start: datetime
    date_end: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    user_id: int
    email: Optional[str] = None
    role: Optional[str] = None