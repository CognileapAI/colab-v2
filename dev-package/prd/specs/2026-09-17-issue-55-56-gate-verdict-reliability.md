# Spec: 게이트 판정 신뢰성 2건 — 실패 시험명 공용 표식 · 병렬 안전성 선언과 측정 레인
출처 intent: `dev-package/intent/2026-09-17-issue-55-frontend-test-failure-naming.md`, `dev-package/intent/2026-09-17-issue-56-parallel-safety-and-measurement-lane.md` (둘 다 승인 2026-09-17)

⚠ 이 두 건은 **한 레인·한 PR** 이다. 두 intent 의 「승인 (2026-09-17) · PR 단위」가 같은
`summary_gate_row()`·`gate_summary_json.py` 표면을 이유로 그렇게 못박았다. 병렬 레인 금지.

## 문제 진술
- `frontend-test` 는 red(판정)일 때 실패한 시험의 파일·이름을 어디에도 남기지 않는다. 요약줄은 통과 건수만 내고(`gates/tools/frontend-test.sh:88`), 실패 경로(`:77-81`)는 vitest 출력을 통째로 들여쓰기해 붙일 뿐이다. `gate-summary.json` 의 게이트 행에는 그 값을 적을 열 자체가 없다(`gates/run.sh:77-79` 4열 고정).
- `frontend/test/upload-transfer.test.tsx:326`·`:348`·`:351` 의 `findBy*` 는 해상도가 벽시계인 폴링 대기이고, 실제로 필요한 것은 마이크로태스크 한 바퀴다. 호스트 부하에서 넘쳐 간헐 red 를 낸다(관측 1건 — `dev-package/reports/r-data-canon/wu-c2a/NOTE.md` 마지막 항).
- `frontend/test/lineage-unknown-20260907.test.tsx:282-303` 은 비동기 경계가 없는 동기 전역 스캔이다(338 파일 · 약 3.9MB 를 `readFileSync` 로 전문 적재). 흔들리는 것은 대기가 아니라 **IO 총량**이다.
- vitest fork worker 기동 시간초과가 지금 red(판정)으로 계수된다. `frontend-test.sh:77-81` 이 `rc != 0` 을 무조건 `exit 1` 로 접고, 준비 실패 통로(`:31-39` `ready_red`)는 `node_modules` 부재(`:55`)와 `vitest` 실행 파일 부재(`:58`)에만 걸려 있다.
- `gates/run.sh` 의 `ALL_GATES`(`:180-201`) 71건 중 `gates/config/parallelism.toml` 선언은 61건이고 **미선언 10건**이다. 선언표에만 있는 이름은 0건이다(이 spec 작성 시점 실물 재파싱으로 확인). 미선언은 `:700` 에서 `solo_gates` 로 접히고 `:716`·`:796-797` 이 매 전수마다 경고를 출력한다 — 상시 출력이라 신호가 아니다.
- 전수만 재는 레인은 task 를 열 수 없다. `scripts/harness/hooks/lifecycle_contract.py:149` 가 역할을 `('researcher','lane-worker')` 로 제한하고, `:342-343` 이 `all`·`task` 선택자를 거절한다. 그 결과 전수 결과가 `:302` 의 완료 검사에 닿지 못하고 산문으로만 남는다.

## 해법 개요
- **#55 ⑴** 공용 표식 `::gate-failure::` 를 신설한다. 게이트가 stdout 에 찍고, 실행기가 집어 게이트 **행**의 5번째 열로 싣고, 배출기가 직렬화한다. `counts` 키 집합은 건드리지 않으므로 `colab-gate-summary/1` 그대로이고 ADR-0004 재검토 조건(`docs/decisions/0004-gate-verdict-three-states.md:41`)에 걸리지 않는다.
- **#55 ⑵-a** `upload-transfer.test.tsx:326`·`:348`·`:351` 을 `await act(async () => {})` ＋ 동기 조회로 바꾼다. 벽시계를 판정에서 뺀다.
- **#55 ⑵-b** `lineage-unknown-20260907.test.tsx:282-303` 은 **실측 예산 명시 ＋ 스캔 축소 둘 다** 한다.
- **#55 ⑶** fork worker 기동 시간초과를 `ready_red` 로 보내 red(준비 · 78)로 계수하고, `frontend-test-selftest.sh` 에 vitest 스텁 red fixture 를 세워 증명한다.
- **#56 ⑴** `ALL_GATES ⊆ parallelism.toml` 단언을 `harness-contract`(`gates/run.sh:208-210` → `scripts/harness/check.py`)에 넣는다. 판정 대상이 **선언표**이므로 **red(판정)** 이고 이슈 #56 완료 조건 ⑴ 의 문면을 그대로 만족한다. `gates/run.sh` 계수 루프와 요약 스키마는 건드리지 않는다.
- **#56 ⑴** 미선언 10건을 근거 한 줄씩 달아 선언한다. **선언 먼저, 승격 나중**이다.
- **#56 ⑵** 측정 전용 역할을 신설한다. `--gate all` 허용은 기각됐다. 본문은 `.agents/roles/` ＋ `scripts/harness/hooks/lifecycle_contract.py` 에 두고 `.claude/` 는 어댑터로 남긴다(ADR-0006).

## 사용자 스토리
1. 레인 작업자로서 `frontend-test` 가 red 일 때 어느 시험이 깨졌는지 요약 한 줄에서 읽고 싶다, 1300건 출력을 뒤지지 않기 위해.
2. 레인 작업자로서 그 값이 `gate-summary.json` 의 그 게이트 행에도 남길 원한다, 회차를 넘어 간헐 실패를 누적해야 하기 때문에.
3. 하네스 소비자로서 `counts` 키 집합이 그대로이길 원한다, 스키마 승격이 일어나면 기존 증거 검사가 전부 걸리기 때문에.
4. 게이트 작성자로서 `::gate-failure::` 를 다음 게이트도 같은 형식으로 쓸 수 있길 원한다, 게이트마다 열을 하나씩 늘리지 않기 위해.
5. 레인 작업자로서 `upload-transfer` 3건이 호스트 부하와 무관하게 같은 판정을 내길 원한다, 재시도로 green 을 만들지 않기 위해.
6. 레인 작업자로서 전역 스캔 시험의 예산이 실측 근거와 함께 코드에 적혀 있길 원한다, 다음 사람이 그 숫자를 근거 없이 올리지 않게.
7. 레인 작업자로서 vitest 워커가 못 뜬 회차가 red(준비 · 78)로 서길 원한다, 「돌지 못했다」와 「돌아서 틀렸다」가 갈려야 하기 때문에(ADR-0004).
8. 레인 작업자로서 그 분류가 셀프테스트 fixture 로 증명되길 원한다, 영영 걸리지 않는 갈래를 만들지 않기 위해.
9. 전수 실행자로서 「병렬 안전성 미선언 N건」 경고가 사라지길 원한다, 상시 출력은 신호가 아니기 때문에.
10. 게이트 신설자로서 선언을 빠뜨리면 `harness-contract` 가 red(판정)으로 막길 원한다, 다음 게이트가 또 조용히 미선언으로 들어오지 않게.
11. 게이트 신설자로서 그 판정이 **단독 게이트 실행에서도** 걸리길 원한다, 전수를 돌기 전에 알기 위해.
12. 측정 레인으로서 `begin` 으로 task 를 열고 전수 결과를 그 task 의 증거로 남기고 싶다, 산문이 아니라 값으로 남기기 위해.
13. 오케스트레이터로서 측정 역할이 「게이트 레인은 단독」(ADR-0002)을 자기 본문에 선언으로 들고 있길 원한다, 그 규율이 역할 밖에서만 적히면 잊히기 때문에.
14. 도구 사용자로서 `.claude/` 가 얇은 어댑터로 남길 원한다, 본문이 두 벌로 갈리면 정본 판정 자리가 없어지기 때문에(ADR-0006).
15. 하네스 소비자로서 게이트 행의 기존 4열 의미가 한 순간도 어긋나지 않길 원한다, 반쯤 이전된 위치 규약은 조용히 틀린 값을 낸다.

