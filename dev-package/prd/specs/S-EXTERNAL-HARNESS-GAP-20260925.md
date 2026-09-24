# Spec: 외부 하네스 대비 개선 — 검사 5종 · 레인 범위 대조 · 흐름 템플릿 · 문서 정비
출처 intent: `dev-package/intent/2026-09-25-external-harness-gap.md` (승인 2026-09-25 · Ted "권고댜로" = 전부 ⓐ).
근거: `dev-package/reports/harness/20260925-external-harness-gap/`(G1 · G2 · G3 · 파일:행). advisor ① 2026-09-25 approve-with-changes — 차단급 7 중 6 · 개선 3 반영(7번의 「handoff 거부 시 stop 1회 통과」는 H7 을 약하게 해 불반영 · 대신 출구 2개 명시).
선행: PR #131(`claude/agent-model-tiering`). 이 브랜치는 그 위에 쌓였고 PR 은 #131 병합 뒤 연다.
모든 커밋 메시지 끝에 `Intent-Ref: dev-package/intent/2026-09-25-external-harness-gap.md` 를 단다(이 spec 이 만드는 검사의 첫 대상).

## 문제 진술
- 훅 등록 누락(매처는 두고 명령 1줄 삭제)을 어떤 검사도 잡지 못한다. ADR 전수 검사 지점이 없다. 홈 절대경로 · 자동 로드 줄 상한 검사가 없다. 커밋 → intent 연결이 기계 판독 불가다. 레인 범위 밖 변경을 인계 때 대조하지 않는다. PR 요약에 원한 결과 대조표가 정형으로 없다(G1 · G2 · G3).

