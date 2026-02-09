from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ....core.database import get_db
from ....core.security import get_current_user_id
from ....crud.event import event_crud
from ....schemas.event import EventCreate, EventResponse

router=APIRouter()

@router.post("/", response_model=EventResponse)
def create_event(
    event_in: EventCreate,
    db: Session=Depends(get_db),
    user_id: int=Depends(get_current_user_id)
):
    return event_crud.create(db=db, obj_in=event_in, owner_id=user_id)


@router.get("/", response_model=List[EventResponse])
def read_events(
    skip: int=0,
    limit: int=100,
    db: Session = Depends(get_db),
    user_id: int=Depends(get_current_user_id)
):
    """Список своих мероприятий"""
    return event_crud.get_multi(db=db, skip=skip, limit=limit, owner_id=user_id)
