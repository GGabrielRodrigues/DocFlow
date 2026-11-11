from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, delete, update
from sqlalchemy.orm import Session

from docflow.domain.audit import (
    AuditAction,
    AuditLog,
    AuditLogFilter,
    AuditLogImmutableError,
)
from docflow.infra.database.audit_repository import AuditLogRepository
from docflow.infra.database.models import AuditLogModel, Base, InstitutionModel


@pytest.fixture
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _create_institution(session: Session, inst_id: str | None = None) -> str:
    unique_num = f"{uuid4().int % 10000000000000:014d}"
    institution = InstitutionModel(
        id=inst_id or str(uuid4()),
        name=f"Inst-{uuid4().hex[:6]}",
        institution_type="SCHOOL",
        cnpj=unique_num,
        email=f"inst_{uuid4().hex[:6]}@example.com",
    )
    session.add(institution)
    session.commit()
    return institution.id


def test_audit_repository_record_and_get(db_session: Session) -> None:
    institution_id = _create_institution(db_session)
    repo = AuditLogRepository(db_session, institution_id)

    log = AuditLog(
        institution_id=institution_id,
        user_id="user-123",
        action=AuditAction.LOGIN,
        resource_type="auth",
        resource_id="session-1",
        details={"method": "password"},
        ip_address="127.0.0.1",
    )

    recorded = repo.record(log)
    db_session.commit()

    assert recorded.id == log.id
    assert recorded.institution_id == institution_id
    assert recorded.user_id == "user-123"
    assert recorded.action == "login"
    assert recorded.details == {"method": "password"}

    fetched = repo.get_by_id(recorded.id)
    assert fetched is not None
    assert fetched.id == recorded.id
    assert fetched.user_id == "user-123"
    assert fetched.action == "login"


def test_audit_repository_record_system_log(db_session: Session) -> None:
    institution_id = _create_institution(db_session)
    repo = AuditLogRepository(db_session, institution_id)

    # user_id é nullable para logs do sistema
    log = AuditLog(
        institution_id=institution_id,
        user_id=None,
        action="system_cleanup",
        resource_type="system",
        details={"purged_files": 10},
    )

    recorded = repo.record(log)
    db_session.commit()

    assert recorded.user_id is None
    fetched = repo.get_by_id(recorded.id)
    assert fetched is not None
    assert fetched.user_id is None
    assert fetched.details == {"purged_files": 10}


def test_audit_repository_rejects_tenant_mismatch(db_session: Session) -> None:
    inst_a = _create_institution(db_session)
    inst_b = _create_institution(db_session)

    repo_a = AuditLogRepository(db_session, inst_a)
    log_b = AuditLog(
        institution_id=inst_b,
        action=AuditAction.LOGIN,
        resource_type="auth",
    )

    with pytest.raises(ValueError, match="Tenant mismatch"):
        repo_a.record(log_b)


def test_audit_repository_strict_multi_tenant_isolation(db_session: Session) -> None:
    inst_a = _create_institution(db_session)
    inst_b = _create_institution(db_session)

    repo_a = AuditLogRepository(db_session, inst_a)
    repo_b = AuditLogRepository(db_session, inst_b)

    log_a = repo_a.record(
        AuditLog(
            institution_id=inst_a,
            action=AuditAction.DOC_CREATE,
            resource_type="document",
            resource_id="doc-a",
        )
    )
    log_b = repo_b.record(
        AuditLog(
            institution_id=inst_b,
            action=AuditAction.DOC_CREATE,
            resource_type="document",
            resource_id="doc-b",
        )
    )
    db_session.commit()

    # Tenant A não pode buscar log do Tenant B pelo ID
    assert repo_a.get_by_id(log_b.id) is None
    assert repo_b.get_by_id(log_a.id) is None

    # Tenant A listando registros só vê os seus próprios
    items_a, total_a = repo_a.list()
    assert total_a == 1
    assert [item.id for item in items_a] == [log_a.id]

    items_b, total_b = repo_b.list()
    assert total_b == 1
    assert [item.id for item in items_b] == [log_b.id]


def test_audit_repository_filtering_and_pagination(db_session: Session) -> None:
    inst_id = _create_institution(db_session)
    repo = AuditLogRepository(db_session, inst_id)

    base_time = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    # Cria múltiplos logs em datas distintas
    for i in range(10):
        action = AuditAction.UPLOAD if i % 2 == 0 else AuditAction.DOC_EDIT
        resource_type = "media" if i % 2 == 0 else "document"
        user_id = f"user-{i % 3}"
        repo.record(
            AuditLog(
                institution_id=inst_id,
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=f"res-{i}",
                created_at=base_time + timedelta(hours=i),
            )
        )
    db_session.commit()

    # 1. Filtro por ação
    items, total = repo.list(filter_params=AuditLogFilter(action=AuditAction.UPLOAD))
    assert total == 5
    assert all(item.action == AuditAction.UPLOAD for item in items)

    # 2. Filtro por resource_type
    items, total = repo.list(filter_params=AuditLogFilter(resource_type="document"))
    assert total == 5
    assert all(item.resource_type == "document" for item in items)

    # 3. Filtro por user_id
    items, total = repo.list(filter_params=AuditLogFilter(user_id="user-0"))
    assert total == 4
    assert all(item.user_id == "user-0" for item in items)

    # 4. Filtro por período
    items, total = repo.list(
        filter_params=AuditLogFilter(
            start_date=base_time + timedelta(hours=2),
            end_date=base_time + timedelta(hours=5),
        )
    )
    assert total == 4

    # 5. Paginação: página 1 com 3 itens
    items, total = repo.list(page=1, page_size=3)
    assert total == 10
    assert len(items) == 3
    # Ordenação deve ser decrescente (mais recente primeiro)
    assert items[0].created_at > items[1].created_at > items[2].created_at

    # Página 4 com 3 itens (sobra 1 item)
    items, total = repo.list(page=4, page_size=3)
    assert total == 10
    assert len(items) == 1


def test_audit_repository_blocks_mutations_and_deletions(db_session: Session) -> None:
    inst_id = _create_institution(db_session)
    repo = AuditLogRepository(db_session, inst_id)

    log = repo.record(
        AuditLog(
            institution_id=inst_id,
            action=AuditAction.APPROVE,
            resource_type="document",
        )
    )
    db_session.commit()

    # 1. Tentativa de chamada aos métodos do repositório
    with pytest.raises(AuditLogImmutableError):
        repo.update(log.id, action="tampered")

    with pytest.raises(AuditLogImmutableError):
        repo.delete(log.id)

    # 2. Tentativa direta de update em instância do modelo SQLAlchemy
    model = db_session.get(AuditLogModel, log.id)
    assert model is not None
    model.action = "tampered"
    with pytest.raises(AuditLogImmutableError):
        db_session.commit()
    db_session.rollback()

    # 3. Tentativa direta de delete em instância do modelo SQLAlchemy
    model = db_session.get(AuditLogModel, log.id)
    assert model is not None
    db_session.delete(model)
    with pytest.raises(AuditLogImmutableError):
        db_session.commit()
    db_session.rollback()

    # 4. Tentativa de bulk delete via SQLAlchemy
    with pytest.raises(AuditLogImmutableError):
        db_session.execute(delete(AuditLogModel))
    db_session.rollback()

    # 5. Tentativa de bulk update via SQLAlchemy
    with pytest.raises(AuditLogImmutableError):
        db_session.execute(update(AuditLogModel).values(action="tampered"))
    db_session.rollback()
