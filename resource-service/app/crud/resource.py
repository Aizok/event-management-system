from datetime import datetime

from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..models.resource import Resource, ResourceAllocation
from ..schemas.resource import ResourceCreate, ResourceUpdate, ResourceAllocationCreate, ResourceAllocationUpdate

class ResourceCRUD:
    async def create_resource(self, db: AsyncSession, obj_in: ResourceCreate, owner_id: int) -> Resource:
        db_obj=Resource(
            **obj_in.model_dump(),
            owner_id=owner_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def get_resource(self, db: AsyncSession, resource_id: int) -> Optional[Resource]:
        query = select(Resource).where(Resource.id == resource_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


    async def get_with_allocations(self, db: AsyncSession, resource_id: int) -> Optional[Resource]:
        query=select(Resource).options(selectinload(Resource.allocations)).where(Resource.id==resource_id)
        result=await db.execute(query)
        return result.scalar_one_or_none()


    async def get_multi_resources(self, db: AsyncSession, skip: int=0, limit: int=100) -> List[Resource]:
        query=select(Resource).offset(skip).limit(limit)
        result=await db.execute(query)
        return result.scalars().all()


    async def update_resource(self, db: AsyncSession, resource_id: int, obj_in: ResourceUpdate) -> Optional[Resource]:
        db_obj=await self.get_resource(db, resource_id)
        if not db_obj:
            return None

        update_data=obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete_resource(self, db: AsyncSession, resource_id: int) -> bool:
        query = delete(Resource).where(Resource.id == resource_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0


    """Allocations"""
    async def create_allocation(self, db: AsyncSession, obj_in: ResourceAllocationCreate, owner_id: int) -> ResourceAllocation:
        if obj_in.date_start >= obj_in.date_end:
            raise ValueError("Invalid time range")

        resource=await self.get_resource(db, obj_in.resource_id)
        if not resource:
            raise ValueError("Resource not found")

        overlaps=await self.get_overlapping_allocations(
            db,
            obj_in.resource_id,
            obj_in.date_start,
            obj_in.date_end
        )

        used_quantity=sum(a.quantity_used for a in overlaps)
        if used_quantity + obj_in.quantity_used > resource.quantity:
            raise ValueError("Not enough resource available")

        db_obj=ResourceAllocation(
            **obj_in.model_dump(),
            owner_id=owner_id
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def get_allocation(self, db: AsyncSession, allocation_id: int) -> Optional[ResourceAllocation]:
        query=select(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


    async def get_multi_allocations(self, db: AsyncSession, skip: int=0, limit: int=100) -> List[ResourceAllocation]:
        query=select(ResourceAllocation).offset(skip).limit(limit).order_by(ResourceAllocation.id)
        result=await db.execute(query)
        return result.scalars().all()


    async def update_allocation(self, db: AsyncSession, allocation_id: int, obj_in: ResourceAllocationUpdate)->Optional[ResourceAllocation]:
        db_obj=await self.get_allocation(db, allocation_id)
        if not db_obj:
            return None

        start=obj_in.date_start or db_obj.date_start
        end=obj_in.date_end or db_obj.date_end
        resource_id=obj_in.resource_id or db_obj.resource_id
        if start >= end:
            raise ValueError("Invalid time range")

        resource = await self.get_resource(db, resource_id)
        if not resource:
            raise ValueError("Resource not found")

        overlaps = await self.get_overlapping_allocations(
            db,
            resource_id,
            start,
            end,
            exclude_id=db_obj.id
        )

        used_quantity = sum(a.quantity_used for a in overlaps)
        new_quantity=obj_in.quantity_used or db_obj.quantity_used
        # or тут нужен, потому что в update могут и не передать quantity_used. В таком случае берём старое значение

        if used_quantity + new_quantity > resource.quantity:
            raise ValueError("Not enough resource available")

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete_allocation(self, db: AsyncSession, allocation_id: int) -> bool:
        query = delete(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
        result=await db.execute(query)
        await db.commit()
        return result.rowcount > 0


    async def get_overlapping_allocations(self, db: AsyncSession, resource_id: int, start: datetime, end: datetime, exclude_id: int | None = None):
        query=select(ResourceAllocation).where(
            ResourceAllocation.resource_id==resource_id,
            ResourceAllocation.date_start<end,
            ResourceAllocation.date_end>start
        )

        if exclude_id:
            query=query.where(ResourceAllocation.id != exclude_id)

        result=await db.execute(query)
        return result.scalars().all()


resource_crud=ResourceCRUD()