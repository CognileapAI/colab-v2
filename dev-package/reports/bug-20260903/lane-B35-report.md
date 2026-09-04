# 레인 B35 보고 — 버그 8·14·13 (확대 한계 표시 · 미리보기 이름표 · 원본 격자 표기)

- 브랜치 `worktree-agent-a463e7e75499856cd` · 워크트리 `.claude/worktrees/agent-a463e7e75499856cd`
- 커밋 `a1ea2d5` (버그 8) · 두 번째 커밋 (버그 14·13, 아래 로그 참조). 워크트리 클린.
- 진행: Sonnet 초안 → Fable(메인 세션) 검토·RED/GREEN 재검증·커밋.

## 버그 8 — 확대·축소·기본 배율로 무동작
- 근본 원인(확정): `useZoomPan.ts` `maxScale = PNG 폭 / 뷰포트 폭` 이 실측 808~821 / ≈820 → 1.0. 기존 시험은 `measure(4096, 512)` 픽스처라 못 잡음.
- 수정(Ted 판정 ⓐ): **maxScale 계산 무변경**(정본 조건 ⑷ · 〈232〉 유지). `atLimit` 조건에 `maxScale <= 1` 추가 → 첫 클릭 전에 「원본 해상도까지 봤어요」 안내, 확대 버튼 `disabled`.
- RED: origin/main 소스로 신규 2건 실패 확인. GREEN 후 유지.
- 검토 결과: 최소 수정, 무관 편집 없음.

## 버그 14 — 미리보기 정체불명
- 수정: `DatasetPreviewSection` 머리에 `detail.name` + `fileName`, `PreviewPanels` 범례 첫 줄에 `legend.variable`(서버가 이미 돌려주는 필드, `preview/types.ts:17`). 새 API·계약 없음.
- 범례 변수명은 `legend.variable` 이 비면 자리째 뺀다.

## 버그 13 — 원본 픽셀 크기 표기 (Ted 판정)
- 수정: `basicInfo.grid`(상세가 이미 읽는 값) + ③지도형 사이드카 `mapGeometry` 의 `width×height`(확대 한계가 쓰는 동일 응답) → 「격자 0.05° (~5km) · 126 × 128」 캡션. ②비지도형(이미지 갈래)은 사이드카가 없어 격자 간격만 낸다. 둘 다 없으면 캡션 없음.
- 누락 필드 없음 — 필요한 값이 전부 기존 props/응답에 있었다.

## 증거
- RED(Part 2·3, 소스 되돌림): 5 failed / 16 passed — 정확히 신규 5건.
- GREEN: 37 파일 580/580 통과. `npm run typecheck` 오류 0.
- 금지 파일(`LineageSection.tsx` · `.pv-tile` 크기 CSS · `pointFromViewport` · `ScreenshotButton.tsx`) diff 0.

## 비고
- Part 2·3 은 같은 파일에 얽혀 커밋 하나로 묶음(지시는 둘로 나누기였음 — 분리 시 hunk 수작업 위험이 커 통합).
