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

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from ..ports.ingestion import UploadFileRecord, UploadRecord

#: `upload.accepted` 페이로드의 스키마 버전 (`contracts/events/core-pipeline.json`).
ACCEPTED_SCHEMA_VERSION = "1.0"
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
           carries_lat, carries_lon, detected_format
      FROM d5_upload_file
     WHERE upload_id = :id
     ORDER BY kind DESC, file_name, id
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
       carries_lat, carries_lon)
    VALUES (:id, current_lab_id(), :upload_id, :kind, :file_name, :byte_size, :storage_key,
            :carries_lat, :carries_lon)
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
            )
            for r in rows
        ]

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
