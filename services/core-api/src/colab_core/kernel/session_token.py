"""무상태 서명 세션 토큰 — **세션 표를 만들지 않는다** (`PLAN-SoT §9 〈90〉-㉯`).

왜 무상태인가
  세션 표를 두면 P0 스키마에 마이그레이션이 하나 붙고, 그 순간 이 회차는 「스키마 변경 필요」로
  중단해야 한다(Ted 2026-08-26 중단 조건 1). 서명 토큰은 **주체를 토큰 안에 담고 서버가
  서명만 검증**하므로 표가 필요 없다.

무엇을 포기했는가 — 감추지 않는다
  만료 전 **조기 회수가 불가능하다.** 서버가 「이 토큰은 죽었다」고 기록할 자리가 없기 때문이다.
  로그아웃은 화면이 토큰을 버리는 것이고, 서버는 만료까지 그 서명을 계속 유효로 본다
  (`fe-core.yaml endSession` 산문 · `〈90〉-㉳`). 회수가 필요해지면 그때 세션 표를 WU 로 연다.

형식
  `v1.<payload b64url>.<hmac b64url>` — payload 는 `{"sub", "lab", "exp"}` 만 담는다.
  이름·역할·권한 스위치를 담지 않는다. 그것들은 언제나 `GET /me` 가 DB 에서 읽는다
  (P-6·P-7 — 화면도 토큰도 권한을 재계산하지 않는다).
"""
from __future__ import annotations

import base64
import dataclasses
import datetime as dt
import hashlib
import hmac
import json

from .auth import Subject
from .ids import Ulid

PREFIX = "v1"


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


@dataclasses.dataclass(frozen=True)
class IssuedSession:
    token: str
    expires_at: dt.datetime


class SessionSigner:
    """서명·검증 한 쌍. 비밀값은 설정에서만 온다 — 코드에 기본값을 두지 않는다."""

    def __init__(self, secret: str, *, ttl_minutes: int) -> None:
        if not secret:
            raise ValueError("세션 비밀값이 비었다 — 서명 없는 세션을 만들지 않는다.")
        if ttl_minutes <= 0:
            raise ValueError(f"세션 수명은 1 이상이어야 한다: {ttl_minutes}")
        self._secret = secret.encode("utf-8")
        self._ttl = dt.timedelta(minutes=ttl_minutes)

    def _mac(self, payload: str) -> str:
        return _b64(hmac.new(self._secret, payload.encode("ascii"), hashlib.sha256).digest())

    def issue(self, subject: Subject, *, now: dt.datetime | None = None) -> IssuedSession:
        now = now or dt.datetime.now(dt.timezone.utc)
        expires_at = (now + self._ttl).replace(microsecond=0)
        body = json.dumps(
            {"sub": str(subject.account_id), "lab": str(subject.lab_id),
             "exp": int(expires_at.timestamp())},
            separators=(",", ":"), sort_keys=True,
        )
        payload = _b64(body.encode("utf-8"))
        return IssuedSession(f"{PREFIX}.{payload}.{self._mac(payload)}", expires_at)

    def verify(self, token: str, *, now: dt.datetime | None = None) -> Subject | None:
        """서명·만료 어느 하나라도 어긋나면 **None**. 이유를 밖으로 흘리지 않는다."""
        now = now or dt.datetime.now(dt.timezone.utc)
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != PREFIX:
            return None
        _, payload, mac = parts
        # 상수 시간 비교 — 서명 검증에서 조기 반환은 타이밍 정보를 흘린다.
        if not hmac.compare_digest(mac, self._mac(payload)):
            return None
        try:
            claims = json.loads(_unb64(payload).decode("utf-8"))
            account_id, lab_id, exp = claims["sub"], claims["lab"], int(claims["exp"])
        except Exception:
            return None
        if exp <= int(now.timestamp()):
            return None
        if not Ulid.is_valid(account_id) or not Ulid.is_valid(lab_id):
            return None
        return Subject(account_id=Ulid(account_id), lab_id=Ulid(lab_id))
