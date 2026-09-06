"""R-A-1 — 확장자 표기 · 관측 간격 · 기간 최소 단위를 **한 head 에** 담는다

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0012 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 한 파일인가 (`R-A-1-db.md` 「마이그레이션 — 한 head」) ━━━━━━━━━━━━━━━

`M-9`(WU-A5 확장자) · `M-6`·`M-7`(WU-A6 관측 간격·기간 최소 단위)는 **같은 회차**의
같은 표를 만진다. 회차마다 파일을 쪼개면 head 가 갈라지고, 갈라진 head 는 배포 순서를
사람이 기억해야 하는 사실로 만든다. `migration-single-head` 게이트가 그것을 잰다.
⭑ **세 변경이 다 들어왔다** — `M-9`(레인 `p3-extension-label`) ＋ `M-6`·`M-7`(레인
   `p3-interval-period`). 뒤 레인은 **이 파일에 이어 적었고** 새 리비전을 만들지 않았다.
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

━━ `M-6` · 관측 간격을 **두 칸**으로 저장한다 (PRD-17 · 미결-4 ⓐ) ━━━━━━━━━━━

사람이 적는 값이라 `d3_dataset_description` 이다 — `autometa` 는 **파일에서 자동으로 읽은
것**만 담는다(정본 §4.1). 관측 간격은 파일이 말해 주지 않는다.

**숫자＋단위 구조화다. 자유 텍스트 한 칸이 아니다.** 화면이 이미 숫자 칸과 단위 셀렉트로
받는 모양이고(docx `D-3-1`), 조립한 구조를 저장 직전에 버리면 「1시간 이하」 같은 조건
검색이 영영 안 선다. 신규 열이라 지금 정하면 **backfill 이 0** 이다.

CHECK 가 **둘**이다. ⑴ 단위는 6값 안(`초·분·시·일·월·년`) ⑵ **둘 다 NULL 이거나 둘 다 값**.
⑵ 가 없으면 「10」만 저장된 반쪽 행이 생기고, 그 행은 화면이 무엇으로도 못 그린다 —
`10` 인지 `10분` 인지 `10일` 인지 DB 가 모른다. 서버의 400 은 그 규율의 앞문이고
CHECK 는 **뒷문**이다(어느 경로로 들어와도 반쪽이 안 생긴다).

⛔ **선택 입력이다** — `NOT NULL` 을 걸지 않는다. 필수로 잠그면 간격이 불규칙하거나 모르는
자료를 올릴 길이 없고, 값이 없는 기존 행에 예외 규칙이 따라붙는다(PRD-17 축자).

━━ `M-7` · 기간의 **최소 단위** 한 칸 (PRD-18 · 미결-18 ⓐ) ━━━━━━━━━━━━━━━━

**저장은 이미 구조화돼 있다** — `period_start`/`period_end` 가 `timestamptz` 다. 없는 것은
「이 기간을 어느 자리까지 말하는가」뿐이다. 그것이 `period_granularity` 한 칸이고,
값 집합은 `년·월·일·시·분·초` 6값이다.

⚠ **시각값 저장을 바꾸지 않는다**(미결-18 ⓐ 축자). 화면이 최소 단위 셀렉트 ＋ Start/End 를
조립해 `timestamptz` 로 만들고, 이 열은 **그 조립을 되돌려 읽는 열쇠**다. 단위를 저장하지
않으면 `2025-06-01T00:00:00Z` 가 「6월 1일」인지 「6월 1일 0시 0분」인지 갈리지 않는다.

`autometa` 인 이유 = 기간 두 칸이 이미 거기 있고, 최소 단위는 **그 두 칸을 읽는 방법**이라
같은 표에 붙어야 한 번의 조회로 함께 온다. 열이 갈리면 기간을 그리는 자리마다 조인이 는다.

**전 행 NULL 이다 = 「단위 미지정」.** 화면은 종전과 같이 `date-time` 전체를 보인다 —
**재선택을 강제하지 않는다.** ⛔ 백필이 없다(있을 수가 없다 — 저장된 시각값은 사람이 어느
자리까지 의도했는지를 말해 주지 않는다. 지어내면 그것이 곧 거짓 정밀도다).

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`downgrade` 는 열을 지운다. **잃는 값이 없다** — 이 열의 값은 전량 `d3_file.file_name`
에서 파생된 것이라 upgrade 를 다시 돌리면 같은 값이 그대로 복원된다. 사람이 손으로 적는
칸이 아니기 때문에 `0007` 류의 「되돌리면 사람의 선택이 안 돌아온다」가 여기엔 없다.

⭑ **열을 지우지 않고 되돌리는 길** (`R-A-1 §3-㉰-⑷`). 배포 뒤 표기만 물리고 싶을 때는
   마이그레이션을 되돌리지 않는다 — **화면·서버의 `fileExtension` 소비를 되돌리면**
   화면이 종전대로 `format` 을 보인다(퇴행 경로가 이미 그 길이다). 열은 남아 있어도
   아무도 읽지 않으므로 무해하고, 두 번째 배포 때 백필을 다시 돌릴 필요도 없다.
   ⛔ 그 경우에도 `topic`·`variables`·`format` 을 지우지 않는다 — 이관 대조 근거다.

⭑ **`M-6`·`M-7` 의 되돌림은 한 걸음 더 조심한다.** 이 두 자리의 값은 **사람이 적은 것**이라
   `M-9` 와 달리 파생이 아니다 — `downgrade` 로 열을 지우면 **사람이 고른 값이 사라지고
   다시 올려도 안 돌아온다**(`0007` 류의 실패). 그래서 배포 뒤 물리고 싶을 때의 정규 경로는
   **소비를 멈추는 쪽**이다: 계약·서버·화면에서 `observationInterval`·`granularity` 를
   되돌리면 열은 남은 채 아무도 안 읽는다(전 행 NULL 이라 무해하고, 그 뒤 다시 열어도
   사람이 적어 둔 값이 그대로 살아 있다). 열까지 지우는 것은 **값이 0 행일 때만** 한다.

Revision ID (아래) 는 바뀌지 않는다 — 세 변경이 한 head 다.

Revision ID: 0013_ra1_ext_interval_period
Revises: 0012_merge_lv1_and_transfer
"""
from __future__ import annotations

