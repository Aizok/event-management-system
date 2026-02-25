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
        db.commit()
        db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, task_id: int, owner_id: Optional[int]=None) -> Optional[Task]:
        return db.query(Task).filter(Task.id==task_id).first()

    async def get_multi(self, db: AsyncSession, skip: int=0, limit: int=100, owner_id: int = None) -> List[Task]:
        query=db.query(Task)
        if owner_id:
            query=query.filter(Task.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()

    async def get_by_event(self, db: AsyncSession, event_id: int, owner_id: int = None) -> List[Task]:
        query=db.query(Task).filter(Task.event_id==event_id)
        if owner_id:
            query=query.filter(Task.owner_id==owner_id)
        return query.all()

    async def update(self, db: AsyncSession, task_id: int, obj_in: TaskUpdate, owner_id: int) -> Task:
        db_obj=self.get(db, task_id)
        if not db_obj:
            raise ValueError("Task not found")

        #TODO Проверка по роли

        update_data=obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj


    async def delete(self, db: AsyncSession, task_id: int) -> bool:
        obj=self.get(db, task_id)
        if obj:
            db.delete(obj)
            db.commit()
            return True
        return False

task_crud=TaskCRUD()