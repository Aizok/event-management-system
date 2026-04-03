from fastapi import HTTPException, status
from sqlalchemy import select
from ..models.event_participant import EventParticipant
from ..core.auth_client import is_admin

ALLOWED_ROLES={"owner", "organizer"}

async def check_event_permissions(db, event_id: int, user_id: int):
    if await is_admin(user_id):
        return

    result = await db.execute(
        select(EventParticipant.role)
        .where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id
        )
    )
    role = result.scalar_one_or_none()

    if role is None or role.value not in {"owner", "organizer"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
