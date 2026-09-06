# 하네스 재설계 스펙 — CoLAB v2 × Claude Fable 5.1

**목적** — 세션 시작 주입을 CoLAB 개발에 실제로 쓰는 것만 남기고, 사람이 기억해 우회하던 결함 D1~D22 를 훅·게이트로 내려 「메인=오케스트레이터, 실행=격리 레인」이 문장이 아니라 코드로 강제되게 한다.

**승인** — Ted, 2026-09-06. 원문: 「판정은 전부 권고대로」. 판정 항목 J-0~J-12 전부 설계 권고안대로 확정. 재개봉 금지.

**상태** — 확정 스펙. ⭑ **⟨증보 2026-09-06 · 마감⟩ 이행 10 phase 중 9 완료 · `P-C` 부분**(H 절 상태 열 · 원장 `dev-package/PLAN-SoT.md §9 〈368〉`~`〈371〉`). ／ 종전 ~~P-T 완료 · P-B 진행 · 나머지 대기~~

**계보** — 설계 v1 → v2(advisor 게이트① 지적 18건 수용) → v3(「AI-native SDLC 플레이북」 갭 분석 16건 반영) → 이 문서(v3 + Ted 확정 판정 + 이행 상태).
**근거** — brief · inventory · workflow-profile · market-survey · grill-me 조사(mattpocock) · 실측 재계수 · Anthropic 문서 인용(V1~V4) · 플레이북 인용. 조사 산출물 8건 = `dev-package/reports/harness/2026-09-06/`(M 절).
**미검증 표식** — `[추론]` 및 K 절 15항은 그대로 보존. 이행 중 확인 대상이지 확정 사실이 아니다.

**v3 대비 이 문서의 변경** — ① J 절이 「판정 필요 항목」에서 **확정 판정 기록**으로 바뀜(선택지 소멸) ② 이행 계획에 **상태 열** 추가 ③ P-T 실행 결과를 「이행 상태」 절로 신설 ④ 절대경로를 레포 상대경로·`~/.claude` 형태로 교체 ⑤ M 절(조사 산출물 색인) 추가. **설계 내용은 무변경.**

---

## 0. 이행 상태 (2026-09-06 기준)

### 0-1. 실행 완료 — P-T 플러그인 토글 + 글로벌 정리

**플러그인 토글**

| 활성 (6) | context7 · skill-creator · code-review · typescript-lsp · pyright-lsp · eli5 |
|---|---|
| **비활성 (9)** | superpowers · claude-mem · understand-anything · ralph-loop · claude-md-management · frontend-design · feature-dev · codex · playwright |

- claude-mem·codex 비활성은 J-2·J-6 실측 판정의 집행이다(호출 0건).
- playwright 는 UI 검증 회차에 **on-demand 재활성**. 상시 비활성이 기본값.
- superpowers 는 플러그인 비활성 + 스킬 5종 vendoring 유지(P-S).

**글로벌 `~/.claude` 정리**

| 대상 | 개수 | 행선지 |
|---|---|---|
| `agents/` humanize 계열 | 12 | `~/.claude/_archive/2026-09-06-harness/` |
| `skills/` apple-design · travel-proposal · humanize 3종 | 5 | 같은 archive |
| `CLAUDE.md` | 1 | 슬림화 진행 중 (5,307B → ≤2,500B) — **P-B** |

**세션 루트 `00 CoLAB/.claude` 정리** (J-3 집행)

| 대상 | 개수 | 행선지 |
|---|---|---|
| `agents/` humanize 6 + presentation 9 | 15 | `10_Humanize-Presentation/.claude/agents/` (형제 폴더) |
| `skills/` humanize 계열 | 6 | `10_Humanize-Presentation/.claude/skills/` |
| 글로벌 고유 humanize 에이전트 | 6 | 같은 곳으로 복사(이름 중복 6 은 archive 로만) |

- archive 는 **복사 후 이동**이며 삭제가 아니다(I 절 되돌리기 보증).
- 이 이동으로 J-0 루트 이동 **이전 구간에서도** S1 이 내려간다.

### 0-2. 실행 완료 — P-B ~ P-J (브랜치 `worktree-harness-fable51-spec`)

⭑ **⟨증보 2026-09-06 · 마감⟩ 아래 표가 이 브랜치의 실적이다.** 상태 열 원본은 H 절이고 여기는 그 요약이다.
／ 종전 ~~진행 중 — P-B(글로벌 CLAUDE.md 슬림화 중 · 프로젝트 §1 교체와 H1 등록 미착수)~~ — **둘 다 끝났다.**

| phase | 커밋 | 이 브랜치에서 끝난 것 | 이 브랜치에서 잴 수 없어 다음 세션으로 넘긴 것 |
|---|---|---|---|
| P0 · P-B · P-E | `15bc4e0`·`18274f0`·`6de6aa4` | 기준선 `dev-package/reports/harness/baseline.md` · 프로젝트 `CLAUDE.md §1` 라운드 파일 1개 · H1·H2 · `run.sh` 자체 source | 없음 |
| P-M | `c26072c` | `.claude/rules/colab-rules.md`(규칙형 18 · 파일명 앵커) · 옛 메모리 `MIGRATED` 표기 | **탐침 3문**(새 세션에서만 성립) |
| P-A | `b7f36c9` | 에이전트 4종 정의 · advisor ② 3항 체크리스트 | **4종 스폰 기동 실측** — 워크트리 세션은 프로젝트 에이전트를 후보에 올리지 않는다 |
| P-S | `65afcf5` | vendored 8종 · `intent/`·`prd/specs/` 템플릿 · `CLAUDE.md` ≤200행 · `colab-v2-work` ≤110행 | **`grill-me` 실전 1회 → `intent.md` 1건** — 첫 발의는 Ted 가 직접 돌린다 |
| P-G | `16c4296` | H3·H4·H5 · `renumber-decisions.sh` · merge driver · `exec-bit` 게이트(57건 조치) · README 킬스위치 | 없음 |
| P-J | `1240b24` | `gate-summary.json` 3상태·`tree` · H6 · H7 | **전수 `all -j 4` 1회** — 병합 전 진입조건 |
| P-C | `3cd1cb8` | archive 복사 · `30_적용완료` 환류 배선 | ⛔ **옛 메모리 삭제 · `MEMORY.md` 3줄화** — 탐침 3문 통과가 조건 |

### 0-3. 선행 의존 — J-0 루트 이동은 훅 등록보다 앞선다

- 문서 인용 V1 — `settings.json` 은 하위 폴더 스코프가 없다. 세션 루트가 `00 CoLAB` 인 동안 `30 CoLAB-v2/.claude/settings.json` 의 훅은 **한 줄도 뜨지 않는다**.
- ⇒ 훅을 쓰는 모든 phase(P-B 의 H1 · P-E · P-G · P-J)는 J-0 이행 뒤에 검증해야 한다. 파일 작성은 앞당겨도 되나 **검증은 불가**.
- 이 커밋의 `.claude/settings.json`(J-10, `effortLevel: high`)도 같은 조건 — 루트 이동 후 발효한다.

### 0-4. 이 커밋에 포함된 것

| 경로 | 내용 |
|---|---|
| `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` | 이 문서 (J-8 집행) |
| `dev-package/reports/harness/2026-09-06/` | 조사 산출물 8건 + README |
| `.claude/settings.json` | `{"effortLevel": "high"}` (J-10 집행) |

훅·에이전트·rules·`intent/`·`prd/specs/` 폴더는 **이 커밋에 없다** — 각 phase 소관.
⭑ **⟨증보 2026-09-06⟩ 그 셋은 뒤 커밋에 들어왔다** — 0-2 표 참조. 이 절은 스펙 첫 커밋의 범위 기록으로 남긴다.

### 0-5. 잔여 후속 (보고 09~13 에서 모은 것 · 이 브랜치 범위 밖)

⚠ **아래는 「나중에」가 아니라 목록이다** — 착수하려면 각 항목을 WU 또는 새 `intent.md` 로 낸다(`CLAUDE.md §5`).

