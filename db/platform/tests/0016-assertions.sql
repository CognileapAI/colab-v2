-- 0016 구조 오라클 — **표·제약·정책이 실제로 섰는가**를 빈 DB 에서 잰다.
--
-- 완료 판정 축자 (`R-B-1-db.md §5` WU-B2) — 「`d3_dataset_variable` 이 서고 RLS ＋
-- 대표 1개 부분 UNIQUE 가 걸린다」.
--
-- ⭑ **정의문을 grep 하지 않는다** — 제약은 텍스트가 아니라 **거부하는 동작**이다.
--    그래서 아래는 전부 「넣어 보고 거부되는가」로 잰다(색인 이름만 바꿔도 통과하는
--    검사를 만들지 않는다).
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0016 오라클 실패 — %', msg; END $$;

-- 재료. 여기까지는 `postgres`(superuser · RLS 우회)로 심는다 — 경계를 재는 것은 아래 B·C 다.
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z'),
  ('0000000000000000000000000B', 'B 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                        uploaded_at, last_modified_at) VALUES
  ('000000000000000000000DSV1A', '0000000000000000000000000T', '00000000000000000000000TP1',
   '00000000000000000000000TP1', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
SET app.current_lab = '0000000000000000000000000T';

-- ⭑ **경계 검사는 비소유자 롤로 한다.** `postgres` 는 superuser 라 RLS 를 **언제나**
--    우회한다 — 그 롤로 「안 보인다」를 재면 전부 거짓 green 이다(v1 CI 가 밟은 자리).
--    아래 B·C 구간은 `t_app`(NOSUPERUSER · NOBYPASSRLS · 비소유자)으로 돈다.
CREATE ROLE t_app NOLOGIN NOSUPERUSER NOBYPASSRLS;
GRANT USAGE ON SCHEMA public TO t_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO t_app;

-- ── A. 표가 선다 ─────────────────────────────────────────────────────────
-- A-⑴ 여덟 칸이 **이 이름**으로 있다. 이름이 갈리면 서버·이관이 같이 죽는다.
DO $$
DECLARE got text;
        want text := 'dataset_id,is_representative,lab_id,missing_rate,name,ordinal,unit,value_range';
BEGIN
  SELECT string_agg(column_name, ',' ORDER BY column_name) INTO got
    FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'd3_dataset_variable';
  IF got IS DISTINCT FROM want THEN
    PERFORM _t_fail(format('열 구성이 %L 다 (기대 %L)', got, want));
  END IF;
END $$;

-- A-⑵ 정상 행 3개가 들어간다 (대표는 첫 행 하나).
INSERT INTO d3_dataset_variable
  (dataset_id, lab_id, ordinal, name, unit, value_range, missing_rate, is_representative) VALUES
  ('000000000000000000000DSV1A', '0000000000000000000000000T', 1, 'precipitation', 'mm', '0~350', '0.2%', true),
  ('000000000000000000000DSV1A', '0000000000000000000000000T', 2, 'temperature',   '℃', '-30~40', NULL, false),
  ('000000000000000000000DSV1A', '0000000000000000000000000T', 3, 'runoff',        'm3/s', NULL, NULL, false);

SET ROLE t_app;   -- 여기부터 **비소유자**다 (위 산문).

-- ── B. 제약 넷이 **거부한다** ────────────────────────────────────────────
-- B-⑴ 같은 `ordinal` 두 번 = PRIMARY KEY (dataset_id, ordinal) 위반.
DO $$
BEGIN
  BEGIN
    INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name)
      VALUES ('000000000000000000000DSV1A', '0000000000000000000000000T', 1, '중복 순서');
    PERFORM _t_fail('같은 (dataset_id, ordinal) 이 두 번 들어갔다 — PK 가 없다');
  EXCEPTION WHEN unique_violation THEN NULL;
  END;
END $$;

-- B-⑵ **대표 둘째** = 부분 UNIQUE 색인 위반. 이 회차의 알맹이다 (PRD-16 「정확히 1개」).
DO $$
BEGIN
  BEGIN
    INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name, is_representative)
      VALUES ('000000000000000000000DSV1A', '0000000000000000000000000T', 9, '둘째 대표', true);
    PERFORM _t_fail('한 데이터셋에 대표가 둘 들어갔다 — 부분 UNIQUE 색인이 없다');
  EXCEPTION WHEN unique_violation THEN NULL;
  END;
END $$;

