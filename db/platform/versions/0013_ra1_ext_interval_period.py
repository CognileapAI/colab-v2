"""R-A-1 — 확장자 표기 · 관측 간격 · 기간 최소 단위를 **한 head 에** 담는다

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0011 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 한 파일인가 (`R-A-1-db.md` 「마이그레이션 — 한 head」) ━━━━━━━━━━━━━━━

`M-9`(WU-A5 확장자) · `M-6`·`M-7`(WU-A6 관측 간격·기간 최소 단위)는 **같은 회차**의
같은 표를 만진다. 회차마다 파일을 쪼개면 head 가 갈라지고, 갈라진 head 는 배포 순서를
사람이 기억해야 하는 사실로 만든다. `migration-single-head` 게이트가 그것을 잰다.
⚠ **이 리비전은 지금 `M-9` 만 담고 있다.** `M-6`·`M-7` 은 레인 `p3-interval-period`
   가 **이 파일에 이어 적는다** — 새 리비전을 만들지 않는다.
⛔ **`M-10`(색인 재정의)은 여기 없다.** `category` 이관·변수명 미러와 한 마이그레이션으로
   묶여 R-B 에서 한 번만 돈다 — 생성 컬럼 재계산 ＋ GIN 재생성을 두 번 하지 않는다.

━━ `M-9` · 왜 확장자를 따로 저장하는가 (PRD-21 · `P-10`·`R-09`) ━━━━━━━━━━━━

「`.hdf` 하나가 서로 호환되지 않는 두 포맷을 가리킨다. 매직 넘버를 읽지 않는 한 단정할
수 없다.」 그런데 화면이 보이던 값(`format`)은 **파이프라인의 판별 결과 문자열**이었다 —
화면이 `HDF5` 라 적으면 그 자리에서 거짓말이 된다. 그래서 **화면이 쓸 값**을 따로 세운다.

`format` 은 **남긴다.** 판별 결과는 파이프라인·미리보기가 계속 쓰고, 확장자가 없는 행의
퇴행 표시이기도 하다. 그리고 `search_vector` 가 아직 `format` 을 B 가중치로 물고 있다 —
검색은 이번 회차에도 종전대로 `format` 으로 잡힌다(`netcdf` 는 되고 `nc` 는 아직 아니다).

**데이터셋당 1값**이다(`P-5`). 한 데이터셋의 조각은 확장자가 한 종류라는 규칙을 등록
전환이 이미 400 으로 강제한다(PRD-32 · `tests/test_ext_mixed.py`).

━━ ⚠ 적재된 데이터 위에서 도는 백필이다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⭑ **2026-09-05 기준 staging `d3_dataset` 13행.** 값은 파일명에서 나온다 —
**마지막 `.` 뒤를 소문자화**하고, 점이 없거나 점 앞이 비면(`.bashrc` 류) **NULL** 이다.
NULL 은 「모른다」이고 화면은 그 자리에서 `format` 을 그대로 보인다(퇴행 표시).

**조각(`본체`)만 본다.** 기준 격자 파일은 확장자가 달라도 정상이라(`test_ext_mixed`),
그것을 세면 데이터셋의 확장자가 격자 파일 쪽으로 뒤집힌다.

`0002`·`0003`·`0004`·`0008` 과 같은 이유로 백필 구간만 `NO FORCE RLS` 다 — 소유자 롤로
도는 마이그레이션도 FORCE 아래에서는 정책을 받아 **두 연구실을 한 번에 못 고친다.**
구간이 끝나면 되올리고, 되올렸는지 **DB 에게 되묻는다**(관례가 아니라 기계가 지킨다).

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`downgrade` 는 열을 지운다. **잃는 값이 없다** — 이 열의 값은 전량 `d3_file.file_name`
에서 파생된 것이라 upgrade 를 다시 돌리면 같은 값이 그대로 복원된다. 사람이 손으로 적는
칸이 아니기 때문에 `0007` 류의 「되돌리면 사람의 선택이 안 돌아온다」가 여기엔 없다.

⭑ **열을 지우지 않고 되돌리는 길** (`R-A-1 §3-㉰-⑷`). 배포 뒤 표기만 물리고 싶을 때는
   마이그레이션을 되돌리지 않는다 — **화면·서버의 `fileExtension` 소비를 되돌리면**
   화면이 종전대로 `format` 을 보인다(퇴행 경로가 이미 그 길이다). 열은 남아 있어도
   아무도 읽지 않으므로 무해하고, 두 번째 배포 때 백필을 다시 돌릴 필요도 없다.
   ⛔ 그 경우에도 `topic`·`variables`·`format` 을 지우지 않는다 — 이관 대조 근거다.

Revision ID: 0013_ra1_ext_interval_period
Revises: 0011_lv1_drop_level_user_set
"""
from __future__ import annotations

