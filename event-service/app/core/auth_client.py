import httpx
from .config import settings
from fastapi import status
import logging

logger=logging.getLogger(__name__)

async def get_service_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://auth-service:8001/api/auth/internal/token",
        json={
                "service_name": "event-service",
                "service_secret": settings.SERVICE_SECRET_EVENT
            }
        )
        resp.raise_for_status()
        data = resp.json()

        return data["access_token"]


async def is_admin(user_id: int)->bool:
    async with httpx.AsyncClient() as client:
        try:
            token=await get_service_token()
            url=f"http://auth-service:8001/api/auth/internal/users/{user_id}"
            resp=await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )

            if resp.status_code == status.HTTP_404_NOT_FOUND:
                return False # пользователь не найден

            resp.raise_for_status()
            data=resp.json()
            return data.get("role")=="admin"

        except Exception as e:
            logger.error(f"Failed to check admin status: {e}")
            return False


async def get_user_role(user_id: int) -> str | None:
    async with httpx.AsyncClient() as client:
        try:
            token = await get_service_token()
            resp = await client.get(
                f"http://auth-service:8001/api/auth/internal/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code == status.HTTP_404_NOT_FOUND:
                return None
            resp.raise_for_status()
            data = resp.json()
            role = data.get("role")
            return str(role) if role is not None else None
        except Exception as e:
            logger.error(f"Failed to get user role: {e}")
            return None
