# R-C-2 · 프론트 계층 — WU-C1 · C2 · C3 · C4 · C5 · C8 · C11 — spec: `dev-package/prd/specs/R-C.md` (출처 intent `dev-package/intent/2026-09-08-r-c.md` 우산 · `dev-package/intent/2026-09-08-preview-slot.md` 축 ①)

> ⛔ **착수 조건 = Ted 가 intent 2건을 커밋(승인) ＋ 21차 승인 문장 기입. 그 전에는 이 파일로 세션을 열지 않는다.**
> 이 파일 하나로 세션을 시작한다. 라운드 = **R-C** · 계층 = **FE** · WU **7건**(순서 고정 C1 → C2 → C3 → C4 → C5 → C8 → C11 · **직렬** — C1~C5 가 `PreviewPanel.tsx`·`DatasetPreviewSection.tsx`·`preview.css` 를 공유한다).
> 통합 브랜치 `integration/r-c` · 워크트리 `.claude/worktrees/r-c` · 기점 = `main` tip(해시를 박지 않는다 · `git rev-parse HEAD`).
> 이 파일은 계약을 **열지 않는다** — C3 이 쓰는 `describe` 는 `R-C-1` WU-C10 이 이미 병합한 21차 첨가분을 **소비**할 뿐이다. 마이그레이션 0.
> spec 우선(`prd/specs/README.md`). POL-021 부분 반전 〈N〉 은 **C5 가 낸다**(원문 무삭제).

---

## 0. 읽기 규칙 — 이 파일이 유일한 부트스트랩

> ⛔ **아래 4개를 통째로 열지 않는다.** `dev-package/03-HANDOFF.md` · `dev-package/PLAN-SoT.md` · `dev-package/work-items.yaml` · `dev-package/WORK-UNITS.md`

- **허용된 접근은 아래 세 줄뿐이다.**
  1. 결정 번호 최대값 — `bash dev-package/prd/tools/max-decision.sh`
  2. 대장에서 항목 하나 — `grep -n -A14 '^  - id: WU-C1' dev-package/work-items.yaml`
  3. 게이트 이름 확인 — `grep -n -A18 '^ALL_GATES=(' gates/run.sh`
- `03-HANDOFF.md` · `CLAUDE.md` · `RESTART.md` 는 **머리 부분만**. 요구 정본 = spec ＋ intent 2건 ＋ 이 파일. 축 ① 측정 원문이 필요하면 `intent/2026-09-08-preview-slot.md` 의 **해당 ①~⑤ 절만**.
- **코드 파일은 고칠 때만 연다.** 정찰은 `researcher` 위임. `path:line` 은 트리 `d969f34` 실측 — R-C-1 이 서버·계약을 고쳤으므로 FE 생성 타입은 **다시 잰다**. 못 재면 `[미상]`.

### 세션 시작
```bash
cd "<작업공간>/30 CoLAB-v2" && claude --add-dir "../40 COLAB-기획"
git -C .claude/worktrees/r-c rev-parse HEAD && git -C .claude/worktrees/r-c status --porcelain   # 0행
git -C .claude/worktrees/r-c log --oneline -1 -- contracts/seams/core-viz.yaml   # C3 착수 전: describe 첨가 커밋이 보여야 한다
```
- 에이전트 역할 — `advisor`(fable · ①·②) · `lane-worker`(opus · `isolation: "worktree"`) · `researcher`(sonnet) · `gate-runner`(haiku). 의존성은 H2 `worktree-setup.sh` 가 건다.

---

## 1. 확정 결정 — 다시 열지 않는다

다르게 구현할 사유를 찾으면 **고치지 말고 보고한다.** 기획자 회신 의존 **0건**.

