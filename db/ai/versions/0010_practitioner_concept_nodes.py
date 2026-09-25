"""보류였던 개념 그래프 6행을 심는다 — ai 체인

선언 정본은 `db/ai/schema.sql` 이다. 이 리비전도 `0009` 와 같이 **스키마를 한 글자도 바꾸지
않는다** — `kind`·`relation`·`source_grade` CHECK 어디도 건드리지 않고 행만 넣는다. 새 값은
전부 기존 CHECK 안에 있다(`원천표기`·`주제` · `같은 말이다` · 등급 5·1).

왜 (`dev-package/intent/2026-09-18-practitioner-cases-ontology.md` · Ted 판정 2026-09-18)
  1회차(`0009`)가 13행만 싣고 6행을 「보류 — 재검토 대기」로 내려놓았다. 그 보류 둘을
  Ted 가 이번에 닫았다.
    · 결정 4 = **재개봉해 싣는다.** 축자 「없어도 앞으로 추가될거니까 넣자」
      2026-08-25 `F-12 ㈎`(「뺀다」)의 재개봉이다. 그때의 기각 사유는
      「15 데이터셋에 ECMWF·ERA5 원천이 0 건」이었고 이번 판정이 그 자리를 대체한다.
    · 결정 5 = **정합화한다.** 축자 「가뭄 파일포멧 예제 넣자. 데이터가 들어오면 검색이
      되어야 한다」 — 사전은 `0006` 으로 이미 6값인데 그래프만 4개이던 비대칭을 없앤다.

무엇이 바뀌고 무엇이 안 바뀌는가
  ⑴ **넣는 것뿐이다** — 노드 5(원천표기 3 · 주제 2) + 엣지 1. 기존 행은 한 줄도 지우거나
    고치지 않는다. 노드 49→54 · 엣지 19→20.
  ⑵ ⛔ **등급 6 노드는 그대로 0 건이다** (`K1b §A`). 새 엣지는 등급 5(기획 정본 어휘)라
    `k2b_graph_check.py::APPROVED_G6` 9줄도 **한 글자도 바뀌지 않는다**.
  ⑶ ⛔ **스키마 CHECK 무변경.** `relation` 은 3값 그대로다 — `~이 제공한다`(ECMWF→ERA5)는
    결정 8 이 닫아 둔 자리이고 이 회차가 열지 않는다. 그래서 `s-era5` 는 엣지가 없는 노드다.
  ⑷ 기준(`db/ai/seed/k2b-graph-standard.tsv`)과 판정기(`k2b_graph_check.py`)가 같은 회차에
    **손으로** 개정된다 — 기준을 적재물에서 생성하면 체크가 영원히 green 이 된다.
  ⑸ 데이터 재작성 0 · 백필 0 · forward-only. 이 체인의 D9 표에는 `lab_id` 가 없어 RLS 대상이
    아니다.

⚠ `downgrade` 는 이 회차가 넣은 6행만 지운다. 목록을 시드 파일에서 생성하지 않는 이유는
  기준 TSV 를 적재물에서 만들지 않는 이유와 같다 — 한 파일이 저 혼자 맞다고 말하게 두지 않는다.
  엣지를 먼저 지우고 노드를 지운다(`d9_concept_edge` 가 `d9_concept` 을 FK 로 참조한다).

⚠ manifest digest 는 개념 ID·kind·label 을 먹으므로 이 리비전 뒤 **모든 연구실의 manifest
  version 이 바뀐다.** 재게시와 변경 엔트리에 의존하는 binding 의 `requeue` 가 따라온다
  (`services/core-api/tests/test_search_ontology.py:51`). 「전면 재처리」가 아니다.

Revision ID: 0010_practitioner_concept
Revises: 0009_practitioner_lexicon
"""
from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0010_practitioner_concept"  # ⚠ 32자 이하다(`alembic_version_ai.version_num`)
down_revision = "0009_practitioner_lexicon"
branch_labels = None
depends_on = None

# db/ai/versions/<이 파일> → db/ai/seed/practitioner_concept_nodes.sql
SEED_SQL = Path(__file__).resolve().parents[1] / "seed" / "practitioner_concept_nodes.sql"

#: `downgrade` 가 지울 노드 5개 — 시드 파일과 **같은 목록**이다(손으로 옮겨 적는다).
NEW_CONCEPTS = ("s-era5", "s-ecmwf", "s-ecmwf-ko", "t-drought", "t-fileformat")

#: `downgrade` 가 지울 엣지 1행 — 같은 규율이다.
NEW_EDGES = (("s-ecmwf", "같은 말이다", "s-ecmwf-ko"),)


def _seed_sql() -> str:
    """파일이 제 트랜잭션을 여닫는다 — alembic 이 이미 트랜잭션 안이므로 BEGIN/COMMIT 은 뺀다."""
    return "\n".join(
        line for line in SEED_SQL.read_text(encoding="utf-8").splitlines()
        if line.strip().upper() not in ("BEGIN;", "COMMIT;")
    )


def _lit(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def upgrade() -> None:
    op.execute(_seed_sql())


def downgrade() -> None:
    # 엣지가 먼저다 — 노드를 먼저 지우면 FK 가 막는다.
    for src, relation, dst in NEW_EDGES:
        op.execute(
            "DELETE FROM d9_concept_edge WHERE src = {} AND relation = {} AND dst = {}".format(
                _lit(src), _lit(relation), _lit(dst)
            )
        )
    ids = ", ".join(_lit(c) for c in NEW_CONCEPTS)
    op.execute(f"DELETE FROM d9_concept WHERE concept_id IN ({ids})")
