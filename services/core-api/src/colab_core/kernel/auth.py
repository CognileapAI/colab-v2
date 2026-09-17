"""인증 주체 — 계약의 `sessionSubject` bearer 하나뿐이다.

계약이 이미 답했다(`fe-core.yaml` securitySchemes) — 자격증명 발급 방식은 정본에 없고,
v2 1차에서는 **개발자가 계정을 심어 제공한다**(P-17). 그래서 여기서 로그인 흐름을 만들지 않고,
심어 둔 토큰 표를 읽기만 한다. 실제 수단은 P1 이 정한다.

인증 주체의 소속은 서버 자격에서만 나온다. 시스템 관리자의 작업 대상 연구실은
인증 주체를 바꾸지 않고 요청의 데이터베이스 스코프에서 별도로 검증한다.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

from .ids import Ulid


@dataclasses.dataclass(frozen=True)
class Subject:
    account_id: Ulid
    lab_id: Ulid | None
    must_change_password: bool = False
    credential_version: int | None = None
    #: 시스템 관리자 자격. 원본은 account_admin.service_operator이며 매 요청 다시 확인한다.
    #: 원소속 lab_id는 작업 대상 연구실을 선택해도 바꾸지 않는다.
    operator: bool = False


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
