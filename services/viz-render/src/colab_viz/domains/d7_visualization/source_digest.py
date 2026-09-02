"""원본을 가리키는 값 — 캐시 키의 재료 (`§7.2` 「원본 해시」 · `PLAN-SoT §9 〈281〉-㉴`).

⚠ **내용 해시가 아니다.** 500 MB 를 렌더마다 다시 읽는 비용을 아직 안 쟀다 — `[미측정]`.

두 규칙이 공존한다 —
- 파일시스템 조각(`version` 없음) = `(이름, 크기, mtime_ns)`. **종전 그대로** — 배포된 미리보기의
  캐시 키가 이 변경으로 바뀌면 staging 의 산출물이 전부 무효화된다.
- 객체 저장소 조각(`version` = ETag) = `(이름, 크기, ETag)`. 내려받은 파일의 mtime 은 내려받을 때마다
  새로 찍히므로 그것을 키에 넣으면 **같은 객체를 렌더마다 새 키로 굽고 `previews/` 가 무한히 는다** —
  어드바이저가 잡은 결함이고, 이 모듈이 그 자리다.
"""
from __future__ import annotations

import hashlib
from collections.abc import Iterable

from ...ports.source import SourcePart


def source_digest(parts: Iterable[SourcePart]) -> str:
    h = hashlib.sha256()
    for p in sorted(parts, key=lambda p: p.file_name):
        if p.version is not None:
            h.update(f"{p.file_name}|{p.size_bytes}|{p.version}|".encode())
        else:
            st = p.path.stat()
            h.update(f"{p.file_name}|{st.st_size}|{st.st_mtime_ns}|".encode())
    return h.hexdigest()
