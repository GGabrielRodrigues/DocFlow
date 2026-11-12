from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from docflow.application.auth import AuthService
from docflow.application.email_service import EmailNotificationService
from docflow.core.config import Settings, get_settings
from docflow.domain.auth import (
    AuthDomainError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    RateLimitExceededError,
    TokenExpiredError,
)
from docflow.infra.auth.rate_limiter import LoginRateLimiter
from docflow.infra.auth.redis_session import RedisSessionStore
from docflow.infra.auth.tokens import TokenManager
from docflow.infra.database.models import UserModel
from docflow.infra.database.session import get_db_session
from docflow.infra.email.smtp import SMTPEmailSender

router = APIRouter(prefix="/auth", tags=["auth"])


# =============================================================================
# Schemas
# =============================================================================


class LoginRequest(BaseModel):
    email: str = Field(..., description="E-mail do usuário")
    password: str = Field(..., description="Senha do usuário")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, description="Nova senha (mínimo 8 caracteres)")


class MessageResponse(BaseModel):
    message: str


class UserMeResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: str
    institution_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InstitutionMeResponse(BaseModel):
    id: str
    name: str
    institution_type: str
    cnpj: str
    email: str
    phone: str | None = None
    address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeResponse(BaseModel):
    user: UserMeResponse
    institution: InstitutionMeResponse


# =============================================================================
# Dependencies
# =============================================================================


@lru_cache
def get_session_store(settings: Settings = Depends(get_settings)) -> RedisSessionStore:
    return RedisSessionStore(redis_url=settings.redis_url)


@lru_cache
def get_rate_limiter(settings: Settings = Depends(get_settings)) -> LoginRateLimiter:
    return LoginRateLimiter(redis_url=settings.redis_url)


def get_token_manager(settings: Settings = Depends(get_settings)) -> TokenManager:
    return TokenManager(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_token_expire_minutes=settings.jwt_access_token_expire_minutes,
    )


def get_auth_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    session_store: RedisSessionStore = Depends(get_session_store),
    rate_limiter: LoginRateLimiter = Depends(get_rate_limiter),
    token_manager: TokenManager = Depends(get_token_manager),
) -> AuthService:
    email_sender = SMTPEmailSender(settings)
    email_service = EmailNotificationService(sender=email_sender)
    return AuthService(
        session=session,
        token_manager=token_manager,
        session_store=session_store,
        rate_limiter=rate_limiter,
        email_service=email_service,
    )


def get_current_user(
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    session: Session = Depends(get_db_session),
    token_manager: TokenManager = Depends(get_token_manager),
) -> UserModel:
    """Valida o cabeçalho Authorization: Bearer <token>, decodifica o JWT e retorna o usuário."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado. Cabeçalho Authorization ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato do cabeçalho de autorização inválido. Use 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    try:
        payload = token_manager.decode_access_token(token)
    except TokenExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = session.get(UserModel, payload.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário associado ao token não encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status.upper() != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo ou suspenso.",
        )

    # Injeta contexto na requisição para compatibilidade com auditoria e logs
    request.state.user = user
    request.state.user_id = user.id
    request.state.institution_id = user.institution_id

    return user


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autentica usuário por e-mail e senha e retorna par de tokens",
)
def login(
    payload: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    client_ip = request.client.host if request.client else None
    try:
        tokens = auth_service.login(
            email=payload.email,
            password=payload.password,
            client_ip=client_ip,
        )
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except RateLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
            headers={"Retry-After": str(exc.retry_after)},
        ) from exc


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotaciona o refresh token e emite novo par access_token + refresh_token",
)
def refresh(
    payload: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        tokens = auth_service.refresh(payload.refresh_token)
        return TokenResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
            expires_in=tokens.expires_in,
        )
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoga o refresh token da sessão",
)
def logout(
    payload: LogoutRequest | None = None,
    current_user: UserModel = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    if payload and payload.refresh_token:
        auth_service.logout(payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Envia e-mail de recuperação de senha com token de uso único",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.request_password_reset(payload.email)
    return MessageResponse(
        message="Se o e-mail estiver cadastrado, um link de recuperação será enviado."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Redefine a senha do usuário utilizando o token de uso único",
)
def reset_password(
    payload: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    try:
        auth_service.reset_password(payload.token, payload.new_password)
        return MessageResponse(message="Senha redefinida com sucesso.")
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except AuthDomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Retorna os dados do usuário autenticado e da sua instituição",
)
def get_me(
    current_user: UserModel = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MeResponse:
    user, institution = auth_service.get_me(current_user.id)
    return MeResponse(
        user=UserMeResponse.model_validate(user),
        institution=InstitutionMeResponse.model_validate(institution),
    )
