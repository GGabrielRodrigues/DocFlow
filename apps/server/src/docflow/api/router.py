from fastapi import APIRouter

from docflow.api.routers.health import router as health_router
from docflow.api.routers.institutions import create_institutions_router


def create_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    router.include_router(create_institutions_router())
    return router
