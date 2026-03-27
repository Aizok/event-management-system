from sqlalchemy import String, Text, DateTime, Float, Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum


class ResourceType(str, enum.Enum):
    EQUIPMENT = "equipment"
    VENUE = "venue"
    PERSONNEL = "personnel"
    MATERIAL = "material"

class ResourceStatus(str, enum.Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    MAINTENANCE = "maintenance"


class Resource(Base):
    __tablename__ = "resources"

    id:Mapped[int]=mapped_column(primary_key=True, index=True)
    name:Mapped[str]=mapped_column(String(255), nullable=False, index=True)
    type:Mapped[ResourceType]=mapped_column(SAEnum(ResourceType), nullable=False)

    description:Mapped[str | None]=mapped_column(Text, nullable=True)
    quantity: Mapped[int]=mapped_column(Integer, default=1)

    cost_per_hour: Mapped[float | None]=mapped_column(Float, nullable=True)

    owner_id: Mapped[int]=mapped_column(Integer, nullable=False, index=True)

    created_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    allocations: Mapped[list["ResourceAllocation"]]=relationship(
        "ResourceAllocation",
        back_populates="resource",
        cascade="all, delete-orphan"
    )


class ResourceAllocation(Base):
    __tablename__ = "resource_allocations"

    id:Mapped[int]=mapped_column(primary_key=True, index=True)

    resource_id: Mapped[int]=mapped_column(ForeignKey("resources.id"))
    resource: Mapped["Resource"]=relationship(
        "Resource",
        back_populates="allocations"
    )

    task_id: Mapped[int]=mapped_column(Integer, nullable=True, index=True)
    event_id: Mapped[int]=mapped_column(Integer, nullable=True, index=True)
    owner_id: Mapped[int]=mapped_column(Integer, nullable=False, index=True)

    quantity_used: Mapped[int]=mapped_column(Integer, default=1)
    status: Mapped[ResourceStatus]=mapped_column(SAEnum(ResourceStatus), default=ResourceStatus.AVAILABLE)

    date_start: Mapped[DateTime]=mapped_column(DateTime(timezone=True), nullable=False)
    date_end: Mapped[DateTime]=mapped_column(DateTime(timezone=True), nullable=False)

