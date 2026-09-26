## PR 3 · 문서·설정 drift + Ted 결정 + 제외
- 행위자: 그룹 C = PR 3 · lane 구현 · PR 2 병합 뒤 develop 기준으로 시작. 그룹 T = Ted 결정·행동 · 에이전트는 질문·선택지만 기록하고 GitHub 설정·브랜치·형제 체크아웃·`/hooks` 신뢰를 바꾸지 않는다. 그룹 X = 이 intent 범위 밖(디자인 시스템 후속 intent).
- 재검증 기준: develop `67a03a05` · 2026-09-25. 아래 file:line 은 이 트리에서 다시 열어 확인한 값이다. 판독자 보고만 있고 다시 열지 않은 사실은 「판독 · 재현 안 함」으로 적는다.

### C1 measurement-lane 역할 본문의 「프로세스 간 뮤텍스가 없다」  (출처: R2-1 corrected · R5-governance-missed)
- 문제: `.agents/roles/measurement-lane.md:13` 이 ADR-0002 를 「첫 번째 규율」 근거로 들고 `:17-18` 에 「`gates/run.sh` 에 프로세스 간 뮤텍스가 없다」고 적는다. `.codex/agents/measurement-lane.toml:12` 도 "gates/run.sh has no cross-process mutex". 코드는 `serial` 게이트에 호스트 뮤텍스를 건다(`gates/tools/_lock.sh` `gate_host_mutex_acquire` · 커밋 `9ece9104`). `.agents/roles/lane-worker.md:52` 「게이트 대기는 호스트 뮤텍스가 한다」와 두 역할 본문이 어긋난다.
- 유지되는 것: `parallel` 게이트는 뮤텍스 밖이고 postgres 슬롯은 호스트 전역이다 → 「게이트 도는 레인은 한 번에 하나」 규율 자체는 유지. ADR-0002 는 superseded(→ ADR-0005) 이력 문서라 고치지 않는다.
- 선택지: ⓐ 전제 문장만 사실(serial = 호스트 뮤텍스 · parallel 제외 · postgres 슬롯 호스트 전역)로 교체, 규율 유지, ADR-0002 인용 옆에 superseded 표기 ⓑ 규율까지 완화(측정 레인 동시 실행 허용) ⓒ 현행 유지
- 권장: ⓐ — 규율의 근거(슬롯 호스트 전역)는 남아 있고 틀린 것은 전제 문장이다. ⓑ 는 동시 실행 시 슬롯 고갈 78 재발 여부 실측이 없다.
- 완료 기준: `grep -rnE '뮤텍스가 없다|no cross-process mutex' .agents/roles .codex/agents` 0건 · `python3 scripts/agent-bridge.py check` · `gates/run.sh harness-contract` green · `docs/decisions/0002-*.md` diff 0.
- 판정 질문: 권장안 수용?

### C2 README.md 하네스 훅 절  (출처: R1-12 corrected · R1-10 corrected)
- 문제: `README.md:64` 「훅 7개」(등록 11) · `:73` git-guard 를 main/master 기준으로 설명(코드 보호 집합 = main|master|develop|product) · `:74`·`:75` migration-guard·decision-number-guard 기준을 `origin/main` 으로 설명(migration-guard 코드 = `origin/develop` · `scripts/harness/hooks/migration-guard.sh:72-77`) · `:76-77` H6/H7 을 미추적 파일·`gate-summary.json` 부재 검사로 설명(현재 lifecycle task runtime 증거 판정) · `:9`·`:60` 「최신 `R-*.md` 하나만 읽는다」.
- `README.md:105` 「모든 훅 스크립트의 첫 줄이 이 값(COLAB_HOOKS=0)을 보고 즉시 통과」 — `uncommitted-artifacts.sh`·`lane-gate-summary.sh`·`lifecycle_contract.py` 의 COLAB_HOOKS 참조 0건. `docs/development/dual-agent.md:56` 「H6 자체를 끄거나 성공으로 위장하지 않는다」 → 동작은 의도, README 쪽 drift(결함 아님).
- 선택지: ⓐ 훅 표를 현재 등록(`.claude/settings.json`·`.agents/harness.yaml`) 기준으로 다시 쓰고 COLAB_HOOKS 예외(H6/H7) 1줄 추가 ⓑ 훅 표를 지우고 정본 링크(`.agents/harness.yaml` 훅 목록 · `docs/development/dual-agent.md`) + COLAB_HOOKS 절(H6/H7 예외 포함)만 남김 ⓒ 표 유지 · 수치·ref 이름만 교정
- 권장: ⓑ — 같은 목록을 두 곳에 두어 생긴 drift 다. 정본을 한 곳으로 줄이면 다음 훅 추가 때 README 를 고칠 일이 없다.
- 완료 기준: `grep -nE '훅 7개|origin/main|최신 .R-\*\.md' README.md` 0건 · COLAB_HOOKS 절에 H6/H7 예외 문장 1건 · `gates/run.sh harness-contract` green.
- 판정 질문: 표 삭제(ⓑ)와 표 갱신(ⓐ) 중 무엇?

