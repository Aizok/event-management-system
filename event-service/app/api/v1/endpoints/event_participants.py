from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....core.database import get_db
from ....core.security import get_current_user_id
from ....crud.event_participant import event_participant_crud
from ....schemas.event_participant import EventParticipantCreate, EventParticipantResponse
from ....models.event_participant import ParticipantRole

router = APIRouter()

@router.post("/{event_id}/participants", response_model=EventParticipantResponse)
async def create_participant(
        event_id: int,
        participant_in: EventParticipantCreate,
        db: AsyncSession=Depends(get_db),
        user_id: int=Depends(get_current_user_id)
):
    current=await event_participant_crud.get_participant(db, event_id, user_id)
    if not current or current.role != ParticipantRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can add participants")

    return await event_participant_crud.create_participant(
        db,
        event_id=event_id,
        user_id=participant_in.user_id,
        role=participant_in.role
    )

@router.get("/{event_id}/participants", response_model=List[EventParticipantResponse])
async def get_participants(
        event_id: int,
        db: AsyncSession=Depends(get_db),
        user_id: int=Depends(get_current_user_id)
):
    current=await event_participant_crud.get_participant(db, event_id, user_id)

    if not current:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return await event_participant_crud.get_participants_by_event(db, event_id)


@router.delete("/{event_id}/participants/{participant_user_id}")
async def delete_participant(
        event_id: int,
        participant_user_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    current=await event_participant_crud.get_participant(db, event_id, user_id)
    if not current or current.role != ParticipantRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can remove participants")

    success = await event_participant_crud.delete_participant(
        db,
        event_id,
        participant_user_id
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")