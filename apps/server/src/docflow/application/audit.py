from typing import Any

from docflow.domain.audit import (
    AuditLog,
    AuditLogFilter,
    AuditLogRepositoryProtocol,
)


class AuditService:
    """Serviço de aplicação para orquestração da trilha de auditoria."""

    def __init__(self, repository: AuditLogRepositoryProtocol) -> None:
        self.repository = repository

    def record_event(
        self,
        institution_id: str,
        action: str,
        resource_type: str,
        user_id: str | None = None,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Registra um evento de auditoria de forma atômica e segura."""
        log = AuditLog(
            institution_id=institution_id,
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        return self.repository.record(log)

    def get_by_id(self, log_id: str) -> AuditLog | None:
        """Busca um registro de auditoria pelo ID."""
        return self.repository.get_by_id(log_id)

    def list_logs(
        self,
        filter_params: AuditLogFilter | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        """Lista registros de auditoria com paginação e filtros."""
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        return self.repository.list(
            filter_params=filter_params,
            page=page,
            page_size=page_size,
        )
