-- ⭑ 시드의 A 연구실 자료는 **교수(AP1) 소유**라 「소유자 ≠ 관리자」를 재지 못한다.
--   연구원(A1)이 소유한 「나만 보기」 자료 한 벌을 이 오라클이 직접 심는다.
\set ON_ERROR_STOP on
BEGIN;
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id,
                        uploaded_at, last_modified_at)
  VALUES ('0000000000000000000000DSX1','0000000000000000000000000A',
          '000000000000000000000000A1','000000000000000000000000A1', now(), now());
INSERT INTO d3_dataset_description (dataset_id, lab_id, name, topic, summary)
  VALUES ('0000000000000000000000DSX1','0000000000000000000000000A',
          '소유자 판정용 비공개 자료','강우·강수','소유자 갈래 오라클');
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key,
                     carries_lat, carries_lon)
  VALUES ('00000000000000000000000FX1','0000000000000000000000000A',
          '0000000000000000000000DSX1','본체','x1-body.csv', 70, 'k/x1', false, false);
INSERT INTO d2_dataset_access (dataset_id, lab_id, state)
  VALUES ('0000000000000000000000DSX1','0000000000000000000000000A','잠김');
COMMIT;
