> spec: dev-package/prd/specs/s2-preview-retention.md

# R-S2-PREVIEW-RETENTION Implementation Plan

## Task 1: BF-12 dev S3 관측 경로

Files: modify `tile_reclaim.py`, `app/main.py`, dev compose; add viz tests and dev declaration test.

- [x] S3 목록 접두사, 바이트 다이제스트, 실패 시 준비 red, apply 강제 무효, dev 스풀 부재를 실패 시험으로 고정하고 RED를 확인한다.
- [x] S3SourcePort를 사용해 대상별로 materialize 즉시 후보 키를 계산하는 관측 전용 job을 구현한다.
- [x] app 조립이 local/local에는 기존 job, s3/s3에는 S3 관측 job을 붙이도록 한다.
- [x] dev compose에 pipeline-worker/viz-render 공용 쓰기 가능 event volume을 선언한다.
- [x] 좁은 시험, viz/pipeline 서비스 게이트, 생성물·import·배포 선언 경계를 green으로 만든다.

## Task 2: BF-12 dev 실측

- [ ] 정확한 변경 SHA, 이미지, 영향, 롤백을 정리하고 dev 배포 직전 승인을 받는다.
- [ ] 승인 후 동일 SHA를 배포하고 8/8 healthy를 확인한다.
- [ ] 한 주기 이상 기다린 뒤 첫 회수 요약의 주체/타일/닿음/못 닿음/삭제 0과 비밀 0을 보존한다.
- [ ] 이 증거가 모두 선 경우에만 BF-12를 done으로 갱신한다.

## Task 3: TL-2 관측 분류

- [ ] BF-12 done을 대장에서 재확인한다. 열려 있으면 이 Task를 시작하지 않는다.
- [ ] 원장 부재와 사이드카 부재가 별도 등급이며 자동 삭제되지 않는 실패 시험을 작성한다.
- [ ] 관측 전용 분류를 구현하고 기존 19벌·재굽기로 닿지 않는 16벌을 dev에서 대조한다.
- [ ] 실제 삭제 0을 확인하고 TL-2 상태와 세션 증거를 갱신한다.

## Task 4: 인계

- [ ] 실증된 범위만 대장·handoff에 반영하고 `work-item-consistency`를 green으로 만든다.
- [ ] 배포 대기와 TL-2 미착수는 partial/open 사유로 숨기지 않는다.
