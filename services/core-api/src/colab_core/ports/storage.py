"""업로드 바이트 저장 Port — 로컬 디스크와 S3 가 갈리는 유일한 이음새.

패턴은 `ports/ingestion.py` 를 승계한다 — Protocol 하나, 구현은 배선 층
(`kernel/storage_backends.py`)에. 저장 **키**의 정본은 여전히
`contracts/storage/layout.json`(생성물 `kernel/storage_layout`)이고, 이 Port 는
그 키가 가리키는 바이트를 **어디에 두는가**만 가른다 (`PLAN-SoT §9 〈173〉`).

네 동작이 전부다 — 라우트(`routes/ingestion.py`)가 바이트를 만지는 자리가
이 네 호출로 봉인돼 있기 때문이다. `put`(바이트열)과 `put_stream`(파일 객체)은 같은
결과를 내고, 라우트는 **`put_stream` 을 쓴다** — 업로드 본문을 통째로 메모리에 올리지
않기 위해서다 (`PLAN-SoT §9 〈175〉`). `put` 은 남겨 둔다(시험·소규모 쓰기).
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import BinaryIO, Protocol

from .ingestion import UploadFileRecord


class UploadStoragePort(Protocol):
    def put(self, *, key: str, payload: bytes) -> None:
        """키 자리에 바이트를 놓는다. 이미 있으면 덮어쓴다."""
        ...

    def put_stream(self, *, key: str, stream: BinaryIO) -> int:
        """키 자리에 스트림의 바이트를 놓고 **놓은 바이트 수**를 돌려준다.

        스트림은 시작 위치에 있어야 한다. 이미 있으면 덮어쓴다. 백엔드가 진짜 스트리밍을
        못 하면(S3 — SigV4 가 본문 전체 해시를 서명에 넣는다) 안에서 읽어 모으되,
        그 사실은 구현 주석이 말한다 — 이 Port 의 약속은 「반환값이 저장된 크기」뿐이다.
        """
        ...

    def discard(self, *, key: str | None, keep: str | None = None) -> None:
        """키의 바이트를 치운다. 없는 것은 조용히 넘어간다 — 이미 없는 것을
        지우지 못했다고 200 을 500 으로 바꾸지 않는다. `keep` 과 같으면 안 지운다."""
        ...

    def relocate(self, *, files: Sequence[UploadFileRecord],
                 new_keys: dict[str, str]) -> None:
        """등록 전환·후주입에서 바이트를 데이터셋 자리로 옮긴다.

        모든 판정이 끝난 뒤 마지막에 불린다. 원본이 이미 없으면 그 파일은
        건너뛴다(원장은 새 자리를 적는다 — 두 자리를 만들지 않는다).
        도중 실패하면 옮긴 것을 되돌리고 예외를 다시 던진다.
        """
        ...