| # | 잔여 | 무엇이 막는가 / 무엇을 해야 하는가 | 근거 |
|---|---|---|---|
| 1 | **DB 게이트 4종의 접속 실패 분류** — 13곳 · 셀프테스트 4종 동반 | 접속 실패가 `red(판정)` 로 접혀 「준비 red」와 갈리지 않는다. 레인 1개 분량 | `12-gate-json-verification.md §5`·`§6-1` |
| 2 | **CI `planning-freshness` red** | 기획 정본 `40 COLAB-기획` 이 레포 밖이라 자동화가 못 본다. 푸는 법 셋(면제표 · 레포 안 사본 · CI 마운트)은 **판정 대기** | `13-planning-applied-wiring.md §7-1` · HANDOFF `§4 #70` |
| 3 | **`planning-freshness-selftest` 가 `ALL_GATES` 에 없다** | 검사기의 `--selftest` 는 실재하나 게이트 이름 미등록 → `run.sh all`·`selftest` 가 안 돈다. 등록하려면 fixture 2·3 의 정본 마운트 의존을 먼저 끊는다 | `13-planning-applied-wiring.md §7-1` |
| 4 | **`40 COLAB-기획/README.md` 문면이 실제와 갈린다** | README 는 `30_적용완료/` 를 「이관 · `적용일_원파일명`」으로 적었으나 집행은 「사본 · `<라운드>/<원파일명>`」이다. 기획 폴더는 읽기 전용이라 **개정 제안만** 남긴다 | `13-planning-applied-wiring.md §7-2` |
| 5 | **vendored 스킬의 외부 인용 1건** — `test-driven-development/writing-good-tests.md:51` 의 `superpowers:writing-skills` | 플러그인 비활성 상태에서 가리키는 대상이 없다. 인용 제거 또는 vendoring 판정 | `11-merge-guards-verification.md §8` |
| 6 | **글로벌 `~/.claude/agents/advisor.md` 삭제** | 프로젝트본이 실제로 뜨는 것을 새 세션에서 확인한 **뒤에** 지운다. 이 브랜치는 글로벌 파일을 건드리지 않았다 | `09-agents-verification.md §4` |
| 7 | **H7 의 `COLAB_GATE_REPORT_DIR` 는 훅 환경에 거의 안 실린다** | Bash env 가 도구 호출 간 유지되지 않아 실질 경로는 「가장 최근 `gate-summary.json`」이다. 회차 폴더를 레인마다 새로 주는 지금 규약에서는 문제가 없으나 **한계로 기록해 둔다** | `12-gate-json-verification.md §6-3` |
| 8 | **스펙 D 예시의 필드 이름** — 예시는 `state`·`log`, 실물은 `status`·`state` 둘 다 내고 `log` 는 없다 | 예시를 실물에 맞추면 두 이름을 하나로 줄일 수 있다. 판정 사항 | `12-gate-json-verification.md §6-2` |
| 9 | **K 미검증 3 — `lane-worker` 의 자율 블록이 advisor ② 를 우회하려는 경향** | **레인 2회차까지 관찰**하고 결과를 `dev-package/reports/harness/2026-09-06/` 에 덧붙인다 | `09-agents-verification.md §4` |

---

## A. 설계 목표와 성공 지표

### A-1. S1 재계수 (advisor 지적 2 수용 — v1 의 「26」은 오계)

에이전트 후보 목록은 4개 출처가 합쳐지고, **같은 이름은 하나로 접힌다**(프로젝트가 글로벌보다 우선).

| 출처 | 개수 | 내용 |
|---|---|---|
| 글로벌 `~/.claude/agents/` | 13 | advisor + humanize 12 |
| 루트 프로젝트 `00 CoLAB/.claude/agents/` | 15 | humanize 6 + presentation 9 |
| ↳ 두 출처 **이름 중복** | −6 | ai-tell-detector · content-fidelity-auditor · humanize-monolith · korean-ai-tell-taxonomist · korean-style-rewriter · naturalness-reviewer |
| **사용자 정의 유니크** | **22** | 이 중 CoLAB 개발에 쓰는 것 = advisor 1개 |
| 플러그인 | 14 | understand-anything 9 · feature-dev 3 · codex 1 · claude-code-guide 1 |
| 내장 | 5~6 | general-purpose · Explore · Plan · claude · statusline-setup |
| **후보 총계(실측)** | **≈42** | v1 이 적은 26 은 어느 조합으로도 나오지 않는다 |

스킬도 동일 구조 — 글로벌 8 + 루트 6 − 중복 3(humanize·humanize-korean·humanize-redo) = **사용자 정의 유니크 11**, 나머지는 플러그인·내장.

**핵심 함의** — humanize/presentation 자산의 **본진이 곧 세션 루트(`00 CoLAB`)** 였다. J-0 이 「루트 이동」으로 확정되어 이동만으로도 후보에서 빠지지만, 이행 전 구간을 덮기 위해 형제 폴더 이동(J-3)을 먼저 집행했다(0-1).

### A-2. 지표

| 지표 | 측정법 | 현재(실측) | 목표 | 측정 시점 |
|---|---|---|---|---|
| S1 후보 목록 | 새 세션 시스템리마인더의 agents/skills 계수 | 에이전트 ≈42 · 스킬 47 | 에이전트 ≤12 · 스킬 ≤20 | 각 phase 종료 시 새 세션 1회 |
| S2 게이트 요약 기계가독 | `gate-summary.json` 존재 + `counts` 가 `run.sh` 요약줄과 일치(이진) | 없음 | 일치 | P-J 종료 후 전수 1회 |
| S3 새 워크트리 준비 red | 새 워크트리 첫 전수의 red(준비) 건수 | 10(D1)+6(D2)=16 | 0 | P-E 종료 후 워크트리 1개 신설 |
| S4 회차 비용 | 레인 1건의 turn 수·토큰(effort 변경 전후) | 미측정 | 기록만 | P0, effort 변경 후 |
| S5 판정 재개봉 | 회차 종료 후 재판정된 확정 항목 건수(intent 확인절 대조) | 2026-09-05 16건 + rev2 3건 | 0 | 각 회차 종료 시 |

(advisor 지적 18 수용 — v1 의 S2「수동 분류 건수」는 run.sh 가 이미 나눠 찍으므로 측정 불가였다.)

---

## J-0. 세션 루트 — **확정: `30 CoLAB-v2` 로 이동**

**실측 사실** — 현 세션 cwd = `00 CoLAB`(git 레포 아님). 자동메모리 디렉터리 키 `-mnt-f-00-Project-00-CoLAB`. 레포는 그 아래 `30 CoLAB-v2/`.

### 문서 인용으로 확정된 로딩 규칙

- **CLAUDE.md / rules** — "Claude Code loads `CLAUDE.md` and `CLAUDE.local.md` from your current working directory and every directory above it." · "Claude also discovers `CLAUDE.md` and `CLAUDE.local.md` files in subdirectories under your current working directory. **Instead of loading them at launch, they are included when Claude reads files in those subdirectories.**"
- **rules 디렉터리** — "Place markdown files in your project's `.claude/rules/` directory… Rules without `paths` frontmatter are loaded at launch with the same priority as `.claude/CLAUDE.md`." 중첩 rules 는 "rules that load on demand, including path-scoped rules and **rules in nested `.claude/rules/` directories**" → **지연 로딩**.
- **settings/hooks/agents** — 설정 파일 스코프 표는 `~/.claude/settings.json`(전 프로젝트) · `.claude/settings.json`(단일 프로젝트, 커밋 가능) · `.claude/settings.local.json`(커밋 안 됨) 3층만 정의. **하위 폴더 settings 는 층이 아니다.**

⇒ 루트가 `00 CoLAB` 인 동안 `30 CoLAB-v2/.claude/settings.json` 에 훅을 넣으면 **한 줄도 안 뜬다**. `30 CoLAB-v2/CLAUDE.md` 는 **뜨긴 뜨되 launch 가 아니라 그 아래 파일을 읽는 순간**(현행 동작과 일치).

### 판정 근거 대조 (기록 — 판정 완료)

| | 루트 유지 = `00 CoLAB` (불채택) | **루트 이동 = `30 CoLAB-v2` (확정)** |
|---|---|---|
| 훅·규칙 위치 | `00 CoLAB/.claude/settings.json` + `.claude/rules/` | `30 CoLAB-v2/.claude/settings.json` + `.claude/rules/` |
| 버전관리 | **안 됨**(레포 밖). 훅 유실·이력 없음 | 됨. 훅이 코드와 함께 리뷰·롤백 |
| 협업자 영향 | 없음(Ted 기계 로컬) | **있음** — 클론하면 차단 훅이 같이 온다(V4) |
| `40 COLAB-기획` 접근 | 그대로 | `--add-dir ../40\ COLAB-기획` 필요 |
| humanize/presentation 자산 | 같은 루트에 상주 → S1 을 못 내린다 | 자동으로 후보에서 빠짐 → S1 즉시 −21 |
| CLAUDE.md | `00 CoLAB/CLAUDE.md` 신설 필요(현재 없음) | 기존 `30 CoLAB-v2/CLAUDE.md` 가 **launch 로딩**으로 승격 |
| 자동메모리 경로 | 현행 유지 | 레포 기준으로 **바뀐다** — 기존 33건 이관 필요 |
| 이행 비용 | 낮음(자산 이동 1회) | 중간(런처 습관 변경 + 메모리 경로 이관) |

