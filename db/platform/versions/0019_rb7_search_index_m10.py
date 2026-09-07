"""R-B-2 `M-10` — 검색 색인 재정의 ＋ 변수명·분류 미러 트리거 (PRD-21 · PRD-05 · WU-B7)

선언 정본은 db/platform/schema.sql 이다. 이 파일은 0018 까지의 스키마에 그 정본의
**차분만** 더한다 — 두 쪽이 갈라지면 schema-diff 게이트가 red 를 낸다.

━━ 왜 여기서 한 번만 도는가 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

R-A 가 PRD-21 「`nc` 로도 찾는다」를 **미충족 1건**으로 이월했다. 색인식을 바꾸면
**생성 컬럼 전 행 재계산 ＋ GIN 재생성**이 돌고, 그것을 회차마다 하지 않으려고 세 가지를
한 마이그레이션에 묶었다 — 이 파일이 그 한 번이다(라운드 축자 「두 번 돌리지 않는다」).

━━ ⑴ `nc` 가 안 잡히던 이유 (실측) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`d3_dataset_autometa.search_vector` 의 B 가중치가 `format` ＋ 변수명뿐이었다.
`format` 은 **판별 결과**(`netcdf`)라서 `netcdf` 는 잡히고 **`nc` 는 안 잡혔다** —
확장자 `file_extension`(`0013` 이 세운 열 · 저장값 `nc`)이 색인식에 없었기 때문이다.
⛔ `format` 을 **빼지 않는다** — `netcdf` 검색의 회귀가 곧 이 회차의 수용 기준이다.

━━ ⑵ `category` 를 색인에 넣는 길 — ㈏(미러 열) ━━━━━━━━━━━━━━━━━━━━━

⚠ **생성 컬럼은 같은 행의 열만 참조한다.** 그런데 `category` 는 `d3_dataset_description`
(사람이 고르는 값 · `0015`)에 살고 색인은 `d3_dataset_autometa` 에 붙는다. 두 갈래가 있었다 —

  ㈎ 색인을 **트리거가 유지하는 평범한 tsvector 열**로 바꾼다.
  ㈏ **미러 열 한 칸**(`category_mirror`)을 두고 생성 컬럼은 그대로 둔다.  ← 고른 쪽

㈏ 가 **작은 변경**이다: ㈎ 는 `format`·`variables`·`crs`·`grid`·`bundle_file_name`·
`file_extension` **여섯 열 전부**의 갱신을 트리거가 떠맡아야 하고, 한 열이라도 빠지는 날
색인이 조용히 낡는다(그 낡음은 오류를 내지 않는다). ㈏ 는 트리거가 **사본 두 칸**만 보고
나머지는 DB 가 하던 대로 자동으로 유지한다.
⛔ 쓰기 정본은 여전히 원천 표 하나다 — 미러를 사람이나 응용이 직접 쓰지 않는다.

━━ ⑶ 변수명 미러 (`0016` 이 남긴 잔여 위험을 닫는다) ━━━━━━━━━━━━━━━━━

`0016` 이 변수를 **행 표**(`d3_dataset_variable`)로 옮겼고 색인은 여전히 배열
(`d3_dataset_autometa.variables`)을 문다. 그래서 **새로 쓴 변수 행이 검색에 안 들어왔다**
(`0016` 모듈 산문이 명시적으로 받아들인 잔여 위험). 이 회차의 트리거가 배열을 행 표의
미러로 유지해 그 자리를 닫는다 — **행 표가 정본이고 배열은 사본**이다(PRD-16 축자
「트리거만 쓴다」). ⛔ `variables` 열을 지우지 않는다(되돌림 경로 · 라운드 ㉴).

━━ 재계산·재생성은 정확히 1회다 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

순서가 그것을 강제한다 — ① 색인 DROP ② 생성 컬럼 DROP ③ 미러 열 ADD ④ **백필**
⑤ 생성 컬럼 ADD(전 행 계산 1회) ⑥ 색인 CREATE(1회) ⑦ 트리거.
백필을 ⑤ 앞에 두는 것이 요점이다 — 뒤에 두면 백필 UPDATE 가 생성 컬럼을 **다시** 계산한다.

⚠ `ALTER TABLE ADD COLUMN` 은 열을 **뒤에** 붙인다. 그래서 `schema.sql` 의
`d3_dataset_autometa` 선언에서 `search_vector` 가 맨 뒤로 내려갔다 — 선언이 이 순서와
다르면 schema-diff 가 red 다(`0013` 이 배운 자리와 같은 규율).

━━ RLS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`d3_dataset_autometa`·`d3_dataset_description`·`d3_dataset_variable` **셋 다 FORCE** 다.
마이그레이터 롤은 `colab_owner`(NOSUPERUSER · NOBYPASSRLS)이고 `app.current_lab` 이 없어
`current_lab_id()` 가 NULL 이다 — FORCE 아래에서 백필은 **오류 없이 0행**으로 끝난다
(`0013`·`0016` 이 배운 자리). 그래서 **백필 구간만 NO FORCE 로 내리고 곧바로 되올린다.**
되올림과 백필 건수는 DO 블록 단언 셋이 DB 에게 되묻는다.

━━ 되돌림 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

`downgrade` 는 트리거·함수·미러 열을 지우고 색인식을 `0018` 형태로 되돌린다(같은 순서로
재계산·재생성 1회). **잃는 값이 없다** — 미러는 사본이고 원천 두 표가 그대로 있다.
⚠ 되돌린 순간 다시 「`nc` 는 안 잡히고 새 변수 행은 색인에 없다」로 돌아간다.

⚠ ⭑ **32자를 넘기지 않는다** — `alembic_version_platform.version_num` 이 `varchar(32)` 다.
   `0019_rb7_search_index_m10` = 24자.

Revision ID: 0019_rb7_search_index_m10
Revises: 0018_rb6_lv0_source
"""
from __future__ import annotations

