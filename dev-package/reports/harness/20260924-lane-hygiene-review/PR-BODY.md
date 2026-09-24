# 하네스 브랜치 정리 — lane-hygiene 검토 완료 · Ponytail 경계 훅 보정

base: `develop` · head: `claude/harness-consolidation`

## 무엇을 모았나
하네스 관련 미병합 브랜치 2개를 한 갈래로 모았다. 나머지 하네스 PR(#116 · #117 · #119)은 이미 develop 에 있다.

| 출처 | 내용 | 처리 |
|---|---|---|
| `origin/claude/harness-lane-hygiene` (2커밋) | 하네스 고도화 intent·보류 spec | 그대로 가져와 intent 의 「진지하게 따질 것」 네 절에 증거로 답하고 권고를 적었다 |
| `worktree-ponytail-systemic` (1커밋 · 2026-09-18) | 코드 편집 시 Ponytail 요지를 싣는 PostToolUse 훅 · lane-worker skills 에 `colab-ponytail` | cherry-pick 후 결함 2건 보정 |

## Ponytail 보정 (적용 대상)
- 훅 원본·어댑터가 `100644` 로 들어와 있었다. 기존 훅 20개는 `100755` 다 → 규칙 `4-3` 대로 인덱스 실행비트 기록.
- Codex 경로에서 bridge 가 `session_id` 를 넘기지 않아 1회 표식 키가 모든 Codex 세션에서 `-main` 으로 겹쳤다(60분 안 두 번째 Codex 세션은 요지를 못 받음) → `codex_payloads` 가 `session_id` 를 넘긴다 · 시험 1건 추가(수정 전 red 확인).
- 중복 여부: lane-worker 는 skills 선적재로 이미 받는다. 훅은 `colab-v2-work` 를 읽지 않은 주 세션·다른 에이전트·Codex 를 덮는다. 막지 않고 세션·에이전트당 1회다.

## lane-hygiene 검토 (구현 없음 · Ted 판정 대기)
intent `dev-package/intent/2026-09-24-harness-lane-hygiene.md` 의 「답」「권고」「판정 요청」. 근거는 이 폴더의 A2·A3·B2·C 와 `lock-inherit-repro.sh`.
- ① 턴 한도: 원인은 역할별로 다르다. 가장 큰 낭비는 종료 훅 반송 루프(재개 researcher 38턴). 권고 = researcher 자동 task 훅(R1) + 체크리스트·역할 본문.
- ② 증거 경로: handoff 계약 변경 대신 절대경로 중계를 규칙화(코드 0).
- ③ 뒤처리: SubagentStop 훅안 기각. 원인은 잠금 fd 상속 + `live_audit.sh` 미종료. 권고 = F2(자기 세션 close + 유휴 종료) · F1(자식에 fd 미상속).
- ④ advisor ① 생략: 초안 기준은 6단계 중 0단계를 생략한다 → 기준 미채택 · 결함 등급 기록.
- 1차 초안 spec 은 「대체된다」 표지만 더했다.

## 검증 (이 브랜치에서 실제 실행)
| 게이트 | 결과 |
|---|---|
| agent-bridge | green 1 / red(판정) 0 / red(준비) 0 |
| harness-contract | green 1 / 0 / 0 |
| harness-contract-selftest | green 1 / 0 / 0 |
| exec-bit | green 1 / 0 / 0 |
| work-item-consistency | green 1 / 0 / 0 |
| planning-freshness | green 1 / 0 / 0 |
- `python3 -m unittest scripts.tests.test_agent_bridge scripts.tests.test_harness_source_layout` OK(skipped 10).
- `agent-bridge.py codex-event` 실호출: 세션 A 첫 편집 1회 · 재호출 0회 · 세션 B 1회.

## 미검증
- 실제 Claude 세션에서 `ponytail-inject.sh` 발화. 병합 뒤 이 PC `/hooks` 에서 새 PostToolUse 항목을 재신뢰해야 한다(사용자 몫).
- 실제 `frontend-visual` 게이트로 잠금 누수를 처음부터 끝까지 재현하지 않았다. 기전은 재현 스크립트와 조사 C 의 probe 로 확인했다.

## 게시 절차 (사용자)
```bash
cd "<32 CoLAB-v2 루트>"
gh pr create --base develop --head claude/harness-consolidation --title "하네스 브랜치 정리 — lane-hygiene 검토 완료 · Ponytail 경계 훅 보정" --body-file dev-package/reports/harness/20260924-lane-hygiene-review/PR-BODY.md
```

## 병합 뒤 정리 (사용자 판단)
```bash
git worktree remove ".claude/worktrees/ponytail-systemic"   # 잠금 표시가 있으면 먼저 git worktree unlock
git branch -D worktree-ponytail-systemic
git push origin --delete worktree-ponytail-systemic claude/harness-lane-hygiene
```
