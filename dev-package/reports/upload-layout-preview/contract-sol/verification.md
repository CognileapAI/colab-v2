# 업로드·레이아웃·미리보기 contract-sol 검증 보고서

## 작업 경계

- 작업 사본: `/home/ttlhi10/colab-ui-contract`
- 브랜치: `codex/upload-preview-contract`
- 기준 HEAD: `690995e33a5525663632d9c699ff6ffe62143ffa`
- 역할: `lane-worker` (backend/contract, 단독 writer)
- lifecycle task: `19044c4c294b4c0e8f11aa5d3ae7624d`
- 구현 범위: 대표 그림 API·저장/정리 원장, 계보 후보 전용 조회, 사람 격자 설명, additive 계약·생성물, platform 0023 migration/schema/RLS, 관련 시험
- 범위 밖: 수기 frontend UI, 브라우저 E2E, 배포·main 병합·push

## lifecycle 준비

공유 루트의 `scripts/agent-bridge.py`로 begin을 시도했으나 분리 브랜치가 bridge 추가 전 기준이고, 공유 bridge가 공유 main을 프로젝트 루트로 고정하여 이 작업 사본과 정확한 정의를 확인할 수 없었다. 이 준비 실패는 exit 78로 기록했다. 부모의 지시에 따라 같은 fail-closed 계약 본체인 공유 루트 `.claude/hooks/lifecycle_contract.py`를 작업 사본 cwd에서 직접 호출해 task를 시작했다. 이후 `run-gates`와 `handoff`도 이 task를 사용한다.

## 구현 결과

### 대표 그림

- 별도 `representative-images` storage key와 D3 이미지 메타데이터를 추가했다.
- `PUT/GET/DELETE /datasets/{datasetId}/representative-image`를 추가하고 기존 편집·body 접근 판정을 재사용했다.
- Pillow의 실제 decode/verify로 PNG/JPEG/WebP만 허용하고 10 MiB 및 50 M pixel 상한을 적용했다.
- 교체는 dataset row lock 뒤 새 바이트 저장, 참조 upsert와 이전 키 cleanup 원장 기록을 한 transaction에 확정한 뒤 이전 바이트를 정리한다.
- 삭제도 참조 삭제와 cleanup 원장 기록을 한 transaction에 확정한다. commit 이후 정리 실패는 성공 응답을 뒤집지 않고 원장을 보존하며 다음 mutation에서 재시도한다.
- 부분 `put` 실패 후 새 키 정리까지 실패하는 이중 실패도 cleanup 원장에 남기고 원래 500 응답을 유지한다.
- 동시 PUT 두 건은 실제 HTTP/DB session 시험에서 직렬화되어 최종 참조 한 건, 현재 파일 한 건, pending cleanup 0건으로 끝난다.

### 계보 후보

- q/category/topic/period/keyset/limit을 D3 SQL에 적용하고 후보 페이지만 batch enrich한다.
- q는 이름 또는 접근 가능한 본체 파일명 OR, category·period·topic은 AND이다. 기간은 겹침 기준이며 기간 미기재 후보는 필터가 없을 때 포함되고 기간 필터 때 제외된다.
- effective processing level은 D3 keyset chunk를 D4 batch summary로 보강한 뒤 limit을 채울 때까지 bounded scan한다. cursor는 마지막 검사 key를 담아 제외 행을 다시 읽지 않는다.
- 잠긴 body 후보는 기존 메타 공개·연결 정책을 유지하되 파일명/확장자를 숨긴다.
- 폴더별 동명 본체 파일명과 확장자를 응답에서 중복 제거한다.

### 격자 설명

- `d3_dataset_description.human_grid_description` nullable 컬럼과 create/update/basic-info additive 계약을 추가했다.
- 상세 응답은 사람값 우선 `gridDescription`, 자동값 `gridDescriptionAutomatic`을 함께 제공하며 사람값 삭제 시 자동값으로 복귀한다.
- 재분석과 `_CLEAR_GRID_META`는 사람 설명을 변경하지 않고 좌표/autometa 계산에도 사용하지 않는다.

