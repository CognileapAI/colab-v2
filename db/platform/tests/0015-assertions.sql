-- 0015 이후의 DB 가 실제로 무엇을 하는가 — 분류 3축 오라클 본체 (M-1·M-2·M-3 · PRD-01·02·03).
--
-- 이 파일 하나가 `0015-drift.sh` 의 세 경우 전부에서 **똑같이** 돈다.
--   · 0015 적용 후      → 전부 통과해야 한다 (green)
--   · 0014 까지만       → 반드시 실패해야 한다 (red)   ← 「되돌리면 red」
--   · 0015 downgrade 후 → 반드시 실패해야 한다 (red)
--
-- **존재 확인만 하지 않는다.** 열이 있는지만 보면 아무도 못 쓰는 열도 통과한다.
-- 그래서 값을 실제로 넣고 · 집합 밖을 밀어 보고 · `topic` 이 여전히 살아 있는지까지 본다.
--
-- 근거 = PRD-01·PRD-02·PRD-03 · 부록 B `M-1`·`M-2`·`M-3` · `dev-package/prd/rounds/R-B-1-db.md §2`

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0015 오라클 실패 — %', msg; END $$;

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
-- A. `M-1` — 분류 5값이 실재하고 **값을 받는다**, 그리고 집합 밖을 **거절한다** (PRD-01)
-- ════════════════════════════════════════════════════════════════════════════
-- ⑴ 5값이 **전부** 통과한다. 한 값이라도 빠지면 화면 셀렉트와 DB 가 갈린다.
DO $$
DECLARE v text;
BEGIN
  FOREACH v IN ARRAY ARRAY['수문 인자', '기상·기후 인자', '식생·탄소 인자',
                           '사회·경제 인자', '환경 인자'] LOOP
    UPDATE d3_dataset_description SET category = v
     WHERE dataset_id = '0000000000000000000000DST1';
  END LOOP;
  SELECT category INTO v FROM d3_dataset_description
   WHERE dataset_id = '0000000000000000000000DST1';
  IF v IS DISTINCT FROM '환경 인자' THEN
    PERFORM _t_fail(format('category 가 %L 다 — 값을 그대로 담지 못한다', v));
  END IF;
END $$;

-- ⑵ 5값 밖은 **거절**한다. 안 막으면 사용자의 오타가 화면에 그대로 그려진다.
--    ⚠ `강우·강수` 는 **주제(topic) 어휘**다 — 분류로는 값이 아니다. 두 축을 짝지으면
--      그 순간 거짓 분류가 박힌다(미결-3 ⓐ 가 자동 매핑을 금지한 이유).
DO $$
BEGIN
  UPDATE d3_dataset_description SET category = '강우·강수'
   WHERE dataset_id = '0000000000000000000000DST1';
  PERFORM _t_fail('분류 5값 밖(`강우·강수`)이 저장됐다 — category CHECK 가 없다');
EXCEPTION WHEN check_violation THEN
  NULL;  -- 기대한 거절
END $$;

-- ⑶ **영문 병기가 저장값이 아니다** (미결-13 ⓐ). 화면이 조립하는 글자를 그대로 밀면 거절된다.
DO $$
BEGIN
  UPDATE d3_dataset_description
     SET category = '기상·기후 인자 (Meteorological & Climatic Factors)'
   WHERE dataset_id = '0000000000000000000000DST1';
  PERFORM _t_fail('영문 병기 문자열이 저장됐다 — 저장·CHECK 는 국문 단일이어야 한다');
EXCEPTION WHEN check_violation THEN
  NULL;
END $$;

-- ⑷ **NULL 로 비울 수 있다** — 「아직 안 골랐다」가 기존 전 행의 상태다(미결-3 ⓐ).
DO $$
BEGIN
  UPDATE d3_dataset_description SET category = NULL
   WHERE dataset_id = '0000000000000000000000DST1';
EXCEPTION WHEN others THEN
  PERFORM _t_fail('category 를 비울 수 없다 — NOT NULL 로 조였다(재선택을 강제하게 된다)');
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- B. `M-2` — 유형 6값 (PRD-02). 컬럼명이 `type` 이 아니라 `data_type` 이다
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE v text;
BEGIN
  FOREACH v IN ARRAY ARRAY['지상관측자료', '위성자료', '재분석자료',
                           '수치모형자료', '합성자료', '관측 기반 산출물'] LOOP
    UPDATE d3_dataset_description SET data_type = v
     WHERE dataset_id = '0000000000000000000000DST1';
  END LOOP;
  SELECT data_type INTO v FROM d3_dataset_description
   WHERE dataset_id = '0000000000000000000000DST1';
  IF v IS DISTINCT FROM '관측 기반 산출물' THEN
    PERFORM _t_fail(format('data_type 이 %L 다 — 값을 그대로 담지 못한다', v));
  END IF;
END $$;

