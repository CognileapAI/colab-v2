"""K2 — 온톨로지 시드 적재: 정본 인용 13 + 주제 4 + 지명 4

범위 정본 = dev-package/ONTOLOGY-SCOPE.md (G8, Ted 승인 2026-08-23)
결정      = PLAN-SoT §9-㊸-④-1 (다) 하이브리드 · ④-2 (가) 문서가 정본 · ④-3/④-4 시드 테이블 3개
규율      = PLAN-SoT §9-㊴-② — 정본에 없으면 만들지 않고 [정본 무근거]로 남긴다

**왜 마이그레이션인가 (스크립트가 아니라).**
  이 시드는 환경별로 갈리는 데이터가 아니다. 값의 출처가 기획 정본 인용뿐이고(K1 §3),
  어느 환경이든 정확히 같은 21개여야 한다. K3(계보 제안)·K4(자연어 검색)는 이 사전이
  **있다는 전제**로 동작한다 — 없으면 제안 문장과 검색 근거가 조용히 비어 버린다.
  「모든 환경에 존재해야 하는 시드는 체인에 들어간다」에 정확히 해당한다.
  환경별로 갈리는 데이터(예시 연구실·데모 데이터셋)였다면 체인 밖 스크립트여야 한다. 그런 것이 아니다.

**왜 SQL 파일을 읽어 실행하는가.**
  같은 시드가 두 벌(마이그레이션 안의 DDL + 재실행용 스크립트)로 갈리면 어느 쪽이 정본인지
  알 수 없게 된다. 적재물 정본은 db/ai/seed/k2_ontology_seed.sql 하나이고,
  이 리비전은 그 파일을 실행하는 절차다. 사람이 재적재할 때도 같은 파일을 psql 로 돌린다.
  그래서 SQL 은 ON CONFLICT … DO UPDATE 로 멱등하다 — 두 번 돌아도 사전이 두 벌이 되지 않는다.

이 리비전은 DDL 을 만들지 않는다. 선언 정본 db/ai/schema.sql 은 그대로이고 schema-diff 대상이 아니다.

Revision ID: 0003_k2_ontology_seed
Revises: 0002_k1_ontology
"""
from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "0003_k2_ontology_seed"
down_revision = "0002_k1_ontology"
branch_labels = None
depends_on = None

# db/ai/versions/<이 파일> → db/ai/seed/k2_ontology_seed.sql
SEED_SQL = Path(__file__).resolve().parents[1] / "seed" / "k2_ontology_seed.sql"


def upgrade() -> None:
    sql = SEED_SQL.read_text(encoding="utf-8")
    # 파일이 자기 트랜잭션을 여닫는다. alembic 이 이미 트랜잭션 안이므로 BEGIN/COMMIT 은 뺀다.
    sql = "\n".join(
        line for line in sql.splitlines()
        if line.strip().upper() not in ("BEGIN;", "COMMIT;")
    )
    op.execute(sql)


def downgrade() -> None:
    # 시드가 넣은 키만 지운다. 사람이 나중에 더한 행은 건드리지 않는다.
    op.execute(
        """
        DELETE FROM d9_method_term WHERE term IN (
          '격자 보간','품질검사','유역 클리핑','유역 평균','유역 집계','일 단위 평균',
          '유역 경계로 잘라냄','임계값 초과일 집계','재격자화','편의 보정','다운스케일',
          '전처리','보간 방식(선형/최근접)')
        """
    )
    op.execute(
        """
        DELETE FROM d9_topic_synonym WHERE synonym IN (
          '강우데이터','강우·강수','식생·NDVI','지형·DEM','토지피복·LULC')
        """
    )
    op.execute(
        """
        DELETE FROM d9_place_alias WHERE alias IN (
          '낙동강 유역','한강 상류','금강 하굿둑','한강 유역')
        """
    )
