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
