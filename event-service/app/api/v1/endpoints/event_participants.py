from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....core.database import get_db
from ....core.security import get_current_user_id
from ....crud.event_participant import event_participant_crud
from ....crud.event import event_crud
from ....schemas.event_participant import EventParticipantCreate, EventParticipantResponse
from ....models.event_participant import ParticipantRole
from ....models.event import Event
from ....api.dependencies.event import get_event_or_404
from ....api.dependencies.participant import get_current_participant

router = APIRouter()

@router.post("/{event_id}/participants", response_model=EventParticipantResponse)
async def create_participant(
        participant_in: EventParticipantCreate,
        db: AsyncSession=Depends(get_db),
        current=Depends(get_current_participant)
):
    if current.role != ParticipantRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can add participants")


    # Нельзя добавить второго owner
    if participant_in.role == ParticipantRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign OWNER role"
        )

    # Запрет дублирования (нельзя одного и того же добавить как участника несколько раз)
    existing = await event_participant_crud.get_participant(
        db, current.event_id, participant_in.user_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already participant"
        )

    return await event_participant_crud.create_participant(
        db,
        event_id=current.event_id,
        user_id=participant_in.user_id,
        role=participant_in.role
    )


@router.get("/{event_id}/participants/{participant_user_id}", response_model=EventParticipantResponse)
async def get_participant(
        participant_user_id: int,
        db: AsyncSession = Depends(get_db),
        current=Depends(get_current_participant)
):
    participant = await event_participant_crud.get_participant(db, current.event_id, participant_user_id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found"
        )

    return participant


@router.get("/{event_id}/participants", response_model=List[EventParticipantResponse])
async def get_participants(
        db: AsyncSession=Depends(get_db),
        current=Depends(get_current_participant)
):
    return await event_participant_crud.get_participants_by_event(db, current.event_id)


@router.delete("/{event_id}/participants/{participant_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_participant(
        participant_user_id: int,
        db: AsyncSession = Depends(get_db),
        current=Depends(get_current_participant)
):
    if current.role != ParticipantRole.OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can remove participants")

    if participant_user_id == current.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot remove themselves"
        )

    success = await event_participant_crud.delete_participant(
        db,
        current.event_id,
        participant_user_id
    )

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