## 구현 결정

### A. `summary_gate_row()` 위치 규약 — 4열 → 5열 (이번 레인의 유일한 실질 충돌)
- **실물 확인(이 spec 작성 중 직접 읽음).**
  - `gates/run.sh:77-79` `summary_gate_row()` = `printf '%s\t%s\t%s\t%s' "$1" "$2" "$3" "$4"` — 고정 4필드 위치 TSV.
  - `gates/tools/gate_summary_json.py:67` = `f = (parts + [""] * 5)[1:5]` (게이트 행). `:59` 가 `counts` 행에 같은 식을 쓴다 — **`counts` 쪽은 건드리지 않는다.**
- **정정 — advisor 문면의 「slice 가 어긋난다」는 정확하지 않다.** `[1:5]` 는 앞에서부터 4개를 떼므로 5번째 필드를 더해도 기존 4개의 자리는 그대로이고, **새 필드가 조용히 버려질 뿐** 오정렬은 아니다. 위험의 성질이 「값이 뒤섞인다」가 아니라 **「게이트는 찍었는데 JSON 에 안 나온다」**(= 재지 않은 것을 잰 것처럼 보이는 모양)이다. 이 성질 때문에 두 파일을 **한 커밋**에서 함께 고쳐야 한다.
- **편집 형태(한 커밋 · 원자적).**
  - `gates/run.sh:77-79` → `summary_gate_row() { # $1=이름 $2=상태 $3=종료코드 $4=준비 표식 $5=실패 표식` · `printf '%s\t%s\t%s\t%s\t%s' "$1" "$2" "$3" "$4" "$5"`.
  - `gates/tools/gate_summary_json.py:67` → `f = (parts + [""] * 6)[1:6]`, `:73-83` 의 dict 에 `"failures": f[4] or None` 한 키를 더한다. **패딩 값을 6으로 같이 올리지 않으면** 열이 없는 옛 입력에서 `IndexError` 가 난다.
  - 호출자 2곳을 같은 커밋에서 인자 5개로 맞춘다 — `gates/run.sh:140`(단독 게이트) · `:770`·`:771`·`:782`·`:783`(전수 루프의 네 갈래). green 갈래(`:770`)와 111 갈래(`:771`)는 빈 문자열을 넘긴다.
- **수집 방식.** 준비 표식은 지금 `grep -m1` 이다(`gates/run.sh:117` 단독 · `:769` 전수). 실패 시험은 여럿이므로 `::gate-failure::` 는 `-m1` 이 아닌 **전 줄 수집 뒤 한 필드로 접어** 넣는다. TSV 한 셀이므로 줄바꿈을 그대로 넣을 수 없다 — 구분자는 `::gate-failure::` 표식이 이미 쓰는 `|` 와 충돌하지 않는 값으로 고르고 형식을 `gates/README.md` 에 적는다. 표식 형식은 기존 `::gate-readiness-failure::gate=…|waited_for=…` 선례(`gates/tools/frontend-test.sh:32-33`)를 따라 `::gate-failure::gate=<이름>|file=<경로>|test=<이름>` 로 한다.
- **계수를 다시 세는 자리를 만들지 않는다**(`gates/README.md:102`). 게이트가 찍고 실행기가 옮기고 배출기는 직렬화만 한다. `gate_summary_json.py:87-97` 의 계수 대조 블록은 손대지 않는다.
- **행 소비자 전수(직접 조회 결과).** 새 키를 더해도 아래 어느 곳도 깨지지 않는다 — 전부 키 이름으로 읽고 미지 키를 거부하지 않는다. 그래도 레인은 이 목록을 그대로 재확인한다.
  - `scripts/harness/verify_evidence.py:146-169`(`verify_gate_summary` — `name`·`status`·`state`·`exit` 만 읽는다) · `:192`(`rglob`) · `:237`.
  - `scripts/harness/hooks/lifecycle_contract.py:193-221`(`validate_report` — `name`·`status`·`state`·`exit` 만 읽는다) · `:356`(자체 행 생성 — 이쪽은 `gates/run.sh` 를 거치지 않는 **두 번째 행 생산처**다) · `:359-361`.
  - `scripts/harness/hooks/lane-gate-summary.sh`(어댑터 `.claude/hooks/lane-gate-summary.sh:3`).
  - `scripts/harness/task_state.py:72`(보고서 경로 결속 — 행을 읽지 않는다).
  - `scripts/agent-bridge.py`(`verify-report` · `docs/development/dual-agent.md:139`), 시험 `scripts/tests/test_agent_bridge.py:50`.
  - 시험 픽스처 — `scripts/tests/test_harness_lifecycle_contract.py:113` · `test_harness_evidence.py:97`·`:220`·`:253`·`:302` · `test_task_runtime.py:33` · `test_pr_contract.py:51` · `test_harness_work_state.py:95` · `test_harness_release_evidence.py:83` · `test_slack_completion.py:17`.
  - ⚠ **`lifecycle_contract.py:356` 은 별도 결정이 필요하다.** 그 자리는 `run_gates()` 가 **자기 손으로** 행을 짓는 곳이고 `gates/run.sh` 의 `summary_gate_row` 를 쓰지 않는다. 같은 스키마의 행을 두 곳이 만든다. 이번 범위에서는 **그 자리에 `failures` 를 더하지 않는다** — 더하면 두 생산처를 동시에 고치는 것이 되고, `run_gates` 는 `::gate-failure::` 를 집는 코드가 없어 항상 `None` 을 적게 된다(재지 않은 것을 잰 것처럼 쓰는 모양). 「행 생산처가 둘」이라는 사실만 `gates/README.md` 에 드러내고 남긴다.

### B. #55 ⑵ — 시험 2건의 대기 방식
- ⑵-a `frontend/test/upload-transfer.test.tsx:326`·`:348`·`:351`: `fireEvent.change` 직후 `await act(async () => {});` 로 마이크로태스크를 비우고 `screen.getByRole(...)` 동기 조회로 바꾼다. 선례는 같은 레포의 `frontend/test/lineage-unknown-20260907.test.tsx:344` 다. **판정 대상(assert)은 바꾸지 않는다** — 대기 방식만 바꾼다.
- ⑵-b `frontend/test/lineage-unknown-20260907.test.tsx:282-303`: **둘 다** 한다.
  - 예산 명시 — 해당 `it()` 에 `{ timeout: N }` 을 단다. N 은 레인이 **1회 실측**해서 정한다(승인된 예외).
  - 스캔 축소 — `:300-301` 이 지금 걸린 파일 전부를 `readFileSync(f,'utf8')` 로 전문 적재한 뒤 `includes` 한다. 한 번 읽어 판정 즉시 버리는 형태로 바꾼다. 대상 확장자·대상 디렉터리(`frontend/src`·`frontend/test`)는 **바꾸지 않는다** — 대상을 줄이면 검사 범위가 줄어 green-by-skip 이다.
- **근거 문면(승인된 정정 · 반드시 이 문장으로 적는다).** 「예산이 없다, 프레임워크 기본값이다」가 **아니다.** 이 레포에는 **사실상의 벽시계 예산 관행이 있다** — `const WAIT = { timeout: 5000 }` 이 최소 5개 파일(`preview-pick-and-fallback` · `preview-controls-20260912` · `preview-slot-4x3` · `upload-pick-conditional-20260913` · `preview-layout-20260912`)에, `{ timeout: 4000 }` 이 `grid-preview.test.tsx`·`upload.test.tsx` 에 약 40회 있다. **관행 예산이 있고 이번엔 그중 2건만 손댄다.**
- 재시도·플레이크 재실행·상한 인상만으로 green 만들기는 금지다(`gates/run.sh:761`).