DO $$
BEGIN
  UPDATE d3_dataset_description SET data_type = 'ERA5'
   WHERE dataset_id = '0000000000000000000000DST1';
  PERFORM _t_fail('유형 6값 밖(`ERA5`)이 저장됐다 — data_type CHECK 가 없다');
EXCEPTION WHEN check_violation THEN
  NULL;
END $$;

-- ⚠ **`type` 이라는 열을 만들지 않았다** (PRD-02 축자 — SQL·TS 예약어 회피).
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_name = 'd3_dataset_description' AND column_name = 'type';
  IF n <> 0 THEN
    PERFORM _t_fail('`type` 이라는 열이 생겼다 — 컬럼명은 `data_type` 이어야 한다');
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- C. `M-3` — 사람이 고른 가공 단계 4값. `0011` 의 **반전**이다 (PRD-03 · 미결-2 ⓐ·7 ⓐ)
-- ════════════════════════════════════════════════════════════════════════════
-- ⑴ 4값이 전부 통과한다. **상한은 `Lv3`** 이다(미결-7 ⓐ) — `Lv3` 이 막히면 4단이 아니다.
DO $$
DECLARE v text;
BEGIN
  FOREACH v IN ARRAY ARRAY['Lv0', 'Lv1', 'Lv2', 'Lv3'] LOOP
    UPDATE d3_dataset SET processing_level_user_set = v
     WHERE id = '0000000000000000000000DST1';
  END LOOP;
  SELECT processing_level_user_set INTO v FROM d3_dataset
   WHERE id = '0000000000000000000000DST1';
  IF v IS DISTINCT FROM 'Lv3' THEN
    PERFORM _t_fail(format('processing_level_user_set 이 %L 다 — Lv3 이 안 담긴다', v));
  END IF;
END $$;

-- ⑵ 4값 밖은 거절한다 (`Lv4` · 정수 `2` 같은 값이 들어오면 화면 칩이 못 그린다).
DO $$
BEGIN
  UPDATE d3_dataset SET processing_level_user_set = 'Lv4'
   WHERE id = '0000000000000000000000DST1';
  PERFORM _t_fail('가공 단계 4값 밖(`Lv4`)이 저장됐다 — CHECK 가 없다');
EXCEPTION WHEN check_violation THEN
  NULL;
END $$;

-- ⑶ **NULL 이 「사람이 아직 고르지 않음」이다** — 그 상태에서 화면이 파생값에 `자동` 을 붙인다.
DO $$
BEGIN
  UPDATE d3_dataset SET processing_level_user_set = NULL
   WHERE id = '0000000000000000000000DST1';
EXCEPTION WHEN others THEN
  PERFORM _t_fail('processing_level_user_set 을 비울 수 없다 — 「자동」을 표현할 자리가 없다');
END $$;

-- ⑷ 유형↔가공 단계 **조합 제약이 없다**(미결-14 ⓐ). `관측 기반 산출물` ＋ `Lv1` 이 선다.
DO $$
BEGIN
  UPDATE d3_dataset_description SET data_type = '관측 기반 산출물'
   WHERE dataset_id = '0000000000000000000000DST1';
  UPDATE d3_dataset SET processing_level_user_set = 'Lv1'
   WHERE id = '0000000000000000000000DST1';
EXCEPTION WHEN others THEN
  PERFORM _t_fail('`관측 기반 산출물` ＋ `Lv1` 이 막혔다 — 조합 검증을 만들면 안 된다');
END $$;

-- ⑸ **가공 단계는 `d3_dataset` 에 있다** — `d3_dataset_description` 이 아니다.
--    `0007` 이 세우고 `0011` 이 지운 **그 자리**여야 반전이 성립한다.
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_name = 'd3_dataset' AND column_name = 'processing_level_user_set';
  IF n <> 1 THEN
    PERFORM _t_fail('processing_level_user_set 이 d3_dataset 에 없다 — 0011 의 반전 자리가 아니다');
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- D. `topic` 을 **지우지 않았다** — 되돌림 경로이자 이관 대조 근거다 (§3-㉴)
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE t text;
BEGIN
  SELECT topic INTO t FROM d3_dataset_description
   WHERE dataset_id = '0000000000000000000000DST1';
  IF t IS DISTINCT FROM '강우·강수' THEN
    PERFORM _t_fail(format('topic 이 %L 다 — 분류를 세우면서 주제 값을 건드렸다', t));
  END IF;
END $$;

-- ⑵ 검색 색인은 **종전 그대로**다. 「`topic` 항을 `category` 로」는 `M-10`(R-B-2)이고
--    여기서 앞당기지 않았음을 이 단언이 붙잡는다.
DO $$
DECLARE v tsvector;
BEGIN
  SELECT search_vector INTO v FROM d3_dataset_description
   WHERE dataset_id = '0000000000000000000000DST1';
  IF NOT (v @@ to_tsquery('simple', '강우')) THEN
    PERFORM _t_fail('종전 검색(주제 `강우`)이 깨졌다 — 0015 가 색인식을 건드렸다');
  END IF;
END $$;

ROLLBACK;
