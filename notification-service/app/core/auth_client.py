import httpx
from .config import settings

async def get_service_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http:/localhost:8080/api/auth/internal/token"
        )

        resp.raise_for_status()
        data = resp.json()

        return data["access_token"]
