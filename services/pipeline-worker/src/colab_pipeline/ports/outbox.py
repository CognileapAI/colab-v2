"""D5 원장 Port — `d5_*` 표를 만지는 유일한 표면 (`ports/lineage.py` 의 Protocol 패턴 승계).

두 개로 가른다. **이벤트 원장(outbox)** 과 **업로드 상태 원장**은 수명이 다르다 —
전자는 릴레이가 비우고, 후자는 reaper 가 만료로 지운다(`〈64〉-ⓒ`).

이 Port 의 실물은 `domains/d5_ingestion.SqlLedger` 이고, 시험 대역은
`tests/memory_ledger.MemoryLedger` 다. 대역이 실물보다 헐거우면 시험이 거짓말을 하므로
멱등 키 유일성은 **양쪽 다** 지킨다.
"""
from __future__ import annotations

from typing import Protocol


class EventLedgerPort(Protocol):
    def append_event(self, envelope: dict) -> bool:
        """outbox 에 한 행. **이미 있는 멱등 키면 False** 를 돌려주고 아무것도 안 만든다."""
        ...

    def unpublished(self, limit: int = 100) -> list[dict]:
        """아직 안 나간 이벤트 — 릴레이가 집는다."""
        ...

    def mark_published(self, event_id: str) -> None: ...


class UploadLedgerPort(Protocol):
    def load_upload(self, upload_id: str) -> dict | None: ...

    def record_file_axes_row(self, *, file_id: str, lab_id: str, upload_id: str,
                             file_name: str, storage_key: str,
                             carries_lat: bool, carries_lon: bool) -> None:
        """기준 격자 파일 행을 **세운다**(`〈69〉-⑴`). 갱신이 아니라 생성이다 —
        접수는 이 행을 만들지 않는다(축을 모르기 때문).

        축 두 불리언(`〈66〉`). **둘 다 false 면 거부한다** — 축이 빈 행을 만들지 않는다.
        """
        ...

    def record_detected_format(self, file_id: str, fmt: str | None) -> None: ...

    def record_status(self, upload_id: str, **fields) -> None: ...

    def expire(self, now=None) -> list[str]:
        """만료된 미등록 업로드를 지운다. 지워진 uploadId 목록을 돌려준다."""
        ...
