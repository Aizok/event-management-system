from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from ..models.task_dependency import TaskDependency
from ..schemas.task import TaskCreate, TaskUpdate


class TaskDependencyCRUD:

    async def create(self, db: AsyncSession, task_id: int, depends_on_task_id: int) -> TaskDependency:
        if task_id==depends_on_task_id:
            raise ValueError("self_dependency")
        if await self.has_cycle(db, task_id, depends_on_task_id):
            raise ValueError("dependency_cycle")

        db_obj=TaskDependency(
            task_id=task_id,
            depends_on_task_id=depends_on_task_id
        )
        db.add(db_obj)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise ValueError("duplicate_dependency")

        await db.refresh(db_obj)
        return db_obj


    async def get_dependencies(self, db: AsyncSession, task_id: int) -> List[TaskDependency]:
        query=select(TaskDependency).where(TaskDependency.task_id==task_id)
        result=await db.execute(query)
        return result.scalars().all()


    async def get_dependency_ids(self, db: AsyncSession, task_id: int) -> List[int]:
        query = select(TaskDependency.depends_on_task_id).where(
            TaskDependency.task_id == task_id
        )
        result = await db.execute(query)
        return [row[0] for row in result.all()]


    async def delete(
            self,
            db: AsyncSession,
            task_id: int,
            depends_on_task_id: int
    ) -> bool:
        query=delete(TaskDependency).where(
            TaskDependency.task_id==task_id,
            TaskDependency.depends_on_task_id==depends_on_task_id
        )
        result=await db.execute(query)
        await db.commit()

        return result.rowcount > 0

    async def has_cycle(
            self,
            db: AsyncSession,
            task_id: int,
            depends_on_task_id: int
    ) -> bool:
        """
        Проверяем: если мы добавим связь task_id -> depends_on_task_id,
        не появится ли цикл
        """

        to_visit = [depends_on_task_id]
        visited = set()

        while to_visit:
            current = to_visit.pop()

            if current == task_id:
                return True  # цикл найден

            if current in visited:
                continue

            visited.add(current)

            query = select(TaskDependency.depends_on_task_id).where(
                TaskDependency.task_id == current
            )
            result = await db.execute(query)
            next_nodes = [row[0] for row in result.all()]

            to_visit.extend(next_nodes)

        return False

task_dependency_crud = TaskDependencyCRUD()