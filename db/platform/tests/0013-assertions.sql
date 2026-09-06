-- 0013 이후의 DB 가 실제로 무엇을 하는가 — 확장자 열 오라클 본체 (M-9 · PRD-21).
--
-- 이 파일 하나가 `0013-drift.sh` 의 세 경우 전부에서 **똑같이** 돈다.
--   · 0013 적용 후      → 전부 통과해야 한다 (green)
--   · 0011 까지만       → 반드시 실패해야 한다 (red)   ← 「되돌리면 red」
--   · 0013 downgrade 후 → 반드시 실패해야 한다 (red)
--
-- **존재 확인만 하지 않는다.** 열이 있는지만 보면 아무도 못 쓰는 열도 통과한다.
-- 그래서 행을 실제로 넣고 · 읽고 · `format` 이 여전히 살아 있는지까지 본다.
--
-- 근거 = PRD-21 · 부록 B `M-9` · `dev-package/prd/rounds/R-A-1-db.md §2`

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0013 오라클 실패 — %', msg; END $$;

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
   '한강 유역 강수량', '강우·강수', '레이더 강수 자료');

-- ════════════════════════════════════════════════════════════════════════════
-- A. 열이 실재하고 **값을 받는다** — nullable text 다
-- ════════════════════════════════════════════════════════════════════════════
INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, file_extension) VALUES
  ('0000000000000000000000DST1', '0000000000000000000000000T', 'NetCDF-4', 'nc');

DO $$
DECLARE ext text;
BEGIN
  SELECT file_extension INTO ext
    FROM d3_dataset_autometa WHERE dataset_id = '0000000000000000000000DST1';
  IF ext IS DISTINCT FROM 'nc' THEN
    PERFORM _t_fail(format('file_extension 이 %L 다 — 값을 그대로 담지 못한다', ext));
  END IF;
END $$;

-- ⑵ **NULL 이 허용된다** — 확장자를 못 뽑은 행은 「모른다」이고, 화면이 `format` 으로 퇴행한다.
--    NOT NULL 로 조이면 기존 행의 재선택을 강제하게 된다 (미결-5 와 같은 종류의 실패).
DO $$
BEGIN
  UPDATE d3_dataset_autometa SET file_extension = NULL
   WHERE dataset_id = '0000000000000000000000DST1';
EXCEPTION WHEN others THEN
  PERFORM _t_fail('file_extension 을 NULL 로 비울 수 없다 — 「모른다」를 표현할 자리가 없다');
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- B. `format` 을 **지우지 않았다** — 판별 결과는 파이프라인·미리보기가 계속 쓰고,
--    확장자가 없는 행의 퇴행 표시이며, 검색 색인이 아직 이 열을 문다 (R-A 는 M-10 을 안 돈다)
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_name = 'd3_dataset_autometa' AND column_name IN ('format', 'variables');
  IF n <> 2 THEN
    PERFORM _t_fail(format('format·variables 중 %s/2 개만 남았다 — 되돌림 경로를 지웠다', n));
  END IF;
END $$;

-- ⑵ 검색은 **종전대로 `format` 으로** 잡힌다. 「`nc` 로도 찾는다」는 R-B 의 `M-10` 이다 —
--    여기서 색인식을 손대지 않았음을 이 단언이 붙잡는다.
DO $$
DECLARE v tsvector;
BEGIN
  UPDATE d3_dataset_autometa SET format = 'netcdf', file_extension = 'nc'
   WHERE dataset_id = '0000000000000000000000DST1';
  SELECT search_vector INTO v FROM d3_dataset_autometa
   WHERE dataset_id = '0000000000000000000000DST1';
  IF NOT (v @@ to_tsquery('simple', 'netcdf')) THEN
    PERFORM _t_fail('종전 검색(`netcdf`)이 깨졌다 — R-A 가 색인을 건드렸다');
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- C. `M-6` — 관측 간격 **두 칸**이 사람이 적는 표에 있고, CHECK 둘이 실제로 문다
--    (PRD-17 · 미결-4 ⓐ). **존재 확인만 하지 않는다** — 반쪽 값을 실제로 밀어 본다.
-- ════════════════════════════════════════════════════════════════════════════
-- ⑴ 단위 `분` ＋ 값 `10` 이 그대로 담기고 그대로 읽힌다.
DO $$
DECLARE v numeric; u text;
BEGIN
  UPDATE d3_dataset_description
     SET observation_interval_value = 10, observation_interval_unit = '분'
   WHERE dataset_id = '0000000000000000000000DST1';
  SELECT observation_interval_value, observation_interval_unit INTO v, u
    FROM d3_dataset_description WHERE dataset_id = '0000000000000000000000DST1';
  IF v IS DISTINCT FROM 10 OR u IS DISTINCT FROM '분' THEN
    PERFORM _t_fail(format('관측 간격이 (%s, %L) 로 담겼다 — 두 칸이 값을 그대로 못 받는다', v, u));
  END IF;
END $$;

