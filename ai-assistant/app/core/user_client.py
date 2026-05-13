import logging

import httpx
from fastapi import HTTPException, status

from .auth_client import get_service_token

logger = logging.getLogger(__name__)

_USER_SVC_BASE = "http://user-service:8003"


async def get_user_profile_id(auth_user_id: int) -> int:
    try:
        token = await get_service_token()
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        snippet = (e.response.text or "")[:200]
        logger.error(
            "auth-service internal/token: HTTP %s body_snippet=%r",
            e.response.status_code,
            snippet,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="auth-service unavailable (service token request failed)",
        ) from e
    except httpx.RequestError as e:
        logger.error("auth-service connection error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="auth-service unavailable (connection)",
        ) from e
    except Exception as e:
        logger.exception("auth-service token: unexpected error")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="auth-service unavailable",
        ) from e

    timeout = httpx.Timeout(15.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(
                f"{_USER_SVC_BASE}/api/users/internal/by-auth/{auth_user_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User profile is required. Create profile in user-service",
                )
            resp.raise_for_status()
            return int(resp.json()["id"])
        except HTTPException:
            raise
        except httpx.HTTPStatusError as e:
            snippet = (e.response.text or "")[:300]
            logger.error(
                "user-service GET /internal/by-auth/%s: HTTP %s snippet=%r",
                auth_user_id,
                e.response.status_code,
                snippet,
            )
            if e.response.status_code == status.HTTP_401_UNAUTHORIZED:
                detail = (
                    "user-service rejected service token "
                    "(ensure SECRET_KEY is identical for auth-service and user-service)"
                )
            elif e.response.status_code == status.HTTP_403_FORBIDDEN:
                detail = "user-service forbade this service request"
            else:
                detail = "user-service unavailable (upstream HTTP error)"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=detail,
            ) from e
        except httpx.RequestError as e:
            logger.error("user-service connection error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="user-service unavailable (connection)",
            ) from e
        except (KeyError, ValueError, TypeError) as e:
            logger.error("user-service invalid response body: %s", e)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="user-service returned invalid data",
            ) from e
