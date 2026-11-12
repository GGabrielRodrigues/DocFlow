from uuid import uuid4

from fastapi.testclient import TestClient

from docflow.core.config import Settings
from docflow.main import create_app


def test_upload_flow_never_sends_file_bytes_to_api() -> None:
    client = TestClient(create_app(Settings(database_url="sqlite:///:memory:")))
    institution_id = str(uuid4())
    headers = {"X-Institution-ID": institution_id}

    response = client.post(
        "/api/v1/media/uploads/init",
        headers=headers,
        json={
            "filename": "reuniao.mp4",
            "content_type": "video/mp4",
            "size_bytes": 60_000_000,
            "duration_seconds": 120,
        },
    )

    assert response.status_code == 201
    body = response.json()
    media_id = body["media_id"]

    presigned = client.post(
        f"/api/v1/media/{media_id}/uploads/presign-parts",
        headers=headers,
        json={"part_numbers": [1, 2]},
    )
    assert presigned.status_code == 200
    assert len(presigned.json()["parts"]) == 2

    completed = client.post(
        f"/api/v1/media/{media_id}/uploads/complete",
        headers=headers,
        json={
            "parts": [
                {"part_number": 1, "etag": "etag-1"},
                {"part_number": 2, "etag": "etag-2"},
            ]
        },
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "PROCESSING"


def test_upload_init_rejects_file_before_creating_session() -> None:
    client = TestClient(create_app(Settings(database_url="sqlite:///:memory:")))

    response = client.post(
        "/api/v1/media/uploads/init",
        headers={"X-Institution-ID": str(uuid4())},
        json={
            "filename": "reuniao.exe",
            "content_type": "application/octet-stream",
            "size_bytes": 100,
            "duration_seconds": 1,
        },
    )

    assert response.status_code == 422
    assert "formato" in response.json()["detail"]
