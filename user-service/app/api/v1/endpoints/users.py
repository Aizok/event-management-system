from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ....core.security import get_current_user_id, get_current_admin, get_current_user_data, get_current_service
from ....core.database import get_db
from ....core.config import settings
from ....crud.user import user_crud
from ....schemas.user import UserCreate, UserResponse, UserPublicResponse, UserUpdate, TokenData
from ....core.auth_client import get_user_email_from_auth

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router=APIRouter()

class ServiceTokenRequest(BaseModel):
    service_name: str
    service_secret: str


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
        user_in: UserCreate,
        db: AsyncSession=Depends(get_db),
        token_data: TokenData = Depends(get_current_user_data)
):
    email=await get_user_email_from_auth(
        auth_user_id=token_data.user_id
    )

    user = await user_crud.create(
        db=db,
        obj_in=user_in,
        owner_id=token_data.user_id,
        email=email
    )
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


@router.get("/internal/{user_id}")
async def get_user_internal(
        user_id: int,
        db: AsyncSession=Depends(get_db),
        service: TokenData = Depends(get_current_service)
):
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Service token data: {service}")

    user = await user_crud.get(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found"
        )

    return {
        "id": user.id,
        "email": user.email
    }


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
        db: AsyncSession=Depends(get_db),
        token_data: TokenData = Depends(get_current_user_data)
):
    profile=await user_crud.get(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )

    if profile.auth_user_id!=token_data.user_id and token_data.role!="admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return profile


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_profile(
        user_id: int,
        user_in: UserUpdate,
        db: AsyncSession=Depends(get_db),
        token_data: TokenData = Depends(get_current_user_data)
):
    profile=await user_crud.get(db, user_id)

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if profile.auth_user_id != token_data.user_id and token_data.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return await user_crud.update(db=db, user_id=user_id, obj_in=user_in)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_profile(
        user_id: int,
        db: AsyncSession=Depends(get_db),
        token_data: TokenData = Depends(get_current_user_data)
):
    profile = await user_crud.get(db, user_id)

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if profile.auth_user_id != token_data.user_id and token_data.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    success = await user_crud.delete(db, user_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
