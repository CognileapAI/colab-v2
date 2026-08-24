-- 0005 이후의 DB 가 실제로 무엇을 하는가 — 검색 인프라 오라클 본체.
--
-- 이 파일 하나가 `0005-drift.sh` 의 세 경우 전부에서 **똑같이** 돈다.
--   · 0005 적용 후      → 전부 통과해야 한다 (green)
--   · 0004 까지만       → 반드시 실패해야 한다 (red)   ← 「되돌리면 red」의 실물
--   · 0005 downgrade 후 → 반드시 실패해야 한다 (red)
--
-- **존재 확인만 하지 않는다.** 열이 있는지·인덱스가 있는지만 보면
--   ① 값이 안 채워지는 죽은 열도 통과하고
--   ② 질의가 절대 타지 않는 인덱스도 통과한다.
-- 그래서 여기서는 **행을 실제로 넣고 매칭시키고 · UPDATE 로 갱신을 확인하고 ·
-- EXPLAIN 으로 GIN 인덱스가 실제로 잡히는지**까지 본다.
--
-- 근거 = PLAN-SoT §9 〈72〉(매칭·순위는 tsvector + 사전 3종) · S1-PLAN §4.3 K4-infra
--
-- ⚠ `ts_config` 는 `'simple'` 고정이다. 이것은 **`[정본 무근거]`** 이고 값이 바뀌면
--    이 오라클의 D 절(형태소 기대)이 함께 바뀌어야 한다. 지금 이 파일은
--    **`simple` 이 실제로 무엇을 하는지**를 시험이 말하게 둔다.

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0005 오라클 실패 — %', msg; END $$;

-- ── 재료 ────────────────────────────────────────────────────────────────────
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_lab_profile (lab_id, university, department, principal_investigator,
                            research_field, introduction, default_visibility) VALUES
  ('0000000000000000000000000T', 'T 대', 'T 과', 'T 교수', '수문학', 'T', '열림');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id, source_label,
                        uploaded_at, last_modified_at) VALUES
  ('0000000000000000000000DST1', '0000000000000000000000000T', '00000000000000000000000TP1',
   '00000000000000000000000TP1', '기상청 GK2A',
   '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
INSERT INTO d3_dataset_description (dataset_id, lab_id, name, topic, summary) VALUES
  ('0000000000000000000000DST1', '0000000000000000000000000T',
   '한강 유역 강수량', '강우·강수', '2020년 여름 한강 유역 레이더 강수 자료');
INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, variables, crs, grid, bundle_file_name) VALUES
  ('0000000000000000000000DST1', '0000000000000000000000000T',
   'NetCDF', ARRAY['Precipitation', 'LST_Day'], 'EPSG:5179', '2048x2048', 'GK2A_LE1B');

-- ════════════════════════════════════════════════════════════════════════════
-- A. 세 검색 열이 실재하고 **생성 열**이다 (손으로 채우는 열이 아니다)
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n
    FROM pg_attribute a
    JOIN pg_class c ON c.oid = a.attrelid
   WHERE c.relname IN ('d3_dataset', 'd3_dataset_description', 'd3_dataset_autometa')
     AND a.attname = 'search_vector'
     AND a.atttypid = 'tsvector'::regtype
     AND a.attgenerated = 's';
  IF n <> 3 THEN
    PERFORM _t_fail(format('STORED 생성 tsvector 열 search_vector 이 %s/3 개다 — 0005 가 적용되지 않았다', n));
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- B. GIN 인덱스 3개가 그 열 위에 실재한다
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n
    FROM pg_index i
    JOIN pg_class ic ON ic.oid = i.indexrelid
    JOIN pg_class tc ON tc.oid = i.indrelid
    JOIN pg_am am    ON am.oid = ic.relam
   WHERE am.amname = 'gin'
     AND tc.relname IN ('d3_dataset', 'd3_dataset_description', 'd3_dataset_autometa')
     AND ic.relname LIKE '%search%';
  IF n <> 3 THEN
    PERFORM _t_fail(format('검색 열 위의 GIN 인덱스가 %s/3 개다', n));
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- C. 열이 **살아 있다** — 값이 채워지고, 원본이 바뀌면 따라 바뀐다
-- ════════════════════════════════════════════════════════════════════════════

-- ⑴ 사람이 적은 말이 잡힌다 (이름 · 주제 · 요약)
DO $$
DECLARE v tsvector;
BEGIN
  SELECT search_vector INTO v FROM d3_dataset_description WHERE dataset_id = '0000000000000000000000DST1';
  IF v IS NULL OR v = ''::tsvector THEN PERFORM _t_fail('d3_dataset_description.search_vector 가 비었다 — 죽은 열이다'); END IF;
  IF NOT (v @@ to_tsquery('simple', '한강'))    THEN PERFORM _t_fail('이름(name)의 낱말이 안 잡힌다'); END IF;
  IF NOT (v @@ to_tsquery('simple', '레이더'))  THEN PERFORM _t_fail('요약(summary)의 낱말이 안 잡힌다'); END IF;
  IF NOT (v @@ to_tsquery('simple', '강우'))    THEN PERFORM _t_fail('주제(topic)의 낱말이 안 잡힌다'); END IF;
END $$;

-- ⑵ 가중치가 실제로 다르다 — 이름이 요약보다 위다 (K4-a 의 순위 근거)
DO $$
DECLARE v tsvector;
BEGIN
  SELECT search_vector INTO v FROM d3_dataset_description WHERE dataset_id = '0000000000000000000000DST1';
  IF ts_rank(v, to_tsquery('simple', '한강')) <= ts_rank(v, to_tsquery('simple', '레이더')) THEN
    PERFORM _t_fail('이름의 가중치가 요약보다 높지 않다 — setweight 이 안 걸렸다');
  END IF;
