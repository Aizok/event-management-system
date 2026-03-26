from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from .config import settings
from ..schemas.event import TokenData, TokenRole

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="auth/login")

def decode_access_token(token: str) -> Optional[TokenData]:
    try:
        payload=jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")

        if role is None:
            return None

        if role == TokenRole.SERVICE.value:
            return TokenData(
                user_id=None,
                email=None,
                role=TokenRole.SERVICE
            )

        if user_id is None or email is None:
            return None

        return TokenData(
            user_id=int(user_id),
            email=email,
            role=TokenRole(role)
        )

    except JWTError:
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


def get_current_user_id(token_data: TokenData=Depends(get_current_user_data)) -> int:
    if token_data.role == "service":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Service token cannot access user endpoint"
        )

    return token_data.user_id