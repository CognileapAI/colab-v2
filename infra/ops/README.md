# 운영 관측·알람·데이터 레지던시

정본은 `alarms.toml`과 `data-residency.toml`이다. `gates/run.sh ops-observability`가 dev compose의 리전, 서비스 trace 배선, 알람 5분/3대상, 외부 AI 처리 위치를 대조한다.

HTTP 세 서비스는 W3C `traceparent`를 이어 받고 응답에 돌려준다. core-api가 viz-render/ai-service로 중계할 때 같은 trace-id를 전달한다. 각 요청은 `colab.ops.v1` JSON 한 줄로 stdout에 남으며 query string, 헤더, 본문, 이메일, 자격증명은 기록하지 않는다. pipeline-worker는 한 바퀴의 ID가 아니라 세 계수만 같은 스키마로 남긴다.

`alarm_runner.py`는 probe의 연속 실패가 임계값에 닿을 때 한 번 raise하고, 회복 때 한 번 clear한다. 활성 상태의 반복 실패와 정상 반복은 webhook 통지를 만들지 않는다. 상태 파일은 원자적으로 0600으로 교체한다. probe stdout/stderr는 알림에 싣지 않는다.

운영 모드는 HTTPS webhook URL 한 줄이 든 0600 파일을 `--webhook-file`로 요구한다. 미선언/권한 오류는 종료 78이다. `--observe-only`는 로컬 시험·배포 전 관측에만 쓰며 실제 알람 완료로 세지 않는다. webhook 목적지 결정과 5분 스케줄 설치는 운영 변경이므로 배포 승인 때 함께 수행한다.

데이터 레지던시의 정직한 한계: S3/RDS 원천은 서울 리전이지만 CloudFront는 글로벌 edge이고, OpenAI 모델 호출의 처리 위치는 공급자 관리이며 국내 고정으로 보장하지 않는다. AI로 보내는 범위는 검색 질의 텍스트와 계보 제안용 업로드 파일 메타다. 원본 파일 바이트나 자격증명을 보낸다고 선언하지 않는다.
