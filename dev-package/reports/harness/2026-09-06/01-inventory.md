# Claude Code 하니스 구성 인벤토리 (2026-09-06)

## 1. 글로벌 지침 파일

| 파일 | 바이트 | 줄 |
|---|---|---|
| ~/.claude/CLAUDE.md | 5307 | 50 |
| ~/.claude/references/selfcontained-html.md | 4626 | - |
| ~/.claude/settings.json | 1849 | - |
| ~/.claude/settings.local.json | 없음 (파일 부재) | - |

CLAUDE.md 섹션(`grep '^#'`): 위임·세션 원칙(1) / 서브에이전트 대화 언어(20) / graphify(29) / 산출물 HTML 규격(39) / travel-proposal(44) / explain-visually(48).

**hooks**: `~/.claude/settings*.json`에는 `"hooks"` 키 없음(글로벌 훅 미설정). 프로젝트 쪽은 `00 CoLAB-PoC`, `01 CoLAB-Plan`, `10 CoLAB-Launch/colab-contracts` 및 그 워크트리들의 `.claude/settings.json`에 훅 다수(각 3~7개 이벤트 블록) — CoLAB-PoC 계열 레거시 레포. **정작 30 CoLAB-v2(현행)에는 `.claude/settings*.json` 자체가 없음.**

keybindings.json / statusline* : 존재하지 않음.

settings.json 요지: `model: claude-fable-5-1[1m]`, `effortLevel: low`(전역) / `fable-5-1: medium`, `enabledPlugins` 14개 true(4개 false: code-simplifier, security-guidance, pr-review-toolkit — 이 3개는 표에서 제외), `autoCompactEnabled: false`.

## 2. 글로벌 에이전트 (~/.claude/agents/*.md, 13개)

| 이름 | model | bytes | lines | 도메인 |
|---|---|---|---|---|
| advisor.md | fable | 3863 | 60 | 조율/게이트 — CoLAB 관련 |
| ai-tell-detector.md | opus | 5589 | 113 | humanize-korean 계열 |
| content-fidelity-auditor.md | opus | 5364 | 109 | humanize-korean 계열 |
| humanize-monolith.md | opus | 8515 | 144 | humanize-korean 계열 |
| humanize-web-architect.md | opus | 5987 | 113 | humanize-korean 계열 |
| korean-ai-tell-taxonomist.md | opus | 3994 | 66 | humanize-korean 계열 |
| korean-style-rewriter.md | opus | 5636 | 103 | humanize-korean 계열 |
| korean-translation-scholar.md | opus | 6194 | 118 | humanize-korean 계열 |
| naturalness-reviewer.md | opus | 5586 | 122 | humanize-korean 계열 |
| post-editese-metric-engineer.md | opus | 6172 | 138 | humanize-korean 계열 |
| quick-rules-integrator.md | opus | 6367 | 136 | humanize-korean 계열 |
| taxonomy-gap-analyzer.md | opus | 4358 | 86 | humanize-korean 계열 |
| translationese-research-distiller.md | 4946 | 84 | 84 | humanize-korean 계열 |

**핵심 발견: 13개 글로벌 에이전트 중 12개가 humanize-korean(윤문) 도메인 전용이고 CoLAB/코딩과 무관. CoLAB 관련은 advisor 하나뿐.** 모두 `tools:` frontmatter 필드 없음(전체 도구 상속 추정). 전부 description이 200~1100자로 길다(§8 트리거 매칭 비용).

## 3. 글로벌 스킬 (~/.claude/skills/*/)

| 스킬 | SKILL.md bytes/lines | desc 길이 | 참조파일 수 | 디렉터리 합계 |
|---|---|---|---|---|
| apple-design | 22814 / 284 | 446 | 0 | 22814 |
| archify | 13857 / 121 | 666 | 179 | 7,804,125 (7.8MB) |
| explain-visually | 7556 / 92 | 488 | 0 | 7556 |
| graphify | 47960 / 1029 | 241 | 1 | 47966 |
| humanize-korean | 11456 / 196 | 1138 | 11 | 203136 |
| humanize-redo | 2013 / 32 | 266 | 0 | 2013 |
| humanize | 1648 / 35 | 221 | 0 | 1648 |
| travel-proposal | 4939 / 43 | 475 | 3 | 15055 |

