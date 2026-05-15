import logging
import asyncio
from .user_client import get_user_email
from .email import send_email
from ..crud.notification import notification_crud
from ..schemas.notification import NotificationCreate, NotificationType, NotificationStatus
from .database import AsyncSessionLocal
from shared.events.consumer import EventConsumer
from shared.events.schemas.events import BaseEvent, EventType

from datetime import datetime, timezone


logger = logging.getLogger(__name__)

consumer = EventConsumer()


async def _notify_task_recipient(
    *,
    task_id: int,
    recipient_id: int,
    initiator_id: int | None,
    title: str,
    message: str,
):
    eff_initiator = int(initiator_id) if initiator_id is not None else int(recipient_id)
    async with AsyncSessionLocal() as db:
        notification = await notification_crud.create(
            db=db,
            obj_in=NotificationCreate(
                task_id=task_id,
                recipient_id=recipient_id,
                initiator_id=eff_initiator,
                title=f"Новая задача '{title}'",
                message=message,
            ),
        )
        logger.info(f"Notification created id={notification.id}")

        user_email = await get_user_email(notification.recipient_id)
        if not user_email:
            await notification_crud.update_status(db, notification.id, NotificationStatus.FAILED)
            logger.warning(f"User email not found for recipient_id={recipient_id}")
            return
        try:
            success = send_email(
                to_email=user_email,
                subject=notification.title,
                body=notification.message or "New task assigned",
            )
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            success = False

        final_status = NotificationStatus.SENT if success else NotificationStatus.FAILED
        sent_at = datetime.now(timezone.utc) if success else None

        await notification_crud.update_status(
            db=db,
            notification_id=notification.id,
            status=final_status,
            sent_at=sent_at,
        )

        logger.info(f"Notification {notification.id} -> {final_status}")


async def handle_task_assigned(event: BaseEvent):
    task_id = event.source_entity_id
    task_data = event.data
    recipient_id = task_data.get("assignee_id")
    initiator_id = task_data.get("owner_id")
    title = task_data.get("title") or ""

    logger.info(
        f"TaskAssigned: task_id={task_id}, title='{title}', recipient_id={recipient_id}"
    )

    if recipient_id:
        await _notify_task_recipient(
            task_id=task_id,
            recipient_id=recipient_id,
            initiator_id=initiator_id,
            title=title,
            message=f"Задача #{task_id}: {title}",
        )
    else:
        logger.warning(f"No assignee_id for task {task_id}")


async def handle_task_assignee_invited(event: BaseEvent):
    task_id = event.source_entity_id
    task_data = event.data
    invitee_ids = task_data.get("invitee_ids") or []
    initiator_id = task_data.get("owner_id")
    title = task_data.get("title") or ""

    logger.info(
        f"TaskAssigneeInvited: task_id={task_id}, invitee_ids={invitee_ids}"
    )

    for recipient_id in invitee_ids:
        if not recipient_id:
            continue
        await _notify_task_recipient(
            task_id=task_id,
            recipient_id=int(recipient_id),
            initiator_id=initiator_id,
            title=title,
            message=f"Приглашение исполнителем по задаче #{task_id}: {title}",
        )


async def dispatch_task_notification(event: BaseEvent):
    if event.event_type == EventType.TASK_ASSIGNED:
        await handle_task_assigned(event)
    elif event.event_type == EventType.TASK_ASSIGNEE_INVITED:
        await handle_task_assignee_invited(event)
    else:
        logger.warning(f"Ignored event type {event.event_type}")


async def start_notification_consumer():
    logger.info("Starting consumer in Notification-service")

    while True:
        try:
            await consumer.consume(
                queue_name="notification_events",
                routing_keys=[
                    "TaskAssigned.task-service",
                    "TaskAssigneeInvited.task-service",
                ],
                callback=dispatch_task_notification,
            )
            logger.info("Consumer started")
            return

        except Exception as e:
            logger.error(f"Consumer crashed: {e}")
            await asyncio.sleep(5)
