from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class AuthDomainError(Exception):
    """Exceção base para erros de autenticação e sessão no domínio."""


class AuthenticationError(AuthDomainError):
    """Falha de autenticação geral."""


class InvalidCredentialsError(AuthenticationError):
    """Credenciais inválidas (usuário não encontrado ou senha incorreta)."""


class InactiveUserError(AuthenticationError):
    """Usuário inativo, suspenso ou bloqueado (RN-04)."""


class TokenExpiredError(AuthenticationError):
    """Token expirado."""


class InvalidTokenError(AuthenticationError):
    """Token inválido, corrompido ou revogado."""


class RateLimitExceededError(AuthenticationError):
    """Limite de tentativas excedido (bloqueio contra força bruta)."""

    def __init__(
        self,
        message: str = "Muitas tentativas de login falhas. Tente novamente mais tarde.",
        retry_after: int = 900,
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


@dataclass(frozen=True, slots=True)
class TokenPayload:
    sub: str
    institution_id: str
    role: str
    email: str
    exp: int | None = None
    iat: int | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "sub": self.sub,
            "institution_id": self.institution_id,
            "role": self.role,
            "email": self.email,
        }
        if self.exp is not None:
            data["exp"] = self.exp
        if self.iat is not None:
            data["iat"] = self.iat
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TokenPayload:
        return cls(
            sub=str(data["sub"]),
            institution_id=str(data["institution_id"]),
            role=str(data["role"]),
            email=str(data.get("email", "")),
            exp=data.get("exp"),
            iat=data.get("iat"),
        )


@dataclass(frozen=True, slots=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: str
    institution_id: str
    name: str
    email: str
    role: str
    status: str


def validate_user_active(status: str) -> None:
    """Valida RN-04: Usuário com status != 'ACTIVE' NÃO pode autenticar."""
    if status.upper() != "ACTIVE":
        raise InactiveUserError("Usuário inativo ou suspenso.")


def validate_password_strength(password: str) -> None:
    """Valida se a senha atende ao tamanho mínimo."""
    if len(password) < 8:
        raise AuthDomainError("A senha deve ter pelo menos 8 caracteres.")
