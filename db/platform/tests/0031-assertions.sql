-- 0031 이후의 DB 가 실제로 무엇을 하는가 — 파일 내용 리비전 ＋ 근거 붙은 검색 사실 오라클 본체.
--
-- 이 파일 하나가 `0031-drift.sh` 의 세 경우에서 **똑같이** 돈다.
--   · 0031 적용 후               → 전부 통과해야 한다 (green)
--   · 0030 머지까지만            → 반드시 실패해야 한다 (red)   ← 「되돌리면 red」의 실물
--   · 0031 downgrade 후          → 반드시 실패해야 한다 (red)
--
-- **존재 확인만 하지 않는다** (0009 와 같은 규율) — 행을 실제로 넣고, 트리거가 리비전을
-- 실제로 올리는지(내용 열을 고칠 때만 · 이름만 고칠 때는 그대로), CHECK 가 실제로 막는지,
-- 복합 FK 가 실제로 CASCADE 하는지까지 본다.
--
-- **제약·트리거 시험이지 RLS 시험이 아니다** — superuser 로 돌아 RLS 를 통째로 우회한다.
-- 그래서 RLS 는 카탈로그(켜짐·FORCE·정책 두 벌)까지만 보고, 행 가시성은 `rls-*` 게이트의 몫이다.
--
-- 근거 = db/platform/versions/0031_search_evidence.py

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0031 오라클 실패 — %', msg; END $$;

-- 리비전 값을 되묻는다.
CREATE FUNCTION _t_rev(f char(26), expected integer, msg text) RETURNS void LANGUAGE plpgsql AS $$
DECLARE got integer;
BEGIN
  SELECT content_revision INTO got FROM d3_file WHERE id = f;
  IF got IS DISTINCT FROM expected THEN
    PERFORM _t_fail(format('%s — content_revision 기대 %s, 실제 %s', msg, expected, got));
  END IF;
END $$;

-- ── 재료 ────────────────────────────────────────────────────────────────────
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000SE01', 'SE 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('0000000000000000000000SE02', '0000000000000000000000SE01', 'SE 교수', 'se@oracle.test');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id) VALUES
  ('0000000000000000000000SED1', '0000000000000000000000SE01',
   '0000000000000000000000SE02', '0000000000000000000000SE02');
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key) VALUES
  ('0000000000000000000000SEF1', '0000000000000000000000SE01',
   '0000000000000000000000SED1', '본체', '관측.nc', 100, 'k/sef1');

