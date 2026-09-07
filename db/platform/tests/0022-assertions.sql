-- 0022 오라클 — **미러 트리거가 문장 단위이고, 미러 값이 종전과 같다**.
--
-- 수용 기준 축자 (`R-C-1-contract-db.md §2` WU-C7) — 「N행 `replace_variables` 에
-- 트리거 실행 **1회**」. DB 쪽이 지는 몫은 **문장 단위라는 사실**이고, 「INSERT 를 한 문장으로
-- 보낸다」는 서버 쪽 몫이라 `services/core-api/tests/test_variable_rows.py` 가 잰다.
--
-- ⭑ **정의문만 보지 않는다** — 트리거는 텍스트가 아니라 **미러를 맞추는 동작**이다.
--    그래서 아래는 「다중 행으로 넣고 그 배열이 맞는가」로도 잰다(회귀).
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0022 오라클 실패 — %', msg; END $$;

-- ── A. 트리거 셋이 **문장 단위**로 서 있고, 행 단위 한 벌은 없다 ───────────
DO $$
DECLARE got text;
        want text := 'd3_dataset_variable_mirror_del,d3_dataset_variable_mirror_ins,d3_dataset_variable_mirror_upd';
BEGIN
  SELECT string_agg(tgname, ',' ORDER BY tgname) INTO got
    FROM pg_trigger WHERE NOT tgisinternal AND tgrelid = 'd3_dataset_variable'::regclass;
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('변수 표의 트리거가 %L 다 (기대 %L) — 행 단위 한 벌이 남았거나 이름이 갈렸다', got, want));
  END IF;
END $$;

-- A-⑵ 셋 다 `FOR EACH STATEMENT` 이고 **전이 표**를 갖는다. 하나라도 행 단위면 N+1 이 남는다.
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT tgname, pg_get_triggerdef(oid) AS def
             FROM pg_trigger WHERE NOT tgisinternal AND tgrelid = 'd3_dataset_variable'::regclass
  LOOP
    IF position('FOR EACH STATEMENT' in r.def) = 0 THEN
      PERFORM _t_fail(format('%s 가 문장 단위가 아니다: %L', r.tgname, r.def));
    END IF;
    IF position('REFERENCING' in r.def) = 0 THEN
      PERFORM _t_fail(format('%s 에 전이 표가 없다 — 어느 행이 바뀌었는지 모른다: %L', r.tgname, r.def));
    END IF;
  END LOOP;
END $$;

-- A-⑶ **다른 두 미러 트리거는 안 건드렸다** (라운드 ㉴ · 이 회차의 범위 밖).
DO $$
DECLARE got text;
        want text := 'd3_dataset_autometa_pull_mirrors,d3_dataset_description_category_mirror';
BEGIN
  SELECT string_agg(tgname, ',' ORDER BY tgname) INTO got
    FROM pg_trigger WHERE NOT tgisinternal
      AND tgrelid IN ('d3_dataset_autometa'::regclass, 'd3_dataset_description'::regclass);
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('형제 미러 트리거가 %L 다 (기대 %L)', got, want));
  END IF;
END $$;

-- ── B. **동작** — 미러가 종전과 같은 값이 되는가 (회귀) ────────────────────
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                        uploaded_at, last_modified_at) VALUES
  ('00000000000000000000000DS1', '0000000000000000000000000T', '00000000000000000000000TP1',
   '00000000000000000000000TP1', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
SET app.current_lab = '0000000000000000000000000T';
INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, total_size_bytes) VALUES
  ('00000000000000000000000DS1', '0000000000000000000000000T', 'netcdf', 0);

CREATE FUNCTION _t_mirror() RETURNS text[] LANGUAGE sql STABLE AS $$
  SELECT variables FROM d3_dataset_autometa WHERE dataset_id = '00000000000000000000000DS1'
$$;

-- B-⑴ **한 문장에 3행** — 문장 단위 트리거가 셋을 다 본다(전이 표를 안 쓰면 마지막 하나만 본다).
INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name, is_representative) VALUES
  ('00000000000000000000000DS1', '0000000000000000000000000T', 1, 'precipitation', true),
  ('00000000000000000000000DS1', '0000000000000000000000000T', 2, 'temperature', false),
  ('00000000000000000000000DS1', '0000000000000000000000000T', 3, 'runoff', false);
DO $$
BEGIN
  IF _t_mirror() IS DISTINCT FROM ARRAY['precipitation','temperature','runoff'] THEN
    PERFORM _t_fail(format('다중 행 INSERT 뒤 미러가 %L 다 (기대 3개 · ordinal 순서)', _t_mirror()));
  END IF;
END $$;

-- B-⑵ UPDATE 한 문장에 여러 행.
UPDATE d3_dataset_variable SET name = name || '_x'
 WHERE dataset_id = '00000000000000000000000DS1' AND ordinal IN (2, 3);
DO $$
BEGIN
  IF _t_mirror() IS DISTINCT FROM ARRAY['precipitation','temperature_x','runoff_x'] THEN
    PERFORM _t_fail(format('다중 행 UPDATE 뒤 미러가 %L 다', _t_mirror()));
  END IF;
END $$;

-- B-⑶ DELETE 한 문장에 여러 행 — 0행이 되면 **빈 배열**이다(NULL 이 아니다).
DELETE FROM d3_dataset_variable WHERE dataset_id = '00000000000000000000000DS1';
DO $$
BEGIN
  IF _t_mirror() IS DISTINCT FROM '{}'::text[] THEN
    PERFORM _t_fail(format('전부 지운 뒤 미러가 %L 다 (기대 빈 배열)', _t_mirror()));
  END IF;
END $$;

ROLLBACK;
