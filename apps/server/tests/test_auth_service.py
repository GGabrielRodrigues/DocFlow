from collections.abc import Generator
from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from docflow.application.auth import AuthService
from docflow.application.email_service import EmailNotificationService
from docflow.domain.auth import (
    AuthDomainError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    RateLimitExceededError,
    TokenExpiredError,
)
from docflow.infra.auth.hasher import PasswordHasher
from docflow.infra.auth.rate_limiter import LoginRateLimiter
from docflow.infra.auth.redis_session import RedisSessionStore
from docflow.infra.auth.tokens import TokenManager
from docflow.infra.database.models import Base, InstitutionModel, UserModel
from docflow.infra.email.memory import FakeEmailSender


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def token_manager() -> TokenManager:
    return TokenManager(
        secret_key="test-secret-key-123456789012345678901234567890",
        access_token_expire_minutes=15,
    )


@pytest.fixture
def session_store() -> RedisSessionStore:
    return RedisSessionStore(force_memory=True)


@pytest.fixture
def rate_limiter() -> LoginRateLimiter:
    return LoginRateLimiter(max_attempts=5, window_seconds=900, force_memory=True)


@pytest.fixture
def email_sender() -> FakeEmailSender:
    return FakeEmailSender()


@pytest.fixture
def auth_service(
    db_session: Session,
    token_manager: TokenManager,
    session_store: RedisSessionStore,
    rate_limiter: LoginRateLimiter,
    email_sender: FakeEmailSender,
) -> AuthService:
    email_service = EmailNotificationService(sender=email_sender)
    return AuthService(
        session=db_session,
        token_manager=token_manager,
        session_store=session_store,
        rate_limiter=rate_limiter,
        email_service=email_service,
    )


# =============================================================================
# Testes de Hasher
# =============================================================================


def test_password_hasher_generate_and_verify() -> None:
    hasher = PasswordHasher()
    pwd = "MinhaSenhaForte123@"
    hashed = hasher.hash(pwd)

    assert hashed.startswith("scrypt$")
    assert hasher.verify(pwd, hashed) is True
    assert hasher.verify("SenhaIncorreta", hashed) is False
    assert hasher.verify("", hashed) is False
    assert hasher.verify(pwd, "") is False
    assert hasher.verify(pwd, "invalid_hash_string") is False


def test_password_hasher_compat_be04_format() -> None:
    import hashlib
    import secrets

    hasher = PasswordHasher()
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(b"senha_legada_be04", salt=salt, n=2**14, r=8, p=1)
    be04_hash = f"scrypt${salt.hex()}${digest.hex()}"

    assert hasher.verify("senha_legada_be04", be04_hash) is True
    assert hasher.verify("senha_errada", be04_hash) is False


# =============================================================================
# Testes de Tokens (JWT e opacos)
# =============================================================================


def test_token_manager_jwt_lifecycle(token_manager: TokenManager) -> None:
    token = token_manager.create_access_token(
        user_id="user-123",
        institution_id="inst-456",
        role="ADMIN",
        email="admin@test.org",
    )

    payload = token_manager.decode_access_token(token)
    assert payload.sub == "user-123"
    assert payload.institution_id == "inst-456"
    assert payload.role == "ADMIN"
    assert payload.email == "admin@test.org"
    assert payload.exp is not None
    assert payload.iat is not None


def test_token_manager_expired_jwt(token_manager: TokenManager) -> None:
    expired_token = token_manager.create_access_token(
        user_id="user-123",
        institution_id="inst-456",
        role="EMPLOYEE",
        email="emp@test.org",
        expires_delta=timedelta(seconds=-10),
    )

    with pytest.raises(TokenExpiredError):
        token_manager.decode_access_token(expired_token)


def test_token_manager_invalid_jwt(token_manager: TokenManager) -> None:
    with pytest.raises(InvalidTokenError):
        token_manager.decode_access_token("not-a-valid-jwt-token")


def test_token_manager_opaque_tokens(token_manager: TokenManager) -> None:
    token1 = token_manager.generate_opaque_token()
    token2 = token_manager.generate_opaque_token()
    assert token1 != token2
    assert len(token1) > 20


# =============================================================================
# Testes de SessionStore (Redis/Memory)
# =============================================================================


