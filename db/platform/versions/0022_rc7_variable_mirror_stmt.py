"""R-C `WU-C7` — 변수명 미러 트리거를 **문장 단위**로 (질의 36 · PRD-16)

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0021 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 무엇이 N+1 이었나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`0019` 가 세운 `d3_dataset_variable_mirror` 가 `FOR EACH ROW` 였다. `replace_variables`
(`domains/d3_catalog.py`)는 변수 N 개를 넣으므로 **미러 전체를 다시 만드는 UPDATE 가 N 번**
돌았다 — 그때마다 `array_agg` 가 그 데이터셋의 변수 행을 전수 훑고, 생성 컬럼
`search_vector` 와 GIN 색인이 **N 번 다시 계산**된다. 마지막 한 번을 뺀 N-1 번은 곧바로
덮여 사라지는 계산이다.

⚠ 트리거만 문장 단위로 바꿔서는 1회가 되지 않는다 — 쓰기 쪽이 INSERT 문을 N 번 보내면
   문장 단위 트리거도 N 번 뛴다. 그래서 **같은 회차에서 `replace_variables` 가 다중 행
   INSERT 한 문장을 보내도록** 함께 고쳤다. 두 쪽이 짝이다.

━━ 왜 트리거가 셋이 되는가 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

문장 단위 트리거가 「어느 행이 바뀌었는가」를 알려면 **전이 표**(`REFERENCING … TABLE`)가
필요하고, PostgreSQL 은 **전이 표를 가진 트리거를 한 이벤트에만** 허용한다
(`INSERT OR UPDATE OR DELETE` 한 줄로 못 쓴다). 그래서 이벤트마다 한 줄씩 셋이다 —
**함수는 하나**이고 `TG_OP` 로 갈린다. 함수를 셋으로 쪼개면 집계식이 세 곳이 되고,
한 곳만 고쳐지는 날 미러가 조용히 낡는다(`0019` 산문이 ㈎ 를 버린 이유와 같다).

⚠ 전이 표 이름은 분기 안에서만 참조된다 — `INSERT` 로 뛴 호출은 `oldtab` 을 적은 문장을
   **실행하지 않는다**(PL/pgSQL 이 분기별로 늦게 준비한다). 이름이 없는 자리를 참조하면
   그 자리에서 오류이므로 분기를 느슨하게 두지 않는다.

━━ 무엇을 안 바꾸나 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⛔ **집계식·정본 방향이 그대로다** — 행 표가 정본이고 `variables` 배열이 사본이다
   (PRD-16 축자 「트리거만 쓴다」). 데이터셋을 옮기는 UPDATE 도 종전처럼 양쪽을 갱신한다
   (`UPDATE` 분기가 `oldtab ∪ newtab` 을 본다 — `0019` 의 `OLD.dataset_id <> NEW.dataset_id`
   가지가 여기서 집합 연산이 됐을 뿐이다).
⛔ `d3_mirror_category`·`d3_pull_mirrors` 는 손대지 않는다. 그 둘은 한 행씩 오는 경로다.
⛔ 열 삭제 0 · drop 0(트리거 재정의는 같은 이름 규칙의 재선언이다).

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`0019` 의 행 단위 트리거와 함수 본문을 **그대로** 되세운다. 값 소실 0 (미러는 파생값이고,
되돌린 직후에도 같은 집계식이 같은 값을 낸다).

⚠ ⭑ **32자를 넘기지 않는다** — `0022_rc7_variable_mirror_stmt` = 30자.

Revision ID: 0022_rc7_variable_mirror_stmt
Revises: 0021_rc7_access_state_gap
"""
from __future__ import annotations

from alembic import op

revision = "0022_rc7_variable_mirror_stmt"
down_revision = "0021_rc7_access_state_gap"
branch_labels = None
depends_on = None


