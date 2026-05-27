from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession 
from typing import List
from ....core.database import get_db
from ....core.security import get_current_service, get_current_profile_id, get_current_user_data
from ....crud.task import task_crud
from ....crud.task_assignee import task_assignee_crud
from ....schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskInvitationPreview,
    TokenData,
    TaskPage,
    TaskMetricsResponse,
    TaskStatus,
    TaskPriority,
)
from ....core.events import (
    publish_task_created,
    publish_task_updated,
    publish_task_rescheduled,
)
from ....core.event_client import get_event_title
from ....core.permissions import (
    check_task_permissions,
    ALLOWED_ROLES,
    check_task_manage_permissions,
    check_task_invitation_preview_permissions,
)
from ....core.event_client import get_user_events_with_roles
from ....core.event_client import get_user_role_in_event

ALLOWED_SERVICES={"resource-service", "ai-assistant"}

router = APIRouter()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
        task_in: TaskCreate,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_profile_id),
        user_data: TokenData = Depends(get_current_user_data)
):
    if user_data.role != "admin":
        events=await get_user_events_with_roles(user_id)

        roles_map={
            e["event_id"]: e["role"]
            for e in events
        }
        role=roles_map.get(task_in.event_id)
        if role not in ALLOWED_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

    try:
        task=await task_crud.create(db=db, obj_in=task_in, owner_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    """Отправка события TaskCreated"""
    await publish_task_created(db, task.id)

    return task


@router.get("/", response_model=TaskPage)
async def read_tasks(
        skip: int = 0,
        limit: int = 25,
        event_id: int | None = Query(None),
        status: TaskStatus | None = Query(None),
        priority: TaskPriority | None = Query(None),
        q: str | None = Query(None),
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_profile_id),
        user_data: TokenData = Depends(get_current_user_data),
):
    limit = min(max(limit, 1), 100)
    skip = max(skip, 0)
    is_admin = user_data.role == "admin"
    allowed_event_ids: list[int] = []
    if not is_admin:
        events = await get_user_events_with_roles(user_id)
        allowed_event_ids = [e["event_id"] for e in events if e["role"] in ALLOWED_ROLES]

    total = await task_crud.count_accessible_tasks(
        db,
        is_admin=is_admin,
        profile_id=user_id,
        allowed_event_ids=allowed_event_ids,
        event_id=event_id,
        status=status,
        priority=priority,
        q=q,
    )
    items = await task_crud.list_accessible_tasks(
        db,
        is_admin=is_admin,
        profile_id=user_id,
        allowed_event_ids=allowed_event_ids,
        skip=skip,
        limit=limit,
        event_id=event_id,
        status=status,
        priority=priority,
        q=q,
    )
    return TaskPage(items=items, total=total)


@router.get("/metrics", response_model=TaskMetricsResponse)
async def read_tasks_metrics(
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_profile_id),
        user_data: TokenData = Depends(get_current_user_data),
):
    is_admin = user_data.role == "admin"
    allowed_event_ids: list[int] = []
    if not is_admin:
        events = await get_user_events_with_roles(user_id)
        allowed_event_ids = [e["event_id"] for e in events if e["role"] in ALLOWED_ROLES]

    total, overdue = await task_crud.metrics_accessible_tasks(
        db,
        is_admin=is_admin,
        profile_id=user_id,
        allowed_event_ids=allowed_event_ids,
    )
    return TaskMetricsResponse(total=total, overdue=overdue)


@router.get("/internal/tasks/{task_id}")
async def get_task_internal(
        task_id: int,
        db: AsyncSession = Depends(get_db),
        service: TokenData=Depends(get_current_service)
):
    if service.service_name not in ALLOWED_SERVICES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )
    task=await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return {
        "id": task.id,
        "status": task.status,
        "start_time": task.start_time,
        "end_time": task.end_time,
        "event_id": task.event_id
    }