### C3 gates/README.md CI 표 · ci.yml 낡은 주석  (출처: R3-15)
- 문제: `gates/README.md:233-245` 표에 `search-golden`·`product-safety`·`required-gates`·`ci-required` 잡 행 없음(`.github/workflows/ci.yml` 잡 16개 중 11개만 수록 · `changes` 제외) · `agent-bridge.yml` 언급 0건 · `:236` frontend-gates 행에 `frontend-fixture-reach` 누락(`ci.yml:324` 실행) · `:244` harness-eval 행 「시크릿 참조」 ↔ 잡은 면제 모드.
- `ci.yml:167-171` 「WU-D3에서 실제 검사를 채운다 · 지금은 골격」 주석 잔존 · `:641` harness-eval 면제 설명이 `repo-hygiene` 잡(`:629`) 구간에 위치.
- 선택지: ⓐ 표를 ci.yml 기준으로 갱신 + 주석 삭제·이동 ⓑ ⓐ + 표의 잡 이름 집합과 ci.yml 잡 이름 집합 대조를 harness-contract 에 추가 ⓒ 표 삭제 · 「정본 = ci.yml」 한 줄
- 권장: ⓐ — 조건·게이트 매핑은 ci.yml 만으로 읽기 어려워 표를 둔다. 대조 검사(ⓑ)는 코드 추가라 Ted 판정.
- 완료 기준: 표 잡 이름 집합 = ci.yml 잡 이름 집합 − `changes`(대조 결과 PR 본문 기재) · `grep -n '골격' .github/workflows/ci.yml` 0건 · ci.yml diff 가 주석 줄뿐(`git diff -U0` 확인).
- 판정 질문: 권장안 수용? 잡 이름 대조 검사(ⓑ) 추가 여부?

### C4 계획·인계 문서 포인터 — #130 · #131 · #140 · 이 intent  (출처: R5-5 corrected · R2-10 일부)
- 문제: `AGENTS.md:18` 은 전환 실행 계획으로 `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md` 를 가리킨다. 그 파일(`:4` 「전면 전환·추가 고도화는 보류」)과 `docs/development/harness-transition-handoff.md`(`:28` 같은 문장) · `AGENTS.md` 의 #130 · #131 · #140 언급 0건. `harness-transition-handoff.md:162`·`:175` 「native hook 허용·차단 미확인」은 같은 문서 `:51-66`(2026-09-15 실측 기록 · 판독)과 어긋난다.
- 범위 기록: 각 하네스 PR 은 Ted 승인 intent 에 근거한다 → 빠진 것은 계획 포인터 갱신이다. 이 intent 는 09-15 「추가 고도화 보류」 범위를 다시 연다 → 그 사실을 계획 문서에 적는다.
- 선택지: ⓐ `R-HARNESS-PR-CENTRIC.md` `:4` 아래에 「2026-09-24~ 재개: #130 · #131 · #140 · 이 intent」 절 추가 + handoff 문서 머리에 이후 이력 포인터 + `:162`·`:175` 정정 ⓑ `AGENTS.md:18` 을 하네스 intent 목록으로 바꾸고 두 문서를 이력으로 동결 표기 ⓒ 현행 유지
- 권장: ⓐ — `AGENTS.md` 는 always-on 120줄 상한 문서라 변경을 두지 않는다. 계획 문서 한 절 추가로 포인터가 닿는다.
- 완료 기준: `grep -cE '#130|#131|#140' dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md docs/development/harness-transition-handoff.md` 각 ≥1 · 이 intent 경로 인용 1건 · `AGENTS.md` diff 0 · `gates/run.sh harness-contract` green.
- 판정 질문: 권장안 수용?

