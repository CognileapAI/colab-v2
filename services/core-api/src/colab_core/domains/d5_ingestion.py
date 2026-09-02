"""D5 업로드 원장의 **core-api 쪽 동기 절반** — `ports/ingestion.py` 의 유일한 구현.

경계
  · **`d5_*` 를 만지는 core-api 코드는 이 파일 하나뿐이다.** 라우트·D3·D4 는 Port 타입으로만
    말한다 (`CLAUDE.md §3-1` · `〈63〉-㉱`).
  · `d5_*` 는 **어느 사용자 읽기 경로에도 비치지 않는다** (`〈64〉-ⓒ` · `P2.md §2-27`).
    카탈로그·계보·검색은 이 모듈을 부르지 않는다 — 부르면 `tests/test_upload_ledger_hidden.py`
    가 red 를 낸다.
  · D3·D4·D6 를 가리키는 조회를 여기 두지 않는다. `registered_at` 은 **시각만** 있고
    `dataset_id` 가 없다(`0004` 주석) — 「이미 전환됐다(409)」에 필요한 것은 여부이지 대상이다.

수명(`NB-2`)
  세 규칙을 코드가 지킨다 — ① 미등록 업로드는 수명이 있다 ② **시계가 처리를 앞지르지 않는다**
  ③ 만료 뒤에는 없는 것으로 답한다(404).
  ②의 「처리 중」을 무엇으로 재는가 = **마지막 파이프라인 이벤트가 수명 창 안에 있는가**다.
  새 숫자를 만들지 않으려고 수명 그 자체를 창으로 쓴다 —
    · 접수만 하고 파이프라인이 한 발짝도 안 나갔으면 마지막 이벤트 = 접수 = `created_at` 이고,
      만료 시각(`created_at + 수명`)에서 `created_at > now - 수명` 은 거짓이라 **정상 만료된다.**
    · 이벤트가 계속 들어오는 업로드는 만료 시각을 지나도 **살아 있다.**
  이 정의가 없으면 ㉳(만료 404)이 green 인 채로 **정상 처리 중인 업로드를 404 로 지운다.**
"""
from __future__ import annotations

import datetime as dt
import json

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from ..ports.ingestion import (HeldAutoMetadata, TransferFileRecord, TransferRecord,
                               UploadFileRecord, UploadRecord)

#: `upload.accepted` 페이로드의 스키마 버전 (`contracts/events/core-pipeline.json`).
ACCEPTED_SCHEMA_VERSION = "1.0"

#: 계약의 사유 3값 (`contracts/schemas/common.json#GridRejectionReason`). **판정하지 않고
#: 중계만 하지만, 값 집합 밖을 화면에 흘리지 않는다** — 세 표면이 한 집합을 공유한다.
GRID_REJECTION_REASONS = ("형상 불일치", "짝 불일치", "축 판별 실패")
#: 이 이벤트를 내는 배포 단위. 봉투가 타입마다 `source` 를 const 로 못 박았다.
ACCEPTED_SOURCE = "core-api"
ACCEPTED_TYPE = "upload.accepted"

# 「처리 중인가」 — 위 주석의 정의를 SQL 한 조각으로 고정한다. 두 군데(조회·reaper)가
# **같은 문장**을 쓰게 해서 한쪽만 고쳐지는 일을 막는다.
_PROCESSING = """
    (u.ready = false AND u.failed_at IS NULL AND EXISTS (
        SELECT 1 FROM d5_pipeline_event e
         WHERE e.upload_id = u.id
           -- **접수 그 자체는 처리 진행의 증거가 아니다.** `upload.accepted` 는 접수 순간
           -- 반드시 한 건 있으므로, 그것을 세면 모든 업로드가 영원히 「처리 중」이 되어
           -- 만료가 통째로 죽는다. 진행의 증거는 **그 뒤의 이벤트**(②~⑦)다.
           AND e.event_type <> 'upload.accepted'
           AND e.occurred_at > COALESCE(:now, now()) - (u.expires_at - u.created_at)
    ))
"""

