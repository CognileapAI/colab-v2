# Intent: frontend-test 가 실패한 시험 이름을 남기고, 대기 예산 시험 2건의 흔들림을 기전에서 없앤다
메타 — 발의자: sungwooHa · 방향 결정: Ted · 작성 2026-09-17 · 승인: 미승인 — Ted 승인 대기

## 문제
- `frontend-test` 요약줄은 통과 건수만 낸다. `gates/tools/frontend-test.sh:88` 「`frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 ${NTESTS}건 · 실패 0건.`」이고 `NTESTS` 는 `:69` 의 `passed` 정규식 하나에서 나온다. 실패 경로(`:77-81`)는 vitest 출력을 통째로 들여쓰기해 붙일 뿐이고, 실패 시험 이름을 뽑는 자리가 없다. 이슈 증상 2항이 현 트리에서 그대로 확인된다.
- `gate-summary.json` 의 게이트 행에는 실패 시험을 적을 열 자체가 없다. 행 조립은 `gates/run.sh:77-79` `summary_gate_row()` 의 4열(이름·상태·종료코드·준비표식)이고, 직렬화는 `gates/tools/gate_summary_json.py:66-83` 이 그 4열을 `name`·`status`·`state`·`exit`·`readiness` 로 옮긴다. 완료 조건 ⑴ 의 「`gate-summary.json` 행 포함」은 새 열을 이 경로에 내야 한다는 뜻이다.
- 간헐 red 의 실물 근거는 1건뿐이다. `dev-package/reports/r-data-canon/wu-c2a/NOTE.md` 마지막 항 축자 — 「관측 1건 = 첫 실행에서 `test/upload-transfer.test.tsx:326`(`표준 격자 가져오기` 조회)이 대기 초과로 1건 red. 단독 실행 16/16 green, 재실행 2회 전건 green — 전수 부하에서의 대기 초과로 판독.」 같은 파일의 앞 항은 그 회차 게이트가 「`frontend-test green — 통과 1329건 · 실패 0건`」이었다고 적는다.
- vitest fork worker 기동 시간초과는 지금 red(판정)으로 계수된다. `frontend-test.sh:77-81` 이 `rc != 0` 을 무조건 `exit 1` 로 접기 때문이다. 준비 실패 통로(`:31-39` `ready_red`)는 `node_modules` 부재(`:55`)와 `vitest` 실행 파일 부재(`:58`)에만 걸려 있다. 대장 `dev-package/work-items.yaml:3689` `GT-1` note 의 B1 축자 「vitest fork worker 기동 시간초과를 red(판정)으로 계수」와 일치한다.

## 원한 결과 (proposed outcome)
- `frontend-test` 가 red(판정)일 때 실패한 시험의 파일과 이름이 요약에 한 줄씩 서고, 같은 값이 `gate-summary.json` 의 그 게이트 행에 남는다. 간헐 실패가 회차를 넘어 누적된다.
- `upload-transfer.test.tsx:326` 과 `lineage-unknown-20260907.test.tsx:282-303` 이 호스트 부하와 무관하게 같은 판정을 낸다. 재시도·플레이크 재실행은 쓰지 않는다.
- vitest fork worker 기동 시간초과가 red(준비 · 78)로 계수되고, 그 분류를 `frontend-test-selftest` 의 red fixture 가 증명한다.
- 게이트 판정 로직의 기존 갈래(수집 0건 red · 건수 미판독 red · 준비 실패 78)는 한 줄도 느슨해지지 않는다.