- 2026-09-05 확정 16 · 2026-09-06 확정 12(존치 6종 축자 = `R-A2.md §1`) · 2026-09-08 R-B 61건(`R-B-ROUND-20260908.md §5`).
- **축 ① 16 판정(2026-09-08 Ted · `intent/2026-09-08-preview-slot.md ## 미해결 질문 → 판정`)** — 이 파일의 요구 문면이다:
  - 자리 = **장면2 진입 즉시 · 상세 열자마자** · PRD-260905:385(장면1 = 드롭존만) **무개정** · 틀 = `aspect-ratio` **4:3** · 4상태(idle·drawing·done·failed)에서 바깥 치수 불변.
  - 문면 **신설 0** — `UNAVAILABLE`(`PreviewPanel.tsx:22`)·`UnavailableNotice`·진행 3단계(`파일 읽는 중…`→`지도 그리는 중…`→`범례 만드는 중…`)·`아직 그리지 않았어요` 그대로. 새 문장이 필요하면 `[미상]` 으로 멈추고 보고.
  - 상세 = **좌 미리보기(sticky) · 우 기본 정보＋파일 · 계보·활용 아래 전폭 · 960px 미만 한 열(미리보기 먼저)** · `SectionMenu` 앵커 3개 무변 · 업로드 모달 배치 무변.
  - 500MB = **상한 유지 ＋ 첫 renderable 조각 자동 재요청**(`fileIds`) · 문면 원천 = `TOO_LARGE_MESSAGE` 둘째 문장 · 서버·상한값 무변.
  - 선택 = **파일·변수·시각** 세 드롭다운 · 기본값 = 서버 선택값(첫 renderable 파일 · `_pick_default` 변수 · 첫 시각)을 **표시** · 컴포넌트 상태(URL 미반영) · 업로드·상세 양쪽 · **바꿔 그리기**(한 번에 값 하나).
  - 축척 = **데이터 `bounds` 중심 ＋ 표준 축척 사다리 스냅**(Ted 원문 「다른지역이 나올수도있는데 데이터를 읽고 그걸 맞추지 못하나?」 — 한반도 고정 프레임 안 **철회**) · 단 값은 상수 한 자리(레인 실측 · 후보 100·300·1,000·3,000·10,000 km) · 세 화면 공유 `useZoomPan`/`.pv-zoom` · 작은 유역 = 외곽선 ＋ 더블클릭 맞춤 · 비지도형 현행.
  - 배경 = **자립형 Natural Earth 1:110m 해안선＋국경** · 도시 없음 · 외부 요청 0 · 500KB 상한(초과 시 간략화) · **POL-021 부분 반전**(타일 서버·CDN 금지 유지) ＋ PLAN-SoT ㉴ 「B-2 미채택」 반전 → 〈N〉.
- R-B 판정 중 이 파일이 쓰는 것 — §5-14 **기간 인라인 칸 철거** · §5-16 `VISIBILITIES` 3값 · §5-28 **Lv0 출처 안내 사람 Lv 기준** · §5-31 400 표면화 · §5-43 **빈 상태 3문면 권한 무관** · §5-45 `.lvl-3` = **Lv2 보다 한 단 진한 같은 계열** · §5-46·47·48·49.
- 존치 6종(`R-A2.md §1` 축자) ＋ 확장보기 ＋ 격자 업로드 블록 — **걷지 않는다**. 회귀 시험도 철거하지 않는다.

---

## 2. 범위 — 이 파일의 WU 7건

### WU-C1 · 미리보기 자리 선점 4:3 틀 (축 ① · 업로드＋상세) — 계층 FE · 크기 M · 레인 `rc-preview-slot`