_FIND = text(f"""
    SELECT u.id, u.uploader_account_id, u.created_at, u.expires_at, u.ready,
           u.renderable, u.metadata_complete, u.failure_reason, u.registered_at,
           {_PROCESSING} AS processing
      FROM d5_upload u
     WHERE u.id = :id
""")

_FILES = text("""
    SELECT id, file_name, kind, byte_size, storage_key,
           carries_lat, carries_lon, detected_format, relative_path
      FROM d5_upload_file
     WHERE upload_id = :id
     ORDER BY kind DESC, file_name, id
""")

#: ⟨동결 4회 해제 · `PLAN-SoT §9-〈88〉` 묶음 7⟩ 워커의 ⑥ `upload.ready` 가 실은 격자 판정.
#: **core-api 는 판정하지 않는다** — 이벤트가 말한 것을 읽어 seam 형태로 옮길 뿐이다.
_READY_PAYLOAD = text("""
    SELECT payload
      FROM d5_pipeline_event
     WHERE upload_id = :id AND event_type = 'upload.ready'
     ORDER BY occurred_at DESC, id DESC
     LIMIT 1
""")

#: **보류된 사건을 읽는 자리.** 큐가 아니라 질의다 — 보류함은 `d5_pipeline_event` 그 자체다.
#: 같은 타입이 두 번 들어올 수 없으므로(멱등 키 UNIQUE) 정렬 없이도 한 타입에 한 행이다.
_HELD_AUTOMETA_EVENTS = text("""
    SELECT event_type, payload
      FROM d5_pipeline_event
     WHERE upload_id = :id
       AND event_type IN ('file.format-detected', 'file.header-parsed')
""")

_INSERT_UPLOAD = text("""
    INSERT INTO d5_upload (id, lab_id, uploader_account_id, expires_at)
    VALUES (:id, current_lab_id(), :uploader, :expires_at)
""")

# **접수 시점에 세울 수 있는 행은 `본체` 뿐이다.**
#   `d5_upload_file` 의 CHECK 가 「기준 격자 파일이면 축 하나 이상 true」를 요구하는데
#   축은 파일을 읽어야 정해지고(`〈63〉-㉰` — 서버가 파일에서 판별), 그 판별은
#   pipeline-worker 소관이다 — core-api 에는 geo 라이브러리가 없다(`CLAUDE.md §3-4`).
#   그래서 격자 파일의 행은 워커가 축을 정한 뒤 **같은 `fileId` 로** 세운다
#   (`colab_pipeline...d5_ingestion.record_file_axes_row`). 여기서 축을 추측해 채우면
#   `〈66〉` 이 금지한 「축이 빈/틀린 격자 행」이 생긴다. **지어내지 않는다.**
_INSERT_FILE = text("""
    INSERT INTO d5_upload_file
      (id, lab_id, upload_id, kind, file_name, byte_size, storage_key,
       carries_lat, carries_lon, relative_path)
    VALUES (:id, current_lab_id(), :upload_id, :kind, :file_name, :byte_size, :storage_key,
            :carries_lat, :carries_lon, :relative_path)
""")

# outbox 한 줄. 멱등 키가 `<타입>:<uploadId>` 라 **재기입해도 행이 하나**다 —
# 제약이 있다는 사실이 아니라 이 `ON CONFLICT` 가 재전달 멱등을 실제로 만든다.
_INSERT_EVENT = text("""
    INSERT INTO d5_pipeline_event
      (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,
       idempotency_key, payload)
    VALUES (:id, current_lab_id(), :actor, :upload_id, :event_type, :schema_version, :source,
            :idempotency_key, CAST(:payload AS jsonb))
    ON CONFLICT ON CONSTRAINT d5_pipeline_event_idempotency_key_unique DO NOTHING
    RETURNING id
""")

