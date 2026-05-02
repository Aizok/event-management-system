from fastapi import HTTPException, status
from ..core.event_client import get_user_role_in_event, event_exists

ALLOWED_ROLES={"owner", "organizer"}

async def check_resource_permissions(event_id: int, user_id: int):
    exists=await event_exists(event_id)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    role = await get_user_role_in_event(event_id, user_id)

    if role is None or role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
