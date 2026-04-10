from sqlalchemy.ext.asyncio import AsyncSession
from ..crud.task import task_crud
from ..crud.task_dependency import task_dependency_crud

class TaskService:
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
                await task_crud.recalculate_schedule(db, current_id)

            # Идём дальше по графу
            children=await task_dependency_crud.get_child_ids(db, current_id)
            to_visit.extend(children)


task_service=TaskService()