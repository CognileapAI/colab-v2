-- 0017 구조 오라클 — **두 표의 CHECK 가 실제로 3값인가**를 빈 DB 에서 잰다.
--
-- 완료 판정 축자 (`R-B-1-db.md §5` WU-B4) — 「`state` 3값 ＋ `default_visibility` 3값이
-- **둘 다** 선다」. ⛔ 한쪽만 넓히면 연구실 기본값이 표현 못 하는 상태가 생긴다.
--
-- ⭑ **정의문을 grep 하지 않는다** — 제약은 텍스트가 아니라 **받아들이는·거부하는 동작**이다.
--    그래서 아래는 전부 「넣어 보고 되는가·거부되는가」로 잰다.
\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0017 오라클 실패 — %', msg; END $$;

-- 재료. 여기까지는 `postgres`(superuser · RLS 우회)로 심는다 — 경계를 재는 것은 C 다.
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z'),
  ('0000000000000000000000000B', 'B 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                        uploaded_at, last_modified_at) VALUES
  ('000000000000000000000DSC1A', '0000000000000000000000000T', '00000000000000000000000TP1',
   '00000000000000000000000TP1', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
SET app.current_lab = '0000000000000000000000000T';

-- ── A. 데이터셋 상태가 3값을 받는다 ──────────────────────────────────────
-- A-⑴ 셋이 **다 들어간다**. 하나라도 막히면 0017 이 안 섰다.
DO $$
DECLARE v text;
BEGIN
  FOREACH v IN ARRAY ARRAY['열림', '잠김', '지정 공개'] LOOP
    BEGIN
      INSERT INTO d2_dataset_access (dataset_id, lab_id, state)
        VALUES ('000000000000000000000DSC1A', '0000000000000000000000000T', v)
        ON CONFLICT (dataset_id) DO UPDATE SET state = EXCLUDED.state;
    EXCEPTION WHEN check_violation THEN
      PERFORM _t_fail(format('d2_dataset_access.state 가 %L 를 거부한다 — CHECK 가 아직 2값이다', v));
    END;
  END LOOP;
END $$;

-- A-⑵ **NULL 은 그대로 허용된다** — 「따로 정하지 않음」이 연구실 기본값으로 떨어지는
--     COALESCE 경로다(P-27). 3값 확장이 그 자리를 닫으면 안 된다.
DO $$
BEGIN
  UPDATE d2_dataset_access SET state = NULL WHERE dataset_id = '000000000000000000000DSC1A';
EXCEPTION WHEN check_violation THEN
  PERFORM _t_fail('state 가 NULL 을 거부한다 — 연구실 기본값 경로가 막혔다');
END $$;

-- A-⑶ **4번째 값은 거부된다** — 넓힌 것이 「아무 문자열이나」가 아니다.
DO $$
BEGIN
  UPDATE d2_dataset_access SET state = '전체 공개' WHERE dataset_id = '000000000000000000000DSC1A';
  PERFORM _t_fail('state 가 3값 밖 문자열을 받았다 — CHECK 가 통째로 사라졌다');
EXCEPTION WHEN check_violation THEN NULL;
END $$;

-- ── B. 연구실 기본값도 **같은 3값**이다 ──────────────────────────────────
-- B-⑴ 셋이 다 들어간다. ⛔ 한쪽만 넓히면 여기서 red 다.
DO $$
DECLARE v text;
BEGIN
  INSERT INTO d1_lab_profile (lab_id, default_visibility)
    VALUES ('0000000000000000000000000T', '열림')
    ON CONFLICT (lab_id) DO NOTHING;
  FOREACH v IN ARRAY ARRAY['열림', '잠김', '지정 공개'] LOOP
    BEGIN
      UPDATE d1_lab_profile SET default_visibility = v
       WHERE lab_id = '0000000000000000000000000T';
    EXCEPTION WHEN check_violation THEN
      PERFORM _t_fail(format('d1_lab_profile.default_visibility 가 %L 를 거부한다 — 두 표 중 한쪽만 넓혔다', v));
    END;
  END LOOP;
END $$;

-- B-⑵ 4번째 값은 거부된다.
DO $$
BEGIN
  UPDATE d1_lab_profile SET default_visibility = '전체 공개'
   WHERE lab_id = '0000000000000000000000000T';
  PERFORM _t_fail('default_visibility 가 3값 밖 문자열을 받았다');
EXCEPTION WHEN check_violation THEN NULL;
END $$;

-- B-⑶ **NOT NULL 은 그대로다** — 기본값 열은 비울 수 없다(현행 유지).
DO $$
BEGIN
  UPDATE d1_lab_profile SET default_visibility = NULL
   WHERE lab_id = '0000000000000000000000000T';
  PERFORM _t_fail('default_visibility 가 NULL 을 받았다 — NOT NULL 이 사라졌다');
EXCEPTION WHEN not_null_violation THEN NULL;
END $$;
UPDATE d1_lab_profile SET default_visibility = '열림'
 WHERE lab_id = '0000000000000000000000000T';

-- ── C. 접근 판정이 안 바뀌었다 — `지정 공개` 는 **grant 갈래**를 탄다 ────
-- ⭑ **경계·본체 검사는 비소유자 롤로 한다.** `postgres` 는 superuser 라 RLS 를 언제나
--    우회한다 — 그 롤로 「안 보인다」를 재면 전부 거짓 green 이다.
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key,
                     carries_lat, carries_lon) VALUES
  ('00000000000000000000000FC1', '0000000000000000000000000T', '000000000000000000000DSC1A',
   '본체', 'c1.nc', 10, 'k/c1', false, false);
UPDATE d2_dataset_access SET state = '지정 공개' WHERE dataset_id = '000000000000000000000DSC1A';

CREATE ROLE t_app NOLOGIN NOSUPERUSER NOBYPASSRLS;
GRANT USAGE ON SCHEMA public TO t_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO t_app;
SET ROLE t_app;
SET app.current_account = '00000000000000000000000TP1';

-- C-⑴ 음성 — `지정 공개` ∧ 유효 grant 0건이면 본체는 **잠김과 같이** 0행이다.
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id = '000000000000000000000DSC1A';
  IF n <> 0 THEN
    PERFORM _t_fail(format('허용 목록이 빈 지정 공개의 본체가 %s 행 보인다 — body_access 가 3값에 열렸다', n));
  END IF;
END $$;

RESET ROLE;
INSERT INTO d2_dataset_access_grant
  (id, lab_id, dataset_id, grantee_account_id, approver_account_id, approved_at, expires_at)
VALUES ('0000000000000000000000GRC1', '0000000000000000000000000T', '000000000000000000000DSC1A',
        '00000000000000000000000TP1', '00000000000000000000000TP1',
        now(), now() + interval '6 months');
SET ROLE t_app;

-- C-⑵ 양성 — 유효 grant 한 줄이면 **종전과 같이** 열린다(판정 함수 무수정의 증명).
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d3_file WHERE dataset_id = '000000000000000000000DSC1A';
  IF n <> 1 THEN
    PERFORM _t_fail(format('허용자에게 지정 공개의 본체가 %s 행이다 (기대 1) — grant 갈래가 끊겼다', n));
  END IF;
END $$;

-- C-⑶ cross-tenant 음성 — 다른 연구실 스코프에서는 **상태 행 자체가 0건**이다.
SET app.current_lab = '0000000000000000000000000B';
DO $$
DECLARE n bigint;
BEGIN
  SELECT count(*) INTO n FROM d2_dataset_access;
  IF n <> 0 THEN
    PERFORM _t_fail(format('B 스코프에서 T 의 접근 상태 행이 %s 건 보인다 — 3값이 경계를 열었다', n));
  END IF;
END $$;

RESET ROLE;
ROLLBACK;
