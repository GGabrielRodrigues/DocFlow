from fastapi.testclient import TestClient

from docflow.core.config import Settings
from docflow.main import create_app

client = TestClient(create_app())


def test_health_returns_liveness_and_request_id() -> None:
    response = client.get("/health", headers={"X-Request-ID": "req-test"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "docflow-api"}
    assert response.headers["X-Request-ID"] == "req-test"


def test_ready_reports_unconfigured_dependencies() -> None:
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["postgres"] == "not_configured"


def test_custom_settings_are_used_by_health_router() -> None:
    response = TestClient(create_app(Settings(app_name="custom-service"))).get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "custom-service"


def test_invalid_request_id_is_replaced() -> None:
    response = client.get("/health", headers={"X-Request-ID": " " * 129})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != " " * 129
    assert len(response.headers["X-Request-ID"]) == 32


def test_http_log_contains_request_id_and_response_metadata(caplog) -> None:
    with caplog.at_level("INFO", logger="docflow.http"):
        response = client.get("/health", headers={"X-Request-ID": "req-log"})

    record = next(record for record in caplog.records if record.name == "docflow.http")
    assert response.status_code == 200
    assert record.event == "http_request_completed"
    assert record.request_id == "req-log"
    assert record.method == "GET"
    assert record.path == "/health"
    assert record.status_code == 200
    assert record.duration_ms >= 0
