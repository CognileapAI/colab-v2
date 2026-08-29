"""다운로드 서명 티켓 — 무상태 · HMAC-SHA256 · 수명 10분 (`PLAN-SoT §9 〈175〉-(다)`).

왜 티켓인가
  브라우저가 파일을 저장하려면 내비게이션(`<a href>`·`window.location`)으로 받아야 하고
  거기에는 Bearer 가 실리지 않는다. 그래서 `getDownloadBytes` 는 `security: []` 이고
  **티켓이 곧 자격**이다 — URL 이 자격이고 수명이 노출 창이다 (`fe-core.yaml` 산문).

왜 무상태인가
  `session_token.py` 와 같은 이유다 — 저장 표를 두면 스키마가 하나 붙는다. 서명이 곧 검증이다.
  포기한 것도 같다: **만료 전 조기 회수가 없다.** 대신 바이트 시점에 경계·`body_access` 를
  **다시 판정**하므로(라우트 + RLS), 접근이 회수된 티켓은 서명이 맞아도 404 다.

수명이 상수(10분)인 이유
  경로 티켓은 nginx 접근 로그·브라우저 이력에 그대로 남는다. 짧을수록 좋고, 운영 설정으로
  늘릴 수 있게 두면 언젠가 늘어난다. `[정본 무근거]` — 정본은 다운로드 수명을 말하지 않는다.

형식
  `d1.<payload b64url>.<hmac b64url>` — payload 는 `{ds, f, lab, sub, exp, scope}` 만 담는다.
  `f` 가 null 이면 묶음(zip), 값이면 그 조각 하나. 키는 `Settings.session_secret` 하나를 같이 쓴다 —
  비밀값이 없으면 발급기가 서지 않고 라우트가 503 을 낸다(조용한 기본값 없음).
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

PREFIX = "d1"
#: 티켓 수명. 상수다 — 위 머리말이 이유를 적었다.
TTL_SECONDS = 600

SCOPE_BUNDLE = "묶음"
SCOPE_FILE = "파일"


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class TicketInvalid(ValueError):
    """형식·서명·내용 어느 하나라도 어긋난다. 이유를 밖으로 흘리지 않는다 — 라우트는 404."""


class TicketExpired(ValueError):
    """서명은 맞는데 수명이 지났다 — 라우트는 410."""


@dataclasses.dataclass(frozen=True)
class DownloadClaims:
    dataset_id: Ulid
    file_id: Ulid | None          #: None = 데이터셋 묶음(zip)
    lab_id: Ulid
    account_id: Ulid
    expires_at: dt.datetime

    @property
    def scope(self) -> str:
        return SCOPE_BUNDLE if self.file_id is None else SCOPE_FILE

    @property
    def subject(self) -> Subject:
        """바이트 시점에 경계를 **다시** 심을 주체 — 발급 시점의 그 사람이다."""
        return Subject(account_id=self.account_id, lab_id=self.lab_id)


@dataclasses.dataclass(frozen=True)
class IssuedTicket:
    ticket: str
    expires_at: dt.datetime


class DownloadTicketSigner:
    """서명·검증 한 쌍. 비밀값은 설정에서만 온다 — 코드에 기본값을 두지 않는다."""

    def __init__(self, secret: str) -> None:
        if not secret:
            raise ValueError("서명 비밀값이 비었다 — 서명 없는 티켓을 만들지 않는다.")
        self._secret = secret.encode("utf-8")

    def _mac(self, payload: str) -> str:
        return _b64(hmac.new(self._secret, payload.encode("ascii"), hashlib.sha256).digest())

    def issue(self, *, dataset_id: Ulid, file_id: Ulid | None, subject: Subject,
              now: dt.datetime | None = None) -> IssuedTicket:
        now = now or dt.datetime.now(dt.timezone.utc)
        expires_at = (now + dt.timedelta(seconds=TTL_SECONDS)).replace(microsecond=0)
        body = json.dumps(
            {"ds": str(dataset_id), "f": None if file_id is None else str(file_id),
             "lab": str(subject.lab_id), "sub": str(subject.account_id),
             "exp": int(expires_at.timestamp()),
             "scope": SCOPE_BUNDLE if file_id is None else SCOPE_FILE},
            separators=(",", ":"), sort_keys=True, ensure_ascii=False,
        )
        payload = _b64(body.encode("utf-8"))
        return IssuedTicket(f"{PREFIX}.{payload}.{self._mac(payload)}", expires_at)

    def verify(self, ticket: str, *, now: dt.datetime | None = None) -> DownloadClaims:
        """서명이 먼저, 만료는 그 다음이다 — 서명이 틀린 티켓의 만료를 말해 주지 않는다."""
        now = now or dt.datetime.now(dt.timezone.utc)
        parts = ticket.split(".")
        if len(parts) != 3 or parts[0] != PREFIX or not parts[1] or not parts[2]:
            raise TicketInvalid()
        _, payload, mac = parts
        # 상수 시간 비교 — 서명 검증에서 조기 반환은 타이밍 정보를 흘린다.
        if not hmac.compare_digest(mac, self._mac(payload)):
            raise TicketInvalid()
        try:
            claims = json.loads(_unb64(payload).decode("utf-8"))
            dataset_id, file_id = claims["ds"], claims["f"]
            lab_id, account_id, exp = claims["lab"], claims["sub"], int(claims["exp"])
            scope = claims["scope"]
        except Exception:
            raise TicketInvalid() from None
        if not (Ulid.is_valid(dataset_id) and Ulid.is_valid(lab_id) and Ulid.is_valid(account_id)):
            raise TicketInvalid()
        if file_id is not None and not Ulid.is_valid(file_id):
            raise TicketInvalid()
        if scope != (SCOPE_BUNDLE if file_id is None else SCOPE_FILE):
            raise TicketInvalid()
        if exp <= int(now.timestamp()):
            raise TicketExpired()
        return DownloadClaims(
            dataset_id=Ulid(dataset_id), file_id=None if file_id is None else Ulid(file_id),
            lab_id=Ulid(lab_id), account_id=Ulid(account_id),
            expires_at=dt.datetime.fromtimestamp(exp, tz=dt.timezone.utc),
        )
