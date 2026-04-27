from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import String, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserRole(str, enum.Enum):
    ADMIN="admin"
    ORGANIZER="organizer"
    EXECUTOR="executor"
    VIEWER="viewer"

class UserStatus(str, enum.Enum):
    ACTIVE="active"
    INACTIVE="inactive"
    BLOCKED="blocked"
    PENDING="pending"

class User(Base):
    __tablename__ = "users"

    id:Mapped[int]=mapped_column(primary_key=True, index=True)    
    email:Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str]=mapped_column(String(255), nullable=False)

    role:Mapped[UserRole]=mapped_column(SAEnum(UserRole), default=UserRole.EXECUTOR, nullable=False)
    status:Mapped[UserStatus]=mapped_column(SAEnum(UserStatus), default=UserStatus.PENDING, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role={self.role.value})>"
