> spec: dev-package/prd/specs/2026-09-18-harness-evidence-hooks.md
# 하네스 증거 계약 3건 — 측정 레인 종료 훅 · spec 을 WATCH 안으로 · 전수 호출문 정본

**Goal:** 실행기가 이미 쥔 사실 셋을 판정으로 내보낸다 — ⑴ 측정 레인이 증거를 남겼는가
⑵ spec 이 증거 계약 안에 있는가 ⑶ 전수 회차의 입력 선언을 어디서 읽는가.

**출처 intent (전부 승인 2026-09-18)**
- A `dev-package/intent/2026-09-17-measurement-lane-subagent-stop-hook.md`
- B `dev-package/intent/2026-09-17-spec-artifacts-outside-lifecycle-watch.md`
- C `dev-package/intent/2026-09-17-gate-input-env-vars-block-merge-gate.md`

**근거 사슬:** ADR-0005 「2026-09-18 개정」의 후속 ③(WATCH)·④(측정 레인 SubagentStop).
ADR-0006 배치를 지킨다 — 판정 본문은 `.agents/`·`scripts/harness/`, `.claude/`·`.codex/` 는 어댑터다.

## 제약

- 코드·문서만 바뀐다. 제품 코드·DB·계약 0건. 화면 코드 0건.
- ADR-0005 ② (호스트 뮤텍스)는 형제 spec `2026-09-18-gate-host-mutex.md` 의 몫이다.
  이 라운드는 `gates/run.sh`·`gates/tools/_lock.sh` 를 건드리지 않는다.
- PR 게시는 사용자가 한다. 병합·push-to-develop 은 이 레인의 범위 밖이다.

## 커밋

### 1. 측정 레인은 red 를 담은 정합 보고로 닫는다

**Files:** `scripts/harness/hooks/lifecycle_contract.py` · `scripts/tests/test_task_runtime.py`

- [x] `test_task_runtime.py` 의 「측정 레인의 red 도 차단된다」 단언을 승인 문면대로 고쳐 red 확인.
      red 로그 = `ValueError: gate failures remain` (`lifecycle_contract.py:239`).
- [x] `validate_report(..., *, allow_red)` 분기. `verify_task_report()` 가 역할로 값을 고른다.
- [x] 면제되는 것은 red 판정 한 줄뿐 — 행 유효·중복 없음·상태값·exit·계수=행 합·선언 게이트
      전건 존재·트리 증거 대조는 그대로 요구한다.
- [x] `lane-worker` 의 red 차단 무변경을 회귀 시험으로 고정.

### 2. 측정 레인 종료를 같은 훅이 판정한다

**Files:** `scripts/harness/hooks/lifecycle_contract.py` · `scripts/harness/hooks/lane-gate-summary.sh`
· `.claude/settings.json` · `.codex/hooks.json` · `scripts/tests/test_harness_lifecycle_contract.py`

- [x] A-ⓐ~ⓓ 를 먼저 써서 red 확인. red 로그 = `2 != 0 : lifecycle evidence blocked: hook role
      differs from event role`. A-ⓐ~ⓒ 는 **claude·codex 두 경로**를 돌고, A-ⓓ
      (`test_role_outside_the_declared_set_is_rejected_by_the_lane_hook`)는 **claude 단일 경로**다.
      ⚠ codex 경로 시험은 `registered_hooks` 를 patch 하므로 **매처 정규식의 실제 라우팅은 시험이
      증명하지 않는다** — 정규식상 자명하고, 두 파일의 매처 동일성은 `agent-bridge` 가 본다.
- [x] 새 훅 파일 없음 — `harness.yaml:48` `hook_names` 불변(intent A Q3 「신규 훅 기각」).
- [x] 역할은 이벤트 페이로드의 `agent_type` 에서 온다. 매처에는 인자를 실을 자리가 없다
      (`config.py` 어댑터 한 줄 고정 · `agent-bridge.py` 의 인자 없는 command 정규식).
- [x] 매처를 `lane-worker|measurement-lane` 으로 넓힌다. **두 파일 모두 같은 문자열**이다 —
      `agent-bridge.py check()` 가 `.claude/settings.json` 과 `.codex/hooks.json` 의 매처 목록을
      순서까지 동일 비교하므로 codex 쪽에 항목을 늘리면 그 검사가 red 가 된다(spec §A-1 정정).

### 3. spec 을 WATCH 안으로 · researcher 의 spec 선언 거절

**Files:** `scripts/harness/hooks/lifecycle_contract.py` · `scripts/tests/test_harness_lifecycle_contract.py`
· `docs/development/lifecycle-evidence.md` · `.agents/roles/researcher.md`

- [x] B-ⓐⓑ 를 먼저 써서 red 확인. red 로그 = `'unhanded output' not found in 'lifecycle evidence
      blocked: researcher changed files outside output scope or omitted artifacts'` 와
      `ValueError: artifact must be a repository-relative research output`.
