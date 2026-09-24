# ⚠ 보류 — 이 spec 은 1차 권고 기준의 초안이며 구현 근거가 아니다
Ted 결정 2026-09-24: "저대로만 개선하기보다 진지하게 따져보고 개선하는게좋을듯하니" → intent `dev-package/intent/2026-09-24-harness-lane-hygiene.md` 의 「진지하게 따질 것」에 답한 뒤 다시 쓴다. 착수했던 레인은 중단(커밋 0).

# Spec: 하네스 고도화 — 턴 한도 재단 규칙 · 증거 경로 규격 · 레인 뒤처리 훅 · advisor ① 생략 기준
출처 intent: `dev-package/intent/2026-09-24-harness-lane-hygiene.md` (승인 2026-09-24 · Ted 원문 "권고대로 해서 하네스고도화하고")

## 문제 진술
- 서브에이전트가 턴 한도에서 산출물 없이 끝난다(researcher 0바이트 2회 · advisor 2회 · lane 1회). 레인 게이트 증거가 Git common dir 에만 있어 advisor ② 가 못 찾는다. 레인 종료 뒤 브라우저·프리뷰 프로세스가 남아 다음 게이트 잠금을 쥔다. 작은 단계에도 advisor ① 이 붙어 비용이 같다.

## 해법 개요
- 규칙·역할·스킬 본문에 수치 규칙 4개를 넣고, `lifecycle handoff` JSON 에 증거 경로를 담고, `SubagentStop` 훅 하나로 워크트리 cwd 프로세스를 정리한다. 제품 코드는 건드리지 않는다.

## 사용자 스토리
1. 오케스트레이터로서 조사·레인 지시문을 쓸 때 범위 상한을 규칙에서 읽고 싶다.
2. advisor ② 로서 게이트 증거 경로를 handoff JSON 에서 바로 받고 싶다.
3. 오케스트레이터로서 레인이 끝나면 브라우저·프리뷰가 스스로 정리되길 바란다.
4. 오케스트레이터로서 어떤 단계에 ① 을 생략해도 되는지 수치 기준을 갖고 싶다.

## 구현 결정
- **① 재단 규칙**(정본 = `.agents/rules/colab-rules.md` 새 절 `1-6. 서브에이전트 지시 범위는 턴 한도로 재단 — subagent-scope-by-turn-budget.md`):
  - researcher(30턴): 조사 절 **2~3개/건** · 지시문에 「**10번째 도구 호출 전에** 산출 파일을 한 번 쓴다(가진 것 전부 · 미완 절은 `[미완]`)」 · 반환은 경로 + 10줄 요약.
  - lane-worker(200턴): 파일 면(계열) **2~3개/건** · 단계마다 커밋 · 「한도 근접 시 green 상태로 커밋·보고서 진행표·정직한 미완 목록으로 handoff」.
  - advisor(12턴): 「**도구 호출 8회 이하** 뒤 판정 · 깨끗하면 깨끗하다고」.
  - 역할 본문(`.agents/roles/{researcher,lane-worker,advisor}.md`)에 각 1문장 + 스킬 `colab-v2-work/SKILL.md §1` 지시문 체크리스트에 항목 1개. 세 곳은 수치를 **규칙 절을 가리켜** 적는다(복제 아님). `.codex/agents/*.toml` 이 역할 본문을 읽는지 확인해 그대로면 무변.
- **② 증거 경로 규격**:
  - `scripts/harness/hooks/lifecycle_contract.py` `main()` 의 `handoff` 분기: `mode == 'complete'` 이고 `task['role'] in GATE_ROLES` 일 때만 JSON 에 `"evidence": {"gate_summary": "<절대경로>", "sha256": "<digest()>", "task_id": …, "run_id": …}` 를 붙인다. 경로는 **지어내지 않고** `resolve_task_path(root, task, task['report'])` 에서 파생한다(colab-task/2 는 `runtime().resolve` · legacy 는 `inside()`). 기존 키 무변(`stop()` 은 `.get` 만 쓰고 키 집합을 검사하지 않음 · `validate_report` 는 gate-summary 쪽 검증이라 무관 — advisor ① 확인). 선택: `stop()` 이 `evidence` 가 있으면 그 경로가 선언된 report 경로와 같은지 대조.
  - `.agents/roles/lane-worker.md`·`measurement-lane.md` 「완료 조건과 보고」: 최종 메시지 항목에 「증거 경로(handoff JSON 의 `evidence.gate_summary`·`sha256` 그대로)」 필수.
  - `.agents/roles/advisor.md` 「입력」: 「게이트 증거는 handoff JSON 의 `evidence.gate_summary` 가 가리키는 파일 — 오케스트레이터가 확인했다고 적으면 재실행하지 않고 문서·코드 대조에 집중」(디렉터리 배치를 문면으로 박지 않는다).
  - `docs/development/lifecycle-evidence.md` 인계 절에 JSON 예시 갱신.
