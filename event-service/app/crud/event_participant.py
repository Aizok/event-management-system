from sqlalchemy import select, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List, Optional, Tuple

from ..models.event import Event
from ..models.event_participant import (
    EventParticipant,
    ParticipantRole,
    MembershipStatus,
)


class EventParticipantCRUD:
    async def create_participant(
        self,
        db: AsyncSession,
        event_id: int,
        user_id: int,
        role: ParticipantRole,
        *,
        membership_status: MembershipStatus = MembershipStatus.ACTIVE,
    ) -> EventParticipant:
        db_obj = EventParticipant(
            event_id=event_id,
            user_id=user_id,
            role=role,
            membership_status=membership_status,
        )
        db.add(db_obj)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise ValueError("duplicate_participant")
        await db.refresh(db_obj)
        return db_obj

    async def get_participant(
        self,
        db: AsyncSession,
        event_id: int,
        user_id: int,
    ) -> Optional[EventParticipant]:
        query = select(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id,
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_active_participant(
        self,
        db: AsyncSession,
        event_id: int,
        user_id: int,
    ) -> Optional[EventParticipant]:
        query = select(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id,
            EventParticipant.membership_status == MembershipStatus.ACTIVE,
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_participants_by_event(
        self, db: AsyncSession, event_id: int
    ) -> List[EventParticipant]:
        query = select(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.membership_status == MembershipStatus.ACTIVE,
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def accept_invitation(
        self, db: AsyncSession, event_id: int, user_id: int
    ) -> Optional[EventParticipant]:
        p = await self.get_participant(db, event_id, user_id)
        if not p or p.membership_status != MembershipStatus.PENDING:
            return None
        p.membership_status = MembershipStatus.ACTIVE
        await db.commit()
        await db.refresh(p)
        return p

    async def decline_invitation(
        self, db: AsyncSession, event_id: int, user_id: int
    ) -> Optional[EventParticipant]:
        p = await self.get_participant(db, event_id, user_id)
        if not p or p.membership_status != MembershipStatus.PENDING:
            return None
        p.membership_status = MembershipStatus.DECLINED
        await db.commit()
        await db.refresh(p)
        return p

    async def list_pending_invitations_for_user(
        self, db: AsyncSession, user_id: int
    ) -> List[Tuple[EventParticipant, Event]]:
        q = (
            select(EventParticipant, Event)
            .join(Event, Event.id == EventParticipant.event_id)
            .where(
                EventParticipant.user_id == user_id,
                EventParticipant.membership_status == MembershipStatus.PENDING,
            )
            .order_by(desc(Event.created_at))
        )
        r = await db.execute(q)
        return list(r.all())

    async def list_sent_pending_invitations(
        self, db: AsyncSession, manager_profile_id: int
    ) -> List[Tuple[EventParticipant, Event]]:
        managed_event_ids = select(EventParticipant.event_id).where(
            EventParticipant.user_id == manager_profile_id,
            EventParticipant.membership_status == MembershipStatus.ACTIVE,
            EventParticipant.role.in_(
                [ParticipantRole.OWNER, ParticipantRole.ORGANIZER]
            ),
        )
        q = (
            select(EventParticipant, Event)
            .join(Event, Event.id == EventParticipant.event_id)
            .where(
                EventParticipant.event_id.in_(managed_event_ids),
                EventParticipant.membership_status == MembershipStatus.PENDING,
                EventParticipant.user_id != manager_profile_id,
            )
            .order_by(desc(Event.created_at))
        )
        r = await db.execute(q)
        return list(r.all())

    async def leave_event(
        self, db: AsyncSession, event_id: int, user_id: int
    ) -> tuple[bool, str | None]:
        p = await self.get_participant(db, event_id, user_id)
        if not p:
            return False, "not_participant"
        if p.membership_status == MembershipStatus.PENDING:
            return False, "pending_use_decline"
        if p.role == ParticipantRole.OWNER:
            return False, "owner_cannot_leave"
        if p.membership_status != MembershipStatus.ACTIVE:
            return False, "not_active"
        ok = await self.delete_participant(db, event_id, user_id)
        return ok, None if ok else "not_participant"

    async def delete_participant(self, db: AsyncSession, event_id: int, user_id: int) -> bool:
        query = delete(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id,
        )
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0


event_participant_crud = EventParticipantCRUD()