- [x] `WATCH` 에 `dev-package/prd/specs/` 한 줄.
- [x] `begin --legacy` 의 산출물 선언에 역할 조건 한 줄 — researcher 는 어느 schema 에서도
      `prd/specs/` 를 선언하지 못한다(우려 #3 · Ted 2026-09-18 판정 ⓑ).
- [x] ⚠ **부수 효과 — `lane-worker` 의 legacy `prd/specs/` 선언은 신규 허용이다.** 종전에는
      `WATCH` 밖이라 `begin` 이 거절했다. spec §B-ⓑ 의 「기존 동작 유지」는 이 점에서 틀렸고,
      `test_harness_lifecycle_contract.py:256-259` 가 새 동작을 단언한다. **판정 영향 0** —
      `stop()` 은 lane-worker 갈래에서 `verify_task_report()` 만 부르고, 그 안의 `artifacts` 검사는
      `colab-task/2` 전용(`lifecycle_contract.py:276-280`)이라 legacy 선언 목록을 읽지 않는다.
- [x] 문서 정합: `lifecycle-evidence.md` 「쓰는 주체는 부모다」 · `researcher.md` 쓰기 범위 한 줄.

**우려 #2 재현 결과 — 재현되지 않는다.** 2026-09-17 관측(researcher 가 spec 을 쓰고 `read-only`
로 닫았다)은 현재 코드로 성립하지 않는다. `snapshot()` 이 `git ls-files --cached --others` 로
트리 전체를 보므로 `read-only`·`draft-return` 은 오늘도 **어떤 변경이든** 막는다(B-ⓐ 가 그것을
시험으로 고정한다). 따라서 이 커밋의 범위는 **선언적 정합**이며 회피 경로를 닫은 것이 아니다.
당시 훅이 발화하지 않았거나 다른 경로였을 개연이 남는다 — 후속 항목으로 올린다.

### 4. 전수 호출문 정본

**Files:** `gates/README.md` · `docs/development/dual-agent.md` · `.agents/roles/measurement-lane.md`
· `docs/decisions/0005-harness-controls-are-declarative.md` · 이 라운드 파일 · `R-HARNESS-PR-CENTRIC.md`

- [x] `gates/README.md` 「돌리기 전」 절에 정본 호출문(전수 1줄 ＋ 측정 레인 `task` 1줄).
      `dual-agent.md` 와 `measurement-lane.md` 는 본문을 복제하지 않고 그 절을 가리킨다.
- [x] `seed-plan-drift` 는 면제가 아니라 `COLAB_REF_ROOT` 실선언이다(intent C 「닫힌 것」).
      명시 면제는 `frontend-visual`·`harness-eval` **2건**.
- [x] ADR-0005 ③④ 를 완료로 갱신한다. ② 는 형제 spec 의 몫이므로 건드리지 않는다.
- [x] 코드 변경 0건.

## 검증

### C-ⓐ — 정본 한 줄을 실제로 돌렸다 (2026-09-18 · 이 호스트 단독)

`COLAB_REF_ROOT` 는 `dev-package/tools/dev-seed/README.md` §0 의 기본 자리(본 체크아웃과 나란한
`03 Reference-Data`)를 실선언했다. 세 게이트 모두 **단독 실행**이고 종료코드 0 이다.

| 게이트 | 모드 | 종료코드 | 출력에 드러난 건수 |
|---|---|---|---|
| `seed-plan-drift` | 실선언 | 0 | datasets 28 · edges 18 · files 543 · bytes 3641736593 (실물 대조 실행) |
| `frontend-visual` | 명시 면제 | 0 | 페이지 0건 · small 0 · lowContrast 0 · 스크린샷 0장 |
| `harness-eval` | 명시 면제 | 0 | 과제 20건(미실행) |

red(준비) 0건. 모델 호출 0건 — `harness-eval` 은 면제형으로만 돌았다.

### 단독 게이트

`agent-bridge` · `harness-contract` · `harness-contract-selftest` 를 이 레인의 선언 집합으로 돌린다.
전수 `all` 은 이 레인의 몫이 아니다(별도 측정 레인).

## 범위 밖

- 실제 `measurement-lane` 서브에이전트를 띄워 훅을 실발화시키는 것. `hook()` 시험이 같은 stdin
  페이로드로 같은 스크립트를 부른다. 실발화는 다음 측정 레인 회차가 자연히 한다.
- `harness-eval` 의 선언형(모델 호출) 실행 · 실브라우저 검증(UI 변경 0건).
- 역할↔훅 매처 대응을 `harness-contract` 가 강제하게 만드는 일반화(intent A Q4 · 별건).
- `lifecycle-evidence.md` 의 「부모의 spec 인계 hash 확인」 구현 · `agent-bridge.py check()` 의
  역할 목록에 `measurement-lane` 보강 · 기존 `prd/specs/**` 소급 증거.
- 커밋 이후의 push·PR 게시·병합·배포·이슈 댓글.
