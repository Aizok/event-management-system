from sqlalchemy import select, func, delete, not_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from ..models.user import UserProfile
from ..schemas.user import UserCreate, UserUpdate


class UserCRUD:
    async def create(self, db: AsyncSession, obj_in: UserCreate, owner_id: int, email: str) -> UserProfile:
        existing = await self.get_by_auth_user_id(db, owner_id)
        if existing:
            return existing
        db_obj = UserProfile(
            **obj_in.dict(),
            auth_user_id=owner_id,
            email=email
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, user_id: int) -> Optional[UserProfile]:
        query=select(UserProfile).where(UserProfile.id == user_id)
        result=await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_auth_user_id(self, db: AsyncSession, auth_user_id: int) -> Optional[UserProfile]:
        query=select(UserProfile).where(UserProfile.auth_user_id == auth_user_id)
        result=await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[UserProfile]:
        query = select(UserProfile).where(func.lower(UserProfile.email) == func.lower(email.strip()))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserProfile]:
        query=select(UserProfile).offset(skip).limit(limit).order_by(UserProfile.created_at.desc())
        result=await db.execute(query)
        return result.scalars().all()

    async def get_by_ids(self, db: AsyncSession, user_ids: List[int]) -> List[UserProfile]:
        if not user_ids:
            return []
        query = select(UserProfile).where(UserProfile.id.in_(user_ids))
        result = await db.execute(query)
        profiles = result.scalars().all()
        profiles_map = {profile.id: profile for profile in profiles}
        return [profiles_map[user_id] for user_id in user_ids if user_id in profiles_map]

    def _apply_public_search_filters(
        self,
        query,
        *,
        q: Optional[str] = None,
        speciality: Optional[str] = None,
        profile_id: Optional[int] = None,
        auth_user_ids: Optional[List[int]] = None,
        exclude_auth_user_ids: Optional[List[int]] = None,
    ):
        q_norm = (q or "").strip()
        speciality_norm = (speciality or "").strip()

        if profile_id is not None:
            query = query.where(UserProfile.id == profile_id)

        if auth_user_ids is not None:
            if not auth_user_ids:
                return query.where(UserProfile.id == -1)
            query = query.where(UserProfile.auth_user_id.in_(auth_user_ids))

        if exclude_auth_user_ids:
            query = query.where(
                not_(UserProfile.auth_user_id.in_(exclude_auth_user_ids))
            )

        if q_norm:
            like = f"%{q_norm}%"
            query = query.where(
                (UserProfile.first_name.ilike(like))
                | (UserProfile.last_name.ilike(like))
            )

        if speciality_norm:
            query = query.where(UserProfile.speciality.ilike(f"%{speciality_norm}%"))

        return query

    async def count_search_public(
        self,
        db: AsyncSession,
        q: Optional[str] = None,
        speciality: Optional[str] = None,
        profile_id: Optional[int] = None,
        auth_user_ids: Optional[List[int]] = None,
        exclude_auth_user_ids: Optional[List[int]] = None,
    ) -> int:
        query = select(func.count()).select_from(UserProfile)
        query = self._apply_public_search_filters(
            query,
            q=q,
            speciality=speciality,
            profile_id=profile_id,
            auth_user_ids=auth_user_ids,
            exclude_auth_user_ids=exclude_auth_user_ids,
        )
        result = await db.execute(query)
        return int(result.scalar_one())

    async def search_public(
            self,
            db: AsyncSession,
            q: Optional[str] = None,
            speciality: Optional[str] = None,
            skip: int = 0,
            limit: int = 100,
            profile_id: Optional[int] = None,
            auth_user_ids: Optional[List[int]] = None,
            exclude_auth_user_ids: Optional[List[int]] = None,
    ) -> List[UserProfile]:
        query = select(UserProfile)
        query = self._apply_public_search_filters(
            query,
            q=q,
            speciality=speciality,
            profile_id=profile_id,
            auth_user_ids=auth_user_ids,
            exclude_auth_user_ids=exclude_auth_user_ids,
        )
        query = (
            query.order_by(UserProfile.first_name, UserProfile.last_name)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def update(self, db: AsyncSession, user_id: int, obj_in: UserUpdate) -> Optional[UserProfile]:
        db_obj = await self.get(db, user_id)
        if not db_obj:
            return None

        update_data=obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj


    async def delete(self, db: AsyncSession, user_id: int, current_user_id: Optional[int]=None) -> bool:
        query = delete(UserProfile).where(UserProfile.id == user_id)
        if current_user_id:
            query = query.where(UserProfile.id == current_user_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

user_crud=UserCRUD()
