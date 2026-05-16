"""Event producer for Event Service"""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from shared.events.producer import EventProducer
from shared.events.schemas.events import EventParticipantInvited
from ..crud.event import event_crud

logger = logging.getLogger(__name__)

producer = EventProducer()


async def publish_event_participant_invited(
    db: AsyncSession,
    *,
    event_id: int,
    invitee_id: int,
    inviter_id: int,
    role: str,
) -> None:
    event = await event_crud.get(db, event_id)
    if not event:
        return

    payload = EventParticipantInvited(
        source_service="event-service",
        source_entity_id=event_id,
        data={
            "invitee_id": invitee_id,
            "inviter_id": inviter_id,
            "title": event.title,
            "start_time": event.start_time.isoformat(),
            "end_time": event.end_time.isoformat(),
            "location": event.location,
            "role": role,
        },
    )
    await producer.publish(payload)
    logger.info(
        f"EventParticipantInvited(event_id={event_id}): invitee={invitee_id}"
    )
