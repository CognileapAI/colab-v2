# Intent: frontend/test 의 사실상 벽시계 예산 관행을 실제 신호 대기로 옮긴다
메타 — 발의자: Ted · 방향 결정: Ted · 작성 2026-09-17 · 승인: 미승인 — Ted 승인 대기(미결 5건)

⚠ **이 intent 는 독립 결정이다.** `2026-09-17-harness-enforces-facts-it-holds.md` 의 규칙 문장에
자동 정렬되지 않는다 — 그 규칙은 **실행기가 쥔 사실**을 다루고, 여기 77 자리는 시험이 스스로
고른 예산이다. 그쪽 intent 도 이 파일을 「이 규칙의 사례가 아님」으로 분류한다.

## 문제
- `#55` 를 고치는 동안 드러난 것 — 레포에 **선언되지 않은 벽시계 예산 관행**이 있다. `#55` 의 intent 는 이를 각주로만 적었다(`dev-package/intent/2026-09-17-issue-55-frontend-test-failure-naming.md:92` 축자 「`{ timeout: 4000 }` 이 약 40회 있다. 레포에 **사실상의 벽시계 예산 관행이 존재**한다.」). 실측하면 40 이 아니다.
- 실측 (현 트리 · `claude/followup-intents`):
  - `const WAIT = { timeout: 5000 };` 선언이 **6 파일**이다. `frontend/test/preview-pick-and-fallback.test.tsx:38` · `frontend/test/preview-layout-20260912.test.tsx:32` · `frontend/test/preview-slot-4x3.test.tsx:34` · `frontend/test/preview-controls-20260912.test.tsx:30` · `frontend/test/upload-pick-conditional-20260913.test.tsx:26` · `frontend/test/upload-preview-poll-20260903.test.tsx:49`. 마지막 하나는 이제껏 집계에 안 잡혔다.
  - 그 `WAIT` 을 넘기는 호출 자리는 **45개**다(식별자 등장 51회 − 선언 6회). 파일별로 17 · 14 · 9 · 4 · 4 · 3 이다.
  - `{ timeout: 4000 }` 은 **28개**다 — `frontend/test/grid-preview.test.tsx` 18 · `frontend/test/upload.test.tsx` 10. 「약 40」은 과다 계상이었다. ⚠ 2026-09-18 develop 재계수에서 `git grep` 히트는 **29건**이지만 그중 `frontend/test/lineage-unknown-20260907.test.tsx:296` 은 **주석**(「레포의 관행 예산은 `{ timeout: 4000 }`·`{ timeout: 5000 }` 이고」)이다. 실제 호출 자리는 **28개가 맞다.**
  - 인라인 `timeout: 5000` 1개 — `frontend/test/thumb-nudge-20260905.test.tsx:157`.
  - 낱개 3개 — `frontend/test/upload-progress-recovery.test.tsx:107`(3000) · `:115`(4500) · `frontend/test/unfinished-uploads.test.tsx:226`(2500).
  - **합계 77 자리 · 10 파일.**
- `testTimeout` 은 레포 전체에 **0건** 선언돼 있다. `frontend/vite.config.ts:15-24` 의 `test` 블록은 `globals`·`environment`·`setupFiles`·`include` 만 잡는다. 나머지 전부를 프레임워크 기본값이 지배한다. `#55` 의 설계트리 Q5(`:38`)가 같은 사실을 적는다.
- **그리고 위 77 자리는 `testTimeout` 이 아니다.** 전부 `screen.findBy*` 의 세 번째 인자이거나 `waitFor` 의 두 번째 인자다(실물 예 — `frontend/test/upload.test.tsx:596` `await screen.findByTestId('up-preview-map', undefined, { timeout: 4000 });`, `frontend/test/thumb-nudge-20260905.test.tsx:155-157` `waitFor(..., { timeout: 5000 })`). 이것은 testing-library 의 async util 예산이고 기본값은 **1000ms** 다. vitest 의 `testTimeout` 기본값 5000ms 와 다른 축이다. `frontend/test/setup.ts` 는 1줄(`import '@testing-library/jest-dom/vitest';`)뿐이라 `configure({ asyncUtilTimeout })` 도 없다.
- 이 77 자리는 `#55` 가 방금 고친 것과 **같은 흔들림 부류**다. `#55` 설계트리 Q3 축자 — 「`findBy*` 는 testing-library 의 폴링 대기라 **해상도가 벽시계 1초**다. 해야 할 일은 마이크로태스크 한 바퀴뿐인데 예산은 CPU 굶주림에 노출된 1초다 — 부하에서 넘친다.」 예산을 4000·5000 으로 올려 둔 자리는 그 넘침을 뒤로 미룬 것이지 없앤 것이 아니다. 구조상 부하 민감하다.

