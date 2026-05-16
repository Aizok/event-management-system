from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ....core.database import get_db
from ....core.config import settings
from ....crud.notification import notification_crud
from ....schemas.notification import NotificationCreate, NotificationResponse, NotificationStatus

from ....core.user_client import get_user_email

from datetime import datetime, timezone
import logging
logger = logging.getLogger(__name__)


router=APIRouter()


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
        notification_in: NotificationCreate,
        db: AsyncSession=Depends(get_db)
):
    notification=await notification_crud.create(db=db, obj_in=notification_in)
    return notification


@router.get("/", response_model=List[NotificationResponse])
async def read_notifications(
        skip: int=0,
        limit: int=100,
        db: AsyncSession = Depends(get_db),
        notification_status: NotificationStatus | None = None
):
    notifications=await notification_crud.get_multi(db=db, skip=skip, limit=limit, status=notification_status)
    return notifications


@router.get("/pending", response_model=List[NotificationResponse])
async def read_pending_notifications(
    db: AsyncSession = Depends(get_db)
):
    """Уведомление для отправки (PENDING статус)"""
    notifications = await notification_crud.get_pending(db)
    return notifications


@router.get("/{notification_id}", response_model=NotificationResponse)
async def read_notification(
        notification_id: int,
        db: AsyncSession=Depends(get_db)
):
    notification=await notification_crud.get(db, notification_id)
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    return notification


@router.get("/task/{task_id}", response_model=List[NotificationResponse])
async def read_notifications_by_task(
        task_id: int,
        db: AsyncSession=Depends(get_db)
):
    """Уведомление по task_id (из события TaskCreated)"""
    notifications=await notification_crud.get_by_task(db=db, task_id=task_id)
    return notifications


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
        notification_id: int,
        db: AsyncSession=Depends(get_db)
):
    success=await notification_crud.delete(db=db, notification_id=notification_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
