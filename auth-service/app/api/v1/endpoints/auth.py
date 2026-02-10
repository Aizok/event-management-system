from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from ....core.database import get_db
from ....core.security import verify_password, create_access_token
from ....core.config import settings
from ....crud.user import user_crud
from ....schemas.user import UserCreate, UserResponse, UserLogin, Token, UserUpdate
from ....models.user import UserRole, UserStatus


router=APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: Session=Depends(get_db)):
    existing_user=user_crud.get_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь с email {user_in.email} уже существует"
        )
    user=user_crud.create(db, user_in)
    return user


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: Session=Depends(get_db)):
    user=user_crud.get_by_email(db, user_in.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    # Проверка пароля
    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )

    # Проверка статуса
    if user.status!=UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Аккаунт {user.status.value}. Обратитесь к администратору"
        )


    access_token_expires=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token=create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )

    # Обновить last_login
    user_crud.update_last_login(db, user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.get("/users", response_model=List[UserResponse])
async def get_users(skip: int=0, limit: int=100, db: Session=Depends(get_db)):
    users=user_crud.get_all(db, skip-skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session=Depends(get_db)):
    user=user_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    return user
