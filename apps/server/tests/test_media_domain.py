import pytest

from docflow.domain.media import (
    MAX_DURATION_SECONDS,
    MAX_FILE_SIZE_BYTES,
    MediaValidationError,
    UploadRequest,
)


def test_upload_request_accepts_supported_media_within_limits() -> None:
    request = UploadRequest.create(
        filename="reuniao.mp4",
        content_type="video/mp4",
        size_bytes=50_000_000,
        duration_seconds=9000,
    )

    assert request.extension == "mp4"
    assert request.total_parts == 1


@pytest.mark.parametrize(
    "filename, content_type",
    [("reuniao.exe", "application/octet-stream"), ("audio.txt", "text/plain")],
)
def test_upload_request_rejects_unsupported_media(filename: str, content_type: str) -> None:
    with pytest.raises(MediaValidationError, match="formato"):
        UploadRequest.create(
            filename=filename,
            content_type=content_type,
            size_bytes=100,
            duration_seconds=1,
        )


@pytest.mark.parametrize(
    "size_bytes, duration_seconds",
    [
        (MAX_FILE_SIZE_BYTES + 1, 1),
        (100, MAX_DURATION_SECONDS + 1),
    ],
)
def test_upload_request_rejects_limit_violations(size_bytes: int, duration_seconds: int) -> None:
    with pytest.raises(MediaValidationError):
        UploadRequest.create(
            filename="reuniao.mp4",
            content_type="video/mp4",
            size_bytes=size_bytes,
            duration_seconds=duration_seconds,
        )
