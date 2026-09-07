-- 0017 「기존 행」 시험의 **재료** — 0017 이 돌기 **전**의 DB 에 심는다 (0016 상태).
--
-- 재는 것 = 수용 기준 축자 「Given 마이그레이션 적용, When 유효 grant 를 가진 잠김
-- 데이터셋 조회, Then 상태가 `지정 공개` 이고 그 사람의 접근이 **종전과 같다**(양성·음성
-- 둘 다)」 ＋ 「`state='잠김'` ∧ 유효 grant ≥1 인 행이 0건」.
--
-- 네 갈래를 심는다 — 넷이 서로 다른 매핑 줄을 잰다.
--   DSC1 = 잠김 ∧ **유효** grant 1건  → `지정 공개` (본선)
--   DSC2 = 잠김 ∧ **만료된** grant 1건 → `잠김` 그대로 (만료는 유효가 아니다)
--   DSC3 = 열림                        → `열림` 그대로
--   DSC4 = 상태 행 **없음**(NULL)      → 행이 생기지 않는다 (연구실 기본값 경로 유지)
\set ON_ERROR_STOP on

INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_lab_profile (lab_id, university, department, principal_investigator,
                            research_field, introduction, default_visibility) VALUES
  ('0000000000000000000000000T', 'T 대', 'T 과', 'T 교수', '수문학', 'T', '열림');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example'),
  ('00000000000000000000000TR1', '0000000000000000000000000T', 'T 연구원', 'res@t.example');

INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                        uploaded_at, last_modified_at)
SELECT id, '0000000000000000000000000T', '00000000000000000000000TP1',
       '00000000000000000000000TP1', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
  FROM (VALUES ('000000000000000000000DSC1A'), ('000000000000000000000DSC2A'),
               ('000000000000000000000DSC3A'), ('000000000000000000000DSC4A')) AS v(id);

INSERT INTO d3_dataset_description (dataset_id, lab_id, name, summary)
SELECT id, '0000000000000000000000000T', '기존 데이터셋 ' || right(id, 3), NULL
  FROM (VALUES ('000000000000000000000DSC1A'), ('000000000000000000000DSC2A'),
               ('000000000000000000000DSC3A'), ('000000000000000000000DSC4A')) AS v(id);

-- 본체 조각 — 「그 사람의 접근이 종전과 같다」를 이 행으로 잰다.
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key,
                     carries_lat, carries_lon) VALUES
  ('00000000000000000000000FC1', '0000000000000000000000000T', '000000000000000000000DSC1A',
   '본체', 'c1.nc', 10, 'k/c1', false, false),
  ('00000000000000000000000FC2', '0000000000000000000000000T', '000000000000000000000DSC2A',
   '본체', 'c2.nc', 10, 'k/c2', false, false);

-- ⚠ **DSC4 는 일부러 행이 없다** — NULL→NULL 유지를 잰다.
INSERT INTO d2_dataset_access (dataset_id, lab_id, state) VALUES
  ('000000000000000000000DSC1A', '0000000000000000000000000T', '잠김'),
  ('000000000000000000000DSC2A', '0000000000000000000000000T', '잠김'),
  ('000000000000000000000DSC3A', '0000000000000000000000000T', '열림');

-- 유효 grant 는 DSC1 하나뿐이다. DSC2 의 줄은 **이미 만료**됐다 —
-- 「만료된 허용 줄은 있으나 마나다」(P-25)가 매핑에도 그대로 걸린다.
INSERT INTO d2_dataset_access_grant
  (id, lab_id, dataset_id, grantee_account_id, approver_account_id, approved_at, expires_at)
VALUES
  ('0000000000000000000000GRC1', '0000000000000000000000000T', '000000000000000000000DSC1A',
   '00000000000000000000000TR1', '00000000000000000000000TP1',
   now() - interval '1 month', now() + interval '5 months'),
  ('0000000000000000000000GRC2', '0000000000000000000000000T', '000000000000000000000DSC2A',
   '00000000000000000000000TR1', '00000000000000000000000TP1',
   '2025-01-01T00:00:00Z', '2025-07-01T00:00:00Z');
