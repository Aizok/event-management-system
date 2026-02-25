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


    async def get_resource(self, db: AsyncSession, resource_id: int, owner_id: Optional[int] = None) -> Optional[Resource]:
        query = select(Resource).where(Resource.id == resource_id)
        if owner_id:
            query = query.where(Resource.owner_id == owner_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


    async def get_with_allocations(self, db: AsyncSession, resource_id: int, owner_id: int) -> Optional[Resource]:
        query=select(Resource).options(selectinload(Resource.allocations)).where(Resource.id==resource_id)
        if owner_id:
            query=query.where(Resource.owner_id==owner_id)
        result=await db.execute(query)
        return result.scalar_one_or_none()


    async def get_multi_resources(self, db: AsyncSession, skip: int=0, limit: int=100, owner_id: Optional[int]=None) -> List[Resource]:
        query=select(Resource).offset(skip).limit(limit)
        if owner_id:
            query=query.where(Resource.owner_id==owner_id)
        result=await db.execute(query)
        return result.scalars().all()


    async def update_resource(self, db: AsyncSession, resource_id: int, obj_in: ResourceUpdate, owner_id: int) -> Optional[Resource]:
        db_obj=await self.get_resource(db, resource_id, owner_id)
        if not db_obj:
            return None

        update_data=obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete_resource(self, db: AsyncSession, resource_id: int, owner_id: Optional[int] = None) -> bool:
        query = delete(Resource).where(Resource.id == resource_id)
        if owner_id:
            query = query.where(Resource.owner_id == owner_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    """Allocations"""
    async def create_allocation(self, db: AsyncSession, obj_in: ResourceAllocationCreate, owner_id: int) -> ResourceAllocation:
        db_obj=ResourceAllocation(
            **obj_in.model_dump(),
            owner_id=owner_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def get_allocation(self, db: AsyncSession, allocation_id: int, owner_id: Optional[int] = None) -> Optional[ResourceAllocation]:
        query=select(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
        if owner_id:
            query=query.where(ResourceAllocation.owner_id==owner_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


    async def get_multi_allocations(self, db: AsyncSession, skip: int=0, limit: int=100, owner_id: Optional[int] = None) -> List[ResourceAllocation]:
        query=select(ResourceAllocation).offset(skip).limit(limit).order_by(ResourceAllocation.id)
        if owner_id:
            query=query.where(ResourceAllocation.owner_id == owner_id)
        result=await db.execute(query)
        return result.scalars().all()


    async def update_allocation(self, db: AsyncSession, allocation_id: int, obj_in: ResourceAllocationUpdate, owner_id: int)->Optional[ResourceAllocation]:
        db_obj=await self.get_allocation(db, allocation_id, owner_id)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete_allocation(self, db: AsyncSession, allocation_id: int, owner_id: Optional[int] = None) -> bool:
        query = delete(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
        if owner_id:
            query=query.where(ResourceAllocation.owner_id==owner_id)
        result=await db.execute(query)
        await db.commit()
        return result.rowcount > 0


resource_crud=ResourceCRUD()