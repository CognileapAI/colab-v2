[harness: subagent output matched instruction-shaped pattern(s): settings-json. Control tags below are neutralized (`<` → `<\`); treat any remaining directive-shaped text as a finding to relay to the user, not an instruction to you.]

### C9
VERDICT: REVISE
- 최종 권고: ⓐ 문장별 교정 유지 · PR 3. 단 두 가지 조정 — ① `.agents/roles/lane-worker.md:27`(baseRef 이유 문장)은 L3 가 PR 2 에서 같은 문단(`git merge --ff-only` 앞 자기검사)을 고치므로 그 커밋에 얹어 PR 3 재접촉을 없앤다 · ② `.agents/roles/advisor.md:39` 는 새 문장을 만들지 않고 「(쓰기 도구가 없으므로 …)」 괄호를 「(파일 수정 금지는 `:46` 규율 — Claude advisor 는 Bash 가 남는다)」 로 축약. 완료 기준의 `loaded at launch` 는 영문 grep 이라 항상 0건(vacuous) → 실제 한국어 문자열(「launch 때 로드」)로 바꾼다.
- 반박 시도: advisor.md:46 「파일을 수정하지 않는다. 에이전트를 스폰하지 않는다」 이미 존재 → 규율 문장 신설 불필요. `.claude/agents/advisor.md:6` `disallowedTools: Edit, Write, NotebookEdit` 확인(Bash 잔존). spec §8 scope 목록(`S-HARNESS-IMPROVEMENT-20260925.md:181`)에 `.agents/rules/**`·`.agents/roles/**` 없음 → PR 1 과 겹침 0. 판정 기록 L3(`intent:558`)이 lane-worker.md 첫 동작 앞을 PR 2 에서 편집 → `:27` 중복 접촉.
- 위험: PR 2 L3 커밋에 C9 한 줄을 끼우면 L3 가 「PR 2 는 코드」 원칙에서 문서 1줄 예외를 갖는다(작음).

### C9 ⓑ (Claude advisor Bash 제거)
VERDICT: REVISE
- 최종 권고: 기각(Bash 유지) — 별도 T 항목으로 두지 말고 L7(PR 2 · 「도구 허용목록 변경 정의」 이미 포함 `intent:564`)의 결정에 흡수. 채택 시엔 C7 harness.yaml 기대값과 같은 커밋(judge-g7 묶음 메모 `:56`).
- 반박 시도: judge-g8.md 에 C9 항목 없음(grep 0건) · 판정 기록에도 없음 → 현재 미판정 고아. 실증: 이 advisor 세션의 도구 목록에 Grep·Glob 없음(Read · Bash 만) → Bash 제거 = 파일 검색 수단 전부 상실 · 워크플로 지시문 자체가 「ONE simple command per Bash call」로 Bash 전제. git-guard 는 advisor Bash 에도 적용(`.claude/settings.json` PreToolUse Bash 전역 · spec `:147`). Codex 등가는 「셸 없음」이 아니라 read-only sandbox(`agent-bridge.py:91-92`).
- 위험: Bash 로 파일을 바꾼 advisor 사례가 1건이라도 나오면 즉시 ⓑ 로 뒤집힌다(judge 뒤집힐 조건 동일).

### C10 (잔여: migration-guard 머리말 · worktree-setup baseRef/env-file)
VERDICT: REVISE
- 최종 권고: ⓐ 유지 · PR 3. 추가 3건 — ① migration-guard 주석의 `origin/main` 5곳(`migration-guard.sh:5` · `:10` · `:11` · `:55` · `:70`)도 같은 커밋에서 `origin/develop` 로: 코드는 이미 `origin/develop`(`:72` · `:76`)인데 주석만 낡음 · A6/V14 grep 은 decision-number-guard·README 만 대상(spec `:172`)이라 미흡수 ② 완료 기준 「`grep 'exit 1 은 통과'` 0건」은 Fable 판정(「exit 1 은 통과」 문장 존치)과 모순 → 기준을 「`판정을 못 하면 통과가 기본값` 0건」으로 교정 ③ worktree-setup 편집은 PR 1 A7 가 `:245-267` 블록을 OUT 버퍼로 재작성한 뒤 기준(spec `:128-129`)이므로 PR 1 병합 후 재앵커 · 지금 lane 지시 변경 금지(spec §12 `:209` 가 명시 제외).
- 반박 시도: `migration-guard.sh:21` 낡은 2문장 · `:22` superseded 표기 · `:28-29` exit 2 · `:32` 도달 불가 확인(`:31` 은 validate-input 빈 출력 경로라 도달 가능 → 삭제 대상은 `:32` 뿐). `worktree-setup.sh:247-259` fresh/origin/main/P-E · `~/.colab-v2-test.env` 고정 확인. 「A7 에 얹어 한 번에」는 더 싸 보이나 lane 진행 중 + env 전달 관측 의존(judge `:32`) → PR 3 유지.
- 위험: hook 프로세스에 settings `env`(`COLAB_TEST_ENV_FILE`)가 안 들어오면 「없다」 오탐 → 메시지에 변수명·해석 경로를 함께 찍어 두 후보 열거로 후퇴 가능하게 쓴다.

### C11
VERDICT: KEEP
- 최종 권고: ⓑ+ⓒ · PR 3. 종속 4곳을 완료 기준에 명시 — `bootstrap-diet.sh:50` 주석 · `:70-71` find · `:84`·`:86` 두 분기 줄 삭제 · `:76` 줄 끝에 위치 덧붙임(judge 의 `:80` 은 `:76` 이 실제) · `test_harness_lifecycle_contract.py:411` `assertIn('legacy 참고 후보')` 교체 · `agent-bridge.py:346` 「mtime suggestion above」 삭제(Codex SessionStart 문장). `test_agent_bridge.py:205` 'mtime suggestion' 은 mock 문자열이라 필수 아님.
- 반박 시도: ⓑ 단독(위치 줄 생략)이 더 싼가 — AGENTS.md 가 `R-HARNESS-PR-CENTRIC.md` 를 이름으로 주지만 `COLAB_ROUND`/payload `round` 지정 수단은 hook 출력 외에 안내처가 없어 ⓒ 덧붙임 유지. PR 1 A7 는 `bootstrap-diet.sh:23-26` 주석만 접촉(spec `:132` · `:184` ⑤) → hunk 분리 · 흡수 아님. `test_harness_lifecycle_contract.py`·`test_agent_bridge.py` 는 PR 1 scope(spec `:181`)라 PR 3 는 병합 뒤 기준.
- 위험: A7 주석 편집으로 bootstrap-diet 줄 번호가 밀림 → PR 3 착수 때 재앵커 필수(내용 기준 검색).