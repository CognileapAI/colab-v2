"""남한 지명 노드 · 남한⊂한반도 엣지 · 지명 별칭 2행을 심는다 — ai 체인

선언 정본은 `db/ai/schema.sql` 이다. 이 리비전은 `0009`·`0010` 과 같이 **스키마를 한 글자도
바꾸지 않는다** — `kind`·`relation`·`source_grade` CHECK 어디도 건드리지 않고 행만 넣는다.
새 값은 전부 기존 CHECK 안에 있다(`지명` · `안에 있다` · 등급 2·6).

왜 (`dev-package/intent/2026-09-21-evidence-promotion.md` 「판정 결과 — 2회차 지역(2026-09-26)」)
  Ted 판정 2026-09-26 「자료 지역 확정」 1 축자 — 「㈎ 기상청 4건(seq 1·2·19·20)=남한,
  GK-2A(seq 6)=한반도, 남한⊂한반도 관계로 연결」. 정본이 남한 자료를 갖게 되었고, 실무자
  사례는 「한반도」로 묻는다. 그 둘을 잇는 한 홉이 이 리비전이다.

무엇이 바뀌고 무엇이 안 바뀌는가
  ⑴ **넣는 것뿐이다** — 노드 1(`p-south-korea` 지명 등급 ②) + 엣지 1(`안에 있다` 등급 ⑥)
    + 별칭 2(`남한`·`대한민국` → `남한`). 노드 54→55 · 엣지 20→21 · 별칭 8→10.
  ⑵ 등급 ⑥ 엣지는 이 판정으로 `k2b_graph_check.py::APPROVED_G6` 에 한 줄 더한다.
    ⛔ 노드는 등급 ⑥ 이 없다(`K1b §A`) — 새 노드는 ② 다.
  ⑶ 한반도의 직계 하위(`안에 있다`)가 1→2 다(충청권 · 남한). 팬아웃 상한 6 안이다.
  ⑷ 기준(`k2b-graph-standard.tsv` · `k2-coverage-standard.tsv`)과 판정기가 같은 회차에
    **손으로** 개정된다.
  ⑸ 데이터 재작성 0 · 백필 0 · forward-only. D9 표에는 `lab_id` 가 없어 RLS 대상이 아니다.

⚠ `downgrade` 는 이 회차가 넣은 4행만 지운다(엣지 → 노드 순서 · FK). 목록은 시드 파일에서
  생성하지 않고 손으로 옮겨 적는다.

⚠ manifest digest 는 개념 ID·kind·label 을 먹으므로 이 리비전 뒤 모든 연구실의 manifest
  version 이 바뀐다(`0010` 과 같은 성질 — 재게시·requeue 가 따라오며 전면 재처리가 아니다).

Revision ID: 0012_region_south_korea
Revises: 0011_d10_model_call_ledger
"""
from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0012_region_south_korea"  # ⚠ 32자 이하다(`alembic_version_ai.version_num`)
down_revision = "0011_d10_model_call_ledger"
branch_labels = None
depends_on = None

# db/ai/versions/<이 파일> → db/ai/seed/region_south_korea.sql
SEED_SQL = Path(__file__).resolve().parents[1] / "seed" / "region_south_korea.sql"

#: `downgrade` 가 지울 행 — 시드 파일과 **같은 목록**이다(손으로 옮겨 적는다).
NEW_CONCEPTS = ("p-south-korea",)
NEW_EDGES = (("p-south-korea", "안에 있다", "p-korea-peninsula"),)
NEW_ALIASES = ("남한", "대한민국")


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
    for src, relation, dst in NEW_EDGES:
        op.execute(
            "DELETE FROM d9_concept_edge WHERE src = {} AND relation = {} AND dst = {}".format(
                _lit(src), _lit(relation), _lit(dst)
            )
        )
    ids = ", ".join(_lit(c) for c in NEW_CONCEPTS)
    op.execute(f"DELETE FROM d9_concept WHERE concept_id IN ({ids})")
    aliases = ", ".join(_lit(a) for a in NEW_ALIASES)
    op.execute(f"DELETE FROM d9_place_alias WHERE alias IN ({aliases})")
