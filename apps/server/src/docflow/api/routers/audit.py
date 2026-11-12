from datetime import datetime
from math import ceil
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from docflow.application.audit import AuditService
from docflow.domain.audit import AuditLogFilter
from docflow.infra.database.audit_repository import AuditLogRepository
from docflow.infra.database.session import get_db_session


class AuditLogItemResponse(BaseModel):
    id: str
    institution_id: str
    user_id: str | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedAuditLogsResponse(BaseModel):
    items: list[AuditLogItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RecordAuditLogRequest(BaseModel):
    action: str
    resource_type: str
    user_id: str | None = None
    resource_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None


def get_current_tenant_id(
    request: Request,
    x_institution_id: str | None = Header(None, alias="X-Institution-ID"),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> str:
    """Extrai o ID da instituição do cabeçalho ou contexto autenticado da requisição."""
    tenant_id = x_institution_id or x_tenant_id
    if tenant_id and tenant_id.strip():
        return tenant_id.strip()

    if hasattr(request.state, "institution_id") and request.state.institution_id:
        return str(request.state.institution_id).strip()

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Identificador de instituição (tenant) é obrigatório.",
    )


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get(
    "",
    response_model=PaginatedAuditLogsResponse,
    summary="Lista registros de auditoria com paginação e filtros",
)
def list_audit_logs(
    request: Request,
    action: str | None = Query(None, description="Filtro por ação"),
    resource_type: str | None = Query(None, description="Filtro por tipo de recurso"),
    user_id: str | None = Query(None, description="Filtro por ID de usuário"),
    start_date: datetime | None = Query(None, description="Data/hora inicial (ISO 8601)"),
    end_date: datetime | None = Query(None, description="Data/hora final (ISO 8601)"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamanho da página"),
    institution_id_query: str | None = Query(
        None,
        alias="institution_id",
        description="Filtro de instituição (deve coincidir com o tenant autenticado)",
    ),
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_db_session),
) -> PaginatedAuditLogsResponse:
    if institution_id_query and institution_id_query != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso não autorizado para a instituição solicitada.",
        )

    repo = AuditLogRepository(session, institution_id=tenant_id)
    service = AuditService(repo)

    filter_params = AuditLogFilter(
        action=action,
        resource_type=resource_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
    )

    items, total = service.list_logs(
        filter_params=filter_params,
        page=page,
        page_size=page_size,
    )

    total_pages = ceil(total / page_size) if total > 0 else 0

    return PaginatedAuditLogsResponse(
        items=[AuditLogItemResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=AuditLogItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra um novo evento na trilha de auditoria",
)
def record_audit_log(
    body: RecordAuditLogRequest,
    request: Request,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_db_session),
) -> AuditLogItemResponse:
    repo = AuditLogRepository(session, institution_id=tenant_id)
    service = AuditService(repo)

    client_ip = body.ip_address
    if not client_ip and request.client:
        client_ip = request.client.host

    log = service.record_event(
        institution_id=tenant_id,
        action=body.action,
        resource_type=body.resource_type,
        user_id=body.user_id,
        resource_id=body.resource_id,
        details=body.details,
        ip_address=client_ip,
    )

    return AuditLogItemResponse.model_validate(log)


@router.get(
    "/{log_id}",
    response_model=AuditLogItemResponse,
    summary="Obtém detalhes de um registro de auditoria",
)
def get_audit_log(
    log_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    session: Session = Depends(get_db_session),
) -> AuditLogItemResponse:
    repo = AuditLogRepository(session, institution_id=tenant_id)
    service = AuditService(repo)

    log = service.get_by_id(log_id)
    if log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de auditoria não encontrado.",
        )

    return AuditLogItemResponse.model_validate(log)
