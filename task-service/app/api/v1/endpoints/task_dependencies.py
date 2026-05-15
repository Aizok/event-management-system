from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....core.database import get_db
from ....core.security import get_current_profile_id, get_current_user_data
from ....crud.task_dependency import task_dependency_crud
from ....crud.task import task_crud
from ....schemas.task_dependency import TaskDependencyResponse, TaskDependencyListResponse
from ....schemas.task import TokenData, TokenRole
from ....core.permissions import check_task_permissions


router = APIRouter()

@router.post("/{task_id}/dependencies/{depends_on_task_id}", response_model=TaskDependencyResponse, status_code=status.HTTP_201_CREATED)
async def create_dependency(
        task_id: int,
        depends_on_task_id: int,
        db: AsyncSession=Depends(get_db),
        profile_id: int=Depends(get_current_profile_id),
        user_data: TokenData=Depends(get_current_user_data),
):
    task=await task_crud.get(db, task_id)
    depends_on=await task_crud.get(db, depends_on_task_id)

    if not task or not depends_on:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if user_data.role != TokenRole.ADMIN:
        await check_task_permissions(db, task, profile_id)
        await check_task_permissions(db, depends_on, profile_id)

    if task.event_id != depends_on.event_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tasks must belong to same event"
        )
    try:
        dependency=await task_dependency_crud.create(
            db,
            task_id,
            depends_on_task_id
        )
        return dependency

    except ValueError as e:
        if str(e)=="self_dependency":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task cannot depend on itself"
            )
        elif str(e)=="dependency_cycle":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dependency cycle detected"
            )
        elif str(e)=="duplicate_dependency":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dependency already exists"
            )
        elif str(e) == "invalid_dependency_order":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dependent task planned start must be on or after predecessor planned end",
            )


@router.get("/{task_id}/dependencies", response_model=List[TaskDependencyResponse])
async def get_dependencies(
        task_id: int,
        db: AsyncSession=Depends(get_db),
        profile_id: int=Depends(get_current_profile_id),
        user_data: TokenData=Depends(get_current_user_data),
):
    task=await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if user_data.role != TokenRole.ADMIN:
        await check_task_permissions(db, task, profile_id)

    deps=await task_dependency_crud.get_dependencies(db, task_id)
    return deps


@router.get("/{task_id}/dependency-ids", response_model=TaskDependencyListResponse)
async def get_dependency_ids(
        task_id: int,
        db: AsyncSession=Depends(get_db),
        profile_id: int=Depends(get_current_profile_id),
        user_data: TokenData=Depends(get_current_user_data),
):
    task=await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if user_data.role != TokenRole.ADMIN:
        await check_task_permissions(db, task, profile_id)

    deps=await task_dependency_crud.get_dependency_ids(db, task_id)
    return TaskDependencyListResponse(task_id=task_id, depends_on=deps)


@router.delete("/{task_id}/dependencies/{depends_on_task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(
        task_id: int,
        depends_on_task_id: int,
        db: AsyncSession = Depends(get_db),
        profile_id: int = Depends(get_current_profile_id),
        user_data: TokenData = Depends(get_current_user_data),
):
    task=await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if user_data.role != TokenRole.ADMIN:
        await check_task_permissions(db, task, profile_id)
    success=await task_dependency_crud.delete(db, task_id, depends_on_task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found"
        )
