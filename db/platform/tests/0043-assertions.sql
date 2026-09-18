-- 0043 오라클 — `d3_dataset_variable.missing_rate_percent` 는 **자유 입력 칸에서 파생된 수치**다.
--
-- 이 파일 하나가 `0043-drift.sh` 의 세 경우에서 똑같이 돈다.
--   · 0043 적용 후      → 전부 통과해야 한다 (green)
--   · 0042 까지만       → 반드시 실패해야 한다 (red)   ← 「되돌리면 red」의 실물
--   · 0043 downgrade 후 → 반드시 실패해야 한다 (red)
--
-- **존재 확인만 하지 않는다.** 행을 실제로 넣고 파생값을 되읽는다. 재는 주장은 넷이다 —
--   ① 파싱 가능한 문면은 수치가 된다 (`'0.2%'`→0.2 · `' 20 % '`→20 · `'5'`→5)
--   ② 파싱 불가·범위 밖은 NULL 이 될 뿐 **등록을 막지 않는다** (`'낮음'`·`'200%'`·`'-1%'`).
--      자릿수가 numeric 한계를 넘는 문면과 전각 숫자도 같다 — 캐스트가 터지면 그 행의
--      INSERT 가 통째로 죽고 그것은 「파싱 불가는 오류가 아니다」를 깨는 것이다(②-h~j).
--   ③ 원본 칸(`missing_rate`)의 자유 입력 계약은 그대로다 — text 이고 CHECK 가 붙지 않았다
--      (`contracts/seams/fe-core.yaml` `missingRate` 「자유 입력」 · PRD-16 · 결정 3=㈐-2)
--   ⑥ 그 안전이 판의 locale 에 딸려 오지 않는다 — 정규식이 ASCII 이고 자릿수가 묶여 있다
--
-- **제약·생성식 시험이지 RLS 시험이 아니다** — superuser 로 돌아 RLS 를 우회한다.
-- 생성 컬럼은 표의 정책을 그대로 물려받으므로 여기서는 카탈로그(켜짐·FORCE·정책)까지만 본다.
--
-- 근거 = db/platform/versions/0043_variable_missing_rate.py

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0043 오라클 실패 — %', msg; END $$;

CREATE FUNCTION _t_percent(ord integer, expected numeric, msg text) RETURNS void LANGUAGE plpgsql AS $$
DECLARE got numeric;
BEGIN
  SELECT missing_rate_percent INTO got FROM d3_dataset_variable
   WHERE dataset_id = '0000000000000000000000MRD1' AND ordinal = ord;
  IF got IS DISTINCT FROM expected THEN
    PERFORM _t_fail(format('%s — 기대 %s, 실제 %s', msg, coalesce(expected::text,'NULL'), coalesce(got::text,'NULL')));
  END IF;
END $$;

-- ── 재료 ────────────────────────────────────────────────────────────────────
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000MR01', 'MR 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('0000000000000000000000MR02', '0000000000000000000000MR01', 'MR 교수', 'mr@oracle.test');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id) VALUES
  ('0000000000000000000000MRD1', '0000000000000000000000MR01',
   '0000000000000000000000MR02', '0000000000000000000000MR02');

-- ── ① 파싱 가능한 문면 → 수치 ───────────────────────────────────────────────
-- 정규식은 intent 축자에서 좁힌 `^\s*([0-9]{1,3}(?:\.[0-9]{1,6})?)\s*%?\s*$` 다 — 왜 좁혔는지는
-- ②의 극단 입력 블록과 `versions/0043_variable_missing_rate.py` 의 `_NUMBER` 주석에 있다.
INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name, missing_rate, is_representative) VALUES
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 1, '강수량', '0.2%',   true),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 2, '기온',   ' 20 % ', false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 3, '풍속',   '5',      false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 4, '습도',   '0',      false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 5, '기압',   '100%',   false);
SELECT _t_percent(1, 0.2, '①-a 0.2%');
SELECT _t_percent(2, 20,  '①-b 앞뒤·% 앞 공백을 견딘다');
SELECT _t_percent(3, 5,   '①-c % 없는 숫자');
SELECT _t_percent(4, 0,   '①-d 하한 0 은 범위 안이다');
SELECT _t_percent(5, 100, '①-e 상한 100 은 범위 안이다');

