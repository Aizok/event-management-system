import httpx
from typing import Optional, List, Dict
from .config import settings
from fastapi import status, HTTPException
from .auth_client import get_service_token

import logging
logger=logging.getLogger(__name__)

async def get_event(event_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            token=await get_service_token()
            url = f"http://event-service:8002/api/events/internal/events/{event_id}"
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code == status.HTTP_404_NOT_FOUND:
                raise ValueError("Event not found")

            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Error getting event: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="event-service unavailable"
            )