## 구현 결정
### 레인 K — 검사·게이트 (파일 계열: `scripts/harness/{config,check}.py`·`.agents/harness.yaml` / `gates/**` / `.github/workflows/ci.yml`·`gates/tools/ci-filter-check.py`)
- **K1 훅 등록 누락**: `.agents/harness.yaml` 에 훅마다 `event`·`matcher` 를 적는 자리를 둔다(기존 `hook_names` 를 넓히든 별도 키든 레인이 고르고 사유를 적는다). `scripts/harness/config.py`(또는 `check.py`)가 `.claude/settings.json` 의 그 event·matcher 항목에 `.claude/hooks/<name>` 명령이 있는지 단언한다. 시험: 매처는 두고 명령 1줄만 뺀 settings 사본 → red · 현재 파일 → green.
- **K2 ADR 게이트** `adr-records`: `gates/run.sh` case → `python3 scripts/harness/adr_gate.py --all`(현 CLI 확인). `gates/config/parallelism.toml` 선언 · `gates/README.md` 행 · `.agents/harness.yaml` 필수 게이트 목록(해당 키가 있으면). CI: `changes` 의 `dev-package` 필터(`ci.yml`)에 `docs/decisions/**` 를 추가하고 그 필터를 소비하는 잡에 `adr-records` 를 넣는다. **모델을 부르는 `harness` 필터는 손대지 않는다**(`ci-filter-check.py` 축자 대조 대상). `gates/tools/ci-filter-check.py` 에 대조 1항 추가: `docs/decisions/0001-….md` 가 `dev-package` 필터에 잡힌다. 시험: 필수 항목이 빠진 ADR fixture → red.
- **K3 홈 절대경로**: `harness-contract` 확장. 대상 = `AGENTS.md`·`CLAUDE.md`·`.agents/**`·`.claude/**`·`.codex/**`·`docs/**`(바이너리 제외). 패턴 = `/home/<u>/`·`/Users/<u>/`·`C:\Users\<u>\`·`/mnt/c/Users/<u>/`. 허용 = `/home/user/`(git-guard 예시) 등 명시 목록. 시험: fixture 로 red · 현재 트리 green.
- **K4 자동 로드 줄 상한**: `.agents/harness.yaml` 에 `always_on_max_lines: 120` · 대상 `AGENTS.md`·`CLAUDE.md`·`.claude/rules/*.md`. 초과 → `harness-contract` red. 시험: 121행 fixture → red.
- **K5 Intent-Ref 검사**(판정 · red): 새 게이트 `intent-ref`(`gates/tools/intent-ref.sh` 또는 py). 입력 = 기준 ref(`COLAB_INTENT_REF_BASE`, CI 는 PR base sha). 미선언이면 `git merge-base HEAD origin/develop` 를 기준으로 쓰고 출력에 그 사실을 찍는다. 그 ref 도 없을 때만 78(준비). 로컬 `gates/run.sh all` 이 호스트에서 늘 78 을 내지 않게 한다.
  - ⑴ 범위 안 커밋 중 **적어도 1개**가 `Intent-Ref: dev-package/intent/<파일>.md` 트레일러를 갖고 그 파일이 존재해야 한다(빈 커밋의 트레일러도 인정 — 트레일러 없는 기존 브랜치의 소급 경로 = `git commit --allow-empty` 1개) — 단 PR 이 `services/**`·`frontend/src/**`·`contracts/**`·`db/**`·`scripts/**`·`gates/**`·`.agents/**`·`.claude/**`·`.codex/**` 중 하나라도 바꿀 때만. 문서만 바꾼 PR 은 대상 밖(출력에 「대상 밖」과 건수).
  - ⑵ 기준 ref 에서 **승인 표기가 있는 intent**(메타 줄에 `승인` 이 있고 `미승인` 이 없음)의 본문이 범위에서 **삭제·변경**되면 red. 줄 추가만 허용한다 — 기존 줄의 오타·서식 수정도 red(재개봉 금지와 같은 뜻 · 필요하면 새 intent). 판별식은 현행 intent 62건 정답표를 시험 fixture 로 고정한다: 승인 44 · 미승인 13 · 메타 줄 없음 5 · `TEMPLATE.md` 는 이름으로 제외 · 알려진 오판 1건(`2026-09-08-harness-evals.md` 실제 승인 · 규칙상 비보호)은 「의도된 비보호」로 시험에 적는다(레인이 실측으로 수치를 다시 확인하고 다르면 보고).
  - CI: `pull_request` 이벤트이고 `github.base_ref != 'product'` 일 때만 base..head 로 실행 · `actions/checkout` `fetch-depth: 0` · `changes` 를 거치지 않는 독립 잡 또는 `dev-package` 필터 잡. promotion·release 워크플로는 제외. 시험: 트레일러 없음 → red · 있는데 파일 없음 → red · 승인 intent 줄 삭제 → red · 줄 추가 → green · 문서만 → 대상 밖 green · 기준 ref 미선언 → 78.
  - 트레일러 규칙 문장은 레인 L 이 `colab-v2-work/SKILL.md` 에 쓴다(L4).
### 레인 L — 레인 범위 대조 · 흐름 · 문서 (파일 계열: `scripts/harness/hooks/lifecycle_contract.py`·`scripts/harness/task_state.py`·시험 / 템플릿 / 문서)
- **L1 레인 범위**: `lifecycle begin --role lane-worker --scope <glob>`(여러 번). 범위가 선언된 task 의 `handoff --mode complete` 는 baseline 대비 변경 파일 중 범위 밖이 있으면 차단하고 목록을 낸다. 기본 허용(선언 불요) = 그 task 의 runtime·증거 경로 · `dev-package/reports/**` · `docs/development/lifecycle-evidence.md`. 차단 메시지에 출구 2개를 적는다 — ⑴ `begin --scope` 로 범위를 넓혀 새 task 를 연다 ⑵ 범위 밖 변경을 되돌린다. H7/`stop()` 은 약하게 만들지 않는다(출구가 있어 반송 루프가 되지 않는다). 선언 없으면 현행 동작. baseline 정의(begin 시 HEAD · untracked 포함 여부)는 레인이 `lifecycle_contract.py` 에서 확인해 보고서에 적는다. `docs/development/lifecycle-evidence.md` 에 한 문단 · `.agents/roles/lane-worker.md` 에 한 줄. 시험: 범위 밖 변경 → handoff 거부 · 범위 안 → 통과 · 미선언 → 현행.
- **L2 PR 가치 표**: `.github/pull_request_template.md` 에 「원한 결과 ↔ 실제 ↔ 근거」 표와 가치 상태 4종(확인됨 · 부분 확인 · 미검증 · 미달)을 넣고 기존 절(목적 · 범위 · 계획 · 결정 · 검증 · 남은 제약)과 「게시 절차」「병합 뒤」 관행을 해치지 않는다.
- **L3 intent·spec 템플릿**: `dev-package/intent/TEMPLATE.md` 에 「가치 가설」 절 · `.agents/skills/to-spec/SKILL.md` 에 원한 결과 식별자(V1…) 와 UI spec 의 선택 항목 `mockup.html`(수기 HTML · 명시 호출 전용 스킬을 부르지 않는다).
- **L4 문서 정비**: `docs/development/dual-agent.md` — 하네스 판정 질문 4~5줄(각 줄 기존 ADR 링크 · ADR-0005 「선언이며 OS 강제가 아님」과 모순 없게) · 「하네스 변경 절차」 절 · 「공통 스킬 13개」 정정. `docs/decisions/README.md` 「언제 남기나」 4항목 · ADR-0006 대안 절에 symlink 미채택 사유 1줄 · `.agents/skills/VENDORED.md` 출처별 커밋 SHA·파일 SHA-256(재다운로드로 확인 · 못 구하면 「미확인」). `.agents/skills/colab-v2-work/SKILL.md` 에 Intent-Ref 규칙 한 줄 + 소급 경로 한 줄(트레일러 없는 기존 브랜치는 `git commit --allow-empty -m "…" -m "Intent-Ref: …"` 1개).
- **L5 보류 기록**: intent 의 보류 7행(재검토 조건 포함)을 `docs/development/dual-agent.md` 판정 질문 절 아래 「보류 중인 외부 장치」 목록으로 옮긴다(7줄).

## 시험 결정
- 각 항목의 수정 전 red → 수정 후 green 을 보고서에 인용한다.
- 레인 K 게이트: `harness-contract` · `harness-contract-selftest` · `adr-records`(신설) · `intent-ref`(신설 · 이 브랜치 base = `origin/claude/agent-model-tiering` 로) · `exec-bit` · `agent-bridge`.
- 레인 L 게이트: `agent-bridge`(lifecycle 시험 포함) · `harness-contract` · `planning-freshness` · `work-item-consistency` · `exec-bit`.
- 병합 뒤 오케스트레이터가 합집합 + `gates/run.sh all` 1회.

## 정책 대조
- 새 Claude/Codex 훅 0 · `/hooks` 재신뢰 0. 제품 코드 0. ADR-0003(adr_gate 는 CLI · 훅 없음)과 정합 — 게이트로만 붙인다. ADR-0005 개정 「무의미하거나 판정이거나」 — K5 는 판정(red), 대상 밖은 건수 출력.

## 범위 밖
- 보류 7 · 불채택 4(intent 설계트리) · `product.md`·`colab-rules.md` 분량 축소 · 제품 코드.

## 산출 계획
- 레인 K · 레인 L 병렬(`lane-worker` · `isolation: worktree` · 기준 `origin/claude/harness-external-gap` — intent 승인본·spec 커밋 포함 · 스폰 전 push 확인). 시험 파일 소유: K = `scripts/tests/test_harness_config.py` 계열·게이트 selftest / L = `scripts/tests/test_task_runtime.py`·lifecycle 시험 · 새 시험 파일은 각자 새 이름. K5 게이트는 `gates/config/parallelism.toml` 에 `parallel` 로 선언하고 `.sh` 면 `exec-bit` 대상이다. 파일 면 무겹침(`colab-v2-work/SKILL.md`·`dual-agent.md` 는 L, `.agents/harness.yaml`·`gates/**`·`ci.yml` 은 K). 레인은 자기 브랜치 커밋까지.
- 병합·게이트 전수·advisor ②·PR 은 오케스트레이터.
