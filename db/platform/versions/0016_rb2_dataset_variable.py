"""R-B-1 `M-5` — 변수를 **행**으로 받는 표 `d3_dataset_variable` (PRD-16)

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0015 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 새 표인가 (PRD-16 축자) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

「변수 3개에 단위 1개면 어느 변수 것인지 알 수 없다.」 지금 저장은
`d3_dataset_autometa.variables text[]` **이름 배열 하나**뿐이라 단위·값 범위·결측률이
데이터셋당 한 칸이 된다. 그 셋은 **변수마다** 붙어야 하는 값이다.

⛔ **기존 표에 컬럼을 더하지 않는다**(`_프롬프트_개발세션_260826.md §3`) — 배열 세 개를
   나란히 두는 모양은 순서가 어긋나는 날 아무도 못 고친다.
⛔ **D3 소유다.** D2 가 이 표를 FK 하지 않는다 (`CLAUDE.md §3-1`).

━━ 이관 — 배열 순서가 곧 `ordinal` 이다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`d3_dataset_autometa.variables` 의 원소를 그대로 옮긴다 — `ordinal` = 배열 순서(1 부터),
`name` = 원소, `unit`·`value_range`·`missing_rate` = **NULL**, `is_representative` =
**첫 행만 true**. 지어낼 값이 없으므로 세 칸은 비운 채 둔다(거짓 정밀도를 만들지 않는다).

⛔ **원본 `variables` 열을 지우지 않는다** — 되돌림 경로이자 이관 대조 근거이고,
   검색 색인(`d3_dataset_autometa.search_vector` 의 `d3_search_join(variables)`)이 아직
   그 열을 문다. 빈 배열인 데이터셋은 **이관 대상이 아니다**(행이 0개로 남는다).

⚠ 공백뿐인 원소는 옮기지 않는다 — `name` 의 CHECK(`length(btrim(name)) > 0`)가 거부한다.
  걸러 낸 뒤 **다시 번호를 매겨** 구멍 없는 `ordinal` 과 「첫 행이 대표」를 함께 지킨다.

━━ 색인 · 트리거는 여기 없다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⛔ **`M-10`(색인 재정의 ＋ 변수명 미러 트리거)은 이 파일에 없다** —
   `R-B-2-server.md`(WU-B7 뒤)에서 라운드에 **한 번만** 돈다(생성 컬럼 재계산 ＋ GIN
   재생성을 두 번 하지 않는다). `search_vector` 를 한 글자도 건드리지 않는다.
⚠ 그래서 **M-10 전까지는 새로 쓴 변수 행이 검색 색인에 안 들어간다.** 이관된 기존 행의
  검색은 그대로다(배열이 그 자리에 남아 있다) — 이 회차가 명시적으로 받아들인 잔여 위험이다.

━━ RLS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

형제 메타 표(`d3_dataset_description`·`d3_dataset_autometa`)와 **같은 경계 정책 한 장** ＋
FORCE 다. ⚠ **정책은 이관 INSERT 뒤에 켠다** — 켠 뒤에 넣으면 소유자 세션이 FORCE 에
걸려 이관이 0행으로 조용히 끝난다(`0013` 이 `NO FORCE` 구간으로 배운 자리의 다른 얼굴).
⚠ **원천 `d3_dataset_autometa` 도 FORCE 다** — 그래서 이관 SELECT 구간만 `NO FORCE` 로
내리고 곧바로 되올린다. 되올림과 이관 건수는 DO 블록 단언 둘이 DB 에게 되묻는다.

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`downgrade` 는 표를 통째로 지운다. **이관된 값은 안 사라진다** — 원본 배열이 그대로
`d3_dataset_autometa.variables` 에 있기 때문이고, 그것이 배열 열을 남긴 이유다.
⚠ 배포 뒤에 사람이 적은 **단위·값 범위·결측률·대표**는 그 배열에 자리가 없어 **사라진다.**
  그때의 정규 경로는 소비를 멈추는 쪽이다(계약·서버·화면에서 객체 배열을 되돌리면 표는
  남은 채 아무도 안 읽는다). 표까지 지우는 것은 그 세 칸이 전 행 NULL 일 때만 한다.

⚠ ⭑ **32자를 넘기지 않는다** — `alembic_version_platform.version_num` 이 `varchar(32)` 다.
   `0016_rb2_dataset_variable` = 25자.

Revision ID: 0016_rb2_dataset_variable
Revises: 0015_rb1_axes_category_type_lv
"""
from __future__ import annotations

from alembic import op

