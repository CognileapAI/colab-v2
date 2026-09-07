"""R-C `WU-C7` — `0017` 이관 **빈틈 보정** (PRD-11 · R-B 판정 20)

선언 정본은 db/platform/schema.sql 이다. **이 파일은 스키마를 한 글자도 안 바꾼다** —
데이터 마이그레이션이다. 그래서 schema-diff 의 대조 대상이 0 이다.

━━ 무엇이 빈틈이었나 (`0017:23-25` 축자) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`0017` 의 이관표 마지막 줄이 `NULL → NULL` 이다 — 「상태를 따로 안 정했으면 연구실
기본값을 그대로 따른다」. 옳은 줄이지만 **연구실 기본값이 `잠김` 인 경우**를 안 갈랐다:

    d2_dataset_access.state IS NULL  ∧  d1_lab_profile.default_visibility = '잠김'
                                     ∧  유효 grant ≥ 1

이 행의 **실효 상태는 `잠김` 인데 허용자가 있다.** `0017` 이 세운 새 불변식(「`잠김` 이면
허용 목록이 비어 있다」)이 상태 행을 명시적으로 쓴 데이터셋에서만 성립하고, 기본값을
따르는 데이터셋에서는 배포 첫날부터 깨져 있었다 — 그 자리를 여기서 닫는다.
`0017` 이 명시 행에 한 것과 **같은 규칙**을 기본값 경로에 한 번 더 적용할 뿐이다.

⚠ **행이 아예 없는 데이터셋은 대상이 아니다.** 판정 20 축자가 「**상태 행 NULL**」이고,
   `0017` 이 이관한 자리도 그것이다. 없는 행을 지어내면 「NULL 과 명시값」의 구별이
   이 마이그레이션 자리에서 무너진다(`test_access_state_three` ㈎ 가 지키는 사실).

⛔ **실물 건수는 배포 창 실측이 적는다**(판정 20 축자). 레인은 픽스처로 짓고, 이 파일은
   **옮긴 행 수를 NOTICE 로 찍는다**. 0 이어도 체인에 남긴다 — 체인은 사실의 기록이다.

━━ RLS — 원천·대상이 셋 다 FORCE 다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`d2_dataset_access`·`d2_dataset_access_grant`·`d1_lab_profile` 이 모두 FORCE 이고
마이그레이터 롤은 NOBYPASSRLS 다. 그대로 두면 UPDATE 가 **오류 없이 0행**으로 끝난다
(`0017`·`0019` 가 배운 자리). ⟹ 세 표를 구간 안에서만 `NO FORCE` 로 내리고 되올린다.
**단언·계수는 그 구간 안에 둔다** — 밖에 두면 `0 = 0` 으로 green 이 된다.

━━ 되돌림 — **옮긴 행만 NULL 로 되돌린다** ━━━━━━━━━━━━━━━━━━━━━━━━━━━

옮긴 행의 목록을 따로 적는 표를 만들지 않았다(표 하나가 늘면 RLS·선언·게이트가 함께
늘고, 그 값은 배포 창 한 번을 위해 영구히 남는다). 대신 **올릴 때와 똑같은 삼중 조건**
(`지정 공개` ∧ 연구실 기본 `잠김` ∧ 유효 grant ≥1)으로 되돌린다.

⚠ 되돌아가는 값은 `잠김` 이 아니라 **NULL** 이다 — 이 행들의 연구실 기본값이 `잠김` 이라
   NULL 이 곧 `잠김` 이고(spec 「`지정 공개`→`잠김` 역이관」의 이 자리에서의 실체),
   `0017` 이 남긴 원래 값이 정확히 NULL 이었다. **값 소실 0** 이다.
⚠ 이 조건은 「올리기 전부터 `지정 공개` 였고 마침 기본값이 `잠김` 이며 허용자가 있는」
   행도 함께 집는다. 그런 행의 되돌린 실효 상태는 `잠김` 이고, 그것은 `0017` 의
   downgrade 가 `지정 공개` 전건에 하는 일과 **같은 등급의 손실**이다(판정 12 계열).
   이 조건보다 좁은 대조 근거는 DB 안에 없다.

⚠ ⭑ **32자를 넘기지 않는다** — `0021_rc7_access_state_gap` = 25자.

Revision ID: 0021_rc7_access_state_gap
Revises: 0020_rc7_project_name_unique
"""
from __future__ import annotations

from alembic import op

revision = "0021_rc7_access_state_gap"
down_revision = "0020_rc7_project_name_unique"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- RC7 GAP BEGIN
ALTER TABLE d2_dataset_access       NO FORCE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access_grant NO FORCE ROW LEVEL SECURITY;
ALTER TABLE d1_lab_profile          NO FORCE ROW LEVEL SECURITY;

DO $$
DECLARE moved bigint; broken bigint;
BEGIN
  UPDATE d2_dataset_access a
     SET state = '지정 공개', updated_at = now()
   WHERE a.state IS NULL
     AND EXISTS (SELECT 1 FROM d1_lab_profile p
                  WHERE p.lab_id = a.lab_id AND p.default_visibility = '잠김')
     AND EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                  WHERE g.dataset_id = a.dataset_id AND g.expires_at > now());
  GET DIAGNOSTICS moved = ROW_COUNT;
  -- **이동 행 수는 출력에 보인다** — 판정 20 「배포 전 실측」이 읽는 한 줄이다.
  RAISE NOTICE '[0021] 이관 빈틈 보정 — NULL ∧ 연구실 기본 잠김 ∧ 유효 grant ≥1 → 지정 공개 : %행 이동', moved;

  -- 불변식 재확인 — 「`잠김` ∧ 유효 grant ≥1」은 **어느 시점에도 0건**이다(R-B 경계 증명).
  SELECT count(*) INTO broken FROM d2_dataset_access a
   WHERE a.state = '잠김'
     AND EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                  WHERE g.dataset_id = a.dataset_id AND g.expires_at > now());
  IF broken > 0 THEN
    RAISE EXCEPTION '0021 중단 — state=''잠김'' 이면서 유효 grant 가 있는 행이 %건 있다 (불변식 위반).', broken;
  END IF;
END $$;

ALTER TABLE d1_lab_profile          FORCE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access_grant FORCE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access       FORCE ROW LEVEL SECURITY;
-- RC7 GAP END
"""

DOWNGRADE = r"""
ALTER TABLE d2_dataset_access       NO FORCE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access_grant NO FORCE ROW LEVEL SECURITY;
ALTER TABLE d1_lab_profile          NO FORCE ROW LEVEL SECURITY;

DO $$
DECLARE back bigint;
BEGIN
  UPDATE d2_dataset_access a
     SET state = NULL, updated_at = now()
   WHERE a.state = '지정 공개'
     AND EXISTS (SELECT 1 FROM d1_lab_profile p
                  WHERE p.lab_id = a.lab_id AND p.default_visibility = '잠김')
     AND EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                  WHERE g.dataset_id = a.dataset_id AND g.expires_at > now());
  GET DIAGNOSTICS back = ROW_COUNT;
  RAISE NOTICE '[0021] 되돌림 — 지정 공개 → NULL(연구실 기본 잠김) : %행', back;
END $$;

ALTER TABLE d1_lab_profile          FORCE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access_grant FORCE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access       FORCE ROW LEVEL SECURITY;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    op.execute(DOWNGRADE)
