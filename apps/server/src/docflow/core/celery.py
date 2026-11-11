from __future__ import annotations

from typing import Any

from celery import Celery, Task
from kombu.entity import Exchange, Queue

from docflow.core.config import Settings, get_settings


class DocFlowTask(Task):  # type: ignore[misc]
    """Base Task para o DocFlow com resiliência por padrão.

    Configura acks_late, reject_on_worker_lost e retentativas automáticas
    com backoff exponencial.
    """

    acks_late: bool = True
    reject_on_worker_lost: bool = True
    autoretry_for: tuple[type[Exception], ...] = (Exception,)
    retry_backoff: bool = True
    retry_backoff_max: int = 600
    retry_jitter: bool = True
    max_retries: int = 3


DEFAULT_EXCHANGE = Exchange("docflow", type="direct")

CELERY_QUEUES: tuple[Queue, ...] = (
    Queue("io", DEFAULT_EXCHANGE, routing_key="io"),
    Queue("cpu", DEFAULT_EXCHANGE, routing_key="cpu"),
    Queue("ai", DEFAULT_EXCHANGE, routing_key="ai"),
)

CELERY_TASK_ROUTES: dict[str, dict[str, str]] = {
    "docflow.worker.ping_worker": {"queue": "io"},
    "docflow.tasks.io.*": {"queue": "io"},
    "docflow.tasks.cpu.*": {"queue": "cpu"},
    "docflow.tasks.ai.*": {"queue": "ai"},
}


def _ping_worker_impl(self: Task, message: str = "pong") -> dict[str, Any]:
    delivery_info = getattr(self.request, "delivery_info", None) or {}
    routing_key = delivery_info.get("routing_key") or "io"
    return {
        "status": "ok",
        "message": message,
        "task_id": self.request.id,
        "queue": routing_key,
    }


def create_celery_app(settings: Settings | None = None) -> Celery:
    """Cria e configura uma instância do Celery App para o DocFlow."""
    cfg = settings or get_settings()
    app = Celery("docflow")

    broker = cfg.celery_broker_url or cfg.redis_url
    backend = cfg.celery_result_backend or cfg.redis_url

    app.conf.update(
        broker_url=broker,
        result_backend=backend,
        task_always_eager=cfg.celery_task_always_eager,
        task_eager_propagates=True,
        task_queues=CELERY_QUEUES,
        task_default_queue=cfg.celery_task_default_queue,
        task_default_exchange="docflow",
        task_default_routing_key=cfg.celery_task_default_queue,
        task_routes=CELERY_TASK_ROUTES,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        worker_prefetch_multiplier=1,
        broker_transport_options={"visibility_timeout": 14400},
        result_backend_transport_options={"visibility_timeout": 14400},
        result_expires=86400,
        task_annotations={
            "*": {
                "retry_backoff": True,
                "retry_backoff_max": 600,
                "retry_jitter": True,
                "max_retries": 3,
                "acks_late": True,
                "reject_on_worker_lost": True,
            }
        },
    )

    register_tasks(app)
    return app


def register_tasks(app: Celery) -> None:
    """Registra as tarefas padrão do sistema no Celery App."""
    app.task(
        _ping_worker_impl,
        name="docflow.worker.ping_worker",
        base=DocFlowTask,
        bind=True,
    )


celery_app: Celery = create_celery_app()
ping_worker: Task = celery_app.tasks["docflow.worker.ping_worker"]

__all__ = [
    "CELERY_QUEUES",
    "CELERY_TASK_ROUTES",
    "DEFAULT_EXCHANGE",
    "DocFlowTask",
    "celery_app",
    "create_celery_app",
    "ping_worker",
    "register_tasks",
]
