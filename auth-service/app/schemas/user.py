import enum
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator
from typing import Optional
from datetime import datetime
from ..models.user import UserRole, UserStatus

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole=UserRole.EXECUTOR


class UserUpdate(BaseModel):
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


class TokenRole(str, enum.Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    EXECUTOR = "executor"
    VIEWER = "viewer"
    SERVICE = "service"


class TokenData(BaseModel):
    role: TokenRole
    user_id: int | None = None
    email: str | None = None
    service_name: str | None = None


class UserSelfUpdate(BaseModel):
    current_password: str = Field(..., min_length=1)
    email: EmailStr | None = None
    new_password: str | None = Field(None, min_length=8, max_length=100)

    @model_validator(mode="after")
    def at_least_one_field(self):
        if self.email is None and self.new_password is None:
            raise ValueError("Укажите новый email и/или новый пароль")
        return self


class UserSelfUpdateResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    message: str = "Сохранено"
