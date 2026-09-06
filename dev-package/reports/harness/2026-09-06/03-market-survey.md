# CoLAB v2 — 엄격 파이프라인용 Claude Code 생태계 실측 조사 (2026-09-06)

조사 방식: WebSearch/WebFetch 실측. 별표 없는 수치는 인용 시점 그대로 기재.
검증 불가 항목은 `[미검증]` 으로 표시.

---

## 1. 확정된 사실 (Anthropic 공식 문서)

### 1.1 `effort` 는 서브에이전트 frontmatter 에서 설정 가능 — 확정

`https://code.claude.com/docs/en/sub-agents` 의 supported frontmatter fields 표, 인용:

> | `effort` | No | Effort level when this subagent is active. Overrides the session effort level. Default: inherits from session. Options: `low`, `medium`, `high`, `xhigh`, `max`; available levels depend on the model |

같은 표에서 함께 확인된, 이 설계에 직접 쓰이는 필드:

| 필드 | 의미 (문서 원문 요지) |
|---|---|
| `model` | `sonnet`/`opus`/`haiku`/`fable`/full id (`claude-opus-5`)/`inherit` |
| `effort` | 위 인용. 세션 effort 를 override |
| `isolation` | `worktree` — 임시 git worktree 에서 실행, 기본 default branch 에서 분기, 변경 없으면 자동 정리 |
| `skills` | 스킬을 **전문 그대로** 서브에이전트 컨텍스트에 프리로드 (description 아님) |
| `memory` | `user`/`project`/`local` — 세션 간 학습 |
| `maxTurns` | 턴 상한, 초과 시 partial 로 반환 후 resume 가능 |
| `permissionMode` | `default`/`acceptEdits`/`auto`/`dontAsk`/`bypassPermissions`/`plan`/`manual` |
| `hooks` | 해당 서브에이전트에만 걸리는 lifecycle hook |
| `disallowedTools` | 상속 목록에서 도구 제거 |

**플러그인 서브에이전트 제약 (동일 문서)**: `permissionMode`, `mcpServers`, `hooks` 는 **plugin subagent 에서 무시됨**.
`effort`/`model`/`isolation` 에 대한 무시 명시는 없음 → 플러그인 에이전트에서도 유효한 것으로 읽히나 `[미검증]`.
결론: **effort 를 확실히 통제하려면 에이전트를 프로젝트/유저 스코프 `.claude/agents/` 에 직접 정의**할 것.

### 1.2 훅 이벤트 · exit 2 차단 의미 (`/docs/en/hooks`)

차단 가능(exit 2)한 이벤트만 발췌:

| 이벤트 | exit 2 시 |
|---|---|
| `PreToolUse` | 도구 호출 차단 |
| `UserPromptSubmit` | 프롬프트 처리 차단 + 프롬프트 삭제 |
| `Stop` | Claude 가 멈추지 못하고 대화 계속 |
| `SubagentStop` | 서브에이전트 종료 차단 |
| `TaskCompleted` | 태스크 완료 표시 차단 |
| `PostToolBatch` | 다음 모델 호출 전 agentic loop 정지 |
| `ConfigChange` | 설정 변경 반영 차단 |
| `TeammateIdle` | teammate idle 진입 차단 |
| `PostToolUse` / `PostToolUseFailure` | **차단 불가** — stderr 를 Claude 에게 보여줄 뿐 |
| `PermissionRequest` | exit 2 무시 — `decision` 객체로 deny 해야 함 |

문서 인용: *"Exit 2 means a blocking error… even a JSON `permissionDecision` of `\"allow\"` can't override it."*
그리고 *"Claude Code treats exit code 1 as a non-blocking error and proceeds"* — 즉 **게이트는 반드시 exit 2**.

기타 확인된 이벤트: `SessionStart`, `Setup`, `SessionEnd`, `StopFailure`, `PreCompact`/`PostCompact`,
`InstructionsLoaded`, `SubagentStart`, `TaskCreated`, `WorktreeCreate`/`WorktreeRemove`, `FileChanged`, `CwdChanged`.

### 1.3 내장 기능 — 중복 구현 금지 목록

