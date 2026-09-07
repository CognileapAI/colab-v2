"""R-C `WU-C7` — `d9_topic_synonym` 에 **분류 5값** 한 칸 (질의 5 · PRD-01)

선언 정본은 db/ai/schema.sql 이다. 이 파일은 0005 까지의 스키마에 그 정본의 **차분만**
더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

⚠ **체인 머리가 라운드 파일의 전망과 다르다.** spec 이 `0004_*`(down = `0003_k2_ontology_seed`)
   로 적었지만 `db/ai` 체인에는 이미 `0004_k1b_concept_graph` · `0005_k2b_concept_graph_seed`
   가 서 있다(실측). 그래서 이 파일은 **`0006`**(down = `0005_k2b_concept_graph_seed`)다 —
   번호를 맞추려고 남의 리비전을 밀어내지 않는다.

━━ 무엇을 하는가 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`d9_topic_synonym.topic` 은 **주제 축** 4값이고, PRD-01 이 신설한 **분류 축**은 5값이다.
질의 5 가 「4값 ↔ 분류 5값 이관」이라 적었지만, `topic` 열을 5값으로 **갈아 끼우면** 안 된다:

  · `topic` 은 `ai-service` 가 `Interpretation.topic` 으로 내는 값이고 core-api 의 주제
    필터가 그 어휘를 그대로 받는다(`ports.TOPICS` · `catalog._TOPICS` · 선언 정본
    `db/platform/schema.sql d3_dataset_description.topic` **6값**). 주제 축과 분류 축은
    **서로 다른 축**이다(PRD-01·PRD-02 「세 축은 서로 독립이다」).
  · `db/ai/tools/k2b_graph_check.py` 의 완료 오라클이 `kind='주제'` 노드 4개와
    `d9_topic_synonym.topic` 4값의 일치를 잰다 — 갈아 끼우면 `0005` 의 오라클이 무너진다.

⟹ **PRD-01 이 플랫폼 쪽에서 한 것과 같은 모양**을 여기서도 한다: 「기존 `topic` 컬럼은
   삭제하지 않고 유지한다(되돌림 경로 · 이관 대조용)」 — `category` 한 칸을 **옆에** 세우고
   5값 CHECK 를 건다. drop 0 · 열 삭제 0.

━━ 매핑 — PRD-01 표의 「대표 인자 예시」가 근거다 ━━━━━━━━━━━━━━━━━━━━

지어내지 않는다. PRD-01 「Data Category」 표가 **대표 인자 예시**로 적은 낱말이 주제 표기와
글자 그대로 겹치는 셋만 옮긴다.

    강우·강수      → 기상·기후 인자   (PRD-01 축자 대표 인자 «강수량, 기온»)
    식생·NDVI      → 식생·탄소 인자   (PRD-01 축자 대표 인자 «NDVI, GPP»)
    토지피복·LULC  → 사회·경제 인자   (PRD-01 축자 대표 인자 «인구밀도, 토지이용»)
    지형·DEM       → **[미상]**        NULL 로 남긴다

⛔ `지형·DEM` 의 분류는 **PRD-01 어느 줄에서도 도출되지 않는다.** 다섯 분류의 설명·대표
   인자 어디에도 지형·고도·DEM 이 없다. 그래서 **고르지 않는다** — 그 자리를 지어내면
   정본에 없는 판단이 DB 에 값으로 남는다. 대신 NULL 로 두고 **건수를 NOTICE 로 찍는다**.
   (R-B 판정 7 의 「이관된 3쌍 · 지형·DEM 만 NULL」이 이 그림과 같은 셋·하나다.)

⚠ 이 표의 행은 **운영팀이 심는 사전 항목**이지 사용자가 적은 값이 아니다(schema 산문
   「항목 추가는 운영팀이 한다」 · P04 §5 전역 고정 목록). 미결-3 ⓐ 의 「사람 입력값
   자동 매핑 없음」은 `d3_dataset_description` 의 사용자 행에 대한 판정이고 여기가 아니다.

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

열 DROP 하나다. `topic` 을 한 글자도 안 건드렸으므로 **값 소실 0** 이고, 다시 올리면
같은 세 줄이 같은 근거로 되살아난다.

Revision ID: 0006_rc7_synonym_category
Revises: 0005_k2b_concept_graph_seed
"""
from __future__ import annotations

from alembic import op

revision = "0006_rc7_synonym_category"
down_revision = "0005_k2b_concept_graph_seed"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- ⑴ 분류 축 한 칸. **선언(`db/ai/schema.sql`)과 한 글자도 다르지 않아야** schema-diff 가 green 이다.
ALTER TABLE d9_topic_synonym ADD COLUMN category text
  CHECK (category IS NULL
         OR category IN ('수문 인자', '기상·기후 인자', '식생·탄소 인자',
                         '사회·경제 인자', '환경 인자'));

-- ⑵ 이관 — PRD-01 「대표 인자 예시」가 글자로 짚어 준 셋만.
-- RC7 SYNONYM MAP BEGIN
DO $$
DECLARE moved bigint; unknown_ bigint;
BEGIN
  UPDATE d9_topic_synonym SET category = CASE topic
      WHEN '강우·강수'     THEN '기상·기후 인자'
      WHEN '식생·NDVI'     THEN '식생·탄소 인자'
      WHEN '토지피복·LULC' THEN '사회·경제 인자'
    END
   WHERE topic IN ('강우·강수', '식생·NDVI', '토지피복·LULC');
  GET DIAGNOSTICS moved = ROW_COUNT;

  SELECT count(*) INTO unknown_ FROM d9_topic_synonym WHERE category IS NULL;
  RAISE NOTICE '[0006] d9_topic_synonym 분류 이관 — 옮긴 행 % · 분류 [미상] %행은 NULL 로 남긴다',
               moved, unknown_;
END $$;
-- RC7 SYNONYM MAP END
"""

DOWNGRADE = r"""
ALTER TABLE d9_topic_synonym DROP COLUMN category;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
