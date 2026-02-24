from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional, List
from datetime import datetime
from ..models.user import User, UserStatus
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash


class UserCRUD:
    async def get_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        result=await db.execute(
            select(User).where(User.id==user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result=await db.execute(
            select(User).where(func.lower(User.email) == func.lower(email))
        )
        return result.scalar_one_or_none()

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result=await db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        db_user=User(
            email=user_in.email.lower(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=user_in.role,
            status=UserStatus.ACTIVE
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def update(self, db: AsyncSession, user_id: int, user_in: UserUpdate) -> Optional[User]:
        db_user = await self.get_by_id(db, user_id)
        if not db_user:
            return None

        update_data=user_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def update_last_login(self, db: AsyncSession, user_id: int) -> None:
        result=await db.execute(
            update(User).where(User.id == user_id)
            .values(last_login=func.now())
            .execution_options(synchronize_session="fetch")
        )
        await db.commit()

    async def delete(self, db: AsyncSession, user_id: int) -> bool:
        result=await db.execute(
            delete(User).where(User.id == user_id)
        )
        await db.commit()
        return result.rowcount > 0

user_crud=UserCRUD()