| 내장 | 위치/호출 | 커버 범위 |
|---|---|---|
| worktree 격리 | `claude --worktree <name>`, `EnterWorktree`, 에이전트 `isolation: worktree` | 파일 편집·bash cwd·git redirect 4중 차단을 **하네스가 강제**. 서브에이전트에도 동일 적용 |
| `worktree.baseRef` | settings `"fresh"`(기본, origin default branch) / `"head"` | 레인 분기 기준 |
| `.worktreeinclude` | 프로젝트 루트 | gitignore 된 `.env` 류를 새 워크트리로 자동 복사 — **현재 "워크트리마다 env 재구축" 문제의 정공법** |
| Dynamic Workflows | `ultracode` 키워드 / `/effort ultracode` / `.claude/workflows/*.js` | JS 스크립트가 오케스트레이터. `agent()`/`pipeline()`/`parallel()`/`phase()`. 재개 가능, 최대 16 동시·1000 에이전트·리스트 4096 |
| `/workflow-authoring` | 번들 스킬 (v2.1.248+) | 워크플로 스크립트 작성 레퍼런스 |
| `/deep-research` | 번들 워크플로 | 교차검증형 리서치 (adversarial verify 내장) |
| `/code-review` | 로컬, effort 인자 | 작업 중 빠른 리뷰 |
| `/code-review ultra` (ultrareview) | 클라우드 fleet | **모든 finding 을 독립 재현·검증**. 5~10분. Pro/Max 무료 3회, 이후 회당 약 $5~25 usage credits. 브랜치 500파일/8000라인 상한. `claude ultrareview` 서브커맨드로 CI 사용 가능(exit 0/1/130) |
| plan mode | `permissionMode: plan` | 계획 단계 쓰기 차단 |
| 백그라운드 태스크 / agent view | `/tasks` | 장기 실행 |

**주의 (비용 게이트)**: ultrareview 는 usage credits 과금. 매 PR 게이트로 걸면 회당 $5~25.
→ "머지 직전 1회" 로만 배치.

### 1.4 Fable 5.1 프롬프팅 가이드 — 기존 툴킷과 충돌하는 지점

`platform.claude.com/.../prompting-claude-fable-5` 에서 이 조사에 직결되는 항목:

- **"Refactor existing prompts and skills."** 원문: *"Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality. Review and consider removing older instructions if default performance is better."*
  → 2025~2026 초 작성된 커뮤니티 스킬(superpowers 계열 포함)은 **그대로 쓰면 품질 저하 가능**.
- **"Don't instruct Claude to reproduce its reasoning in the response."** 원문: reflection/show-your-thinking 지시는 `reasoning_extraction` refusal 을 유발해 Opus 4.8 로 fallback 상승.
  → "생각을 적어라 / 근거를 나열하라" 류 스킬 문안은 **감사 대상**.
- **자율 파이프라인 시스템 리마인더** (권장 원문 그대로 채택 권고):
  > "You are operating autonomously. The user is not watching in real time… For reversible actions that follow from the original request, proceed without asking… Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done, do that work now with tool calls."
- **진행 보고 근거 강제**: *"Before reporting progress, audit each claim against a tool result from this session."*
- **검증은 자기비평보다 별도 컨텍스트 verifier 가 우수**: *"Separate, fresh-context verifier subagents tend to outperform self-critique."*
  → advisor 게이트 + verifier 서브에이전트 구조가 공식 권고와 일치.
- **effort 기본값**: `high` 권장, 역량 민감 작업만 `xhigh`, 루틴은 `medium`/`low`.

---

## 2. 후보 목록 (16건)

인기 지표는 조사일(2026-09-06) 기준 인용 소스 표기값. 별 수치는 소스 간 편차가 커서 `[표기값]` 으로만 취급.

