from sqlalchemy.orm import Session
from sqlalchemy import select, func, update, delete
from typing import List, Optional
from ..models.event import Event
from ..schemas.event import EventCreate, EventUpdate

class EventCRUD:
    async def get(self, db: Session, event_id: int, owner_id: Optional[int]=None) -> Optional[Event]:
        query=select(Event).where(Event.id ==event_id)
        if owner_id:
            query=query.where(Event.owner_id==owner_id)
        result=db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(self, db: Session, skip: int=0, limit: int=100, owner_id: int = None) -> List[Event]:
        query=db.query(Event)
        if owner_id:
            query=query.filter(Event.owner_id == owner_id)
        return query.offset(skip).limit(limit).all()

    async def create(self, db: Session, obj_in: EventCreate, owner_id: int) -> Event:
        db_obj=Event(
            **obj_in.model_dump(),
            owner_id=owner_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    async def update(self, db: Session, event_id: int, obj_in: EventUpdate, owner_id: int) -> Event:
        db_obj=await self.get(db, event_id)
        if not db_obj:
            raise ValueError("Event not found")
        if db_obj.owner_id != owner_id:
            raise PermissionError("Not enough permissions")

        update_data=obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete(self, db: Session, event_id: int, owner_id: Optional[int]=None) -> bool:
        obj=self.get(db, event_id)
        if obj and obj.owner_id == owner_id:
            db.delete(obj)
            db.commit()
            return True
        return False

event_crud=EventCRUD()