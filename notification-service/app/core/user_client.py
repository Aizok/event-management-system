import httpx
from typing import Optional
from .config import settings
from fastapi import status



import logging
logger=logging.getLogger(__name__)


async def get_user_email(user_id: int) -> Optional[str]:
    async with httpx.AsyncClient() as client:
        try:
            user_resp=await client.get(
                f"http://localhost:8080/api/users/{user_id}",
                headers={"Authorization": f"Bearer {settings.SECRET_KEY}"}
            )
            if user_resp.status_code!=status.HTTP_200_OK:
                logger.error(f"user-service error: {user_resp.status_code}")
                return None

            user_profile=user_resp.json()
            auth_user_id = user_profile.get("auth_user_id")
            if not auth_user_id:
                logger.error("auth_user_id not found")
                return None

            auth_resp = await client.get(
                f"http://localhost:8080/api/auth/users/{auth_user_id}",
                headers={"Authorization": f"Bearer {settings.SECRET_KEY}"}
            )
            if auth_resp.status_code != status.HTTP_200_OK:
                logger.error(f"user-service error: {auth_resp.status_code}")
                return None

            auth_data=auth_resp.json()
            return auth_data.get("email")

        except Exception as e:
            logger.error(f"")