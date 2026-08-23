"""D3 Catalog — 데이터셋 · 파일 · 메타.

계보 상태와 가공 단계 Lv 는 **저장하지 않고 계산한다** (PLAN-SoT §9-⑳). 계산에 필요한
D4 사실은 `ports.LineageSummaryPort` 로 받는다 — D4 테이블을 여기서 직접 읽지 않는다.
"""
from __future__ import annotations

import dataclasses

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from ..ports.lineage import LineageSummary

# 묘비(삭제된 데이터셋)는 카탈로그 목록에 서지 않는다 — 상세 화면도 없다
# (Policy_데이터셋_상세 §7). 계보 그래프에는 묘비 노드로 남는다(그건 D4 의 일이다).
_ROWS = text("""
    SELECT d.id, d.uploader_account_id, d.owner_account_id, d.source_label,
           d.last_modified_at, d.uploaded_at, d.lineage_confirmed_at,
           dd.name, dd.topic, dd.summary,
           u.name AS uploader_name,
           -- **조각 수는 메타다** — `d3_file` 을 세지 않는다 (PLAN-SoT §9-㊼).
           -- `body_access` RESTRICTIVE 아래서 본체 테이블을 세면 잠긴 행이 0 을 낸다(실측).
           -- 트리거가 이 열을 유지하고, `tests/test_file_count_drift.py` 가 드리프트를 잡는다.
           d.file_count
      FROM d3_dataset d
      JOIN d3_dataset_description dd ON dd.dataset_id = d.id
      JOIN d1_account u ON u.id = d.uploader_account_id
     WHERE d.deleted_at IS NULL
""")

_FILES = text("""
    SELECT f.id, f.file_name, f.kind
      FROM d3_file f
     WHERE f.dataset_id = :dataset_id
     ORDER BY f.kind DESC, f.file_name, f.id
""")

_EXISTS = text("SELECT 1 FROM d3_dataset WHERE id = :dataset_id AND deleted_at IS NULL")

# 상세 한 건. 목록 질의와 같은 형태를 쓰되 소유자 이름까지 함께 읽는다 —
# 상세의 `기본 정보` 는 소유자와 올린 사람을 **둘 다** 적는다 (Policy_데이터셋_상세 §5 · P-30).
_ONE = text("""
    SELECT d.id, d.uploader_account_id, d.owner_account_id, d.source_label,
           d.last_modified_at, d.uploaded_at, d.lineage_confirmed_at, d.file_count,
           dd.name, dd.topic, dd.summary,
           u.name AS uploader_name,
           o.name AS owner_name
      FROM d3_dataset d
      JOIN d3_dataset_description dd ON dd.dataset_id = d.id
      JOIN d1_account u ON u.id = d.uploader_account_id
      JOIN d1_account o ON o.id = d.owner_account_id
     WHERE d.id = :dataset_id AND d.deleted_at IS NULL
""")

# 자동으로 읽은 정보. 사람이 타이핑하지 않는다 (Policy_데이터셋_상세 §5).
_AUTOMETA = text("""
    SELECT format, variables, period_start, period_end, crs, grid,
           total_size_bytes, bundle_file_name
      FROM d3_dataset_autometa
     WHERE dataset_id = :dataset_id
""")

# 기준 격자 파일 유무. **없으면 없다고 적는다** — 짝 파일이 없어 못 그리는 것인지
# 원래 필요 없는 포맷인지가 갈린다 (Policy_데이터셋_상세 §5).
# 본체 테이블이라 잠긴 데이터에서는 0행이 나온다. 그래서 이 값은 `basicInfo` 를
# 내리는 경우(=본체에 닿는 경우)에만 묻는다.
_HAS_GRID = text("""
    SELECT 1 FROM d3_file
     WHERE dataset_id = :dataset_id AND kind = '기준 격자 파일'
     LIMIT 1
""")


@dataclasses.dataclass(frozen=True)
class DatasetAutometa:
    """자동으로 읽은 메타. 값이 없으면 `None` 이고 **지어내지 않는다**."""

    format: str | None
    variables: list[str]
    period_start: object
    period_end: object
    crs: str | None
    grid: str | None
    total_size_bytes: int | None
    bundle_file_name: str | None


@dataclasses.dataclass(frozen=True)
class DatasetCore:
    dataset_id: str
    name: str
    topic: str | None
    summary: str | None
    file_count: int
    uploader_id: str
    uploader_name: str
    owner_id: str | None = None
    owner_name: str | None = None
    source_label: str | None = None
    last_modified_at: object = None
    uploaded_at: object = None
    lineage_confirmed_at: object = None