| # | 이름 | 출처 | 인기 지표 (본 소스) | 한 줄 | 로딩 방식 | 주입 비용 | 파이프라인 단계 | Fable 5.1 충돌 | 오케스트레이터 적합 | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **superpowers** (obra) | github.com/obra/superpowers | 282.1k stars, MIT | brainstorm→spec→plan→TDD→subagent dev→review→finalize 7단계 스킬군 | plugin (+SessionStart 훅이 bootstrap 주입) | **높음** — 14 스킬 + 상시 `using-superpowers` 게이트 | 전 단계 | 상 — 상시 주입·구형 처방적 문안·"모든 응답 전 스킬 호출" 강제 | 중 (스킬 자체는 적합, 게이트가 방해) | **부분 채택 (vendoring)** |
| 2 | superpowers-skills | github.com/obra/superpowers-skills | 745 stars, MIT, **2025-10-27 archived** | superpowers 스킬 본문 저장소 | plugin 이 `~/.config/superpowers/skills/` 로 clone | — | — | 아카이브 = 갱신 없음 | — | 참고용 (vendoring 소스) |
| 3 | **mattpocock-skills** | 공식 마켓플레이스 등재 (`mattpocock-skills`), github.com/mattpocock/skills | 252.6k stars, MIT | grill/to-spec/to-tickets/implement(TDD+review 게이트 내장)/tdd/code-review/diagnosing-bugs/domain-modeling | plugin (공식 마켓) | 중 — user-invoked 다수라 상시 주입 적음 | spec→ticket→구현→리뷰 | 낮음~중 `[미검증]` | 상 (사용자 호출형) | **채택 후보 (A/B 공통)** |
| 4 | git-guardrails-claude-code | mattpocock/skills `skills/misc/` | 상동 레포 | main/master push·protected branch 삭제·`gh pr merge` 차단 | skill(+훅 생성) | 소 | 병합 게이트 | 낮음 | 상 | **부분 채택 (훅으로 직접 구현)** |
| 5 | **claude-code-hooks** (karanb192) | github.com/karanb192/claude-code-hooks | 498 stars, 플러그인 마켓 | 20+ 훅: block-dangerous-commands, git-safety, protect-tests, protect-secrets, format-code, config-guard, pr-provenance-stamp | plugin marketplace | 소 (훅은 컨텍스트 주입 없음) | 전 단계 가드 | 없음 (훅=코드) | 상 | **부분 채택 (레시피 참조 후 자체 훅)** |
| 6 | **hookify** | 공식 마켓플레이스 (`./plugins/hookify`) | Anthropic 관리 | 대화 패턴·명시 요청에서 커스텀 훅 생성 | plugin | 소 | 훅 저작 | 없음 | 상 | **채택 (B), 설치 후 훅 생성하고 비활성 가능** |
| 7 | **claude-code-setup** | 공식 마켓플레이스 (`./plugins/claude-code-setup`) | Anthropic 관리 | 코드베이스 분석 후 훅/스킬/MCP 추천 | plugin | 소 | 셋업 1회 | 없음 | 상 | **1회용 채택 후 제거** |
| 8 | **claude-security** | 공식 마켓플레이스 (`./plugins/claude-security`) | Anthropic 관리 | 세션 내에서 자기 코드 취약점 스캔, effort 지정 | plugin | 소 | 리뷰 게이트 | 없음 | 상 | **채택 (B)** |
| 9 | security-guidance | 공식 마켓플레이스 | Anthropic | Claude diff 를 injection/XSS/SSRF/secret/IDOR/auth-bypass 관점 리뷰 | plugin | 소 | 리뷰 | 없음 | 상 | 채택 (B) |
| 10 | code-simplifier | 공식 마켓플레이스 (`./plugins/code-simplifier`) | Anthropic | 기능 보존 단순화 에이전트 (`/simplify` 내장과 중복) | plugin | 소 | 리뷰 | 없음 | 중 | **스킵** (내장 `/simplify` 로 대체) |
| 11 | commit-commands | 공식 마켓플레이스 | Anthropic | commit/push/PR 커맨드 | plugin | 소 | 병합 | 없음 | 상 | 채택 (B) |
| 12 | **spec-kit** (GitHub) | github/spec-kit | 80,000+ stars (2026 초 기준 인용) | `specify` CLI + 프롬프트/템플릿/슬래시커맨드, 다중 에이전트 지원 | CLI + 커맨드 파일 | 중 | spec→plan | 중 — 템플릿이 처방적 | 중 (레포에 spec 산출물 고정은 장점) | **부분 채택** — 템플릿만 참고 |
| 13 | **BMAD-METHOD** | BMAD-METHOD | 37,000+ stars | analyst/PM/architect/SM/dev/QA 가상 애자일 팀, PRD·아키텍처 샤딩 | 에이전트+템플릿 다수 | **매우 높음** | 전 단계 | 상 — 대량 처방적 페르소나 문안 | 하 — 자체 오케스트레이션이 사용자 구조와 충돌 | **스킵** |
| 14 | **OpenSpec** | Fission-AI/OpenSpec | 66.9k stars | proposal→specs→design→tasks→impl→archive, 경량 | CLI + 커맨드 | 중 | spec | 낮음 | 중 | **스킵** — `openspec validate` 는 구조만 검사, `/opsx:verify` 는 **명시적 non-blocking**. "건널 수 없는 게이트" 요건 미충족 |
| 15 | claude-flow | claude-flow | 59.4k stars | 코드 우선 멀티에이전트 오케스트레이션 레이어 | 외부 프레임워크 | 높음 | 오케스트레이션 | 상 | 하 — Workflow 내장과 정면 중복 | **스킵** |
| 16 | SuperClaude_Framework | SuperClaude | 23k+ stars | 슬래시커맨드·페르소나·행동 모드 설정 프레임워크 | CLAUDE.md/커맨드 대량 | 높음 | 전 단계 | 상 — 페르소나 상시 주입 | 하 | **스킵** |
| 17 | claude-code-templates | davila7 등 | 29,516 stars (2026-04-21 인용) | 템플릿/스타터 모음 | 파일 복사 | 가변 | 셋업 | 중 | 중 | 스킵 (샘플 참고만) |
| 18 | CCPM | ccpm | 7.6k stars | GitHub Issues + worktree 로 병렬 에이전트 PM | 커맨드 세트 | 중 | 계획·병렬 | 중 | 중 — worktree 내장과 중복 | **스킵** |
| 19 | agent-os (Brian Casel) | agent-os | v3 (2026-01) | 표준 우선. **v3 에서 영속 spec 작성을 버리고 Claude Code Plan Mode 를 쓰는 쪽으로 선회** | 표준 문서 | 소 | 계획 | 낮음 | 상 (사상만) | **스킵 (사상만 채택)** — "프론티어 모델은 스캐폴딩 불필요" 는 Fable 가이드와 같은 결론 |
| 20 | GSD / GoopSpec | open-gsd, GoopSpec | 신생 | Discuss→Plan→Execute→Audit→Confirm 5단계 | plugin | 중 | 전 단계 | `[미검증]` | 중 | **스킵** (성숙도 부족) |

