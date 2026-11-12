from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, sessionmaker

from docflow.application.media import MediaUploadService
from docflow.domain.media import MediaValidationError, UploadRequest
from docflow.infra.database.models import MediaModel


class UploadInitRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    size_bytes: int = Field(gt=0)
    duration_seconds: int = Field(gt=0)


class UploadInitResponse(BaseModel):
    media_id: UUID
    upload_id: str
    part_size: int
    total_parts: int
    status: str


class PresignPartsRequest(BaseModel):
    part_numbers: list[int] = Field(min_length=1, max_length=10000)


class PresignPartsResponse(BaseModel):
    parts: list[dict[str, object]]


class CompleteUploadRequest(BaseModel):
    parts: list[dict[str, object]] = Field(min_length=1, max_length=10000)


class UploadStatusResponse(BaseModel):
    media_id: UUID
    status: str


def create_media_router(
    session_factory: sessionmaker[Session], upload_service: MediaUploadService
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/media", tags=["media"])

    def tenant(value: str) -> UUID:
        try:
            return UUID(value)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant inválido") from error

    @router.post("/uploads/init", response_model=UploadInitResponse, status_code=status.HTTP_201_CREATED)
    async def init_upload(
        payload: UploadInitRequest,
        x_institution_id: str = Header(..., alias="X-Institution-ID"),
    ) -> UploadInitResponse:
        try:
            request = UploadRequest.create(**payload.model_dump())
            session = upload_service.start(tenant(x_institution_id), request)
        except MediaValidationError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        with session_factory() as db:
            db.add(
                MediaModel(
                    id=str(session.media_id),
                    institution_id=str(session.institution_id),
                    original_filename=request.filename,
                    content_type=request.content_type,
                    size_bytes=request.size_bytes,
                    declared_duration_seconds=request.duration_seconds,
                    storage_bucket=upload_service.bucket,
                    storage_key=session.key,
                    multipart_upload_id=session.upload_id,
                    status=session.status,
                )
            )
            db.commit()
        return UploadInitResponse(
            media_id=session.media_id,
            upload_id=session.upload_id,
            part_size=50 * 1024 * 1024,
            total_parts=request.total_parts,
            status=session.status,
        )

    @router.post("/{media_id}/uploads/presign-parts", response_model=PresignPartsResponse)
    async def presign_parts(
        media_id: UUID,
        payload: PresignPartsRequest,
        x_institution_id: str = Header(..., alias="X-Institution-ID"),
    ) -> PresignPartsResponse:
        session = upload_service.sessions.get(media_id)
        if session is None or session.institution_id != tenant(x_institution_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload não encontrado")
        if any(part < 1 or part > session.request.total_parts for part in payload.part_numbers):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Parte inválida")
        return PresignPartsResponse(parts=upload_service.presign_parts(media_id, payload.part_numbers))

    @router.post("/{media_id}/uploads/complete", response_model=UploadStatusResponse)
    async def complete_upload(
        media_id: UUID,
        payload: CompleteUploadRequest,
        x_institution_id: str = Header(..., alias="X-Institution-ID"),
    ) -> UploadStatusResponse:
        session = upload_service.sessions.get(media_id)
        if session is None or session.institution_id != tenant(x_institution_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload não encontrado")
        try:
            completed = upload_service.complete(media_id, payload.parts)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        with session_factory() as db:
            media = db.get(MediaModel, str(media_id))
            if media is not None:
                media.status = completed.status
                db.commit()
        return UploadStatusResponse(media_id=media_id, status=completed.status)

    @router.post("/{media_id}/uploads/abort", status_code=status.HTTP_204_NO_CONTENT)
    async def abort_upload(
        media_id: UUID,
        x_institution_id: str = Header(..., alias="X-Institution-ID"),
    ) -> None:
        session = upload_service.sessions.get(media_id)
        if session is None or session.institution_id != tenant(x_institution_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload não encontrado")
        upload_service.abort(media_id)
        with session_factory() as db:
            media = db.get(MediaModel, str(media_id))
            if media is not None:
                media.status = "CANCELED"
                db.commit()

    return router
