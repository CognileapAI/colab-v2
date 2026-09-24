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
| L3a 구현(GREEN) | 완료 — 전체 131파일 1627건 통과 · tsc 0 | (이 커밋) |
| L3b 시험 작성(RED) | 대기 | — |
| L3b 구현(GREEN) | 대기 | — |
| 레인 게이트 | 대기 | — |

## vitest 건수

| 시점 | 파일 | 시험 | 결과 |
|---|---|---|---|
| 기준(e8fc4e13) | 130 | 1613 | 전부 통과 |
| L3a GREEN | 131 | 1627 | 전부 통과(＋14 = 새 시험) |

## RED 기록

- L3a: `npx vitest run` 6파일 → `Tests 18 failed | 71 passed (89)`. 대표 줄 `AssertionError: expected "vi.fn()" to be called with arguments: [ 1 ]` · `expected -544 to be close to -1088`(이관 파일 · 훅이 pointerdown 을 받지 않음) · `expected "vi.fn()" to be called +0 times, but got 1 times`(끌기 뒤 click 조회).
- RED 가 아닌 새 시험 1건: 「주 단추가 아니면 끌기를 시작하지 않는다」(현행도 pointerdown 을 무시하므로 통과 — 구현 뒤 회귀 방지용). 이관 파일 중 `dataset-preview-zoom-latency` 3건 · `preview-map-viewport` 466 이관분은 현행에서도 통과(변환 문자열 존재 · 불변만 단언).

## before → after

| # | before | after | 근거 |
|---|---|---|---|
| 3 | `onMouseDown` ＋ 창 `mousemove`/`mouseup` · 1px 부터 끌기 · 마우스 전용 · 끌기 뒤 click 이 값 조회를 부름 | `onPointerDown` ＋ 창 `pointermove`/`pointerup`/`pointercancel`(pointerId 대조) · `setPointerCapture?.()` · 임계 10px 초과 전 불변 · 넘는 순간 누른 자리 기준 1:1 · 끌기 성립 뒤 click 1회를 뷰포트 캡처 단계에서 멈춤(도구 층 click 제외) | `frontend/src/components/preview/useZoomPan.ts` `DRAG_THRESHOLD` · `onPointerDown` · `swallow` · 호출부 `PreviewPanels.tsx:314` · `upload/PreviewPanel.tsx:619` · `:780` · `PreviewOverlay.tsx:51` |

- GREEN 도중 발견·수정: 첫 구현은 끌기 뒤 남은 「click 버림」 표지가 다음 도구 층 click(「기본 배율로」)까지 삼켰다 — 이관 시험 `preview-map-viewport-20260918` 「기본 배율로가 넘치는 축도 중앙으로 되돌린다」가 red 로 잡았다. 도구 층(`.pv-overlay`) 안의 click 은 표지를 건드리지 않게 고쳤다(휠 핸들러의 같은 target 검사와 같은 규칙).

## 수용 기준 대조

(채운다)

## 게이트 3계수

(채운다)

## 하지 않은 것

(채운다)

## 부수 변화

(채운다)
