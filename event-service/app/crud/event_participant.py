from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional
from ..models.event_participant import EventParticipant, ParticipantRole

class EventParticipantCRUD:
    async def create_participant(self, db: AsyncSession, event_id: int, user_id: int, role: ParticipantRole) ->EventParticipant:
        db_obj=EventParticipant(
            event_id=event_id,
            user_id=user_id,
            role=role
        )
        db.add(db_obj)
        # Это дополнительный блок защиты от дублирования юзера, чтобы один запрос не упал с IntegrityError
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already participant"
            )
        await db.refresh(db_obj)
        return db_obj

    async def get_participant(
            self,
            db: AsyncSession,
            event_id: int,
            user_id: int
    ) -> Optional[EventParticipant]:
        query = select(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


    async def get_participants_by_event(self, db: AsyncSession, event_id: int) -> List[EventParticipant]:
        query = select(EventParticipant).where(EventParticipant.event_id == event_id)
        result = await db.execute(query)
        return result.scalars().all()


    async def delete_participant(self, db: AsyncSession, event_id: int, user_id: int) -> bool:
        query = delete(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0


event_participant_crud = EventParticipantCRUD()