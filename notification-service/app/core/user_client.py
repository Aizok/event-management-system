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
            url = f"http://user-service:8003/api/users/internal/{user_id}"

            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
            logger.info(f"Response from user-service: {resp.status_code} {resp.text}")

            if resp.status_code != status.HTTP_200_OK:
                logger.error(f"Failed to get user email: {resp.status_code} {resp.text}")
                return None

            return resp.json().get("email")

        except Exception as e:
            logger.error(f"Error fetching user email: {e}")
            return None
