import httpx
from .config import settings
from fastapi import status
import logging

logger=logging.getLogger(__name__)

async def get_service_token() -> str:
    async with httpx.AsyncClient(timeout=7.0) as client:
        try:
            resp = await client.post(
                "http://auth-service:8001/api/auth/internal/token",
                json={
                    "service_name": "ai-assistant",
                    "service_secret": settings.SERVICE_SECRET_AI,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["access_token"]
        except httpx.HTTPStatusError as e:
            snippet = (e.response.text or "")[:200]
            logger.error(
                "auth internal/token: HTTP %s body_snippet=%r",
                e.response.status_code,
                snippet,
            )
            raise
        except KeyError as e:
            logger.error("auth internal/token: missing access_token in JSON: %s", e)
            raise


async def is_admin(user_id: int)->bool:
    async with httpx.AsyncClient(timeout=10.0) as client:
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
