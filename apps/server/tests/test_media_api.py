from uuid import uuid4

from fastapi.testclient import TestClient

from docflow.api.routers.auth import get_current_user
from docflow.core.config import Settings
from docflow.infra.database.models import UserModel
from docflow.main import create_app


def test_upload_flow_never_sends_file_bytes_to_api() -> None:
    institution_id = str(uuid4())
    author = UserModel(
        id=str(uuid4()),
        institution_id=institution_id,
        name="Autor",
        email="autor@example.com",
        password_hash="test",
        role="EMPLOYEE",
        status="ACTIVE",
    )
    app = create_app(Settings(database_url="sqlite:///:memory:"))
    app.dependency_overrides[get_current_user] = lambda: author
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token"}

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
    app = create_app(Settings(database_url="sqlite:///:memory:"))
    institution_id = str(uuid4())
    app.dependency_overrides[get_current_user] = lambda: UserModel(
        id=str(uuid4()),
        institution_id=institution_id,
        name="Autor",
        email="autor@example.com",
        password_hash="test",
        role="EMPLOYEE",
        status="ACTIVE",
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/media/uploads/init",
        headers={"Authorization": "Bearer test-token"},
        json={
            "filename": "reuniao.exe",
            "content_type": "application/octet-stream",
            "size_bytes": 100,
            "duration_seconds": 1,
        },
    )

    assert response.status_code == 422
    assert "formato" in response.json()["detail"]


def test_media_endpoints_require_authentication() -> None:
    client = TestClient(create_app(Settings(database_url="sqlite:///:memory:")))

    response = client.get("/api/v1/media")

    assert response.status_code == 401


def test_media_detail_delete_and_author_access() -> None:
    from docflow.infra.storage import InMemoryObjectStorage

    storage = InMemoryObjectStorage()
    institution_id = str(uuid4())
    author_id = str(uuid4())
    author = UserModel(
        id=author_id,
        institution_id=institution_id,
        name="Autor",
        email="autor@example.com",
        password_hash="test",
        role="EMPLOYEE",
        status="ACTIVE",
    )
    app = create_app(
        Settings(database_url="sqlite:///:memory:", jwt_secret_key="test-secret"),
        storage=storage,
    )
    app.dependency_overrides[get_current_user] = lambda: author
    client = TestClient(app)
    headers = {"Authorization": "Bearer test-token"}

    init = client.post(
        "/api/v1/media/uploads/init",
        headers=headers,
        json={
            "filename": "reuniao.mp4",
            "content_type": "video/mp4",
            "size_bytes": 60_000_000,
            "duration_seconds": 120,
        },
    )
    assert init.status_code == 201
    media_id = init.json()["media_id"]

    parts = client.post(
        f"/api/v1/media/{media_id}/uploads/presign-parts",
        headers=headers,
        json={"part_numbers": [1, 2]},
    )
    assert parts.status_code == 200

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

    detail = client.get(f"/api/v1/media/{media_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["author_id"] == author_id
    assert detail.json()["preview_url"].startswith("memory://")
    assert detail.json()["download_url"].startswith("memory://")
    assert detail.json()["expires_in"] == 900

    listing = client.get("/api/v1/media", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    denied = client.get(
        f"/api/v1/media/{media_id}",
        headers=headers,
    )
    app.dependency_overrides[get_current_user] = lambda: UserModel(
        id=str(uuid4()),
        institution_id=institution_id,
        name="Outro usuário",
        email="outro@example.com",
        password_hash="test",
        role="EMPLOYEE",
        status="ACTIVE",
    )
    denied = client.get(f"/api/v1/media/{media_id}", headers=headers)
    assert denied.status_code == 403

    app.dependency_overrides[get_current_user] = lambda: author
    shared_user_id = str(uuid4())
    app.dependency_overrides[get_current_user] = lambda: author
    shared = client.post(
        f"/api/v1/media/{media_id}/shares",
        headers=headers,
        json={"user_id": shared_user_id},
    )
    assert shared.status_code == 404

    app.dependency_overrides[get_current_user] = lambda: author

    deleted = client.delete(f"/api/v1/media/{media_id}", headers=headers)
    assert deleted.status_code == 204

    removed = client.get(f"/api/v1/media/{media_id}", headers=headers)
    assert removed.status_code == 404
