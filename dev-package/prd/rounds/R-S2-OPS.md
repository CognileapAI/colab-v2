> spec: dev-package/prd/specs/s2-ops.md

# R-S2-OPS Implementation Plan

## Task 1: IS4 격리 복구

Files: create `infra/staging/tunnel/rehearse-state-recovery.sh`, `infra/staging/tunnel/rehearse-state-recovery-selftest.sh`; update tunnel README.

- [x] 입력 부재 78, 기존 state/.terraform 유입 red, add/destroy/replace red, ID/토큰 출력 red를 실패 fixture로 고정한다.
- [x] Terraform 1.9.8 새 컨테이너·빈 scratch에서 init/import/plan/refresh-only-state/plan을 수행하는 runner를 구현한다.
- [ ] selftest green 뒤 실자격증명 read-only 리허설을 실행하고 `No changes`, 원격 apply 0을 기록한다.

## Task 2: I4 추적·구조화 로그

Files: create common observability kernel in four services; modify codegen manifest, three FastAPI roots, core relay, pipeline worker; add service tests.

- [x] traceparent 부재/유효/무효/all-zero, 응답 헤더, 비밀·query 미기록, JSON 필수키를 실패 시험으로 작성하고 RED를 확인한다.
- [x] 공통 pure-stdlib ASGI trace middleware와 JSON event emitter를 최소 구현하고 생성물 등기에 세 복제본을 추가한다.
- [x] core→viz/AI 전파와 pipeline 한 바퀴 summary를 연결한다.
- [x] 네 서비스 좁은 시험, 전체 서비스 게이트, import/generated 경계를 실행한다.

## Task 3: I4 알람·레지던시

Files: create `infra/ops/` alarm runner/config/residency declaration and tests; create gate runner/selftest; wire gate declarations.

- [x] 연속 실패 전 raise 0, 임계 도달 raise 1, 반복 실패 통지 0, 회복 clear 1, 상태 손상 red, webhook 부재 readiness 78을 실패 시험으로 고정한다.
- [x] probe 결과 전이와 webhook 전송을 구현한다. 본문/비밀은 보내지 않고 event·target·count·timestamp만 보낸다.
- [x] AWS/CloudFront/OpenAI 처리 위치와 전송 데이터 범위를 TOML에 명시하고 compose region drift 음성 fixture를 고정한다.
- [x] 운영 gate/selftest와 docs를 green으로 만든다. 실제 webhook·cron 연결은 승인 대기다.

## Task 4: I3 최신 15행과 배포 경계

- [x] `sessions/I3.md §6` 15행을 현재 스크립트·과거 증거·실행 필요로 재분류한다.
- [x] 로컬 selftest에서 실제 판정 red/green과 5분 trigger 구성의 fail-closed를 확인한다.
- [ ] 실제 staging/dev 실행 목록, SHA, 영향, 롤백을 제시하고 배포·크론·변이 승인을 받는다.
- [ ] 승인 후 한 배포 SHA에서 trigger 완주, red→green, health 200→200, deploy_doctor 15/15를 증명한다.

## Task 5: 인계

- [x] 실증된 범위만 대장에 반영하고 `work-item-consistency` green.
- [x] actual apply/deploy/notification 미실행은 partial 사유로 숨기지 않는다.