### 2.1 이미 설치된 것 중 재판정이 필요한 항목

| 항목 | 판정 | 이유 |
|---|---|---|
| superpowers 6.3.0 (플러그인 전체) | **비활성 + vendoring** | 3장 참조 |
| claude-mem 13.0.0 | 유지하되 스킬 수 축소 검토 | 11개 스킬(`do`/`make-plan`/`babysit`/`pathfinder`/`learn-codebase` 등)이 항상 목록에 오름. 메모리 자체는 유용 |
| ralph-loop | **스킵 후보** | 무한 루프형. Stop 훅 + Workflow "keep fixing until check passes" 패턴이 상위 호환 |
| understand-anything 2.7.7 | **비활성 권고** | 서브에이전트 9종 + 스킬 8종을 상시 목록에 추가 = 현재 26 에이전트/47 스킬 팽창의 최대 단일 기여자 |
| codex (openai) | 유지 | 2nd-opinion 리뷰축으로 유효 |
| feature-dev / code-review / frontend-design / context7 / playwright / LSP 2종 | 유지 | 공식 관리, 주입 작음 |
| skill-creator, claude-md-management, eli5 | 유지 (저비용) | |

---

## 3. superpowers 정밀 평가

**결론: 체인 설계는 여전히 최고 수준이나, 플러그인 통째 활성은 Fable 5.1 에 역효과. 스킬 vendoring 이 정답.**

근거 3가지:

1. **상시 게이트 실재.** 레포 확인 결과 *"runs the plugin's session-start hook, so Superpowers is active from the first message."*
   `using-superpowers` 스킬 설명은 *"requiring skill invocation before ANY response including clarifying questions"* — 오케스트레이터 메인 세션에
   매 턴 스킬 호출을 강제하므로, "메인은 논의·위임만" 원칙과 정면 충돌하고 토큰도 낭비.
