# Dev 실제 연결 사전 점검

사용자가 현재 대화에서 Dev 실제 배포·AWS 연결·Slack 전송을 승인했다. 종전 로컬 전용 제한은 이번 수동 Dev 작업에 대해 변경되었다. 별도 자동배포 HOLD는 유지한다.

## 직접 확인

- 기존 `colab-dev` AWS 프로필 STS 인증 성공. 주체는 `colab-platform-s3-uploader-dev`.
- 해당 프로필의 EC2 DescribeInstances, Secrets Manager ListSecrets, CloudFormation ListStacks는 AccessDenied.
- 기존 Dev SSH 접속 성공. CURRENT_SHA: `fc45a9aa7c64`.
- Dev 서버 인스턴스 역할 STS 인증 성공. CloudFormation ListStacks는 AccessDenied.
- Dev core-api `/healthz`: `status=alive`. 이는 배포 doctor 전체 통과를 의미하지 않는다.
- 서버 비밀 파일 이름 목록에서 기존 `ops-slack-webhook.url` 확인. 신규 두 채널 매핑·secret ARN은 미확인. 내용은 출력하지 않았다.
- 신규 operator schedule/runtime의 지정 후보 경로는 존재하지 않았다. 다른 경로 설치 여부는 미확인.

## 필요한 입력

1. CloudFormation·IAM·Lambda·EventBridge·SQS·DynamoDB·Secrets Manager 설치를 수행할 수 있는 승인된 AWS 인증 경로. 조회 거부만으로 모든 쓰기 권한이 없다고 단정하지 않으며, 현재 자원/변경 내용을 확인할 권한도 확보해야 한다.
2. 개발 상태 및 활동·감사 보고의 두 Slack 채널 ID와 별도 webhook 비밀 파일 경로 또는 secret ARN.
3. manifest용 실제 연구실·계정 제외 목록과 수집 시작 시각은 승인 사양 및 실제 DB를 대조해 고정한다.

## 실행 순서와 상태

- [완료] 현재 사용자 승인 범위, 기존 절차, 접속/권한 사전 확인.
- [입력 대기] 위 AWS 인증과 두 채널 매핑.
- [대기] 검증된 소스와 main 배포 원천 정합, 고정 릴리스 입력/원복 계획 검토.
- [대기] advisor go/no-go 후 Dev 앱/비파괴 감사 마이그레이션 및 최소 권한 역할 배포.
- [대기] AWS 알림 자원/두 secret 연결, exporter/probe/전송/08시 스케줄 활성화.
- [대기] 실제 사건 전달과 채널 분리, 배포 doctor, AWS 처리 결과 및 Slack 접수 검증.

배포·AWS 자원 변경·Slack 전송은 아직 수행하지 않았다. 기존 데이터·미커밋 변경·HOLD를 보존했다. 이전 19개 로컬 통과는 실제 연결 검증을 대신하지 않는다.

## 후속 실제 수신 및 재점검

- 사용자가 서버 상태와 별도 활동·감사 채널의 시험 메시지 수신을 모두 확인했다.
- 활동 비밀은 저장소 밖 `/home/ttlhi10/.config/colab/slack-activity-webhook`에 0600으로 저장했으며 서버 webhook과 값이 다르다. URL은 기록하지 않는다.
- 사용자 승인 범위는 Dev 및 Stage 수동 배포·AWS 연결·실제 Slack 전송으로 확장되었다. 자동배포 HOLD 해제는 수행하지 않는다.
- WSL `colab-dev` STS 성공, CloudFormation ListStacks AccessDenied 재현. 두 webhook 준비는 해결됐으나 AWS 배포 인증 권한은 여전히 미해결이다.
- Stage 컨테이너 8개가 모두 healthy 상태임을 조회했다. 신규 알림 배포/마이그레이션/스케줄 설치는 아직 실행하지 않았다.
- 기존 상단의 webhook 미준비 및 전송 미실행 항목은 최초 점검 시점 기록이다. 현재 채널 수신 확인은 완료이며 AWS 자원 설치·자동 집계는 미완료다.

## HSW 인증 및 AWS 비밀 등록 완료

- `aws login --profile colab-hsw` 완료. STS는 계정 606175197146의 HSW 사용자로 확인했다.
- 기존 인증을 보존하고 `colab-notifications-deployer` 역할 프로필을 추가했다. AssumeRole 및 CloudFormation ListStacks 성공. 이전 권한 차단은 해소됐다.
- 실제 배포 역할의 인라인 정책 및 runtime boundary v1을 제공 JSON과 대조해 두 건 모두 일치 확인했다. 기존 colab-notify-* 역할은 0개였다.
- 서울 Secrets Manager에 다음 두 신규 비밀을 생성했다. URL은 출력/문서 기록하지 않았으며 각 파일 입력으로 전달했다.
  - development: arn:aws:secretsmanager:ap-northeast-2:606175197146:secret:colab/notifications/development-bdXWM7
  - activity: arn:aws:secretsmanager:ap-northeast-2:606175197146:secret:colab/notifications/activity-FCWhvQ
- Dev 사전 deploy_doctor: 실제 15개 검사 모두 통과, 실패 0, 면제 0. DB platform head는 0026_login_sessions다.
- 현재 main의 로그인/계정 변경과 이전 알림 변경을 별도 `/home/ttlhi10/colab-notifications-release-20260912`에서 통합했다. 원본 미커밋 변경은 그대로 보존한다.
- 알림 미배포 migration은 기존 0025 번호 충돌을 피하도록 후보에서 0027_operator_audit로 옮겨 0026_login_sessions 뒤에 연결했다. 이 변경은 아직 운영 DB에 적용하지 않았다.
- 후보 core API 회귀 시험 1127건 통과(실행 1127, skip 0, 외부 E2E deselected 6). 추가 통합 검사 진행 중.
- CloudFormation 알림 스택 생성, 앱 배포, 운영 감사 마이그레이션, cron 활성화는 아직 미실행이다. 자동배포 HOLD 유지.
