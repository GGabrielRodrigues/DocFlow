from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any


request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = getattr(record, "request_id", request_id_context.get())
        if request_id is not None:
            payload["request_id"] = request_id

        for field in ("event", "method", "path", "status_code", "duration_ms"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    if any(getattr(handler, "_docflow_handler", False) for handler in root_logger.handlers):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler._docflow_handler = True  # type: ignore[attr-defined]
    root_logger.addHandler(handler)
