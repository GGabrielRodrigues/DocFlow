from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from docflow.application.email_service import EmailNotificationService
from docflow.domain.auth import (
    AuthenticationError,
    AuthTokens,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    RateLimitExceededError,
    validate_password_strength,
    validate_user_active,
)
from docflow.infra.auth.hasher import PasswordHasher, default_hasher
from docflow.infra.auth.rate_limiter import LoginRateLimiter
from docflow.infra.auth.redis_session import RedisSessionStore
from docflow.infra.auth.tokens import TokenManager
from docflow.infra.database.models import InstitutionModel, UserModel

logger = logging.getLogger("docflow.auth.service")


class AuthService:
    """Serviço de aplicação para autenticação, rotação de tokens e recuperação de senhas."""

    def __init__(
        self,
        session: Session,
        token_manager: TokenManager,
        session_store: RedisSessionStore,
        rate_limiter: LoginRateLimiter,
        hasher: PasswordHasher | None = None,
        email_service: EmailNotificationService | None = None,
    ) -> None:
        self.session = session
        self.token_manager = token_manager
        self.session_store = session_store
        self.rate_limiter = rate_limiter
        self.hasher = hasher or default_hasher
        self.email_service = email_service

    def login(
        self,
        email: str,
        password: str,
        client_ip: str | None = None,
    ) -> AuthTokens:
        normalized_email = email.strip().lower()
        rate_key = f"{client_ip}:{normalized_email}" if client_ip else normalized_email

        if not self.rate_limiter.is_allowed(rate_key):
            retry_after = self.rate_limiter.get_retry_after(rate_key)
            raise RateLimitExceededError(
                "Muitas tentativas de login falhas. Tente novamente mais tarde.",
                retry_after=retry_after,
            )

        stmt = select(UserModel).where(UserModel.email == normalized_email)
        user = self.session.scalar(stmt)

        if user is None or not self.hasher.verify(password, user.password_hash):
            self.rate_limiter.record_failure(rate_key)
            raise InvalidCredentialsError("Credenciais inválidas.")

        # Valida RN-04: Usuário com status != 'ACTIVE' NÃO pode autenticar
        try:
            validate_user_active(user.status)
        except InactiveUserError:
            raise

        # Sucesso no login: reseta tentativas falhas
        self.rate_limiter.reset(rate_key)

        access_token = self.token_manager.create_access_token(
            user_id=user.id,
            institution_id=user.institution_id,
            role=user.role,
            email=user.email,
        )

        refresh_token = self.token_manager.generate_opaque_token()
        session_data: dict[str, Any] = {
            "user_id": user.id,
            "institution_id": user.institution_id,
            "role": user.role,
            "email": user.email,
        }
        self.session_store.store_refresh_token(refresh_token, session_data)

        return AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=self.token_manager.access_token_expire_minutes * 60,
        )

    def refresh(self, refresh_token: str) -> AuthTokens:
        session_data = self.session_store.get_refresh_token(refresh_token)
        if not session_data:
            raise InvalidTokenError("Refresh token inválido ou expirado.")

        user_id = str(session_data.get("user_id", ""))
        user = self.session.get(UserModel, user_id)
        if user is None:
            self.session_store.revoke_refresh_token(refresh_token)
            raise InvalidTokenError("Usuário associado ao token não encontrado.")

        validate_user_active(user.status)

        # Rotação de refresh token: revoga o anterior e emite novo par
        self.session_store.revoke_refresh_token(refresh_token)

        new_access_token = self.token_manager.create_access_token(
            user_id=user.id,
            institution_id=user.institution_id,
            role=user.role,
            email=user.email,
        )
        new_refresh_token = self.token_manager.generate_opaque_token()
        new_session_data: dict[str, Any] = {
            "user_id": user.id,
            "institution_id": user.institution_id,
            "role": user.role,
            "email": user.email,
        }
        self.session_store.store_refresh_token(new_refresh_token, new_session_data)

        return AuthTokens(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=self.token_manager.access_token_expire_minutes * 60,
        )

    def logout(self, refresh_token: str | None = None) -> None:
        if refresh_token:
            self.session_store.revoke_refresh_token(refresh_token)

    async def request_password_reset(
        self,
        email: str,
        reset_base_url: str = "/reset-password",
    ) -> None:
        normalized_email = email.strip().lower()
        stmt = select(UserModel).where(UserModel.email == normalized_email)
        user = self.session.scalar(stmt)

        # Retorno silencioso contra enumeração de e-mails
        if user is None:
            logger.info("Solicitação de reset para e-mail não cadastrado: %s", normalized_email)
            return

        token = self.token_manager.generate_opaque_token()
        reset_data: dict[str, Any] = {
            "user_id": user.id,
            "email": user.email,
        }
        # TTL de 1 hora (3600 segundos)
        self.session_store.store_password_reset_token(token, reset_data, ttl_seconds=3600)

        if self.email_service is not None:
            reset_url = f"{reset_base_url}?token={token}"
            try:
                await self.email_service.send_password_reset(
                    recipient_email=user.email,
                    user_name=user.name,
                    reset_url=reset_url,
                    token=token,
                    expires_in_minutes=60,
                )
            except Exception as exc:
                logger.error("Erro ao enviar e-mail de recuperação de senha: %s", exc)

    def reset_password(self, token: str, new_password: str) -> None:
        validate_password_strength(new_password)

        token_data = self.session_store.consume_password_reset_token(token)
        if not token_data:
            raise InvalidTokenError("Token de recuperação inválido ou expirado.")

        user_id = str(token_data.get("user_id", ""))
        user = self.session.get(UserModel, user_id)
        if user is None:
            raise InvalidTokenError("Usuário não encontrado.")

        user.password_hash = self.hasher.hash(new_password)
        self.session.commit()

    def get_me(self, user_id: str) -> tuple[UserModel, InstitutionModel]:
        user = self.session.get(UserModel, user_id)
        if user is None:
            raise InvalidTokenError("Usuário não encontrado.")

        institution = self.session.get(InstitutionModel, user.institution_id)
        if institution is None:
            raise AuthenticationError("Instituição vinculada não encontrada.")

        return user, institution