def list_dataset_cores(session: Session) -> list[DatasetCore]:
    """연구실 경계는 RLS 가 이미 걸었다 — 여기에 lab_id 조건을 다시 적지 않는다."""
    rows = session.execute(_ROWS).mappings().all()
    return [
        DatasetCore(
            dataset_id=r["id"], name=r["name"], topic=r["topic"], summary=r["summary"],
            file_count=int(r["file_count"]), uploader_id=r["uploader_account_id"],
            uploader_name=r["uploader_name"], owner_id=r["owner_account_id"],
            owner_name=None, source_label=r["source_label"],
            last_modified_at=r["last_modified_at"], uploaded_at=r["uploaded_at"],
            lineage_confirmed_at=r["lineage_confirmed_at"],
        )
        for r in rows
    ]


def find_dataset_core(session: Session, dataset_id: Ulid) -> DatasetCore | None:
    """상세 한 건. **묘비는 여기서 걸러진다** — 지운 데이터는 상세 화면이 없다 (§7)."""
    r = session.execute(_ONE, {"dataset_id": str(dataset_id)}).mappings().first()
    if r is None:
        return None
    return DatasetCore(
        dataset_id=r["id"], name=r["name"], topic=r["topic"], summary=r["summary"],
        file_count=int(r["file_count"]), uploader_id=r["uploader_account_id"],
        uploader_name=r["uploader_name"], owner_id=r["owner_account_id"],
        owner_name=r["owner_name"], source_label=r["source_label"],
        last_modified_at=r["last_modified_at"], uploaded_at=r["uploaded_at"],
        lineage_confirmed_at=r["lineage_confirmed_at"],
    )


def find_autometa(session: Session, dataset_id: Ulid) -> DatasetAutometa | None:
    r = session.execute(_AUTOMETA, {"dataset_id": str(dataset_id)}).mappings().first()
    if r is None:
        return None
    return DatasetAutometa(
        format=r["format"], variables=list(r["variables"] or []),
        period_start=r["period_start"], period_end=r["period_end"],
        crs=r["crs"], grid=r["grid"],
        total_size_bytes=(None if r["total_size_bytes"] is None else int(r["total_size_bytes"])),
        bundle_file_name=r["bundle_file_name"],
    )


def has_reference_grid_file(session: Session, dataset_id: Ulid) -> bool:
    return session.execute(_HAS_GRID, {"dataset_id": str(dataset_id)}).first() is not None


def count_datasets(session: Session) -> int:
    """AI 가 **뒤진 범위**를 먼저 밝히기 위한 셈 (`AiSearchScope.searchedCount`).
    0건이면 그 자체가 「제안할 근거가 없다」의 정직한 형태다."""
    return int(session.execute(
        text("SELECT count(*) FROM d3_dataset WHERE deleted_at IS NULL")).scalar_one())


def dataset_exists(session: Session, dataset_id: Ulid) -> bool:
    """경계 밖이면 RLS 가 행을 지우므로 여기서 False 가 되고, 호출자는 404 를 낸다 (P-9·P-10)."""
    return session.execute(_EXISTS, {"dataset_id": str(dataset_id)}).first() is not None


def list_files(session: Session, dataset_id: Ulid) -> list[dict]:
    rows = session.execute(_FILES, {"dataset_id": str(dataset_id)}).mappings().all()
    return [{"fileId": r["id"], "fileName": r["file_name"], "kind": r["kind"]} for r in rows]


# ════════════════════════════════════════════════════════════════════════════
# 쓰기 — 등록 전환 · 파일 후주입/교체/삭제 · 계보 확인 기록
#
# **`createDataset` 은 「새로 만들기」가 아니라 「등록 전환」이다** (계약 산문 · `Policy §7.2`).
# 업로드 세계의 `fileId` ULID 가 `d3_file.id` 로 **그대로** 온다 — 새로 만들지 않는다
# (`NB-A` 동일성, Ted 승인 2026-08-23). `d5_upload_file.id → d3_file.id` 에 FK 가 없으므로
# (불변규칙 1 이 금지한다) 이 동일성을 지키는 것은 **여기 코드와 그 시험뿐**이다.
# ════════════════════════════════════════════════════════════════════════════

