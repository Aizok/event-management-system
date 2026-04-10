from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..models.task_history import TaskHistory
from datetime import datetime, timezone, timedelta


class TaskHistoryCRUD:
    async def get_by_task(self, db: AsyncSession, task_id: int) -> List[TaskHistory]:
        query=select(TaskHistory).where(TaskHistory.task_id==task_id).order_by(TaskHistory.changed_at.desc())
        result=await db.execute(query)
        return result.scalars().all()


    async def get(self, db: AsyncSession, history_id: int) -> Optional[TaskHistory]:
        query=select(TaskHistory).where(TaskHistory.id==history_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()


    async def delete(self, db: AsyncSession, history_id: int) -> bool:
        query = delete(TaskHistory).where(TaskHistory.id == history_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

task_history_crud=TaskHistoryCRUD()