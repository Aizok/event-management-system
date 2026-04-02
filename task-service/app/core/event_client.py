import httpx
from typing import Optional
from .config import settings
from fastapi import status
from .auth_client import get_service_token


import logging
logger=logging.getLogger(__name__)

async def get_user_role_in_event(event_id: int, user_id: int)-> Optional[str]:
    async with httpx.AsyncClient() as client:
        try:
            token=await get_service_token()
            url=f"http://event-service:8002/api/events/{event_id}/participants/{user_id}"
            resp=await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
            logger.info(f"Event-service response: {resp.status_code} {resp.text}")

            if resp.status_code!=status.HTTP_200_OK:
                logger.error(f"Failed to get role: {resp.status_code}")
                return None

            return resp.json().get("role")

        except Exception as e:
            logger.error(f"Error fetching role: {e}")
            return None