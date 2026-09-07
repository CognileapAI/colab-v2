-- 0016 「기존 행」 시험의 **재료** — 0016 이 돌기 **전**의 DB 에 심는다 (0015 상태).
--
-- 재는 것 = 수용 기준 축자 「Given 마이그레이션 후, When 3원소이던 기존 행 조회, Then
-- `d3_dataset_variable` 에 3행이 **순서대로** 있고 첫 행만 대표다」 ＋ 「Given 변수
-- `precipitation`, When 검색어 `precipitation`, Then 이관 전후 **같은** 데이터셋이 나온다」.
--
-- 세 갈래를 심는다 — 셋이 서로 다른 규칙을 잰다.
--   DSV1 = 3원소   → 3행 · 순서대로 · 첫 행만 대표 (본선)
--   DSV2 = 빈 배열 → **0행** (이관 대상이 아니다)
--   DSV3 = 첫 원소가 공백 → 걸러 낸 뒤 **다시 번호를 매긴다**(`ordinal` 에 구멍 없음 ·
--          대표가 한 행도 없는 데이터셋을 만들지 않는다)
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
  FROM (VALUES ('000000000000000000000DSV1A'), ('000000000000000000000DSV2A'),
               ('000000000000000000000DSV3A')) AS v(id);

INSERT INTO d3_dataset_description (dataset_id, lab_id, name, summary)
SELECT id, '0000000000000000000000000T', '기존 데이터셋 ' || right(id, 3), NULL
  FROM (VALUES ('000000000000000000000DSV1A'), ('000000000000000000000DSV2A'),
               ('000000000000000000000DSV3A')) AS v(id);

-- ⚠ **배열 순서가 뜻이다** — 이관은 이 순서를 `ordinal` 로 옮긴다.
INSERT INTO d3_dataset_autometa (dataset_id, lab_id, format, variables, crs, total_size_bytes) VALUES
  ('000000000000000000000DSV1A', '0000000000000000000000000T', 'NetCDF',
   ARRAY['precipitation', 'temperature', 'runoff'], 'EPSG:5179', 0),
  ('000000000000000000000DSV2A', '0000000000000000000000000T', 'CSV',
   ARRAY[]::text[], 'EPSG:5179', 0),
  ('000000000000000000000DSV3A', '0000000000000000000000000T', 'CSV',
   ARRAY['   ', 'tp'], 'EPSG:5179', 0);
