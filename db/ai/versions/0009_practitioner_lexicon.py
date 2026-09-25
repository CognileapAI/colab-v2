"""실무자 사례 14건이 드러낸 어휘 13행을 심는다 — ai 체인

선언 정본은 `db/ai/schema.sql` 이다. 이 리비전은 **스키마를 한 글자도 바꾸지 않는다** —
CHECK·컬럼·인덱스 어디도 건드리지 않고 행만 넣는다. 그래서 `schema-diff` 는 이 리비전 앞뒤로
같은 것을 봐야 한다(그게 이 회차의 승인 범위가 「(i) 스키마 무변경」인 것의 실물이다).

왜 (`dev-package/intent/2026-09-18-practitioner-cases-ontology.md` · Ted 「다 권고대로」 2026-09-18)
  실무자 14건이 요구하는 검색 성분 중 온톨로지가 닿는 것은 **어휘 관문뿐**인데, 그 관문조차
  막혀 있었다 — `eval/k4-search/README.md:68` 축자 「여전히 0건인 것 — 「강수량」·「위성」·
  「다운스케」. 매칭은 표기를 넘지 못한다.」 그리고 `d9_place_alias` 는 4행뿐이라 **「한반도」가
  사전에 없었다** — 같은 값이 `d9_concept` 에는 등급 ② 로 이미 있는데도 그랬다(비대칭).

무엇이 바뀌고 무엇이 안 바뀌는가
  ⑴ **넣는 것뿐이다** — 주제 동의어 9행 + 지명 별칭 4행. 기존 행은 한 줄도 지우거나 고치지 않는다.
  ⑵ ⛔ **개념 그래프(`d9_concept`·`d9_concept_edge`)를 만지지 않았다.** 결정 4(ERA5·ECMWF
    원천표기)·결정 5(주제 노드 4→6)는 **보류**다. 그래서 `k2b-graph-standard.tsv` 도
    `k2b_graph_check.py` 도 이 리비전 앞뒤로 같은 값을 본다.
  ⑶ ⛔ **스키마 CHECK 무변경.** `topic` 은 `0006` 이 이미 6값으로 넓혔고 새 9행은 전부
    「강우·강수」다. `d9_place_alias` 에는 값 CHECK 자체가 없다.
  ⑷ 데이터 재작성 0 · 백필 0 · forward-only. RLS 구간을 열지 않는다 — 이 체인의 D9 표에는
    `lab_id` 가 없어 애초에 RLS 대상이 아니다.
  ⑸ 커버리지 기준(`db/ai/seed/k2-coverage-standard.tsv`)의 지명 항목이 4→6 으로 함께 개정된다.
    기준은 **손으로** 옮겨 적는다 — 적재물에서 생성하면 체크가 영원히 green 이 된다.

⚠ `downgrade` 는 이 회차가 넣은 13행만 지운다. 목록을 시드 파일에서 생성하지 않는 이유는
  기준 TSV 를 적재물에서 만들지 않는 이유와 같다 — 한 파일이 저 혼자 맞다고 말하게 두지 않는다.

Revision ID: 0009_practitioner_lexicon
Revises: 0008_dataset_knowledge
"""
from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0009_practitioner_lexicon"  # ⚠ 32자 이하다(`alembic_version_ai.version_num`)
down_revision = "0008_dataset_knowledge"
branch_labels = None
depends_on = None

# db/ai/versions/<이 파일> → db/ai/seed/practitioner_lexicon.sql
SEED_SQL = Path(__file__).resolve().parents[1] / "seed" / "practitioner_lexicon.sql"

#: `downgrade` 가 지울 질의어 9개 — 시드 파일과 **같은 목록**이다(손으로 옮겨 적는다).
NEW_SYNONYMS = ("강수량", "강수", "강우", "강우량", "강수자료",
                "강우관측", "집중호우", "호우", "precipitation")

#: `downgrade` 가 지울 별칭 4개 — 같은 규율이다.
NEW_ALIASES = ("한반도", "Korea", "충청권", "southern Gyeonggi and Chungcheong regions")


def _seed_sql() -> str:
    """파일이 제 트랜잭션을 여닫는다 — alembic 이 이미 트랜잭션 안이므로 BEGIN/COMMIT 은 뺀다."""
    return "\n".join(
        line for line in SEED_SQL.read_text(encoding="utf-8").splitlines()
        if line.strip().upper() not in ("BEGIN;", "COMMIT;")
    )


def upgrade() -> None:
    op.execute(_seed_sql())


def downgrade() -> None:
    synonyms = ", ".join(f"'{s}'" for s in NEW_SYNONYMS)
    aliases = ", ".join("'" + a.replace("'", "''") + "'" for a in NEW_ALIASES)
    op.execute(f"DELETE FROM d9_topic_synonym WHERE synonym IN ({synonyms})")
    op.execute(f"DELETE FROM d9_place_alias WHERE alias IN ({aliases})")
