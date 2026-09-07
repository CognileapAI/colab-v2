-- 0019 구조 오라클 — **색인식과 미러 트리거가 실제로 섰는가**를 빈 DB 에서 잰다.
--
-- 완료 판정 축자 (`R-B-2-server.md §5` `M-10`) — 「`nc` 로 잡힌다 · `netcdf` 가 종전과
-- 같이 잡힌다 · 변수명 검색이 종전과 같이 잡힌다 · 색인 재생성이 1회」.
--
-- ⭑ **정의문만 grep 하지 않는다** — 색인은 텍스트가 아니라 **찾아 내는 동작**이다.
--    그래서 아래는 전부 「넣어 보고 그 낱말로 잡히는가」로 잰다.
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0019 오라클 실패 — %', msg; END $$;

-- 「이 데이터셋이 이 낱말로 잡히는가」 한 줄. 실행기(`d3_catalog._SEARCH`)와 **같은 식**이다 —
-- `simple` 사전 · `to_tsquery` · autometa 색인.
CREATE FUNCTION _t_hits(ds text, word text) RETURNS boolean LANGUAGE sql STABLE AS $$
  SELECT coalesce((SELECT a.search_vector @@ to_tsquery('simple', word)
                     FROM d3_dataset_autometa a WHERE a.dataset_id = ds), false)
$$;

-- 재료. 여기까지는 `postgres`(superuser · RLS 우회)로 심는다.
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                        uploaded_at, last_modified_at) VALUES
  ('000000000000000000000DSM1A', '0000000000000000000000000T', '00000000000000000000000TP1',
   '00000000000000000000000TP1', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
SET app.current_lab = '0000000000000000000000000T';

-- ── A. 미러 열이 선다 ────────────────────────────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'd3_dataset_autometa' AND column_name = 'category_mirror') THEN
    PERFORM _t_fail('d3_dataset_autometa.category_mirror 가 없다 — M-10 의 ㈏ 경로가 안 섰다');
  END IF;
END $$;

-- A-⑵ 색인식이 **셋을 다 문다** — `file_extension`(신설) · `category_mirror`(신설) ·
--     `format`(회귀 · 지운 것이 없다). 식 자체를 보는 유일한 단언이고, 아래 C 가 동작을 잰다.
DO $$
DECLARE def text;
BEGIN
  SELECT pg_get_expr(d.adbin, d.adrelid) INTO def
    FROM pg_attrdef d JOIN pg_attribute a ON a.attrelid = d.adrelid AND a.attnum = d.adnum
   WHERE d.adrelid = 'd3_dataset_autometa'::regclass AND a.attname = 'search_vector';
  IF def IS NULL THEN PERFORM _t_fail('autometa.search_vector 가 생성 컬럼이 아니다'); END IF;
  IF position('file_extension' in def) = 0 THEN
    PERFORM _t_fail(format('색인식에 file_extension 이 없다 — nc 가 안 잡힌다: %L', def));
  END IF;
  IF position('category_mirror' in def) = 0 THEN
    PERFORM _t_fail(format('색인식에 category_mirror 가 없다: %L', def));
  END IF;
  IF position('format' in def) = 0 OR position('d3_search_join' in def) = 0 THEN
    PERFORM _t_fail(format('색인식이 format·변수명을 잃었다 — 더하기만 하는 회차다: %L', def));
  END IF;
END $$;

-- A-⑶ GIN 색인이 **한 개** 그 자리에 있다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM pg_indexes
   WHERE tablename = 'd3_dataset_autometa' AND indexname = 'd3_dataset_autometa_search_idx';
  IF n <> 1 THEN PERFORM _t_fail(format('검색 GIN 색인이 %s 개다 (기대 1)', n)); END IF;
END $$;

-- ── B. 트리거 셋이 선다 ──────────────────────────────────────────────────
DO $$
DECLARE got text;
        want text := 'd3_dataset_autometa_pull_mirrors,d3_dataset_description_category_mirror,d3_dataset_variable_mirror';
BEGIN
  SELECT string_agg(tgname, ',' ORDER BY tgname) INTO got
    FROM pg_trigger
   WHERE NOT tgisinternal
     AND tgrelid IN ('d3_dataset_autometa'::regclass, 'd3_dataset_description'::regclass,
                     'd3_dataset_variable'::regclass);
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('미러 트리거가 %L 다 (기대 %L)', got, want));
  END IF;
END $$;

-- ── C. **동작** — 넣어 보고 그 낱말로 잡히는가 ───────────────────────────
INSERT INTO d3_dataset_description (dataset_id, lab_id, name, summary, category) VALUES
  ('000000000000000000000DSM1A', '0000000000000000000000000T', '미러 시험', '한 줄', '수문 인자');
INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name, is_representative) VALUES
  ('000000000000000000000DSM1A', '0000000000000000000000000T', 1, 'precipitation', true);
-- 메타 행은 **뒤에** 온다 — 등록 전환의 순서다. `BEFORE INSERT` 트리거가 두 사본을 채운다.
INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, file_extension, total_size_bytes) VALUES
  ('000000000000000000000DSM1A', '0000000000000000000000000T', 'netcdf', 'nc', 0);

-- C-⑴ **`nc` 로 잡힌다** — 이 회차가 닫는 R-A 이월 1건이다 (PRD-21).
DO $$
BEGIN
  IF NOT _t_hits('000000000000000000000DSM1A', 'nc') THEN
    PERFORM _t_fail('`nc` 로 안 잡힌다 — file_extension 이 색인에 안 들어갔다 (PRD-21 이월분)');
  END IF;
