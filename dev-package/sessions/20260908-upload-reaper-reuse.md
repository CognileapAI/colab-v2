# 업로드 만료 정리 재사용 조사 — 2026-09-08

## 결론

- `archive/feature/rtf400_upload_reaper`는 구현 태그가 아니라 조사 근거 정정 태그다. `git diff --stat main...<tag>`는 문서3파일(PLAN-SoT, WORK-UNITS, work-items) 6삽입/5삭제뿐. 끝 커밋 `5c1458e`도 evidence를 미착수로 유지한다.
- 앞선 조사에서 이 태그를 기존 구현이라고 부른 표현은 정정한다. 코드 재사용 대상은 태그 변경분에 없다. 조사 결과를 현재 실물과 대조해 필요한 부분만 반영해야 한다.
- 태그의 배선0 주장은 core-api `UploadLedgerAdapter.reap_expired`에 한정된다. 현 main 워커 `worker.py:345`는 `reap_expired_uploads(ledger)`를 호출하고 `domains/d5_ingestion.py:711`가 `SqlLedger.expire`를 호출한다. 현재 워커에 만료 호출이 없다고 반입하면 틀린 문서가 된다.

## 기존 완료 정의 대조

정본: `dev-package/work-items.yaml` U-2 completion_def. 현재 작업 트리 코드를 읽었으며 운영 실행/데이터 조회는 하지 않았다.

| 항목 | 현재 확인 | 분류 |
|---|---|---|
| 만료 원장행+S3 객체 동시 정리 | `pipeline-worker/.../domains/d5_ingestion.py:662` expire가 DELETE FROM d5_upload만 실행. S3 삭제 호출 없음 | 구현 필요 |
| S3 실패 시 행 보존/재시도 | 현재 expire에 S3 시도 자체가 없음 | 구현 필요 |
| 등록 업로드 보호 | expire 조건 `registered_at IS NULL` 존재. 등록 중 경합/데이터셋 참조 검증은 이번 미실행 | 일부 코드 존재, 전체 수용 미확인 |
| 버킷 루트 스캔 금지·원장 키만 | 현 만료 SQL은 버킷 스캔 안 함. 삭제 대상 key 조회/처리 경로는 없음 | 제약 유지하며 구현 필요 |
| d3_dataset/d5_upload/열린 전송 세 부재 판별 시험 | 현 expire는 등록시각·만료시각·PROCESSING 조건이며 셋 부재를 검사하는 S3 회수 시험은 확인 못 함 | 구현/음성 시험 필요 |

## 재사용 가능한 현재 구성요소

- `core-api/.../app/routes/upload_transfers.py:102-123`: 미완결 전송 정리의 원장 파일 조회→멀티파트 중단/업로드 객체 삭제→행 삭제 순서. S3Error에서는 continue하여 행 유지. 다만 미완결 전송용이므로 완결 접수의 판별식으로 그대로 쓰면 안 된다.
- `pipeline-worker/.../kernel/s3.py:344`: S3 delete_objects 메서드가 이미 있다. 공유 커널 파일 동일성 규약을 확인해야 하며 임의로 워커 사본만 바꾸지 않는다.
- `worker.py:329-356`: 연구실 스코프·트랜잭션·rollback·commit 경로. 이미 만료 호출이 있어 새 스케줄러를 먼저 만들 필요가 있다는 결론은 나오지 않는다.
- 단일 DB 트랜잭션은 S3 삭제를 rollback하지 못한다. 키 소유/등록 경합을 잠그고 부분 S3 성공 뒤 재시도해도 안전한 처리인지 실패 시험이 필요하다. 이는 코드 설계/검증 항목이다.

## 결정이 필요한 부분과 바로 해결할 코드 결손

- 바로 설계/구현 가능한 결손: 현 DB-only 만료 삭제를 원장 키 기반 S3 처리와 연결하고 S3 실패 시 행/키 증거를 보존한다. 등록/처리중/타 연구실/열린 전송을 보호하는 음성 시험, 호출 경로 시험이 필요하다. 운영의 실제 고아 삭제는 별도 행동이며 이번 조사 범위 밖.
- Port: `pipeline-worker/.../ports/blobs.py:20` UploadBlobPort는 materialize/discard만 가진 읽기 Port. discard는 임시 작업 디렉터리 정리이며 원천 바이트 삭제가 아니다. 대장은 별도 삭제 Port 여부를 먼저 판단하라고 적는다. 좁은 문서 검색에서 이미 확정된 Port 결정은 찾지 못했다. 내부 아키텍처 선택이므로 제품 정책 판단과 구분한다.
- 보존 기간: 완결 전송 원장 행은 `completed_at IS NULL` 만료 대상에서 제외된다(`core-api/.../domains/d5_ingestion.py:377`). 대장 note는 완결 뒤 보관 기간을 정해야 한다고 명시한다. intent/prd/sessions와 대장 좁은 검색에서 기간 승인 근거를 찾지 못했다. 임의 7일/30일을 만들지 않는다. 버킷 multipart 7일 라이프사이클은 완결 DB행 보존정책과 다르다.
- 사용자 제품 결정 후보: 완결 전송 원장 보관 기간/감사·재개 필요, 실제 운영 고아 삭제 범위. 읽기 Port 분리는 구현 계획 검토에서 정할 수 있으나 승인된 제품 결정으로 꾸미지 않는다.

## 근거 반입 주의

- 태그의 옛 운영 고아 개수는 2026-09-06 관측 기록이며 현재 개수가 아니다. 이번 운영 데이터 실측0.
- 태그 〈368〉 번호는 현 main 하네스 기록과 충돌한다(최신 R-D 라운드에도 명시). 문서 cherry-pick 대신 근거 재검토 후 메인이 새 번호를 발급한다.
- 이 조사에서는 코드/대장 변경·운영 삭제·네트워크 접촉·시험 실행0. 지정 보고 파일만 작성했다.
