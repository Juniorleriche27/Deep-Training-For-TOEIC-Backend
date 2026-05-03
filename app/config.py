from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = Field(default="deeptraining-toeic-api", alias="SERVICE_NAME")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    frontend_origin: str = Field(default="http://localhost:3000", alias="FRONTEND_ORIGIN")
    frontend_origins: str = Field(
        default="https://deeptrainingfortoeic.com,https://www.deeptrainingfortoeic.com,http://localhost:3000,http://127.0.0.1:3000",
        alias="FRONTEND_ORIGINS",
    )

    ai_gateway_base_url: str = Field(default="https://ai.deeptrainingfortoeic.com", alias="AI_GATEWAY_BASE_URL")
    ai_gateway_api_key: str = Field(default="", alias="AI_GATEWAY_API_KEY")
    ai_gateway_timeout_seconds: int = Field(default=120, alias="AI_GATEWAY_TIMEOUT_SECONDS")
    ai_default_response_mode: str = Field(default="fast", alias="AI_DEFAULT_RESPONSE_MODE")

    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    default_profile_id: str = Field(
        default="11111111-1111-1111-1111-111111111111",
        alias="DEFAULT_PROFILE_ID",
    )
    allow_default_profile_fallback: bool = Field(
        default=True,
        alias="ALLOW_DEFAULT_PROFILE_FALLBACK",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_cors_origins() -> list[str]:
    settings = get_settings()
    origins = [item.strip() for item in settings.frontend_origins.split(",") if item.strip()]
    if settings.frontend_origin and settings.frontend_origin not in origins:
        origins.append(settings.frontend_origin)
    return origins
