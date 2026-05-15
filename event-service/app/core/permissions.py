from fastapi import HTTPException, status
from sqlalchemy import select
from ..models.event_participant import EventParticipant, MembershipStatus
from ..schemas.event import TokenRole

ALLOWED_ROLES={"owner", "organizer"}
EVENT_CREATE_ALLOWED_ROLES={TokenRole.ADMIN, TokenRole.ORGANIZER}

def check_event_create_permissions(user_role: TokenRole):
    if user_role not in EVENT_CREATE_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin and organizer can create events"
        )

async def check_event_permissions(db, event_id: int, user_id: int):
    result = await db.execute(
        select(EventParticipant.role)
        .where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id,
            EventParticipant.membership_status == MembershipStatus.ACTIVE,
        )
    )
    role = result.scalar_one_or_none()

    if role is None or role.value not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )


def check_event_delete_permissions(event, user_id: int, token_role: TokenRole) -> None:
    if token_role == TokenRole.ADMIN:
        return
    if user_id != event.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event owner can delete this event",
        )


async def check_event_read_permissions(db, event_id: int, user_id: int):
    await check_event_preview_permissions(db, event_id, user_id)


async def check_event_preview_permissions(db, event_id: int, user_id: int):
    result = await db.execute(
        select(EventParticipant.membership_status)
        .where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id,
        )
    )
    membership_status = result.scalar_one_or_none()

    if membership_status not in (
        MembershipStatus.PENDING,
        MembershipStatus.ACTIVE,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
