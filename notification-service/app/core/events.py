import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from shared.events.consumer import EventConsumer
from shared.events.schemas.events import BaseEvent, TaskCreated

logger=logging.getLogger(__name__)

consumer=EventConsumer()

async def handle_task_created(event: BaseEvent):
    """Обработчик события TaskCreated - создаём уведомление в бд"""
    logger.info(f"Task Created received: task_id={event.event_id}, title='{event.data.get('title')}'")

    task_data=event.data
    user_id=task_data.get("assignee_id") or task_data.get("owner_id")

    if user_id:
        # TODO: 1. Найти пользователя в БД
        # TODO: 2. Отправить email/push notification
        # TODO: 3. Обновить user notifications в БД

        logger.info(f"Notification Created for user {user_id} about task with id={event.event_id}")
    else:
        logger.warning(f"There is no user_id in task {event.event_id}")


async def start_notification_consumer():
    """Запуск consumer в фоне"""
    logger.info("Starting consumer in Notification service")
    queue=await consumer.consume(
        queue_name="notification_events", #Другая очередь
        routing_keys=[
            "TaskCreated.task-service"
        ],
        callback=handle_task_created
    )
    logger.info(f"Notification consumer was starting on queue: {queue.name}")
    return queue

