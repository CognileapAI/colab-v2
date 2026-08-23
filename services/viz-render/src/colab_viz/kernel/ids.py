"""ULID — 정규 ID 타입 (`contracts/schemas/common.json#/$defs/Ulid`).

정의 자리는 계약이고 여기는 그 규격을 만족하는 값을 만드는 자리다:
Crockford base32 26 자, 앞 10 자가 밀리초 시각이라 사전순 = 시간순이다.
"""
from __future__ import annotations

import os
import re
import time

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


def _encode(value: int, length: int) -> str:
    out = []
    for _ in range(length):
        out.append(_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


def new_ulid() -> str:
    return _encode(int(time.time() * 1000), 10) + _encode(
        int.from_bytes(os.urandom(10), "big"), 16)


def is_ulid(value: str) -> bool:
    return bool(ULID_RE.match(value or ""))
