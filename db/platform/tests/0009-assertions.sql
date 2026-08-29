-- 0009 이후의 DB 가 실제로 무엇을 하는가 — 파일 관리 오라클 본체.
--
-- 이 파일 하나가 `0009-drift.sh` 의 네 경우 전부에서 **똑같이** 돈다.
--   · 0009 적용 후             → 전부 통과해야 한다 (green)
--   · 0008 까지만              → 반드시 실패해야 한다 (red)   ← 「되돌리면 red」의 실물
--   · 0009 downgrade 후        → 반드시 실패해야 한다 (red)
--   · 낡은 합계 위에 0009 적용 → 전부 통과해야 한다 (green) — ⑥ 이 여기서만 **비어 있지 않다**
--
-- **존재 확인만 하지 않는다** (0004~0008 과 같은 규율) — 행을 실제로 넣고 읽고, CHECK 가
-- 실제로 막는지, 트리거가 합계를 실제로 움직이는지(증가·이동·감소·NULL=0·행 없으면 건너뜀),
-- FORCE RLS 가 켜져 있는지, 백필 결과가 합계와 같은지까지 본다.
--
-- **제약·트리거 시험이지 RLS 시험이 아니다** — superuser 로 돈다. RLS 는 `rls-*` 게이트의 몫이고,
-- 백필의 RLS 창은 `0009-drift.sh ㈑` 이 소유자 롤(비superuser·NOBYPASSRLS)로 실물 적용해 본다.
--
-- 근거 = PLAN-SoT §9 〈175〉 (파일 관리 — relative_path 승계 · 파일 단위 내려받기 · 용량 합계 트리거)

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION _t_fail(msg text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION '0009 오라클 실패 — %', msg; END $$;

-- 합계 열이 기대값인지 되묻는다.
CREATE FUNCTION _t_total(ds char(26), expected bigint, msg text) RETURNS void LANGUAGE plpgsql AS $$
DECLARE got bigint;
BEGIN
  SELECT total_size_bytes INTO got FROM d3_dataset_autometa WHERE dataset_id = ds;
  IF got IS DISTINCT FROM expected THEN
    PERFORM _t_fail(format('%s — total_size_bytes 기대 %s, 실제 %s', msg, expected, got));
  END IF;
END $$;

-- ── ⑥-a 백필 — 이미 있던 모든 autometa 행의 합계가 d3_file 합계와 같은가 ──────
-- 빈 DB 에서는 대상 0건이다. 그래서 `0009-drift.sh ㈑` 이 낡은 값(999·NULL)을 심은 뒤
-- 0009 를 적용하고 이 파일을 다시 돌린다 — 그 경우에만 이 검사가 실제로 무언가를 잰다.
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM d3_dataset_autometa a
     WHERE a.total_size_bytes IS DISTINCT FROM
           (SELECT COALESCE(sum(f.size_bytes), 0) FROM d3_file f WHERE f.dataset_id = a.dataset_id)
  ) THEN
    PERFORM _t_fail('백필 뒤에도 total_size_bytes 가 d3_file 합계와 다른 행이 있다');
  END IF;
END $$;

-- ── 재료 ────────────────────────────────────────────────────────────────────
INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id) VALUES
  ('0000000000000000000000DST1', '0000000000000000000000000T',
   '00000000000000000000000TP1', '00000000000000000000000TP1'),
  ('0000000000000000000000DST2', '0000000000000000000000000T',
   '00000000000000000000000TP1', '00000000000000000000000TP1');
-- DST1 만 autometa 행이 있다 — 합계는 **NULL 로 시작**한다(NULL + n 이 NULL 로 물들지 않는지).
-- DST2 는 일부러 autometa 행이 없다 — 트리거가 오류 없이 건너뛰는지.
INSERT INTO d3_dataset_autometa (dataset_id, lab_id, total_size_bytes) VALUES
  ('0000000000000000000000DST1', '0000000000000000000000000T', NULL);