2. **라이선스상 vendoring 가능.** superpowers / superpowers-skills 모두 **MIT**. `.claude/skills/` 로 복사 후 `SKILL.md` 문안 수정 가능.
   단 superpowers-skills 는 **2025-10-27 아카이브** → 상류 갱신 없음. 복사 시점 스냅샷으로 관리하면 됨.
3. **문안이 구형.** Fable 가이드가 명시적으로 경고한 "too prescriptive… can degrade output quality" 범주.
   vendoring 하면서 (a) 사고 재현 지시 제거, (b) 나열형 열거 축약, (c) 진행 보고 근거 강제 문구 삽입이 필요.

**vendoring 대상 5종 (나머지는 내장/훅으로 대체):**

| 스킬 | 대체 불가 이유 |
|---|---|
| `writing-plans` | 계획 문서 포맷 = 실행 세션 간 인계 계약 |
| `executing-plans` | 계획→실행 시 체크포인트 규약 |
| `test-driven-development` | red-green-refactor 순서 강제 (훅으로는 순서를 못 잡음) |
| `verification-before-completion` | "증거 먼저" 규약. Fable 가이드의 progress-audit 지시와 합성 |
| `receiving-code-review` | 리뷰 피드백을 맹종/형식적 수용하지 않게 하는 규약 |

**대체되는 것들:**
`using-git-worktrees` → 내장 worktree + `isolation: worktree`.
`dispatching-parallel-agents`/`subagent-driven-development` → Workflow tool.
`requesting-code-review` → `/code-review`, `/code-review ultra`, advisor 게이트.
`brainstorming` → plan mode + advisor.
`using-superpowers` → **버림** (게이트 자체가 문제).
`systematic-debugging` → 유지해도 되지만 저빈도, 필요 시 vendoring.

---

## 4. 훅 레시피 (엄격 게이트)

모두 `settings.json` 의 `hooks` 에 등록. **차단은 exit 2 만 유효**.

| # | 이벤트 | 게이트 | 구현 요지 | 출처 |
|---|---|---|---|---|
| H1 | `PreToolUse` matcher `Bash` | main/master 직접 push·force push·`gh pr merge` 차단 | stdin JSON 의 `.tool_input.command` 를 jq 로 읽고 현재 브랜치 확인, 위반 시 stderr + exit 2 | docs/en/hooks 예제; mattpocock git-guardrails; karanb192 `git-safety` |
| H2 | `PreToolUse` matcher `Edit\|Write` | Alembic 기존 마이그레이션 파일 수정 차단 (신규만 허용) | 경로가 `migrations/versions/` 이고 git 에 이미 추적 중이면 exit 2 | 자체 (CoLAB 특화) |
| H3 | `PreToolUse` matcher `Edit\|Write` | 테스트 파일 삭제/무력화 차단 | karanb192 `protect-tests` 패턴 | karanb192/claude-code-hooks |
| H4 | `PostToolUse` matcher `Edit\|Write` | 저장 즉시 포맷/린트 (ruff+prettier/eslint) | **차단 불가 이벤트** — stderr 로 Claude 에게 결과 전달만 | docs 표(PostToolUse: No); karanb192 `format-code` |
| H5 | `PostToolBatch` | 배치 후 타입체크 실패 시 루프 정지 | 차단 가능한 유일한 "편집 후" 이벤트. `tsc --noEmit` / pyright | docs/en/hooks exit-2 표 |
| H6 | `Stop` | 테스트 게이트 미통과 시 종료 차단 | 게이트 스크립트 실행 → 실패 시 출력 stderr + exit 2. **`stop_hook_active` 가 true 면 반드시 exit 0** (무한 루프 방지) | docs/en/hooks; claudefa.st stop-hook 문서 |
| H7 | `SubagentStop` | 구현 레인 서브에이전트가 자기 레인 테스트 없이 종료하려 하면 차단 | agent_type 이 `implementer-*` 일 때만 검사 | docs (SubagentStop: Yes) |
| H8 | `TaskCompleted` | 완료 표시 전 verifier 산출물(증거 파일) 존재 확인 | 없으면 exit 2 | docs (TaskCompleted: Yes) |
| H9 | `SessionStart` | 워크트리에서 시작했는데 `.venv`/`node_modules` 없으면 경고 출력 | 차단 대신 안내 | 자체 (MEMORY: worktree gate env setup) |
| H10 | `WorktreeCreate` 대신 `.worktreeinclude` | `.env`, `~/.colab-v2-test.env` 사본 자동 반입 | 파일 한 줄씩 | docs/en/worktrees |
| H11 | `UserPromptSubmit` | (선택) 기획 확정 사항 재개봉 시도 감지 시 차단 | 위험 — 오탐 시 프롬프트가 **삭제**됨. 권장하지 않음 | docs (프롬프트 erase 명시) |