### C. #55 ⑶ — fork worker 기동 시간초과의 red(준비) 분류
- 자리: `gates/tools/frontend-test.sh` 의 **⑷ 수집 0건 검사(`:70-76`) 뒤 · `rc != 0` 갈래(`:77-81`) 앞**. 이 갈래에서 `:31-39` 의 `ready_red` 를 부른다. 표식·종료코드는 그 함수의 것을 그대로 쓴다(두 벌로 두지 않는다).
- **미검증 — 레인이 구현 전에 확인한다:** vitest 4.1.11(`frontend/package.json:33`)이 fork worker 기동 시간초과에 찍는 **축자 문면**. 이 워크트리에 `frontend/node_modules` 가 없어 tinypool 원문을 읽지 못했다. 추측 문면으로 정규식을 쓰면 영영 걸리지 않는 갈래가 된다. 레인이 실물 문면을 확인하고 정규식을 확정한 뒤, 그 문면을 스크립트 주석에 축자로 남긴다.
- **미검증 — 레인이 확인한다:** 그 문면이 `:70` 의 `No test files found|Tests\s+no tests` 정규식에도 걸리는지. 걸린다면 새 갈래를 `:70` **앞**으로 옮긴다(준비 실패가 판정 red 로 선행 흡수되면 안 된다).
- 증명: `gates/tools/frontend-test-selftest.sh` 에 케이스 ⓔ 를 더한다. 선례는 `:76-79`(ⓓ `red-ready`)이고 하네스는 이미 있다 — `:35-40` `mk_tree` · `:47-58` `expect_case`(`green`/`red`/`red-ready`). ⓔ 는 ⓓ 와 같이 심볼릭 링크를 지우고 `$d/node_modules/.bin/vitest` 자리에 **기동 시간초과 문면을 찍고 비영으로 끝나는 실행 가능 스텁**을 놓아 분류기를 결정적으로 때린다. `expect_case red-ready "ⓔ …" "$d"` 로 단언하고 파일 머리 주석(`:8-11`)의 케이스 목록에 ⓔ 를 더한다.
- **진짜 시간초과 재현은 기각됐다** — 그 자체가 부하 의존 시험이 된다(승인 문면).

### D. #56 ⑴-a — `harness-contract` 에 `ALL_GATES ⊆ parallelism.toml` 단언
- 숙주 실물 확인: `scripts/harness/check.py` 는 **40행**이고 이미 3상태가 배선돼 있다 — 계약 적재 실패를 `::gate-readiness-failure::` ＋ **78**(`:24-25`), `check_contract` 결과를 `red(판정): …` ＋ **1**(`:28-30`), 통과를 green 한 줄(`:31-36`). `parallelism`·`ALL_GATES` 관련 검사는 현재 **0건**이다. 게이트 배선은 `gates/run.sh:208-210`(`harness-contract) exec python3 "$REPO_ROOT/scripts/harness/check.py"`).
- 넣는 자리: `check.py:26` `errors = check_contract(root, value)` **뒤**, `:27` 의 `if errors:` **앞**. 새 단언의 결과를 같은 `errors` 리스트에 이어 붙인다 — 배출 경로를 새로 만들지 않는다(이미 `red(판정):` ＋ 1 이 배선돼 있다).
- 판정 내용: `gates/run.sh` 의 `ALL_GATES` 배열을 파싱해 얻은 이름 집합이 `gates/config/parallelism.toml` 의 `[gates]` 키 집합에 포함되는지. 빠진 이름마다 `red(판정)` 한 줄. **역방향(선언표에만 있는 이름)** 도 같은 자리에서 낸다 — 현재 0건이고, `gates/run.sh:703-708` 이 이미 전수에서 경고로 내고 있는 것을 판정으로 올린다.
- `ALL_GATES` 파싱이 불가능하면(파일 부재·형식 변경) `red(판정)` 이 아니라 **`::gate-readiness-failure::` ＋ 78** 이다 — 판정 대상을 읽지 못한 것이지 대상이 규율을 어긴 것이 아니다(ADR-0004 `docs/decisions/0004-gate-verdict-three-states.md:17`·`:21`).
- **건드리지 않는 것:** `gates/run.sh` 의 계수 루프(`:767-784`) · `undeclared_gates` 경고(`:796-798`) · `counts` 키 집합 · `colab-gate-summary/1` 스키마. 승인 문면이 명시했다.
- **드러냄(승인 시 Ted 에게 밝힌 성격):** 어느 형태의 승격이든 `gates/run.sh:653-654`·`:716` 의 「미선언 → 안전한 쪽(단독) ＋ 출력에 명시」라는 **의도된 설계를 뒤집는다.** 결함 수정이 아니라 결정 전환이다.
- **순서 강제:** 선언 10건이 먼저 들어간 커밋 뒤에만 이 단언을 켠다. ADR-0004 의 「병합 진입 조건은 두 red 가 모두 0」(`gates/README.md:112`) 때문이다. 뒤집으면 전수가 즉시 막힌다.

### E. #56 ⑴-b — 미선언 10건 선언표
**판정 원칙(승인 문면).** 「초안의 parallel 8건 판정은 advisor 가 읽어서 확인하지 않았다. 레인이 선언 전에 각 스크립트를 직접 확인하고 근거 줄을 쓴다. **확인되지 않으면 안전한 쪽(serial)으로 선언한다.**」
이 spec 은 그 원칙을 spec 작성자 자신에게도 적용한다 — **아래 표에서 「미확인」으로 적힌 4건은 내가 스크립트를 열어 읽지 못한 것이고, 안전한 쪽으로 `serial` 을 적었다.** 레인이 그 4건을 실제로 읽어 `parallel` 로 올릴 수 있으며, 그때 근거 줄을 실제 `file:line` 으로 갈아 끼운다. **올리지 못하면 `serial` 그대로 둔다.**

