-- 0006 오라클 — `d9_topic_synonym.category` 5값 CHECK ＋ 이관 3쌍 ＋ [미상] 1값.
--
-- 수용 기준 축자 (`R-C-1-contract-db.md §2` WU-C7) — 「`d9` 5값 CHECK」.
-- 매핑 근거는 PRD-01 「Data Category」 표의 **대표 인자 예시** 축자다(마이그레이션 산문).
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0006 오라클 실패 — %', msg; END $$;

-- ── A. 열이 서고 CHECK 가 **정확히 5값**이다 ───────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'd9_topic_synonym' AND column_name = 'category') THEN
    PERFORM _t_fail('d9_topic_synonym.category 가 없다');
  END IF;
END $$;

-- ⭑ **정의문만 보지 않는다** — 값 집합은 「넣어 보고 튕기는가」로 잰다.
DO $$
DECLARE v text;
        five text[] := ARRAY['수문 인자','기상·기후 인자','식생·탄소 인자','사회·경제 인자','환경 인자'];
BEGIN
  FOREACH v IN ARRAY five LOOP
    BEGIN
      INSERT INTO d9_topic_synonym (synonym, topic, source_note, category)
      VALUES ('_t_' || v, '강우·강수', '오라클 임시 행', v);
    EXCEPTION WHEN check_violation THEN
      PERFORM _t_fail(format('분류 5값의 하나(%L)가 CHECK 에 막힌다', v));
    END;
  END LOOP;
  -- 5값 밖은 **막힌다**. 안 막히면 CHECK 가 없는 것과 같다.
  BEGIN
    INSERT INTO d9_topic_synonym (synonym, topic, source_note, category)
    VALUES ('_t_out', '강우·강수', '오라클 임시 행', '지형 인자');
    PERFORM _t_fail('5값 밖의 분류가 들어갔다 — CHECK 가 값 집합을 안 닫는다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  -- NULL 은 허용이다 — [미상]을 담는 자리다.
  BEGIN
    INSERT INTO d9_topic_synonym (synonym, topic, source_note, category)
    VALUES ('_t_null', '지형·DEM', '오라클 임시 행', NULL);
  EXCEPTION WHEN check_violation THEN
    PERFORM _t_fail('NULL 이 막힌다 — [미상]을 적을 자리가 없어진다');
  END;
  DELETE FROM d9_topic_synonym WHERE synonym LIKE '\_t\_%';
END $$;

-- ── B. **이관 3쌍** — 시드 행이 실제로 옮겨졌다 ────────────────────────────
DO $$
DECLARE r record;
BEGIN
  FOR r IN SELECT * FROM (VALUES
      ('강우·강수',     '기상·기후 인자'),
      ('식생·NDVI',     '식생·탄소 인자'),
      ('토지피복·LULC', '사회·경제 인자')) AS v(topic, want)
  LOOP
    IF EXISTS (SELECT 1 FROM d9_topic_synonym s
                WHERE s.topic = r.topic AND s.category IS DISTINCT FROM r.want) THEN
      PERFORM _t_fail(format('topic %L 의 분류가 %L 이 아니다 — PRD-01 대표 인자 축자와 어긋난다',
                             r.topic, r.want));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM d9_topic_synonym s WHERE s.topic = r.topic) THEN
      PERFORM _t_fail(format('topic %L 행이 없다 — 시드(0003)가 안 실렸다', r.topic));
    END IF;
  END LOOP;
END $$;

-- ── C. **[미상]은 NULL 로 남는다** — `지형·DEM` 을 지어내지 않는다 ─────────
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d9_topic_synonym
   WHERE topic = '지형·DEM' AND category IS NOT NULL;
  IF n > 0 THEN
    PERFORM _t_fail(format('지형·DEM 행 %s 건에 분류가 채워졌다 — PRD-01 어느 줄에서도 도출되지 않는 값이다', n));
  END IF;
END $$;

-- ── D. **주제 축은 한 글자도 안 바뀌었다** (`0005` 의 완료 오라클이 이것을 잰다) ──
DO $$
DECLARE got text;
        want text := '강우·강수,식생·NDVI,지형·DEM,토지피복·LULC';
BEGIN
  SELECT string_agg(DISTINCT topic, ',' ORDER BY topic) INTO got FROM d9_topic_synonym;
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('주제 축이 %L 다 (기대 %L) — 이 회차는 topic 을 안 건드린다', got, want));
  END IF;
END $$;

ROLLBACK;
