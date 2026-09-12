# 운영 알림 실행 연결

코드 반영만으로 배포·AWS 생성·cron 설치·Slack 전송을 수행하지 않는다. 실제 연결 전 승인된 환경 설정과 두 채널의 Secrets Manager ARN을 준비한다.

## 실행 위치와 설정

명령은 고정된 배포 소스의 저장소 루트에서 실행한다. `runtime_python`에는 별도 운영 Python 환경의 절대 경로를 지정한다(미지정 시 배치 PATH의 `python3`). 앱 가상환경을 변경하지 않고 [설치 입력](../ops/OPERATOR_RUNTIME_SETUP.md)에 따라 core 패키지와 알림 의존성을 함께 준비한다. connected 명령에는 `COLAB_OPERATOR_TABLE`, `COLAB_OPERATOR_MANIFEST_JSON`, `DEVELOPMENT_QUEUE_URL/ARN`, `ACTIVITY_QUEUE_URL/ARN`, `DEVELOPMENT_WEBHOOK_SECRET_ARN`, `ACTIVITY_WEBHOOK_SECRET_ARN`, `INSTANCE_STATUS_ALARM_NAME`, `SYSTEM_STATUS_ALARM_NAME`이 필요하다. EC2의 IAM 역할을 사용한다. DB exporter는 별도 exporter 로그인 연결을 `COLAB_OPERATOR_DATABASE_URL`에서 읽으며 Slack/Lambda에 DB 자격을 전달하지 않는다. Webhook 값은 명령 인자·manifest에 넣지 않는다.

manifest `probes`는 아래처럼 환경별 **실제 명령 인자와 제한 시간**을 선언한다. 대상 환경의 endpoint·port·image·backup oracle을 그 명령 인자/설정으로 고정한다. 다른 환경의 기본값을 가져오지 않는다.

```json
{"target":"service-health","command":["/absolute/python","/absolute/verified/probe.py","--endpoint","https://declared-environment.example/healthz"],"timeout":120}
```

예제 경로는 연결 값이 아니다. dev의 기존 `infra/ops/probes/*`는 dev 전용이므로 staging 명령으로 재사용하지 않는다. rehearsal은 명시한 로컬 fixture 명령으로 실행한다. manifest 검증은 5개 audit source, 두 분리 채널, 시간대, 제외 대상, probe argv, AWS 범위를 누락 시 78로 거부한다.

## 연결되는 작업

`python3 -m infra.notifications.install_jobs --manifest /absolute/manifest.json --render`는 설치 없이 실제 호출 가능한 명령을 출력한다. `--apply`는 설치를 수행하지 않고 78이다. 운영 배치 관리자가 고정 저장소 루트와 위 환경을 설정한 후 다음 간격으로 연결한다.

- `probe.commands` 각각: 5분. 상태 파일별 잠금, 연속 두 실패 및 복구를 spool에 저장하고 remote heartbeat를 기록한다.
- `export`: 1분. 커밋된 audit outbox를 원격에 저장·확인한 다음 원본 수신 표식을 기록한다.
- `spool`: 1분. 배포/관측 이벤트를 원격 저장소에서 다시 확인한 뒤 로컬 파일을 제거한다. SQS 전송 장애와 무관하게 원격 retry가 재발행한다.
- `retry`: 1분. 원격 미전송 사건을 queue에 재발행하며 15분 heartbeat 부재도 판정한다. 재발행은 Slack 전달 완료와 구별한다.
- `daily`: KST 08시 및 누락 보충용 5분 반복. 실제 작업 내부의 날짜·시각 검사가 중복 보고를 막는다.

배포 CLI의 기본 spool은 `/var/lib/colab/operator-spool`이며 `COLAB_OPERATOR_SPOOL_DIRECTORY`로 경로를 명시할 수 있다. 배포 상태 `queued`는 전달 완료가 아니다. 알림 재시도는 배포/검증 명령을 다시 실행하지 않는다. 미전송 처리에는 위 spool/retry 작업을 사용한다.

## 확인과 해소

```bash
python3 -m infra.notifications.cli validate --manifest /absolute/manifest.json --profile connected
python3 -m infra.notifications.cli status --profile connected EVENT_ID
python3 -m infra.notifications.cli resolve --profile connected EVENT_ID confirmed-sent --actor OPERATOR_ID
python3 -m infra.notifications.cli resolve --profile connected EVENT_ID retry --actor OPERATOR_ID
```

`resolve`는 held/uncertain에만 적용되며 작업자와 처리 시각을 기록한다. 재전송 본문은 중복 가능 표시를 붙인다. `publish-pending`은 남은 미전송이 있으면 20, 설정 준비 실패는 78이다. local 프로필은 서로 다른 loopback 수신처만 허용한다.
