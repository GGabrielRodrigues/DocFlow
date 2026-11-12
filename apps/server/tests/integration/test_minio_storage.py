import os

import pytest

from docflow.infra.storage import S3ObjectStorage

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("RUN_MINIO_TESTS") != "1",
    reason="Defina RUN_MINIO_TESTS=1 para executar testes que exigem Docker/MinIO",
)
def test_s3_storage_round_trip_with_minio() -> None:
    from minio import Minio
    from testcontainers.minio import MinioContainer

    with MinioContainer("minio/minio:latest") as container:
        client = Minio(
            container.get_container_host_ip() + ":" + str(container.get_exposed_port(9000)),
            access_key=container.MINIO_ROOT_USER,
            secret_key=container.MINIO_ROOT_PASSWORD,
            secure=False,
        )
        client.make_bucket("media-raw")
        storage = S3ObjectStorage(
            endpoint=f"http://{container.get_container_host_ip()}:{container.get_exposed_port(9000)}",
            access_key=container.MINIO_ROOT_USER,
            secret_key=container.MINIO_ROOT_PASSWORD,
        )
        upload_id = storage.create_multipart_upload(
            bucket="media-raw", key="tenant/media.mp4", content_type="video/mp4"
        )
        assert upload_id
        storage.abort_multipart_upload(
            bucket="media-raw", key="tenant/media.mp4", upload_id=upload_id
        )