## 원한 결과 (proposed outcome)
- 진짜 비동기 경계가 마이크로태스크 한 바퀴인 자리에서는 벽시계가 판정에서 빠진다. `#55` 가 채택한 `await act(async () => {});` ＋ 동기 조회 형태다.
- 벽시계가 불가피한 자리(IO 총량·타이머 실물)는 예산을 **한 곳에** 선언하고, 그 값이 성능 단언이 아니라 **병리 탐지기**임을 문면으로 남긴다.
- 흔들릴 때마다 한 파일씩 땜질하는 현 상태를 끝낸다. 어느 자리가 의도된 예산이고 어느 자리가 관성인지 읽는 사람이 구분할 수 있다.
- 기존 green 이 한 건도 약해지지 않는다. 특히 예산을 **좁히는** 변경은 그 자체로 새 흔들림 생산자다.

## 영향 범위
- 시험 파일 10개 · 호출 자리 77개. `frontend/test/preview-pick-and-fallback.test.tsx`(17) · `frontend/test/grid-preview.test.tsx`(18) · `frontend/test/preview-layout-20260912.test.tsx`(14) · `frontend/test/upload.test.tsx`(10) · `frontend/test/upload-pick-conditional-20260913.test.tsx`(9) · `frontend/test/preview-slot-4x3.test.tsx`(4) · `frontend/test/upload-preview-poll-20260903.test.tsx`(4) · `frontend/test/preview-controls-20260912.test.tsx`(3) · `frontend/test/upload-progress-recovery.test.tsx`(2) · `frontend/test/unfinished-uploads.test.tsx`(1) · `frontend/test/thumb-nudge-20260905.test.tsx`(1).
- 설정: `frontend/vite.config.ts:15-24` 또는 `frontend/test/setup.ts:1` 중 한 곳에 예산 선언이 생길 수 있다.
- 제품 코드 · 서비스 · 스키마 · 계약: 없음.
- 계약 파괴 여부: 아니오.

## 제약
- **너무 좁은 예산은 그 자체가 흔들림 생산자다.** 이 명제가 선택지 (b) 를 실질적으로 죽인다 — 77 자리를 지우면 예산이 testing-library 기본값 1000ms 로 **떨어진다**(4000·5000 → 1000). 완화가 아니라 4~5배 조임이다.
- 그래서 `testTimeout` 선언으로는 이 77 자리를 대체할 수 없다. 축이 다르다. 대응하는 중앙 손잡이는 `configure({ asyncUtilTimeout })`(`@testing-library/dom`)이며 `frontend/test/setup.ts:1` 이 그 자리다. 이 사실을 확인하지 않고 (b) 를 고르면 전 파일이 red 가 된다.
- `#55` 는 자기 예산을 p50 실측의 약 350배로 잡았다. 성능 단언이 아니라 **병리 탐지기**로서다 — 정상 회차가 넘을 수 없는 값을 두고, 넘으면 그것이 성능 저하가 아니라 고장이라는 뜻이 되게 한다. 여기서 예산을 정하는 자리도 같은 규율을 따른다. (배수 확인 — develop 의 `frontend/test/lineage-unknown-20260907.test.tsx:288` 이 p50 5.6ms 를 적었고 `:297` 의 예산이 2000ms 이므로 약 357배다.)
- 흔들림을 눈금으로 덮지 않는다. `gates/run.sh:775` 축자 — 「상한 연장·재시도·병렬도 축소·건너뛰기로 green 을 만들지 않는다.」 예산을 **올리는** 방향의 변경은 실측 없이는 이 문장에 걸린다.
- 이번 회차에 vitest 실행이 금지돼 있다. 모든 수치는 정적 계수이며 p50 실측은 없다.
- `#55` 가 이미 손댄 2건은 이 intent 의 대상이 아니다. **그 수정은 PR #113(`dda542f1`)으로 develop 에 병합됐다**(2026-09-18 확인 · 초안의 「현 트리에는 아직 없다」는 낡았다). develop 실물 — `frontend/test/upload-transfer.test.tsx:326-329`·`:352-353`(`findBy*` → `await act(async () => {});` ＋ 동기 조회), `frontend/test/lineage-unknown-20260907.test.tsx:285-297`(`LEGACY_SCAN_BUDGET_MS = 2000` 이 `:297` 에 선언되고 `:302` 의 `it()` 두 번째 인자로 들어간다).

