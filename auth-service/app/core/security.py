from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from .config import settings
from ..schemas.user import TokenData, TokenRole
from ..models.user import UserRole
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="auth/login")

pwd_context=CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode=data.copy()

    if expires_delta:
        expire=datetime.now(timezone.utc) + expires_delta
    else:
        expire=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})

    encoded_jwt=jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload=jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if role == "service":
            return TokenData(
                user_id=None,
                email=None,
                role=TokenRole.SERVICE
            )

        if user_id is None or email is None:
            return None

    except JWTError:
        return None


def get_current_user_data(token: str=Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload=jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if role == "service":
            return TokenData(
                user_id=None,
                email=None,
                role=TokenRole.SERVICE
            )

        if user_id is None:
            raise credentials_exception

        return TokenData(
            user_id=int(user_id),
            email=email,
            role=TokenRole(role)
        )
    except JWTError:
        raise credentials_exception


def get_current_service(token_data: TokenData = Depends(get_current_user_data)):
    if token_data.role != "service":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Service access required")
    return token_data
