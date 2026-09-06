# 09. P-A 프로젝트 에이전트 4종 — 검증 결과와 다음 세션 수용 절차

스펙 = `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` B-3 · C · F · K.
산출 = `.claude/agents/{advisor,lane-worker,researcher,gate-runner}.md`.

## 1. 이 브랜치에서 끝낸 검증

| 항목 | 방법 | 결과 |
|---|---|---|
| frontmatter 파싱 | PyYAML `safe_load` 로 `---` 블록 4건 | **4/4 통과.** `name`·`description` 전건 존재 |
| 본문 길이 | 종료 `---` 이후 행수 | advisor 49 · gate-runner 41 · lane-worker 65 · researcher 82 (상한 120) |
| 훅 matcher 일치 | `.claude/settings.json` `matcher` 값 대조 | `SubagentStart` = `lane-worker` — 파일 `name` 과 **일치**. `SubagentStop:researcher`(H6)·`SubagentStop:lane-worker`(H7)는 **미등록**(P-E·P-J 몫) |
| 절대경로 부재 | `grep -c -E "/mnt/\|/home/"` | 4파일 전부 **0** |
| 필드명 근거 | 공식 서브에이전트 문서 필드표 재확인(2026-09-06) | `name`·`description`·`tools`·`disallowedTools`·`model`·`permissionMode`·`maxTurns`·`skills`·`mcpServers`·`hooks`·`memory`·`background`·`effort`·`isolation`·`color`·`initialPrompt`·`experimental` 실재. `model` 허용값에 `fable` 포함, `effort` = low/medium/high/xhigh/max, `isolation` = worktree |
| 미존재 스킬 허용 | 같은 문서 | 인용 — "If a listed skill is missing or disabled … Claude Code skips it and logs a warning to the debug log." ⇒ P-S 이전에도 `skills:` 4종 선기재 안전 |

## 2. 이 브랜치에서 **할 수 없는** 검증

에이전트 정의는 **`.claude/settings.json`·`agents/` 와 같은 층**이라 하위 폴더 스코프가 없다(K절 V1).
워크트리(`.claude/worktrees/…`)에서 연 세션은 프로젝트 루트가 이 워크트리이므로 스폰 자체는 뜨지만,
**J-0(세션 루트 = `30 CoLAB-v2`) 이동 + 병합 이후의 루트 세션**이 실제 운용 조건이다.
따라서 스폰 기동은 **다음 세션의 수용 절차**로 넘긴다.

## 3. 다음 세션 수용 절차 (P-A 합격선)

병합 후 **레포 루트에서 새 세션 1개**를 열고 아래를 순서대로 수행한다. 전건 통과해야 P-A 수용.

| # | 실행 | 기대 결과 |
|---|---|---|
| ㉮ | `/agents` (또는 에이전트 목록 표시) | `advisor` · `lane-worker` · `researcher` · `gate-runner` **4건이 프로젝트 스코프로 표시**. 글로벌 `advisor` 와 이름이 겹치면 **프로젝트가 우선**인지 표시로 확인 |
| ㉯ | `gate-runner` 스폰 — 지시 「`bash gates/run.sh exec-bit` 한 번만 돌리고 계 줄과 로그 경로만 회수」 | 계 줄(`── 계 :` 또는 단독 게이트 요약)과 종료코드가 회수됨. **재시도 없음 · 파일 변경 0건**(`git status --short` 로 확인) |
| ㉰ | `researcher` 스폰 — 지시 「`gates/README.md` 의 게이트 이름을 세어 `dev-package/sessions/` 아래 파일 1건으로 내고 경로만 회수」 | 파일 1건 + ≤15행 회수. 종료 시 `SubagentStop:researcher` 훅이 등록돼 있으면 미추적 산출물에서 **exit 2 + 경로 열거**(H6 등록 전이면 이 항목은 「훅 미등록」으로 기록) |
| ㉱ | `lane-worker` 스폰 — 지시 「`git rev-parse --show-toplevel` 과 `git branch --show-current` 만 보고」 | **워크트리 경로**(`.claude/worktrees/agent-…`)와 **자체 브랜치**가 회수됨 ⇒ `isolation: worktree` 실동작. 최종 메시지에 `WORKTREE=… BRANCH=…` 형식 포함 |
| ㉲ | ㉱ 스폰 시점의 오케스트레이터 출력 | `SubagentStart:lane-worker` 훅(H2 `worktree-setup.sh`)이 **뜬 흔적**이 보임. `researcher`·`advisor` 스폰에는 **미발동** |
| ㉳ | `advisor` 스폰 — 아무 계획 1건 검토 요청 | 회신에 `For:` 와 `Against:` 가 **둘 다** 존재. `Against:` 가 완화된 수정안으로 채워져 있으면 **불합격**(전역 정의에서 이관한 핵심 규칙) |
| ㉴ | `advisor` 에게 파일 수정 요청 | `Edit`·`Write` 도구 부재로 **거절**되거나 도구 목록에 없음 |

## 4. 남은 연결 작업 (다른 phase 몫)

- **P-C** — 글로벌 `~/.claude/agents/advisor.md` 삭제. 병합 전까지는 존치(이 브랜치는 글로벌 파일을 건드리지 않았다). 프로젝트본이 뜨는 것을 ㉮·㉳ 로 확인한 뒤 지운다.
- **P-E** — `SubagentStop:researcher`(H6 `uncommitted-artifacts.sh`) 등록. 미등록 상태에서는 researcher 본문 규칙만이 강제다.
- **P-J** — `gates/run.sh` 의 `gate-summary.json` 배출 + `SubagentStop:lane-worker`(H7) 등록. 그때까지 lane-worker 는 계수·로그 경로를 최종 메시지에 적는 것으로 갈음한다.
- **K 미검증 3** — 자율 블록을 넣은 `lane-worker` 가 advisor 게이트 ②를 우회하려는 경향. **레인 2회차까지 관찰**하고 결과를 이 폴더에 덧붙인다.