-- ── ① d3_file.relative_path — 넣고 읽는다 ───────────────────────────────────
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key, relative_path)
VALUES ('0000000000000000000000TF01', '0000000000000000000000000T',
        '0000000000000000000000DST1', '본체', '작은.nc', 100, 'k/tf01', '기상/작은.nc');
DO $$ BEGIN
  IF (SELECT relative_path FROM d3_file WHERE id = '0000000000000000000000TF01') <> '기상/작은.nc' THEN
    PERFORM _t_fail('d3_file.relative_path 가 보존되지 않았다');
  END IF;
END $$;
-- ④-a 본체 1건 INSERT → NULL 이던 합계가 100 이 된다
SELECT _t_total('0000000000000000000000DST1', 100, '④-a 본체 INSERT 뒤');

-- ── ② CHECK — 길이 0 과 1025 는 막히고 1024 는 선다 ─────────────────────────
DO $$ BEGIN
  BEGIN
    INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key, relative_path)
    VALUES ('0000000000000000000000TF9A', '0000000000000000000000000T',
            '0000000000000000000000DST1', '본체', 'x', 0, 'k/x9a', '');
    PERFORM _t_fail('길이 0 인 relative_path 가 통과했다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  BEGIN
    INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key, relative_path)
    VALUES ('0000000000000000000000TF9B', '0000000000000000000000000T',
            '0000000000000000000000DST1', '본체', 'x', 0, 'k/x9b', repeat('a', 1025));
    PERFORM _t_fail('길이 1025 인 relative_path 가 통과했다');
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key, relative_path)
VALUES ('0000000000000000000000TF9C', '0000000000000000000000000T',
        '0000000000000000000000DST1', '본체', 'x', 0, 'k/x9c', repeat('a', 1024));
DELETE FROM d3_file WHERE id = '0000000000000000000000TF9C';
SELECT _t_total('0000000000000000000000DST1', 100, '② 경계값(1024) 삽입·삭제 뒤 — 0 바이트라 합계 불변');

-- ── ④ 용량 합계 트리거 — 실제로 움직이는가 ──────────────────────────────────
-- ④-b size_bytes NULL 인 격자 파일은 0 으로 센다
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key, carries_lat, carries_lon)
VALUES ('0000000000000000000000TG01', '0000000000000000000000000T',
        '0000000000000000000000DST1', '기준 격자 파일', 'grid.nc', NULL, 'k/tg01', true, true);
SELECT _t_total('0000000000000000000000DST1', 100, '④-b size NULL 격자 INSERT 뒤');

-- ④-c 한 문장에 조각 둘 → 한 번에 더해진다
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key) VALUES
  ('0000000000000000000000TF02', '0000000000000000000000000T', '0000000000000000000000DST1', '본체', 'b.nc', 10, 'k/tf02'),
  ('0000000000000000000000TF03', '0000000000000000000000000T', '0000000000000000000000DST1', '본체', 'c.nc', 20, 'k/tf03');
SELECT _t_total('0000000000000000000000DST1', 130, '④-c 한 문장 2건 INSERT 뒤');

-- ④-d size_bytes UPDATE → 차이만큼 이동 (100 → 250 : +150)
UPDATE d3_file SET size_bytes = 250 WHERE id = '0000000000000000000000TF01';
SELECT _t_total('0000000000000000000000DST1', 280, '④-d size_bytes 100→250 UPDATE 뒤');

-- ④-e size_bytes 아닌 열만 UPDATE → 불변
UPDATE d3_file SET file_name = '이름만.nc' WHERE id = '0000000000000000000000TF01';
SELECT _t_total('0000000000000000000000DST1', 280, '④-e 이름만 UPDATE 뒤');

