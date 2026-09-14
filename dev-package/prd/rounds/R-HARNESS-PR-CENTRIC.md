> spec: dev-package/prd/specs/harness-pr-centric.md
# Claude·Codex 공통 PR 중심 하네스 실행 계획

> **For agentic workers:** 위임 원칙(글로벌 `CLAUDE.md`)과 역할별 격리를 적용한다. 현재 사용자가 지정한 `codex/harness-pr-centric` worktree의 쓰기 주체는 이 실행 세션 하나다. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** CoLAB의 공통 하네스를 도구 중립 원본과 PR·commit·CI 증거 중심 구조로 전환한다.

**Architecture:** `.agents/`와 `scripts/harness/`가 공통 선언·절차·판정을 소유하고 `.claude/`와 `.codex/`는 등록과 payload 변환만 소유한다. 기존 기록은 읽기 호환 상태로 유지하면서 시험 입력과 미완료 상태를 먼저 이전하고, 삭제는 별도 승인 단계로 남긴다.

**Tech Stack:** Python 3.11+, Bash, JSON-compatible YAML, Git/GitHub Actions, 기존 CoLAB gates, Claude Code, Codex.

**Spec:** `dev-package/prd/specs/harness-pr-centric.md`

## Global Constraints

- `30 CoLAB-v2`에 접근하거나 변경하지 않는다.
- push, Draft PR, Issue/ruleset 쓰기는 대상과 내용을 먼저 제시하고 승인 후 수행한다.
- **2026-09-15 사용자 개정:** PR 생성·게시는 사용자 담당, 에이전트는 로컬 요약·검증 근거·절차만 안내한다. 게시 대기를 이유로 독립 로컬 전환 작업을 중단하지 않는다. 이전 게시 승인 대기 기록은 이력으로 보존한다.
- 병합, 배포, 기존 기록 삭제는 각각 별도 승인을 받는다.
- 검사 범위 축소·비활성화·green-by-skip을 금지한다. exit 0/1/78을 그대로 보존한다.
- 새 `.sh`는 Git index mode 100755로 등록한다.
- 같은 checkout의 쓰기 주체는 하나다. 이 계획은 현재 격리 worktree에서 직렬 실행한다.

## 현재 상태

### 참고 저장소 갱신 — 2026-09-15

