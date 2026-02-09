from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ....core.database import get_db
from ....core.security import get_current_user_id
from ....crud.event import event_crud
from ....schemas.event import EventCreate, EventUpdate, EventResponse

router = APIRouter()

@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(event_in: EventCreate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return event_crud.create(db=db, obj_in=event_in, owner_id=user_id)

@router.get("/", response_model=List[EventResponse])
def read_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return event_crud.get_multi(db, skip=skip, limit=limit, owner_id=user_id)

@router.get("/{event_id}", response_model=EventResponse)
def read_event(event_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    event = event_crud.get(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event

@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_in: EventUpdate, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return event_crud.update(db=db, event_id=event_id, obj_in=event_in, owner_id=user_id)

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)  # ✅ Для DELETE
def delete_event(event_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    success = event_crud.delete(db, event_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
