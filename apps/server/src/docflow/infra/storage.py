from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import cast
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import uuid4
from xml.etree import ElementTree


class StorageError(RuntimeError):
    pass


class ObjectStorage:
    def create_multipart_upload(self, *, bucket: str, key: str, content_type: str) -> str:
        raise NotImplementedError

    def presign_part(self, *, bucket: str, key: str, upload_id: str, part_number: int) -> str:
        raise NotImplementedError

    def complete_multipart_upload(self, *, bucket: str, key: str, upload_id: str, parts: list[dict[str, object]]) -> None:
        raise NotImplementedError

    def abort_multipart_upload(self, *, bucket: str, key: str, upload_id: str) -> None:
        raise NotImplementedError

    def head_object(self, *, bucket: str, key: str) -> dict[str, object]:
        raise NotImplementedError


class S3ObjectStorage(ObjectStorage):
    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        presign_expiry_seconds: int = 900,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.presign_expiry_seconds = presign_expiry_seconds

    def create_multipart_upload(self, *, bucket: str, key: str, content_type: str) -> str:
        response = cast(
            bytes,
            self._request(
                "POST",
                bucket,
                key,
                query={"uploads": ""},
                headers={"Content-Type": content_type},
            ),
        )
        root = ElementTree.fromstring(response)
        upload_id = root.findtext("{*}UploadId")
        if not upload_id:
            raise StorageError("S3 não retornou upload_id")
        return upload_id

    def presign_part(self, *, bucket: str, key: str, upload_id: str, part_number: int) -> str:
        query = {"partNumber": str(part_number), "uploadId": upload_id}
        return self._presigned_url("PUT", bucket, key, query)

    def complete_multipart_upload(
        self, *, bucket: str, key: str, upload_id: str, parts: list[dict[str, object]]
    ) -> None:
        payload = ElementTree.Element("CompleteMultipartUpload")
        for part in sorted(parts, key=lambda item: int(str(item["part_number"]))):
            node = ElementTree.SubElement(payload, "Part")
            ElementTree.SubElement(node, "PartNumber").text = str(part["part_number"])
            ElementTree.SubElement(node, "ETag").text = str(part["etag"])
        self._request(
            "POST",
            bucket,
            key,
            query={"uploadId": upload_id},
            headers={"Content-Type": "application/xml"},
            body=ElementTree.tostring(payload, encoding="utf-8"),
        )

    def abort_multipart_upload(self, *, bucket: str, key: str, upload_id: str) -> None:
        self._request("DELETE", bucket, key, query={"uploadId": upload_id})

    def head_object(self, *, bucket: str, key: str) -> dict[str, object]:
        headers = cast(dict[str, str], self._request("HEAD", bucket, key, return_headers=True))
        return {"content_length": int(headers.get("Content-Length", "0"))}

    def _presigned_url(
        self, method: str, bucket: str, key: str, query: dict[str, str]
    ) -> str:
        now = datetime.now(UTC)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date = now.strftime("%Y%m%d")
        credential_scope = f"{date}/{self.region}/s3/aws4_request"
        path = f"/{quote(bucket)}/{quote(key, safe='/')}"
        params = {
            **query,
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": f"{self.access_key}/{credential_scope}",
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(self.presign_expiry_seconds),
            "X-Amz-SignedHeaders": "host",
        }
        canonical_query = urlencode(sorted(params.items()))
        canonical_request = "\n".join(
            [method, path, canonical_query, f"host:{self._host()}\n", "host", "UNSIGNED-PAYLOAD"]
        )
        string_to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                amz_date,
                credential_scope,
                hashlib.sha256(canonical_request.encode()).hexdigest(),
            ]
        )
        signature = hmac.new(
            self._signing_key(date),
            string_to_sign.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"{self.endpoint}{path}?{canonical_query}&X-Amz-Signature={signature}"

    def _request(
        self,
        method: str,
        bucket: str,
        key: str,
        *,
        query: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        return_headers: bool = False,
    ) -> bytes | dict[str, str]:
        now = datetime.now(UTC)
        path = f"/{quote(bucket)}/{quote(key, safe='/')}"
        request_headers = {"Host": self._host(), "x-amz-content-sha256": hashlib.sha256(body or b"").hexdigest()}
        request_headers["x-amz-date"] = now.strftime("%Y%m%dT%H%M%SZ")
        request_headers.update(headers or {})
        date = now.strftime("%Y%m%d")
        credential_scope = f"{date}/{self.region}/s3/aws4_request"
        canonical_headers = "".join(
            f"{name.lower()}:{' '.join(value.strip().split())}\n"
            for name, value in sorted(request_headers.items(), key=lambda item: item[0].lower())
        )
        signed_headers = ";".join(
            name.lower() for name, _ in sorted(request_headers.items(), key=lambda item: item[0].lower())
        )
        canonical_query = urlencode(sorted((query or {}).items()))
        canonical_request = "\n".join(
            [
                method,
                path,
                canonical_query,
                canonical_headers,
                signed_headers,
                request_headers["x-amz-content-sha256"],
            ]
        )
        string_to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                request_headers["x-amz-date"],
                credential_scope,
                hashlib.sha256(canonical_request.encode()).hexdigest(),
            ]
        )
        signature = hmac.new(
            self._signing_key(date), string_to_sign.encode(), hashlib.sha256
        ).hexdigest()
        request_headers["Authorization"] = (
            f"AWS4-HMAC-SHA256 Credential={self.access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        request = Request(
            f"{self.endpoint}{path}" + (f"?{urlencode(query or {})}" if query else ""),
            data=body,
            headers=request_headers,
            method=method,
        )
        try:
            with urlopen(request) as response:
                return dict(response.headers.items()) if return_headers else response.read()
        except Exception as error:
            raise StorageError("Falha na operação S3") from error

    def _host(self) -> str:
        return self.endpoint.split("://", 1)[1]

    def _signing_key(self, date: str) -> bytes:
        date_key = hmac.new(f"AWS4{self.secret_key}".encode(), date.encode(), hashlib.sha256).digest()
        region_key = hmac.new(date_key, self.region.encode(), hashlib.sha256).digest()
        service_key = hmac.new(region_key, b"s3", hashlib.sha256).digest()
        return hmac.new(service_key, b"aws4_request", hashlib.sha256).digest()