from alembic import op

revision = "0019_rb7_search_index_m10"
down_revision = "0018_rb6_lv0_source"
branch_labels = None
depends_on = None


UPGRADE = r"""
-- ① 색인 · ② 생성 컬럼을 떨군다. 이 둘이 먼저 가야 백필이 재계산을 유발하지 않는다.
DROP INDEX IF EXISTS d3_dataset_autometa_search_idx;
ALTER TABLE d3_dataset_autometa DROP COLUMN search_vector;

-- ③ 미러 열. 선언(`db/platform/schema.sql`)과 **한 글자도 다르지 않아야** schema-diff 가 green 이다.
ALTER TABLE d3_dataset_autometa ADD COLUMN category_mirror text;

-- ④ 백필 — **원천 두 표를 읽는 이 구간만 FORCE 를 내린다**(모듈 산문 「RLS」).
ALTER TABLE d3_dataset_autometa     NO FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_description  NO FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_variable     NO FORCE ROW LEVEL SECURITY;

-- >>> M10 BACKFILL BEGIN — 드리프트 대조군(㈑-b)이 이 구간만 도려낸다. 표식을 지우지 않는다.
UPDATE d3_dataset_autometa a
   SET category_mirror = dd.category
  FROM d3_dataset_description dd
 WHERE dd.dataset_id = a.dataset_id;

-- 변수 배열을 행 표의 미러로 맞춘다. **행이 0개인 데이터셋은 배열도 빈 배열**이다 —
-- `0016` 이 「빈 배열은 이관 대상이 아니다」로 남긴 행과 같은 상태로 수렴한다.
-- ⚠ 순서는 `ordinal` 이다(`0016` 이 배열 순서를 그대로 `ordinal` 로 옮겼으므로 무변이 정상).
UPDATE d3_dataset_autometa a
   SET variables = coalesce(
         (SELECT array_agg(v.name ORDER BY v.ordinal)
            FROM d3_dataset_variable v WHERE v.dataset_id = a.dataset_id), '{}'::text[]);

-- 백필이 실제로 한 일을 DB 에게 되묻는다. **「돌았다」가 아니라 「맞다」를 센다.**
-- ⚠ 단언은 **NO FORCE 구간 안**에 둔다 — 밖에 두면 두 쪽이 다 RLS 에 막혀 `0 = 0` 으로
--   green 이 되고, 단언이 결함을 못 잡는다(`0016` 이 배운 자리).
DO $$
DECLARE bad bigint;
BEGIN
  SELECT count(*) INTO bad
    FROM d3_dataset_autometa a
    JOIN d3_dataset_description dd ON dd.dataset_id = a.dataset_id
   WHERE a.category_mirror IS DISTINCT FROM dd.category;
  IF bad <> 0 THEN
    RAISE EXCEPTION '분류 미러가 원천과 다른 행이 %건이다 — 백필이 전수를 못 덮었다 (M-10)', bad;
  END IF;

  SELECT count(*) INTO bad
    FROM d3_dataset_autometa a
   WHERE a.variables IS DISTINCT FROM coalesce(
           (SELECT array_agg(v.name ORDER BY v.ordinal)
              FROM d3_dataset_variable v WHERE v.dataset_id = a.dataset_id), '{}'::text[]);
  IF bad <> 0 THEN
    RAISE EXCEPTION '변수 미러가 행 표와 다른 행이 %건이다 — 백필이 전수를 못 덮었다 (M-10)', bad;
  END IF;
END
$$;
-- <<< M10 BACKFILL END

-- FORCE 를 되올리고, 되올렸는지 DB 에게 되묻는다.
ALTER TABLE d3_dataset_autometa     FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_description  FORCE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset_variable     FORCE ROW LEVEL SECURITY;

DO $$
DECLARE unforced text;
BEGIN
  SELECT string_agg(relname, ', ') INTO unforced
    FROM pg_class
   WHERE relnamespace = 'public'::regnamespace
     AND relname IN ('d3_dataset_autometa', 'd3_dataset_description', 'd3_dataset_variable')
     AND NOT relforcerowsecurity;
  IF unforced IS NOT NULL THEN
    RAISE EXCEPTION 'FORCE ROW LEVEL SECURITY 가 복구되지 않았다(%) — 마이그레이션을 되돌린다', unforced;
  END IF;
END
$$;

-- ⑤ 색인식 재정의 — **전 행 재계산은 이 한 줄에서 1회**다.
--    `file_extension`(`nc`)과 `category_mirror` 가 B 가중치로 들어오고, `format` 은 그대로다.
ALTER TABLE d3_dataset_autometa ADD COLUMN search_vector tsvector GENERATED ALWAYS AS (
  setweight(to_tsvector('simple',
    coalesce(format, '') || ' ' || d3_search_join(variables) || ' ' ||
    coalesce(file_extension, '') || ' ' || coalesce(category_mirror, '')), 'B') ||
  setweight(to_tsvector('simple',
    coalesce(crs, '') || ' ' || coalesce(grid, '') || ' ' ||
    coalesce(bundle_file_name, '')), 'C')
) STORED;

-- ⑥ GIN 재생성 — **1회**.
CREATE INDEX d3_dataset_autometa_search_idx
  ON d3_dataset_autometa USING gin (search_vector);

-- ⑦ 미러를 **앞으로** 유지하는 트리거들. 선언 정본은 schema.sql 이다.
CREATE FUNCTION d3_mirror_variables() RETURNS trigger
  LANGUAGE plpgsql AS $fn$
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
END $fn$;

CREATE TRIGGER d3_dataset_variable_mirror
  AFTER INSERT OR UPDATE OR DELETE ON d3_dataset_variable
  FOR EACH ROW EXECUTE FUNCTION d3_mirror_variables();

CREATE FUNCTION d3_mirror_category() RETURNS trigger
  LANGUAGE plpgsql AS $fn$
BEGIN
  UPDATE d3_dataset_autometa a
     SET category_mirror = NEW.category
   WHERE a.dataset_id = NEW.dataset_id AND a.category_mirror IS DISTINCT FROM NEW.category;
  RETURN NULL;
END $fn$;

CREATE TRIGGER d3_dataset_description_category_mirror
  AFTER INSERT OR UPDATE OF category ON d3_dataset_description
  FOR EACH ROW EXECUTE FUNCTION d3_mirror_category();

CREATE FUNCTION d3_pull_mirrors() RETURNS trigger
  LANGUAGE plpgsql AS $fn$
BEGIN
  IF NEW.category_mirror IS NULL THEN
    SELECT dd.category INTO NEW.category_mirror
      FROM d3_dataset_description dd WHERE dd.dataset_id = NEW.dataset_id;
  END IF;
  IF NEW.variables IS NULL OR cardinality(NEW.variables) = 0 THEN
    NEW.variables := coalesce(
      (SELECT array_agg(v.name ORDER BY v.ordinal)
         FROM d3_dataset_variable v WHERE v.dataset_id = NEW.dataset_id), '{}'::text[]);
  END IF;
  RETURN NEW;
END $fn$;

CREATE TRIGGER d3_dataset_autometa_pull_mirrors
  BEFORE INSERT ON d3_dataset_autometa
  FOR EACH ROW EXECUTE FUNCTION d3_pull_mirrors();
"""

