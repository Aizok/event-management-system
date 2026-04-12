import httpx
from typing import Optional, List
from fastapi import status, HTTPException
from .auth_client import get_service_token
import logging

logger=logging.getLogger(__name__)


async def get_task(task_id: int):
    async with httpx.AsyncClient(timeout=7.0) as client:
        try:
            token = await get_service_token()
            url = f"http://task-service:8004/api/tasks/internal/tasks/{task_id}"
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"}
            )

            if resp.status_code == status.HTTP_404_NOT_FOUND:
                return None

            if resp.status_code != status.HTTP_200_OK:
                raise Exception("task-service unavailable")

            return resp.json()

        except Exception as e:
            logger.error(f"task-service error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="task-service unavailable"
            )