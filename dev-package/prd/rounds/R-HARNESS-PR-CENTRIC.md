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
- 병합, 배포, 기존 기록 삭제는 각각 별도 승인을 받는다.
- 검사 범위 축소·비활성화·green-by-skip을 금지한다. exit 0/1/78을 그대로 보존한다.
- 새 `.sh`는 Git index mode 100755로 등록한다.
- 같은 checkout의 쓰기 주체는 하나다. 이 계획은 현재 격리 worktree에서 직렬 실행한다.

## 현재 상태

| 단계 | 상태 | 증거/다음 조건 |
|---|---|---|
| 기준선 측정 | 부분 완료 | 정적 3건 green, baseline fresh Codex 시작·훅은 WSL 공식 launcher 부재로 준비 실패 |
| 게이트·CI 재조사 | 완료 | 본 게이트 38+selftest 29, CI/SHA 결함과 문서 입력 의존 확인 |
| 전환 표·계획·수용 기준 | 완료 | 독립 검토의 필수 누락을 반영 |
| 구현·검증 | 진행 중 | 단계별 guard→실패 시험→구현→단독 게이트 |
| 외부 게시 | 승인 대기 전 | 로컬 구현·검증 뒤 초안 제시 |

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
- [ ] CI가 적용 대상 필수 gate 집합을 검증하고 gate summary를 실행 event SHA와 함께 업로드하며 job summary에 3계수를 기록하게 한다.
- [ ] 단위 시험과 workflow 정적 검사를 green으로 만든 뒤 커밋한다.

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
- [ ] 공통 규칙·역할 본문과 skill 인접 resources를 `.agents`로 이동하고 AGENTS/CLAUDE 및 양쪽 역할 adapter를 갱신한다.
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
- [ ] task state가 외부 산출물·gate report를 명시적으로 허용하되 경로·hash·run id를 검증하게 한다.
- [ ] PR template와 checker가 필수 절·Plan-Ref·head SHA·CI/gate 증거를 검증하게 한다.
- [ ] work-item consistency, planning freshness, seam consistency, Slack completion, `gates/run.sh task`가 PR/task evidence를 소비하게 바꾸고 음성 fixture를 유지한다.
- [ ] 유효 결정은 변경 불가 archive+생성 색인으로 보존한다. 기존 sessions/reports 입력은 임시 compatibility read만 허용하고 신규 task 기본값에서는 쓰지 않는다.
- [ ] 임시 호환 입력 허용→외부 PR #35/#38 해소 확인→기존 소비자 0 계측→전환 종료 순서를 checker에 선언한다. 공통 본문 중복 수와 역사 기록 보존 수를 별도 계수로 낸다.
- [ ] 단위 시험·`agent-bridge`·`harness-contract` green 뒤 커밋한다.

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
- [ ] 배포 전 판정기가 같은 full SHA의 main 조상·필수 CI 성공·doctor 단일 실행을 요구하게 한다.
- [ ] deployment와 annotated dev tag 생성은 판정 뒤에만 가능하도록 dry-run 명령을 제공한다.
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
- [ ] `all -j 2~4`는 다른 무거운 작업 없이 1회 실행하고 3계수와 준비 실패를 기록한다.
- [ ] spec 수용 기준을 대조하고 상태 표를 갱신한다.

### Task 8: 외부 게시 초안과 후속 이전 목록

**Files:**
- Update: `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md`
- No external writes before approval.

- [ ] push 대상 `codex/harness-pr-centric`와 exact head SHA를 제시한다.
- [ ] Draft PR 제목·본문·필수 checks와 ruleset 적용안을 제시한다.
- [ ] open/partial/deferred와 HANDOFF 블로커를 중복 제거한 Issue 제목·본문 요약·라벨 목록으로 제시한다. 비밀 2건은 제외한다.
- [ ] 사용자 승인 전에는 push·PR·Issue·ruleset 쓰기를 하지 않는다.
- [ ] 병합·배포·기존 기록 삭제는 후속 별도 승인으로 남긴다.

## 계획 자체 수용 기준

- [ ] spec의 유지·교체·이전·폐기 각 행이 적어도 한 Task와 연결된다.
- [ ] 단계마다 명시된 파일, 실패 시험, green 검증, 커밋 경계가 있다.
- [ ] 문서 삭제나 GitHub 쓰기가 로컬 구현과 섞이지 않는다.
- [ ] 계획 검토 후 구현 상태를 `진행 중`으로 바꾼다.
- [ ] 모든 수정 Task는 대상별 `guard-edit`와 명령별 `guard-command`를 첫 단계로 실행한다.
