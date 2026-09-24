# Intent: 하네스 고도화 — 턴 한도 재단 · 증거 경로 규격 · 레인 뒤처리 훅 · 작은 단계의 advisor ① 생략 기준
메타 — 발의자: Ted · 작성 2026-09-24 · 승인: **2026-09-24 Ted 원문 "권고대로 해서 하네스고도화하고. 좋아. 작업은계속하자"**(디자인 구조 프로그램의 하네스 평가에서 낸 권고 4건을 그대로 승인)

## 문제
- 디자인 구조 프로그램(P0~P3 · 2026-09-24) 실측: researcher 가 30턴을 조사에 다 쓰고 **0바이트**로 끝난 사례 2회 · advisor 12턴 잘림 2회 · lane-worker 200턴 잘림 1회. 매번 「먼저 쓰고 좁혀서 재개」로 살렸으나 재개 비용이 붙었다. 원인은 지시 범위가 턴 한도보다 컸던 것이다(6개 절 조사 · 7계열 레인).
- 레인의 게이트 증거는 Git common dir 의 task runtime(`colab-harness/<checkout>/<task>/<run>/gate-summary.json`)에만 있다. advisor ② 는 그 자리를 몰라 「증거 없음」으로 판정했고(P0), 이후엔 오케스트레이터가 매번 먼저 열어 확인하고 「재실행 금지」를 프롬프트에 박아야 했다.
- 레인이 끝난 뒤 agent-browser 데몬 · chrome 34개 · `vite preview` 가 남는다. 이 데몬이 호스트 게이트 잠금을 쥐면 다음 회차가 exit 78 이 난다(메모리 `gate-lanes-cannot-run-in-parallel`). 매번 오케스트레이터가 손으로 죽였다.
- 단계마다 spec + advisor ① + lane + advisor ② + 오케스트레이터 대조 = 60~80만 토큰. 작은 단계(P3 규모)에도 같은 절차가 붙는다. 다만 advisor ① 이 이번 프로그램에서 가장 많은 결함을 잡았으므로(spec 5건 중 5건 approve-with-changes · 차단급 결함 3건) 「작다」의 기준 없이 생략하면 안 된다.

## 원한 결과 (proposed outcome)
- **① 지시 범위 재단 규칙**이 공통 규칙·역할·스킬 본문에 있다: researcher 는 2~3개 절/건, lane 은 계열(파일 면) 2~3개/건, 지시문에 「N번째 도구 호출 전에 산출 파일을 한 번 쓴다」를 수치로, advisor 에는 「도구 호출 8회 이하 뒤 판정」. Codex 역할(`.codex/agents/*.toml`)에도 같은 문장이 적용된다.
- **② 증거 경로 규격**: lane-worker·measurement-lane 의 최종 메시지 규격에 「runtime `gate-summary.json` 경로(git-common-dir 상대) + task·run id」가 필수 항목으로 있고, `lifecycle handoff --mode complete` 의 `COLAB_HANDOFF` JSON 이 그 경로를 담는다. advisor 역할 본문에 「게이트 증거는 그 경로에 있다 · 오케스트레이터가 확인했다고 적힌 것은 재실행하지 않는다」가 있다.
- **③ 레인 뒤처리 훅**: `SubagentStop`(lane-worker · measurement-lane · researcher) 에서 **그 워크트리를 cwd 로 가진** agent-browser 데몬 · chrome · `vite preview` 프로세스를 종료하고 종료 건수를 systemMessage 로 낸다. 비차단(exit 0). 다른 워크트리·세션의 브라우저는 건드리지 않는다. Codex 브리지(`.codex/hooks.json`)에도 같은 이벤트가 연결된다.
- **④ advisor ① 생략 기준**: 공통 스킬 §2 어드바이저 게이트 표에 「① 생략 가능 조건」이 수치로 있다 — spec 60행 이하 **그리고** 새 게이트·훅·마이그레이션·계약 변경 없음 **그리고** 제품 코드 변경 파일 3개 이하 **그리고** 시각 변경 0 증명 도구(캡처 대조)나 동등한 기계 판정이 적용됨. 넷 중 하나라도 깨지면 ① 을 건다. ② 는 항상.
- 위 넷이 실제로 동작함을 셀프테스트·실행으로 보인다(훅은 red 픽스처 · 규격은 `harness-contract-selftest` 류 기존 게이트로).

