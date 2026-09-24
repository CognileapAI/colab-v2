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
| L3b 구현(GREEN) | 완료 — 전체 132파일 1642건 통과 · tsc 0 · L3 관련 7파일 3회 반복 104/104 | (이 커밋) |
| 레인 게이트 | 대기 | — |

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

## 수용 기준 대조

(채운다)

## 게이트 3계수

(채운다)

## 하지 않은 것

(채운다)

## 부수 변화

(채운다)
