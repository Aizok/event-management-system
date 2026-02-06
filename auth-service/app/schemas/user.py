from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.user import UserRole, UserStatus

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole=UserRole.EXECUTOR


class UserUpdate(BaseModel):
    full_name: str = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole]=None
    status: Optional[UserStatus]=None


class UserResponse(UserBase):
    id: int
    role: UserRole
    status: UserStatus
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: int
    email: str
    role: UserRole
