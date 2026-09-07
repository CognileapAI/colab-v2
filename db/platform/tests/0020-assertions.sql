-- 0020 구조 오라클 — **제약이 실제로 거절하는가**를 빈 DB 에서 잰다.
--
-- 수용 기준 축자 (`R-C-1-contract-db.md §2` WU-C7) — 「같은 연구실 같은 이름 INSERT 가
-- **DB 에서** 거절(앱 우회) · 다른 연구실 성공」.
--
-- ⭑ **정의문만 grep 하지 않는다** — 제약은 텍스트가 아니라 **거절하는 동작**이다.
--    그래서 아래는 「넣어 보고 두 번째가 튕기는가」로 잰다. 여기서 넣는 경로는
--    `routes/project.py` 의 400 을 **한 번도 타지 않는다** — 그것이 「앱 우회」의 실체다.
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0020 오라클 실패 — %', msg; END $$;

INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z'),
  ('0000000000000000000000000V', 'V 연구실', '2020-01-01T00:00:00Z');
SET app.current_lab = '0000000000000000000000000T';

-- ── A. 제약이 **그 이름으로** 서 있다 (schema.sql 선언과 같은 이름) ─────────
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM pg_constraint
   WHERE conrelid = 'd6_project'::regclass AND conname = 'd6_project_lab_name_unique'
     AND contype = 'u';
  IF n <> 1 THEN PERFORM _t_fail('d6_project_lab_name_unique UNIQUE 제약이 없다'); END IF;
END $$;

-- A-⑵ 열쇠가 **(lab_id, name)** 두 칸이다 — `type` 을 넣으면 유형이 다른 동명이 통과한다.
DO $$
DECLARE cols text;
BEGIN
  SELECT string_agg(a.attname, ',' ORDER BY k.ord) INTO cols
    FROM pg_constraint c
    JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord) ON true
    JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
   WHERE c.conrelid = 'd6_project'::regclass AND c.conname = 'd6_project_lab_name_unique';
  IF cols IS DISTINCT FROM 'lab_id,name' THEN
    PERFORM _t_fail(format('제약 열쇠가 %L 다 (기대 lab_id,name)', cols));
  END IF;
END $$;

-- ── B. **동작** — 같은 연구실 같은 이름 둘째가 튕긴다 ──────────────────────
INSERT INTO d6_project (id, lab_id, type, name) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', '국가과제', '동명 과제');

DO $$
BEGIN
  BEGIN
    INSERT INTO d6_project (id, lab_id, type, name) VALUES
      ('00000000000000000000000TP2', '0000000000000000000000000T', '국가과제', '동명 과제');
    PERFORM _t_fail('같은 연구실 같은 이름이 DB 에서 들어갔다 — 뒷문이 없다');
  EXCEPTION WHEN unique_violation THEN NULL;
  END;
END $$;

-- B-⑵ **유형이 달라도 겹침이다** (PRD-42 수용 기준 2행).
DO $$
BEGIN
  BEGIN
    INSERT INTO d6_project (id, lab_id, type, name) VALUES
      ('00000000000000000000000TP3', '0000000000000000000000000T', '논문', '동명 과제');
    PERFORM _t_fail('유형이 다른 동명이 들어갔다 — 열쇠에 type 이 섞였다');
  EXCEPTION WHEN unique_violation THEN NULL;
  END;
END $$;

-- ── C. **다른 연구실은 성공한다** — 판정 축은 연구실 경계 안이다 ───────────
SET app.current_lab = '0000000000000000000000000V';
INSERT INTO d6_project (id, lab_id, type, name) VALUES
  ('00000000000000000000000VP1', '0000000000000000000000000V', '국가과제', '동명 과제');
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d6_project WHERE name = '동명 과제';
  IF n < 1 THEN PERFORM _t_fail('다른 연구실의 동명이 서지 않았다 — 제약이 연구실을 안 가른다'); END IF;
END $$;

ROLLBACK;
