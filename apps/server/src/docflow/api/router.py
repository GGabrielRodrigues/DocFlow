from fastapi import APIRouter

from docflow.api.routers.audit import router as audit_router
from docflow.api.routers.health import router as health_router


def create_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)

    v1_router = APIRouter(prefix="/api/v1")
    v1_router.include_router(audit_router)
    router.include_router(v1_router)

    return router
