# 하네스 고도화 — lane-hygiene 검토·구현 · Ponytail 경계 훅 보정

base: `develop` · head: `claude/harness-consolidation`

## 무엇을 모았나
하네스 관련 미병합 브랜치 2개를 한 갈래로 모았다. 나머지 하네스 PR(#116 · #117 · #119)은 이미 develop 에 있다.

| 출처 | 처리 |
|---|---|
| `origin/claude/harness-lane-hygiene` (intent·보류 spec) | 네 검토 질문에 증거로 답함 → Ted 승인 "전부 권고대로 할게," → spec v2 → 레인 2개로 구현 |
| `worktree-ponytail-systemic` (Ponytail PostToolUse 훅) | cherry-pick 후 결함 2건 보정(실행비트 · Codex 세션 구분) |

## 무엇이 바뀌나
- **researcher 자동 task 훅(R1)** `scripts/harness/hooks/researcher-task.sh` — researcher 가 뜨면 H6 작업 증거를 자동으로 열고 task_id·handoff 명령을 맥락에 싣는다. 지시문에 절차가 빠져 종료 훅 반송으로 30턴을 태우던 문제(재개 researcher 24회·38턴 · 이번 세션 2/2 절단)를 없앤다. agent_id 는 걸지 않는다(Start/Stop 일치 미증명).
- **브라우저 세션 종료(F2)** `live_audit.sh` — 스스로 만든 세션만 EXIT 에서 닫는다. 호출자가 준 `AB_SESSION` 은 닫지 않는다. `frontend-visual` 은 `AGENT_BROWSER_IDLE_TIMEOUT_MS` 기본 10분.
- **잠금 미상속(F1)** `gates/tools/_lock.sh` `gate_mutex_spawn` — 데몬을 띄우는 자식에 호스트 뮤텍스 fd 를 넘기지 않는다. 레인 뒤 데몬이 잠금을 쥐어 다음 게이트가 605~640초 대기·78 나던 원인.
- **지시·역할 규칙** — 재개 지시문 task_id 재기재 · researcher 중 같은 체크아웃 커밋 금지 · 레인 1건 = 계열 2~3개 · advisor ② 에 gate-summary 절대경로 · advisor 도구 8회 뒤 판정 · advisor ① 지적마다 차단급/개선 등급.
- **Ponytail** — 코드 경로 첫 편집에 `colab-ponytail` 요지를 세션·에이전트당 1회 싣는다(비차단).
- 버린 것: SubagentStop 뒤처리 훅(다른 저장소 브라우저를 죽임) · handoff JSON 계약 변경 · advisor ① 생략 기준(6단계 중 0단계 생략).

## 검증 (합친 브랜치에서 실제 실행)
`gates/run.sh all` 1회(develop 7acd0fce 병합 뒤 · HEAD 736df0f9):
```
── 계 : green 54 / red(판정) 3 / red(준비) 17
── 호스트 뮤텍스 : 잠금 17건 · 면제(parallel 선언) 57건 · 대기 누계 0s
```
- 이 브랜치가 건드린 게이트 8개는 모두 green: agent-bridge · harness-contract · harness-contract-selftest · exec-bit · gate-host-mutex-selftest · work-item-consistency · planning-freshness · frontend-visual-selftest(실브라우저).
- 바뀐 `run_one` 호출부로 serial 17건이 잠금을 잡고 풀었다. `Bad file descriptor` · `ambiguous redirect` · `unbound variable` 0건.
- red(준비) 17 = 이 작업 사본에 서비스 venv·`frontend/node_modules` 부재(표식 전문은 로그).
- red(판정) 3의 판정:
  - `generated-up-to-date` · `frontend-design-lint-selftest` — `node_modules` 부재를 판정 red 로 분류했다. 주 체크아웃 `node_modules` 를 링크해 다시 돌리면 둘 다 green 1 / 0 / 0. 도구 부재를 78 이 아니라 1 로 내는 분류 결함이다 → 후속 항목.
  - `ops-observability-selftest` — develop(7acd0fce) 격리 사본에서도 같은 오류로 red(「backup probe가 기존 check_backups와 결합되지 않았다」). 이 게이트가 develop 에서 이미 잡는 결함이다 → 후속 항목.
- 수정 전 red 증명: 잠금 재현 스크립트(BLOCKED → 수정 후 획득) · mutex selftest ⑴⑵ · visual selftest ⑶(고유 세션 아님) · ⑸(trap 을 끄면 세션 프로세스 3개씩 잔존) · 훅 시험 12건 · f2 2건 · bridge 문구 1건.
- 레인 뒤 · 전수 뒤 이 브랜치가 연 `la-…` 세션 프로세스 0개.

## 미검증
- 실제 Claude·Codex 세션에서 새 훅 2개(researcher-task · ponytail-inject)의 발화. 병합 뒤 이 PC `/hooks` 재신뢰가 필요하다(사용자 몫). 재신뢰 뒤 researcher 1건으로 첫 정지 H6 통과와 Start/Stop agent_id 일치 여부를 기록한다(spec 후속).
- `gates/run.sh` 에 게이트 여러 개를 넘기면 첫 번째만 돈다(부수 발견 · intent 기재 · 이 PR 범위 밖).

## 근거
- intent `dev-package/intent/2026-09-24-harness-lane-hygiene.md` · spec v2 `dev-package/prd/specs/S-HARNESS-LANE-HYGIENE-20260924.md`
- 증거 `dev-package/reports/harness/20260924-lane-hygiene-review/`(A2 · A3 · B2 · C · `lock-inherit-repro.sh`)
- advisor ① approve-with-changes(차단급 4 · 개선 5 반영) · advisor ② approve-with-changes — 차단급 2(실브라우저 세션 소멸 단언 · 전수 뒤 잔존 0 증거) · 개선 4 반영

## 게시 절차 (사용자)
```bash
cd "<32 CoLAB-v2 루트>"
gh pr create --base develop --head claude/harness-consolidation --title "하네스 고도화 — lane-hygiene 검토·구현 · Ponytail 경계 훅 보정" --body-file dev-package/reports/harness/20260924-lane-hygiene-review/PR-BODY.md
```

## 병합 뒤 (사용자)
```bash
# /hooks 에서 새 SubagentStart(researcher)·PostToolUse(ponytail) 항목 재신뢰
git worktree remove ".claude/worktrees/ponytail-systemic"
git branch -D worktree-ponytail-systemic
git push origin --delete worktree-ponytail-systemic claude/harness-lane-hygiene
```