def test_session_store_refresh_and_reset_token(session_store: RedisSessionStore) -> None:
    # Refresh token
    session_store.store_refresh_token(
        "ref-1",
        {"user_id": "u1", "role": "ADMIN"},
        ttl_seconds=60,
    )
    assert session_store.get_refresh_token("ref-1") == {"user_id": "u1", "role": "ADMIN"}
    assert session_store.revoke_refresh_token("ref-1") is True
    assert session_store.get_refresh_token("ref-1") is None

    # Password reset token (uso único)
    session_store.store_password_reset_token("rst-1", {"user_id": "u1"}, ttl_seconds=60)
    assert session_store.get_password_reset_token("rst-1") == {"user_id": "u1"}
    consumed = session_store.consume_password_reset_token("rst-1")
    assert consumed == {"user_id": "u1"}
    assert session_store.get_password_reset_token("rst-1") is None
    assert session_store.consume_password_reset_token("rst-1") is None


# =============================================================================
# Testes de RateLimiter
# =============================================================================


def test_login_rate_limiter_blocks_after_max_attempts(rate_limiter: LoginRateLimiter) -> None:
    key = "user@test.org"
    assert rate_limiter.is_allowed(key) is True
    assert rate_limiter.get_remaining_attempts(key) == 5

    for i in range(1, 5):
        rate_limiter.record_failure(key)
        assert rate_limiter.is_allowed(key) is True
        assert rate_limiter.get_remaining_attempts(key) == 5 - i

    rate_limiter.record_failure(key)
    assert rate_limiter.is_allowed(key) is False
    assert rate_limiter.get_remaining_attempts(key) == 0

    rate_limiter.reset(key)
    assert rate_limiter.is_allowed(key) is True
    assert rate_limiter.get_remaining_attempts(key) == 5


# =============================================================================
# Testes de AuthService (Use Cases)
# =============================================================================


def test_auth_service_login_success(
    auth_service: AuthService,
    db_session: Session,
) -> None:
    hasher = PasswordHasher()
    inst = InstitutionModel(
        id=str(uuid4()),
        name="Escola Alpha",
        institution_type="SCHOOL",
        cnpj="11222333000181",
        email="escola@alpha.org",
    )
    user = UserModel(
        id=str(uuid4()),
        institution_id=inst.id,
        name="Carlos Admin",
        email="carlos@alpha.org",
        password_hash=hasher.hash("segredo123"),
        role="ADMIN",
        status="ACTIVE",
    )
    db_session.add_all([inst, user])
    db_session.commit()

    tokens = auth_service.login("carlos@alpha.org", "segredo123")
    assert tokens.access_token is not None
    assert tokens.refresh_token is not None
    assert tokens.token_type == "Bearer"
    assert tokens.expires_in == 900


def test_auth_service_login_wrong_credentials(
    auth_service: AuthService,
    db_session: Session,
) -> None:
    hasher = PasswordHasher()
    inst = InstitutionModel(
        id=str(uuid4()),
        name="Escola Beta",
        institution_type="SCHOOL",
        cnpj="22333444000192",
        email="escola@beta.org",
    )
    user = UserModel(
        id=str(uuid4()),
        institution_id=inst.id,
        name="Maria Silva",
        email="maria@beta.org",
        password_hash=hasher.hash("senha_correta"),
        role="EMPLOYEE",
        status="ACTIVE",
    )
    db_session.add_all([inst, user])
    db_session.commit()

    # Senha errada
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("maria@beta.org", "senha_incorreta")

    # E-mail não existente
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("naoexiste@beta.org", "senha_qualquer")


def test_auth_service_login_inactive_user_rn04(
    auth_service: AuthService,
    db_session: Session,
) -> None:
    hasher = PasswordHasher()
    inst = InstitutionModel(
        id=str(uuid4()),
        name="Escola Gama",
        institution_type="SCHOOL",
        cnpj="33444555000103",
        email="escola@gama.org",
    )
    user = UserModel(
        id=str(uuid4()),
        institution_id=inst.id,
        name="Inativo User",
        email="inativo@gama.org",
        password_hash=hasher.hash("segredo123"),
        role="EMPLOYEE",
        status="INACTIVE",
    )
    db_session.add_all([inst, user])
    db_session.commit()

    with pytest.raises(InactiveUserError):
        auth_service.login("inativo@gama.org", "segredo123")