CoLAB v2 개발과 직접 관련된 글로벌 스킬은 **0개**. archify(아키텍처 다이어그램)는 조건부 활용 가능. 나머지(apple-design, humanize-korean/redo/humanize, travel-proposal, explain-visually)는 코딩과 무관한 도메인. graphify는 명시 호출 전용으로 CLAUDE.md가 이미 억제 중.

`colab-v2-work` 스킬은 **글로벌이 아니라 레포 내부**(`30 CoLAB-v2/.claude/skills/colab-v2-work/SKILL.md`, 15785 bytes / 169 lines)에 있음. §5 참조.

## 4. 플러그인 (settings.json enabledPlugins=true, 14개)

플러그인 캐시 경로: `~/.claude/plugins/cache/{marketplace}/{plugin}/{version}`. 마켓플레이스 5개: claude-plugins-official, thedotmack(claude-mem), openai-codex(codex), understand-anything, claude-community(eli5).

| 플러그인 | agents | skills | commands | hook 참조파일 | 총 용량 |
|---|---|---|---|---|---|
| superpowers (6.3.0) | 0 | 14 | 0 | 6 | 1.71MB |
| feature-dev | 3 | 0 | 1 | 0 | 36KB |
| context7 | 0 | 0 | 0 | 0 | 2.9KB |
| frontend-design | 0 | 1 | 0 | 0 | 32KB |
| code-review | 0 | 0 | 1 | 0 | 27KB |
| skill-creator | 0 | 1 | 0 | 0 | 237KB |
| playwright | 0 | 0 | 0 | 0 | 0.7KB (MCP 서버 wrapper) |
| ralph-loop | 0 | 0 | 3 | 3 | 38KB |
| claude-md-management | 0 | 1 | 1 | 0 | 1.10MB |
| typescript-lsp | 0 | 0 | 0 | 0 | 12KB |
| pyright-lsp | 0 | 0 | 0 | 0 | 12KB |
| claude-mem (13.0.0) | 0 | 11 | 0 | 3 (hooks.json 등) | 7.77MB(대부분 bun 런타임 번들) |
| codex (1.0.4) | 1 | 3 | 7 | 4 | 208KB |
| understand-anything (2.7.7) | 9 | 8 | 0 | 27 | **442MB**(대부분 `node_modules` — 프롬프트 주입과 무관, 디스크만 차지) |
| eli5 (1.0.0) | 0 | 1 | 0 | 0 | 1.2KB |

**합계**: 플러그인이 시스템에 주입하는 agent 13개(feature-dev 3 + codex 1 + understand-anything 9), skill 39개(superpowers 14 + frontend-design 1 + skill-creator 1 + claude-md-management 1 + claude-mem 11 + codex 3 + understand-anything 8 + eli5 1). 여기에 글로벌 agents 13개 + skills 8개가 더해짐 → **에이전트 총 26개, 스킬 총 47개**가 매 세션 후보 목록(현재 대화 상단 시스템 리마인더에 실제로 열거된 스킬 수와 대략 일치)에 오름.

**superpowers**: `using-superpowers/SKILL.md` 3108 bytes / 63 lines — 이것이 매 세션 시작 시 주입되는 "스킬 사용법" 본문(설명대로 "Use when starting any conversation"). references 서브디렉터리 별도 존재.

**claude-mem**: `hooks/hooks.json`에 `Setup`(버전체크) · `SessionStart`(matcher `startup|clear|compact`, worker-service 기동 + `hook claude-code context` 컨텍스트 주입, `suppressOutput:true`) · `UserPromptSubmit`(매 프롬프트마다 `session-init` 훅 실행) · `PostToolUse`(매 도구 호출마다 `observation` 훅 실행) 4종 이벤트가 걸려 있음. 즉 **세션 시작 1회 컨텍스트 주입 + 매 프롬프트/매 도구호출마다 별도 프로세스(node/bun) 실행** — 레이턴시·토큰 오버헤드가 세션 전체에 걸쳐 상시 발생하는 구조.

