from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
from ..models.user import User, UserStatus
from ..schemas.user import UserCreate, UserUpdate
from ..core.security import get_password_hash


class UserCRUD:
    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(func.lower(User.email) == func.lower(email)).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, user_in: UserCreate) -> User:
        db_user=User(
            email=user_in.email.lower(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            role=user_in.role,
            status=UserStatus.ACTIVE
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def update(self, db: Session, user_id: int, user_in: UserUpdate) -> Optional[User]:
        db_user = self.get_by_id(db, user_id)
        if not db_user:
            return None

        update_data=user_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    def update_last_login(self, db: Session, user_id: int) -> None:
        db_user=self.get_by_id(db, user_id)
        if db_user:
            db_user.last_login=datetime.utcnow()
            db.commit()

    def delete(self, db: Session, user_id: int) -> bool:
        db_user=self.get_by_id(db, user_id)
        if db_user:
            db.delete(db_user)
            db.commit()
            return True
        return False

user_crud=UserCRUD()