사용자가 알린 최신 기준은 `sungwooHa/ai-sdlc-harness` PR #2의
`fc424e8f21f5d4479a43780e41ce9883ed1dbc7f`다(기존 PR #1 기준에서 변경).
새로 추가된 것은 구현 전 합의본 보존, 양쪽 호스트의 승인 범위·소스 검증,
PR의 합의 기대/실제 결과 비교, 선택적 ADR 작성·대체·제안이다.
기존 사용자 승인과 게시 경계는 유지한다. 과거 승인 이벤트를 소급 생성하지 않는다.
남은 PR 인계·지속 결정 설계는 이 버전과 대조하며, 별도 중복 구현을 추가하지 않는다.
현재 코드 checkpoint는 `d76b0eb1`이다. 공통 원본·PR 상태는 `e125dd55`, 배포 증거는 `d76b0eb1`에 로컬 커밋했다.
최신 참고의 순수 ADR·합의본 보존 로직과 PR 표현을 적용했다. 새 승인 훅이나 실제 승인 기록은 생성하지 않았다.
PR 완료와 draft의 ‘검증됨’은 registry 기반 CI artifact bundle을 재검증한다.
외부 합의본 폴더는 명시적인 `--repo` 설정이 필요하다. PR 기본 필수는 6절이며 추가 표현은 선택이다.
부모 재검증: `python3 -m unittest scripts.tests.test_pr_contract scripts.tests.test_harness_config scripts.tests.test_harness_evidence`
25 tests, 실패/오류 0, exit 0. 독립 수용 검토에서 이전 3결함의 해소를 확인했다.
이 결과는 실제 GitHub CI·모델 행동·배포 검증을 뜻하지 않는다.

### 최신 main 로컬 병합 완료 — 2026-09-15

읽기 전용 원격 조회에서 PR #35와 #38은 이미 병합됐고, 원격 main은
`6db30323a78a4e63f3e28810db0f325b69551979`다. 기준선 이후 원격 변경은 172경로다.
우리 커밋 및 현재 변경과 겹치는 경로는 6개다:
`.claude/rules/deploy.md`, `CLAUDE.md`, `infra/dev/ship.sh`, `infra/dev/tag-release.sh`,
`scripts/deploy_release.py`, `scripts/tests/test_deploy_release.py`.
이는 경로 중복 계수이며 실제 내용 충돌 판정이 아니다. open PR 0건을 충돌 0건으로 간주하지 않는다.
사용자의 “좋아 병합 진행” 승인 후 지정 SHA를 fetch하고 현재 브랜치에 로컬 병합했다.
병합 커밋은 `b7c05242de5da16f69dd12e0615054afb0b8851f`이며 두 부모는 `736855df`, `6db30323`이다.
실제 충돌은 `.claude/rules/deploy.md` 1개였다. upstream 규칙을 `.agents/rules/deploy.md`로 반영하고 adapter를 유지했다.
미커밋 tracked/untracked 변경은 stash `c11809dc6bfc51a9783e7f6ba5f93bf571493afe`로 보존 후 복원했다.
4개 배포 파일은 자동 병합됐고 독립 검토에서 양측 변경 유실이 없음을 확인했다. stash는 삭제하지 않았다.
복원 후 부모 실행: deploy/release/evidence/PR/config/source-layout 단위 시험 62개 통과, 셸 문법·bridge 연결 검사 exit 0.
현재 미커밋 diff 공백 검사 exit 0. 병합으로 가져온 기존 보고서·시험 파일의 공백 오류는 보존했고 전체 cached diff 검사는 exit 2였다.
제품 전수·실환경 검증 결과로 확대하지 않는다. rebase·push·배포·원격 main 변경은 하지 않았다.

| 작업 | 현재 판정 | 남은 조건 |
|---|---|---|
| 공통 선언·CI 증거 | 로컬 구현·관련 검증 완료 | 실제 원격 CI 미실행 |
| 시험 입력 이전 | 로컬 검증 완료 | 검색 helpers 43·golden 질문 12 실행, 기존 기록 보존 |
| 공통 스킬·규칙·역할·훅 | 로컬 구현·관련 검증 완료 | 제품 단일 원본·얇은 연결·신규 task 시작/종료 연결; native 실발화와 구분 |
| task·PR·ADR | 로컬 구현 반영 | 상태·기획·계약 소비자, 결정 색인, 호환 종료 검사 구현; 실제 Issue 이전과 호환 종료는 미완료 |
| 배포 증거 | 로컬 구현·독립 수용 완료 | 동일 doctor 실행·실로그 hash·소스·full SHA 연결; 실배포 미실행 |
| 실발화·모델·양방향 인계 | 미완료 | Claude 합성 해석 2회 통과만 확인. Codex 공식 실행기는 UNC unsigned 정책 차단; native hook·양방향 미확인 |
| 전수 검사·게시 안내 | 실행·기록 완료, 전체 수용 미달 | 코드 `d76b0eb1` 전수 67/2/0, exit 1(9분 52초). 사용자 PR 절차는 마감 문서 |

부모 재검증: scripts/tests 전체 313개 중 303 통과·Windows 10 skipped·실패 0, ship mock dev 36/prod 48 통과. 독립 수용 완료.
`ship.sh`는 전달/load만 하며 자동 기동을 추가하지 않는다. dev는 사전 PR/CI → 별도 배포 → 사후 검증 → tag, prod는 사전 PR/CI → tag → 별도 배포 → 사후 검증이다.
staging 리허설의 기존 의미를 유지하며 dev 완료로 간주하지 않는다.
Issue 미게시 상태에서는 compatibility만 허용 가능하며, 신구 상태의 영구 이중 쓰기를 도입하지 않는다.

| 단계 | 상태 | 증거/다음 조건 |
|---|---|---|
| 기준선 측정 | 부분 완료 | 정적 3건 green. 실행기 부재라는 당시 판단은 정정: PowerShell은 있으나 UNC unsigned 정책으로 차단, fresh 시작·훅 미측정 |
| 게이트·CI 재조사 | 완료 | 본 게이트 38+selftest 29, CI/SHA 결함과 문서 입력 의존 확인 |
| 전환 표·계획·수용 기준 | 완료 | 독립 검토의 필수 누락을 반영 |
| 구현·검증 | 로컬 구현 마감·전체 수용 미달 | 프런트·schema-diff 실패와 실발화·양방향 인계 미확인, 호환 종료 미완료 |
| 외부 게시 | 미실행 | PR은 사용자 직접 게시. push·Issue·ruleset은 내용·대상 승인 후 별도 수행 |

### Task 1: 공통 하네스 선언과 검사기

**Files:**
- Create: `.agents/harness.yaml`
- Create: `scripts/harness/config.py`
- Create: `scripts/harness/check.py`
- Create: `scripts/tests/test_harness_config.py`
- Modify: `gates/run.sh`
- Modify: `gates/README.md`

**Interfaces:**
- Produces: `load_contract(path) -> dict`, `check_contract(root) -> list[str]`, 신규 gate `harness-contract`.
- Contract: JSON parse 실패, 필수 key 누락, 빈 required gate, 존재하지 않는 경로·command는 준비 실패다.

- [ ] 실패 fixture로 malformed config, 빈 gate 선언, 누락 adapter를 red로 고정한다.
- [ ] `harness.yaml`에 branch, surfaces, gates, evidence, adapters, local/retired roots를 CoLAB 값으로 선언한다.
- [ ] checker가 schema·경로·양쪽 adapter·hook 공통 원본을 fail-closed 검증하게 한다.
- [ ] `harness-contract`와 selftest를 `gates/run.sh`·README에 등록하고 exit 0/1/78을 확인한다.
- [ ] `agent-bridge`, `harness-contract`, selftest를 실행하고 논리 단계로 커밋한다.

### Task 2: CI breaking 기준과 SHA 증거

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/agent-bridge.yml`
- Create: `scripts/harness/verify_evidence.py`
- Create: `scripts/tests/test_harness_evidence.py`
- Modify: `scripts/tests/test_ci_eval_policy.py`

**Interfaces:**
- Consumes: `harness.yaml.evidence`.
- Produces: base/head SHA, tree, gate 3계수, run identity를 검증하는 CLI와 CI summary/artifact.

- [ ] 현재 `event-breaking`의 base env 누락을 잡는 실패 시험을 먼저 red로 확인한다.
- [ ] contract/event breaking에 pull request event의 고정 base SHA를 전달하고 PR head, merge 시험, push before/after SHA를 구분한다.
- [ ] 누락·다른 SHA·준비 red·중복 gate를 거절하는 evidence 시험을 red로 추가한다.
- [x] CI가 적용 대상 필수 gate 집합을 검증하고 gate summary를 실행 event SHA와 함께 업로드하며 job summary에 3계수를 기록하게 한다.
- [x] 단위 시험과 workflow 정적 검사를 green으로 만든 뒤 커밋한다.

보완 검증(2026-09-15): 기존 needs 성공만 집계하던 결함을 음성 시험으로 재현한 뒤
14개 논리 생산자/38개 명령을 정본 등록하고 명령별 artifact를 대조하도록 교체했다.
누락·다른 SHA·계수/행 불일치·미선언 집합은 거절한다. 실패 집계도 계수 단위를 명시한 JSON을 남긴다.
메인 재실행: harness-contract-selftest 18 tests exit 0, ci-filter-check exit 0.
실제 GitHub Actions는 미실행이며 원격 게시 승인 뒤 검증한다.

### Task 3: 세션 문서 시험 입력 선이전

**Files:**
- Create: `contracts/ui/e01-permission-gates.json`
- Move test inputs: `dev-package/reports/reference-data/datasets-md`, core-api/search golden inputs → 코드·계약 인접 fixture 경로
- Modify: `frontend/test/e01-apply-points.test.ts`
- Modify: `frontend/vite.config.ts`
- Modify: `gates/tools/frontend-typecheck-selftest.sh`
- Modify: `gates/tools/frontend-test-selftest.sh`

**Interfaces:**
- Produces: 제품 권한 회귀의 repo-native JSON fixture. 기존 세션 마크다운은 호환 기록으로만 남는다.

- [ ] sessions 문서가 없어도 시험이 계약 fixture를 읽는 실패 시험을 추가하고 red를 확인한다.
- [ ] E-01 표의 route/permission 값을 JSON으로 그대로 이전하고 test parser를 JSON schema 대조로 바꾼다.
- [ ] Vite의 sessions filesystem 허용과 selftest symlink를 제거한다.
- [ ] `frontend-test`, `frontend-typecheck`와 두 selftest를 green으로 확인하고 커밋한다.
- [ ] seed plan·core-api·search golden 입력의 실행 소비자를 색인하고, 문서/보고서 경로가 아닌 fixture로 선이전한다.
- [ ] 이전 전후 같은 게이트가 같은 대상 건수로 green인지 확인하고 커밋한다.

### Task 4: 스킬·훅 공통 원본 이전

**Files:**
- Move source bodies: `.claude/skills/*/SKILL.md` → `.agents/skills/*/SKILL.md`
- Replace with adapters: `.claude/skills/*/SKILL.md`
- Move common rules/roles/resources: `.claude/rules`, `.claude/agents`의 공통 본문과 skill 인접 resources → `.agents/` 원본
- Keep tool adapters: `CLAUDE.md`, `.claude/`, `.codex/`
- Move source judges: `.claude/hooks/*` → `scripts/harness/hooks/*`
- Replace with adapters: `.claude/hooks/*`
- Modify: `scripts/agent-bridge.py`
- Modify: `docs/development/dual-agent.md`
- Modify: `.agents/harness.yaml`
- Modify: `scripts/tests/test_agent_bridge.py`

**Interfaces:**
- Common skill/rule/role links resolve repository paths from Git root; Claude/Codex adapters contain no duplicated procedure body.
- Common hook input schema is produced by Claude wrappers and Codex bridge; both invoke the same judge file.

- [ ] checker 시험으로 중복 본문과 adapter의 잘못된 target을 red로 고정한다.
- [x] 스킬 본문을 `.agents`로 이동하고 Claude adapter를 생성한다. 인접 resources의 기준 경로를 명시한다.
- [x] 공통 규칙·역할 본문과 skill 인접 resources를 `.agents`로 이동하고 AGENTS/CLAUDE 및 양쪽 역할 adapter를 갱신한다.
- [x] hook judge를 `scripts/harness/hooks`로 이동하고 `.claude/hooks`를 실행 adapter로 바꾼다.
- [ ] bridge와 설정의 mapping을 공통 config 기반으로 바꾸고 기존 payload 음성 시험을 유지한다.
- [ ] `agent-bridge`, `harness-contract`, `exec-bit` green 뒤 커밋한다.

진행 증거(2026-09-14): 훅 원본을 먼저 이동하면서 PreToolUse import/진입점이 끊겼다.
사용자가 기존 진입점 복사본을 복원한 뒤, 소비자 경로부터 바꾸고 기존 파일을 어댑터화했다.
복구 후 agent-bridge 103 tests(93 pass, Windows 10 skipped), harness-contract exit 0,
exec-bit 238개 exit 0, frontend-visual-selftest 4개 기대 판정 일치, diff whitespace 검사 exit 0.
이 결과는 공통 규칙·역할 이전, config mapping, 실제 양쪽 모델/인계 검증 완료를 뜻하지 않는다.
추가로 훅 호스트의 import 경로 누락을 복구했고, 저장소 밖 cwd와 Python 격리 모드에서
파일명으로 bridge를 로드하는 회귀 검사를 등록했다. 어댑터 오대상·본문 중복·원본 누락은
공통 계약 검사기가 거절하며 해당 음성 fixture를 포함한 6개 selftest가 통과했다.

### Task 5: 로컬 task 상태와 PR 중심 인계

**Files:**
- Create: `scripts/harness/task_state.py`
- Create: `scripts/harness/pr_contract.py`
- Create: `.github/pull_request_template.md`
- Modify: `docs/development/lifecycle-evidence.md`
- Modify: `.claude/agents/lane-worker.md`
- Modify: `.claude/agents/researcher.md`
- Modify: `.codex/agents/lane-worker.toml`
- Modify: `.codex/agents/researcher.toml`
- Modify: `scripts/agent-bridge.py`
- Modify: `gates/tools/work_item_consistency.py`
- Modify: `gates/tools/seam_consistency.py`
- Modify: `scripts/slack_completion.py`
- Modify: `gates/run.sh`
- Create: `scripts/tests/test_harness_task_state.py`
- Create: `scripts/tests/test_harness_pr_contract.py`

**Interfaces:**
- Task runtime root: Git common dir의 `colab-harness/<checkout-id>/<task-id>/<run-id>/`; checkout 밖 산출물도 명시 경로+hash로 검증하고 다른 worktree 증거를 거절한다.
- PR contract: 목적, 범위, 계획 참조, 결정, head SHA, gate 3계수, CI run, 남은 제약.

- [ ] checkout 밖 실행 산출물을 거절하는 현 결함과 stale/different-SHA 인계를 실패 시험으로 고정한다.
- [x] task state가 외부 산출물·gate report를 명시적으로 허용하되 경로·hash·run id를 검증하게 한다.
- [x] PR template와 checker가 필수 절·Plan-Ref·head SHA·CI/gate 증거를 검증하게 한다.
- [ ] work-item consistency의 작업 상태·의존·완료 판정을 PR/Issue/task evidence로 이전하고 결정 ID 중복 검사는 보존한다. Slack completion·`gates/run.sh task`도 같은 증거를 소비한다.
- [ ] planning freshness의 HTML/MD·적용 사본 실물 대조와 seam consistency의 ge/gb/flow 검사는 유지한다. 적용 상태·병합 근거와 citation 허용 링크만 전환하고 기존 음성 fixture를 유지한다.
- [ ] 유효 결정은 변경 불가 archive+생성 색인으로 보존한다. 기존 sessions/reports 입력은 임시 compatibility read만 허용하고 신규 task 기본값에서는 쓰지 않는다.
- [ ] 임시 호환 입력 허용→외부 PR #35/#38 해소 확인→기존 소비자 0 계측→전환 종료 순서를 checker에 선언한다. 공통 본문 중복 수와 역사 기록 보존 수를 별도 계수로 낸다.
- [ ] 단위 시험·`agent-bridge`·`harness-contract` green 뒤 커밋한다.

부분 증거(2026-09-15): 신규 schema2 작업은 common-dir/checkout/task/run에 보고서와 로그를 쓴다.
기존 schema1은 호환 읽기하며 신규 legacy 생성은 명시 `--legacy`로만 가능하다.
일반 외부 경로 보호는 유지하고 선언·task/agent 식별이 있는 runtime 경로만 예외로 해석한다.
실제 사본의 begin→단독 harness-contract→runtime report/log→complete handoff exit 0 확인.
직접 apply_patch 이벤트의 task/agent 식별 정보 공급은 미확인이다. CLI 경로 검증과 구분한다.
PR 계약과 상태/결정 색인·호환 종료 판정부는 구현됐다. 실제 Issue 게시·HANDOFF 분류·호환 종료는 미완료다.

### Task 6: 배포 전 SHA·CI 판정과 원격 적용안

**Files:**
- Create: `scripts/harness/release_evidence.py`
- Create: `scripts/tests/test_harness_release_evidence.py`
- Modify: `scripts/deploy_release.py`
- Create: `docs/development/github-ruleset.json`

**Interfaces:**
- Consumes: full target SHA, main ancestry, same-SHA required CI result, deploy_doctor redacted 15-item summary.
- Produces: tag/deployment 전 로컬 allow/deny 판정과 승인 후 적용할 required `required-gates` ruleset 문서.

- [ ] 알려진 CI 실패 SHA, main 비조상, SHA 불일치, doctor 15/15 아님을 각각 거절하는 시험을 red로 확인한다.
- [ ] 배포 전 판정기는 full SHA의 main 조상·병합 PR 연결·같은 SHA의 필수 CI 성공을 요구한다. 첫 배포 이전에는 doctor 결과를 요구하지 않는다.
- [ ] deploy 뒤 verify에서 같은 환경·release ID·full target SHA의 신규 doctor 15항목 통과를 요구한다. 이전 run·다른 SHA·면제된 검사를 성공으로 수용하지 않는다.
- [ ] annotated dev tag와 성공 확정은 사후 검증 뒤에만 가능하도록 dry-run 명령을 제공한다. 태그 실패와 배포 검증 성공을 구분한다.
- [ ] required PR+`required-gates`+admin 적용을 담은 ruleset JSON과 읽기 전용 검증 명령을 작성한다. 원격 적용은 하지 않는다.
- [ ] 단위 시험·관련 정적 게이트 green 뒤 커밋한다.

### Task 7: 정적·실발화·모델·양방향 인계 검증

**Files:**
- Update: `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md`
- Local only: Git common dir의 task/gate evidence와 구독 CLI 결과.

**Interfaces:**
- Produces: 검증 종류별 통과/판정 실패/준비 실패와 대상 SHA. 결과를 합산해 다른 종류의 통과로 바꾸지 않는다.

- [ ] Claude·Codex 각각 안전 명령 허용 1건과 보호 편집 차단 1건을 실제 hook으로 확인한다.
- [ ] 동일 fixture/판정부의 모델 행동 평가를 양쪽 구독 CLI로 실행한다.
- [ ] PR 요약 fixture로 Claude→Codex와 Codex→Claude가 승인 경계·다음 행동·SHA를 복원하는지 확인한다.
- [x] `all -j 2~4`는 다른 무거운 작업 없이 1회 실행하고 3계수와 준비 실패를 기록한다.
- [x] spec 수용 기준을 대조하고 상태 표를 갱신한다. 미달은 마감 문서에 명시하며 전체 완료로 닫지 않는다.

### Task 8: 외부 게시 초안과 후속 이전 목록

2026-09-15 개정: 아래 PR 게시 항목은 사용자 직접 수행용 안내다. 에이전트가 생성·게시하지 않는다.

**Files:**
- Update: `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md`
- No external writes before approval.

- [x] push 대상 `codex/harness-pr-centric`와 검증 대상 exact SHA를 마감 문서에 제시한다. 실제 push 미실행.
- [x] 사용자 PR 제목·6절 본문 절차·필수 checks와 ruleset 적용안을 연결한다. 실제 게시 미실행.
- [ ] active 57항목과 HANDOFF 분류 대상 18행을 중복 검토한 Issue 초안을 제시한다. 비밀 내용은 제외하며 과거 '2건'을 현재 제외 목록으로 사용하지 않는다.
- [ ] 사용자 승인 전에는 push·PR·Issue·ruleset 쓰기를 하지 않는다.
- [ ] 병합·배포·기존 기록 삭제는 후속 별도 승인으로 남긴다.

## 계획 자체 수용 기준

마감 실측·사용법·사용자 게시 절차는 `docs/development/harness-transition-handoff.md`에 한 번 기록한다.
아래 세부 체크박스는 단계별 과거 실행 기록이며, 현재 완료 범위는 위 상태표와 마감 실측을 우선한다.

2026-09-15 진입점 검증: product 원문 SHA-256 보존·CLAUDE thin adapter·신규 task 우선 안내 연결.
agent-bridge 111 tests(Windows 10 skipped), harness 자기검사27, legacy selftest19 및 대장235/stage35 대조 green.
상태 실측235=done178/open52/partial3/deferred1/blocked1(active57). Issue 미게시·HANDOFF 검토·legacy 소비자 잔존은 호환 종료와 별도이며 로컬 구현을 멈추는 게시 대기로 삼지 않는다.

- [ ] spec의 유지·교체·이전·폐기 각 행이 적어도 한 Task와 연결된다.
- [ ] 단계마다 명시된 파일, 실패 시험, green 검증, 커밋 경계가 있다.
- [ ] 문서 삭제나 GitHub 쓰기가 로컬 구현과 섞이지 않는다.
- [ ] 계획 검토 후 구현 상태를 `진행 중`으로 바꾼다.
- [ ] 모든 수정 Task는 대상별 `guard-edit`와 명령별 `guard-command`를 첫 단계로 실행한다.
