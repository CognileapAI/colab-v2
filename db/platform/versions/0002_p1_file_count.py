"""P1 — 조각 수를 메타 층으로 올린다 (d3_dataset.file_count)

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0001 이 세운 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

왜 (PLAN-SoT §9-㊼)
  `DatasetRow.fileCount` 는 계약상 required · minimum 1 인데, `count(*) FROM d3_file` 로 세면
  `body_access` RESTRICTIVE 아래에서 **잠긴 데이터셋이 0** 을 낸다 (DSA2 = 실제 1건, 앱 롤에는 0).
  RESTRICTIVE 는 PERMISSIVE 로 뚫리지 않고 FORCE RLS 아래에서는 소유자도 정책을 받는다.
  경계를 우회하는 대신 **세는 대상을 본체 테이블에서 메타 테이블로 옮긴다.**
  드러나는 것은 개수 하나뿐이고 파일의 이름·종류·본체는 그대로 잠긴다.

Revision ID: 0002_p1_file_count
Revises: 0001_p0_platform
"""
from __future__ import annotations

from alembic import op

revision = "0002_p1_file_count"
down_revision = "0001_p0_platform"
branch_labels = None
depends_on = None

COLUMN = r"""
ALTER TABLE d3_dataset
  ADD COLUMN file_count integer NOT NULL DEFAULT 0 CHECK (file_count >= 0);
"""

TRIGGERS = r"""
-- 조각 수 유지 (㊼). **다시 세지 않고 증분으로 더한다.**
--   · 다시 세면 세는 주체가 `body_access` 를 받아 잠긴 데이터셋에 0 을 써 넣는다 — 고치려던 결함을 트리거가 재현한다
--   · 문장 단위 + 전이 테이블: 전이 테이블은 RLS 로 걸러지지 않는다(실제로 영향받은 행 그대로).
--     한 문장이 조각 수백 개를 넣어도 `d3_dataset` UPDATE 는 한 번이다
--   · `UPDATE ... SET file_count = file_count + n` 은 행 잠금을 잡는다 — 동시 삽입도 어긋나지 않는다
--   · 갱신된 행 수가 기대와 다르면 **예외로 멈춘다.** 경계 정책이 UPDATE 를 0행으로 막는 순간
--     조용히 드리프트가 생기는데, 조용한 드리프트가 비정규화의 유일한 위험이다
CREATE FUNCTION sync_dataset_file_count() RETURNS trigger
  LANGUAGE plpgsql
  AS $$
  DECLARE
    ids     char(26)[];
    deltas  bigint[];
    touched bigint;
  BEGIN
    IF TG_OP = 'INSERT' THEN
      SELECT array_agg(g.dataset_id), array_agg(g.n) INTO ids, deltas
        FROM (SELECT dataset_id, count(*)::bigint AS n FROM new_files GROUP BY dataset_id) g;
    ELSIF TG_OP = 'DELETE' THEN
      SELECT array_agg(g.dataset_id), array_agg(-g.n) INTO ids, deltas
        FROM (SELECT dataset_id, count(*)::bigint AS n FROM old_files GROUP BY dataset_id) g;
    ELSE
      SELECT array_agg(g.dataset_id), array_agg(g.n) INTO ids, deltas
        FROM (
          SELECT dataset_id, sum(d)::bigint AS n
            FROM (SELECT dataset_id, 1 AS d FROM new_files
                  UNION ALL
                  SELECT dataset_id, -1 AS d FROM old_files) s
           GROUP BY dataset_id HAVING sum(d) <> 0
        ) g;
    END IF;

    IF ids IS NULL THEN
      RETURN NULL;
    END IF;

    WITH applied AS (
      UPDATE d3_dataset t
         SET file_count = t.file_count + u.n
        FROM unnest(ids, deltas) AS u(dataset_id, n)
       WHERE t.id = u.dataset_id
      RETURNING 1
    )
    SELECT count(*) INTO touched FROM applied;

    IF touched <> array_length(ids, 1) THEN
      RAISE EXCEPTION '조각 수를 유지하지 못했다 — d3_dataset % 건 중 % 건만 갱신됐다 (PLAN-SoT 9-47)',
        array_length(ids, 1), touched;
    END IF;
    RETURN NULL;
  END;
  $$;

CREATE TRIGGER d3_file_count_insert
  AFTER INSERT ON d3_file
  REFERENCING NEW TABLE AS new_files
  FOR EACH STATEMENT EXECUTE FUNCTION sync_dataset_file_count();

CREATE TRIGGER d3_file_count_delete
  AFTER DELETE ON d3_file
  REFERENCING OLD TABLE AS old_files
  FOR EACH STATEMENT EXECUTE FUNCTION sync_dataset_file_count();

-- 조각이 다른 데이터셋으로 옮겨 가는 경우. 열 목록(`UPDATE OF dataset_id`)을 붙이지 않는다 —
-- postgres 는 열 목록과 전이 테이블을 함께 못 쓴다. 옮김이 아닌 UPDATE 는 증분이 0 이라 저절로 빠진다.
CREATE TRIGGER d3_file_count_move
  AFTER UPDATE ON d3_file
  REFERENCING OLD TABLE AS old_files NEW TABLE AS new_files
  FOR EACH STATEMENT EXECUTE FUNCTION sync_dataset_file_count();
"""

# 백필. **읽을 수 없는 것을 세야 하는 자리다.**
#   마이그레이션은 소유자 롤(colab_owner)로 돈다. FORCE RLS 아래에서 소유자도 정책을 받으므로
#   여기서 그냥 `count(*) FROM d3_file` 을 하면 잠긴 데이터셋이 0 으로 백필된다 — 고치려던 결함을
#   마이그레이션이 그대로 재현한다.
#   그래서 **백필 한 구간 동안만** 두 표의 FORCE 를 내렸다가 되올린다. 이것은
#   ① 정책을 고치거나 지우지 않고 ② 어떤 롤에도 BYPASSRLS 를 주지 않으며 ③ 같은 트랜잭션 안에서
#   원상복구되고 ④ 복구 여부를 마지막에 DB 에게 되물어 확인한다. 남는 완화가 없다.
#   런타임 경로가 아니라 DDL 경로다 — 이 롤은 이미 정책을 DROP 할 수 있는 롤이다.
BACKFILL = r"""
ALTER TABLE d3_dataset NO FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_file    NO FORCE ROW LEVEL SECURITY;

UPDATE d3_dataset d
   SET file_count = (SELECT count(*) FROM d3_file f WHERE f.dataset_id = d.id);

ALTER TABLE d3_dataset FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_file    FORCE ROW LEVEL SECURITY;

-- 되올렸는지 DB 에게 되묻는다. 관례가 아니라 기계가 지킨다.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class
     WHERE relname IN ('d3_dataset', 'd3_file')
       AND relnamespace = 'public'::regnamespace
       AND NOT relforcerowsecurity
  ) THEN
    RAISE EXCEPTION 'FORCE ROW LEVEL SECURITY 가 복구되지 않았다 — 마이그레이션을 되돌린다';
  END IF;
END
$$;
"""


def upgrade() -> None:
    op.execute(COLUMN)
    op.execute(TRIGGERS)
    op.execute(BACKFILL)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS d3_file_count_move ON d3_file")
    op.execute("DROP TRIGGER IF EXISTS d3_file_count_delete ON d3_file")
    op.execute("DROP TRIGGER IF EXISTS d3_file_count_insert ON d3_file")
    op.execute("DROP FUNCTION IF EXISTS sync_dataset_file_count()")
    op.execute("ALTER TABLE d3_dataset DROP COLUMN IF EXISTS file_count")
