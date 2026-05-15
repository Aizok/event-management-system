from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....core.security import get_current_profile_id, get_current_user_data
from ....core.permissions import ALLOWED_ROLES, check_task_permissions
from ....core.event_client import get_user_role_in_event, get_event_title
from ....crud.task import task_crud
from ....crud.task_assignee import task_assignee_crud
from ....schemas.task import (
    TaskAssigneeResponse,
    TaskAssigneeInvite,
    TaskAssigneeInvitationItem,
    TaskSentInvitationItem,
    TokenData,
    TokenRole,
)
from ....core.events import publish_task_assignee_invited, publish_task_assigned_accept

router = APIRouter()


async def _event_title_cached(event_id: int, cache: dict[int, str]) -> str:
    if event_id not in cache:
        title = await get_event_title(event_id)
        cache[event_id] = title or f"Мероприятие #{event_id}"
    return cache[event_id]


@router.get("/invitations/me", response_model=list[TaskAssigneeInvitationItem])
async def list_my_task_invitations(
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
):
    rows = await task_assignee_crud.list_pending_invitations_for_user(db, profile_id)
    title_cache: dict[int, str] = {}
    result = []
    for ta, task in rows:
        event_title = await _event_title_cached(task.event_id, title_cache)
        result.append(
            TaskAssigneeInvitationItem(
                task_id=ta.task_id,
                event_id=task.event_id,
                event_title=event_title,
                title=task.title,
                invited_by=ta.invited_by,
                created_at=ta.created_at,
            )
        )
    return result


@router.get("/invitations/sent/me", response_model=list[TaskSentInvitationItem])
async def list_my_sent_task_invitations(
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
):
    rows = await task_assignee_crud.list_sent_pending_invitations_for_user(db, profile_id)
    title_cache: dict[int, str] = {}
    result = []
    for ta, task in rows:
        event_title = await _event_title_cached(task.event_id, title_cache)
        result.append(
            TaskSentInvitationItem(
                task_id=ta.task_id,
                event_id=task.event_id,
                event_title=event_title,
                title=task.title,
                invitee_user_id=ta.user_id,
                created_at=ta.created_at,
            )
        )
    return result


async def _can_manage_assignees(
    task,
    profile_id: int,
    user_data: TokenData,
) -> bool:
    if user_data.role == TokenRole.ADMIN:
        return True
    if task.owner_id == profile_id:
        return True
    role = await get_user_role_in_event(task.event_id, profile_id)
    return role in ALLOWED_ROLES


@router.get("/{task_id}/assignees", response_model=list[TaskAssigneeResponse])
async def list_task_assignees(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
    user_data: TokenData = Depends(get_current_user_data),
):
    task = await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if user_data.role != TokenRole.ADMIN:
        await check_task_permissions(db, task, profile_id)
    return task.assignees


@router.post(
    "/{task_id}/assignees",
    response_model=TaskAssigneeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_task_assignee(
    task_id: int,
    body: TaskAssigneeInvite,
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
    user_data: TokenData = Depends(get_current_user_data),
):
    task = await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if not await _can_manage_assignees(task, profile_id, user_data):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    if body.user_id == profile_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot invite yourself this way",
        )
    existing = await task_assignee_crud.get_row(db, task_id, body.user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has an assignee record for this task",
        )
    row = await task_assignee_crud.invite(
        db,
        task_id=task_id,
        user_id=body.user_id,
        invited_by=profile_id,
    )
    await publish_task_assignee_invited(db, task_id, [body.user_id])
    await db.commit()
    return row


@router.post("/{task_id}/assignees/{user_id}/accept", response_model=TaskAssigneeResponse)
async def accept_task_assignee(
    task_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
    user_data: TokenData = Depends(get_current_user_data),
):
    if user_data.role != TokenRole.ADMIN and user_id != profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only accept your own invitation",
        )
    task = await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    row = await task_assignee_crud.accept(db, task_id, user_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending invitation to accept",
        )
    await publish_task_assigned_accept(db, task_id, user_id)
    await db.commit()
    return row


@router.post("/{task_id}/assignees/{user_id}/decline", response_model=TaskAssigneeResponse)
async def decline_task_assignee(
    task_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
    user_data: TokenData = Depends(get_current_user_data),
):
    if user_data.role != TokenRole.ADMIN and user_id != profile_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only decline your own invitation",
        )
    task = await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    row = await task_assignee_crud.decline(db, task_id, user_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending invitation to decline",
        )
    await db.commit()
    return row


@router.delete("/{task_id}/assignees/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_task_assignee(
    task_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
    user_data: TokenData = Depends(get_current_user_data),
):
    task = await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if not await _can_manage_assignees(task, profile_id, user_data):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    ok = await task_assignee_crud.delete_row(db, task_id, user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")
    await db.commit()
