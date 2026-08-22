"""정규 ID 타입 `Ulid` — 코드 쪽 유일한 정의 자리 (CLAUDE.md §3-6).

값 정본은 `contracts/schemas/common.json#/$defs/Ulid` 이고, DB 쪽은
`db/platform/schema.sql` 의 DOMAIN `ulid` 다. 이 모듈은 그 정본을 코드 층으로 옮겨 적는다 —
v1 의 #1 함정(`users.id` 를 String(20/30/36) 으로 제각각 선언)을 원천 차단한다.

여기 말고 어디서도 ID 형태를 다시 선언하지 않는다.
"""
from __future__ import annotations

import os
import re
import time

# Crockford Base32 — I·L·O·U 를 뺀 32 글자. 정본 정규식과 같은 집합이다.
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
LENGTH = 26


class Ulid(str):
    """26 자 Crockford Base32 문자열. 만들 때 검증하므로 잘못된 값이 도는 일이 없다."""

    __slots__ = ()

    def __new__(cls, value: str) -> "Ulid":
        if not isinstance(value, str) or not PATTERN.match(value):
            raise ValueError(f"정규 ID 가 아니다 (26자 Crockford Base32): {value!r}")
        return super().__new__(cls, value)

    @classmethod
    def is_valid(cls, value: object) -> bool:
        return isinstance(value, str) and bool(PATTERN.match(value))

    @classmethod
    def generate(cls, now_ms: int | None = None) -> "Ulid":
        """시각 48비트 + 난수 80비트. 정렬 가능성이 목록 커서의 전제다."""
        ms = int(time.time() * 1000) if now_ms is None else now_ms
        rand = int.from_bytes(os.urandom(10), "big")
        n = (ms << 80) | rand
        out = []
        for _ in range(LENGTH):
            out.append(_ALPHABET[n & 0x1F])
            n >>= 5
        return cls("".join(reversed(out)))
