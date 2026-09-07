-- 0015 「기존 행」 시험의 **재료** — 0015 가 돌기 **전**의 DB 에 심는다 (0014 상태).
--
-- 재는 것 = 수용 기준 축자 「Given 마이그레이션 적용, When `SELECT topic, category FROM
-- d3_dataset_description`, Then 전 행이 `category IS NULL` 이고 `topic` 값은 그대로다」.
-- ⚠ 행 수를 13 으로 맞추지 않는다 — 13 은 **staging 의 그날 실측치**이고 오라클의 값이
--   아니다. 오라클은 「전 행이 NULL 이고 topic 이 한 글자도 안 바뀐다」이며, 그 성질은
--   행 수와 무관하게 성립해야 한다. 여기서는 주제 어휘 6값을 **전부** 심어 어느 값도
--   자동 매핑되지 않음을 본다.
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
  FROM (VALUES ('000000000000000000000DST1'||'A'), ('000000000000000000000DST2'||'A'),
               ('000000000000000000000DST3'||'A'), ('000000000000000000000DST4'||'A'),
               ('000000000000000000000DST5'||'A'), ('000000000000000000000DST6'||'A'),
               ('000000000000000000000DST7'||'A')) AS v(id);

-- 주제 6값 ＋ NULL 한 행. **여섯 값 전부가 이관 대상이 아니다**(미결-3 ⓐ).
INSERT INTO d3_dataset_description (dataset_id, lab_id, name, topic, summary)
SELECT id, '0000000000000000000000000T', '기존 데이터셋 ' || right(id, 2), topic, NULL
  FROM (VALUES ('000000000000000000000DST1'||'A', '강우·강수'),
               ('000000000000000000000DST2'||'A', '식생·NDVI'),
               ('000000000000000000000DST3'||'A', '지형·DEM'),
               ('000000000000000000000DST4'||'A', '토지피복·LULC'),
               ('000000000000000000000DST5'||'A', '가뭄'),
               ('000000000000000000000DST6'||'A', '파일 포맷 예제'),
               ('000000000000000000000DST7'||'A', NULL)) AS v(id, topic);
