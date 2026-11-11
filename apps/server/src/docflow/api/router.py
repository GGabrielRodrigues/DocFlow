from fastapi import APIRouter

from docflow.api.routers.health import router as health_router


def create_api_router() -> APIRouter:
    router = APIRouter()
    router.include_router(health_router)
    return router