@router.post("/internal/tasks", status_code=status.HTTP_201_CREATED)
async def create_task_internal(
        task_in: TaskCreate,
        owner_id: int,
        db: AsyncSession=Depends(get_db),
        service: TokenData=Depends(get_current_service)
):
    if service.service_name not in ALLOWED_SERVICES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    try:
        task=await task_crud.create(
            db=db,
            obj_in=task_in,
            owner_id=owner_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await publish_task_created(db, task.id)
    return task


@router.get("/{task_id}/invitation-preview", response_model=TaskInvitationPreview)
async def read_task_invitation_preview(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_profile_id),
    user_data: TokenData = Depends(get_current_user_data),
):
    task = await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if user_data.role != "admin":
        await check_task_invitation_preview_permissions(db, task_id, user_id)
    event_title = await get_event_title(task.event_id) or f"Мероприятие #{task.event_id}"
    return TaskInvitationPreview(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        start_time=task.start_time,
        end_time=task.end_time,
        deadline=task.deadline,
        event_id=task.event_id,
        event_title=event_title,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def read_task(
        task_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_profile_id),
        user_data: TokenData = Depends(get_current_user_data)
):
    task = await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if user_data.role != "admin":
        await check_task_permissions(db, task, user_id)
    return task


@router.get("/event/{event_id}", response_model=List[TaskResponse])
async def read_tasks_by_event(
        event_id: int,
        db: AsyncSession=Depends(get_db),
        user_id: int = Depends(get_current_profile_id),
        user_data: TokenData = Depends(get_current_user_data)
):
    if user_data.role == "admin":
        return await task_crud.get_by_event(db, event_id)

    events=await get_user_events_with_roles(user_id)

    roles_map = {
        e["event_id"]: e["role"]
        for e in events
    }
    role = roles_map.get(event_id)

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Для организаторов все задачи
    if role in ALLOWED_ROLES:
        return await task_crud.get_by_event(db, event_id)
    # Для исполнителей только его

    return await task_crud.get_by_event_and_assignee(db, event_id, user_id)


@router.get(
    "/event/{event_id}/participant/{participant_user_id}/assigned",
    response_model=List[TaskResponse],
)
async def read_participant_assigned_tasks(
    event_id: int,
    participant_user_id: int,
    db: AsyncSession = Depends(get_db),
    profile_id: int = Depends(get_current_profile_id),
    user_data: TokenData = Depends(get_current_user_data),
):
    if user_data.role != "admin":
        role = await get_user_role_in_event(event_id, profile_id)
        if role not in ALLOWED_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
    return await task_crud.get_by_event_for_user_as_assignee(
        db, event_id, participant_user_id
    )


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
        task_id: int,
        task_in: TaskUpdate,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_profile_id),
        user_data: TokenData = Depends(get_current_user_data)
):
    old_task=await task_crud.get(db, task_id)
    if not old_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if user_data.role != "admin":
        await check_task_permissions(db, old_task, user_id)
        role = await get_user_role_in_event(old_task.event_id, user_id)
        is_executor_assignee = role == "executor" and await task_assignee_crud.is_accepted(
            db, task_id, user_id
        )
        if is_executor_assignee:
            changed_fields = set(task_in.model_dump(exclude_unset=True).keys())
            allowed_fields = {"status"}
            if not changed_fields.issubset(allowed_fields):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Executor can only update task status"
                )
            new_status = getattr(task_in.status, "value", task_in.status)
            if new_status not in {"in_progress", "done"}:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Executor can only set task status to in_progress or done"
                )

    previous_status=old_task.status.value

    try:
        task=await task_crud.update(db=db, task_id=task_id, obj_in=task_in, user_id=user_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    """Формирование изменений"""
    changes = task_in.model_dump(exclude_unset=True)
    changes["previous_status"] = previous_status
    changes["updated_by"] = user_id

    time_changed = "start_time" in changes or "end_time" in changes

    if time_changed:
        await publish_task_rescheduled(db, task.id)

    """Отправка события TaskUpdated"""
    await publish_task_updated(db, task.id, changes)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)  
async def delete_task(
        task_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_profile_id),
        user_data: TokenData = Depends(get_current_user_data)
):
    task = await task_crud.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if user_data.role != "admin":
        await check_task_manage_permissions(task, user_id)
    success = await task_crud.delete(db, task_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
