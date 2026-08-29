-- staging 부분 재시드 — D3/D4/D5 한정.
--
-- 배경 = 2026-08-25 손 DELETE 로 D3·D4·D5 전량 소실. D1·D2·D6·D8 은 생존.
--        `services/core-api/tests/fixtures/seed.sql` 전량 재적용은 생존 도메인에서 전건 중복.
--        조사 근거 = `dev-package/sessions/S2-BLOCKER-INVESTIGATION.md` §2.5·§2.6.
-- 판정   = 2026-08-26 Ted ③ — D3/D4/D5 만 **동일 `dataset_id`** 로 재시드.
--
-- 이 파일은 픽스처 정본(`services/core-api/tests/fixtures/seed.sql`)의 D3·D4 블록을 값 그대로 옮긴 것이다.
-- D5(`d5_upload`·`d5_upload_file`·`d5_pipeline_event`)는 정본에 행이 없다 — 재시드 대상 0행.
-- 값을 바꾸면 게이트 픽스처와 갈라진다. 정본이 바뀌면 이 파일도 같은 커밋에서 바꾼다.
--
-- 선행 조건 ① 대상 5표가 전부 0행. 하나라도 행이 있으면 중단한다(중복 적재 방지).
-- 선행 조건 ② 실행 직전 백업 취득. 절차는 `dev-package/sessions/S2-EXEC-PLAN.md` §8-0.
-- DELETE 문장을 두지 않는다 — 이 파일은 INSERT 전용이다.

\set ON_ERROR_STOP on
BEGIN;

DO $$
DECLARE n bigint;
BEGIN
  SELECT (SELECT count(*) FROM d3_dataset)
       + (SELECT count(*) FROM d3_dataset_description)
       + (SELECT count(*) FROM d3_dataset_autometa)
       + (SELECT count(*) FROM d3_file)
       + (SELECT count(*) FROM d4_lineage_edge) INTO n;
  IF n <> 0 THEN
    RAISE EXCEPTION '선행 조건 미충족 — 대상 5표 합계 %행. 0행이 아니면 재시드하지 않는다.', n;
  END IF;
END $$;

INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id, source_label,
                        uploaded_at, last_modified_at, lineage_confirmed_at) VALUES
  ('0000000000000000000000DSA1', '0000000000000000000000000A', '00000000000000000000000AP1',
   '000000000000000000000000A1', '기상청', '2026-01-01T00:00:00Z', '2026-01-02T00:00:00Z', NULL),
  ('0000000000000000000000DSA2', '0000000000000000000000000A', '00000000000000000000000AP1',
   '000000000000000000000000A1', NULL,    '2026-02-01T00:00:00Z', '2026-02-02T00:00:00Z', '2026-02-03T00:00:00Z'),
  ('0000000000000000000000DSB1', '0000000000000000000000000B', '00000000000000000000000BP1',
   '00000000000000000000000BP1', '환경부', '2026-01-05T00:00:00Z', '2026-01-06T00:00:00Z', NULL);

INSERT INTO d3_dataset_description (dataset_id, lab_id, name, topic, summary) VALUES
  ('0000000000000000000000DSA1', '0000000000000000000000000A', 'A 강우 원자료', '강우·강수', '관측 원자료'),
  ('0000000000000000000000DSA2', '0000000000000000000000000A', 'A 강우 격자화', '강우·강수', '격자화 결과'),
  ('0000000000000000000000DSB1', '0000000000000000000000000B', 'B 토지피복 원자료', '토지피복·LULC', '관측 원자료');

INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, variables, crs, total_size_bytes) VALUES
  ('0000000000000000000000DSA1', '0000000000000000000000000A', 'CSV',    '{강우량}', 'EPSG:5179', 100),
  ('0000000000000000000000DSA2', '0000000000000000000000000A', 'NetCDF', '{강우량}', 'EPSG:5179', 200),
  ('0000000000000000000000DSB1', '0000000000000000000000000B', 'CSV',    '{토지피복}', 'EPSG:5179', 300);

INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key, carries_lat, carries_lon) VALUES
  ('00000000000000000000000FA1', '0000000000000000000000000A', '0000000000000000000000DSA1', '본체',            'a1-body.csv', 50, 'k/a1',  false, false),
  ('00000000000000000000000FA2', '0000000000000000000000000A', '0000000000000000000000DSA1', '기준 격자 파일', 'a1-grid.nc',  50, 'k/a1g', true,  true),
  ('00000000000000000000000FA3', '0000000000000000000000000A', '0000000000000000000000DSA2', '본체',            'a2-body.nc', 200, 'k/a2',  false, false),
  ('00000000000000000000000FB1', '0000000000000000000000000B', '0000000000000000000000DSB1', '본체',            'b1-body.csv', 300, 'k/b1',  false, false);

INSERT INTO d4_lineage_edge (id, lab_id, child_dataset_id, parent_dataset_id, parent_role,
                             method, origin, confirmed_by_account_id, confirmed_at) VALUES
  ('000000000000000000000EDGA1', '0000000000000000000000000A', '0000000000000000000000DSA2',
   '0000000000000000000000DSA1', '주입력', '역거리가중 격자화', 'manual',
   '00000000000000000000000AP1', '2026-02-03T00:00:00Z');

COMMIT;
