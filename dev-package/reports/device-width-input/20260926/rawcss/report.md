# 휴대폰·패드 대응 20260926 — 정리 레인 rawcss 보고

- spec: `dev-package/prd/specs/S-DEVICE-WIDTH-INPUT-20260926.md` · intent: `dev-package/intent/2026-09-26-device-width-input-rules.md`
- 기준: 통합 헤드 `909fe89e` · 브랜치 `claude/dwi-rawcss`
- 결정 근거: advisor ② L3b 지적 — 새 시험이 CSS 를 `node:fs` + `@ts-expect-error` 로 읽음. 저장소 규칙(`frontend/test/e01-apply-points.test.ts` 머리 주석 · `frontend/vite.config.ts` `test.css.include` 주석 · 2026-09-02 배포 불가 사고)은 `?raw` + 허용 목록.

## 변경

| 파일 | 변경 |
|---|---|
| `frontend/vite.config.ts` | `test.css.include` 에 `?raw` 전용 8항목 추가: preview · lineage · lineageGraph · approval · members · variableTable · login · touchNote |
| `frontend/test/device-width-input-20260926-L2b.test.ts` | CSS 12파일 `?raw` import · `targets.json` 도 `?raw` + `JSON.parse` · `node:fs`/`node:path` import 와 `@ts-expect-error` 2줄 삭제 |
| `frontend/test/device-width-input-20260926-L3b.test.tsx` | CSS 2파일 `?raw` import · `node:fs`/`node:path` import 와 `@ts-expect-error` 2줄 삭제 |
| `frontend/test/device-width-input-20260926-L2a.test.ts` | CSS 4파일 `?raw` import · `node:fs`/`node:path` import 와 `@ts-expect-error` 2줄 삭제 |
| `frontend/test/device-width-input-20260926-L1.test.tsx` | CSS 2파일(preview · detail) `?raw` 로 전환 · 비 CSS 읽기 유지 |
| `frontend/test/device-width-input-20260926-L3a.test.tsx` | CSS 4파일(touchNote · lineageGraph · login · tokens) `?raw` 로 전환 · 비 CSS 읽기 유지 |

- 5파일마다 「CSS 원문 적재」 시험 추가: 원문 길이 > 0 · 파일별 알려진 선택자 1개 포함. 합 24항목. 허용 목록 누락 시 빈 문자열 → red.
- `?raw` 조회 함수는 표에 없는 경로면 throw — 오타 · 누락이 조용히 통과하지 않음.
- 단언 삭제 0 — 삭제 줄 중 `expect(` 0건. 기존 단언의 대상 문자열 · 주석 제거 처리 불변.
- `?raw` 전용 정규식만 추가 — 계산값 적재 대상은 늘리지 않음(다른 시험의 jsdom 계산값 불변).

## node:fs 사용 — 전 · 후

| 시험 | 전 | 후 |
|---|---|---|
| L2b | CSS 12 · targets.json | 0 |
| L3b | CSS 2 | 0 |
| L2a | CSS 4 | 0 |
| L1 | CSS 2 · spec md · targets.json · src 전수 걷기 · PreviewPanels.tsx | CSS 0 · 나머지 유지 |
| L3a | CSS 4 · tsx 전수 걷기 · TouchNote.tsx | CSS 0 · 나머지 유지 |
| L0a | scenes.json · 임시 디렉터리 · diff.mjs · capture.py 실행 | 변경 없음(CSS 아님) |
| L0b | targets.json · judge-exempt.txt · scenes.json · 임시 디렉터리 · measure.js 외 | 변경 없음(CSS 아님) |

## RED → GREEN

- RED(시험만 전환 · 허용 목록 변경 전): 5파일 262건 중 59 실패. 「적재」 12항목 실패 = 목록 밖 8파일(preview · lineageGraph · lineage · approval · members · variableTable · login · touchNote). 예: `AssertionError: src/components/members/members.css: expected 0 to be greater than 0`. L2a 는 4파일 모두 기존 목록 안 → green.
- GREEN(허용 목록 추가 후): 5파일 262 통과 · `tsc --noEmit` 오류 0.

## 게이트

- `gates/run.sh task`(frontend-typecheck · frontend-test): green 2 / red(판정) 0 / red(준비) 0 · vitest 152파일 2234건 통과.

## 후속 후보

- L0a · L0b · L1 · L3a 의 비 CSS `node:fs` 읽기는 `@ts-expect-error` 로 남음. JSON · md 는 `?raw`, 소스 전수는 `import.meta.glob` 으로 옮길 수 있음 — 이번 범위(CSS) 밖. 임시 디렉터리 · 스크립트 실행(L0a · L0b)은 대체 수단 없음.
- 같은 `@ts-expect-error` + `node:fs` import 가 이 회차 밖 시험 19파일에도 있음(예: `design-fix-20260924-L1` · `preview-map-viewport-20260918`). `tsc` 는 `@ts-expect-error` 로 통과 → 이 금지 규칙을 검사하는 게이트 없음.
