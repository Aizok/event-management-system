"""Event producer for  Task Service"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from shared.events.producer import EventProducer
from shared.events.schemas.events import TaskCreated, TaskUpdated
from database import get_db
from ..crud.task import task_crud

logger=logging.getLogger(__name__)

producer=EventProducer()

async def publish_rask_created(db: AsyncSession, task_id: int):
    """Отправить событие TaskCreated при создании задачи"""
    task=await task_crud.get(db, task_id)
    if task:
        event=TaskCreated(
            source_service="task-service",
            source_entity_id=task_id,
            data={
                "title": task.title,
                "description": task.description,
                "owner_id": task.owner_id,
                "event_id": getattr(task, 'event_id', None),
                "status": task.status
            }
        )