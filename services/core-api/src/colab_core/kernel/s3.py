"""S3 컨트롤 플레인 클라이언트 — stdlib 만.

서버가 직접 부르는 호출만 담는다: 멀티파트 시작/조회/완료/중단, HeadObject,
DeleteObjects, ListObjects. 파일 바이트를 나르는 PUT 은 브라우저가 프리사인드
URL 로 하므로 여기 없다 — 컨트롤 플레인은 서버, 데이터 플레인은 브라우저 (dev-package/S3.md §3).

실전에서 확인된 함정 네 가지를 코드로 방어한다:
① `CompleteMultipartUpload` 는 200 OK 본문에 `<Error>` 를 담을 수 있다 — 루트 태그를 확인한다
② 응답 XML 에 네임스페이스가 있다 — `{*}` 와일드카드로 찾는다
③ Complete 요청 본문은 네임스페이스 없이 PartNumber 오름차순, ETag 는 따옴표 포함 그대로
④ `x-amz-checksum-algorithm` 을 절대 넣지 않는다 — 넣으면 브라우저 파트 PUT 이 전부 깨진다

재시도: 5xx·네트워크 오류는 3회 지수 백오프, 4xx 는 즉시 실패.
타임아웃 10초, Complete 만 60초 (조립이 오래 걸릴 수 있다).
"""
from __future__ import annotations

import base64
import hashlib
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterator

from colab_core.kernel.aws_credentials import load_credentials
from colab_core.kernel.sigv4 import Credentials, sign_headers, uri_encode

# transport(method, url, headers, payload, timeout) -> (status, 응답 헤더, 본문)
Transport = Callable[[str, str, dict[str, str], bytes, float], tuple[int, dict[str, str], bytes]]

_ATTEMPTS = 3
_DELETE_BATCH = 1000


class S3Error(RuntimeError):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(f"S3 {status} {code}: {message}")
        self.status = status
        self.code = code


@dataclass(frozen=True)
class Part:
    number: int
    etag: str  # ListParts 가 준 그대로 — 따옴표 포함
    size: int


def _urllib_transport(method: str, url: str, headers: dict[str, str],
                      payload: bytes, timeout: float) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, method=method, headers=headers,
                                 data=payload if payload else None)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read()


def _xml(body: bytes) -> ET.Element:
    return ET.fromstring(body.decode("utf-8", "replace"))


def _error_from(body: bytes, status: int) -> S3Error:
    code, message = "", ""
    try:
        root = _xml(body)
        node = root if root.tag.endswith("Error") else root.find(".//{*}Error")
        if node is not None:
            code = (node.findtext("{*}Code") or "").strip()
            message = (node.findtext("{*}Message") or "").strip()
    except ET.ParseError:
        message = body[:200].decode("utf-8", "replace")
    return S3Error(status, code, message)


