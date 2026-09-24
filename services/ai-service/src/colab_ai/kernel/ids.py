"""정규 ID `Ulid` — 이 배포 단위의 코드 쪽 자리.

**값 정본은 `contracts/schemas/common.json#/$defs/Ulid`** 다 (`CLAUDE.md §3-6`).
배포 단위는 서로를 import 하지 않으므로(`import-boundary` units-independent) 다른 단위의
같은 파일을 가져다 쓸 수 없다 — **같은 정본을 각 단위가 한 번씩 옮겨 적는다.**
형태를 여기서 새로 정하지 않는다.
"""
from __future__ import annotations

import os
import re
import time

#: Crockford Base32 — I·L·O·U 를 뺀 32 글자. 위 정규식과 같은 집합이다.
_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
LENGTH = 26
PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


def is_valid_ulid(value: object) -> bool:
    return isinstance(value, str) and bool(PATTERN.match(value))


def new_ulid(now_ms: int | None = None) -> str:
    """시각 48비트 + 난수 80비트.

    ⚠ **이것은 저장된 무엇의 ID 가 아니다.** 계보 제안의 `suggestionId` 는 화면이 항목을
    구분하려고 쓰는 값일 뿐이고(`core-ai.yaml suggestLineage` 산문 축자), 이 단위에는
    저장이 없다 — 제안은 응답과 함께 죽는다 (`d10_suggestion` 머리말).
    """
    ms = int(time.time() * 1000) if now_ms is None else now_ms
    n = (ms << 80) | int.from_bytes(os.urandom(10), "big")
    out = []
    for _ in range(LENGTH):
        out.append(_ALPHABET[n & 0x1F])
        n >>= 5
    return "".join(reversed(out))
