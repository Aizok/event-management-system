from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..models.event import Event
from ..schemas.event import EventCreate, EventUpdate
from .event_participant import event_participant_crud, ParticipantRole

class EventCRUD:
    async def create(self, db: AsyncSession, obj_in: EventCreate, owner_id: int) -> Event:
        db_obj=Event(
            **obj_in.model_dump(),
            owner_id=owner_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        await event_participant_crud.add_participant(
            db,
            event_id=db_obj.id,
            user_id=owner_id,
            role=ParticipantRole.OWNER)
        return db_obj


    async def get(self, db: AsyncSession, event_id: int, owner_id: Optional[int]=None) -> Optional[Event]:
        query = select(Event).where(Event.id == event_id)
        if owner_id:
            query=query.where(Event.owner_id==owner_id)
        result=await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int=0, limit: int=100, owner_id: Optional[int] = None) -> List[Event]:
        query=select(Event).offset(skip).limit(limit).order_by(Event.created_at.desc())
        if owner_id:
            query=query.where(Event.owner_id == owner_id)
        result=await db.execute(query)
        return result.scalars().all()


    async def update(self, db: AsyncSession, event_id: int, obj_in: EventUpdate, owner_id: int) -> Optional[Event]:
        db_obj=await self.get(db, event_id, owner_id)
        if not db_obj:
            return None

        update_data=obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete(self, db: AsyncSession, event_id: int, owner_id: Optional[int]=None) -> bool:
        query=delete(Event).where(Event.id==event_id)
        if owner_id:
            query=query.where(Event.owner_id==owner_id)
        result=await db.execute(query)
        await db.commit()
        return result.rowcount > 0

event_crud=EventCRUD()