### C5 존재하지 않는 `main` 을 가리키는 설정·문서·guard 기준  (출처: R3-3 corrected · R4-17 · R1-13 · R1-hooks-missed(ref guard 실패 방향))
- 문제: `docs/development/github-ruleset.json:6` 대상 `refs/heads/main` — 원격 main 없음 · 적용 규칙셋은 product 하나(메인 재현 2026-09-25). `docs/development/release-evidence.md:43`·`:45` main PR 제안 문구. `scripts/harness/hooks/decision-number-guard.sh:63-73` 기준선 `origin/main` — 로컬 ref 부재(2026-09-25 `git rev-parse --verify origin/main` 실패) → 매번 워킹트리 `max-decision.sh` 로 물러서고, 그것도 못 읽으면 `:73` exit 0(통과). migration-guard 는 `origin/develop` 부재 시 준비 실패로 막는다(`migration-guard.sh:72-74`) → 두 ref 기반 guard 의 실패 방향이 반대. `migration-guard.sh:5`·`:10-11`·`:55`·`:70` 주석은 여전히 `origin/main`. PLAN-SoT 는 legacy 읽기 호환 자료(AGENTS.md) → low.
- 선택지: ⓐ ruleset JSON 을 T1 결론대로 `refs/heads/develop` 대상으로 다시 쓰고 release-evidence 문구 동기화 · decision-number-guard 기준을 `origin/develop` 로, 기준 부재 시 migration-guard 와 같은 준비 실패(차단) · migration-guard 주석 교정 ⓑ ruleset JSON 에 「폐기 · 원격 설정은 T1」 표기 · guard 는 주석만 교정 ⓒ 현행 유지
- 권장: ⓐ(ruleset 부분은 T1 판정 뒤) — 없는 ref 를 기준으로 삼는 상태를 끝내고, 「선언하면 검사」 원칙과 어긋나는 exit 0 경로를 없앤다.
- 완료 기준: `grep -nE 'refs/heads/main|origin/main' docs/development/github-ruleset.json docs/development/release-evidence.md scripts/harness/hooks/decision-number-guard.sh scripts/harness/hooks/migration-guard.sh` 0건 · decision-number-guard 「기준 ref 부재 → exit 2」 시험 1건 red→green · `gates/run.sh agent-bridge` green · T1 이 「적용 안 함」이면 JSON 에 폐기 표기.
- 판정 질문: decision-number-guard 기준 부재 시 차단(ⓐ) 수용? 이 guard 수정을 PR 1(막는 장치)로 옮길지?

### C6 Claude skill adapter — 명시 호출 플래그 · parity 검사 한 방향 · VENDORED.md  (출처: R2-3 · R2-4 corrected · R2-17 · R2-15 corrected)
- 문제: 본문 4종(`.agents/skills/{agent-browser,apple-design,grill-me,to-spec}/SKILL.md`)은 `disable-model-invocation: true`, Claude adapter 17개 중 이 키 0건(예: `.claude/skills/grill-me/SKILL.md:1-4`) → Claude 에서 모델 호출 목록에 오른다. `scripts/agent-bridge.py:101-111` 은 본문 → adapter 한 방향만 검사: 본문 없는 adapter · 플래그 불일치 미검출.
- adapter description 은 「Claude에서 공통 X 절차를 연결한다」로 본문 「Use when…」 트리거가 빠짐(R2-4 · low · 본문은 한 번 더 읽어서 닿는다).
- `.agents/skills/VENDORED.md:5` 「전 8종 명시 호출 전용」(본문 기준으로도 사실 아님) · `:98` 재대조 diff 대상이 9줄 adapter(`.claude/skills/<name>/SKILL.md`) → 본문 경로(`.agents/skills/<name>/SKILL.md`)여야 한다.
- 선택지: ⓐ adapter 에 본문의 `disable-model-invocation` 값을 싣고 agent-bridge check 가 두 값 일치 + adapter → 본문 역방향 존재를 검사 · description 은 현행 ⓑ ⓐ + adapter description 에 본문 트리거 문구 복사(검사 포함) ⓒ VENDORED.md 만 정정
- 권장: ⓐ + VENDORED.md `:5`·`:98` 정정 — 명시 호출 정책을 Codex(`agents/openai.yaml` `allow_implicit_invocation: false`)와 맞춘다. 트리거 복사(ⓑ)는 자동 호출 범위를 넓혀 ⓐ 와 방향이 반대라 따로 판정.
- 완료 기준: agent-bridge 부정 fixture 시험 2건(플래그 불일치 · 본문 없는 adapter) red→green · `python3 scripts/agent-bridge.py check` green · 새 Claude 세션 스킬 목록에서 4종 제외 여부 1회 관측 기록.
- 판정 질문: ⓐ 수용? 트리거 문구 복사(ⓑ)는 하지 않는 것으로 확정?

