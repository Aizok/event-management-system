from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.event_client import get_user_role_in_event
from ..crud.task_assignee import task_assignee_crud
from ..models.task_assignee import TaskAssigneeStatus

ALLOWED_ROLES={"owner", "organizer"}

async def check_task_permissions(db: AsyncSession, task, user_id: int):
    role=await get_user_role_in_event(task.event_id, user_id)

    if role in ALLOWED_ROLES:
        return
    if role == "executor" and await task_assignee_crud.is_accepted(db, task.id, user_id):
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions"
    )


async def check_task_invitation_preview_permissions(
    db: AsyncSession, task_id: int, user_id: int
):
    row = await task_assignee_crud.get_row(db, task_id, user_id)
    if row is None or row.status != TaskAssigneeStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )


async def check_task_manage_permissions(task, user_id: int):
    role = await get_user_role_in_event(task.event_id, user_id)

    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
