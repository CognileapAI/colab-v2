-- 0016 「기존 행」 오라클 — **적재된 데이터 위에서 이관이 무엇을 했는가**.
--
-- 수용 기준 축자 (`R-B-1-db.md §2` WU-B2) 둘을 여기서 잰다 —
--   ㈎ 「Given 마이그레이션 후, When 3원소이던 기존 행 조회, Then `d3_dataset_variable` 에
--      3행이 **순서대로** 있고 첫 행만 대표다.」
--   ㈏ 「Given 변수 `precipitation`, When 검색어 `precipitation`, Then 이관 전후 **같은**
--      데이터셋이 나온다.」
--
-- ⭑ 이 오라클은 「옮겼다」와 **「순서·대표까지 옮겼다」**를 가른다. 대조군(`0016-drift.sh`
--    ㈑-b)은 대표를 첫 행에서 떼어 놓은 DB 이고, 거기서 red 가 나야 이 오라클이 오라클이다.
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0016 기존 행 오라클 실패 — %', msg; END $$;

-- 정책이 FORCE 라 소유자 세션도 스코프가 필요하다.
SET app.current_lab = '0000000000000000000000000T';

-- ⑴ **3원소 → 3행 · 순서대로.** `ordinal` 이 1·2·3 이고 이름이 배열 순서 그대로다.
DO $$
DECLARE got text; want text := '1:precipitation,2:temperature,3:runoff';
BEGIN
  SELECT string_agg(ordinal || ':' || name, ',' ORDER BY ordinal) INTO got
    FROM d3_dataset_variable WHERE dataset_id = '000000000000000000000DSV1A';
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('DSV1 의 변수 행이 %L 다 (기대 %L) — 배열 순서가 ordinal 로 안 옮겨졌다',
                           got, want));
  END IF;
END $$;

-- ⑵ **첫 행만 대표다.** 둘이면 부분 UNIQUE 가 먼저 죽고, 0이면 대표 없는 데이터셋이 된다.
DO $$
DECLARE got text;
BEGIN
  SELECT string_agg(ordinal::text, ',' ORDER BY ordinal) INTO got
    FROM d3_dataset_variable
   WHERE dataset_id = '000000000000000000000DSV1A' AND is_representative;
  IF got IS DISTINCT FROM '1' THEN
    PERFORM _t_fail(format('DSV1 의 대표 행이 ordinal %L 다 (기대 1 하나) — 첫 행 대표가 아니다',
                           coalesce(got, '(없음)')));
  END IF;
END $$;

-- ⑶ **부가 세 칸은 NULL 이다.** 이관이 지어낼 값이 없다 — 채우면 그것이 거짓 정밀도다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset_variable
   WHERE unit IS NOT NULL OR value_range IS NOT NULL OR missing_rate IS NOT NULL;
  IF n > 0 THEN
    PERFORM _t_fail(format('단위·값 범위·결측률이 채워진 이관 행이 %s 건이다 — 지어냈다', n));
  END IF;
END $$;

-- ⑷ **빈 배열은 0행이다** — 이관 대상이 아니다(PRD-16 축자).
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset_variable
   WHERE dataset_id = '000000000000000000000DSV2A';
  IF n <> 0 THEN
    PERFORM _t_fail(format('빈 배열 데이터셋에 변수 행이 %s 건 생겼다', n));
  END IF;
END $$;

-- ⑸ **공백 원소는 걸러 내고 다시 번호를 매긴다.** `ordinal` 에 구멍이 없고 대표가 선다.
DO $$
DECLARE got text; want text := '1:tp:t';
BEGIN
  SELECT string_agg(ordinal || ':' || name || ':' || left(is_representative::text, 1),
                    ',' ORDER BY ordinal) INTO got
    FROM d3_dataset_variable WHERE dataset_id = '000000000000000000000DSV3A';
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('DSV3 의 변수 행이 %L 다 (기대 %L) — 공백 원소를 거른 뒤 다시 '
                           '번호를 매기고 첫 행을 대표로 세워야 한다', got, want));
  END IF;
END $$;

-- ⑹ **원본 배열이 그대로 남아 있다** — 되돌림 경로이자 이관 대조 근거다 (§3-㉴).
DO $$
DECLARE got text; want text := 'precipitation,temperature,runoff';
BEGIN
  SELECT array_to_string(variables, ',') INTO got
    FROM d3_dataset_autometa WHERE dataset_id = '000000000000000000000DSV1A';
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('autometa.variables 가 %L 다 (기대 %L) — 원본 열을 건드렸다', got, want));
  END IF;
END $$;

-- ⑺ **검색이 이관 전후 같은 데이터셋을 낸다** (수용 기준 ㈏).
--    색인을 한 글자도 안 건드렸으므로 `precipitation` 은 여전히 DSV1 하나를 낸다.
DO $$
DECLARE got text;
BEGIN
  SELECT string_agg(dataset_id, ',' ORDER BY dataset_id) INTO got
    FROM d3_dataset_autometa
   WHERE search_vector @@ to_tsquery('simple', 'precipitation');
  IF got IS DISTINCT FROM '000000000000000000000DSV1A' THEN
    PERFORM _t_fail(format('검색어 precipitation 이 %L 를 냈다 (기대 DSV1 하나) — '
                           '이관이 검색 결과를 바꿨다', coalesce(got, '(0건)')));
  END IF;
END $$;

ROLLBACK;
