from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import uuid4


class AuditAction(StrEnum):
    LOGIN = "login"
    LOGOUT = "logout"
    UPLOAD = "upload"
    DOC_CREATE = "doc_create"
    DOC_EDIT = "doc_edit"
    APPROVE = "approve"
    RETURN = "return"
    EXPORT = "export"
    DELETE = "delete"


class AuditLogImmutableError(Exception):
    """Exceção levantada ao tentar alterar ou excluir um registro de auditoria."""

    pass


@dataclass(frozen=True)
class AuditLog:
    institution_id: str
    action: str
    resource_type: str
    id: str = field(default_factory=lambda: str(uuid4()))
    user_id: str | None = None
    resource_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not self.institution_id or not self.institution_id.strip():
            raise ValueError("institution_id é obrigatório")
        if not self.action or not self.action.strip():
            raise ValueError("action é obrigatória")
        if not self.resource_type or not self.resource_type.strip():
            raise ValueError("resource_type é obrigatório")


@dataclass(frozen=True)
class AuditLogFilter:
    action: str | None = None
    resource_type: str | None = None
    user_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class AuditLogRepositoryProtocol(Protocol):
    def record(self, audit_log: AuditLog) -> AuditLog: ...

    def get_by_id(self, log_id: str) -> AuditLog | None: ...

    def list(
        self,
        filter_params: AuditLogFilter | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]: ...
