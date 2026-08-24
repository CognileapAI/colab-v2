"""정규 ID `Ulid` — 이 배포 단위의 코드 쪽 자리.

**값 정본은 `contracts/schemas/common.json#/$defs/Ulid`** 다 (`CLAUDE.md §3-6`).
배포 단위는 서로를 import 하지 않으므로(`import-boundary` units-independent) 다른 단위의
같은 파일을 가져다 쓸 수 없다 — **같은 정본을 각 단위가 한 번씩 옮겨 적는다.**
형태를 여기서 새로 정하지 않는다.
"""
from __future__ import annotations

import re

PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


def is_valid_ulid(value: object) -> bool:
    return isinstance(value, str) and bool(PATTERN.match(value))
