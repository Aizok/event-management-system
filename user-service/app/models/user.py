from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, DateTime, Enum as SAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id:Mapped[int]=mapped_column(Integer, primary_key=True, index=True)
    auth_user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    first_name:Mapped[str]=mapped_column(String(100), nullable=False)
    last_name:Mapped[str]=mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]]=mapped_column(String(20), unique=True, nullable=True, index=True)
    speciality: Mapped[Optional[str]]=mapped_column(String(100))
    bio: Mapped[Optional[str]]=mapped_column(String(255))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role={self.role.value})>"