from alembic import op

revision = "0013_ra1_ext_interval_period"
down_revision = "0012_merge_lv1_and_transfer"
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

-- ⑶ M-6 — 관측 간격 **두 칸**. 사람이 적는 값이라 `d3_dataset_description` 이다.
--    ⛔ 백필이 없다. 전 행 NULL 이 정상이고 재선택을 강제하지 않는다 (PRD-17).
ALTER TABLE d3_dataset_description
  ADD COLUMN observation_interval_value numeric,
  ADD COLUMN observation_interval_unit  text;

-- 단위는 6값 안이다. NULL 은 「모른다」이고 그것이 기본 상태다.
ALTER TABLE d3_dataset_description
  ADD CONSTRAINT d3_dataset_description_interval_unit_check
  CHECK (observation_interval_unit IS NULL
         OR observation_interval_unit IN ('초', '분', '시', '일', '월', '년'));

-- **둘 다 NULL 이거나 둘 다 값**. 반쪽 행은 화면이 무엇으로도 못 그린다 —
-- `10` 인지 `10분` 인지 DB 가 모른다. 서버의 400 이 앞문이고 이 CHECK 가 뒷문이다.
ALTER TABLE d3_dataset_description
  ADD CONSTRAINT d3_dataset_description_interval_pair_check
  CHECK ((observation_interval_value IS NULL) = (observation_interval_unit IS NULL));

-- ⑷ M-7 — 기간의 **최소 단위** 한 칸. 기간 두 칸이 사는 표에 붙인다 (한 조회로 함께 온다).
--    전 행 NULL = 「단위 미지정」이고 화면은 종전 표기 그대로다 (PRD-18).
ALTER TABLE d3_dataset_autometa
  ADD COLUMN period_granularity text;

ALTER TABLE d3_dataset_autometa
  ADD CONSTRAINT d3_dataset_autometa_period_granularity_check
  CHECK (period_granularity IS NULL
         OR period_granularity IN ('년', '월', '일', '시', '분', '초'));
"""

DOWNGRADE = r"""
-- ⑴ M-7 되돌림.
ALTER TABLE d3_dataset_autometa
  DROP CONSTRAINT IF EXISTS d3_dataset_autometa_period_granularity_check;
ALTER TABLE d3_dataset_autometa
  DROP COLUMN IF EXISTS period_granularity;

-- ⑵ M-6 되돌림. ⚠ **사람이 적은 값이 여기 있으면 사라진다** — 다시 올려도 안 돌아온다.
--    값이 있는 배포에서 표기만 물리려면 이 경로가 아니라 **소비를 멈추는 쪽**이다(윗글).
ALTER TABLE d3_dataset_description
  DROP CONSTRAINT IF EXISTS d3_dataset_description_interval_pair_check;
ALTER TABLE d3_dataset_description
  DROP CONSTRAINT IF EXISTS d3_dataset_description_interval_unit_check;
ALTER TABLE d3_dataset_description
  DROP COLUMN IF EXISTS observation_interval_unit;
ALTER TABLE d3_dataset_description
  DROP COLUMN IF EXISTS observation_interval_value;

-- ⑶ M-9 되돌림. 값은 전량 파일명에서 파생된 것이라 다시 올리면 그대로 복원된다.
ALTER TABLE d3_dataset_autometa
  DROP COLUMN IF EXISTS file_extension;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """열 넷을 지운다.

    `file_extension`(M-9)은 **잃는 값이 없다** — 파일명에서 다시 뽑히는 파생값이다.
    ⚠ `observation_interval_*`(M-6)·`period_granularity`(M-7)는 **사람이 고른 값**이라
    지우면 다시 올려도 안 돌아온다. 값이 있는 배포에서는 이 경로 대신 **소비를 멈추는
    쪽**을 쓴다(모듈 산문 「되돌림」).
    """
    op.execute(DOWNGRADE)
