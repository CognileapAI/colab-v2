-- 0018 이후의 DB 가 실제로 무엇을 하는가 — Lv0 출처 두 칸 오라클 본체 (M-8 · PRD-19).
--
-- 이 파일 하나가 `0018-drift.sh` 의 세 경우 전부에서 **똑같이** 돈다.
--   · 0018 적용 후      → 전부 통과해야 한다 (green)
--   · 0017 까지만       → 반드시 실패해야 한다 (red)   ← 「되돌리면 red」
--   · 0018 downgrade 후 → 반드시 실패해야 한다 (red)
--
-- **존재 확인만 하지 않는다.** 열이 있는지만 보면 아무도 못 쓰는 열도 통과한다.
-- 그래서 값을 실제로 넣고 · 비울 수 있는지 보고 · **Lv 조건 제약이 없는지**까지 본다 —
-- 이 회차의 알맹이가 「선택 입력이고 Lv 로 갈리지 않는다」이기 때문이다.
--
-- 근거 = PRD-19 · 부록 B `M-8` · `dev-package/prd/rounds/R-B-1-db.md §2 WU-B6`

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0018 오라클 실패 — %', msg; END $$;

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
-- A. 두 칸이 **실재하고 값을 받는다** (PRD-19 「어디서 언제 받았는지를 남겨요」)
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE u text; d date;
BEGIN
  UPDATE d3_dataset
     SET source_url = 'https://cds.climate.copernicus.eu/datasets/reanalysis-era5',
         source_downloaded_on = DATE '2026-08-20'
   WHERE id = '0000000000000000000000DST1';
  SELECT source_url, source_downloaded_on INTO u, d
    FROM d3_dataset WHERE id = '0000000000000000000000DST1';
  IF u IS DISTINCT FROM 'https://cds.climate.copernicus.eu/datasets/reanalysis-era5' THEN
    PERFORM _t_fail(format('source_url 이 %L 다 — 값을 그대로 담지 못한다', u));
  END IF;
  IF d IS DISTINCT FROM DATE '2026-08-20' THEN
    PERFORM _t_fail(format('source_downloaded_on 이 %L 다 — 값을 그대로 담지 못한다', d));
  END IF;
END $$;

-- ⑵ **`source_downloaded_on` 은 `date` 다** — 「내려받은 날」은 날짜이고 시각이 아니다.
DO $$
DECLARE t text;
BEGIN
  SELECT data_type INTO t FROM information_schema.columns
   WHERE table_name = 'd3_dataset' AND column_name = 'source_downloaded_on';
  IF t IS DISTINCT FROM 'date' THEN
    PERFORM _t_fail(format('source_downloaded_on 의 타입이 %L 다 — date 여야 한다', t));
  END IF;
END $$;

-- ⑶ **`source_url` 은 text 다** — 길이 상한을 걸지 않았다(주소는 길다).
DO $$
DECLARE t text;
BEGIN
  SELECT data_type INTO t FROM information_schema.columns
   WHERE table_name = 'd3_dataset' AND column_name = 'source_url';
  IF t IS DISTINCT FROM 'text' THEN
    PERFORM _t_fail(format('source_url 의 타입이 %L 다 — text 여야 한다', t));
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- B. **선택 입력이다** — 비울 수 있고, 한쪽만 채워도 된다 (PRD-19 「비어도 등록된다」)
-- ════════════════════════════════════════════════════════════════════════════
-- ⑴ 둘 다 NULL 로 비울 수 있다. NOT NULL 로 조였으면 여기서 걸린다.
DO $$
BEGIN
  UPDATE d3_dataset SET source_url = NULL, source_downloaded_on = NULL
   WHERE id = '0000000000000000000000DST1';
EXCEPTION WHEN others THEN
  PERFORM _t_fail('두 칸을 비울 수 없다 — 선택 입력이 아니게 조였다(등록이 막힌다)');
END $$;

-- ⑵ **반쪽도 정상이다** — pdf 축자가 「출처**나** URL」로 택일까지 적었다.
--    쌍 CHECK(관측 간격 `M-6` 같은 모양)를 여기 걸면 그 문면이 깨진다.
DO $$
BEGIN
  UPDATE d3_dataset SET source_url = 'https://example.org/a', source_downloaded_on = NULL
   WHERE id = '0000000000000000000000DST1';
  UPDATE d3_dataset SET source_url = NULL, source_downloaded_on = DATE '2026-08-20'
   WHERE id = '0000000000000000000000DST1';
