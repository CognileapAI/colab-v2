-- 0006 이후의 DB 가 실제로 무엇을 하는가 — 한국어 매칭 보강 오라클 본체.
--
-- 이 파일 하나가 `0006-drift.sh` 의 세 경우 전부에서 **똑같이** 돈다.
--   · 0006 적용 후      → 전부 통과해야 한다 (green)
--   · 0005 까지만       → 반드시 실패해야 한다 (red)   ← 「되돌리면 red」의 실물
--   · 0006 downgrade 후 → 반드시 실패해야 한다 (red)
--
-- **존재 확인만 하지 않는다** (`0005-assertions.sql` 과 같은 규율). 확장이 설치됐는지,
-- 인덱스가 있는지만 보면 **아무도 안 쓰는 확장**도 통과한다. 그래서 여기서는
-- 행을 실제로 넣고 · 유사도를 재고 · 접두 질의가 실제로 더 잡는지까지 본다.
--
-- 근거 = PLAN-SoT §9 〈89〉(접두 질의 + pg_trgm · 순위 결정성 보존)

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0006 오라클 실패 — %', msg; END $$;

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

-- ════════════════════════════════════════════════════════════════════════════
-- A. 확장이 실재한다
-- ════════════════════════════════════════════════════════════════════════════
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm') THEN
    PERFORM _t_fail('pg_trgm 확장이 없다 — 0006 이 적용되지 않았다');
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- B. 이름 위의 **삼중자 GIN 인덱스**가 실재한다 (tsvector 인덱스와 다른 물건이다)
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n
    FROM pg_index i
    JOIN pg_class ic  ON ic.oid = i.indexrelid
    JOIN pg_class tc  ON tc.oid = i.indrelid
    JOIN pg_am am     ON am.oid = ic.relam
    JOIN pg_opclass oc ON oc.oid = i.indclass[0]
   WHERE am.amname = 'gin'
     AND tc.relname = 'd3_dataset_description'
     AND oc.opcname = 'gin_trgm_ops';
  IF n <> 1 THEN
    PERFORM _t_fail(format('이름 위의 gin_trgm_ops 인덱스가 %s/1 개다', n));
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- C. 확장이 **일한다** — 유사도가 실제로 값을 낸다
-- ════════════════════════════════════════════════════════════════════════════

-- ⑴ **한 글자 틀린 질의**가 이름과 닮았다고 판정된다. 이것이 보조 팔이 사는 자리다.
--    ⚠ 실측 — 띄어쓰기를 **전부** 지운 「한강유역강수량」은 0.286 으로 문턱 아래다.
--    낮춰서 통과시키지 않는다. 그 사실은 한계로 남기고 시험이 아래 ⑵ 로 붙잡는다.
DO $$
DECLARE s real;
BEGIN
  SELECT similarity(name, '한강 유억 강수량') INTO s
    FROM d3_dataset_description WHERE dataset_id = '0000000000000000000000DST1';
  IF s IS NULL OR s < 0.3 THEN
    PERFORM _t_fail(format('한 글자 틀린 질의의 유사도가 %s 다 — 문턱 0.3 아래면 못 잡는다', s));
  END IF;
END $$;

-- ⑵ **아무 말이나 닮았다고 하지 않는다.** 문턱이 의미를 가지려면 이쪽도 참이어야 한다.
DO $$
DECLARE s real;
BEGIN
  SELECT similarity(name, '토지피복분류') INTO s
    FROM d3_dataset_description WHERE dataset_id = '0000000000000000000000DST1';
  IF s >= 0.3 THEN
    PERFORM _t_fail(format('상관없는 말의 유사도가 %s 다 — 문턱이 아무것도 안 거른다', s));
  END IF;
END $$;

-- ⑶ 인덱스가 실제로 잡힌다 — **있는데 절대 안 타는 인덱스**를 통과시키지 않는다.
DO $$
DECLARE plan text := '';
        r record;
BEGIN
  SET LOCAL enable_seqscan = off;
  FOR r IN EXPLAIN SELECT dataset_id FROM d3_dataset_description
                    WHERE name % '한강유역강수량'
  LOOP
    plan := plan || r."QUERY PLAN" || E'\n';
  END LOOP;
  IF plan NOT LIKE '%d3_dataset_description_name_trgm_idx%' THEN
    PERFORM _t_fail('유사도 질의가 삼중자 인덱스를 안 탄다: ' || plan);
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- D. **접두 질의가 실제로 더 잡는다** — `〈89〉-㉮①` 이 푼 한계
--
-- ⚠ 접두 질의 자체는 마이그레이션이 아니라 실행기의 규칙이다. 그래도 여기서 재는 이유는
--    `0006` 이 없는 DB 에서 이 오라클이 red 를 내야 하기 때문이 아니라(A·B·C 가 그 일을
--    한다), **개정된 매칭 규칙이 이 스키마 위에서 성립한다**를 한 자리에서 보이기 위해서다.
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE v tsvector;
BEGIN
  SELECT search_vector INTO v FROM d3_dataset_description
   WHERE dataset_id = '0000000000000000000000DST1';
  -- 「레이」를 쓴다. 「강수」는 요약에 통짜로 들어 있어 접두의 효과를 못 가른다 (실측).
  IF v @@ to_tsquery('simple', '레이') THEN
    PERFORM _t_fail('「레이」가 통짜 질의로 「레이더」를 잡았다 — simple 의 성질이 바뀌었다');
  END IF;
  IF NOT (v @@ to_tsquery('simple', '레이:*')) THEN
    PERFORM _t_fail('접두 질의 「레이:*」가 「레이더」를 못 잡는다 — 〈89〉-㉮① 이 성립하지 않는다');
  END IF;
END $$;

ROLLBACK;
