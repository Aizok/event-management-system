import httpx
from fastapi import HTTPException, status
from .auth_client import get_service_token


async def get_user_profile_id(auth_user_id: int) -> int:
    async with httpx.AsyncClient() as client:
        try:
            token = await get_service_token()
            resp = await client.get(
                f"http://user-service:8003/api/users/internal/by-auth/{auth_user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User profile is required. Create profile in user-service"
                )
            resp.raise_for_status()
            return int(resp.json()["id"])
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="user-service unavailable"
            )


async def ensure_user_profile_exists(auth_user_id: int) -> None:
    await get_user_profile_id(auth_user_id)


async def get_auth_user_id_by_profile_id(profile_id: int) -> int:
    async with httpx.AsyncClient() as client:
        try:
            token = await get_service_token()
            resp = await client.get(
                f"http://user-service:8003/api/users/internal/{profile_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found"
                )
            resp.raise_for_status()
            return int(resp.json()["auth_user_id"])
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="user-service unavailable"
            )
