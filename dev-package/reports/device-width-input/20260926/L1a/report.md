# 레인 보고 — L1a 지도 시범 핵심(지도 칸 폭 · 아래 블록 · 입력 방식 · 데이터에 맞춤)

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 「레인 확정」 L1a 줄 · 부록 I 「L1」 행 · 구현 결정 「미리보기 지도 시범」 · 시험 결정
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-l1a` · 기준 `351a1962`(통합 브랜치 `claude/device-width-input-impl` 머리) · 구현 커밋 `6c8d460a` · `f39b4301`
- task: `49e2db6a19bb46f6b2fadf634a65c872`(게이트 `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint` · `frontend-visual` · 범위 선언 없음)
- 판정: **L1a 완료.** 시험 RED 23 실패 → GREEN 27 통과 · 게이트 green 5 / red(판정) 0 / red(준비) 0 · 390 레인 L1 판정 red 0 · 820 · 507 가림 0 · 390 값 결과 장면 `map.valueState` = 값 · 1440 대 B0 픽셀 차이 0.

## 1. 바뀐 것

| 파일 | 변경 |
|---|---|
| `frontend/src/components/preview/useMapCellWidth.ts`(새) | 지도 칸 폭 측정 훅 `useMapCellLayout` · 경계 상수 `MAP_CELL_BOUNDARY = 810`. 첫 레이아웃 읽기(`getBoundingClientRect`) ＋ `ResizeObserver` `contentRect.width` · 폭 0 · `ResizeObserver` 없음 = 「모름」(지금 배치) · 상태는 배치 값(모름 · 위 · 아래)이라 경계를 넘을 때만 바뀜 |
| `frontend/src/components/common/useInputMode.ts`(새) | 입력 방식 훅 `useInputMode`(`(pointer: coarse)` · `useSyncExternalStore` 로 변화 구독 · 매체 질의 없음 = 마우스). TSX 의 입력 매체 조건 문자열은 이 파일 한 곳 |
| `frontend/src/components/preview/PreviewOverlay.tsx` | 배치 규칙 한 곳: `below` · `shot` 속성 추가 · 좁은 칸에서 도구 층에는 `bottomRight`(확대 묶음)만 · 새 `PreviewBelow`(순서 좌표 · 값 조회 → 범례 → 스크린샷). 도구 층 요소는 남고 모서리 묶음만 빈다. 넓은 칸 · 모름의 DOM 은 종전과 같다 |
| `frontend/src/components/preview/PreviewPanels.tsx` | `PreviewMap` 이 지도 구역에 폭 훅을 달고, 도구 네 자리를 한 객체로 만들어 도구 층과 아래 블록에 같이 넘긴다. 아래 블록은 뷰포트 JSX 밖(Fragment 의 지도 구역 형제 자리)에서 만든다 — 상세 = 틀 묶음 아래 자리로 portal · 미등록 = 지도 구역 바로 뒤 형제. 뷰포트 핸들러 변경 0 |
| `frontend/src/components/preview/PreviewSlot.tsx` | 틀 뒤 · 같은 틀 묶음 안에 아래 자리(`.pv-frame-below`) ＋ 그 요소를 알리는 문맥 `PreviewSlotBelow`. 틀 바깥 치수 · 틀 묶음 클래스 이름 그대로 |
| `frontend/src/components/preview/PreviewZoomControls.tsx` | 터치일 때만 3단추 줄 밖 같은 모서리에 「데이터에 맞춤」(`FIT_TO_DATA_LABEL` · `zoom.fitToData` = 배율 1) 감싸개 `.pv-fit`. Fragment 반환. 마우스 · 판별 불가는 종전 마크업 그대로. 확대 가능한 지도 3곳(상세 · 업로드 인라인 · 확장보기)이 이 부품을 같이 써서 `PreviewPanel.tsx` 변경 0 |
| `frontend/src/components/preview/preview.css` | 640px 블록의 `.pv-control select { font-size: 16px; }` 삭제(부록 G) · 파일 끝(기존 블록 뒤)에 `.pv-overlay .pv-fit`(누름 받기 · 면 · 테두리 · 모서리 · 그림자 0) · `.pv-fit button` · `.pv-frame-below:empty { display: none }` · `.pv-below`(세로 · `gap: var(--space-2)`) · `.pv-below > *`(margin 0) · `.pv-map + .pv-below`(미등록 여백 토큰 한 칸) · 아래 블록 면 규칙 · 아래 블록 범위 긴 이름 줄바꿈 · `.dt-preview > .pv-muted` 줄바꿈(`preview-target-file`) · `@media (pointer: coarse)` 한 블록(부록 B 23 · 29 · 30 ＋ 맞춤 단추 · 최소 높이 · 가로 `var(--control-height)`) |
| `frontend/src/components/detail/detail.css` | 끝(기존 블록 뒤)에 `.detail-page .dh-file { overflow-wrap: anywhere; }` 1규칙(「레인 확정」 허용) |
| `frontend/test/helpers/mapCellWidth.ts`(새) | 지도 칸 폭 시험 도우미(가짜 `ResizeObserver` · `section.pv-map` 관찰에만 폭 알림 · 콜백 횟수 · `vi.unstubAllGlobals` 되돌리기) ＋ 입력 방식 스텁(`matchMedia` 질의 기록) |
| `frontend/test/device-width-input-20260926-L1.test.tsx`(새) | L1a 27사례(아래 §2) |

`UnregisteredPreviewPage.tsx` · `PreviewPanel.tsx` · 셸 · 기본 · 프리미티브 CSS · 다른 화면 CSS(허용된 `dh-file` 1규칙 밖) 변경 0. 기존 시험 파일 변경 0.

## 2. 시험 RED → GREEN

- 새 시험 27사례: 810 상수(spec 줄 1개 = 810 = 코드 상수) · 도우미 폭 목록 길이 5 먼저 · 상세 폭 5종(332 · 730 · 809 아래 · 810 · 1190 위 · 마우스 판별) · 폭 0 = 지금 배치 · 도우미가 지도 구역 밖 관찰에는 알리지 않음 · 아래 블록 안 누름 · 포인터 누름 · 끌기 · 마우스 이동 → 조회 0 · 배율 불변 · 좌표 표시 불변 · 좁은 배치 그림 누름 조회 1회 · 1190 → 332 → 1190 값 결과 유지 · 값 조회 알림 영역 1개 · 「범례」 한 곳 · 미등록 332(지도 구역 바로 뒤 형제 · 좌표 → 범례 · 도구 층 모서리 0) · 미등록 1190 · 상세 332 터치(도구 층 = 맞춤 단추 ＋ 확대 줄 · 3단추 줄 밖 같은 모서리 · 확대 2 → 맞춤 1) · 업로드 인라인 · 확장보기 터치(맞춤 → 배율 1) · 마우스 판별 · 매체 질의 없음 · 미등록 터치 = 맞춤 단추 없음 · TSX 입력 매체 문자열 = 훅 1곳 · CSS 7(맞춤 감싸개 · 아래 블록 · 긴 이름 범위 · 빈 아래 자리 · 터치 44(대상 목록 레인 L1 = 3 먼저) · 16px 하한 삭제 · 넘침 2곳).
- 모든 폭 도우미 사례는 가짜 `ResizeObserver` 콜백 ≥ 1회를 단언하고, 입력 방식 사례는 `(pointer: coarse)` 질의가 불렸음을 단언한다.
- RED(시험 · 도우미만 · 구현 0): `Tests  23 failed | 4 passed (27)` — 예: `Cannot find module '/src/components/preview/useMapCellWidth'` · 폭 도우미 사례 `expected 0 to be greater than or equal to 1`(훅 없음 → 콜백 0) · `인라인 도구 층에 맞춤 단추가 없다: expected undefined to be truthy` · `expected [] to include '(pointer: coarse)'` · CSS `expected [] to have a length of 1 but got +0` · 16 하한 `expected '\n  .pv-control select { font-size: 1…' not to match /font-size:\s*16px/`. 처음부터 통과한 4사례는 음성 · 회귀 감시다(도우미 폭 목록 길이 · 도우미가 다른 대상에 알리지 않음 · 매체 질의 없음 = 맞춤 단추 없음 · 미등록 터치 = 맞춤 단추 없음).
- GREEN: `Tests  27 passed (27)`. 추가 단언 1건(미등록 지도 구역 ↔ 아래 블록 여백 토큰 — 390 캡처에서 좌표 표시가 지도에 붙은 것을 보고 더함): RED `1 failed | 26 passed (27)` → GREEN `27 passed (27)`(기존 사례 안 단언 추가).
- GREEN 단계에서 고친 이 레인 새 시험 3곳(기존 시험 아님): ⑴ 상세 자리 단언을 「아래 블록의 부모 = 틀 묶음」에서 「아래 블록 → 아래 자리(`.pv-frame-below`) → 틀 묶음 · 아래 자리 앞 = 틀」로(spec 용어의 아래 자리 · 아래 블록 구분) ⑵ 확대 누름 전에 뷰포트 상자 · 원본 해상도를 심는 준비(#120 시험과 같은 방식 · 재기 전에는 확대가 눌리지 않음) ⑶ 터치 44 선택자 비교를 평문 목록 대조로 단순화.
- 전체: `frontend-test` 148파일 1999건 통과(B0 끝 1972 ＋ 27). #120 고정 시험(`preview-map-viewport-20260918.test.tsx`) · 세로로 긴 그림 기본 배율 터치 이동 시험(`design-fix-20260924-L3b.test.tsx`) · 틀 · 배치 시험(`preview-layout-20260912` · `preview-slot-4x3`) 수정 없이 green. 기존 시험 단언 삭제 0.

## 3. RED 확인 목록(시험 결정 「L1 시험 작성 단계(RED) 확인 목록」)

- 명령: spec 이 적은 저장소 검색 명령(`-i -e 'touch-action' -e 'touchAction' -- frontend/test gates`).
- 시험 작성 전(`351a1962`): 3건 — `frontend/test/device-width-input-20260926-L0b.test.ts:264`(판정 픽스처의 수치 값 `touchAction: 'none'`) · `:599` · `:601`(측정 스크립트가 `touchAction` 키를 낸다는 단언). 셋 다 판정 · 측정 도구의 시험이고 `preview.css` 의 `.pv-viewport` `touch-action` 원문을 고정하지 않는다. L1a 는 `touch-action` 을 바꾸지 않았다(L1b 몫) — 세 적중 모두 수정 없이 green.
- 구현 뒤: 위 3건 ＋ 이 레인 새 시험 머리 주석 1줄(`device-width-input-20260926-L1.test.tsx:9` · 「L1b 몫(끌기 축 `touch-action` …)은 이 파일에 아직 없다」 · 단언 아님).
- `.pv-viewport {` 블록을 읽는 기존 시험(`preview-map-viewport-20260918.test.tsx` ⑺ `position: relative`)은 green 그대로.
- 원문 CSS 첫 일치 위험: 새 규칙은 모두 `preview.css` · `detail.css` 끝(기존 블록 뒤)에 있다. 기존 시험이 잘라 읽는 `.pv-map {` · `.pv-zoom {` · `.pv-overlay {` · `.pv-overlay .pv-zoom,` · `.pv-frame {` · `.pv-frame-wrap {` · `.pv-frame .pv-mapcol {` 는 첫 일치가 종전 블록 그대로다.

## 4. 게이트(task 실행 · 호스트 단독)

- 명령: `COLAB_TEST_ENV_FILE=~/.colab-v2-test-32.env COLAB_VISUAL_URLS=<6건> COLAB_TASK_ID=49e2db6a19bb46f6b2fadf634a65c872 bash gates/run.sh task`
- `COLAB_VISUAL_URLS` = 이 레인이 띄운 audit 빌드(`vite preview --config audit.vite.config.ts --host 127.0.0.1 --port 47413 --strictPort` · 시작 때 PID 기록 · 그 PID 만 종료)의 `audit-design.html?scene=<장면>&design=full` 6건(`detail` · `preview` · `preview-done` · `detail-preview-map` · `detail-preview-map-value` · `upload-preview-expand`). `COLAB_VISUAL_EXEMPT` 미사용.

| 게이트 | 결과(1회차 · `f39b4301`) |
|---|---|
| `frontend-typecheck` | green — 오류 0 |
| `frontend-test` | green — 148파일 1999건 통과 · 실패 0 |
| `frontend-fixture-reach` | green — 도달 211(진입점 제외 210) · 금지 모듈 0 |
| `frontend-design-lint` | green — 파일 21 · a–h 0 · 문서 표 갈림 0 |
| `frontend-visual` | green — 페이지 6 · 13px 미만 0 · 대비 < 4.5 0 · 스크린샷 12 |
| 계 | **green 5 / red(판정) 0 / red(준비) 0** |

- `tsc --noEmit -p tsconfig.audit.json`(게이트 밖 · audit 진입점) 오류 0.
- 이 보고서 커밋 뒤 같은 명령으로 한 번 더 돌려 인계한다(최종 gate-summary 경로와 3계수는 인계 메시지).

## 5. 수치(L0b 도구 · 직렬 실행 · 최종 트리 `f39b4301` · audit 빌드는 첫 390 실행이 다시 빌드)

### 5-1. 390 터치 수치 전용 · 레인 L1 판정

- 실행: `capture.py --label dwi0926-l1a-f390 --metrics-only --scene <장면> --viewport 390`(6장면 × 2테마 · 12 파일 · 모두 종료 0) → `judge.mjs --lane L1` → **종료 0**.
- 요약줄: `files=12 lane=L1 red=0 readiness=0 notMeasured=20 captureBlind=0 exemptHits=0 smallOther=2 outsideRed=16:0,44:78,넘침:0,가림:0 exit=0`.

| 장면(라이트 · 다크 같음) | 레인 L1 대상 누름 칸(가로x세로) | 16 미만 | 넘침 루트 | 지도 칸 | 네 도구 가림 % | 확대 묶음 % (기록) | 값 패널 |
|---|---|---|---|---|---|---|---|
| `detail` | 29: 358x44 | 0 | 0 | — | — | — | — |
| `preview` | 23: 94.9x44 | 0 | 0 | — | — | — | — |
| `preview-done` | 23: 94.9x44 | 0 | 0 | 358 | **0** | 0 | — |
| `detail-preview-map` | 29: 358x44 · 30: 44.5x44 ×2 · 81.5x44 · 67x44 | 0 | 0 | 332 | **0** | 26.4 | 안내 |
| `detail-preview-map-value` | 같음 | 0 | 0 | 332 | **0** | 26.4 | **값** |
| `upload-preview-expand` | 29: 356x44 · 290.1x44 · 30: 44.5x44 ×4 · 81.5x44 ×2 | 0 | 0 | —(기록만) | 0 | 10.5 | — |

- B0 대비(같은 390): 네 도구 가림 `detail-preview-map` 100 → 0 · `detail-preview-map-value` 84 → 0 · `preview-done` 14.7 → 0. 넘침 루트(`dh-file` · `preview-target-file`) 4 → 0. 레인 L1 44 red(23 · 29 · 30) → 0.
- 16: 부록 G 미리보기 하한을 지운 뒤에도 390 16 미만 0 — 셸 640px 규칙이 유지한다(멈춤 조건 해당 없음).
- 레인 밖 red 는 개수만: 44 78건(뒤 레인 대상 · 맨 위 메뉴 등) · 목록 밖 작은 누름 칸 2.

### 5-2. 820 · 507 가림(수치 전용 · 가림만 판정)

- 실행: `--metrics-only --scene <detail-preview-map · detail-preview-map-value · preview-done> --viewport <820 · 507x820>`(12 파일 · `dwi0926-l1a-fmid` · 모두 종료 0) → `judge.mjs --lane L1` 종료 1 — red 28 은 전부 820 의 16(아래 개수) · 가림 red 0 · 넘침 0.

| 장면 | 820 지도 칸 · 네 도구 % | 507x820 지도 칸 · 네 도구 % | 확대 묶음 % 820 · 507(기록) |
|---|---|---|---|
| `detail-preview-map` | 730 · **0**(B0 14.2) | 449 · **0**(B0 56.4) | 1.7 · 11.3 |
| `detail-preview-map-value` | 730 · **0**(B0 19.2) | 449 · **0**(B0 61.3) | 1.7 · 11.3 |
| `preview-done` | 756 · **0**(B0 14.7) | 475 · **0**(B0 미측정) | 0 · 0 |

- 개수만(「레인 확정」 · 16 은 L2a 가 모음): 16 미만 820 28건(맨 위 메뉴 테마 선택 6 · 상세 미리보기 팔레트 · 구간 수 선택 8 · 파일 · 변수 · 시각 고르개 12 · 미등록 구간 수 2) · 507x820 0건. 44 레인 L1 red 0 · 레인 밖 44 108건.
- 값 결과 장면 `map.valueState`: 820 · 507x820 모두 값.
- 참고(전 크기 캡처 `dwi0926-l1a-fcap` 수치): 844x390 네 도구 가림 `detail-preview-map` 0 · `-value` 0 · `preview-done` 0(칸 754 · 754 · 780). 상세 1024 · 1180 은 지도 위 배치 그대로 6.7 · 4.1 / 8.8 · 5.1(V3 기대 12% 이하 · B0 와 같음). `preview-done` 1024 · 1180 · 1440 은 14.7(칸 ≥ 810 · 기록만).

### 5-3. `detail-preview-map-value` 390 `map.valueState`

| 뷰포트 | 라이트 | 다크 | B0 |
|---|---|---|---|
| 390 | **값** | **값** | 안내 |

- 390 에서 지도 중심 누름이 조회에 닿는다(캡처의 값 패널 「셀값 0.0412」 확인). 확대 묶음 모서리의 맞춤 단추를 확대 줄 **앞**(위쪽)에 두어 확대 줄이 지도 가운데 높이까지 올라가지 않는다 — 390 에서 확대 줄 상자 y 774.3–832.3 · 맞춤 단추 x 238.3–349 · 지도 중심 (195, 723).

### 5-4. 1440 마우스 캡처 대 B0 `dwi0926-base`

- 캡처: `capture.py --label dwi0926-l1a-fcap --skip-build --parallel 2 --metrics --only <6장면>` 종료 0 · 72장.
- 대조: `diff.mjs --subset --viewport 1440 <B0 dwi0926-base> dwi0926-l1a-fcap dwi0926-l1a-fdiff-1440` → **종료 0 · 12장 · red 0 · 엄격 픽셀 0**.
- B0 폴더: 워크트리 `agent-abf926c2ed31f5520` 의 `frontend/.visual/dwi0926-base`(읽기만).

## 6. 이탈 · 결정 · 남은 것

- 원한 결과 대조(intent (b) · spec V2 · V4(구조) · V6 · V7 · V8 미리보기 · V11 맞춤 단추):
  - 충족: 지도 칸 810 미만에서 네 도구가 지도 아래 · 지도 위는 확대 묶음(＋터치 맞춤 단추)만(intent 끝 줄 5) · 390 · 844x390 · 820 · 507x820 네 도구 가림 0 · 390 탭 조회 도달(캡처 값) · 마우스 좁은 창도 아래 배치(V6 · vitest 730) · 넓은 마우스 창 1440 픽셀 변화 0 · 레인 L1 44 대상 390 red 0 · 미리보기 16 하한 삭제 뒤 390 16 red 0 · 새 지도 장면 넘침 0.
  - 미달(이 레인 몫 아님): intent (c) 한 손가락 끌기(V5) · V11 터치 탭 좌표 · V12 지도 문구 = L1b. V7 · V8 의 820 이상 터치 크기 16 은 L2a · E.
  - 초과: 미등록 지도 구역 ↔ 아래 블록 여백 규칙 1개 · `.dt-preview > .pv-muted` 줄바꿈이 원천 격자 줄에도 걸림(같은 넘침 자리 · 1440 픽셀 변화 0).

- 레인 결정(spec 빈칸 · 근거로 닫음):
  - 아래 자리 「쓰일 때만 그린다」: 요소는 늘 두고 비어 있으면 `.pv-frame-below:empty { display: none }` 으로 그리지 않는다. portal 대상 요소가 먼저 있어야 해서다. 비어 있을 때 틀 묶음 gap 8px 이 생기지 않고, 1440 픽셀 차이 0 으로 확인.
  - 맞춤 단추를 확대 줄 앞(모서리 위쪽)에 둔다: 390 에서 뒤에 두면 확대 줄이 지도 중심 높이(y 708–766)를 덮어 V4 캡처의 중심 누름이 「확대」로 간다(B0 와 같은 실패). 앞에 두면 중심은 맞춤 단추 가로 범위 밖이다.
  - 미등록 지도 구역과 아래 블록 사이 `margin-top: var(--space-2)`(블록 자신의 바깥 여백 · 자식 여백은 0): 상세는 틀 묶음 gap 이 같은 8px 을 준다.
  - 아래 블록은 `align-items: flex-start`(각 부품이 내용 폭 · 칸 폭 상한) · 스크린샷에도 도구 층과 같은 면 규칙.
  - 긴 파일 경로 넘침 `preview-target-file` 은 `.dt-preview > .pv-muted`(같은 자리의 원천 격자 줄도 포함)로 건다 — `.dt-preview` 에는 다른 CSS 규칙이 없고 `DatasetPreviewSection.tsx` 는 L1 파일 목록 밖이라 TSX 에 클래스를 더하지 않았다.
  - 입력 방식 훅 자리: `frontend/src/components/common/useInputMode.ts`(공용 · L3a · L3b 가 이어 씀).
- 우려 6 ⓐ(기록): 지도 칸이 810 을 넘나들면 도구가 도구 층과 아래 블록 사이를 옮겨 다시 만들어진다 — 스크린샷 오류 문장이 사라질 수 있다. 값 결과는 남는다(시험 1190 → 332 → 1190).
- 이 레인 밖(L1b): 끌기 축 `touch-action`(V5) · 터치 탭 좌표 · 터치 좌표 문구(V12 지도). 모든 지도 캡처의 계산된 `touch-action` 은 여전히 `none`.
- 후속:
  - 820 터치의 16 미만 28건(미리보기 · 상세 고르개 · 맨 위 메뉴)은 레인 게이트(390)에 걸리지 않는다 — L2a(「640px 이하 또는 터치 기기」 한 곳) 뒤 E 의 거르기 없는 판정에서 드러난다.
  - 390 확대 묶음 가림 20.5 → 26.4(맞춤 단추 더함 · 기록만 · 우려 4 ⓐ 의 「조금 더해짐」).
- 캡처 폴더(추적 제외 · `frontend/.visual/`): 중간 트리 `6c8d460a` — `dwi0926-l1a-390` · `dwi0926-l1a-mid` · `dwi0926-l1a-cap` · `dwi0926-l1a-diff-1440`(같은 결과) / 최종 트리 — `dwi0926-l1a-f390` · `dwi0926-l1a-fmid` · `dwi0926-l1a-fcap` · `dwi0926-l1a-fdiff-1440`. 수치 판정 JSON 은 각 폴더 `judge-L1.json`.
- agent-browser: 캡처 도구가 만든 실행별 세션(`vb-…`)과 게이트 판정부 세션만 쓰였고 각 도구가 닫았다. 직접 연 세션 0 · `pkill` · `close --all` 0. 미리보기 서버는 시작 때 기록한 PID 하나만 종료.
