from sqlalchemy import select, func, update, delete, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Any
from ..models.user import UserProfile
from ..schemas.user import UserCreate, UserUpdate


class UserCRUD:
    async def create(self, db: AsyncSession, obj_in: UserCreate, owner_id: int) -> UserProfile:
        db_obj=UserProfile(**obj_in.dict(), auth_user_id=owner_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, user_id: int) -> Optional[UserProfile]:
        query=select(UserProfile).where(UserProfile.id == user_id)
        result=await db.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[UserProfile]:
        query=select(UserProfile).offset(skip).limit(limit).order_by(UserProfile.created_at.desc())
        result=await db.execute(query)
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
