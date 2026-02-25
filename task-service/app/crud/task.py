from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..models.task import Task
from ..schemas.task import TaskCreate, TaskUpdate


class TaskCRUD:
    async def create(self, db: AsyncSession, obj_in: TaskCreate, owner_id: int) -> Task:
        db_obj=Task(
            **obj_in.model_dump(),
            owner_id=owner_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def get(self, db: AsyncSession, task_id: int, owner_id: Optional[int]=None) -> Optional[Task]:
        query = select(Task).where(Task.id == task_id)
        if owner_id:
            query=query.where(Task.owner_id==owner_id)
        result=await db.execute(query)
        return result.scalar_one_or_none()


    async def get_multi(self, db: AsyncSession, skip: int=0, limit: int=100, owner_id: Optional[int] = None) -> List[Task]:
        query = select(Task).offset(skip).limit(limit).order_by(Task.created_at.desc())
        if owner_id:
            query = query.where(Task.owner_id == owner_id)
        result = await db.execute(query)
        return result.scalars().all()


    async def get_by_event(self, db: AsyncSession, event_id: int, owner_id: int = None) -> List[Task]:
        query=select(Task).where(Task.event_id==event_id)
        if owner_id:
            query=query.where(Task.owner_id==owner_id)
        result=await db.execute(query)
        return result.scalars().all()


    async def update(self, db: AsyncSession, task_id: int, obj_in: TaskUpdate, owner_id: Optional[int]=None) -> Optional[Task]:
        db_obj=await self.get(db, task_id, owner_id)
        if not db_obj:
            return None

        update_data=obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete(self, db: AsyncSession, task_id: int, owner_id: Optional[int]=None) -> bool:
        query=delete(Task).where(Task.id==task_id)
        if owner_id:
            query=query.where(Task.owner_id==owner_id)
        result=await db.execute(query)
        await db.commit()
        return result.rowcount > 0

task_crud=TaskCRUD()