## 영향 범위
- 파일: `.agents/rules/colab-rules.md`(§1·§2 절 추가) · `.agents/roles/{lane-worker,measurement-lane,researcher,advisor}.md` · `.agents/skills/colab-v2-work/SKILL.md §1·§2` · `scripts/harness/hooks/lane-cleanup.sh`(신설) + `.claude/hooks/lane-cleanup.sh`(어댑터) · `.claude/settings.json`(SubagentStop 등록 1건) · `.codex/hooks.json`(브리지 1건) · `scripts/harness/hooks/lifecycle_contract.py`(handoff JSON 에 evidence 경로) · `docs/development/dual-agent.md`·`lifecycle-evidence.md`(규격 반영) · `.codex/agents/*.toml`(역할 문장 반영 여부 확인) · 기존 게이트 selftest 갱신.
- 서비스 · 스키마 · 계약: 없음. 제품 코드 변경 0.
- 계약 파괴 여부: 아니오.

## 제약
- 훅은 **비차단**(exit 0) · 대상은 「종료하는 서브에이전트의 워크트리를 cwd 로 가진 프로세스」로 한정(`/proc/<pid>/cwd` 대조) · 잡음 대신 요약 한 줄.
- `.claude/settings.json` 훅 정의 변경은 이 PC 의 `/hooks` 재신뢰가 필요하다(`docs/development/dual-agent.md`) — 레인은 등록까지 하고, 신뢰 확인은 사용자 몫으로 보고서에 적는다.
- 하네스 본문 수정은 원본(`.agents/**` · `scripts/harness/**`)에서 한 번만, Claude 어댑터(`.claude/**`)는 연결만(`dual-agent.md` 표).
- 규칙 문장은 수치로 적는다(「적당히」 금지). 생략 기준 ④ 는 보수적으로 — advisor ① 이 이번에 잡은 결함이 근거.
- 게이트 우회·축소 없음. `harness-eval` 은 면제 모드 그대로(승격 별건).

## 설계트리
- Q1 재단 규칙을 어디에 두나 → 공통 규칙 `.agents/rules/colab-rules.md` 에 절 1개(수치) + 역할 본문 각 1문장 + 스킬 §1 지시문 항목. 세 곳이 같은 수치를 가리킨다(복제 아님 · 규칙이 정본).
- Q2 증거 경로를 어디서 만드나 → `lifecycle handoff` 가 이미 run id 를 안다 → JSON 에 `evidence` 키 추가 · 역할 규격은 그 값을 옮겨 적으라고만.
- Q3 뒤처리 훅의 대상 판정 → cwd 기준. 이름 패턴만으로 죽이면 다른 세션의 브라우저를 잡는다. 대상 0건이면 「정리 0」을 낸다(조용히 통과 아님).
- Q4 ① 생략 조건 → 네 조건 AND. 「spec 60행」은 이번 P3 spec(≈70행 · 정정 뒤)보다 작다 — P3 도 ① 이 필요했던 단계이므로 그 아래로.

## 미해결 질문
- 없음.

## 범위 밖 (명시 제외)
- 턴 한도 자체 변경(`.claude/agents/*.md` maxTurns) · `harness-eval` 실행 모드 승격 · 디자인 구조 프로그램의 코드 · 커밋·push·PR 게시(사용자).

## 확인
- Ted 확인 문장(원문 그대로): "권고대로 해서 하네스고도화하고. 좋아. 작업은계속하자" (2026-09-24)
- 권고 원문: 이 대화의 하네스 평가 답변 「판정」 절 1~4.
- 재개봉 금지: 예.

## 참조
- 실측 근거: `dev-package/reports/design-system/20260924/p0/report.md`(advisor ② 증거 부재 판정) · 메모리 `subagent-turn-limits-truncate-results` · `gate-lanes-cannot-run-in-parallel` · `issue-pr-workflow-shape`
- 훅 스펙: `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` C절 · `docs/development/dual-agent.md`
- spec: `dev-package/prd/specs/S-HARNESS-LANE-HYGIENE-20260924.md`
