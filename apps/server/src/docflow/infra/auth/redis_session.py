from __future__ import annotations

import json
import logging
import time
from typing import Any

import redis

logger = logging.getLogger("docflow.auth.session")


class InMemoryTokenStore:
    """Armazenamento em memória para tokens com expiração (TTL)."""

    def __init__(self) -> None:
        self._storage: dict[str, tuple[dict[str, Any], float]] = {}

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        expires_at = time.time() + ttl_seconds
        self._storage[key] = (value, expires_at)
        self._cleanup()

    def get(self, key: str) -> dict[str, Any] | None:
        entry = self._storage.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            self._storage.pop(key, None)
            return None
        return value

    def delete(self, key: str) -> bool:
        return self._storage.pop(key, None) is not None

    def _cleanup(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._storage.items() if now > exp]
        for k in expired:
            self._storage.pop(k, None)

    def clear(self) -> None:
        self._storage.clear()


class RedisSessionStore:
    """Gerencia armazenamento de refresh tokens e tokens de recuperação no Redis com fallback para memória."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        *,
        force_memory: bool = False,
    ) -> None:
        self.redis_url = redis_url
        self.force_memory = force_memory
        self._memory = InMemoryTokenStore()
        self._redis_client: Any = None
        self._redis_available: bool | None = None

        if not force_memory:
            try:
                client = redis.from_url(  # type: ignore[no-untyped-call]
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=1.0,
                    socket_timeout=1.0,
                )
                client.ping()
                self._redis_client = client
                self._redis_available = True
                logger.info("Conectado ao Redis com sucesso para gerenciamento de sessões.")
            except Exception as exc:
                self._redis_available = False
                logger.warning(
                    "Redis indisponível (%s). Usando fallback em memória para sessões e tokens.",
                    exc,
                )

    def is_using_redis(self) -> bool:
        return bool(self._redis_available and self._redis_client is not None)

    def store_refresh_token(
        self,
        token: str,
        data: dict[str, Any],
        ttl_seconds: int = 7 * 24 * 3600,
    ) -> None:
        key = f"refresh_token:{token}"
        if self._redis_available and self._redis_client is not None:
            try:
                self._redis_client.set(key, json.dumps(data), ex=ttl_seconds)
                return
            except Exception as exc:
                logger.warning("Falha ao gravar no Redis (%s). Recorrendo à memória.", exc)
                self._redis_available = False

        self._memory.set(key, data, ttl_seconds)

    def get_refresh_token(self, token: str) -> dict[str, Any] | None:
        key = f"refresh_token:{token}"
        if self._redis_available and self._redis_client is not None:
            try:
                raw: Any = self._redis_client.get(key)
                if raw is not None:
                    return json.loads(str(raw))  # type: ignore[no-any-return]
                return None
            except Exception as exc:
                logger.warning("Falha ao ler do Redis (%s). Recorrendo à memória.", exc)
                self._redis_available = False

        return self._memory.get(key)

    def revoke_refresh_token(self, token: str) -> bool:
        key = f"refresh_token:{token}"
        if self._redis_available and self._redis_client is not None:
            try:
                deleted: Any = self._redis_client.delete(key)
                return bool(int(deleted) > 0)
            except Exception as exc:
                logger.warning("Falha ao excluir do Redis (%s). Recorrendo à memória.", exc)
                self._redis_available = False

        return self._memory.delete(key)

    def store_password_reset_token(
        self,
        token: str,
        data: dict[str, Any],
        ttl_seconds: int = 3600,
    ) -> None:
        key = f"reset_token:{token}"
        if self._redis_available and self._redis_client is not None:
            try:
                self._redis_client.set(key, json.dumps(data), ex=ttl_seconds)
                return
            except Exception as exc:
                logger.warning("Falha ao gravar no Redis (%s). Recorrendo à memória.", exc)
                self._redis_available = False

        self._memory.set(key, data, ttl_seconds)

    def get_password_reset_token(self, token: str) -> dict[str, Any] | None:
        key = f"reset_token:{token}"
        if self._redis_available and self._redis_client is not None:
            try:
                raw: Any = self._redis_client.get(key)
                if raw is not None:
                    return json.loads(str(raw))  # type: ignore[no-any-return]
                return None
            except Exception as exc:
                logger.warning("Falha ao ler do Redis (%s). Recorrendo à memória.", exc)
                self._redis_available = False

        return self._memory.get(key)

    def consume_password_reset_token(self, token: str) -> dict[str, Any] | None:
        """Lê o token de redefinição e o invalida imediatamente para garantir uso único."""
        key = f"reset_token:{token}"
        if self._redis_available and self._redis_client is not None:
            try:
                raw: Any = self._redis_client.get(key)
                if raw is not None:
                    self._redis_client.delete(key)
                    return json.loads(str(raw))  # type: ignore[no-any-return]
                return None
            except Exception as exc:
                logger.warning(
                    "Falha ao consumir token no Redis (%s). Recorrendo à memória.", exc
                )
                self._redis_available = False

        value = self._memory.get(key)
        if value is not None:
            self._memory.delete(key)
        return value
