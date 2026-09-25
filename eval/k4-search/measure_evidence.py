"""28건 근거 적재 **전/후**를 같은 DB 에서 나란히 잰다 — `measure.py` 의 짝.

`measure.py` 는 AI 그래프 확장을 재고 그 대상은 `seed-15.sql` 의 15건이다. 이 회차가 바꾼 것은
**D3 의 검색 근거·topic·source_label** 이라 그 하네스가 재는 자리를 하나도 움직이지 않는다
(실측 — 9질의 전부 동일). 그래서 이 파일이 바뀐 자리를 잰다.

같은 DB 에서 두 번 잰다: 먼저 적재된 상태(after)를, 그다음 같은 트랜잭션 안에서 근거·topic·
source_label 만 비운 상태(before)를 재고 **rollback** 한다. 두 DB 를 따로 세우면 시드 차이가
측정에 섞이므로 그러지 않는다.

**제품 코드가 아니다.** DEV 제품 DB 에 대고 돌리지 않는다 — 일회용 DB 전용이다
(before 측정이 근거 행을 지웠다가 되돌리는 자리라 운영 DB 에서는 절대 돌리지 않는다).

쓰는 법
  services/core-api/.venv/bin/python eval/k4-search/measure_evidence.py <platform-app-url>
"""
from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "services" / "core-api" / "src"))

from sqlalchemy import text                                          # noqa: E402

from colab_core.domains import d3_catalog, d3_client_search          # noqa: E402
from colab_core.kernel.auth import Subject                           # noqa: E402
from colab_core.kernel.db import make_engine, make_session_factory   # noqa: E402
from colab_core.kernel.ids import Ulid                               # noqa: E402
from colab_core.kernel.scope import apply_scope                      # noqa: E402

LAB = "0000000000000000000000000A"
ACCOUNT = "000000000000000000000000A1"
#: 일회용 DB 의 DEV 재현 28건에만 붙는 ID 꼴. 시드 세 건(DSA1·DSA2·DSB1)은 건드리지 않는다.
DEV_LIKE = "%DV__"

LEXICAL = (
    ("주제 결합 — 「강수」 + topic 강우·강수", {"terms": ("강수",), "topic": "강우·강수"}),
    ("주제 결합 — 「가뭄」 + topic 가뭄", {"terms": ("가뭄",), "topic": "가뭄"}),
    ("원천 표기 — 「기상청」", {"terms": ("기상청",), "topic": None}),
)

CONDITIONS = (
    ("조건 검색 platform=ground", {"platform": "ground"}),
    ("조건 검색 platform=satellite", {"platform": "satellite"}),
    ("조건 검색 cadence=hourly (결정 2-ⓐ 로 연 값)", {"cadence": "hourly"}),
    ("조건 검색 cadence=15min", {"cadence": "15min"}),
    ("조건 검색 directObservation=true", {"directObservation": True}),
    ("조건 검색 maxResolutionM<=5000", {"maxResolutionM": 5000}),
    ("조건 검색 variable=precipitation + coverageYear 2022",
     {"variable": "precipitation", "coverageYear": 2022}),
)


def _measure(session, label: str) -> None:
    print(f"\n### {label}")
    for name, kwargs in LEXICAL:
        _rows, total = d3_catalog.search_datasets(session, limit=50, offset=0, **kwargs)
        print(f"  {name}: {total}건")
    for name, conditions in CONDITIONS:
        rows, _capped = d3_client_search.candidates(session, dict(conditions))
        print(f"  {name}: {len(rows)}건")
    counts = {
        "d3_search_evidence": "SELECT count(*) FROM d3_search_evidence",
        "topic 비-NULL": "SELECT count(*) FROM d3_dataset_description WHERE topic IS NOT NULL",
        "source_label 비-NULL": "SELECT count(*) FROM d3_dataset WHERE source_label IS NOT NULL",
    }
    print("  " + " · ".join(f"{k} {session.execute(text(v)).scalar()}행"
                            for k, v in counts.items()))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 78
    factory = make_session_factory(make_engine(sys.argv[1]))
    session = factory()
    session.begin()
    try:
        apply_scope(session, Subject(account_id=Ulid(ACCOUNT), lab_id=Ulid(LAB)))
        _measure(session, "적재 후 (after)")
        session.execute(text("DELETE FROM d3_search_evidence WHERE dataset_id LIKE :p"),
                        {"p": DEV_LIKE})
        session.execute(text("UPDATE d3_dataset_description SET topic=NULL WHERE dataset_id LIKE :p"),
                        {"p": DEV_LIKE})
        session.execute(text("UPDATE d3_dataset SET source_label=NULL WHERE id LIKE :p"),
                        {"p": DEV_LIKE})
        _measure(session, "적재 전 (before) — 같은 DB 에서 근거·topic·source_label 만 비운 상태")
    finally:
        session.rollback()
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
