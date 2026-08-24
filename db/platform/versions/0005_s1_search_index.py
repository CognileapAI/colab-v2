"""S1 — 자연어 검색 인프라: D3 카탈로그의 tsvector 생성 열 3개 + GIN 인덱스 3개

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0004 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 platform 체인인가 (CLAUDE.md §3-1 §3-3) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

검색이 훑는 글자는 **D3 Catalog 가 소유한 자기 테이블의 열**이다 — 이름·주제·요약
(`d3_dataset_description`) · 포맷·변수·좌표계·격자·묶음 이름(`d3_dataset_autometa`) ·
원천 표기(`d3_dataset`). 그래서 색인은 **그 열 옆에** 선다.

**AI 체인(D9·D10)에는 아무것도 넣지 않는다.** 넣었다면 그쪽이 D3 의 글자를 복제해
들고 있어야 하고, 그것을 최신으로 유지하려면 도메인 경계를 넘는 참조가 생긴다(§3-1).
(⚠ 이 파일에 AI 체인 **경로 문자열**을 적지 않는다 — `ai-no-lineage-write` 게이트 ⑩ 이
 platform 체인 파일의 그 문자열을 체인 참조로 세고 red 를 낸다. 실제로 한 번 냈다.)
`〈72〉` 가 정한 경계도 같은 방향이다 — **LLM 은 자연어 질의를 검색어·필터로 해석하는
데까지만 쓰고, 매칭·순위는 `tsvector` + 사전 3종이 정한다.** 매칭이 D3 쪽 일이므로
색인도 D3 쪽 일이다. 새 표도, 새 FK 도 만들지 않는다.

━━ 왜 생성 열(GENERATED … STORED)인가 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

트리거로 채우면 **채우는 것을 잊은 경로**가 생긴다(등록·수정·백필이 각각 다른 코드다).
생성 열은 그 경로가 존재할 수 없다 — 원본이 바뀌면 DB 가 바꾸고, 손으로는 못 쓴다.
`db/platform/tests/0005-assertions.sql` C-⑸⑹ 가 그 둘을 실물로 시험한다.

**생성 열은 IMMUTABLE 식만 받는다.** 그래서 배열(`variables text[]`)이 문제가 됐다 —
`array_to_string` 은 STABLE 이고(실측: `pg_proc.provolatile = 's'`), `v::text` 도 마찬가지라
둘 다 「generation expression is not immutable」로 거절된다(실측). 유일한 내장 대안
`array_to_tsvector` 는 IMMUTABLE 이지만 **대소문자를 그대로 둔다** — 실측하면
`array_to_tsvector(ARRAY['Precipitation'])` 는 `'Precipitation'` 을 내고
`to_tsquery('simple','Precipitation')` 은 `'precipitation'` 을 물어 **영원히 안 만난다.**
있는데 절대 안 맞는 색인이 될 뻔했다.

그래서 **`text[]` 로만 서명을 좁힌 IMMUTABLE 래퍼 하나**를 둔다. `array_to_string` 이
STABLE 인 이유는 `anyarray` 의 원소 출력 함수가 GUC 를 읽을 수 있기 때문이고
(`timestamptz` 는 DateStyle 을 읽는다), 원소 타입을 **`text` 로 못 박으면 그 사유가
사라진다** — `textout` 은 IMMUTABLE 이다. 다른 타입 배열에는 이 함수를 쓰지 않는다.

━━ ⚠ `ts_config` = `'simple'` — **`[정본 무근거]`** ━━━━━━━━━━━━━━━━━━━━━━━━

한국어 `ts_config` 를 정한 정본 줄이 없다([검색준비도] D-3-3 · S1-PLAN §7-㉨).
**지어내지 않는다**(`㊴-②`). 실측으로 확인한 것 = `postgres:16-alpine` 의
`pg_ts_config` 29개에 한국어가 **없다**(있는 것: simple + 영어권·유럽어 28종).

`'simple'` 이 실제로 하는 일 — **소문자화 + 공백·구두점 분리뿐**이다. 어간 추출도
불용어도 형태소 분석도 없다. 결과: 「강수량」은 통째로 한 낱말이고 **「강수」로는 안
잡힌다**(접두 질의 `강수:*` 로는 잡힌다). 영문 변수명·기관명·좌표계 코드는 잘 맞는다.

값이 바뀌면(예: 형태소 분석기 확장 도입) 이 마이그레이션의 리터럴 3곳 + 오라클 D 절이
함께 바뀌고 **전 행이 재생성**된다. 그 사실을 시험이 붙잡고 있다.

━━ pgvector 는 여기 없다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`postgres:16-alpine` 에 `vector` 확장이 **없다**(실측 — 아래 두 증거).
  ① `SELECT … FROM pg_available_extensions WHERE name='vector'` → 0행
     (같은 질의에서 `pg_trgm`·`unaccent` 는 나온다 — 질의가 틀린 것이 아니다)
  ② 컨테이너의 `/usr/local/share/postgresql/extension/` 에 `vector*` 파일 0건
확장을 「있겠지」로 걸지 않는다. 이미지를 조용히 바꾸지도 않는다 — 그 판단과
`compose.i2.yml` 은 이 레인 소유가 아니다. **`K4-a` 는 pgvector 를 소비하지 않으므로
(`〈72〉` — 매칭·순위는 tsvector) 이 마이그레이션은 그것 없이 완결된다.**

Revision ID: 0005_s1_search_index
Revises: 0004_p2_grid_axis_and_d5
"""
from __future__ import annotations

