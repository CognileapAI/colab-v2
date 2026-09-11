# Stage 2 운영 준비 — 복구·배포·관측

출처: `R-STAGE1-STAGE2-CLOSEOUT.md` Task 5, 대장 `IS4`·`I3`·`I4`, `sessions/I3.md §6`, `sessions/IS4.md`, 사용자 2026-09-10 승인 경계.

## 범위와 안전 경계

- 로컬 코드·시험·문서, 격리 scratch state의 read/refresh-only 리허설은 연속 진행한다.
- 실제 Cloudflare/AWS 자원 변경, main push, staging/dev 배포, 크론 설치, 실배포 red/green 변이는 실행 직전 별도 승인을 받는다.
- `I4`는 `R-1`의 회차 단위 복원 성공 근거를 받아 쓰며 복원을 다시 돌리지 않는다. WAL 시점 복구는 prod 개통 관문으로 유지한다.
- 추적·로그에 Authorization, Cookie, DB/S3 URL, 요청/응답 본문, query string, 계정 이메일을 남기지 않는다.

## IS4 — 맨몸 state 복구

- 레포 선언만 read-only mount한 새 Terraform 1.9.8 컨테이너와 빈 작업·플러그인 디렉터리를 사용한다. 기존 `.terraform`·state·호스트 terraform 바이너리는 재사용하지 않는다.
- 자격증명은 레포 밖 0600 env에서 필요한 Cloudflare 세 값만 process env로 전달한다. 값과 resource ID는 보고서에 출력하지 않는다.
- `init → import → plan`으로 add/destroy/replace 0과 ingress 값 무변경을 확인한다. import 직후 sensitivity 메타 갱신만 있으면 scratch state에 한해 `apply -refresh-only`를 허용한다. 그래도 metadata-only plan이 남으면 원격 apply 없이 `No changes`가 성립하지 않는 승인 경계로 78을 내고 멈춘다.
- 실환경 입력이 없으면 selftest green으로 대체하지 않고 readiness 78로 남긴다.

## I3 — 남은 배포 자동화 증거

- 정본 15행을 최신 트리에서 다시 센다. 로컬에서 닫을 수 있는 스크립트·실패 픽스처만 보강한다.
- 남은 실제 조건은 호스트 5분 trigger 1회 완주, 배포 판정 단계의 의도적 red 뒤 green, 배포 직전/직후 `/healthz` 200, 한 번의 전체 게이트 준비실패 0이다.
- 크론 설치와 실제 배포는 운영 변경이므로 승인 전에는 실행하지 않는다.

## I4 — 분산 추적과 구조화 로그

- W3C `traceparent` v00의 trace-id/span-id를 HTTP 진입에서 검증한다. 유효 입력은 trace-id를 이어 받고 새 server span-id를 만들며, 무효/부재 입력은 새 trace를 만든다. all-zero·대문자·잘못된 길이는 받지 않는다.
- core-api의 viz/AI 중계는 현재 요청의 trace를 `traceparent`로 전달한다. 사람 세션·연구실 경계 헤더와 섞지 않는다.
- core-api·viz-render·ai-service는 요청 완료마다 JSON 한 줄을 stdout에 남긴다: schema, timestamp, level, event, service, trace_id, span_id, parent_span_id, method, path, status, duration_ms. query/header/body는 제외한다.
- pipeline-worker는 한 바퀴 요약을 같은 JSON 스키마로 남기되 실패를 삼키지 않는다. 예외는 기존처럼 프로세스를 죽여 restart 정책과 알람이 잡게 한다.
- 공통 관측 커널은 core 원본과 세 복제본을 생성물 등기부로 byte-identical하게 고정한다.

## I4 — 알람과 데이터 레지던시

- 상태형 probe runner가 연속 실패/회복 전이에만 `alarm.raised`/`alarm.cleared` JSON을 남긴다. 정상 반복은 통지하지 않는다. probe 실행 실패·출력 부재·상태 파일 손상은 fail-closed다.
- 알람 대상은 배포 검증, 서비스 health, 백업 신선도다. 배포 시 5분 주기로 설치하며 알림 목적지는 레포 밖 `COLAB_OPS_ALERT_WEBHOOK_FILE`로 받는다. 목적지 미선언은 실제 운영 완료가 아니라 readiness 78이다.
- 레지던시 정본은 machine-readable TOML 하나다. AWS 저장/처리는 `ap-northeast-2`; CloudFront는 글로벌 edge cache; OpenAI 모델 호출은 공급자 관리 처리 위치이며 국내 고정이 아님을 명시한다. 실제 compose의 region과 선언이 갈리면 red다.
- AI에 보내는 데이터 범위를 질의 텍스트/제안 메타로 한정해 기록한다. 원본 파일 바이트·DB 자격증명 전송을 허용한다고 쓰지 않는다.

## 완료 판정

- 로컬: 실패 시험 RED → 최소 구현 GREEN, 서비스/경계/생성물/운영 selftest green.
- `IS4`: 격리 컨테이너 실리허설과 최종 `No changes`, 원격 변경 0.
- `I3`: 승인된 실제 trigger·red/green·health 전후·deploy_doctor 15/15.
- `I4`: 같은 배포 SHA에서 trace 연결, JSON 로그, 알람 raise/clear, 레지던시 gate, 기존 R-1 근거 소비. 알림 목적지와 스케줄이 실제로 연결되기 전에는 partial이다.