### C7 Claude role frontmatter 값 자동 검사 없음  (출처: R2-5)
- 문제: `scripts/harness/config.py:160-165` 는 `.claude/agents/*.md` 의 frontmatter 를 떼고 본문(2줄 포인터)만 비교한다. `scripts/agent-bridge.py:82-92` 는 Codex toml 만 검사하고, Codex model/effort 는 `scripts/tests/test_agent_bridge.py:35` 가 단언한다. Claude 쪽 기대값 검사는 수동 grep(`dev-package/prd/specs/S-AGENT-MODEL-TIERING-20260924.md:62`) → model·effort·maxTurns·isolation·disallowedTools 를 바꿔도 모든 gate 통과.
- 선택지: ⓐ `.agents/harness.yaml` 에 역할별 기대값 선언 + check 가 Claude frontmatter · Codex toml 양쪽 대조 ⓑ 단위 시험에 Claude frontmatter 기대값 단언 추가(Codex 방식과 같은 형태) ⓒ 현행 유지
- 권장: ⓑ — Codex 쪽과 대칭을 맞추는 최소 변경(시험 파일 1개). ⓐ 는 선언 구조 신설이라 범위가 늘어난다.
- 완료 기준: frontmatter 값 1개(예: advisor maxTurns)를 바꾼 사본에서 시험 red, 원복 후 green(`gates/run.sh agent-bridge`).
- 판정 질문: 권장안 수용?

### C8 docs/development 사실 갱신 — dual-agent.md · lifecycle-evidence.md  (출처: R2-10 · R2-roles-codex-missed(정의 변경 3회) · R2-14 · R4-16)
- 문제: `docs/development/dual-agent.md:70` 「5개 이벤트」 · `:83`·`:85` 「7개 등록 항목」 ↔ `.codex/hooks.json` 6 이벤트 · 9 항목(2026-09-25 재계수). 마지막 신뢰 기록은 2026-09-09(7 항목 · `:82-83`), 그 뒤 정의 변경 3회 — `012df481` 09-12 Stop · `4c07f1ea` 09-18 SubagentStop 대상 확대 · `faff6734` 09-24 SubagentStart researcher(`git log -- .codex/hooks.json`). 재신뢰 요청 문장(`:87-89`)은 09-24 정의만 든다.
- `dual-agent.md:54` 「lane-worker frontmatter 스킬 4개」 ↔ `.claude/agents/lane-worker.md:7` 5개(colab-ponytail 포함).
- `docs/development/lifecycle-evidence.md` measurement-lane 언급 0건 · `:10` 역할을 researcher·lane-worker 로만 적음 ↔ `scripts/harness/hooks/lifecycle_contract.py:55` `MEASURING_ROLES = ('measurement-lane',)` · `:254`.
- 선택지: ⓐ 수치·역할 사실 교정 ⓑ 개수 수치를 문서에서 빼고 「정본 = `.codex/hooks.json`」 참조 + 재신뢰 대상에 09-12 · 09-18 · 09-24 정의 명시 + measurement-lane 절 추가 ⓒ 현행 유지
- 권장: ⓑ — 개수는 정의 추가마다 다시 어긋난다. 재신뢰 대상 목록은 T5 결과를 적을 자리가 된다.
- 완료 기준: `grep -nE '[0-9]+개 (이벤트|등록 항목)|스킬 [0-9]+개' docs/development/dual-agent.md` 0건 · `grep -c measurement-lane docs/development/lifecycle-evidence.md` ≥1 · 재신뢰 대상 3개 정의 명시.
- 판정 질문: 권장안 수용?