| 게이트 | 선언 | 근거 한 줄 (선언표에 그대로 적는다) |
| --- | --- | --- |
| `agent-bridge` | `parallel` | `gates/run.sh:206` 이 `python3 -m unittest` 6모듈만 돈다. 6모듈 전수 조회 결과 격리는 전부 `tempfile.TemporaryDirectory()` ＋ 그 안의 `git init` 이고(`test_harness_lifecycle_contract.py:28,31` · `test_task_runtime.py:18,21` · `test_slack_completion.py:11-16` · `test_deploy_release.py:9,161-163`), docker·psycopg·포트·`_pg.sh` 히트 0건. |
| `seed-plan-drift` | `parallel` | `gates/tools/seed-plan-drift.sh:42-43` 이 커밋된 등재표와 정본 md 를 **읽기만** 한다. `mktemp`·`docker`·`_pg.sh`·`_lock.sh` 히트 0건이고 `COLAB_REF_ROOT`(`:72`)는 읽기 입력이다 — 미선언이면 `:104` 에서 red(준비)로 서며 이는 실행 순서가 아니라 환경이 정한다. |
| `seed-plan-drift-selftest` | `parallel` | `gates/tools/seed-plan-drift-selftest.sh:38` `WORK="$(mktemp -d -t seed-plan-drift-selftest-XXXXXX)"`. 판정은 `:57-67` 이 `COLAB_SEED_PLAN_MD_ROOT`·`COLAB_SEED_PLAN_MANIFEST` 로 **사본**을 물려 돈다 — 레포 픽스처는 읽기 전용이다. |
| `harness-eval-selftest` | **`serial`** | **벽시계가 판정에 들어간다.** `:79-81` 이 `COLAB_EVAL_TIMEOUT=1 STUB_SLEEP=4` 로, `:83-85` 가 `COLAB_EVAL_TIMEOUT=5 STUB_SLEEP=0` 으로 green 을 기대한다. 5초 상한 아래의 green 기대는 경합에서 흔들린다 — `harness-eval` 자신(`parallelism.toml:219-227`)·`render-latency`(`:132-137`)를 serial 로 둔 것과 **같은 사유**다. 격리 요구는 없다(`:39` `mktemp -d` · `:46` 스텁 `claude`)지만 측정값이 흔들리는 자리다. |
| `frontend-visual` | **`serial`** | `gates/tools/frontend-visual.sh` 가 `agent-browser` 를 요구하고 실제 페이지를 연다 — 실브라우저(단일 프로필)가 독점 자원이라 선택지가 없다. 전수 시간 증가를 받는다(승인 문면). ⚠ **미확인 — 레인이 확인한다:** 인용 행(`:61` `command -v agent-browser`)을 내가 열어 대조하지 못했다. 선언 값은 바뀌지 않는다. |
| `frontend-visual-selftest` | **`serial`** | 같은 판정부를 여러 번 호출하므로 같은 브라우저 자원을 잡는다. 승인 문면이 `serial` 로 못박았다. ⚠ **미확인 — 레인이 확인한다:** 인용 행(`:8` · `:45-50`)을 내가 열어 대조하지 못했다. 선언 값은 바뀌지 않는다. |
| `dev-reseed-selftest` | **`serial`** ⚠ | **미확인 — 안전한 쪽으로 선언.** `gates/tools/dev-reseed-selftest.sh` 를 내가 열어 읽지 못했다. 앞선 조사는 `:13` 의 PATH 대역(`ssh`·`scp`·`docker`·`aws`·`agent-browser` 가림) 주석을 근거로 `parallel` 을 제시했으나, 같은 조사가 「픽스처 7건 전체의 쓰기 경로는 전 구간을 읽지 않았다」고 자인했다. 레인이 `gates/tools/dev-reseed-selftest.sh` 전문과 `dev-package/tools/dev-reseed/tests/*` 의 쓰기 경로를 읽어 확인되면 `parallel` 로 올리고 근거 줄을 갈아 끼운다. |
| `is4-recovery-selftest` | **`serial`** ⚠ | **미확인 — 안전한 쪽으로 선언.** 판정부가 `infra/staging/tunnel/rehearse-state-recovery-selftest.sh` 이고 내가 열어 읽지 못했다. 앞선 조사는 `:63`(「실제 Cloudflare/Terraform 없이」) · `:72`(`mktemp -d`)를 근거로 `parallel` 을 제시했다. 레인이 그 두 행을 실제로 대조하고 원격 접촉 0을 확인하면 `parallel` 로 올린다. |
| `product-release-selftest` | **`serial`** ⚠ | **미확인 — 안전한 쪽으로 선언.** `gates/tools/product-release-selftest.sh` 를 내가 열어 읽지 못했다. 앞선 조사는 `:163-165`(`--junitxml="$(mktemp)"` 로 pytest) · `:120-122`(venv python 읽기)를 근거로 `parallel` 을 제시했다. ⚠ pytest 묶음은 이 레포에서 **부하**를 이유로 넷 다 serial 이다(`parallelism.toml:155-167`) — 레인은 자원 격리뿐 아니라 **부하 성질**까지 보고 판정한다. |
| `product-reseed-selftest` | **`serial`** ⚠ | **미확인 — 안전한 쪽으로 선언.** `gates/tools/product-reseed-selftest.sh` 를 내가 열어 읽지 못했다. 앞선 조사는 `:190-192`(`--noconftest` 로 실DB fixture 배제) · `:188`(junitxml `mktemp`)을 근거로 `parallel` 을 제시했다. 같은 부하 성질 주의가 적용된다. |

- 실물 계수(이 spec 작성 중 `ALL_GATES` ↔ `[gates]` 독립 재파싱): **`ALL_GATES` 71 · 선언 61 · 미선언 10 · 선언표에만 있는 이름 0.** 미선언 10건 이름표는 위 표와 일치한다. **레인은 이 대조를 다시 한다** — `product-release-selftest`·`product-reseed-selftest` 가 뒤늦게 들어와 8건이 10건이 된 전례가 있다.
- 선언 형식은 기존 표의 관행을 따른다 — 게이트 이름 위에 `#` 주석으로 근거를 적고 그 아래 `"이름" = "값"` 한 줄. `serial` → `parallel` 편집은 **격리 요구를 없앤 결정**이라는 경고(`parallelism.toml:18-19`)를 이번에 새로 어기지 않는다 — 이번 10건은 전부 **신규 선언**이지 기존 값 변경이 아니다.

### F. #56 ⑵ — 측정 전용 역할
- **`--gate all` 허용은 기각됐다**(재개봉 금지). 근거는 ADR-0005(`docs/decisions/0005-harness-controls-are-declarative.md:21-22`) — 기계가 실제로 강제하는 것은 게이트 종료코드와 작업 증거 계약 둘뿐인데 `--gate all` 은 후자를 깎는다.
- **본문 소유(ADR-0006).** 실물 확인: 판정부는 `scripts/harness/hooks/lifecycle_contract.py` **489행**이고 `.claude/hooks/lifecycle_contract.py` 는 **6행**의 `runpy.run_path` 어댑터다. 따라서 수정은 `scripts/harness/` 와 `.agents/` 에 들어가고 `.claude/` 에는 **등록만** 한다.
- **역할 본문** — 신규 `.agents/roles/<이름>.md` ＋ 얇은 어댑터 `.claude/agents/<이름>.md`(선례 `.claude/agents/gate-runner.md:13` 「본문은 저장소 루트 기준 `.agents/roles/gate-runner.md`를 읽고 따른다.」). 본문에 **ADR-0002 의 「게이트를 도는 레인은 한 번에 하나」를 선언으로 싣는다**(`docs/decisions/0002-gate-running-lanes-run-alone.md:17-19`). 이것은 권한 부여가 아니라 증거 계약의 한 줄이다(ADR-0005 · `AGENTS.md:49`).
- **`gate-runner` 는 건드리지 않는다.** 그것은 명령을 글자 그대로 도는 실행기이고, task 를 여는 부모 자리를 측정 역할이 채운다.
- **판정부에서 고칠 자리(이 spec 작성 중 직접 확인한 것만 적는다).**
  - `lifecycle_contract.py:149` — `if role not in ('researcher','lane-worker'): raise ValueError('unsupported task role')`. **확인됨.** 새 역할을 이 집합에 더한다.
  - `:153-159` — `legacy` 아닌 신규 경로의 게이트 선언 규칙. `:156-157` = lane-worker 는 게이트 필수(`'lane requires explicit gates'`), `:158-159` = researcher 는 게이트 선언 금지(`'research task must not declare implementation gates'`). **확인됨**(원 인용 `:156-158` 은 한 줄 짧다 — raise 는 `:159`). 측정 역할은 **게이트를 선언한다**(구체 이름 집합). 어느 쪽 갈래에 붙일지는 레인이 정한다.
  - `:224-227` `gate_evidence` — `:226-227` `if task['role'] != 'lane-worker': raise ValueError('gate evidence requires lane-worker task')`. **확인됨.** 새 역할을 허용해야 한다.
  - `:300-303` `stop()` 의 lane 갈래 — `:301-302` `if mode != 'complete': raise ValueError('lane completion requires current gate evidence')`, `:303` `verify_task_report(root, task)`. **확인됨.** `stop()` 은 `:282` 에서 `expected_role == 'researcher'` 만 분기하므로 **새 역할은 자동으로 이 lane 갈래로 떨어진다** — 의도한 결과지만 레인이 명시적으로 확인한다.
  - `:307-310` `gate_start` — `:309-310` `if task['role'] != 'lane-worker': raise ValueError('gate execution requires lane-worker task')`. **확인됨.** 새 역할을 허용해야 한다.
  - `:341-343` — `for index, gate in enumerate(task['gates']):` / `if gate in ('all','task'): raise ValueError('declare concrete gates, not nested group selectors')`. **행 번호는 확인됨. 다만 이 코드는 `gate_start` 가 아니라 `run_gates()`(`:330-375`) 안에 있다** — 두 intent 본문이 `gate_start` 라고 적은 것은 잘못된 함수 귀속이다. **이 갈래는 그대로 둔다** — 측정 역할도 구체 이름을 선언한다.
  - `:356` — `rows.append(dict(name=gate, status=state, state=state, exit=…, readiness=…))`. **확인됨.** 위 §A 의 두 번째 행 생산처다.
  - `:359-361` — `doc = dict(schema='colab-gate-summary/1', gates=rows, counts=counts, targets=dict(requested='task', selected=task['gates']), …)`. **확인됨**(원 인용대로). 역시 `run_gates()` 안이며 `gate_start` 가 아니다.
  - `:418` — `start.add_argument('--role', required=True, choices=('researcher','lane-worker'))`. **확인됨.** 새 역할 이름을 `choices` 에 더한다. `:419-420` 은 `--artifact`·`--gate` 이고 역할 선택지와 무관하다 — 원 인용 `:418-420` 중 실제 해당 행은 `:418` 하나다.
  - `:441-442` — `hook = commands.add_parser('stop')` / `hook.add_argument('--role', required=True)`. **확인됨. 여기에는 `choices` 제약이 없다** — 두 intent 가 짚지 않은 자리다. 즉 `stop --role` 은 argparse 를 그냥 통과하고 실제 판정은 `stop()` 본문(`:259-260`·`:277-278`)이 한다.
  - `:461-465` — `run-bound-gate` 의 `:463-464` `if task['gates'] != [args.gate]: raise ValueError('single gate differs from declared task set; use gates/run.sh task')`. **확인됨.**
  - **`scripts/harness/task_state.py:72`** — `task['report'] = str(base / 'gate-summary.json') if task['role'] == 'lane-worker' else None`. **확인됨. 두 intent 어디에도 없는 자리이고, 여기를 고치지 않으면 새 역할의 `report` 가 `None` 이 되어 `verify_task_report`(`lifecycle_contract.py:234-241`)가 반드시 실패한다.** 이번 레인의 필수 편집이다.
