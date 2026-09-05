"""D3 Catalog — 다운로드 집행이 읽는 질의 (`PLAN-SoT §9 〈339〉-(다)`). **읽기 전용.**

`d3_catalog.py` 와 같은 도메인(D3)의 두 번째 모듈이다 — 그쪽이 목록 op 을 위해 `DatasetFile`
dict 로 접어 내리는 자리(`list_files`)와 달리, 다운로드는 **저장 키**가 필요하다.
행의 모양(`FileRow`)과 열 집합(`_FILE_COLUMNS`)·매핑(`_file_row`)은 그쪽 것을 그대로 쓴다 —
열을 두 곳에 적으면 한쪽만 넓힌 날 KeyError 가 난다(그쪽 주석의 규칙 그대로).

경계는 RLS 가 건다: 연구실(`lab_boundary`)과 본체(`body_access` RESTRICTIVE). 그래서 잠긴
데이터셋의 파일 행은 **여기서 0행**이고, 바이트 시점의 재판정이 그 성질 위에 선다.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..kernel.ids import Ulid
from .d3_catalog import _FILE_COLUMNS, FileRow, _file_row

#: 묶음(zip)의 엔트리 순서 — 본체가 먼저(kind DESC: '본체' > '기준 격자 파일'), 그 안에서는
#: 폴더 경로 → 이름 → id. 결정적이어야 같은 데이터셋의 zip 이 매번 같은 순서로 나온다.
_FILES = text(f"""
    SELECT {_FILE_COLUMNS}
      FROM d3_file
     WHERE dataset_id = :dataset_id
     ORDER BY kind DESC, relative_path NULLS LAST, file_name, id
""")


def file_rows(session: Session, dataset_id: Ulid) -> list[FileRow]:
    """그 데이터셋의 파일 행 전건 — 저장 키 포함. 잠겼거나 경계 밖이면 빈 목록이다."""
    rows = session.execute(_FILES, {"dataset_id": str(dataset_id)}).mappings().all()
    return [_file_row(r) for r in rows]