-- ── ② 파싱 불가·범위 밖 → NULL. **등록은 막히지 않는다** ────────────────────
-- 막으면 자유 입력 계약(PRD-16)을 뒤집는 것이고, 그것이 결정 3 에서 ㈐-1 을 접은 이유다.
INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name, missing_rate, is_representative) VALUES
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 6,  '운량',   '낮음',       false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 7,  '시정',   '약 5%',      false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 8,  '일사',   '5% 내외',    false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 9,  '증발량', '200%',       false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 10, '적설',   '-1%',        false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 11, '지온',   '',           false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 12, '수온',   NULL,         false);
SELECT _t_percent(6,  NULL, '②-a 수치가 아닌 문면');
SELECT _t_percent(7,  NULL, '②-b 접두어가 붙은 문면');
SELECT _t_percent(8,  NULL, '②-c 접미어가 붙은 문면');
SELECT _t_percent(9,  NULL, '②-d 100 초과는 범위 밖이다');
SELECT _t_percent(10, NULL, '②-e 음수는 정규식에서 걸린다');
SELECT _t_percent(11, NULL, '②-f 빈 문자열');
SELECT _t_percent(12, NULL, '②-g NULL');

-- ② 계속 — **극단 입력도 등록을 막지 않는다.** 위 일곱은 「수치가 아니다」이고 아래 여섯은
-- 「수치처럼 생겼는데 캐스트가 터진다」다. `missing_rate` 에는 길이 상한이 없으므로
-- (`catalog.py` `_VARIABLE_FIELDS` 검사는 「문자열이거나 null」까지다) 자릿수가 numeric 한계를
-- 넘는 문면이 실제로 들어올 수 있고, 숫자 문자 집합은 collation 에 딸려 온다.
--   · `\d` 는 locale 의존이라 ICU collation 아래에서는 전각 숫자(U+FF15)까지 잡는다 —
--     잡아 놓고 `::numeric` 이 거절하면 그 자리에서 INSERT 가 죽는다.
--   · `\d+` 는 자릿수가 무제한이라 numeric 한계(정수부 131072 · 소수부 16383)를 넘기면
--     `value overflows numeric format` 이 난다.
-- 둘 다 **파일 맨 위 ②의 주장을 정면으로 깬다** — 파싱 불가는 NULL 일 뿐 오류가 아니어야 한다.
-- 그래서 정규식은 ASCII 숫자만, 자릿수를 묶어서 적는다(`[0-9]{1,3}(?:\.[0-9]{1,6})?`).
INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name, missing_rate, is_representative) VALUES
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 20, '누적강수', repeat('9', 140000),   false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 21, '누적일사', '0.' || repeat('9', 20000), false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 22, '전각결측', U&'\FF15' || '%',       false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 23, '지수표기', '1e5',                 false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 24, '과다소수', '0.1234567',           false),
  ('0000000000000000000000MRD1', '0000000000000000000000MR01', 25, '사십자리', repeat('9', 40),       false);
SELECT _t_percent(20, NULL, '②-h 정수부가 numeric 한계를 넘는 문면 — 등록이 죽으면 안 된다');
SELECT _t_percent(21, NULL, '②-i 소수부가 numeric 한계를 넘는 문면 — 정수부만 묶어서는 못 막는다');
SELECT _t_percent(22, NULL, '②-j 전각 숫자 — ICU collation 에서 `\d` 가 잡으면 캐스트가 터진다');
SELECT _t_percent(23, NULL, '②-k 지수 표기 — numeric 은 받지만 결측률 문면은 아니다');
SELECT _t_percent(24, NULL, '②-l 소수 7자리는 묶인 자릿수 밖이다 — 값이 아니라 NULL 로 빠진다');
SELECT _t_percent(25, NULL, '②-m 40자리는 numeric 한계 안이지만 100 초과라 범위 밖이다');
DO $$
DECLARE n integer;
BEGIN
  SELECT count(*) INTO n FROM d3_dataset_variable WHERE dataset_id = '0000000000000000000000MRD1';
  IF n <> 18 THEN PERFORM _t_fail(format('② 18행을 넣었는데 %s행이 남았다 — 파생이 등록을 막았다', n)); END IF;
