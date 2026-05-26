import httpx
from fastapi import status
import logging
from .config import settings

logger = logging.getLogger(__name__)


async def get_service_token() -> str:
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://auth-service:8001/api/auth/internal/token",
        json={
                "service_name": "user-service",
                "service_secret": settings.SERVICE_SECRET_USER
            }
        )
        resp.raise_for_status()
        data = resp.json()

        return data["access_token"]



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


async def get_auth_user_ids_by_role(role: str) -> list[int]:
    try:
        token = await get_service_token()
    except Exception as e:
        logger.error(f"Failed to get service token for role filter: {e}")
        return []

    async with httpx.AsyncClient() as client:
        try:
            params = {"role": role}
            resp = await client.get(
                "http://nginx/api/auth/internal/user-ids",
                params=params,
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code != status.HTTP_200_OK:
                logger.error(
                    f"auth-service user-ids error: {resp.status_code}, body: {resp.text}"
                )
                return []
            data = resp.json()
            ids = data.get("ids") if isinstance(data, dict) else None
            if not isinstance(ids, list):
                return []
            return [int(x) for x in ids]
        except Exception as e:
            logger.error(f"Error fetching auth user ids by role: {e}")
            return []


async def delete_auth_user(auth_user_id: int) -> None:
    try:
        token = await get_service_token()
    except Exception as e:
        logger.error(f"Failed to get service token for auth user delete: {e}")
        raise

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.delete(
                f"http://nginx/api/auth/internal/users/{auth_user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == status.HTTP_404_NOT_FOUND:
                logger.error(f"auth user {auth_user_id} not found for delete")
                raise Exception("Auth user not found")
            if resp.status_code != status.HTTP_204_NO_CONTENT:
                logger.error(
                    f"auth-service delete error: {resp.status_code}, body: {resp.text}"
                )
                raise Exception("Failed to delete auth user")
        except Exception as e:
            logger.error(f"Error deleting auth user {auth_user_id}: {e}")
            raise


async def get_user_role_from_auth(auth_user_id: int) -> str | None:
    try:
        token = await get_service_token()
    except Exception as e:
        logger.error(f"Failed to get service token for role lookup: {e}")
        return None

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"http://nginx/api/auth/internal/users/{auth_user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if resp.status_code == status.HTTP_404_NOT_FOUND:
                return None
            if resp.status_code != status.HTTP_200_OK:
                logger.error(f"auth-service role error: {resp.status_code}, body: {resp.text}")
                return None
            return resp.json().get("role")
        except Exception as e:
            logger.error(f"Error fetching role: {e}")
            return None
