from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..models.event import Event
from ..models.event_participant import EventParticipant
from ..schemas.event import EventCreate, EventUpdate
from .event_participant import event_participant_crud, ParticipantRole

class EventCRUD:
    async def create(self, db: AsyncSession, obj_in: EventCreate, owner_id: int) -> Event:
        if obj_in.end_time < obj_in.start_time:
            raise ValueError("end_time must be >= start_time")
        db_obj=Event(
            **obj_in.model_dump(),
            owner_id=owner_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        await event_participant_crud.create_participant(
            db,
            event_id=db_obj.id,
            user_id=owner_id,
            role=ParticipantRole.OWNER)
        return db_obj


    async def get(self, db: AsyncSession, event_id: int) -> Optional[Event]:
        query = select(Event).where(Event.id == event_id)
        result=await db.execute(query)
        return result.scalar_one_or_none()


    async def get_by_event_ids(self, db: AsyncSession, event_ids, skip: int=0, limit:int=100):
        query = (
            select(Event)
            .where(Event.id.in_(event_ids))
            .order_by(Event.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()


    async def get_by_user(self, db: AsyncSession, user_id: int) -> List[Event]:
        query=(
            select(Event)
            .join(EventParticipant, Event.id==EventParticipant.event_id)
            .where(EventParticipant.user_id==user_id)
            .order_by(Event.created_at.desc())
        )
        result=await db.execute(query)
        return result.scalars().all()


    async def get_user_events_with_roles(self, db: AsyncSession, user_id: int):
        query = (
            select(Event.id, EventParticipant.role)
            .join(EventParticipant, Event.id == EventParticipant.event_id)
            .where(EventParticipant.user_id == user_id)
            .order_by(Event.created_at.desc())
        )
        result = await db.execute(query)
        return [
            {
                "event_id": row[0],
                "role": row[1].value
            }
            for row in result.all()
        ]


    async def get_multi(self, db: AsyncSession, skip: int=0, limit: int=100) -> List[Event]:
        query=select(Event)
        query=query.order_by(Event.created_at.desc()).offset(skip).limit(limit)
        result=await db.execute(query)
        return result.scalars().all()


    async def update(self, db: AsyncSession, event_id: int, obj_in: EventUpdate) -> Optional[Event]:
        db_obj=await self.get(db, event_id)
        if not db_obj:
            return None

        update_data=obj_in.model_dump(exclude_unset=True)
        new_start = update_data.get("start_time", db_obj.start_time)
        new_end = update_data.get("end_time", db_obj.end_time)
        if new_end < new_start:
            raise ValueError("end_time must be >= start_time")
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete(self, db: AsyncSession, event_id: int, owner_id: Optional[int]=None) -> bool:
        query=delete(Event).where(Event.id==event_id)
        if owner_id is not None:
            query=query.where(Event.owner_id==owner_id)
        result=await db.execute(query)
        await db.commit()
        return result.rowcount > 0

event_crud=EventCRUD()