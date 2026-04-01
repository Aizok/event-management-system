import httpx
from .config import settings

async def get_service_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://auth-service:8001/api/auth/internal/token",
        json={
                "service_name": "task-service",
                "service_secret": settings.SERVICE_SECRET_TASK
            }
        )
        resp.raise_for_status()
        data = resp.json()

        return data["access_token"]
