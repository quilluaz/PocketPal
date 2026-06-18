from functools import lru_cache
from uuid import UUID

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql://postgres:postgres@localhost:54322/postgres"
    supabase_url: str = "http://localhost:54321"
    supabase_anon_key: str = "replace_me"
    supabase_jwt_secret: str = "replace_me"
    supabase_service_role_key: str = "replace_me"

    default_base_currency: str = "PHP"
    default_timezone: str = "Asia/Manila"

    mock_webhook_secret: str = "replace_me"
    plaid_client_id: str = "replace_me"
    plaid_secret: str = "replace_me"
    plaid_env: str = "sandbox"

    cors_origins: str = "http://localhost:8081,http://localhost:19006"
    development_user_id: UUID = Field(
        default=UUID("00000000-0000-4000-8000-000000000001"),
        description="Only used when APP_ENV=development and X-Dev-User-Id is absent.",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