**확정 이유 셋** — ① 훅이 레포 이력에 들어가야 「코드로 강제」가 성립(유지안은 Ted 기계에만 존재하는 규칙, D 목록이 반복될 조건 그대로) ② S1 의 21개(humanize+presentation)가 파일 이동 없이 사라짐 ③ `30 CoLAB-v2/CLAUDE.md` 가 지연이 아니라 launch 로딩이 되어 §1 부트스트랩 규칙이 첫 턴부터 걸린다.
**완화** — 협업자 영향은 J-9(커밋 + `COLAB_HOOKS=0` 킬스위치 README 명시)로 처리. 메모리 이관은 P-M 에서 rules 로 흡수하므로 추가 비용 없음.
**선행 집행 기록** — humanize/presentation 자산은 루트 이동을 기다리지 않고 형제 폴더 `10_Humanize-Presentation/.claude` 로 **이동 완료**(J-3, 0-1). 이행 전 구간에도 S1 이 내려간다.

**이하 모든 경로는 `30 CoLAB-v2/` = 레포 루트 = 세션 루트 기준.**

---

## B. 3층 구조

### B-1. 글로벌 `~/.claude`

| 경로 | 처리 |
|---|---|
| `CLAUDE.md` | 불변 규칙만 존치(위임 원칙·서브에이전트 언어·HTML 규격). 스킬 3절(graphify/travel-proposal/explain-visually)은 각 스킬 description 이 담당 → 삭제. 5,307B → **≤2,500B**. **P-B 진행 중** |
| `settings.json` `effortLevel` | **글로벌은 건드리지 않는다**(전 프로젝트 비용 영향 — J-10). `30 CoLAB-v2/.claude/settings.json` 에 프로젝트 스코프로 `high`. **이 커밋에서 집행 완료** |
| `agents/advisor.md` | 프로젝트로 이동 → `30 CoLAB-v2/.claude/agents/advisor.md` (P-A) |
| `agents/` humanize 12 | **archive 이동 완료**(`~/.claude/_archive/2026-09-06-harness/`). 고유 6 은 `10_Humanize-Presentation/.claude` 로도 복사 |
| `skills/` apple-design·travel-proposal·humanize 3종 | **archive 이동 완료**. `archify`·`explain-visually`·`graphify` 존치 |
| `references/selfcontained-html.md` | 존치 |

### B-2. 프로젝트 `30 CoLAB-v2/.claude/` + 아티팩트 폴더

```
.claude/
  settings.json          # 공유 훅 + worktree.baseRef=fresh + effortLevel:high + permissions
  settings.local.json    # 개인 전용 훅만 (J-9 확정 = 공유 훅은 settings.json 커밋)
  rules/colab-rules.md   # 메모리 규칙형 16건 흡수 (G절)
  agents/                # 4개 (B-3)
  skills/colab-v2-work/  # 유지. 훅으로 이관한 규칙문 축약(169행→≈110행)
  skills/{writing-plans,executing-plans,test-driven-development,
          verification-before-completion,receiving-code-review}/   # vendored(superpowers, MIT)
  skills/{grilling,grill-me,to-spec}/                              # vendored(mattpocock/skills, MIT)
  hooks/                 # C절 스크립트
dev-package/
  intent/<YYYY-MM-DD>-<주제>.md   # 발의 아티팩트 (J-12 확정 = 레포 안). 템플릿 L-1
  prd/specs/<회차>.md             # to-spec 산출. 템플릿 L-2
```

- `CLAUDE.md`(17,852B): §1 을 「라운드 파일 1개만」으로 교체, §6 5줄 규약, 배포 절 dev+doctor 14/14. 상세는 rules 로 이관. **≤200행**(문서 권고: "target under 200 lines per CLAUDE.md file").
- vendored 스킬은 Fable 5.1 가이드대로 ⑴ 사고 재현 지시 제거 ⑵ 나열형 축약 ⑶ 「보고 전 각 주장을 이 세션의 도구 결과와 대조」 삽입. **8종 전부 MIT · 명시 호출 전용 · 훅 없음**(mattpocock 계열엔 훅 자동화가 하나도 없음이 확인됨).

| 스킬 | 출처 | 개조 |
|---|---|---|
| `grilling` | mattpocock | 설계트리 → 라운드 → **프론티어**(선행이 해소된 결정만) → 번호 질문 + 각 권장 답 구조 유지. 「finding facts is your job, never the user's」 유지 = 조회 가능한 사실은 서브에이전트가 찾고 Ted 에게 묻지 않는다. 권장 답 제시를 **Ted ⓐ/ⓑ 문법**으로 치환 |
| `grill-me` | mattpocock | `grilling` 을 호출하는 얇은 래퍼. `disable-model-invocation: true` 유지 = 명시 호출 전용(graphify 선례). 원형은 파일을 쓰지 않으므로 **종료 시 intent.md 초안 작성** 1행 추가 |
| `to-spec` | mattpocock | **재인터뷰 없음** 유지. 이슈트래커 발행·`ready-for-agent` 라벨 단계 삭제 → `dev-package/prd/specs/<회차>.md` 파일 배출. 시험 seam 선정(기존 우선·신설 최소·가장 높은 층) 유지. Ted ⓐ/ⓑ 우려 항목 절 + CLAUDE.md §2·§3 인용 삽입(갭 G7 = 사후 게이트가 아닌 **작성 시점 제약**) |
| `writing-plans`·`executing-plans`·`test-driven-development`·`receiving-code-review` | superpowers | v2 그대로 |
| `verification-before-completion` | superpowers | **intent 대조 절 추가** — proposed outcome 미달·초과 항목을 열거한 뒤에만 완료 주장 |
| `brainstorming`(superpowers) · `grill-with-docs`·`to-tickets`·`triage`·`wayfinder`(mattpocock) | — | **미채택** — brainstorming: grill-me 가 같은 자리(모호성 해소 전 무행동)를 차지 · 1문1답이 `batch-questions-product-framed` 규율과 충돌 · "You MUST use this before any creative work" 자동 발동이 명시 호출 정책과 충돌. 나머지: grill-with-docs 는 CONTEXT.md·ADR 로 〈N〉 이중화, to-tickets·triage·wayfinder 는 외부 이슈트래커 전제(경쟁 원장) |

**충돌 메모(수정 7 ↔ v2 설계자 결정 「mattpocock-skills 미도입」)** — 플러그인 전면 도입은 여전히 미채택, 갭 G1·G3 근거로 **3종 한정 파일 vendoring 으로 개정**. advisor 수용 항목(에이전트 4·훅 7·게이트 JSON·phase 순서·J-2/J-6)에 저촉 없음. S1 스킬 목표는 vendored 8 을 포함해도 ≤20 유지.

**intent.md 의 집·소유** (J-12 확정 = 레포 안)
- 위치 = `dev-package/intent/<YYYY-MM-DD>-<주제>.md`. 커밋·게이트·〈N〉 역링크 대상이라 `40 COLAB-기획` 밖. 기획자 원본(`10_적용전`)은 **무수정**, intent 는 경로로 참조만 한다.
- 소유 = **에이전트가 초안, Ted 가 교정·커밋**(플레이북: "The product owner reviews and corrects the agent-written intent.md before it is committed"). 커밋이 곧 승인.
- **승인 후 개정 금지 · 신규 발행** — 승인된 intent 는 고치지 않고 새 intent.md 를 낸다. **[추론]** — 플레이북에 명시 규칙 없음(K 미검증 11).

### B-3. 에이전트 4종 (v1 의 6 → advisor 지적 13 수용)

| name | model | effort | isolation | 역할 | 자율 블록 |
|---|---|---|---|---|---|
| `advisor` | fable | `high` | — | 3게이트 자문. 실행·편집 금지. **게이트 ② 체크리스트 3항 고정** — ① Alembic 회차의 revision 체인 정합(v1 migration-reviewer 흡수) ② 「main 과 동일」 금지(F13) ③ **intent 대조** — intent.md 의 proposed outcome 중 **미달·초과 항목 열거** | 없음 |
| `lane-worker` | opus | `high` | `worktree` | 레인 1건 구현 + 단독 게이트 green | **있음** + 범위/테스트 블록 |
| `researcher` | sonnet | `medium` | — | 조사·PRD화. 산출은 `dev-package/sessions/<회차>/`. **전수 red(판정) 로그·`deploy_doctor` 미달 항목·기획자 문의를 받으면 그 근거로 intent 초안 1건 작성**(S6 경로, F 절) | 있음 + 「도구 결과 대조」 |
| `gate-runner` | haiku | `low` | — | **선택** — 전수 실행 후 요약만. `run_in_background` 로 대체 가능하므로 P-J 에서 `gate-summary.json` 이 나오면 **폐기** | 없음 |

```yaml
# .claude/agents/advisor.md
---
name: advisor
description: 3게이트 자문(계획 검토 / 산출물 수용 / 비가역 go-no-go). 리뷰만, 실행 금지.
model: fable
effort: high          # 가이드 "start at high". xhigh 는 P0 비용 실측 뒤 재검토
disallowedTools: Edit, Write, NotebookEdit
maxTurns: 12
---
```
```yaml
# .claude/agents/lane-worker.md
---
name: lane-worker
description: 레인 1건을 격리 워크트리에서 구현하고 단독 게이트 green 까지 책임진다.
model: opus
effort: high
isolation: worktree
skills: test-driven-development, verification-before-completion
maxTurns: 60
---
```
```yaml
# .claude/agents/researcher.md  (model: sonnet / effort: medium / maxTurns: 30 / disallowedTools: Edit)
# .claude/agents/gate-runner.md (model: haiku / effort: low / tools: Bash, Read, Grep / maxTurns: 20)
```

