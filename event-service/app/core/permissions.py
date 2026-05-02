from fastapi import HTTPException, status
from sqlalchemy import select
from ..models.event_participant import EventParticipant
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
            EventParticipant.user_id == user_id
        )
    )
    role = result.scalar_one_or_none()

    if role is None or role.value not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

async def check_event_read_permissions(db, event_id: int, user_id: int):
    result = await db.execute(
        select(EventParticipant.role)
        .where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id
        )
    )
    role = result.scalar_one_or_none()

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
