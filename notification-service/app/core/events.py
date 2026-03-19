import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from .user_client import get_user_email
from .email import send_email
from ..crud.notification import notification_crud
from ..schemas.notification import NotificationCreate, NotificationType

from .database import AsyncSessionLocal

from shared.events.consumer import EventConsumer
from shared.events.schemas.events import BaseEvent, TaskCreated

logger=logging.getLogger(__name__)

consumer=EventConsumer()

async def handle_task_created(event: TaskCreated):
    # Было event: BaseEvent
    """Обработчик события TaskCreated – шлём пользователю уведомление"""
    task_id = event.source_entity_id
    event_id = event.event_id

    task_data=event.data
    user_id=task_data.get("assignee_id") or task_data.get("owner_id")

    logger.info(f"Task Created received: task_id={task_id}, event_id={event_id}, title='{event.data.get('title')}'")


    if user_id:
        async with AsyncSessionLocal() as db:
            notification=await notification_crud.create(
                db=db,
                obj_in=NotificationCreate(
                    task_id=task_id,
                    user_id=user_id,
                    title=f"Новая задача '{task_data['title']}'",
                    message=f"Задача #{task_id}: {task_data['title']}"
                )
            )
            logger.info(f"Notification created id={notification.id}")
    else:
        logger.warning(f"No user_id for task {task_id}")
        # TODO: 1. Найти пользователя в БД
        # TODO: 2. Отправить email/push notification
        # TODO: 3. Обновить user notifications в БД



async def start_notification_consumer():
    """Запуск consumer в фоне"""
    logger.info("Starting consumer in Notification-service")
    queue=await consumer.consume(
        queue_name="notification_events",
        routing_keys=[
            "TaskCreated.task-service"
        ],
        callback=handle_task_created
    )
    logger.info(f"Notification_events consumer was starting on queue: {queue.name}")
    return queue