- **제외 근거** — `migration-reviewer` = Alembic 회차에만 뜨는 읽기전용 리뷰 → advisor ② 프롬프트 절로 충분. `merge-prep` = 실체가 스크립트 2개(`renumber-decisions.sh`, merge driver)이며 아직 없음 → P-G 에서 스크립트를 먼저 만들고, 그때 에이전트화 여부를 재판정.
- `effort` / `isolation` 필드 존재는 문서 확인됨(sub-agents frontmatter 표: `effort` = low/medium/high/xhigh/max, `isolation` = worktree).

### B-4. 플러그인 (**P-T 집행 완료** — 0-1)

| 활성(6) | context7 · typescript-lsp · pyright-lsp · code-review · eli5 · skill-creator |
|---|---|
| **비활성(9)** | superpowers(5스킬 vendoring 으로 대체 · `brainstorming` 은 **grill-me 가 자리를 차지**해 대체) · claude-mem(**J-2 확정**) · codex(**J-6 확정**) · understand-anything(에이전트 9+스킬 8, S1 최대 기여자) · ralph-loop · claude-md-management · frontend-design · feature-dev(에이전트 3) · playwright(필요 회차에만 on-demand) |

- mattpocock 은 **플러그인 설치 안 함**(`claude plugins install mattpocock-skills` 미사용) — 설치하면 나머지 20여 스킬 description 이 S1 에 그대로 얹힌다. **파일 복사 vendoring 3종만**, 훅 0개.

---

## C. 훅 설계 (13 → 6)

등록처 = `30 CoLAB-v2/.claude/settings.json`(J-9 확정 = 커밋. 개인 전용 훅만 `settings.local.json`).
**등록 형식은 전부 `bash .claude/hooks/<x>.sh`** — D5(NTFS exec bit)가 훅 자신에게도 적용되기 때문.
**킬스위치** — 모든 스크립트 첫 줄 `[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0`. **README 에 명시**(J-9).
차단은 **exit 2** 만 유효(exit 1 은 통과).

| # | event | matcher | 등록 | 차단 | 해소 프릭션 | 오탐 시나리오 점검 |
|---|---|---|---|---|---|---|
| H1 | `SessionStart` | `startup\|clear` | `bash .claude/hooks/bootstrap-diet.sh` | **비차단**(stdout 안내) | D7·D20 — 2.4MB 부트스트랩 | 안내만 하므로 오탐 없음. 라운드 파일이 0건인 신규 회차에도 「없음」을 찍고 통과 |
| H2 | `SubagentStart` | `lane-worker` | `bash .claude/hooks/worktree-setup.sh` | **비차단**(setup 실행 + 결과 stdout) | D1 — 준비 red 10건 | **오케스트레이터 계획 턴에서 안 뜬다**(matcher 가 에이전트 타입). `researcher`·`advisor` 스폰엔 미발동. venv 는 **복사가 아니라 재생성**(pyvenv.cfg 절대경로 문제) |
| H3 | `PreToolUse` | `Bash` | `bash .claude/hooks/git-guard.sh` | **차단** | F8·D10 인접 | ⚠ **레인 첫 줄 `git merge --ff-only` 를 막으면 안 된다**(D6 해법). 차단 대상을 명시 열거로 좁힘 — ⑴ main/master 로 push ⑵ `--force`/`-f` push ⑶ **HEAD 가 main/master 일 때의** `git merge` ⑷ `gh pr merge` ⑸ `branch -D main`. 비-main 브랜치에서의 `merge --ff-only` 는 **허용** |
| H4 | `PreToolUse` | `Edit\|Write` | `bash .claude/hooks/migration-guard.sh` | **차단** | Alembic 계약 파괴 | ⚠ 조건은 「추적 중」이 아니라 **`git cat-file -e origin/main:<path>` 성공**. 레인이 자기 첫 커밋 뒤 자기 신규 revision 을 고치는 경우는 origin/main 에 없으므로 **통과** |
| H5 | `PreToolUse` | `Edit\|Write` | `bash .claude/hooks/decision-number-guard.sh` | **차단** | D3 — 〈N〉 충돌 2회 | `PLAN-SoT.md §9` 에 새 〈N〉 을 쓰는 편집만 대상. `prd/tools/max-decision.sh` 의 `max+1` 과 불일치 시 차단. **§9 외 파일에서 기존 〈N〉 을 인용하는 편집엔 미발동**(정규식이 「§9 블록 + 신규 행」에만 매칭) |
| H6 | `SubagentStop` | `researcher` | `bash .claude/hooks/uncommitted-artifacts.sh` | **차단** | D9 — 하루 4회 | ⚠ **자동 커밋하지 않는다**(v1 H9 철회). 미추적 파일이 `dev-package/sessions/`·`reports/` 아래 있으면 exit 2 + 경로 열거 → researcher 가 `git add <경로>` 로 직접 커밋. `git add -A`·push 금지. 오케스트레이터 체크아웃의 무관한 변경을 쓸어담지 않는다 |
| H7 | `SubagentStop` | `lane-worker` | `bash .claude/hooks/lane-gate-summary.sh` | **차단** | D11·D12 | `reports/<회차>/<레인>/gate-summary.json` 존재 + `counts.red_판정 == 0` 확인. **스키마 위반이 아니라 부재만** 차단하므로 게이트를 안 돌린 레인만 걸린다 |

(6 목표 대비 7 — H1 은 순수 안내라 차단 훅 계수에서 제외. 차단 훅 = H3~H7 5개.)

### 삭제한 훅과 대체 (advisor 지적 4·7·9·10·11 전면 수용)

| v1 | 삭제 이유 | 대체 |
|---|---|---|
| H3 gate-env-guard | Bash env 는 도구 호출 간 유지되지 않아 문자열 매칭밖에 못 한다. `~/.colab-v2-test.env` 는 HOME 에 있어 모든 워크트리에서 보인다 → `.worktreeinclude` 와 무관 | **`gates/run.sh` 가 스스로 source**. 파일 부재 시 exit 78 + readiness 표식 |
| H6 work-items-guard | Edit/Write 훅은 「끝 덧붙임」과 「정당한 신규 블록」을 구분 못 한다. 모든 신규 WU 가 덧붙임이다. D4 는 리베이스 시점 문제 | `.gitattributes` **custom merge driver**(F4) + 기존 `work-item-consistency` 게이트(id 유일성 이미 강제) |
| H7 exec-bit-guard | `git commit` 문자열 가로채기가 취약(v1 K-3 이 자인) | **`gates/run.sh exec-bit` 게이트** — `git ls-files -s -- '*.sh' \| awk '$1=="100644"'` → red. CI 에서 같이 돈다 |
| H11 Stop | **모든 세션의 모든 응답 끝**에 뜬다. 오케스트레이터 계획 턴마다 게이트 검사를 요구한다. `stop_hook_active` 우회는 매 턴 잔소리로 남는다 | 레인 완료 검사는 H7(SubagentStop). HANDOFF 리마인더는 `SessionEnd` 비차단 또는 CLAUDE.md §6 |
| H12 TaskCompleted | 레인이 Task 목록을 쓴다는 근거가 프로파일에 없다. 「증거 경로 인용」은 스크립트로 검증 불가 | F13 은 **advisor ② 체크리스트 항목**(colab-v2-work 에 이미 있음) |
| H13 format-on-save | 오케스트레이터의 마크다운 편집에도 발동해 무관한 diff 생성 | 없음(포매터는 게이트/CI) |

---

## D. 게이트 요약 계약 (v1 의 4상태 폐기 — advisor 지적 3 수용)

**`gates/run.sh` 는 이미 3상태를 구현하고 있다.** run.sh:452-493 이 `green / red(판정) / red(준비)` 를 exit 78 + `::gate-readiness-failure::` 표식으로 가르고 계수까지 찍는다. run.sh:39 는 「대상 0건은 전부 red」(CLAUDE.md §4 green-by-skip 금지)를 명시한다. D12 는 **출력 부재가 아니라 읽는 사람의 오독**이었다.

⇒ **게이트 로직은 한 줄도 고치지 않는다.** 요약 블록 끝에서 같은 변수로 JSON 한 개만 더 배출한다.

```json
{"schema":"colab-gate-summary/1",
 "tree":"<git rev-parse HEAD^{tree}>",
 "parallelism":4,
 "counts":{"green":50,"red_판정":0,"red_준비":0,"red_준비_입력미선언":0},
 "gates":[{"name":"rls-policy","state":"green","exit":0,"log":"reports/.../rls.log"}]}
```
- `state` 값은 **`green` / `red_판정` / `red_준비` 3개뿐**. `SKIP` 은 만들지 않는다 — 이 레포는 대상 0건을 red 로 못박았고, SKIP 은 green-by-skip 통로를 다시 여는 것이다.
- `counts` 는 run.sh 가 이미 세는 `n_green` / `n_red_judge` / `n_red_ready` / `n_undeclared_input` 을 그대로 쓴다. 새 계수 개념(`targets`) 없음 → v1 K-4(53게이트가 targets 를 낼 수 있는가) **소멸**.
- 병합 진입 조건 = `red_판정 == 0` **및** `red_준비 == 0`(준비 red 도 red 다 — run.sh 주석 그대로).
- `tree` 가 직전 판정본과 같으면 전수 재실행 갈음(D8).
- 산출 위치 `dev-package/reports/<회차>/<레인>/gate-summary.json`. 소비자 = H7.

---

## E. 요구사항 21 × 대응 (변경분만)

| F# | 요구 | 대응 | 비고 |
|---|---|---|---|
| F1 | 워크트리 env 자동 구축 | H2(`SubagentStart:lane-worker`) + `worktree-setup.sh` | v1 은 `SessionStart` — **isolation 워크트리는 세션 중간에 생기므로 안 뜬다**(지적 8) |
| F2 | 테스트 env 주입 | `run.sh` 자체 source + 부재 시 exit 78 | 훅 삭제 |
| F3 | 게이트 기계 출력 | D절 JSON 배출 | 게이트 로직 무변경 |
| F4 | work-items 충돌 | `.gitattributes` merge driver | 훅 삭제 |
| F5 | 〈N〉 원자 발급 | H5 + `renumber-decisions.sh` | merge-prep 에이전트 없이 |
| F8 | 병합 권한 잠금 | H3(열거식) | `merge --ff-only` 허용 |
| F10 | `.sh` exec bit | `run.sh exec-bit` 게이트 | 훅 → 게이트 |
| F11 | 산출물 커밋 | H6(차단, 자동커밋 아님) | |
| F13 | 「main 과 동일」 금지 | advisor ② 체크리스트 **3항 중 ②** | 훅 삭제 |
| F14 | ELI5 내부용어 차단 | `colab-v2-work` 절차 + 보고 전 grep(`창 [0-9]`·`WU-`·`〈`) | 훅 삭제(보고서 편집마다 발동은 과잉) |
| F16 | 라운드 파일 생성기 | **`to-spec` → `spec.md` → 라운드 파일**(spec 의 실행 뷰) | v1 은 researcher 직접 작성 |
| F17 | 판정 캡처 | **intent.md 확인절** — 프론티어 공집합·Ted 확인 문장 원문·재개봉 금지 예/아니오 | 절차문 → 파일 아티팩트로 승격 |
| F19 | 병렬도 | 단독=narrow, 병합 전=`all -j 4` | 지시문 |
| F20 | `30_적용완료` 환류 | **J-1 활성 확정** + 잔여 결함은 새 intent.md 로 발행(기존 intent 개정 아님) | P-C 에서 배선 |
| F21 | API 529 | 하네스 제어 수단 없음 — rules 문장으로만 | unresolved |

(F6·F7·F9·F12·F15·F18 은 v1 과 동일.) **상시 지표 감시 → 자동 발의는 요구 21 에 대응 번호가 없다**(F22 후보) — S6 경로는 감시 인프라 없이 전수 red 로그로만 개통(F 절).

---

## F. 파이프라인 게이트표 (변경분 — 신설 2단계 포함)

| 단계 | 주체 | 산출 | 차단 게이트 |
|---|---|---|---|
| **1.5 grill-me**(신설) | **메인 세션 — Ted 가 직접 답한다.** 위임 없음, **자율 블록 없음** | 파일 없음(대화). 결과는 3 의 intent.md §설계트리로 흡수 | **프론티어 공집합 + Ted 확인 문장(원문 캡처)**. 확인 전 무행동. 조회 가능한 사실은 서브에이전트가 찾고 Ted 에게 묻지 않는다 |
| 3 Ted 판정(개정) | Ted | **`dev-package/intent/<날짜>-<주제>.md`** + ELI5 HTML. `결정서_Ted_*.md` 는 intent 승인 기록으로 흡수(J-11 확정) | F14 eli5-lint. Ted 교정·커밋 = 승인 |
| **3.5 to-spec**(신설) | `to-spec` 스킬 — **재인터뷰 없음**(intent 를 합성만) | **`dev-package/prd/specs/<회차>.md`** | advisor ① 계획 검토. 정책 대조절(CLAUDE.md §2·§3·계약 파괴 여부)이 비어 있으면 반려 |
| 4 라운드 파일(개정) | 메인 세션 | `prd/rounds/R-*.md` — **spec 의 실행 뷰**, 첫 줄에 spec 링크 | **≤300행 상한은 라운드 파일에만** 적용 |
| 8 advisor ②(개정) | `advisor` | 수용 검토 | 3항 — revision 체인 / 「main 과 동일」 금지 / **intent proposed outcome 미달·초과 항목 열거** |
| 10 병합 + 〈N〉(개정) | 오케스트레이터 전용 | §9 〈N〉 행이 **`intent:`·`spec:` 경로 2필드 포함** | 전수 `all -j 4` FAIL_JUDGMENT=0 + max+1 재실측 |
| 15 환류(개정) | 오케스트레이터 (**J-1 활성 확정**) | `30_적용완료` 이동 + **잔여 결함은 새 intent.md** | 승인된 intent 개정 금지 |

v2 유지분 — 8.5 마이그레이션 주체 `migration-reviewer` → **advisor ② 1항 흡수** · 9 병합 준비 주체 `merge-prep` → **오케스트레이터 + `renumber-decisions.sh`** · 13 HANDOFF 의 H11 → **`SessionEnd` 비차단 안내 + CLAUDE.md §6**.
**spec.md ↔ 라운드 파일** — spec.md 는 「무엇을·왜·어떤 결정으로」의 불변 기록, 라운드 파일은 그 **실행 뷰**(파일·순서·증명 기준·레인 배치)다. 라운드 파일 첫 줄이 spec 을 링크하고, 두 문서가 어긋나면 **spec 이 우선**한다. 설계 근거가 300행 상한에 밀려 먼저 잘리던 문제(갭 G3)는 근거를 spec 으로 옮겨 해소.
**충돌 메모** — ⑴ 수정 3 ↔ F6·`session-bootstrap-diet`: spec.md 는 **부트스트랩 대상이 아니다**. 세션 시작에 읽는 파일은 여전히 라운드 파일 1개, spec 은 첫 줄 링크로 필요할 때만 연다. ⑵ 수정 2 ↔ `ted-decisions-*` 재개봉 금지: J-11 은 **기록 형식** 판정이지 확정 판정의 재개봉이 아니다 — 기존 결정서 4건은 그대로 두고 신규 회차부터 intent 로 일원화.

**S6(감시 → 에이전트 자동 발의) 경로 — 후행 phase / nice-to-have.** 플레이북 Stage 6 = 감시 breach·티켓·메시지가 사람 없이 에이전트를 기동 → 에이전트가 로그를 근거로 intent.md 를 쓰고 파이프라인 1 로 재진입.
- **지금 만들지 않는다** — 상시 지표 감시 인프라는 신규 phase 를 요구하고, 대응 티어(1σ 기록 / 2σ 읽기전용 진단 / 3σ 행동 허용)는 롤백 경로가 증명된 뒤 문제다(플레이북 채택 순서: 가속 전에 게이트).
- **지금 개통하는 최소분** — 입력 = 전수 `red(판정)` 로그 · `deploy_doctor` 14/14 미달 항목 · 기획자 문의/티켓. 처리 = `researcher` 가 intent 초안 1건(B-3). 승인 = Ted 교정·커밋. 요구 번호 대응 없음(F22 후보), 대응 티어는 **P-C 이후 재판정**.

---

## G. 메모리 33건 이행 (검증 절차 추가 — 지적 16 수용)

v1 의 4갈래 분류(rules 16 / 훅대체 6 / HANDOFF 8 / 원장 4)는 유지. 훅 대체분만 정정 —
`ntfs-exec-bit-update-index` → **exec-bit 게이트**, `parallel-lanes-ledger-append-conflict` → **merge driver + work-item-consistency**, `gates-need-test-env-sourced` → **run.sh 자체 source**.

**삭제 전 검증(명명된 절차)** — 새 세션 1개를 열어 ⑴ `/context` 의 Memory files 에 `colab-rules.md` 가 있는지 확인 ⑵ 규칙 내용에서 뽑은 **탐침 질문 3개**(예 「같은 트리를 다시 전수 돌리나」·「보고서에 창 번호를 쓰나」·「main 과 동일한 오류는 수용 근거인가」)에 규칙대로 답하는지 확인. 둘 다 통과해야 삭제.
**앵커 규칙** — 병합된 `colab-rules.md` 안에 원본 **파일명 16개를 소제목 옆에 그대로 남긴다**. diff 로 「무엇이 누락됐나」를 기계 대조할 수 있어야 한다.
MEMORY.md 는 이 검증 통과 후에만 3줄 포인터로 축소.
**주의** — J-0 루트 이동으로 자동메모리 디렉터리 키가 바뀐다. 기존 33건은 P-M 에서 rules 로 흡수되므로 별도 이관 작업은 없으나, 흡수 전 세션에서는 메모리가 비어 보인다.

