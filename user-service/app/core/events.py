import logging
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from shared.events.consumer import EventConsumer
from shared.events.schemas.events import BaseEvent, TaskCreated

logger=logging.getLogger(__name__)

consumer=EventConsumer()

async def handle_task_created(event: BaseEvent):
    """Обработчик события TaskCreated – шлём пользователю уведомление"""
    task_id = event.source_entity_id
    event_id = event.event_id
    logger.info(f"Task Created received: task_id={task_id}, event_id={event_id}, title='{event.data.get('title')}'")

    task_data=event.data
    user_id=task_data.get("owner_id")

    if user_id:
        # TODO: 1. Найти пользователя в БД
        # TODO: 2. Отправить email/push notification
        # TODO: 3. Обновить user notifications в БД

        logger.info(f"Notification was sent to user {user_id} about task with id={task_id} (event_id={event_id})")
    else:
        logger.warning(f"There is no user_id in task {task_id} (event_id={event_id})")


async def start_user_consumer():
    """Запуск consumer в фоне"""
    logger.info("Starting consumer in User-service")
    queue=await consumer.consume(
        queue_name="user_events",
        routing_keys=[
            "TaskAssigned.task-service"
        ],
        callback=handle_task_created
    )
    logger.info(f"User consumer was starting on queue: {queue.name}")
    return queue

