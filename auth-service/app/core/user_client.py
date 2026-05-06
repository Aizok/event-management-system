import logging

import httpx
from fastapi import HTTPException, status

from .config import settings

logger = logging.getLogger(__name__)

AUTH_INTERNAL_BASE = "http://auth-service:8001"
USER_SERVICE_BASE = "http://user-service:8003"


async def get_user_service_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{AUTH_INTERNAL_BASE}/api/auth/internal/token",
            json={
                "service_name": "user-service",
                "service_secret": settings.SERVICE_SECRET_USER,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


async def sync_user_profile_email(auth_user_id: int, email: str) -> None:
    token = await get_user_service_token()
    async with httpx.AsyncClient() as client:
        resp = await client.patch(
            f"{USER_SERVICE_BASE}/api/users/internal/by-auth/{auth_user_id}/email",
            json={"email": email},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )
        if resp.status_code >= 400:
            detail = resp.text
            try:
                detail = resp.json().get("detail", detail)
            except Exception:
                pass
            logger.error("user-service email sync failed: %s %s", resp.status_code, detail)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Не удалось синхронизировать email в профиле пользователя",
            )
