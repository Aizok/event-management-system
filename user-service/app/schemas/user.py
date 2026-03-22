from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    first_name: str=Field(..., min_length=1, max_length=100)
    last_name: str=Field(..., min_length=1, max_length=100)
    phone: Optional[str]=Field(None, max_length=20)
    speciality: Optional[str]=Field(None, max_length=20)


class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    speciality: Optional[str] = Field(None, max_length=20)


class UserResponse(BaseModel):
    id: int
    auth_user_id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    speciality: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserPublicResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    speciality: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None