EXCEPTION WHEN others THEN
  PERFORM _t_fail('한 칸만 채우는 것이 막혔다 — 두 칸에 쌍 CHECK 를 걸었다(PRD-19 반증)');
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- C. **Lv 로 갈리지 않는다** — 이 회차의 알맹이 (⛔ 폐기된 판정의 회귀 방지)
-- ════════════════════════════════════════════════════════════════════════════
-- ⑴ `Lv1` 이상에서 값을 실어도 DB 가 거절하지 않는다.
--    종전 완료 판정(「Lv1 이상 값 전송 시 400」)은 폐기됐다(PRD-19 · 미결-11 ⓐ).
DO $$
DECLARE v text;
BEGIN
  FOREACH v IN ARRAY ARRAY['Lv0', 'Lv1', 'Lv2', 'Lv3'] LOOP
    UPDATE d3_dataset
       SET processing_level_user_set = v,
           source_url = 'https://example.org/' || v,
           source_downloaded_on = DATE '2026-08-20'
     WHERE id = '0000000000000000000000DST1';
  END LOOP;
EXCEPTION WHEN others THEN
  PERFORM _t_fail('Lv 와 출처 두 칸의 조합이 막혔다 — Lv 조건 제약을 만들면 안 된다');
END $$;

-- ⑵ `Lv0` 인데 두 칸이 비어도 DB 가 막지 않는다 (「Lv0 이면 두 칸 필수」도 폐기됐다).
DO $$
BEGIN
  UPDATE d3_dataset
     SET processing_level_user_set = 'Lv0', source_url = NULL, source_downloaded_on = NULL
   WHERE id = '0000000000000000000000DST1';
EXCEPTION WHEN others THEN
  PERFORM _t_fail('Lv0 ∧ 두 칸 빔이 막혔다 — 필수 검사를 DB 에 걸었다(폐기된 판정)');
END $$;

-- ⑶ **두 열에 CHECK 제약이 하나도 없다.** 위 ⑴⑵ 는 「지금 막히지 않는다」를 보고,
--    이 단언은 「막을 장치 자체가 없다」를 본다 — 조건부 CHECK 는 특정 값에서만 걸린다.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY (c.conkey)
   WHERE c.conrelid = 'd3_dataset'::regclass AND c.contype = 'c'
     AND a.attname IN ('source_url', 'source_downloaded_on');
  IF n <> 0 THEN
    PERFORM _t_fail(format('출처 두 칸에 CHECK 가 %s 건 걸려 있다 — 선택 입력이 아니다', n));
  END IF;
END $$;

-- ⑷ 두 열이 **NOT NULL 이 아니다**.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_name = 'd3_dataset'
     AND column_name IN ('source_url', 'source_downloaded_on')
     AND is_nullable = 'NO';
  IF n <> 0 THEN
    PERFORM _t_fail(format('출처 두 칸 중 %s 개가 NOT NULL 이다 — 비운 채 등록이 막힌다', n));
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- D. **`source_label` 을 건드리지 않았다** — 원천 표기는 Lv 무관 상시 노출 (미결-11 ⓐ)
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE l text;
BEGIN
  SELECT source_label INTO l FROM d3_dataset WHERE id = '0000000000000000000000DST1';
  IF l IS DISTINCT FROM '기상청 GK2A' THEN
    PERFORM _t_fail(format('source_label 이 %L 다 — 두 칸을 세우면서 원천 표기를 건드렸다', l));
  END IF;
END $$;

-- ⑵ 정규화 열과 **자동완성 색인이 그대로 있다**. 그 색인이 사라지면 자동완성이 전체 스캔이 된다.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM pg_indexes
   WHERE tablename = 'd3_dataset' AND indexname = 'd3_dataset_source_label_normalized_idx';
  IF n <> 1 THEN
    PERFORM _t_fail('d3_dataset_source_label_normalized_idx 가 없다 — 자동완성 색인을 건드렸다');
  END IF;
END $$;

-- ⑶ 검색 색인은 **종전 그대로**다 — `source_label` 이 B 가중치로 계속 물린다.
DO $$
DECLARE v tsvector;
BEGIN
  SELECT search_vector INTO v FROM d3_dataset WHERE id = '0000000000000000000000DST1';
  IF NOT (v @@ to_tsquery('simple', '기상청')) THEN
    PERFORM _t_fail('종전 검색(원천 표기 `기상청`)이 깨졌다 — 0018 이 색인식을 건드렸다');
  END IF;
END $$;

-- ⑷ **두 칸이 검색 색인에 들어가지 않았다.** 주소는 검색어가 아니다 — 색인 재정의는
--    `M-10`(R-B-2) 소유이고 여기서 앞당기지 않았음을 이 단언이 붙잡는다.
DO $$
DECLARE d text;
BEGIN
  SELECT pg_get_expr(d.adbin, d.adrelid) INTO d FROM pg_attrdef d
    JOIN pg_attribute a ON a.attrelid = d.adrelid AND a.attnum = d.adnum
   WHERE d.adrelid = 'd3_dataset'::regclass AND a.attname = 'search_vector';
  IF d IS NOT NULL AND (d LIKE '%source_url%' OR d LIKE '%source_downloaded_on%') THEN
    PERFORM _t_fail('search_vector 가 출처 두 칸을 물었다 — 색인 재정의는 M-10 소유다');
  END IF;
END $$;

ROLLBACK;
