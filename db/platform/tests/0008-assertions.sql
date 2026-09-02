-- 0008 이후의 DB 가 실제로 무엇을 하는가 — 프리사인드 전송 원장 오라클 본체.
--
-- 이 파일 하나가 `0008-drift.sh` 의 세 경우 전부에서 **똑같이** 돈다.
--   · 0008 적용 후      → 전부 통과해야 한다 (green)
--   · 0007 까지만       → 반드시 실패해야 한다 (red)   ← 「되돌리면 red」의 실물
--   · 0008 downgrade 후 → 반드시 실패해야 한다 (red)
--
-- **존재 확인만 하지 않는다** (0005·0006 과 같은 규율) — 행을 실제로 넣고,
-- 제약이 실제로 막는지(멀티파트 id 는 파트 크기 없이 못 선다), FORCE RLS 가
-- 실제로 켜져 있는지까지 본다.
--
-- 근거 = PLAN-SoT §9 〈276〉·〈277〉 (프리사인드 전송 원장 · relative_path 메타)

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0008 오라클 실패 — %', msg; END $$;

-- ── 재료 ────────────────────────────────────────────────────────────────────
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');

-- ── ① 전송 원장에 행이 서는가 (relative_path 포함) ─────────────────────────
INSERT INTO d5_upload_transfer (id, lab_id, uploader_account_id, source_label, expires_at)
VALUES ('0000000000000000000000TR01', '0000000000000000000000000T',
        '00000000000000000000000TP1', '시험 묶음', now() + interval '72 hours');
INSERT INTO d5_upload_transfer_file
  (id, lab_id, transfer_id, kind, file_name, relative_path, byte_size, storage_key, part_size)
VALUES ('0000000000000000000000TF01', '0000000000000000000000000T',
        '0000000000000000000000TR01', '본체', '작은.nc', '기상/작은.nc', 1024,
        'uploads/0000000000000000000000TR01/0000000000000000000000TF01', NULL);

DO $$ BEGIN
  IF (SELECT relative_path FROM d5_upload_transfer_file
       WHERE id = '0000000000000000000000TF01') <> '기상/작은.nc' THEN
    PERFORM _t_fail('전송 파일의 relative_path 가 보존되지 않았다');
  END IF;
END $$;

-- ── ② 제약 — 멀티파트 id 는 파트 크기 없이 못 선다 ──────────────────────────
DO $$ BEGIN
  BEGIN
    INSERT INTO d5_upload_transfer_file
      (id, lab_id, transfer_id, kind, file_name, byte_size, storage_key,
       part_size, transfer_ref)
    VALUES ('0000000000000000000000TF02', '0000000000000000000000000T',
            '0000000000000000000000TR01', '본체', '큰.nc', 99, 'k/tf02', NULL, 'mp-1');
    PERFORM _t_fail('part_size 없는 transfer_ref 가 통과했다 — 단일 PUT 에 멀티파트 id 가 붙는다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;

-- ── ③ d5_upload_file.relative_path — 접수 승계 자리가 실재하는가 ────────────
INSERT INTO d5_upload (id, lab_id, uploader_account_id, expires_at) VALUES
  ('0000000000000000000000WP01', '0000000000000000000000000T',
   '00000000000000000000000TP1', now() + interval '24 hours');
INSERT INTO d5_upload_file
  (id, lab_id, upload_id, kind, file_name, byte_size, storage_key, relative_path)
VALUES ('0000000000000000000000TF01', '0000000000000000000000000T',
        '0000000000000000000000WP01', '본체', '작은.nc', 1024, 'k/up01', '기상/작은.nc');
DO $$ BEGIN
  IF (SELECT relative_path FROM d5_upload_file
       WHERE id = '0000000000000000000000TF01') <> '기상/작은.nc' THEN
    PERFORM _t_fail('d5_upload_file.relative_path 가 보존되지 않았다');
  END IF;
END $$;

-- ── ④ FORCE RLS — 관례가 아니라 엔진에 물어본다 ─────────────────────────────
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_class
              WHERE relname IN ('d5_upload_transfer', 'd5_upload_transfer_file')
                AND NOT relforcerowsecurity) THEN
    PERFORM _t_fail('전송 원장에 FORCE ROW LEVEL SECURITY 가 꺼져 있다');
  END IF;
END $$;

ROLLBACK;
