"""계보 출처 레이블을 영어 세 값으로 — ai · manual · processed

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0007 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 무엇을 바꾸나 (PLAN-SoT §9 〈198〉·〈205〉 · 10 차 동결 해제) ━━━━━━━━━━━━

`d4_lineage_edge.origin` 의 값 집합을 두 한국어 값에서 **영어 세 값**으로 바꾼다.

    'AI 제안을 사람이 확인'  →  'ai'
    '사람이 직접 연결'       →  'manual'
    (신설)                   →  'processed'   -- 가공으로 자동 생성

━━ ⚠ `ai` 의 뜻 — 「AI 가 만든 것」이 아니다 ━━━━━━━━━━━━━━━━━━━━━━━━━━

`ai` 는 **AI 가 제안하고 사람이 확인한 것**이다. 이 레포의 불변 규칙은 그대로다 —
**AI 는 계보를 쓰지 않는다**(`CLAUDE.md §3-2`). 게이트 `ai-no-lineage-write` 가
계약·코드·체인 세 층에서 그것을 강제하고, 이 개명은 그 셋을 하나도 건드리지 않는다.
레이블이 짧아 뜻을 다 담지 못하므로 값의 뜻은 계약 산문
(`contracts/schemas/common.json#/$defs/LineageOrigin` 의 `description`)과 위 CHECK
주석이 함께 못 박는다.

━━ ⚠ `processed` 를 만드는 경로는 이 회차에 만들지 않았다 ━━━━━━━━━━━━━━━

값만 열어 두었다. 만드는 주체(데이터 프로세스 `DP-1`)가 `after_stage2` 다.
**쓰는 쪽을 만들지 않은 것은 누락이 아니라 결정이다** — 값이 없으면 그 기능을 세울 때
다시 마이그레이션을 해야 하고, 그건 이번 회차가 여는 것과 같은 문이다.

━━ ⚠ 되돌릴 수 없다 — 전진 전용이다 (〈168〉-㉲) ━━━━━━━━━━━━━━━━━━━━━━━

**`downgrade` 는 없다.** `RAISE EXCEPTION` 으로 막는다. 이유 둘 —

  ⑴ **값 이행이 비가역이다.** 되돌리려면 'ai'→한국어 · 'manual'→한국어 로 되짚어야
     하는데, 되돌린 시점에 새로 들어온 `'processed'` 행은 **되짚을 옛 값이 없다.**
     옛 집합에 대응물이 없는 값을 임의로 골라 넣는 것은 마이그레이션이 발명하는 값이다.
  ⑵ 되돌림이 필요할 만큼 형태가 갈리는 변경이 아니다. 복구가 필요하면 **앞으로 가는
     새 리비전**을 쓴다.

━━ 이행 대상 (착수 시점 실측) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

staging `d4_lineage_edge` = **6 행, 전부 `사람이 직접 연결`**(2026-08-29 읽기 전용 조회).
⚠ 이 수는 **적용 시점에 다를 수 있다.** 그래서 아래는 건수를 조건으로 삼지 않고
**값으로 갈라 전량을 옮긴다.** 옮긴 뒤 옛 값 잔존 0 을 DB 에게 되묻는다.

⚠ 이 표는 FORCE ROW LEVEL SECURITY 아래에 있어 소유자 롤로 도는 마이그레이션도
정책을 받는다. 스코프가 비어 있으면 `UPDATE` 가 **0 행을 고치고 성공한다** — 그러면
그 다음 `ALTER … ADD CONSTRAINT` 가 옛 값 위에서 실패하거나, 더 나쁘게는 잔존 확인이
「없다」고 조용히 거짓말한다. `0002`·`0003`·`0004` 와 **같은 방식**으로 이 한 구간만
FORCE 를 내린다 — ① 정책을 고치거나 지우지 않고 ② 어떤 롤에도 BYPASSRLS 를 주지
않으며 ③ 같은 트랜잭션 안에서 원상복구되고 ④ 복구 여부를 DB 에게 되묻는다.

Revision ID: 0008_lineage_origin_labels
Revises: 0007_p2_human_written_meta
"""
from __future__ import annotations

from alembic import op

revision = "0008_lineage_origin_labels"
down_revision = "0007_p2_human_written_meta"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- ⑴ 옛 CHECK 를 먼저 뗀다. 떼지 않으면 아래 UPDATE 가 새 값에서 걸린다.
--    이름은 0001 이 인라인 무명 CHECK 로 만든 것이라 postgres 가 붙인 규칙명이다.
ALTER TABLE d4_lineage_edge DROP CONSTRAINT d4_lineage_edge_origin_check;

-- ⑵ 값 이행. **이 한 구간만 FORCE 를 내린다** (위 산문 참조).
ALTER TABLE d4_lineage_edge NO FORCE ROW LEVEL SECURITY;

UPDATE d4_lineage_edge SET origin = 'ai'     WHERE origin = 'AI 제안을 사람이 확인';
UPDATE d4_lineage_edge SET origin = 'manual' WHERE origin = '사람이 직접 연결';

-- 잔존을 DB 에게 되묻는다. 관례가 아니라 기계가 지킨다.
DO $$
DECLARE
  leftover bigint;
  sample text;
BEGIN
  SELECT count(*), min(origin) INTO leftover, sample
    FROM d4_lineage_edge
   WHERE origin NOT IN ('ai', 'manual', 'processed');

  IF leftover > 0 THEN
    RAISE EXCEPTION '세 값 밖의 출처가 % 건 남았다 (예: %) — 값 이행이 전량을 못 옮겼다 (PLAN-SoT 9-205)',
      leftover, sample;
  END IF;
END
$$;

ALTER TABLE d4_lineage_edge FORCE ROW LEVEL SECURITY;

-- 되올렸는지 DB 에게 되묻는다.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class
     WHERE relname = 'd4_lineage_edge'
       AND relnamespace = 'public'::regnamespace
       AND NOT relforcerowsecurity
  ) THEN
    RAISE EXCEPTION 'FORCE ROW LEVEL SECURITY 가 복구되지 않았다 — 마이그레이션을 되돌린다';
  END IF;
END
$$;

-- ⑶ 새 CHECK. NOT VALID 를 쓰지 않는다 — 기존 행을 검증하지 않고 통과시키는 순간
--    「DB 가 강제한다」가 다시 약속으로 내려앉는다.
--    이름은 선언 정본(schema.sql)의 인라인 무명 CHECK 가 얻을 이름과 같아야 한다.
ALTER TABLE d4_lineage_edge
  ADD CONSTRAINT d4_lineage_edge_origin_check
  CHECK (origin IN ('ai', 'manual', 'processed'));
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """⚠ **전진 전용이다 — 되돌릴 수 없다** (`〈168〉-㉲`).

    `'processed'` 로 들어온 행에는 되짚을 옛 값이 없다. 되돌림을 흉내 내면
    마이그레이션이 값을 발명하게 된다. 복구가 필요하면 **앞으로 가는 새 리비전**을 쓴다.
    """
    raise RuntimeError(
        "0008_lineage_origin_labels 는 전진 전용이다 — 되돌리지 않는다. "
        "'processed' 로 들어온 행에 대응하는 옛 값이 없다 (PLAN-SoT §9 〈205〉)."
    )
