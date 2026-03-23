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
        role = payload.get("role")

        if role == TokenRole.SERVICE.value:
            return TokenData(
                user_id=None,
                email=None,
                role=TokenRole.SERVICE
            )

        user_id=payload.get("sub")
        email=payload.get("email")
        if user_id is None or email is None:
            return None

        return TokenData(user_id=int(user_id), email=email, role=TokenRole(role))

    except JWTError:
        return None


def create_service_token(service_name: str, secret: str) -> str |None:
    #Проверка секрета
    expected_secret=getattr(settings, f"SERVICE_{service_name.upper()}_SECRET")
    if expected_secret is None or expected_secret!=secret:
        return None

    expire=datetime.now(timezone.utc) + timedelta(minutes=60)
    payload={
        "sub": service_name,
        "role": TokenRole.SERVICE.value,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    token=jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token

def get_current_user_data(token: str=Depends(oauth2_scheme)) -> TokenData:
    token_data=decode_access_token(token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    return token_data


def get_current_service(token_data: TokenData = Depends(get_current_user_data)):
    if token_data.role != "service":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Service access required")
    return token_data
