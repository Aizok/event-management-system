from sqlalchemy import select, func, update, delete, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from ..models.notification import Notification, NotificationStatus
from ..schemas.notification import NotificationCreate
from datetime import datetime, timezone

class NotificationCRUD:
    async def create(self, db: AsyncSession, obj_in: NotificationCreate) -> Notification:
        db_obj=Notification(
            **obj_in.model_dump()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def get(self, db: AsyncSession, notification_id: int) -> Optional[Notification]:
        query = select(Notification).where(Notification.id == notification_id)
        result=await db.execute(query)
        return result.scalar_one_or_none()


    async def get_multi(self, db: AsyncSession, skip: int=0, limit: int=100, status: Optional[str] = None) -> List[Notification]:
        """Можно получить все, а можно с выбранным статусом"""
        query = select(Notification).offset(skip).limit(limit)
        if status:
            query=query.where(Notification.status==status)
        query=query.order_by(Notification.updated_at.desc())
        result = await db.execute(query)
        return result.scalars().all()


    async def get_by_task(self, db: AsyncSession, task_id: int) -> List[Notification]:
        query=select(Notification).where(Notification.task_id==task_id)
        result=await db.execute(query)
        return result.scalars().all()


    async def get_pending(self, db: AsyncSession) -> List[Notification]:
        result = await db.execute(
            select(Notification)
            .where(Notification.status == NotificationStatus.PENDING)
            .order_by(Notification.created_at)
            .limit(10)
        )
        return result.scalars().all()


    async def update_status(
            self,
            db: AsyncSession,
            notification_id: int,
            status: NotificationStatus,
            sent_at: Optional[datetime]=None
    ) -> Optional[Notification]:
        """Обновление статуса (pending сменить на sent/failed)"""
        db_obj=await self.get(db, notification_id)
        if not db_obj:
            return None

        update_data={"status": status}
        if sent_at:
            update_data["sent_at"]=sent_at
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def increment_retry(self, db: AsyncSession, notification_id: int) -> Optional[Notification]:
        """Для failed уведомлений нужно увеличить счётчик retry_count"""
        db_obj = await self.get(db, notification_id)
        if not db_obj:
            return None

        db_obj.retry_count +=1
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete(self, db: AsyncSession, notification_id: int) -> bool:
        query=delete(Notification).where(Notification.id==notification_id)
        result=await db.execute(query)
        await db.commit()
        return result.rowcount > 0

notification_crud=NotificationCRUD()