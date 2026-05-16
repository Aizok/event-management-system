import logging
import asyncio
from .user_client import get_user_email
from .email import send_email
from ..crud.notification import notification_crud
from ..schemas.notification import NotificationCreate, NotificationStatus
from .database import AsyncSessionLocal
from shared.events.consumer import EventConsumer
from shared.events.schemas.events import BaseEvent, EventType

from datetime import datetime, timezone


logger = logging.getLogger(__name__)

consumer = EventConsumer()

_TASK_UPDATE_META_KEYS = frozenset(
    {
        "previous_status",
        "owner_id",
        "assignee_ids",
        "updated_by",
        "title",
    }
)


async def _send_notification_email(
    *,
    db,
    notification,
) -> None:
    user_email = await get_user_email(notification.recipient_id)
    if not user_email:
        await notification_crud.update_status(db, notification.id, NotificationStatus.FAILED)
        logger.warning(
            f"User email not found for recipient_id={notification.recipient_id}"
        )
        return
    try:
        success = send_email(
            to_email=user_email,
            subject=notification.title,
            body=notification.message or "",
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


async def _notify_task_recipient(
    *,
    task_id: int,
    recipient_id: int,
    initiator_id: int | None,
    notification_title: str,
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
                title=notification_title,
                message=message,
            ),
        )
        logger.info(f"Notification created id={notification.id}")
        await _send_notification_email(db=db, notification=notification)


async def _notify_event_recipient(
    *,
    event_id: int,
    recipient_id: int,
    initiator_id: int | None,
    notification_title: str,
    message: str,
):
    eff_initiator = int(initiator_id) if initiator_id is not None else int(recipient_id)
    async with AsyncSessionLocal() as db:
        notification = await notification_crud.create(
            db=db,
            obj_in=NotificationCreate(
                event_id=event_id,
                recipient_id=recipient_id,
                initiator_id=eff_initiator,
                title=notification_title,
                message=message,
            ),
        )
        logger.info(f"Notification created id={notification.id}")
        await _send_notification_email(db=db, notification=notification)


def _format_task_update_message(task_id: int, title: str, event_data: dict) -> str:
    changed = [
        key
        for key in event_data
        if key not in _TASK_UPDATE_META_KEYS
    ]
    body = f"Задача #{task_id} «{title}» обновлена."
    if changed:
        body += f" Изменены поля: {', '.join(changed)}."
    return body


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
            notification_title=f"Новая задача '{title}'",
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
            notification_title=f"Новая задача '{title}'",
            message=f"Приглашение исполнителем по задаче #{task_id}: {title}",
        )


async def handle_task_updated(event: BaseEvent):
    task_id = event.source_entity_id
    task_data = event.data
    title = task_data.get("title") or ""
    assignee_ids = task_data.get("assignee_ids") or []
    updated_by = task_data.get("updated_by")
    initiator_id = task_data.get("owner_id")

    logger.info(
        f"TaskUpdated: task_id={task_id}, assignee_ids={assignee_ids}, updated_by={updated_by}"
    )

    message = _format_task_update_message(task_id, title, task_data)
    notification_title = f"Задача обновлена: '{title}'"

    for recipient_id in assignee_ids:
        if not recipient_id:
            continue
        rid = int(recipient_id)
        if updated_by is not None and rid == int(updated_by):
            continue
        await _notify_task_recipient(
            task_id=task_id,
            recipient_id=rid,
            initiator_id=initiator_id,
            notification_title=notification_title,
            message=message,
        )


async def handle_event_participant_invited(event: BaseEvent):
    event_id = event.source_entity_id
    data = event.data
    recipient_id = data.get("invitee_id")
    initiator_id = data.get("inviter_id")
    title = data.get("title") or f"Мероприятие #{event_id}"
    role = data.get("role") or ""
    start_time = data.get("start_time") or ""
    end_time = data.get("end_time") or ""
    location = data.get("location") or "—"

    logger.info(
        f"EventParticipantInvited: event_id={event_id}, invitee_id={recipient_id}"
    )

    if not recipient_id:
        logger.warning(f"No invitee_id for event {event_id}")
        return

    location_line = f"Место: {location}\n" if location and location != "—" else ""
    message = (
        f"Вас пригласили в мероприятие #{event_id} «{title}».\n"
        f"Роль: {role}\n"
        f"Период: {start_time} — {end_time}\n"
        f"{location_line}"
        f"Примите или отклоните приглашение в личном кабинете."
    )

    await _notify_event_recipient(
        event_id=event_id,
        recipient_id=int(recipient_id),
        initiator_id=initiator_id,
        notification_title=f"Приглашение в мероприятие «{title}»",
        message=message,
    )


async def dispatch_notification(event: BaseEvent):
    if event.event_type == EventType.TASK_ASSIGNED:
        await handle_task_assigned(event)
    elif event.event_type == EventType.TASK_ASSIGNEE_INVITED:
        await handle_task_assignee_invited(event)
    elif event.event_type == EventType.TASK_UPDATED:
        await handle_task_updated(event)
    elif event.event_type == EventType.EVENT_PARTICIPANT_INVITED:
        await handle_event_participant_invited(event)
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
                    "TaskUpdated.task-service",
                    "EventParticipantInvited.event-service",
                ],
                callback=dispatch_notification,
            )
            logger.info("Consumer started")
            return

        except Exception as e:
            logger.error(f"Consumer crashed: {e}")
            await asyncio.sleep(5)