### C9 규칙·역할 본문의 낡은 문장  (출처: R2-18 corrected · R2-roles-codex-missed(launch 로드 · baseRef · advisor 쓰기) · R2-11 corrected)
- 문제:
  - `.agents/rules/colab-rules.md:4` 「`paths` frontmatter 없음 → launch 때 로드」 — 현재 launch 로드는 5줄 포인터 `.claude/rules/colab-rules.md` 뿐, 본문은 필요한 절만 읽는다(AGENTS.md 「작업에 필요한 절을 읽는다」).
  - `:28` §1-3 「Sonnet 하강 없이 Fable 로 재시도」 — 현재 역할 등급(lane-worker opus · measurement-lane sonnet · S-AGENT-MODEL-TIERING)과 어긋남. 앵커 파일명 부재는 설계(`:5`)라 결함 아님.
  - `:62` §2-3 「P-A 에이전트 정의로 강제 예정」 — `.claude/agents/lane-worker.md` 에 `isolation: worktree` 이미 있음.
  - `:65` §2-3 · `.agents/roles/lane-worker.md:27` 「워크트리 기본 기준은 `origin/<default>`」 — `.claude/settings.json:4` `baseRef: "head"`(ADR-0001). `git merge --ff-only` 첫 줄 자체는 유지, 이유 문장만 낡음.
  - `.agents/roles/advisor.md:39` 「쓰기 도구가 없으므로」 — Claude advisor 는 `disallowedTools: Edit, Write, NotebookEdit`(`.claude/agents/advisor.md:6`)라 Bash 가 남는다. Codex 는 `sandbox_mode = "read-only"`.
- 선택지: ⓐ 문장별 사실 교정(§1-3 은 역할 등급 spec 참조로 대체 · advisor 는 「파일을 수정하지 않는다 — Claude 에서는 Bash 가 남아 있어 규율이다」) ⓑ ⓐ + Claude advisor frontmatter 에서 Bash 제거(전제를 도구 제한으로 참으로 만듦) ⓒ 현행 유지
- 권장: ⓐ — advisor 는 판정 근거 확인에 Bash 읽기 명령을 쓴다. ⓑ 는 advisor 동작 범위를 바꾸는 별도 판정이다.
- 완료 기준: 인용 문자열 5종(`loaded at launch` 주장 · `Fable 로 재시도` · `강제 예정` · `기본 기준은 \`origin/<default>\`` · `쓰기 도구가 없으므로`) grep 0건 · `python3 scripts/agent-bridge.py check` · `gates/run.sh harness-contract` green.
- 판정 질문: 권장안 수용?

### C10 hook 머리말·안내 문구 drift  (출처: R1-9 · R1-16)
- 문제: `scripts/harness/hooks/git-guard.sh:71` · `migration-guard.sh:21` · `test-file-guard.sh:27` 「exit 1 은 통과다 · 판정 못 하면 통과가 기본값」 — 실제는 python3 부재 시 exit 2(`git-guard.sh:82` · `migration-guard.sh:28` · `test-file-guard.sh:38`)이고 뒤의 `command -v python3 … || exit 0`(`:90` · `:32` · `:42`)은 도달 불가.
- `scripts/harness/hooks/worktree-setup.sh:247-259` 「`baseRef: fresh` … origin/main · P-E 브랜치」 안내 + `~/.colab-v2-test.env` 만 확인 ↔ `.claude/settings.json:4` `baseRef: "head"` · `gates/run.sh:264` `COLAB_TEST_ENV_FILE` 우선.
- 선택지: ⓐ 주석·안내 교정 + 도달 불가 줄 삭제 + worktree-setup 이 `COLAB_TEST_ENV_FILE` 을 run.sh 와 같은 규칙으로 확인 ⓑ 주석만 교정
- 권장: ⓐ — `git-guard.sh`·`test-file-guard.sh` 는 PR 1 이 고치는 파일이므로 두 파일 머리말은 PR 1 에 얹고, PR 3 은 `migration-guard.sh`·`worktree-setup.sh` 만.
- 완료 기준: `grep -n 'exit 1 은 통과' scripts/harness/hooks/*.sh` 0건 · `grep -nE 'fresh|P-E' scripts/harness/hooks/worktree-setup.sh` 0건 · `COLAB_TEST_ENV_FILE` 만 있는 환경에서 worktree-setup 이 「있음」을 출력하는 시험 1건 · `gates/run.sh agent-bridge` green.
- 판정 질문: 권장안 수용(두 파일 머리말은 PR 1)?