- **시험.** `scripts/tests/test_harness_lifecycle_contract.py`(현재 `:28` `tempfile.TemporaryDirectory()` 기반)에 새 역할 케이스를 더한다 — ⑴ 새 역할로 `begin` 이 서고 ⑵ `gate_start`·`gate_evidence` 가 거절하지 않고 ⑶ `handoff --mode complete` 가 전수 증거를 요구하며 ⑷ **`--gate all` 은 여전히 거절된다**(`:342-343` 회귀 방지). `scripts/tests/test_task_runtime.py`(`:87` 이 이미 `begin(..., 'lane-worker', gates=['check'], …)` 로 같은 축을 잡는다)에 report 결속 케이스를 더한다. 두 파일은 `agent-bridge` 게이트가 돈다(`gates/run.sh:206`).
- **미검증 — 레인이 확정한다:** 역할 이름 · `.agents/harness.yaml` 의 `sources`(39-50)·`adapters`(51-61) `required_files` 집합을 실제로 바꾸는지. 바뀌면 그때 드러내고 ADR-0006 재검토 조건(`docs/decisions/0006-agents-dir-owns-body-thin-adapters.md:38`)을 확인한다. 바뀌면 `harness-contract` 가 그 구조를 검사하므로 §D 의 새 단언과 같은 게이트에서 함께 판정된다.
- **미검증 — 레인이 확정한다:** `handoff --mode complete` 가 측정 역할에 요구할 증거의 정확한 형태(전수 `gate-summary.json` 1건 vs 게이트별 행)와 `verify_task_report`(`:234-253`)의 기대.

### G. 커밋·PR 단위
- **PR 1건 · 레인 1개 · 커밋 7개.** 순서는 아래 §커밋 순서를 글자 그대로 지킨다.
- 동일 체크아웃의 쓰기 주체는 하나다(`AGENTS.md:43`). #55·#56 을 병렬 레인으로 돌리지 않는다.

## 커밋 순서 (레인이 그대로 따른다)

| # | 커밋 | 대상 파일 | 이 자리여야 하는 이유 |
| --- | --- | --- | --- |
| 1 | **병렬 안전성 미선언 10건을 선언한다** | `gates/config/parallelism.toml` | ADR-0004 의 「병합 진입 조건은 두 red 가 모두 0」(`gates/README.md:112`) 때문에 **승격보다 반드시 먼저**다. 뒤집으면 커밋 2 시점에 전수가 즉시 red 로 막힌다. 이 커밋만으로 `gates/run.sh:796-797` 의 미선언 경고가 0건이 되어 사라진다. |
| 2 | **`harness-contract` 에 `ALL_GATES ⊆ parallelism.toml` 단언을 넣는다** | `scripts/harness/check.py`, `gates/README.md` | 커밋 1 이 이미 미선언 0건을 만든 뒤라야 이 단언이 green 으로 선다. 판정 대상이 선언표이므로 red(판정)이고 이슈 #56 완료 조건 ⑴ 의 문면을 그대로 만족한다. |
| 3 | **게이트 행의 위치 규약을 4열 → 5열로 옮긴다 (원자적 · 한 커밋)** | `gates/run.sh:77-79`(정의) · `:140`(단독 호출자) · `:770`·`:771`·`:782`·`:783`(전수 호출자 4갈래) · `gates/tools/gate_summary_json.py:67`(slice·패딩) · `:73-83`(새 키) · `gates/README.md` | **생산자와 소비자를 같은 커밋에서 옮겨야 위치 규약이 반쯤 이전된 상태가 존재하지 않는다.** 정의만 바꾸고 배출기를 미루면 게이트가 찍은 값이 JSON 에서 조용히 사라지고, 배출기만 먼저 바꾸면 패딩 `[""]*5` 아래에서 `IndexError` 가 난다. 이 커밋에서는 아직 어느 게이트도 `::gate-failure::` 를 찍지 않으므로 새 열은 전부 빈 값이고, 기존 4열의 의미는 한 순간도 어긋나지 않는다. |
| 4 | **`frontend-test` 가 실패 시험명을 `::gate-failure::` 로 찍게 한다** | `gates/tools/frontend-test.sh`(`:77-81` 실패 갈래), `gates/tools/frontend-test-selftest.sh`(실패명 단언 추가) | 커밋 3 이 통로를 이미 열어 둔 뒤라야 찍은 값이 JSON 에 닿는다. intent 의 구현 순서 근거 ⑴ → ⑶ → ⑵ 중 ⑴ 이다 — 이것이 먼저 들어가야 ⑵ 가 고칠 간헐 실패의 표본이 쌓인다. |
| 5 | **fork worker 기동 시간초과를 red(준비 · 78)로 분류하고 스텁 fixture 로 증명한다** | `gates/tools/frontend-test.sh`(`:76`↔`:77` 사이 새 갈래 · `:31-39` `ready_red` 재사용), `gates/tools/frontend-test-selftest.sh`(`:79` 뒤 케이스 ⓔ · `:8-11` 주석) | ⑶ 이다. 커밋 4 가 실패 갈래를 이미 손댄 뒤라 같은 자리를 두 번 흔들지 않는다. 분류 정규식은 레인이 실물 문면을 확인한 뒤 확정한다. |
| 6 | **시험 2건의 대기 방식을 바꾼다** | `frontend/test/upload-transfer.test.tsx:326`·`:348`·`:351`, `frontend/test/lineage-unknown-20260907.test.tsx:282-303` | ⑵ 다. 커밋 4·5 로 실패가 이름과 상태를 갖게 된 뒤에 손대야 red → green 전이를 값으로 볼 수 있다. ⑵-b 의 예산 N 실측 1회는 이 커밋 안에서 한다. |
| 7 | **측정 전용 역할을 신설한다** | `.agents/roles/<이름>.md`(신규), `.claude/agents/<이름>.md`(어댑터), `scripts/harness/hooks/lifecycle_contract.py:149`·`:153-159`·`:226-227`·`:309-310`·`:418`, `scripts/harness/task_state.py:72`, `scripts/tests/test_harness_lifecycle_contract.py`, `scripts/tests/test_task_runtime.py`, 필요 시 `.agents/harness.yaml` | 게이트 표면과 독립이라 마지막이다. `.agents/harness.yaml` 을 바꾸면 커밋 2 가 세운 `harness-contract` 단언과 같은 게이트에서 함께 판정되므로, 그 게이트가 이미 green 인 상태에서 얹는 것이 안전하다. |

