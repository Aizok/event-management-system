from fastapi import HTTPException, status
from sqlalchemy import select
from ..core.auth_client import is_admin
from ..core.event_client import get_user_role_in_event

ALLOWED_ROLES={"owner", "organizer"}

async def check_resource_permissions(event_id: int, user_id: int):
    if await is_admin(user_id):
        return

    role = await get_user_role_in_event(event_id, user_id)

    if role is None or role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
