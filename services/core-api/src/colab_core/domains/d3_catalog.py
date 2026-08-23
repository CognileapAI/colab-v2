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


def dataset_exists(session: Session, dataset_id: Ulid) -> bool:
    """경계 밖이면 RLS 가 행을 지우므로 여기서 False 가 되고, 호출자는 404 를 낸다 (P-9·P-10)."""
    return session.execute(_EXISTS, {"dataset_id": str(dataset_id)}).first() is not None


def list_files(session: Session, dataset_id: Ulid) -> list[dict]:
    rows = session.execute(_FILES, {"dataset_id": str(dataset_id)}).mappings().all()
    return [{"fileId": r["id"], "fileName": r["file_name"], "kind": r["kind"]} for r in rows]


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
