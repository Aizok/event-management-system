from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....core.database import get_db
from ....core.security import get_current_user_id
from ....crud.task_history import task_history_crud
from ....crud.task import task_crud
from ....schemas.task_history import TaskHistoryResponse
from ....core.permissions import check_task_permissions, ALLOWED_ROLES
from ....core.auth_client import is_admin
from ....core.event_client import get_user_events_with_roles
from ....core.event_client import get_user_role_in_event


router=APIRouter()


@router.get("/tasks/{task_id}/history", response_model=List[TaskHistoryResponse])
async def get_task_history(
        task_id: int,
        db: AsyncSession=Depends(get_db),
        user_id: int=Depends(get_current_user_id)
):
    task=await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await check_task_permissions(task, user_id)
    history=await task_history_crud.get_by_task(db, task_id)
    return history


@router.delete("/tasks/{task_id}/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history(
        task_id: int,
        history_id: int,
        db: AsyncSession=Depends(get_db),
        user_id: int=Depends(get_current_user_id)
):
    task=await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await check_task_permissions(task, user_id)

    history=await task_history_crud.get(db, history_id)
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found")

    if history.task_id!=task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="History does not belong to this task")

    success=await task_history_crud.delete(db, history_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found")
