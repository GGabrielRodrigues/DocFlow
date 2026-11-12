from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from docflow.api.routers.auth import (
    get_auth_service,
    get_rate_limiter,
    get_session_store,
    get_token_manager,
)
from docflow.application.auth import AuthService
from docflow.application.email_service import EmailNotificationService
from docflow.core.config import Settings, get_settings
from docflow.infra.auth.hasher import PasswordHasher
from docflow.infra.auth.rate_limiter import LoginRateLimiter
from docflow.infra.auth.redis_session import RedisSessionStore
from docflow.infra.auth.tokens import TokenManager
from docflow.infra.database.models import Base, InstitutionModel, UserModel
from docflow.infra.database.session import get_db_session
from docflow.infra.email.memory import FakeEmailSender
from docflow.main import create_app

AuthFixture = tuple[TestClient, Session, FakeEmailSender, TokenManager, RedisSessionStore]


@pytest.fixture
def auth_fixture() -> Generator[AuthFixture, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    settings = Settings(
        database_url="sqlite:///:memory:",
        jwt_secret_key="api-test-secret-key-321012345678901234567890",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=15,
        jwt_refresh_token_expire_days=7,
    )

    fake_email_sender = FakeEmailSender()
    email_service = EmailNotificationService(sender=fake_email_sender)
    session_store = RedisSessionStore(force_memory=True)
    rate_limiter = LoginRateLimiter(max_attempts=5, window_seconds=900, force_memory=True)
    token_manager = TokenManager(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
    )

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as s:
            try:
                yield s
                s.commit()
            except Exception:
                s.rollback()
                raise

    def override_auth_service() -> AuthService:
        with Session(engine) as s:
            return AuthService(
                session=s,
                token_manager=token_manager,
                session_store=session_store,
                rate_limiter=rate_limiter,
                email_service=email_service,
            )

    app: FastAPI = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    app.dependency_overrides[get_db_session] = override_session
    app.dependency_overrides[get_session_store] = lambda: session_store
    app.dependency_overrides[get_rate_limiter] = lambda: rate_limiter
    app.dependency_overrides[get_token_manager] = lambda: token_manager
    app.dependency_overrides[get_auth_service] = override_auth_service

    with Session(engine) as session:
        # Cria dados iniciais
        hasher = PasswordHasher()
        inst = InstitutionModel(
            id="tenant-alpha",
            name="Instituição Alfa",
            institution_type="SCHOOL",
            cnpj="11222333000181",
            email="alfa@exemplo.org",
        )
        active_user = UserModel(
            id="user-active-1",
            institution_id="tenant-alpha",
            name="Administrador Alfa",
            email="admin@alfa.org",
            password_hash=hasher.hash("senha_admin_123"),
            role="ADMIN",
            status="ACTIVE",
        )
        inactive_user = UserModel(
            id="user-inactive-1",
            institution_id="tenant-alpha",
            name="Usuário Inativo",
            email="inativo@alfa.org",
            password_hash=hasher.hash("senha_inativo_123"),
            role="EMPLOYEE",
            status="INACTIVE",
        )
        session.add_all([inst, active_user, inactive_user])
        session.commit()

        with TestClient(app) as client:
            yield client, session, fake_email_sender, token_manager, session_store


def test_login_success(auth_fixture: AuthFixture) -> None:
    client, _, _, _, _ = auth_fixture
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@alfa.org", "password": "senha_admin_123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 900


def test_login_invalid_password(auth_fixture: AuthFixture) -> None:
    client, _, _, _, _ = auth_fixture
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@alfa.org", "password": "senha_errada"},
    )
    assert response.status_code == 401
    assert "Credenciais inválidas" in response.json()["detail"]


def test_login_user_not_found(auth_fixture: AuthFixture) -> None:
    client, _, _, _, _ = auth_fixture
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inexistente@alfa.org", "password": "qualquer_senha"},
    )
    assert response.status_code == 401
    assert "Credenciais inválidas" in response.json()["detail"]


def test_login_inactive_user_rn04(auth_fixture: AuthFixture) -> None:
    client, _, _, _, _ = auth_fixture
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inativo@alfa.org", "password": "senha_inativo_123"},
    )
    assert response.status_code == 403
    assert "inativo" in response.json()["detail"].lower()


def test_login_rate_limit_lockout(auth_fixture: AuthFixture) -> None:
    client, _, _, _, _ = auth_fixture
    for _ in range(5):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@alfa.org", "password": "senha_errada"},
        )
        assert resp.status_code == 401

    # Sexta tentativa deve tomar 429
    blocked = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@alfa.org", "password": "senha_errada"},
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert "Muitas tentativas" in blocked.json()["detail"]


def test_refresh_token_lifecycle(auth_fixture: AuthFixture) -> None:
    client, _, _, _, _ = auth_fixture
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@alfa.org", "password": "senha_admin_123"},
    )
    tokens = login_resp.json()
    refresh_token = tokens["refresh_token"]

    # Refresh
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != refresh_token

    # Reutilização do refresh token antigo deve falhar
    reuse_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert reuse_resp.status_code == 401