UPGRADE = r"""
DROP TRIGGER d3_dataset_variable_mirror ON d3_dataset_variable;

CREATE OR REPLACE FUNCTION d3_mirror_variables() RETURNS trigger
  LANGUAGE plpgsql AS $$
BEGIN
  -- 전이 표는 **분기 안에서만** 참조한다. 없는 이름을 적은 문장은 그 자리에서 오류다.
  IF TG_OP = 'INSERT' THEN
    UPDATE d3_dataset_autometa a
       SET variables = coalesce(
             (SELECT array_agg(v.name ORDER BY v.ordinal)
                FROM d3_dataset_variable v WHERE v.dataset_id = a.dataset_id), '{}'::text[])
     WHERE a.dataset_id IN (SELECT DISTINCT n.dataset_id FROM newtab n);
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE d3_dataset_autometa a
       SET variables = coalesce(
             (SELECT array_agg(v.name ORDER BY v.ordinal)
                FROM d3_dataset_variable v WHERE v.dataset_id = a.dataset_id), '{}'::text[])
     WHERE a.dataset_id IN (SELECT DISTINCT o.dataset_id FROM oldtab o);
  ELSE
    -- 행이 데이터셋을 옮겨 가는 경로를 덮는다 — 옛 자리와 새 자리를 **둘 다** 다시 센다.
    UPDATE d3_dataset_autometa a
       SET variables = coalesce(
             (SELECT array_agg(v.name ORDER BY v.ordinal)
                FROM d3_dataset_variable v WHERE v.dataset_id = a.dataset_id), '{}'::text[])
     WHERE a.dataset_id IN (SELECT o.dataset_id FROM oldtab o
                            UNION SELECT n.dataset_id FROM newtab n);
  END IF;
  RETURN NULL;
END $$;

CREATE TRIGGER d3_dataset_variable_mirror_ins
  AFTER INSERT ON d3_dataset_variable
  REFERENCING NEW TABLE AS newtab
  FOR EACH STATEMENT EXECUTE FUNCTION d3_mirror_variables();

CREATE TRIGGER d3_dataset_variable_mirror_upd
  AFTER UPDATE ON d3_dataset_variable
  REFERENCING OLD TABLE AS oldtab NEW TABLE AS newtab
  FOR EACH STATEMENT EXECUTE FUNCTION d3_mirror_variables();

CREATE TRIGGER d3_dataset_variable_mirror_del
  AFTER DELETE ON d3_dataset_variable
  REFERENCING OLD TABLE AS oldtab
  FOR EACH STATEMENT EXECUTE FUNCTION d3_mirror_variables();
"""

DOWNGRADE = r"""
DROP TRIGGER d3_dataset_variable_mirror_del ON d3_dataset_variable;
DROP TRIGGER d3_dataset_variable_mirror_upd ON d3_dataset_variable;
DROP TRIGGER d3_dataset_variable_mirror_ins ON d3_dataset_variable;

CREATE OR REPLACE FUNCTION d3_mirror_variables() RETURNS trigger
  LANGUAGE plpgsql AS $$
DECLARE target ulid;
BEGIN
  IF TG_OP = 'DELETE' THEN target := OLD.dataset_id; ELSE target := NEW.dataset_id; END IF;
  UPDATE d3_dataset_autometa a
     SET variables = coalesce(
           (SELECT array_agg(v.name ORDER BY v.ordinal)
              FROM d3_dataset_variable v WHERE v.dataset_id = target), '{}'::text[])
   WHERE a.dataset_id = target;
  IF TG_OP = 'UPDATE' AND OLD.dataset_id <> NEW.dataset_id THEN
    UPDATE d3_dataset_autometa a
       SET variables = coalesce(
             (SELECT array_agg(v.name ORDER BY v.ordinal)
                FROM d3_dataset_variable v WHERE v.dataset_id = OLD.dataset_id), '{}'::text[])
     WHERE a.dataset_id = OLD.dataset_id;
  END IF;
  RETURN NULL;
END $$;

CREATE TRIGGER d3_dataset_variable_mirror
  AFTER INSERT OR UPDATE OR DELETE ON d3_dataset_variable
  FOR EACH ROW EXECUTE FUNCTION d3_mirror_variables();
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
