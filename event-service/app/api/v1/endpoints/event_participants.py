from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....core.database import get_db
from ....core.security import (
    get_current_user_id,
    get_current_service,
    get_current_user_data,
    get_current_profile_id,
)
from ....crud.event_participant import event_participant_crud
from ....crud.event import event_crud
from ....schemas.event_participant import (
    EventParticipantCreate,
    EventParticipantResponse,
    EventParticipantInvitationItem,
    EventSentInvitationItem,
)
from ....schemas.event import TokenData
from ....models.event_participant import ParticipantRole, EventParticipant, MembershipStatus
from ....api.dependencies.participant import get_current_participant, get_current_owner
from ....core.user_client import get_user_profile_id
from ....core.user_client import get_auth_user_id_by_profile_id
from ....core.auth_client import get_user_role
from ....core.events import publish_event_participant_invited

ALLOWED_SERVICES={"task-service", "resource-service"}


router = APIRouter()


@router.get("/invitations/me", response_model=List[EventParticipantInvitationItem])
async def list_my_event_invitations(
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
):
    rows = await event_participant_crud.list_pending_invitations_for_user(db, profile_id)
    return [
        EventParticipantInvitationItem(
            event_id=ep.event_id,
            title=ev.title,
            role=ep.role,
            start_time=ev.start_time,
            end_time=ev.end_time,
            location=ev.location,
            description=ev.description,
        )
        for ep, ev in rows
    ]


@router.get("/invitations/sent/me", response_model=List[EventSentInvitationItem])
async def list_my_sent_event_invitations(
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
):
    rows = await event_participant_crud.list_sent_pending_invitations(db, profile_id)
    return [
        EventSentInvitationItem(
            event_id=ep.event_id,
            event_title=ev.title,
            invitee_user_id=ep.user_id,
            role=ep.role,
        )
        for ep, ev in rows
    ]


@router.get("/{event_id}/participants/me", response_model=EventParticipantResponse)
async def get_my_participant(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
):
    event = await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    participant = await event_participant_crud.get_participant(db, event_id, profile_id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )
    return participant


@router.post("/{event_id}/participants/me/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_event_as_participant(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
):
    event = await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    ok, reason = await event_participant_crud.leave_event(db, event_id, profile_id)
    if ok:
        return None
    if reason == "pending_use_decline":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use decline to reject a pending invitation",
        )
    if reason == "owner_cannot_leave":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot leave the event",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Participant not found",
    )


@router.post(
    "/{event_id}/participants/me/accept",
    response_model=EventParticipantResponse,
)
async def accept_my_event_invitation(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
):
    event = await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    row = await event_participant_crud.accept_invitation(db, event_id, profile_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending invitation to accept",
        )
    return row


@router.post(
    "/{event_id}/participants/me/decline",
    response_model=EventParticipantResponse,
)
async def decline_my_event_invitation(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
):
    event = await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    row = await event_participant_crud.decline_invitation(db, event_id, profile_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending invitation to decline",
        )
    return row


@router.get("/internal/{event_id}/participants/{participant_user_id}")
async def internal_get_participant(
        event_id: int,
        participant_user_id: int,
        db: AsyncSession = Depends(get_db),
        service: TokenData = Depends(get_current_service)
):
    if service.service_name not in ALLOWED_SERVICES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    event=await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    participant = await event_participant_crud.get_active_participant(
        db, event_id, participant_user_id
    )
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant not found",
        )

    return {"role": participant.role}


@router.post("/{event_id}/participants", response_model=EventParticipantResponse)
async def create_participant(
        event_id: int,
        participant_in: EventParticipantCreate,
        db: AsyncSession=Depends(get_db),
        auth_user_id: int = Depends(get_current_user_id),
        token_data: TokenData = Depends(get_current_user_data)
):
    event = await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    current_profile_id = await get_user_profile_id(auth_user_id)
    if token_data.role != "admin":
        current_participant = await event_participant_crud.get_active_participant(
            db, event_id, current_profile_id
        )
        if not current_participant or current_participant.role not in {
            ParticipantRole.OWNER,
            ParticipantRole.ORGANIZER,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

    # Нельзя добавить второго owner
    if participant_in.role == ParticipantRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign OWNER role",
        )

    existing = await event_participant_crud.get_participant(
        db, event_id, participant_in.user_id
    )
    if existing:
        if existing.membership_status == MembershipStatus.DECLINED:
            existing.role = participant_in.role
            existing.membership_status = MembershipStatus.PENDING
            await db.commit()
            await db.refresh(existing)
            await publish_event_participant_invited(
                db,
                event_id=event_id,
                invitee_id=participant_in.user_id,
                inviter_id=current_profile_id,
                role=participant_in.role.value,
            )
            return existing
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already participant",
        )

    target_auth_user_id = await get_auth_user_id_by_profile_id(participant_in.user_id)
    auth_role = await get_user_role(target_auth_user_id)

    if auth_role == "viewer" and participant_in.role != ParticipantRole.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="System viewer can only be added with event role viewer",
        )

    if participant_in.role == ParticipantRole.ORGANIZER:
        if auth_role == "executor":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System executor cannot be assigned as event organizer"
            )

    try:
        participant = await event_participant_crud.create_participant(
            db,
            event_id=event_id,
            user_id=participant_in.user_id,
            role=participant_in.role,
            membership_status=MembershipStatus.PENDING,
        )
        await publish_event_participant_invited(
            db,
            event_id=event_id,
            invitee_id=participant_in.user_id,
            inviter_id=current_profile_id,
            role=participant_in.role.value,
        )
        return participant
    except ValueError as e:
        if str(e) == "duplicate_participant":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Duplicate participant")
        raise


@router.get("/{event_id}/participants/{participant_user_id}", response_model=EventParticipantResponse)
async def get_participant(
        participant_user_id: int,
        db: AsyncSession = Depends(get_db),
        current:EventParticipant=Depends(get_current_participant)
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
        event_id: int,
        db: AsyncSession = Depends(get_db),
        auth_user_id: int = Depends(get_current_user_id),
        token_data: TokenData = Depends(get_current_user_data),
):
    event = await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    if token_data.role != "admin":
        current_profile_id = await get_user_profile_id(auth_user_id)
        current_participant = await event_participant_crud.get_active_participant(
            db, event_id, current_profile_id
        )
        if not current_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a participant of this event"
            )
    return await event_participant_crud.get_participants_by_event(db, event_id)


@router.delete(
    "/{event_id}/invitations/{invitee_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_event_invitation(
    event_id: int,
    invitee_user_id: int,
    db: AsyncSession = Depends(get_db),
    auth_user_id: int = Depends(get_current_user_id),
    token_data: TokenData = Depends(get_current_user_data),
):
    event = await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    current_profile_id = await get_user_profile_id(auth_user_id)
    if token_data.role != "admin":
        current_participant = await event_participant_crud.get_active_participant(
            db, event_id, current_profile_id
        )
        if not current_participant or current_participant.role not in {
            ParticipantRole.OWNER,
            ParticipantRole.ORGANIZER,
        }:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

    success = await event_participant_crud.cancel_pending_invitation(
        db, event_id, invitee_user_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pending invitation not found",
        )


@router.delete("/{event_id}/participants/{participant_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_participant(
        participant_user_id: int,
        db: AsyncSession = Depends(get_db),
        current:EventParticipant=Depends(get_current_owner)
):
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
