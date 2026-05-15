from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional, List
from datetime import datetime
from ..models.user import User, UserStatus, UserRole
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash


class AuthCRUD:
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

    async def list_user_ids(self, db: AsyncSession, role: Optional[str] = None) -> List[int]:
        query = select(User.id)
        if role:
            query = query.where(User.role == UserRole(role))
        result = await db.execute(query.order_by(User.id))
        return list(result.scalars().all())

    async def count_users(self, db: AsyncSession, role: Optional[str] = None) -> int:
        query = select(func.count()).select_from(User)
        if role:
            query = query.where(User.role == UserRole(role))
        result = await db.execute(query)
        return int(result.scalar_one())

    async def create(self, db: AsyncSession, user_in: UserCreate) -> User:
        db_user=User(
            email=user_in.email.lower(),
            hashed_password=get_password_hash(user_in.password),
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

auth_crud=AuthCRUD()
