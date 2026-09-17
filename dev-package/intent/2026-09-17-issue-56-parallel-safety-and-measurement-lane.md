# Intent: 병렬 안전성을 전 게이트가 선언하고, 전수 측정 레인이 task 증거를 남긴다
메타 — 발의자: sungwooHa(이슈 #56) · 방향 결정: Ted · 작성 2026-09-17 · 승인 2026-09-17(advisor 검토 결과 제시 후 Ted 명시 승인)

## 문제
- ⑴ `gates/config/parallelism.toml` 의 선언이 `gates/run.sh:180-201` `ALL_GATES` 를 덮지 못한다. **현재 실물은 `ALL_GATES` 71건 · 선언 61건 · 미선언 10건**이다. 이슈 본문의 「67 ↔ 59 · 8건」은 발견 시점(2026-09-14) 값이며 그 뒤 `product-release-selftest` · `product-reseed-selftest` 2건이 `ALL_GATES` 에 추가되면서 미선언이 10건으로 늘었다. 선언표에만 있고 `ALL_GATES` 에 없는 이름은 0건이다.
- 미선언은 `gates/run.sh:700` 에서 `solo_gates` 로 접히고 `:716` 이 「**미선언 — 안전한 쪽을 골랐다.**」를 매 전수마다 출력한다. 10건이 단독으로 도는 만큼 전수 시간이 늘고, 경고가 상시 출력이라 신호가 아니다.
- ⑵ 전수만 재는 레인은 task 를 열 수 없다. `scripts/harness/hooks/lifecycle_contract.py:149` 가 역할을 `('researcher', 'lane-worker')` 로 제한하고, `:156-157` 이 lane-worker 에 게이트 선언을 요구하며(`'lane requires explicit gates'`), `:158` 이 researcher 의 게이트 선언을 막는다(`'research task must not declare implementation gates'`). 게이트를 실제로 도는 `gate_start` 는 `:342-343` 에서 `if gate in ('all', 'task'): raise ValueError('declare concrete gates, not nested group selectors')` 로 전수 선택자를 거절한다.
- 그 결과 `handoff --mode complete` 의 `:302` `'lane completion requires current gate evidence'` 검사에 전수 결과가 닿지 못한다. `gate-runner` 는 `.agents/roles/gate-runner.md:5` 「`bash gates/run.sh all -j <N>`」 를 글자 그대로 도는 역할이고 `:6` 에서 **부모가 준** `COLAB_TASK_ID` 를 유지할 뿐 스스로 task 를 열지 않는다. 전수 결과는 `gate-summary.json` 증거가 아니라 회차 기록의 산문으로만 남는다(이슈 본문 근거 `R-DATA-CANON.md` §11).

## 원한 결과 (proposed outcome)
- `gates/run.sh all` 요약의 「병렬 안전성 **미선언** N건」 줄(`gates/run.sh:796-797`)이 0건이 되어 출력되지 않는다.
- 미선언 10건이 각각 `parallel`/`serial` 로 근거 한 줄과 함께 `parallelism.toml` 에 선언된다.
- 게이트를 신설하면 선언 없이는 전수가 통과하지 못한다 — 승격 상태는 `red(준비 · 입력미선언 · 78)` 다(아래 제약 참조).
- 전수만 재는 레인이 `begin` 으로 task 를 열고 종료 시 전수 `gate-summary.json` 을 그 task 의 증거로 남긴다.
- 게이트 로직·판정·종료코드는 한 줄도 바뀌지 않는다(ADR-0004 「게이트 로직을 고쳐 요약을 맞추기 — 배제」).

## 영향 범위
- 사용자 / 화면: 없음. 제품 코드·계약·DB 무변경.
- 하네스: `gates/config/parallelism.toml`(선언 10건 추가) · `gates/run.sh`(미선언 승격 분기) · `gates/README.md`(신설 규약) · `scripts/harness/hooks/lifecycle_contract.py`(측정 역할) · `.agents/roles/`·`.claude/agents/`(역할 파일) · `scripts/tests/test_harness_lifecycle_contract.py`·`scripts/tests/test_task_runtime.py`(시험).
- 계약 파괴 여부: 선언 추가만 하면 아니오. 미선언 승격을 `colab-gate-summary/1` 의 `counts` 에 새 키로 노출하면 예(ADR-0004 재검토 조건 — `.agents/harness.yaml:30` `report_schema`).

### 미선언 10건의 병렬/직렬 판정과 근거
| 게이트 | 판정 | 독점 자원 한 줄 근거 |
| --- | --- | --- |
| `agent-bridge` | parallel | `gates/run.sh:206` 이 `python3 -m unittest` 6개 모듈만 돈다. 격리는 `scripts/tests/test_task_runtime.py:18`·`test_harness_lifecycle_contract.py:28` 의 `tempfile.TemporaryDirectory()` 이고 포트·컨테이너·psycopg·docker 문자열이 4개 시험 파일에 0건이다. |
| `seed-plan-drift` | parallel | `gates/tools/seed-plan-drift.sh` 가 커밋된 등재표와 md 를 대조만 한다. `mktemp`·포트·`docker`·`_pg.sh` 히트 0건이고 `COLAB_REF_ROOT` 는 읽기 입력이다(`gates/run.sh:232-235`). |
| `seed-plan-drift-selftest` | parallel | `gates/tools/seed-plan-drift-selftest.sh:38` `WORK="$(mktemp -d …)"` — `:15` 「판정은 `mktemp -d` **사본**에서만」, 픽스처 원본은 읽기 전용. |
| `dev-reseed-selftest` | parallel | `gates/tools/dev-reseed-selftest.sh:13` 「`ssh`·`scp`·`docker`·`aws`·`agent-browser` 를 PATH 대역으로 가려 **실물에 한 바이트도 나가지 않는다.**」 — 실브라우저·원격·컨테이너를 잡지 않는다. |
| `frontend-visual` | **serial** | `gates/tools/frontend-visual.sh:61` `command -v agent-browser` 를 요구하고 실제 페이지를 연다 — 실브라우저(단일 프로필)가 독점 자원이다. |
| `frontend-visual-selftest` | **serial** | `gates/tools/frontend-visual-selftest.sh:8` 「`agent-browser 0.27.0` 이 `file://` 을 여는 것은 이 세션에서 실측했다」 — 같은 판정부를 `:45-50` 에서 3회 호출하므로 같은 브라우저 자원을 잡는다. |
| `harness-eval-selftest` | parallel | `gates/tools/harness-eval-selftest.sh:39` `WORK="$(mktemp -d …)"` · `gates/run.sh:24` 「모델 호출 0회(스텁)」 — 외부 호출·고정 경로 없음. |
| `is4-recovery-selftest` | parallel | `infra/staging/tunnel/rehearse-state-recovery-selftest.sh:63` 「실제 Cloudflare/Terraform 없이」 · `:72` `TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" …)"` — 원격 접촉 0. |
| `product-release-selftest` | parallel | `gates/tools/product-release-selftest.sh:163-165` 가 `--junitxml="$(mktemp)"` 로 pytest 를 돈다. venv python 은 읽기(`:120-122`)이고 DB·포트를 잡지 않는다. |
| `product-reseed-selftest` | parallel | `gates/tools/product-reseed-selftest.sh:190-192` 주석 「The service-wide autouse real-DB fixture belongs to service-tests-core-api.」 — `--noconftest` 로 실DB fixture 를 배제하고 junitxml 은 `mktemp`(`:188`). |

판정 결과: serial 2건(`frontend-visual` · `frontend-visual-selftest`) · parallel 8건.

## 제약
- 미선언 승격의 상태는 `red(판정)` 이 아니라 `red(준비 · 입력미선언 · 78)` 다. 이슈 완료 조건 ⑴ 의 「red(판정)으로 승격」과 ADR-0004 사이의 충돌이며, 이 intent 는 ADR 쪽을 따른다. 근거 — `gates/run.sh:757` 「가르는 축은 하나다 — **대상이 판정됐는가.** 셋째 범주를 만들지 않는다.」 병렬 선언 누락은 대상이 규율을 어긴 것이 아니라 입력이 선언되지 않은 것이고, `AGENTS.md:46` 「아무 선언도 없으면 준비 실패로 처리한다」가 그 자리를 이미 정한다(ADR-0004 「입력의 세 상태」).
- 계수는 다시 세지 않는다(ADR-0004 · `gates/README.md:102`). 현재 `undeclared_gates` 는 `gates/run.sh:695-702` 의 실행 계획 변수일 뿐 요약 JSON 의 `counts` 에 들어가지 않는다(`:763`·`:803-804` 의 4계수는 `n_green`·`n_red_judge`·`n_red_ready`·`n_undeclared_input`). 승격은 기존 `n_undeclared_input` 축에 얹어야 하고, 새 키를 만들면 `colab-gate-summary/1` → `/2` 이며 ADR-0004 재검토 조건에 걸린다.
- 병합 진입 조건은 두 red 가 모두 0 이다(ADR-0004 · `gates/README.md:112`). 승격은 선언 10건을 먼저 넣은 뒤에만 켤 수 있다. 순서를 뒤집으면 전수가 즉시 78 로 막힌다.
- 게이트를 도는 레인은 한 번에 하나다(ADR-0002). 이 intent 가 만드는 측정 레인도 예외가 아니며, `gates/run.sh` 의 호스트 전역 뮤텍스 부재와 `_pg.sh` 슬롯 전역 공유는 **이 이슈의 범위가 아니다**(ADR-0002 재검토 조건의 2026-09-17 정정).
- 훅·역할 정의는 선언이며 OS 강제가 아니다(ADR-0005). 측정 역할 신설은 권한 부여가 아니라 증거 계약의 한 줄이다. `AGENTS.md:49` 「문서나 에이전트 역할 정의 자체가 새 권한을 부여하지 않는다.」
- 본문 소유는 `.agents/`·`scripts/harness/` 다(ADR-0006). 실물이 이미 그렇다 — 판정부는 `scripts/harness/hooks/lifecycle_contract.py`(489행)이고 `.claude/hooks/lifecycle_contract.py`(6행)는 `runpy.run_path` 로 그것을 불러오는 어댑터다. 역할도 같다 — `.claude/agents/gate-runner.md:13` 「본문은 저장소 루트 기준 `.agents/roles/gate-runner.md`를 읽고 따른다.」 **따라서 수정은 `scripts/harness/` 와 `.agents/` 에 들어가고 `.claude/` 에는 등록만 한다.**
- 승인은 사람이 한다(ADR-0003). 이 판정에 자동 Stop/PreToolUse/UserPromptSubmit 훅을 걸지 않는다.

## 설계트리 (grill-me 결과)
- Q1 8건인가 10건인가 → A 10건이다. 이슈는 발견 시점 값이고 `product-release-selftest`·`product-reseed-selftest` 가 그 뒤 `ALL_GATES` 에 들어왔다. 선언표를 고치는 작업은 **실물 대조를 매번 다시 한다.**
- Q2 미선언을 `red(판정)` 으로 올리는가 → A 아니다. `red(준비 · 입력미선언 · 78)` 다. 판정 축은 「대상이 판정됐는가」 하나고(`gates/run.sh:757`) 선언 누락은 입력 쪽이다(ADR-0004). 이슈 완료 조건과 어긋나므로 Ted 판단 항목으로 올린다.
- Q3 ⑵ 를 `--gate all` 허용으로 푸는가, 측정 전용 역할 신설로 푸는가 → A **측정 전용 역할 신설.** 근거는 아래 Q4·Q5.
- Q4 `--gate all` 허용의 비용은 → A 증거 검사가 기대는 성질을 깎는다. `gate_start` 는 `:360` 에서 `targets=dict(requested='task', selected=task['gates'])` 로 **선언한 구체 이름 집합**을 증거에 박고, `handoff --mode complete`(`:302`)와 `:464` 「`single gate differs from declared task set`」가 그 집합에 기댄다. `'all'` 을 넣으면 선언 시점과 실행 시점의 `ALL_GATES` 가 달라도 같은 증거로 보이고, 선택자 확장을 기록해도 「무엇을 선언했는가」와 「무엇이 돌았는가」를 가르는 자리가 사라진다. ADR-0005 가 「기계가 실제로 강제하는 것은 게이트 종료코드와 작업 증거 계약뿐」이라고 못박은 그 두 가지 중 하나를 얇게 만드는 변경이다.
- Q5 역할 신설이 ADR 과 맞는가 → A 맞는다. ADR-0002 가 요구하는 「게이트 레인은 단독」을 역할 본문의 선언으로 그대로 옮길 수 있고(ADR-0005 — 선언이지 OS 강제가 아니다), ADR-0006 대로 본문은 `.agents/roles/` 에 두고 `.claude/agents/` 는 얇은 어댑터로 둔다. ADR-0003 과도 무관하다 — 역할은 승인을 만들지 않는다.
- Q6 바꿀 자리는 → A `scripts/harness/hooks/lifecycle_contract.py` 의 역할 화이트리스트 `:149` · 게이트 선언 규칙 `:156-158` · 역할 검사 `:226-227`·`:309-310` · 완료 검사 `:302` · 선택자 거절 `:342-343` · 증거 `targets` `:359-360` · CLI `choices` `:418` · `:464`. 신규 `.agents/roles/gate-measurer.md` 와 `.claude/agents/gate-measurer.md`(어댑터). 필요하면 `.agents/harness.yaml` 의 `sources`(39-50) · `adapters`(51-61).
- Q7 시험은 어디에 → A `scripts/tests/test_harness_lifecycle_contract.py`(현재 `:28` `tempfile.TemporaryDirectory()` 기반 · 240행대에 게이트 종료코드 픽스처)와 `scripts/tests/test_task_runtime.py`(`:87` 이 `begin(..., 'lane-worker', gates=['check'], …)` 로 이미 같은 축을 잡는다). 두 파일은 `agent-bridge` 게이트가 돈다(`gates/run.sh:206`).
- Q8 `gate-runner` 를 고치는가 → A 아니다. `gate-runner` 는 명령을 글자 그대로 도는 실행기다(`.agents/roles/gate-runner.md:5-7`). task 를 여는 주체는 부모이고, 측정 역할이 그 부모 자리를 채운다. `gate-runner` 본문은 건드리지 않는다.
- Q9 전수 시간이 실제로 줄어드는가 → A 미측정. 게이트 실행 금지 제약(다른 레인과 충돌) 때문에 이번 조사에서 재지 않았다. 미해결 질문으로 남긴다.

## 미해결 질문
- 선언 8건을 `parallel` 로 돌렸을 때 전수 시간이 실제로 얼마나 줄고 판정이 유지되는지 — 미측정. 이 조사는 게이트를 한 번도 돌리지 않았다(다른 레인과의 충돌 회피 · ADR-0002). 구현 레인이 단독 구간에서 `-j` 값을 고정해 실측해야 한다.
- `dev-reseed-selftest` 는 PATH 대역으로 실물 접촉이 없음이 주석과 스크립트 머리에서 확인되나, 픽스처 7건 전체가 어떤 임시 자리에 쓰는지는 전 구간을 읽지 않았다. `parallel` 확정 전에 구현 레인이 `gates/tools/dev-reseed-selftest.sh` 전문과 `dev-package/tools/dev-reseed/tests/*` 의 쓰기 경로를 확인한다.
- `seed-plan-drift` 의 `COLAB_REF_ROOT` 실물 대조 분기가 참조 정본에 쓰기를 하지 않는지 — grep 으로 쓰기 히트가 없음만 확인했고 실행으로 확인하지 않았다.
- 미선언 승격을 `n_undeclared_input` 에 얹을 때, 그 계수가 지금은 **게이트별 `::gate-readiness-failure::` 표식에서** 세어진다(`gates/run.sh:776-778`). 실행기 자신의 선언 누락을 같은 계수에 넣는 방식(가짜 게이트 행을 만들지 않고)의 구체 형태는 미설계.
- 측정 역할이 `handoff --mode complete` 에서 요구할 증거의 정확한 형태(전수 `gate-summary.json` 1건 vs 게이트별 행) — `:302` 주변 검사와 `verify_task_report` 의 기대를 구현 레인이 확정한다.

## 범위 밖 (명시 제외)
- `gates/run.sh` 의 호스트 전역 프로세스 간 뮤텍스 도입과 `gates/tools/_pg.sh` 슬롯의 레포 루트 키잉. ADR-0002 재검토 조건의 2026-09-17 정정이 「이 두 수정은 **#56·#47 의 범위가 아니다**」라고 명시한다. 담는 이슈가 아직 없다.
- `colab-gate-summary/1` → `/2` 스키마 승급과 `counts` 키 집합 변경.
- 게이트 판정 로직·종료코드·검사 대상 변경. 이번 작업은 선언과 증거 계약만 다룬다.
- `gate-runner` 역할 본문 변경과 그 폐기(`.agents/roles/gate-runner.md:38-40` 「폐기 예정」).
- 이슈 #47 · #55 의 간헐 red 수정.
- 다른 이슈 구현, 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- 프론티어 공집합 확인: 2026-09-17(읽기 전용 조사 · 게이트 미실행).
- Ted 확인 문장: 대기 중.
- 승인 필요 지점:
  1. 미선언 게이트를 red 로 승격할 것인가, 승격한다면 상태를 `red(준비 · 입력미선언 · 78)` 로 할 것인가. 이슈 완료 조건 ⑴ 은 「red(판정)」이라 적었고 ADR-0004 · `AGENTS.md:46` 은 준비 쪽을 가리킨다. 둘 중 하나를 고르는 판단이다.
  2. ⑵ 를 `--gate all` 허용으로 풀 것인가, 측정 전용 역할 신설로 풀 것인가. 이 intent 의 권고는 역할 신설이다(ADR-0005 · ADR-0002 · ADR-0006).
  3. 승격 스위치의 도입 시점 — 선언 10건 반영과 같은 PR 에 넣을 것인가, 선언이 먼저 병합된 뒤 별도로 켤 것인가.
  4. `frontend-visual` · `frontend-visual-selftest` 를 `serial` 로 못박는 것 — 전수 시간이 그만큼 늘어난다는 비용을 받는 결정이다.
  5. 신설 역할의 이름과 `.agents/harness.yaml` `adapters.required_files` 집합 변경 여부(ADR-0006 재검토 조건에 걸린다).
- 재개봉 금지: 해당 없음. 아직 승인된 결정이 없다.

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/56
- 결정: [ADR-0002](../../docs/decisions/0002-gate-running-lanes-run-alone.md) · [ADR-0003](../../docs/decisions/0003-human-approval-machine-checks-form.md) · [ADR-0004](../../docs/decisions/0004-gate-verdict-three-states.md) · [ADR-0005](../../docs/decisions/0005-harness-controls-are-declarative.md) · [ADR-0006](../../docs/decisions/0006-agents-dir-owns-body-thin-adapters.md)
- 실행기: `gates/run.sh:180-201`(`ALL_GATES` 71건) · `:647-658`(`all)` 머리) · `:679-708`(선언 읽기·세 갈래) · `:713-717`(계획 출력) · `:750-798`(요약·미선언 경고) · `:799-807`(요약 JSON)
- 선언표: `gates/config/parallelism.toml:12-19`(세 상태 규약) · `:21-`(`[gates]` 표 · 선언 61건)
- 판정부: `scripts/harness/hooks/lifecycle_contract.py:146-158` · `:226-227` · `:302` · `:309-310` · `:342-343` · `:359-360` · `:418-420` · `:464` / 어댑터 `.claude/hooks/lifecycle_contract.py:1-6`
- 역할: `.agents/roles/gate-runner.md:5-7`·`:20-24`·`:38-40` / 어댑터 `.claude/agents/gate-runner.md:1-14`
- 시험: `scripts/tests/test_harness_lifecycle_contract.py` · `scripts/tests/test_task_runtime.py` (둘 다 `agent-bridge` 게이트가 돈다 — `gates/run.sh:206`)
- spec: 미작성. Ted 승인 뒤 합성한다.
- 결정: 신규 legacy 결정번호 발급 없음.

## advisor 검토 결과 (2026-09-17, 초안 작성 후 추가)
- [정정] 「ADR-0004 충돌」은 실재하지 않는다. 인용은 둘 다 축자 정확하나 거기서 끌어낸 추론이 틀렸다.
  `gates/run.sh:757` 의 가르는 축은 「대상이 판정됐는가」인데, 미선언 게이트는 `run.sh:700` 에서
  `solo_gates` 로 접혀 **정상적으로 끝까지 판정된다**. `:753-754` 가 정의하는 red(준비) = 「검사기가
  판정을 못 냈다」는 이 경우 사실이 아니다. 초안은 :757 을 인용하면서 그 기준을 자기 사례에 적용하지 않았다.
- [정정] ADR-0004 의 「입력」은 **게이트 검사의 입력**이지 실행기 스케줄러의 입력이 아니다. 레포 안의
  `cause=입력미선언` 용례는 전부 게이트가 판정에 필요한 값을 못 받은 경우다(`run.sh:325`·`:339` 적용 DB URL).
  `parallelism.toml` 은 `all` 스케줄러만 읽고(`run.sh:683-702`) 어떤 게이트도 읽지 않는다.
  같은 계수기에 두 뜻을 싣게 된다.
- [불가] 초안이 권고한 상태는 명세대로 배출되지 않는다. `n_undeclared_input` 은 게이트별
  `::gate-readiness-failure:: … cause=입력미선언` 표식에서만 증가하고(`run.sh:776`) 그 루프는
  `for g in "${ALL_GATES[@]}"` 안이다. 실행기 자신의 선언 누락을 귀속시킬 게이트 행이 없다.
  초안 미해결 질문 ④가 「구체 형태는 미설계」로 스스로 인정한 지점이다.
- [대안·권고] **제3안 — 검사를 실행기 상태가 아니라 게이트로 만든다.** `ALL_GATES ⊆ parallelism.toml`
  단언을 `harness-contract`(`gates/run.sh:206-208` → `scripts/harness/check.py`)에 넣는다.
  그러면 판정 대상은 **선언표**이고 선언표가 규율을 어긴 것이므로 **red(판정)** 이 맞다 —
  이슈 완료 조건 ⑴ 의 문면을 **그대로** 만족하며, `run.sh` 계수 루프 무변경·스키마 무변경·가짜 행 없음이고
  단독 게이트 실행에서도 걸린다. 충돌은 「검사가 `all` 스케줄러에 살아야 한다」는 전제가 만든 허상이다.
- [검증] 제3안의 숙주는 실물 확인됐다. `scripts/harness/check.py` 는 40행이고 이미
  `check_contract(root, value)` 결과를 `red(판정): …` ＋ 종료코드 1 로, 계약 적재 실패를
  `::gate-readiness-failure::` ＋ 78 로 내보낸다. 3상태가 이미 배선돼 있어 새 배관이 필요 없다.
  현재 `parallelism`·`ALL_GATES` 관련 검사는 0건이다(추가 여지 있음).
- [주의] 이슈도 초안도 「승격」이 기존 결정을 뒤집는다는 점을 말하지 않는다. `run.sh:653-654`·`:716`
  의 「미선언 → 안전한 쪽(단독) ＋ 출력에 명시」는 결함이 아니라 의도된 설계다. 어느 형태의 승격이든
  그 결정을 뒤집는 것이며, Ted 에게 묻는 질문의 성격이 달라진다.
- [확인] 계수 재검은 독립 재파싱으로 일치했다 — `ALL_GATES` 71 · 선언 61 · 미선언 10 · 선언표에만 있는 이름 0.
  미선언 10건 이름표도 동일했다.
- [미검증] `frontend-visual`·`frontend-visual-selftest` 의 serial 판정과 나머지 8건의 parallel 판정,
  `lifecycle_contract.py` 행 인용은 advisor 가 읽어서 확인하지 않았다.

## 승인 (2026-09-17)
- Ted 확인 문장(원문 그대로): "권고대로  분리해"
- 수용한 권고 — 이 intent 해당분:
  - ⑴ **제3안을 채택한다.** `ALL_GATES ⊆ parallelism.toml` 단언을 `harness-contract`
    (`gates/run.sh:206-208` → `scripts/harness/check.py`)에 넣는다. 판정 대상이 선언표이므로
    **red(판정)** 이고 이슈 완료 조건 ⑴ 의 문면을 그대로 만족한다.
    `gates/run.sh` 계수 루프와 `colab-gate-summary/1` 스키마는 **건드리지 않는다.**
    「red(판정) 이냐 red(준비·78) 이냐」는 판정 대상이 아니게 됐으므로 묻지 않는다.
  - ⑴ 선언 10건을 `parallelism.toml` 에 근거 한 줄씩 달아 올린다.
    `frontend-visual`·`frontend-visual-selftest` 는 **serial** 로 못박는다 — 실브라우저 독점이라
    선택지가 없고, 전수 시간 증가를 받아들인다. 나머지 8건은 parallel.
    **단, 초안의 parallel 8건 판정은 advisor 가 읽어서 확인하지 않았다.** 레인이 선언 전에
    각 스크립트를 직접 확인하고 근거 줄을 쓴다. 확인되지 않으면 안전한 쪽(serial)으로 선언한다.
  - 순서는 **선언 먼저, 승격 나중**이다. ADR-0004 의 「두 red 가 모두 0」 때문에 강제된다.
    같은 PR 안에서 선언 커밋 → 승격 커밋 순으로 간다.
  - ⑵ **측정 전용 역할을 신설한다.** `--gate all` 허용은 배제한다 — ADR-0005 가 기계 강제 대상을
    게이트 종료코드와 작업 증거 계약으로 못박았는데 `--gate all` 은 후자를 깎는다.
    본문은 ADR-0006 대로 `.agents/roles/` ＋ `scripts/harness/hooks/lifecycle_contract.py` 에 두고
    `.claude/` 는 어댑터로 남긴다. ADR-0002 의 「게이트 레인은 단독」을 역할 본문에 선언으로 싣는다.
  - 역할 이름과 `.agents/harness.yaml` `adapters.required_files` 변경은 레인이 정한다.
    실제로 `required_files` 가 바뀌면 그때 드러내고 ADR-0006 재검토 조건을 확인한다.
- 드러냄: 어느 형태의 승격이든 `gates/run.sh:653-654`·`:716` 의 「미선언 → 안전한 쪽(단독) ＋
  출력에 명시」라는 **기존 의도된 설계를 뒤집는다.** Ted 에게 이 성격을 밝힌 뒤 승인받았다.
- PR 단위: **#55 와 한 묶음**이다. #55 의 `::gate-failure::` 작업과 같은
  `summary_gate_row()`·`gate_summary_json.py` 표면을 건드리므로 한 레인에서 순차로 간다.
- 재개봉 금지: 예. 제3안 채택과 `--gate all` 기각을 다시 질문하지 않는다.