- ⚠ **커밋 3 을 쪼개지 않는다.** 4→5 필드 전환은 생산자(`gates/run.sh`)와 소비자(`gates/tools/gate_summary_json.py`)가 **같은 커밋**에 있어야 한다.
- ⚠ 커밋 1 과 2 의 순서를 바꾸지 않는다(ADR-0004 강제).
- ⚠ 이 spec 의 범위에 커밋·push·PR 게시·배포·이슈 댓글·이슈 종결은 포함하지 않는다. PR 게시는 사용자가 수행한다.

## 완료 조건 (레인이 스스로 대조한다)
1. `gates/config/parallelism.toml` 의 `[gates]` 키 집합이 `gates/run.sh` 의 `ALL_GATES` 를 **전부** 덮는다. 미선언 0건 · 선언표에만 있는 이름 0건. 실행기 재파싱으로 확인한다.
2. 선언 10건 각각에 근거 한 줄이 붙어 있고, 그 근거가 **레인이 실제로 읽은 `file:line`** 을 가리킨다. 읽지 못한 것은 `serial` 이고 그 사실이 근거 줄에 적혀 있다.
3. `frontend-visual`·`frontend-visual-selftest` 가 `serial` 이다.
4. `bash gates/run.sh all` 출력에 「병렬 안전성 **미선언** N건」 줄(`gates/run.sh:796-797`)이 **나오지 않는다.**
5. `scripts/harness/check.py` 가 `ALL_GATES ⊄ parallelism.toml` 을 `red(판정):` ＋ 종료코드 **1** 로 낸다. 일부러 한 줄 지운 사본에서 실제로 1 이 나오는 것을 본다. 3상태가 유지된다 — 파싱 불가는 `::gate-readiness-failure::` ＋ **78**.
6. `gates/run.sh` 의 `counts` 키 집합이 그대로다. `colab-gate-summary/1` 이 그대로다. `n_green`·`n_red_judge`·`n_red_ready`·`n_undeclared_input` 네 계수의 정의가 한 줄도 바뀌지 않았다.
7. `summary_gate_row()` 호출자 **전부**가 5인자다 — `gates/run.sh:140`·`:770`·`:771`·`:782`·`:783`. `grep -n summary_gate_row gates/run.sh` 로 세어 정의 1 ＋ 호출 5 = 6 히트를 확인한다.
8. `gate_summary_json.py` 의 게이트 행 slice 가 `(parts + [""] * 6)[1:6]` 이고, `counts` 행 slice(`:59`)는 **바뀌지 않았다.**
9. 열이 없는 옛 TSV 입력(4필드)을 `gate_summary_json.py` 에 먹여도 예외 없이 `failures: null` 로 직렬화된다.
10. `frontend-test` 가 red(판정)일 때 요약에 실패 시험의 파일과 이름이 한 줄씩 서고, 같은 값이 `gate-summary.json` 의 그 게이트 행에 남는다.
11. `frontend-test-selftest` 의 기존 4케이스(ⓐ green · ⓑ red · ⓒ red · ⓓ red-ready)가 전부 살아 있고 ⓔ red-ready 가 더해져 **5케이스**다.
12. vitest 스텁이 기동 시간초과 문면을 찍고 비영으로 끝날 때 게이트가 종료코드 **78** 을 낸다. 분류 정규식이 대조하는 축자 문면이 스크립트 주석에 실물 근거와 함께 적혀 있다.
13. `upload-transfer.test.tsx` 의 세 자리에 `findBy*` 벽시계 대기가 남아 있지 않고, 판정하는 `expect` 가 변경 전과 같다.
14. `lineage-unknown-20260907.test.tsx:282-303` 에 **실측 근거가 주석으로 적힌** 명시 예산이 있고, 파일 전문 적재가 사라졌으며, **대상 디렉터리·확장자는 그대로**다.
15. 측정 역할로 `begin` → 전수 실행 → `handoff --mode complete` 가 실제로 성립하고, 그 task 의 증거로 전수 `gate-summary.json` 이 남는다.
16. `lifecycle_contract.py:341-343` 의 `all`·`task` 선택자 거절이 **살아 있다.** 그것을 확인하는 시험 케이스가 있다.
17. `.claude/hooks/lifecycle_contract.py` 가 여전히 6행 어댑터이고, `.claude/agents/<새 역할>.md` 가 본문을 복제하지 않는다(ADR-0006).
18. `scripts/harness/task_state.py:72` 가 새 역할에도 report 를 결속한다.
19. 준비 실패·미실행·검증 실패를 green 으로 세지 않는다. 게이트 3계수와 종료코드를 그대로 회수한다.

## 검증 계획

### ① 단독 게이트로 증명하는 것 (호스트 독점 불필요)
- `harness-contract` — §D 의 새 단언. green 1건 ＋ **일부러 깨뜨린 사본에서 red(판정) 1** ＋ **파싱 불가 사본에서 78**. 세 상태를 전부 본다.
- `harness-contract-selftest` — 커밋 2 가 `check.py` 를 건드리므로 함께 돈다.
- `frontend-test-selftest` — ⓐ~ⓔ 5케이스. **red fixture 가 실제로 red 를 내는 것**이 이번 ⑶ 의 증명이다.
- `frontend-test` — 커밋 6 뒤 단독 green. **단독 green 은 ⑵ 의 증명이 아니다**(아래 ② 참조).
- `agent-bridge` — 커밋 7 의 `lifecycle_contract.py`·`task_state.py`·두 시험 파일을 판정한다(`gates/run.sh:206`).
- `frontend-typecheck` — 커밋 6 이 `frontend/test/**` 를 건드리므로 돈다.
- `work-item-consistency` — legacy 대장을 건드리지 않았음을 확인하는 자리. 이번 레인은 신규 legacy 결정번호·대장 항목을 만들지 않는다.