_MARK_REGISTERED = text("""
    UPDATE d5_upload SET registered_at = now()
     WHERE id = :id AND registered_at IS NULL
     RETURNING id
""")

# reaper — 만료분을 지운다(`〈64〉-ⓒ`). **처리 중인 것은 건너뛴다**(`NB-2` 규칙 ②).
# 등록 전환된 업로드도 지운다: D3 로 옮겨 갔으므로 임시 원장에 남을 이유가 없다.
_REAP = text(f"""
    DELETE FROM d5_upload u
     WHERE u.expires_at <= COALESCE(:now, now())
       AND NOT {_PROCESSING}
    RETURNING u.id
""")


def _record(row) -> UploadRecord:
    return UploadRecord(
        upload_id=row["id"],
        uploader_account_id=row["uploader_account_id"],
        created_at=row["created_at"],
        expires_at=row["expires_at"],
        ready=bool(row["ready"]),
        renderable=row["renderable"],
        metadata_complete=row["metadata_complete"],
        failure_reason=row["failure_reason"],
        registered_at=row["registered_at"],
        processing=bool(row["processing"]),
    )


def idempotency_key(event_type: str, upload_id: str) -> str:
    """`<이벤트 타입>:<uploadId>`. **난수를 쓰지 않는다** — 그래서 재기입이 멱등이다."""
    return f"{event_type}:{upload_id}"


