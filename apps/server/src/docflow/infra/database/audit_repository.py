from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from docflow.domain.audit import (
    AuditLog,
    AuditLogFilter,
    AuditLogImmutableError,
)
from docflow.infra.database.models import AuditLogModel
from docflow.infra.database.repository import TenantRepository


class AuditLogRepository(TenantRepository[AuditLogModel]):
    def __init__(self, session: Session, institution_id: str) -> None:
        super().__init__(
            session=session,
            model=AuditLogModel,
            institution_id=institution_id,
        )

    def record(self, log: AuditLog) -> AuditLog:
        if log.institution_id != self.institution_id:
            raise ValueError(
                f"Tenant mismatch: repository is scoped to institution '{self.institution_id}', "
                f"but audit log has institution '{log.institution_id}'"
            )
        model = AuditLogModel.from_domain(log)
        self.session.add(model)
        self.session.flush()
        return model.to_domain()

    def get_by_id(self, log_id: str) -> AuditLog | None:
        model = self.get(log_id)
        if model is None:
            return None
        return model.to_domain()

    def list(  # type: ignore[override]
        self,
        filter_params: AuditLogFilter | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        stmt = self.statement()
        count_stmt = select(func.count()).select_from(self.statement().subquery())

        if filter_params:
            if filter_params.action:
                stmt = stmt.where(AuditLogModel.action == filter_params.action)
                count_stmt = select(func.count()).select_from(stmt.subquery())
            if filter_params.resource_type:
                stmt = stmt.where(AuditLogModel.resource_type == filter_params.resource_type)
                count_stmt = select(func.count()).select_from(stmt.subquery())
            if filter_params.user_id:
                stmt = stmt.where(AuditLogModel.user_id == filter_params.user_id)
                count_stmt = select(func.count()).select_from(stmt.subquery())
            if filter_params.start_date:
                stmt = stmt.where(AuditLogModel.created_at >= filter_params.start_date)
                count_stmt = select(func.count()).select_from(stmt.subquery())
            if filter_params.end_date:
                stmt = stmt.where(AuditLogModel.created_at <= filter_params.end_date)
                count_stmt = select(func.count()).select_from(stmt.subquery())

        total = self.session.scalar(count_stmt) or 0

        # Ordenação: mais recentes primeiro
        stmt = stmt.order_by(
            AuditLogModel.created_at.desc(),
            AuditLogModel.id.desc(),
        )

        # Paginação
        offset = max(0, (page - 1) * page_size)
        stmt = stmt.offset(offset).limit(page_size)

        models = list(self.session.scalars(stmt).all())
        return [cast(AuditLogModel, m).to_domain() for m in models], total

    def update(self, *args: Any, **kwargs: Any) -> Any:
        raise AuditLogImmutableError(
            "Operações de atualização não são permitidas em AuditLog (append-only)."
        )

    def delete(self, *args: Any, **kwargs: Any) -> Any:
        raise AuditLogImmutableError(
            "Operações de exclusão não são permitidas em AuditLog (append-only)."
        )
