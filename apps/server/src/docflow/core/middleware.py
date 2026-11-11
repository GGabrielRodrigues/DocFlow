import logging
from time import perf_counter
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from docflow.core.logging import request_id_context

MAX_REQUEST_ID_LENGTH = 128
logger = logging.getLogger("docflow.http")


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        request_id = self._request_id(headers.get(b"x-request-id"))
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_context.set(request_id)
        started_at = perf_counter()
        status_code = 500

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                response_headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": response_headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            logger.info(
                "HTTP request completed",
                extra={
                    "event": "http_request_completed",
                    "request_id": request_id,
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "status_code": status_code,
                    "duration_ms": round((perf_counter() - started_at) * 1000, 2),
                },
            )
            request_id_context.reset(token)

    @staticmethod
    def _request_id(value: bytes | None) -> str:
        if value is None:
            return uuid4().hex

        try:
            request_id = value.decode("ascii")
        except UnicodeDecodeError:
            return uuid4().hex

        if 0 < len(request_id) <= MAX_REQUEST_ID_LENGTH and request_id.isprintable():
            return request_id
        return uuid4().hex
