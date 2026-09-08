# Vendored 스킬 10종 — 출처·라이선스·개조 목록

이행 = 하네스 재설계 **P-S**(스펙 `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` B-2·F·H 7행).
원칙 = **개조 목록에 적힌 것 외에는 원문 그대로.** 저자가 시험한 문안을 보존한다.
전 8종 **명시 호출 전용 · 훅 0개**. 상류 갱신 시 이 파일의 「내려받은 날」을 갱신하고 diff 를 다시 뜬다.

## 출처

| 출처 | URL | 라이선스 | 판본 | 내려받은 날 |
|---|---|---|---|---|
| superpowers | `https://github.com/obra/superpowers` | MIT (Copyright (c) 2025 Jesse Vincent) | 플러그인 캐시 **6.3.0** (`~/.claude/plugins/cache/claude-plugins-official/superpowers/6.3.0/skills/`) | 2026-09-06 (설치본 파일 스탬프 2026-08-17) |
| mattpocock/skills | `https://github.com/mattpocock/skills` | MIT (Copyright (c) 2026 Matt Pocock) | `main` tarball · `package.json` version **1.2.3** | **2026-09-06** (`refs/heads/main.tar.gz`) |
| emilkowalski/skills | `https://github.com/emilkowalski/skills` | MIT (Copyright (c) 2025 Emil Kowalski) | `main` tarball · 커밋 **`d23d7f8`**(2026-08-21) | **2026-09-08** (`refs/heads/main.tar.gz`) |
| vercel-labs/agent-browser | `https://github.com/vercel-labs/agent-browser` | Apache-2.0 (Copyright 2025 Vercel Inc.) | CLI **0.27.0**(`npm i -g agent-browser`) 이 내는 `agent-browser skills get core` 출력 · Chrome for Testing 152 | **2026-09-08** |

⚠ mattpocock 은 커밋 SHA 가 아니라 **브랜치 tarball** 이다(`git clone` 미사용 · 지시 제약). 재현 기준은
「1.2.3 + 2026-09-06」이고, 정확한 SHA 가 필요하면 그 날짜의 `main` 을 다시 받아 대조한다.

## 공통 개조 3종 (Fable 5.1 문안 교정 · 8종 전부)

1. **사고 재현 지시 제거** — 모델에게 추론을 말로 재생하라는 지시를 뺀다. 실제 삭제분 =
   `writing-plans`·`executing-plans` 의 `**Announce at start:** "I'm using the ... skill"` 2건,
   `executing-plans` 의 `Announce: "I'm using the finishing-a-development-branch skill"` 1건,
   `receiving-code-review` 의 `If you're uncomfortable pushing back out loud: Name that tension`
   → `Push back even when it is uncomfortable:` 로 치환(행동 지시만 남김).
2. **단순 반복 나열 축약** — 앞 절을 그대로 되풀이하는 목록만 줄인다.
   `test-driven-development` Red Flags 13행 → 7행(뒤 7행이 Common Rationalizations 표의 재기술이라
   `Any excuse from the Common Rationalizations table above` 한 줄로 대체),
   `verification-before-completion` 「Rule applies to」 4행 → 1행,
   `receiving-code-review` 감사 표현 금지 4행 → 2행.
   ⛔ 하드 게이트·체크리스트·근거(rationale)는 축약 대상이 아니다 — 삭제분 0건.
3. **도구 결과 대조 1행 삽입** — 각 SKILL.md 끝에
   `Before reporting, check each claim against this session's tool results.`

frontmatter `description` 은 8종 전부 **≤2문장**(후보 목록 경량 유지). `to-spec` 만 개조로 문안이 바뀌었다.

## 스킬별 개조

