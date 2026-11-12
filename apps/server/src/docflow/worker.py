from __future__ import annotations

import sys
from collections.abc import Sequence

from docflow.core.celery import (
    CELERY_QUEUES,
    CELERY_TASK_ROUTES,
    DEFAULT_EXCHANGE,
    DocFlowTask,
    celery_app,
    create_celery_app,
    ping_worker,
)

app = celery_app
celery = celery_app


def main(argv: Sequence[str] | None = None) -> None:
    """Entrypoint CLI para execução dos workers do Celery via linha de comando."""
    if argv is not None:
        args = list(argv)
    else:
        args = sys.argv[1:]

    if not args:
        args = ["worker", "-Q", str(celery_app.conf.task_default_queue)]

    celery_app.start(args)


if __name__ == "__main__":
    main()

__all__ = [
    "CELERY_QUEUES",
    "CELERY_TASK_ROUTES",
    "DEFAULT_EXCHANGE",
    "DocFlowTask",
    "app",
    "celery",
    "celery_app",
    "create_celery_app",
    "main",
    "ping_worker",
]