-- ── ① content_revision — NOT NULL · 기본값 1 · CHECK(>0) 이 실제로 막는다 ────
SELECT _t_rev('0000000000000000000000SEF1', 1, '① 새 행의 기본값');
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
     WHERE table_name = 'd3_file' AND column_name = 'content_revision'
       AND is_nullable = 'NO' AND data_type = 'integer'
  ) THEN PERFORM _t_fail('① d3_file.content_revision 이 없거나 NOT NULL 정수가 아니다'); END IF;
  BEGIN
    UPDATE d3_file SET content_revision = 0 WHERE id = '0000000000000000000000SEF1';
    PERFORM _t_fail('① content_revision 0 이 통과했다 — CHECK(>0) 이 막지 않는다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;

-- ── ② 트리거 — **내용 열을 고칠 때만** 리비전이 오른다 ──────────────────────
-- 이것이 이 회차의 주장이다. 이름만 바뀐 파일은 같은 내용이므로 근거를 무효로 만들지 않는다.
UPDATE d3_file SET storage_key = 'k/sef1-v2' WHERE id = '0000000000000000000000SEF1';
SELECT _t_rev('0000000000000000000000SEF1', 2, '②-a storage_key 교체 뒤');
UPDATE d3_file SET size_bytes = 200 WHERE id = '0000000000000000000000SEF1';
SELECT _t_rev('0000000000000000000000SEF1', 3, '②-b size_bytes 교체 뒤');
UPDATE d3_file SET file_name = '관측-이름만바꿈.nc' WHERE id = '0000000000000000000000SEF1';
SELECT _t_rev('0000000000000000000000SEF1', 3, '②-c 이름만 바꿨을 때는 오르지 않아야 한다');

-- ── ③ d3_search_evidence — 넣고 읽는다 ──────────────────────────────────────
INSERT INTO d3_search_evidence
  (file_id, lab_id, dataset_id, file_revision, revision, status, facts,
   source_label, source_locator, source_text, source_sha256)
VALUES ('0000000000000000000000SEF1', '0000000000000000000000SE01',
        '0000000000000000000000SED1', 3, 1, 'draft', '{"변수": "강수량"}'::jsonb,
        '관측 설명서', '3쪽 표 2', '강수량은 mm 단위다.',
        '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef');
DO $$ BEGIN
  IF (SELECT facts->>'변수' FROM d3_search_evidence
       WHERE file_id = '0000000000000000000000SEF1') <> '강수량' THEN
    PERFORM _t_fail('③ d3_search_evidence.facts 가 보존되지 않았다');
  END IF;
END $$;

-- ── ④ CHECK — 카탈로그가 아니라 **막는지**를 본다 ───────────────────────────
DO $$ BEGIN
  -- ④-a 검토 짝 — reviewed 인데 검토자·검토시각이 비면 거절
  BEGIN
    UPDATE d3_search_evidence SET status = 'reviewed'
     WHERE file_id = '0000000000000000000000SEF1';
    PERFORM _t_fail('④-a 검토자 없는 reviewed 가 통과했다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  -- ④-b draft 인데 검토자가 붙으면 거절
  BEGIN
    UPDATE d3_search_evidence SET reviewed_by = '0000000000000000000000SE02'
     WHERE file_id = '0000000000000000000000SEF1';
    PERFORM _t_fail('④-b 검토자가 붙은 draft 가 통과했다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  -- ④-c 허용값 밖의 상태
  BEGIN
    UPDATE d3_search_evidence SET status = 'pending'
     WHERE file_id = '0000000000000000000000SEF1';
    PERFORM _t_fail('④-c 허용값 밖의 status 가 통과했다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  -- ④-d 빈 facts — 「근거 필드 필수」(CLAUDE.md §3)가 빈 객체로 충족되지 않는다
  BEGIN
    UPDATE d3_search_evidence SET facts = '{}'::jsonb
     WHERE file_id = '0000000000000000000000SEF1';
    PERFORM _t_fail('④-d 빈 facts 가 통과했다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  -- ④-e sha256 모양이 아닌 값
  BEGIN
    UPDATE d3_search_evidence SET source_sha256 = 'nothex'
     WHERE file_id = '0000000000000000000000SEF1';
    PERFORM _t_fail('④-e sha256 모양이 아닌 값이 통과했다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;
-- ④-f 짝을 갖춘 reviewed 는 선다 (막기만 하고 통과를 못 시키면 그 열은 쓸 수 없다)
UPDATE d3_search_evidence
   SET status = 'reviewed', reviewed_by = '0000000000000000000000SE02', reviewed_at = now()
 WHERE file_id = '0000000000000000000000SEF1';

-- ── ⑤ 복합 FK — 파일이 지워지면 근거도 따라 지워진다 (ON DELETE CASCADE) ────
DO $$ BEGIN
  -- 없는 파일을 가리키는 근거는 서지 못한다.
  BEGIN
    INSERT INTO d3_search_evidence
      (file_id, lab_id, dataset_id, file_revision, revision, status, facts,
       source_label, source_locator, source_text, source_sha256)
    VALUES ('0000000000000000000000SEF9', '0000000000000000000000SE01',
            '0000000000000000000000SED1', 1, 1, 'draft', '{"x": "y"}'::jsonb,
            'l', 'p', 't', repeat('a', 64));
    PERFORM _t_fail('⑤ 없는 파일을 가리키는 근거가 통과했다 — 복합 FK 가 걸려 있지 않다');
  EXCEPTION WHEN foreign_key_violation THEN NULL;
  END;
END $$;
DELETE FROM d3_file WHERE id = '0000000000000000000000SEF1';
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM d3_search_evidence WHERE file_id = '0000000000000000000000SEF1') THEN
    PERFORM _t_fail('⑤ 파일을 지웠는데 근거 행이 남았다 — CASCADE 가 걸려 있지 않다');
  END IF;
END $$;

-- ── ⑥ 연구실 경계 — RLS 가 켜져 있고 FORCE 이며 정책 두 벌이 걸려 있다 ──────
-- superuser 로는 가시성을 잴 수 없다. 여기서는 **스위치가 실제로 켜졌는가**까지 본다.
DO $$
DECLARE rls boolean; forced boolean; n integer;
BEGIN
  SELECT relrowsecurity, relforcerowsecurity INTO rls, forced
    FROM pg_class WHERE relname = 'd3_search_evidence';
  IF rls IS NOT TRUE THEN PERFORM _t_fail('⑥ d3_search_evidence 의 RLS 가 꺼져 있다'); END IF;
  IF forced IS NOT TRUE THEN PERFORM _t_fail('⑥ d3_search_evidence 의 FORCE RLS 가 꺼져 있다'); END IF;

  SELECT count(*) INTO n FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid
   WHERE c.relname = 'd3_search_evidence' AND p.polname = 'lab_boundary';
  IF n <> 1 THEN PERFORM _t_fail('⑥ lab_boundary 정책이 없다'); END IF;

  -- 본체 접근 정책은 **RESTRICTIVE** 여야 한다. PERMISSIVE 면 다른 정책과 OR 로 묶여
  -- 잠금이 풀린다 — 있다는 것과 제 몫을 하는 것은 다른 사실이다.
  SELECT count(*) INTO n FROM pg_policy p JOIN pg_class c ON c.oid = p.polrelid
   WHERE c.relname = 'd3_search_evidence' AND p.polname = 'body_access' AND p.polpermissive IS FALSE;
  IF n <> 1 THEN PERFORM _t_fail('⑥ body_access 정책이 없거나 RESTRICTIVE 가 아니다'); END IF;
END $$;

ROLLBACK;
