from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class JobType(StrEnum):
    METADATA_EXTRACTION = "METADATA_EXTRACTION"
    VIDEO_COMPRESSION = "VIDEO_COMPRESSION"
    TRANSCRIPTION = "TRANSCRIPTION"
    DOCUMENT_GENERATION = "DOCUMENT_GENERATION"
    DOCUMENT_REVIEW = "DOCUMENT_REVIEW"
    DOCUMENT_EXPORT = "DOCUMENT_EXPORT"


class JobState(StrEnum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class InvalidJobTransitionError(ValueError):
    pass


TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    JobState.QUEUED: frozenset({JobState.PROCESSING, JobState.CANCELED}),
    JobState.PROCESSING: frozenset(
        {JobState.PROCESSING, JobState.COMPLETED, JobState.FAILED, JobState.QUEUED, JobState.CANCELED}
    ),
    JobState.COMPLETED: frozenset(),
    JobState.FAILED: frozenset({JobState.QUEUED}),
    JobState.CANCELED: frozenset({JobState.QUEUED}),
}


@dataclass(frozen=True, slots=True)
class Job:
    id: UUID
    institution_id: UUID
    requested_by_id: UUID
    type: JobType
    state: JobState
    progress: int
    error: str | None
    attempts: int
    resource_type: str
    resource_id: UUID
    idempotency_key: str | None
    celery_task_id: str | None

    def transition(self, new_state: JobState) -> Job:
        if new_state not in TRANSITIONS[self.state]:
            raise InvalidJobTransitionError(
                f"Transição de job inválida: {self.state.value} -> {new_state.value}"
            )
        if new_state == JobState.PROCESSING and self.progress > 0:
            progress = self.progress
        else:
            progress = self.progress
        return Job(
            id=self.id,
            institution_id=self.institution_id,
            requested_by_id=self.requested_by_id,
            type=self.type,
            state=new_state,
            progress=progress,
            error=self.error,
            attempts=self.attempts,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            idempotency_key=self.idempotency_key,
            celery_task_id=self.celery_task_id,
        )

    def with_progress(self, progress: int) -> Job:
        if progress < 0 or progress > 100:
            raise ValueError("O progresso do job deve estar entre 0 e 100")
        return Job(
            id=self.id,
            institution_id=self.institution_id,
            requested_by_id=self.requested_by_id,
            type=self.type,
            state=self.state,
            progress=progress,
            error=self.error,
            attempts=self.attempts,
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            idempotency_key=self.idempotency_key,
            celery_task_id=self.celery_task_id,
        )

    def with_error(self, error: str, attempts: int) -> Job:
        return Job(
            id=self.id,
            institution_id=self.institution_id,
            requested_by_id=self.requested_by_id,
            type=self.type,
            state=self.state,
            progress=self.progress,
            error=error[:2000],
            attempts=max(1, attempts),
            resource_type=self.resource_type,
            resource_id=self.resource_id,
            idempotency_key=self.idempotency_key,
            celery_task_id=self.celery_task_id,
        )
