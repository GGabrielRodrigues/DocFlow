from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "docflow-api"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = 8000
    database_url: str = Field(
        default="sqlite:///./docflow.db",
        validation_alias=AliasChoices("DOCFLOW_DATABASE_URL"),
    )

    # SMTP / E-mail
    smtp_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("DOCFLOW_SMTP_HOST", "SMTP_HOST"),
    )
    smtp_port: int = Field(
        default=1025,
        validation_alias=AliasChoices("DOCFLOW_SMTP_PORT", "SMTP_PORT"),
    )
    smtp_user: str = Field(
        default="",
        validation_alias=AliasChoices("DOCFLOW_SMTP_USER", "SMTP_USER"),
    )
    smtp_password: str = Field(
        default="",
        validation_alias=AliasChoices("DOCFLOW_SMTP_PASSWORD", "SMTP_PASSWORD"),
    )
    smtp_from_email: str = Field(
        default="noreply@docflow.local",
        validation_alias=AliasChoices("DOCFLOW_SMTP_FROM_EMAIL", "SMTP_FROM_EMAIL"),
    )
    smtp_use_tls: bool = Field(
        default=False,
        validation_alias=AliasChoices("DOCFLOW_SMTP_USE_TLS", "SMTP_USE_TLS"),
    )
    smtp_use_ssl: bool = Field(
        default=False,
        validation_alias=AliasChoices("DOCFLOW_SMTP_USE_SSL", "SMTP_USE_SSL"),
    )
    smtp_timeout: float = Field(
        default=10.0,
        validation_alias=AliasChoices("DOCFLOW_SMTP_TIMEOUT", "SMTP_TIMEOUT"),
    )

    # Redis / Celery
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias=AliasChoices("DOCFLOW_REDIS_URL", "REDIS_URL"),
    )
    celery_broker_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DOCFLOW_CELERY_BROKER_URL", "CELERY_BROKER_URL"),
    )
    celery_result_backend: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DOCFLOW_CELERY_RESULT_BACKEND", "CELERY_RESULT_BACKEND"),
    )
    celery_task_always_eager: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "DOCFLOW_CELERY_TASK_ALWAYS_EAGER", "CELERY_TASK_ALWAYS_EAGER"
        ),
    )
    celery_task_default_queue: str = Field(
        default="io",
        validation_alias=AliasChoices(
            "DOCFLOW_CELERY_TASK_DEFAULT_QUEUE", "CELERY_TASK_DEFAULT_QUEUE"
        ),
    )

    # JWT / Auth
    jwt_secret_key: str = Field(
        default="dev-only-jwt-secret-key-change-in-production-0123456789abcdef",
        validation_alias=AliasChoices("DOCFLOW_JWT_SECRET_KEY", "JWT_SECRET_KEY"),
    )
    jwt_algorithm: str = Field(
        default="HS256",
        validation_alias=AliasChoices("DOCFLOW_JWT_ALGORITHM", "JWT_ALGORITHM"),
    )
    jwt_access_token_expire_minutes: int = Field(
        default=15,
        validation_alias=AliasChoices(
            "DOCFLOW_JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
        ),
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        validation_alias=AliasChoices(
            "DOCFLOW_JWT_REFRESH_TOKEN_EXPIRE_DAYS", "JWT_REFRESH_TOKEN_EXPIRE_DAYS"
        ),
    )
    password_reset_token_expire_minutes: int = Field(
        default=60,
        validation_alias=AliasChoices(
            "DOCFLOW_PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
            "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES",
        ),
    )

    model_config = SettingsConfigDict(
        env_prefix="DOCFLOW_",
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
