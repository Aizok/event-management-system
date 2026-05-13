from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ....core.security import get_current_user_id, get_current_admin, get_current_user_data, get_current_service
from ....core.database import get_db
from ....core.config import settings
from ....crud.user import user_crud
from ....schemas.user import UserCreate, UserResponse, UserPublicResponse, UserPublicWithRoleResponse, UserUpdate, TokenData
from ....core.auth_client import get_user_email_from_auth, get_user_role_from_auth

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router=APIRouter()

class ServiceTokenRequest(BaseModel):
    service_name: str
    service_secret: str


class EmailSyncRequest(BaseModel):
    email: EmailStr


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
        user_in: UserCreate,
        db: AsyncSession=Depends(get_db),
        token_data: TokenData = Depends(get_current_user_data)
):
    existing_profile = await user_crud.get_by_auth_user_id(db, token_data.user_id)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile already exists"
        )

    email=await get_user_email_from_auth(
        auth_user_id=token_data.user_id
    )

    try:
        user = await user_crud.create(
            db=db,
            obj_in=user_in,
            owner_id=token_data.user_id,
            email=email
        )
    except IntegrityError as error:
        await db.rollback()
        details = str(getattr(error, "orig", error))
        if "ix_user_profiles_email" in details:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use"
            ) from error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile data violates uniqueness constraints"
        ) from error
    return user


@router.get("/", response_model=List[UserResponse])
async def read_user_profiles(
        skip: int=0,
        limit: int=100,
        q: str | None = None,
        speciality: str | None = None,
        db: AsyncSession=Depends(get_db),
        admin_data: TokenData = Depends(get_current_admin)
        #admin_data Только для проверки роли
):
    _ = admin_data
    users = await user_crud.search_public(db, q=q, speciality=speciality, skip=skip, limit=limit)
    output: list[UserResponse] = []
    for user in users:
        role = await get_user_role_from_auth(user.auth_user_id)
        output.append(
            UserResponse(
                id=user.id,
                auth_user_id=user.auth_user_id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                speciality=user.speciality,
                bio=user.bio,
                role=role,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
    return output


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
        "email": user.email,
        "auth_user_id": user.auth_user_id
    }


@router.get("/internal/by-auth/{auth_user_id}")
async def get_user_internal_by_auth(
        auth_user_id: int,
        db: AsyncSession=Depends(get_db),
        service: TokenData = Depends(get_current_service)
):
    user = await user_crud.get_by_auth_user_id(db, auth_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with auth_user_id={auth_user_id} not found"
        )
    return {
        "id": user.id,
        "email": user.email
    }


@router.patch("/internal/by-auth/{auth_user_id}/email")
async def internal_sync_email_by_auth(
        auth_user_id: int,
        body: EmailSyncRequest,
        db: AsyncSession = Depends(get_db),
        service: TokenData = Depends(get_current_service),
):
    _ = service
    profile = await user_crud.get_by_auth_user_id(db, auth_user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )
    new_email = body.email.lower().strip()
    other = await user_crud.get_by_email(db, new_email)
    if other and other.id != profile.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use in user profiles",
        )
    profile.email = new_email
    await db.commit()
    await db.refresh(profile)
    return {"ok": True, "email": profile.email}


@router.get("/me", response_model=UserResponse)
async def read_own_profile(
    db: AsyncSession = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    profile = await user_crud.get_by_auth_user_id(db, current_user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    role = await get_user_role_from_auth(profile.auth_user_id)
    return UserResponse(
        id=profile.id,
        auth_user_id=profile.auth_user_id,
        email=profile.email,
        first_name=profile.first_name,
        last_name=profile.last_name,
        phone=profile.phone,
        speciality=profile.speciality,
        bio=profile.bio,
        role=role,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/public/by-ids", response_model=List[UserPublicWithRoleResponse])
async def read_public_profiles_by_ids(
        ids: List[int] = Query(default=[]),
        db: AsyncSession = Depends(get_db),
        token_data: TokenData = Depends(get_current_user_data)
):
    _ = token_data
    unique_ids = list(dict.fromkeys(ids))
    if not unique_ids:
        return []
    profiles = await user_crud.get_by_ids(db, unique_ids)
    output: list[UserPublicWithRoleResponse] = []
    for profile in profiles:
        role = await get_user_role_from_auth(profile.auth_user_id)
        output.append(
            UserPublicWithRoleResponse(
                id=profile.id,
                first_name=profile.first_name,
                last_name=profile.last_name,
                speciality=profile.speciality,
                role=role
            )
        )
    return output


@router.get("/public", response_model=List[UserPublicWithRoleResponse])
async def read_public_profiles(
        q: str | None = None,
        speciality: str | None = None,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        token_data: TokenData = Depends(get_current_user_data)
):
    profiles = await user_crud.search_public(db, q=q, speciality=speciality, skip=skip, limit=limit)
    output: list[UserPublicWithRoleResponse] = []
    for profile in profiles:
        role = await get_user_role_from_auth(profile.auth_user_id)
        if token_data.role != "admin" and role == "admin":
            continue
        output.append(
            UserPublicWithRoleResponse(
                id=profile.id,
                first_name=profile.first_name,
                last_name=profile.last_name,
                speciality=profile.speciality,
                role=role
            )
        )
    return output


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
