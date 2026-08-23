-- 0004 이후의 DB 가 실제로 무엇을 막는가 — 오라클 본체.
--
-- 이 파일 하나가 `0004-drift.sh` 의 세 경우 전부에서 **똑같이** 돈다.
--   · 0004 적용 후  → 전부 통과해야 한다 (green)
--   · 0004 없음     → 반드시 실패해야 한다 (red)   ← 이게 「되돌리면 red」의 실물이다
--   · 0004 downgrade 후 → 반드시 실패해야 한다 (red)
--
-- **제약 시험이지 RLS 시험이 아니다.** 그래서 superuser 로 돈다 — FORCE RLS 가 CHECK·유니크
-- 인덱스의 판정을 가리지 않게 하려는 것이고, RLS 자체는 `rls-coverage`·`rls-effect` 가 본다.
-- 이 파일이 RLS 를 green 으로 세지 않는다(§A-6 은 「정책이 선언돼 있는가」만 본다).
--
-- 근거 = PLAN-SoT §9 〈66〉 · sessions/P2.md §2-22-a · P2-EXEC §4 W1 ⑴⑵
--
-- 판정 방식 — 「거절되어야 하는 삽입」은 SAVEPOINT 로 감싸 실제로 시도하고, **통과해 버리면**
-- 그 자리에서 EXCEPTION 을 던진다. 「제약이 존재한다」를 카탈로그로만 확인하지 않는다 —
-- 존재 확인은 조건이 틀린 제약도 통과시킨다.

\set ON_ERROR_STOP on
BEGIN;

