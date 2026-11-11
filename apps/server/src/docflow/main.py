from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from docflow.api.router import create_api_router
from docflow.core.config import Settings, get_settings
from docflow.core.logging import configure_logging
from docflow.core.middleware import RequestIdMiddleware


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
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
    app.include_router(create_api_router())
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
