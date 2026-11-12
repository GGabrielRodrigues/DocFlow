from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from docflow.core.celery import (
    CELERY_QUEUES,
    CELERY_TASK_ROUTES,
    DocFlowTask,
    celery_app,
    create_celery_app,
    ping_worker,
)
from docflow.core.config import Settings
from docflow.worker import app as worker_app
from docflow.worker import celery as worker_celery
from docflow.worker import main as worker_main


def test_celery_queues_configuration() -> None:
    """Valida se as 3 filas específicas (io, cpu, ai) estão configuradas corretamente."""
    queue_names = {queue.name for queue in CELERY_QUEUES}
    assert queue_names == {"io", "cpu", "ai"}

    for queue in CELERY_QUEUES:
        assert queue.exchange.name == "docflow"
        assert queue.routing_key in {"io", "cpu", "ai"}
        assert queue.exchange.type == "direct"

    conf_queues = {q.name for q in celery_app.conf.task_queues}
    assert conf_queues == {"io", "cpu", "ai"}
    assert celery_app.conf.task_default_queue == "io"
    assert celery_app.conf.task_default_exchange == "docflow"
    assert celery_app.conf.task_default_routing_key == "io"


def test_celery_resilience_configuration() -> None:
    """Valida configurações de resiliência: acks_late, reject_on_worker_lost e prefetch."""
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.task_reject_on_worker_lost is True
    assert celery_app.conf.worker_prefetch_multiplier == 1
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert "json" in celery_app.conf.accept_content

    # DocFlowTask base
    assert DocFlowTask.acks_late is True
    assert DocFlowTask.reject_on_worker_lost is True
    assert DocFlowTask.retry_backoff is True
    assert DocFlowTask.retry_backoff_max == 600
    assert DocFlowTask.retry_jitter is True
    assert DocFlowTask.max_retries == 3

    # Anotações globais de tarefas
    annotations = celery_app.conf.task_annotations.get("*", {})
    assert annotations.get("retry_backoff") is True
    assert annotations.get("retry_backoff_max") == 600
    assert annotations.get("retry_jitter") is True
    assert annotations.get("max_retries") == 3
    assert annotations.get("acks_late") is True
    assert annotations.get("reject_on_worker_lost") is True


def test_celery_task_routes() -> None:
    """Valida mapeamento de rotas de tarefas para as filas designadas."""
    assert CELERY_TASK_ROUTES["docflow.worker.ping_worker"] == {"queue": "io"}
    assert CELERY_TASK_ROUTES["docflow.tasks.io.*"] == {"queue": "io"}
    assert CELERY_TASK_ROUTES["docflow.tasks.cpu.*"] == {"queue": "cpu"}
    assert CELERY_TASK_ROUTES["docflow.tasks.ai.*"] == {"queue": "ai"}


def test_celery_config_loading_from_settings() -> None:
    """Valida carregamento de configurações a partir do objeto Settings."""
    # 1. Configurações padrão
    default_settings = Settings()
    app_default = create_celery_app(default_settings)
    assert app_default.conf.broker_url == default_settings.redis_url
    assert app_default.conf.result_backend == default_settings.redis_url
    assert app_default.conf.task_default_queue == "io"

    # 2. Configurações customizadas de Redis
    custom_settings = Settings(
        redis_url="redis://custom-host:6380/2",
        celery_task_always_eager=True,
        celery_task_default_queue="cpu",
    )
    app_custom = create_celery_app(custom_settings)
    assert app_custom.conf.broker_url == "redis://custom-host:6380/2"
    assert app_custom.conf.result_backend == "redis://custom-host:6380/2"
    assert app_custom.conf.task_always_eager is True
    assert app_custom.conf.task_default_queue == "cpu"

    # 3. Overrides explícitos de broker e result backend
    override_settings = Settings(
        redis_url="redis://base-redis:6379/0",
        celery_broker_url="redis://broker-only:6379/1",
        celery_result_backend="redis://backend-only:6379/2",
    )
    app_override = create_celery_app(override_settings)
    assert app_override.conf.broker_url == "redis://broker-only:6379/1"
    assert app_override.conf.result_backend == "redis://backend-only:6379/2"


def test_celery_environment_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Garante que variáveis de ambiente como REDIS_URL sejam lidas corretamente."""
    monkeypatch.setenv("REDIS_URL", "redis://env-redis:6379/5")
    settings = Settings()
    assert settings.redis_url == "redis://env-redis:6379/5"

    app = create_celery_app(settings)
    assert app.conf.broker_url == "redis://env-redis:6379/5"
    assert app.conf.result_backend == "redis://env-redis:6379/5"


def test_ping_worker_eager_execution() -> None:
    """Valida execução síncrona/eager da task de healthcheck ping_worker."""
    app = create_celery_app(Settings(celery_task_always_eager=True))
    task = app.tasks["docflow.worker.ping_worker"]

    # Chamada padrão com argumento default
    async_res = task.delay()
    assert async_res.successful()
    result = async_res.get()
    assert result["status"] == "ok"
    assert result["message"] == "pong"
    assert result["task_id"] == async_res.id
    assert result["queue"] == "io"

    # Chamada com mensagem personalizada
    custom_res = task.apply_async(args=["healthcheck-ok"], queue="io")
    assert custom_res.successful()
    custom_data = custom_res.get()
    assert custom_data["status"] == "ok"
    assert custom_data["message"] == "healthcheck-ok"


def test_docflow_task_retry_mechanism() -> None:
    """Valida que o DocFlowTask aciona retentativa automática com backoff em caso de falha."""
    from celery.exceptions import Retry

    app = create_celery_app(Settings(celery_task_always_eager=True))

    attempts: list[int] = []

    @app.task(base=DocFlowTask, bind=True, max_retries=2, default_retry_delay=1)  # type: ignore[untyped-decorator]
    def flaky_task(self: DocFlowTask) -> str:
        attempts.append(1)
        raise ValueError("Falha transitória simulada")

    with pytest.raises(Retry) as exc_info:
        flaky_task.delay()

    assert "Falha transitória simulada" in str(exc_info.value)
    assert len(attempts) == 1


def test_worker_entrypoint_aliases() -> None:
    """Verifica que docflow.worker expõe os aliases esperados pelo Celery CLI."""
    assert worker_app is celery_app
    assert worker_celery is celery_app
    assert "docflow.worker.ping_worker" in worker_app.tasks
    assert ping_worker.name == "docflow.worker.ping_worker"


def test_worker_main_cli_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida que o entrypoint worker_main despacha os argumentos corretos."""
    mock_start = MagicMock()
    monkeypatch.setattr(celery_app, "start", mock_start)

    # Invocação sem argumentos específicos -> default worker com fila io
    worker_main([])
    mock_start.assert_called_with(["worker", "-Q", "io"])

    mock_start.reset_mock()
    # Invocação com argumentos explícitos (ex: celery worker -Q cpu)
    worker_main(["worker", "-Q", "cpu", "-l", "info"])
    mock_start.assert_called_with(["worker", "-Q", "cpu", "-l", "info"])


def test_worker_main_cli_default_sys_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valida execução de worker_main quando sys.argv não possui argumentos extras."""
    mock_start = MagicMock()
    monkeypatch.setattr(celery_app, "start", mock_start)
    monkeypatch.setattr("sys.argv", ["docflow-worker"])
    worker_main()
    mock_start.assert_called_with(["worker", "-Q", "io"])
