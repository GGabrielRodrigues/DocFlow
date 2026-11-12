from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "docflow-api"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000
    database_url: str = "sqlite:///./docflow.db"
    storage_endpoint: str | None = None
    storage_access_key: str | None = None
    storage_secret_key: str | None = None
    storage_region: str = "us-east-1"
    storage_bucket_media_raw: str = "media-raw"

    model_config = SettingsConfigDict(
        env_prefix="DOCFLOW_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