class S3Client:
    def __init__(self, *, bucket: str, region: str, creds: Credentials | None = None,
                 transport: Transport | None = None, backoff_base: float = 0.5):
        self.bucket = bucket
        self.region = region
        self._creds = creds
        self._transport = transport or _urllib_transport
        self._backoff_base = backoff_base

    @property
    def host(self) -> str:
        return f"{self.bucket}.s3.{self.region}.amazonaws.com"

    def _credentials(self) -> Credentials:
        if self._creds is not None:
            return self._creds
        creds, _source = load_credentials()
        return creds

    def _call(self, *, method: str, key: str = "", query: dict[str, str] | None = None,
              payload: bytes = b"", extra_headers: dict[str, str] | None = None,
              timeout: float = 10.0) -> tuple[dict[str, str], bytes]:
        query = query or {}
        if payload and not any(h.lower() == "content-type" for h in (extra_headers or {})):
            # content-type 을 명시하지 않으면 urllib 이 form-urlencoded 를 붙이고,
            # S3 가 본문을 쿼리로 해석해 서명이 어긋난다 (s3_smoke 최초 실행에서 실측)
            extra_headers = {**(extra_headers or {}), "content-type": "application/xml"}
        qs = "&".join(
            f"{uri_encode(k)}={uri_encode(v)}" if v else f"{uri_encode(k)}="
            for k, v in sorted(query.items())
        )
        url = f"https://{self.host}/{uri_encode(key, keep_slash=True)}" + (f"?{qs}" if qs else "")
        last: Exception | None = None
        for attempt in range(_ATTEMPTS):
            headers = sign_headers(method=method, host=self.host, key=key, region=self.region,
                                   creds=self._credentials(), query=query, payload=payload,
                                   now=datetime.now(timezone.utc), headers=extra_headers)
            try:
                status, resp_headers, body = self._transport(method, url, headers, payload, timeout)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last = e
                time.sleep(self._backoff_base * (2 ** attempt))
                continue
            if status >= 500:
                last = _error_from(body, status)
                time.sleep(self._backoff_base * (2 ** attempt))
                continue
            if status >= 400:
                raise _error_from(body, status)
            return resp_headers, body
        raise last if isinstance(last, S3Error) else S3Error(0, "Unreachable", str(last))

    # ── 멀티파트 ────────────────────────────────────────────────────────────

    def create_multipart_upload(self, key: str, content_type: str | None = None) -> str:
        extra = {"content-type": content_type} if content_type else None
        _h, body = self._call(method="POST", key=key, query={"uploads": ""},
                              extra_headers=extra)
        upload_id = _xml(body).findtext("{*}UploadId")
        if not upload_id:
            raise _error_from(body, 200)
        return upload_id

    def list_parts(self, key: str, upload_id: str) -> list[Part]:
        parts: list[Part] = []
        marker = ""
        while True:
            query = {"uploadId": upload_id}
            if marker:
                query["part-number-marker"] = marker
            _h, body = self._call(method="GET", key=key, query=query)
            root = _xml(body)
            for node in root.findall("{*}Part"):
                parts.append(Part(
                    number=int(node.findtext("{*}PartNumber") or 0),
                    etag=(node.findtext("{*}ETag") or "").strip(),
                    size=int(node.findtext("{*}Size") or 0),
                ))
            if (root.findtext("{*}IsTruncated") or "").lower() != "true":
                return parts
            marker = (root.findtext("{*}NextPartNumberMarker") or "").strip()

    def complete_multipart_upload(self, key: str, upload_id: str, parts: list[Part]) -> str:
        rows = "".join(
            f"<Part><PartNumber>{p.number}</PartNumber><ETag>{p.etag}</ETag></Part>"
            for p in sorted(parts, key=lambda p: p.number)
        )
        payload = f"<CompleteMultipartUpload>{rows}</CompleteMultipartUpload>".encode("utf-8")
        _h, body = self._call(method="POST", key=key, query={"uploadId": upload_id},
                              payload=payload, timeout=60.0)
        root = _xml(body)  # ① 200 이어도 본문이 <Error> 일 수 있다
        if root.tag.endswith("Error"):
            raise _error_from(body, 200)
        return (root.findtext("{*}ETag") or "").strip()

    def abort_multipart_upload(self, key: str, upload_id: str) -> None:
        self._call(method="DELETE", key=key, query={"uploadId": upload_id})

    def list_multipart_uploads(self, prefix: str = "") -> list[tuple[str, str]]:
        query = {"uploads": ""}
        if prefix:
            query["prefix"] = prefix
        _h, body = self._call(method="GET", query=query)
        return [
            ((n.findtext("{*}Key") or ""), (n.findtext("{*}UploadId") or ""))
            for n in _xml(body).findall("{*}Upload")
        ]

    # ── 객체 ────────────────────────────────────────────────────────────────

    def head_object(self, key: str) -> tuple[int, str]:
        headers, _body = self._call(method="HEAD", key=key)
        lowered = {k.lower(): v for k, v in headers.items()}
        return int(lowered.get("content-length", "0")), lowered.get("etag", "")

    def delete_objects(self, keys: list[str]) -> None:
        for start in range(0, len(keys), _DELETE_BATCH):
            rows = "".join(
                f"<Object><Key>{k.replace('&', '&amp;').replace('<', '&lt;')}</Key></Object>"
                for k in keys[start:start + _DELETE_BATCH]
            )
            payload = f"<Delete><Quiet>true</Quiet>{rows}</Delete>".encode("utf-8")
            md5 = base64.b64encode(hashlib.md5(payload).digest()).decode("ascii")
            _h, body = self._call(method="POST", query={"delete": ""}, payload=payload,
                                  extra_headers={"content-md5": md5})
            failed = _xml(body).find("{*}Error")
            if failed is not None:
                raise _error_from(body, 200)

    def list_objects(self, prefix: str) -> Iterator[tuple[str, int]]:
        token = ""
        while True:
            query = {"list-type": "2", "prefix": prefix}
            if token:
                query["continuation-token"] = token
            _h, body = self._call(method="GET", query=query)
            root = _xml(body)
            for node in root.findall("{*}Contents"):
                yield (node.findtext("{*}Key") or ""), int(node.findtext("{*}Size") or 0)
            if (root.findtext("{*}IsTruncated") or "").lower() != "true":
                return
            token = (root.findtext("{*}NextContinuationToken") or "").strip()
