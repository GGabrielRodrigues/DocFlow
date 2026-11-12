from __future__ import annotations

from dataclasses import dataclass
from math import ceil

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 * 1024
MAX_DURATION_SECONDS = 150 * 60
PART_SIZE_BYTES = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = frozenset({"mp4", "mkv", "mov", "webm", "mp3", "wav", "m4a", "flac", "ogg"})
ALLOWED_CONTENT_TYPES = frozenset(
    {
        "video/mp4",
        "video/x-matroska",
        "video/quicktime",
        "video/webm",
        "audio/mpeg",
        "audio/wav",
        "audio/x-wav",
        "audio/mp4",
        "audio/flac",
        "audio/ogg",
    }
)


class MediaValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class UploadRequest:
    filename: str
    content_type: str
    size_bytes: int
    duration_seconds: int
    extension: str
    total_parts: int

    @classmethod
    def create(
        cls,
        *,
        filename: str,
        content_type: str,
        size_bytes: int,
        duration_seconds: int,
    ) -> UploadRequest:
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in ALLOWED_EXTENSIONS or content_type not in ALLOWED_CONTENT_TYPES:
            raise MediaValidationError("formato de mídia não suportado")
        if size_bytes <= 0 or size_bytes > MAX_FILE_SIZE_BYTES:
            raise MediaValidationError("O arquivo deve ter no máximo 10 GB")
        if duration_seconds <= 0 or duration_seconds > MAX_DURATION_SECONDS:
            raise MediaValidationError("A duração deve ser de no máximo 2h30")
        return cls(
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            duration_seconds=duration_seconds,
            extension=extension,
            total_parts=ceil(size_bytes / PART_SIZE_BYTES),
        )
