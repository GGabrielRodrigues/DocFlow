from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from docflow.api.router import create_api_router
from docflow.core.config import Settings, get_settings
from docflow.core.logging import configure_logging
from docflow.core.middleware import RequestIdMiddleware
from docflow.infra.database.models import Base
from docflow.infra.database.session import create_session_factory
from docflow.infra.storage import InMemoryObjectStorage, ObjectStorage, S3ObjectStorage


def create_app(
    settings: Settings | None = None, storage: ObjectStorage | None = None
) -> FastAPI:
    app_settings = settings or get_settings()
    session_factory = create_session_factory(app_settings)
    if app_settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(session_factory.kw["bind"])
    configure_logging(app_settings.log_level)
    app = FastAPI(
        title="DocFlow API",
        version=app_settings.app_version,
        description="API HTTP.",
        docs_url="/docs" if app_settings.debug else None,
        redoc_url="/redoc" if app_settings.debug else None,
    )
    app.dependency_overrides[get_settings] = lambda: app_settings
    app.add_middleware(RequestIdMiddleware)
    configured_storage = storage
    if configured_storage is None and app_settings.storage_endpoint:
        if not app_settings.storage_access_key or not app_settings.storage_secret_key:
            raise ValueError("Credenciais do storage são obrigatórias")
        configured_storage = S3ObjectStorage(
            endpoint=app_settings.storage_endpoint,
            access_key=app_settings.storage_access_key,
            secret_key=app_settings.storage_secret_key,
            region=app_settings.storage_region,
        )
    app.include_router(
        create_api_router(
            session_factory,
            configured_storage or InMemoryObjectStorage(),
            app_settings.storage_bucket_media_raw,
        )
    )
    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run(
        "docflow.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