@dataclass(slots=True)
class _Upload:
    bucket: str
    key: str
    content_type: str
    created_at: datetime


@dataclass(slots=True)
class InMemoryObjectStorage(ObjectStorage):
    uploads: dict[str, _Upload] = field(default_factory=dict)
    objects: dict[tuple[str, str], dict[str, object]] = field(default_factory=dict)

    def create_multipart_upload(self, *, bucket: str, key: str, content_type: str) -> str:
        upload_id = str(uuid4())
        self.uploads[upload_id] = _Upload(
            bucket=bucket,
            key=key,
            content_type=content_type,
            created_at=datetime.now(UTC),
        )
        return upload_id

    def presign_part(self, *, bucket: str, key: str, upload_id: str, part_number: int) -> str:
        upload = self.uploads.get(upload_id)
        if upload is None or (upload.bucket, upload.key) != (bucket, key):
            raise StorageError("Upload multipart inexistente")
        return f"memory://{bucket}/{key}?uploadId={upload_id}&partNumber={part_number}"

    def complete_multipart_upload(
        self, *, bucket: str, key: str, upload_id: str, parts: list[dict[str, object]]
    ) -> None:
        if upload_id not in self.uploads:
            raise StorageError("Upload multipart inexistente")
        self.objects[(bucket, key)] = {"parts": parts, "content_type": self.uploads[upload_id].content_type}
        del self.uploads[upload_id]

    def abort_multipart_upload(self, *, bucket: str, key: str, upload_id: str) -> None:
        upload = self.uploads.get(upload_id)
        if upload is None or (upload.bucket, upload.key) != (bucket, key):
            raise StorageError("Upload multipart inexistente")
        del self.uploads[upload_id]

    def head_object(self, *, bucket: str, key: str) -> dict[str, object]:
        try:
            return self.objects[(bucket, key)]
        except KeyError as error:
            raise StorageError("Objeto não encontrado") from error

    def cleanup_expired(self, *, older_than: timedelta) -> int:
        cutoff = datetime.now(UTC) - older_than
        expired = [upload_id for upload_id, upload in self.uploads.items() if upload.created_at < cutoff]
        for upload_id in expired:
            del self.uploads[upload_id]
        return len(expired)
