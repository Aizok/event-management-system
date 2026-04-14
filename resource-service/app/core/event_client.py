import httpx
from typing import Optional, List, Dict
from .config import settings
from fastapi import status, HTTPException
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

            if resp.status_code==status.HTTP_404_NOT_FOUND:
                return None

            if resp.status_code!=status.HTTP_200_OK:
                raise Exception("event-service unavailable")

            return resp.json().get("role")

        except Exception as e:
            logger.error(f"Error fetching role: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="event-service unavailable"
            )


async def get_user_events_with_roles(user_id: int) -> List[Dict]:
    async with httpx.AsyncClient() as client:
        try:
            token=await get_service_token()
            url = f"http://event-service:8002/api/events/internal/users/{user_id}/events"
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
            resp.raise_for_status()
            return resp.json()["events"]
        except Exception as e:
            logger.error(f"Error fetching user events: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="event-service unavailable"
            )


async def event_exists(event_id: int) -> bool:
    async with httpx.AsyncClient() as client:
        try:
            token = await get_service_token()
            url = f"http://event-service:8002/api/events/internal/events/{event_id}"
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )

            if resp.status_code == status.HTTP_404_NOT_FOUND:
                return False
            if resp.status_code != status.HTTP_200_OK:
                raise Exception("event-service unavailable")
            return True
        except Exception as e:
            logger.error(f"Error checking event existence: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="event-service unavailable"
            )