| 스킬 | 출처 | 공통 3종 외 개조 |
|---|---|---|
| `grilling` | mattpocock | **원문 유지** — 설계트리 → 라운드 → 프론티어 → 번호 질문 + 권장 답 · 「finding facts is your job, never the user's」 · 「프론티어가 빌 때까지 무행동」. **증보 절 1개** — 사실 조회는 `researcher` 서브에이전트로, Ted 에게 묻지 않는다 / Ted 질문은 라운드 단위로 묶고 각 건에 ⓐ·ⓑ 선택지와 권고 1개 / 질문문에 내부 약어 노출 금지(`rules §5-2`·`§5-4`) |
| `grill-me` | mattpocock | `disable-model-invocation: true` **유지**(명시 호출 전용). **종료 절 신설** — 프론티어 공집합 + Ted 확인 뒤 `dev-package/intent/<YYYY-MM-DD>-<주제>.md` 초안을 `TEMPLATE.md`(스펙 L-1)로 작성 · **확인 문장은 원문 그대로** · **미해결 질문 0건** · 초안은 **Ted 교정·커밋 대기(커밋 = 승인)** 임을 사용자에게 알린다 |
| `to-spec` | mattpocock | 「재인터뷰 없음」·시험 seam 선정(기존 우선·최소·최고층) **유지**. **삭제** — 이슈트래커 발행 · `ready-for-agent` 라벨 · `/setup-matt-pocock-skills` 전제. **치환** — 산출 = `dev-package/prd/specs/<회차>.md`, 템플릿은 스펙 L-2. **신설** — 「정책 대조」 절(CLAUDE.md §2·§3·§5·계약 파괴 여부)과 「우려 항목(ⓐ/ⓑ)」 절이 **비면 advisor ① 에 올리지 않는다**. description 에서 issue tracker 문구 제거 |
| `verification-before-completion` | superpowers | **「intent 대조」 절 신설** — 연결된 intent.md 의 proposed outcome 을 한 줄씩 대조해 **미달·초과 항목을 열거한 뒤에만** 완료를 주장한다. 둘 다 0건이어야 충족이고, 0건이 아니면 그 목록을 보고에 싣는다(advisor ② 가 같은 목록을 요구) |
| `writing-plans` | superpowers | 산출 경로 치환 — `docs/superpowers/plans/…` → **`dev-package/prd/rounds/R-*.md` · ≤300행 · 첫 줄에 spec 링크**. 라운드 파일은 spec 의 실행 뷰이고 어긋나면 spec 우선. 워크트리 문장은 `Agent(isolation: "worktree")` 로 갱신 |
| `executing-plans` | superpowers | 공통 3종만 |
| `test-driven-development` | superpowers | 공통 3종만 (참조 파일 `writing-good-tests.md` 는 무수정) |
| `receiving-code-review` | superpowers | 공통 3종만 |
| `apple-design` | emilkowalski/skills | **원문 유지**(본문 무수정 · 2026-09-06 아카이브본과 본문 동일함을 diff 로 확인). 개조 = frontmatter `disable-model-invocation: true`(명시 호출 전용 · `/apple-design` 또는 `design-review` 가 경로로 읽는다) ＋ `license` 행 ＋ 출처 주석 1행(SHA·날짜) ＋ 공통 개조 3(대조 1행). `LICENSE.txt` 동봉. 공통 개조 1·2 해당 없음(사고 재현 지시·반복 나열 0건) |
| `agent-browser` | vercel-labs/agent-browser | 원문 = CLI 가 생성하는 `core` 스킬(본문 무수정). 개조 = `name: core` → `agent-browser` · `description` 2문장 한국어로 축약(원문 5문장 · 후보 목록 경량) · `disable-model-invocation: true` · `license` 행 · 출처 주석 1행(CLI 버전) · 공통 개조 3(대조 1행). 재회수 = `agent-browser skills get core`. 도구 실체는 전역 npm(레포 밖) — 설치 명령은 `design-review §2-5` |

## 자작 스킬 (vendored 아님 · 참고)

`design-review`(2026-09-08) — 이 레포 전용. `apple-design` 을 정본의 한 축으로 읽고 `researcher`·`advisor`·`lane-worker`·`gate-runner` 위에서 audit/fix 를 돈다. 정적 계측기 `design-review/scripts/css_audit.py` 동봉. 상류 없음 · 개조표 대상 아님.

## 미채택 (스펙 B-2)

`brainstorming`(superpowers) — `grill-me` 와 같은 자리 · 1문1답이 「질문은 묶어서」 규율과 충돌 ·
"MUST use before any creative work" 자동 발동이 명시 호출 정책과 충돌.
`grill-with-docs`·`to-tickets`·`triage`·`wayfinder`(mattpocock) — CONTEXT.md·ADR 이 `PLAN-SoT §9` 와
이중화되고, 뒤 셋은 외부 이슈트래커 전제라 원장이 둘로 갈린다.

## 공통 개조 4 — 상류 스킬 참조를 로컬 등가물로 치환 (P-G 후속 · 2026-09-06)

vendoring 은 **파일 5종만** 복사했으므로 `superpowers:<이름>` 형태의 상류 참조는
**이 레포에서 해소되지 않는다**(플러그인 비활성 · 해당 스킬 미복사). 지시문이 없는 스킬을
「REQUIRED SUB-SKILL」로 가리키면 그 줄은 실행 불가 지시가 된다. 치환표 —

| 상류 참조 | 로컬 등가물 | 치환 자리 |
|---|---|---|
| `superpowers:subagent-driven-development` | 위임 원칙(글로벌 `CLAUDE.md`) ＋ `lane-worker` 에이전트 | `writing-plans/SKILL.md` 2곳 · `executing-plans/SKILL.md` 1곳 |
| `superpowers:using-git-worktrees` | `lane-worker` `isolation: worktree`(자동) | `executing-plans/SKILL.md` 1곳 |
| `superpowers:finishing-a-development-branch` | `colab-v2-work` §병합 규약(오케스트레이터 ff 병합·〈N〉 발급) | `executing-plans/SKILL.md` 1곳 |
| `superpowers:executing-plans` | `executing-plans`(로컬 vendored) | `writing-plans/SKILL.md` 2곳 |

⚠ **남긴 것 1건** — `test-driven-development/writing-good-tests.md:51` 의 `superpowers:writing-skills`.
문장 안의 **괄호 인용**이지 실행 지시가 아니고, 이 파일은 개조표에서 **무수정**으로 못박혀 있다.
`receiving-code-review`·`verification-before-completion` 에는 상류 참조가 0건이다.

## 원본 대조

원본은 이 레포에 두지 않는다. 대조가 필요하면 위 표의 경로·URL 에서 다시 받아
`diff <원본>/SKILL.md .claude/skills/<name>/SKILL.md` 로 뜨고, 나오는 차이가 위 개조 목록과 일치하는지 본다.
목록에 없는 차이가 나오면 그것이 결함이다.
