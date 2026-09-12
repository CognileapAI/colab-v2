"""서버 원장에 묶인 브라우저 세션과 과도기 무상태 토큰 서명.

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
DATABASE_PREFIX = "db1"
TRACKED_PREFIX = "ss1"
_KINDS = frozenset(("database", "planted-code", "legacy-file"))
_PURPOSES = frozenset(("normal", "password-change"))


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


@dataclasses.dataclass(frozen=True)
class IssuedSession:
    token: str
    expires_at: dt.datetime


@dataclasses.dataclass(frozen=True)
class TrackedSessionClaims:
    subject: Subject
    session_id: Ulid
    expires_at: dt.datetime
    generation: int
    credential_kind: str
    purpose: str
    credential_version: int | None
    #: 발급 시점의 운영자 여부. **판정 입력이 아니라 기록**이다 — 매 요청의 판정은
    #: `service_operator` 재조회가 하고, 여기 값과 어긋나면 그 세션을 거절한다.
    operator: bool = False


@dataclasses.dataclass(frozen=True)
class DatabaseSessionClaims:
    subject: Subject
    must_change_password: bool
    session_version: int


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
        # ⚠ **ASCII 인지 먼저 본다** (`CODE-REVIEW-20260903` #12). 토큰은
        # `v1.<b64url>.<b64url>` 이라 **구성상 ASCII 다.** 그런데 `_mac` 의
        # `.encode("ascii")` 가 아래 `try` 밖에 있어, 비ASCII Bearer 하나가
        # `UnicodeEncodeError` 로 탈출해 **비인증 요청이 500** 을 냈다 — 인증 경계에서
        # 토큰 모양 하나로 오류율을 올릴 수 있다는 뜻이다. 인증 실패는 **401** 이다.
        if not token.isascii():
            return None
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

    def issue_tracked(
        self,
        subject: Subject,
        *,
        session_id: Ulid,
        generation: int,
        credential_kind: str,
        purpose: str,
        credential_version: int | None,
        expires_at: dt.datetime,
        operator: bool = False,
    ) -> IssuedSession:
        if credential_kind not in _KINDS or purpose not in _PURPOSES:
            raise ValueError("unknown tracked session kind or purpose")
        if generation < 1:
            raise ValueError("session generation must be positive")
        if credential_kind == "database" and credential_version is None:
            raise ValueError("database session requires credential version")
        if credential_kind != "database" and credential_version is not None:
            raise ValueError("non-database session cannot carry credential version")
        body = {
            "sid": str(session_id),
            "sub": str(subject.account_id),
            "lab": str(subject.lab_id),
            "exp": int(expires_at.timestamp()),
            "generation": generation,
            "credential_kind": credential_kind,
            "purpose": purpose,
        }
        if credential_version is not None:
            body["credential_version"] = credential_version
        # 거짓일 때는 칸 자체를 두지 않는다 — 「없음」과 「거짓」을 갈라 둘 이유가 없고,
        # 칸을 비워 두면 옛 토큰과 같은 모양이라 판정이 한 갈래로 모인다.
        if operator:
            body["operator"] = True
        payload = _b64(json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        mac = _b64(hmac.new(
            self._secret, f"{TRACKED_PREFIX}.{payload}".encode("ascii"), hashlib.sha256
        ).digest())
        return IssuedSession(f"{TRACKED_PREFIX}.{payload}.{mac}", expires_at)

    def verify_tracked(
        self, token: str, *, now: dt.datetime | None = None
    ) -> TrackedSessionClaims | None:
        now = now or dt.datetime.now(dt.timezone.utc)
        if not token.isascii():
            return None
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != TRACKED_PREFIX:
            return None
        _, payload, mac = parts
        expected = _b64(hmac.new(
            self._secret, f"{TRACKED_PREFIX}.{payload}".encode("ascii"), hashlib.sha256
        ).digest())
        if not hmac.compare_digest(mac, expected):
            return None
        try:
            raw = json.loads(_unb64(payload).decode("utf-8"))
            account_id, lab_id, sid = raw["sub"], raw["lab"], raw["sid"]
            exp, generation = int(raw["exp"]), int(raw["generation"])
            kind, purpose = raw["credential_kind"], raw["purpose"]
            version = raw.get("credential_version")
            version = int(version) if version is not None else None
            operator = raw.get("operator", False)
        except Exception:
            return None
        if operator is not True and operator is not False:
            return None
        if (exp <= int(now.timestamp()) or generation < 1 or kind not in _KINDS
                or purpose not in _PURPOSES):
            return None
        if (kind == "database") != (version is not None):
            return None
        if version is not None and version < 1:
            return None
        if not all(Ulid.is_valid(value) for value in (account_id, lab_id, sid)):
            return None
        return TrackedSessionClaims(
            subject=Subject(Ulid(account_id), Ulid(lab_id)),
            session_id=Ulid(sid),
            expires_at=dt.datetime.fromtimestamp(exp, tz=dt.timezone.utc),
            generation=generation,
            credential_kind=kind,
            purpose=purpose,
            credential_version=version,
            operator=operator,
        )


class DatabaseSessionSigner(SessionSigner):
    """DB 자격 전용 토큰. 기존 v1 검증기가 추가 claim을 무시해도 prefix가 갈린다."""

    def issue(self, credential, *, now: dt.datetime | None = None) -> IssuedSession:
        now = now or dt.datetime.now(dt.timezone.utc)
        expires_at = (now + self._ttl).replace(microsecond=0)
        body = json.dumps({
            "sub": str(credential.subject.account_id),
            "lab": str(credential.subject.lab_id),
            "exp": int(expires_at.timestamp()),
            "purpose": "password-change" if credential.must_change_password else "session",
            "version": credential.session_version,
        }, separators=(",", ":"), sort_keys=True)
        payload = _b64(body.encode("utf-8"))
        return IssuedSession(f"{DATABASE_PREFIX}.{payload}.{self._database_mac(payload)}", expires_at)

    def verify(self, token: str, *, now: dt.datetime | None = None) -> DatabaseSessionClaims | None:
        now = now or dt.datetime.now(dt.timezone.utc)
        if not token.isascii():
            return None
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != DATABASE_PREFIX:
            return None
        _, payload, mac = parts
        if not hmac.compare_digest(mac, self._database_mac(payload)):
            return None
        try:
            claims = json.loads(_unb64(payload).decode("utf-8"))
            account_id, lab_id = claims["sub"], claims["lab"]
            exp, version = int(claims["exp"]), int(claims["version"])
            purpose = claims["purpose"]
        except Exception:
            return None
        if exp <= int(now.timestamp()) or version < 1:
            return None
        if purpose not in ("session", "password-change"):
            return None
        if not Ulid.is_valid(account_id) or not Ulid.is_valid(lab_id):
            return None
        return DatabaseSessionClaims(
            Subject(Ulid(account_id), Ulid(lab_id)),
            purpose == "password-change", version)
    def _database_mac(self, payload: str) -> str:
        return _b64(hmac.new(self._secret, f"{DATABASE_PREFIX}.{payload}".encode("ascii"),
                             hashlib.sha256).digest())
