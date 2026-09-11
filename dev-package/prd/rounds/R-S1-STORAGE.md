> spec: dev-package/prd/specs/s1-storage.md

# S3 미등록 업로드 회수 Implementation Plan

**Goal:** exact-key 원본 회수 성공 뒤에만 원장을 지우고 완료 transfer 메타를 7일 기준으로 정리한다.
**Architecture:** core app 조립 → D5 후보/잠금 + D2 가시성 Port + D3 소유 Port + S3 회수 Port. pipeline은 선삭제를 중단한다.
**Tech Stack:** Python, SQLAlchemy, PostgreSQL RLS, 기존 SigV4 S3 client.

## Task 1: 실패 시험

Files: create `services/core-api/tests/test_storage_maintenance.py`, `services/pipeline-worker/tests/test_storage_reaper_dbint.py`, `dev-package/tools/run-storage-tests.sh`.

- [x] 일회용 DB+앱 롤로 공개/잠금 dataset과 expired upload를 고정 fixture로 구성한다.
- [x] `run_storage_maintenance(factory, subject, s3, mode, now)` 외부 결과와 실제 행/바이트 보존 시험 작성.
- [x] `bash dev-package/tools/run-storage-tests.sh` RED 확인. 수집 오류가 아닌 기능부재/행보존 단언 실패를 기록한다.

## Task 2: Port·원장·조립 구현

Files: create `services/core-api/src/colab_core/app/storage_maintenance.py`; modify `domains/d3_catalog.py`, `domains/d5_ingestion.py`, `app/routes/upload_transfers.py`, `kernel/config.py` (모두 core-api src 아래). pipeline modify `domains/d5_ingestion.py`.

- [x] D5 후보 row lock과 사건/키 검증, 완료 transfer 7일 메타 prune.
- [x] D2-readable·D3-owned/unknown 판정을 같은 snapshot으로 조립.
- [x] exact-key S3 회수 후 D5 삭제; 오류/unknown 보존.
- [x] 기본observe 설정, local 제외, 기존 요청 경로 연결.
- [x] 원장 선삭제를 주장한 옛 시험을 승인된 보존 동작으로 정정한다.

## Task 3: 검증·인계

- [x] 좁은 실DB 시험 GREEN, 등록경쟁·실패멱등 포함.
- [x] `service-tests-core-api`, `service-tests-pipeline-worker`, `import-boundary`, `db-boundary` 실행; 준비 실패를 통과로 세지 않는다.
- [x] 검증 근거·의도 미달/초과·운영 한계를 session 기록에 남기고 부모에게 반환한다.
- [x] 배포·실제삭제 승인은 대기. 대장 done 변경·커밋·push 없음.