revision = "0016_rb2_dataset_variable"
down_revision = "0015_rb1_axes_category_type_lv"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- ⑴ 표. 선언(`db/platform/schema.sql`)과 **한 글자도 다르지 않아야** schema-diff 가 green 이다.
CREATE TABLE d3_dataset_variable (
  dataset_id ulid    NOT NULL REFERENCES d3_dataset(id),
  lab_id     ulid    NOT NULL REFERENCES d1_lab(id),
  ordinal    integer NOT NULL,
  name       text    NOT NULL CHECK (length(btrim(name)) > 0),
  unit          text,
  value_range   text,
  missing_rate  text,
  is_representative boolean NOT NULL DEFAULT false,
  PRIMARY KEY (dataset_id, ordinal)
);
CREATE INDEX d3_dataset_variable_lab_idx ON d3_dataset_variable (lab_id);
CREATE UNIQUE INDEX d3_dataset_variable_representative_idx
  ON d3_dataset_variable (dataset_id)
  WHERE is_representative;

-- ⑵ 이관. **배열 순서가 곧 `ordinal`** 이고 **첫 행만 대표**다.
--    공백뿐인 원소를 먼저 걸러 낸 뒤 `row_number()` 로 다시 번호를 매긴다 —
--    걸러 낸 자리를 그대로 두면 `ordinal` 에 구멍이 나고, 첫 원소가 공백이면
--    대표가 한 행도 없는 데이터셋이 생긴다.
--
-- ⚠ **원천을 읽는 이 한 구간만 FORCE 를 내린다**(`0013` 과 같은 이유). 마이그레이터 롤은
--   `colab_owner`(NOSUPERUSER · NOBYPASSRLS)이고 `app.current_lab` 이 없으므로
--   `current_lab_id()` 가 NULL 이다 — FORCE 아래에서는 `d3_dataset_autometa` SELECT 가
--   0행을 내고 INSERT 가 **오류 없이 0행**으로 끝난다. 대상 표는 아직 정책이 없다(⑶ 이 켠다).
ALTER TABLE d3_dataset_autometa NO FORCE ROW LEVEL SECURITY;

INSERT INTO d3_dataset_variable
  (dataset_id, lab_id, ordinal, name, unit, value_range, missing_rate, is_representative)
SELECT s.dataset_id, s.lab_id,
       row_number() OVER w,
       s.name,
       NULL, NULL, NULL,
       row_number() OVER w = 1
FROM (
  SELECT a.dataset_id, a.lab_id, v.name, v.ord
  FROM d3_dataset_autometa a
  CROSS JOIN LATERAL unnest(a.variables) WITH ORDINALITY AS v(name, ord)
  WHERE length(btrim(v.name)) > 0
) s
WINDOW w AS (PARTITION BY s.dataset_id ORDER BY s.ord);

-- 이관이 실제로 한 일을 DB 에게 되묻는다. **「돌았다」가 아니라 「맞다」를 센다.**
-- ⚠ 이 단언은 **NO FORCE 구간 안 · 정책을 켜기 전**에 둔다 — 밖에 두면 두 쪽(원천 배열 ·
--   대상 표)이 다 RLS 에 막혀 `0 = 0` 으로 green 이 되고, 단언이 결함을 못 잡는다.
DO $$
DECLARE want bigint; got bigint;
BEGIN
  SELECT count(*) INTO want
    FROM d3_dataset_autometa a
    CROSS JOIN LATERAL unnest(a.variables) AS v(name)
   WHERE length(btrim(v.name)) > 0;
  SELECT count(*) INTO got FROM d3_dataset_variable;
  IF got <> want THEN
    RAISE EXCEPTION '변수 이관 건수가 % 다 (기대 % = 공백 제외 배열 원소 수) — 이관이 전수를 못 덮었다 (M-5)',
      got, want;
  END IF;
END
$$;

-- FORCE 를 되올리고, 되올렸는지 DB 에게 되묻는다.
ALTER TABLE d3_dataset_autometa FORCE ROW LEVEL SECURITY;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_class
     WHERE relname = 'd3_dataset_autometa'
       AND relnamespace = 'public'::regnamespace
       AND NOT relforcerowsecurity
  ) THEN
    RAISE EXCEPTION 'FORCE ROW LEVEL SECURITY 가 복구되지 않았다 — 마이그레이션을 되돌린다';
  END IF;
END
$$;

-- ⑶ 경계 정책 — **이관 뒤에** 켠다(모듈 산문 「RLS」).
ALTER TABLE d3_dataset_variable ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_variable FORCE  ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_dataset_variable FOR ALL
  USING (lab_id = current_lab_id()) WITH CHECK (lab_id = current_lab_id());
"""

DOWNGRADE = r"""
-- 표를 지운다. 이관된 **이름**은 `d3_dataset_autometa.variables` 에 그대로 남아 있다.
-- ⚠ 사람이 적은 단위·값 범위·결측률·대표는 그 배열에 자리가 없어 **사라진다**(모듈 산문).
DROP TABLE IF EXISTS d3_dataset_variable;
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """표를 지운다.

    이름은 `d3_dataset_autometa.variables` 에 남아 있어 **이관분은 잃지 않는다**.
    ⚠ 배포 뒤에 사람이 적은 단위·값 범위·결측률·대표는 사라지고 다시 올려도 안 돌아온다 —
    그때의 정규 경로는 **소비를 멈추는 쪽**이다(모듈 산문 「되돌림」).
    """
    op.execute(DOWNGRADE)