-- ④-f 다른 데이터셋으로 옮김 — 받는 쪽(DST2)은 autometa 행이 없다 → 오류 없이 건너뛰고
--     보내는 쪽(DST1)만 준다
UPDATE d3_file SET dataset_id = '0000000000000000000000DST2' WHERE id = '0000000000000000000000TF02';
SELECT _t_total('0000000000000000000000DST1', 270, '④-f 조각 10 을 DST2 로 옮긴 뒤');
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM d3_dataset_autometa WHERE dataset_id = '0000000000000000000000DST2') THEN
    PERFORM _t_fail('autometa 행이 없던 DST2 에 트리거가 행을 만들었다 — 만들면 안 된다');
  END IF;
END $$;

-- ④-g DELETE → 감소. size NULL 인 격자를 지워도 불변
DELETE FROM d3_file WHERE id = '0000000000000000000000TF03';
SELECT _t_total('0000000000000000000000DST1', 250, '④-g 조각 20 DELETE 뒤');
DELETE FROM d3_file WHERE id = '0000000000000000000000TG01';
SELECT _t_total('0000000000000000000000DST1', 250, '④-g size NULL 격자 DELETE 뒤');

-- ④-h autometa 행이 없는 데이터셋에 직접 INSERT/DELETE → 오류 없음
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key)
VALUES ('0000000000000000000000TF04', '0000000000000000000000000T',
        '0000000000000000000000DST2', '본체', 'd.nc', 7, 'k/tf04');
DELETE FROM d3_file WHERE id = '0000000000000000000000TF04';

-- ── ③ d8_download.file_id — NULL(묶음)과 값(파일 단위) 둘 다 선다 ────────────
INSERT INTO d8_download (id, lab_id, account_id, dataset_id, file_id) VALUES
  ('0000000000000000000000TD01', '0000000000000000000000000T', '00000000000000000000000TP1',
   '0000000000000000000000DST1', NULL),
  ('0000000000000000000000TD02', '0000000000000000000000000T', '00000000000000000000000TP1',
   '0000000000000000000000DST1', '0000000000000000000000TF01');
DO $$ BEGIN
  IF (SELECT file_id FROM d8_download WHERE id = '0000000000000000000000TD01') IS NOT NULL
     OR (SELECT file_id FROM d8_download WHERE id = '0000000000000000000000TD02')
        IS DISTINCT FROM '0000000000000000000000TF01' THEN
    PERFORM _t_fail('d8_download.file_id 가 NULL/값 그대로 보존되지 않았다');
  END IF;
END $$;
-- FK 가 없다 — 파일이 지워져도 이력은 남는다 (append-only 는 별개 트리거가 지킨다)
DELETE FROM d3_file WHERE id = '0000000000000000000000TF01';
DO $$ BEGIN
  IF (SELECT count(*) FROM d8_download WHERE file_id = '0000000000000000000000TF01') <> 1 THEN
    PERFORM _t_fail('파일을 지웠더니 파일 단위 내려받기 이력이 사라졌다 — FK 가 걸려 있다');
  END IF;
END $$;
SELECT _t_total('0000000000000000000000DST1', 0, '③ 마지막 본체(250) DELETE 뒤');

-- ── ⑤ FORCE RLS — 관례가 아니라 엔진에 물어본다 ─────────────────────────────
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_class
              WHERE relnamespace = 'public'::regnamespace
                AND relname IN ('d3_file', 'd8_download', 'd3_dataset_autometa')
                AND NOT relforcerowsecurity) THEN
    PERFORM _t_fail('d3_file · d8_download · d3_dataset_autometa 에 FORCE ROW LEVEL SECURITY 가 꺼져 있다');
  END IF;
END $$;

-- ── ⑥-b 이 파일이 움직인 뒤에도 모든 autometa 행의 합계 = d3_file 합계 ─────────
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM d3_dataset_autometa a
     WHERE a.total_size_bytes IS DISTINCT FROM
           (SELECT COALESCE(sum(f.size_bytes), 0) FROM d3_file f WHERE f.dataset_id = a.dataset_id)
  ) THEN
    PERFORM _t_fail('트리거가 움직인 뒤 total_size_bytes 가 d3_file 합계와 다른 행이 있다');
  END IF;
END $$;

ROLLBACK;
