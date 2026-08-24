"""S1 — 한국어 매칭 보강: `pg_trgm` 확장 + 데이터셋 이름의 삼중자 색인

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0005 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 이것이 필요한가 (PLAN-SoT §9-〈89〉) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`0005` 가 자기 서두에 한계를 적어 두었다 — `ts_config='simple'` 은 **소문자화 + 공백·
구두점 분리뿐**이고 형태소를 자르지 않는다. 그래서 「강수」가 「강수량」을 못 잡는다.
그 줄은 이어서 **「접두 질의 `강수:*` 로는 잡힌다」**고도 적었고, 그것이 이 리비전의
절반이다. 나머지 절반은 접두로도 못 넘는 자리다 — **질의가 색인된 낱말보다 긴 경우**
(「강수량」으로 「강수」를 부르기)와 표기가 어긋난 경우. 거기를 유사도가 받는다.

**매칭 규칙을 바꾸는 일이라 정본이 먼저 바뀌었다.** `〈72〉-㉮` 가 「매칭·순위는 tsvector
+ 사전 3종」으로 매칭 방식까지 못 박고 있었고, `〈89〉` 가 그 줄을 개정한 뒤에 이 파일이
있다. 순서를 뒤집으면 코드 레인이 정본을 혼자 옮긴 것이 된다 (CLAUDE.md §5).

━━ 왜 platform 체인인가 (CLAUDE.md §3-1 §3-3) ━━━━━━━━━━━━━━━━━━━━━━━━━

색인이 붙는 글자가 **D3 Catalog 가 소유한 자기 테이블의 열**(`d3_dataset_description.name`)
이기 때문이다. `0005` 와 같은 근거이고, 같은 이유로 AI 체인에는 아무것도 넣지 않는다.
(⚠ 이 파일에 그 체인의 **경로 문자열**을 적지 않는다 — 게이트가 그 글자를 체인 참조로
 센다. 실제로 red 를 낸 적이 있다. 고칠 것은 게이트가 아니라 문장이다.)

━━ 왜 이름 한 칸에만 거는가 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`0005` 가 이름에 A 가중치를 준 것과 같은 판단이다 — 사람이 데이터셋을 부를 때 쓰는 말은
이름이고, 요약·자동메타까지 유사도로 훑으면 **아무 말이나 조금씩 닮아** 관련도 막대가
전부 같은 길이가 된다(`§D-6` 의 과확장과 같은 실패 모양이다). 보조 팔은 좁을수록 정직하다.

━━ 확장은 이미지에 있는 것만 건다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

실측 — `postgres:16-alpine` 의 `pg_available_extensions` 에 `pg_trgm` **1.6** 이 있다.
같은 질의에서 `vector` 는 0행이었고(`0005` 서두), 그래서 그때는 걸지 않았다.
**「있겠지」로 걸지 않는다**는 그 규율이 여기서도 그대로다.

Revision ID: 0006_s1_trgm_matching
Revises: 0005_s1_search_index
"""
from __future__ import annotations

from alembic import op

revision = "0006_s1_trgm_matching"
down_revision = "0005_s1_search_index"
branch_labels = None
depends_on = None


TRGM = r"""
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX d3_dataset_description_name_trgm_idx
  ON d3_dataset_description USING gin (name gin_trgm_ops);
"""

DOWN = r"""
DROP INDEX IF EXISTS d3_dataset_description_name_trgm_idx;

-- 색인을 먼저 지운다 — 색인이 이 확장의 연산자 클래스에 의존하므로 순서를 바꾸면 거절된다.
DROP EXTENSION IF EXISTS pg_trgm;
"""


def upgrade() -> None:
    op.execute(TRGM)


def downgrade() -> None:
    op.execute(DOWN)