## 설계트리 (grill-me 결과)
- Q1 관행이 실제로 있는가 → A 있다. 6 파일이 같은 이름(`WAIT`)의 같은 값(5000)을 독립적으로 선언했고, 두 파일이 28 자리에 4000 을 뿌렸다. 우연이 아니라 복제된 관행이다.
- Q2 「약 40회」가 맞나 → A 아니다. `{ timeout: 4000 }` 은 28개다. 전체 벽시계 자리는 77개다. `#55` intent 의 각주 수치를 이 intent 가 정정한다.
- Q3 `testTimeout` 을 선언하면 되나 → A **아니다. 축이 다르다.** 77 자리는 전부 `findBy*`/`waitFor` 의 async util 예산(기본 1000ms)이고 `testTimeout` 은 `it()` 전체 예산(기본 5000ms)이다. 중앙 선언의 후보는 `configure({ asyncUtilTimeout })` 이고 자리는 `frontend/test/setup.ts:1` 이다.
- Q4 (b) 「중앙 선언 ＋ 개별 예산 삭제」의 실제 결과는 → A 4000·5000 이 1000 으로 **좁아진다**. 제약 첫 항목에 정면으로 걸린다. `asyncUtilTimeout` 을 5000 으로 올려 놓고 삭제하면 값은 보존되지만, 그때는 **모든 시험이 5초 예산을 갖게 되어** 지금 1초로 충분한 자리까지 느슨해진다. 어느 쪽이든 순수 이득이 아니다.
- Q5 (a) 실제 신호 대기로 바꾸는 것은 전부에 적용되나 → A 아니다. 폴링이 필요한 자리가 남는다. 그러나 `#55` Q3 의 판정이 여기에도 적용될 자리가 많다 — `frontend/test/upload.test.tsx:596`·`:650`·`:676`·`:689` 는 `up-preview-map`·`up-preview-tile` 이 뜨기를 기다리는데, 그 앞 단계가 즉시 resolve 하는 mock 이면 필요한 것은 마이크로태스크 한 바퀴뿐이다. 자리별 판정이 필요하다.
- Q6 (c) 흔들릴 때만 파일 단위로 전환하는 것은 → A 지금까지의 방식이고, 그 결과가 이 77 자리다. 다만 **77 자리 일괄 전환의 위험이 이득보다 크다** — 각 자리가 진짜 폴링인지 마이크로태스크인지는 개별 판정이고, 77건을 한 PR 에서 판정하면 검토가 불가능해진다.
- Q7 그러면 권고는 → A **(a) 를 목표로 하되 (c) 의 속도로 간다.** 구체적으로 ① `frontend/test/setup.ts:1` 에 `configure({ asyncUtilTimeout: 5000 })` 를 선언해 관행 값을 **문면화**하고 근거 주석을 단다(병리 탐지기라는 규율 포함) ② 그 위에서 중복이 된 6개 `WAIT` 선언과 45개 전달 자리를 지운다 — 값이 보존되므로 안전한 기계적 삭제다 ③ `{ timeout: 4000 }` 28개는 5000 보다 좁으므로 **남긴다**(지우면 넓어진다 — 판정이 느슨해진다) ④ `upload.test.tsx` · `grid-preview.test.tsx` 의 실제 신호 전환은 별도 후속 레인으로 분리한다.
- Q8 각 선택지가 만지는 크기는 → A (a) 전량 = 10 파일 · 77 자리. (b) 설정 1 파일 ＋ 10 파일 · 77 자리 삭제(그리고 값이 1000 으로 좁아짐). (c) 흔들린 파일만 = 회차당 1 파일 내외. (d) 0. 권고안 Q7 = 설정 1 파일(`frontend/test/setup.ts:1`) ＋ 6 파일 · 51 자리 삭제, 나머지 31 자리는 손대지 않음.
- Q9 이것이 게이트 판정을 바꾸나 → A 아니다. 통과 건수도 시험 이름도 그대로다. `#55` 의 게이트 요약 작업과 독립이다.

## 미해결 질문
- 77 자리 각각이 진짜 폴링인지 마이크로태스크 한 바퀴인지 미판정. 이번 회차는 정적 계수만 했다. 레인이 먼저 열 자리 — `frontend/test/upload.test.tsx:596` · `frontend/test/grid-preview.test.tsx` 의 첫 `timeout: 4000` 자리 · `frontend/test/preview-pick-and-fallback.test.tsx:38`(WAIT 17회로 최다).
- `asyncUtilTimeout` 기본값이 이 레포의 testing-library 판에서 실제로 1000ms 인지 미확인. 근거를 `frontend/package.json` 의 `@testing-library/dom`·`@testing-library/react` 판번호에서 확인해야 한다. 레인은 `frontend/package.json` 을 열어 판번호를 먼저 적는다. **이 값이 다르면 Q4·Q7 의 판단이 바뀐다.**
- `configure()` 가 `frontend/test/setup.ts:1` 에서 전 시험에 걸리는지 미확인(`frontend/vite.config.ts:18` 의 `setupFiles` 경로가 그 파일이다). 실행 금지라 확인하지 못했다.
- ~~`#55` 의 「p50 의 약 350배」 실측값~~ — 닫혔다. develop 의 `frontend/test/lineage-unknown-20260907.test.tsx:285-289` 가 실측을 주석으로 남겼다(대상 338 파일 / 3,343,168 바이트 · 13회 반복 · 현재 min 4.9 · **p50 5.6** · max 9.3 ms). `LEGACY_SCAN_BUDGET_MS = 2000`(`:297`)은 p50 5.6ms 의 약 357배다.
- 6개 `WAIT` 선언이 전부 `findBy*`/`waitFor` 로만 흘러가는지 부분 확인. 표본 6자리(`frontend/test/preview-pick-and-fallback.test.tsx:107`·`:141`·`:149`·`:152`·`:198`·`:209`)가 `findByTestId` 였다. 나머지 39 자리는 미대조 — 만약 `it()` 의 옵션 인자로 쓰인 자리가 섞여 있으면 그 자리는 축이 달라 일괄 삭제 대상에서 빠진다.

