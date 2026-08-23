"""정규 ID `Ulid` — 이 배포 단위의 코드 쪽 자리.

**값 정본은 `contracts/schemas/common.json#/$defs/Ulid`** 이고 DB 쪽은
`db/platform/schema.sql` 의 DOMAIN `ulid` 다(`CLAUDE.md §3-6`). 배포 단위는 서로를
import 하지 않으므로(`import-boundary` units-independent) core-api 의 `kernel/ids.py` 를
가져다 쓸 수 없다 — **같은 정본을 각 단위가 한 번씩 옮겨 적는다.** 형태를 여기서 새로
정하지 않는다.
"""
from __future__ import annotations

import os
import re
import time

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"   # Crockford Base32 (I·L·O·U 제외)
PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
LENGTH = 26


def is_valid(value: object) -> bool:
    return isinstance(value, str) and bool(PATTERN.match(value))


def new_ulid(now_ms: int | None = None) -> str:
    """시각 48비트 + 난수 80비트. 정렬 가능성이 원장 커서의 전제다."""
    ms = int(time.time() * 1000) if now_ms is None else now_ms
    n = (ms << 80) | int.from_bytes(os.urandom(10), "big")
    out = []
    for _ in range(LENGTH):
        out.append(_ALPHABET[n & 0x1F])
        n >>= 5
    return "".join(reversed(out))
