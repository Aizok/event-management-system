from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from .config import settings
from ..schemas.resource import TokenData, TokenRole
from .user_client import ensure_user_profile_exists, get_user_profile_id
import logging

logger=logging.getLogger(__name__)

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="auth/login")

def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload=jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        try:
            role = TokenRole(payload.get("role"))
        except ValueError:
            logger.warning("Invalid role in token")
            return None

        if role == TokenRole.SERVICE:
            service_name=payload.get("sub")
            if not service_name:
                return None

            return TokenData(
                role=TokenRole.SERVICE,
                service_name=service_name,
                user_id=None,
                email=None
            )

        try:
            user_id=int(payload.get("sub"))
        except(TypeError, ValueError):
            return None
        email=payload.get("email")
        if user_id is None or email is None:
            return None

        return TokenData(user_id=user_id, email=email, role=role, service_name=None)

    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def get_current_user_data(token: str=Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    token_data=decode_access_token(token)
    if not token_data:
        raise credentials_exception

    return token_data


async def get_current_user_id(token_data: TokenData=Depends(get_current_user_data)) -> int:
    if token_data.role == TokenRole.SERVICE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Service token cannot access user endpoint"
        )
    if token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    await ensure_user_profile_exists(token_data.user_id)
    return token_data.user_id


async def get_current_profile_id(token_data: TokenData=Depends(get_current_user_data)) -> int:
    if token_data.role == TokenRole.SERVICE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Service token cannot access user endpoint"
        )
    if token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return await get_user_profile_id(token_data.user_id)