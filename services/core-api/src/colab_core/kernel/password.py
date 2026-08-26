"""비밀번호 검증 — **평문을 저장하지 않는다** (Ted 2026-08-26 필수 취급 조건 1).

## 왜 scrypt 인가

표준 KDF 이고(RFC 7914) **파이썬 표준 라이브러리에 있다**(`hashlib.scrypt`, OpenSSL 경유).
bcrypt·argon2 는 새 의존성을 들이고, 이 회차는 배포 단위의 의존 목록을 늘리지 않는 것이 낫다.
필요해지면 여기 한 파일만 바뀐다 — `kdf` 값으로 갈라 두었다.

## 저장 형태

자격 파일 한 줄에 `kdf`·`salt`·`hash`·`n`·`r`·`p` 가 함께 들어간다. **파라미터를 코드에 박지
않는 이유**는 세기를 올릴 때 옛 자격이 통째로 못 쓰게 되지 않게 하기 위해서다.

## 적지 않는 것

**평문 비밀번호는 로그·오류 메시지·예외 문자열 어디에도 넣지 않는다.** 이 파일의 함수는
비밀번호를 인자로만 받고, 실패해도 그 값을 담은 메시지를 만들지 않는다.
"""
from __future__ import annotations

import base64
import dataclasses
import hashlib
import hmac
import os

KDF_SCRYPT = "scrypt"

#: 초기 파라미터. `n` 은 2 의 거듭제곱이어야 한다. 값의 근거는 RFC 7914 의 상호작용용 권장선이며
#: **[정본 무근거]** 다 — 정본은 비밀번호 자체를 다루지 않는다.
DEFAULT_N = 16384
DEFAULT_R = 8
DEFAULT_P = 1
DKLEN = 32
SALT_BYTES = 16


@dataclasses.dataclass(frozen=True)
class PasswordHash:
    kdf: str
    salt: str      # base64
    digest: str    # base64
    n: int = DEFAULT_N
    r: int = DEFAULT_R
    p: int = DEFAULT_P

    def as_dict(self) -> dict:
        return {"kdf": self.kdf, "salt": self.salt, "hash": self.digest,
                "n": self.n, "r": self.r, "p": self.p}

    @classmethod
    def from_dict(cls, raw: dict) -> "PasswordHash":
        return cls(kdf=raw["kdf"], salt=raw["salt"], digest=raw["hash"],
                   n=int(raw.get("n", DEFAULT_N)), r=int(raw.get("r", DEFAULT_R)),
                   p=int(raw.get("p", DEFAULT_P)))


def _derive(password: str, salt: bytes, *, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=DKLEN)


def hash_password(password: str, *, n: int = DEFAULT_N, r: int = DEFAULT_R,
                  p: int = DEFAULT_P) -> PasswordHash:
    if not password:
        raise ValueError("빈 비밀번호를 해시하지 않는다.")
    salt = os.urandom(SALT_BYTES)
    digest = _derive(password, salt, n=n, r=r, p=p)
    return PasswordHash(kdf=KDF_SCRYPT,
                        salt=base64.b64encode(salt).decode("ascii"),
                        digest=base64.b64encode(digest).decode("ascii"),
                        n=n, r=r, p=p)


def verify_password(password: str, stored: PasswordHash) -> bool:
    """맞으면 True. **틀린 이유를 돌려주지 않는다.**"""
    if stored.kdf != KDF_SCRYPT:
        # 모르는 KDF 는 **거부**한다. 「모르니까 통과」는 fail-open 이다.
        return False
    try:
        salt = base64.b64decode(stored.salt)
        expected = base64.b64decode(stored.digest)
        actual = _derive(password, salt, n=stored.n, r=stored.r, p=stored.p)
    except Exception:
        return False
    return hmac.compare_digest(actual, expected)
