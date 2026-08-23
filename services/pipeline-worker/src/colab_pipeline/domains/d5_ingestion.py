"""D5 Ingestion & Pipeline — 워커 골격 · outbox 원장 · 릴레이 · reaper.

**이 모듈은 파서를 다시 쓰지 않는다.** `d5/` 9모듈(감지·파싱·좌표·COG·판정)은 실물 62건
재판정으로 실측된 산출이고, 여기서는 그것을 **단계로 묶어 이벤트로 내보낼 뿐**이다.

이벤트 7종 중 **②~⑦ 이 이 배포 단위 소관**이다. `upload.accepted`(①)만 core-api 가
내고, 봉투가 `source` 를 const 로 못박았으며 `d5_pipeline_event` 가 CHECK 로 강제한다.

**저장 자리는 W1 이 만든 `d5_*` 표다** — 새 표를 만들지 않는다(`sessions/P2-db-report.md`).
`d5_*` 는 어느 사용자 읽기 경로에도 안 비치고 만료되면 reaper 가 지운다(`〈64〉-ⓒ`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ..d5.axis import detect_axes_for_upload
from ..d5.detect import detect_format
from ..d5.events import (
    STAGE_ORDER,
    cog_built_payload,
    crs_normalized_payload,
    format_detected_payload,
    header_parsed_payload,
    idempotency_key,
    make_envelope,
    upload_failed_payload,
    upload_ready_payload,
)
from ..d5.formats import UNKNOWN
from ..d5.pipeline import PipelineResult, run_file
from ..d5.renderable import is_renderable
from ..kernel.ids import new_ulid
from ..ports.outbox import EventLedgerPort, UploadLedgerPort

#: 좌표 정규화의 목표 좌표계. **계약에 상수로 박히지 않았다** — 값은 발행자가 정한다.
#: `cog.py` 가 실측 위경도로 규칙 격자를 만들므로 결과는 WGS84 지리좌표다.
TARGET_CRS = "WGS84"

# `run_file` 이 남기는 실패 문구 → (멈춘 단계, 정본 사유, 실패 분류).
# **문구를 새로 만들지 않는다** — 기존 파이프라인이 이미 내는 것을 단계로 옮겨 적는다.
# 사유 값 집합의 정본은 `envelope.json#FailureReason` 이다.
_FAILURE_MAP: list[tuple[str, str, str, str]] = [
    ("감지 실패", "file.format-detected", "형식 인식 실패", "영구"),
    ("지원 목록 밖", "file.format-detected", "형식 인식 실패", "영구"),
    ("TIFF 구조 판독 실패", "file.header-parsed", "헤더 인식 실패", "영구"),
    ("파싱 실패", "file.header-parsed", "헤더 인식 실패", "영구"),
    # 격자는 **후주입으로 붙일 수 있다**(`〈58〉`) — 그래서 영구가 아니라 재시도 가능이다.
    ("좌표/격자 없음", "file.crs-normalized", "좌표계 변환 실패", "재시도 가능"),
    ("COG 변환 실패", "preview.cog-built", "미리보기 준비 실패", "재시도 가능"),
]


def _classify_failure(messages: list[str]) -> tuple[str, str, str]:
    for msg in messages:
        for prefix, stage, reason, klass in _FAILURE_MAP:
            if msg.startswith(prefix):
                return stage, reason, klass
    return "upload.failed", "내부 오류", "영구"


# ── 입력 ────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class UploadFileWork:
    file_id: str
    path: Path
    kind: str            # '본체' | '기준 격자 파일'
    file_name: str


@dataclass(frozen=True)
class UploadWork:
    upload_id: str
    lab_id: str
    actor_account_id: str
    workdir: Path
    files: list[UploadFileWork]
    grid_dir: Path | None = None
    kind: str = "continuous"      # 오버뷰 리샘플링 분기 (`DR-12`)


# ── 출력 ────────────────────────────────────────────────────────────────────
@dataclass
class FileOutcome:
    file_id: str
    detected_format: str | None = None
    input_cog_class: str | None = None
    status: str = "SUCCESS"
    failures: list[str] = field(default_factory=list)
    carries_lat: bool | None = None
    carries_lon: bool | None = None


@dataclass
class ProcessResult:
    events: list[dict] = field(default_factory=list)
    files: dict[str, FileOutcome] = field(default_factory=dict)
    artifacts: list = field(default_factory=list)      # ArtifactRecord (`DR-2`)
    rejected: dict[str, str] = field(default_factory=dict)


class IngestionService:
    """업로드 하나를 단계로 통과시키며 ②~⑦ 을 발행한다."""

    def __init__(self, ledger, *, id_factory: Callable[[], str] = new_ulid) -> None:
        # 두 Port 를 한 객체가 만족한다 — 같은 트랜잭션 안에서 상태행과 outbox 행을
        # 함께 써야 하기 때문이다(README 「상태행과 outbox행은 단일 트랜잭션」).
        self._ledger: EventLedgerPort | UploadLedgerPort = ledger
        self._new_id = id_factory

    # ── 발행 ────────────────────────────────────────────────────────────────
    def _emit(self, work: UploadWork, res: ProcessResult, event_type: str, payload: dict) -> dict:
        env = make_envelope(
            event_type=event_type, event_id=self._new_id(), lab_id=work.lab_id,
            actor_account_id=work.actor_account_id, upload_id=work.upload_id, payload=payload,
        )
        self._ledger.append_event(env)     # 이미 있는 멱등 키면 아무것도 안 만든다
        res.events.append(env)
        return env

    def _fail(self, work: UploadWork, res: ProcessResult, *, stage: str, reason: str,
              klass: str, detail: str | None = None) -> ProcessResult:
        self._ledger.record_status(
            work.upload_id, ready=False, failed_at=datetime.now(timezone.utc),
            failure_class=klass, failure_reason=reason)
        self._emit(work, res, "upload.failed", upload_failed_payload(
            failed_at=stage, failure_class=klass, reason=reason,
            will_retry=(klass == "재시도 가능"), detail=detail))
        return res

    # ── 본 흐름 ─────────────────────────────────────────────────────────────
    def process_upload(self, work: UploadWork) -> ProcessResult:
        res = ProcessResult()
        bodies = [f for f in work.files if f.kind == "본체"]
        grids = [f for f in work.files if f.kind == "기준 격자 파일"]
        for f in work.files:
            res.files[f.file_id] = FileOutcome(file_id=f.file_id)

        grid_dir = self._resolve_grid_axes(work, res, grids)

        # ② 포맷 감지 — 매직바이트. 헤더 파싱보다 앞이다(파서를 고르려면 포맷이 먼저다)
        per_file = []
        for f in bodies:
            det = detect_format(f.path)
            res.files[f.file_id].detected_format = det.format
            self._ledger.record_detected_format(f.file_id, det.format)
            per_file.append({"fileId": f.file_id, "format": det.format})
        seen = {p["format"] for p in per_file}
        readable = {s for s in seen if s is not None}
        uniform = len(readable) <= 1
        fmt = next(iter(readable)) if len(readable) == 1 else None
        renderable = is_renderable(fmt)
        self._emit(work, res, "file.format-detected", format_detected_payload(
            fmt=fmt, renderable=renderable, uniform=uniform, per_file=per_file))

        if not readable:
            return self._fail(work, res, stage="file.format-detected",
                              reason="형식 인식 실패", klass="영구",
                              detail="본체 전건이 알려진 매직바이트가 아니다")
        if not uniform:
            # 조각의 포맷이 다르면 조각이 아니라 다른 데이터다 (`DataModel §4.3`)
            return self._fail(work, res, stage="file.format-detected",
                              reason="조각이 서로 다름", klass="영구",
                              detail=f"감지된 포맷 {sorted(readable)}")

        # ③④⑤ — 기존 파이프라인을 파일마다 통과시킨다 (파서를 다시 쓰지 않는다)
        results: dict[str, PipelineResult] = {}
        for f in bodies:
            r = run_file(f.path, workdir=work.workdir, grid_dir=grid_dir, kind=work.kind)
            results[f.file_id] = r
            out = res.files[f.file_id]
            out.status, out.failures = r.status, list(r.failures)
            out.input_cog_class = r.input_cog_class
            if r.artifact is not None:
                res.artifacts.append(r.artifact)

        ok = {fid: r for fid, r in results.items() if r.status == "SUCCESS"}
        if not ok:
            stage, reason, klass = _classify_failure(
                [m for r in results.values() for m in r.failures])
            return self._fail(work, res, stage=stage, reason=reason, klass=klass,
                              detail="; ".join(m for r in results.values() for m in r.failures))

        # ③ 헤더 파싱 — 일부만 못 읽어도 **읽은 것으로 지나간다**(정본 §9 조각 일부 실패)
        unreadable = [{"fileId": f.file_id, "fileName": f.file_name}
                      for f in bodies if f.file_id not in ok]
        meta = next(iter(ok.values())).metadata
        variables = list(meta.variables) if meta and meta.variables else None
        grid_text = None
        if meta and isinstance(meta.grid, tuple):
            grid_text = f"{meta.grid[0]}x{meta.grid[1]}"
        period = None
        if meta and isinstance(meta.period, tuple):
            period = {"start": meta.period[0], "end": meta.period[1]}
        crs = None if (meta is None or meta.crs == UNKNOWN) else meta.crs
        total = sum((results[fid].metadata.size_bytes or 0) for fid in ok
                    if results[fid].metadata)
        self._emit(work, res, "file.header-parsed", header_parsed_payload(
            variables=variables, period=period, crs=crs, grid=grid_text,
            byte_size_total=int(total), unreadable_files=unreadable))
        metadata_complete = bool(variables) and period is not None and crs is not None \
            and grid_text is not None and total > 0

        # ④ 좌표계 정규화
        self._emit(work, res, "file.crs-normalized", crs_normalized_payload(
            source_crs=crs, target_crs=TARGET_CRS,
            transformed=any(results[fid].cog_path for fid in ok), file_ids=sorted(ok)))

        # ⑤ 미리보기용 COG. **이미 COG 인 입력은 우리 산출물이 아니다**(`DR-2`) —
        #    변환하지 않았어도 미리보기 대상으로는 준비돼 있다.
        overview_levels = 0
        for fid in ok:
            if results[fid].cog_path:
                overview_levels = max(overview_levels, 1)
        self._emit(work, res, "preview.cog-built", cog_built_payload(
            file_ids=sorted(ok), overview_levels=overview_levels,
            reference_grid_available=(grid_dir is not None) if grid_dir is not None else None))

        # ⑥ 준비 완료 — 저장된 것은 아무것도 없다(`upload.ready` 에 datasetId 가 없는 이유)
        upload = self._ledger.load_upload(work.upload_id) or {}
        expires = upload.get("expires_at")
        self._ledger.record_status(work.upload_id, ready=True, renderable=renderable,
                                   metadata_complete=metadata_complete)
        self._emit(work, res, "upload.ready", upload_ready_payload(
            renderable=renderable, metadata_complete=metadata_complete,
            expires_at=_iso(expires)))
        return res

    # ── 격자 축 ────────────────────────────────────────────────────────────
    def _resolve_grid_axes(self, work: UploadWork, res: ProcessResult,
                           grids: list[UploadFileWork]) -> Path | None:
        """축을 판별해 원장에 두 불리언으로 적는다. 못 정한 파일은 **거절**한다(`〈66〉`)."""
        if not grids:
            return work.grid_dir
        by_path = {g.path: g for g in grids}
        detection = detect_axes_for_upload([g.path for g in grids])
        for path, d in detection.resolved.items():
            g = by_path[path]
            out = res.files[g.file_id]
            out.carries_lat, out.carries_lon = d.carries_lat, d.carries_lon
            self._ledger.record_file_axes(
                g.file_id, carries_lat=d.carries_lat, carries_lon=d.carries_lon)
        for path, why in detection.rejected.items():
            # 그 파일만 막고 등록은 막지 않는다(`〈63〉-ⓒ`). 축이 빈 행을 만들지 않는다.
            res.rejected[by_path[path].file_id] = why
        usable = [p for p in detection.resolved]
        if not usable:
            return work.grid_dir
        return work.grid_dir or Path(usable[0]).parent


def _iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, datetime):
        v = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    return str(value)


# ════════════════════════════════════════════════════════════════════════════
# SQL 원장 — W1 이 만든 `d5_*` 표. 새 표를 만들지 않는다.
# ════════════════════════════════════════════════════════════════════════════
class SqlLedger:
    """`EventLedgerPort` + `UploadLedgerPort` 실물. 세션 하나 = 트랜잭션 하나."""

    def __init__(self, session) -> None:
        self._s = session

    # ── EventLedgerPort ────────────────────────────────────────────────────
    def append_event(self, envelope: dict) -> bool:
        from sqlalchemy import text
        import json
        row = self._s.execute(text("""
            INSERT INTO d5_pipeline_event
              (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,
               occurred_at, idempotency_key, attempt, max_attempts, payload)
            VALUES (:id, :lab, :acc, :uid, :type, :ver, :src, :occurred, :key,
                    :attempt, :max_attempts, CAST(:payload AS jsonb))
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING id
        """), {
            "id": envelope["eventId"], "lab": envelope["labId"],
            "acc": envelope["actorAccountId"], "uid": envelope["uploadId"],
            "type": envelope["type"], "ver": envelope["schemaVersion"],
            "src": envelope["source"], "occurred": envelope["occurredAt"],
            "key": envelope["idempotencyKey"],
            "attempt": envelope["delivery"]["attempt"],
            "max_attempts": envelope["delivery"]["maxAttempts"],
            "payload": json.dumps(envelope["payload"], ensure_ascii=False),
        }).first()
        return row is not None

    def unpublished(self, limit: int = 100) -> list[dict]:
        from sqlalchemy import text
        rows = self._s.execute(text("""
            SELECT id, lab_id, actor_account_id, upload_id, event_type, schema_version,
                   source, occurred_at, idempotency_key, attempt, max_attempts,
                   first_published_at, dead_lettered, payload
              FROM d5_pipeline_event
             WHERE published_at IS NULL
             ORDER BY occurred_at, id
             LIMIT :limit
        """), {"limit": limit}).mappings().all()
        out = []
        for r in rows:
            out.append({
                "eventId": r["id"], "type": r["event_type"],
                "schemaVersion": r["schema_version"], "source": r["source"],
                "occurredAt": _iso(r["occurred_at"]), "labId": r["lab_id"],
                "actorAccountId": r["actor_account_id"], "uploadId": r["upload_id"],
                "idempotencyKey": r["idempotency_key"],
                "delivery": {
                    "attempt": r["attempt"], "maxAttempts": r["max_attempts"],
                    "firstPublishedAt": _iso(r["first_published_at"]) or _iso(r["occurred_at"]),
                    "publishedAt": _iso(datetime.now(timezone.utc)),
                    "redelivery": r["attempt"] > 1, "deadLettered": r["dead_lettered"],
                },
                "payload": r["payload"],
            })
        return out

    def mark_published(self, event_id: str) -> None:
        from sqlalchemy import text
        self._s.execute(text("""
            UPDATE d5_pipeline_event
               SET published_at = now(),
                   first_published_at = COALESCE(first_published_at, now())
             WHERE id = :id
        """), {"id": event_id})

    # ── UploadLedgerPort ───────────────────────────────────────────────────
    def load_upload(self, upload_id: str) -> dict | None:
        from sqlalchemy import text
        r = self._s.execute(text("""
            SELECT id, lab_id, uploader_account_id, created_at, expires_at, ready,
                   renderable, metadata_complete, failed_at, failure_class,
                   failure_reason, registered_at
              FROM d5_upload WHERE id = :id
        """), {"id": upload_id}).mappings().first()
        return dict(r) if r else None

    def record_file_axes(self, file_id: str, *, carries_lat: bool, carries_lon: bool) -> None:
        from sqlalchemy import text
        if not (carries_lat or carries_lon):
            raise ValueError("축이 빈 기준 격자 파일 행을 만들지 않는다 (〈66〉)")
        self._s.execute(text("""
            UPDATE d5_upload_file
               SET carries_lat = :lat, carries_lon = :lon
             WHERE id = :id
        """), {"id": file_id, "lat": carries_lat, "lon": carries_lon})

    def record_file_axes_row(self, *, file_id: str, lab_id: str, upload_id: str,
                             file_name: str, storage_key: str,
                             carries_lat: bool, carries_lon: bool) -> None:
        """격자 파일 행을 **축이 정해진 뒤에** 세운다.

        ⚠ 접수 시점에는 이 행을 만들 수 없다 — `d5_upload_file` 의 CHECK 가
        「기준 격자 파일이면 축 하나 이상 true」를 요구하는데 축은 워커가 정한다.
        """
        from sqlalchemy import text
        if not (carries_lat or carries_lon):
            raise ValueError("축이 빈 기준 격자 파일 행을 만들지 않는다 (〈66〉)")
        self._s.execute(text("""
            INSERT INTO d5_upload_file
              (id, lab_id, upload_id, kind, file_name, storage_key, carries_lat, carries_lon)
            VALUES (:id, :lab, :uid, '기준 격자 파일', :name, :key, :lat, :lon)
            ON CONFLICT (id) DO UPDATE
               SET carries_lat = EXCLUDED.carries_lat, carries_lon = EXCLUDED.carries_lon
        """), {"id": file_id, "lab": lab_id, "uid": upload_id, "name": file_name,
               "key": storage_key, "lat": carries_lat, "lon": carries_lon})

    def record_detected_format(self, file_id: str, fmt: str | None) -> None:
        from sqlalchemy import text
        self._s.execute(text(
            "UPDATE d5_upload_file SET detected_format = :f WHERE id = :id"),
            {"id": file_id, "f": fmt})

    def record_status(self, upload_id: str, **fields) -> None:
        from sqlalchemy import text
        allowed = {"ready", "renderable", "metadata_complete", "failed_at",
                   "failure_class", "failure_reason", "registered_at"}
        bad = set(fields) - allowed
        if bad:
            raise ValueError(f"업로드 상태에 없는 열: {sorted(bad)}")
        sets = ", ".join(f"{k} = :{k}" for k in fields)
        self._s.execute(text(f"UPDATE d5_upload SET {sets} WHERE id = :id"),
                        {"id": upload_id, **fields})

    def expire(self, now=None) -> list[str]:
        from sqlalchemy import text
        rows = self._s.execute(text("""
            DELETE FROM d5_upload
             WHERE registered_at IS NULL AND expires_at <= COALESCE(:now, now())
            RETURNING id
        """), {"now": now}).all()
        return [r[0] for r in rows]


# ── 릴레이 · reaper ────────────────────────────────────────────────────────
def relay_unpublished(ledger, *, publish: Callable[[dict], None], limit: int = 100) -> int:
    """미발행 이벤트를 내보내고 발행 시각을 찍는다.

    at-least-once 다 — 내보낸 뒤 표시하므로 **같은 이벤트가 두 번 갈 수 있고**, 소비자는
    멱등 키로 거른다. 반대 순서(먼저 표시)로 하면 조용히 유실된다.
    """
    sent = 0
    for env in ledger.unpublished(limit=limit):
        publish(env)
        ledger.mark_published(env["eventId"])
        sent += 1
    return sent


def reap_expired_uploads(ledger, *, now=None) -> list[str]:
    """만료된 미등록 업로드를 지운다 (`〈64〉-ⓒ`). 등록된 것은 건드리지 않는다."""
    return ledger.expire(now)
