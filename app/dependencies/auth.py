import logging

from fastapi import Header, HTTPException, status

from app.config import get_settings
from app.services.supabase_client import (
    SupabaseNotConfiguredError,
    get_user_profile_id_from_access_token,
)

logger = logging.getLogger("deeptraining.auth")


def get_current_profile_id(authorization: str | None = Header(default=None)) -> str:
    settings = get_settings()

    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header",
            )

        try:
            return get_user_profile_id_from_access_token(token.strip())
        except (SupabaseNotConfiguredError, LookupError, ValueError) as exc:
            logger.warning("auth failed for bearer token: %s", exc)
            if not settings.allow_default_profile_fallback:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthorized",
                ) from exc
        except Exception as exc:
            logger.exception("unexpected auth resolution error: %s", exc)
            if not settings.allow_default_profile_fallback:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthorized",
                ) from exc

    if settings.allow_default_profile_fallback:
        return settings.default_profile_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
    )
