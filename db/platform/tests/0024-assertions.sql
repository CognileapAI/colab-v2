-- 0024 오라클 — 프로필/기본 격자/첫 파일 임시 업로드 자리와 경계.
\set ON_ERROR_STOP on
BEGIN;

DO $$
DECLARE t text; forced boolean; policies integer;
BEGIN
  FOREACH t IN ARRAY ARRAY['d3_dataset_grid_profile','d3_lab_default_grid','d5_upload_grid_profile'] LOOP
    SELECT relforcerowsecurity INTO forced FROM pg_class WHERE oid=t::regclass;
    IF forced IS DISTINCT FROM true THEN
      RAISE EXCEPTION '0024 오라클 실패 — % FORCE RLS가 아니다', t;
    END IF;
    SELECT count(*) INTO policies FROM pg_policy WHERE polrelid=t::regclass AND polname='lab_boundary';
    IF policies <> 1 THEN
      RAISE EXCEPTION '0024 오라클 실패 — % lab_boundary가 %건이다', t, policies;
    END IF;
  END LOOP;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                  WHERE table_name='d5_upload_transfer' AND column_name='early_preview_upload_id') THEN
    RAISE EXCEPTION '0024 오라클 실패 — early_preview_upload_id가 없다';
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
INSERT INTO d3_dataset_grid_profile
 (dataset_id,lab_id,body_shape,grid_shape,grid_digest,grid_format_signature,
  west,south,east,north,map_state,grid_source)
VALUES
 ('00000000000000000000000DS1','0000000000000000000000000T',ARRAY[2,2],ARRAY[2,2],
  repeat('a',64),'NumPy+NumPy',121.9,31.1,133.6,43.3,'지도 있음','직접 업로드');
INSERT INTO d3_lab_default_grid (lab_id,dataset_id,set_by) VALUES
 ('0000000000000000000000000T','00000000000000000000000DS1','00000000000000000000000TP1');

INSERT INTO d5_upload (id,lab_id,uploader_account_id,expires_at) VALUES
 ('00000000000000000000000XP1','0000000000000000000000000T',
  '00000000000000000000000TP1',now()+interval '1 day');
INSERT INTO d5_upload_grid_profile
 (upload_id,lab_id,body_shape,map_state,grid_source) VALUES
 ('00000000000000000000000XP1','0000000000000000000000000T',ARRAY[2,2],
  '지도 없음','직접 업로드');

DO $$ BEGIN
  BEGIN
    UPDATE d3_dataset_grid_profile SET body_shape=ARRAY[2,2,2]
     WHERE dataset_id='00000000000000000000000DS1';
    RAISE EXCEPTION '0024 오라클 실패 — 3차원 body_shape가 들어갔다';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  BEGIN
    UPDATE d5_upload_grid_profile SET grid_digest='not-sha256'
     WHERE upload_id='00000000000000000000000XP1';
    RAISE EXCEPTION '0024 오라클 실패 — 잘못된 digest가 들어갔다';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  BEGIN
    UPDATE d5_upload_grid_profile SET west=1, south=NULL, east=2, north=3
     WHERE upload_id='00000000000000000000000XP1';
    RAISE EXCEPTION '0024 오라클 실패 — 반쪽 bounds가 들어갔다';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
END $$;

ROLLBACK;
