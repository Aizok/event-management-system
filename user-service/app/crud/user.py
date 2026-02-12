from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Any
from ..models.user import UserProfile
from ..schemas.user import UserCreate, UserUpdate


class UserCRUD:
    def create(self, db: Session, obj_in: UserCreate, owner_id: int) -> UserProfile:
        db_obj=UserProfile(**obj_in.dict(), auth_user_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, user_id: int) -> Optional[UserProfile]:
        return db.query(UserProfile).filter(UserProfile.id == user_id).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[UserProfile]:
        return db.query(UserProfile).offset(skip).limit(limit).all()

    def update(self, db: Session, user_id: int, obj_in: UserUpdate) -> Optional[UserProfile]:
        db_obj = self.get(db, user_id)
        if not db_obj:
            return None

        update_data=obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj


    def delete(self, db: Session, user_id: int) -> bool:
        db_obj=self.get(db, user_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False

user_crud=UserCRUD()
