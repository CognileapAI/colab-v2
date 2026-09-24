# design-fix 20260924 — L3 미리보기 제스처 (#3 → #5)

- spec: `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` §1 #3 · #5 · §3 L3 · §4 L3 · §5 L3 · 확정 값 4 · 5 · 6
- intent: `dev-package/intent/2026-09-25-design-fix-20260924.md`
- 기준 HEAD: `e8fc4e13` (브랜치 `worktree-design-review-apple-20260924`) · 레인 브랜치 `worktree-agent-a6e847b2be938daef`
- lifecycle task: `352411c5f72c489398365b8bc347ebb4` · 선언 게이트 `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `frontend-design-lint` · `frontend-visual`
- 준비: `frontend/` `npm ci` exit 0

## 진행 상태

| 단계 | 상태 | 커밋 |
|---|---|---|
| L3a 시험 작성(RED) | 완료 — 새 시험 14건 중 13 RED · 기존 5파일 9곳 이관 중 5건 RED(포인터 미처리) | `b6d69bd3` |
| L3a 구현(GREEN) | 완료 — 전체 131파일 1627건 통과 · tsc 0 | `d8a1d407` |
| L3b 시험 작성(RED) | 완료 — 새 시험 15건 · 모듈 부재로 파일 RED · 임시 스텁 대조 9 RED | `4f137bbb` |
| L3b 구현(GREEN) | 완료 — 전체 132파일 1642건 통과 · tsc 0 · L3 관련 7파일 3회 반복 104/104 | `e691d4e1` |
| 레인 게이트 | 완료 — green 5 / red(판정) 0 / red(준비) 0 | 측정 대상 `e691d4e1` |

## vitest 건수

| 시점 | 파일 | 시험 | 결과 |
|---|---|---|---|
| 기준(e8fc4e13) | 130 | 1613 | 전부 통과 |
| L3a GREEN | 131 | 1627 | 전부 통과(＋14 = 새 시험) |
| L3b GREEN | 132 | 1642 | 전부 통과(＋15 = 새 시험) |

## RED 기록

- L3a: `npx vitest run` 6파일 → `Tests 18 failed | 71 passed (89)`. 대표 줄 `AssertionError: expected "vi.fn()" to be called with arguments: [ 1 ]` · `expected -544 to be close to -1088`(이관 파일 · 훅이 pointerdown 을 받지 않음) · `expected "vi.fn()" to be called +0 times, but got 1 times`(끌기 뒤 click 조회).
- RED 가 아닌 새 시험 1건: 「주 단추가 아니면 끌기를 시작하지 않는다」(현행도 pointerdown 을 무시하므로 통과 — 구현 뒤 회귀 방지용). 이관 파일 중 `dataset-preview-zoom-latency` 3건 · `preview-map-viewport` 466 이관분은 현행에서도 통과(변환 문자열 존재 · 불변만 단언).

- L3b: `design-fix-20260924-L3b.test.tsx` → `Error: Failed to resolve import "../src/components/preview/spring"`(파일 전체 RED). 동작 RED 이유를 따로 보려고 커밋하지 않는 임시 `spring.ts`(시작값 그대로 반환)를 두고 다시 돌림 → `Tests 9 failed | 6 passed (15)` · 대표 줄 `expected -531 to be greater than -531`(놓은 뒤 이어지지 않음) · `expected 1000 to be less than 0.5`(스프링 미수렴). 임시 파일은 곧바로 지웠다. 스텁으로도 통과한 6건(상수 · t=0 · 넘지 않음 · 렌더 재요청 0 · 멈춤 뒤 관성 0 · 동작 줄이기)은 구현 뒤 회귀 방지용.
- L3b 를 별도 파일로 둔 까닭: spec §3 은 `-L3.test.tsx` 1파일을 적었지만, 없는 모듈 import 가 #3 단언 전부를 가리므로 레인 지시문의 `design-fix-20260924-L3*.test.ts(x)` 범위 안에서 `-L3b.test.tsx` 로 나눴다.

## before → after

| # | before | after | 근거 |
|---|---|---|---|
| 3 | `onMouseDown` ＋ 창 `mousemove`/`mouseup` · 1px 부터 끌기 · 마우스 전용 · 끌기 뒤 click 이 값 조회를 부름 | `onPointerDown` ＋ 창 `pointermove`/`pointerup`/`pointercancel`(pointerId 대조) · `setPointerCapture?.()` · 임계 10px 초과 전 불변 · 넘는 순간 누른 자리 기준 1:1 · 끌기 성립 뒤 click 1회를 뷰포트 캡처 단계에서 멈춤(도구 층 click 제외) | `frontend/src/components/preview/useZoomPan.ts` `DRAG_THRESHOLD` · `onPointerDown` · `swallow` · 호출부 `PreviewPanels.tsx:314` · `upload/PreviewPanel.tsx:619` · `:780` · `PreviewOverlay.tsx:51` |
| 5 | 놓으면 그 자리에 딱 멈춤 | 놓을 때 속도 = 마지막 100ms 이동 기록(누른 자리 포함 · 놓은 자리 포함)의 평균(px/s) → 목표 = 현재 편차 ＋ (v/1000)·0.998/(1−0.998) 를 `clampView` 로 자른 자리 → 임계 감쇠 스프링(ω = 2π/0.4 · X·Y 따로)이 놓은 속도를 이어받아 rAF 로 간다 · 매 프레임 `clampView` · 0.5px 안이면 목표로 맞추고 끝 · 새 누르기 · 휠 · 확대/축소/기본 배율로 · 더블클릭이 그 프레임에서 끊음 · `prefers-reduced-motion: reduce` 면 관성 없음 · 언마운트 시 프레임 취소 | 신설 `frontend/src/components/preview/spring.ts`(상수 4 ＋ `projectedDistance` ＋ `spring`) · `useZoomPan.ts` `stopInertia` · `samples` · `up()` |

- GREEN 도중 발견·수정: 첫 구현은 끌기 뒤 남은 「click 버림」 표지가 다음 도구 층 click(「기본 배율로」)까지 삼켰다 — 이관 시험 `preview-map-viewport-20260918` 「기본 배율로가 넘치는 축도 중앙으로 되돌린다」가 red 로 잡았다. 도구 층(`.pv-overlay`) 안의 click 은 표지를 건드리지 않게 고쳤다(휠 핸들러의 같은 target 검사와 같은 규칙).

## 수용 기준 대조 (spec §4 L3)

| 단언 | 결과 | 시험 |
|---|---|---|
| #3 pointerDown(1 · 300,300 · 0) → 305 불변 → 311 에서 누른 자리 기준 11px · 상세 · 업로드 | 충족 | `design-fix-20260924-L3.test.tsx` 「#3 포인터 끌기」 6건 |
| `setPointerCapture(1)` 호출(시험이 스텁) · 없는 환경에서 끌기 성립(optional-call · F5) | 충족 | 같은 파일 6건 ＋ 「캡처가 없는 환경」 ＋ 원문 `setPointerCapture?.(` |
| pointerType touch · pen 같다 | 충족 | mouse · touch · pen × 두 화면 |
| 끌기 성립 뒤 click 은 값 조회 0 · 임계 안 click 은 조회 1 | 충족 | 「#3 끌기 뒤 click 버림」 |
| `useZoomPan.ts` 와 호출부에 `onMouseDown` 0 | 충족(4파일 · 도구 층 포함) | 「#3 공개 인터페이스」 4건 |
| 도구 층 위 pointerDown 이 뷰포트로 새지 않는다 | 충족 | `preview-map-viewport-20260918.test.tsx` 466 이관분 |
| 기존 5파일 단언 값 불변 · 스텁 없이 green | 충족 — 이벤트 이름 27줄만 교체(9곳 × 3) · 시험 이름 1곳 `mousedown` → `pointerdown` | 5파일 |
| 감시 `prd39-rev2-build-20260906.test.tsx:497,512` · `prd34-close-copy-20260907.test.tsx:352` 수정 없이 green | 충족 | 전체 실행 |
| #5 스프링: t=0 위치·속도 · 넘지 않음 · 3×response 안 0.5px | 충족 | `design-fix-20260924-L3b.test.tsx` 「spring()」 4건 |
| #5 끌기 → 놓기 → 같은 방향으로 이어져 `clampView(투영 목표)` 에 섬 | 충족 — 범위 안 목표(상세) · 범위 끝에서 자름(업로드) | 「놓은 뒤 관성」 |
| 관성 중 pointerDown → 그 프레임 값에서 멈춤 · 휠 · 확대 · 축소 · 기본 배율로 · 더블클릭 멈춤 | 충족 | 「관성 중단」 6건 |
| reduced-motion 참이면 관성 0 | 충족 | 「동작 줄이기」 |
| 끌기 중 · 관성 뒤 렌더 재요청 0 | 충족 | `dataset-preview-zoom-latency` ＋ L3b 「렌더를 다시 걸지 않는다」 |
| (값 5 = 대안) `package.json` 의존성 | 해당 없음 — 값 5 = 직접 구현 · 의존성 증감 0 | — |

## 게이트 3계수

- 호출: `COLAB_TASK_ID=352411c5f72c489398365b8bc347ebb4 COLAB_VISUAL_URLS="http://127.0.0.1:4187/audit-design.html?design=full&scene=preview http://127.0.0.1:4187/audit-design.html?design=full&scene=detail" bash gates/run.sh task`(선언 5게이트 · 한 run · 순차 · 호스트 뮤텍스). audit 빌드 = 이 레인 트리 `npm run audit:build` → `audit:preview` 4187(다른 레인이 4187 을 쓰는 동안 기다렸다가 띄움 · 게이트 뒤 종료).
- run `10aea2ef38fd42d3a5144b6b5065462e`(측정 커밋 `e691d4e1`): **green 5 / red(판정) 0 / red(준비) 0**.
  - `frontend-typecheck` green(tsc 오류 0) · `frontend-test` green(132파일 1642건) · `frontend-fixture-reach` green(도달 208 · 금지 모듈 0) · `frontend-design-lint` green(g=0 · 인라인 변수 대입 7 — 기존 수) · `frontend-visual` green(페이지 2 · 13px 미만 0 · 대비<4.5 0 · 스크린샷 4 · 근거 `/tmp/frontend-visual-nsG65O/frontend-visual` · 커밋 안 됨).
- 증거 경로: Git common `colab-harness/88de758c9a42632bdfc3970d1e651d3e/352411c5f72c489398365b8bc347ebb4/<run>/gate-summary.json`. 이 보고서를 커밋한 뒤 같은 호출로 한 번 더 돌린 run 이 최종 증거이고, 그 run_id 는 레인 최종 메시지의 `COLAB_HANDOFF` 줄에 있다(보고서 수정이 파일 hash 를 바꾸기 때문).
- `frontend-visual` 은 audit 픽스처 장면(preview · detail) 이며 라이트 기준이다. 다크 URL 은 따로 선언하지 않았다.

## 하지 않은 것

- 실화면 증거(agent-browser · drag 6px/20px · 빠른 끌기 연속 스크린샷 · 터치 에뮬레이션) — spec §4 에 따라 통합 단계 몫(advisor ① F3). 레인은 vitest ＋ 게이트만.
- 캡처 대조(`visual:capture` 레인 라벨 · `fix0924-base` 대 diff) — 돌리지 않았다. L3 는 CSS 무변이라 정지 화면 차이를 예상하지 않지만 확인하지 않은 상태다.
- production build(`frontend/` build) — 값 5 = 직접 구현이라 L3 필수 아님(§5 표). 돌리지 않았다(audit:build 는 exit 0).
- `COLAB_FIX_LANE=1` 은 훅 프로세스 환경에 넣을 수 없었다(세션 시작 때 고정). 대신 구현 커밋 2개(`d8a1d407` · `e691d4e1`)가 `frontend/test/**` 를 건드리지 않았음을 커밋 파일 목록으로 확인할 수 있다.
- 타일 갈래에서 관성 프레임마다 보이는 조각이 바뀌는 것(조각 이미지 요청)은 끌기 중과 같은 경로이며 따로 재지 않았다. spec §7 위험 4 의 「렌더 재요청」은 0 으로 쟀다.

## 부수 변화

- 공개 인터페이스 `ZoomPan.onMouseDown` 삭제 → `onPointerDown`(인자에 `pointerId` · `currentTarget` 추가). 호출부는 상세 · 업로드 인라인 · 업로드 확장보기 3곳 ＋ 도구 층 `stop`.
- 오른쪽 · 가운데 단추 누름은 종전처럼 끌기를 시작하지 않는다(시험 추가).
- 끌기 뒤 click 버림은 뷰포트 노드의 캡처 단계 네이티브 리스너 한 곳에 있다. 도구 층(`.pv-overlay`) 안 click 은 제외(첫 구현이 「기본 배율로」 click 을 삼킨 것을 이관 시험이 잡음).
- 놓을 때 속도는 누른 자리 · 임계 전 이동 · 놓은 자리를 모두 이동 기록으로 센다(마지막 100ms 창). 놓기 전 100ms 이상 멈춰 있었으면 속도 0 → 관성 없음.
- 기존 끌기 시험(실시간 rAF)에서도 놓은 뒤 관성이 돈다. 단언은 모두 놓은 직후 동기라 값이 바뀌지 않고, 언마운트 때 프레임을 취소한다. act 경고 0건.
- 새 파일: `frontend/src/components/preview/spring.ts`(38줄 · 의존성 0) · 시험 2파일(`-L3.test.tsx` 14건 · `-L3b.test.tsx` 15건).
