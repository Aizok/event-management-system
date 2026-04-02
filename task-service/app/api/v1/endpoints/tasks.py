from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession 
from typing import List

from ....core.database import get_db
from ....core.security import get_current_user_id
from ....crud.task import task_crud
from ....schemas.task import TaskCreate, TaskUpdate, TaskResponse
from ....core.events import publish_task_created, publish_task_updated
from ....core.permissions import check_task_permissions, ALLOWED_ROLES
from ....core.event_client import get_user_role_in_event
from ....core.auth_client import is_admin
from ....core.event_client import get_user_events_with_roles

router = APIRouter()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
        task_in: TaskCreate,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    task=await task_crud.create(db=db, obj_in=task_in, owner_id=user_id)

    """Отправка события TaskCreated"""
    await publish_task_created(db, task.id)

    return task


@router.get("/", response_model=List[TaskResponse])
async def read_tasks(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    if await is_admin(user_id):
        return await task_crud.get_multi(db, skip, limit)

    events=await get_user_events_with_roles(user_id)
    allowed_event_ids = [
        e["event_id"]
        for e in events
        if e["role"] in ALLOWED_ROLES
    ]

    return await task_crud.get_by_event_ids(
        db,
        allowed_event_ids,
        skip,
        limit
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def read_task(
        task_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    task = await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    await check_task_permissions(task, user_id)
    return task


@router.get("/event/{event_id}", response_model=List[TaskResponse])
async def read_tasks_by_event(
        event_id: int,
        db: AsyncSession=Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    tasks=await task_crud.get_by_event(db, event_id)
    for task in tasks:
        await check_task_permissions(task, user_id)
    return tasks


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
        task_id: int,
        task_in: TaskUpdate,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    old_task=await task_crud.get(db, task_id)
    if not old_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await check_task_permissions(old_task, user_id)

    previous_status=old_task.status

    task=await task_crud.update(db=db, task_id=task_id, obj_in=task_in)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    """Формирование изменений"""
    changes=task_in.model_dump(exclude_unset=True)
    changes['previous_status']=previous_status

    """Отправка события TaskUpdated"""
    await publish_task_updated(db, task.id, changes)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)  
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    task = await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await check_task_permissions(task, user_id)
    success = await task_crud.delete(db, task_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
