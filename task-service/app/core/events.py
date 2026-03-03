"""Event producer for  Task Service"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from shared.events.producer import EventProducer
from shared.events.schemas.events import TaskCreated, TaskUpdated
from .database import get_db
from ..crud.task import task_crud
from ..models.task import TaskStatus, TaskPriority

logger=logging.getLogger(__name__)

producer=EventProducer()

async def publish_task_created(db: AsyncSession, task_id: int):
    """Отправить событие TaskCreated при создании задачи"""
    task=await task_crud.get(db, task_id)
    if task:
        deadline = getattr(task, 'deadline', None)
        event=TaskCreated(
            source_service="task-service",
            source_entity_id=task_id,
            data={
                "title": task.title,
                "description": getattr(task, 'description', None),
                "owner_id": task.owner_id,
                "assignee_id": getattr(task, 'assignee_id', None),
                "status": getattr(task, 'status', TaskStatus.TODO.value),
                "priority": getattr(task, 'priority', TaskPriority.MEDIUM.value),
                "deadline": str(deadline) if deadline else None
            }
        )
        await producer.publish(event)
        logger.info(f"TaskCreated(id={task_id}):  {event.data['title']}")


async def publish_task_updated(
        db: AsyncSession,
        task_id: int,
        changes: Dict[str, Any]
):
    task=await task_crud.get(db, task_id)
    if task:
        event_data={
            "previous_status": changes.get('previous_status'),
            **changes,
            "owner_id": task.owner_id
        }

        event=TaskUpdated(
            source_service="task-service",
            source_entity_id=task_id,
            data=event_data
        )
        await producer.publish(event)
        logger.info(f"Task Updated (id={task_id}): {changes}")
