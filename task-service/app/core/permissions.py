from fastapi import HTTPException, status
from ..core.event_client import get_user_role_in_event
from ..core.auth_client import is_admin

ALLOWED_ROLES={"owner", "organizer"}

async def check_task_permissions(task, user_id: int, roles_map=None):
    if await is_admin(user_id):
        return

    if roles_map is not None:
        role=roles_map.get(task.event_id)
    else:
        role=await get_user_role_in_event(task.event_id, user_id)

    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
