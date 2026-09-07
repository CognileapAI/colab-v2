-- 0019 「기존 행」 시험의 **재료** — 0019 가 돌기 **전**의 DB 에 심는다 (0018 상태).
--
-- 재는 것 = `M-10` 수용 기준 축자 —
--   「`nc` 로 잡힌다 · `netcdf` 가 **종전과 같이** 잡힌다 · 변수명 검색이 **종전과 같이**
--    잡힌다 · 색인 재생성이 1회」 ＋ 백필이 **전수를 덮었는가**.
--
-- 두 갈래를 심는다 — 둘이 서로 다른 규칙을 잰다.
--   DSM1 = `0016` 이관을 마친 행(배열 ＝ 행 표) ＋ 확장자 `nc` ＋ 분류 있음
--          → 백필 뒤 `nc`·`netcdf`·변수명·분류가 **다 잡힌다**
--   DSM2 = **행 표에만** 있고 배열이 빈 행(`0016` 뒤에 새로 쓴 변수 — 색인 밖이던 자리)
--          → 백필이 배열을 채워 그 변수명이 **처음으로** 잡힌다
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
  FROM (VALUES ('000000000000000000000DSM1A'), ('000000000000000000000DSM2A')) AS v(id);

-- ⚠ 분류는 `d3_dataset_description` 에 산다 — 그것이 미러 열이 필요한 이유다.
INSERT INTO d3_dataset_description (dataset_id, lab_id, name, summary, category) VALUES
  ('000000000000000000000DSM1A', '0000000000000000000000000T', '기존 데이터셋 M1', '한 줄', '수문 인자'),
  ('000000000000000000000DSM2A', '0000000000000000000000000T', '기존 데이터셋 M2', '한 줄', NULL);

INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, variables, file_extension,
                                 crs, total_size_bytes) VALUES
  ('000000000000000000000DSM1A', '0000000000000000000000000T', 'netcdf',
   ARRAY['precipitation'], 'nc', 'EPSG:5179', 0),
  -- 배열이 비어 있다 = `0016` 뒤에 사람이 쓴 변수 행이 **색인에 안 들어가 있던** 상태다.
  ('000000000000000000000DSM2A', '0000000000000000000000000T', 'csv',
   ARRAY[]::text[], 'csv', 'EPSG:5179', 0);

INSERT INTO d3_dataset_variable (dataset_id, lab_id, ordinal, name, is_representative) VALUES
  ('000000000000000000000DSM1A', '0000000000000000000000000T', 1, 'precipitation', true),
  ('000000000000000000000DSM2A', '0000000000000000000000000T', 1, 'evapotranspiration', true);
