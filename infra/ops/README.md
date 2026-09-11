# 운영 관측·알람·데이터 레지던시

정본은 `alarms.toml`과 `data-residency.toml`이다. `gates/run.sh ops-observability`가 dev compose의 리전, 서비스 trace 배선, 알람 5분/3대상, 외부 AI 처리 위치를 대조한다.

HTTP 세 서비스는 W3C `traceparent`를 이어 받고 응답에 돌려준다. core-api가 viz-render/ai-service로 중계할 때 같은 trace-id를 전달한다. 각 요청은 `colab.ops.v1` JSON 한 줄로 stdout에 남으며 query string, 헤더, 본문, 이메일, 자격증명은 기록하지 않는다. pipeline-worker는 한 바퀴의 ID가 아니라 세 계수만 같은 스키마로 남긴다.

`alarm_runner.py`는 probe의 연속 실패가 임계값에 닿을 때 한 번 raise하고, 회복 때 한 번 clear한다. 활성 상태의 반복 실패와 정상 반복은 webhook 통지를 만들지 않는다. 상태 파일은 원자적으로 0600으로 교체한다. probe stdout/stderr는 알림에 싣지 않는다.

운영 모드는 HTTPS webhook URL 한 줄이 든 0600 파일을 `--webhook-file`로 요구한다. 미선언/권한 오류는 종료 78이다. `--observe-only`는 로컬 시험·배포 전 관측에만 쓰며 실제 알람 완료로 세지 않는다. webhook 목적지 결정과 5분 스케줄 설치는 운영 변경이므로 배포 승인 때 함께 수행한다.

dev에서는 `install-schedule.sh`가 `/etc/cron.d/colab-ops` 전용 파일에 세 대상을 5분마다 건다. 기존 `/etc/cron.d/colab-dev`의 백업·정리 잡은 hash 전후 대조로 보존한다. 설치·제거 전에는 `/opt/colab-v2/ops-alerts`에 snapshot을 남기며, 기존 ops 파일이 생성 내용과 다르면 덮어쓰거나 지우지 않는다. `run-scheduled.sh`는 target별 0600 state/log와 별도 잠금을 쓴다. 5분 안에 앞 회차가 끝나지 않으면 `already-running`과 종료 75를 남기고 서비스 실패 계수를 올리지 않는다.

세 probe는 임의 명령을 받지 않는다. `deploy-verification`은 `CURRENT_SHA`의 실제 core-api 이미지에서 기존 dev `deploy_doctor.py --env dev` 15항 전체를 실행한다. `service-health`는 dev의 core·pipeline·viz·AI 네 `/healthz`가 HTTP 200과 정확한 `unit` 본문을 함께 내는지 본다. `backup-freshness`는 같은 현재 SHA 이미지에서 기존 `deploy_doctor.check_backups`만 불러 dev S3 `_ops/backups/dev/`의 24시간 oracle을 재사용한다.

`infra/dev/ship.sh`는 working tree가 아니라 배포 SHA의 `git archive`에서 probe·doctor·마이그레이션 head·RLS 판정기 묶음을 만든다. EC2는 archive hash를 확인한 뒤 일반 사용자가 바꿀 수 없는 `/opt/colab-ops/versions/<SHA>`에 root 소유로 풀고, 고정 경로 `/opt/colab-ops/bin/dispatch-current.sh`를 cron에 건다. dispatcher는 매 회차 `CURRENT_SHA`에 해당하는 bundle의 manifest·파일 hash·root 소유·상위 디렉터리 쓰기 권한·symlink 부재를 확인한 뒤 실행한다. 따라서 새 SHA 반입과 이전 SHA rollback 때 cron을 다시 쓰지 않는다. source 또는 manifest가 없거나, 옛 source이거나, 한 파일이라도 바뀌면 준비 실패 또는 RED다.

데이터 레지던시의 정직한 한계: S3/RDS 원천은 서울 리전이지만 CloudFront는 글로벌 edge이고, OpenAI 모델 호출의 처리 위치는 공급자 관리이며 국내 고정으로 보장하지 않는다. AI로 보내는 범위는 검색 질의 텍스트와 계보 제안용 업로드 파일 메타다. 원본 파일 바이트나 자격증명을 보낸다고 선언하지 않는다.
