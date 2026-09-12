# 운영자 알림 런타임

infra.notifications는 개발 상태와 운영 일일 보고를 서로 다른 Slack webhook으로 전달한다. 로컬 검증은 loopback HTTP만 사용한다.

manifest 필수값은 환경, 용도, 수집 시작 시각, 명시적인 시험 연구실·계정 제외 목록, 전체 원천, probe argv/timeout, AWS 계정·리전·자원, 서로 다른 두 채널 secret ARN이다. cli validate의 local 또는 connected profile로 검사한다. connected 입력 부재와 같은 secret 참조는 78이다.

영속 상태는 pending, sending, retry_wait, uncertain, held, sent다. 일반 uncertain·held는 ID 지정 resolve로만 해소한다. 업무나 배포 명령을 다시 실행해 알림을 재시도하지 않는다.

install_jobs.py --render는 probe 5분, export/retry 1분, 일일 보고 08:00 Asia/Seoul을 출력한다. --apply는 별도 실제 연결 절차 없이는 78을 반환한다.