def test_refresh_token_invalid(auth_fixture: AuthFixture) -> None:
    client, _, _, _, _ = auth_fixture
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "token_totalmente_invalido"},
    )
    assert resp.status_code == 401


def test_logout(auth_fixture: AuthFixture) -> None:
    client, _, _, _, _ = auth_fixture
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@alfa.org", "password": "senha_admin_123"},
    )
    tokens = login_resp.json()

    # Logout sem autenticação deve retornar 401
    unauth_resp = client.post("/api/v1/auth/logout")
    assert unauth_resp.status_code == 401

    # Logout autenticado
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout_resp.status_code == 204

    # Refresh com o token revogado deve falhar
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 401


def test_forgot_and_reset_password_flow(auth_fixture: AuthFixture) -> None:
    client, _, fake_email_sender, _, _ = auth_fixture

    # Forgot password
    forgot_resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "admin@alfa.org"},
    )
    assert forgot_resp.status_code == 200
    assert len(fake_email_sender.sent_messages) == 1
    email_body = fake_email_sender.sent_messages[0].body_text
    assert "token=" in email_body
    token = email_body.split("token=")[1].split()[0]

    # Reset com senha muito curta (< 8 chars)
    short_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "123"},
    )
    assert short_resp.status_code == 422

    # Reset com sucesso
    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "nova_senha_admin_456"},
    )
    assert reset_resp.status_code == 200
    assert "Senha redefinida com sucesso" in reset_resp.json()["message"]

    # Tentativa de reutilizar o mesmo token
    reuse_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "outra_senha_qualquer"},
    )
    assert reuse_resp.status_code == 400

    # Login com nova senha
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@alfa.org", "password": "nova_senha_admin_456"},
    )
    assert new_login.status_code == 200


def test_forgot_password_anti_enumeration(auth_fixture: AuthFixture) -> None:
    client, _, fake_email_sender, _, _ = auth_fixture
    initial_emails = len(fake_email_sender.sent_messages)

    resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nao_existe@qualquer.org"},
    )
    assert resp.status_code == 200
    assert len(fake_email_sender.sent_messages) == initial_emails


def test_get_me_endpoint(auth_fixture: AuthFixture) -> None:
    client, _, _, _, _ = auth_fixture

    # Sem header de autenticação
    no_auth = client.get("/api/v1/auth/me")
    assert no_auth.status_code == 401

    # Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@alfa.org", "password": "senha_admin_123"},
    )
    access_token = login_resp.json()["access_token"]

    # Com autenticação válida
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    data = me_resp.json()
    assert data["user"]["id"] == "user-active-1"
    assert data["user"]["email"] == "admin@alfa.org"
    assert data["user"]["role"] == "ADMIN"
    assert data["institution"]["id"] == "tenant-alpha"
    assert data["institution"]["cnpj"] == "11222333000181"


def test_auth_headers_and_token_validation(auth_fixture: AuthFixture) -> None:
    client, session, _, token_manager, _ = auth_fixture

    # Header sem Bearer
    resp1 = client.get("/api/v1/auth/me", headers={"Authorization": "Basic 12345"})
    assert resp1.status_code == 401
    assert "Formato" in resp1.json()["detail"]

    # Header com formato inválido
    resp2 = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer"})
    assert resp2.status_code == 401

    # Token inválido
    resp3 = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token_invalido"})
    assert resp3.status_code == 401
    assert "inválido" in resp3.json()["detail"]

    # Token expirado
    from datetime import timedelta

    expired_token = token_manager.create_access_token(
        user_id="user-active-1",
        institution_id="tenant-alpha",
        role="ADMIN",
        email="admin@alfa.org",
        expires_delta=timedelta(seconds=-10),
    )
    resp4 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp4.status_code == 401
    assert "expirado" in resp4.json()["detail"]

    # Token para usuário inexistente
    ghost_token = token_manager.create_access_token(
        user_id="user-ghost",
        institution_id="tenant-alpha",
        role="ADMIN",
        email="ghost@alfa.org",
    )
    resp5 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ghost_token}"})
    assert resp5.status_code == 401
    assert "não encontrado" in resp5.json()["detail"]

    # Token para usuário inativo
    inactive_token = token_manager.create_access_token(
        user_id="user-inactive-1",
        institution_id="tenant-alpha",
        role="EMPLOYEE",
        email="inativo@alfa.org",
    )
    resp6 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {inactive_token}"})
    assert resp6.status_code == 403
    assert "inativo" in resp6.json()["detail"].lower()


def test_refresh_token_inactive_user(auth_fixture: AuthFixture) -> None:
    client, session, _, token_manager, session_store = auth_fixture

    # Cria refresh token para usuário inativo
    session_store.store_refresh_token(
        "ref-inativo",
        {"user_id": "user-inactive-1", "institution_id": "tenant-alpha"},
    )
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "ref-inativo"})
    assert resp.status_code == 403
    assert "inativo" in resp.json()["detail"].lower()

