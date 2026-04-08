from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from ..models.task_dependency import TaskDependency
from ..schemas.task import TaskCreate, TaskUpdate
from .task import task_crud

class TaskDependencyCRUD:

    async def create(self, db: AsyncSession, task_id: int, depends_on_task_id: int, commit: bool=True) -> TaskDependency:
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
            if commit:
                await db.flush()
                await self.sync_task_and_descendants(db, task_id)

                await db.commit()
                await db.refresh(db_obj)
            else:
                await db.flush()

                await self.sync_task_and_descendants(db, task_id)

        except IntegrityError:
            if commit:
                await db.rollback()
            raise ValueError("duplicate_dependency")

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

        if result.rowcount > 0:
            await self.sync_task_and_descendants(db, task_id)
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


    async def get_parent_ids(self, db: AsyncSession, task_id: int) ->List[int]:
        query=select(TaskDependency.depends_on_task_id).where(
            TaskDependency.task_id == task_id
        )
        result=await db.execute(query)
        return [row[0] for row in result.all()]


    async def get_child_ids(self, db: AsyncSession, task_id: int) -> List[int]:
        query = select(TaskDependency.task_id).where(
            TaskDependency.depends_on_task_id == task_id
        )
        result = await db.execute(query)
        return [row[0] for row in result.all()]


    async def sync_task_and_descendants(self, db: AsyncSession, task_id: int):
        to_visit=[task_id]
        visited=set()

        while to_visit:
            current_id=to_visit.pop()

            if current_id in visited:
                continue

            visited.add(current_id)

            task=await task_crud.get(db, current_id)
            if task:
                await task_crud.sync_blocked_status(db, task)

            # Идём дальше по графу
            children=await self.get_child_ids(db, current_id)
            to_visit.extend(children)


task_dependency_crud = TaskDependencyCRUD()
