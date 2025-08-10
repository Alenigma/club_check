import os
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLUB_CHECK_", extra="ignore")

    app_name: str = "Club Check API"
    environment: str = Field(default="development", description="development|staging|production")

    secret_key: str = Field(default="change-me-in-production", description="JWT secret key")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = Field(default="sqlite:///./club_check.db")

    # Accept raw string from env to allow JSON array or CSV; app will normalize to list
    cors_origins: str = Field(default="*")

    create_tables_on_startup: bool = True
    seed_on_startup: bool = False

    # Optional BLE verification for presence
    enable_ble_check: bool = False
    ble_service_uuid_hint: str | None = None


@lru_cache()
def get_settings() -> Settings:
    use_env_file = os.getenv("CLUB_CHECK_USE_ENV_FILE", "true").lower() not in ("false", "0", "no")
    env_file = ".env" if use_env_file else None
    return Settings(_env_file=env_file)


