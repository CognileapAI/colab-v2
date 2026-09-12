# 이슈 조사 C군 — 미리보기 이미지·컨트롤 (#26 · #27 · #28 · #25 · #29)

- 조사 기준 커밋 `10a3fb8` (조사 워크트리 HEAD `1f1f58b` = `10a3fb8` ＋ 이슈 회수본 파일)
- 작성자 researcher · 승인 **미승인**
- 입력 = `dev-package/reports/issues/2026-09-12-github-open-issues.md` `## #29`~`## #25`
- 스크린샷 = 7건 전부 다운로드·열람 완료(#26 1 · #27 1 · #28 3 · #25 1 · #29 1). 「스크린샷 미열람」 0건
- 근거 등급 표기 = `코드에 존재` / `테스트 존재` / `미확인`. 행 번호를 적지 않고 문자열 앵커로 지목

---

## 0. 이 군이 공유하는 구조 (다섯 건이 같은 두 파일에 모인다)

- 업로드 화면 미리보기의 실물 = `frontend/src/components/upload/PreviewPanel.tsx` 한 파일(746행). 인라인 미리보기와 확장보기 오버레이가 **같은 컴포넌트 안**에 있다 — 앵커 `<PreviewSlot state={slotState} testId="up-preview-slot">` 와 `{expanded && (`.
- 4:3 틀 = `frontend/src/components/preview/PreviewSlot.tsx`(`.pv-frame` · `.pv-frame-in`), 치수 규칙은 `frontend/src/components/preview/preview.css` 앵커 `--pv-frame-ratio` · `.pv-frame-in`.
- 확장보기 틀 = `frontend/src/components/upload/PreviewExpandOverlay.tsx`, 치수 규칙은 `frontend/src/components/upload/upload.css` 앵커 `.modal-b.pvx-b`.
- 확대 컨트롤 = `frontend/src/components/preview/PreviewZoomControls.tsx`(세 화면 공용 · 앵커 `export function PreviewZoomControls`).
- 요지 — **#25 ⑵ · #26 · #27 · #28 넷은 「고정 치수 상자 안에 세로로 쌓인 자식 목록」이라는 한 구조에서 나온다.** 자세한 대조는 각 항 4번.

### 0-1. 공통 구조 사실 셋 (전부 `코드에 존재`)

1. `.pv-frame` 은 `aspect-ratio: var(--pv-frame-ratio)`(4/3) ＋ `overflow: hidden` 이고, 안쪽 `.pv-frame-in` 은 `flex-direction: column` ＋ `justify-content: center` ＋ `overflow: auto` 다(`preview.css` 앵커 `.pv-frame` · `.pv-frame-in`).
2. 그 안쪽에 `PreviewPanel` 이 순서대로 넣는 자식 = ① `PreviewPickRow`(파일·변수·시각) ② 진행 안내 `up-preview-stage` ③ 오류 ④ 부분 실패 ⑤ `.mapcanvas`(배지 · 썸네일 · `.pv-viewport` · `PreviewZoomControls`) ⑥ salvage ⑦ 색 범위 안내 ⑧ `.vizph`.
3. 상자 높이는 고정인데 자식 총 높이는 상태에 따라 늘어난다 ⟹ **그림이 완성되면 ① 은 스크롤 위로, ⑤ 끝의 확대 줄은 스크롤 아래로 밀려난다.** 화면에 남는 것은 가운데 그림뿐이다.

---

## 1. `#26` [버그] 이미지 미리보기가 이상한 곳에 하나 더 그려짐

### 1-1. 이슈 요지

업로드 화면 미리보기 그림 왼쪽 위에 작은 그림 조각이 하나 더 표시된다. 사용자는 이것을 렌더 중복으로 인지한다.

### 1-2. 재현 경로

| 단계 | 내용 | 등급 |
|---|---|---|
| 화면 | 업로드 모달 장면2 · 좌측 미리보기 칸 | 코드에 존재 |
| 조작 | 파일 선택 후 미리보기 렌더 완료(`job.status === '완료'`) | 코드에 존재 |
| 관측 | 4:3 틀 왼쪽 위에 64×64 크기의 축소 그림 1개 ＋ 그 아래 본 그림 | 스크린샷 `issue-26-1` |
| 기대 | 그림 1개 | — |

### 1-3. 관련 코드 앵커

- `frontend/src/components/upload/PreviewPanel.tsx` — `.mapcanvas` 블록 안 앵커 `data-testid="up-preview-thumb"` (`layers?.thumbnailUrl ? <img className="thumb" …>`).
- `frontend/src/components/upload/PreviewPanel.tsx` — 같은 블록의 앵커 `data-testid="up-preview-viewport"`(본 그림).
- `frontend/src/components/upload/upload.css` — 앵커 `.mapcanvas .thumb { width: 64px; height: 64px; object-fit: contain; image-rendering: pixelated; }`.
- `frontend/src/components/upload/PreviewPanel.tsx` — `representativePicker` 안 앵커 `data-testid="up-thumb-img"`(대표 그림 고르개의 같은 축소본. `<details className="up-preview-options">` 안이라 접혀 있다).

### 1-4. 원인 가설

- **가설 A (채택 후보 · `코드에 존재`)** — 중복 렌더가 아니라 **자동 생성 축소본(`up-preview-thumb`)이 지도 자리 안에 함께 그려지고 있다.** 근거 셋 — ⑴ `.mapcanvas` 자식 순서상 축소본이 `.pv-viewport` **앞**이라 왼쪽 위에 온다 ⑵ CSS 가 64×64 를 준다 ⑶ 스크린샷의 조각은 본 그림과 같은 자료의 축소본 형상이다(그림 대조). 같은 축소본이 `up-thumb-img` 로 대표 그림 고르개에도 이미 있으므로 지도 자리의 것은 **두 번째 표시**다.
- **가설 B (`미확인`)** — 서버가 한 렌더에서 두 산출물(`imageUrl` ＋ 축소본)을 주는데 화면이 둘 다 지도 층에 얹는 형태. `services/viz-render` 쪽 중복 생성 여부는 이번 조사에서 재지 않았다.
- **배제한 것** — React StrictMode 이중 effect · 정리 없는 stale effect · 타일/한 장 동시 마운트. `PreviewPanel` 은 `pollGen` 세대 검사로 늦은 응답을 버리고(앵커 `const gen = ++pollGen.current;`), `PreviewMap` 의 갈래는 `const tiled = Boolean(...)` 로 배타이며, 확장보기 그림은 오버레이 안에만 있다.

### 1-5. 수정 범위 초안

- 파일 = `frontend/src/components/upload/PreviewPanel.tsx`(축소본 img 제거 또는 `<details>` 안으로 이동) ＋ 필요 시 `frontend/src/components/upload/upload.css`(`.mapcanvas .thumb` 규칙 정리).
- `contracts/` 변경 = 없음. DB 마이그레이션 = 없음. **동결 해제 서명 불요.**
- 프런트 전용. 백엔드(viz-render) 무접촉 — 가설 B 로 판정이 바뀌면 그때 재산정.

### 1-6. red 테스트 후보

- 기존 파일 = `frontend/test/upload.test.tsx`(`up-preview-thumb` 참조 존재) · `frontend/test/grid-preview.test.tsx`.
- 첫 실패 테스트 = 「렌더 완료 후 `up-preview-map` 안에 그림 요소가 1개다」 — `within(getByTestId('up-preview-map')).queryAllByRole('img')` 길이 1 단언. 현재 2 로 red.

### 1-7. 겹침·순서 의존

- 같은 파일 = `#25` ⑵ · `#27` · `#28`. **직렬**.
- A군(`#32`~`#34` · `UploadModal.tsx`) · B군(`#31`·`#24` · `RegisterArea`/`UploadModal`)과 파일 겹침 없음 ⟹ 병렬 가능.

### 1-8. 범위 판정 후보

- **`v2 버그`.** 근거 = 라벨 `bug` · 하나의 데이터에 그림이 둘로 보이는 것은 「무엇을 그렸는가」를 흐린다. AI 무관 · 대화형 UI 무관 · 편의 기능 아님.

### 1-9. 크기

- 파일 2 · 추정 5~15행(삭제 위주) ＋ 시험 1건. 근거 = 조작 대상이 단일 `<img>` 블록과 CSS 한 줄.

### 1-10. 대장 대조

- `dev-package/work-items.yaml` — `id: WU-C1` / `status: done`(미리보기 자리 선점 4:3 틀).
- 같은 파일 — `id: WU-C4` / `status: done`(축척 사다리 ＋ 세 화면 공유 확대).
- 축소본 표시 자체를 소유한 항목 = `WU-A10`(대표 그림). 대장에서 `id: WU-A10` 행은 이번 조사에서 확인하지 않음 `[미확인]`.

---

## 2. `#27` [개선] 이미지 컨트롤과 줌 영역 분리

### 2-1. 이슈 요지

확대·축소·기본 배율로 세 버튼이 미리보기 상자 스크롤 맨 아래에 있어 눈에 들어오지 않는다. 확대·축소 시 그림이 아니라 그림이 든 칸 자체가 움직이는 것으로 인지된다.

### 2-2. 재현 경로

| 단계 | 내용 | 등급 |
|---|---|---|
| 화면 | 업로드 모달 장면2 좌측 미리보기 칸 | 코드에 존재 |
| 조작 | 렌더 완료 후 미리보기 상자를 아래로 스크롤 | 코드에 존재 |
| 관측 | 그림 아래·색 범위 안내 위에 확대/축소/기본 배율로 3버튼. 스크롤하지 않으면 보이지 않는다 | 스크린샷 `issue-27-1`(우측 스크롤바 표시) |
| 기대 | 그림 위에 고정된 조작 자리 | — |

### 2-3. 관련 코드 앵커

- `frontend/src/components/upload/PreviewPanel.tsx` — `.mapcanvas` 끝 앵커 `<PreviewZoomControls zoom={zoom} testId="up-preview-zoom" />`.
- `frontend/src/components/preview/preview.css` — 앵커 `.pv-frame-in`(`overflow: auto`) · `.pv-zoom`(`display: flex`, 위치 지정 없음) · `.pv-viewport`(`overflow: hidden`).
- `frontend/src/components/preview/useZoomPan.ts` — 앵커 `export function centeredPanFor` · `const pan = centeredPanFor(view, box());`.
- `frontend/src/components/preview/PreviewPanels.tsx` — 상세 화면 쪽 같은 배치 앵커 `{zoom ? <PreviewZoomControls zoom={zoom} /> : null}`(`.pv-mapcol` 세로 흐름의 마지막).

### 2-4. 원인 가설

- **가설 A (`코드에 존재`)** — 확대 줄이 **뷰포트 위에 겹쳐 놓이지 않고 세로 흐름의 형제 요소**다. 4:3 고정 상자가 세로 공간을 다 쓰면 그 줄은 스크롤 밖으로 나간다(`0-1` 구조 사실 3).
- **가설 B — 「칸 자체가 움직인다」 (`코드에 존재`)** — 변환은 `.pv-layers` 하나에 `translate(x,y) scale(s)` 로 걸리고(`PreviewPanel.tsx` 앵커 `transform: \`translate(${zoom.x}px, ${zoom.y}px) scale(${zoom.scale})\``), 바깥 `.pv-viewport` 는 `overflow: hidden` 이다. 즉 잘라 내는 창은 고정이다. 다만 `.pv-layers .pv-tile` 이 `width: 100%` 이고 `.pv-frame` 계열의 `max-height` 제약이 `.pv-viewport` 안쪽까지 닿지 않아, 배율이 1 을 넘으면 층 상자가 창보다 커지며 `.pv-frame-in` 의 스크롤이 함께 움직인다. 실제 스크롤 발생 여부는 브라우저 실측 필요 `[미확인]`.

### 2-5. 수정 범위 초안

- 파일 = `frontend/src/components/upload/PreviewPanel.tsx`(확대 줄을 `.pv-viewport` 안 절대 배치로 이동) · `frontend/src/components/preview/preview.css`(`.pv-zoom` 위치 규칙 신설) · 세 화면 공유를 유지하려면 `frontend/src/components/preview/PreviewPanels.tsx`·`frontend/src/components/datasetpreview/DatasetPreviewSection.tsx` 동반 확인.
- `contracts/` · DB 마이그레이션 = 없음. **동결 해제 서명 불요.**
- 프런트 전용.

### 2-6. red 테스트 후보

- 기존 파일 = `frontend/test/scale-ladder.test.tsx`(`up-preview-zoom` 참조) · `frontend/test/dataset-preview-zoom.test.tsx` · `frontend/test/preview-slot-4x3.test.tsx`.
- 첫 실패 테스트 = 「`up-preview-zoom` 이 `up-preview-viewport` 의 자손이다」 — `getByTestId('up-preview-viewport').contains(getByTestId('up-preview-zoom'))` 단언. 현재 형제라 red.
- 보조 = `preview.css` 원문 계측(`.pv-zoom` 에 `position: absolute` 존재) — 이 레포가 jsdom 한계 때문에 이미 쓰는 방식(`preview-slot-4x3.test.tsx` 선례).

### 2-7. 겹침·순서 의존

- **`#28` 과 같은 사안의 두 화면판이다.** 확장보기 쪽 배치가 `#28`, 인라인 쪽 배치가 `#27`. 공용 컴포넌트 `PreviewZoomControls` 를 함께 건드리므로 **한 레인**으로 묶는다.
- `#26`·`#25` ⑵ 와 같은 파일 ⟹ 직렬.

### 2-8. 범위 판정 후보

- **`v2 버그` 후보**(판정은 Ted). 근거 = 라벨은 `improvemet` 이나 「조작 자리가 화면에 보이지 않는다」는 기능 도달 실패다. 대장 `BF-3`(확대 한계 안내)이 같은 계열을 이미 버그로 다뤘다.
- 반대 근거 = 「지도 서비스처럼 고정」은 새 배치 요구이므로 편의 기능으로 읽을 여지 있음. **양쪽을 적고 승자를 고르지 않는다.**

### 2-9. 크기

- 파일 2~4 · 추정 30~60행. 근거 = 배치 CSS 신설 ＋ 세 화면(업로드·상세·확장보기) 동반 확인.

### 2-10. 대장 대조

- `dev-package/work-items.yaml` — `id: WU-C4` / `status: done`. `completion_def` 축자 일부 = `useZoomPan/.pv-zoom 을 상세·업로드·확장보기가 공유`. **공유 요구는 살아 있으므로 한 화면만 고치면 그 완료 정의가 깨진다.**
- 같은 파일 — `id: BF-3` / `status: done`(확대 한계 안내).

---

## 3. `#28` [개선] 미리보기 확장 시 버튼 위치

### 3-1. 이슈 요지

확장보기를 열면 확대·축소·기본 배율로 버튼이 그림 오른쪽 옆에 세로로 눌려 배치된다(글자가 두 줄로 접힌다). 화면 한쪽에 고정되는 배치를 요청한다.

### 3-2. 재현 경로

| 단계 | 내용 | 등급 |
|---|---|---|
| 화면 | 업로드 모달 장면2 → 미리보기 머리의 `⤢` | 코드에 존재(앵커 `data-testid="pv-expand"`) |
| 조작 | 확장보기 오버레이 열기 | 코드에 존재 |
| 관측 | 그림 오른쪽에 3버튼이 세로 배치·글자 접힘 | 스크린샷 `issue-28-1` |
| 기대 | 그림 위 한쪽에 고정된 조작 자리(예시 스크린샷 `issue-28-2`·`issue-28-3`) | — |

### 3-3. 관련 코드 앵커

- `frontend/src/components/upload/upload.css` — 앵커 `.modal-b.pvx-b{height:min(70vh,640px);overflow:auto;display:flex;align-items:center;justify-content:center;}`.
- `frontend/src/components/upload/PreviewPanel.tsx` — 확장보기 블록 앵커 `data-testid="pv-expand-viewport"` 와 그 형제 `<PreviewZoomControls zoom={expandZoom} testId="pv-expand-zoom" />`.
- `frontend/src/components/upload/upload.css` — 앵커 `.pvx-img{display:block;max-width:100%;max-height:100%;image-rendering:pixelated;}`.
- `frontend/src/components/preview/preview.css` — 앵커 `.pv-layers .pv-tile { display: block; width: 100%; … }`.

### 3-4. 원인 가설

- **가설 A (채택 후보 · `코드에 존재`)** — 오버레이 본문이 `display: flex` 이고 방향 선언이 없어 **기본값 `row`** 다. 자식이 `.pv-viewport` 와 `.pv-zoom` 둘이므로 확대 줄이 그림 **오른쪽 열**로 간다. 인라인 쪽(`#27`)은 같은 두 자식이 `column` 흐름이라 아래로 간다 — **한 컴포넌트가 부모 방향에 따라 두 자리로 갈린다.**
- **가설 B (`코드에 존재`)** — 그림 폭이 `.pv-layers .pv-tile { width: 100% }` 로 잡히는데 `.pv-viewport` 에 폭 상한이 없어 flex 행에서 그림이 남는 폭을 다 먹고, 버튼 열은 최소 폭으로 눌린다(스크린샷의 「확 대」 두 줄 접힘이 그 증상).
- 두 가설은 배타가 아니다 — A 가 열을 만들고 B 가 그 열을 눌렀다.

### 3-5. 수정 범위 초안

- 파일 = `frontend/src/components/upload/upload.css`(`.pvx-b` 방향·정렬) · `frontend/src/components/upload/PreviewPanel.tsx`(확대 줄을 뷰포트 안으로) · `frontend/src/components/preview/preview.css`(`#27` 과 같은 규칙 재사용).
- `contracts/` · DB 마이그레이션 = 없음. **동결 해제 서명 불요.**
- 프런트 전용.

### 3-6. red 테스트 후보

- 기존 파일 = `frontend/test/upload.test.tsx`(`pv-expand` 계열 참조) · `frontend/test/preview-slot-4x3.test.tsx`.
- 첫 실패 테스트 = 「`pv-expand-zoom` 이 `pv-expand-viewport` 의 자손이다」 단언. 현재 형제라 red.
- 보조 = `upload.css` 원문 계측(`.pvx-b` 에 `flex-direction: column` 또는 그림 폭 상한 존재).

### 3-7. 겹침·순서 의존

- **`#27` 과 같은 레인.** 같은 컴포넌트(`PreviewZoomControls`)와 같은 두 CSS 파일을 만진다. 따로 두면 두 레인이 같은 줄을 서로 다른 자리로 옮긴다.
- `#26`·`#25` ⑵ 와 같은 파일(`PreviewPanel.tsx`) ⟹ 직렬.

### 3-8. 범위 판정 후보

- **`v2 버그` 후보**(판정은 Ted). 근거 = 버튼 글자가 두 줄로 접혀 읽히는 것은 표시 결함이다.
- 「화면 한쪽에 계속 고정」이라는 **요청 형태 자체**는 새 배치 요구 ⟹ 그 부분만 떼면 `편의 기능(후일 묶음)`. 권고 = 접힘·가림 해소까지를 버그로 처리하고 고정 배치 방식은 Ted 판정 항목으로 올린다.

### 3-9. 크기

- 파일 2~3 · 추정 20~40행. `#27` 과 합치면 합계 40~80행 · 파일 3~4.

### 3-10. 대장 대조

- `dev-package/work-items.yaml` — `id: WU-C4` / `status: done`(확장보기 포함 세 화면 공유).
- 같은 파일 — `id: WU-C1` / `status: done`(4:3 틀). 확장보기는 그 틀 **밖**이다(`PreviewSlot.tsx` 머리 주석 축자 「확장보기(㈎)·격자 업로드 블록은 이 틀 **밖**·같은 컨테이너 안에 그대로 남는다」).

---

## 4. `#25` [개선] 업로드 화면 진입 시 지도를 한참 그림 / 이미지 선택 위치

이슈에 항목이 둘이다. 원인이 다르므로 갈라 적는다.

### 4-1. 이슈 요지

⑴ 업로드 화면 진입 후 「지도 그리는 중…」 상태가 길게 이어진다. ⑵ 파일·변수·시각 고르개가 미리보기 상자 **안**에 있고, 그림이 나오면 사라진다.

### 4-2. 재현 경로

| 단계 | 내용 | 등급 |
|---|---|---|
| 화면 | 업로드 모달 장면2(파일 141개 · `gk2a_ami_le2_lst_ko_202005010000.nc`) | 스크린샷 `issue-25-1` |
| 조작 ⑴ | 등록 단계 진입 즉시 자동 렌더 | 코드에 존재 — `PreviewPanel.tsx` 앵커 `if (!props.autoPreview \|\| !uploadId \|\| !palette \|\| autoRequested.current === uploadId) return;` |
| 관측 ⑴ | `지도 그리는 중…` 이 장시간 유지 | 스크린샷 `issue-25-1`. 실측 소요 = **`미확인`** |
| 조작 ⑵ | 렌더 완료까지 대기 | 코드에 존재 |
| 관측 ⑵ | 렌더 전에는 파일·변수·시각 고르개가 보이고, 완료 후에는 보이지 않는다 | 스크린샷 `issue-25-1`(렌더 중, 고르개 보임) ↔ `issue-26-1`(완료, 고르개 없음·스크롤바 있음) |
| 기대 ⑵ | 고르개가 상태와 무관하게 같은 자리에 있다 | — |

### 4-3. 관련 코드 앵커

- 고르개 = `frontend/src/components/preview/PreviewPickRow.tsx` 앵커 `export function PreviewPickRow` · 마운트 자리는 `PreviewPanel.tsx` 앵커 `<PreviewPickRow` (`<PreviewSlot …>` 바로 안).
- 틀 = `frontend/src/components/preview/preview.css` 앵커 `.pv-frame` · `.pv-frame-in`.
- 자동 렌더 = `PreviewPanel.tsx` 앵커 `autoRequested.current = uploadId;` · `void draw(false);`.
- 재마운트 열쇠 = `frontend/src/components/upload/UploadModal.tsx` 앵커 `key={\`${signature}:${previewUploadId ?? ''}:${gridRevision}\`}`.
- 폴링 = `PreviewPanel.tsx` 앵커 `const POLL_MS = 250;` · `function poll(renderId: string, gen: number)`.
- 배경 벡터 = `frontend/src/components/preview/BasemapLayer.tsx` 앵커 `export function basemapPathData`(정적 import · `useMemo`).

### 4-4. 원인 가설

**⑵ 고르개가 사라진다 — 가설 A (채택 후보 · `코드에 존재`)**
- 고르개는 조건부 렌더가 아니다(`PreviewPickRow` 는 무조건 마운트되고 후보가 없으면 잠긴다 — 같은 파일 머리 주석 축자 「후보가 없어도 자리를 지킨다(disabled)」).
- 사라지는 것이 아니라 **4:3 고정 상자의 스크롤 위로 밀려난다.** `.pv-frame-in` 의 `justify-content: center` 가 내용이 넘칠 때 위쪽을 잘라 내는 쪽으로 작동한다.
- 대조 근거 = 스크린샷 `issue-26-1` 에 세로 스크롤바가 표시된다.

**⑴ 렌더가 길다 — 가설 A (`미확인` · 서버 몫)**
- 원장 실측 = `dev-package/PLAN-SoT.md` `〈241〉`-㉳ 축자 「p95 를 만드는 것은 갈래가 아니라 **원천 두 건**이다(`MODIS MOD15A2H 견본` 14.2 s · `GK2A/AMI NDVI 원자료(Lv.0)` 12.2 s — 나머지는 0.34 ~ 2.5 s)」. **이슈의 파일도 GK2A/AMI 계열**이다.
- 상한 눈금 = 같은 문서 `〈240〉`-㉱⑶ 축자 「`〈233〉` 이 적은 렌더 성능·상한(p95 10초 · 상한 60초 · 확대 100 ms)」.
- 이번 조사에서 실측 0회 ⟹ 「길다」의 값은 `미확인`.

**⑴ 렌더가 길다 — 가설 B (`코드에 존재` · 화면 몫)**
- `PreviewPanel` 의 `key` 에 `signature`·`gridRevision` 이 들어 있어 그 둘이 바뀌면 **컴포넌트가 다시 마운트되고 `autoRequested` ref 가 초기화되어 자동 렌더가 다시 걸린다.** 141개 파일 업로드처럼 `signature` 가 도중에 갈리는 흐름에서 렌더가 반복될 수 있다.
- 반복 발생 여부는 브라우저 실측 필요 `[미확인]`.
- 폴링 간격 250 ms 는 지연의 원인이 아니라 표시 갱신 주기다.

### 4-5. POL-021 대조 (지시받은 확인 항목)

- **화면이 그리는 배경은 POL-021 위반이 아니다.** 근거 = `dev-package/PLAN-SoT.md` `〈375〉` 축자 「반전 범위 = 레포에 반입한 **자립형 벡터 배경**(Natural Earth 1:110m 해안선＋국경 …) **만 허용** · **타일 서버·외부 CDN·지도 라이브러리 금지는 그대로 유지**」.
- 대조 = `BasemapLayer.tsx` 는 `import coastline from '../../assets/basemap/ne_110m_coastline.json'` 정적 import 로만 자산을 들이고 네트워크 호출이 없다. 대장 `dev-package/work-items.yaml` `id: WU-C5` / `status: done` 의 `completion_def` 축자 「외부 요청 0 · 도시 표기 0」.
- 타일 서빙 = 기본값 「한 장」(`〈240〉`-㉲ 축자 「**기본값 = 꺼짐 = 한 장**」). 스크린샷의 결과는 `imageUrl` 갈래로 보이며 타일 요청은 관측되지 않았다 `[미확인 — 네트워크 미계측]`.
- 결론 = **#25 ⑴ 의 지연을 POL-021 위반으로 볼 근거 없음.** 지연은 렌더 원천 시간 또는 화면 재마운트 쪽이다.

### 4-6. 수정 범위 초안

- ⑵ = `frontend/src/components/upload/PreviewPanel.tsx`(고르개를 `PreviewSlot` 밖 고정 줄로 이동) ＋ `frontend/src/components/preview/preview.css`(`.pv-pick` 자리) ＋ 상세 화면 동반 확인 `frontend/src/components/datasetpreview/DatasetPreviewSection.tsx`.
- ⑴ = 먼저 **실측**(렌더 소요 · 재마운트 횟수). 화면 몫이면 `frontend/src/components/upload/UploadModal.tsx` 의 `key` 산식, 서버 몫이면 `services/viz-render` 렌더 경로.
- `contracts/` · DB 마이그레이션 = 없음(현 범위). **동결 해제 서명 불요.**
- ⑵ 프런트 전용 / ⑴ 프런트·백엔드 판정 대기.

### 4-7. red 테스트 후보

- 기존 파일 = `frontend/test/upload.test.tsx` · `frontend/test/preview-slot-4x3.test.tsx` · `frontend/test/upload-preview-poll-20260903.test.tsx`(재렌더 회차 규약).
- 첫 실패 테스트 ⑵ = 「`up-pick-row` 가 `up-preview-slot` 의 자손이 아니다」 단언. 현재 자손이라 red.
- 첫 실패 테스트 ⑴ = `upload-preview-poll-20260903.test.tsx` 계열에 「같은 업로드에서 `createRender` 호출은 1회다」 추가. 재마운트가 실재하면 red.

### 4-8. 겹침·순서 의존

- ⑵ = `#26`·`#27`·`#28` 과 같은 파일 ⟹ **직렬 · 같은 레인**.
- ⑴ = `UploadModal.tsx` 를 만질 수 있다 ⟹ **A군(`#32`~`#34`)·B군(`#24`)과 같은 파일** ⟹ 병렬 금지. 실측 단계까지는 읽기 전용이라 병렬 가능.

### 4-9. 범위 판정 후보

- ⑵ = **`v2 버그`.** 조작 자리가 상태에 따라 화면에서 사라지는 것은 `WU-C1` 완료 정의(치수 불변)와 `WU-C3` 취지(자리를 지킨다)에 어긋난다.
- ⑴ = **판정 보류 — 실측 후.** 눈금 안(p95 10초)이면 `범위 밖`(이미 판정된 성능 기준 충족), 넘으면 `v2 버그`.

### 4-10. 크기

- ⑵ = 파일 2~3 · 추정 20~40행.
- ⑴ = 실측 1회차 ＋ 수정 미정. 근거 = 원인 위치가 갈리지 않았다.

### 4-11. 대장 대조

- `dev-package/work-items.yaml` — `id: WU-C3` / `status: done`. `completion_def` 축자 일부 = `파일·변수·시각 드롭다운 3개 · … · 업로드·상세 양쪽`.
- 같은 파일 — `id: WU-C1` / `status: done` · `id: WU-C5` / `status: done` · `id: PV-1` / `status: done`(미리보기 뒷단).

---

## 5. `#29` [개선] 미리보기 달력에서 고르기

### 5-1. 이슈 요지

미리보기 확장보기 화면에 「기간 (조각 합집합) (선택) · 한 시점이면 비워 둬요 · 달력에서 고르기」가 보인다. 작성자는 용도를 인지하지 못했고, 미리보기에서 고르는 것이라면 업로드된 이미지 중에서 고르는 방식을 제안한다.

### 5-2. 재현 경로

| 단계 | 내용 | 등급 |
|---|---|---|
| 화면 | 업로드 모달 → 미리보기 확장보기 열림 | 코드에 존재 |
| 관측 | 그림 위에 기간 라벨·안내·`달력에서 고르기` 버튼이 겹쳐 보임 | 스크린샷 `issue-29-1`·`issue-28-1` |
| 기대 | 미리보기 화면에는 미리보기 조작만 | — |

### 5-3. 관련 코드 앵커

- 실물 소유자 = `frontend/src/components/upload/RegisterArea.tsx` — 앵커 `const periodLabel = sliced ? '기간 (조각 합집합)' : '기간';` · `<label htmlFor="reg-period-open">{periodLabel} (선택)</label>` · `data-testid="reg-period-open"`(버튼 문면 `달력에서 고르기`) · `data-testid="reg-period-single-hint"`.
- 팝오버 = `frontend/src/components/upload/PeriodCalendarPopover.tsx` 앵커 `export function PeriodCalendarPopover`.
- 배치 = `frontend/src/components/upload/RegisterArea.tsx` 앵커 `<div className="form-row daterange">` · CSS `frontend/src/components/upload/upload.css` 앵커 `.daterange{position:relative;}` · `.dr-pop{position:absolute;…z-index:60;`.
- 오버레이 = `frontend/src/components/upload/upload.css` 앵커 `.modal-back.pvx-back{position:fixed;inset:0;z-index:250;…}` · `.modal.pvx{…background: var(--color-surface);…}`.
- 레이아웃 = `frontend/src/components/upload/UploadModal.tsx` 앵커 `<div className="up-split-preview" data-testid="up-split-preview">`(미리보기) ↔ `<div className="up-split-form" data-testid="up-split-form">`(RegisterArea).

### 5-4. 원인 가설

- **확정된 사실 (`코드에 존재`)** — 화면에 보인 세 요소는 **미리보기 컴포넌트의 것이 아니다.** `PreviewExpandOverlay` 의 자식은 뷰포트와 확대 줄뿐이고(`PreviewPanel.tsx` 앵커 `{expanded && (`), 기간 입력은 오른쪽 폼 칸(`RegisterArea`)에 산다. 레포 전체에서 문자열 `달력에서 고르기` 는 `RegisterArea.tsx` 1곳뿐이다.
- **가설 A — 겹침(스택 문맥) 결함 (`미확인`)** — 오버레이는 `z-index: 250`, 기간 칸은 `.daterange{position:relative}`(z-index 자동)이므로 CSS 선언만으로는 오버레이가 위여야 한다. 관측이 반대이므로 오버레이가 갇힌 스택 문맥이 있거나 `--color-surface` 배경이 적용되지 않는 경로가 있다. **브라우저 실측 필요.** 지어내지 않는다.
- **가설 B — 배치 인지 결함 (`코드에 존재`)** — 뷰포트 폭 1023px 이하에서 `.up-split` 이 1열로 접힌다(`upload.css` 앵커 `@media (max-width: 1023px) { .up-split { grid-template-columns: 1fr; } }`). 스크린샷 `issue-28-1` 의 모달 폭이 `96vw` 로 보이므로 촬영 시점 뷰포트가 그 이하일 가능성이 있다. 1열이면 기간 칸이 미리보기 바로 아래로 와서 「미리보기 안의 것」으로 읽힌다.
- 두 가설은 배타가 아니다.

### 5-5. `colab-rules.md §6-2` 예외 해당 여부

- 규칙 축자 = 「**Ted 지정 예외는 판정으로만 성립**(실례 = rev2 기간 달력 팝오버 판정-2 ⓑ)」(`.claude/rules/colab-rules.md §6-2`).
- 판정 = **그 예외는 업로드 기간 입력의 달력 팝오버 존치에 대한 것이고, 이 이슈는 그 컨트롤의 존치를 다투지 않는다.** 이슈가 묻는 것은 ⑴ 왜 미리보기 자리에 보이는가(배치·겹침) ⑵ 미리보기에서 「업로드된 이미지 중 고르기」를 줄 수 있는가(신규 요구)다.
- ⟹ ⑴ 은 예외와 무관한 별개 사안, ⑵ 는 **새 요구**로 예외에 덮이지 않는다.

### 5-6. 수정 범위 초안

- ⑴ 겹침·배치 = `frontend/src/components/upload/upload.css`(스택 문맥·`.pvx-back` 격리) ＋ 필요 시 `frontend/src/components/upload/PreviewExpandOverlay.tsx`(포털 사용) — 실측 후 확정.
- ⑵ 「업로드된 이미지에서 고르기」 = 신규 기능. `RegisterArea.tsx` · `PreviewPickRow.tsx` · 계약 확인 필요(조각 목록에서 시각을 유도하는 경로가 이미 `describeTarget` 에 있는지). **계약 변경이 필요하면 동결 해제 서명 대상 — 착수 전 플래그.**
- 프런트 전용(⑴) / 미정(⑵).

### 5-7. red 테스트 후보

- 기존 파일 = `frontend/test/upload.test.tsx`(`reg-period-open` 참조) · `frontend/test/interval-period-20260906.test.tsx` · `frontend/test/period-open-ended.test.ts`.
- 첫 실패 테스트 ⑴ = 「확장보기가 열려 있는 동안 `reg-period-open` 이 `inert`/`aria-hidden` 아래 있거나 오버레이보다 뒤에 그려진다」 — jsdom 이 페인트 순서를 주지 않으므로 **DOM 격리 단언**(오버레이가 `document.body` 직속 포털) 또는 **CSS 원문 계측**으로 세운다.
- ⑵ 는 요구가 확정되기 전에는 테스트를 세우지 않는다.

### 5-8. 겹침·순서 의존

- **B군(`#31`·`#24`)이 `RegisterArea.tsx` 를 소유한다** ⟹ 같은 파일. **병렬 금지.**
- `upload.css` 는 C군 다른 이슈(`#28`)와도 겹친다 ⟹ C군 안에서도 직렬.
- 권고 = ⑴ 은 C군 배치 레인에 붙이고(`upload.css` 한 파일), `RegisterArea.tsx` 를 실제로 고쳐야 하면 B군 레인 뒤로 돌린다.

### 5-9. 범위 판정 후보

- ⑴ 겹침·배치 = **`v2 버그`.** 다른 화면의 입력 컨트롤이 미리보기 위에 표시되는 것은 표시 결함이다.
- ⑵ 「업로드된 이미지에서 고르기」 = **`편의 기능(후일 묶음)`.** 근거 = `colab-rules.md §6-2` 의 편의 기능 정의(추천·재사용·스마트 기본값·자동 매칭·단축 경로)에 「기간을 이미지에서 유도해 고르게 한다」가 든다. 기간 입력의 정문(달력)이 이미 있고 기능·정합성이 아니라 입력 편의다. 대화형 UI 도입은 아니다.

### 5-10. 크기

- ⑴ = 파일 1~2 · 추정 5~20행 ＋ 실측 1회.
- ⑵ = 미산정(요구 미확정).

### 5-11. 대장 대조

- `dev-package/work-items.yaml` — `id: WU-C1` / `status: done` · `id: WU-C3` / `status: done`.
- 기간 달력 팝오버를 세운 항목 = `WU-C8` 계열로 코드 주석이 지목한다(`RegisterArea.tsx` 앵커 「㈏ 달력 팝오버 (R-A′ 이관 · PRD-18 · WU-C8 §5-14)」). 대장의 `id: WU-C8` 행은 이번 조사에서 확인하지 않음 `[미확인]`.

---

## 6. 군 요약표

| 이슈 | 판정 후보 | 크기(파일 · 행) | 겹치는 파일 | 병렬 가능 여부 |
|---|---|---|---|---|
| #26 이미지 중복 표시 | `v2 버그` | 2 · 5~15 | `PreviewPanel.tsx` · `upload.css` | C군 내 불가 / A·B군과 가능 |
| #27 컨트롤 위치(인라인) | `v2 버그` 후보 (배치 요구분은 편의 기능) | 2~4 · 30~60 | `PreviewPanel.tsx` · `preview.css` · `PreviewPanels.tsx` | C군 내 불가 / A·B군과 가능 |
| #28 컨트롤 위치(확장보기) | `v2 버그` 후보 (고정 배치는 Ted 판정) | 2~3 · 20~40 | `PreviewPanel.tsx` · `upload.css` · `preview.css` | #27 과 **한 레인** |
| #25 ⑵ 고르개 자리 | `v2 버그` | 2~3 · 20~40 | `PreviewPanel.tsx` · `preview.css` · `DatasetPreviewSection.tsx` | C군 내 불가 |
| #25 ⑴ 렌더 지연 | 실측 후 판정 | 미산정 | `UploadModal.tsx` · `services/viz-render` | A·B군과 **불가**(같은 파일) |
| #29 ⑴ 기간 칸 겹침 | `v2 버그` | 1~2 · 5~20 | `upload.css` · `PreviewExpandOverlay.tsx` | C군 내 불가 |
| #29 ⑵ 이미지에서 기간 고르기 | `편의 기능(후일 묶음)` | 미산정 | `RegisterArea.tsx` | B군과 **불가** |

- **계수 기준** = 「겹치는 파일」은 수정 범위 초안에 적은 파일만 센다(읽기만 하는 파일 제외). 「크기」는 이 조사의 앵커 대조에 기반한 추정이고 실측 아님.

---

## 7. 레인 분할 제안

### 7-1. 레인 C-1 — 미리보기 상자 배치 (직렬 · 한 레인 · 최우선)

- 대상 = `#26` · `#27` · `#28` · `#25` ⑵
- 파일 = `frontend/src/components/upload/PreviewPanel.tsx` · `frontend/src/components/preview/preview.css` · `frontend/src/components/upload/upload.css` · `frontend/src/components/preview/PreviewZoomControls.tsx`
- 근거 = 네 건이 「4:3 고정 상자 안 세로 흐름」이라는 한 구조에서 나오고, 같은 4개 파일을 만진다. 나누면 같은 줄을 서로 다른 자리로 옮기는 충돌이 난다.
- 순서 = ① `#26`(축소본 제거 — 가장 좁다) → ② `#25` ⑵(고르개를 틀 밖 고정 줄로) → ③ `#27`＋`#28`(확대 줄을 뷰포트 안 절대 배치 · 세 화면 동시)
- 진입조건 = `WU-C4` 완료 정의 「세 화면 공유」를 깨지 않는다는 확인. 상세 화면(`PreviewPanels.tsx`·`DatasetPreviewSection.tsx`) 회귀 시험 포함.

### 7-2. 레인 C-2 — 렌더 지연 실측 (읽기 전용 선행 · C-1 과 병렬 가능)

- 대상 = `#25` ⑴
- 산출 = 렌더 소요 실측값 · `createRender` 호출 횟수 · 재마운트 발생 여부
- 근거 = 원인 위치(서버 vs 화면)가 갈리지 않아 수정 레인을 열 수 없다. 실측 단계는 파일을 고치지 않으므로 C-1 과 병렬 가능.
- 수정 단계는 A·B군과 `UploadModal.tsx` 를 공유하므로 **그 두 군이 끝난 뒤**에만 연다.

### 7-3. 레인 C-3 — 기간 칸 겹침 (B군 뒤 · 조건부)

- 대상 = `#29` ⑴
- `upload.css` 만 고치면 C-1 에 합류(같은 파일). `RegisterArea.tsx`·`PreviewExpandOverlay.tsx` 를 고쳐야 하면 B군 완료 후 별도 레인.
- 판정 입력 = 7-2 와 같은 브라우저 실측 1회에 함께 잰다(스택 문맥 · 뷰포트 폭).

### 7-4. `#29` ⑵ — 레인을 열지 않는다

- 「업로드된 이미지에서 기간 고르기」는 편의 기능 후보이고 요구가 미확정이다. **Ted 판정 항목으로 올린다.**

---

## 8. 후속 항목 (이 조사에서 고치지 않고 적어 둔 것)

1. `dev-package/work-items.yaml` — `WU-A10`·`WU-C8` 행 확인 미실시 `[미확인]`. #26·#29 의 소유 항목 대조에 필요.
2. 브라우저 실측 3건 미실시 — ⑴ 렌더 소요 ⑵ 확장보기 스택 문맥 ⑶ `.pv-frame-in` 스크롤 실제 발생. 전부 `[미확인]`.
3. `services/viz-render` 쪽 축소본 중복 생성 여부(#26 가설 B) 미조사.
4. `PreviewZoomControls` 가 부모의 flex 방향에 따라 두 자리로 갈리는 것은 공용 컴포넌트 설계 문제다 — 개별 이슈 수정과 별개로 배치 규칙을 컴포넌트가 쥐게 할지 검토 필요.
5. `#27` 의 「칸 자체가 움직인다」는 `.pv-layers .pv-tile { width: 100% }` 와 `.pv-viewport` 폭 상한 부재의 상호작용으로 보이나 미실측 `[미확인]`.
