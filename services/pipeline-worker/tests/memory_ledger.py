"""메모리 원장 — `ports.outbox` 두 Port 의 시험용 구현.

실물은 `domains.d5_ingestion.SqlLedger`(`d5_*` 표)다. 이 대역은 **같은 Port 를 만족**하되
DB 없이 돈다. 멱등 키 유일 제약도 흉내낸다 — 대역이 실물보다 헐거우면 시험이 거짓말을 한다.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


class MemoryLedger:
    def __init__(self) -> None:
        self.uploads: dict[str, dict] = {}
        self.events: list[dict] = []
        self._keys: set[str] = set()
        self.axes: dict[str, tuple[bool, bool]] = {}
        self.formats: dict[str, str | None] = {}
        #: `d5_upload_file` 행. **접수는 격자 파일 행을 만들지 않는다**(`〈69〉-⑴`) —
        #: 그래서 `accept()` 는 이 사전을 비워 둔 채 시작한다.
        self.file_rows: dict[str, dict] = {}

    # ── 접수(= core-api 몫). 시험에서 전건을 세우기 위해 대역이 대신 해 준다 ──
    def accept(self, *, upload_id: str, lab_id: str, actor_account_id: str,
               ttl_hours: int = 24) -> None:
        now = datetime.now(timezone.utc)
        self.uploads[upload_id] = {
            "id": upload_id, "lab_id": lab_id, "uploader_account_id": actor_account_id,
            "created_at": now, "expires_at": now + timedelta(hours=ttl_hours),
            "ready": False, "renderable": None, "metadata_complete": None,
            "failed_at": None, "failure_class": None, "failure_reason": None,
            "registered_at": None,
        }
        self.append_event({
            "eventId": "01JQ000000000000000000ACC0", "type": "upload.accepted",
            "schemaVersion": "1.0", "source": "core-api",
            "occurredAt": now.isoformat().replace("+00:00", "Z"),
            "labId": lab_id, "actorAccountId": actor_account_id, "uploadId": upload_id,
            "idempotencyKey": f"upload.accepted:{upload_id}",
            "delivery": {"attempt": 1, "maxAttempts": 5,
                         "firstPublishedAt": now.isoformat().replace("+00:00", "Z"),
                         "publishedAt": now.isoformat().replace("+00:00", "Z"),
                         "redelivery": False, "deadLettered": False},
            "payload": {"files": []},
        })

    # ── EventLedgerPort ────────────────────────────────────────────────────
    def append_event(self, envelope: dict) -> bool:
        key = envelope["idempotencyKey"]
        if key in self._keys:
            return False           # 이미 있는 작업 — 두 벌 만들지 않는다
        self._keys.add(key)
        self.events.append(envelope)
        return True

    def unpublished(self, limit: int = 100) -> list[dict]:
        return [e for e in self.events if not e.get("_published")][:limit]

    def mark_published(self, event_id: str) -> None:
        for e in self.events:
            if e["eventId"] == event_id:
                e["_published"] = True

    def record_delivery_failure(self, event_id: str) -> None:
        """실물 `SqlLedger` 와 같은 사실만 남긴다 — **전달 횟수만 올린다.**

        실물은 다음 바퀴의 `unpublished()` 가 열 값으로 봉투를 다시 짓지만, 이 대역은
        저장한 봉투를 그대로 돌려주므로 `redelivery` 도 함께 맞춘다. 값이 갈리면
        대역이 실물보다 헐거운 것이 된다.
        """
        for e in self.events:
            if e["eventId"] == event_id and not e.get("_published"):
                d = e["delivery"]
                d["attempt"] = int(d["attempt"]) + 1
                d["redelivery"] = d["attempt"] > 1

    # ── UploadLedgerPort ───────────────────────────────────────────────────
    def load_upload(self, upload_id: str) -> dict | None:
        return self.uploads.get(upload_id)

    def record_file_axes_row(self, *, file_id: str, lab_id: str, upload_id: str,
                             file_name: str, storage_key: str,
                             carries_lat: bool, carries_lon: bool) -> None:
        """격자 파일 행을 **세운다**(`〈69〉-⑴`). DB CHECK 와 같은 거절을 흉내낸다."""
        if not (carries_lat or carries_lon):
            raise ValueError("축이 빈 기준 격자 파일 행을 만들지 않는다 (〈66〉)")
        self.file_rows[file_id] = {
            "id": file_id, "lab_id": lab_id, "upload_id": upload_id,
            "kind": "기준 격자 파일", "file_name": file_name, "storage_key": storage_key,
            "carries_lat": carries_lat, "carries_lon": carries_lon,
        }
        self.axes[file_id] = (carries_lat, carries_lon)

    def record_detected_format(self, file_id: str, fmt: str | None) -> bool:
        """실물과 같은 값을 돌려준다 — **이번이 처음 적는 것인가**(`〈253〉`)."""
        first_time = file_id not in self.formats
        self.formats[file_id] = fmt
        return first_time

    def record_status(self, upload_id: str, **fields) -> None:
        self.uploads[upload_id].update(fields)

    def _processing(self, upload_id: str, now: datetime) -> bool:
        """`SqlLedger._PROCESSING` 과 같은 정의 — 대역이 헐거우면 시험이 거짓말을 한다."""
        r = self.uploads[upload_id]
        if r["ready"] or r["failed_at"] is not None:
            return False
        window = now - (r["expires_at"] - r["created_at"])
        for e in self.events:
            if e["uploadId"] != upload_id or e["type"] == "upload.accepted":
                continue
            at = datetime.fromisoformat(e["occurredAt"].replace("Z", "+00:00"))
            if at > window:
                return True
        return False

    def expire(self, now=None) -> list[str]:
        now = now or datetime.now(timezone.utc)
        gone = [u for u, r in self.uploads.items()
                if r["registered_at"] is None and r["expires_at"] <= now
                and not self._processing(u, now)]
        for u in gone:
            del self.uploads[u]
            self.events = [e for e in self.events if e["uploadId"] != u]
        return gone
