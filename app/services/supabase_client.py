import logging
from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings

logger = logging.getLogger("deeptraining.supabase")


class SupabaseNotConfiguredError(RuntimeError):
    pass


@lru_cache
def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise SupabaseNotConfiguredError("Supabase is not configured")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_app_schema_client():
    return get_supabase_client().schema("app")


def get_supabase_auth_user(access_token: str):
    try:
        user_response = get_supabase_client().auth.get_user(access_token)
    except SupabaseNotConfiguredError:
        raise
    except Exception as exc:
        logger.warning("supabase token validation failed")
        raise ValueError("Invalid access token") from exc

    user = getattr(user_response, "user", None)
    if user is None or not getattr(user, "id", None):
        raise ValueError("Invalid access token")
    return user


def get_user_profile_id_from_access_token(access_token: str) -> str:
    user = get_supabase_auth_user(access_token)
    rows = (
        get_app_schema_client()
        .from_("profiles")
        .select("id")
        .eq("auth_user_id", str(user.id))
        .limit(1)
        .execute()
    ).data or []
    if not rows:
        raise LookupError("Profile not found for authenticated user")
    return rows[0]["id"]
