"""AWS 자격증명 공급자 — 환경변수 → ECS → EC2 IMDSv2 순서.

표준 라이브러리(`urllib.request`)만 쓴다. 만료 5분 전까지 캐시하고,
캐시 갱신은 `threading.Lock` 으로 보호한다 — FastAPI 가 동기 라우트를
스레드풀에서 실행하므로 동시 접근이 실제로 발생한다.

`effective_ttl()` 은 프리사인드 URL 의 수명을 자격증명 만료 안쪽으로 클램프한다.
임시 자격증명으로 서명한 URL 은 자격증명이 만료되는 순간 함께 죽는다 —
이걸 계산하지 않으면 배포 후에만 재현되는 간헐적 403 이 된다.

⚠ 세 배포 단위가 **같은 바이트**로 갖는 파일이다 — 정본은 core-api 의 `kernel/aws_credentials.py`
이고, pipeline-worker·viz-render 의 같은 이름 파일은 `contracts/codegen/manifest.toml` 에 등기된
복제본이다(`generated-up-to-date` 게이트가 드리프트를 잡는다). 배포 단위끼리 import 하지
않으므로(`import-boundary` units-independent) 공유 라이브러리로 빼지 않는다. 그래서 형제
모듈은 **상대 import** 로만 부른다 — 패키지 절대 경로가 들어가면 복제본이 깨진다. 고칠 때는
core-api 원본을 고치고 **같은 커밋에** 재생성한다. 위 FastAPI 언급은 core-api 원본 기준이다.
"""
from __future__ import annotations

import json
import os
import threading
import urllib.request
from datetime import datetime, timedelta, timezone

from .sigv4 import MAX_PRESIGN_TTL, Credentials

_ECS_BASE = "http://169.254.170.2"
_IMDS_BASE = "http://169.254.169.254"
_TIMEOUT = 1.0  # 초 — 실패하면 다음 공급자로

_lock = threading.Lock()
_cached: tuple[Credentials, str] | None = None


def clear_cache() -> None:
    global _cached
    with _lock:
        _cached = None


def effective_ttl(configured: int, creds: Credentials, now: datetime) -> int:
    """프리사인 TTL 을 `min(설정값, 자격증명 만료 - 60초)` 로 클램프. 바닥은 60초."""
    if creds.expires_at is None:
        return min(configured, MAX_PRESIGN_TTL)
    headroom = int((creds.expires_at - now).total_seconds()) - 60
    return max(60, min(configured, headroom, MAX_PRESIGN_TTL))


def load_credentials(now: datetime | None = None) -> tuple[Credentials, str]:
    """(자격증명, 출처) 를 돌려준다. 출처는 'env' | 'ecs' | 'imds'.

    어느 공급자에서도 못 얻으면 RuntimeError — 기본값을 코드에 두지 않는다.
    """
    global _cached
    now = now or datetime.now(timezone.utc)
    with _lock:
        if _cached is not None:
            creds, _source = _cached
            if creds.expires_at is None or creds.expires_at - now > timedelta(minutes=5):
                return _cached
        for provider in (_from_env, _from_ecs, _from_imds):
            got = provider()
            if got is not None:
                _cached = got
                return got
    raise RuntimeError(
        "AWS 자격증명을 찾지 못했다 — AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY 환경변수, "
        "ECS 컨테이너 자격증명, EC2 IMDSv2 를 순서대로 시도했다. 설정 방법: dev-package/S3.md §1."
    )


def _from_env() -> tuple[Credentials, str] | None:
    # ⚠ **배포된 서버의 env 에 액세스 키를 넣지 않는다.** EC2 는 IAM 역할이 IMDSv2 로 임시
    #    자격증명을 준다. 키를 넣으면 이 분기가 **먼저 잡혀** 역할이 무의미해지고,
    #    `effective_ttl()` 의 프리사인드 TTL 클램프도 함께 무의미해진다(만료가 없는 키라
    #    클램프할 대상이 없다). 이 분기는 **로컬 도구용**이다.
    ak = os.environ.get("AWS_ACCESS_KEY_ID")
    sk = os.environ.get("AWS_SECRET_ACCESS_KEY")
    if not ak or not sk:
        return None
    token = os.environ.get("AWS_SESSION_TOKEN") or None
    return Credentials(access_key=ak, secret_key=sk, session_token=token), "env"


def _http(url: str, *, method: str = "GET", req_headers: dict[str, str] | None = None) -> str:
    req = urllib.request.Request(url, method=method, headers=req_headers or {})
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310 — 링크로컬 고정 주소
        return resp.read().decode("utf-8")


def _parse_role_creds(body: str) -> Credentials:
    data = json.loads(body)
    expires = datetime.fromisoformat(data["Expiration"].replace("Z", "+00:00"))
    return Credentials(
        access_key=data["AccessKeyId"],
        secret_key=data["SecretAccessKey"],
        session_token=data.get("Token") or data.get("SessionToken"),
        expires_at=expires,
    )


def _from_ecs() -> tuple[Credentials, str] | None:
    relative = os.environ.get("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
    if not relative:
        return None
    try:
        return _parse_role_creds(_http(_ECS_BASE + relative)), "ecs"
    except Exception:
        return None


def _from_imds() -> tuple[Credentials, str] | None:
    try:
        token = _http(
            f"{_IMDS_BASE}/latest/api/token", method="PUT",
            req_headers={"x-aws-ec2-metadata-token-ttl-seconds": "21600"},
        )
        auth = {"x-aws-ec2-metadata-token": token}
        role = _http(
            f"{_IMDS_BASE}/latest/meta-data/iam/security-credentials/", req_headers=auth
        ).strip().splitlines()[0]
        body = _http(
            f"{_IMDS_BASE}/latest/meta-data/iam/security-credentials/{role}", req_headers=auth
        )
        return _parse_role_creds(body), "imds"
    except Exception:
        return None
