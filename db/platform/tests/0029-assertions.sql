-- 0029 오라클 — 운영자 전 연구실 읽기 정책.
-- 0028 판(이전 head)과 downgrade 판에서는 이 파일이 **실패해야** 한다.
--
-- 카탈로그만 보지 않는다. 스위치를 실제로 켜고 ⑴ 남의 연구실 행이 보이는지 ⑵ 그 행에 대한
-- UPDATE 가 여전히 **한 행도 바꾸지 못하는지** ⑶ 남의 연구실로의 INSERT 가 거절되는지를
-- 행동으로 확인한다 — 정책이 있다는 것과 정책이 의도대로 도는 것은 다른 사실이다.
--
-- ⚠ 판정은 **비소유자 롤**로 한다. 이 파일을 적용하는 `postgres` 는 superuser 라 RLS 를
--   통째로 우회한다 — 그 자리에서 잰 값은 정책에 대해 아무것도 말하지 않는다.
DO $$
DECLARE
  seen integer;
  touched integer;
  refused boolean := false;
BEGIN
  IF to_regprocedure('is_operator_read()') IS NULL THEN
    RAISE EXCEPTION '운영자 읽기 스위치 함수가 없다';
  END IF;

  -- 스위치가 선언되지 않으면 false 다. 없는 값을 참으로 읽으면 그 자리가 전면 개방이다.
  IF is_operator_read() THEN
    RAISE EXCEPTION '스위치가 선언되지 않았는데 켜진 것으로 읽힌다';
  END IF;

  IF (SELECT count(*) FROM pg_policy WHERE polname = 'operator_read') < 31 THEN
    RAISE EXCEPTION '운영자 읽기 정책이 테넌트 테이블 전부에 걸려 있지 않다';
  END IF;

  -- ⓐ 읽기 전용이어야 한다 — `polcmd` 가 'r'(SELECT) 이 아닌 것이 있으면 쓰기가 열린다.
  IF EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'operator_read' AND polcmd <> 'r') THEN
    RAISE EXCEPTION '운영자 읽기 정책이 SELECT 밖의 명령에 걸려 있다';
  END IF;

  -- ⓑ PERMISSIVE 여야 한다. RESTRICTIVE 면 AND 로 합쳐져 **모든 읽기를 막는다**.
  IF EXISTS (SELECT 1 FROM pg_policy WHERE polname = 'operator_read' AND NOT polpermissive) THEN
    RAISE EXCEPTION '운영자 읽기 정책이 RESTRICTIVE 다';
  END IF;

  -- ⓒ 경계 정책은 한 줄도 줄지 않았다.
  IF (SELECT count(*) FROM pg_policy WHERE polname = 'lab_boundary') < 31 THEN
    RAISE EXCEPTION '연구실 경계 정책이 줄었다';
  END IF;
END $$;

-- ── 행동 확인 — 비소유자 롤로 잰다 ───────────────────────────────────────────
CREATE ROLE _0028_probe NOSUPERUSER NOBYPASSRLS;
GRANT SELECT, INSERT, UPDATE, DELETE ON d1_lab_profile TO _0028_probe;
GRANT SELECT ON d1_lab TO _0028_probe;

INSERT INTO d1_lab(id, name, opened_at) VALUES
  ('00000000000000000000000281', '0028 시험 연구실 가', now()),
  ('00000000000000000000000282', '0028 시험 연구실 나', now());
INSERT INTO d1_lab_profile(lab_id) VALUES
  ('00000000000000000000000281'), ('00000000000000000000000282');

DO $$
DECLARE
  seen integer;
  touched integer;
  refused boolean := false;
BEGIN
  SET LOCAL ROLE _0028_probe;
  PERFORM set_config('app.current_lab', '00000000000000000000000281', true);

  -- 스위치가 꺼져 있으면 남의 연구실은 보이지 않는다.
  SELECT count(*) INTO seen FROM d1_lab_profile WHERE lab_id = '00000000000000000000000282';
  IF seen <> 0 THEN RAISE EXCEPTION '스위치가 꺼졌는데 남의 연구실이 보인다'; END IF;

  -- 켜면 보인다.
  PERFORM set_config('app.operator_read', 'on', true);
  SELECT count(*) INTO seen FROM d1_lab_profile WHERE lab_id = '00000000000000000000000282';
  IF seen <> 1 THEN RAISE EXCEPTION '운영자 읽기 스위치가 남의 연구실을 열지 못했다'; END IF;

  -- 켜져 있어도 **한 행도 바꾸지 못한다.** 쓰기 판정은 여전히 `lab_boundary` 다.
  UPDATE d1_lab_profile SET default_visibility = '잠김'   -- 기본값('열림')과 다른 값이어야 한다
   WHERE lab_id = '00000000000000000000000282';
  GET DIAGNOSTICS touched = ROW_COUNT;
  IF touched <> 0 THEN
    RAISE EXCEPTION '운영자 읽기 스위치가 켜진 채로 남의 연구실 행이 고쳐졌다 (% 행)', touched;
  END IF;

  DELETE FROM d1_lab_profile WHERE lab_id = '00000000000000000000000282';
  GET DIAGNOSTICS touched = ROW_COUNT;
  IF touched <> 0 THEN
    RAISE EXCEPTION '운영자 읽기 스위치가 켜진 채로 남의 연구실 행이 지워졌다 (% 행)', touched;
  END IF;

  -- 남의 연구실로의 INSERT 는 WITH CHECK 이 막는다 — 이쪽은 조용히 0 행이 아니라 오류다.
  BEGIN
    INSERT INTO d1_lab_profile(lab_id) VALUES ('00000000000000000000000282');
  EXCEPTION WHEN insufficient_privilege THEN
    refused := true;
  END;
  IF NOT refused THEN
    RAISE EXCEPTION '운영자 읽기 스위치가 켜진 채로 남의 연구실에 행이 들어갔다';
  END IF;
END $$;

DROP OWNED BY _0028_probe;
DROP ROLE _0028_probe;
DELETE FROM d1_lab_profile WHERE lab_id IN
  ('00000000000000000000000281', '00000000000000000000000282');
DELETE FROM d1_lab WHERE id IN
  ('00000000000000000000000281', '00000000000000000000000282');
