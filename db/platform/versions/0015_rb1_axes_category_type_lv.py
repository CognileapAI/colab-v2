"""R-B-1 — 분류 3축(분류 · 유형 · 사람이 고른 가공 단계)을 **한 head 에** 담는다

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0014 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 한 파일인가 (`R-B-1-db.md` 「마이그레이션 — 한 head」) ━━━━━━━━━━━━━━

`M-1`(분류) · `M-2`(유형) · `M-3`(사람이 고른 가공 단계)는 **같은 회차**의 같은 등록
화면이 요구하는 세 칸이다. 회차마다 파일을 쪼개면 head 가 갈라지고, 갈라진 head 는
배포 순서를 사람이 기억해야 하는 사실로 만든다. `migration-single-head` 가 그것을 잰다.
⭑ **이 리비전이 R-B 의 head 를 만든다** — `M-5`(WU-B2) · `M-4`(WU-B4) · `M-8`(WU-B6)
   이 뒤 레인에서 **이 파일에 이어 적거나** 이 리비전을 잇는다.
⛔ **`M-10`(색인 재정의 ＋ 변수명 미러)은 여기 없다** — `R-B-2-server.md`(WU-B7 뒤)에서
   라운드에 **한 번만** 돈다. 생성 컬럼 재계산 ＋ GIN 재생성을 두 번 하지 않는다.
⛔ **색인식을 한 글자도 건드리지 않는다.** PRD-01 은 「`search_vector` 의 B 가중치 항을
   `topic` 에서 `category` 로 교체」라고 적었으나, 그 교체는 `M-10` 소유다(라운드 파일
   「마이그레이션 — 한 head」절이 색인 작업을 R-B-2 로 넘겼다). 여기서 앞당기면 같은
   생성 컬럼을 두 회차가 재계산한다.

━━ `M-1`·`M-2` · 왜 사람이 적는 표인가 (PRD-01 · PRD-02) ━━━━━━━━━━━━━━━━

분류·유형은 **사람이 고르는 값**이라 `d3_dataset_description` 이다 — `autometa` 는
파일에서 자동으로 읽은 것만 담는다(정본 §4.1). 파일은 「이것이 재분석자료인가」를
말해 주지 않는다.

**저장값은 국문뿐이다**(미결-13 ⓐ 축자 「표시만 국문＋영문 병기 … 저장·CHECK·필터·
색인은 국문 단일」). `기상·기후 인자 (Meteorological & Climatic Factors)` 는 화면이
조립하는 글자이고 DB 는 앞의 국문만 안다.

**컬럼명이 `data_type` 인 것은 우연이 아니다**(PRD-02 축자) — `type` 은 SQL·TS 양쪽에서
예약어·내장 이름과 겹친다.

⛔ **조합 검증을 만들지 않는다**(미결-14 ⓐ). 「관측 기반 산출물 ↔ Level 2 와 밀접」은
   표의 안내 문구이고 제약이 아니다. 세 축은 서로 독립이다.

━━ `M-3` · `0011` 의 **반전**이다 (PRD-03 · 미결-2 ⓐ · 미결-7 ⓐ) ━━━━━━━━━━━

`0007` 이 세운 `d3_dataset.processing_level_user_set` 을 `0011` 이 지웠다 — 근거는
`PLAN-SoT §9 〈194〉`(＋`〈276〉`)의 「레벨은 언제나 계보에서 나온다 — 사람이 직접
정하지 못한다 … 예외 없음」이었다. **이번 회차가 그 문장을 되돌린다.**

⛔ **삭제 근거를 지우지 않는다.** `db/platform/schema.sql` 의 `0011` 문단은 그대로 있고,
   그 아래에 반전 문장을 **덧붙였다**. 지우면 「왜 두 번 뒤집혔는가」를 아무도 못 읽는다.

**파생 계산은 폐기되지 않는다**(PRD-10). 두 값이 병존하고, 어긋나면 **경고만** 낸다 —
등록을 막지 않는다. 응답에서 두 값을 갈라 싣는 열쇠(`processingLevelDerived` ·
`processingLevelMismatch`)와 파생 상한(`LV_CAP`) 조정은 **`WU-B5` 몫**이라 여기 없다.

**상한은 `Lv3` 이다**(미결-7 ⓐ) — CHECK 4값 · 계약 enum 4값 · 화면 칩 4단.

━━ 기존 데이터 — **backfill 이 0 이다** ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

세 열 전부 **전 행 NULL** 이고 자동 매핑을 만들지 않는다(미결-3 ⓐ 축자). 그래서 이
마이그레이션에는 `UPDATE` 가 한 줄도 없고, `0013` 이 필요로 했던 `NO FORCE ROW LEVEL
SECURITY` 구간도 **없다**(고칠 행이 없으므로 정책을 내릴 이유가 없다).

  · `category`·`data_type` — 대응 관계가 없다. `topic` 6값과 분류 5값은 **다른 축**이고
    (`강우·강수` 는 분류가 아니라 주제다), 짝지으면 그 순간 거짓 분류가 13행에 박힌다.
  · `processing_level_user_set` — 파생값을 복사하면 「사람이 골랐다」와 「계산됐다」의
    구분이 영구히 사라진다. 화면은 NULL 인 동안 파생값에 `자동` 표기를 붙인다.

⛔ **`topic` 열을 지우지 않는다** — 되돌림 경로이자 이관 대조 근거다. 사람이 상세 수정
   에서 분류를 고를 때 종전 주제 값을 보고 고른다.

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`downgrade` 는 세 열을 지운다. 배포 직후라면 전 행 NULL 이라 **잃는 값이 0** 이다.

⚠ **값이 쌓인 뒤에는 다르다.** 세 칸은 전부 **사람이 고른 값**이라 `M-6`·`M-7` 과 같은
   부류다 — 열을 지우면 다시 올려도 안 돌아온다(`0007` 류의 실패). 그래서 배포 뒤
   표기만 물리고 싶을 때의 정규 경로는 **소비를 멈추는 쪽**이다: 계약·서버·화면에서
   `category`·`dataType`·`processingLevelUserSet` 을 되돌리면 열은 남은 채 아무도 안
   읽는다(전 행 NULL 이면 무해하고, 그 뒤 다시 열어도 적어 둔 값이 살아 있다).
   **열까지 지우는 것은 값이 0 행일 때만** 한다.

⚠ ⭑ **32자를 넘기지 않는다** — `alembic_version_platform.version_num` 이 `varchar(32)` 다.
   `0015_rb1_axes_category_type_lv` = 30자.

Revision ID: 0015_rb1_axes_category_type_lv
Revises: 0014_merge_ra1_and_topic_vocab
"""
from __future__ import annotations

