from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from docflow.api.routers.auth import get_current_user
from docflow.application.media import MediaUploadService
from docflow.domain.media import MediaValidationError, UploadRequest
from docflow.infra.database.models import MediaModel, MediaShareModel, UserModel
from docflow.infra.storage import StorageError


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


class MediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    institution_id: UUID
    author_id: UUID | None = None
    original_filename: str
    content_type: str
    size_bytes: int
    declared_duration_seconds: int
    status: str


class MediaDetailResponse(MediaResponse):
    preview_url: str
    download_url: str
    expires_in: int


class MediaListResponse(BaseModel):
    items: list[MediaResponse]
    total: int


class MediaShareRequest(BaseModel):
    user_id: UUID


class MediaShareResponse(BaseModel):
    media_id: UUID
    user_id: UUID


def create_media_router(
    session_factory: sessionmaker[Session],
    upload_service: MediaUploadService,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/media", tags=["media"])

    def can_access(
        db: Session,
        media: MediaModel,
        institution_id: UUID,
        user_id: str | None,
        user_role: str | None,
    ) -> bool:
        if media.institution_id != str(institution_id):
            return False
        if user_role and user_role.upper() == "ADMIN":
            return True
        if user_id and media.author_id == user_id:
            return True
        if user_id:
            share = db.scalar(
                select(MediaShareModel).where(
                    MediaShareModel.media_id == media.id,
                    MediaShareModel.user_id == user_id,
                )
            )
            return share is not None
        return False

    def forbidden() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso à mídia negado",
        )

    def can_manage(media: MediaModel, current_user: UserModel) -> bool:
        return (
            media.institution_id == current_user.institution_id
            and (
                media.author_id == current_user.id
                or current_user.role.upper() == "ADMIN"
            )
        )

    @router.post("/uploads/init", response_model=UploadInitResponse, status_code=status.HTTP_201_CREATED)
    async def init_upload(
        payload: UploadInitRequest,
        current_user: UserModel = Depends(get_current_user),
    ) -> UploadInitResponse:
        try:
            request = UploadRequest.create(**payload.model_dump())
            institution_id = UUID(current_user.institution_id)
            session = upload_service.start(institution_id, request)
        except MediaValidationError as error:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
        with session_factory() as db:
            db.add(
                MediaModel(
                    id=str(session.media_id),
                    institution_id=str(session.institution_id),
                    author_id=current_user.id,
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
        current_user: UserModel = Depends(get_current_user),
    ) -> PresignPartsResponse:
        session = upload_service.sessions.get(media_id)
        if session is None or session.institution_id != UUID(current_user.institution_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload não encontrado")
        if any(part < 1 or part > session.request.total_parts for part in payload.part_numbers):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Parte inválida")
        return PresignPartsResponse(parts=upload_service.presign_parts(media_id, payload.part_numbers))

    @router.post("/{media_id}/uploads/complete", response_model=UploadStatusResponse)
    async def complete_upload(
        media_id: UUID,
        payload: CompleteUploadRequest,
        current_user: UserModel = Depends(get_current_user),
    ) -> UploadStatusResponse:
        session = upload_service.sessions.get(media_id)
        if session is None or session.institution_id != UUID(current_user.institution_id):
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

    @router.get("", response_model=MediaListResponse)
    async def list_media(
        current_user: UserModel = Depends(get_current_user),
        status_filter: str | None = None,
        content_type: str | None = None,
        search: str | None = None,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> MediaListResponse:
        institution_id = UUID(current_user.institution_id)
        with session_factory() as db:
            stmt = select(MediaModel).where(MediaModel.institution_id == str(institution_id))
            if status_filter:
                stmt = stmt.where(MediaModel.status == status_filter)
            if content_type:
                stmt = stmt.where(MediaModel.content_type.startswith(content_type))
            if search:
                stmt = stmt.where(MediaModel.original_filename.ilike(f"%{search}%"))
            all_media = list(db.scalars(stmt).all())
            visible = [
                media
                for media in all_media
                if can_access(db, media, institution_id, current_user.id, current_user.role)
            ]
            paged = visible[offset : offset + limit]
            return MediaListResponse(
                items=[MediaResponse.model_validate(media) for media in paged],
                total=len(visible),
            )

    @router.post("/{media_id}/shares", response_model=MediaShareResponse, status_code=status.HTTP_201_CREATED)
    async def share_media(
        media_id: UUID,
        payload: MediaShareRequest,
        current_user: UserModel = Depends(get_current_user),
    ) -> MediaShareResponse:
        with session_factory() as db:
            media = db.get(MediaModel, str(media_id))
            if media is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mídia não encontrada")
            if not can_manage(media, current_user):
                raise forbidden()
            shared_user = db.get(UserModel, str(payload.user_id))
            if shared_user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
            if shared_user.institution_id != current_user.institution_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário de outra instituição")
            existing = db.scalar(
                select(MediaShareModel).where(
                    MediaShareModel.media_id == media.id,
                    MediaShareModel.user_id == shared_user.id,
                )
            )
            if existing is None:
                db.add(
                    MediaShareModel(
                        media_id=media.id,
                        user_id=shared_user.id,
                    )
                )
                db.commit()
            return MediaShareResponse(media_id=media_id, user_id=UUID(shared_user.id))

    @router.delete("/{media_id}/shares/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def unshare_media(
        media_id: UUID,
        user_id: UUID,
        current_user: UserModel = Depends(get_current_user),
    ) -> None:
        with session_factory() as db:
            media = db.get(MediaModel, str(media_id))
            if media is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mídia não encontrada")
            if not can_manage(media, current_user):
                raise forbidden()
            db.query(MediaShareModel).filter(
                MediaShareModel.media_id == media.id,
                MediaShareModel.user_id == str(user_id),
            ).delete()
            db.commit()

    @router.get("/{media_id}", response_model=MediaDetailResponse)
    async def get_media(
        media_id: UUID,
        current_user: UserModel = Depends(get_current_user),
    ) -> MediaDetailResponse:
        institution_id = UUID(current_user.institution_id)
        with session_factory() as db:
            media = db.get(MediaModel, str(media_id))
            if media is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mídia não encontrada")
            if not can_access(db, media, institution_id, current_user.id, current_user.role):
                raise forbidden()
            expires_in = 900
            try:
                preview_url = upload_service.storage.presign_object(
                    bucket=media.storage_bucket,
                    key=media.storage_key,
                    expires_seconds=expires_in,
                )
                download_url = upload_service.storage.presign_object(
                    bucket=media.storage_bucket,
                    key=media.storage_key,
                    expires_seconds=expires_in,
                )
            except (StorageError, NotImplementedError) as error:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Storage temporariamente indisponível",
                ) from error
            return MediaDetailResponse(
                id=UUID(media.id),
                institution_id=UUID(media.institution_id),
                author_id=UUID(media.author_id) if media.author_id else None,
                original_filename=media.original_filename,
                content_type=media.content_type,
                size_bytes=media.size_bytes,
                declared_duration_seconds=media.declared_duration_seconds,
                status=media.status,
                preview_url=preview_url,
                download_url=download_url,
                expires_in=expires_in,
            )

    @router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_media(
        media_id: UUID,
        current_user: UserModel = Depends(get_current_user),
    ) -> None:
        with session_factory() as db:
            media = db.get(MediaModel, str(media_id))
            if media is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mídia não encontrada")
            if not can_manage(media, current_user):
                raise forbidden()
            prefix = f"{media.institution_id}/{media_id}/"
            try:
                upload_service.storage.delete_prefix(
                    bucket=media.storage_bucket,
                    prefix=prefix,
                )
            except (StorageError, NotImplementedError) as error:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Não foi possível excluir os arquivos da mídia",
                ) from error
            db.query(MediaShareModel).filter(MediaShareModel.media_id == media.id).delete()
            db.delete(media)
            db.commit()

    @router.post("/{media_id}/uploads/abort", status_code=status.HTTP_204_NO_CONTENT)
    async def abort_upload(
        media_id: UUID,
        current_user: UserModel = Depends(get_current_user),
    ) -> None:
        session = upload_service.sessions.get(media_id)
        if session is None or session.institution_id != UUID(current_user.institution_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload não encontrado")
        upload_service.abort(media_id)
        with session_factory() as db:
            media = db.get(MediaModel, str(media_id))
            if media is not None:
                media.status = "CANCELED"
                db.commit()

    return router