-- ⑵ **반쪽은 못 들어간다** — 숫자만 채우면 pair CHECK 가 막는다.
--    막지 못하면 `10` 인지 `10분` 인지 아무도 모르는 행이 남는다.
DO $$
BEGIN
  UPDATE d3_dataset_description
     SET observation_interval_value = 10, observation_interval_unit = NULL
   WHERE dataset_id = '0000000000000000000000DST1';
  PERFORM _t_fail('숫자만 채운 반쪽 관측 간격이 저장됐다 — 둘 다 NULL 이거나 둘 다 값 CHECK 가 없다');
EXCEPTION WHEN check_violation THEN
  NULL;  -- 기대한 거절
END $$;

-- ⑵-b 단위만 채운 반대쪽도 같다.
DO $$
BEGIN
  UPDATE d3_dataset_description
     SET observation_interval_value = NULL, observation_interval_unit = '분'
   WHERE dataset_id = '0000000000000000000000DST1';
  PERFORM _t_fail('단위만 채운 반쪽 관측 간격이 저장됐다 — pair CHECK 가 한쪽만 본다');
EXCEPTION WHEN check_violation THEN
  NULL;
END $$;

-- ⑶ 단위는 **6값 밖을 거절한다**. 안 막으면 사용자의 오타가 화면에 그대로 그려진다.
DO $$
BEGIN
  UPDATE d3_dataset_description
     SET observation_interval_value = 10, observation_interval_unit = 'minute'
   WHERE dataset_id = '0000000000000000000000DST1';
  PERFORM _t_fail('단위 6값 밖(`minute`)이 저장됐다 — unit CHECK 가 없다');
EXCEPTION WHEN check_violation THEN
  NULL;
END $$;

-- ⑷ 6값이 **전부** 통과한다. 한 값이라도 빠지면 화면 셀렉트와 DB 가 갈린다.
DO $$
DECLARE u text;
BEGIN
  FOREACH u IN ARRAY ARRAY['초', '분', '시', '일', '월', '년'] LOOP
    UPDATE d3_dataset_description
       SET observation_interval_value = 1, observation_interval_unit = u
     WHERE dataset_id = '0000000000000000000000DST1';
  END LOOP;
END $$;

-- ⑸ **둘 다 NULL 로 비울 수 있다** — 선택 입력이고 전 행 NULL 이 정상 상태다.
DO $$
BEGIN
  UPDATE d3_dataset_description
     SET observation_interval_value = NULL, observation_interval_unit = NULL
   WHERE dataset_id = '0000000000000000000000DST1';
EXCEPTION WHEN others THEN
  PERFORM _t_fail('관측 간격을 비울 수 없다 — NOT NULL 로 조였다(선택 입력이어야 한다)');
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- D. `M-7` — 기간의 최소 단위 (PRD-18 · 미결-18 ⓐ)
-- ════════════════════════════════════════════════════════════════════════════
-- ⑴ 6값이 담기고, ⑵ 밖은 거절되고, ⑶ NULL 이 「단위 미지정」으로 남는다.
DO $$
DECLARE g text;
BEGIN
  FOREACH g IN ARRAY ARRAY['년', '월', '일', '시', '분', '초'] LOOP
    UPDATE d3_dataset_autometa SET period_granularity = g
     WHERE dataset_id = '0000000000000000000000DST1';
  END LOOP;
  SELECT period_granularity INTO g FROM d3_dataset_autometa
   WHERE dataset_id = '0000000000000000000000DST1';
  IF g IS DISTINCT FROM '초' THEN
    PERFORM _t_fail(format('period_granularity 가 %L 다 — 값을 그대로 담지 못한다', g));
  END IF;
END $$;

DO $$
BEGIN
  UPDATE d3_dataset_autometa SET period_granularity = 'day'
   WHERE dataset_id = '0000000000000000000000DST1';
  PERFORM _t_fail('period_granularity 6값 밖(`day`)이 저장됐다 — CHECK 가 없다');
EXCEPTION WHEN check_violation THEN
  NULL;
END $$;

DO $$
BEGIN
  UPDATE d3_dataset_autometa SET period_granularity = NULL
   WHERE dataset_id = '0000000000000000000000DST1';
EXCEPTION WHEN others THEN
  PERFORM _t_fail('period_granularity 를 비울 수 없다 — 「단위 미지정」을 표현할 자리가 없다');
END $$;

-- ⑷ **기간 두 칸은 그대로다** — 시각값 저장을 바꾸지 않았다(미결-18 ⓐ).
--    최소 단위를 더하면서 `timestamptz` 를 문자열로 갈아치우면 이 단언이 red 다.
DO $$
DECLARE t text;
BEGIN
  SELECT string_agg(data_type, ',' ORDER BY column_name) INTO t
    FROM information_schema.columns
   WHERE table_name = 'd3_dataset_autometa'
     AND column_name IN ('period_start', 'period_end');
  IF t IS DISTINCT FROM 'timestamp with time zone,timestamp with time zone' THEN
    PERFORM _t_fail(format('기간 두 칸의 타입이 %L 다 — 시각값 저장을 바꿨다', t));
  END IF;
END $$;

ROLLBACK;