## 영향 범위
- 게이트: `gates/tools/frontend-test.sh`(실패명 추출 · 기동 시간초과 분류) · `gates/tools/frontend-test-selftest.sh`(red fixture 추가).
- 실행기·배출기: 완료 조건 ⑴ 을 선언된 방식으로 내려면 `gates/run.sh:77-79`·`:117`·`:140`·`:769`·`:805` 와 `gates/tools/gate_summary_json.py:66-83` 이 함께 바뀐다. 이 두 파일은 전 게이트 공용이라 폭발 반경이 이 게이트 하나가 아니다.
- 시험: `frontend/test/upload-transfer.test.tsx:326`(및 같은 조회를 쓰는 `:348`·`:351`) · `frontend/test/lineage-unknown-20260907.test.tsx:282-303`. 판정 대상(assert)은 바꾸지 않고 대기 방식만 바꾼다.
- 설정: `frontend/vite.config.ts:15-40` 에 `testTimeout` 선언이 없다. 예산을 명시하기로 하면 이 자리 또는 해당 `it()` 인자가 바뀐다.
- 계약 파괴 여부: 아니오. `colab-gate-summary/1` 소비자는 키 이름으로 읽고 미지 키를 거부하지 않는다(`scripts/harness/verify_evidence.py:146-169`). `counts` 키 집합이 그대로이므로 `docs/decisions/0004-gate-verdict-three-states.md:41` 의 스키마 승격 조건에 걸리지 않는다.

## 제약
- 판정은 세 상태뿐이다. `docs/decisions/0004-gate-verdict-three-states.md:17` 「게이트 판정은 셋뿐이다 — `green`(exit 0) · `red_판정`(exit 1) · `red_준비`(exit 78). `SKIP`을 만들지 않는다.」 실패명 열은 상태가 아니라 부가 정보이며 새 상태를 만들지 않는다.
- 계수를 다시 세는 자리를 만들지 않는다. `gates/README.md:102` 「**계수를 다시 세는 자리를 만들지 않았다** — 배출기(`gates/tools/gate_summary_json.py`)는 직렬화만 한다.」 실패명도 게이트가 찍고 실행기가 옮기며 배출기는 직렬화만 한다.
- 열을 실어 나르는 선언된 통로는 하나다 — 게이트가 stdout 에 표식 줄을 찍고(`frontend-test.sh:32-33` 의 `::gate-readiness-failure::gate=…|waited_for=…` 형식), 실행기가 `grep` 으로 집어(`run.sh:117`·`:769`) `summary_gate_row` 의 열로 넣고(`run.sh:77-79`·`:140`·`:805`), 배출기가 적는다(`gate_summary_json.py:66-83`). 임의 파일 직접 쓰기는 이 경로 밖이다.
- 준비 실패 표식 수집은 지금 `grep -m1` 이다(`run.sh:117`·`:769`). 실패 시험이 여럿이면 첫 줄만 남으므로 실패명 표식은 `-m1` 이 아닌 수집이 필요하다.
- 흔들림을 눈금으로 덮지 않는다. `gates/run.sh:761` 「상한 연장·재시도·병렬도 축소·건너뛰기로 green 을 만들지 않는다.」 이슈 ⑵ 의 「재시도로 green 을 만들지 않는다」와 같은 규율이다. 예산을 올리는 선택지는 실측 근거 없이는 이 문장에 걸린다.
- `frontend-test` 는 이미 `serial` 이다. `gates/config/parallelism.toml:147` 이고 사유는 `:139-146` 「자원 충돌이 아니라 **부하** 가 이유다. … ⚠ 이 값을 `parallel` 로 바꾸려면 **실측**이 필요하다」. 2026-09-03 `40edc652` 부터 그렇다. 즉 전수 `-j 4` 에서도 이 게이트 옆에는 다른 게이트가 서지 않는다 — 관측된 부하는 형제 게이트가 아니라 ⓐ vitest 자신의 워커 팬아웃과 ⓑ 같은 호스트의 다른 레인이다.
- `frontend-test.sh` 는 `COLAB_GATE_INNER_JOBS` 를 읽지 않는다(파일 전체에 참조 0건). 실행기가 단독 게이트에 `solo_inner=$ncpu` 를 넘기지만(`run.sh:666`·`:733`) 게이트는 무시하고 vitest 기본 팬아웃으로 돈다.
- 판정 명령을 게이트 사본으로 갈아타지 않는다. `frontend-test.sh:46-52` 가 `frontend/package.json` 의 `test` 가 `vitest run` 으로 시작하는지 대조하고(`frontend/package.json:12` = `"vitest run"`), 갈리면 red 다. 실패명 추출은 리포터 인자 수준에서 끝내야 하며 명령 자체를 갈아치우면 이 대조에 걸린다.

## 설계트리 (grill-me 결과)
- Q1 실패 시험명을 게이트가 직접 `gate-summary.json` 에 쓰는가 → A 아니다. 배출기 단일 작성자 규율(`gates/README.md:102`)을 깬다. 게이트는 표식 줄만 찍고 실행기가 옮긴다.
- Q2 그러면 `run.sh`·`gate_summary_json.py` 를 건드려야 하는데 폭발 반경이 크다. 대안은 → A 두 형태가 있다. ⓐ 공용 표식 `::gate-failure::` 를 만들어 **모든 게이트**가 쓸 수 있게 한다(일관되지만 실행기 공용 코드 변경) · ⓑ frontend-test 전용으로 `readiness` 열처럼 한 열만 더한다(좁지만 다음 게이트가 같은 요구를 낼 때 또 늘린다). **Ted 결정 지점 1.** 권고는 ⓐ — `readiness` 표식이 이미 게이트 공용 규약이라 같은 배치가 자연스럽다.
- Q3 `upload-transfer.test.tsx:326` 의 대기는 진짜 비동기 경계인가 → A 경계는 진짜지만 대기 방식이 벽시계다. `:326` 은 `fireEvent.click(await screen.findByRole('button', { name: '표준 격자 가져오기' }))` 이고, 그 버튼은 `:325` 의 파일 선택이 `sources.upload.gridOptions`(`:311-314` 에서 즉시 resolve 하는 async 함수)를 태운 뒤 React 가 커밋해야 선다. `findBy*` 는 testing-library 의 폴링 대기라 **해상도가 벽시계 1초**다. 해야 할 일은 마이크로태스크 한 바퀴뿐인데 예산은 CPU 굶주림에 노출된 1초다 — 부하에서 넘친다.
- Q4 `:326` 의 고침 형태는 (a) 격리 · (b) 실제 신호 대기 · (c) 예산 재산출 중 무엇인가 → A **(b)**. `fireEvent.change` 뒤에 `await act(async () => {});` 로 마이크로태스크를 비우고 `screen.getByRole(...)` 로 동기 조회한다. 같은 레포에 선례가 있다 — `frontend/test/lineage-unknown-20260907.test.tsx:344` 가 `await act(async () => {});` 를 그 용도로 쓴다. 벽시계가 판정에서 빠지므로 부하와 무관해진다. 격리(a)는 기전을 남긴 채 자리만 옮기는 것이고, 예산 재산출(c)은 없앨 수 있는 벽시계를 남긴다.
- Q5 `lineage-unknown-20260907.test.tsx` 전역 스캔의 5000ms 는 어디에 선언돼 있나 → A **어디에도 선언돼 있지 않다.** `frontend/vite.config.ts:15-40` 의 `test` 블록에 `testTimeout` 이 없고 레포 전체에 선언 0건이다. 5000ms 는 vitest(`frontend/package.json:33` = `4.1.11`)의 기본 `testTimeout` 이다. 이슈의 「5000ms 예산」은 레포가 정한 예산이 아니라 프레임워크 기본값이다.
- Q6 그 시험은 무엇을 기다리나 → A **아무것도 기다리지 않는다.** `:282-303` 은 전부 동기다. `:289-297` 의 `walk()` 가 `readdirSync`/`statSync` 로 `frontend/src`·`frontend/test` 를 훑고, `:300-301` 이 걸린 파일 전부를 `readFileSync(f,'utf8')` 로 읽는다. 현 트리 실측 = 대상 338 파일 · 약 3.9MB. 비동기 경계가 없으므로 「대기가 흔들린다」가 아니라 **작업량 자체가 IO 바운드**이고, 호스트 IO 경합에서 5초를 넘는다.
- Q7 그러면 (a)(b)(c) 중 무엇인가 → A (b)는 불가능하다 — 기다릴 신호가 없다. (a) 격리도 듣지 않는다 — vitest 워커 동시성이 아니라 IO 총량이 원인이다. 남는 것은 **(c) 실측 근거로 예산을 명시**하며, 그와 짝으로 **작업량을 줄이는 것**이다(현재는 파일 전문을 문자열로 올린 뒤 `includes` 한다). **Ted 결정 지점 2** — ⓐ 예산만 명시(`it(..., { timeout: N })`, N 은 실측)할지 ⓑ 예산 명시 ＋ 스캔 축소(한 번 읽어 `includes` 판정 후 즉시 버리기 · 대상 확장자 유지)를 함께 할지. 권고는 ⓑ. 단 N 의 실측이 이번 조사에서 금지된 게이트 실행을 요구한다(미해결 질문 참조).
- Q8 ⑶ 의 red(준비) 분류는 어디에 넣나 → A `frontend-test.sh:77-81` 의 `rc != 0` 갈래 **앞**이다. 출력이 fork worker 기동 시간초과일 때 `:31-39` 의 `ready_red` 로 78 을 낸다. 표식 형식은 그 함수가 이미 쓰는 `::gate-readiness-failure::gate=frontend-test|waited_for=…|limit=…|elapsed=…|detail=…` 를 그대로 쓴다.
- Q9 그 분류를 무엇으로 증명하나 → A `gates/tools/frontend-test-selftest.sh` 에 케이스 ⓔ 를 더한다. 하네스는 이미 있다 — `:35-40` `mk_tree`(사본 트리 · `node_modules` 심볼릭 링크) · `:47-58` `expect_case`(`green`/`red`/`red-ready` 3갈래) · `:76-79` 가 `red-ready` 를 이미 증명한다(vitest 실행 파일 부재). ⓔ 는 사본 트리의 `node_modules/.bin/vitest` 자리에 **기동 시간초과 문면을 찍고 비영으로 끝나는 스텁**을 놓아 분류기를 결정적으로 때린다. 진짜 시간초과를 재현하려 들면 그 자체가 부하 의존 시험이 된다.
- Q10 ⑵ 를 「재시도 금지」로만 읽으면 병렬도 축소는 되는가 → A 아니다. `gates/run.sh:761` 이 재시도와 병렬도 축소를 같은 줄에서 금지한다. `frontend-test` 는 이미 `serial` 이므로 더 줄일 게이트 수준 여지도 없다.
- Q11 ⑷ 를 단독 게이트 3회로 갈음할 수 있나 → A 아니다. 근거는 Q10·제약 6항 — `serial` 선언 때문에 `-j 4` 는 이 게이트 옆에 다른 게이트를 세우지 않고, 부하는 호스트 전역(다른 레인)에서 온다. 갈음하려면 「무엇이 부하였는지」를 다시 정의해야 하고 그것은 이 intent 가 정할 수 없다.

