from __future__ import annotations

import logging
from typing import Any

from celery import Task

from docflow.application.email_service import EmailNotificationService
from docflow.core.config import Settings
from docflow.infra.database.models import JobModel, UserModel
from docflow.infra.database.session import create_session_factory
from docflow.infra.email.smtp import SMTPEmailSender

logger = logging.getLogger("docflow.jobs")


def _notify_job_result(
    settings: Settings,
    session_factory: Any,
    job: JobModel,
    is_success: bool,
) -> None:
    with session_factory() as db:
        user = db.get(UserModel, job.requested_by_id)
    if user is None:
        return
    try:
        service = EmailNotificationService(sender=SMTPEmailSender(settings))
        service.send_job_completed_sync(
            recipient_email=user.email,
            recipient_name=user.name,
            job_title=f"{job.resource_type} {job.resource_id}",
            job_type=job.type,
            status="Concluído" if is_success else "Falhou",
            is_success=is_success,
            error_message=None if is_success else job.error,
        )
    except Exception as exc:
        logger.warning(
            "Falha ao enviar notificação do job %s: %s",
            job.id,
            exc,
        )


def _advance_job(
    session_factory: Any,
    job_id: str,
    institution_id: str,
    progress: int,
) -> JobModel | None:
    with session_factory() as db:
        job = db.get(JobModel, job_id)
        if job is None or job.institution_id != institution_id:
            return None
        if job.state == "CANCELED":
            return job
        if job.state == "COMPLETED":
            return job
        job.progress = progress
        if progress == 100:
            job.state = "COMPLETED"
        db.commit()
        return job


def run_job_impl(self: Task, job_id: str, institution_id: str) -> dict[str, Any]:
    database_url = str(self.app.conf.docflow_database_url)
    settings = Settings(database_url=database_url)
    session_factory = create_session_factory(settings)
    with session_factory() as db:
        job = db.get(JobModel, job_id)
        if job is None or job.institution_id != institution_id:
            return {"job_id": job_id, "status": "not_found"}
        if job.state == "CANCELED":
            return {"job_id": job_id, "status": "canceled"}
        if job.state == "COMPLETED":
            return {"job_id": job_id, "status": "completed", "progress": 100}
        if job.state == "FAILED":
            return {"job_id": job_id, "status": "failed"}
        job.state = "PROCESSING"
        job.error = None
        job.attempts = max(job.attempts, 1)
        db.commit()

    try:
        for progress in (25, 50, 75, 100):
            job = _advance_job(session_factory, job_id, institution_id, progress)
            if job is None:
                return {"job_id": job_id, "status": "not_found"}
            if job.state == "CANCELED":
                return {"job_id": job_id, "status": "canceled"}
            if progress == 100 and job.state == "COMPLETED":
                completed_job = job
            self.update_state(
                task_id=self.request.id,
                state="PROGRESS",
                meta={"progress": progress},
            )
        _notify_job_result(settings, session_factory, completed_job, is_success=True)
        return {"job_id": job_id, "status": "completed", "progress": 100}
    except Exception as exc:
        retry_number = int(getattr(self.request, "retries", 0))
        with session_factory() as db:
            job = db.get(JobModel, job_id)
            if job is None or job.institution_id != institution_id:
                return {"job_id": job_id, "status": "not_found"}
            if job.state == "CANCELED":
                return {"job_id": job_id, "status": "canceled"}
            job.attempts = max(job.attempts, retry_number + 1)
            if retry_number >= 3:
                job.state = "FAILED"
                job.error = str(exc)[:2000]
                db.commit()
                _notify_job_result(settings, session_factory, job, is_success=False)
                return {"job_id": job_id, "status": "failed", "error": str(exc)}
            job.state = "QUEUED"
            job.error = str(exc)[:2000]
            db.commit()
        raise self.retry(
            exc=exc,
            countdown=min(30 * (2**retry_number), 600),
        ) from exc
