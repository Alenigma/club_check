from functools import lru_cache
from typing import List

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CLUB_CHECK_", extra="ignore")

    app_name: str = "Club Check API"
    environment: str = Field(default="development", description="development|staging|production")

    secret_key: str = Field(default="change-me-in-production", description="JWT secret key")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = Field(default="sqlite:///./club_check.db")

    cors_origins: List[str] = Field(default_factory=lambda: ["*"])

    create_tables_on_startup: bool = True
    seed_on_startup: bool = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