- **의존**: 없음(FE 안에서 맨 앞). 계약 0.
- **현재 코드** — `frontend/src/components/upload/upload.css:168-169`(`.mapcanvas { margin-top }` · `.tile { max-width:100% }` — 높이·비율 0) · `preview.css:111-116`(`.pv-tile` max-width 뿐) · `PreviewPanel.tsx:234`(`.mapstage`) · `:462-467`(`.vizph` 「아직 그리지 않았어요」) · `:350-356`(진행 3단계 · `data-testid="up-preview-stage"`) · `:358-362`(`.vizerr`) · `DatasetPreviewSection.tsx:151-192`(컨테이너 즉시 마운트) · 소비 규약 한 자리 `:135-136`.
- **할 일** — `frontend/src/components/preview/` 에 **틀 컴포넌트 1개** 신설(`aspect-ratio: 4/3` · 상태별 내부 슬롯 export) → 업로드 `PreviewPanel`·상세 `DatasetPreviewSection` 이 그것을 쓴다. 장면2 진입 즉시·상세 열림 즉시 틀이 선다. 내부만 `.vizph` → 진행 3단계 → 그림/`.vizerr`(salvage 유지). 확장보기·격자 블록은 같은 컨테이너 안에 그대로.
- **수용 기준** — Given 파일 선택 직후(그리기 전), Then 틀 요소가 있고 `aspect-ratio` 4:3 · Given idle→drawing→done→failed 네 상태, Then 바깥 `getBoundingClientRect` 폭·높이 **불변**(4상태 건수 단언) · 상세 열림 직후 같은 틀 · 진행 문면 3단계·`UNAVAILABLE` 축자 유지 · 장면1 에 틀 **없음**(PRD-260905:385).
- **시험 seam** — `frontend/test/preview.test.tsx`(445행) · `upload-preview-poll-20260903.test.tsx` · `detail.test.tsx`.
- **좁은 게이트** — `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach`.

### WU-C2 · 데이터셋 상세 좌우 배치 (축 ①-②) — 계층 FE · 크기 M · 레인 `rc-detail-split`

- **의존**: WU-C1(틀이 좌측 열의 sticky 대상).
- **현재 코드** — `frontend/src/components/detail/detail.css:27`(`.detail-page { max-width:1200px }` · 좌우 grid 0) · `DatasetDetailPage.tsx:243`(`BasicInfoGrid`) → `:286`(`FileList`) → `:298`(`LineageSection`) → `:325`(`#sec-preview`) → `UsageSection` · `SectionMenu.tsx:10-12` 앵커 3개.
- **할 일** — grid 컨테이너 **한 겹**: 좌 = `#sec-preview`(sticky) · 우 = `BasicInfoGrid`＋`FileList` · 아래 전폭 = `LineageSection`·`UsageSection`. `@media (max-width: 959px)` 한 열 · 미리보기 먼저. 헤더·목록·`SectionMenu` 무변. 업로드 모달 무접촉.
- **수용 기준** — 1200px 에서 2열(좌 preview · 우 infogrid＋files · 2분기 단언) · 960px 미만 1열이고 preview 가 먼저 · `sec-lineage`·`sec-preview`·`sec-usage` 앵커 3개 존재 · `detail-section-menu.test.tsx` 회귀 green.
- **시험 seam** — `frontend/test/detail.test.tsx` · `detail-section-menu.test.tsx`.
- **좁은 게이트** — `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach`.

### WU-C3 · 500MB 조각 폴백 ＋ 파일·변수·시각 선택 UI (축 ①-③④) — 계층 FE(＋describe 소비) · 크기 L · 레인 `rc-preview-pick`

- **의존**: WU-C1 · **WU-C10(describe 계약 병합)** — 착수 전 `git log -- contracts/seams/core-viz.yaml` 로 확인.
- **현재 코드** — `PreviewPanel.tsx:140-144`(`createRender({ target:{uploadId}, style, withoutReferenceGrid })` · `fileIds`·`variable`·`instant` 0) · viz-render 413 `RENDER_TOO_LARGE`(`app/routes/renders.py:88,97` · `failures.py:54` 문면) · 계약 `core-viz.yaml:386-431`(`fileIds`·`variable`·`instant`) · 파일 목록 `fe-core.yaml:574`(`renderable`)·`:1070` · 소비 규약 `DatasetPreviewSection.tsx:135-136`(`usePreviewRender` 한 자리).
- **할 일** — ⑴ 폴백: `usePreviewRender` 한 자리에서 413 `RENDER_TOO_LARGE` 수신 → files 조회 → 첫 `renderable` → `fileIds:[그것]` 재요청 → 틀 안 문면(원천 = `TOO_LARGE_MESSAGE` 둘째 문장 ＋ 조각 이름) ⑵ 선택: 틀 안 컨트롤 줄에 파일·변수·시각 드롭다운 3개(목록 = files 조회 ＋ describe 응답) · 바꾸면 `fileIds`/`variable`/`instant` 를 실어 **바꿔 그리기** · 기본값 = describe 의 서버 기본값을 표시 · 컴포넌트 상태 · 업로드·상세 양쪽.
- **수용 기준** — 413 픽스처 → files 조회 1회 → `createRender` 스파이 호출 **2회** · 두 번째 인자 `target.fileIds` 길이 1 · 드롭다운 3개 · 변수 바꾸면 `variable` 송신 · 시각 바꾸면 `instant` 송신 · 기본값 표시 문자열 = describe 응답값 · describe 배열 길이 ≥1 단언 · 한 번에 값 하나(겹쳐 그리기 0).
- **시험 seam** — `frontend/test/preview.test.tsx` · `upload-preview-poll-20260903.test.tsx` · 새 픽스처(413 · describe).
- **좁은 게이트** — `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `e2e-format-coverage`.

### WU-C4 · 축척 사다리 ＋ 공유 확대/축소 세 화면 (축 ①-⑤a) — 계층 FE · 크기 M · 레인 `rc-scale-ladder`

- **의존**: WU-C1 · WU-C3(컨트롤 줄 공유).
- **현재 코드** — `frontend/src/components/preview/useZoomPan.ts:65`(`useZoomPan()` · 상세만) · `preview.css:208-224`(`.pv-zoom`) · 확장보기 `PreviewExpandOverlay.tsx:29-58`(모달 껍데기 · 배율 0) · `PreviewPanels.tsx:169-201`(`pvLonOf`/`pvLatOf` · `bounds` 역산) · 서버 `bounds` = `jobs.py:188`.
- **할 일** — 사다리 상수 **한 파일 한 자리**(`frontend/src/components/preview/` · 값은 레인이 staging 실물 `bounds` 분포로 실측해 확정 · 후보 5단 100·300·1,000·3,000·10,000 km · spec 우려 1) · `useZoomPan` 에 스냅(데이터 폭을 담는 최소 단) ＋ 더블클릭 `bounds` 맞춤 ＋ 외곽선 사각형 추가 · 업로드 `PreviewPanel`·확장보기 오버레이가 같은 훅＋`.pv-zoom` 을 쓴다 · 비지도형은 현행.
- **수용 기준** — `bounds` 폭 W 에 대해 스냅 단 = W 를 담는 최소 단(사다리 **전 단 각 1건** · 상수 길이 단언) · 세 화면에서 `.pv-zoom` 버튼 3개 · 더블클릭 → `bounds` 맞춤 · 비지도형 회귀 green(`dataset-preview-zoom.test.tsx` 304행).
- **좁은 게이트** — `frontend-typecheck` · `frontend-test` · `render-latency`(회귀 확인).

### WU-C5 · 자립형 배경 지도 (축 ①-⑤b · POL-021 부분 반전) — 계층 FE 자산 · 크기 M · 레인 `rc-basemap`

- **의존**: WU-C4(좌표계·배율 공유).
- **현재 코드** — geo 자산·라이브러리 **0건**(`frontend/package.json` · `frontend/src` · `services/viz-render/requirements.txt` rasterio 만) · POL-021 원문 `PLAN-SoT.md:591`·`WORK-UNITS.md:425`·`CLAUDE.md:19`(`〈240〉`) · PLAN-SoT ㉴ 「B-2 해안선 오버레이 미채택」(`:660`).
- **할 일** — `frontend/src/assets/basemap/` 에 Natural Earth 1:110m 해안선＋국경 GeoJSON(Public Domain · 출처·버전·간략화 절차를 같은 폴더 README 에 · 실크기 실측 · 500KB 초과 시 간략화) · 배경 SVG 컴포넌트 1개(`bounds` 있을 때만 · `pvLonOf`/`pvLatOf` 와 같은 좌표계 · 래스터 아래) · 세 화면 공용. ⛔ 타일 서버·외부 CDN·지도 라이브러리 반입 0.
- **수용 기준** — `bounds` 있는 결과에 배경 SVG **1개** · 없는 결과 **0개** · 자산 파일 존재＋크기 ≤ 500KB 를 **시험이 센다** · 네트워크 요청 0(fetch 스파이 호출 0) · 도시 표기 0.
- **〈N〉 초안(병합 직전 R-C-3 에서 등재)** — 「POL-021 「타일 서버도 바탕 지도도 쓰지 않는다」 **부분 반전** — 자립형 벡터 배경(레포 반입 · 외부 요청 0)만 허용 · 타일 서버·CDN 금지 유지 · ㉴ 「B-2 해안선 오버레이 미채택」 반전 · Ted 2026-09-08 「자립형 벡터 해안선 · POL-021 부분 반전」」. ⛔ 원문 문단은 지우지 않고 덧붙인다.
- **좁은 게이트** — `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach` · `exec-bit`(자산 파일 비트).

### WU-C8 · FE 소형 5건 (질의 14·16·28·31·43) — 계층 FE · 크기 M · 레인 `rc-fe-fix`

- **의존**: WU-C9(사람 값 표시 함수 — R-C-1) · C1~C5 뒤(같은 CSS 파일 접촉 순서).
- **현재 코드** — `frontend/src/components/lab/LabInfoPanel.tsx:30`(`VISIBILITIES = ['열림','잠김']` · `:207` 렌더) · `UploadModal.tsx:844`(`catch` 가 400 message 를 일반 문구로 덮음) · `RegisterArea.tsx:341`(「종전 인라인 칸은 그대로 산다」) · `BasicInfoGrid.tsx:114`(Lv0 안내 = 파생 Lv 기준) · `detail/format.ts:16` · `LineageSection.tsx:316,323`(`canEdit` 분기 안 3문면 중 1).
- **할 일** — `VISIBILITIES` 3값(`지정 공개` 추가 · 계약 `LabDefaultVisibility` 는 이미 3값) · `submit` catch 를 400(서버 message 그대로) ↔ 그 외(일반 문구) 로 가른다 · 인라인 기간 칸 철거(팝오버 하나만 · §5-14) · Lv0 안내를 **사람 Lv** 기준으로 · 「원자료(Lv0)…」 문면을 `canEdit` 밖으로.
- **수용 기준** — 셀렉트 옵션 3 · 서버 400 문면이 그대로 뜨고 500 은 일반 문구 · 인라인 기간 칸 0개＋팝오버 1개 · 사람 Lv0＋파생≠0 행에 안내가 뜬다 · `canEdit=false` 계정도 3문면.
- **좁은 게이트** — `frontend-typecheck` · `frontend-test` · `frontend-fixture-reach`.

### WU-C11 · CSS 잔여 (질의 45·46·47·48·49) — 계층 FE·CSS · 크기 S · 레인 `rc-css-residual`

- **의존**: C1~C8 전부 뒤(같은 CSS 를 마지막에 만진다 — 앞서 돌면 재작성으로 지워진다).
- **현재 코드** — `frontend/src/components/catalog/catalog.css:127-129`(`.lvl-0`~`.lvl-2` · `.lvl-3` 부재) · `:137`(`.lin--none` gray-400 · 3.41:1) · `detail.css:134`(`.dt-gridact margin: -8px …`) · `upload.css` 자식 `margin-top` 9곳(`:147,150,159,166,168,170,191,234-237,243,251` — C1 이 `.mapcanvas:168` 을 고치므로 **재측정**) · `lineageGraph.css:7`(`.detail-page .dsec { margin-top }` · 부모 무클래스 · TSX 필요) · 코랄 액센트 = 목업 `:root` 회수 조건부.
- **할 일** — `.lvl-3`(Lv2 보다 한 단 진한 같은 계열 · 판정 축자) · `.lin--none` ≥ 4.5:1 · `.dt-gridact` 음수 제거 · `margin-top` 9곳 → 컨테이너 gap · `.dsec` 부모 클래스(TSX 1곳) · 코랄은 목업 `:root` 가 회수돼 있을 때만(없으면 `[미상]` 보고 · 고치지 않는다).
- **수용 기준** — grep 계측: `.lvl-3` 존재＋대비 AA · `.lin--none` ≥ 4.5:1 · `.dt-gridact` 음수 margin 0 · `upload.css` 자식 `margin-top` 0곳 · `.dsec` 부모 클래스 존재 · 미정의 토큰 참조 0건(B11 회귀).
- **좁은 게이트** — `frontend-typecheck` · `frontend-test`.

---

## 3. 지켜야 하는 규약 — 명령으로

### ㉮ 워크트리 레인
- WU 하나에 레인 하나 = `rc-preview-slot`(C1) · `rc-detail-split`(C2) · `rc-preview-pick`(C3) · `rc-scale-ladder`(C4) · `rc-basemap`(C5) · `rc-fe-fix`(C8) · `rc-css-residual`(C11). 통합 브랜치에서 딴 자기 워크트리 · ff 병합 · **직렬**(`rules §3-1` 같은 파일 병렬 금지).

### ㉯ 착수 전 — `work-items.yaml` 등재는 **이미 끝났다**
- 확인 = `grep -n -A14 '^  - id: WU-C1' dev-package/work-items.yaml`. 완료 시 `status: done` ＋ `evidence`. `bash gates/run.sh work-item-consistency` green.

### ㉰ 계약 동결 해제 — **이 파일은 쓰지 않는다**
- ⛔ `contracts/` 무접촉. C3 은 C10 이 병합한 describe 를 **소비**한다. 없는 열쇠가 필요하면 **고치지 말고 보고한다**(21차 패키지 밖 = 22차 사안).

### ㉱ 결정 번호 〈N〉 — 예약하지 않는다
```bash
git fetch origin main && bash dev-package/prd/tools/max-decision.sh   # 병합 직전에 다시 잰다
```
- 착수 시점 참고값 = **〈374〉**(2026-09-08 · 근거 아님). C5 의 POL-021 반전 행은 `R-C-3-verify.md ㉱` 문안으로 병합 직전 등재. ⛔ HANDOFF 에 값을 적지 않는다.

### ㉲ 게이트 — 작업 중엔 단독, 라운드 끝엔 전건
```bash
COLAB_GATE_REPORT_DIR=dev-package/reports/R-C/<레인> ./gates/run.sh frontend-typecheck
COLAB_GATE_REPORT_DIR=dev-package/reports/R-C/<레인> ./gates/run.sh frontend-test
COLAB_GATE_REPORT_DIR=dev-package/reports/R-C/<레인> ./gates/run.sh frontend-fixture-reach   # C1·C2·C3·C5·C8
./gates/run.sh render-latency                                                                  # C4
./gates/run.sh e2e-format-coverage                                                             # C3
```
- ⛔ 게이트를 끄거나 대상을 줄이지 않는다 · 구현 전 **red 를 눈으로 확인** · 상태·분기·상수 **건수를 단언**(green-by-skip 방지).

### ㉳ 커밋 문면
```
FE R-C-2 <WU 제목> (WU-C_)

