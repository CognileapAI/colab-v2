# 레인 A3 — 업로드 좌측 미리보기의 변수·시각 고르개 조건부 표시

- 기점 = `origin/main` `b5e8e79f` (`git rev-parse HEAD` 대조 일치).
- 범위 = 프론트 3파일. 대장·원장·HANDOFF 무접촉.

## 1. 변경 파일

| 파일 | 무엇을 |
|---|---|
| `frontend/src/components/preview/PreviewPickRow.tsx` | prop `hideSingleChoice` 신설. 켜지면 변수 고르개는 `variables.length >= 2` 일 때만, 시각 고르개는 `description.instants.count > 1` 일 때만 렌더. 파일 고르개 무변. 머릿말에 예외 조건과 근거(업로드 화면 · 기획서 rev2) 한 절 추가 |
| `frontend/src/components/upload/PreviewPanel.tsx` | 인라인(업로드 모달) 호출부에만 `hideSingleChoice` 전달 |
| `frontend/test/upload-pick-conditional-20260913.test.tsx` | 신규 시험 5건 |

- 판정식 = `PreviewPickRow.tsx` `showVariable`·`showInstant` 두 줄.
- 시각 판정의 입력은 `instantChoicesOf()` 의 배열이 아니라 `InstantRange.count` 다 — 그 함수는 처음·마지막 둘만 세우므로 건수 판정에 쓸 수 없다.

## 2. 호출부 3곳 상태

| 호출부 | 화면 | `hideSingleChoice` |
|---|---|---|
| `frontend/src/components/upload/PreviewPanel.tsx:538` (`idPrefix="up"`) | 업로드 모달 인라인 | **전달함** |
| `frontend/src/components/upload/PreviewPanel.tsx:722` (`idPrefix="pvx"`) | 확장보기 오버레이 | 무변(미전달) |
| `frontend/src/components/datasetpreview/DatasetPreviewSection.tsx:272` (`idPrefix="dt"`) | 데이터셋 상세 | 무변(미전달) |

- 실측 = `grep -rn "hideSingleChoice" frontend/src` → 정의 3행 ＋ 전달 1행(`PreviewPanel.tsx:549`). 전달은 인라인 호출부 한 곳뿐.
- 기본값 `false` 이므로 무변 두 곳의 렌더 트리는 변경 전과 동일.

## 3. 시험 계수

- RED 확인(구현 전) — 5건 중 2건 실패.
  - `AssertionError: expected <select class="sel" …(3)></select> to be null` · 수신값 `data-testid="up-pick-instant"`.
  - 같은 형태로 `up-pick-variable` 도 실패.
- GREEN(구현 후) — 신규 파일 단독 `5 passed (5)`.
- 신규 시험 5건의 갈래
  - 업로드 인라인 · 단일 변수(1) · 단일 시각(`count` 1) → 변수·시각 고르개 부재 · `select` 1개.
  - 업로드 인라인 · `instants: null` → 시각 고르개 부재 · 변수 고르개 존재 · `select` 2개.
  - 업로드 인라인 · 다변수(2) · 다시각(`count` 2) → `select` 3개.
  - 데이터셋 상세 · 단일 변수·단일 시각 → `select` 3개 유지(무변 잠금 확인).
  - 확장보기 오버레이 · 단일 변수·단일 시각 → `select` 3개 유지(무변 잠금 확인).
- 기존 시험 무변 — `preview-layout-20260912.test.tsx`·`preview-pick-and-fallback.test.tsx` 는 픽스처가 변수 2 · `count` 2 라 업로드 갈래에서도 세 고르개가 그대로 서고, 수정 없이 통과.

## 4. 게이트 요약줄

선언 = `lifecycle begin --role lane-worker --gate frontend-test --gate frontend-typecheck`,
배출처 `dev-package/reports/upload-form-rev2/lane-A3-gates`.

최종 실행(형제 레인 유휴 확인 뒤 1회) —

- `frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 1331건 · 실패 0건.`
- `frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.`
- `── 계 : green 2 / red(판정) 0 / red(준비) 0`
- `gate-summary.json` = `schema colab-gate-summary/1` · `counts {green 2, red_판정 0, red_준비 0}` · `task_evidence.before.files` 와 `after.files` 동일(`dfdb5c59…`).

## 5. 앞선 회차의 red 판독 — 판정 red 가 아니라 호스트 부하

- 형제 레인(`.claude/worktrees/agent-a69909e167d07b4d5`)이 같은 호스트에서 `vitest run` 전수를 동시에 돌렸다. 실측 load average 78 → 173.
- 그 구간의 실패는 전부 **벽시계 대기**에 걸린 것이고, 이 레인이 고친 컴포넌트와 무관한 데이터셋 상세 화면의 확대·지연 시험이다.
  - `dataset-preview-zoom.test.tsx` — `TestingLibraryElementError: Unable to find an element by: [data-testid="preview-map"]` (`findByTestId` 기본 1000 ms).
  - `dataset-preview-tiles.test.tsx`·`dataset-preview-zoom-latency.test.tsx` — `잰값.max` 가 상한 100 ms 를 넘음(실측 최대 119.064 ms · 같은 표본의 p95 는 27.402 ms).