_INSERT_DATASET = text("""
    INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id, source_label)
    VALUES (:id, current_lab_id(), :owner, :uploader, :source_label)
    RETURNING id
""")

_INSERT_DESCRIPTION = text("""
    INSERT INTO d3_dataset_description (dataset_id, lab_id, name, topic, summary)
    VALUES (:dataset_id, current_lab_id(), :name, :topic, :summary)
""")

# 자동으로 읽은 정보의 **자리**를 함께 세운다. 값은 파일에서 나오고 그 읽기는
# pipeline-worker 의 일이라(`P2.md §2-14`), 접수 단계에서 아는 것 말고는 **비워 둔다.**
# 비워 두는 것과 지어내는 것은 다르다.
_INSERT_AUTOMETA = text("""
    INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, bundle_file_name,
                                     total_size_bytes)
    VALUES (:dataset_id, current_lab_id(), :format, :bundle_file_name, :total_size_bytes)
""")

_INSERT_FILE = text("""
    INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key,
                         carries_lat, carries_lon)
    VALUES (:id, current_lab_id(), :dataset_id, :kind, :file_name, :size_bytes, :storage_key,
            :carries_lat, :carries_lon)
    RETURNING id
""")

_FIND_FILE = text("""
    SELECT id, dataset_id, kind, file_name, size_bytes, storage_key, carries_lat, carries_lon
      FROM d3_file
     WHERE id = :file_id AND dataset_id = :dataset_id
""")

_DELETE_FILE = text("DELETE FROM d3_file WHERE id = :file_id RETURNING id")

_UPDATE_FILE = text("""
    UPDATE d3_file
       SET file_name = :file_name, size_bytes = :size_bytes, storage_key = :storage_key
     WHERE id = :file_id
     RETURNING id, dataset_id, kind, file_name, size_bytes, storage_key,
               carries_lat, carries_lon
""")

# `〈60〉-②` — 좌표계·격자는 **그 파일에서 나오는 값**이라 격자 파일이 바뀌면 재계산한다.
# core-api 는 파일을 읽지 못하므로(`CLAUDE.md §3-4`) **재계산의 결과로 「모른다」를 쓴다** —
# 낡은 값을 그대로 두면 지워진 파일에서 읽은 값이 화면에 남는다. 새 값은 파일을 읽는 쪽이 채운다.
_CLEAR_GRID_META = text("""
    UPDATE d3_dataset_autometa SET crs = NULL, grid = NULL, updated_at = now()
     WHERE dataset_id = :dataset_id
""")

# **`마지막 수정` 을 건드리지 않는다** (`〈60〉-①`) — 그 열을 밀면 파생인 `계보 상태` 가
# `확정` 에서 `확인 필요` 로 접히고, 사람이 확인하러 갔다가 아무것도 안 바뀐 걸 본다.
_CONFIRM_LINEAGE = text("""
    UPDATE d3_dataset SET lineage_confirmed_at = now()
     WHERE id = :dataset_id AND deleted_at IS NULL
     RETURNING id
""")


@dataclasses.dataclass(frozen=True)
class FileRow:
    file_id: str
    dataset_id: str
    kind: str
    file_name: str
    size_bytes: int | None
    storage_key: str
    carries_lat: bool
    carries_lon: bool


def _file_row(r) -> FileRow:
    return FileRow(
        file_id=r["id"], dataset_id=r["dataset_id"], kind=r["kind"],
        file_name=r["file_name"],
        size_bytes=(None if r["size_bytes"] is None else int(r["size_bytes"])),
        storage_key=r["storage_key"],
        carries_lat=bool(r["carries_lat"]), carries_lon=bool(r["carries_lon"]),
    )


def register_dataset(session: Session, *, dataset_id: Ulid, owner_id: Ulid,
                     uploader_id: Ulid, name: str, topic: str | None,
                     summary: str | None, source_label: str | None,
                     detected_format: str | None, bundle_file_name: str | None,
                     total_size_bytes: int | None) -> str:
    """D3 세 표를 한 트랜잭션에서 세운다.

    **반쪽이 남지 않는다** — 요청 하나 = 트랜잭션 하나이고(`app/deps.scoped_db`),
    뒤에 오는 파일·계보·프로젝트 삽입이 하나라도 실패하면 이 행까지 통째로 rollback 된다
    (음성 시험 ㉰ 등록 원자성).
    """
    new_id = session.execute(_INSERT_DATASET, {
        "id": str(dataset_id), "owner": str(owner_id), "uploader": str(uploader_id),
        "source_label": source_label,
    }).scalar_one()
    session.execute(_INSERT_DESCRIPTION, {
        "dataset_id": str(dataset_id), "name": name, "topic": topic, "summary": summary,
    })
    session.execute(_INSERT_AUTOMETA, {
        "dataset_id": str(dataset_id), "format": detected_format,
        "bundle_file_name": bundle_file_name, "total_size_bytes": total_size_bytes,
    })
    return new_id