DOWNGRADE = r"""
-- 트리거·함수를 걷고 색인식을 `0018` 형태로 되돌린다. **잃는 값이 없다** — 미러는 사본이고
-- 원천 두 표(`d3_dataset_description`·`d3_dataset_variable`)가 그대로 있다.
DROP TRIGGER IF EXISTS d3_dataset_autometa_pull_mirrors ON d3_dataset_autometa;
DROP TRIGGER IF EXISTS d3_dataset_description_category_mirror ON d3_dataset_description;
DROP TRIGGER IF EXISTS d3_dataset_variable_mirror ON d3_dataset_variable;
DROP FUNCTION IF EXISTS d3_pull_mirrors();
DROP FUNCTION IF EXISTS d3_mirror_category();
DROP FUNCTION IF EXISTS d3_mirror_variables();

DROP INDEX IF EXISTS d3_dataset_autometa_search_idx;
ALTER TABLE d3_dataset_autometa DROP COLUMN search_vector;
ALTER TABLE d3_dataset_autometa DROP COLUMN category_mirror;
ALTER TABLE d3_dataset_autometa ADD COLUMN search_vector tsvector GENERATED ALWAYS AS (
  setweight(to_tsvector('simple',
    coalesce(format, '') || ' ' || d3_search_join(variables)), 'B') ||
  setweight(to_tsvector('simple',
    coalesce(crs, '') || ' ' || coalesce(grid, '') || ' ' ||
    coalesce(bundle_file_name, '')), 'C')
) STORED;
CREATE INDEX d3_dataset_autometa_search_idx
  ON d3_dataset_autometa USING gin (search_vector);
"""


def upgrade() -> None:
    op.execute(UPGRADE)


def downgrade() -> None:
    """색인식을 되돌리고 미러를 걷는다.

    ⚠ 되돌린 순간 다시 **`nc` 는 안 잡히고 새 변수 행은 색인에 없다** — 그것이 `0018`
    까지의 상태이고, 그 잔여 위험은 `0016` 모듈 산문이 이미 적어 뒀다.
    """
    op.execute(DOWNGRADE)
