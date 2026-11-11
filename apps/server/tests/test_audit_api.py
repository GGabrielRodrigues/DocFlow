from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from docflow.infra.database.models import Base, InstitutionModel
from docflow.infra.database.session import get_db_session
from docflow.main import create_app


@pytest.fixture
def app_and_session() -> Generator[tuple[TestClient, Session], None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    app = create_app()
    app.dependency_overrides[get_db_session] = override_session

    with Session(engine) as session:
        # Cria instituições de teste
        inst_a = InstitutionModel(id="tenant-a", name="Instituição A")
        inst_b = InstitutionModel(id="tenant-b", name="Instituição B")
        session.add_all([inst_a, inst_b])
        session.commit()

        with TestClient(app) as client:
            yield client, session


def test_get_audit_logs_requires_tenant_header(app_and_session) -> None:
    client, _ = app_and_session
    response = client.get("/api/v1/audit")
    assert response.status_code == 400
    assert "Identificador de instituição" in response.json()["detail"]


def test_get_audit_logs_empty(app_and_session) -> None:
    client, _ = app_and_session
    response = client.get("/api/v1/audit", headers={"X-Institution-ID": "tenant-a"})
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total_pages"] == 0


def test_post_audit_log_success(app_and_session) -> None:
    client, _ = app_and_session
    payload = {
        "action": "login",
        "resource_type": "auth",
        "user_id": "user-123",
        "resource_id": "session-1",
        "details": {"device": "browser", "success": True},
        "ip_address": "203.0.113.195",
    }
    response = client.post(
        "/api/v1/audit",
        json=payload,
        headers={"X-Institution-ID": "tenant-a"},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["institution_id"] == "tenant-a"
    assert created["action"] == "login"
    assert created["resource_type"] == "auth"
    assert created["user_id"] == "user-123"
    assert created["details"] == {"device": "browser", "success": True}
    assert created["ip_address"] == "203.0.113.195"
    assert created["id"] is not None

    # Consulta individual
    get_res = client.get(
        f"/api/v1/audit/{created['id']}",
        headers={"X-Institution-ID": "tenant-a"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == created["id"]


def test_post_audit_log_system_event(app_and_session) -> None:
    client, _ = app_and_session
    payload = {
        "action": "upload",
        "resource_type": "media",
        "resource_id": "media-xyz",
        "details": {"size": 1048576},
    }
    response = client.post(
        "/api/v1/audit",
        json=payload,
        headers={"X-Tenant-ID": "tenant-a"},
    )
    assert response.status_code == 201
    assert response.json()["user_id"] is None


def test_audit_logs_filters_and_pagination(app_and_session) -> None:
    client, _ = app_and_session
    headers = {"X-Institution-ID": "tenant-a"}

    # Cria múltiplos registros
    client.post(
        "/api/v1/audit",
        json={"action": "login", "resource_type": "auth", "user_id": "u1"},
        headers=headers,
    )
    client.post(
        "/api/v1/audit",
        json={"action": "upload", "resource_type": "media", "user_id": "u1"},
        headers=headers,
    )
    client.post(
        "/api/v1/audit",
        json={"action": "doc_create", "resource_type": "document", "user_id": "u2"},
        headers=headers,
    )
    client.post(
        "/api/v1/audit",
        json={"action": "doc_edit", "resource_type": "document", "user_id": "u2"},
        headers=headers,
    )

    # 1. Filtro por action
    res = client.get("/api/v1/audit?action=upload", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["action"] == "upload"

    # 2. Filtro por resource_type
    res = client.get("/api/v1/audit?resource_type=document", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 2

    # 3. Filtro por user_id
    res = client.get("/api/v1/audit?user_id=u1", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 2

    # 4. Paginação
    res = client.get("/api/v1/audit?page=1&page_size=2", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 2
    assert res.json()["total"] == 4
    assert res.json()["total_pages"] == 2


def test_audit_api_strict_multi_tenant_isolation(app_and_session) -> None:
    client, _ = app_and_session

    # Registra no Tenant A
    res_a = client.post(
        "/api/v1/audit",
        json={"action": "upload", "resource_type": "media"},
        headers={"X-Institution-ID": "tenant-a"},
    )
    log_a_id = res_a.json()["id"]

    # Registra no Tenant B
    res_b = client.post(
        "/api/v1/audit",
        json={"action": "approve", "resource_type": "document"},
        headers={"X-Institution-ID": "tenant-b"},
    )
    log_b_id = res_b.json()["id"]

    # Consulta Tenant A: vê apenas log_a
    list_a = client.get("/api/v1/audit", headers={"X-Institution-ID": "tenant-a"})
    assert list_a.status_code == 200
    assert [item["id"] for item in list_a.json()["items"]] == [log_a_id]

    # Consulta Tenant B: vê apenas log_b
    list_b = client.get("/api/v1/audit", headers={"X-Institution-ID": "tenant-b"})
    assert list_b.status_code == 200
    assert [item["id"] for item in list_b.json()["items"]] == [log_b_id]

    # Tentativa de tenant A buscar item de tenant B pelo ID -> 404
    get_other = client.get(
        f"/api/v1/audit/{log_b_id}",
        headers={"X-Institution-ID": "tenant-a"},
    )
    assert get_other.status_code == 404

    # Tentativa de passar institution_id diferente do header na query string -> 403 Forbidden
    cross_tenant = client.get(
        "/api/v1/audit?institution_id=tenant-b",
        headers={"X-Institution-ID": "tenant-a"},
    )
    assert cross_tenant.status_code == 403


def test_audit_api_blocks_mutation_methods(app_and_session) -> None:
    client, _ = app_and_session
    headers = {"X-Institution-ID": "tenant-a"}

    # Não existem rotas de alteração ou exclusão: FastAPI deve retornar 405 Method Not Allowed
    assert client.put("/api/v1/audit", headers=headers).status_code == 405
    assert client.patch("/api/v1/audit", headers=headers).status_code == 405
    assert client.delete("/api/v1/audit", headers=headers).status_code == 405

    assert client.put("/api/v1/audit/some-id", headers=headers).status_code == 405
    assert client.patch("/api/v1/audit/some-id", headers=headers).status_code == 405
    assert client.delete("/api/v1/audit/some-id", headers=headers).status_code == 405


def test_tenant_extracted_from_request_state(app_and_session) -> None:
    _, session = app_and_session
    engine = session.bind
    from starlette.middleware.base import BaseHTTPMiddleware

    app = create_app()

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as s:
            try:
                yield s
                s.commit()
            except Exception:
                s.rollback()
                raise

    app.dependency_overrides[get_db_session] = override_session

    class FakeTenantMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.institution_id = "tenant-a"
            return await call_next(request)

    app.add_middleware(FakeTenantMiddleware)
    client_with_middleware = TestClient(app)

    # Sem header X-Institution-ID, mas com request.state.institution_id setado pelo middleware
    res = client_with_middleware.get("/api/v1/audit")
    assert res.status_code == 200
    assert res.json()["total"] == 0


def test_db_session_dependency() -> None:
    from docflow.core.config import Settings
    from docflow.infra.database.session import get_db_session, get_engine

    settings = Settings(database_url="sqlite:///:memory:")
    gen = get_db_session(settings)
    session = next(gen)
    assert session is not None
    # Conclui gerador
    try:
        next(gen)
    except StopIteration:
        pass

    # Testa engine caching
    eng1 = get_engine("sqlite:///:memory:")
    eng2 = get_engine("sqlite:///:memory:")
    assert eng1 is eng2


def test_audit_logs_period_filter_via_api(app_and_session) -> None:
    client, _ = app_and_session
    headers = {"X-Institution-ID": "tenant-a"}

    # Cria log com data controlada via repositório
    from docflow.domain.audit import AuditLog
    from docflow.infra.database.audit_repository import AuditLogRepository

    engine = app_and_session[1].bind
    with Session(engine) as s:
        repo = AuditLogRepository(s, "tenant-a")
        repo.record(
            AuditLog(
                institution_id="tenant-a",
                action="login",
                resource_type="auth",
                created_at=datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc),
            )
        )
        repo.record(
            AuditLog(
                institution_id="tenant-a",
                action="login",
                resource_type="auth",
                created_at=datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc),
            )
        )
        s.commit()

    # Filtra período de 4 a 6 de maio (deve retornar 0)
    res = client.get(
        "/api/v1/audit?start_date=2026-05-04T00:00:00Z&end_date=2026-05-06T23:59:59Z",
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["total"] == 0

    # Filtra período de 1 a 2 de maio (deve retornar 1)
    res2 = client.get(
        "/api/v1/audit?start_date=2026-05-01T00:00:00Z&end_date=2026-05-02T23:59:59Z",
        headers=headers,
    )
    assert res2.status_code == 200
    assert res2.json()["total"] == 1