**understand-anything**: agent 9개·skill 8개로 플러그인 중 최대 규모. 442MB는 거의 전부 `node_modules`(런타임 의존성, 프롬프트에는 안 들어감).

**eli5**: 매우 가벼움(1.2KB), agent 없음, 훅 없음.

## 5. CoLAB v2 프로젝트 레벨 구성

레포: `/mnt/f/00_Project/00 CoLAB/30 CoLAB-v2` (git 저장소, 정상).

| 항목 | 내용 |
|---|---|
| CLAUDE.md | 17852 bytes / 210 lines, 최상위 1개만 존재(하위 디렉터리에 추가 CLAUDE.md 없음) |
| AGENTS.md | 없음 |
| HANDOFF/PLAN (최상위) | 최상위엔 없음 — `planning/`, `dev-package/`(README에서 `03-HANDOFF.md` 참조 확인) 하위에 존재 |
| .claude/ | `skills/colab-v2-work/SKILL.md` 단 하나. agents·commands·settings·hooks 전무 |
| .claude/worktrees/ | 4개 워크트리 디렉터리(40 COLAB-기획, agent-a3276c.., agent-a992b5.., agent-acbe67..) — 병렬 레인 잔재로 추정, 정리 여부 확인 필요 |

CLAUDE.md 섹션 헤딩(`grep '^#'`): 0.이 레포가 무엇인가 / 1.세션 시작 순서 / 2.도메인(10개,3레이어) / 3.불변 규칙 / AI 응답 규격 / 4.작업 규약(순서 불변, 경계, 게이트 정책) / 5.절대 하지 않는 것 / 6.세션 종료 규약(예외 없음) / 7.커밋 / 8.자주 쓰는 것 / 업로드(S3) / 배포(깨뜨리면 안 되는 것/고치기 전 확인/확장).

**colab-v2-work 스킬**: `.claude/skills/colab-v2-work/SKILL.md`, 15785 bytes / 169 lines. `~/.claude/CLAUDE.md:35`이 "CoLAB v2 → `colab-v2-work`"로 참조하는 대상이 바로 이것 — 글로벌이 아니라 레포 로컬 스킬. 글로벌 CLAUDE.md에서 이 이름을 언급하는 곳은 1곳뿐(graphify 억제 문맥).

docs/ 최상위 문서(용량 미측정, 존재만 확인): DEPLOY.md, DEPLOY_HANDOVER.md, DEPLOY_NOTES.md, DEPLOY-evidence-{doctor,viz,worker}.txt, planning/README.md.

## 6. 메모리

`~/.claude/projects/-mnt-f-00-Project-00-CoLAB/memory/`: 파일 33개, 총 64,277 bytes(~63KB), `MEMORY.md` 32줄(색인 파일, 실제 항목은 개별 .md 32개에 분산).

CoLAB 관련 프로젝트 디렉터리(`~/.claude/projects` 중 `colab` 매칭, 총 17개) — 다수가 워크트리별로 별도 프로젝트 디렉터리를 가짐(예: `30-CoLAB-v2--claude-worktrees-agent-a463e7e75499856cd` 등 5개 이상). 레거시 CoLAB-PoC/CoLAB-Launch 계열도 여전히 잔존.

## 7. 세션 부트스트랩 로드 추정

| 구성요소 | 바이트(대략) | 비고 |
|---|---|---|
| 글로벌 CLAUDE.md | 5,307 | 매 세션 |
| 프로젝트 CLAUDE.md(30 CoLAB-v2) | 17,852 | 해당 레포에서 작업 시 |
| MEMORY.md (색인) | 32줄, 수 KB | 실제 32개 세부 파일은 필요시 로드 추정 |
| using-superpowers SKILL.md | 3,108 | "대화 시작 시 항상 사용" 트리거 — 사실상 상시 주입 |
| claude-mem SessionStart 컨텍스트 주입 | 가변(런타임 쿼리 결과, 정적 크기 측정 불가 — 별도 DB/코퍼스 질의) | `suppressOutput:true`지만 컨텍스트 자체는 주입됨 |
| 전체 스킬 description 합 (글로벌 8 + 플러그인 39 = 47개) | 대략 47개 × 평균 300~600자 ≈ 15,000~28,000자 | 목록 형태로 시스템 리마인더에 상시 노출(본 대화 상단 목록 실측 47개) |
| 전체 에이전트 description 합 (글로벌 13 + 플러그인 13 = 26개) | 대략 26개 × 평균 150~1,100자(특히 humanize 계열 장문) ≈ 10,000~15,000자 | Agent 도구 사용 시 후보 목록으로 노출 |