-- B-⑶ 공백뿐인 이름 = CHECK 위반. 「이름 없는 변수 행」은 화면이 무엇으로도 못 그린다.
DO $$
BEGIN
  BEGIN
    INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name)
      VALUES ('000000000000000000000DSV1A', '0000000000000000000000000T', 8, '   ');
    PERFORM _t_fail('공백뿐인 이름이 들어갔다 — name CHECK 가 없다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;

-- B-⑷ **다른 연구실 `lab_id`** = 경계 정책의 WITH CHECK 위반 (cross-tenant 쓰기 음성).
--     ⚠ FK 가 먼저 잡으면 정책을 안 잰 것이 된다 — 그래서 그 연구실을 **실재**시켜 둔다
--     (재료는 위에서 postgres 가 심었다).
DO $$
BEGIN
  BEGIN
    INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name)
      VALUES ('000000000000000000000DSV1A', '0000000000000000000000000B', 7, '남의 연구실');
    PERFORM _t_fail('다른 연구실 lab_id 로 행이 들어갔다 — 경계 정책의 WITH CHECK 가 없다');
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;

-- B-⑸ **대표가 false 인 행은 몇 개든 된다** — 부분 색인이라 그렇다.
--     여기서 red 가 나면 색인에서 `WHERE is_representative` 가 빠진 것이다.
INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name, is_representative)
  VALUES ('000000000000000000000DSV1A', '0000000000000000000000000T', 4, '넷째', false);

-- ── C. RLS ───────────────────────────────────────────────────────────────
-- C-⑴ ENABLE ＋ **FORCE** 둘 다. FORCE 가 없으면 소유자 세션에서 정책이 꺼진다.
DO $$
DECLARE en boolean; fo boolean;
BEGIN
  SELECT relrowsecurity, relforcerowsecurity INTO en, fo
    FROM pg_class WHERE relname = 'd3_dataset_variable';
  IF NOT en OR NOT fo THEN
    PERFORM _t_fail(format('RLS enable=%s force=%s — 둘 다 참이어야 한다', en, fo));
  END IF;
END $$;

-- C-⑵ 정책 이름·개수가 형제 표와 같다(경계 한 장). 본체 정책을 더하지 않았다.
DO $$
DECLARE got text;
BEGIN
  SELECT string_agg(policyname || ':' || permissive, ',' ORDER BY policyname) INTO got
    FROM pg_policies WHERE schemaname = 'public' AND tablename = 'd3_dataset_variable';
  IF got IS DISTINCT FROM 'lab_boundary:PERMISSIVE' THEN
    PERFORM _t_fail(format('정책이 %L 다 (기대 lab_boundary:PERMISSIVE 한 장)', got));
  END IF;
END $$;

-- C-⑶ **다른 연구실로 스코프를 옮기면 0건** (cross-tenant 읽기 음성).
DO $$
DECLARE n bigint;
BEGIN
  PERFORM set_config('app.current_lab', '0000000000000000000000000B', true);
  SELECT count(*) INTO n FROM d3_dataset_variable;
  IF n <> 0 THEN
    PERFORM _t_fail(format('다른 연구실 스코프에서 변수 행 %s 건이 보였다 — 경계가 열려 있다', n));
  END IF;
  PERFORM set_config('app.current_lab', '0000000000000000000000000T', true);
END $$;

RESET ROLE;   -- 아래 D 는 카탈로그 조회라 소유자로 본다.

-- ── D. 이 회차가 **안 건드린 것** ────────────────────────────────────────
-- D-⑴ `d3_dataset_autometa.variables` 가 그대로 있다 (되돌림 경로 · §3-㉴).
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name = 'd3_dataset_autometa' AND column_name = 'variables') THEN
    PERFORM _t_fail('d3_dataset_autometa.variables 가 없다 — 지우지 않기로 한 열이다');
  END IF;
END $$;

-- D-⑵ **색인식을 한 글자도 안 건드렸다** — `M-10` 은 이 파일 밖이다(R-B-2 · WU-B7).
--     `search_vector` 가 아직 `d3_search_join(variables)` 를 물고 있어야 한다.
DO $$
DECLARE def text;
BEGIN
  SELECT pg_get_expr(d.adbin, d.adrelid) INTO def
    FROM pg_attrdef d JOIN pg_attribute a ON a.attrelid = d.adrelid AND a.attnum = d.adnum
   WHERE d.adrelid = 'd3_dataset_autometa'::regclass AND a.attname = 'search_vector';
  IF def IS NULL OR position('d3_search_join' in def) = 0 THEN
    PERFORM _t_fail(format('autometa.search_vector 식이 %L 다 — 이 회차는 색인을 건드리지 않는다', def));
  END IF;
END $$;

-- D-⑶ **미러 트리거가 없다** — `M-10` 소속이고 여기서 앞당기면 라운드에 두 번 돈다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM pg_trigger
   WHERE tgrelid = 'd3_dataset_variable'::regclass AND NOT tgisinternal;
  IF n <> 0 THEN
    PERFORM _t_fail(format('d3_dataset_variable 에 트리거가 %s 개 있다 — M-10 을 앞당겼다', n));
  END IF;
END $$;

ROLLBACK;