- **③ 뒤처리 훅** `scripts/harness/hooks/lane-cleanup.sh`(원본) + `.claude/hooks/lane-cleanup.sh`(어댑터 · 기존 `worktree-setup.sh` 어댑터와 같은 꼴):
  - 이벤트 `SubagentStop` · matcher `lane-worker|measurement-lane|researcher`. 첫 줄은 다른 훅과 같은 `[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0`.
  - **대상 판정은 경로 접두어가 아니라 toplevel 일치**: stdin JSON 의 `cwd` 를 `git -C <cwd> rev-parse --show-toplevel` 로 정규화(`lifecycle_contract.py` `checkout()` 과 같은 방식)하고, 그 toplevel 이 **주 체크아웃**(`git worktree list` 첫 행)이면 「주 체크아웃 · 건너뜀 · 0」을 내고 exit 0 한다(레인 워크트리가 주 체크아웃 경로 **아래**에 있으므로 접두어 판정은 전 워크트리·오케스트레이터의 브라우저까지 죽인다). 후보 = `/proc/*/cwd` 를 같은 방식으로 정규화해 toplevel 이 **일치**하는 프로세스 중 이름이 `agent-browser*` · `node …vite preview` 인 것. chrome 은 cwd 가 `/` 일 수 있으므로 cwd 로 고른 agent-browser 데몬의 **자손**(`/proc/*/stat` ppid 추적)으로 정리한다. SIGTERM → 2초 뒤 SIGKILL.
  - 출력 = `{"systemMessage": "레인 뒤처리: agent-browser n · chrome n · vite preview n 종료"}`(대상 0건이면 「정리 0」) · **항상 exit 0**(비차단 · `worktree-setup.sh` 원칙). `/proc` 이 없는 환경은 「미지원 · 0」 exit 0.
  - **순서**: 같은 SubagentStop 의 별도 matcher 훅은 병렬로 실행되어 `lane-gate-summary.sh`(H7)와 순서가 보장되지 않는다. H7 이 exit 2 로 막아 레인이 계속 작업할 때 브라우저·프리뷰는 이미 종료된 상태일 수 있다 — agent-browser 는 다음 명령에서 데몬을 다시 띄우고 `capture.py` 는 프리뷰 서버를 스스로 띄우므로 **이 영향을 받아들인다**(spec 결정).
  - 등록: `.claude/settings.json` SubagentStop 항목 1개 추가 · `.codex/hooks.json` 은 **무변 확인**(SubagentStop 이 이미 `researcher`·`lane-worker|measurement-lane` 로 발화하고 `scripts/agent-bridge.py` `registered_hooks()` 가 `.claude/settings.json` matcher 를 `re.fullmatch` 로 전달한다) · `scripts/harness/config.py` 가 읽는 계약의 `adapters.required_files` 에 어댑터 등록 여부 확인 · `docs/development/dual-agent.md` 「자동 훅 등록 상태」 훅 수(9 → 10)와 재신뢰 안내 갱신 · 새 `.sh` 3개(원본·어댑터·selftest) `git update-index --chmod=+x`(규칙 `4-3`).
  - selftest `gates/tools/lane-cleanup-selftest.sh`(+ `gates/run.sh` 등록 · `parallelism.toml` · README 행): ⓐ 워크트리 cwd 로 띄운 `sleep` 가짜 프로세스(이름 패턴 맞춤 · `exec -a`)는 종료 ⓑ 다른 toplevel 의 같은 이름은 생존 ⓒ 대상 0건 → 「정리 0」 ⓓ stdin 에 cwd 없음 → 「미지원 · 0」 exit 0 ⓔ 하위 `.claude/worktrees/x` 의 프로세스는 상위 워크트리 stop 에서 생존 ⓕ 주 체크아웃 stop → 「건너뜀 · 0」. 자손 추적(chrome)은 가짜 프로세스로 드러나지 않으므로 **실제 agent-browser 1회 smoke**(데몬 띄우고 stop 이벤트를 흉내내 종료 확인)를 하고, 못 하면 「미검증」으로 보고한다.
