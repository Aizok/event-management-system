from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..models.task_dependency import TaskDependency
from ..schemas.task import TaskCreate, TaskUpdate


class TaskDependencyCRUD:

    async def create(self, db: AsyncSession, task_id: int, depends_on_task_id: int) -> TaskDependency:
        db_obj=TaskDependency(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    # async def get_dependencies(self, db: AsyncSession, task_id: int) -> List[TaskDependency]:
