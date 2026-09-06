# AI-native SDLC 플레이북 대조 · 갭 분석

조사 2026-09-06. 1차 출처 = Anthropic 「The AI-native SDLC playbook」(claude.com/blog/the-ai-native-sdlc-playbook, WebFetch 4회 분할 추출).
2차 = transcript_ko/en(Tech Bridge, 2026-09-04) · grill-me.md · design-v2.md · workflow-profile.md.
인용은 원문 짧은 직접 인용(영문)만. 요약 문장에는 인용부호를 붙이지 않았다.
`[미검증]` = 7절.

---

## 1. 플레이북 요지

### 1-1. 원칙

- 병목이 코드에서 사람 게이트로 옮겨졌다는 진단이 출발점 — "Code is no longer the bottleneck".
- 사람은 판단이 필요한 결정에 남는다 — "Humans remain accountable for every decision that requires judgment."
- 직무 분리가 구조로 강제된다 — "The agent that wrote the code has no way to approve it."
- 각 단계는 버전관리에 아티팩트 1개를 쓰고 끝난다 — "Each stage ends by writing one to version control" · "The chain of commits is also the audit trail."

### 1-2. 6단계 표

| 단계 | 산출 아티팩트 | 쓰는 이 | 승인·게이트 | 원문 인용(짧게) |
|---|---|---|---|---|
| Stage 1 Plan | `intent.md` (`intent/` 폴더) | originator 가 Claude 와 대화 → **에이전트가 초안 작성** | product owner 검토·수정 후 커밋. 승인은 머지/리뷰 종료로 기록 | "The product owner reviews and corrects the agent-written intent.md before it is committed." |
| Stage 2 Design | `spec.md` (intent.md 옆에 커밋) | **Claude 가 작성** | product owner 검토(작성 안 함), 플래그 항목은 policy owner 가 먼저 해소 | "The product owner reviews that spec, but doesn't write it." · "Commit spec.md alongside intent.md." |
| Stage 3 Build | `plan.md` + diff | Claude(plan mode) 작성, 엔지니어가 심문·수락 | plan 승인 전 코드 작성 차단(훅). 계획 이탈 시 같은 커밋에서 plan.md 갱신 | "Work starts with a written plan that Claude produces in plan mode, where it can read the codebase without changing anything." · "Commit the approved plan as `plan.md`." |
| Stage 4 Test | 시험·빌드·스크린샷 diff 결과 | Claude 자기검증 → verifier 서브에이전트(별도 세션) | 사람이 보기 전에 피드백 루프 통과 | "Give Claude a way to verify its own work, whether tests, a build, or a screenshot diff." · verifier: "Do not fix anything; report only" |
| Stage 5 Deploy | 리뷰 붙은 PR · 병합본 | Claude 가 리뷰 패스 실행, code owner 가 승인 | branch protection + 훅. 프로덕션은 지명 승인 | "All PRs get an identical set of review passes, with findings ranked by severity." · "A hook can also ask, pausing the action until a specific person approves." |
| Stage 6 Maintain | **새 `intent.md`** | 결정론적 감시 스크립트가 이상 탐지 → Claude 가 진단문을 intent.md 로 기술 | service owner 가 triage. 1σ 기록 / 2σ 읽기전용 진단 / 3σ 행동 허용 | "The agent writes its diagnosis as `intent.md` in the Stage 1: Plan format" · "From there the finding goes through the pipeline like anything else." |

### 1-3. intent.md 정확한 정의

| 항목 | 플레이북이 말하는 것 |
|---|---|
| 무엇을 담나 | 문제 · 제안하는 결과(proposed outcome) · 영향받는 사용자/시스템 · 제약 · 미해결 질문 |
| 취지 | 발의자의 말로 **한 번에** 포착해 버전관리 아티팩트로 만든다 — "capture once, in the originator's own words, as a version-controlled artifact the next stage can act on" |
| 누가 쓰나 | originator 가 Claude 와 브레인스토밍, **초안은 에이전트가 씀**. originator 는 오해를 교정 |
| 발의자 자격 | 부서 무관, 전문가 아니어도 됨. 고객 문의·프로세스 개선도 발의가 된다 (transcript 03:29~03:49) |
| 대화 방식 | 분석가가 물을 것을 Claude 가 묻는다 — "Claude asks the questions an analyst would ask: scope, users, constraints, and what success looks like." |
| 무엇이 **아닌가** | 명시적 부정문은 원문에 없음. 대신 대비로 규정 — 종전에는 아이디어가 백로그를 거쳐 제품팀원을 설득해야 기록됐다. 즉 **위원회 통과 후 PM 이 쓰는 정식 요구사항 문서가 아니다**. 또한 spec 이 아니다(구현 결정은 Stage 2 로) |
| 어디 사는가 | 제품 레포 안 `intent/` 폴더가 가장 단순한 형태. "A dedicated intent repo is only worth the overhead when intent spans many repositories." |
| 시간에 따른 갱신 | **승인 후 개정 규칙은 원문에 없다.** 대신 ⑴ 한 PR 로 안 되는 것은 새 intent.md 로 — "For anything wider than one patch… write it up as `intent.md`" ⑵ 첫 plan.md 커밋 이후의 spec 변경은 요구사항 재작업의 후행지표로 계측. ⇒ **개정이 아니라 신규 발행이 기본형** |
| 에이전트가 스스로 만드는 경우 | Stage 6. 감시 breach·티켓·Slack 메시지·스케줄이 사람 없이 Claude 를 기동 → 로그/티켓을 근거로 스스로 intent.md 를 생성 (transcript 13:43 "generating its own intent.mmd file based on the logs that it's discovered or whatever ticket or message it's been sent"). Claude Tag 경로에서는 작은 수정은 PR, 큰 것은 intent.md |
| spec/plan 과의 관계 | intent(무엇을 왜) → spec(요구사항·설계, 조직 skill 이 제약으로 적용) → plan(파일·순서·증명 기준). "The file pair records what was asked for and what was decided." |

### 1-4. 역할

| 역할 | 담당 |
|---|---|
| originator | intent.md 발의·교정 |
| product owner | intent 승인 · spec 검토(작성 금지) · 플래그 라우팅 · build 진행 여부 |
| policy owner | spec 의 플래그 항목 해소, 자기 도메인 skill 변경 승인 |
| engineer | plan 심문·수락, 피드백 루프, 병렬 세션 조종 |
| tech lead | 고위험 spec, 리뷰 정책, skill 변경 서명 |
| code owner | PR 승인(전 줄이 아니라 intent·위험 기준) |
| service owner | 감시 지표·대응 티어 선정, 발견 triage |

### 1-5. 채택 순서

- 화살표가 들어오지 않는 play 부터 — "Start with any clay play—nothing points into it, so it needs nothing first."
- 가속 전에 게이트 — PR 리뷰 루프와 승인 훅이 CI/CD 자동화보다 앞선다. Stage 6 자율 루프는 롤백 경로가 증명된 뒤.

---

## 2. 대조표

범례: **있음** = 동등물이 코드/문서로 존재 · **부분** = 관행으로만 있거나 다른 그릇에 섞여 있음 · **없음**.

| 플레이북 단계 | mattpocock | superpowers | 우리 현행(workflow-profile A) | design-v2 F 표 | 판정 |
|---|---|---|---|---|---|
| S1 Plan / 발의 포착 | `grill-me`·`grilling` (설계트리·프론티어·확인 정지) | `brainstorming` (1문1답) | A-1 #1 기획 문서 수령(`10_적용전` 원본 무수정) — **대화형 발의 포착 없음** | 1 기획 수령 | **부분** |
| S1 산출 `intent.md` | `grill-with-docs` → intent.md·CONTEXT.md·ADR | 세션 내 design doc(파일 아님) | 없음 — Ted 판정이 `결정서_Ted_<날짜>.md` 로 사후 기록될 뿐 | 없음 | **없음** |
| S1 승인 게이트 | 「shared understanding 확인 전 무행동」 | 암묵 | A-1 #3 Ted ⓐ/ⓑ + 「재개봉 금지」 | 3 Ted 판정 | **있음**(단 발의 아닌 판정만) |
| S2 Design `spec.md` | `to-spec`(재인터뷰 없음, 고정 템플릿) | `writing-plans` 에 흡수 | 라운드 파일 `prd/rounds/R-*.md` ≤300행 + `PRD-*.md` | 4 라운드 파일 | **부분** |
| S2 정책 skill 을 spec 제약으로 | `domain-modeling`·`codebase-design` | 없음 | CLAUDE.md §2·§3 + 게이트가 사후 강제 | — | **부분**(사후 판정, 작성시점 제약 아님) |
| S3 Build `plan.md` | `to-tickets`·`implement` | `writing-plans`·`executing-plans` | 라운드 파일이 plan 역할 겸함. 별도 plan.md 없음 | 4·7 | **부분** |
| S3 plan 심문 게이트 | grilling 재사용 | plan mode | advisor 게이트 ① | 5 advisor ① | **있음** |
| S3 격리 병렬 | — | `using-git-worktrees` | `Agent isolation:"worktree"`, 레인 최대 7 | 7 구현 | **있음** |
| S4 Test 자기검증 | `tdd`·`diagnosing-bugs` | `test-driven-development`·`systematic-debugging` | 서비스 단독 게이트 연속 green | 7 | **있음** |
| S4 verifier 별도 세션 | `code-review`(사양 대조축) | `verification-before-completion` | advisor ② + 전수 `run.sh all -j 4` | 8 advisor ② | **있음** |
| S4 evals 를 CI 에서 상시 | 없음 | 없음 | `gates/run.sh` 53 + selftest 짝 + Actions 8잡 | D절 JSON | **있음**(플레이북보다 강함) |
| S5 Deploy PR 게이트 | `code-review` | `finishing-a-development-branch` | 병합=오케스트레이터 전용, PR 리뷰는 `/code-review ultra` 회차 1회 | 9.5·10 | **있음** |
| S5 직무 분리 | — | — | 레인은 병합 불가(H3 열거식 잠금) | 10 | **있음** |
| S5 프로덕션 지명 승인 | — | — | advisor ③ + Ted 서명(계약 파괴 시) | 12 advisor ③ | **있음** |
| S6 Maintain 감시→진단 | — | — | `deploy_doctor` 14/14 는 배포 시점만. **상시 지표 감시 없음** | 11 | **없음** |
| S6 에이전트가 intent.md 생성 | — | — | 없음 | 없음 | **없음** |
| 아티팩트 체인 = 감사 추적 | ADR | — | 〈N〉 원장 298건 + 커밋 문면 | 10 | **부분**(체인 아닌 원장) |
| 리뷰 결과가 CLAUDE.md 로 환류 | — | — | 메모리 33건(교정 16) — 파일 아닌 메모리 | G절 rules 이관 | **부분** |
| 계획 이탈 시 문서 동기화 | — | — | 없음 | 없음 | **없음** |

---

## 3. 갭 목록

| # | 갭 | 플레이북 근거 | CoLAB v2 에서 왜 문제인가 | 최소 변경 |
|---|---|---|---|---|
| G1 | **발의 심문(discovery) 단계 부재** | Stage 1 은 대화로 시작. "Claude asks the questions an analyst would ask" | 현행은 기획 문서를 받아 서브에이전트가 조사→PRD→Ted 가 ⓐ/ⓑ 판정. 질문 설계가 매번 즉흥이라 **미결이 판정 시점까지 살아남는다** — 2026-09-05 에 미결 16건이 한 번에 몰렸고 rev2 에서 또 3건. `explain-before-asking-judgment`·`batch-questions-product-framed` 두 메모리가 이 결핍의 흉터 | `grilling`+`grill-me` vendoring, 라운드 파일 작성 **전** 1회 실행. 종료 기준 = 프론티어 공집합 + Ted 확인 문장 |
| G2 | **intent.md 라는 지속 아티팩트와 그 집 없음** | "capture once, in the originator's own words, as a version-controlled artifact" · `intent/` 폴더 | 발의 근거가 3곳으로 흩어짐 — `40 COLAB-기획/10_적용전`(기획자 원본, 무수정) · `결정서_Ted_*.md` · 메모리 `ted-decisions-*` 4건. 「왜 이렇게 하기로 했나」를 다음 세션이 재구성 못 해 **재개봉 금지 선언으로 사람이 틀어막고 있다**. F6(부트스트랩 1파일)과도 충돌 — 근거가 라운드 파일에 안 들어옴 | `dev-package/intent/<날짜>-<주제>.md` 신설. 기획자 원본은 그대로 두고 intent 가 **참조만** 한다(원본 무수정 규칙 유지) |
| G3 | **spec.md 가 라운드 파일과 미분화** | "Commit spec.md alongside intent.md. The file pair records what was asked for and what was decided." | 라운드 파일 1개가 지금 spec·plan·부트스트랩 3역을 겸한다. ≤300행 상한(F6·D7) 안에서 셋을 다 담으려니 **설계 근거가 먼저 잘린다**. R-B 4분할 예정도 같은 압력 | 라운드 파일을 **spec 의 실행 뷰**로 재정의. spec.md 는 회차 폴더에 두고 라운드 파일이 첫 줄에서 링크. 상한은 라운드 파일에만 적용 |
| G4 | **〈N〉 원장이 ADR 역할을 하는데 결정 근거가 안 붙음** | 아티팩트 체인이 감사 추적 · "All artifacts note the record ID" | 〈N〉 298건이 `PLAN-SoT.md` 1.30MB 에 누적. 동시 세션 3개가 같은 번호를 발급해 2회 재번호(D3). 번호는 있는데 **그 결정을 낳은 intent/spec 으로 가는 링크가 없어** 원장을 열어도 「왜」가 안 나온다 | 〈N〉 항목에 `intent:`·`spec:` 경로 2필드 추가. `renumber-decisions.sh`(P-G) 가 어차피 전 파일을 건드리므로 같은 스크립트에서 처리 |
| G5 | **검증 시점의 intent 대조 없음** | "When implementation departs from the plan, update `plan.md` in the same commit" · verifier 는 "report only" | advisor ② 는 게이트 결과와 「main 과 동일」 금지만 본다. 구현이 **원 의도에서 벗어났는지**는 아무도 안 본다. D22(기획-코드 드리프트)가 상시 문제이고 rev2 판정-1(「목업에 없다 ≠ 걷어라」)이 그 판례 | advisor ② 체크리스트에 1행 추가 — 「intent.md 의 proposed outcome 중 미달·초과 항목을 열거하라」. 훅 불요 |
| G6 | **티켓·로그에서 에이전트가 발의를 못 만든다** | Stage 6. 감시 스크립트가 breach 탐지 → Claude 가 intent.md 작성 → 파이프라인 재진입 | 현행 감시는 배포 시점 `deploy_doctor` 14/14 뿐. 그 사이 회귀는 다음 회차 전수까지 안 보인다. `30_적용완료` 0건 = **환류 루프가 설계돼 있으나 안 돎**(B절 실측) | 신규 감시 인프라는 지금 만들지 않는다. 대신 **전수 red(판정) 이 나오면 그 로그로 intent 초안을 쓰는 것**을 gate-runner/researcher 산출 규격에 넣는다. 1σ/2σ/3σ 티어는 J-1 활성 뒤 재판정 |
| G7 | 정책이 spec **작성 시점** 제약이 아니라 사후 게이트 | "The organization's skills are applied as constraints on the spec." | 게이트 53개는 코드가 나온 뒤에만 판정. 계약 파괴 변경이 구현 끝까지 갔다가 Ted 서명(19차 승인)으로 되돌아오는 왕복이 발생 | to-spec 스킬 본문에 CLAUDE.md §2·§3 불변 규칙과 계약 파괴 판정 절을 인용으로 박는다. 새 게이트 불요 |
| G8 | 리뷰 환류처가 메모리 | "When a review flags a mistake for the second time, the correction goes into `CLAUDE.md`" | 교정형 메모리 16건이 검색 의존이라 유실 위험(G절이 이미 지적) | design-v2 G절 `rules/colab-rules.md` 이관으로 **이미 해소 예정**. 갭이라기보다 미이행 |

---

## 4. 개정 파이프라인 제안 (단일 권고안)

```
발의 ──▶ grill-me ──▶ intent.md ──▶ to-spec ──▶ spec.md ──▶ 라운드 파일 ──▶ 레인 실행
 │         (메인)      (Ted 승인)     (재인터뷰X)   (advisor①)   (≤300행)    (worktree/TDD)
 │                                                                              │
 └◀── 새 intent.md ◀── HANDOFF/ELI5 ◀── 병합·〈N〉 ◀── advisor② ◀── verification ◀┘
        (S6 환류)                        (ADR 링크)   (intent 대조)
```

| # | 단계 | 주체 | 산출 | 종료·게이트 조건 |
|---|---|---|---|---|
| 1 | 발의 | 기획 문서 / Ted / 전수 red 로그·티켓 | 발의 트리거 기록 | 원본은 `40 .../10_적용전` 무수정 |
| 2 | **grill-me** | 메인 세션(위임 안 함 — Ted 가 직접 답해야 함) | 라운드별 번호 질문 + 각 권장 답 | 프론티어 공집합 **그리고** Ted 확인 문장. 확인 전 무행동 |
| 3 | **intent.md** | 에이전트 초안 → Ted 교정 | `dev-package/intent/<YYYY-MM-DD>-<주제>.md` | Ted 승인 = 커밋. 승인 후 **개정 금지, 신규 발행만**(플레이북 원칙) |
| 4 | **spec.md** | `to-spec`(재인터뷰 없음) | `dev-package/prd/specs/<회차>.md` | advisor ① 계획 검토 |
| 5 | 라운드 파일 | 메인 세션 | `prd/rounds/R-*.md` ≤300행, 첫 줄에 spec 링크 | 부트스트랩 단일 파일 규칙(F6) |
| 6 | plan | `writing-plans` | 라운드 파일 §구현순서에 흡수 | 파일·순서·증명 기준 명시 |
| 7 | 레인 실행 | `lane-worker`(worktree, TDD) | 코드 + 시험 | 서비스 단독 게이트 연속 green |
| 8 | 검증 | `verification-before-completion` + **intent 대조** | 게이트 요약 JSON + 미달/초과 항목표 | 증거 없는 완료 주장 금지 |
| 9 | advisor ② | `advisor`(fable) | 수용 검토 | 「main 과 동일」 금지 + intent 대조 결과 첨부 |
| 10 | 병합·〈N〉 | 오케스트레이터 전용 | main ff + §9 〈N〉 (`intent:`·`spec:` 필드 포함) | 전수 `all -j 4` FAIL_JUDGMENT=0, max+1 재실측 |
| 11 | HANDOFF/ELI5 | 세션 종료 | HANDOFF ≤5줄 + ELI5 자립형 HTML | 내부 용어 grep 차단(F14) |
| 12 | 환류 | 오케스트레이터 | `30_적용완료` 이동 · 잔여 결함은 **새 intent.md** | J-1 활성 시 |

### 4-1. 스킬 조달처

| 스킬 | 출처 | 채택 | 개조 |
|---|---|---|---|
| `grilling` | mattpocock (MIT) | **채택** | 「finding facts is your job」 규칙 유지. 권장 답 제시 방식은 Ted ⓐ/ⓑ 문법으로 치환 |
| `grill-me` | mattpocock | **채택** | `disable-model-invocation: true` 유지 — 명시 호출 전용(graphify 선례와 동일 규율) |
| `grill-with-docs` | mattpocock | **미채택** | CONTEXT.md·ADR 를 별도로 낳아 〈N〉 원장과 이중화. intent.md 작성 동작만 떼어 `grill-me` 뒤 단계로 |
| `to-spec` | mattpocock | **채택** | 이슈트래커·`ready-for-agent` 라벨 발행 단계 삭제. 대신 spec.md 파일 배출 + Ted ⓐ/ⓑ 매핑 절 추가 |
| `to-tickets`·`triage`·`wayfinder` | mattpocock | **미채택** | 외부 이슈트래커 전제. 〈N〉 원장·라운드 파일과 경쟁 원장이 됨 |
| `writing-plans` | superpowers | 채택(design-v2 기존) | |
| `executing-plans` | superpowers | 채택(기존) | |
| `test-driven-development` | superpowers | 채택(기존) | |
| `verification-before-completion` | superpowers | 채택(기존) | + intent 대조 절 추가 |
| `receiving-code-review` | superpowers | 채택(기존) | |
| `brainstorming` | superpowers | **미채택 — 권고** | 아래 |

### 4-2. superpowers:brainstorming 은 grill-me 이후 필요한가 — **불요(권고)**

- 기능 중복이 본질적이다. 둘 다 「모호함이 해소될 때까지 인터뷰, 그 전엔 행동 금지」로 같은 자리를 차지한다.
- 질문 방식에서 grill-me 가 우월 — 프론티어 단위 배치 질문 + 각 질문에 권장 답. brainstorming 은 엄격 1문1답이라 왕복이 늘고, 이는 **Ted 판정 왕복을 줄이라**는 기존 규율(`batch-questions-product-framed`)과 정면으로 어긋난다.
- 종료 기준이 형식적 — 프론티어 공집합 + 사용자 확인. brainstorming 은 암묵 종료라 「재개봉 금지」를 걸 지점이 없다.
- 발동 규율 — brainstorming description 은 "You MUST use this before any creative work" 로 자동 발동을 유도한다. 이 사용자의 명시호출 전용 정책(graphify 선례)과 충돌. grill-me 는 `disable-model-invocation: true` 로 정책과 일치.
- 남길 근거가 있다면 하나뿐 — 문제가 아직 「무엇을 만들지」 수준일 때. 다만 CoLAB v2 는 기획 문서가 항상 먼저 오므로 그 국면이 사실상 없다. **미채택하고, 실제로 아쉬우면 P-S 이후 재판정.**

---

## 5. 템플릿 최종안

### 5-1. `dev-package/intent/<YYYY-MM-DD>-<주제>.md` (39행)

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

### 5-2. `dev-package/prd/specs/<회차>.md` (40행)

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

## 6. design-v2 수정 목록

| # | 섹션 | 무엇을 바꾸나 |
|---|---|---|
| 1 | **F 파이프라인 게이트표** | 단계 1 앞에 **1.5 grill-me**(주체 메인 세션 / 산출 없음 / 게이트 = 프론티어 공집합 + Ted 확인) 삽입 |
| 2 | **F** | 단계 3(Ted 판정) 산출에 **`dev-package/intent/<날짜>-<주제>.md`** 추가. `결정서_Ted_*.md` 는 intent 승인 기록으로 흡수 |
| 3 | **F** | 단계 4(라운드 파일) 앞에 **3.5 to-spec → `prd/specs/<회차>.md`** 삽입. 라운드 파일 정의를 「spec 의 실행 뷰, 첫 줄에 spec 링크」로 개정. ≤300행 상한은 라운드 파일에만 |
| 4 | **F** | 단계 8(advisor ②) 차단 게이트에 「intent proposed outcome 미달·초과 항목 열거」 1행 추가 |
| 5 | **F** | 단계 10(병합+〈N〉) 산출에 「〈N〉 항목이 `intent:`·`spec:` 경로 2필드를 포함」 추가 |
| 6 | **F** | 단계 15(환류)에 「잔여 결함은 새 intent.md 로 발행」 추가. 기존 intent 개정 금지 명시 |
| 7 | **B-2 프로젝트 `.claude/`** | vendored 스킬 목록에 `grilling`·`grill-me`·`to-spec` 3종(mattpocock, MIT) 추가. superpowers 5종은 유지. `brainstorming` 은 미채택으로 명기 |
| 8 | **B-4 플러그인** | 비활성 사유 문구에 "brainstorming 은 grill-me 로 대체" 근거 1행 |
| 9 | **B-3 에이전트** | `advisor.md` 설명에 게이트 ② 체크리스트 3항(revision 체인 / 「main 과 동일」 금지 / **intent 대조**) 명시. `researcher` 산출 규격에 「전수 red(판정) 로그에서 intent 초안 작성」 추가 |
| 10 | **E 요구사항 21 대응** | F20(`30_적용완료` 환류)에 「잔여 결함 → 새 intent」 경로 추가. F13 을 advisor ② 3항 중 1항으로 재배치 |
| 11 | **H 이행 계획** | P-S(스킬 vendoring, 7번)에 grill-me/to-spec 3종 추가, 검증에 「grill-me 1회 실전 실행 후 intent.md 1건 산출」 추가. **신규 phase 불요** |
| 12 | **H** | P-G(병합 가드, 8번)의 `renumber-decisions.sh` 사양에 「〈N〉 항목 `intent:`·`spec:` 필드 보존·이동」 추가 |
| 13 | **J Ted 판정** | **J-11 신설** — intent.md 도입 시 `결정서_Ted_*.md` 를 ⓐ 폐지·intent 로 일원화 vs ⓑ 병존. 권고 ⓐ |
| 14 | **J** | **J-12 신설** — `dev-package/intent/` 위치를 ⓐ 레포 안 vs ⓑ `40 COLAB-기획` 안. 권고 ⓐ(레포 안 — 커밋·게이트 대상이어야 함, 기획자 원본은 무수정 유지) |
| 15 | **A-2 지표** | S5 신설 — 「회차당 Ted 판정 재개봉 건수」(목표 0). grill-me 도입 효과의 유일한 계측점 |
| 16 | **K 미검증** | 아래 7절 5건 이관 |

