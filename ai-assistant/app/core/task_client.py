import httpx
from fastapi import HTTPException, status
from .config import settings
import logging

logger = logging.getLogger(__name__)


async def create_task(task_data: dict, token: str, owner_id: int):
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            url = f"{settings.TASK_SERVICE_URL}/api/tasks/internal/tasks"
            resp = await client.post(
                url,
                json=task_data,
                params={"owner_id": owner_id},
                headers={"Authorization": f"Bearer {token}"}
            )

            if resp.status_code != status.HTTP_201_CREATED:
                logger.error(f"task-service error: {resp.text}")
                raise Exception("task-service unavailable")

            return resp.json()

        except Exception as e:
            logger.error(f"task-service error: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="task-service unavailable"
            )