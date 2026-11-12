from fastapi import APIRouter
from sqlalchemy.orm import Session, sessionmaker

from docflow.api.routers.audit import router as audit_router
from docflow.api.routers.auth import router as auth_router
from docflow.api.routers.health import router as health_router
from docflow.api.routers.institutions import create_institutions_router


def create_api_router(session_factory: sessionmaker[Session] | None = None) -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)

    if session_factory is not None:
        router.include_router(create_institutions_router(session_factory))

    v1_router = APIRouter(prefix="/api/v1")
    v1_router.include_router(audit_router)
    v1_router.include_router(auth_router)
    router.include_router(v1_router)

    return router
