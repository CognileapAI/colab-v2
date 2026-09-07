"""R-C `WU-C7` — 프로젝트 이름 **DB 제약** `UNIQUE (lab_id, name)` (PRD-42 · 질의 R-A′ 이월)

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0019 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 지금 DB 로 내려가는가 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`WU-A7R` 이 응용 층 400 을 세웠다(`routes/project.py` `DUPLICATE_NAME_MESSAGE`).
그 자리가 **유일한 방어선**이라, 그 함수를 안 타는 경로(직접 SQL · 다음 회차가 세울
다른 생성 경로 · 두 요청의 경합)에서는 같은 이름이 그대로 들어간다. 응용 400 은
**문면을 주는 앞문**이고 이 제약은 **뒷문**이다 — 둘 다 있어야 「겹치지 않는다」가 사실이다.

⚠ 판정 축은 **연구실 안**이다. 유형(`type`)이 달라도 겹침이다(PRD-42 수용 기준 2행) —
   그래서 제약은 `(lab_id, name)` 이고 `type` 을 열쇠에 넣지 않는다.

━━ 기존 중복 행 — **멈춘다. 지우지 않는다** ━━━━━━━━━━━━━━━━━━━━━━━━━

라운드 ㉴ 가 「사람 입력값 자동 변경 0 · 중복 이름 자동 개명 금지」다(spec 우려 6).
그래서 이 마이그레이션은 겹치는 행을 만나면 **건수를 적어 실패**한다 — 사람이 화면에서
이름을 고친 뒤 다시 돌린다. 자동으로 `(2)` 를 붙이면 그 순간 사용자가 짓지 않은 이름이
DB 에 남고, 되돌릴 근거가 사라진다.

━━ RLS — 사전 점검만 `NO FORCE` 다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

마이그레이터 롤은 `colab_owner`(NOSUPERUSER · NOBYPASSRLS)이고 `app.current_lab` 이
없어 `current_lab_id()` 가 NULL 이다. `d6_project` 가 FORCE 라 그대로 두면 사전 점검이
**0행을 세고 조용히 통과**한다(`0016`·`0017`·`0019` 가 같은 자리에서 배운 것).
⟹ 세는 구간만 `NO FORCE` 로 내리고 곧바로 되올린다. **단언은 그 구간 안에 둔다.**
⚠ `ALTER TABLE … ADD CONSTRAINT` 자체는 DDL 이라 RLS 를 안 탄다 — 중복이 남아 있으면
   그 자리에서도 실패한다. 사전 점검은 **건수를 사람에게 보여 주려고** 있다.

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

제약 DROP 뿐이다. 행을 건드리지 않으므로 **값 소실 0** 이다.

⚠ ⭑ **32자를 넘기지 않는다** — `alembic_version_platform.version_num` 이 `varchar(32)` 다.
   `0020_rc7_project_name_unique` = 28자.

Revision ID: 0020_rc7_project_name_unique
Revises: 0019_rb7_search_index_m10
"""
from __future__ import annotations

from alembic import op

revision = "0020_rc7_project_name_unique"
down_revision = "0019_rb7_search_index_m10"
branch_labels = None
depends_on = None


#: 제약 이름은 선언(`schema.sql`)과 **한 글자도 다르지 않아야** schema-diff 가 green 이다.
UPGRADE = r"""
-- ⑴ 사전 점검 — **겹치는 행이 있으면 건수를 적고 멈춘다.** 지우지도 고치지도 않는다.
--    RC7 DUPCHECK BEGIN
ALTER TABLE d6_project NO FORCE ROW LEVEL SECURITY;
DO $$
DECLARE pairs bigint; rows_ bigint;
BEGIN
  SELECT count(*), coalesce(sum(n), 0) INTO pairs, rows_
    FROM (SELECT count(*) AS n FROM d6_project
           GROUP BY lab_id, name HAVING count(*) > 1) AS dup;
  RAISE NOTICE '[0020] 프로젝트 이름 중복 점검 — 겹치는 (연구실, 이름) 짝 % · 관련 행 %', pairs, rows_;
  IF pairs > 0 THEN
    RAISE EXCEPTION '0020 중단 — 같은 연구실 안에서 이름이 겹치는 (연구실, 이름) 짝이 %건(행 %건) 있다. '
                    '자동으로 지우거나 개명하지 않는다(라운드 ㉴). 화면에서 이름을 고친 뒤 다시 돌린다.',
                    pairs, rows_;
  END IF;
END $$;
ALTER TABLE d6_project FORCE ROW LEVEL SECURITY;
--    RC7 DUPCHECK END

-- ⑵ 뒷문. 응용 400 과 **같은 판정 축**(연구실 안 · 유형 무관)이다.
ALTER TABLE d6_project
  ADD CONSTRAINT d6_project_lab_name_unique UNIQUE (lab_id, name);
"""

DOWNGRADE = r"""
ALTER TABLE d6_project DROP CONSTRAINT d6_project_lab_name_unique;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
