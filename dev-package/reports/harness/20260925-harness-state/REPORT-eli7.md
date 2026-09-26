# 하네스 상태 보고 — 2026-09-25 · develop 67a03a05 (ELI7)

## 한 줄
하네스의 기본 구조는 잘 서 있고, 오늘 돌린 검사는 모두 통과했다.
그런데 막아야 할 것을 못 막는 구멍이 있고, 가짜 red를 내는 곳이 있다. 문서와 메모리는 코드보다 늦다.

## 하네스 = 5부분
- hook 11개: 에이전트가 도구를 쓰기 직전·직후에 자동으로 돈다. 위험한 git 명령 같은 것을 막는다.
- 역할 5개: advisor(fable·16턴) · researcher(opus·50) · lane-worker(opus·200) · measurement-lane(sonnet·60) · gate-runner(haiku·20)
- gate 76개: gates/run.sh 로 돈다. 그중 "required"로 적힌 것이 12개다.
- CI workflow 3개: PR마다 gate를 돌리고 증거를 모은다.
- 증거 저장소: .git/colab-harness. 레인이 무엇을 바꾸고 무엇을 검사했는지 적힌다.

## 오늘 실측 (plain mode · 모두 exit 0)
harness-contract · agent-bridge check · agent-bridge gate(unit test 156 통과·10 skip) · adr-records(ADR 9)
돌리지 않은 것: DB gate · 서비스/프론트 테스트 · E2E · task 모드

## 고칠 것 top 6
1. git-guard 공백 경로 `git -C "…"` 우회 — high · 메인 재현 · git-guard.sh:167
2. test-file-guard 가 Claude 레인에서 꺼져 있음 — medium · test-file-guard.sh:32
3. develop 원격 필수 검사 없음 · required 12개는 개수만 셈 · pr_contract 는 CI 밖 — medium
4. Workflow lane 격리 미보장 — high · 1회 관측 · 원인 미기록
5. 증거 저장소 153MB · task 204개 · 고아 74개 · close 없음 — medium
6. 가짜 red(merge-parent · ai-service 전용 PR 잠복) · run.sh 인자 무시 · 0/1/78 어긋남 — medium

자세한 내용: findings-verified.md · R1–R5 노트 · advisor2.md
