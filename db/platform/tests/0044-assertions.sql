-- 0044 오라클 — `d3_search_evidence` 의 운영자 전 연구실 **읽기** 정책.
--
-- 이 파일 하나가 `0044-drift.sh` 의 세 경우에서 똑같이 돈다.
--   · 0044 적용 후      → 전부 통과해야 한다 (green)
--   · 0043 까지만       → 반드시 실패해야 한다 (red)   ← 「되돌리면 red」의 실물
--   · 0044 downgrade 후 → 반드시 실패해야 한다 (red)
--
-- 재는 주장 (intent 2026-09-25-operator-search-scope.md §설계트리 Q7) —
--   ① 정책이 있고 `0029` 와 같은 모양이다 — FOR SELECT · PERMISSIVE · `is_operator_read()`
--   ② 경계 정책(`lab_boundary`)과 본체 정책(RESTRICTIVE `body_access`)은 그대로다
--   ③ 행동 — 스위치가 꺼져 있으면 남의 연구실 근거가 안 보이고, 켜면 보인다.
--      무소속 운영자(`app.current_lab` 빈 값)도 켜면 보인다 — 이슈 #158 의 주체가 이것이다.
--   ④ 켜져 있어도 남의 연구실 근거를 **고치지도 지우지도 넣지도 못한다** — 쓰기는 `lab_boundary`.
--
-- ⚠ 판정은 **비소유자 롤**로 한다. 이 파일을 적용하는 `postgres` 는 superuser 라 RLS 를
--   통째로 우회한다 — 그 자리에서 잰 값은 정책에 대해 아무것도 말하지 않는다(`0029-assertions.sql`).
--
-- 근거 = db/platform/versions/0044_evidence_operator_read.py

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0044 오라클 실패 — %', msg; END $$;

-- ── ①·② 카탈로그 ───────────────────────────────────────────────────────────
DO $$
DECLARE n integer; cmd "char"; permissive boolean; qual text;
BEGIN
  SELECT count(*) INTO n FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid
   WHERE c.relname = 'd3_search_evidence' AND p.polname = 'operator_read';
  IF n <> 1 THEN PERFORM _t_fail(format('①-a operator_read 정책이 %s건이다 (기대 1)', n)); END IF;
  SELECT p.polcmd, p.polpermissive, pg_get_expr(p.polqual, p.polrelid) INTO cmd, permissive, qual
    FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid
   WHERE c.relname = 'd3_search_evidence' AND p.polname = 'operator_read';
  IF cmd <> 'r' THEN PERFORM _t_fail(format('①-b SELECT 밖의 명령에 걸렸다 (polcmd=%s) — 쓰기가 열린다', cmd)); END IF;
  IF NOT permissive THEN PERFORM _t_fail('①-c RESTRICTIVE 다 — AND 로 합쳐져 모든 읽기를 막는다'); END IF;
  IF qual IS DISTINCT FROM 'is_operator_read()' THEN
    PERFORM _t_fail(format('①-d 조건이 스위치 하나가 아니다: %s', coalesce(qual, 'NULL')));
  END IF;
  SELECT count(*) INTO n FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid
   WHERE c.relname = 'd3_search_evidence' AND p.polname = 'lab_boundary' AND p.polcmd = '*';
  IF n <> 1 THEN PERFORM _t_fail('②-a lab_boundary(FOR ALL) 가 없다'); END IF;
  SELECT count(*) INTO n FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid
   WHERE c.relname = 'd3_search_evidence' AND p.polname = 'body_access' AND NOT p.polpermissive;
  IF n <> 1 THEN PERFORM _t_fail('②-b RESTRICTIVE body_access 가 없다'); END IF;
END $$;

-- ── 재료 — 두 연구실, 나 연구실에만 검토된 근거 한 건 ───────────────────────
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000EV0A', '0044 연구실 가', '2020-01-01T00:00:00Z'),
  ('0000000000000000000000EV0B', '0044 연구실 나', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('0000000000000000000000EVAA', '0000000000000000000000EV0A', '가 구성원', 'ev-a@oracle.test'),
  ('0000000000000000000000EVAB', '0000000000000000000000EV0B', '나 교수',   'ev-b@oracle.test');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id) VALUES
  ('0000000000000000000000EVD1', '0000000000000000000000EV0B',
   '0000000000000000000000EVAB', '0000000000000000000000EVAB');
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, storage_key) VALUES
  ('0000000000000000000000EVF1', '0000000000000000000000EV0B', '0000000000000000000000EVD1',
   '본체', 'rain.nc', 'oracle/0044/rain.nc'),
  ('0000000000000000000000EVF2', '0000000000000000000000EV0B', '0000000000000000000000EVD1',
   '본체', 'rain-2.nc', 'oracle/0044/rain-2.nc');
