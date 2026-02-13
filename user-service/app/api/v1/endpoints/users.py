from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ....core.security import get_current_user_id
from ....core.database import get_db
from ....core.config import settings
from ....crud.user import user_crud
from ....schemas.user import UserCreate, UserResponse, UserUpdate


router=APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(user_in: UserCreate, db: Session=Depends(get_db), user_id: int=Depends(get_current_user_id)):
    return user_crud.create(db=db, obj_in=user_in, owner_id=user_id)


@router.get("/", response_model=List[UserResponse])
async def read_user_profiles(
        skip: int=0,
        limit: int=100,
        db: Session=Depends(get_db),
        current_user_id: int=Depends(get_current_user_id)):
    users=user_crud.get_multi(db, skip-skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def read_user_profile(
        user_id: int,
        db: Session=Depends(get_db),
        current_user_id: int=Depends(get_current_user_id)
):
    profile=user_crud.get(db, user_id)
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
        db: Session=Depends(get_db),
        current_user_id: int = Depends(get_current_user_id)
):
    return user_crud.update(db=db, user_id=user_id, obj_in=user_in)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(
        user_id: int,
        db: Session=Depends(get_db),
        current_user_id: int=Depends(get_current_user_id)
):
    success=user_crud.delete(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )


@router.get("/me", response_model=UserResponse)
async def read_own_profile(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    profile = user_crud.get(db, current_user_id)  # Поиск своего профиля
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    return profile
