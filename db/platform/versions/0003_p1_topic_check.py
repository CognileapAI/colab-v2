"""P1 — 데이터셋의 주제를 DB 가 강제한다 (d3_dataset_description.topic 4값 CHECK)

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0002 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

왜 (PLAN-SoT §9-〈55〉 · ⑲)
  `⑲`「값 집합은 DB가 강제한다」가 P0 에서 확정 열거값 9종을 못 박았을 때 **주제가 그 목록에 없었다.**
  주제 4값을 정한 `㊸-④-2` 가 하루 뒤(2026-08-23)에 났기 때문이지 판단이 아니었다 — **시간차다.**
  4값 CHECK 가 걸린 곳은 `d9_topic_synonym`(ai 체인)뿐이고 그것은 **사전 항목**을 지키지
  데이터셋의 주제를 지키지 않는다. 앱 코드로만 지키면 이 보장은 문서상 약속으로 내려앉는다.
  → 주제가 **열거값 10번째**가 된다.

무엇을 강제하고 무엇을 강제하지 않는가 (〈55〉-③)
  강제하는 것은 **「값이 있다면 넷 중 하나」**이지 「반드시 있다」가 아니다.
  **nullable 을 유지한다** — 사람이 아직 주제를 정하지 않은 상태가 표현되어야 한다.
  대가는 이미 감수했다: 4값이 담지 못하는 실데이터(`D-11` SPI/SPEI · `D-12` GK2A L2 LST)는
  **영원히 NULL** 이다. 억지로 가까운 값에 배정하면 검색·분류가 조용히 틀린다.

Revision ID: 0003_p1_topic_check
Revises: 0002_p1_file_count
"""
from __future__ import annotations

from alembic import op

revision = "0003_p1_topic_check"
down_revision = "0002_p1_file_count"
branch_labels = None
depends_on = None

TOPICS = "'강우·강수', '식생·NDVI', '지형·DEM', '토지피복·LULC'"

# 적용 전 위반 행 조회 (〈55〉「적용 전 위반 행 조회가 선행」).
#   **여기서 그냥 SELECT 하면 안 된다** — 이 표는 FORCE ROW LEVEL SECURITY 아래에 있어
#   소유자 롤(colab_owner)로 도는 마이그레이션도 정책을 받는다. 스코프가 비어 있으면
#   위반 행이 있어도 **0 건으로 보이고**, 사전 조회가 「없다」고 조용히 거짓말한다.
#   그래서 0002 가 백필에 쓴 것과 **같은 방식**으로 이 한 구간만 FORCE 를 내린다 —
#   ① 정책을 고치거나 지우지 않고 ② 어떤 롤에도 BYPASSRLS 를 주지 않으며
#   ③ 같은 트랜잭션 안에서 원상복구되고 ④ 복구 여부를 DB 에게 되물어 확인한다.
#   위반이 있으면 **여기서 멈춘다.** 값을 고치거나 버리지 않는다 — 무엇을 어디에 넣을지는
#   사람이 정할 값이지 마이그레이션이 발명할 값이 아니다.
PRECHECK = rf"""
ALTER TABLE d3_dataset_description NO FORCE ROW LEVEL SECURITY;

DO $$
DECLARE
  bad bigint;
  sample text;
BEGIN
  SELECT count(*), min(topic) INTO bad, sample
    FROM d3_dataset_description
   WHERE topic IS NOT NULL AND topic NOT IN ({TOPICS});

  IF bad > 0 THEN
    RAISE EXCEPTION '주제 4값 밖의 행이 % 건 있다 (예: %) — 사람이 먼저 정리해야 한다 (PLAN-SoT 9-55)',
      bad, sample;
  END IF;
END
$$;

ALTER TABLE d3_dataset_description FORCE ROW LEVEL SECURITY;

-- 되올렸는지 DB 에게 되묻는다. 관례가 아니라 기계가 지킨다.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class
     WHERE relname = 'd3_dataset_description'
       AND relnamespace = 'public'::regnamespace
       AND NOT relforcerowsecurity
  ) THEN
    RAISE EXCEPTION 'FORCE ROW LEVEL SECURITY 가 복구되지 않았다 — 마이그레이션을 되돌린다';
  END IF;
END
$$;
"""

# NOT VALID 를 쓰지 않는다 — 기존 행을 검증하지 않고 통과시키는 순간
# 「DB 가 강제한다」가 다시 약속으로 내려앉는다. 위반이 있으면 여기서도 크게 실패한다.
CONSTRAINT = rf"""
ALTER TABLE d3_dataset_description
  ADD CONSTRAINT d3_dataset_description_topic_check
  CHECK (topic IS NULL OR topic IN ({TOPICS}));
"""


def upgrade() -> None:
    op.execute(PRECHECK)
    op.execute(CONSTRAINT)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE d3_dataset_description "
        "DROP CONSTRAINT IF EXISTS d3_dataset_description_topic_check"
    )
