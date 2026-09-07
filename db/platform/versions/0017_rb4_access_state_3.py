"""R-B-1 `M-4` — 공개 범위 **3값** · 두 표 (PRD-11)

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0016 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 두 표인가 (PRD-11 축자) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`d2_access.py` 의 판정식이 `COALESCE(a.state, p.default_visibility, '열림')` 이다 —
데이터셋 상태와 연구실 기본값이 **같은 어휘 한 벌**을 쓴다. ⛔ **한쪽만 넓히면 연구실
기본값이 표현할 수 없는 상태가 생긴다.** 그래서 `d2_dataset_access.state` 와
`d1_lab_profile.default_visibility` 를 **같은 3값**으로 함께 넓힌다.

값 = `열림`(연구실 구성원 전체) · `잠김`(나만 보기 · 허용 목록이 비어 있다) ·
`지정 공개`(지정한 사람만 · `d2_dataset_access_grant`).
⛔ **「열림/잠김」 어휘를 지우지 않는다** — 결정 용어라 코드·시험·문서가 붙어 있다.
⛔ **RLS 경계를 넓히지 않는다** — 연구실 밖 열람 상태를 만들지 않는다(PRD-37 · 범위 밖).

━━ 이관 — 유효 grant 의 유무가 가른다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**자동 매핑한다. 재선택을 요구하지 않는다**(PRD-11 「기존 데이터」 축자).

    열림                    → 열림
    잠김 ∧ 유효 grant 0건   → 잠김
    잠김 ∧ 유효 grant ≥1건  → 지정 공개
    NULL                    → NULL (연구실 기본값을 그대로 따른다)

종전 2값에서는 `잠김` 인 채로 grant 를 받는 것이 **정상**이었다(P6 접근 요청 경로 ·
마이그레이션 `0010`). 3값이 되면 그 상태가 곧 `지정 공개` 라, 이관하지 않으면 새 불변식
(「`잠김` 이면 허용 목록이 비어 있다」)이 배포 첫날부터 깨진 채로 시작한다.

⚠ **`d3_file.body_access` 정책은 한 글자도 안 건드린다** — 그 정책은 `= '열림'
OR 유효 grant 존재` 라 `지정 공개` 가 **grant 갈래를 그대로 탄다**. 접근 판정이 안
바뀌는 것이 이 이관의 요점이고(PRD-11 「접근 판정 함수를 고치지 않는다」), 그래서
매핑 뒤에도 기존 허용자의 접근이 종전과 같다.

━━ RLS — 원천·대상이 **둘 다 FORCE** 다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

마이그레이터 롤은 `colab_owner`(NOSUPERUSER · NOBYPASSRLS · `infra/dev/db-bootstrap.sh`)
이고 `app.current_lab` 이 없으므로 `current_lab_id()` 가 NULL 이다. `d2_dataset_access`
(`schema.sql` RLS 절)와 `d2_dataset_access_grant` 가 **둘 다 FORCE** 라, 그대로 두면
매핑 UPDATE 가 **오류 없이 0행**으로 끝난다 — `0016` 이 advisor ② 로 배운 자리와 같다.
⟹ 매핑 구간만 두 표를 `NO FORCE` 로 내리고 곧바로 되올린다. 되올림과 매핑 건수는
DO 블록 단언들이 DB 에게 되묻는다. **단언은 NO FORCE 구간 안에 둔다** — 밖에 두면 양쪽이
다 RLS 에 막혀 `0 = 0` 으로 green 이 되고 단언이 결함을 못 잡는다.

━━ 되돌림 — **값이 하나 사라진다** ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`downgrade` 는 CHECK 를 2값으로 좁힌다. 좁히기 **전에** 두 표의 `지정 공개` 를 `잠김`
으로 되돌린다 — 안 그러면 좁히는 그 자리에서 CHECK 위반으로 크게 실패한다.
⚠ **그 되돌림이 손실이다** — 「지정한 사람만」과 「나만 보기」가 되돌린 뒤에는 구별되지
않는다. `d2_dataset_access_grant` 의 허용 줄은 **그대로 남으므로** 접근 자체는 종전과
같이 유지되고(`body_access` 의 grant 갈래), 다시 올리면 이 파일의 매핑이 유효 grant 를
근거로 `지정 공개` 를 **되살린다**. 되살아나지 않는 것은 **유효 grant 가 하나도 없는
채로 `지정 공개` 를 고른** 데이터셋뿐이고, 그 상태는 사람에게 `나만 보기` 와 같은
범위였다(PRD-11 「허용 목록 0건으로 시작해 사실상 나만 보기와 같다」).

⚠ ⭑ **32자를 넘기지 않는다** — `alembic_version_platform.version_num` 이 `varchar(32)` 다.
   `0017_rb4_access_state_3` = 22자.

Revision ID: 0017_rb4_access_state_3
Revises: 0016_rb2_dataset_variable
"""
from __future__ import annotations

