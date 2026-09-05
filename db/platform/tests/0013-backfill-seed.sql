-- 0013 백필 시험의 **재료** — 0013 가 돌기 **전**의 DB 에 심는다 (0011 상태).
--
-- 네 장면을 심는다. 백필이 무엇을 채우고 무엇을 비워 두는지가 여기서 갈린다.
--   DST1 `nakdong_precip_2025.nc` 조각 2건        → `nc`
--   DST2 `swath.hdf`                              → `hdf`   (HDF4/5 를 단정하지 않는다)
--   DST3 `nakdong_precip_2025` (점 없음)          → NULL    (화면은 `format` 으로 퇴행)
--   DST4 본체 `A.NC` ＋ 기준 격자 파일 `grid.tif` → `nc`    (격자는 확장자를 정하지 않는다)
\set ON_ERROR_STOP on

INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_lab_profile (lab_id, university, department, principal_investigator,
                            research_field, introduction, default_visibility) VALUES
  ('0000000000000000000000000T', 'T 대', 'T 과', 'T 교수', '수문학', 'T', '열림');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');

INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                        uploaded_at, last_modified_at)
SELECT id, '0000000000000000000000000T', '00000000000000000000000TP1',
       '00000000000000000000000TP1', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
  FROM (VALUES ('0000000000000000000000DST1'), ('0000000000000000000000DST2'),
               ('0000000000000000000000DST3'), ('0000000000000000000000DST4')) AS v(id);

INSERT INTO d3_dataset_description (dataset_id, lab_id, name, topic, summary)
SELECT id, '0000000000000000000000000T', '시험 데이터셋 ' || right(id, 1), NULL, NULL
  FROM (VALUES ('0000000000000000000000DST1'), ('0000000000000000000000DST2'),
               ('0000000000000000000000DST3'), ('0000000000000000000000DST4')) AS v(id);

-- 자동 메타 행. **`format` 에는 판별 결과 문자열이 이미 들어 있다** — 백필 전의 실제 상태다.
INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format) VALUES
  ('0000000000000000000000DST1', '0000000000000000000000000T', 'NetCDF-4'),
  ('0000000000000000000000DST2', '0000000000000000000000000T', 'HDF5'),
  ('0000000000000000000000DST3', '0000000000000000000000000T', 'NetCDF-4'),
  ('0000000000000000000000DST4', '0000000000000000000000000T', NULL);

INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key,
                     carries_lat, carries_lon) VALUES
  ('00000000000000000000000F11', '0000000000000000000000000T', '0000000000000000000000DST1',
   '본체', 'nakdong_precip_2025.nc', 100, 'k/f11', false, false),
  ('00000000000000000000000F12', '0000000000000000000000000T', '0000000000000000000000DST1',
   '본체', 'nakdong_precip_2026.nc', 100, 'k/f12', false, false),
  ('00000000000000000000000F21', '0000000000000000000000000T', '0000000000000000000000DST2',
   '본체', 'swath.hdf', 100, 'k/f21', false, false),
  ('00000000000000000000000F31', '0000000000000000000000000T', '0000000000000000000000DST3',
   '본체', 'nakdong_precip_2025', 100, 'k/f31', false, false),
  ('00000000000000000000000F41', '0000000000000000000000000T', '0000000000000000000000DST4',
   '본체', 'A.NC', 100, 'k/f41', false, false),
  ('00000000000000000000000F42', '0000000000000000000000000T', '0000000000000000000000DST4',
   '기준 격자 파일', 'grid.tif', 100, 'k/f42', true, true);
