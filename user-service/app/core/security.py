from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from .config import settings
from pydantic import BaseModel
from typing import Optional
# from ..models.user import UserProfile
from ..schemas.user import TokenData

# oauth2_scheme=OAuth2PasswordBearer(tokenUrl="http://localhost:8001/api/v1/auth/login")
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="auth/login")



def get_current_user_id(token: str=Depends(oauth2_scheme)) -> int:
    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload=jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except JWTError:
        raise credentials_exception

def get_current_user_data(token: str=Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload=jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)
        user_id: str= payload.get("sub")
        email: str= payload.get("email")
        role: str= payload.get("role")

        if user_id is None:
            raise credentials_exception

        return TokenData(user_id=int(user_id), email=email, role=role)
    except JWTError:
        raise credentials_exception