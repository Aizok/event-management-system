import httpx
from typing import Optional
from .config import settings
from fastapi import status
from .auth_client import get_service_token


import logging
logger=logging.getLogger(__name__)


async def get_user_email(user_id: int) -> Optional[str]:
    async with httpx.AsyncClient() as client:
        try:
            token = await get_service_token()

            resp = await client.get(
                f"http://user_service:8001/api/v1/internal/{user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            if resp.status_code != status.HTTP_200_OK:
                logger.error(f"Failed to get user email: {resp.status_code} {resp.text}")
                return None

            return resp.json().get("email")

        except Exception as e:
            logger.error(f"Error fetching user email: {e}")
            return None