END $$;

-- ── ③ 파생 컬럼의 성질 — GENERATED ALWAYS ＊STORED＊ 이고 원본을 따라 바뀐다 ──
DO $$
DECLARE gen text; expr text;
BEGIN
  SELECT is_generated, generation_expression INTO gen, expr FROM information_schema.columns
   WHERE table_name = 'd3_dataset_variable' AND column_name = 'missing_rate_percent';
  IF gen IS DISTINCT FROM 'ALWAYS' THEN
    PERFORM _t_fail(format('③-a missing_rate_percent 가 생성 컬럼이 아니다 (is_generated=%s)', coalesce(gen,'없음')));
  END IF;
  IF expr IS NULL OR position('missing_rate' in expr) = 0 THEN
    PERFORM _t_fail('③-b 생성식이 missing_rate 를 읽지 않는다 — 원본이 아닌 곳에서 파생되고 있다');
  END IF;
  IF (SELECT data_type FROM information_schema.columns
       WHERE table_name = 'd3_dataset_variable' AND column_name = 'missing_rate_percent') <> 'numeric' THEN
    PERFORM _t_fail('③-c missing_rate_percent 가 numeric 이 아니다');
  END IF;
  -- 직접 쓰기는 거절된다. 사본이 아니라 파생이라는 뜻이다.
  BEGIN
    INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name, missing_rate_percent, is_representative)
    VALUES ('0000000000000000000000MRD1', '0000000000000000000000MR01', 13, '직접쓰기', 1, false);
    PERFORM _t_fail('③-d 생성 컬럼에 직접 쓰기가 통과했다 — GENERATED ALWAYS 가 아니다');
  EXCEPTION WHEN generated_always THEN NULL;
  END;
END $$;
-- ③-e 원본을 고치면 파생이 따라간다 — 동기화 주체가 따로 없다는 주장의 실물
UPDATE d3_dataset_variable SET missing_rate = '3.5%'
 WHERE dataset_id = '0000000000000000000000MRD1' AND ordinal = 1;
SELECT _t_percent(1, 3.5, '③-e 원본 수정이 파생에 반영된다');
UPDATE d3_dataset_variable SET missing_rate = '측정 안 함'
 WHERE dataset_id = '0000000000000000000000MRD1' AND ordinal = 1;
SELECT _t_percent(1, NULL, '③-f 수치를 지우면 파생도 NULL 로 돌아간다');

-- ── ④ 원본 칸의 자유 입력 계약은 그대로다 ──────────────────────────────────
DO $$
DECLARE n integer;
BEGIN
  IF (SELECT data_type FROM information_schema.columns
       WHERE table_name = 'd3_dataset_variable' AND column_name = 'missing_rate') <> 'text' THEN
    PERFORM _t_fail('④-a missing_rate 가 text 가 아니다 — 자유 입력 결정(PRD-16)이 뒤집혔다');
  END IF;
  IF (SELECT is_nullable FROM information_schema.columns
       WHERE table_name = 'd3_dataset_variable' AND column_name = 'missing_rate') <> 'YES' THEN
    PERFORM _t_fail('④-b missing_rate 가 NOT NULL 이 됐다 — 선택 입력이 아니다');
  END IF;
  SELECT count(*) INTO n FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
   WHERE t.relname = 'd3_dataset_variable' AND c.contype = 'c'
     AND pg_get_constraintdef(c.oid) LIKE '%missing_rate%';
  IF n <> 0 THEN PERFORM _t_fail(format('④-c missing_rate 에 CHECK 가 %s건 붙었다 — 입력 검증(㈐-1)은 이 회차가 아니다', n)); END IF;