class UploadLedgerAdapter:
    """`ports.UploadLedgerReadPort` + `ports.UploadLedgerWritePort` 의 유일한 구현."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── 읽기 ────────────────────────────────────────────────────────────────
    def find(self, upload_id: Ulid, now: dt.datetime | None = None) -> UploadRecord | None:
        row = self._session.execute(
            _FIND, {"id": str(upload_id), "now": now}).mappings().first()
        return None if row is None else _record(row)

    def files(self, upload_id: Ulid) -> list[UploadFileRecord]:
        rows = self._session.execute(_FILES, {"id": str(upload_id)}).mappings().all()
        return [
            UploadFileRecord(
                file_id=r["id"], file_name=r["file_name"], kind=r["kind"],
                byte_size=(None if r["byte_size"] is None else int(r["byte_size"])),
                storage_key=r["storage_key"],
                carries_lat=bool(r["carries_lat"]), carries_lon=bool(r["carries_lon"]),
                detected_format=r["detected_format"],
                # 0008 의 열. 쓰기만 하고 읽지 않던 열이었다 — 등록 전환이 `d3_file` 로
                # 승계하려면(0009 · `〈278〉-(나)`) 여기서 읽어야 한다.
                relative_path=r["relative_path"],
            )
            for r in rows
        ]

    def held_auto_metadata(self, upload_id: Ulid) -> HeldAutoMetadata:
        """등록 전에 난 사건이 나른 값을 **읽기만** 한다. **판정하지 않는다.**

        `upload.ready` 를 읽는 `_READY_PAYLOAD` 와 같은 모양이다 — core-api 는 이벤트가
        말한 것을 옮길 뿐이고, 값을 만드는 것은 파일을 읽는 쪽(pipeline-worker)이다
        (`CLAUDE.md §3-4` — core-api 에는 geo 라이브러리가 없다).

        **없는 값을 지어내지 않는다.** 사건이 없으면 전부 `None` 이고 `event_types` 가
        비어 있다 — 그 사실을 유실 감지가 건수로 읽는다.
        """
        fmt = crs = grid = None
        variables = None
        period_start = period_end = None
        byte_total = None
        seen: list[str] = []
        rows = self._session.execute(
            _HELD_AUTOMETA_EVENTS, {"id": str(upload_id)}).mappings().all()
        for row in rows:
            payload = row["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            if not isinstance(payload, dict):
                continue
            seen.append(row["event_type"])
            if row["event_type"] == "file.format-detected":
                # **조각마다 다르면 아직 모르는 것이다** — 등록 경로가 `detected_format`
                # 에 쓰는 규칙과 같다. `uniform` 이 거짓이면 값을 옮기지 않는다.
                if payload.get("uniform") is not False:
                    fmt = payload.get("format")
            else:
                variables = payload.get("variables")
                if not isinstance(variables, list):
                    variables = None
                crs = payload.get("crs")
                grid = payload.get("grid")
                period = payload.get("period")
                if isinstance(period, dict):
                    period_start = period.get("start")
                    period_end = period.get("end")
                size = payload.get("byteSizeTotal")
                byte_total = size if isinstance(size, int) else None
        return HeldAutoMetadata(
            format=fmt, variables=variables, period_start=period_start,
            period_end=period_end, crs=crs, grid=grid, byte_size_total=byte_total,
            event_types=tuple(sorted(seen)))

    def grid_rejections(self, upload_id: Ulid) -> list[dict]:
        """`UploadStatus.gridRejections` — **거절된 격자가 왜 목록에서 사라졌는가.**

        축을 못 정한 격자는 `d5_upload_file` 행이 아예 안 만들어지므로(`0004` CHECK ·
        `〈63〉-ⓒ`) 접수 201 에 있던 파일이 조회 200 에서 **말없이 사라진다.** 그 자리를
        말하는 것이 이 목록이다 (스윕 `B-2`).

        ⚠ **값 집합 밖은 중계하지 않는다.** 판정은 워커가 하지만, 화면이 모르는 어휘가
        seam 을 건너가면 화면이 조용히 아무 상태도 못 만든다 — 그때는 차라리 비운다.
        """
        row = self._session.execute(_READY_PAYLOAD, {"id": str(upload_id)}).first()
        if row is None:
            return []
        payload = row[0]
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            return []
        out: list[dict] = []
        for item in payload.get("gridResolution") or []:
            if not isinstance(item, dict):
                continue
            reason = item.get("rejectionReason")
            if reason not in GRID_REJECTION_REASONS:
                continue                       # 확정분(`gridAxis`)이거나 값 집합 밖이다
            entry: dict = {"fileName": item.get("fileName") or "", "reason": reason}
            shapes = item.get("shapes")
            if isinstance(shapes, dict) and shapes:
                entry["shapes"] = shapes
            out.append(entry)
        return out

    # ── 쓰기 ────────────────────────────────────────────────────────────────
    def accept(self, *, upload_id: Ulid, uploader_account_id: Ulid,
               expires_at: dt.datetime, files: list[UploadFileRecord]) -> None:
        """접수 행을 세운다. `lab_id` 는 요청이 아니라 `current_lab_id()` 가 넣는다."""
        self._session.execute(_INSERT_UPLOAD, {
            "id": str(upload_id), "uploader": str(uploader_account_id),
            "expires_at": expires_at,
        })
        for f in files:
            if f.kind == "기준 격자 파일":
                # 위 `_INSERT_FILE` 주석 참조 — 축을 모르는 채 행을 세우지 않는다.
                continue
            self._session.execute(_INSERT_FILE, {
                "id": f.file_id, "upload_id": str(upload_id), "kind": f.kind,
                "file_name": f.file_name, "byte_size": f.byte_size,
                "storage_key": f.storage_key,
                "carries_lat": f.carries_lat, "carries_lon": f.carries_lon,
                "relative_path": f.relative_path,
            })

    def publish_accepted(self, *, upload_id: Ulid, actor_account_id: Ulid,
                         files: list[UploadFileRecord]) -> bool:
        """`upload.accepted` 를 outbox 에 넣는다 — **core-api 가 내는 유일한 이벤트**다.

        두 번 불러도 행은 하나다. 돌려주는 값은 「이번 호출이 새 행을 만들었는가」다.
        """
        import json

        payload = {"files": [
            {"fileId": f.file_id, "fileName": f.file_name, "kind": f.kind,
             "byteSize": 0 if f.byte_size is None else f.byte_size}
            for f in files
        ]}
        row = self._session.execute(_INSERT_EVENT, {
            "id": str(Ulid.generate()), "actor": str(actor_account_id),
            "upload_id": str(upload_id), "event_type": ACCEPTED_TYPE,
            "schema_version": ACCEPTED_SCHEMA_VERSION, "source": ACCEPTED_SOURCE,
            "idempotency_key": idempotency_key(ACCEPTED_TYPE, str(upload_id)),
            "payload": json.dumps(payload, ensure_ascii=False),
        }).first()
        return row is not None

    def mark_registered(self, upload_id: Ulid) -> bool:
        """등록 전환 도장. **이미 찍혀 있으면 False** — 호출자가 409 를 낸다."""
        return self._session.execute(
            _MARK_REGISTERED, {"id": str(upload_id)}).first() is not None

    def reap_expired(self, now: dt.datetime | None = None) -> list[str]:
        return [r[0] for r in self._session.execute(_REAP, {"now": now}).all()]


# ═══════════════════════ 프리사인드 전송 원장 (〈277〉) ═══════════════════════
# `d5_*` 를 만지는 core-api 모듈은 이 파일 하나뿐이라는 규칙(`test_upload_ledger_hidden`)
# 때문에 전송 원장의 SQL 도 여기 산다. 전송은 `d5_upload` 이전의 세계다 — 완결(complete)
# 시 라우트가 같은 ULID 로 `accept()` 를 불러 기존 원장으로 승계한다.

_T_INSERT = text("""
    INSERT INTO d5_upload_transfer
      (id, lab_id, uploader_account_id, source_label, expires_at)
    VALUES (:id, current_lab_id(), :uploader, :source_label, :expires_at)