from alembic import op

revision = "0017_rb4_access_state_3"
down_revision = "0016_rb2_dataset_variable"
branch_labels = None
depends_on = None


#: 제약 이름은 열 CHECK 의 postgres 기본 이름과 같게 둔다 (`schema.sql` 이 인라인 CHECK 다 ·
#: `0015` 와 같은 규율). 이름이 어긋나면 schema-diff 가 red 를 낸다.
UPGRADE = r"""
-- ⑴ 두 표의 CHECK 를 **같은 3값**으로 넓힌다. 순서가 규칙이다 — 값을 쓰기 전에 넓힌다.
ALTER TABLE d2_dataset_access DROP CONSTRAINT IF EXISTS d2_dataset_access_state_check;
ALTER TABLE d2_dataset_access
  ADD CONSTRAINT d2_dataset_access_state_check
  CHECK (state IN ('열림', '잠김', '지정 공개'));

ALTER TABLE d1_lab_profile DROP CONSTRAINT IF EXISTS d1_lab_profile_default_visibility_check;
ALTER TABLE d1_lab_profile
  ADD CONSTRAINT d1_lab_profile_default_visibility_check
  CHECK (default_visibility IN ('열림', '잠김', '지정 공개'));

-- ⑵ 이관. **유효 grant 의 유무가 가른다.**
--
-- ⚠ **이 구간만 FORCE 를 내린다**(모듈 산문 「RLS」). 원천(`d2_dataset_access_grant`)과
--   대상(`d2_dataset_access`)이 둘 다 FORCE 이고 마이그레이터 롤은 NOBYPASSRLS 라,
--   그대로 두면 UPDATE 가 **오류 없이 0행**으로 끝난다.
ALTER TABLE d2_dataset_access       NO FORCE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access_grant NO FORCE ROW LEVEL SECURITY;

-- 이관이 실제로 한 일을 DB 에게 되묻는다. **「돌았다」가 아니라 「맞다」를 센다.**
DO $$
DECLARE want bigint; moved bigint; stuck bigint;
BEGIN
  SELECT count(*) INTO want
    FROM d2_dataset_access a
   WHERE a.state = '잠김'
     AND EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                  WHERE g.dataset_id = a.dataset_id AND g.expires_at > now());

  UPDATE d2_dataset_access a
     SET state = '지정 공개', updated_at = now()
   WHERE a.state = '잠김'
     AND EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                  WHERE g.dataset_id = a.dataset_id AND g.expires_at > now());
  GET DIAGNOSTICS moved = ROW_COUNT;

  IF moved <> want THEN
    RAISE EXCEPTION '공개 범위 이관이 % 행이다 (기대 % = 잠김 ∧ 유효 grant ≥1) — 이관이 전수를 못 덮었다 (M-4)',
      moved, want;
  END IF;

  -- **불변식이 이 자리에서 처음 선다** — 「`잠김` 이면 허용 목록이 비어 있다」.
  SELECT count(*) INTO stuck
    FROM d2_dataset_access a
   WHERE a.state = '잠김'
     AND EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                  WHERE g.dataset_id = a.dataset_id AND g.expires_at > now());
  IF stuck <> 0 THEN
    RAISE EXCEPTION '이관 뒤에도 잠김 ∧ 유효 grant ≥1 인 행이 % 건이다 — 불변식이 배포 첫날부터 깨진다 (M-4)',
      stuck;
  END IF;
END
$$;

-- FORCE 를 되올리고, 되올렸는지 DB 에게 되묻는다.
ALTER TABLE d2_dataset_access       FORCE ROW LEVEL SECURITY;
ALTER TABLE d2_dataset_access_grant FORCE ROW LEVEL SECURITY;

DO $$
DECLARE loose text;
BEGIN
  SELECT string_agg(relname, ', ') INTO loose
    FROM pg_class
   WHERE relnamespace = 'public'::regnamespace
     AND relname IN ('d2_dataset_access', 'd2_dataset_access_grant')
     AND NOT relforcerowsecurity;
  IF loose IS NOT NULL THEN
    RAISE EXCEPTION 'FORCE ROW LEVEL SECURITY 가 복구되지 않았다 (%) — 마이그레이션을 되돌린다', loose;
  END IF;
END
$$;
"""

