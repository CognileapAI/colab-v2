# design-fix 20260924 · CI 경합 수정 레인 F-ci 보고

- spec: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「CI 경합 수정 레인 F-ci」 항목 1–4
- intent: `dev-package/intent/2026-09-25-design-fix-20260924.md` — 커밋 4개 모두 꼬리표 `Intent-Ref:` 를 마지막 줄에 둠
- 기준 HEAD: `6f8cd74c`(브랜치 `worktree-design-review-apple-20260924`) — `git merge --ff-only 6f8cd74c…` 뒤 `git rev-parse HEAD` 일치 · 레인 브랜치 `worktree-wf_669944f2-38e-1`
- lifecycle task: `199d9c9661a34632a8b3d7df2241b65e`(role lane-worker · 선언 게이트 4 — frontend-typecheck · frontend-test · frontend-fixture-reach · frontend-design-lint)
- 준비: `frontend/` 에서 `npm ci` 종료 0
- 진단 입력: 강제 지연 재현 `zz-forced-late.test.tsx` · 수정 후보 `zz-forced-late-fixed.test.tsx`(진단 워크플로 산출물 · 레포 밖 · 커밋하지 않음)

## 1. 단계 · 커밋

| 단계 | 커밋 | 변경 파일 |
|---|---|---|
| 시험 작성(RED) — 항목 2·3·4 ＋ 헬퍼 | `bb6f16e8` | 새 `frontend/test/design-fix-20260924-F-ci.test.tsx` · 새 `frontend/test/helpers/previewDraw.ts` · 기존 시험 14파일 |
| 시험 — 역할명 클릭 2곳 추가 교체 | `812c95e9` | `frontend/test/scale-ladder.test.tsx` |
| 구현 — 항목 1 | `2398cd2d` | `frontend/src/components/upload/PreviewPanel.tsx`(1파일 · +5) |
| 보고 | 이 파일의 커밋 | 이 파일 |

- 구현 커밋 `2398cd2d` 의 변경 파일은 `frontend/src/**` 1개뿐이고 `frontend/test/**` · `gates/**` · `contracts/**` 는 0(`git show --stat` 로 확인).
- 시험 커밋이 구현 커밋보다 앞선다. `812c95e9` 는 전체 실행 중 `grep 'up-preview-draw'` 밖의 같은 버튼 클릭 자리(`findByRole('button', { name: /미리보기 그리기/ })`)를 찾아 구현 커밋 전에 따로 넣은 것이다.

## 2. 항목 · before → after

