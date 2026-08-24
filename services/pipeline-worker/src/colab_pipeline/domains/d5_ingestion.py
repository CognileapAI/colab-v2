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

from ..d5.axis import REASON_AXIS_UNDECIDED, detect_axes_for_upload
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
#
# ⚠ **stage 1 에서 살아 있는 것은 위 둘뿐이다** — 감지만 도므로 나머지 넷은 발화하지 않는다.
#    **지우지 않는다**(`〈73〉` — 건너뛴 구간만 다시 켜면 stage 2 다). 아래 표기는
#    `S1-PLAN-REFOUND §D.6-4` 의 판정이다: 「좌표/격자 없음」은 **되살아나되 업로드 실패가
#    아니라 렌더 결과의 「보류」**로 표현되고(D7 소관), 나머지 셋은 **죽은 채 남는다.**
_FAILURE_MAP: list[tuple[str, str, str, str]] = [
    ("감지 실패", "file.format-detected", "형식 인식 실패", "영구"),          # stage 1 에서 산다
    ("지원 목록 밖", "file.format-detected", "형식 인식 실패", "영구"),        # stage 1 에서 산다
    ("TIFF 구조 판독 실패", "file.header-parsed", "헤더 인식 실패", "영구"),   # 죽은 분기 — stage 2
    ("파싱 실패", "file.header-parsed", "헤더 인식 실패", "영구"),             # 죽은 분기 — stage 2
    # 격자는 **후주입으로 붙일 수 있다**(`〈58〉`) — 그래서 영구가 아니라 재시도 가능이다.
    # stage 1 에서는 이 분기가 안 돌고, 같은 사실을 **D7 이 「격자 없음 — 지도형 보류」 배지**로
    # 말한다(`K-4`). 업로드는 실패하지 않는다 — 그릴 수 없는 것과 등록할 수 없는 것은 다르다.
    ("좌표/격자 없음", "file.crs-normalized", "좌표계 변환 실패", "재시도 가능"),
    ("COG 변환 실패", "preview.cog-built", "미리보기 준비 실패", "재시도 가능"),  # 죽은 분기 — stage 2
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
    #: 격자 파일 행은 **워커가 만든다**(`〈69〉-⑴`) — 만들려면 저장 키가 필요하다.
    #: 접수가 이미 행을 세운 본체에는 쓰이지 않는다.
    storage_key: str | None = None


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
    def process_upload(self, work: UploadWork, *, stage1: bool = False) -> ProcessResult:
        """`stage1=True` 면 **감지 다음이 곧 `ready`** 다 (`〈73〉` · `S1-PLAN-REFOUND §D.6`).

        ⚠ **미리보기가 stage 1 로 돌아왔다고 이 구간이 켜지는 것이 아니다.**
        `〈74〉`·`〈75〉` 가 되살린 미리보기는 **워커 파이프라인 안이 아니라 화면 요청형**이다 —
        `upload.ready` 뒤에 FE 가 `POST /previews` 를 부르고, 그리는 것은 **D7(viz-render)** 다
        (`§D.6` 흐름도). 그래서 파싱·좌표·COG 는 `〈73〉` 이 정한 대로 stage 1 밖에 남는다.

        **늘어난 것은 단계가 아니라 `ready` 의 판정 조건이다** (`〈79〉-⑷`) — 「본체 감지가
        끝났고, 함께 올라온 격자 파일의 축이 확정되거나 거절됐다」. 축 판별은 아래
        `_resolve_grid_axes` 가 **stage 여부와 무관하게** 먼저 돈다.

        **건너뛴 구간을 지우지 않는다** — stage 2 는 「건너뛴 구간만 다시 켜면」 된다(`〈73〉`).
        뜯어내면 비용이 없어지는 것이 아니라 stage 2 로 옮겨갈 뿐이다.
        """
        res = ProcessResult()
        bodies = [f for f in work.files if f.kind == "본체"]
        grids = [f for f in work.files if f.kind == "기준 격자 파일"]
        for f in work.files:
            res.files[f.file_id] = FileOutcome(file_id=f.file_id)

        grid_dir, grid_resolution = self._resolve_grid_axes(work, res, grids)

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

        if stage1:
            # ⑥ 로 곧장 간다. **`renderable` 은 감지로 안 사실**이라 그대로 싣고,
            # `metadataComplete` 는 **헤더를 안 읽었으니 false** 다 — 「읽어 보고 아니었다」와
            # 「안 읽었다」를 갈라 적을 자리가 계약에 없어서, 원장 열은 NULL 로 남긴다
            # (`S1-PLAN-REFOUND §D.1 #20` — 열은 살리되 값은 NULL).
            upload = self._ledger.load_upload(work.upload_id) or {}
            self._ledger.record_status(work.upload_id, ready=True)
            self._emit(work, res, "upload.ready", upload_ready_payload(
                renderable=renderable, metadata_complete=False,
                expires_at=_iso(upload.get("expires_at")),
                grid_resolution=grid_resolution))
            return res

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
            expires_at=_iso(expires), grid_resolution=grid_resolution))
        return res

    # ── 격자 축 ────────────────────────────────────────────────────────────
    def _resolve_grid_axes(self, work: UploadWork, res: ProcessResult,
                           grids: list[UploadFileWork]) -> tuple[Path | None, list[dict]]:
        """축을 판별하고, 그 뒤에 **격자 파일 행을 세운다**(`〈69〉-⑴`).

        접수(`createUpload`)는 업로드와 본체 파일 행까지만 만든다 — `d5_upload_file` 의
        CHECK 가 「기준 격자 파일이면 축 하나 이상 true」를 요구하는데 축은 파일을
        열어야 나오기 때문이다. **`0004` 는 고치지 않는다**(`〈69〉`): CHECK 를 상태로
        조건화하면 「축이 빈 격자 행」이 합법한 상태가 되어 불변식이 약해진다.

        못 정한 파일은 **거절**한다(`〈66〉`) — 행 자체를 만들지 않고, 등록은 진행한다.

        ⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 8⟩ **두 번째 반환값이 `gridResolution` 이다.**
        파일마다 「축을 확정했다(`gridAxis`)」 또는 「못 쓰겠다(`rejectionReason`)」 중
        정확히 하나를 말한다 — 그것이 `upload.ready` 에 실린다. 이전에는 이 판정이
        **파이썬 딕셔너리 안의 산문**으로만 남고 어떤 페이로드에도 안 실렸다(스윕 `G`).
        """
        if not grids:
            return work.grid_dir, []
        by_path = {g.path: g for g in grids}
        detection = detect_axes_for_upload([g.path for g in grids])
        for path, d in detection.resolved.items():
            g = by_path[path]
            out = res.files[g.file_id]
            out.carries_lat, out.carries_lon = d.carries_lat, d.carries_lon
            self._ledger.record_file_axes_row(
                file_id=g.file_id, lab_id=work.lab_id, upload_id=work.upload_id,
                file_name=g.file_name, storage_key=g.storage_key or g.file_name,
                carries_lat=d.carries_lat, carries_lon=d.carries_lon)
        for path, why in detection.rejected.items():
            # 그 파일만 막고 등록은 막지 않는다(`〈63〉-ⓒ`). 축이 빈 행을 만들지 않는다.
            res.rejected[by_path[path].file_id] = why

        # 파일 순서를 그대로 둔다 — 화면이 올린 순서로 말할 수 있게.
        resolution: list[dict] = []
        for g in grids:
            row: dict = {"fileId": g.file_id, "fileName": g.file_name}
            d = detection.resolved.get(g.path)
            if d is not None:
                row["gridAxis"] = {"carriesLat": bool(d.carries_lat),
                                   "carriesLon": bool(d.carries_lon)}
            else:
                row["rejectionReason"] = detection.reasons.get(
                    g.path, REASON_AXIS_UNDECIDED)
                shape = detection.shapes.get(g.path)
                if shape:
                    row["shapes"] = {"gridShape": list(shape)}
            resolution.append(row)

        usable = [p for p in detection.resolved]
        if not usable:
            return work.grid_dir, resolution
        return (work.grid_dir or Path(usable[0]).parent), resolution


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