**중복 금지 확인**: worktree 강제는 훅 불필요(하네스가 4중 차단), 병렬 팬아웃 훅 불필요(Workflow),
"테스트 통과까지 반복"은 Workflow 의 keep-fixing 패턴으로도 가능(단 세션 종료 게이트는 H6 가 필요).

---

## 5. 제안 A — 엄격 파이프라인, 최소 주입

목표: **모든 게이트를 유지하되 세션 시작 주입을 현재의 절반 이하로.**

### 5.1 플러그인

| 활성 | 비활성/제거 |
|---|---|
| context7, typescript-lsp, pyright-lsp, code-review, claude-md-management | **superpowers**(vendoring 으로 대체), **understand-anything**(에이전트 9+스킬 8), **ralph-loop**, feature-dev, frontend-design, playwright(필요 시 on-demand), skill-creator, codex, eli5, claude-mem(또는 mem-search 만) |

### 5.2 vendoring 스킬 (`.claude/skills/`) — 5개

`writing-plans`, `executing-plans`, `test-driven-development`, `verification-before-completion`, `receiving-code-review`
(superpowers MIT 사본. Fable 5.1 용으로 문안 축약 + 사고 재현 지시 제거 + progress-audit 문구 삽입)

### 5.3 에이전트 (`.claude/agents/`) — 5개

| name | model | effort | 역할 |
|---|---|---|---|
| `advisor` | fable | `xhigh` | 기존 유지. 3게이트 자문, 실행 금지 |
| `spec-writer` | fable | `high` | 기획 문서 → 실행 가능 spec + 수용 기준 |
| `implementer` | fable | `high` | `isolation: worktree`, `skills: [test-driven-development]`, 레인 1건 구현 |
| `verifier` | fable | `high` | **fresh context**. spec 대비 산출물 검증, 증거 파일 산출. 편집 도구 미부여 |
| `gatekeeper` | sonnet | `medium` | 전수 게이트 실행·결과 요약만. 판단 없음 |

### 5.4 훅

H1, H2, H3, H4, H6, H8 + `.worktreeinclude`. (6 훅)

### 5.5 단계별 게이트 표

| 단계 | 도구 | 진행을 막는 것 |
|---|---|---|
| 1 spec | plan mode + `spec-writer` | advisor 가 수용 기준 미비 판정 시 중단 |
| 2 plan | vendored `writing-plans` | 계획 파일 미존재 시 3단계 진입 금지 (H8) |
| 3 구현 | `implementer` (`isolation: worktree`) | 하네스가 main checkout 편집 차단 |
| 4 테스트 | `Stop` 훅 H6 | 게이트 스크립트 미통과 시 세션 종료 불가 |
| 5 리뷰 | `/code-review` (로컬) | 미해결 finding 존재 시 advisor 가 6단계 차단 |
| 6 검증 | `verifier` (fresh context) | 증거 파일 없으면 `TaskCompleted` 차단 (H8) |
| 7 병합 | H1 PreToolUse | main 직접 push / force push 차단, PR 경유만 |

### 5.6 주입 추정

| | 현재 | 안 A |
|---|---|---|
| 에이전트 | 26 | **5 + 내장(Explore/Plan/general-purpose)** ≈ 8 |
| 스킬 | 47 | **vendored 5 + 내장 번들 + context7/lsp/code-review 계열** ≈ 15~18 |

---

## 6. 제안 B — 엄격 파이프라인, 풀 툴킷

A 에 아래를 더한다. Fable 5.1 호환은 유지(상시 주입형 프레임워크는 여전히 배제).