### ② 호스트 독점 전수 실행으로만 증명되는 것
- **완료 조건 ⑷(#55)** = 전수 `-j 4` green **3회 연속**. 승인 문면이 3회를 배정했고 **이슈 #47 과 같은 예산**이다.
- **갈음 불가.** `frontend-test` 는 `serial` 이라(`parallelism.toml:147`) 전수 `-j 4` 에서 옆에 다른 게이트가 서지 않는다. 단독 게이트 3회는 ⑷ 가 말하는 「같은 구성」이 아니다 — 부하는 형제 게이트가 아니라 ⓐ vitest 자신의 워커 팬아웃과 ⓑ 같은 호스트의 다른 레인에서 온다.
- **ADR-0002 준수.** 이 전수 구간에는 호스트에서 **레인 하나만** 돈다(`docs/decisions/0002-gate-running-lanes-run-alone.md:17-19`). 다른 레인은 그 구간에 게이트를 돌리지 않는다. `_pg.sh` 슬롯이 호스트 전역 4개이고 `gates/run.sh` 에 프로세스 간 뮤텍스가 없다는 것이 그 근거다(같은 ADR `:11-12`).
- **커밋 1·2 뒤의 전수 1회**로 「미선언 경고 0건」과 「새 단언 green」을 함께 본다. 이것은 위 3회와 별도 회차이며, 같은 호스트 독점 구간에 이어 붙인다.
- **1회 실측(승인된 예외)** — ⑵-b 의 예산 N. `lineage-unknown-20260907.test.tsx` 전역 스캔의 실제 소요를 한 번 잰다. **이 측정은 부하 없는 단독 구간에서 한다** — 부하 중 측정값을 예산으로 박으면 눈금으로 흔들림을 덮는 것이 된다(`gates/run.sh:761`).

### ③ 하지 않는 것
- 재시도·플레이크 재실행·상한 인상·병렬도 축소·건너뛰기로 green 만들기. `gates/run.sh:761` 축자 금지이고 이슈 #55 ⑵ 도 같은 규율이다.
- 진짜 fork worker 시간초과 재현. 그 자체가 부하 의존 시험이다(승인 문면이 기각).
- 실브라우저 검증. 이번 레인에 UI 변경이 **0건**이다. `frontend-visual` 은 선언표에 `serial` 로 적히기만 하고 이번 판정 대상이 아니다.

## 정책 대조 (작성 시점 제약)
대조 원본은 `.agents/rules/product.md` §3(불변 규칙 8항)·§5(절대 하지 않는 것)이다.
⚠ **미확인 — 레인이 확인한다:** 이 spec 작성자는 `.agents/rules/product.md` 본문을 **열어 읽지 못했다.** 아래 항목별 판단은 이번 변경이 제품 코드·DB·계약에 한 줄도 닿지 않는다는 사실에 근거한 것이며, 원문 대조가 아니다. 레인이 §3·§5 를 실제로 읽고 이 절을 갱신한다.
- §3-1 도메인은 자기 테이블 ＋ 공용 커널만 참조: **저촉 없음(추정).** 변경 전부가 게이트·하네스·프런트 시험이다. DB 접근 0건.
- §3-2 AI → 계보 쓰기 경로 없음: **저촉 없음.** AI 경로 무변경.
- §3-3 AI 저장소 마이그레이션 체인 분리: **저촉 없음.** 마이그레이션 0건.
- §3-4 core-api 에 geo 라이브러리 import 금지: **저촉 없음.** 백엔드 무변경.
- §3-5 모든 조회에 연구실 경계 자동 주입: **저촉 없음.** 조회 0건.
- §3-6 정규 ID 타입은 공통 스키마에서만: **저촉 없음.** 새 ID 타입 없음.
- §3-7 생성된 타입·클라이언트를 손으로 고치지 않는다: **저촉 없음.** 생성물 무변경.
- §3-8 문서에 절대경로를 적지 않는다: **준수.** 이 spec 의 모든 경로는 저장소 상대다.
- §5 게이트 우회·비활성화: **저촉 없음 — 반대 방향이다.** 이번 변경은 미선언을 판정으로 올리고 준비 실패를 준비 실패로 부르게 한다.
- §5 「나중에」로 남기기: **부분 해당 — 드러내 둔다.** ⓐ `lifecycle_contract.py:356` 의 두 번째 행 생산처 미통일 ⓑ `::gate-failure::` 를 다른 게이트(`service-tests-*` 등)로 넓히는 일 ⓒ `gates/run.sh` 호스트 전역 뮤텍스와 `_pg.sh` 슬롯 레포 루트 키잉. 셋 다 승인된 intent 가 범위 밖으로 명시했다. 완료로 세지 않고 아래 「범위 밖」에 남긴다.
- §5 범위 늘리기: **저촉 없음.** 두 intent 의 승인 절이 확정한 범위를 넘지 않는다.
- 계약 동결 해제 필요: **아니오.** `colab-gate-summary/1` 이 그대로이고 `counts` 키 집합이 바뀌지 않는다. ADR-0004 재검토 조건(`docs/decisions/0004-gate-verdict-three-states.md:41`)에 걸리지 않는다 — 스키마 범프 **0회**.
- 결정 로그 대조: 신규 legacy 결정번호를 발급하지 않는다(두 intent 모두 명시). ADR 은 기존 0002·0004·0005·0006 을 인용할 뿐 새로 세우지 않는다.
- 용어: `dev-package/DOMAINS.md` 의 표기를 그대로 쓴다. 게이트 3상태의 한국어 표기(`green` · `red(판정)` · `red(준비)`)는 `gates/run.sh:18-19` 의 것을 승계한다.

### 디자인 제약 확인
**해당 없음.** 이번 레인의 변경은 게이트 스크립트·하네스 파이썬·선언표·역할 문서·프런트 **시험** 파일이며, 화면 코드·스타일·토큰을 한 줄도 건드리지 않는다. `frontend/src/**` 변경 0건. 따라서 `design-review §0` 판정 대상이 없고 `frontend-visual` 계측도 이번 완료 조건이 아니다.

## 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | 게이트 행이 4열 → 5열로 가는 동안 생산자와 소비자가 갈리면, **게이트는 실패명을 찍었는데 JSON 에는 없는** 상태가 생긴다. 이것은 「재지 않은 것을 잰 것처럼」 보이는 모양이고 이 레포가 가장 싫어하는 실패 유형이다. | 정의·호출자 5곳·배출기 slice·패딩을 **한 커밋**에서 함께 옮기고, 그 커밋에서는 아직 어느 게이트도 표식을 찍지 않는다 | 배출기를 먼저 바꾸고 실행기를 뒤 커밋으로 미룬다 | ⓐ — ⓑ는 패딩 `[""]*5` 아래에서 `IndexError` 가 나거나 값이 조용히 사라진다 |
| 2 | 미선언 승격(§D)을 선언 10건보다 **먼저** 켜면 전수가 즉시 red(판정)으로 막힌다. | 커밋 1(선언) → 커밋 2(승격) 순서를 고정한다 | 같은 커밋에 넣는다 | ⓐ — ADR-0004 의 「두 red 가 모두 0」이 강제한다. 승인 문면도 같다 |
| 3 | 앞선 조사가 `parallel` 로 판정한 8건 중 **4건을 이 spec 작성자도 읽지 못했다.** 확인되지 않은 `parallel` 선언은 다음 전수에서 재현 안 되는 red 를 만든다 — 판정이 아니라 배선이 낸 red 다. | 읽지 못한 4건을 `serial` 로 선언하고, 레인이 스크립트를 실제로 읽어 확인한 것만 `parallel` 로 올린다 | 앞선 조사의 판정을 그대로 옮겨 적는다 | ⓐ — 승인 문면이 「확인되지 않으면 안전한 쪽(serial)」이라고 못박았다. 전수 시간 증가는 받는 비용이다 |
| 4 | `harness-eval-selftest` 는 앞선 조사가 `parallel` 로 판정했으나 **케이스 안에 벽시계 상한이 있다**(`:79-85` — `COLAB_EVAL_TIMEOUT=1/5`). 5초 상한 아래 green 기대는 경합에서 흔들린다. | `serial` 로 선언한다 — `harness-eval`·`render-latency` 를 serial 로 둔 것과 같은 사유(경합이 곧 판정을 흔드는 자리) | 격리 요구가 없으므로 `parallel` 로 둔다 | ⓐ — 격리 요구의 유무가 아니라 **측정값이 흔들리는가**가 이 레포의 기준이다(`parallelism.toml:132-137`) |
| 5 | `lifecycle_contract.py:356` 이 `gates/run.sh` 를 거치지 않고 **같은 스키마의 게이트 행을 따로 만든다.** 이번에 `failures` 를 한쪽에만 더하면 두 생산처가 다른 모양의 행을 낸다. | 이번에는 `run.sh` 쪽만 더하고, 「행 생산처가 둘」이라는 사실을 `gates/README.md` 에 드러내 남긴다 | `:356` 에도 `failures=None` 을 더해 모양을 맞춘다 | ⓐ — ⓑ는 `run_gates` 가 표식을 집지 않으므로 **항상 `None`** 이고, 그것은 재지 않은 것을 잰 것처럼 쓰는 모양이다 |
| 6 | 측정 역할이 `stop()` 의 lane 갈래(`:300-303`)로 **자동으로** 떨어진다. `stop()` 은 `:282` 에서 researcher 만 분기하기 때문이다. 의도한 결과지만 아무도 선언하지 않은 채로 성립한다. | 레인이 그 분기를 **명시적으로 확인하는 시험 케이스**를 더한다 | 동작하니 그대로 둔다 | ⓐ — 우연히 맞는 것과 선언해서 맞는 것은 다르다 |
| 7 | `scripts/harness/task_state.py:72` 는 **두 intent 어디에도 인용되지 않았다.** 고치지 않으면 새 역할의 `report` 가 `None` 이 되어 `verify_task_report` 가 반드시 실패한다. | 커밋 7 의 필수 편집으로 명시한다(이 spec §F) | intent 가 짚은 자리만 고친다 | ⓐ — intent 가 놓친 자리다. 이 spec 이 드러낸다 |
| 8 | vitest 기동 시간초과의 **축자 문면을 아무도 확인하지 못했다**(워크트리에 `frontend/node_modules` 부재). 추측 문면으로 정규식을 쓰면 영영 걸리지 않는 갈래가 선다. | 레인이 실물 문면을 먼저 확인하고 정규식을 확정한 뒤, 그 문면을 스크립트 주석에 축자로 남긴다 | 그럴듯한 정규식을 써 두고 넘어간다 | ⓐ — ⓑ는 red fixture 는 통과하는데 실물은 영영 안 걸리는 게이트를 만든다 |
| 9 | `::gate-failure::` 는 실패가 여럿이라 **여러 줄**인데, 게이트 행은 TSV 한 셀이다. 줄바꿈을 그대로 넣으면 TSV 가 깨진다. | 표식 줄들을 한 필드로 접는 구분자를 정하고 그 형식을 `gates/README.md` 에 적는다. 준비 표식의 `grep -m1`(`:117`·`:769`)과 달리 **전 줄을 수집한다** | 첫 줄만 남기는 `grep -m1` 을 그대로 쓴다 | ⓐ — ⓑ는 실패가 여럿일 때 나머지를 잃는다. intent 제약 4항이 이미 짚었다 |

## 범위 밖
- (#55 승계) `GT-1` 묶음의 나머지 — `service-tests-viz-render` 가상환경 패키지 설치 누락 분류 · `tests/fixtures/setup-db.sh` 비멱등 · `migration-drift` 오라클 정비 · 호스트 시각 역행 탐지.
- (#55 승계) `frontend-test` 의 `serial` 선언 변경. `parallelism.toml:139-147` 이 실측을 요구하며 이번 범위 밖이다.
- (#55 승계) `::gate-failure::` 를 다른 게이트(`service-tests-*` 등)로 넓히는 일.
- (#56 승계) `gates/run.sh` 의 호스트 전역 프로세스 간 뮤텍스 도입과 `gates/tools/_pg.sh` 슬롯의 레포 루트 키잉. ADR-0002 재검토 조건의 2026-09-17 정정이 「이 두 수정은 **#56·#47 의 범위가 아니다**」라고 명시한다. 담는 이슈가 아직 없다.
- (#56 승계) `gate-runner` 역할 본문 변경과 그 폐기(`.agents/roles/gate-runner.md:38-40`).
- 두 건 공통: `colab-gate-summary/1` → `/2` 승급 · `counts` 키 집합 변경 · 새 게이트 상태 신설 · 게이트 판정 로직·종료코드·검사 대상 변경.
- 두 건 공통: 이슈 #47 의 수집계수 문제, 다른 이슈 구현.
- `lifecycle_contract.py:356` 의 두 번째 행 생산처 통일.
- 커밋·push·PR 게시·배포·이슈 댓글·이슈 종결. PR 게시는 사용자가 수행하며 에이전트는 로컬 PR 요약과 실제 검증 근거만 제공한다.

## 산출 계획
- 라운드 파일: `dev-package/prd/rounds/R-ISSUE-55-56-GATE-VERDICT-RELIABILITY.md`(≤300행, 첫 줄에서 이 spec 을 링크). 미작성.
- 예상 레인 수: **1 (직렬).** 두 건이 `summary_gate_row()`·`gate_summary_json.py` 라는 같은 표면을 건드린다. 한 체크아웃의 쓰기 주체는 하나만 유지한다(`AGENTS.md:43`).
- 커밋 7개, PR 1건. 위 「커밋 순서」를 그대로 지킨다.
- 이슈별 결과·미달·초과, 게이트 3계수와 종료코드, 호스트 독점 전수 3회의 실제 회차 기록, 사용자 게시용 로컬 PR 요약을 남긴다.

## 미확인 (이 spec 작성 중 확인하지 못한 것 — 레인이 구현 전에 확인한다)
1. **선언 10건 중 4건의 스크립트 원문** — `gates/tools/dev-reseed-selftest.sh` · `infra/staging/tunnel/rehearse-state-recovery-selftest.sh` · `gates/tools/product-release-selftest.sh` · `gates/tools/product-reseed-selftest.sh`. **안전한 쪽(`serial`)으로 선언해 두었다.** 레인이 읽어 확인되면 `parallel` 로 올리고 근거 줄을 실제 `file:line` 으로 갈아 끼운다.
2. **`frontend-visual`·`frontend-visual-selftest` 의 인용 행** — `frontend-visual.sh:61` · `frontend-visual-selftest.sh:8`·`:45-50` 을 직접 대조하지 못했다. **선언 값(`serial`)은 승인 문면이 못박았으므로 바뀌지 않는다** — 바뀔 수 있는 것은 근거 줄의 인용뿐이다.
3. **vitest 4.1.11 의 fork worker 기동 시간초과 축자 문면** — 이 워크트리에 `frontend/node_modules` 가 없다(조회 0건). §C 의 분류 정규식이 여기에 걸려 있다.
4. **⑵-b 의 예산 N** — 실측하지 않았다. 승인된 1회 실측을 레인이 부하 없는 단독 구간에서 한다.
5. **`.agents/rules/product.md` §3·§5 원문** — 열어 읽지 못했다. 「정책 대조」 절의 항목별 판단은 변경 범위에 근거한 추정이다.
6. **`.agents/harness.yaml` `sources`(39-50)·`adapters`(51-61) 원문** — 열어 읽지 못했다. 새 역할이 `required_files` 를 바꾸는지는 레인이 확인한다(ADR-0006 재검토 조건).
7. **`gates/README.md:83-143`(요약 JSON 절) 원문** — 인용은 ADR-0004 와 두 intent 를 거쳐 받은 것이고 직접 대조하지 않았다. §A 의 `::gate-failure::` 형식을 적을 자리가 이 절이다.
8. **`gates/tools/parallelism.py` 원문 51행** — 선언 파싱기를 열어 읽지 못했다. §D 의 단언을 `check.py` 가 이 파서를 재사용할지 자체 파싱할지는 레인이 정한다. **재사용을 권고한다** — 두 벌로 두면 한쪽이 언젠가 다른 말을 한다(`gates/README.md:122` 「정본은 하나」와 같은 규율).
9. **`scripts/harness/hooks/lane-gate-summary.sh` 원문** — 게이트 행의 소비자로 이름만 확인했고 본문을 읽지 못했다. §A 의 소비자 목록에서 유일하게 읽지 않은 항목이다.