INSERT INTO d3_search_evidence (file_id, lab_id, dataset_id, file_revision, revision, status, facts,
                                source_label, source_locator, source_text, source_sha256,
                                reviewed_by, reviewed_at) VALUES
  ('0000000000000000000000EVF1', '0000000000000000000000EV0B', '0000000000000000000000EVD1',
   1, 1, 'reviewed', '{"variable": "precipitation"}', '0044 오라클', '1절', '강수',
   repeat('a', 64), '0000000000000000000000EVAB', now());

CREATE ROLE _0044_probe NOSUPERUSER NOBYPASSRLS;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO _0044_probe;
GRANT INSERT, UPDATE, DELETE ON d3_search_evidence TO _0044_probe;

-- ── ③·④ 행동 — 비소유자 롤로 잰다 ───────────────────────────────────────────
DO $$
DECLARE seen integer; touched integer; refused boolean := false;
BEGIN
  SET LOCAL ROLE _0044_probe;
  PERFORM set_config('app.current_lab', '0000000000000000000000EV0A', true);
  PERFORM set_config('app.current_account', '0000000000000000000000EVAA', true);
  -- 운영자는 본체 관리자다(`kernel/scope.py` · 0033) — body_access 는 그 갈래로 열린다.
  PERFORM set_config('app.operator_manage', 'on', true);

  -- ③-a 스위치가 꺼져 있으면 남의 연구실 근거는 보이지 않는다.
  PERFORM set_config('app.operator_read', '', true);
  SELECT count(*) INTO seen FROM d3_search_evidence WHERE lab_id = '0000000000000000000000EV0B';
  IF seen <> 0 THEN PERFORM _t_fail('③-a 스위치가 꺼졌는데 남의 연구실 근거가 보인다'); END IF;

  -- ③-b 켜면 보인다.
  PERFORM set_config('app.operator_read', 'on', true);
  SELECT count(*) INTO seen FROM d3_search_evidence WHERE lab_id = '0000000000000000000000EV0B';
  IF seen <> 1 THEN PERFORM _t_fail(format('③-b 운영자 읽기 스위치가 남의 연구실 근거를 열지 못했다 (%s행)', seen)); END IF;

  -- ③-c 무소속 운영자(연구실 GUC 빈 값)도 켜면 보인다 — 이슈 #158 의 주체.
  PERFORM set_config('app.current_lab', '', true);
  SELECT count(*) INTO seen FROM d3_search_evidence;
  IF seen < 1 THEN PERFORM _t_fail('③-c 무소속 운영자에게 검토된 근거가 0행이다'); END IF;
  PERFORM set_config('app.current_lab', '0000000000000000000000EV0A', true);

  -- ④ 켜져 있어도 한 행도 고치거나 지우지 못한다. 쓰기 판정은 여전히 `lab_boundary` 다.
  UPDATE d3_search_evidence SET source_label = '고쳐졌다' WHERE file_id = '0000000000000000000000EVF1';
  GET DIAGNOSTICS touched = ROW_COUNT;
  IF touched <> 0 THEN PERFORM _t_fail(format('④-a 남의 연구실 근거가 고쳐졌다 (%s행)', touched)); END IF;
  DELETE FROM d3_search_evidence WHERE file_id = '0000000000000000000000EVF1';
  GET DIAGNOSTICS touched = ROW_COUNT;
  IF touched <> 0 THEN PERFORM _t_fail(format('④-b 남의 연구실 근거가 지워졌다 (%s행)', touched)); END IF;
  BEGIN
    INSERT INTO d3_search_evidence (file_id, lab_id, dataset_id, file_revision, revision, status,
                                    facts, source_label, source_locator, source_text, source_sha256)
    VALUES ('0000000000000000000000EVF2', '0000000000000000000000EV0B', '0000000000000000000000EVD1',
            1, 1, 'draft', '{"variable": "precipitation"}', '넣기', '1절', '강수', repeat('b', 64));
  EXCEPTION WHEN insufficient_privilege THEN
    refused := true;
  END;
  IF NOT refused THEN PERFORM _t_fail('④-c 남의 연구실로 근거가 들어갔다'); END IF;
END $$;

ROLLBACK;
