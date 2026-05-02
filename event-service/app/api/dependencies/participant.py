from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.security import get_current_profile_id
from ...crud.event_participant import event_participant_crud
from ...models.event_participant import EventParticipant, ParticipantRole
from ...models.event import Event
from .event import get_event_or_404

async def get_current_participant(
        event: Event=Depends(get_event_or_404),
        db: AsyncSession=Depends(get_db),
        user_id: int=Depends(get_current_profile_id)
) -> EventParticipant:
    participant=await event_participant_crud.get_participant(db, event.id, user_id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a participant of this event"
        )

    return participant


async def get_current_owner(
        current: EventParticipant = Depends(get_current_participant)
) -> EventParticipant:
    if current.role!=ParticipantRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner allowed"
        )
    return current
