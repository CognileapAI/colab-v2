"""D3 격자 편의 사실 — 후보·연구실 기본값·등록 프로필.

파일을 읽고 지리값을 만드는 일은 pipeline-worker 소관이다. 이 모듈은 그 결과를
같은 연구실/RLS 경계 안에서 조회하고 D5 프로필을 등록 시 D3로 옮길 뿐이다.
"""
from __future__ import annotations

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid


_PROFILE = text("""
    SELECT dataset_id, body_shape, grid_shape, grid_digest, grid_format_signature,
           west, south, east, north, map_state, grid_source
      FROM d3_dataset_grid_profile
     WHERE dataset_id = :dataset_id
""")

_CANDIDATES = text("""
    SELECT p.dataset_id, dd.name AS dataset_name, p.body_shape, p.grid_shape,
           p.grid_digest, p.grid_format_signature,
           p.west, p.south, p.east, p.north, p.map_state, p.grid_source,
           (g.dataset_id IS NOT NULL) AS is_default,
           array_agg(f.file_name ORDER BY f.file_name, f.id) AS file_names
      FROM d3_dataset_grid_profile p
      JOIN d3_dataset d ON d.id = p.dataset_id AND d.deleted_at IS NULL
      JOIN d3_dataset_description dd ON dd.dataset_id = d.id
      JOIN d3_file f ON f.dataset_id = d.id AND f.kind = '기준 격자 파일'
      LEFT JOIN d3_lab_default_grid g
        ON g.lab_id = p.lab_id AND g.dataset_id = p.dataset_id
     WHERE p.grid_shape = CAST(:shape AS integer[])
     GROUP BY p.dataset_id, dd.name, p.body_shape, p.grid_shape, p.grid_digest,
              p.grid_format_signature, p.west, p.south, p.east, p.north,
              p.map_state, p.grid_source, g.dataset_id
     ORDER BY (g.dataset_id IS NOT NULL) DESC, dd.name, p.dataset_id
""")

_GRID_FILES = text("""
    SELECT id, file_name, size_bytes, storage_key, carries_lat, carries_lon, relative_path
      FROM d3_file
     WHERE dataset_id = :dataset_id AND kind = '기준 격자 파일'
     ORDER BY file_name, id
""")

_SET_DEFAULT = text("""
    INSERT INTO d3_lab_default_grid (lab_id, dataset_id, set_by)
    SELECT lab_id, id, :actor FROM d3_dataset
     WHERE id = :dataset_id AND deleted_at IS NULL
    ON CONFLICT (lab_id) DO UPDATE
       SET dataset_id = EXCLUDED.dataset_id, set_by = EXCLUDED.set_by, updated_at = now()
    RETURNING dataset_id
""")

_DEFAULT = text("""
    SELECT p.dataset_id, p.body_shape, p.grid_shape, p.grid_digest,
           p.grid_format_signature, p.west, p.south, p.east, p.north,
           p.map_state, p.grid_source
      FROM d3_lab_default_grid g
      JOIN d3_dataset_grid_profile p ON p.dataset_id = g.dataset_id
""")

_UPSERT_PROFILE = text("""
    INSERT INTO d3_dataset_grid_profile
      (dataset_id, lab_id, body_shape, grid_shape, grid_digest,
       grid_format_signature, west, south, east, north, map_state, grid_source)
    SELECT CAST(:dataset_id AS ulid), d.lab_id, :body_shape, :grid_shape, :grid_digest,
           :grid_format_signature, :west, :south, :east, :north, :map_state, :grid_source
      FROM d3_dataset d WHERE d.id = CAST(:dataset_id AS ulid)
    ON CONFLICT (dataset_id) DO UPDATE SET
      body_shape = EXCLUDED.body_shape, grid_shape = EXCLUDED.grid_shape,
      grid_digest = EXCLUDED.grid_digest,
      grid_format_signature = EXCLUDED.grid_format_signature,
      west = EXCLUDED.west, south = EXCLUDED.south,
      east = EXCLUDED.east, north = EXCLUDED.north,
      map_state = EXCLUDED.map_state, grid_source = EXCLUDED.grid_source,
      updated_at = now()
""")


def profile(session: Session, dataset_id: Ulid) -> dict | None:
    row = session.execute(_PROFILE, {"dataset_id": str(dataset_id)}).mappings().first()
    return None if row is None else dict(row)


def candidates(session: Session, body_shape: list[int] | tuple[int, int]) -> list[dict]:
    rows = session.execute(_CANDIDATES, {"shape": list(body_shape)}).mappings().all()
    return [dict(row) for row in rows]


def grid_files(session: Session, dataset_id: Ulid) -> list[dict]:
    return [dict(row) for row in session.execute(
        _GRID_FILES, {"dataset_id": str(dataset_id)}).mappings().all()]


def set_default(session: Session, *, dataset_id: Ulid, actor_id: Ulid) -> bool:
    return session.execute(_SET_DEFAULT, {
        "dataset_id": str(dataset_id), "actor": str(actor_id),
    }).first() is not None


def default_profile(session: Session) -> dict | None:
    row = session.execute(_DEFAULT).mappings().first()
    return None if row is None else dict(row)


def upsert_profile(session: Session, *, dataset_id: Ulid, values: dict) -> None:
    session.execute(_UPSERT_PROFILE, {"dataset_id": str(dataset_id), **values})


def map_states(session: Session, dataset_ids: list[Ulid]) -> dict[str, str]:
    if not dataset_ids:
        return {}
    query = text("""
        SELECT dataset_id, map_state FROM d3_dataset_grid_profile
         WHERE dataset_id IN :ids
    """).bindparams(bindparam("ids", expanding=True))
    return {row["dataset_id"]: row["map_state"] for row in session.execute(
        query, {"ids": [str(value) for value in dataset_ids]}).mappings()}
