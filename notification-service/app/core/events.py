import logging
import asyncio
from .user_client import get_user_email
from .email import send_email
from ..crud.notification import notification_crud
from ..schemas.notification import NotificationCreate, NotificationType, NotificationStatus
from .database import AsyncSessionLocal
from shared.events.consumer import EventConsumer
from shared.events.schemas.events import BaseEvent, TaskCreated, TaskAssigned, TaskUpdated

from datetime import datetime, timezone


logger=logging.getLogger(__name__)

consumer=EventConsumer()

async def handle_task_assigned(event: TaskAssigned):
    """Обработчик события TaskAssigned – шлём пользователю уведомление"""
    task_id = event.source_entity_id
    event_id = event.event_id
    task_data=event.data

    recipient_id=task_data.get("assignee_id")
    initiator_id=task_data.get("owner_id")

    logger.info(f"Task Assigned received: task_id={task_id}, event_id={event_id}, title='{event.data.get('title')}'")

    if recipient_id:
        async with AsyncSessionLocal() as db:
            notification=await notification_crud.create(
                db=db,
                obj_in=NotificationCreate(
                    task_id=task_id,
                    recipient_id=recipient_id,
                    initiator_id=initiator_id,
                    title=f"Новая задача '{task_data['title']}'",
                    message=f"Задача #{task_id}: {task_data['title']}"
                )
            )
            logger.info(f"Notification created id={notification.id}")

            user_email=await get_user_email(notification.recipient_id)
            if not user_email:
                await notification_crud.update_status(db, notification.id, NotificationStatus.FAILED)
                logger.warning(f"User email not found for recipient_id={recipient_id}")
                return
            try:
                success = send_email(
                    to_email=user_email,
                    subject=notification.title,
                    body=notification.message or "New task assigned"
                )
            except Exception as e:
                logger.error(f"Email sending failed: {e}")
                success = False

            # Обновление статуса
            final_status = NotificationStatus.SENT if success else NotificationStatus.FAILED
            sent_at = datetime.now(timezone.utc) if success else None

            notification = await notification_crud.update_status(
                db=db,
                notification_id=notification.id,
                status=final_status,
                sent_at=sent_at
            )

            logger.info(f"Notification {notification.id} for event {event_id} -> {final_status}")

    else:
        logger.warning(f"No assignee_id for task {task_id}")


async def start_notification_consumer():
    logger.info("Starting consumer in Notification-service")

    while True:
        try:
            await consumer.consume(
                queue_name="notification_events",
                routing_keys=["TaskAssigned.task-service"],
                callback=handle_task_assigned
            )
            logger.info("✅ Consumer started")
            return

        except Exception as e:
            logger.error(f"Consumer crashed: {e}")
            await asyncio.sleep(5)