## TDD 증거

RED:

- 대표 그림 최초 route 시험: `4 failed` (예상한 404). 없는 API 계약을 잡았다.
- 세 기능 결합 최초 시험: `8 failed, 12 passed`. 누락 필드·route·storage key를 잡았다.
- 리뷰 회귀 RED: 부분 put 이중 실패 뒤 orphan 2개, 교체 cleanup 실패 500, 삭제 cleanup 실패 500을 재현했다. cleanup 원장과 성공 응답 보존으로 수정했다.
- 민감도 점검에서 중복 제거와 effective Lv 선필터를 임시로 제거하면 각각 동명 파일 중복과 잘못된 첫 페이지로 `2 failed`가 나는 것을 확인했다. 임시 변경을 복구한 현재 구현에서 계보 시험 `8 passed`를 재확인했다.

GREEN:

- 변경 관련 묶음: `64 passed`
- 대표 그림 단독: `14 passed`
- 계보 후보 최종: `8 passed`
- core-api 전체: `1015 passed, 6 deselected` (159.71초)
- migration drift: platform `15/15`, ai `3/3`, 합계 `18/18`
- 0023 전용 drift oracle: GREEN

## 게이트 증거

- `contract-lint`: GREEN, seam 3개 / 오류 0
- `contract-breaking`: GREEN
- `generated-up-to-date`: GREEN, 생성물 10개
- `migration-single-head`: GREEN, platform 27개/head 0023, ai 8개/head 0007
- `rls-coverage`: GREEN, 36개 table; 신규 이미지·cleanup table 포함
- `rls-effect`: GREEN, lab_id table 28개와 body/meta/cross-tenant 효과 확인
- `ci-schema-diff.sh`: GREEN, platform/ai 양쪽 clean schema와 migration schema 일치
- `service-tests-core-api`: GREEN, `1015 passed, 6 deselected`

`bash gates/run.sh schema-diff`의 최초 두 번은 홈 테스트 env의 오래된 applied DB 주소(`172.17.0.3`) 때문에 연결이 끊겨 판정하지 못했다. 이를 성공으로 세지 않았다. 공식 CI schema wrapper는 새 일회성 DB에서 GREEN이었다. 최종 lifecycle 게이트는 새 applied DB와 임시 env를 사용해 실제 선언된 `schema-diff`를 다시 판정한다.

## 미실행과 제한

- 실제 S3 live smoke는 실행하지 않았다. 저장 순서·실패·재시도는 LocalObjectStorage 외부 행위 시험으로 검증했다.
- frontend 수기 구현과 브라우저 E2E는 이 레인의 소유 범위 밖이며 부모 frontend 레인에서 검증한다.
- 전체 intent의 통합 화면·시각·배포 검증은 부모/Advisor 단계에 남는다. backend/contract 소비 준비 상태에는 알려진 gap이 없다.

## Astra 재심사 보완

- commit 후 drain 두 개를 강제로 교차해, 이전 mutation의 `keep` 키와 같은 cleanup 행을 backend no-op 뒤 finish하면 orphan과 추적 상실이 생기는 RED를 확인했다.
- `_drain_cleanups`는 `pending.storage_key == keep`인 행에 삭제와 finish를 모두 수행하지 않는다. 뒤 mutation의 drain이 실제 삭제에 성공한 뒤 행을 끝낸다.
- `LocalFilesystemStorage.discard`가 `PermissionError`와 `IsADirectoryError`를 성공으로 삼는 RED 2건을 확인했다. 이제 `FileNotFoundError`만 멱등 성공으로 처리하고 실제 삭제 실패는 호출자에게 전파한다.
- 수정 직후 표적 시험 `3 passed`, 대표 그림·storage backend 관련 전체 `37 passed`를 확인했다. 최종 전체 서비스 시험과 lifecycle 8개 게이트는 후속 commit에서 다시 실행한다.
