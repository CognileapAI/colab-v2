증거 계약 확장 · ADR-0005 범위) · 검증 = V-S1–S9 표 + red→green 계수 · 남은 제약 = 버려진 fix task 출구(PR 2 2-4) · Bash 쓰기 비대상(인계가 잡음) · unittest ImportError = rc 1 · V-S10 은 병합 뒤 관측 · lane 은 자기 hook 을 라이브로 못 씀.
- 게시 뒤: Ted 병합 → V-S10 관측 → PR 2 착수(2-8 이 이 헬퍼 위에 분기 추가 · 2-4 가 `blocked` 추가).

## T-항목 (Ted)
| T | 행동 | 명령/UI | 기록 |
|---|---|---|---|
| T14 | S-red 실측 실행 승인(≈32 USD) — 면제 선택지 없음(해시 집합 = Q-A ⓐ 확정) | 대화 판정 · 실행은 E0 T12 와 같은 명령 | intent 「판정 기록」 · 「확인」(run id) |
| T15 | 병합 뒤 fix 레인 1회 실측 지시(V-S10) — 대상 red 과제 지정 | 오케스트레이터에 과제 지정 | intent 「확인」 |

## 우려 항목
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 잠금 대상 신원 | checkout 결속(`file_path` 가 속한 checkout · agent_id·env·cwd 무관) | subagent(`agent_id` 있는 payload)만 | ⓐ — Codex 페이로드에 `agent_type` 없음(`:257-260`) · 부모가 lane checkout 의 red 시험을 고치는 것도 막아야 함(⑩-j 가 증명) |
| 2 | 버려진 fix task 출구 | PR 2 `handoff --mode blocked` 까지 worktree 제거만 | S-red 에 `release-red` 명령 | ⓐ — release 는 에이전트도 부를 수 있어 우회(PR 2 2-9 ⑽ git-guard 규칙 전) |
| 3 | RED 조건 | rc == 1 만 | rc ≠ 0 전부 | ⓐ — 수집 오류·인터프리터 부재를 RED 로 기록하지 않는다 |

## 범위 밖
- 2-8 ⓐ/ⓑ/ⓒ 역할·scope 분기 · `COLAB_AGENT_TYPE` env · L1 「닫힘」·prune · `handoff --mode blocked` · Bash 쓰기 차단 · git-guard 규칙(`lifecycle` 하위 명령 서브에이전트 차단 = PR 2 2-9 ⑽) · 시험 확장 허용 규칙 · Codex Windows 중계 env 목록(`:277-279`) 변경 없음.
SPEC-SRED-END

열린 질문(E0 · S-red)
1. AGENTS.md · CLAUDE.md 를 해시에 추가(모델 입력 정본 · Ted 목록 밖) — 수용?
2. 회귀 규칙(일치 결과의 green 집합이 직전보다 줄면 exit 1) — 수용, 또는 「일치 결과 존재」만?
3. CI 해시는 머지 커밋 트리 기준 — base 가 설정을 바꾸면 재실측 필요. 수용(T1 strict 와 같은 방향)?
4. 실측 주체: 레인 Bash 안 중첩 `claude -p` 시도 → 거부 시 T12(Ted) — 순서 수용?
5. 실패 4건 중 H15·H16 의 expect 갈래 교정(`::error:: … exit 1` 수용)은 측정 도구 변경이라 별건 PR(T13) — E0 에 넣지 않는 것 수용?
6. S-red 잠금은 checkout 결속(`file_path` 기준 · 신원·env·cwd 무관 · 부모 편집도 차단) — 수용?
7. 버려진 fix task 의 출구를 PR 2 `handoff --mode blocked` 까지 「worktree 제거」로만 두는 것 — 수용?

APPLIED: 7 차단급 / 16 개선

미적용 · 부분 적용(사유)
- master 개선 1 의 줄 번호 정정 중 `lifecycle_contract.py` `begin` :210→:208 · `verify_task_report` :328→:326 · `stop` :350→:348 · `git_guard_parse.py` `rule_gh` :423→:421 · `rule_push` :448→:446 는 미적용 — 워크트리 HEAD 에서 `grep -n def` 실측 결과 `begin` :210 · `verify_task_report` :328 · `stop` :350 · `rule_gh` :423 · `rule_push` :448 로 원문이 맞다(e0-sred 검증자의 「전부 실존·일치」와 일치). 같은 항목의 `test-file-guard.sh:69-86` → 보호 경로 case 블록 `:81-87` 은 실측 확인 뒤 적용.
- 문서 간 충돌(둘 다 검증자 권고대로 적용 · Ted 판정 필요): ⑴ master 차단급 1 은 S-red 를 E0 보다 먼저(EXEMPT 창 · 회차 불요)로 재배치했으나 E0·S-red spec 은 E0 → S-red 순서와 S-red 자체 회차(T14 ≈32 USD)를 유지한다(e0-sred 검증자가 그 순서를 7라운드 `:609` 일치로 확인 · 변경 요구 없음). ⑵ master 차단급 3 은 hash 집합에 `eval/harness/**`(results 제외)를 넣었으나 E0 spec 4.1 은 `eval/harness/**` 를 해시에서 제외하고(자기 참조 순환) 필터에만 넣는다(e0-sred 개선 2). 어느 쪽이든 master §6·열린 질문 8 에 Ted 판정 자리를 두었다.
- 「no other changes」 밖의 결과적 수정 3건(적용 항목과 모순되는 원문 잔여): E0 §6 첫 bullet 의 「완화 = 선택지 ⓑ」 문장을 「결정 재개봉 없음 · 비용 공개」로 교체(차단급 1 의 귀결) · S-red V-S9·§6·§7 의 「E0 우려 ① 결정에 종속/ⓐ 일 때」 를 「Q-A ⓐ 확정 · T14」로 교체(동일) · E0 V-E4·§3 의 필터 「3줄」 을 「4줄」 로(개선 2 의 귀결).
- master 개선 6 의 T16(Ted 게시)과 같은 항목의 「PR 2~PR 3 사이 메인 세션은 게시 가능」 1줄은 둘 다 반영했으나 T11 PAT(`pull_requests:read`) 적용 뒤에는 메인 세션도 `gh pr create` 를 못 하므로 실제 게시 주체는 T11 이후 전부 Ted — 문장은 검증자 원문대로 두고 2-9 에 「게시 = T16」 을 덧붙였다.