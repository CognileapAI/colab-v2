-- 0018 「기존 행」 시험의 **재료** — 0018 이 돌기 **전**의 DB 에 심는다 (0017 상태).
--
-- 재는 것 = PRD-19 축자 「두 컬럼 전 행 NULL. 필수 검사가 없으므로 기존 행의 수정이
-- 막히지 않는다.」
-- ⚠ 행 수를 13 으로 맞추지 않는다 — 13 은 staging 의 그날 실측치이고 오라클의 값이 아니다.
--   오라클은 「전 행이 NULL 이고 `source_label` 이 한 글자도 안 바뀐다」이며 행 수와 무관하다.
--   **파생 Lv 가 갈리는 행을 섞어 심는다** — 부모가 있는 행(Lv≥1)과 없는 행(Lv0)이 같은
--   대우를 받는지가 이 회차의 알맹이다.
\set ON_ERROR_STOP on

INSERT INTO d1_lab (id, name, opened_at) VALUES
  ('0000000000000000000000000T', 'T 연구실', '2020-01-01T00:00:00Z');
INSERT INTO d1_lab_profile (lab_id, university, department, principal_investigator,
                            research_field, introduction, default_visibility) VALUES
  ('0000000000000000000000000T', 'T 대', 'T 과', 'T 교수', '수문학', 'T', '열림');
INSERT INTO d1_account (id, lab_id, name, email) VALUES
  ('00000000000000000000000TP1', '0000000000000000000000000T', 'T 교수', 'prof@t.example');

-- 원천 표기가 **있는 행과 없는 행**을 섞는다. 있는 값은 지워지면 안 되고(미결-11 ⓐ),
-- 없는 행에 지어내면 안 된다.
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id, source_label,
                        uploaded_at, last_modified_at)
SELECT id, '0000000000000000000000000T', '00000000000000000000000TP1',
       '00000000000000000000000TP1', label, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z'
  FROM (VALUES ('000000000000000000000DST1'||'A', 'ECMWF ERA5'),
               ('000000000000000000000DST2'||'A', '기상청 GK2A'),
               ('000000000000000000000DST3'||'A', NULL),
               ('000000000000000000000DST4'||'A', 'NASA MODIS'),
               ('000000000000000000000DST5'||'A', NULL)) AS v(id, label);

INSERT INTO d3_dataset_description (dataset_id, lab_id, name, topic, summary)
SELECT id, '0000000000000000000000000T', '기존 데이터셋 ' || right(id, 3), '강우·강수', NULL
  FROM (VALUES ('000000000000000000000DST1'||'A'), ('000000000000000000000DST2'||'A'),
               ('000000000000000000000DST3'||'A'), ('000000000000000000000DST4'||'A'),
               ('000000000000000000000DST5'||'A')) AS v(id);
