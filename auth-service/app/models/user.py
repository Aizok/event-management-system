from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base=declarative_base()


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

    id=Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password=Column(String(255), nullable=False)
    full_name=Column(String(255), nullable=False)

    role=Column(SQLEnum(UserRole), default=UserRole.EXECUTOR, nullable=False)
    status=Column(SQLEnum(UserStatus), default=UserStatus.PENDING, nullable=False)

    created_at=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at=Column(DateTime(timezone=True), onupdate=func.now())
    last_login=Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role={self.role.value})>"



