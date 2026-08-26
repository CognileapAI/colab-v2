-- 픽스처 A·B 관측치 고정 — 읽기 전용.
--
-- 용도 = `dev-package/sessions/S2-EXEC-PLAN.md` §8 2단 「픽스처 관측치 고정」의 DB 측 산출.
-- 이 파일은 SELECT 만 한다. INSERT·UPDATE·DELETE·DDL 0건.
-- 화면·API 측 판정기준(검색 degraded · 미리보기 산출 수)은 이 파일이 재지 못한다 — 별도 수단.

\set ON_ERROR_STOP on

SELECT '데이터셋 수'        AS 판정기준, lab_id AS 연구실, count(*)::text AS 값 FROM d3_dataset GROUP BY lab_id
UNION ALL
SELECT '파일 수 합',        lab_id, count(*)::text FROM d3_file GROUP BY lab_id
UNION ALL
SELECT '파일 크기 합(byte)', lab_id, coalesce(sum(size_bytes),0)::text FROM d3_file GROUP BY lab_id
UNION ALL
SELECT '기준 격자 파일 수',  lab_id, count(*)::text FROM d3_file WHERE kind = '기준 격자 파일' GROUP BY lab_id
UNION ALL
SELECT '계보 간선 수',      lab_id, count(*)::text FROM d4_lineage_edge GROUP BY lab_id
UNION ALL
SELECT '잠김 데이터셋 수',   lab_id, count(*)::text FROM d2_dataset_access WHERE state = '잠김' GROUP BY lab_id
UNION ALL
SELECT '열림 데이터셋 수',   lab_id, count(*)::text FROM d2_dataset_access WHERE state = '열림' GROUP BY lab_id
UNION ALL
SELECT 'Verified true 수',  lab_id, count(*)::text FROM d2_verified WHERE verified GROUP BY lab_id
UNION ALL
SELECT '패싯 주제 ' || topic, lab_id, count(*)::text FROM d3_dataset_description GROUP BY topic, lab_id
UNION ALL
SELECT '이름에 「강우」 포함 수', lab_id, count(*)::text FROM d3_dataset_description WHERE name LIKE '%강우%' GROUP BY lab_id
UNION ALL
SELECT '프로젝트-데이터셋 연결 수', lab_id, count(*)::text FROM d6_project_dataset GROUP BY lab_id
UNION ALL
SELECT '고아 dataset_id 수(4표 합)', lab_id, count(*)::text FROM (
  SELECT lab_id, dataset_id FROM d6_project_dataset
  UNION ALL SELECT lab_id, dataset_id FROM d2_dataset_access
  UNION ALL SELECT lab_id, dataset_id FROM d2_verified
  UNION ALL SELECT lab_id, dataset_id FROM d8_download
) x WHERE NOT EXISTS (SELECT 1 FROM d3_dataset d WHERE d.id = x.dataset_id) GROUP BY lab_id
ORDER BY 1, 2;