END $$;

-- C-⑵ **`netcdf` 는 종전과 같이 잡힌다** (회귀 — `format` 을 뺀 것이 아니다).
DO $$
BEGIN
  IF NOT _t_hits('000000000000000000000DSM1A', 'netcdf') THEN
    PERFORM _t_fail('`netcdf` 가 안 잡힌다 — 회귀다');
  END IF;
END $$;

-- C-⑶ **행 표에 넣은 변수명이 잡힌다** — `0016` 이 남긴 잔여 위험(새 행이 색인 밖)이 닫혔다.
DO $$
BEGIN
  IF NOT _t_hits('000000000000000000000DSM1A', 'precipitation') THEN
    PERFORM _t_fail('행 표에 새로 넣은 변수명이 안 잡힌다 — 미러 트리거가 안 돈다');
  END IF;
END $$;

-- C-⑷ **분류가 잡힌다** — `category` 는 다른 표에 살고 미러가 그 자리를 받는다.
DO $$
BEGIN
  IF NOT _t_hits('000000000000000000000DSM1A', '수문') THEN
    PERFORM _t_fail('분류로 안 잡힌다 — category_mirror 가 안 채워졌다');
  END IF;
END $$;

-- ── D. 미러가 **행 표와 같다** — insert · update · delete 세 갈래 ────────
INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name) VALUES
  ('000000000000000000000DSM1A', '0000000000000000000000000T', 2, 'temperature');
DO $$
DECLARE got text[];
BEGIN
  SELECT variables INTO got FROM d3_dataset_autometa WHERE dataset_id = '000000000000000000000DSM1A';
  IF got IS DISTINCT FROM ARRAY['precipitation', 'temperature'] THEN
    PERFORM _t_fail(format('INSERT 뒤 미러가 %L 다 (기대 precipitation,temperature · ordinal 순서)', got));
  END IF;
END $$;

UPDATE d3_dataset_variable SET name = 'runoff'
 WHERE dataset_id = '000000000000000000000DSM1A' AND ordinal = 2;
DO $$
DECLARE got text[];
BEGIN
  SELECT variables INTO got FROM d3_dataset_autometa WHERE dataset_id = '000000000000000000000DSM1A';
  IF got IS DISTINCT FROM ARRAY['precipitation', 'runoff'] THEN
    PERFORM _t_fail(format('UPDATE 뒤 미러가 %L 다 (기대 precipitation,runoff)', got));
  END IF;
END $$;

DELETE FROM d3_dataset_variable
 WHERE dataset_id = '000000000000000000000DSM1A' AND ordinal = 1;
DO $$
DECLARE got text[];
BEGIN
  SELECT variables INTO got FROM d3_dataset_autometa WHERE dataset_id = '000000000000000000000DSM1A';
  IF got IS DISTINCT FROM ARRAY['runoff'] THEN
    PERFORM _t_fail(format('DELETE 뒤 미러가 %L 다 (기대 runoff 하나)', got));
  END IF;
  IF _t_hits('000000000000000000000DSM1A', 'precipitation') THEN
    PERFORM _t_fail('지운 변수명이 아직 색인에 있다 — 미러가 지우기를 안 따라간다');
  END IF;
END $$;

-- D-⑷ 분류를 고쳐도 미러가 따라온다.
UPDATE d3_dataset_description SET category = '환경 인자'
 WHERE dataset_id = '000000000000000000000DSM1A';
DO $$
DECLARE got text;
BEGIN
  SELECT category_mirror INTO got FROM d3_dataset_autometa WHERE dataset_id = '000000000000000000000DSM1A';
  IF got IS DISTINCT FROM '환경 인자' THEN
    PERFORM _t_fail(format('분류 수정 뒤 미러가 %L 다 (기대 환경 인자)', got));
  END IF;
END $$;

-- ── E. 이 회차가 **안 건드린 것** ────────────────────────────────────────
-- E-⑴ `variables`·`format`·`topic` 열이 그대로 있다 (라운드 ㉴ 금지 목록).
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(want, ', ') INTO missing FROM (VALUES
      ('d3_dataset_autometa', 'variables'), ('d3_dataset_autometa', 'format'),
      ('d3_dataset_description', 'topic')) AS v(tbl, want)
   WHERE NOT EXISTS (SELECT 1 FROM information_schema.columns
                      WHERE table_name = v.tbl AND column_name = v.want);
  IF missing IS NOT NULL THEN
    PERFORM _t_fail(format('지우지 않기로 한 열이 없다: %s', missing));
  END IF;
END $$;

-- E-⑵ FORCE 가 세 표 모두 되올려져 있다 — 백필 구간의 NO FORCE 가 남아 있으면 경계가 열린다.
DO $$
DECLARE unforced text;
BEGIN
  SELECT string_agg(relname, ', ') INTO unforced FROM pg_class
   WHERE relnamespace = 'public'::regnamespace
     AND relname IN ('d3_dataset_autometa', 'd3_dataset_description', 'd3_dataset_variable')
     AND NOT relforcerowsecurity;
  IF unforced IS NOT NULL THEN
    PERFORM _t_fail(format('FORCE 가 안 켜진 표가 있다: %s', unforced));
  END IF;
END $$;

ROLLBACK;