---

## H. 이행 계획 (해제가치 순 재배열 — 지적 17 수용)

**레인 정지가 필요한 phase 는 없다.**

| 순서 | Phase | 상태 | 내용 | 검증(측정) | 세션 | 레인 진행 중 가능? |
|---|---|---|---|---|---|---|
| 1 | **P0 기준선** | **완료 2026-09-06**(`15bc4e0` 동반) | S1/S3/S4 현 상태 실측 → `dev-package/reports/harness/baseline.md` | 3지표 수치 기록 | 0.5 | 가능 |
| 2 | **P-T 플러그인 토글** | **완료 2026-09-06** | 플러그인 9 비활성·6 활성, 글로벌 에이전트 12·스킬 5 archive, 루트 에이전트 15·스킬 6 형제 폴더 이동(0-1) | 새 세션 후보 목록 **에이전트 42→≤12** — 다음 새 세션에서 실측 | 0.5 | 가능 |
| 3 | **P-B CLAUDE.md §1 + H1** | **완료 2026-09-06**(`15bc4e0` — 프로젝트 `CLAUDE.md §1` 라운드 파일 1개 + H1 등록. 글로벌 `~/.claude/CLAUDE.md` 슬림화는 레포 밖) | 글로벌 CLAUDE.md 슬림화 진행 중. 프로젝트 §1 을 라운드 파일 1개로 교체, `bootstrap-diet.sh` 등록은 **J-0 이행 후** | 새 세션에서 부트스트랩 읽기 바이트 2.4MB→라운드 1개 | 0.5 | 가능 |
| 4 | **P-E 워크트리 env** | **완료 2026-09-06**(`15bc4e0`·`18274f0`·`6de6aa4` — advisor ② 지적 수정 반영: venv Python 3.12 고정 · 스탬프 기반 외부 venv 판별 · 3.12 전수 로그 커밋 · 기준선 문구 정정) | H2(`SubagentStart:lane-worker`) + `worktree-setup.sh`(venv 재생성) + run.sh 자체 source | 레인 1개 스폰 → 첫 전수 red(준비) **16→0** | 1 | 가능(새 레인에서 검증) |
| 5 | **P-M 메모리 이관** | **완료 2026-09-06**(`c26072c`) | `rules/colab-rules.md` 작성, 메모리 33건에 `MIGRATED` 표기(삭제 아님) | G절 탐침 3문 통과 | 1 | 가능 |
| 6 | **P-A 에이전트** | **완료 2026-09-06**(`b7f36c9` — ⚠ **4종 스폰 기동 실측은 다음 세션**. 워크트리 세션에서는 프로젝트 에이전트가 후보에 뜨지 않아 이 브랜치에서 잴 수 없다) | `.claude/agents/` 4개 작성, advisor 글로벌→프로젝트 | 4개 스폰 각 1회 정상 기동, advisor ② 가 revision 체크리스트 포함 | 0.5 | 가능 |
| 7 | **P-S 스킬 vendoring** | **완료 2026-09-06**(`65afcf5` — ⚠ **`grill-me` 실전 1회 → `intent.md` 1건 산출은 다음 세션**. 첫 발의는 Ted 가 직접 돌린다) | superpowers 5 + **mattpocock 3**(`grilling`·`grill-me`·`to-spec`) 복사·Fable 5.1 문안 교정, to-spec 의 이슈트래커 절 제거, `dev-package/intent/`·`prd/specs/` 신설, `colab-v2-work` 축약 | CLAUDE.md ≤200행, colab-v2-work ≤110행, 스킬 후보 47→≤20(vendored 8 포함) **+ grill-me 1회 실전 실행 → intent.md 1건 산출(확인 문장 원문 포함) + to-spec 1회 → spec.md 1건 및 라운드 파일 첫 줄 링크 존재** | 1.5 | 가능 |
| 8 | **P-G 병합 가드** | **완료 2026-09-06**(`16c4296` — 의도적 위반 5/5 차단 · `exec-bit` 도입 시 `100644` 57건 조치 · 재번호 역링크 대조 통과) | H3·H4·H5, `renumber-decisions.sh`(**〈N〉 행의 `intent:`·`spec:` 필드 보존·이동 포함**), merge driver, exec-bit 게이트, **README 킬스위치 문안**(J-9) | 의도적 위반 5종 시도 → 5/5 차단 **+ 레인 첫 줄 `merge --ff-only` 1회 통과 확인**(오탐 반증) **+ 재번호 후 표본 5건의 `intent:`·`spec:` 경로가 실존 파일을 가리키는지 확인** | 1 | 가능 |
| 9 | **P-J 게이트 JSON** | **완료 2026-09-06**(`1240b24`) | `run.sh` 요약 끝에 JSON 배출 + H6·H7 | 전수 1회에서 `counts` 가 요약줄과 일치 | 0.5 | 가능(게이트 로직 무변경이라 공유자산 위험 없음) |
| 10 | **P-C 정리** | **부분 2026-09-06**(`3cd1cb8` — archive 복사 · `30_적용완료` 환류 배선까지. ⛔ **옛 메모리 삭제 · `MEMORY.md` 3줄화 잔여** — 조건은 새 세션의 탐침 3문 통과) | 메모리 삭제 실행, MEMORY.md 3줄화, `30_적용완료` 배선(J-1 활성) | 메모리 33→≤4 | 0.5 | 가능 |

합계 **약 7.5 세션**(P-S 가 vendoring 3종·실전 1회로 +0.5). 비가역 인접은 P-C 하나뿐이며 그 앞의 archive 복사가 보증한다.

**phase 밖 선행 작업** — **J-0 루트 이동**. 훅을 쓰는 P-B(H1)·P-E·P-G·P-J 의 **검증이 성립하는 조건**이므로 P-E 착수 전에 실행한다(0-3).

---

## I. 되돌리기

v1 과 동일(archive 복사 → 대체물 검증 → 삭제). 변경 3건 —
- **훅 비활성은 파일 편집 없이** `COLAB_HOOKS=0` 환경변수 한 개로 전 훅이 즉시 무력화된다.
- `run.sh` 개정은 **JSON 배출 한 블록 추가**이므로 revert 가 1커밋이며 게이트 판정에 영향이 없다.
- P-T 되돌리기 = `~/.claude/_archive/2026-09-06-harness/` 에서 복원 + 플러그인 재활성. 삭제한 것이 없으므로 손실 0.

---

## J. 확정 판정 (Ted 2026-09-06 — 「판정은 전부 권고대로」)

**재개봉 금지.** 아래 11건은 확정 사실이며 후속 세션에서 선택지로 되돌리지 않는다. 이행 중 실측이 판정을 뒤집을 근거를 내면 **새 발의(intent.md)** 로 올린다.

| # | 항목 | **확정** | 근거 1줄 | 집행 |
|---|---|---|---|---|
| **J-0** | 세션 루트 | **`30 CoLAB-v2` 로 이동** | 훅이 레포 이력에 들어가야 「코드로 강제」가 성립하고 humanize/presentation 21개가 후보에서 자동 소거된다 | P-E 착수 전 (0-3) |
| **J-1** | `40 COLAB-기획/30_적용완료` | **활성화** | 폐지하면 D22 기획 드리프트를 red 로 잡는 지점이 사라진다 | P-C |
| **J-2** | claude-mem | **비활성** | 최근 30일 사용자 주도 호출 0건(실측 — 아래 계수표) | **완료 P-T** |
| **J-3** | humanize/presentation 자산 | **형제 폴더 `10_Humanize-Presentation/.claude` 로 이동** | J-0 이행 전 구간에서도 S1 이 즉시 내려간다(이동 후엔 자연 소거와 중복이나 무해) | **완료 2026-09-06** |
| **J-4** | `/code-review ultra` 주기 | **배포 회차당 1회**(병합 직전) | 매 병합은 회당 $5~25, 회차 1회면 비용 1/n 이고 검출 시점이 여전히 병합 전이다 | 회차 운영 규약 |
| **J-6** | codex 플러그인 | **비활성** | 최근 30일 호출 0건(실측) | **완료 P-T** |
| **J-8** | 설계 문서 위치 | **`docs/superpowers/specs/`** | 레포 이력에 귀속되어야 리뷰·롤백 대상이 된다 | **완료 — 이 문서** |
| **J-9** | 훅 등록 위치 | **`.claude/settings.json` 커밋 + `COLAB_HOOKS=0` 킬스위치를 README 에 명시** | 훅이 팀에 함께 가되 환경변수 하나로 무력화된다(훅은 층 간 병합이라 개인 훅과 공존) | P-G |
| **J-10** | `effortLevel: high` 스코프 | **프로젝트 스코프** | 글로벌은 humanize·발표자료 등 전 프로젝트 비용이 같이 오른다 | **완료 — 이 커밋 `.claude/settings.json`** |
| **J-11** | `결정서_Ted_*.md` | **폐지 · intent 로 일원화** | 판정 근거·확인 문장·재개봉 표식이 한 파일에 모이고 〈N〉 이 역링크로 가리킨다. 기존 4건은 보존, 신규 회차부터 | P-S |
| **J-12** | `intent/` 위치 | **레포 안 `dev-package/intent/`** | 커밋·게이트·〈N〉 역링크 대상이 되고 레인이 같은 트리에서 읽는다. 기획자 원본 무수정은 참조로 유지 | P-S |