#: 「처리 중인가」 — `〈67〉-ⓐ` 규칙 ② 의 대상 집합. `core-api` 의 `_PROCESSING` 과
#: **같은 문장**이다(`colab_core.domains.d5_ingestion`). 두 서비스의 reaper 가 서로
#: 다른 행을 지우면 「처리 중은 안 지운다」는 보장이 한쪽에서만 성립한다.
#: 「처리 중」의 정의 자체는 정본에 없다 — 새 숫자를 만들지 않으려고 **수명 그 자체를
#: 창으로** 썼다. 이것은 레포 판단이다(정본 값이 아니다).
_PROCESSING = """
    (u.ready = false AND u.failed_at IS NULL AND EXISTS (
        SELECT 1 FROM d5_pipeline_event e
         WHERE e.upload_id = u.id
           AND e.event_type <> 'upload.accepted'
           AND e.occurred_at > COALESCE(:now, now()) - (u.expires_at - u.created_at)
    ))
"""

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

    def pending_uploads(self, limit: int = 20) -> list[dict]:
        """아직 처리하지 않은 접수 건 (`〈73〉` 배선의 소비 쪽).

        조건 넷 — 접수됐고(`upload.accepted` 가 있고) · 아직 `ready` 가 아니고 ·
        실패하지 않았고 · 등록 전환 전이다. **`ready` 를 조건에 넣는 것이 멱등의 전부다** —
        같은 업로드를 두 번 돌려도 두 번째는 이 집합에 없다. 이벤트 쪽 멱등 키가
        두 벌 발행을 막고, 이 조건이 두 번째 처리 자체를 막는다.
        """
        from sqlalchemy import text
        rows = self._s.execute(text("""
            SELECT u.id, u.lab_id, u.uploader_account_id
              FROM d5_upload u
             WHERE u.ready = false AND u.failed_at IS NULL AND u.registered_at IS NULL
               AND EXISTS (SELECT 1 FROM d5_pipeline_event e
                            WHERE e.upload_id = u.id AND e.event_type = 'upload.accepted')
             ORDER BY u.created_at, u.id
             LIMIT :limit
        """), {"limit": limit}).mappings().all()
        return [dict(r) for r in rows]

    def accepted_files(self, upload_id: str) -> list[dict]:
        """접수된 파일 **전건** — `upload.accepted` 페이로드에서 읽는다.

        ⚠ **`d5_upload_file` 을 보면 안 된다.** `〈79〉-㈎ⓑ` 대로 접수는 **본체 행만** 만들고
        격자는 저장만 한다(축을 모르는 채로는 CHECK 를 통과하지 못한다). 그래서 원장 행을
        세면 **격자가 통째로 안 보이고**, 축 판별을 돌릴 대상이 사라진다.
        접수 이벤트의 `files` 는 `FileRef` 전건이라 격자가 거기 있다.
        """
        from sqlalchemy import text
        r = self._s.execute(text("""
            SELECT payload FROM d5_pipeline_event
             WHERE upload_id = :uid AND event_type = 'upload.accepted'
             ORDER BY occurred_at LIMIT 1
        """), {"uid": upload_id}).mappings().first()
        if r is None:
            return []
        payload = r["payload"] or {}
        files = payload.get("files") if isinstance(payload, dict) else None
        return list(files) if isinstance(files, list) else []

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
        """만료 스윕. **처리 중인 업로드는 건드리지 않는다**(`〈67〉` 이행 제약 ㉠).

        「시계가 처리를 앞지르지 않는다」가 정본 규칙이다. `expires_at` 만 보고 지우면
        **처리 중인 업로드가 사라져 정상 동작이 404 로 답한다** — 그러면 음성 시험
        ㉳(만료된 업로드는 전환되지 않는다)가 그 실패 위에서 green 을 보고한다.

        「처리 중」의 정의는 `core-api` 쪽(`colab_core…d5_ingestion._PROCESSING`)과
        **같은 문장**이다 — 한쪽만 갈라지면 두 스윕이 다른 행을 지운다.
        `upload.accepted` 를 진행의 증거에서 빼는 이유는 그것이 접수 순간 반드시
        있어서, 세면 만료가 통째로 죽기 때문이다.
        """
        from sqlalchemy import text
        rows = self._s.execute(text(f"""
            DELETE FROM d5_upload u
             WHERE u.registered_at IS NULL
               AND u.expires_at <= COALESCE(:now, now())
               AND NOT {_PROCESSING}
            RETURNING u.id
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
