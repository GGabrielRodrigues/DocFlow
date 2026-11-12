from __future__ import annotations

import logging
import time
from typing import Any

import redis

logger = logging.getLogger("docflow.auth.rate_limiter")


class InMemoryRateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 900) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._failures: dict[str, tuple[int, float]] = {}

    def is_allowed(self, key: str) -> bool:
        entry = self._failures.get(key)
        if entry is None:
            return True
        count, expires_at = entry
        if time.time() > expires_at:
            self._failures.pop(key, None)
            return True
        return count < self.max_attempts

    def record_failure(self, key: str) -> int:
        now = time.time()
        entry = self._failures.get(key)
        if entry is None or now > entry[1]:
            new_count = 1
            expires_at = now + self.window_seconds
        else:
            new_count = entry[0] + 1
            expires_at = entry[1]

        self._failures[key] = (new_count, expires_at)
        return new_count

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)

    def get_remaining_attempts(self, key: str) -> int:
        entry = self._failures.get(key)
        if entry is None or time.time() > entry[1]:
            return self.max_attempts
        return max(0, self.max_attempts - entry[0])

    def get_retry_after(self, key: str) -> int:
        entry = self._failures.get(key)
        if entry is None:
            return 0
        remaining = int(entry[1] - time.time())
        return max(0, remaining)


class LoginRateLimiter:
    """Rate limiter para proteção contra força bruta no login, com suporte a Redis e fallback em memória."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_attempts: int = 5,
        window_seconds: int = 900,
        *,
        force_memory: bool = False,
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.force_memory = force_memory
        self._memory = InMemoryRateLimiter(max_attempts, window_seconds)
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
            except Exception as exc:
                self._redis_available = False
                logger.warning(
                    "Redis indisponível (%s). Usando rate limiter em memória.",
                    exc,
                )

    def _format_key(self, key: str) -> str:
        return f"rate_limit:login:{key}"

    def is_allowed(self, key: str) -> bool:
        redis_key = self._format_key(key)
        if self._redis_available and self._redis_client is not None:
            try:
                val: Any = self._redis_client.get(redis_key)
                if val is None:
                    return True
                return int(str(val)) < self.max_attempts
            except Exception as exc:
                logger.warning("Erro no Redis rate limiter (%s). Recorrendo à memória.", exc)
                self._redis_available = False

        return self._memory.is_allowed(key)

    def record_failure(self, key: str) -> int:
        redis_key = self._format_key(key)
        if self._redis_available and self._redis_client is not None:
            try:
                pipe = self._redis_client.pipeline()
                pipe.incr(redis_key)
                pipe.ttl(redis_key)
                results: list[Any] = pipe.execute()
                count = int(results[0])
                ttl = int(results[1])
                if ttl == -1:  # Se não tiver expiração definida
                    self._redis_client.expire(redis_key, self.window_seconds)
                return count
            except Exception as exc:
                logger.warning("Erro no Redis rate limiter (%s). Recorrendo à memória.", exc)
                self._redis_available = False

        return self._memory.record_failure(key)

    def reset(self, key: str) -> None:
        redis_key = self._format_key(key)
        if self._redis_available and self._redis_client is not None:
            try:
                self._redis_client.delete(redis_key)
            except Exception as exc:
                logger.warning("Erro no Redis rate limiter (%s). Recorrendo à memória.", exc)
                self._redis_available = False

        self._memory.reset(key)

    def get_remaining_attempts(self, key: str) -> int:
        redis_key = self._format_key(key)
        if self._redis_available and self._redis_client is not None:
            try:
                val: Any = self._redis_client.get(redis_key)
                if val is None:
                    return self.max_attempts
                return max(0, self.max_attempts - int(str(val)))
            except Exception as exc:
                logger.warning("Erro no Redis rate limiter (%s). Recorrendo à memória.", exc)
                self._redis_available = False

        return self._memory.get_remaining_attempts(key)

    def get_retry_after(self, key: str) -> int:
        redis_key = self._format_key(key)
        if self._redis_available and self._redis_client is not None:
            try:
                ttl_val: Any = self._redis_client.ttl(redis_key)
                ttl = int(ttl_val)
                if ttl > 0:
                    return ttl
                return self.window_seconds
            except Exception as exc:
                logger.warning("Erro no Redis rate limiter (%s). Recorrendo à memória.", exc)
                self._redis_available = False

        return self._memory.get_retry_after(key)