def test_auth_service_login_rate_limiting(
    auth_service: AuthService,
    db_session: Session,
) -> None:
    for _ in range(5):
        with pytest.raises(InvalidCredentialsError):
            auth_service.login("ataque@exemplo.org", "senha_errada")

    with pytest.raises(RateLimitExceededError) as exc:
        auth_service.login("ataque@exemplo.org", "senha_errada")
    assert exc.value.retry_after > 0


def test_auth_service_refresh_token_rotation(
    auth_service: AuthService,
    db_session: Session,
) -> None:
    hasher = PasswordHasher()
    inst = InstitutionModel(
        id=str(uuid4()),
        name="Escola Delta",
        institution_type="SCHOOL",
        cnpj="44555666000114",
        email="escola@delta.org",
    )
    user = UserModel(
        id=str(uuid4()),
        institution_id=inst.id,
        name="Juliana",
        email="juliana@delta.org",
        password_hash=hasher.hash("segredo123"),
        role="ADMIN",
        status="ACTIVE",
    )
    db_session.add_all([inst, user])
    db_session.commit()

    tokens1 = auth_service.login("juliana@delta.org", "segredo123")

    # Refresh
    tokens2 = auth_service.refresh(tokens1.refresh_token)
    assert tokens2.access_token != tokens1.access_token
    assert tokens2.refresh_token != tokens1.refresh_token

    # Refresh token anterior deve ter sido revogado (rotação)
    with pytest.raises(InvalidTokenError):
        auth_service.refresh(tokens1.refresh_token)


def test_auth_service_logout(
    auth_service: AuthService,
    db_session: Session,
) -> None:
    hasher = PasswordHasher()
    inst = InstitutionModel(
        id=str(uuid4()),
        name="Escola Epsilon",
        institution_type="SCHOOL",
        cnpj="55666777000125",
        email="escola@epsilon.org",
    )
    user = UserModel(
        id=str(uuid4()),
        institution_id=inst.id,
        name="Paulo",
        email="paulo@epsilon.org",
        password_hash=hasher.hash("segredo123"),
        role="EMPLOYEE",
        status="ACTIVE",
    )
    db_session.add_all([inst, user])
    db_session.commit()

    tokens = auth_service.login("paulo@epsilon.org", "segredo123")
    auth_service.logout(tokens.refresh_token)

    # Não deve mais conseguir dar refresh
    with pytest.raises(InvalidTokenError):
        auth_service.refresh(tokens.refresh_token)


@pytest.mark.asyncio
async def test_auth_service_forgot_and_reset_password(
    auth_service: AuthService,
    db_session: Session,
    email_sender: FakeEmailSender,
    session_store: RedisSessionStore,
) -> None:
    hasher = PasswordHasher()
    inst = InstitutionModel(
        id=str(uuid4()),
        name="Escola Zeta",
        institution_type="SCHOOL",
        cnpj="66777888000136",
        email="escola@zeta.org",
    )
    user = UserModel(
        id=str(uuid4()),
        institution_id=inst.id,
        name="Lucas",
        email="lucas@zeta.org",
        password_hash=hasher.hash("senha_antiga_123"),
        role="ADMIN",
        status="ACTIVE",
    )
    db_session.add_all([inst, user])
    db_session.commit()

    # Solicita redefinição
    await auth_service.request_password_reset("lucas@zeta.org")
    assert len(email_sender.sent_messages) == 1
    sent = email_sender.sent_messages[0]
    assert "lucas@zeta.org" in sent.recipient_emails

    # Recupera o token gerado a partir do link enviado
    assert "token=" in sent.body_text
    token = sent.body_text.split("token=")[1].split()[0]

    # Redefine a senha com sucesso
    auth_service.reset_password(token, "nova_senha_forte_987")

    # Login com a nova senha deve funcionar
    tokens = auth_service.login("lucas@zeta.org", "nova_senha_forte_987")
    assert tokens.access_token is not None

    # Login com senha antiga falha
    with pytest.raises(InvalidCredentialsError):
        auth_service.login("lucas@zeta.org", "senha_antiga_123")

    # Tentativa de reusar o token de uso único deve falhar
    with pytest.raises(InvalidTokenError):
        auth_service.reset_password(token, "outra_senha_qualquer")


