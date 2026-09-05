"""AWS SigV4 서명 — 표준 라이브러리만 사용.

신규 런타임 의존 0 결정(진행 파일 결정 기록 08-25)에 따라 boto3 를 쓰지 않고
`hmac`·`hashlib`·`datetime`·`urllib.parse` 로 서명을 직접 만든다.

두 가지 서명 형태를 낸다.
- `presign()`      쿼리스트링 인증 프리사인드 URL — 브라우저가 S3 를 직접 호출할 때
- `sign_headers()` 헤더 인증 — 서버가 S3/STS 컨트롤 플레인을 직접 호출할 때

`now` 를 인자로 받는 이유: 테스트가 시간을 고정하기 위해서다.
내부에서 `datetime.now()` 를 부르지 않는다.

정규화 규칙(UriEncode·정렬·빈 줄)은 AWS SigV4 규격 문서 그대로이고,
`tests/test_sigv4.py`(core-api 원본 기준)가 AWS 문서의 알려진 정답 벡터로 대조한다.

⚠ 세 배포 단위가 **같은 바이트**로 갖는 파일이다 — 정본은 core-api 의 `kernel/sigv4.py` 이고,
pipeline-worker·viz-render 의 `kernel/sigv4.py` 는 `contracts/codegen/manifest.toml` 에 등기된
복제본이다(`generated-up-to-date` 게이트가 드리프트를 잡는다). 배포 단위끼리 import 하지
않으므로(`import-boundary` units-independent) 공유 라이브러리로 빼지 않는다 — `ids.py` 와 같은
방식이다. 고칠 때는 core-api 원본을 고치고 **같은 커밋에** 재생성한다. 이 파일 안의 경로·시험
언급은 전부 core-api 원본 기준이다.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timezone

# 빈 본문의 SHA-256 — 헤더 인증 GET/HEAD 가 항상 쓴다
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

_UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)

# 프리사인드 URL 의 최대 수명 (AWS 규격 7일)
MAX_PRESIGN_TTL = 604800


@dataclass(frozen=True)
class Credentials:
    access_key: str
    secret_key: str
    session_token: str | None = None
    expires_at: datetime | None = None  # 임시 자격증명이면 설정됨


def uri_encode(value: str, *, keep_slash: bool = False) -> str:
    """SigV4 전용 UriEncode — `urllib.parse.quote` 의 기본값과 규칙이 다르다.

    unreserved(`A-Za-z0-9-._~`)만 그대로 두고 나머지 모든 바이트를 대문자 %XX 로.
    공백은 %20(절대 '+' 아님). 객체 키 안의 '/' 만 `keep_slash=True` 로 보존한다.
    """
    out: list[str] = []
    for ch in value:
        if ch in _UNRESERVED or (keep_slash and ch == "/"):
            out.append(ch)
        else:
            out.extend(f"%{b:02X}" for b in ch.encode("utf-8"))
    return "".join(out)


def _amz_dates(now: datetime) -> tuple[str, str]:
    """(x-amz-date, 날짜 스코프). naive 는 UTC 로 간주한다."""
    utc = now.astimezone(timezone.utc) if now.tzinfo else now.replace(tzinfo=timezone.utc)
    return utc.strftime("%Y%m%dT%H%M%SZ"), utc.strftime("%Y%m%d")


def _canonical_uri(key: str) -> str:
    # 키 안 '/' 보존 · 이중 인코딩 없음(S3 특례). 키가 비면 '/'
    return "/" + uri_encode(key, keep_slash=True)


def _canonical_query(params: dict[str, str]) -> str:
    # name/value 각각 UriEncode 후 name 기준 바이트 정렬. 값 없는 서브리소스는 'name='
    pairs = sorted((uri_encode(k), uri_encode(v)) for k, v in params.items())
    return "&".join(f"{k}={v}" for k, v in pairs)


def _canonical_headers(headers: dict[str, str]) -> tuple[str, str]:
    """(CanonicalHeaders 블록, SignedHeaders). 소문자화·공백 축약·이름 정렬."""
    norm = {k.lower(): " ".join(v.strip().split()) for k, v in headers.items()}
    names = sorted(norm)
    block = "".join(f"{n}:{norm[n]}\n" for n in names)  # 각 줄이 \n 로 끝난다
    return block, ";".join(names)


def _scope(date: str, region: str, service: str) -> str:
    return f"{date}/{region}/{service}/aws4_request"


def _signing_key(secret_key: str, date: str, region: str, service: str) -> bytes:
    def h(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    k_date = h(("AWS4" + secret_key).encode("utf-8"), date)
    k_region = h(k_date, region)
    k_service = h(k_region, service)
    return h(k_service, "aws4_request")


def _sign(creds: Credentials, region: str, service: str,
          amz_date: str, date: str, canonical_request: str) -> str:
    string_to_sign = "\n".join([
        "AWS4-HMAC-SHA256",
        amz_date,
        _scope(date, region, service),
        hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
    ])
    key = _signing_key(creds.secret_key, date, region, service)
    return hmac.new(key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()


def canonical_request_for_presign(*, method: str, host: str, key: str, region: str,
                                  creds: Credentials, query: dict[str, str],
                                  expires: int, now: datetime,
                                  service: str = "s3") -> tuple[str, dict[str, str]]:
    """프리사인용 CanonicalRequest 와, 서명 전 쿼리 파라미터 전체를 돌려준다."""
    amz_date, date = _amz_dates(now)
    params = dict(query)
    params["X-Amz-Algorithm"] = "AWS4-HMAC-SHA256"
    params["X-Amz-Credential"] = f"{creds.access_key}/{_scope(date, region, service)}"
    params["X-Amz-Date"] = amz_date
    params["X-Amz-Expires"] = str(expires)
    params["X-Amz-SignedHeaders"] = "host"
    if creds.session_token is not None:
        params["X-Amz-Security-Token"] = creds.session_token
    cr = "\n".join([
        method,
        _canonical_uri(key),
        _canonical_query(params),
        f"host:{host}\n",          # CanonicalHeaders 블록 — 뒤의 빈 줄은 규격이다
        "host",
        "UNSIGNED-PAYLOAD",
    ])
    return cr, params


def canonical_request_for_headers(*, method: str, host: str, key: str, region: str,
                                  creds: Credentials, query: dict[str, str],
                                  payload: bytes, now: datetime,
                                  headers: dict[str, str] | None = None,
                                  service: str = "s3") -> tuple[str, dict[str, str]]:
    """헤더 인증용 CanonicalRequest 와, 서명 대상 헤더 전체(host 포함)를 돌려준다."""
    amz_date, _date = _amz_dates(now)
    payload_hash = hashlib.sha256(payload).hexdigest() if payload else EMPTY_SHA256
    all_headers = dict(headers or {})
    all_headers["host"] = host
    all_headers["x-amz-content-sha256"] = payload_hash
    all_headers["x-amz-date"] = amz_date
    if creds.session_token is not None:
        all_headers["x-amz-security-token"] = creds.session_token  # 반드시 서명 대상
    block, signed_names = _canonical_headers(all_headers)
    cr = "\n".join([
        method,
        _canonical_uri(key),
        _canonical_query(query),
        block,                     # 각 줄이 \n 로 끝나 블록 뒤에 빈 줄이 생긴다
        signed_names,
        payload_hash,
    ])
    return cr, all_headers


def presign(*, method: str, host: str, key: str, region: str, creds: Credentials,
            query: dict[str, str] | None = None, expires: int, now: datetime,
            service: str = "s3") -> str:
    """쿼리스트링 인증 프리사인드 URL. 브라우저가 직접 호출한다."""
    amz_date, date = _amz_dates(now)
    cr, params = canonical_request_for_presign(
        method=method, host=host, key=key, region=region, creds=creds,
        query=query or {}, expires=expires, now=now, service=service,
    )
    signature = _sign(creds, region, service, amz_date, date, cr)
    # X-Amz-Signature 는 서명 대상이 아니므로 맨 마지막에 덧붙인다
    return (f"https://{host}{_canonical_uri(key)}"
            f"?{_canonical_query(params)}&X-Amz-Signature={signature}")


def sign_headers(*, method: str, host: str, key: str, region: str, creds: Credentials,
                 query: dict[str, str] | None = None, payload: bytes = b"",
                 now: datetime, headers: dict[str, str] | None = None,
                 service: str = "s3") -> dict[str, str]:
    """헤더 인증. 서버가 S3/STS 를 직접 호출할 때 쓴다. 요청에 실을 헤더 전부를 돌려준다."""
    amz_date, date = _amz_dates(now)
    cr, all_headers = canonical_request_for_headers(
        method=method, host=host, key=key, region=region, creds=creds,
        query=query or {}, payload=payload, now=now, headers=headers, service=service,
    )
    signed_names = ";".join(sorted(h.lower() for h in all_headers))
    signature = _sign(creds, region, service, amz_date, date, cr)
    all_headers["Authorization"] = (
        f"AWS4-HMAC-SHA256 Credential={creds.access_key}/{_scope(date, region, service)}"
        f",SignedHeaders={signed_names},Signature={signature}"
    )
    return all_headers