정확한 바이트 합산은 스킬/에이전트 description을 개별 추출해야 하나(런타임에서만 조합), 위 추정만으로도 **"스킬 47개 + 에이전트 26개"라는 후보 목록 자체가 매 세션 고정 오버헤드**라는 점이 핵심 — 그중 CoLAB v2 개발에 실질 관련된 것은 advisor(agent) + colab-v2-work(레포 로컬 skill) + 범용 도구성 플러그인(superpowers/feature-dev/code-review/context7/playwright/typescript-lsp/pyright-lsp 등) 정도이고, humanize-korean 계열 12 agents + apple-design/travel-proposal/explain-visually/humanize* skills는 이 프로젝트에서 상시 무관.

## 8. 안티패턴 스캔 (Fable 5.1 프롬프팅 가이드 기준)

대상: `~/.claude/CLAUDE.md`, `~/.claude/agents/*`, `~/.claude/skills/*`, `30 CoLAB-v2/CLAUDE.md`, `30 CoLAB-v2/.claude/skills/colab-v2-work/SKILL.md`. (레포 `.claude/worktrees/` 하위는 병렬 레인 산출물이라 스캔 범위에서 제외 — 포함 시 "조용히"라는 도메인 용어가 코드 주석에 수백 건 나와 노이즈만 커짐.)

| 카테고리 | 결과 |
|---|---|
| a. 서술 억제(hold findings/조용히/최종에만) | **없음** (레포 코드의 "조용히"는 "silent failure 금지"라는 제품 도메인 용어이지 하니스 지시 아님) |
| b. 안티포맷팅(no bullet/볼드 금지 등) | **없음** |
| c. 승인 요청 유도(ask before/확인 후/Shall I) | **없음** |
| d. 전체 재작성 유도(rewrite the file/전체 재작성) | **없음** |
| e. 모델 핀(opus/sonnet/haiku/fable) | CLAUDE.md/colab-v2-work SKILL.md 본문엔 없음. **모델 핀은 agents frontmatter에만 존재**: 12개 opus + advisor 1개 fable (§2 표 참조) |
| f. effort/ultrathink 언급 | **없음**(대상 3파일 기준) |
| g. compact/요약 지침 | CoLAB CLAUDE.md:28 "진행 상황 요약의 출발점"(HANDOFF 문서 설명, 지시 아님), CLAUDE.md:171 "변경 요약"(문서명), colab-v2-work SKILL.md:100 "요약줄이 건너뛴 건수를 숨기고 통과만 말하는가"(오히려 **은폐 금지** 체크리스트 — 안티패턴이 아니라 그 반대) |
| h. 서브에이전트 대기 지시(wait for/대기) | **없음** |
| i. 테스트 작성 강제(write tests/테스트 작성) | **없음** |

**결론**: 3개 핵심 파일(글로벌 CLAUDE.md, 프로젝트 CLAUDE.md, colab-v2-work 스킬) 자체에는 Fable 5.1 안티패턴이 사실상 없음. 유일한 실질 이슈는 **에이전트 12/13이 opus로 하드핀**되어 있다는 점(§2) — 재설계 시 판단·리뷰형만 opus 유지, 기계적 서브태스크는 sonnet/haiku로 낮추라는 사용자 CLAUDE.md 정책(모델은 작업 난이도에 맞춘다)과 충돌 여지.

## 9. 제품 코드 내 Anthropic API 사용

`grep -rlE 'anthropic|claude-' --include=*.py --include=*.ts --include=*.tsx`를 `node_modules`/`.venv`/`.claude` 제외하고 레포 전체(30 CoLAB-v2)에서 실행 → **매칭 파일 0개**. 제품 코드 자체에는 Anthropic/Claude API 직접 호출이나 별도 프롬프팅 계층이 없음(하니스 설정과 제품 코드가 완전히 분리되어 있음을 확인).