def test_auth_service_reset_password_short_password(auth_service: AuthService) -> None:
    with pytest.raises(AuthDomainError):
        auth_service.reset_password("any_token", "curta")


def test_auth_service_get_me(
    auth_service: AuthService,
    db_session: Session,
) -> None:
    hasher = PasswordHasher()
    inst = InstitutionModel(
        id=str(uuid4()),
        name="Escola Eta",
        institution_type="SCHOOL",
        cnpj="77888999000147",
        email="escola@eta.org",
    )
    user = UserModel(
        id=str(uuid4()),
        institution_id=inst.id,
        name="Renata",
        email="renata@eta.org",
        password_hash=hasher.hash("segredo123"),
        role="ADMIN",
        status="ACTIVE",
    )
    db_session.add_all([inst, user])
    db_session.commit()

    u, i = auth_service.get_me(user.id)
    assert u.id == user.id
    assert u.name == "Renata"
    assert i.id == inst.id
    assert i.name == "Escola Eta"


def test_password_hasher_parameterized_scrypt() -> None:
    import hashlib
    import secrets

    hasher = PasswordHasher()
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(b"senha_teste", salt=salt, n=16384, r=8, p=1)
    param_hash = f"scrypt$16384$8$1${salt.hex()}${digest.hex()}"

    assert hasher.verify("senha_teste", param_hash) is True
    assert hasher.verify("senha_errada", param_hash) is False


def test_password_hasher_argon2_and_invalid_formats() -> None:
    hasher = PasswordHasher()
    # Sem argon2 instalado, deve retornar False graciosamente
    assert hasher.verify("senha", "$argon2id$v=19$m=65536,t=2,p=1$fake$hash") is False
    assert hasher.verify("senha", "md5$12345") is False
    assert hasher.verify("senha", "scrypt$invalid$format$extra$parts$here$fail") is False


def test_token_payload_serialization() -> None:
    from docflow.domain.auth import TokenPayload

    payload = TokenPayload(
        sub="u1",
        institution_id="inst1",
        role="ADMIN",
        email="a@b.com",
        exp=123456789,
        iat=123456700,
    )
    d = payload.to_dict()
    assert d["sub"] == "u1"
    assert d["exp"] == 123456789

    restored = TokenPayload.from_dict(d)
    assert restored == payload


def test_session_store_redis_client_mock() -> None:
    from unittest.mock import MagicMock

    store = RedisSessionStore(force_memory=True)
    mock_redis = MagicMock()
    mock_redis.get.return_value = '{"user_id": "u100"}'
    mock_redis.delete.return_value = 1
    mock_redis.ttl.return_value = 500

    store._redis_client = mock_redis
    store._redis_available = True
    assert store.is_using_redis() is True

    store.store_refresh_token("mock-tok", {"user_id": "u100"}, ttl_seconds=100)
    mock_redis.set.assert_called_once()

    data = store.get_refresh_token("mock-tok")
    assert data == {"user_id": "u100"}

    assert store.revoke_refresh_token("mock-tok") is True
    mock_redis.delete.assert_called_once()

    # Password reset via mock
    mock_redis.get.return_value = '{"user_id": "u200"}'
    store.store_password_reset_token("mock-rst", {"user_id": "u200"})
    assert store.get_password_reset_token("mock-rst") == {"user_id": "u200"}
    assert store.consume_password_reset_token("mock-rst") == {"user_id": "u200"}


def test_rate_limiter_redis_client_mock() -> None:
    from unittest.mock import MagicMock

    limiter = LoginRateLimiter(max_attempts=3, window_seconds=600, force_memory=True)
    mock_redis = MagicMock()
    mock_redis.get.return_value = "2"
    mock_redis.ttl.return_value = 450
    mock_pipe = MagicMock()
    mock_pipe.execute.return_value = [1, -1]
    mock_redis.pipeline.return_value = mock_pipe

    limiter._redis_client = mock_redis
    limiter._redis_available = True

    assert limiter.is_allowed("test@mock.org") is True
    mock_redis.get.return_value = "3"
    assert limiter.is_allowed("test@mock.org") is False

    cnt = limiter.record_failure("test@mock.org")
    assert cnt == 1

    limiter.reset("test@mock.org")
    mock_redis.delete.assert_called_once()

    assert limiter.get_retry_after("test@mock.org") == 450
    assert limiter.get_remaining_attempts("test@mock.org") == 0

