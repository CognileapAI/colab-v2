"""S3 컨트롤 플레인 클라이언트 — stdlib 만.

서버가 직접 부르는 호출만 담는다: 멀티파트 시작/조회/완료/중단, HeadObject,
DeleteObjects, ListObjects. 파일 바이트를 나르는 PUT 은 브라우저가 프리사인드
URL 로 하므로 여기 없다 — 컨트롤 플레인은 서버, 데이터 플레인은 브라우저 (dev-package/S3.md §3).

**예외 하나 — 묶음 다운로드의 GetObject** (`PLAN-SoT §9 〈175〉-(다)`): zip 은 서버가 만들어야
하므로 `get_object_stream` 이 S3 GET 을 **청크로** 흘려보낸다. 단일 파일은 여전히 브라우저가
프리사인드 GET(`presign_get`)으로 직접 받는다. 본문 없는 GET 이라 `content-type` 함정이 없다.

실전에서 확인된 함정 네 가지를 코드로 방어한다:
① `CompleteMultipartUpload` 는 200 OK 본문에 `<Error>` 를 담을 수 있다 — 루트 태그를 확인한다
② 응답 XML 에 네임스페이스가 있다 — `{*}` 와일드카드로 찾는다
③ Complete 요청 본문은 네임스페이스 없이 PartNumber 오름차순, ETag 는 따옴표 포함 그대로
④ `x-amz-checksum-algorithm` 을 절대 넣지 않는다 — 넣으면 브라우저 파트 PUT 이 전부 깨진다

재시도: 5xx·네트워크 오류는 3회 지수 백오프, 4xx 는 즉시 실패.
타임아웃 10초, Complete 만 60초 (조립이 오래 걸릴 수 있다).

⚠ 세 배포 단위가 **같은 바이트**로 갖는 파일이다 — 정본은 core-api 의 `kernel/s3.py` 이고,
pipeline-worker·viz-render 의 `kernel/s3.py` 는 `contracts/codegen/manifest.toml` 에 등기된
복제본이다(`generated-up-to-date` 게이트가 드리프트를 잡는다). 배포 단위끼리 import 하지
않으므로(`import-boundary` units-independent) 공유 라이브러리로 빼지 않는다. 그래서 형제
모듈(`sigv4`·`aws_credentials`)은 **상대 import** 로만 부른다 — 패키지 절대 경로가 들어가면
복제본이 깨진다. 고칠 때는 core-api 원본을 고치고 **같은 커밋에** 재생성한다. 이 파일 안의
경로·시험 언급은 전부 core-api 원본 기준이다.
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
from typing import Any, Callable, Iterator

from .aws_credentials import effective_ttl, load_credentials
from .sigv4 import Credentials, presign, sign_headers, uri_encode

# transport(method, url, headers, payload, timeout) -> (status, 응답 헤더, 본문)
Transport = Callable[[str, str, dict[str, str], bytes, float], tuple[int, dict[str, str], bytes]]
# stream_transport(method, url, headers, timeout) -> (status, 응답 헤더, 본문)
#   본문은 2xx 면 **읽기 객체**(`read(n)`·`close()`), 4xx/5xx 면 통째로 읽은 bytes(오류 XML).
#   `_call` 이 본문을 통째로 읽는 것과 달리 응답을 열어 둔 채 돌려준다 — 그래서 별도 계약이다.
StreamTransport = Callable[[str, str, dict[str, str], float], tuple[int, dict[str, str], Any]]

_ATTEMPTS = 3
_DELETE_BATCH = 1000
#: GetObject 스트림의 청크. 묶음 zip 이 이 단위로 흘러가므로 메모리는 청크 하나다.
STREAM_CHUNK = 1024 * 1024


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


def _urllib_stream_transport(method: str, url: str, headers: dict[str, str],
                             timeout: float) -> tuple[int, dict[str, str], Any]:
    """응답을 **열어 둔 채** 돌려준다 — 본문은 호출자가 청크로 읽고 닫는다."""
    req = urllib.request.Request(url, method=method, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        with e:
            return e.code, dict(e.headers or {}), e.read()
    return resp.status, dict(resp.headers), resp


def _xml(body: bytes) -> ET.Element:
    return ET.fromstring(body.decode("utf-8", "replace"))


def _drain(body: Any) -> bytes:
    """오류 응답의 본문 — 전송이 bytes 를 줬든 읽기 객체를 줬든 통째로."""
    if isinstance(body, (bytes, bytearray)):
        return bytes(body)
    try:
        return body.read()
    finally:
        close = getattr(body, "close", None)
        if close is not None:
            close()


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
                 transport: Transport | None = None,
                 stream_transport: StreamTransport | None = None,
                 backoff_base: float = 0.5):
        self.bucket = bucket
        self.region = region
        self._creds = creds
        self._transport = transport or _urllib_transport
        self._stream_transport = stream_transport or _urllib_stream_transport
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
        url = self._url(key, query)
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

    def _url(self, key: str, query: dict[str, str]) -> str:
        qs = "&".join(
            f"{uri_encode(k)}={uri_encode(v)}" if v else f"{uri_encode(k)}="
            for k, v in sorted(query.items())
        )
        return f"https://{self.host}/{uri_encode(key, keep_slash=True)}" + (f"?{qs}" if qs else "")

    def _stream(self, *, key: str, query: dict[str, str] | None = None,
                timeout: float = 30.0) -> tuple[dict[str, str], Any]:
        """`_call` 의 스트림 변형 — 본문 없는 GET 만. 서명은 같은 경로(`sign_headers`)다.

        재시도는 **첫 바이트 전**까지만이다 — 응답이 열린 뒤의 네트워크 오류는 호출자에게
        간다(반쯤 흘려보낸 zip 을 처음부터 다시 쓸 수는 없다).
        """
        query = query or {}
        url = self._url(key, query)
        last: Exception | None = None
        for attempt in range(_ATTEMPTS):
            headers = sign_headers(method="GET", host=self.host, key=key, region=self.region,
                                   creds=self._credentials(), query=query, payload=b"",
                                   now=datetime.now(timezone.utc))
            try:
                status, resp_headers, body = self._stream_transport("GET", url, headers, timeout)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last = e
                time.sleep(self._backoff_base * (2 ** attempt))
                continue
            if status >= 500:
                last = _error_from(_drain(body), status)
                time.sleep(self._backoff_base * (2 ** attempt))
                continue
            if status >= 400:
                raise _error_from(_drain(body), status)
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

    # ── 프리사인 (브라우저 직접 PUT 용) ─────────────────────────────────────

    def url_ttl(self, configured: int, now: datetime) -> int:
        """프리사인 TTL 을 자격증명 만료 안쪽으로 클램프한다 (`aws_credentials.effective_ttl`)."""
        return effective_ttl(configured, self._credentials(), now)

    def presign_put(self, key: str, *, query: dict[str, str] | None = None,
                    expires: int, now: datetime) -> str:
        """브라우저가 직접 PUT 할 프리사인드 URL. 서명은 서버, 바이트는 브라우저."""
        return presign(method="PUT", host=self.host, key=key, region=self.region,
                       creds=self._credentials(), query=query or {},
                       expires=expires, now=now)

    def presign_get(self, key: str, *, query: dict[str, str] | None = None,
                    expires: int, now: datetime) -> str:
        """브라우저가 직접 GET 할 프리사인드 URL — `presign_put` 의 대칭 (`〈175〉-(다)` 단일 파일).

        `query` 에 `response-content-disposition` 을 실으면 S3 가 그 헤더로 응답한다 —
        저장 이름(`DownloadTicket.fileName`)이 core 를 거치지 않고도 지켜지는 길이다.
        쿼리는 서명 대상이라 나중에 바꿔 붙일 수 없다.
        """
        return presign(method="GET", host=self.host, key=key, region=self.region,
                       creds=self._credentials(), query=query or {},
                       expires=expires, now=now)

    def get_object_stream(self, key: str, *, chunk_size: int = STREAM_CHUNK) -> Iterator[bytes]:
        """GetObject 를 청크로. **없는 키·4xx 는 호출 시점에 `S3Error`** 다 — 제너레이터의 첫
        `next()` 에서 터지게 두면 라우트는 이미 200 헤더를 보낸 뒤라 404 를 낼 수 없다."""
        _headers, body = self._stream(key=key)

        def chunks() -> Iterator[bytes]:
            try:
                while True:
                    chunk = body.read(chunk_size)
                    if not chunk:
                        return
                    yield chunk
            finally:
                body.close()

        return chunks()

    # ── 객체 ────────────────────────────────────────────────────────────────

    def put_object(self, key: str, payload: bytes,
                   content_type: str = "application/octet-stream",
                   cache_control: str | None = None) -> str:
        """단일 PUT. 서버가 직접 바이트를 놓는 경로(저장 백엔드 s3 모드)에서만 쓴다.

        `cache_control` 을 주면 객체 메타데이터 `Cache-Control` 로 저장된다 — 정적 자산(FE 번들·
        미리보기 산출물)을 CDN·브라우저가 얼마나 오래 들고 있어도 되는지는 **놓는 쪽**이 정한다.
        `sign_headers` 는 받은 헤더 전부를 SignedHeaders 에 넣으므로 이 헤더도 서명 대상이다.
        """
        extra = {"content-type": content_type}
        if cache_control:
            extra["cache-control"] = cache_control
        headers, _body = self._call(method="PUT", key=key, payload=payload,
                                    extra_headers=extra, timeout=60.0)
        lowered = {k.lower(): v for k, v in headers.items()}
        return lowered.get("etag", "")

    def copy_object(self, src_key: str, dst_key: str) -> None:
        """같은 버킷 안 서버사이드 복사 — 바이트가 서버를 오가지 않는다.

        CompleteMultipartUpload 처럼 **200 본문에 <Error> 가 올 수 있다** — 루트 태그를
        확인한다 (등록 전환의 이동이 조용히 실패하면 안 된다).
        """
        source = f"/{self.bucket}/{uri_encode(src_key, keep_slash=True)}"
        _h, body = self._call(method="PUT", key=dst_key,
                              extra_headers={"x-amz-copy-source": source}, timeout=60.0)
        root = _xml(body)
        if root.tag.endswith("Error") or root.findtext("{*}ETag") is None:
            raise _error_from(body, 200)

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