## 범위 밖 (명시 제외)
- `#55` 가 이미 다루는 2건(develop 기준 `frontend/test/upload-transfer.test.tsx:326-329`·`:352-353`, `frontend/test/lineage-unknown-20260907.test.tsx:283-302`).
- `vitest` 의 `testTimeout` 선언. 축이 달라 이 문제를 풀지 않는다. 필요하면 별건으로 세운다.
- 예산을 **올리는** 변경. 실측 없이는 `gates/run.sh:775` 에 걸린다.
- `{ timeout: 4000 }` 28 자리의 실제 신호 전환. 후속 레인으로 분리한다.
- 재시도·플레이크 재실행·`-j` 축소 도입.
- 제품 코드·계약·게이트 스크립트 변경.
- 다른 이슈 구현, 커밋·push·PR 게시·배포·이슈 댓글·종결.

## 확인
- Ted 확인 문장: 대기 중.
- 승인 필요 지점:
  - ⑴ 권고안(Q7 의 ①②③④ 4단)을 채택할지, 아니면 (c) 단독 — 흔들릴 때만 전환 — 으로 둘지.
  - ⑵ `frontend/test/setup.ts:1` 에 `configure({ asyncUtilTimeout: 5000 })` 를 선언해 관행 값을 문면화하는 것을 허용할지. 이 값은 성능 단언이 아니라 병리 탐지기로 적는다.
  - ⑶ 6개 `WAIT` 선언과 45개 전달 자리의 일괄 삭제를 이 PR 에 넣을지, ②를 별도 커밋으로 가를지.
  - ⑷ `{ timeout: 4000 }` 28 자리를 남기는 판단(삭제하면 5000 으로 넓어져 판정이 느슨해진다)을 확정할지.
  - ⑸ `asyncUtilTimeout` 기본값과 `configure()` 적용 여부를 확인하는 vitest 1회 실행을 레인에 허가할지.
- 삭제된 항목 — ~~⑹ 이 intent 를 `#55` 와 같은 PR 에 얹을지~~. **무효**다. `#55` 는 PR #113(`dda542f1`)으로 이미 병합됐으므로 얹을 PR 이 없다. 이 intent 는 별도 PR 로 간다.
- 남은 승인 필요 지점: **⑴~⑸ 5건.** 2026-09-18 의 하네스 결정 묶음은 이 파일을 건드리지 않았다 — 독립 결정이다.
- 재개봉 금지: 해당 없음(미승인).

## 참조
- 이슈: https://github.com/CognileapAI/colab-v2/issues/55 (이 intent 는 그 작업 중 드러난 별건이다)
- 선행 intent: `dev-package/intent/2026-09-17-issue-55-frontend-test-failure-naming.md:20`·`:36`·`:38`·`:92-95`
- 선행 spec: `dev-package/prd/specs/2026-09-17-issue-55-56-gate-verdict-reliability.md`
- `WAIT` 선언: `frontend/test/preview-pick-and-fallback.test.tsx:38` · `frontend/test/preview-layout-20260912.test.tsx:32` · `frontend/test/preview-slot-4x3.test.tsx:34` · `frontend/test/preview-controls-20260912.test.tsx:30` · `frontend/test/upload-pick-conditional-20260913.test.tsx:26` · `frontend/test/upload-preview-poll-20260903.test.tsx:49`
- 4000 자리: `frontend/test/grid-preview.test.tsx`(18) · `frontend/test/upload.test.tsx:596`·`:650`·`:676`·`:689` 외(10)
- 낱개: `frontend/test/thumb-nudge-20260905.test.tsx:157` · `frontend/test/upload-progress-recovery.test.tsx:107`·`:115` · `frontend/test/unfinished-uploads.test.tsx:226`
- 설정: `frontend/vite.config.ts:15-24`, `frontend/test/setup.ts:1`
- 규율: `gates/run.sh:775`
- spec: 미작성. Ted 승인 뒤 합성한다.
- 결정: 신규 legacy 결정번호 발급 없음.