DOWNGRADE = r"""
-- ⑴ **좁히기 전에 값을 되돌린다.** 남겨 두면 CHECK 를 좁히는 자리에서 크게 실패한다.
--    ⚠ 이것이 되돌림의 손실이다 — 「지정한 사람만」이 「나만 보기」와 구별되지 않는다
--      (모듈 산문 「되돌림」). 허용 줄(`d2_dataset_access_grant`)은 **그대로 남는다.**
ALTER TABLE d2_dataset_access NO FORCE ROW LEVEL SECURITY;
UPDATE d2_dataset_access SET state = '잠김', updated_at = now() WHERE state = '지정 공개';
ALTER TABLE d2_dataset_access FORCE ROW LEVEL SECURITY;

ALTER TABLE d1_lab_profile NO FORCE ROW LEVEL SECURITY;
UPDATE d1_lab_profile SET default_visibility = '잠김' WHERE default_visibility = '지정 공개';
ALTER TABLE d1_lab_profile FORCE ROW LEVEL SECURITY;

-- ⭑ **⟨advisor ② · Missed⟩ 되올렸는지 DB 에게 되묻는다 — upgrade 와 같은 단언이다.**
--   되돌림 창도 두 표의 FORCE 를 내렸다 왔다. 단언이 upgrade 에만 있으면 downgrade 로
--   내려간 DB 는 RLS 가 풀린 채로 남고, 그 사실을 아무 검사도 잡지 않는다.
DO $$
DECLARE loose text;
BEGIN
  SELECT string_agg(relname, ', ') INTO loose
    FROM pg_class
   WHERE relnamespace = 'public'::regnamespace
     AND relname IN ('d2_dataset_access', 'd1_lab_profile')
     AND NOT relforcerowsecurity;
  IF loose IS NOT NULL THEN
    RAISE EXCEPTION 'FORCE ROW LEVEL SECURITY 가 복구되지 않았다 (%) — 되돌림을 되돌린다', loose;
  END IF;
END
$$;

-- ⑵ 2값으로 좁힌다.
ALTER TABLE d2_dataset_access DROP CONSTRAINT IF EXISTS d2_dataset_access_state_check;
ALTER TABLE d2_dataset_access
  ADD CONSTRAINT d2_dataset_access_state_check
  CHECK (state IN ('열림', '잠김'));

ALTER TABLE d1_lab_profile DROP CONSTRAINT IF EXISTS d1_lab_profile_default_visibility_check;
ALTER TABLE d1_lab_profile
  ADD CONSTRAINT d1_lab_profile_default_visibility_check
  CHECK (default_visibility IN ('열림', '잠김'));
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """3값을 2값으로 좁힌다.

    ⚠ **`지정 공개` 를 `잠김` 으로 되돌린다 — 그 구별은 사라진다**(모듈 산문 「되돌림」).
    허용 줄은 남으므로 접근 자체는 유지되고, 다시 올리면 매핑이 유효 grant 를 근거로
    `지정 공개` 를 되살린다. 되살아나지 않는 것은 **유효 grant 0건인 `지정 공개`** 뿐이다.
    """
    op.execute(DOWNGRADE)
