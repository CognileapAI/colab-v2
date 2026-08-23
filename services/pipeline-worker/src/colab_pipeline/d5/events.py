"""이벤트 봉투 만들기 — 정본은 `contracts/events/envelope.json` · `core-pipeline.json`.

**계약은 동결이다**(`〈61〉-㉢`). 이 모듈은 계약을 **옮겨 적지 않고 만족**한다 — 값 집합은
계약이 소유하고, 여기서는 그 값을 골라 담는다. 어긋나면 `tests/test_events.py` 가 계약 파일을
직접 읽어 red 를 낸다.

두 정체성을 가른다 (envelope.json `IdempotencyKey` 설명 그대로):
  `eventId`        = **전달의 정체성** — 재전달에서 바뀌지 않는다
  `idempotencyKey` = **작업의 정체성** — `<타입>:<uploadId>`. 난수를 쓰지 않으므로
                     outbox 행이 다시 만들어져도 같은 키가 나온다

**`upload.accepted` 는 core-api 만 낸다** — 봉투가 타입마다 `source` 를 const 로 못박았고
`d5_pipeline_event` 가 CHECK 로 강제한다. 워커가 그것을 만들려 하면 여기서 막는다.
"""
from __future__ import annotations

from datetime import datetime, timezone

EVENT_TYPES: tuple[str, ...] = (
    "upload.accepted",
    "file.format-detected",
    "file.header-parsed",
    "file.crs-normalized",
    "preview.cog-built",
    "upload.ready",
    "upload.failed",
)

#: 행복 경로의 단계 순서 — 실패는 어느 단계에서든 갈라져 나온다.
STAGE_ORDER: tuple[str, ...] = (
    "file.format-detected",
    "file.header-parsed",
    "file.crs-normalized",
    "preview.cog-built",
    "upload.ready",
)

SOURCE_BY_TYPE: dict[str, str] = {
    t: ("core-api" if t == "upload.accepted" else "pipeline-worker") for t in EVENT_TYPES
}

#: 타입마다 매긴다 — 한 단계가 바뀌었다고 나머지 여섯의 버전을 올릴 이유가 없다.
SCHEMA_VERSION_BY_TYPE: dict[str, str] = {t: "1.0" for t in EVENT_TYPES}

#: 상한을 넘으면 재시도하지 않고 DLQ 로 보낸다. **정본에 항목 없음 — 레포 결정(기본 5)**
#: 이고 계약이 그 기본값을 적어 뒀다(envelope.json `maxAttempts.default`).
DEFAULT_MAX_ATTEMPTS = 5


class WorkerCannotEmitError(Exception):
    """이 배포 단위가 낼 수 없는 이벤트다 — 봉투의 `source: const` 를 코드가 지킨다."""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def idempotency_key(event_type: str, upload_id: str) -> str:
    """`<이벤트 타입>:<uploadId>`. 결정론적이다 — 난수 없음."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"계약에 없는 이벤트 타입: {event_type}")
    return f"{event_type}:{upload_id}"


def make_envelope(
    *,
    event_type: str,
    event_id: str,
    lab_id: str,
    actor_account_id: str,
    upload_id: str,
    payload: dict,
    occurred_at: str | None = None,
    attempt: int = 1,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    first_published_at: str | None = None,
    published_at: str | None = None,
    dead_lettered: bool = False,
    allow_core_api_source: bool = False,
) -> dict:
    """봉투 하나. `allow_core_api_source` 는 **계약 검증용 시험 경로**에서만 연다."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"계약에 없는 이벤트 타입: {event_type}")
    source = SOURCE_BY_TYPE[event_type]
    if source != "pipeline-worker" and not allow_core_api_source:
        raise WorkerCannotEmitError(
            f"`{event_type}` 는 {source} 가 내는 이벤트다 — pipeline-worker 가 만들지 않는다")

    ts = occurred_at or now_iso()
    pub = published_at or now_iso()
    return {
        "eventId": event_id,
        "type": event_type,
        "schemaVersion": SCHEMA_VERSION_BY_TYPE[event_type],
        "source": source,
        "occurredAt": ts,
        "labId": lab_id,
        "actorAccountId": actor_account_id,
        "uploadId": upload_id,
        "idempotencyKey": idempotency_key(event_type, upload_id),
        "delivery": {
            "attempt": attempt,
            "maxAttempts": max_attempts,
            "firstPublishedAt": first_published_at or pub,
            "publishedAt": pub,
            "redelivery": attempt > 1,
            "deadLettered": dead_lettered,
        },
        "payload": payload,
    }