## 미해결 질문
- vitest 4.1.11 이 fork worker 기동 시간초과에 찍는 **축자 문면**을 확인하지 못했다. 이 워크트리에 `frontend/node_modules` 가 없어(파일 조회 0건) tinypool 원문을 읽을 수 없었다. 분류 정규식은 레인에서 실물 문면을 확인한 뒤 확정한다. 추측 문면으로 분류기를 쓰면 영영 걸리지 않는 갈래가 된다.
- Q7 의 예산 N 실측값. 전역 스캔의 실제 소요는 재 본 적이 없다. 이번 조사에는 게이트·vitest 실행 금지가 걸려 있어 측정하지 않았다.
- 간헐 red 의 표본이 1건이다(`NOTE.md` 관측 1건). `:348`·`:351` 의 같은 조회가 같은 기전으로 흔들릴 수 있으나 관측 기록은 없다. ⑴ 이 먼저 들어가야 이 표본이 쌓인다 — 구현 순서를 ⑴ → ⑶ → ⑵ 로 두는 근거다.
- Q2 의 ⓐ 를 고르면 `::gate-failure::` 를 다른 게이트(예 `service-tests-*`, `gates/tools/service-tests.sh:240` 「위 pytest 출력에 실패한 케이스 이름이 있다」)도 쓰게 할지가 뒤따른다. 이번 범위에서 다른 게이트를 개조할지는 정해지지 않았다.

