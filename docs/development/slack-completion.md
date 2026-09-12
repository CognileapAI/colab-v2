# Slack 개발 완료 보고

slack-completion 스킬은 전체 사용자 요청이 끝나고 선언된 검증이 모두 green일 때만 한국어 ELI5 보고서와 완료 증거를 준비한다. Codex Stop 훅은 모델이나 스킬을 호출하지 않고 같은 세션과 체크아웃 상태에 묶인 준비물만 전송한다.

일반 응답 종료, 개별 레인 종료, red 또는 준비 실패가 있는 증거, 남은 작업이 있는 완료 선언은 전송되지 않는다. 보고서, 증거, HEAD, 작업 파일이 준비 후 바뀌어도 전송하지 않는다. 동시 Stop은 원자적으로 한 건만 선점한다. 전송 결과가 불명확하면 자동 재시도하지 않고 Git private 디렉터리에 uncertain 기록을 남긴다. 성공하거나 결과가 불명확한 동일 완료 건은 다시 준비할 수 없다. 같은 대화에서 별도 개발 요청을 새 task 증거로 끝낸 경우에는 새 완료 건으로 준비할 수 있다.

웹훅은 저장소 밖 ~/.config/colab/slack-webhook에 mode 0600으로 둔다. 아래 대화형 명령은 비밀을 화면에 표시하지 않으며, 입력이 비었거나 정확한 Slack HTTPS 웹훅 형식이 아니면 기존 값을 보존한다.

    python3 scripts/slack_completion.py setup

완료 보고서는 첫 gate-summary.json과 같은 전용 보고서 디렉터리에 slack-eli5.md로 작성한다. lifecycle 검증기는 시작 때 선언된 gate report 디렉터리를 입력 스냅숏에서 제외하므로, 검증 뒤 설명문을 작성해도 검증 근거가 낡은 것으로 바뀌지 않는다. 실제 task-bound gate summary를 모두 지정해 준비한다.

    python3 scripts/slack_completion.py prepare \
      --report <eli5-report.md> \
      --evidence <task-id>:<gate-summary.json> \
      --whole-scope-complete

.codex/hooks.json 변경은 자동 활성화가 아니다. 새 워크트리에서 프로젝트 설정을 신뢰하고 /hooks에서 새 Stop 정의를 따로 검토해야 한다. 직접 실행한 fixture 테스트는 실제 Codex 앱 훅 활성화를 증명하지 않는다. Windows 이벤트는 기존 agent-bridge.py codex-event 경로가 JSON stdin을 WSL로 전달한다.

## 배포 완료 알림은 종료 훅과 분리

배포는 [공통 실행기](../../infra/releases/README.md)가 배포·검증 성공 직후 자동 전송한다. DV/ST 묶음, 중복 방지, 알림 실패/전송 불명확 기록 및 알림만 재시도는 배포 실행기가 담당한다. 개발 완료 Stop 훅은 유지하지만, 같은 배포 건을 다시 `prepare`하여 중복 알림을 만들지 않는다. 배포 알림에는 Codex 훅 trust/Stop 발생 여부가 필요하지 않다.