### 6.1 추가 플러그인

| 플러그인 | 이유 |
|---|---|
| `mattpocock-skills` (공식 마켓) | `to-spec`/`to-tickets`/`implement`(TDD+review 게이트 내장)/`code-review`(standards+spec 이중축)/`domain-modeling`. 대부분 user-invoked 라 상시 주입 낮음 |
| `claude-security` | 세션 내 취약점 스캔, effort 지정 가능 |
| `security-guidance` | diff 단위 injection/XSS/SSRF/secret 검사 |
| `hookify` | 훅 저작 후 비활성 가능 |
| `commit-commands` | 커밋/PR 정형화 |
| `claude-code-setup` | 1회 실행 후 제거 |
| `karanb192/claude-code-hooks` | 훅 레시피를 플러그인으로 받아 골라 씀 (컨텍스트 주입 없음) |

### 6.2 추가 에이전트

| name | model | effort | 역할 |
|---|---|---|---|
| `spec-auditor` | fable | `high` | 기획 문서 ↔ 구현 산출물 1:1 대조 (기존 intent-verifier 패턴) |
| `migration-reviewer` | fable | `high` | Alembic revision 체인·down_revision·데이터 손실 전용 리뷰 |
| `frontend-verifier` | sonnet | `medium` | playwright 로 화면 렌더·콘솔 에러 확인 |
| `second-opinion` | (codex) | — | 독립 구현/진단 2차 의견 |

### 6.3 추가 훅

H5(`PostToolBatch` 타입체크), H7(`SubagentStop`), H9(`SessionStart` 환경 점검).

### 6.4 추가 게이트

| 단계 | 도구 | 차단 조건 |
|---|---|---|
| 3.5 마이그레이션 | `migration-reviewer` | revision 체인 불일치·비가역 DDL 미표기 |
| 5.5 보안 | `claude-security` / `security-guidance` | High 이상 finding 미해결 |
| 6.5 프리머지 | `/code-review ultra` (**머지 직전 1회만**) | 재현·검증된 버그 잔존 시 병합 금지 |
| 6.6 워크플로 | 저장된 `.claude/workflows/colab-gate.js` | 전수 게이트를 `pipeline()` 로 서비스별 분할 후 실패 서비스만 재실행 |

### 6.5 주입 추정

| | 현재 | 안 B |
|---|---|---|
| 에이전트 | 26 | **9 + 내장** ≈ 12 |
| 스킬 | 47 | **vendored 5 + mattpocock ~16 + 보안 2 + 내장** ≈ 28~30 |

---

## 7. 권고

1. **안 A 로 시작**하고, spec 단계가 병목이면 `mattpocock-skills` 만 추가해 A+ 로 올린다 (B 전체는 과다).
2. **superpowers 는 플러그인 비활성 + 5스킬 vendoring**. MIT 라 합법, 아카이브라 상류 추적 부담 없음.
3. **understand-anything 비활성**이 주입 감축 최대 효과 (에이전트 9 + 스킬 8).
4. **effort 는 에이전트 파일에 직접 기재** — 플러그인 에이전트에서의 유효성은 문서에 명시 없음(`[미검증]`).
5. `.worktreeinclude` 도입으로 "워크트리마다 env 재구축" 반복 비용 제거.
6. ultrareview 는 **비용 게이트** — 창(배포 회차)당 1회로 제한.
7. 모든 vendored 스킬·CLAUDE.md 에서 **"사고 과정을 서술하라" 류 문구 제거** (refusal/fallback 유발).

---

## 8. 미검증 항목

- 플러그인 서브에이전트에서 `effort`/`isolation` 이 존중되는지 (문서는 `permissionMode`/`mcpServers`/`hooks` 만 무시 대상으로 명시).
- `mattpocock-skills` 개별 스킬의 세션 주입 바이트 (SKILL.md 크기 미측정).
- superpowers 6.3.0(설치본)이 상류 282k-star 레포와 동일 스킬 세트인지.
- GSD/GoopSpec 의 Fable 5.1 호환성.
- 각 star 수치는 소스가 서로 다른 날짜를 인용하며 편차가 큼 — 상대 순위 근거로만 사용.