from alembic import op

revision = "0005_s1_search_index"
down_revision = "0004_p2_grid_axis_and_d5"
branch_labels = None
depends_on = None


SEARCH = r"""
-- text[] **전용** 결합기. 다른 타입 배열에 쓰지 않는다 (윗주석 참조).
CREATE FUNCTION d3_search_join(arr text[]) RETURNS text
  LANGUAGE sql IMMUTABLE PARALLEL SAFE
  AS $$ SELECT array_to_string(coalesce(arr, '{}'::text[]), ' ') $$;

-- 원천 표기. 계보 그래프의 점선 노드 이름이 검색어가 된다.
ALTER TABLE d3_dataset ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', coalesce(source_label, '')), 'B')
  ) STORED;
CREATE INDEX d3_dataset_search_idx ON d3_dataset USING gin (search_vector);

-- 사람이 적은 말. **이름이 가장 무겁다** — K4-a 의 순위가 여기서 갈린다.
ALTER TABLE d3_dataset_description ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', coalesce(name, '')),    'A') ||
    setweight(to_tsvector('simple', coalesce(topic, '')),   'B') ||
    setweight(to_tsvector('simple', coalesce(summary, '')), 'C')
  ) STORED;
CREATE INDEX d3_dataset_description_search_idx
  ON d3_dataset_description USING gin (search_vector);

-- 파일에서 자동으로 읽은 말. 변수명·포맷이 좌표계·격자·묶음 이름보다 앞선다.
ALTER TABLE d3_dataset_autometa ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('simple',
      coalesce(format, '') || ' ' || d3_search_join(variables)), 'B') ||
    setweight(to_tsvector('simple',
      coalesce(crs, '') || ' ' || coalesce(grid, '') || ' ' ||
      coalesce(bundle_file_name, '')), 'C')
  ) STORED;
CREATE INDEX d3_dataset_autometa_search_idx
  ON d3_dataset_autometa USING gin (search_vector);
"""

DOWN = r"""
DROP INDEX IF EXISTS d3_dataset_autometa_search_idx;
DROP INDEX IF EXISTS d3_dataset_description_search_idx;
DROP INDEX IF EXISTS d3_dataset_search_idx;

ALTER TABLE d3_dataset_autometa    DROP COLUMN IF EXISTS search_vector;
ALTER TABLE d3_dataset_description DROP COLUMN IF EXISTS search_vector;
ALTER TABLE d3_dataset             DROP COLUMN IF EXISTS search_vector;

-- 열을 먼저 지운다 — 열이 이 함수에 의존하므로 순서를 바꾸면 DROP 이 거절된다.
DROP FUNCTION IF EXISTS d3_search_join(text[]);
"""


def upgrade() -> None:
    op.execute(SEARCH)


def downgrade() -> None:
    op.execute(DOWN)
