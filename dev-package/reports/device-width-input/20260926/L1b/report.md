# 레인 보고 — L1b 끌기 축 · 터치 탭 좌표 · 터치 좌표 문구

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` 「레인 확정」 L1b 줄 · V5 · V11 · V12 · 구현 결정 끌기 축 표 · 「좌표 표시(미리보기 지도 부품)」 · 시험 결정 「L1 시험 작성 단계(RED) 확인 목록」 · 우려 7ⓐ · 「새 문구안」 「커서를 지도 위로」 행
- intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 브랜치: `claude/dwi-l1b` · 기준 `6ba304b1`(통합 브랜치 `claude/device-width-input-impl` 머리 · L1a 포함) · 구현 커밋 `d900c096`
- task: `b2eafcecd1ea4eb59a7cdf8570c246e9`(게이트 `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint` · `frontend-visual` · 범위 선언 없음)
- 판정: **L1b 완료.** 시험 RED 18 실패 / 32 통과 → GREEN 50 통과 · 전체 148파일 2022건 통과 · 게이트 green 5 / red(판정) 0 / red(준비) 0 · 390 레인 L1 판정 red 0 · 1440 대 B0 픽셀 차이 0 · 브라우저 확대 뒤 `touch-action` `none` · 끌기 축 `both`.

## 1. 바뀐 것

| 파일 | 변경 |
|---|---|
| `frontend/src/components/preview/useZoomPan.ts` | 끌기 축 `dragAxis`(`none` · `x` · `y` · `both`)를 낸다. 배율 > 기본 배율(`atLimit` 과 같은 비교 · 「데이터에 맞춤」이 확대일 때 포함)이면 `both`. 기본 배율에서는 이동 범위 반폭(`clampView` 와 같은 계산 · 새 함수 `panHalf` 를 둘이 같이 씀)이 0 보다 큰 축만. 상자를 못 재면 `none`. 포인터 처리(임계 · 두 번째 포인터 · 취소 경로) 변경 0 |
| `frontend/src/components/preview/PreviewPanels.tsx` | 상세 뷰포트에 `data-drag-axis`(확대 가능할 때만). 입력 방식 훅이 터치이면 좌표 표시 대기 문구 = 새 상수 `HUD_IDLE_TOUCH` 「지도를 누르면 그 자리 좌표를 보여 줘요」(`HUD_IDLE` 바로 뒤 줄). 터치에서 지도 click 이 그 점의 위도 · 경도를 좌표 표시에 낸다(경계 밖 = 「지도 밖」). 값 조회가 있으면(상세) 조회도 그대로 1회. 뷰포트 click 처리기는 `onPickPoint` 가 있거나 터치일 때 달리고, `data-value-lookup` 은 `onPickPoint` 가 있을 때만. 마우스 이동 · 마우스 나감 경로 변경 0 |
| `frontend/src/components/upload/PreviewPanel.tsx` | 업로드 인라인 · 확장보기 뷰포트에 `data-drag-axis` 각 1줄 |
| `frontend/src/components/preview/preview.css` | `.pv-viewport {` 기본 블록의 `touch-action: none` → `pan-x pan-y`(페이지 스크롤). 그 블록 바로 뒤에 `[data-drag-axis='none' / 'y' / 'x' / 'both']` → `pan-x pan-y` / `pan-x` / `pan-y` / `none` 4규칙 |
| `frontend/src/components/preview/useMapCellWidth.ts` | 첫 읽기 border-box(`getBoundingClientRect`) · 관찰 content-box(`contentRect`) 같음 전제 주석 1줄(`.pv-map` 에 padding · border 없음 — `preview.css` 의 `.pv-map` 규칙 3개 확인) |
| `frontend/test/device-width-input-20260926-L1.test.tsx` | L1b 23사례 추가 ＋ L1a 사례 안에 모서리 순서 단언 1줄(아래 §2). 머리 주석 1줄 교체(단언 아님) |
| `dev-package/reports/device-width-input/20260926/L1a/report.md` | 세로로 긴 그림 기본 배율 터치 이동 시험 파일 이름 정정 1줄: `design-fix-20260924-L3b.test.tsx` → `design-fix-20260924-L3.test.tsx`(pointerType mouse · touch · pen 끌기 사례가 L3 에 있다 · L3b 는 같은 세로로 긴 내용을 쓰는 관성 시험) |

`UnregisteredPreviewPage.tsx` 변경 0(탭 좌표는 `PreviewMap` 안에서 처리). `useInputMode` 서명 변경 0. `HUD_IDLE` 상수 · 값 변경 0. 기존 시험 파일 변경 0. `scenes.json` 변경 0.

## 2. 시험 RED → GREEN

- 새 사례 23(`device-width-input-20260926-L1.test.tsx` 뒤쪽 「L1b」 절):
  - V5 끌기 축 상세 7: 사례 목록 길이 4 먼저 · 기본 배율 뷰포트 512x512 에 내용 512x512 → `none` · 512x1600 → `y` · 1600x512 → `x` · 1600x1600 → `both` · 「확대」 → `both` · 「기본 배율로」 → `none` · 작은 유역 경계(기본 배율 < 1)에서 터치 「데이터에 맞춤」 → 배율 1 · `both`.
  - V5 적용 자리 2: 업로드 인라인 · 확장보기 세로로 긴 그림 → `y` · 미등록 → 속성 없음.
  - V5 CSS 원문 6: `.pv-viewport {` 첫 블록 = `touch-action: pan-x pan-y` · `none` 없음 · `position: relative` 유지 · 대응표 길이 4 먼저 · 축 4규칙 각각 본문이 정확히 `touch-action: <값>;` 이고 기본 블록 뒤.
  - V11 · 우려 7ⓐ 탭 좌표 4: 상세 터치 — 포인터 누름 · 놓기 ＋ click(마우스 이동 없음) → 좌표 표시 `역산값 · 위도 -5.0000 · 경도 -45.0000` · 값 조회 1회 / 미등록 터치 — 같은 좌표 · `data-value-lookup` 없음 / 미등록 터치 경계 밖 → 「지도 밖」 / 마우스 — click 만으로는 대기 문구 그대로, 마우스 이동에서 좌표.
  - V12 지도 문구 4: 상세 터치 · 미등록 터치 = 새 문구 · 마우스 = `HUD_IDLE` 「커서를 지도 위로」(질의 `(pointer: coarse)` 불림 확인) · 새 상수가 `HUD_IDLE` 바로 뒤(4줄 안)에 이름 붙어 있음.
- L1a 개선: 상세 332 터치 사례의 모서리 자식 순서 `['pv-fit', 'pv-zoom']` 단언 추가(집합 단언은 그대로 둠).
- RED(시험만 · 구현 0 · `6ba304b1` 위): `Tests  18 failed | 32 passed (50)`. 실패 예: 끌기 축 7사례 `waitFor` 5초 초과(속성 없음) · `expected '\n  overflow: hidden;\n  border: 1px …' to match /touch-action:\s*pan-x pan-y;/` · 축 규칙 `expected [] to have a length of 1 but got +0` · `expected '커서를 지도 위로' to be '지도를 누르면 그 자리 좌표를 보여 줘요'` · 「지도 밖」 사례 `expected '커서를 지도 위로' to be '지도 밖'` · 상수 위치 `expected -1 to be greater than 7890`.
- 처음부터 통과한 새 단언(음성 · 회귀 감시 5사례 ＋ 1단언): 사례 목록 길이 2 · 미등록 속성 없음 · 마우스 click 불변 · 마우스 문구 · 모서리 순서(L1a 가 이미 맞춤 단추를 앞에 둠).
- GREEN: `Tests  50 passed (50)`. 전체 `frontend-test` 148파일 2022건 통과(L1a 끝 1999 ＋ 23).
- 수정 없이 green: `design-fix-20260924-L3.test.tsx`(세로로 긴 그림 기본 배율 터치 · 마우스 · 펜 끌기) · `design-fix-20260924-L3b.test.tsx`(관성) · `preview-map-viewport-20260918.test.tsx`(#120 · `.pv-viewport {` 첫 블록 `position: relative`) · `prd39-rev2-build-20260906.test.tsx`(「커서를 지도 위로」) — 4파일 87건.
- 기존 시험 단언 삭제 0. 이 레인 파일의 삭제 줄은 머리 주석 1줄뿐.

## 3. RED 확인 목록(시험 결정 「L1 시험 작성 단계(RED) 확인 목록」)

- 명령: spec 의 저장소 검색 명령(`-n -i -e 'touch-action' -e 'touchAction' -- frontend/test gates`).
- 시험 작성 전(`6ba304b1`): 4건 — `device-width-input-20260926-L0b.test.ts:264`(판정 픽스처 수치 값 `touchAction: 'none'`) · `:599` · `:601`(측정 스크립트가 `touchAction` 키를 낸다는 단언) · `device-width-input-20260926-L1.test.tsx:9`(L1a 머리 주석 · 단언 아님). 넷 다 `preview.css` 의 `.pv-viewport` 원문을 고정하지 않는다 — 변경 뒤 수정 없이 green(L0b 시험 포함 전체 green).
- 구현 뒤: L0b 3건 그대로 ＋ 이 레인 새 단언 · 주석(`device-width-input-20260926-L1.test.tsx` V5 CSS 원문 절).
- 원문 CSS 첫 일치: 축 4규칙은 선택자 머리가 `.pv-viewport[data-drag-axis=…]` 라 `.pv-viewport {` 첫 블록 검색에 걸리지 않고, 기본 블록 뒤에 있다.

## 4. 게이트(task 실행 · 호스트 단독)

- 명령: `COLAB_TEST_ENV_FILE=~/.colab-v2-test-32.env COLAB_VISUAL_URLS=<6건> COLAB_TASK_ID=b2eafcecd1ea4eb59a7cdf8570c246e9 bash gates/run.sh task`
- `COLAB_VISUAL_URLS` = 이 레인이 띄운 audit 빌드(`vite preview --config audit.vite.config.ts --host 127.0.0.1 --port 47431 --strictPort` · 시작 때 PID 기록 · 그 PID 만 종료)의 `audit-design.html` 6장면(`detail` · `preview` · `preview-done` · `detail-preview-map` · `detail-preview-map-value` · `upload-preview-expand`). `COLAB_VISUAL_EXEMPT` 미사용.

| 게이트 | 1회차(`d900c096`) |
|---|---|
| `frontend-typecheck` | green — 오류 0 |
| `frontend-test` | green — 2022건 통과 · 실패 0 |
| `frontend-fixture-reach` | green — 도달 211(진입점 제외 210) · 금지 모듈 0 |
| `frontend-design-lint` | green — 파일 21 · a–h 0 · 문서 표 갈림 0 |
| `frontend-visual` | green — 페이지 5 · 13px 미만 0 · 대비 < 4.5 0 · 스크린샷 10 |
| 계 | **green 5 / red(판정) 0 / red(준비) 0** |

- 1회차 URL 은 `?design=full&scene=<장면>` 순서였고, 판정부가 근거 파일 이름을 URL 앞 60자로 자르면서 `detail-preview-map` 과 `detail-preview-map-value` 가 한 이름으로 겹쳐 페이지 5로 셌다(아래 §6 후속). 인계 실행은 L1a 와 같은 `?scene=<장면>&design=full` 순서로 6건을 다시 잰다.
- `tsc --noEmit -p tsconfig.audit.json`(게이트 밖 · audit 진입점) 오류 0.
- 이 보고서 커밋 뒤 같은 명령으로 한 번 더 돌려 인계한다(최종 gate-summary 경로와 3계수는 인계 메시지).

## 5. 수치 · 브라우저 확인(직렬 실행 · 트리 `d900c096`)

### 5-1. 390 터치 수치 전용 · 레인 L1 판정

- 실행: `capture.py --label dwi0926-l1b-390 --metrics-only --scene <장면> --viewport 390`(6장면 × 2테마 · 12파일 · 모두 종료 0 · 첫 실행이 audit 빌드) → `judge.mjs --lane L1` → **종료 0**.
- 요약줄: `files=12 lane=L1 red=0 readiness=0 notMeasured=20 captureBlind=0 exemptHits=0 smallOther=2 outsideRed=16:0,44:78,넘침:0,가림:0 exit=0`(L1a 최종과 같은 값).
- 네 도구 가림 `detail-preview-map` · `-value` · `preview-done` 0 · 확대 묶음(＋맞춤 단추) 26.4 · 26.4 · 0 · `upload-preview-expand` 10.5(기록만) — L1a 와 같음. `detail-preview-map-value` `map.valueState` = 값(라이트 · 다크).

### 5-2. 기본 배율의 계산된 `touch-action` · 끌기 축(수치 파일 `map.touchAction` · `map.dragAxis` · 라이트 · 다크 같음)

| 장면 · 뷰포트 | `touchAction` | `dragAxis` | 종전(L1a) |
|---|---|---|---|
| `detail-preview-map` 390 | `pan-x pan-y` | `none` | `none` · 속성 없음 |
| `detail-preview-map-value` 390 | `pan-x pan-y` | `none` | `none` · 속성 없음 |
| `preview-done`(미등록) 390 | `pan-x pan-y` | 없음(속성 없음) | `none` · 속성 없음 |
| `upload-preview-expand` 390 | `pan-x pan-y` | `none` | `none` · 속성 없음 |
| `upload-preview-expand` 844x390 · 820 · 1024 · 1440 | `pan-x` | `y` | `none` · 속성 없음 |
| `detail-preview-map` · `preview-done` 844x390 · 820 · 1024 · 1440 | `pan-x pan-y` | `none` · 없음 | `none` · 속성 없음 |

- 확장보기 `y` 는 실제 끌 범위다(자기 세션 820 터치 측정: 뷰포트 `clientHeight` 394 · 층 묶음 `offsetHeight` 608 × 기본 배율 0.742 = 451 > 394 → 세로 반폭 약 28px). 반올림 1px 로 생긴 축이 아니다.

### 5-3. 확대 뒤(agent-browser 자기 세션 `l1b-zoomcheck` · 터치 실행 래퍼 · 390x844 · `detail-preview-map` 라이트)

| 상태 | 배율(기본 0.742 · 한계 3.084) | `getComputedStyle(viewport).touchAction` | `dataset.dragAxis` |
|---|---|---|---|
| 그린 직후(기본 배율) | 0.742 | `pan-x pan-y` | `none` |
| 「확대」 | 1.484 | **`none`** | **`both`** |
| 「기본 배율로」 | 0.742 | `pan-x pan-y` | `none` |
| 「데이터에 맞춤」(배율 1 > 기본 배율) | 1 | `none` | `both` |
| 「기본 배율로」 | 0.742 | `pan-x pan-y` | `none` |

- `(pointer: coarse)` 참 · 창 390 · 맞춤 단추 있음 · 좌표 표시 대기 문구 「지도를 누르면 그 자리 좌표를 보여 줘요」.
- 탭 좌표: 같은 세션에서 뷰포트 (가로 1/4 · 세로 1/2) 자리에 `PointerEvent`(`pointerType: 'touch'`) 누름 · 놓기 ＋ `click` 을 보냈다(마우스 이동 없음). 좌표 표시 「역산값 · 위도 35.6303 · 경도 126.9905」 · 값 조회 패널 「고른 자리 위도 35.6303 · 경도 126.9905 · 셀값 0.0412」 — 두 자리의 좌표가 같다(우려 7ⓐ 「상세에서는 좌표가 두 곳에 보임」).
- 이 세션에서 agent-browser `click` 은 그리기 단추 · 지도 모두에 효과가 없었다(뷰포트가 창 밖 y 3288 에 있었음 · 캡처 도구는 같은 동작 전에 가까운 위치로 스크롤한다). 단추와 탭은 페이지 스크립트로 눌렀다. 실제 손가락 끌기 · 탭은 Ted 실기기(spec V5 · V11 확인 방법) 몫이다.
- 세션 `l1b-zoomcheck` · `l1b-expandcheck` 는 각각 자기 이름으로 닫았다. 다른 세션 닫기 · 프로세스 일괄 종료 0.

### 5-4. 1440 마우스 캡처 대 B0 `dwi0926-base`

- 캡처: `capture.py --label dwi0926-l1b-cap --skip-build --parallel 2 --metrics --only <6장면>` 종료 0 · 72장.
- 대조: `diff.mjs --subset --viewport 1440 <B0 dwi0926-base> dwi0926-l1b-cap dwi0926-l1b-diff-1440` → **종료 0 · 12장 · red 0 · 엄격 픽셀 0**.
- B0 폴더: 워크트리 `agent-abf926c2ed31f5520` 의 `frontend/.visual/dwi0926-base`(읽기만).

## 6. 이탈 · 결정 · 남은 것

- 원한 결과 대조(intent (c) · spec V5 · V11 탭 좌표 · V12 지도):
  - 충족: 기본 배율 · 끌 범위 없는 지도는 페이지 스크롤(`pan-x pan-y`) · 끌 범위 있는 축만 지도(확장보기 세로 → `pan-x`) · 확대 · 맞춤 확대 = `none` · 미등록 = 속성 없음 · 기본값 · 세로로 긴 그림 기본 배율 터치 이동 시험 수정 없이 green · 터치 탭 좌표 상세 · 미등록 · 터치 문구 · 마우스 문구와 동작 불변(1440 픽셀 0 · 기존 문구 단언 green).
  - 미달: 실제 손가락 끌기로 페이지가 스크롤되는지 · 지도가 옮겨지는지는 이 레인에서 재지 않았다(jsdom · 합성 이벤트로는 브라우저의 스크롤 넘겨받기를 만들 수 없음) — Ted 실기기(부록 J) 몫.
  - 초과: 없음. `panHalf` 는 `clampView` 의 같은 식을 함수로 뺀 것이다(값 변화 0 · 기존 끌기 시험 green).
- 레인 결정(spec 빈칸 · 근거로 닫음):
  - 기본 배율에서 축 판정 문턱은 반폭 > 0(`clampView` 와 같은 식 그대로). 측정한 장면에서 반올림으로 생긴 축은 없었다(5-2).
  - 상자를 못 잰 순간은 `none`(페이지 스크롤) — 없는 끌 범위를 지어내지 않는다.
  - 터치 탭 좌표는 click 처리기에서 입력 방식 훅이 터치일 때만 낸다. 마우스 click 은 좌표 표시를 바꾸지 않는다(마우스 이동 표시가 맡음 · spec 「마우스 이동 표시는 바뀌지 않는다」).
  - 새 문구 상수 이름 `HUD_IDLE_TOUCH`(마우스 상수 바로 뒤 · spec 「새 터치 문구는 … 마우스 문구 상수 바로 옆」).
- 후속:
  - `frontend-visual` 판정부 `.agents/skills/design-review/scripts/live_audit.sh` 의 근거 파일 이름(`SLUG` · URL 앞 60자)이 앞 60자가 같은 두 URL(`…?design=full&scene=detail-preview-map` · `…-value`)을 한 파일로 겹쳐 페이지 수가 5로 줄어든다. 게이트는 green 을 냈다 — 이 겹침은 어느 검사에도 걸리지 않는다(선언 URL 수와 probe 파일 수를 대조하지 않음). L1b 는 URL 순서를 `?scene=…&design=full` 로 바꿔 피했다.
  - 터치에서 지도 밖을 누른 뒤 브라우저 호환 마우스 이벤트(`mouseleave`)가 좌표 표시를 대기 문구로 되돌릴 수 있다 — 실기기 확인 항목.
- 캡처 폴더(추적 제외 · `frontend/.visual/`): `dwi0926-l1b-390`(수치 · `judge-L1.json`) · `dwi0926-l1b-cap` · `dwi0926-l1b-diff-1440`.