### C11 bootstrap-diet 의 mtime legacy 라운드 출력  (출처: R5-governance-missed(bootstrap-diet))
- 문제: `scripts/harness/hooks/bootstrap-diet.sh:70-71` 이 `dev-package/prd/rounds/R-*.md` 를 mtime 순으로 골라 `:84` 「legacy 참고 후보(mtime) … 신규 task 선택 근거 아님」을 지정 라운드가 없는 매 세션 시작에 출력한다. AGENTS.md 「mtime으로 다음 작업을 결정하지 않는다」.
- 선택지: ⓐ 라벨 유지(현행) ⓑ 지정 라운드(`SELECTED`)가 없으면 후보 줄을 출력하지 않음 ⓒ 후보 파일 대신 「legacy 라운드 위치 = `dev-package/prd/rounds/`」 한 줄
- 권장: ⓑ — 출력과 AGENTS.md 원칙이 어긋나고, 후보 줄이 없어도 `:75-76` 신규 작업 안내는 남는다.
- 완료 기준: SELECTED 없는 SessionStart 출력에 `mtime` 문자열 0건 — bootstrap-diet 시험 갱신 후 `gates/run.sh agent-bridge` green.
- 판정 질문: ⓑ(출력 삭제)와 ⓐ(라벨 유지) 중 무엇?

### C12 css-edit-audit PostToolUse 출력이 Claude 모델에 닿는지 — 관측 먼저  (출처: R1-3 · 문서 근거 · 미측정)
- 문제: `scripts/harness/hooks/css-edit-audit.sh:21` 머리말 「PostToolUse 의 stdout 은 맥락으로 실려 들어간다」, `:74` `echo "$OUT"` 평문 출력. 저장소가 인용한 Claude hook 문서(`bootstrap-diet.sh:24-26`)는 평문 stdout 이 모델 맥락에 들어가는 이벤트를 SessionStart·SubagentStart 로 든다 → Claude 에서 감사 행이 모델에 닿지 않을 가능성(문서 근거 · 미측정). `ponytail-inject.sh:76` 은 `hookSpecificOutput.additionalContext` JSON 을 쓴다. Codex 는 bridge 가 평문을 감싼다(판독).
- 선택지: ⓐ 관측 1회(`frontend/src` CSS 파일 1건 Edit → 모델 맥락에 감사 행이 보이는지) 후 결과로 ⓑ 여부 판정 ⓑ 출력을 additionalContext JSON 으로 변경(ponytail-inject 방식) ⓒ 현행 유지
- 권장: ⓐ → 닿지 않으면 ⓑ. 관측 없이 바꾸면 전후 차이를 확인할 수단이 없다.
- 완료 기준: 관측 기록 1건(날짜 · Claude Code 버전 · 결과). ⓑ 채택 시 css-edit-audit JSON 출력 시험 + Codex bridge 시험(`scripts/tests/test_agent_bridge.py`) green.
- 판정 질문: 관측을 PR 3 lane 에 맡길지(권장안 수용?)

### T1 develop 필수 status check · PR 규칙  (출처: R3-3 corrected · R3-2 corrected · R4-2 corrected)
- 문제(메인 재현 2026-09-25): develop branch protection `required_status_checks` null · `required_pull_request_reviews` null · force push·삭제 금지만. 규칙셋은 23379713 product-promotion-policy(product) 하나. → develop 에서 red CI 가 병합을 막지 않는다. 저장소 문서는 미적용을 밝혀 두었다(`harness-transition-handoff.md:191` · `release-evidence.md:45`) → 공개된 미적용 상태. `.agents/harness.yaml` `gates.required` 12개는 모양·개수만 검사(R4-2).
- 연결: `ci-required` 는 `required-gates` 를 needs 에 포함한다(`ci.yml:848`). PR 2 가 병합 부모 거짓 red(H6 · R3-1)를 고치기 전에 필수로 걸면 develop 이 움직일 때마다 병합이 막힌다 → 적용 시점은 PR 2 병합 뒤. harness-contract 는 path-filtered `agent-bridge.yml` 에서만 돌아 `ci-required` 밖이다.
- 선택지: ⓐ develop 필수 check = `ci-required` 1개 + PR 필수(승인 0) ⓑ `ci-required` + `required-gates` 2개 ⓒ 현행 유지(미적용 공개 상태)
- 권장: ⓐ — `ci-required` 가 `required-gates` 결과를 이미 포함한다. PR 필수는 git-guard 우회(PR 1 대상) 같은 로컬 사고의 원격 방어선이 된다.
- 완료 기준: Ted 적용 후 `gh api repos/CognileapAI/colab-v2/branches/develop/protection` 의 required_status_checks 에 선택한 이름이 보이고, C5 의 ruleset JSON 이 같은 내용을 기록.
- 판정 질문: 어느 check 를 필수로(ⓐ/ⓑ/ⓒ)? 적용 시점 = PR 2 병합 뒤로 확정?

