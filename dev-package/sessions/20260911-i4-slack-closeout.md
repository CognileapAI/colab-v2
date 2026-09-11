# I4 Slack 자동 점검·알림 마무리

사용자 전체 실행·개발·main push/배포 승인은 유지된다. 수신처를 Slack으로 정하고 Webhook 파일을 저장했다. 사용자 콘솔에서 ColabDevPublicWebDoctorRead 정책 생성 완료를 통보한 뒤, 배포42e44에서 실제 IMDS deploy-verification 단일15/0/0 exit0을 확인했다. IAM 정책 문서 원격 조회 성공으로 확대하지 않는다. 기존 uploader 자격에는 IAM 조회 권한이 없다.

| 작업 | 수용 기준 | 상태 |
|---|---|---|
| 권한 적용 효과 | 서버자체계정 단일15/0/0 | 확인 |
| Slack 메시지 형식 | exact Slack hostname·text·응답ok·generic호환·전송실패 상태 보존 | 관련4게이트 통과 |
| 코드 main·배포 | 관련 게이트·독립검토·봉인 source·현재SHA 일치 | PR21 main42cffb3·dev/staging 배포 완료 |
| 격리 알람 시험 | 실제 probe 실패3회 발생1/반복0·복구1회 해제1 | 23:23:52~55 전송 성공·실서비스 불변 |
| 수신 확인 | 지정 수신처에 시험 발생·해제 각1개 확인 | **완료 — 2026-09-11 사용자 “엉 왔음”** |
| 정기 실행 | 실제5분cron 3targets exit0/정상state, 기존cron불변 | 23:25 실제3targets 정상·CROND 시작/종료확인 |
| 완료 반영 | 구현→관련시험→실제환경·수신확인→대장done→최종main반영 | **대장 done 반영** |

시험은 acceptance 고유 target·별도state·probe입력 디렉터리를 사용한다. 실제 서비스·운영CURRENT_SHA·운영alarm state를 실패조건으로 바꾸지 않는다. Webhook URL·키·DBURL·probe본문은 메시지와 공개 기록에서 제외한다. 서버에는 root:0600 파일로 저장한다. 실패시 새cron전용파일을 기존 remove 절차로 제거하고 직전 정상 이미지/설정을 복원한다. 사용자생성IAM정책을 임의로 삭제하지 않는다.

준비물·실행 로그는 보호된 `$HOME/colab-v2-releases/i4-slack-closeout`에 둔다. 원본 사용자 변경은 유지하고 격리 사본에서만 기록한다. 완료 전에는 I4open을 유지했다. 사용자 수신 확인 뒤 I4를 done으로 반영했다.

## 실제 실행·복구 근거

코드 `42cffb328b1e5fbd9d20ca0c6fa34139467c3c47`, PR21, 배포 태그 `dev-20260911-2`. Slack 메시지는 2xx 응답과 본문 ok를 함께 확인하고, 전송 실패 때 성공 state를 저장하지 않는다. generic webhook 동작은 유지한다. 관련 mock에는 실제 네트워크 호출이 없다. 초기 source 게이트 실패는 격리 사본의 core-api Python 환경 부재였으며 기존 환경 연결 후 같은 검사가 통과했다. 소스 레인의 verify-report는 부모가 실제 소스 경로에서 검증했다. 종료 훅의 부모 cwd 고정 제한을 source 성공으로 위장하지 않았다.

사용자 콘솔 정책 생성 후 실제 서버 IMDS 점검은 변경 전·후 단일15/0/0이다. 로컬 운영자15/0/0과 합산하지 않았다. 정책 JSON의 IAM 원격 재조회는 성공했다고 주장하지 않는다.

실제 Slack 시험 target은 `acceptance-deploy-verification-42cffb328b1e`다. 별도 입력에서만 현재SHA를 없는 이미지로 지정했다. 실패1은 통지0, 실패2는 발생1, 실패3은 반복0, 실제SHA로 돌아온 복구1은 해제1. 각 단계 state와 exit가 기대값에 맞았고 실제 앱4개 ID·image·health는 불변이었다. 서버 전송 성공과 채널 수신 확인은 분리한다. 2026-09-11 사용자가 지정 수신처에서 두 문구를 “엉 왔음”으로 확인했다. 채널 이름은 추정하지 않는다. 따라서 I4 완료 조건을 충족했다.

실제 cron은 23:25에 3대상 모두 실패0/active=false를 저장했다. 설치 전 이 3state가 없었고, CROND의 CMD/CMDEND 각3건과 새 observed_at을 확인했다. 설치 외에 운영 target을 수동 호출하지 않았다. 기존 dev cron과 새 ops cron hash는 설치 직후와 같다. 원문과 계수는 `reports/i4-slack-closeout/results.json`.

중단할 때는 현재 SHA를 먼저 확인하고 아래 기존 설치기의 remove를 실행한다. 이 명령은 기록만 했고 실행하지 않았다. 기존 dev 백업·정리 cron은 보존한다.

```bash
sudo /opt/colab-ops/versions/42cffb328b1e/infra/ops/install-schedule.sh --env dev --webhook-file /etc/colab/ops-slack-webhook.url remove
```

개발 서버 직전 정상 버전은42e44이며 `/opt/colab-v2/evidence/i4-slack-42cffb328b1e`의 설정·CURRENT_SHA·MAIN_SHA를 보존했다. 롤백은 ops cron을 멈춘 뒤 이미지5종·설정·기록을 모두 직전 버전으로 맞추고 up/doctor로 검증한다. 사용자 생성 IAM 정책을 임의 삭제하지 않는다. 최종 요구 미달0건, 범위 초과0건이다.