(J-5·J-7 은 v2 에서 설계자 결정으로 하향되어 이 표에 없다 — 아래 「설계자 결정」 절.)

### J-2 / J-6 을 기억이 아니라 계수로 판정한 방법 (지적 7 수용)

**v1 명령은 결함이 있었다** — 세션 로그(`.jsonl`)에는 실제 호출(`tool_use` 블록)뿐 아니라 매 세션마다 주입되는 도구 정의 목록도 들어있어, 단순 `grep -rho "도구이름"` 은 정의 목록까지 계수해 모든 도구가 ~2,452건으로 잡혔다(호출 0건이어도 동일). 아래 v2 명령은 `"name":"..."` / `"skill":"..."` JSON 필드 형태로만 매칭해 실제 호출·스킬 발동만 센다.

```bash
cd ~/.claude/projects
# 실제 호출(tool_use 블록)만 계수 — 도구 정의 목록은 제외됨
find . -name '*.jsonl' -mtime -30 -print0 | xargs -0 grep -ho '"name":"mcp__plugin_claude-mem_mcp-search__[a-z_]*"' | sort | uniq -c | sort -rn
find . -name '*.jsonl' -mtime -30 -print0 | xargs -0 grep -ho '"skill":"\(claude-mem\|codex\|understand-anything\|superpowers\|feature-dev\|ralph-loop\|frontend-design\):[a-z-]*"' | sort | uniq -c | sort -rn
```
판정 규칙 — 최근 30일 호출 **0회면 비활성**, 1~2회면 「그때 뭘 했는지」를 확인한 뒤 판정, 3회 이상이면 유지.

**실측 결과 (2026-09-06, 최근 30일, 세션 로그 1,680개)**

| 항목 | 호출/발동 | 판정 |
|---|---|---|
| claude-mem (mcp) | timeline 1, get_observations 1 (오늘 워크플로 측정 서브에이전트의 가용성 샘플링, 사용자 주도 사용 0) | 비활성 |
| claude-mem:mem-search 스킬 | 0 | 비활성 |
| codex | 0 | 비활성 |
| understand-anything | 0 | 비활성 |
| feature-dev | 0 | 비활성 |
| ralph-loop | ralph-loop 1, cancel-ralph 1 | 비활성 |
| frontend-design | 1 | 비활성 (UI 작업 시 재활성) |
| superpowers | brainstorming 3(1 은 당일), systematic-debugging 1 | 설계대로 플러그인 비활성 + 5스킬 vendoring 유지 |

### 설계자 결정 (Ted 판정 불요 — v1 J-5·J-7 을 여기로 내림)

| 항목 | 결정 | 이유 |
|---|---|---|
| `mattpocock-skills` 도입 | **3종 한정 vendoring**(`grilling`·`grill-me`·`to-spec`) — 플러그인 전면 설치는 미도입 유지 | v2 의 「미도입」을 갭 G1·G3 근거로 개정. 라운드 파일이 spec·plan·부트스트랩 3역을 겸하면서 설계 근거가 먼저 잘렸고, 3종은 이슈트래커 비의존이라 〈N〉 원장과 경쟁하지 않는다. S1 은 vendored 8 로도 ≤20 |
| `brainstorming` 채택 | **미채택**(P-S 이후 재판정) | grill-me 와 기능 중복 · 1문1답이 batch-questions 규율과 충돌 · 자동 발동 유도가 명시 호출 정책과 충돌 |
| intent 승인 후 취급 | **개정 금지·신규 발행** | 플레이북 명시 규칙 아님 **[추론]**(K 미검증 11). 「한 패치보다 넓은 것은 새 intent 로」 + spec 재작업 후행지표 계측에서 유도 |
| 병렬 레인 정책 | **직렬 1개 유지**, P-G 완료 후 오케스트레이터가 완화안을 제안 | 2026-09-05 에 이미 판정된 사항 — 재개봉하지 않는다 |
| 글로벌 humanize 12 에이전트 | archive 이동 | 본진과 6건 이름 중복 = 순수 중복 |
| superpowers | 플러그인 비활성 + 5스킬 vendoring | MIT. 상시 게이트가 오케스트레이터 원칙과 충돌 |
| understand-anything / ralph-loop / claude-md-management / frontend-design / feature-dev | 비활성 | 사용 이력 없음, S1 최대 기여자 |
| `migration-reviewer` / `merge-prep` 에이전트 | 만들지 않음 | 전자는 advisor ② 체크리스트, 후자는 실체가 스크립트 2개 |
| verifier 별도 에이전트 | 두지 않음 | advisor ② 가 fresh-context 검증을 수행 |
| 자율 블록 배치 | `lane-worker`·`researcher` 만 | 메인·advisor 는 human-in-the-loop / 비가역 인접 |
| 에이전트 스코프 | 전부 프로젝트 `.claude/agents/` | 플러그인 에이전트는 `hooks`·`permissionMode` 무시 |

---

## K. 검증 결과와 미검증 사항

### 검증 완료 (문서 인용)

| | 질문 | 결과 | 인용 |
|---|---|---|---|
| **V1** | `.claude/rules/*.md` · 하위 CLAUDE.md 의 로딩 지점 | **부분 확인** — launch 로딩은 cwd 와 그 **상위** 디렉터리만. 하위 폴더의 CLAUDE.md·rules 는 **그 폴더 파일을 읽을 때 지연 로딩**. `settings.json`·`agents/`·`hooks` 는 하위 폴더 스코프가 **아예 없다**(설정 3층: user/project/local) | "loads `CLAUDE.md` … from your current working directory and every directory above it" · "files in subdirectories … **are included when Claude reads files in those subdirectories**" · "Rules without `paths` frontmatter are loaded at launch with the same priority as `.claude/CLAUDE.md`" · "rules that load on demand, including … rules in nested `.claude/rules/` directories" |
| **V2** | `SubagentStart`/`SubagentStop` matcher 가 에이전트 타입명인가 | **확인** — 맞다. `lane-worker`·`researcher` 로 직접 매칭 가능 | matcher 표: "`SubagentStart` \| agent type", "`SubagentStop` \| agent type" / 값 예시 "general-purpose, Explore, Plan, **custom agent names**, or plugin-scoped names like `^my-plugin:reviewer$`" |
| **V3** | `WorktreeCreate` 발동 시점·범위 | **부분 확인** — `isolation:"worktree"` 에서도 발동하지만 **생성을 대체(replace)** 하는 훅이지 생성 후 setup 훅이 아니다. 비영 종료면 워크트리 생성 자체가 실패 | "When a worktree is being created via `--worktree`, `isolation: \"worktree\"`, or for a background session. **Replaces default git behavior**" · "`WorktreeCreate` fails creation on any nonzero exit no matter what your JSON says" → **env setup 을 여기 넣지 않는다**. H2(`SubagentStart`)로 간 것이 옳다 |
| **V4** | 프로젝트 `settings.json` 공유 여부 | **확인** — `.claude/settings.json` 은 커밋 대상(팀 공유), `.claude/settings.local.json` 은 gitignore. 훅은 층 간 **병합** | "`.claude/settings.json` \| Single project \| **Yes, can be committed to the repo**" · "`.claude/settings.local.json` \| … \| **No, gitignored**" · "Hook entries **merge across settings levels** rather than replacing each other" |

부수 확인 — 서브에이전트 frontmatter 에 `effort`(low/medium/high/xhigh/max)·`isolation`(worktree)·`skills`·`maxTurns`·`disallowedTools` 필드가 실재한다(sub-agents 문서 필드표). CLAUDE.md 권고 크기 "target under 200 lines".

### 미검증 (이행 중 확인)

