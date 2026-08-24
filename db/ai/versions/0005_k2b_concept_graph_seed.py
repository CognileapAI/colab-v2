"""K2b — 그래프 시드 적재: 노드 49 · 엣지 19 (등급 ⑥ 엣지 8)

내용 정본 = dev-package/sessions/K1b-ONTOLOGY-CONTENT.md §A·§B
판정      = Ted 2026-08-25 (PLAN-SoT §9) — F-4d ❌ · F-7 ❌ · F-10 ㈏ · F-12 ㈎ · 나머지 ✅

**왜 마이그레이션인가.** 0003 과 같은 근거다 — 값의 출처가 정본 인용과 SEED-DATA 실측뿐이라
환경별로 갈리지 않는다. K4-b(그래프 확장 검색)는 이 그래프가 **있다는 전제**로 동작한다.
없으면 확장이 조용히 0 건이 되고, 검색은 아무 에러 없이 나빠진다.

**왜 SQL 파일을 읽어 실행하는가.** 0003 과 같은 규약이다. 적재물 정본은
db/ai/seed/k2b_concept_graph_seed.sql 하나이고, 이 리비전은 그 파일을 실행하는 절차다.
사람이 재적재할 때도 같은 파일을 psql 로 돌린다 — 그래서 SQL 이 ON CONFLICT … DO UPDATE 로 멱등하다.

**완료 오라클은 이 리비전이 아니다.** db/ai/seed/k2b-graph-standard.tsv(기준)와
db/ai/tools/k2b_graph_check.py(판정기)가 적재물과 갈라져 있고, 특히 **source_grade=6 행이
Ted 승인 목록과 정확히 일치하는지**를 본다 — 승인 안 난 도메인 상식이 몰래 들어오면 red 다.
판정기가 red 를 낼 수 있다는 증명은 db/ai/tools/k2b-graph-selftest.sh (16 케이스).

이 리비전은 DDL 을 만들지 않는다. 선언 정본 db/ai/schema.sql 은 0004 가 이미 반영했다.

Revision ID: 0005_k2b_concept_graph_seed
Revises: 0004_k1b_concept_graph
"""
from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0005_k2b_concept_graph_seed"
down_revision = "0004_k1b_concept_graph"
branch_labels = None
depends_on = None

# db/ai/versions/<이 파일> → db/ai/seed/k2b_concept_graph_seed.sql
SEED_SQL = Path(__file__).resolve().parents[1] / "seed" / "k2b_concept_graph_seed.sql"


def upgrade() -> None:
    sql = SEED_SQL.read_text(encoding="utf-8")
    # 파일이 자기 트랜잭션을 여닫는다. alembic 이 이미 트랜잭션 안이므로 BEGIN/COMMIT 은 뺀다.
    sql = "\n".join(
        line for line in sql.splitlines()
        if line.strip().upper() not in ("BEGIN;", "COMMIT;")
    )
    op.execute(sql)


def downgrade() -> None:
    # 시드가 넣은 것만 지운다. 엣지가 먼저다 (FK).
    # 사람이 나중에 더한 행은 건드리지 않는다 — 그래서 TRUNCATE 를 쓰지 않는다.
    op.execute(
        """
        DELETE FROM d9_concept_edge
         WHERE (src, relation, dst) IN (
           ('m-nearest','같은 말이다','m-nearest-en'),
           ('m-bilinear','같은 말이다','m-bilinear-en'),
           ('m-cokriging','같은 말이다','m-regkriging'),
           ('m-dqf','같은 말이다','m-qc'),
           ('m-basin-clip','같은 말이다','m-basin-cut'),
           ('p-chungcheong','같은 말이다','p-chungcheong-en'),
           ('p-korea-en','같은 말이다','p-korea-peninsula'),
           ('s-gk2a','같은 말이다','s-gk2a-hyphen'),
           ('s-gk2a-hyphen','같은 말이다','s-gk2a-ko'),
           ('s-nmsc','같은 말이다','s-nmsc-ko'),
           ('s-kwra','같은 말이다','s-kwra-ko'),
           ('m-nearest','~의 한 가지다','m-regrid'),
           ('m-bilinear','~의 한 가지다','m-regrid'),
           ('m-idw','~의 한 가지다','m-regrid'),
           ('m-nearest','~의 한 가지다','m-interp-mode'),
           ('m-bilinear','~의 한 가지다','m-interp-mode'),
           ('m-grid-interp','~의 한 가지다','m-regrid'),
           ('m-downscale','~의 한 가지다','m-regrid'),
           ('p-chungcheong','안에 있다','p-korea-peninsula')
         )
        """
    )
    op.execute(
        """
        DELETE FROM d9_concept WHERE concept_id IN (
          'm-grid-interp','m-qc','m-basin-clip','m-basin-mean','m-basin-agg','m-daily-mean',
          'm-basin-cut','m-thresh-days','m-regrid','m-bias-corr','m-downscale','m-preproc',
          'm-interp-mode','m-nearest','m-nearest-en','m-bilinear','m-bilinear-en','m-idw',
          'm-cokriging','m-regkriging','m-reproject','m-savgol','m-thinning','m-unet','m-dqf',
          'm-roi-crop','m-monthly-mean',
          't-precip','t-veg','t-dem','t-lulc',
          'p-nakdong','p-han-upper','p-geum-estuary','p-han','p-chungcheong','p-chungcheong-en',
          'p-korea-peninsula','p-korea-en',
          's-gk2a-hyphen','s-gk2a','s-gk2a-ko','s-nmsc','s-nmsc-ko','s-kma-hub','s-modis',
          's-hls','s-kwra','s-kwra-ko'
        )
        """
    )
