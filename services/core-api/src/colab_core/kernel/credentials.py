"""자격 파일 — 계정 이름 → 주체 + **비밀번호 해시** (Ted 2026-08-26).

## 주체 표와 갈라 두는 이유

주체 표(`COLAB_CORE_SUBJECTS_FILE`)는 **토큰이 곧 자격**인 표라 도구·시험이 그 값을 그대로
쓴다. 비밀번호 해시를 그 표에 섞으면 두 성격이 한 파일에 앉고, 한쪽을 배포하다 다른 쪽이
같이 새는 자리가 된다. **파일을 나누면 권한(`0600`)과 배포 경로도 나눌 수 있다.**

## 파일 형태 (평문 없음)

```json
{
  "colab": {
    "accountId": "…26자…", "labId": "…26자…",
    "kdf": "scrypt", "salt": "<base64>", "hash": "<base64>", "n": 16384, "r": 8, "p": 1
  }
}
```

**평문 비밀번호가 들어갈 칸이 없다.** 값을 심고 바꾸는 자리는 `ops/set-password.py` 하나이고,
그 스크립트가 `0600` 으로 쓴다 (`〈93〉` 비밀 취급).

## 이 파일이 하지 않는 것

계정을 만들지 않는다 (P-17). 여기 없는 이름은 그냥 **없는 것**이고, 그 사실을 밖으로
흘리지도 않는다 — 판정은 `authn.PasswordIssuer` 가 한다.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

from .auth import Subject
from .ids import Ulid
from .password import PasswordHash, hash_password, verify_password

#: 없는 계정에도 같은 일을 시키기 위한 대역 해시. 값은 프로세스마다 다르고 쓰이지 않는다.
_DUMMY = hash_password("존재하지-않는-자격")


@dataclasses.dataclass(frozen=True)
class CredentialRecord:
    subject: Subject
    password: PasswordHash


class CredentialStore:
    def __init__(self, table: dict[str, CredentialRecord]) -> None:
        self._table = table

    @property
    def empty(self) -> bool:
        return not self._table

    @classmethod
    def from_file(cls, path: str | None) -> "CredentialStore":
        if not path:
            return cls({})
        file = pathlib.Path(path)
        if not file.exists():
            # **없는 파일을 빈 표로 넘기지 않는다** — 경로 오타가 「비밀번호 로그인이 조용히
            # 사라진 배포」가 되고, 그 증상은 401 하나뿐이라 원인을 못 찾는다.
            raise RuntimeError(f"자격 파일이 없다: {path}")
        raw = json.loads(file.read_text(encoding="utf-8"))
        table: dict[str, CredentialRecord] = {}
        for name, spec in raw.items():
            table[name] = CredentialRecord(
                subject=Subject(account_id=Ulid(spec["accountId"]),
                                lab_id=Ulid(spec["labId"])),
                password=PasswordHash.from_dict(spec),
            )
        return cls(table)

    def find(self, account_name: str) -> CredentialRecord | None:
        return self._table.get(account_name)

    def dummy_verify(self, password: str) -> None:
        """없는 계정에도 같은 계산을 태운다 — 응답 시간으로 존재 여부가 새지 않게."""
        verify_password(password, _DUMMY)