## 범위 밖 (명시 제외)
- `GT-1` 묶음의 나머지 — `service-tests-viz-render` 가상환경 패키지 설치 누락 분류(#56 계열) · `tests/fixtures/setup-db.sh` 비멱등 · `migration-drift` 오라클 정비 · 호스트 시각 역행 탐지. `dev-package/work-items.yaml:3689` `GT-1` 이 한 묶음으로 적고 있으나 이 intent 는 이슈 #55 의 완료 조건 4건만 다룬다.
- 재시도·플레이크 재실행·시간초과 상한 인상만으로 green 만들기. 이슈 ⑵ 축자 금지이고 `gates/run.sh:761` 과 같은 규율이다.
- `frontend-test` 의 `serial` 선언 변경. `gates/config/parallelism.toml:143-146` 이 변경에 실측을 요구하며 이번 범위 밖이다.
- `colab-gate-summary/1` 의 `counts` 키 집합 변경 · 스키마 `/2` 승격 · 새 게이트 상태 신설.
- 시험이 판정하는 내용(assert) 변경. 대기 방식만 바꾼다.
- 다른 이슈 구현, 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- 프론티어 공집합 확인: 2026-09-17.
- Ted 확인 문장: 대기 중.
- 승인 필요 지점:
  - ⑴ 실패명 열의 통로 — 공용 표식 `::gate-failure::` 신설(`run.sh`·`gate_summary_json.py` 공용 변경) 대 frontend-test 전용 열 1개. 권고는 공용 표식.
  - ⑵-a `upload-transfer.test.tsx:326`(및 `:348`·`:351`)을 `await act(async () => {})` ＋ 동기 조회로 바꾸는 것. 권고안이며 `lineage-unknown-20260907.test.tsx:344` 가 선례다.
  - ⑵-b `lineage-unknown-20260907.test.tsx:282-303` 을 예산 명시만 할지, 예산 명시 ＋ 스캔 축소까지 할지. 권고는 둘 다.
  - ⑵-c 그 예산 N 을 실측하는 1회 측정을 레인에 허가할지. 이 조사에서는 실행하지 않았다.
  - ⑶ fork worker 기동 시간초과 red fixture 를 **vitest 스텁**으로 결정적으로 세울지, 진짜 시간초과 재현을 요구할지. 권고는 스텁.
  - ⑷ 전수 `-j 4` green 3회 연속을 레인 일정에 넣을지. 아래 일정 제약 참조.
- 일정 제약(이 intent 가 풀지 않는다): 완료 조건 ⑷ 는 **전수 `-j 4` 실행 없이는 충족될 수 없다.** `frontend-test` 가 `serial` 이라 단독 게이트 3회는 ⑷ 가 말하는 「같은 구성」이 아니다. 그리고 전수 실행은 `docs/decisions/0002-gate-running-lanes-run-alone.md` 에 따라 호스트에서 레인 하나만 돌 때 해야 하는 직렬 비용이다. 착수 레인의 일정 항목으로 잡는다.
- 재개봉 금지: 해당 없음(미승인 초안).

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/55
- 게이트: `gates/tools/frontend-test.sh:31-39`·`:46-52`·`:55`·`:58`·`:69`·`:77-81`·`:88`, `gates/tools/frontend-test-selftest.sh:35-40`·`:47-58`·`:76-79`
- 실행기·배출기: `gates/run.sh:77-79`·`:117`·`:140`·`:666`·`:733`·`:761`·`:769`·`:805`, `gates/tools/gate_summary_json.py:66-83`
- 소비자: `scripts/harness/verify_evidence.py:146-169`·`:192`, `.claude/hooks/lane-gate-summary.sh`, `gates/README.md:99-112`
- 병렬 선언: `gates/config/parallelism.toml:139-147`(도입 커밋 `40edc652` 2026-09-03)
- 시험: `frontend/test/upload-transfer.test.tsx:311-314`·`:325-326`·`:348`·`:351`, `frontend/test/lineage-unknown-20260907.test.tsx:282-303`·`:344`
- 설정: `frontend/vite.config.ts:15-40`(`testTimeout` 선언 없음), `frontend/package.json:12`·`:33`
- 결정: `docs/decisions/0004-gate-verdict-three-states.md:17`·`:41`, `docs/decisions/0002-gate-running-lanes-run-alone.md`
- 실물 근거: `dev-package/reports/r-data-canon/wu-c2a/NOTE.md`(마지막 항 관측 1건), `dev-package/work-items.yaml:3689` `GT-1`(note B1·B2)
- spec: 미작성. Ted 승인 뒤 합성한다.
- 결정: 신규 legacy 결정번호 발급 없음.

## advisor 검토 결과 (2026-09-17, 초안 작성 후 추가)
- [정정] Q5 의 결론이 범위를 좁게 읽힌다. `testTimeout` 선언이 레포 전체 0건인 것은 사실로 확인됐으나
  (`node_modules`·`.git` 제외 전수 조회), `frontend/test` 는 **질의별 명시 벽시계 대기로 포화돼 있다**.
  `const WAIT = { timeout: 5000 }` 가 최소 5개 파일(`preview-pick-and-fallback` ·
  `preview-controls-20260912` · `preview-slot-4x3` · `upload-pick-conditional-20260913` ·
  `preview-layout-20260912`)에 있고, `grid-preview.test.tsx` 와 `upload.test.tsx` 에
  `{ timeout: 4000 }` 이 약 40회 있다. 레포에 **사실상의 벽시계 예산 관행이 존재**한다.
- [영향] 따라서 이번에 다루는 시험 2건은 특별한 예외가 아니라 같은 부류의 표본이며, 흔들림 종류는
  레포 전역이다. 이번 범위를 2건으로 한정하는 것은 유효한 선택이지만, 「기본값이라 예산이 없다」가
  아니라 「관행 예산이 있고 이번엔 2건만 손댄다」로 근거를 바꿔 적어야 한다.
- [확인] `parallelism.toml:147` = `"frontend-test" = "serial"` 은 정확하다. 전수 `-j 4` 에서 옆에
  다른 게이트가 서지 않는다는 판정은 성립한다.
- [충돌] ⑴ 의 공용 표식은 `gates/run.sh:77-79` `summary_gate_row()` 의 **고정 4필드 위치 규약**을
  건드린다. `gate_summary_json.py` 가 `(parts + [""] * 5)[1:5]` 로 고정 자리에서 잘라내므로 5번째
  게이트 필드를 더하면 그 slice 가 어긋난다. #56 의 승격 작업도 같은 행을 만드는 `run.sh:769-778`
  표식 주사 루프를 고친다 — **같은 두 파일·같은 함수**다. 두 건을 병렬 레인으로 돌리지 않는다.
- [해소] 스키마 범프 우려는 근거 없다. ADR-0004 재검토 조건은 「`counts` 키 집합이 바뀔 때」로 적혀
  있고 ⑴ 은 게이트 **행**에 붙지 `counts` 에 붙지 않는다. #56 과 함께 해도 범프는 **0회**다.
