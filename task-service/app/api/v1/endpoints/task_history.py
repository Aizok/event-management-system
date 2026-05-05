from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....core.database import get_db
from ....core.security import get_current_profile_id, get_current_user_data
from ....crud.task_history import task_history_crud
from ....crud.task import task_crud
from ....schemas.task_history import TaskHistoryResponse
from ....schemas.task import TokenData, TokenRole
from ....core.permissions import check_task_permissions


router=APIRouter()


@router.get("/tasks/{task_id}/history", response_model=List[TaskHistoryResponse])
async def get_task_history(
        task_id: int,
        db: AsyncSession=Depends(get_db),
        profile_id: int=Depends(get_current_profile_id),
        user_data: TokenData=Depends(get_current_user_data),
):
    task=await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if user_data.role != TokenRole.ADMIN:
        await check_task_permissions(task, profile_id)
    history=await task_history_crud.get_by_task(db, task_id)
    return history


@router.delete("/tasks/{task_id}/history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_history(
        task_id: int,
        history_id: int,
        db: AsyncSession=Depends(get_db),
        profile_id: int=Depends(get_current_profile_id),
        user_data: TokenData=Depends(get_current_user_data),
):
    task=await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if user_data.role != TokenRole.ADMIN:
        await check_task_permissions(task, profile_id)

    history=await task_history_crud.get(db, history_id)
    if not history:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found")

    if history.task_id!=task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="History does not belong to this task")

    success=await task_history_crud.delete(db, history_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History record not found")