-- ── 재료 (이 파일만의 것 — seed.sql 을 읽지 않는다) ─────────────────────────
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_lab_profile (lab_id, university, department, principal_investigator,
                            research_field, introduction, default_visibility) VALUES
  ('0000000000000000000000000T', 'T 대', 'T 과', 'T 교수', '수문학', 'T', '열림');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                        uploaded_at, last_modified_at) VALUES
  ('0000000000000000000000DST1', '0000000000000000000000000T', '00000000000000000000000TP1',
   '00000000000000000000000TP1', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0004 오라클 실패 — %', msg; END $$;

-- 「이 INSERT 는 거절되어야 한다」. 통과하면 실패로 잡는다.
CREATE FUNCTION _t_must_reject(stmt text, msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  BEGIN
    EXECUTE stmt;
  EXCEPTION WHEN check_violation OR unique_violation OR not_null_violation THEN
    -- **엉뚱한 이유로 막힌 것을 「막혔다」로 세지 않는다.** ULID 도메인 위반도 23514 라
    -- 라벨을 안 펴면 이 함수가 전부 통과시킨다 — 실제로 한 번 그랬다.
    IF SQLERRM LIKE '%ulid_crockford_base32%' THEN
      RAISE EXCEPTION '0004 오라클 실패 — 시험 재료가 틀렸다(ULID 도메인 위반). 판정이 아니다: %', msg;
    END IF;
    RETURN;                             -- 기대대로 막혔다
  END;
  RAISE EXCEPTION '0004 오라클 실패 — %', msg;   -- 안 막혔다
END $$;

-- 짧은 라벨을 정규 ULID(26자 Crockford base32)로 편다. **도메인 위반으로 거절되면
-- `_t_must_reject` 가 「막혔다」로 잘못 세어 거짓 green 이 난다** — 실제로 한 번 그랬다.
CREATE FUNCTION _t_ulid(label text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
  SELECT rpad(label, 26, '0')
$$;

CREATE FUNCTION _t_file(id text, kind text, lat boolean, lon boolean) RETURNS text
  LANGUAGE sql IMMUTABLE AS $$
  SELECT format(
    'INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, storage_key, carries_lat, carries_lon)'
    ' VALUES (%L, ''0000000000000000000000000T'', ''0000000000000000000000DST1'', %L, %L, %L, %L, %L)',
    _t_ulid(id), kind, id || '.dat', 'k/' || id, lat, lon)
$$;

-- ════════════════════════════════════════════════════════════════════════════
-- A. 축 열 두 개가 실재한다 (〈66〉 — 텍스트 단일값이 아니다)
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE n int;
BEGIN
  SELECT count(*) INTO n FROM information_schema.columns
   WHERE table_name = 'd3_file' AND column_name IN ('carries_lat', 'carries_lon')
     AND data_type = 'boolean';
  IF n <> 2 THEN
    PERFORM _t_fail(format('d3_file 에 boolean carries_lat·carries_lon 이 없다 (%s/2). 0004 가 적용되지 않았다', n));
  END IF;
END $$;

-- 폐기된 모양이 되살아나지 않는다 — grid_axis 텍스트 열은 〈66〉 이 물렸다.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
              WHERE table_name = 'd3_file' AND column_name = 'grid_axis') THEN
    PERFORM _t_fail('d3_file.grid_axis 가 있다 — 〈66〉 이 폐기한 단일값 모양이다');
  END IF;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- B. CHECK 2종 — 「축 없는 격자 파일」도 「축 붙은 본체」도 만들어지지 않는다
-- ════════════════════════════════════════════════════════════════════════════
SELECT _t_must_reject(_t_file('B1', '기준 격자 파일', false, false),
                      '축이 하나도 없는 기준 격자 파일이 들어갔다 (CHECK ㈎ 부재)');
SELECT _t_must_reject(_t_file('B2', '본체', true, false),
                      '위도를 실은 본체가 들어갔다 (CHECK ㈏ 부재 — 반쪽만 걸었다)');
SELECT _t_must_reject(_t_file('B3', '본체', false, true),
                      '경도를 실은 본체가 들어갔다 (CHECK ㈏ 부재)');
SELECT _t_must_reject(_t_file('B4', '본체', true, true),
                      '결합축 본체가 들어갔다 (CHECK ㈏ 부재)');

-- 양성 — 정상 조합은 전부 들어간다. 막으면 그것도 실패다.
SAVEPOINT s_ok;
DO $$
BEGIN
  EXECUTE _t_file('P1', '본체', false, false);
  EXECUTE _t_file('P2', '기준 격자 파일', true, false);
  EXECUTE _t_file('P3', '기준 격자 파일', false, true);
EXCEPTION WHEN others THEN
  PERFORM _t_fail('정상 조합(본체 · 위도격자 · 경도격자)이 거절됐다: ' || SQLERRM);
END $$;
ROLLBACK TO SAVEPOINT s_ok;

-- ════════════════════════════════════════════════════════════════════════════
-- C. 유일성 — 축 원소마다 1건. 「위도 2건」도 「위도1 + 결합1」도 못 들어간다
-- ════════════════════════════════════════════════════════════════════════════

-- 옛 인덱스는 걷혔다. 남아 있으면 실물 `.npy` 쌍이 오늘도 못 들어간다 (W0-R1 §2.5).
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_indexes
              WHERE tablename = 'd3_file'
                AND indexname = 'd3_file_one_reference_grid_per_dataset') THEN
    PERFORM _t_fail('옛 인덱스 d3_file_one_reference_grid_per_dataset 가 살아 있다 — 데이터셋당 격자 1건이 그대로다');
  END IF;
END $$;

-- 위도 + 경도 쌍은 **둘 다** 들어간다 (〈58〉 이 말한 실물 쌍).
SAVEPOINT s_pair;
DO $$
BEGIN
  EXECUTE _t_file('C1', '기준 격자 파일', true, false);
  EXECUTE _t_file('C2', '기준 격자 파일', false, true);
EXCEPTION WHEN others THEN
  PERFORM _t_fail('위도·경도 한 쌍이 둘 다 들어가지 못했다: ' || SQLERRM);
END $$;

-- 같은 축이 두 번은 못 들어간다.
SELECT _t_must_reject(_t_file('C3', '기준 격자 파일', true, false),
                      '위도 격자 파일이 2건 들어갔다 (carries_lat 부분 유니크 인덱스 부재)');
SELECT _t_must_reject(_t_file('C4', '기준 격자 파일', false, true),
                      '경도 격자 파일이 2건 들어갔다 (carries_lon 부분 유니크 인덱스 부재)');
-- 결합축은 두 인덱스에 동시에 걸린다 — 「위도1 + 결합1」이 여기서 막힌다.
-- 제3값(단일 텍스트 enum)으로는 못 막는 자리이고, 〈66〉 이 두 불리언을 고른 이유가 이것이다.
SELECT _t_must_reject(_t_file('C5', '기준 격자 파일', true, true),
                      '위도 1건 + 결합축 1건이 함께 들어갔다 — 제3값 안이 탈락한 바로 그 구멍이다');
ROLLBACK TO SAVEPOINT s_pair;

-- 결합축 1건만 있는 데이터셋도 정상이다 (실물 16건 중 2건이 이 모양 — 〈66〉).
SAVEPOINT s_combined;
DO $$
BEGIN
  EXECUTE _t_file('C6', '기준 격자 파일', true, true);
EXCEPTION WHEN others THEN
  PERFORM _t_fail('결합축 격자 파일 1건이 거절됐다: ' || SQLERRM);
END $$;
SELECT _t_must_reject(_t_file('C7', '기준 격자 파일', true, false),
                      '결합축 1건 + 위도 1건이 함께 들어갔다');
SELECT _t_must_reject(_t_file('C8', '기준 격자 파일', true, true),
                      '결합축이 2건 들어갔다');
ROLLBACK TO SAVEPOINT s_combined;

-- ════════════════════════════════════════════════════════════════════════════
-- D. d5_* 업로드 원장이 실재한다 (P2-EXEC §4 W1 ⑵ · 〈63〉-㉱ · 〈64〉)
-- ════════════════════════════════════════════════════════════════════════════
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['d5_upload', 'd5_upload_file', 'd5_pipeline_event'] LOOP
    IF NOT EXISTS (SELECT 1 FROM pg_class
                    WHERE relname = t AND relnamespace = 'public'::regnamespace AND relkind = 'r') THEN
      PERFORM _t_fail(format('%s 테이블이 없다', t));
    END IF;
    -- lab_id 가 없으면 경계를 걸 자리 자체가 없다 (CLAUDE.md §3-5)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_name = t AND column_name = 'lab_id') THEN
      PERFORM _t_fail(format('%s 에 lab_id 가 없다', t));
    END IF;
    -- ENABLE 만으로는 부족하다 — 소유자에게도 걸리게 FORCE 까지
    IF NOT EXISTS (SELECT 1 FROM pg_class
                    WHERE relname = t AND relnamespace = 'public'::regnamespace
                      AND relrowsecurity AND relforcerowsecurity) THEN
      PERFORM _t_fail(format('%s 에 RLS ENABLE+FORCE 가 둘 다 켜져 있지 않다', t));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies
                    WHERE tablename = t AND policyname = 'lab_boundary') THEN
      PERFORM _t_fail(format('%s 에 lab_boundary 정책이 없다', t));
    END IF;
  END LOOP;
