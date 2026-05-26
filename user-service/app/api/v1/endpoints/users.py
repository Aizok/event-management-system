from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Union

from ....core.security import get_current_user_id, get_current_admin, get_current_user_data, get_current_service
from ....core.database import get_db
from ....core.config import settings
from ....crud.user import user_crud
from ....schemas.user import (
    UserCreate,
    UserResponse,
    UserPublicWithRoleResponse,
    UserUpdate,
    TokenData,
    TokenRole,
    UserPage,
    UserAdminPage,
)
from ....core.auth_client import (
    get_user_email_from_auth,
    get_user_role_from_auth,
    get_auth_user_ids_by_role,
    delete_auth_user,
)

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router=APIRouter()


async def _resolve_user_list_filters(
    token_data: TokenData,
    role: str | None,
) -> tuple[list[int] | None, list[int] | None]:
    auth_user_ids: list[int] | None = None
    if role:
        auth_user_ids = await get_auth_user_ids_by_role(role)
        if not auth_user_ids:
            return [], []

    exclude_auth_user_ids: list[int] | None = None
    if token_data.role != TokenRole.ADMIN:
        admin_ids = await get_auth_user_ids_by_role("admin")
        if admin_ids:
            exclude_auth_user_ids = admin_ids
    return auth_user_ids, exclude_auth_user_ids


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


@router.get("/", response_model=UserAdminPage)
async def read_user_profiles(
        skip: int=0,
        limit: int=100,
        q: str | None = None,
        speciality: str | None = None,
        role: str | None = None,
        id: int | None = None,
        db: AsyncSession=Depends(get_db),
        admin_data: TokenData = Depends(get_current_admin),
):
    _ = admin_data
    auth_user_ids, exclude_auth_user_ids = await _resolve_user_list_filters(admin_data, role)
    if auth_user_ids == []:
        return UserAdminPage(items=[], total=0)

    total = await user_crud.count_search_public(
        db,
        q=q,
        speciality=speciality,
        profile_id=id,
        auth_user_ids=auth_user_ids,
        exclude_auth_user_ids=exclude_auth_user_ids,
    )
    users = await user_crud.search_public(
        db,
        q=q,
        speciality=speciality,
        skip=skip,
        limit=limit,
        profile_id=id,
        auth_user_ids=auth_user_ids,
        exclude_auth_user_ids=exclude_auth_user_ids,
    )
    output: list[UserResponse] = []
    for user in users:
        user_role = await get_user_role_from_auth(user.auth_user_id)
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
                role=user_role,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        )
    return UserAdminPage(items=output, total=total)


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


@router.get("/public/page", response_model=UserPage)
async def read_public_profiles_page(
        q: str | None = None,
        speciality: str | None = None,
        role: str | None = None,
        id: int | None = None,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        token_data: TokenData = Depends(get_current_user_data),
):
    auth_user_ids, exclude_auth_user_ids = await _resolve_user_list_filters(token_data, role)
    if auth_user_ids == []:
        return UserPage(items=[], total=0)

    total = await user_crud.count_search_public(
        db,
        q=q,
        speciality=speciality,
        profile_id=id,
        auth_user_ids=auth_user_ids,
        exclude_auth_user_ids=exclude_auth_user_ids,
    )
    profiles = await user_crud.search_public(
        db,
        q=q,
        speciality=speciality,
        skip=skip,
        limit=limit,
        profile_id=id,
        auth_user_ids=auth_user_ids,
        exclude_auth_user_ids=exclude_auth_user_ids,
    )
    output: list[UserPublicWithRoleResponse] = []
    for profile in profiles:
        profile_role = await get_user_role_from_auth(profile.auth_user_id)
        output.append(
            UserPublicWithRoleResponse(
                id=profile.id,
                first_name=profile.first_name,
                last_name=profile.last_name,
                speciality=profile.speciality,
                role=profile_role,
            )
        )
    return UserPage(items=output, total=total)


@router.get("/public", response_model=List[UserPublicWithRoleResponse])
async def read_public_profiles(
        q: str | None = None,
        speciality: str | None = None,
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        token_data: TokenData = Depends(get_current_user_data),
):
    page = await read_public_profiles_page(
        q=q,
        speciality=speciality,
        skip=skip,
        limit=limit,
        db=db,
        token_data=token_data,
    )
    return page.items


@router.get("/{user_id}", response_model=Union[UserResponse, UserPublicWithRoleResponse])
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

    if profile.auth_user_id!=token_data.user_id and token_data.role!=TokenRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    role = await get_user_role_from_auth(profile.auth_user_id)
    if token_data.role == TokenRole.ADMIN or profile.auth_user_id == token_data.user_id:
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

    return UserPublicWithRoleResponse(
        id=profile.id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        speciality=profile.speciality,
        role=role,
    )


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

    is_owner = profile.auth_user_id == token_data.user_id
    is_admin = token_data.role == TokenRole.ADMIN

    if not is_owner and not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    if is_owner and is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete your own account",
        )

    if is_admin:
        try:
            await delete_auth_user(profile.auth_user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to delete auth account",
            )

    success = await user_crud.delete(db, user_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
