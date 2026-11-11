from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, event
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, declared_attr, mapped_column

from docflow.domain.audit import AuditLog, AuditLogImmutableError

Id = Annotated[str, mapped_column(String(36), primary_key=True)]


class Base(DeclarativeBase):
    pass


class InstitutionModel(Base):
    __tablename__ = "institutions"
    __table_args__ = (UniqueConstraint("cnpj", name="uq_institutions_cnpj"),)

    id: Mapped[Id] = mapped_column(default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_type: Mapped[str] = mapped_column(String(50), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    address: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class TenantScopedMixin:
    @declared_attr
    def institution_id(cls) -> Mapped[str]:
        return mapped_column(
            String(36),
            ForeignKey("institutions.id"),
            nullable=False,
            index=True,
        )


class UserModel(TenantScopedMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("institution_id", "email", name="uq_users_institution_email"),
    )

    id: Mapped[Id] = mapped_column(default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class AuditLogModel(TenantScopedMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[Id] = mapped_column(default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    details: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
    )

    def to_domain(self) -> AuditLog:
        return AuditLog(
            id=self.id,
            institution_id=self.institution_id,
            user_id=self.user_id,
            action=self.action,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            details=self.details,
            ip_address=self.ip_address,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, entity: AuditLog) -> "AuditLogModel":
        return cls(
            id=entity.id,
            institution_id=entity.institution_id,
            user_id=entity.user_id,
            action=str(entity.action),
            resource_type=entity.resource_type,
            resource_id=entity.resource_id,
            details=dict(entity.details),
            ip_address=entity.ip_address,
            created_at=entity.created_at,
        )


@event.listens_for(AuditLogModel, "before_update")
def _prevent_audit_log_update(mapper: Any, connection: Any, target: Any) -> None:
    raise AuditLogImmutableError(
        "Registros de auditoria são append-only e não podem ser alterados."
    )


@event.listens_for(AuditLogModel, "before_delete")
def _prevent_audit_log_delete(mapper: Any, connection: Any, target: Any) -> None:
    raise AuditLogImmutableError(
        "Registros de auditoria são append-only e não podem ser excluídos."
    )


@event.listens_for(Session, "do_orm_execute")
def _prevent_audit_log_bulk_mutation(orm_execute_state: Any) -> None:
    if orm_execute_state.is_delete or orm_execute_state.is_update:
        for bind_mapper in orm_execute_state.all_mappers:
            if issubclass(bind_mapper.class_, AuditLogModel):
                raise AuditLogImmutableError(
                    "Operações em lote de alteração ou exclusão em AuditLog são proibidas (append-only)."
                )