1. `work-items.yaml` custom merge driver 가 572KB·140항목에서 실용 속도인지 → P-G 에서 실측.
2. `effortLevel: high` 의 실제 비용 증가폭 → P0 의 S4 로 전후 비교.
3. Fable 5.1 자율 블록을 `lane-worker` 에 넣었을 때 advisor 게이트②를 우회하려는 경향 → P-A 후 레인 2회차까지 관찰.
4. superpowers 6.3.0 설치본이 상류와 동일 스킬 세트인지 → P-S 에서 원문 대조.
5. `/code-review ultra` 의 500파일·8,000라인 상한이 CoLAB 회차 diff 를 넘지 않는지.
6. `worktree-setup.sh` 의 venv **재생성** 소요시간이 레인 스폰 지연으로 체감되는지(복사 불가는 확정) → P-E 에서 측정.
7. `SubagentStart` 훅의 stdout 이 서브에이전트 컨텍스트에 주입되는지, 아니면 오케스트레이터에만 보이는지 → P-E 5줄 테스트 훅으로 확인.
8. J-2/J-6 계수 명령이 실제 세션 로그 포맷(`.jsonl`)에서 유효한지 → 0 이 나오면 「미사용」이 아니라 「패턴 불일치」일 수 있으므로 먼저 아무 문자열(`Bash`)로 grep 해 히트가 나오는지 대조한다. 2026-09-06 실측 때 이 대조를 수행했고 히트가 나왔다.
9. 플레이북 원문 전체를 직접 읽지 못함 — **WebFetch 가 요약 모델을 경유**한다. 4회 분할 추출로 교차 확인하고 인용은 짧은 직접 인용만 실었으나, **단계표·역할표의 표 형식은 요약 모델이 구성한 것일 수 있다**.
10. 단계 제목 표기 불일치(1회차 "Stage 1: Plan" / 3회차 "Stage 1 — Plan") — 표기 인용 시 확인. `intent/` 폴더 이름은 본문·transcript 가 일치하나 **템플릿 파일·예제 레포 링크는 발견 못 함**.
11. **intent 승인 후 개정 규칙은 원문에 없다.** 「개정 금지·신규 발행」은 두 근거(한 패치보다 넓으면 새 intent / spec 재작업 후행지표)로부터의 **추론**.
12. **플레이북은 ADR 을 언급하지 않는다.** 「〈N〉 원장 = ADR 역할」은 mattpocock 쪽 개념을 우리 원장에 매핑한 **우리 해석**이다.
13. mattpocock SKILL.md 원문도 같은 요약 경유 — `grill-with-docs` 의 intent.md 실제 섹션 구성 미확인. L-1 은 플레이북 정의(문제·결과·영향·제약·미해결) 우선, 설계트리·확인절만 `grilling` 에서 차용. 레포 스타 수 "252.8k" 도 요약 아티팩트로 판단(vendoring 은 파일 복사라 판정 무관).
14. `to-spec` 템플릿 항목명·순서(Problem/Solution/User Stories/Implementation/Testing/Out of Scope/Further Notes)는 **근사**. 채택 순서 인용의 "any clay play" 는 추출 오류 가능성 — **인용으로 쓰지 말 것**.
15. playbook-gap 이 미대조로 남긴 「F 표 수정 ↔ C·D 절 충돌」은 **v3 에서 해소** — 신설 2단계는 훅을 0개 추가하고 게이트 로직을 건드리지 않는다(훅 7 · 게이트 JSON 계약 불변).

### 반론 (advisor 지적 중 부분 반박 1건)

- **지적 1 「하위 폴더 CLAUDE.md 는 파일 접근 시에만 로드」는 맞으나, 「B-2 의 어떤 것도 로드되지 않는다」는 과장이다.** 문서상 `30 CoLAB-v2/CLAUDE.md` 와 `30 CoLAB-v2/.claude/rules/*.md` 는 **그 아래 파일을 읽는 순간 실제로 로드된다**(nested rules 도 on-demand 로 명시). 로드되지 않는 것은 **`settings.json`(훅·permissions·effortLevel)과 `agents/`** 다. 결론(J-0 을 세워야 한다)은 동일하므로 수용했고, 판정 근거 대조표에 반영했다.

---

## L. 아티팩트 템플릿 (playbook-gap 5절 최종안 — 본문 원문 그대로, 행 예산 위해 절 사이 빈 줄만 제거)

### L-1. `dev-package/intent/<YYYY-MM-DD>-<주제>.md`

```markdown
# Intent: <한 줄 제목>
메타 — 발의자: <이태헌 | 조성진 | Ted | agent(전수 red 로그)> · 작성 2026-MM-DD · 승인 <날짜 | 미승인>
## 문제
- <현상 1~3행. 코드가 아니라 사용자·운영 관점>
## 원한 결과 (proposed outcome)
- <달성 시 무엇이 달라지나. 검증 가능한 문장으로>
## 영향 범위
- 사용자 / 화면:
- 서비스 · 스키마 · 계약:
- 계약 파괴 여부: 예(Ted 서명 필요) / 아니오
## 제약
- <기술·기획·일정. CLAUDE.md §2·§3 불변 규칙 중 걸리는 것>
## 설계트리 (grill-me 결과)
- Q1 <질문> → A <답> (권장안 수용 / 반대: <사유>)
- Q2 <질문> → A <답>
  - Q2a <종속 질문> → A <답>
## 미해결 질문
- <남은 것. 없으면 「없음」>
## 범위 밖 (명시 제외)
- <항목>
## 확인
- 프론티어 공집합 확인: <날짜>
- Ted 확인 문장(원문 그대로): "<...>"
- 재개봉 금지: 예 / 아니오
## 참조
- 기획 원본: `40 COLAB-기획/10_적용전/<파일>` (무수정)
- spec: `dev-package/prd/specs/<회차>.md`
- 라운드 파일: `dev-package/prd/rounds/R-*.md`
- 결정: 〈N〉 (병합 시 기입)
```

### L-2. `dev-package/prd/specs/<회차>.md`

```markdown
# Spec: <회차·제목>   ← intent.md 로부터 합성. 재인터뷰 없음
출처 intent: `dev-package/intent/<파일>` (승인 <날짜>)
## 문제 진술
- <intent 문제절을 개발 언어로 1~3행>
## 해법 개요
- <사용자 관점 서술. 「사용자 관점 동일 행위는 기존 흐름 재사용」 원칙 적용>
## 사용자 스토리
1. <행위자>로서 <기능>을 원한다, <이유> 때문에.
2. ...
## 구현 결정
- 모듈 · 인터페이스:
- 스키마 · 마이그레이션: (Alembic 포함 시 revision 체인 명시 → advisor ② 항목)
- API 계약: 파괴 / 비파괴
- 코드 조각은 산문보다 결정을 정확히 담을 때만 (상태기계·타입 형태)
## 시험 결정
- 외부 행위 기준 검증 항목:
- 재사용 seam: / 신설 seam:
- 해당 서비스 단독 게이트 이름:
- green-by-skip 방지: 대상 0건이 아님을 무엇으로 보이나
## 정책 대조 (작성 시점 제약)
- CLAUDE.md §2 도메인 / §3 불변 규칙 중 저촉 항목: 없음 / <항목>
- 계약 동결 해제 필요: 예(Ted 서명) / 아니오
## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | <ELI5 로 풀어 쓴 항목> | <선택지> | <선택지> | ⓐ |
## 범위 밖
- <intent 에서 승계 + 확장>
## 산출 계획
- 라운드 파일: `prd/rounds/R-*.md` (≤300행, 이 spec 을 첫 줄에서 링크)
- 예상 레인 수: <n> (진짜 독립일 때만 병렬, 기본 직렬 1)
```

---

## M. 조사 산출물 (근거 원본)

`dev-package/reports/harness/2026-09-06/` — **조사 8건**(아래 표). 이 스펙의 모든 수치·인용의 출처.
⭑ **⟨증보 2026-09-06⟩ 같은 폴더에 이행 실행·검증 기록 6건이 더 있다** — `08-memory-migration.md`(P-M) · `09-agents-verification.md`(P-A) · `10-skills-vendoring.md`(P-S) · `11-merge-guards-verification.md`(P-G) · `12-gate-json-verification.md`(P-J) · `13-planning-applied-wiring.md`(P-C 부분). **조사와 다른 성질이다** — 조사는 설계의 입력이고 이 여섯은 집행의 증적이다. 색인은 그 폴더 `README.md`.

| 파일 | 내용 |
|---|---|
| `00-brief.md` | 착수 브리프 — 결함 D1~D22, 요구 F1~F21 |
| `01-inventory.md` | 하네스 자산 실측 인벤토리(에이전트·스킬·플러그인·훅·메모리) |
| `02-workflow-profile.md` | 실제 세션 로그 기반 워크플로 프로파일 |
| `03-market-survey.md` | 외부 하네스·에이전트 운영 사례 조사 |
| `04-grill-me.md` | mattpocock 스킬 계열 조사(`grilling`·`grill-me`·`to-spec` 외) |
| `05-playbook-gap.md` | 「AI-native SDLC 플레이북」 대비 갭 16건 + 아티팩트 템플릿 초안 |
| `06-advisor-review-gate1.md` | advisor 게이트① 계획 검토 지적 18건 |
| `07-design-v3.md` | 설계 v3 원본(이 스펙의 직전 판본) |
</content>