""")

_T_INSERT_FILE = text("""
    INSERT INTO d5_upload_transfer_file
      (id, lab_id, transfer_id, kind, file_name, relative_path, byte_size,
       storage_key, part_size)
    VALUES (:id, current_lab_id(), :transfer_id, :kind, :file_name, :relative_path,
            :byte_size, :storage_key, :part_size)
""")

_T_FIND = text("SELECT * FROM d5_upload_transfer WHERE id = :id")

_T_FILES = text("""
    SELECT * FROM d5_upload_transfer_file
     WHERE transfer_id = :transfer_id
     ORDER BY created_at, id
""")

_T_SET_REF = text("""
    UPDATE d5_upload_transfer_file SET transfer_ref = :ref
     WHERE id = :id AND transfer_ref IS NULL
     RETURNING transfer_ref
""")

_T_SET_OUTCOME = text("UPDATE d5_upload_transfer_file SET outcome = :outcome WHERE id = :id")

_T_COMPLETE = text("""
    UPDATE d5_upload_transfer SET completed_at = now()
     WHERE id = :id AND completed_at IS NULL
     RETURNING id
""")

# 본인 것만 — 배너는 남의 미완료를 보여 줄 이유가 없다 (연구실 경계는 RLS 가 먼저 긋는다).
_T_INCOMPLETE = text("""
    SELECT t.*,
           count(*) FILTER (WHERE f.outcome = '올라감')            AS uploaded_files,
           count(f.id)                                             AS planned_files,
           COALESCE(sum(f.byte_size) FILTER (WHERE f.outcome = '올라감'), 0) AS uploaded_bytes,
           COALESCE(sum(f.byte_size), 0)                           AS planned_bytes
      FROM d5_upload_transfer t
      JOIN d5_upload_transfer_file f ON f.transfer_id = t.id
     WHERE t.uploader_account_id = :uploader
       AND t.completed_at IS NULL
       AND t.expires_at > COALESCE(:now, now())
     GROUP BY t.id
     ORDER BY t.created_at DESC
""")

_T_EXPIRED = text("""
    SELECT id FROM d5_upload_transfer
     WHERE completed_at IS NULL AND expires_at <= COALESCE(:now, now())
