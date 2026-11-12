from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel

from docflow.core.config import Settings, get_settings


class LivenessResponse(BaseModel):
    status: str
    service: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]
    request_id: str


router = APIRouter(tags=["health"])


def _readiness_checks() -> dict[str, str]:
    return {
        "postgres": "not_configured",
        "redis": "not_configured",
        "storage": "not_configured",
    }


@router.get(
    "/health",
    response_model=LivenessResponse,
    summary="Verifica se a API está viva",
)
async def health(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> LivenessResponse:
    response.headers["Cache-Control"] = "no-store"
    return LivenessResponse(status="ok", service=settings.app_name)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Verifica dependências da API",
)
async def ready(
    request: Request,
    response: Response,
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    checks = _readiness_checks()
    is_ready = all(value == "ok" for value in checks.values())
    response.status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        checks=checks,
        request_id=request.state.request_id,
    )
