from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ....core.security import get_current_user_id, get_current_admin
from ....core.database import get_db
from ....core.config import settings
from ....crud.notification import notification_crud
from ....schemas.notification import NotificationCreate, NotificationResponse


router=APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
        user_in: UserCreate,
        db: AsyncSession=Depends(get_db),
        user_id: int=Depends(get_current_user_id)
):
    user=await user_crud.create(db=db, obj_in=user_in, owner_id=user_id)
    return user


@router.get("/", response_model=List[UserResponse])
async def read_user_profiles(
        skip: int=0,
        limit: int=100,
        db: AsyncSession=Depends(get_db),
        admin_data: TokenData = Depends(get_current_admin)
        #admin_data Только для проверки роли
):
    users=await user_crud.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/me", response_model=UserResponse)
async def read_own_profile(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    profile = await user_crud.get(db, current_user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return profile


@router.get("/{user_id}", response_model=UserPublicResponse)
async def read_user_profile(
        user_id: int,
        db: AsyncSession=Depends(get_db)
):
    profile=await user_crud.get(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return profile


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_profile(
        user_id: int,
        user_in: UserUpdate,
        db: AsyncSession=Depends(get_db),
        current_user_id: int = Depends(get_current_user_id)
):
    user=await user_crud.update(db=db, user_id=user_id, obj_in=user_in, owner_id=current_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(
        user_id: int,
        db: AsyncSession=Depends(get_db),
        current_user_id: int=Depends(get_current_user_id)
):
    success=await user_crud.delete(db, user_id, current_user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
