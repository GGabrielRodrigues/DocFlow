from pathlib import Path
from uuid import uuid4

from docflow.api.routers.auth import get_current_user
from docflow.core.celery import create_celery_app
from docflow.core.config import Settings
from docflow.domain.jobs import InvalidJobTransitionError, Job, JobState, JobType
from docflow.infra.database.models import Base, JobModel, UserModel
from docflow.infra.database.session import create_session_factory
from docflow.main import create_app


def test_job_state_machine_transitions() -> None:
    job = Job(
        id=uuid4(),
        institution_id=uuid4(),
        requested_by_id=uuid4(),
        type=JobType.TRANSCRIPTION,
        state=JobState.QUEUED,
        progress=0,
        error=None,
        attempts=1,
        resource_type="MEDIA",
        resource_id=uuid4(),
        idempotency_key="job-1",
        celery_task_id=None,
    )

    processing = job.transition(JobState.PROCESSING)
    completed = processing.transition(JobState.COMPLETED)
    assert completed.state == JobState.COMPLETED
    failed = processing.transition(JobState.FAILED)
    requeued = failed.transition(JobState.QUEUED)
    assert requeued.state == JobState.QUEUED

    try:
        completed.transition(JobState.PROCESSING)
    except InvalidJobTransitionError:
        pass
    else:
        raise AssertionError("Job concluído não pode voltar para processamento")


def test_job_create_status_idempotency_and_sse(tmp_path) -> None:
    from fastapi.testclient import TestClient

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
    database_path = tmp_path / "jobs.db"
    app = create_app(
        Settings(
            database_url=f"sqlite:///{database_path}",
            celery_task_always_eager=True,
        ),
        storage=None,
        celery_app=create_celery_app(
            Settings(
                database_url=f"sqlite:///{database_path}",
                celery_task_always_eager=True,
                celery_broker_url="memory://",
                celery_result_backend="cache+memory://",
            )
        ),
    )
    app.dependency_overrides[get_current_user] = lambda: author
    client = TestClient(app)

    init = client.post(
        "/api/v1/media/uploads/init",
        json={
            "filename": "reuniao.mp4",
            "content_type": "video/mp4",
            "size_bytes": 60_000_000,
            "duration_seconds": 120,
        },
    )
    assert init.status_code == 201
    media_id = init.json()["media_id"]

    created = client.post(
        "/api/v1/jobs",
        headers={"Idempotency-Key": "same-request"},
        json={"type": "TRANSCRIPTION", "media_id": media_id},
    )
    assert created.status_code == 202
    job = created.json()
    assert job["state"] == "COMPLETED"
    assert job["progress"] == 100
    assert job["attempts"] == 1

    repeated = client.post(
        "/api/v1/jobs",
        headers={"Idempotency-Key": "same-request"},
        json={"type": "TRANSCRIPTION", "media_id": media_id},
    )
    assert repeated.status_code == 202
    assert repeated.json()["id"] == job["id"]

    status_response = client.get(f"/api/v1/jobs/{job['id']}")
    assert status_response.status_code == 200
    assert status_response.json()["state"] == "COMPLETED"

    events = client.get(f"/api/v1/jobs/{job['id']}/events")
    assert events.status_code == 200
    assert "COMPLETED" in events.text


def test_job_cancel_list_and_reprocess(tmp_path: Path) -> None:
    from fastapi.testclient import TestClient

    institution_id = str(uuid4())
    user = UserModel(
        id=str(uuid4()),
        institution_id=institution_id,
        name="Autor",
        email="autor@example.com",
        password_hash="test",
        role="EMPLOYEE",
        status="ACTIVE",
    )
    job_id = str(uuid4())
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'cancel.db'}",
        celery_task_always_eager=True,
    )
    celery_app = create_celery_app(
        Settings(
            database_url=settings.database_url,
            celery_task_always_eager=True,
            celery_broker_url="memory://",
            celery_result_backend="cache+memory://",
        )
    )
    app = create_app(settings, storage=None, celery_app=celery_app)
    app.dependency_overrides[get_current_user] = lambda: user
    factory = create_session_factory(settings)
    Base.metadata.create_all(factory.kw["bind"])
    with factory() as db:
        db.add(
            JobModel(
                id=job_id,
                institution_id=institution_id,
                requested_by_id=user.id,
                type=JobType.TRANSCRIPTION.value,
                state=JobState.QUEUED.value,
                progress=0,
                error=None,
                attempts=1,
                resource_type="MEDIA",
                resource_id=str(uuid4()),
            )
        )
        db.commit()

    client = TestClient(app)
    canceled = client.post(f"/api/v1/jobs/{job_id}/cancel")
    assert canceled.status_code == 200
    assert canceled.json()["state"] == "CANCELED"

    reprocessed = client.post(f"/api/v1/jobs/{job_id}/retry")
    assert reprocessed.status_code == 200
    assert reprocessed.json()["state"] == "COMPLETED"

    listing = client.get("/api/v1/jobs")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


def test_job_worker_persists_failed_state_after_retries(
    tmp_path: Path,
    monkeypatch,
) -> None:
    institution_id = str(uuid4())
    job_id = str(uuid4())
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'failure.db'}",
        celery_task_always_eager=True,
    )
    celery_app = create_celery_app(
        Settings(
            database_url=settings.database_url,
            celery_task_always_eager=True,
            celery_broker_url="memory://",
            celery_result_backend="cache+memory://",
        )
    )
    factory = create_session_factory(settings)
    Base.metadata.create_all(factory.kw["bind"])
    with factory() as db:
        db.add(
            JobModel(
                id=job_id,
                institution_id=institution_id,
                requested_by_id=str(uuid4()),
                type=JobType.TRANSCRIPTION.value,
                state=JobState.QUEUED.value,
                progress=0,
                error=None,
                attempts=1,
                resource_type="MEDIA",
                resource_id=str(uuid4()),
            )
        )
        db.commit()

    import docflow.tasks.jobs as jobs_task

    def fail_progress(*args, **kwargs):
        raise RuntimeError("provedor indisponível")

    monkeypatch.setattr(jobs_task, "_advance_job", fail_progress)
    monkeypatch.setattr(jobs_task, "_notify_job_result", lambda *args, **kwargs: None)

    task = celery_app.tasks["docflow.tasks.jobs.run"]
    task.push_request(retries=3, id="failure-test", is_eager=True)
    try:
        task.run(job_id, institution_id)
    finally:
        task.pop_request()

    with factory() as db:
        job = db.get(JobModel, job_id)
        assert job is not None
        assert job.state == JobState.FAILED.value
        assert job.error == "provedor indisponível"