- **④ advisor ① 생략 기준**(`colab-v2-work/SKILL.md §2` 표 아래 문단 + 규칙 `1-6` 에 같은 수치): ① 생략 가능 = spec **60행 이하이고 4,000자 이하**(긴 행 우회 봉쇄) ∧ 새 게이트·훅·마이그레이션·**계약 변경 없음**(계약 = `contracts/**` · handoff/gate-summary JSON · `.claude/settings.json` 훅 · 역할 권한) ∧ 제품 코드 변경 파일 **3개 이하** ∧ **변경 면을 직접 판정하는 기존 게이트 이름을 명시**(시각 변경 0 캡처 대조 등 · 아무 게이트나 끌어오지 못하게). 하나라도 깨지면 ①. ② 는 항상. **③(비가역·사용자 노출 go/no-go)은 생략 대상이 아니다.** 생략했으면 보고서에 네 조건의 충족 근거를 적는다. 근거 문장: 「2026-09-24 디자인 구조 P0~P3 에서 ① 이 차단급 결함 3건을 잡았다」.
- **규칙 파일 형식**: `colab-rules.md` 절 제목 옆 `*.md` 는 메모리 이관본의 표지일 뿐 실제 파일이 없다(advisor ① 확인) — 새 파일을 만들지 말고 `## 1.` 의 마지막 자리에 `1-6` 절만 더한다. `.codex/agents/*.toml` 은 실행 시 `.agents/roles/*.md` 를 읽으므로 무변.
- 스키마 · 마이그레이션: 없음. API 계약: 비파괴.

## 시험 결정
- ⓐ `lane-cleanup-selftest` 4케이스 기대대로 · `gates/run.sh lane-cleanup-selftest` exit 0.
- ⓑ `lifecycle handoff --mode complete` 가 `evidence.gate_summary` 를 내고 그 경로의 파일이 실존(레인 자신의 handoff 로 증명) · `harness-contract-selftest`·`gate-host-mutex-selftest` 등 기존 하네스 게이트 green.
- ⓒ 규칙·역할·스킬 문장 실존(grep · 세 곳이 규칙 절 이름을 가리킴) · `dual-agent.md` 훅 수 갱신.
- ⓓ `work-item-consistency`·`planning-freshness`(dev-package 문서 변경 시) green.
- 해당 서비스 단독 게이트: `lane-cleanup-selftest`(신설) · `harness-contract-selftest` · `gate-host-mutex-selftest` · `work-item-consistency` · `planning-freshness` · `exec-bit`.
- green-by-skip 방지: selftest 대상 0건 케이스가 「정리 0」 문자열을 요구 · handoff JSON `evidence` 키 부재·경로 불일치는 `scripts/tests/test_task_runtime.py` 에 케이스 추가(이 파일이 `harness-contract-selftest` 에서 도는지 레인이 확인하고, 안 돌면 그 사실을 보고).

## 정책 대조
- `product.md §3·§5` 저촉 없음(제품 코드 0 · 게이트 우회 0 · 절대경로 0). `harness-eval` 면제 모드 유지. 계약 동결 해제: 아니오.
- 훅 정의 변경 → 이 PC `/hooks` 재신뢰 필요(사용자 몫 · 보고서에 명시).

### 디자인 제약 확인
대상 화면: 해당 없음(하네스 전용).

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 뒤처리 훅이 researcher 에도 걸리면 조사 중 띄운 브라우저도 죽는다 | 셋 다(레인·측정·조사) | 레인·측정만 | ⓐ · 조사도 agent-browser 를 쓴다(P0 DOM 질의) |
| 2 | `evidence` 키 추가가 H7 대조를 깨는지 | 키 무시 확인 후 추가 | 별도 파일 | ⓐ |

## 범위 밖
- maxTurns 변경 · `harness-eval` 승격 · 디자인 구조 코드 · 커밋·push·PR 게시(사용자).

## 산출 계획
- 레인 1(직렬 · P2b 레인과 파일 면 무겹침 · 게이트는 호스트 뮤텍스가 직렬화) · `lane-worker` · `isolation: worktree` · 기준 = 통합 브랜치. 보고서 `dev-package/reports/harness/20260924-lane-hygiene/report.md`.