# ── 페이로드 만들기 — 계약의 required 를 코드가 채운다 ──────────────────────
def format_detected_payload(*, fmt: str | None, renderable: bool, uniform: bool,
                            per_file: list[dict] | None = None) -> dict:
    p: dict = {"format": fmt, "renderable": renderable, "uniform": uniform}
    if per_file is not None:
        p["perFile"] = per_file
    return p


def header_parsed_payload(*, variables: list[str] | None, period: dict | None,
                          crs: str | None, grid: str | None, byte_size_total: int,
                          unreadable_files: list[dict], source_label: str | None = None) -> dict:
    p: dict = {
        "variables": variables, "period": period, "crs": crs, "grid": grid,
        "byteSizeTotal": byte_size_total, "unreadableFiles": unreadable_files,
    }
    if source_label:
        p["sourceLabel"] = source_label
    return p


def crs_normalized_payload(*, source_crs: str | None, target_crs: str,
                           transformed: bool, file_ids: list[str]) -> dict:
    return {"sourceCrs": source_crs, "targetCrs": target_crs,
            "transformed": transformed, "fileIds": file_ids}


def cog_built_payload(*, file_ids: list[str], overview_levels: int,
                      reference_grid_available: bool | None = None) -> dict:
    p: dict = {"fileIds": file_ids, "overviewLevels": overview_levels}
    if reference_grid_available is not None:
        p["referenceGridAvailable"] = reference_grid_available
    return p


def upload_ready_payload(*, renderable: bool, metadata_complete: bool,
                         expires_at: str | None = None) -> dict:
    p: dict = {"renderable": renderable, "metadataComplete": metadata_complete}
    if expires_at:
        p["expiresAt"] = expires_at
    return p


def upload_failed_payload(*, failed_at: str, failure_class: str, reason: str,
                          will_retry: bool, detail: str | None = None) -> dict:
    f: dict = {"failedAt": failed_at, "class": failure_class,
               "reason": reason, "willRetry": will_retry}
    if detail:
        f["detail"] = detail[:500]
    return {"failure": f}


def sample_payloads(upload_id: str) -> dict[str, dict]:
    """7종 각각의 최소 유효 페이로드 — 계약 검증 시험이 쓴다."""
    fid = "01JQ00000000000000000000F1"
    return {
        "upload.accepted": {"files": [
            {"fileId": fid, "fileName": "a.tif", "kind": "본체", "byteSize": 1},
        ]},
        "file.format-detected": format_detected_payload(
            fmt="GeoTIFF", renderable=True, uniform=True,
            per_file=[{"fileId": fid, "format": "GeoTIFF"}]),
        "file.header-parsed": header_parsed_payload(
            variables=["LST"], period=None, crs="WGS84", grid="64x64",
            byte_size_total=1, unreadable_files=[]),
        "file.crs-normalized": crs_normalized_payload(
            source_crs="WGS84", target_crs="EPSG:4326", transformed=False, file_ids=[fid]),
        "preview.cog-built": cog_built_payload(file_ids=[fid], overview_levels=2),
        "upload.ready": upload_ready_payload(renderable=True, metadata_complete=True),
        "upload.failed": upload_failed_payload(
            failed_at="file.format-detected", failure_class="영구",
            reason="형식 인식 실패", will_retry=False),
    }
