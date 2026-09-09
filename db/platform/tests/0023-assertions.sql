-- 0023 오라클 — 사람 격자 설명과 대표 그림 원장·제약·RLS·cascade.
\set ON_ERROR_STOP on
BEGIN;

DO $$
DECLARE forced boolean; cleanup_forced boolean; policy_count integer; delete_action "char";
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_schema='public' AND table_name='d3_dataset_description'
                    AND column_name='human_grid_description' AND is_nullable='YES') THEN
    RAISE EXCEPTION '0023 오라클 실패 — nullable human_grid_description이 없다';
  END IF;
  SELECT relforcerowsecurity INTO forced FROM pg_class
   WHERE oid='d3_dataset_representative_image'::regclass;
  IF forced IS DISTINCT FROM true THEN
    RAISE EXCEPTION '0023 오라클 실패 — 대표 그림 표 FORCE RLS가 아니다';
  END IF;
  SELECT count(*) INTO policy_count FROM pg_policy
   WHERE polrelid='d3_dataset_representative_image'::regclass AND polname='lab_boundary';
  IF policy_count <> 1 THEN
    RAISE EXCEPTION '0023 오라클 실패 — 대표 그림 lab_boundary 정책이 %건이다', policy_count;
  END IF;
  SELECT relforcerowsecurity INTO cleanup_forced FROM pg_class
   WHERE oid='d3_representative_image_cleanup'::regclass;
  IF cleanup_forced IS DISTINCT FROM true THEN
    RAISE EXCEPTION '0023 오라클 실패 — 대표 그림 cleanup 표 FORCE RLS가 아니다';
  END IF;
  SELECT count(*) INTO policy_count FROM pg_policy
   WHERE polrelid='d3_representative_image_cleanup'::regclass AND polname='lab_boundary';
  IF policy_count <> 1 THEN
    RAISE EXCEPTION '0023 오라클 실패 — cleanup lab_boundary 정책이 %건이다', policy_count;
  END IF;
  SELECT confdeltype INTO delete_action FROM pg_constraint
   WHERE conrelid='d3_dataset_representative_image'::regclass AND contype='f'
     AND confrelid='d3_dataset'::regclass;
  IF delete_action IS DISTINCT FROM 'c' THEN
    RAISE EXCEPTION '0023 오라클 실패 — dataset FK가 ON DELETE CASCADE가 아니다';
  END IF;
END $$;

INSERT INTO d1_lab (id,name,opened_at) VALUES
 ('0000000000000000000000000T','T 연구실','2020-01-01T00:00:00Z');
INSERT INTO d1_account (id,lab_id,name,email) VALUES
 ('00000000000000000000000TP1','0000000000000000000000000T','T 교수','t@example.test');
SET app.current_lab='0000000000000000000000000T';
INSERT INTO d3_dataset (id,lab_id,owner_account_id,uploader_account_id) VALUES
 ('00000000000000000000000DS1','0000000000000000000000000T',
  '00000000000000000000000TP1','00000000000000000000000TP1');
INSERT INTO d3_dataset_description
 (dataset_id,lab_id,name,human_grid_description) VALUES
 ('00000000000000000000000DS1','0000000000000000000000000T','자료','사람 격자');
INSERT INTO d3_dataset_representative_image
 (dataset_id,lab_id,image_id,file_name,content_type,size_bytes,storage_key) VALUES
 ('00000000000000000000000DS1','0000000000000000000000000T',
  '00000000000000000000000PM1','대표.png','image/png',10,'representative-images/DS1/PM1');
INSERT INTO d3_representative_image_cleanup
 (cleanup_id,lab_id,dataset_id,storage_key) VALUES
 ('00000000000000000000000CN1','0000000000000000000000000T',
  '00000000000000000000000DS1','representative-images/DS1/OLD');
DELETE FROM d3_dataset_description WHERE dataset_id='00000000000000000000000DS1';
DELETE FROM d3_dataset WHERE id='00000000000000000000000DS1';
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM d3_dataset_representative_image
              WHERE dataset_id='00000000000000000000000DS1') THEN
    RAISE EXCEPTION '0023 오라클 실패 — dataset 삭제 뒤 대표 그림 행이 남았다';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM d3_representative_image_cleanup
                  WHERE dataset_id='00000000000000000000000DS1') THEN
    RAISE EXCEPTION '0023 오라클 실패 — dataset 삭제가 pending cleanup 추적도 지웠다';
  END IF;
END $$;
ROLLBACK;