END $$;

-- ════════════════════════════════════════════════════════════════════════════
-- E. 원장의 축 열 — D3 와 같은 두 불리언 · 같은 두 CHECK
--    (등록 전환 때 뒤늦게 터지지 않게 원장이 같은 모양을 미리 강제한다)
-- ════════════════════════════════════════════════════════════════════════════
INSERT INTO d5_upload (id, lab_id, uploader_account_id, expires_at) VALUES
  ('0000000000000000000000PKG1', '0000000000000000000000000T', '00000000000000000000000TP1',
   now() + interval '1 day');

CREATE FUNCTION _t_ufile(id text, kind text, lat boolean, lon boolean) RETURNS text
  LANGUAGE sql IMMUTABLE AS $$
  SELECT format(
    'INSERT INTO d5_upload_file (id, lab_id, upload_id, kind, file_name, storage_key, carries_lat, carries_lon)'
    ' VALUES (%L, ''0000000000000000000000000T'', ''0000000000000000000000PKG1'', %L, %L, %L, %L, %L)',
    _t_ulid(id), kind, id || '.dat', 'u/' || id, lat, lon)
$$;

SELECT _t_must_reject(_t_ufile('E1', '기준 격자 파일', false, false),
                      '원장에 축 없는 격자 파일이 들어갔다');
SELECT _t_must_reject(_t_ufile('E2', '본체', true, false),
                      '원장에 축 붙은 본체가 들어갔다');

SAVEPOINT s_u;
DO $$
BEGIN
  EXECUTE _t_ufile('E3', '기준 격자 파일', true, false);
  EXECUTE _t_ufile('E4', '기준 격자 파일', false, true);
EXCEPTION WHEN others THEN
  PERFORM _t_fail('원장에 위도·경도 한 쌍이 못 들어갔다: ' || SQLERRM);
END $$;
SELECT _t_must_reject(_t_ufile('E5', '기준 격자 파일', true, true),
                      '한 업로드 안에 위도 1건 + 결합축 1건이 함께 들어갔다');
ROLLBACK TO SAVEPOINT s_u;

-- ════════════════════════════════════════════════════════════════════════════
-- F. 멱등 키 유일 제약 — 같은 사실이 outbox 에 두 줄로 서지 않는다
--    (S2 완료 판정이 재전달 멱등을 요구하고 PoC 에 선례가 없다 — P2.md §10-(나))
-- ════════════════════════════════════════════════════════════════════════════
INSERT INTO d5_pipeline_event
  (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,
   idempotency_key, payload)
VALUES
  ('0000000000000000000000EVT1', '0000000000000000000000000T', '00000000000000000000000TP1',
   '0000000000000000000000PKG1', 'upload.accepted', '1.0', 'core-api',
   'upload.accepted:0000000000000000000000PKG1', '{}'::jsonb);

SELECT _t_must_reject(
  'INSERT INTO d5_pipeline_event (id, lab_id, actor_account_id, upload_id, event_type,'
  ' schema_version, source, idempotency_key, payload) VALUES'
  ' (''0000000000000000000000EVT2'', ''0000000000000000000000000T'', ''00000000000000000000000TP1'','
  ' ''0000000000000000000000PKG1'', ''upload.accepted'', ''1.0'', ''core-api'','
  ' ''upload.accepted:0000000000000000000000PKG1'', ''{}''::jsonb)',
  '같은 멱등 키가 두 번 들어갔다 — 재전달 멱등이 DB 층에서 안 지켜진다');

-- 이벤트 종류는 계약의 7종뿐이다 (envelope.json EventType). 여덟 번째를 DB 가 받지 않는다.
SELECT _t_must_reject(
  'INSERT INTO d5_pipeline_event (id, lab_id, actor_account_id, upload_id, event_type,'
  ' schema_version, source, idempotency_key, payload) VALUES'
  ' (''0000000000000000000000EVT3'', ''0000000000000000000000000T'', ''00000000000000000000000TP1'','
  ' ''0000000000000000000000PKG1'', ''upload.reticulated'', ''1.0'', ''core-api'','
  ' ''upload.reticulated:0000000000000000000000PKG1'', ''{}''::jsonb)',
  '계약에 없는 이벤트 종류가 들어갔다');

ROLLBACK;