### T2 pr_contract 를 CI 에서 돌릴지  (출처: R4-5 · R4-judges-evidence-missed(placeholder 판정))
- 문제: 실제 PR 본문에 `scripts/harness/pr_contract.py` 를 돌리는 gate case·CI 스텝 없음 — `gates/run.sh:316` 은 단위 시험 `test_pr_contract.py` 만, `.github/workflows/*.yml` 참조 0건(2026-09-25 재확인). 병합 PR #140 · #144 · #159 · #160 본문의 「검증 상태: 부분 검증」은 판독 · 재현 안 함. `pr_contract.py:46-48` 의 꺾쇠 텍스트 placeholder 오판은 미검증 — CI 편입 전 재현 필요.
- 선택지: ⓐ CI 잡으로 편입(draft 검사) → PR 2 범위로 ⓑ 로컬 절차 유지 — 에이전트가 로컬 PR 요약 작성 때 실행하도록 `colab-v2-work` 절차에 1줄 ⓒ 폐기
- 권장: ⓑ — PR 게시는 사용자 몫(AGENTS.md)이라 CI 가 본문을 막으면 게시 뒤 본문 수정 루프가 생긴다.
- 완료 기준: 결정이 이 intent 판정 절에 기록되고, ⓐ 면 PR 2 항목으로 이관, ⓑ 면 절차 문서 1줄이 PR 3 에 포함.
- 판정 질문: CI 강제(ⓐ)와 로컬 절차(ⓑ) 중 무엇?

### T3 형제 체크아웃 32 · 33  (출처: R5-12 · R5-governance-missed(33))
- 문제(2026-09-25 재확인): 30 · 31 · 32 · 33 이 호스트 잠금 경로 `${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host` 를 공유한다(`gates/tools/_lock.sh:78`). `32 CoLAB-v2` HEAD `02d251d8` — `gate_mutex_spawn` 0건 → frontend-visual 데몬이 잠금 fd 를 물려받는 이전 코드. `33 CoLAB-v2` HEAD `cb30d344` — `gate_host_mutex` 0건 → 게이트가 호스트 잠금을 잡지 않고 postgres 슬롯은 공유. 33 사용 여부 미검증. `30 CoLAB-v2` 는 `67a03a05` · 수정 포함.
- 선택지: ⓐ 32·33 을 develop 로 갱신 ⓑ 은퇴(삭제·보관) ⓒ 유지 + 그 체크아웃에서 게이트 실행 금지
- 권장: 사용 중이면 ⓐ, 아니면 ⓑ — 사용 여부는 Ted 만 안다.
- 완료 기준: 결정 기록 1줄 · ⓐ 면 두 체크아웃 `gates/tools/_lock.sh` 에 `gate_mutex_spawn` 존재 확인.
- 판정 질문: 32·33 을 지금 쓰는가?