from alembic import op

revision = "0015_rb1_axes_category_type_lv"
down_revision = "0014_merge_ra1_and_topic_vocab"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- ⑴ M-1·M-2 — 분류·유형. 사람이 고르는 값이라 `d3_dataset_description` 이다.
--    ⛔ 백필이 없다. 전 행 NULL 이 정상이고 재선택을 강제하지 않는다 (미결-3 ⓐ).
ALTER TABLE d3_dataset_description
  ADD COLUMN category  text,
  ADD COLUMN data_type text;

-- 값 집합은 **국문 단일**이다 — 영문 병기는 화면이 조립한다 (미결-13 ⓐ).
-- 제약 이름은 열 CHECK 의 postgres 기본 이름과 같게 둔다 (schema.sql 이 인라인 CHECK 다).
ALTER TABLE d3_dataset_description
  ADD CONSTRAINT d3_dataset_description_category_check
  CHECK (category IS NULL
         OR category IN ('수문 인자', '기상·기후 인자', '식생·탄소 인자',
                         '사회·경제 인자', '환경 인자'));

ALTER TABLE d3_dataset_description
  ADD CONSTRAINT d3_dataset_description_data_type_check
  CHECK (data_type IS NULL
         OR data_type IN ('지상관측자료', '위성자료', '재분석자료',
                          '수치모형자료', '합성자료', '관측 기반 산출물'));

-- ⑵ M-3 — 사람이 고른 가공 단계. `0011` 이 지운 열을 **재신설**한다 (`〈194〉`·`〈276〉` 반전).
--    ⛔ 백필이 없다 — 파생값을 여기 복사하면 두 값의 구분이 영구히 사라진다 (PRD-03 축자).
ALTER TABLE d3_dataset
  ADD COLUMN processing_level_user_set text;

ALTER TABLE d3_dataset
  ADD CONSTRAINT d3_dataset_processing_level_user_set_check
  CHECK (processing_level_user_set IS NULL
         OR processing_level_user_set IN ('Lv0', 'Lv1', 'Lv2', 'Lv3'));
"""

DOWNGRADE = r"""
-- ⑴ M-3 되돌림.
ALTER TABLE d3_dataset
  DROP CONSTRAINT IF EXISTS d3_dataset_processing_level_user_set_check;
ALTER TABLE d3_dataset
  DROP COLUMN IF EXISTS processing_level_user_set;

-- ⑵ M-1·M-2 되돌림. ⚠ **사람이 고른 값이 여기 있으면 사라진다** — 다시 올려도 안 돌아온다.
--    값이 있는 배포에서 표기만 물리려면 이 경로가 아니라 **소비를 멈추는 쪽**이다(윗글).
ALTER TABLE d3_dataset_description
  DROP CONSTRAINT IF EXISTS d3_dataset_description_data_type_check;
ALTER TABLE d3_dataset_description
  DROP CONSTRAINT IF EXISTS d3_dataset_description_category_check;
ALTER TABLE d3_dataset_description
  DROP COLUMN IF EXISTS data_type;
ALTER TABLE d3_dataset_description
  DROP COLUMN IF EXISTS category;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """열 셋을 지운다.

    배포 직후라면 **잃는 값이 0** 이다(세 열 전부 전 행 NULL · backfill 없음).
    ⚠ 값이 쌓인 뒤에는 **사람이 고른 값**이 사라지고 다시 올려도 안 돌아온다 —
    그때의 정규 경로는 **소비를 멈추는 쪽**이다(모듈 산문 「되돌림」).
    """
    op.execute(DOWNGRADE)