from alembic import op

revision = "0013_ra1_ext_interval_period"
down_revision = "0011_lv1_drop_level_user_set"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- ⑴ M-9 — 조각의 확장자. 자리부터 세운다. 값은 아래 ⑵ 가 채운다.
ALTER TABLE d3_dataset_autometa
  ADD COLUMN file_extension text;

-- ⑵ M-9 백필. **이 한 구간만 FORCE 를 내린다** (위 산문 참조).
ALTER TABLE d3_dataset_autometa NO FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_file             NO FORCE ROW LEVEL SECURITY;

-- 파일명 → 확장자. `regexp` 하나로 규칙을 적는다 —
--   `\.([^.]+)$` = 마지막 점 뒤. 점 앞이 비면(`.bashrc`) 안 잡힌다 = 확장자가 아니다.
-- 조각이 여럿이면 아무거나가 아니라 **가장 작은 값**을 고른다. 규칙상 전부 같지만,
-- 어긋난 과거 행이 있어도 결과가 실행마다 흔들리지 않아야 재실행이 같은 값을 낸다.
UPDATE d3_dataset_autometa a
   SET file_extension = sub.ext
  FROM (
    SELECT f.dataset_id,
           min(lower((regexp_match(f.file_name, '\.([^.]+)$'))[1])) AS ext
      FROM d3_file f
     WHERE f.kind = '본체'
     GROUP BY f.dataset_id
  ) AS sub
 WHERE a.dataset_id = sub.dataset_id
   AND sub.ext IS NOT NULL;

-- 백필이 실제로 한 일을 DB 에게 되묻는다. **「돌았다」가 아니라 「맞다」를 센다.**
-- 조각의 파일명이 확장자를 말하는데 열이 비어 있는 행이 하나라도 남으면 실패다.
DO $$
DECLARE leftover bigint; sample text;
BEGIN
  SELECT count(*), min(f.file_name) INTO leftover, sample
    FROM d3_file f
    JOIN d3_dataset_autometa a ON a.dataset_id = f.dataset_id
   WHERE f.kind = '본체'
     AND regexp_match(f.file_name, '\.([^.]+)$') IS NOT NULL
     AND a.file_extension IS NULL;
  IF leftover > 0 THEN
    RAISE EXCEPTION '확장자를 뽑을 수 있는데 안 채워진 행이 % 건 남았다 (예: %) — 백필이 전수를 못 덮었다 (M-9)',
      leftover, sample;
  END IF;
END
$$;

ALTER TABLE d3_dataset_autometa FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_file             FORCE ROW LEVEL SECURITY;

-- 되올렸는지 DB 에게 되묻는다.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class
     WHERE relname IN ('d3_dataset_autometa', 'd3_file')
       AND relnamespace = 'public'::regnamespace
       AND NOT relforcerowsecurity
  ) THEN
    RAISE EXCEPTION 'FORCE ROW LEVEL SECURITY 가 복구되지 않았다 — 마이그레이션을 되돌린다';
  END IF;
END
$$;
"""

DOWNGRADE = r"""
-- ⑴ M-9 되돌림. 값은 전량 파일명에서 파생된 것이라 다시 올리면 그대로 복원된다.
ALTER TABLE d3_dataset_autometa
  DROP COLUMN IF EXISTS file_extension;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """열을 지운다. **잃는 값이 없다** — 파일명에서 다시 뽑히는 파생값이다."""
    op.execute(DOWNGRADE)
