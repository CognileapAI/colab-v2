# U-2 S3 고아 바이트 정리 — 로컬 구현·검증

날짜: 2026-09-11. 범위: 로컬 코드·시험·문서만. dev 배포, 운영 설정 변경, 실제 S3 조회·삭제, 커밋·push는 수행하지 않았다.

## 구현 결과

- core app이 D5 만료 후보 row lock, accepted 사건/규약 키, 열린 transfer, D3 dataset/file 소유와 body access를 하나의 `REPEATABLE READ` 작업으로 조립한다.
- 버킷 목록 조회 없이 원장이 아는 exact key만 삭제한다. S3 일부 실패·소유 unknown·키 충돌이면 객체/원장을 보존한다. 객체 삭제 성공 뒤에만 D5 원장을 지운다.
- 등록과 회수 경쟁은 `FOR UPDATE SKIP LOCKED`와 등록 UPDATE의 직렬화로 고정했다. DB commit 실패 뒤에는 없는 exact key 재삭제를 허용해 원장 정리를 재시도한다.
- 유지보수는 기존 S3 transfer 요청에서 별도 트랜잭션으로 호출한다. 뒤따른 요청의 4xx rollback이 이미 끝난 메타 정리를 되돌리지 않는다.
- 기본 모드는 `observe`; local 저장은 성공으로 가장하지 않고 제외한다. pipeline과 구 core reaper의 원장 선삭제는 보존 동작으로 바꿨다.
- 완료 transfer와 transfer_file 메타는 `completed_at <= now-7d`만 apply에서 prune한다. D5 업로드, D3 파일/데이터셋, 원본 객체는 이 메타 정리로 삭제하지 않는다.

## TDD·게이트 증거

- RED: 종전 core/pipeline reaper가 원장 행을 먼저 지우는 단언 실패와 신규 조립 모듈 부재를 확인했다. 수집 오류를 RED로 세지 않았다.
- 좁은 실DB 러너: core 19 passed, pipeline dbint 2 passed.
- core-api 전체: 1040 passed, 6 deselected, failed/error/skipped 0. xdist 4 worker 격리 DB 경로에서도 green.
- pipeline-worker 전체: 268 passed, 48 deselected, failed/error/skipped 0.
- import-boundary: kept 8, broken 0. db-boundary: 7 units, 360 files, violations 0. banned import: 158 files, violations 0.
- 운영 AWS/S3 요청은 0건이다. 테스트 S3는 실패·부분 실패·멱등을 제어하는 fake 경계다.

## 판정

완료 정의의 로컬 구현과 회귀 검증은 충족했다. 그러나 U-2는 `partial`이다. `observe` 배포 후 후보 목록/계수를 확인하고, 정확한 SHA·대상·복구 가능성을 제시해 별도 승인을 받은 뒤에만 `apply`와 실제 삭제를 실행할 수 있다. 그 전에는 `done`으로 올리지 않는다.

의도 대비 범위 초과는 없다. 버킷 스캔, local 삭제, 원본 TTL, 운영 cron, Google 로그인은 추가하지 않았다.
