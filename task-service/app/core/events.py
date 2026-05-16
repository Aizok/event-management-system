"""Event producer for  Task Service"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from shared.events.producer import EventProducer
from shared.events.schemas.events import (
    TaskCreated,
    TaskUpdated,
    TaskAssigned,
    TaskRescheduled,
    TaskAssigneeInvited,
)
from .database import get_db
from ..crud.task import task_crud
from ..crud.task_assignee import task_assignee_crud
from ..models.task import TaskStatus, TaskPriority
from ..models.task_assignee import TaskAssigneeStatus

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
    task = await task_crud.get(db, task_id)
    if not task:
        return

    assignee_rows = await task_assignee_crud.list_for_task(db, task_id)
    assignee_ids = [
        a.user_id
        for a in assignee_rows
        if a.status == TaskAssigneeStatus.ACCEPTED
    ]

    event_data = {
        "previous_status": changes.get("previous_status"),
        **changes,
        "owner_id": task.owner_id,
        "title": task.title,
        "assignee_ids": assignee_ids,
    }

    event = TaskUpdated(
        source_service="task-service",
        source_entity_id=task_id,
        data=event_data,
    )
    await producer.publish(event)
    logger.info(f"Task Updated (id={task_id}): {changes}")


async def publish_task_assignee_invited(
    db: AsyncSession, task_id: int, invitee_user_ids: list[int]
):
    """Уведомления о приглашении исполнителя (строка task_assignees со статусом pending)."""
    if not invitee_user_ids:
        return
    task = await task_crud.get(db, task_id)
    if not task:
        return
    event = TaskAssigneeInvited(
        source_service="task-service",
        source_entity_id=task_id,
        data={
            "invitee_ids": invitee_user_ids,
            "owner_id": task.owner_id,
            "title": task.title,
            "event_id": task.event_id,
        },
    )
    await producer.publish(event)
    logger.info(
        f"TaskAssigneeInvited(id={task_id}): invitees={invitee_user_ids}"
    )


async def publish_task_assigned_accept(
    db: AsyncSession, task_id: int, assignee_id: int
):
    task = await task_crud.get(db, task_id)
    if not task or not assignee_id:
        return
    assigned_event = TaskAssigned(
        source_service="task-service",
        source_entity_id=task_id,
        data={
            "assignee_id": assignee_id,
            "owner_id": task.owner_id,
            "title": task.title,
        },
    )
    await producer.publish(assigned_event)
    logger.info(f"TaskAssigned after accept (id={task_id}): assignee={assignee_id}")


async def publish_task_rescheduled(db: AsyncSession, task_id: int):
    task=await task_crud.get(db, task_id)
    if not task:
        return

    event=TaskRescheduled(
        source_service="task-service",
        source_entity_id=task_id,
        data={
            "task_id": task.id,
            "event_id": task.event_id,
            "start_time": task.start_time.isoformat(),
            "end_time": task.end_time.isoformat()
        }
    )

    await producer.publish(event)
    logger.info(
        f"TaskRescheduled (id={task_id})"
    )
