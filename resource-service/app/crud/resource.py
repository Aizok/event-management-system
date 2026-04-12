from datetime import datetime, timezone
from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..models.resource import Resource, ResourceAllocation, AllocationStatus
from ..schemas.resource import ResourceCreate, ResourceUpdate, ResourceAllocationCreate, ResourceAllocationUpdate
from ..core.task_client import get_task

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

        # Проверка корректности временного диапазона
        if obj_in.date_start >= obj_in.date_end:
            raise ValueError("Invalid time range")

        # Проверка существования ресурса
        resource=await self.get_resource(db, obj_in.resource_id)
        if not resource:
            raise ValueError("Resource not found")

        # Если есть task_id, то есть ли такая task
        if obj_in.task_id is not None:
            task=await get_task(obj_in.task_id)
            if not task:
                raise ValueError("Task not found")
            # Проверка, чтобы event_id у RA совпадал с event_id таски
            if task["event_id"] != obj_in.event_id:
                raise ValueError("Task does not belong to this event")
            if task["status"] == "DONE":
                raise ValueError("Cannot allocate to completed task")

            task_start = datetime.fromisoformat(task["start_time"].replace("Z", "+00:00"))
            task_end = datetime.fromisoformat(task["end_time"].replace("Z", "+00:00"))

            if obj_in.date_start < task_start or obj_in.date_end > task_end:
                raise ValueError("Allocation outside task time")
        # Проверка конфликтов использования ресурса (по количеству)
        overlaps=await self.get_overlapping_allocations(
            db,
            obj_in.resource_id,
            obj_in.date_start,
            obj_in.date_end
        )

        used_quantity=sum(a.quantity_used for a in overlaps)
        if used_quantity + obj_in.quantity_used > resource.quantity:
            raise ValueError("Not enough resource available")

        # Создание
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

        if db_obj.status in [AllocationStatus.CANCELLED, AllocationStatus.COMPLETED]:
            raise ValueError("Cannot update completed or cancelled allocation")

        # Получение нужных значений, если они не переданы, берём старые
        start=obj_in.date_start or db_obj.date_start
        end=obj_in.date_end or db_obj.date_end
        resource_id=obj_in.resource_id or db_obj.resource_id
        event_id=obj_in.event_id or db_obj.event_id
        task_id=obj_in.task_id if obj_in.task_id is not None else db_obj.task_id

        # Корректность временного интервала
        if start >= end:
            raise ValueError("Invalid time range")

        # Проверка ресурса
        resource = await self.get_resource(db, resource_id)
        if not resource:
            raise ValueError("Resource not found")

        # Проверка таски
        if task_id is not None:
            task=await get_task(task_id)
            if not task:
                raise ValueError("Task not found")
            # Проверка принадлежности таски к ивенту
            if task["event_id"] != event_id:
                raise ValueError("Task does not belong to this event")
            if task["status"] == "DONE":
                raise ValueError("Cannot allocate to completed task")

            task_start=datetime.fromisoformat(task["start_time"].replace("Z", "+00:00"))
            task_end=datetime.fromisoformat(task["end_time"].replace("Z", "+00:00"))

            if start<task_start or end > task_end:
                raise ValueError("Allocation outside task time")

        # Проверка конфликтов
        overlaps = await self.get_overlapping_allocations(
            db,
            resource_id,
            start,
            end,
            exclude_id=db_obj.id
            # exclude_id для исключения подсчёта данного ресурса, так как запись о нём уже есть
        )

        used_quantity = sum(a.quantity_used for a in overlaps)
        new_quantity=(
            obj_in.quantity_used
            if obj_in.quantity_used is not None
            else db_obj.quantity_used
        )
        # В update могут и не передать quantity_used. В таком случае берём старое значение

        if used_quantity + new_quantity > resource.quantity:
            raise ValueError("Not enough resource available")

        # Обновление полей
        update_data = obj_in.model_dump(exclude_unset=True, exclude={"status"})
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        # Изменение статуса
        now=datetime.now(timezone.utc)
        if end <= now:
            db_obj.status = AllocationStatus.COMPLETED
        elif start <= now <end:
            db_obj.status=AllocationStatus.ACTIVE
        else:
            db_obj.status = AllocationStatus.PLANNED


        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete_allocation(self, db: AsyncSession, allocation_id: int) -> bool:
        query = delete(ResourceAllocation).where(ResourceAllocation.id == allocation_id)
        result=await db.execute(query)
        await db.commit()
        return result.rowcount > 0


    """ Различная логика """
    async def get_overlapping_allocations(self, db: AsyncSession, resource_id: int, start: datetime, end: datetime, exclude_id: int | None = None):
        query=select(ResourceAllocation).where(
            ResourceAllocation.resource_id==resource_id,
            ResourceAllocation.status != AllocationStatus.CANCELLED,
            ResourceAllocation.date_start<end,
            ResourceAllocation.date_end>start
        )

        if exclude_id is not None:
            query=query.where(ResourceAllocation.id != exclude_id)

        result=await db.execute(query)
        return result.scalars().all()


    async def update_allocation_statuses(self, db: AsyncSession):
        now=datetime.now(timezone.utc)
        # Planned в Active
        query=(
            update(ResourceAllocation)
            .where(
                ResourceAllocation.status == AllocationStatus.PLANNED,
                ResourceAllocation.date_start <= now,
                ResourceAllocation.date_end > now
            )
            .values(status=AllocationStatus.ACTIVE)
        )
        await db.execute(query)

        # Active в Completed
        query = (
            update(ResourceAllocation)
            .where(
                ResourceAllocation.status == AllocationStatus.ACTIVE,
                ResourceAllocation.date_end <= now
            )
            .values(status=AllocationStatus.COMPLETED)
        )
        await db.execute(query)
        await db.commit()


resource_crud=ResourceCRUD()