- <바뀐 자리 1~3줄 · 문면 신설 0 / 원천 축자>
- 계약 0 · 스키마 0 · 마이그레이션 0 (C5: POL-021 부분 반전 〈N〉 병합 직전 등재)
- RED 선실측 → GREEN: <시험 파일>:<건수>
```

### ㉴ 금지
- ⛔ `main` 직접 push · ⛔ `contracts/` 수정 · ⛔ 마이그레이션 · ⛔ 새 문면 짓기(`[미상]` 보고) · ⛔ PRD-260905:385 개정(장면1 에 틀).
- ⛔ 존치 6종·확장보기·격자 블록 제거 · ⛔ 타일 서버·CDN·지도 라이브러리 반입 · ⛔ 도시 표기 · ⛔ 겹쳐 그리기.
- ⛔ 한반도 고정 프레임(Ted 철회) · ⛔ 사다리 값 하드코드 재정의(상수 한 자리) · ⛔ 코랄 액센트를 목업 `:root` 없이 복원.
- ⛔ 이 세션이 `03-HANDOFF.md` 본문을 직접 고치기 · ⛔ `40 COLAB-기획/` 수정 · ⛔ 문서·주석에 절대경로.

---

## 4. 산출물과 근거

| 무엇 | 어디 |
|---|---|
| 틀·배경·사다리 | `frontend/src/components/preview/` — 틀 컴포넌트 1 · 배경 SVG 1 · 사다리 상수 1 · `useZoomPan.ts` 증보 |
| 자산 | `frontend/src/assets/basemap/` — NE 1:110m GeoJSON ＋ README(출처·버전·크기·간략화) |
| 업로드·상세 | `PreviewPanel.tsx` · `DatasetPreviewSection.tsx` · `DatasetDetailPage.tsx` · `PreviewExpandOverlay.tsx` · `detail.css` · `upload.css` · `preview.css` |
| 소형·CSS | `LabInfoPanel.tsx` · `UploadModal.tsx` · `RegisterArea.tsx` · `BasicInfoGrid.tsx` · `LineageSection.tsx` · `catalog.css` · `lineageGraph.css` |
| 세션 노트 | `dev-package/sessions/rc-<레인>-<YYYYMMDD>.md` × 7 — 각 ≤ 60행 · 사다리 실측 분포 · NE 실크기 |
| 대장 | `work-items.yaml` — 7 블록 완료 시 `done` ＋ `evidence` |

**HANDOFF 갱신문(오케스트레이터가 붙인다 · 5줄 이하)**
```
R-C-2(FE) 완료 — WU-C1·C2·C3·C4·C5·C8·C11, 레인 rc-preview-slot … rc-css-residual, 병합 <sha>
틀 4:3 · 상세 좌우 · 500MB 조각 폴백 · 파일·변수·시각 선택 · 사다리 <단 값 실측> · NE 배경 <KB 실측> · 계약 0 · 마이그레이션 0
게이트: frontend-typecheck·frontend-test·frontend-fixture-reach green · FE 시험 <n>
POL-021 부분 반전 〈N〉 초안 → R-C-3 에서 등재 · 코랄 복원 <집행/미상>
다음 = R-C-3-verify.md(C12 · 전수 게이트 · 병합 · 등재)
```

---

## 5. 완료 판정

- **C1** 4상태 치수 불변 · 장면1 틀 없음 · 문면 신설 0. **C2** 2열/1열 분기 · 앵커 3. **C3** 스파이 2회 · `fileIds` 1 · 드롭다운 3 · `variable`/`instant` 송신. **C4** 전 단 스냅 · `.pv-zoom` 세 화면 · 더블클릭 맞춤. **C5** SVG 1/0 · ≤500KB 계측 · 네트워크 0. **C8** 5건 수용 기준 전부. **C11** grep 계측 5항 ＋ 토큰 0건.
- **게이트** — 각 레인 좁은 집합 green ＋ `gate-summary.json` 배출 · advisor ② 가 intent `원한 결과` 1~10 미달·초과를 열거.
- **절차** — `contracts/` 무접촉이 diff 로 보인다 · 사다리 값·NE 크기가 세션 노트에 **실측값**으로 있다(`[미측정]` 잔존 0).

### 다음 파일
`dev-package/prd/rounds/R-C-3-verify.md`(C12 ＋ R-C 종료 검증 · 병합 · 〈N〉 3행 등재).
