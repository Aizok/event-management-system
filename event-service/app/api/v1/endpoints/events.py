from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ....core.database import get_db
from ....core.security import get_current_user_id, get_current_service
from ....crud.event import event_crud
from ....schemas.event import EventCreate, EventUpdate, EventResponse, TokenData

router = APIRouter()


@router.get("/internal/users/{user_id}/events")
async def get_user_events(
        user_id: int,
        db: AsyncSession = Depends(get_db),
        service: TokenData = Depends(get_current_service)
):
    events=await event_crud.get_user_events_with_roles(db, user_id)
    return {"events": events}


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event_in: EventCreate, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    event=await event_crud.create(db=db, obj_in=event_in, owner_id=user_id)
    return event

@router.get("/", response_model=List[EventResponse])
async def read_events(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    events=await event_crud.get_multi(db, skip=skip, limit=limit, owner_id=user_id)
    return events

@router.get("/{event_id}", response_model=EventResponse)
async def read_event(event_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    event = await event_crud.get(db, event_id, user_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event

@router.put("/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, event_in: EventUpdate, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    event=await event_crud.update(db=db, event_id=event_id, obj_in=event_in, owner_id=user_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    success = await event_crud.delete(db, event_id, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