""")

_T_DELETE = text("DELETE FROM d5_upload_transfer WHERE id = :id")


def _transfer(row) -> TransferRecord:
    return TransferRecord(
        transfer_id=row["id"], uploader_account_id=row["uploader_account_id"],
        source_label=row["source_label"], created_at=row["created_at"],
        expires_at=row["expires_at"], completed_at=row["completed_at"],
    )


def _transfer_file(row) -> TransferFileRecord:
    return TransferFileRecord(
        file_id=row["id"], file_name=row["file_name"], kind=row["kind"],
        byte_size=row["byte_size"], storage_key=row["storage_key"],
        relative_path=row["relative_path"], part_size=row["part_size"],
        transfer_ref=row["transfer_ref"], outcome=row["outcome"],
    )


class UploadTransferAdapter:
    """전송 원장의 유일한 구현. 소비자는 `routes/upload_transfers.py` 하나다."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def open(self, *, transfer_id: Ulid, uploader_account_id: Ulid, source_label: str,
             expires_at: dt.datetime, files: list[TransferFileRecord]) -> None:
        self._session.execute(_T_INSERT, {
            "id": str(transfer_id), "uploader": str(uploader_account_id),
            "source_label": source_label, "expires_at": expires_at,
        })
        for f in files:
            self._session.execute(_T_INSERT_FILE, {
                "id": f.file_id, "transfer_id": str(transfer_id), "kind": f.kind,
                "file_name": f.file_name, "relative_path": f.relative_path,
                "byte_size": f.byte_size, "storage_key": f.storage_key,
                "part_size": f.part_size,
            })

    def find(self, transfer_id: Ulid) -> TransferRecord | None:
        row = self._session.execute(_T_FIND, {"id": str(transfer_id)}).mappings().first()
        return None if row is None else _transfer(row)

    def files(self, transfer_id: Ulid,
              file_ids: list[str] | None = None) -> list[TransferFileRecord]:
        rows = self._session.execute(
            _T_FILES, {"transfer_id": str(transfer_id)}).mappings().all()
        out = [_transfer_file(r) for r in rows]
        if file_ids is not None:
            wanted = set(file_ids)
            out = [f for f in out if f.file_id in wanted]
        return out

    def set_ref(self, file_id: str, ref: str) -> None:
        """멀티파트 UploadId 는 한 번만 적힌다 — 두 번째 시작 요청은 기존 값을 유지한다."""
        self._session.execute(_T_SET_REF, {"id": file_id, "ref": ref})

    def set_outcome(self, file_id: str, outcome: str) -> None:
        self._session.execute(_T_SET_OUTCOME, {"id": file_id, "outcome": outcome})

    def complete(self, transfer_id: Ulid) -> bool:
        """완결 도장. 이미 찍혀 있으면 False — 호출자가 409 를 낸다."""
        return self._session.execute(
            _T_COMPLETE, {"id": str(transfer_id)}).first() is not None

    def incomplete_for(self, uploader_account_id: Ulid,
                       now: dt.datetime | None = None) -> list[dict]:
        rows = self._session.execute(
            _T_INCOMPLETE, {"uploader": str(uploader_account_id), "now": now}).mappings().all()
        return [{
            "record": _transfer(r),
            "uploaded_files": int(r["uploaded_files"]),
            "planned_files": int(r["planned_files"]),
            "uploaded_bytes": int(r["uploaded_bytes"]),
            "planned_bytes": int(r["planned_bytes"]),
        } for r in rows]

    def expired_open(self, now: dt.datetime | None = None) -> list[str]:
        """만료된 미완결 전송 id — 지연 정리 대상. **원장이 아는 것만** 지운다 (버킷
        루트 감사 금지 — 개발자별 버킷에서 다른 원장의 데이터를 지우게 된다)."""
        return [r[0] for r in self._session.execute(_T_EXPIRED, {"now": now}).all()]

    def delete(self, transfer_id: str) -> None:
        self._session.execute(_T_DELETE, {"id": transfer_id})