- 같은 트리·같은 세 파일을 **부하가 빠진 뒤 단독 실행**하면 `3 passed (3)` / `35 passed (35)`.
- 전수 실적(같은 명령 · 6회) — 형제 레인 유휴 구간 3회는 전부 `109 passed (109)` / `1331 passed (1331)`, 동시 실행 구간 3회는 각각 27건 · 3건 · 3건 실패. 실패 목록은 회차마다 달랐고 겹치는 파일은 벽시계 대기가 있는 셋뿐이다.
- 규칙 대조 = `.claude/rules/colab-rules.md §1-b ⑸`(검사기 판정은 낮은 병렬도로 재현한 뒤 병합 기준으로 쓴다) · 같은 파일 `§9`(전수 게이트 중 다른 실행 레인 금지).

## 6. 기존 결함 — 어느 검사에 걸리나

「main 에도 있다」로 적지 않고 걸리는 검사를 적는다.

1. **벽시계 지연 단언이 `frontend-test` 게이트 안에 있다.**
   - 자리 = `frontend/test/dataset-preview-tiles.test.tsx:307,339,355` · `frontend/test/dataset-preview-zoom-latency.test.tsx:29,126,142` (`상한_밀리초 = 100` · `expect(잰값.max).toBeLessThan(...)`).
   - 결과 = 게이트 판정이 호스트 부하에 종속된다. 같은 트리에서 green 과 red 가 갈린다.
   - 걸리는 검사 = `frontend-test` 한 곳뿐이고, 이 게이트는 그 red 를 **판정 red** 로 낸다(준비 red 갈래가 없다).
2. **이 호스트의 기본 `node` 로는 `frontend-test` 가 아예 돌지 않는다.**
   - 실측 = `/usr/local/bin/node` = `v21.4.0`. `frontend/package.json` 의 `engines.node` 는 `>=22`.
   - 증상 = `SyntaxError: The requested module 'node:util' does not provide an export named 'styleText'`(rolldown). node 22.9.0 으로 올려도 `ERR_REQUIRE_ESM`(`html-encoding-sniffer` → `@exodus/bytes`) 로 막히고 node 22.20.0 에서 통과.
   - 걸리는 검사 = 없다. `frontend-test.sh` 는 `node_modules`·`vitest` 실행 파일 **존재**만 준비 조건으로 보고 **node 버전은 보지 않는다**. 그래서 이 실패가 준비 red(78)가 아니라 판정 red(1)로 나온다.
3. **워크트리 `npm ci` 가 선택적 네이티브 바인딩을 빠뜨렸다.**
   - 실측 = 이 워크트리 `frontend/node_modules/@rolldown/` 에 `binding-darwin-x64` 부재(본 체크아웃에는 있음 · 두 곳 다 `rolldown` 1.2.5).
   - 조치 = 본 체크아웃의 같은 버전 디렉터리를 복사(`node_modules` 는 추적 대상이 아니므로 파일 변경 0).
   - 걸리는 검사 = 없다. 훅 `worktree-setup.sh` 의 설치 성공 여부를 재는 자리가 없다.
4. **CSS 주석이 이번 예외와 어긋난다.**
   - 자리 = `frontend/src/components/preview/preview.css:374`~`377` — 「자리가 상태마다 사라지지 않는다 — 후보가 없어도 잠긴 채 서 있다(세 화면 자리 일관성)」.
   - 업로드 화면은 이제 예외라 이 문장이 세 화면 모두에 성립하지 않는다. 배치는 `.pv-pick { display:flex; gap:8px }` 라 자식이 줄어도 깨지지 않는다.
   - 이 레인의 소유 파일 밖이라 고치지 않았다. 후속 항목.

## 7. 완료 정의 대조

지시문이 정한 완료 정의 대비.

| 항목 | 상태 |
|---|---|
| 업로드 화면에서만 후보 둘 이상일 때 변수·시각 고르개 표시 | 충족 |
| 상세·확장보기 무변 | 충족(grep ＋ 시험 2건) |
| 시험 red → green 확인 | 충족(red 2건 인용 · green 5/5) |
| `npx vitest run` ＋ `tsc --noEmit` 3회 연속 green | **부분** — `tsc --noEmit` 은 실행한 모든 회차에서 오류 0건. `vitest run` 전수는 6회 중 3회 green(전부 1331/1331) 이고, 마지막 2회(코드 동결 뒤 게이트 실행분)는 **연속 green** 이다. 연속 3회는 성립하지 않았고 미달 사유는 5절(형제 레인 동시 실행)이다. 남은 조건 = 형제 레인이 멈춘 구간에서 전수 1회 더 |
| `frontend-test`·`frontend-typecheck` 각 1회 green | 충족 — 최종 실행 `── 계 : green 2 / red(판정) 0 / red(준비) 0` |

초과분(요청되지 않은 변경) = 없다. 변경 파일은 소유 목록 안의 3개뿐이다.
