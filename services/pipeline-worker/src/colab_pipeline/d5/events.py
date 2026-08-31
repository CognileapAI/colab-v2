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
    # ⭑ ⟨2026-08-31 · 12차 동결 해제 · `PLAN-SoT §9 〈253〉` · Ted RULING ㉗⟩
    #   **D5 → D7 알림 3종.** 앞의 7종과 성격이 다르다 — 앞은 업로드 하나가 단계를
    #   지나는 **진행**이고, 이 셋은 「이미 선 미리보기의 재료가 바뀌었다」는 **사실**이다.
    #   무엇을 지울지는 여기서 말하지 않는다. 받는 쪽(D7)이 계산한다(`Y-1` 완료 정의 ⓔ).
    "preview.backend-rerun",
    "preview.grid-changed",
    "preview.file-added",
)

#: 트리거 이름 → 이벤트 종류. **이름의 정본은 대장**(`WORK-UNITS §10.2-b` `Y-1` 행 ·
#: 첫째는 `〈206〉`-㉮ 로 「재가공」에서 바뀌었다)이고 계약이 그것을 열거로 못 박았다
#: (`envelope.json#/$defs/InvalidationTrigger`). **여기서 새로 짓지 않는다.**
#:
#: ⚠ **왜 한 종류가 아니라 셋인가** — 멱등 키가 `<타입>:<uploadId>` 라서다. 한 종류로
#: 묶으면 업로드 하나당 트리거가 **한 번만** 나가고, 「트리거 3종이 **각각** 무효화를
#: 일으킨다」(`Y-1` 완료 정의 ⓑ)가 배선에서 성립하지 않는다.
TYPE_BY_TRIGGER: dict[str, str] = {
    "미리보기 뒷단 재실행": "preview.backend-rerun",
    "격자 변경": "preview.grid-changed",
    "파일 추가": "preview.file-added",
}

#: **E-04 업로드 파이프라인 7종** — 업로드 하나가 단계를 지나는 진행.
#: 이름을 준 이유 = `EVENT_TYPES` 가 10종이 된 뒤로 「전 종」과 「파이프라인 전 종」이
#: 다른 집합이 됐고, 그 둘을 산문으로 구분하면 시험이 갈린다.
PIPELINE_TYPES: tuple[str, ...] = EVENT_TYPES[:7]

#: **D7 이 받는 종류.** 릴레이가 이벤트 버스로 내보낼 대상을 이 집합으로 가른다 —
#: 업로드 파이프라인의 내부 진행을 D7 에 흘리지 않는다.
PREVIEW_STALE_TYPES: frozenset[str] = frozenset(TYPE_BY_TRIGGER.values())

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
                         expires_at: str | None = None,
                         grid_resolution: list[dict] | None = None) -> dict:
    """⑥ 준비 완료.

    ⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 8⟩ `gridResolution` 이 붙었다 —
    `〈79〉-⑷` 가 `ready` 의 뜻에 넣은 「격자 축이 확정되거나 거절됐다」를 **페이로드가
    실제로 말한다.** 격자가 없으면 **빈 배열**이다: `null` 로 「모른다」를 말하지 않는다.
    """
    p: dict = {"renderable": renderable, "metadataComplete": metadata_complete}
    if expires_at:
        p["expiresAt"] = expires_at
    p["gridResolution"] = list(grid_resolution or [])
    return p


def preview_stale_payload(*, trigger: str) -> dict:
    """⑧⑨⑩ **미리보기가 낡았다** — 담는 것은 「어느 사건이었나」 하나뿐이다.

    대상은 봉투의 `uploadId` 가 이미 말한다. **지울 경로·캐시 키를 싣지 않는다** —
    발신자가 수신자의 산출물 배치를 알면 그 순간 D5 가 D7 의 저장소를 아는 것이 되고,
    그것이 `03-HANDOFF §4 #20`(세 곳이 각자 배치를 쓰고 있었다)의 무늬다.
    """
    if trigger not in TYPE_BY_TRIGGER:
        raise ValueError(
            f"계약에 없는 트리거다: {trigger!r} — {list(TYPE_BY_TRIGGER)} 셋뿐이다")
    return {"trigger": trigger}


def upload_failed_payload(*, failed_at: str, failure_class: str, reason: str,
                          will_retry: bool, detail: str | None = None) -> dict:
    f: dict = {"failedAt": failed_at, "class": failure_class,
               "reason": reason, "willRetry": will_retry}
    if detail:
        f["detail"] = detail[:500]
    return {"failure": f}


def sample_payloads(upload_id: str) -> dict[str, dict]:
    """전 종 각각의 최소 유효 페이로드 — 계약 검증 시험이 쓴다."""
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
        "preview.backend-rerun": preview_stale_payload(trigger="미리보기 뒷단 재실행"),
        "preview.grid-changed": preview_stale_payload(trigger="격자 변경"),
        "preview.file-added": preview_stale_payload(trigger="파일 추가"),
    }