| # | 파일 | before | after |
|---|---|---|---|
| 1 | `PreviewPanel.tsx` `up-preview-draw` | `uploadId` 만 있으면 첫 렌더부터 누를 수 있음. 팔레트 도착 전 클릭은 `draw()` 첫 줄 `if (!uploadId \|\| !palette) return;` 에서 조용히 버려짐 | `disabled={!palette}`. 팔레트 조회 실패 → 기존 catch 가 `setError(UNAVAILABLE)` → `up-preview-error`「지금 미리보기를 만들 수 없어요. …」. 빈 목록 → 기존 `up-palette-issue`「팔레트 목록이 예상한 3종과 달라요. …」. 새 색·토큰·문구 0 |
| 2 | 새 `design-fix-20260924-F-ci.test.tsx` | — | 5건: ① 팔레트 전 disabled · 비활성 중 클릭은 `createRender` 0회 · 슬롯 `idle` ② 팔레트 도착(deferred resolve) 뒤 enabled · 누르면 `style.palette='viridis'` 로 1회 그리고 그림이 선다 ③ 강제 지연(팔레트가 클릭 시도 뒤 20ms) — 헬퍼로 누르면 그림이 선다 ④ 조회 실패 → disabled ＋ `up-preview-error` ⑤ 빈 목록 → disabled ＋ `up-palette-issue` |
| 3 | 새 `frontend/test/helpers/previewDraw.ts` ＋ 15파일 | 버튼이 보이자마자 누름(일부는 팔레트 값 대기, 일부는 `up-style-palette` 존재만 대기 — 항상 참) | `clickPreviewDrawWhenReady({ wait?, click? })` — `waitFor` 로 `disabled=false` 까지 기다린 뒤 누른다. `wait` 는 종전 `findByTestId` 에 넘기던 값을 그대로(`upload-pick-conditional` 의 `WAIT`), `click` 은 `upload.test.tsx` 고유 `click`(누른 뒤 `act` 한 바퀴)을 그대로. 판정 `expect` 값 변경 0 |
| 4 | `thumb-nudge-20260905.test.tsx` | `15062c91` 의 `DRAWN_TIMEOUT_MS = 20_000` 을 두 시험(17 · 대조)에 적용 | 되돌림 — 시험 한도는 vitest 기본(5초). 근거: 원인은 버려진 클릭이라 한도를 늘려도 그려지지 않는다(spec F-ci 절 · PR #141 CI attempt 1 에서 `15062c91` 뒤에도 17번이 `idle` 로 red) |

- 항목 4 범위 조사: `git log -S "timeout: "` 로 교체 대상 파일들의 한도 도입 커밋을 확인. `4000`·`5000` 한도는 각 시험 도입 커밋(`875aa2a0` · `e235f456` · `6afa776a` · `ccaf27f6` · `ec59f7de` · `fa170ed9`)에서 정해진 값이고 vitest 기본 시험 한도(5초) 이하라 두었다. `fbaf18ad` 의 `LEGACY_SCAN_BUDGET_MS = 2000` 은 실측 근거가 있는 예산이라 대상이 아니다.

## 3. 교체 자리 전수(sites)

`grep -rn "up-preview-draw" frontend/test`(작업 전 44줄) 중 누르는 자리 35곳 ＋ `grep -rn "미리보기 그리기" frontend/test` 로 찾은 역할명 클릭 2곳 = 37곳. 앞 번호는 작업 전 줄, 뒤는 작업 뒤 줄.

| 파일 | before(줄 · 형태) | after(줄) |
|---|---|---|
| `upload-transfer` | 287 `fireEvent.click(getByTestId)` | 288 |
| `upload-progress-recovery` | 43 · 56 · 81 `fireEvent.click(await findByTestId)` | 44 · 57 · 82 |
| `preview-controls-20260912` | 96 `fireEvent.click(getByTestId)` | 97 |
| `grid-preview` | 100 `fireEvent.click(await findByTestId)` · 165 `fireEvent.click(getByTestId)` | 101 · 166 |
| `preview-layout-20260912` | 115 `const draw = findBy…` → `fireEvent.click(draw)` · 207 같은 형태 · 213 `fireEvent.click(getByTestId)` | 117 · 208 · 212 |
| `design-fix-20260924-L3` | 91 `const draw = findBy…` → `fireEvent.click(draw)` | 93 |
| `upload-preview-poll-20260903` | 64 `const draw = findBy…` → `fireEvent.click(draw)` 두 번(①·②) · 91 `fireEvent.click(await findByTestId)` | 65 · 68 · 90 |
| `preview-pick-and-fallback` | 144 `const draw = findBy…` → `fireEvent.click(draw)` | 146 |
| `design-fix-20260924-L3b` | 84 `const draw = findBy…` → `fireEvent.click(draw)` | 86 |
| `thumb-nudge-20260905` | 155 `fireEvent.click(await findByTestId)`(`drawn()`) | 150 |
| `preview-slot-4x3` | 128 `fireEvent.click(getByTestId)` · 140 · 157 · 173 `fireEvent.click(await findByTestId)` | 129 · 141 · 158 · 174 |
| `preview-map-viewport-20260918` | 112 `const draw = findBy…` → `fireEvent.click(draw)` | 114 |
| `upload` | 585 · 615 · 637 · 649 · 675 · 688 · 699 · 1232 · 2133 · 2145 · 2168 · 2191 `await click(await findByTestId)` | 586 · 616 · 638 · 650 · 676 · 689 · 700 · 1233 · 2134 · 2146 · 2169 · 2192 (`{ click }`) |
| `upload-pick-conditional-20260913` | 149 `fireEvent.click(await findByTestId(…, WAIT))` | 150 (`{ wait: WAIT }`) |
| `scale-ladder` | 255 · 263 `fireEvent.click(await findByRole('button', { name: /미리보기 그리기/ }))` | 256 · 264 |

누르지 않는 자리 10곳은 그대로 둠: `upload-progress-recovery:84`(`toBeEnabled` 단언) · `preview-layout-20260912:158`(목록 상수) · `:162` · `:171` · `:188` · `:198` · `:229`(존재 대기 뒤 배치 단언) · `upload:2614`(목록 상수) · `thumb-nudge-20260905:44`(넛지 시험 마운트 대기) · `preview-slot-4x3:124`(idle 상자 측정 전 대기).

## 4. RED 증거

- 시험 커밋 `bb6f16e8` 트리(제품 변경 전)에서 `npx vitest run` 15파일: `Tests 5 failed | 306 passed (311)` — 실패 5건 모두 `design-fix-20260924-F-ci.test.tsx`.
  - ①·②·④·⑤: `Error: expect(element).toBeDisabled()` · `Received element is not disabled:`
  - ③ 강제 지연: `TestingLibraryElementError: Unable to find an element by: [data-testid="up-preview-image"]`(헬퍼가 즉시 활성인 버튼을 누르고 클릭이 `draw()` 에서 버려짐)
- 구현 뒤 같은 15파일 `Tests 311 passed (311)` · `scale-ladder` 16 통과 · `tsc --noEmit` 종료 0.

## 5. 경합 증명(최종 트리 `2398cd2d`)

| 대상 | 반복 | 결과 |
|---|---|---|
| `thumb-nudge-20260905.test.tsx`(5건) | 20회(별도 프로세스) | 통과 20 / 실패 0 |
| `preview-slot-4x3.test.tsx`(8건) | 20회 | 통과 20 / 실패 0 |
| 강제 지연 재현 — 진단 사본의 클릭 한 줄만 헬퍼로 바꾼 임시 사본 | 20회 | 통과 20 / 실패 0 |
| 강제 지연 재현 — 진단 사본 그대로(보이자마자 누름) | 3회 | 통과 0 / 실패 3 — 비활성 버튼 클릭은 무시되어 그림이 서지 않음. 제품이 이른 클릭을 받지 않는다는 뜻이고, 시험이 헬퍼를 써야 하는 이유다 |

- 임시 사본 2개는 `frontend/test/` 에 두고 실행한 뒤 지웠다(커밋 0). 반복 실행은 부하 없는 호스트 단독 구간이다 — CI 부하 조건 재현은 아니다. 강제 지연 사본이 시간 요인을 20ms 고정 지연으로 대신한다.

## 6. 게이트

- run `18ea79f9fdc24cc68fec76cd11728e68`(커밋 `2398cd2d` · 이 보고서 작성 전): green 4 / red(판정) 0 / red(준비) 0 — frontend-typecheck 오류 0 · frontend-test `Test Files 140 passed` · `Tests 1824 passed` · frontend-fixture-reach 금지 모듈 0 · frontend-design-lint 전 항목 0(면제 6).
- 보고서 커밋 뒤 최종 run 은 레인 최종 메시지의 `COLAB_HANDOFF` 줄에 적는다.
- 시험 수: 140파일 1824건. 이 레인이 더한 것은 새 파일 1개 · 5건이고 기존 시험의 건수 변경은 0(교체는 누르는 방식만 바꿈).

## 7. 원한 결과 대조

- 미달 0: 항목 1–4 수행 · RED 확인 · 커밋 꼬리표 · 경합 증명 20×2 ＋ 강제 지연.
- 초과: ① `scale-ladder.test.tsx` 2곳 교체(지시 grep 밖 · 같은 버튼) ② F-ci 시험 ④·⑤(팔레트 실패·빈 목록 — 항목 1 의 「설명 없이 죽지 않음」 검증용) ③ `fireEvent` 가 쓰이지 않게 된 3파일의 import 정리(`preview-controls-20260912` · `preview-slot-4x3` · `upload-preview-poll-20260903` — `noUnusedLocals` 로 typecheck red).

## 8. 남은 위험 · 후속

- 빈 목록일 때 안내 문면 「…받은 목록을 표시하고 있어요」는 받은 목록이 0개인 경우에도 같은 문장이다. 새 문구 금지라 그대로 두었다 — 빈 목록 전용 문면이 필요하면 기획 판정 대상.
- 팔레트 조회 실패 뒤 다시 조회하는 경로가 없다(`useEffect([source])` 1회). 버튼은 비활성으로 남고 오류 문면이 이유를 말하지만 재시도 수단은 없다 — 기존 동작이며 이 레인 범위 밖.
- 브라우저 여정 스크립트 `scripts/upload-preview-journey.py:161` 은 접기 안 버튼을 활성 대기 없이 누른다(같은 파일 `:163` 은 `:not(:disabled)` 대기). `scripts/issue-73-82-journey.py:159` 는 팔레트를 고른 뒤 누르므로 팔레트는 준비된 상태다. 두 스크립트는 어떤 게이트에도 걸리지 않는다 — 제품 변경 뒤 `:161` 경로를 실제로 밟으면 클릭이 무시될 수 있어 후속 점검 항목.
- UI 동작 변경(버튼 비활성)의 실제 브라우저 검증은 이 레인에서 하지 않았다(agent-browser 기동 0). jsdom 시험만으로 판정.
