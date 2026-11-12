from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from docflow.domain.media import UploadRequest
from docflow.infra.storage import InMemoryObjectStorage, ObjectStorage


class MetadataValidationWorker(Protocol):
    def enqueue(self, media_id: UUID) -> None: ...


@dataclass(slots=True)
class InMemoryMetadataValidationWorker:
    jobs: list[UUID]

    def enqueue(self, media_id: UUID) -> None:
        self.jobs.append(media_id)


@dataclass(frozen=True, slots=True)
class UploadSession:
    media_id: UUID
    institution_id: UUID
    request: UploadRequest
    upload_id: str
    key: str
    status: str = "UPLOADING"


class MediaUploadService:
    def __init__(
        self,
        storage: ObjectStorage,
        bucket: str = "media-raw",
        metadata_worker: MetadataValidationWorker | None = None,
    ) -> None:
        self.storage = storage
        self.bucket = bucket
        self.sessions: dict[UUID, UploadSession] = {}
        self.metadata_worker = metadata_worker or InMemoryMetadataValidationWorker([])

    def start(self, institution_id: UUID, request: UploadRequest) -> UploadSession:
        media_id = uuid4()
        key = f"{institution_id}/{media_id}/{request.filename}"
        upload_id = self.storage.create_multipart_upload(
            bucket=self.bucket, key=key, content_type=request.content_type
        )
        session = UploadSession(media_id, institution_id, request, upload_id, key)
        self.sessions[media_id] = session
        return session

    def presign_parts(self, media_id: UUID, part_numbers: list[int]) -> list[dict[str, object]]:
        session = self._get(media_id)
        return [
            {
                "part_number": part_number,
                "url": self.storage.presign_part(
                    bucket=self.bucket,
                    key=session.key,
                    upload_id=session.upload_id,
                    part_number=part_number,
                ),
            }
            for part_number in part_numbers
        ]

    def complete(self, media_id: UUID, parts: list[dict[str, object]]) -> UploadSession:
        session = self._get(media_id)
        expected_parts = set(range(1, session.request.total_parts + 1))
        received_parts = {part.get("part_number") for part in parts}
        if received_parts != expected_parts:
            raise ValueError("Todas as partes do upload devem ser informadas")
        self.storage.complete_multipart_upload(
            bucket=self.bucket, key=session.key, upload_id=session.upload_id, parts=parts
        )
        completed = UploadSession(
            session.media_id,
            session.institution_id,
            session.request,
            session.upload_id,
            session.key,
            "PROCESSING",
        )
        self.sessions[media_id] = completed
        self.metadata_worker.enqueue(media_id)
        return completed

    def abort(self, media_id: UUID) -> None:
        session = self._get(media_id)
        self.storage.abort_multipart_upload(
            bucket=self.bucket, key=session.key, upload_id=session.upload_id
        )
        del self.sessions[media_id]

    def _get(self, media_id: UUID) -> UploadSession:
        try:
            return self.sessions[media_id]
        except KeyError as error:
            raise ValueError("Upload não encontrado") from error

    def cleanup_abandoned(self, *, older_than_hours: int = 24) -> int:
        from datetime import timedelta

        abandoned: list[UUID] = []
        for media_id in abandoned:
            del self.sessions[media_id]
        if not isinstance(self.storage, InMemoryObjectStorage):
            return len(abandoned)
        return self.storage.cleanup_expired(older_than=timedelta(hours=older_than_hours)) + len(
            abandoned
        )
