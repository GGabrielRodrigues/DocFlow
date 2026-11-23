from __future__ import annotations

import asyncio
import json
from datetime import datetime
from uuid import UUID, uuid4

from celery import Celery
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from docflow.api.routers.auth import get_current_user
from docflow.domain.jobs import JobState, JobType
from docflow.infra.database.models import JobModel, MediaModel, UserModel


class CreateJobRequest(BaseModel):
    type: JobType
    media_id: UUID


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_id: UUID
    type: JobType
    state: JobState
    progress: int
    progress_percent: int
    error: str | None
    attempts: int
    resource_type: str
    resource_id: UUID
    celery_task_id: str | None
    created_at: datetime
    updated_at: datetime


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int


def create_jobs_router(
    session_factory: sessionmaker[Session],
    celery_app: Celery,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

    def get_tenant_job(db: Session, job_id: UUID, institution_id: str) -> JobModel:
        job = db.scalar(
            select(JobModel).where(
                JobModel.id == str(job_id),
                JobModel.institution_id == institution_id,
            )
        )
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job não encontrado")
        return job

    def to_response(job: JobModel) -> JobResponse:
        return JobResponse(
            id=UUID(job.id),
            institution_id=UUID(job.institution_id),
            type=JobType(job.type),
            state=JobState(job.state),
            progress=job.progress,
            progress_percent=job.progress,
            error=job.error,
            attempts=job.attempts,
            resource_type=job.resource_type,
            resource_id=UUID(job.resource_id),
            celery_task_id=job.celery_task_id,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    def publish(job: JobModel) -> str:
        task = celery_app.tasks["docflow.tasks.jobs.run"]
        result = task.apply_async(args=[job.id, job.institution_id])
        job.celery_task_id = result.id
        return result.id

    @router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
    async def create_job(
        payload: CreateJobRequest,
        current_user: UserModel = Depends(get_current_user),
        idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    ) -> JobResponse:
        institution_id = current_user.institution_id
        with session_factory() as db:
            media = db.scalar(
                select(MediaModel).where(
                    MediaModel.id == str(payload.media_id),
                    MediaModel.institution_id == institution_id,
                )
            )
            if media is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mídia não encontrada")

            existing: JobModel | None = None
            if idempotency_key:
                existing = db.scalar(
                    select(JobModel).where(
                        JobModel.institution_id == institution_id,
                        JobModel.idempotency_key == idempotency_key,
                    )
                )
                if existing is not None and (
                    existing.type != payload.type.value
                    or existing.resource_id != str(payload.media_id)
                ):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Chave de idempotência já utilizada para outro job",
                    )
            if existing is None:
                existing = db.scalar(
                    select(JobModel)
                    .where(
                        JobModel.institution_id == institution_id,
                        JobModel.type == payload.type.value,
                        JobModel.resource_type == "MEDIA",
                        JobModel.resource_id == str(payload.media_id),
                        JobModel.state.in_(("QUEUED", "PROCESSING", "COMPLETED")),
                    )
                    .order_by(JobModel.created_at.desc())
                )
            if existing is not None:
                return to_response(existing)

            job = JobModel(
                id=str(uuid4()),
                institution_id=institution_id,
                requested_by_id=current_user.id,
                type=payload.type.value,
                state=JobState.QUEUED.value,
                progress=0,
                error=None,
                attempts=1,
                resource_type="MEDIA",
                resource_id=str(payload.media_id),
                idempotency_key=idempotency_key,
            )
            db.add(job)
            try:
                db.commit()
            except IntegrityError as conflict:
                db.rollback()
                if idempotency_key:
                    existing = db.scalar(
                        select(JobModel).where(
                            JobModel.institution_id == institution_id,
                            JobModel.idempotency_key == idempotency_key,
                        )
                    )
                    if existing is not None:
                        return to_response(existing)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Não foi possível criar o job por conflito de idempotência",
                ) from conflict
            db.refresh(job)
            publish(job)
            db.commit()
            db.refresh(job)
            return to_response(job)

    @router.get("", response_model=JobListResponse)
    async def list_jobs(
        current_user: UserModel = Depends(get_current_user),
        state: JobState | None = None,
        job_type: JobType | None = None,
        media_id: UUID | None = None,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> JobListResponse:
        with session_factory() as db:
            stmt = select(JobModel).where(
                JobModel.institution_id == current_user.institution_id
            )
            if state is not None:
                stmt = stmt.where(JobModel.state == state.value)
            if job_type is not None:
                stmt = stmt.where(JobModel.type == job_type.value)
            if media_id is not None:
                stmt = stmt.where(
                    JobModel.resource_type == "MEDIA",
                    JobModel.resource_id == str(media_id),
                )
            count_stmt = select(JobModel.id).where(
                JobModel.institution_id == current_user.institution_id
            )
            if state is not None:
                count_stmt = count_stmt.where(JobModel.state == state.value)
            if job_type is not None:
                count_stmt = count_stmt.where(JobModel.type == job_type.value)
            if media_id is not None:
                count_stmt = count_stmt.where(
                    JobModel.resource_type == "MEDIA",
                    JobModel.resource_id == str(media_id),
                )
            jobs = list(
                db.scalars(
                    stmt.order_by(JobModel.created_at.desc()).offset(offset).limit(limit)
                ).all()
            )
            total = db.scalar(select(func.count()).select_from(count_stmt.subquery())) or 0
            return JobListResponse(
                items=[to_response(job) for job in jobs],
                total=total,
            )

    @router.get("/{job_id}", response_model=JobResponse)
    async def get_job(
        job_id: UUID,
        current_user: UserModel = Depends(get_current_user),
    ) -> JobResponse:
        with session_factory() as db:
            return to_response(get_tenant_job(db, job_id, current_user.institution_id))

    @router.post("/{job_id}/cancel", response_model=JobResponse)
    async def cancel_job(
        job_id: UUID,
        current_user: UserModel = Depends(get_current_user),
    ) -> JobResponse:
        with session_factory() as db:
            job = get_tenant_job(db, job_id, current_user.institution_id)
            if job.state not in (JobState.QUEUED.value, JobState.PROCESSING.value):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Job {job.state} não pode ser cancelado",
                )
            job.state = JobState.CANCELED.value
            job.error = None
            if job.celery_task_id:
                celery_app.control.revoke(job.celery_task_id, terminate=True)
            db.commit()
            db.refresh(job)
            return to_response(job)

    @router.post("/{job_id}/reprocess", response_model=JobResponse)
    async def reprocess_job(
        job_id: UUID,
        current_user: UserModel = Depends(get_current_user),
    ) -> JobResponse:
        with session_factory() as db:
            job = get_tenant_job(db, job_id, current_user.institution_id)
            if job.state not in (
                JobState.FAILED.value,
                JobState.CANCELED.value,
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Job {job.state} não pode ser reprocessado",
                )
            job.state = JobState.QUEUED.value
            job.progress = 0
            job.error = None
            job.attempts += 1
            job.celery_task_id = None
            db.commit()
            db.refresh(job)
            publish(job)
            db.commit()
            db.refresh(job)
            return to_response(job)

    @router.post("/{job_id}/retry", response_model=JobResponse)
    async def retry_job(
        job_id: UUID,
        current_user: UserModel = Depends(get_current_user),
    ) -> JobResponse:
        return await reprocess_job(job_id, current_user)

    @router.get("/{job_id}/events")
    async def job_events(
        job_id: UUID,
        current_user: UserModel = Depends(get_current_user),
    ) -> StreamingResponse:
        async def stream():
            last_snapshot: tuple[str, int] | None = None
            for _ in range(300):
                with session_factory() as db:
                    job = get_tenant_job(db, job_id, current_user.institution_id)
                    snapshot = (job.state, job.progress)
                    if snapshot != last_snapshot:
                        data = {
                            "id": job.id,
                            "state": job.state,
                            "progress": job.progress,
                            "progress_percent": job.progress,
                            "error": job.error,
                            "attempts": job.attempts,
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                        last_snapshot = snapshot
                    if job.state in (
                        JobState.COMPLETED.value,
                        JobState.FAILED.value,
                        JobState.CANCELED.value,
                    ):
                        yield "event: close\ndata: {}\n\n"
                        return
                await asyncio.sleep(1)

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return router
