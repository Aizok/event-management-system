from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession 
from datetime import timedelta
from typing import List


from ....core.database import get_db
from ....core.security import (
    verify_password,
    create_access_token,
    get_current_service,
    get_current_user_id,
    get_password_hash,
)
from ....core.config import settings
from ....core.user_client import sync_user_profile_email
from ....crud.user import auth_crud
from ....schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    UserUpdate,
    TokenData,
    UserSelfUpdate,
    UserSelfUpdateResponse,
)
from ....models.user import UserRole, UserStatus
from pydantic import BaseModel

router=APIRouter()

class ServiceTokenRequest(BaseModel):
    service_name: str
    service_secret: str


@router.post("/internal/token")
async def get_service_token(req: ServiceTokenRequest):
    # Проверка секрета конкретного сервиса
    if req.service_name == "notification-service":
        if req.service_secret != settings.SERVICE_SECRET_NOTIFICATION:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service secret")
    elif req.service_name == "task-service":
        if req.service_secret != settings.SERVICE_SECRET_TASK:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service secret")
    elif req.service_name == "user-service":
        if req.service_secret != settings.SERVICE_SECRET_USER:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service secret")
    elif req.service_name == "event-service":
        if req.service_secret != settings.SERVICE_SECRET_EVENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service secret")
    elif req.service_name == "resource-service":
        if req.service_secret != settings.SERVICE_SECRET_RESOURCE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service secret")
    elif req.service_name == "ai-assistant":
        if req.service_secret != settings.SERVICE_SECRET_AI:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid service secret")
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unknown service")
    # Создание JWT для сервисов
    token=create_access_token(
        data={
            "sub": req.service_name,
            "role": "service"
        },
        expires_delta=None
        # Срок жизни токена
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600
    }


@router.get("/internal/user-ids")
async def list_user_ids_internal(
    role: str | None = None,
    db: AsyncSession = Depends(get_db),
    service: TokenData = Depends(get_current_service),
):
    _ = service
    if role:
        try:
            UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )
    ids = await auth_crud.list_user_ids(db, role=role)
    return {"ids": ids}


@router.get("/internal/users/{user_id}")
async def get_user_internal(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    service: TokenData = Depends(get_current_service)
):
    user = await auth_crud.get_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found"
        )

    return {
        "id": user.id,
        "email": user.email,
        "role": user.role
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession=Depends(get_db)):
    existing_user=await auth_crud.get_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь с email {user_in.email} уже существует"
        )
    user=await auth_crud.create(db, user_in)
    return user


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession=Depends(get_db)):
    user=await auth_crud.get_by_email(db, user_in.email)
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
    await auth_crud.update_last_login(db, user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.patch("/me", response_model=UserSelfUpdateResponse)
async def update_me(
        body: UserSelfUpdate,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(get_current_user_id),
):
    user = await auth_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль",
        )

    email_changed = False
    if body.email is not None:
        new_email = body.email.lower().strip()
        if new_email != user.email.lower():
            existing_user = await auth_crud.get_by_email(db, body.email)
            if existing_user and existing_user.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким email уже существует",
                )
            user.email = new_email
            email_changed = True

    if body.new_password:
        user.hashed_password = get_password_hash(body.new_password)

    await db.commit()
    await db.refresh(user)

    access_token = None
    expires_in = None
    if email_changed:
        await sync_user_profile_email(user.id, user.email)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value,
            },
            expires_delta=access_token_expires,
        )
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    return UserSelfUpdateResponse(
        access_token=access_token,
        expires_in=expires_in,
        message="Учётная запись обновлена",
    )


@router.get("/users", response_model=List[UserResponse])
async def get_users(skip: int=0, limit: int=100, db: AsyncSession=Depends(get_db)):
    users=await auth_crud.get_all(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession=Depends(get_db)):
    user=await auth_crud.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    return user
