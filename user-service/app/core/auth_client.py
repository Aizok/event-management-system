import httpx
from fastapi import status
import logging

logger = logging.getLogger(__name__)


async def get_service_token() -> str:
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                "http://nginx/api/auth/internal/token"
            )
            resp.raise_for_status()
            return resp.json()["access_token"]
        except Exception as e:
            logger.error(f"Error getting service token: {e}")
            raise



async def get_user_email_from_auth(auth_user_id: int) -> str:
    try:
        token = await get_service_token()
    except Exception as e:
        logger.error(f"Failed to get service token: {e}")
        raise

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"http://nginx/api/auth/internal/users/{auth_user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )

            if resp.status_code != status.HTTP_200_OK:
                logger.error(f"auth-service error: {resp.status_code}, body: {resp.text}")
                raise Exception("Failed to fetch email")

            return resp.json()["email"]

        except Exception as e:
            logger.error(f"Error fetching email: {e}")
            raise
