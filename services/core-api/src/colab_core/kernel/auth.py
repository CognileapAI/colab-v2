"""인증 주체 — 계약의 `sessionSubject` bearer 하나뿐이다.

계약이 이미 답했다(`fe-core.yaml` securitySchemes) — 자격증명 발급 방식은 정본에 없고,
v2 1차에서는 **개발자가 계정을 심어 제공한다**(P-17). 그래서 여기서 로그인 흐름을 만들지 않고,
심어 둔 토큰 표를 읽기만 한다. 실제 수단은 P1 이 정한다.

**`labId` 를 요청에서 받지 않는다.** 연구실 경계는 오직 이 주체에서 나온다
(CLAUDE.md §3-5 · P-9·P-10). 헤더로 lab_id 를 주입하는 임시 경로를 두지 않는다 —
그런 경로가 하나라도 있으면 경계 증명이 전부 무의미해진다.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

from .ids import Ulid


@dataclasses.dataclass(frozen=True)
class Subject:
    account_id: Ulid
    lab_id: Ulid


class SubjectRegistry:
    """토큰 → 주체. 심어 둔 표를 그대로 읽는다."""

    def __init__(self, table: dict[str, Subject]) -> None:
        self._table = table

    @classmethod
    def from_file(cls, path: str | None) -> "SubjectRegistry":
        if not path:
            return cls({})
        raw = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        table: dict[str, Subject] = {}
        for token, spec in raw.items():
            table[token] = Subject(
                account_id=Ulid(spec["accountId"]),
                lab_id=Ulid(spec["labId"]),
            )
        return cls(table)

    def resolve(self, token: str) -> Subject | None:
        return self._table.get(token)


def bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None
