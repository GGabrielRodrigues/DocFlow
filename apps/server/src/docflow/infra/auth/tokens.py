from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from docflow.domain.auth import InvalidTokenError, TokenExpiredError, TokenPayload


class TokenManager:
    """Responsável pela criação e validação de JWTs e tokens opacos."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 15,
    ) -> None:
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    def create_access_token(
        self,
        *,
        user_id: str,
        institution_id: str,
        role: str,
        email: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        now = datetime.now(UTC)
        expire = now + (
            expires_delta
            if expires_delta is not None
            else timedelta(minutes=self.access_token_expire_minutes)
        )

        payload: dict[str, Any] = {
            "sub": str(user_id),
            "institution_id": str(institution_id),
            "role": str(role),
            "email": str(email),
            "jti": secrets.token_hex(16),
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> TokenPayload:
        try:
            payload: dict[str, Any] = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return TokenPayload.from_dict(payload)
        except jwt.ExpiredSignatureError as err:
            raise TokenExpiredError("Token de acesso expirado.") from err
        except jwt.PyJWTError as err:
            raise InvalidTokenError("Token de acesso inválido.") from err

    @staticmethod
    def generate_opaque_token(nbytes: int = 32) -> str:
        """Gera um token seguro opaco para refresh ou redefinição de senha."""
        return secrets.token_urlsafe(nbytes)
