from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from tornado.process import task_id

from ....core.database import get_db
from ....core.security import get_current_user_id
from ....crud.task_dependency import task_dependency_crud
from ....crud.task import task_crud
from ....schemas.task_dependency import TaskDependencyResponse, TaskDependencyListResponse

router = APIRouter()

@router.post("/{task_id}/dependencies/{depends_on_task_id}", response_model=TaskDependencyResponse, status_code=status.HTTP_201_CREATED)
async def create_dependency(
        task_id: int,
        depends_on_task_id: int,
        db: AsyncSession=Depends(get_db),
        user_id: int=Depends(get_current_user_id)
):
    task=await task_crud.get(db, task_id, user_id)
    depends_on=await task_crud.get(db, depends_on_task_id, user_id)

    if not task or not depends_on:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
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

@router.get("/{task_id}/dependencies", response_model=List[TaskDependencyResponse])
async def get_dependencies(
        task_id: int,
        db: AsyncSession=Depends(get_db),
        user_id: int=Depends(get_current_user_id)
):
    task=await task_crud.get(db, task_id, user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    deps=await task_dependency_crud.get_dependencies(db, task_id)
    return deps


@router.get("/{task_id}/dependency-ids", response_model=TaskDependencyListResponse)
async def get_dependency_ids(
        task_id: int,
        db: AsyncSession=Depends(get_db),
        user_id: int=Depends(get_current_user_id)
):
    task=await task_crud.get(db, task_id, user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    deps=await task_dependency_crud.get_dependency_ids(db, task_id)
    return TaskDependencyListResponse(task_id=task_id, depends_on=deps)


@router.delete("/{task_id}/dependencies/{depends_on_task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dependency(
        task_id: int,
        depends_on_task_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    task=await task_crud.get(db, task_id, user_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    success=await task_dependency_crud.delete(db, task_id, depends_on_task_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found"
        )