def insert_file(session: Session, *, file_id: str, dataset_id: Ulid, kind: str,
                file_name: str, size_bytes: int | None, storage_key: str,
                carries_lat: bool, carries_lon: bool) -> str:
    """**`file_id` 를 여기서 만들지 않는다** — 부르는 쪽이 업로드가 발급한 값을 넘긴다.

    이 함수가 ULID 를 새로 뽑는 순간 `NB-A` 동일성이 조용히 깨진다. FK 가 없어
    DB 는 아무 말도 하지 않는다 — 그래서 인자로만 받는다.
    """
    if not Ulid.is_valid(file_id):
        raise ValueError(f"파일 ID 가 정규 ID 가 아니다: {file_id!r}")
    return session.execute(_INSERT_FILE, {
        "id": file_id, "dataset_id": str(dataset_id), "kind": kind,
        "file_name": file_name, "size_bytes": size_bytes, "storage_key": storage_key,
        "carries_lat": carries_lat, "carries_lon": carries_lon,
    }).scalar_one()


def find_file(session: Session, *, dataset_id: Ulid, file_id: Ulid) -> FileRow | None:
    r = session.execute(_FIND_FILE, {
        "file_id": str(file_id), "dataset_id": str(dataset_id)}).mappings().first()
    return None if r is None else _file_row(r)


def replace_file(session: Session, *, file_id: Ulid, file_name: str,
                 size_bytes: int | None, storage_key: str) -> FileRow:
    """교체는 **행을 갈아 끼우지 않고 같은 행의 본체를 바꾼다** — `fileId` 가 유지돼야
    계보·활동 기록이 같은 대상을 가리킨다. 축(`carries_*`)은 건드리지 않는다: 새 파일의
    축은 파일을 읽는 쪽이 다시 정한다."""
    r = session.execute(_UPDATE_FILE, {
        "file_id": str(file_id), "file_name": file_name, "size_bytes": size_bytes,
        "storage_key": storage_key,
    }).mappings().one()
    return _file_row(r)


def delete_file(session: Session, file_id: Ulid) -> bool:
    return session.execute(_DELETE_FILE, {"file_id": str(file_id)}).first() is not None


def recompute_grid_metadata(session: Session, dataset_id: Ulid) -> None:
    """`〈60〉-②` 재계산. 위 `_CLEAR_GRID_META` 주석이 「왜 NULL 인가」를 적었다."""
    session.execute(_CLEAR_GRID_META, {"dataset_id": str(dataset_id)})


def confirm_lineage(session: Session, dataset_id: Ulid) -> bool:
    return session.execute(_CONFIRM_LINEAGE, {"dataset_id": str(dataset_id)}).first() is not None


def processing_level(summary: LineageSummary | None) -> int:
    """원자료 Lv0 · 주입력 부모의 최대 + 1 (E-00 · common.json#/$defs/ProcessingLevel)."""
    if summary is None or summary.max_primary_parent_level is None:
        return 0
    return summary.max_primary_parent_level + 1


def lineage_state(core: DatasetCore, summary: LineageSummary | None) -> str:
    """계보 상태 4값을 계산한다. 저장 컬럼이 없는 것이 이 계산의 강제다 (DATAMODEL-BASELINE §3-③).

    판정 순서 —
      1) 부모가 있고 `마지막 수정 > 계보 확정일`(또는 확정일 없음) → `확인 필요`
         (DATAMODEL-BASELINE §3-③ 이 못 박은 유일한 판정식)
      2) 부모가 있고 확정일이 최신 → `확정`
      3) 부모가 없고 원천 표기가 있다 → `원천`
      4) 그 밖 → `기록 없음`
    """
    if summary is not None and summary.parent_count > 0:
        confirmed = core.lineage_confirmed_at
        if confirmed is None or core.last_modified_at > confirmed:
            return "확인 필요"
        return "확정"
    if core.source_label:
        return "원천"
    return "기록 없음"