END $$;

-- ⑶ 자동 정보가 잡힌다. **배열(variables)이 소문자로 정규화돼 들어가는지**가 핵심이다 —
--    array_to_tsvector 는 대소문자를 그대로 둬서 to_tsquery 와 절대 안 만난다(실측).
DO $$
DECLARE v tsvector;
BEGIN
  SELECT search_vector INTO v FROM d3_dataset_autometa WHERE dataset_id = '0000000000000000000000DST1';
  IF NOT (v @@ to_tsquery('simple', 'netcdf'))       THEN PERFORM _t_fail('format 이 안 잡힌다'); END IF;
  IF NOT (v @@ to_tsquery('simple', 'precipitation')) THEN PERFORM _t_fail('variables 배열 원소가 소문자로 안 잡힌다 — 배열 결합이 틀렸다'); END IF;
  IF NOT (v @@ to_tsquery('simple', 'lst_day'))      THEN PERFORM _t_fail('variables 두 번째 원소가 안 잡힌다'); END IF;
  IF NOT (v @@ to_tsquery('simple', 'gk2a_le1b'))    THEN PERFORM _t_fail('bundle_file_name 이 안 잡힌다'); END IF;
END $$;

-- ⑷ 원천 표기가 잡힌다
DO $$
DECLARE v tsvector;
BEGIN
  SELECT search_vector INTO v FROM d3_dataset WHERE id = '0000000000000000000000DST1';
  IF NOT (v @@ to_tsquery('simple', '기상청')) THEN PERFORM _t_fail('d3_dataset.source_label 이 안 잡힌다'); END IF;
END $$;

-- ⑸ **갱신된다.** 생성 열이 아니라 한 번 구운 값이면 여기서 걸린다.
DO $$
DECLARE v tsvector;
BEGIN
  UPDATE d3_dataset_description SET name = '낙동강 유역 유출량'
   WHERE dataset_id = '0000000000000000000000DST1';
  SELECT search_vector INTO v FROM d3_dataset_description WHERE dataset_id = '0000000000000000000000DST1';
  -- ⚠ 「한강」으로 재지 않는다 — 요약에도 들어 있어 이름이 안 바뀌어도 계속 잡힌다.
  --    실제로 이 시험을 그렇게 썼다가 걸렸다. **이름에만 있는 낱말**로 잰다.
  IF v @@ to_tsquery('simple', '강수량') THEN PERFORM _t_fail('이름을 바꿨는데 옛 낱말이 남아 있다 — 열이 갱신되지 않는다'); END IF;
  IF NOT (v @@ to_tsquery('simple', '유출량')) THEN PERFORM _t_fail('바뀐 이름이 안 들어갔다'); END IF;
  UPDATE d3_dataset_description SET name = '한강 유역 강수량'
   WHERE dataset_id = '0000000000000000000000DST1';
END $$;

-- ⑹ 손으로 못 쓴다 — 생성 열이므로 INSERT/UPDATE 대상이 아니다.
DO $$
BEGIN
  BEGIN
    EXECUTE $q$UPDATE d3_dataset_description SET search_vector = ''::tsvector$q$;
  EXCEPTION WHEN others THEN RETURN;   -- 기대대로 거절
  END;
  PERFORM _t_fail('생성 열 search_vector 를 손으로 덮어썼다 — 생성 열이 아니다');
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- D. `simple` 이 무엇을 하는지 시험이 말한다 — `[정본 무근거]` 의 대가를 기록한다
--    한국어 형태소 분석이 없으므로 「기상청」은 통째로 한 낱말이고 「기상」은 그것을 못 만난다.
--    ⚠ `d3_dataset.search_vector`(원천 표기 한 칸)로 잰다 — 이름·주제·요약이 섞인
--       벡터로 재면 **다른 칸에 우연히 들어 있는 같은 낱말**이 판정을 가린다.
--       실제로 그렇게 썼다가 「강수」가 요약의 독립 낱말로 잡혀 거짓 red 가 났다.
--    ts_config 가 바뀌면 이 절이 함께 바뀐다. 조용히 바뀌지 않게 시험이 붙잡는다.
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE v tsvector;
BEGIN
  SELECT search_vector INTO v FROM d3_dataset WHERE id = '0000000000000000000000DST1';
  IF NOT (v @@ to_tsquery('simple', '기상청')) THEN PERFORM _t_fail('「기상청」 전체 일치조차 안 된다'); END IF;
  IF v @@ to_tsquery('simple', '기상') THEN
    PERFORM _t_fail('「기상」이 「기상청」을 잡았다 — ts_config 가 simple 이 아니다. 이 시험을 정본과 함께 고쳐라');
  END IF;
  -- 접두 일치는 된다 — K4-a 가 부분어를 다룰 실제 수단이 이것이다.
  IF NOT (v @@ to_tsquery('simple', '기상:*')) THEN PERFORM _t_fail('접두 일치(기상:*)조차 안 된다'); END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- E. GIN 인덱스가 **실제로 잡힌다** — 있는데 안 타는 인덱스를 green 으로 세지 않는다
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE plan text := ''; line text;
BEGIN
  SET LOCAL enable_seqscan = off;
  FOR line IN EXECUTE $q$
    EXPLAIN (COSTS OFF, FORMAT TEXT)
    SELECT dataset_id FROM d3_dataset_description
     WHERE search_vector @@ to_tsquery('simple', '한강')
  $q$ LOOP
    plan := plan || line || E'\n';
  END LOOP;
  IF plan NOT ILIKE '%Bitmap Index Scan%' AND plan NOT ILIKE '%Index Scan%' THEN
    PERFORM _t_fail('검색 질의가 인덱스를 타지 않는다: ' || plan);
  END IF;
END $$;

ROLLBACK;