END $$;

-- ── ⑤ 경계 — 파생 컬럼은 표의 정책을 그대로 물려받는다 ──────────────────────
DO $$
DECLARE rls boolean; forced boolean; n integer;
BEGIN
  SELECT relrowsecurity, relforcerowsecurity INTO rls, forced
    FROM pg_class WHERE relname = 'd3_dataset_variable';
  IF rls IS NOT TRUE THEN PERFORM _t_fail('⑤ d3_dataset_variable 의 RLS 가 꺼져 있다'); END IF;
  IF forced IS NOT TRUE THEN PERFORM _t_fail('⑤ d3_dataset_variable 의 FORCE RLS 가 꺼져 있다'); END IF;
  SELECT count(*) INTO n FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid
   WHERE c.relname = 'd3_dataset_variable' AND p.polname = 'lab_boundary';
  IF n <> 1 THEN PERFORM _t_fail('⑤ lab_boundary 정책이 없다'); END IF;
END $$;

-- ── ⑥ 정규식 자체의 성질 — ASCII 이고 자릿수가 묶여 있다 ────────────────────
-- ②-h~j 는 **행동**으로 재고 여기서는 **식**으로 잰다. 둘 다 필요한 이유는 기본 collation 이
-- libc 인 판(공식 postgres:16·16-alpine 둘 다 그렇다)에서는 `\d` 가 전각 숫자를 잡지 않아
-- ②-j 만으로는 locale 의존이 드러나지 않기 때문이다. 식을 직접 보면 판과 무관하게 잡힌다.
--
-- 비교 대상은 **살아 있는 생성식에서 꺼낸 문자열**이다 — 여기에 정규식을 다시 적으면
-- 리비전과 갈라져도 시험이 모른다.
DO $$
DECLARE pat text; wide text := U&'\FF15' || '%';
BEGIN
  SELECT (regexp_match(generation_expression, '''(\^[^'']*\$)''::text'))[1] INTO pat
    FROM information_schema.columns
   WHERE table_name = 'd3_dataset_variable' AND column_name = 'missing_rate_percent';
  IF pat IS NULL THEN
    PERFORM _t_fail('⑥-a 생성식에서 정규식을 꺼내지 못했다 — 식의 모양이 바뀌었다');
  END IF;
  IF position('\d' in pat) > 0 THEN
    PERFORM _t_fail(format('⑥-b 정규식이 locale 의존 숫자 클래스 \d 를 쓴다 (%s) — ICU collation 에서 전각 숫자를 잡고 ::numeric 이 터진다', pat));
  END IF;
  IF position('[0-9]' in pat) = 0 THEN
    PERFORM _t_fail(format('⑥-c 정규식이 ASCII 숫자 범위를 명시하지 않는다 (%s)', pat));
  END IF;
  -- 자릿수가 묶여 있지 않으면 numeric 한계를 넘는 문면에서 다시 터진다(②-h·②-i).
  IF position('+' in pat) > 0 THEN
    PERFORM _t_fail(format('⑥-d 정규식에 무제한 반복 + 가 남아 있다 (%s) — 자릿수를 묶어야 한다', pat));
  END IF;
  -- 같은 식을 ICU collation 아래에서 실제로 돌려 본다. 기본 collation 이 libc 여도 결론이 같다.
  IF NOT EXISTS (SELECT 1 FROM pg_collation WHERE collname = 'und-x-icu') THEN
    PERFORM _t_fail('⑥-e und-x-icu collation 이 없다 — 이 오라클은 ICU 가 있는 판에서 돈다(공식 postgres:16 이미지 기준)');
  END IF;
  IF substring(wide COLLATE "und-x-icu" from pat) IS NOT NULL THEN
    PERFORM _t_fail(format('⑥-f ICU collation 에서 전각 숫자가 정규식에 잡힌다 (%s) — 그 캐스트가 등록을 죽인다', pat));
  END IF;
END $$;

ROLLBACK;