---

## 7. 미검증 목록

| # | 항목 | 상태 |
|---|---|---|
| 1 | 플레이북 원문 전체를 직접 읽지 못함 | WebFetch 가 요약 모델을 경유한다. 4회 분할 추출로 교차 확인했고 인용은 짧은 직접 인용만 실었으나, **표 형식(1-2·1-4)은 요약 모델이 구성한 것일 수 있다**. 원문에 그 표가 실제로 인쇄돼 있는지 미확인 |
| 2 | 단계 제목 표기 | 1회차 추출은 "Stage 1: Plan", 3회차는 "Stage 1 — Plan". **구두점 불일치** — 표기 인용 시 확인 필요 |
| 3 | `intent/` 폴더 이름 | 본문 인용과 transcript(02:37 "creating a folder called intent") 가 일치. 다만 **템플릿 파일이나 예제 레포 링크는 발견 못 함** — 아웃바운드 링크 목록에 intent 템플릿·예제 저장소 없음 |
| 4 | intent.md 승인 후 개정 규칙 | **원문에 없다**(4회차 확인). 「개정 금지, 신규 발행」은 ⑴ "For anything wider than one patch… write it up as intent.md" ⑵ spec 재작업 후행지표 계측, 두 근거로부터의 **추론**. 플레이북의 명시 규칙 아님 |
| 5 | ADR | 플레이북은 ADR 을 언급하지 않는다(4회차 확인). 「〈N〉 = ADR 역할」은 mattpocock 쪽 개념을 우리 원장에 매핑한 것 |
| 6 | mattpocock SKILL.md 원문 | grill-me.md 8절 caveat 그대로 승계 — `grill-with-docs` 의 intent.md 실제 섹션 구성은 미확인. 5-1 템플릿은 플레이북 정의(문제·결과·영향·제약·미해결) 우선, 설계트리·확인절만 grilling 에서 차용 |
| 7 | `to-spec` 템플릿 항목명 | 요약 경유 추출. Problem Statement/Solution/User Stories/Implementation Decisions/Testing Decisions/Out of Scope/Further Notes 순서는 근사 |
| 8 | 채택 순서 인용 "any clay play" | 원문에 다이어그램 기반 표현이 있는 것으로 보이나 **"clay" 는 추출 오류 가능성** — 색상 범례(예: 특정 색 play)를 잘못 옮겼을 수 있음. 인용으로 쓰지 말 것 |
| 9 | 우리 쪽 실측 | design-v2 D절(게이트 요약 계약)·C절(훅 6종) 본문은 이번에 열지 않음. F 표 수정 제안이 D·C 와 충돌하는지 미대조 |
