from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ....core.database import get_db
from ....core.security import get_current_user_id, get_current_service
from ....crud.event import event_crud
from ....crud.event_participant import event_participant_crud
from ....schemas.event import EventCreate, EventUpdate, EventResponse, TokenData
from ....core.permissions import check_event_permissions, ALLOWED_ROLES
from ....core.auth_client import is_admin

ALLOWED_SERVICES={"task-service", "resource-service"}

router = APIRouter()


@router.get("/internal/users/{user_id}/events")
async def get_user_events(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        service: TokenData = Depends(get_current_service)
):
    if service.service_name not in ALLOWED_SERVICES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    events=await event_crud.get_user_events_with_roles(db, user_id)
    return {"events": events}


@router.get("/internal/events/{event_id}")
async def internal_get_event(
        event_id: int,
        db: AsyncSession = Depends(get_db),
        service: TokenData = Depends(get_current_service)
):
    if service.service_name not in ALLOWED_SERVICES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    event = await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    return {"id": event.id}


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event_in: EventCreate, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    event=await event_crud.create(db=db, obj_in=event_in, owner_id=user_id)
    return event



@router.get("/", response_model=List[EventResponse])
async def read_events(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if await is_admin(user_id):
        return await event_crud.get_multi(db, skip=skip, limit=limit)
    events = await event_crud.get_user_events_with_roles(db, user_id)

    allowed_event_ids = [
        e["event_id"]
        for e in events
        if e["role"] in ALLOWED_ROLES
    ]
    if not allowed_event_ids:
        return []
    return await event_crud.get_by_event_ids(db, allowed_event_ids, skip, limit)


@router.get("/{event_id}", response_model=EventResponse)
async def read_event(event_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    event = await event_crud.get(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    await check_event_permissions(db, event.id, user_id)
    return event


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, event_in: EventUpdate, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    event=await event_crud.get(db=db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    await check_event_permissions(db, event.id, user_id)
    return await event_crud.update(db, event_id, event_in)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    event=await event_crud.get(db=db, event_id=event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    await check_event_permissions(db, event.id, user_id)
    success = await event_crud.delete(db, event_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