### T4 낡은 브랜치 · f3846f32  (출처: R5 §5 브랜치 표)
- 문제(2026-09-25 재확인: 존재): 로컬 `worktree-agent-a06b599e…` · `worktree-agent-a20a6e57…`(git cherry 기준 고유 커밋 0 — 판독 · 재현 안 함) · `worktree-agent-abe5bbb8…`(`f3846f32` 포함 — #130 이 뺀 handoff JSON 계약 변경) · 원격 `origin/worktree-ponytail-systemic`(#130 본문이 삭제 요청 — 판독).
- 선택지: ⓐ 네 브랜치 삭제 ⓑ `f3846f32` 만 태그로 보관 후 삭제 ⓒ 유지
- 권장: ⓐ — 둘은 develop 에 이미 반영, 하나는 #130 이 채택하지 않은 작업, 원격 하나는 삭제 요청분. 삭제는 비가역이라 Ted 가 실행.
- 완료 기준: `git branch -a --list '*worktree-agent*' '*worktree-ponytail*'` 출력이 결정과 일치.
- 판정 질문: 권장안 수용? `f3846f32` 보관(ⓑ) 필요?

### T5 `/hooks` 재신뢰 · researcher 라이브 스모크  (출처: H10 · R1-19 corrected · R5-10 corrected · R2-roles-codex-missed(정의 변경 3회))
- 문제: #130 병합 뒤 할 일(이 PC `/hooks` 재신뢰 · researcher 1건 라이브 스모크 — Start/Stop agent_id 일치)의 저장소 기록 0건. 재신뢰 여부는 저장소로 판정할 수 없다 → 「안 했다」가 아니라 「기록 없음」. 정의별 재신뢰 필요는 문서 근거(`dual-agent.md:87-89`). Codex 는 09-09 신뢰 기록 뒤 정의 변경 3회(C8). `lifecycle-evidence.md` 는 agent_id 일치를 「증명되지 않음」으로 둔다 → 자동 task 는 ID 대조를 건너뛴다(대체 절차 있음 · low).
- 선택지: ⓐ 지금 재신뢰 + 스모크 ⓑ PR 1 · PR 3 병합 뒤 한 번에(이 intent 가 훅 정의를 바꾸면 재신뢰 대상이 늘어남) ⓒ 기록 없이 진행
- 권장: ⓑ — 정의 변경을 모아 한 번에 신뢰한다. 결과는 C8 이 만든 자리(`dual-agent.md` 재신뢰 대상 목록)와 `lifecycle-evidence.md` 에 기록.
- 완료 기준: 기록 1건 — 날짜 · PC · 도구(Claude/Codex) · 신뢰한 정의 목록 · 스모크 Start/Stop agent_id 두 값.
- 판정 질문: 권장안 수용?

### T6 #131 원한 결과 8 — 한도 도달률 재측정  (출처: R2-13)
- 문제: `dev-package/intent/2026-09-24-agent-model-tiering.md:38` 「병합 뒤 재측정 … 기록을 남긴다(후속 · 병합 조건 아님)」. 저장소에는 병합 전 기준(`dev-package/reports/harness/20260924-agent-model-tiering/M1-role-usage.md` · 09-24)과 후속 표기(`PR-BODY.md:39`)만 있고 재측정 기록 없음(2026-09-25 `git grep 도달률`).
- 선택지: ⓐ 유지 — 별도 측정 회차 ⓑ 폐기(원한 결과 8 삭제 사유 기록) ⓒ 이 intent 의 세 PR 동안 생기는 advisor·researcher·measurement-lane 스폰을 표본으로 M1 방식 집계
- 권장: ⓒ — 별도 회차 없이 표본이 생긴다.
- 완료 기준: 역할별 스폰 수 · 한도 도달 수 표 1개가 PR 3 본문 또는 reports 에 기록.
- 판정 질문: 권장안 수용, 또는 폐기(ⓑ)?

### X 제외 — 디자인 시스템 후속 intent 로 이관  (근거: `dev-package/reports/design-system/20260924/architecture.md` §7)
- X1 H11 캡처 장면 사각 — 대상이 `frontend/scripts/visual-baseline/scenes.json` 이고 장면 추가는 기준 재촬영을 동반한다. hook·gate 판정 정확도와 무관(§7 후속 4).
- X2 H12 `tsconfig.audit.json` gate 편입 — frontend 타입 검사 범위 결정이다(§7 후속 5).
- X3 H13 시각 대조 gate 승격 — 캡처 약 8분 · agent-browser 필요 · 기준 캡처 보관 위치가 디자인 쪽 결정이다(§7 후속 6).
- X4 H15 `frontend-test` 부하 시 대기 초과 — 원인 후보가 렌더 비용(제품 코드)·시험 대기 한도다.
- 흡수 메모: 초안 `2026-09-25-harness-design-round-residuals.md` 의 A39 「남은 일 ①」(주 체크아웃 `7acd0fce`)은 해소 — 31 은 `67a03a05`(#130 포함). 「③ 30 · 31 저장소」는 낡음 — 노출 체크아웃은 32 · 33(T3). H10 은 T5 로 흡수.
