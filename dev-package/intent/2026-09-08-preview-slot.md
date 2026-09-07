# Intent: 미리보기 5건 — 자리 선점·좌우 배치·500MB 초과·대상 선택·축척 기준

⛔ **초안 · R-C 축 ① · grill-me 2026-09-08 완료(프론티어 공집합) · Ted 커밋 전 정본 아님**

- 발의자: Ted (구두 발의 2026-09-08, 4건 순차 추가)
- 작성일: 2026-09-08
- 승인: 미승인
- 상위 intent: `dev-package/intent/2026-09-08-r-c.md`(R-C 우산 · 축 ② R-B 후속 포함)

---

## 문제

### ① 미리보기 자리 선점 (원 발의, verbatim)

> 미리보기가 완성되면 화면에 띄우는데, 이미 공간은 갖고 있어야 하고, 미리보기 보여지는거에서 프로그레스처럼 읽는중.. 범례확보 등 (지금 띄우는 표현) 실행됨을 노티하는 것이 있어야하며, 못그린다면 지금 못그린다는 표현 해도 된다. 핵심은 미리보기 화면이 완성되면 나타나는게 아니라, 이미 공간을 할당 받아야 한다.

**측정 — 업로드 모달(장면2 좌측)**

- `PreviewPanel`(`frontend/src/components/upload/PreviewPanel.tsx`)은 파일을 하나도 고르지 않은 장면1에는 아예 마운트되지 않는다 — `UploadModal.tsx:1008-1010` 이 `{picked.length > 0 && (<div className="up-split">…<PreviewPanel …/>…)}` 로 좌우 2단 자체를 파일 선택 뒤에만 그린다. PRD 도 같은 상태를 정본으로 못박는다 — `dev-package/prd/PRD-260905-적용전기획.md:385` 「장면1 — 파일 없음. 드롭존만 크게 보인다. 등록 폼·미리보기는 화면에 없다.」
- 파일을 고른 뒤 `.mapstage`(`PreviewPanel.tsx:234`)는 마운트되지만 **고정 크기·비율 예약이 없다**. CSS(`frontend/src/components/upload/upload.css:81-84`)는 `.mapstage`에 `border`·`padding`만 주고 `min-height`·`aspect-ratio` 가 없다. `.mapcanvas`(그림 자리, `upload.css:168`)도 `margin-top: 12px` 뿐이고 이미지가 오면 그 순간 세로 길이가 늘어난다(레이아웃 점프).
- 미완성 상태에서 자리를 채우는 것은 팔레트·구간 수 컨트롤(`vizsetup`) ＋ 「미리보기 그리기」 버튼 ＋ (그리기를 누른 뒤) `.vizload` 진행줄 또는 `.vizph`(「아직 그리지 않았어요」, `PreviewPanel.tsx:462-467`)뿐이다. **그리기를 누르기 전에는 그림이 놓일 자리 자체가 얇다** — 컨트롤 줄과 안내 문구 두 줄 높이만 차지한다.
- 진행 문구(정본 §8 그대로, `PreviewPanel.tsx:1-4,350-356`) = `파일 읽는 중…` → `지도 그리는 중…` → `범례 만드는 중…`, 한 덩어리 「로딩 중」이 아니다. `role="status" aria-live="polite"`, `data-testid="up-preview-stage"`. 서버 값 원본 = `services/viz-render/src/colab_viz/domains/d7_visualization/jobs.py:35-40` `STAGE_READ`·`STAGE_DRAW`·`STAGE_LEGEND`·`STATUS_DRAWING`.
- 실패는 200+`failure`(HTTP 상태로 판정하지 않음, `PreviewPanel.tsx:9,175-176`). 못 그림 문구 기본값 = `PreviewPanel.tsx:22` `UNAVAILABLE = '지금 미리보기를 만들 수 없어요. 잠시 뒤 다시 시도해 주세요.'`, `.vizerr`(`role="alert" aria-live="assertive"`, `PreviewPanel.tsx:358-362`)로 표시. 실패해도 이미 구운 값 미리보기·썸네일은 감추지 않는다(`salvage`, `PreviewPanel.tsx:179-180,414-434`). **실패 시 영역이 접히지 않는다** — `.vizerr`가 컨트롤·썸네일 자리 아래에 추가로 얹힐 뿐 `.mapstage` 자체는 그대로 남는다.
- 팔레트 목록 조회 실패 시에도 같은 `UNAVAILABLE` 문구가 뜬다(`PreviewPanel.tsx:111-117`) — 「그릴 수 없는 것과 등록할 수 없는 것은 다르다」는 주석대로 등록 경로는 막지 않는다.

**측정 — 데이터셋 상세**

- `DatasetPreviewSection`(`frontend/src/components/datasetpreview/DatasetPreviewSection.tsx`)은 상세 페이지가 열리는 즉시 `<section className="dt-preview">`가 마운트되고(`:151-192`), 그 안에서 `start.phase`(`시작하는 중`→`시작함`/`그릴 수 없음`/`만들 수 없음`)로 갈린다. `시작하는 중`에는 `RenderStageNotice()`(단계 문구 없는 기본형, `frontend/src/components/preview/PreviewPanels.tsx`)가 뜬다. **업로드 모달과 달리 컨테이너 자체는 열자마자 선다** — 다만 그 안 요소들(문구·그림)의 높이가 폭 대비 고정돼 있는지는 `detail.css`가 아니라 `frontend/src/components/preview/preview.css`가 쥐고 있고, 이번 조사에서 `preview.css`의 `.pv-*` 고정 높이 규칙은 확인하지 못했다(`[미확인]`).
- 렌더가 `시작함`으로 넘어간 뒤에만 `StartedPreview`가 마운트되고, 그 안에서 `그리는 중`(`RenderStageNotice(stage)`) → `완료`(`PreviewMap`) → `실패`(`RenderFailureNotice`) → `그릴 수 없음`(`NotRenderableNotice`) → `만들 수 없음`/`만료됨`(`UnavailableNotice`)로 분기한다(`DatasetPreviewSection.tsx:275-312`). 소비 규약은 업로드와 **한 자리**(`usePreviewRender`)를 공유한다(`:135-136` 주석 — 「S-08 과 두 벌로 두면 두 화면의 판정이 갈린다」).
- 못 그림 문구 = `UnavailableNotice`(`:210-217`)가 서버 메시지 + 「다운로드·계보 확인은 그대로 할 수 있어요.」를 `role="alert" aria-live="assertive"`로 낸다.

**측정 — PRD·존치 제약**

- `PRD-260905-적용전기획.md:386,392` 및 `dev-package/prd/rounds/R-B-3-frontend.md:71,133`가 이미 「장면2 = 좌측 미리보기 ＋ 우측 등록 3단계」를 확정했고, 존치 규칙(§0.3-5, `R-B-3-frontend.md:71`)이 2단 등록 게이트·기준 격자 파일 흐름·이어올리기 배너를 「걷지 않는다」로 못박는다. `PreviewPanel`의 격자 업로드 블록(`gridFlow.ts`/`GridUploadBlock`, `PreviewPanel.tsx:444-460`)과 확장보기(㈎, `PreviewExpandOverlay` · `:472-482`)는 같은 컨테이너 안에 공존하며, 이번 intent 로 자리를 옮기지 않는다.
- Ted 의 발의는 이 존치 배치와 충돌하지 않는다 — 요구는 「자리가 그리기 완료 전에 이미 확보돼 있어야 한다」이지 배치를 바꾸라는 것이 아니다. 다만 **장면1(파일 없음)에는 미리보기 자리 자체가 없다**는 현재 정본(PRD-260905:385)과, 「이미 공간을 할당 받아야 한다」는 이번 발의가 어느 시점부터 충돌하는지는 미해결(아래 참조).

---

### ② 좌 이미지·우 정보 배치 (verbatim)

> 두번째는, 왼쓪에 이미지 보여주고 관련정보는 우측에 위치해야할걸?

**측정 — 업로드 모달**: 이미 좌-미리보기·우-등록 구조다. `UploadModal.tsx:1008-1010` `up-split`(그리드, `upload.css:74-79` `display: grid`) 안에 `up-split-preview`(좌)·`up-split-form`(우, 등록 3단계)이 나란히 선다. PRD 정본(`PRD-260905-적용전기획.md:386,392`, `R-B-3-frontend.md:71`)이 이 배치를 이미 확정값으로 적는다. **업로드 모달은 이미 요구를 충족한다.**

**측정 — 데이터셋 상세**: 반대다. `DatasetDetailPage.tsx:104` `BasicInfoGrid`(기본 정보, 3열 그리드 `.infogrid`, `detail.css:64-80`)가 먼저 세로로 서고, `:186-187` `<div id="sec-preview">…<DatasetPreviewSection …/>` 가 그 아래에 **한 열로 이어진다**. `detail.css:27` `.detail-page { max-width: 1200px; margin: 0 auto; }` 하나로 전체가 세로 단일 컬럼이고, 미리보기와 기본 정보를 좌우로 가르는 grid/flex 규칙은 이번 조사에서 찾지 못했다(부재 확인 근거 = `grep -n "d-main\|d-grid\|grid-template-columns" detail.css` 결과에 `.infogrid` 내부 3열 하나뿐). 즉 **상세 페이지는 위-아래 배치이지 좌-우 배치가 아니다.**

---

### ③ 500MB 초과 파일도 그려 달라 (verbatim)

> 500 mb 넘는것도 그려달라.

**측정**: 상한이 실재한다.
- `services/viz-render/src/colab_viz/domains/d7_visualization/failures.py:53-54` — `TOO_LARGE_MESSAGE = "미리보기는 500MB까지 그려요. 조각 하나를 골라 그려 보세요."`, 주석에 `[가정]` 표식이 붙어 있다(정본 확정치가 아니라 개발측 가정).
- `services/viz-render/src/colab_viz/kernel/config.py:63` 같은 자리 주석 — 「정본 `Policy_데이터셋_상세 §8` — 「미리보기는 500MB까지 그려요」 **[가정]**.」, 값 자체는 하드코드 500이 아니라 환경변수 `COLAB_VIZ_WORK_MAX_BYTES`(`config.py:143`)로 주입 — `parse_work_max_bytes()`(`:219-230`)가 바이트 정수 또는 `none`(명시 무제한)을 받는다.
- 강제 지점 = `services/viz-render/src/colab_viz/ports/source.py:169-183,226-228` `S3SourcePort` — 대상 다운로드 시 `need > self.max_bytes` 면 `대상 {target_id} 가 {need} B 로 작업 디렉터리 상한 {max_bytes} 를 넘는다` 로 거절. 이유는 **작업 디렉터리(디스크) 용량 상한**이지 메모리·타임아웃이 1차 근거로 명시돼 있지 않다 — 「렌더마다 다시 읽는 비용을 아직 안 쟀다 `[미측정]`」(`source_digest.py:3`)이 인접 주석.
- 복구 경로는 이미 계약에 있다 — `contracts/seams/core-viz.yaml:398-404` `RenderTarget.fileIds` — 「조각 하나만 골라 그리는 복구 경로가 여기로 온다」. 즉 500MB 초과일 때 **전체 대신 조각(파일) 하나를 골라 다시 요청하는 길은 이미 계약에 있고**, 그 조각 선택 UI 는 ④ 항목과 겹친다(아래).
- `COLAB_VIZ_WORK_MAX_BYTES` 실제 배포값(개발/스테이징)은 이번 조사에서 확인하지 못했다(`[미확인]`) — `test_source_mode_env.py:25`의 시험값은 `1073741824`(=1GiB)이지만 이것이 운영값이라는 근거는 없다.

---

### ④ 그릴 대상(파일·변수·시점) 선택 UI 부재 (verbatim)

> 그리고 보고자하는 이미지 미리보기 선택하는게 있어야하는데 그것도 없다

**측정**: 선택 UI가 실제로 없다.
- `PreviewPanel.tsx`·`DatasetPreviewSection.tsx` 전문을 읽은 결과 팔레트(`select`)·구간 수(`input number`) 두 컨트롤뿐이고, 파일·변수·시점을 고르는 드롭다운·탭·썸네일열은 없다(`grep -n "fileIds\|variable" frontend/src/components/upload/*.ts* frontend/src/components/datasetpreview/*.ts* frontend/src/components/preview/*.ts*` 결과 — FE 는 `variable`을 **응답에서 읽기만** 한다. `preview/types.ts:26` `variable?: string`은 완료된 렌더의 `legend.variable`에서만 채워진다는 주석, `PreviewPanels.tsx:348-351`이 그 값을 배지처럼 표시할 뿐 선택 입력이 아니다).
- 계약은 이미 선택 축 둘을 갖고 있다 — `contracts/seams/core-viz.yaml:386-407` `RenderTarget.fileIds`(그릴 조각들, 생략 시 전체) · `:411-420` `RenderRequest.variable`(그릴 값 하나, 생략하면 viz-render 가 기본값을 고름 — 「core 가 파일의 변수 목록을 해석해」로 문장이 끊겨 있어 기본값 산출 규칙 원문은 이번 조사에서 끝까지 확인하지 못했다 `[미확인]`). **시점(time step)을 고르는 별도 파라미터는 이번 grep 에서 찾지 못했다** — `variable`이 시점까지 포괄하는지, 아니면 시점 선택 축 자체가 계약에 없는지는 미해결.
- FE 가 그리기를 요청할 때 실제로 보내는 값 = `PreviewPanel.tsx:140-144` `source.createRender({ target: { uploadId }, style: { palette, classCount }, withoutReferenceGrid })` — `fileIds`·`variable` 어느 쪽도 실지 않는다. 즉 **서버는 이미 골라 받을 준비가 돼 있는데 화면이 아무것도 안 보낸다.**
- 선택지를 채울 목록 자체(「이 업로드/데이터셋에 그릴 수 있는 파일·변수 목록」)를 돌려주는 조회 엔드포인트는 `contracts/seams/core-viz.yaml`에서 찾지 못했다(`grep -n "variables:\|listVariables\|renderableVariables"` 결과 없음) — 있는 것은 `palettes()`(팔레트 목록)뿐이다. **선택 UI를 만들려면 최소한 그 목록을 돌려줄 자리가 계약에 있어야 하는데, 지금은 없다.**

---

### ⑤ 축척 기준 (verbatim, 3문장 순서대로)

> 사이즈가 미리보기 뒤죽박죽인데, 축적은 어느정도 우리시스템에서 기준을 갖고 가야하지 않을까? 각 화면에서 확대/축소/기본배율 뭐 이렇게 하고,
> 기본적으로 대한민국 나오고 중국 우측 좀 나오고 일본 간사이 쪽 까진 나오는 형태면 좋을거같은데
> 그냥 이정도의 축척
> 지도 레이어 반입은 왜빠져 배경해주면 좋을거같은데, 위치 축척 같은걸 데이터에서 뽑아낼수있지않아?

**측정 — 지금의 크기 결정 방식**: 시스템 기준 축척이 없다. 데이터셋 상세(`.pv-tile`, `preview.css:111-115`)와 업로드(`.mapcanvas .tile`, `upload.css:169`) 둘 다 `max-width: 100%`(상세는 `width:100%`도 추가, `preview.css:198-200` `.pv-layers .pv-tile`)로 **컨테이너 폭에 맞춰 늘어나는 상대 크기**다 — 원본 픽셀 수·지리 범위와 무관하게 화면 폭이 곧 배율이 된다. 이것이 Ted 가 첨부한 스크린샷의 「사이즈가 뒤죽박죽」 증상과 일치한다.

**측정 — 확대/축소·기본 배율 컨트롤**: 데이터셋 상세에만 있다. `useZoomPan`(`frontend/src/components/preview/useZoomPan.ts`)이 `scale`(초기값 1, `:67`)·`zoomIn`/`zoomOut`(`:114-126`)·`resetView`(`:130` 초기화)를 쥐고 있고, 한계 배율은 「데이터가 가진 실제 픽셀 수와 화면에 놓인 크기의 비」에서 정한다(`:9-10,17` 정본 §8 조건 ⑷, 수치 하드코드 금지). `.pv-zoom` 버튼(`preview.css:208-224`)이 그 조작 UI다. **업로드 모달에는 이 훅이 없다** — `PreviewPanel.tsx`는 확대 대신 `PreviewExpandOverlay`(㈎ 확장보기, `:238-248,472-482`)로 원본 이미지를 새 레이어에 크게 띄울 뿐, 그 안에도 배율 조절은 없다(오버레이 내부에 `<img className="pvx-img">` 하나, 자체 줌 없음).

**측정 — 지리 위치·축척 정보가 데이터에서 이미 나오는가(Ted 질문 「데이터에서 뽑아낼수있지않아?」에 대한 사실 확인)**: 그렇다. `services/viz-render/src/colab_viz/domains/d7_visualization/jobs.py:188` `result["bounds"] = a.geometry.bounds_dict()` — 지도형 결과에는 서버가 이미 서·남·동·북 경계값을 싣는다(`jobs.py:169` 주석 「③이 있으면 지도형 — `bounds`·사이드카·월드파일이 함께 간다」). FE 는 이 값을 이미 소비한다 — `pvLonOf`/`pvLatOf`(`frontend/src/components/preview/PreviewPanels.tsx:169-201`)가 화면 픽셀 오프셋을 `bounds`로 역산해 커서 위경도 HUD 를 그린다(`:276-277`). **즉 위치·축척을 데이터에서 뽑아내는 경로는 이미 있다** — 새 계약 열쇠 없이 `bounds`만으로 「이 래스터가 지도 위 어디에, 얼마만한 크기로 놓이는가」는 계산 가능하다. 다만 이것은 **지도형(③에 `bounds`가 실리는 경우)에 한정**되고, 비지도형(좌표 없는 값 미리보기)에는 적용되지 않는다.

**측정 — 배경 지도 레이어(해안선·국경) 존재 여부**: 없다. `grep -rn "coastline\|basemap\|natural.?earth\|geojson" frontend/src services/viz-render/src`(이번 조사 범위)에서 일치 없음 — 래스터 한 장만 그리고 그 위·아래에 배경 지도를 얹는 코드가 없다. `CLAUDE.md §0` stage 표가 「타일 서버도 바탕 지도도 쓰지 않는다」(POL-021)를 정본으로 적어 **현재는 바탕 지도 자체가 정책상 빠져 있다** — Ted 의 이번 요구가 그 정책을 다시 여는 요청인지 확인 필요(미해결 질문).

---

## 원한 결과 (proposed outcome)

1. 미리보기 자리는 파일이 놓이는(업로드) 또는 상세가 열리는(상세) 즉시 고정 크기로 선점된다 — 그리기 시작 전·진행 중·완료·실패 네 상태 전부에서 바깥 컨테이너의 가로·세로가 바뀌지 않는다(레이아웃 점프 0).
2. 완성 전에는 진행 단계가 그 자리 안에서 지금 쓰는 표현(`파일 읽는 중…`→`지도 그리는 중…`→`범례 만드는 중…`, `role="status" aria-live="polite"`)으로 보인다.
3. 못 그리면 그 자리에 명시 표현(문면 원천은 미해결 질문 참조, 현재 값 = `UNAVAILABLE`/`UnavailableNotice` 문구)이 뜬다.
4. 완성되면 같은 자리에 그림이 들어온다.
5. 데이터셋 상세에서 이미지가 좌, 기본 정보·계보 등 관련 정보가 우에 위치한다(반응형 폴백은 미해결 질문). 업로드 모달은 이미 이 배치이므로 변경 대상에서 제외한다.
6. 500MB를 넘는 파일도 미리보기가 그려진다 — 전량을 한 번에 읽어 그리는 방식이든, 조각(파일) 단위로 나눠 그리는 방식이든 사용자에게는 「그려진다」로 도달한다. 시간이 오래 걸리면 원한 결과 1·2의 진행 상태 표현으로 보인다.
7. 사용자가 파일·변수·(시점, 계약 존재 여부에 따라)를 고를 수 있고, 고른 것이 원한 결과 1의 선점된 자리에 그려진다. 기본 선택 규칙은 미해결 질문.
8. 시스템 전체가 하나의 축척 기준을 갖는다 — 기본 배율은 픽셀이 아니라 **고정 지리 폭**(대략 한반도 전체 ＋ 중국 동부 일부 ＋ 일본 간사이까지 들어오는 정도의 폭, 약 1,500~2,000km 폭에 해당하는 크기 등급, 정확한 km/px 값은 미해결 질문)으로 정하고, 화면별(상세·업로드·확장보기)로 그 값을 적용한다. 데이터 래스터는 이 틀 안에서 실제 지리 위치·크기로 놓이므로 작은 유역 데이터는 틀 안에서 작게 보일 수 있다.
9. 위 기본 배율 위에서 확대/축소 컨트롤이 세 화면(상세·업로드·확장보기) 모두에 있다 — 지금은 상세에만 있다.
10. 지도형 결과(`bounds` 보유)에는 래스터 아래에 배경 지도 레이어(해안선 등)가 깔려 위치·축척을 눈으로 확인할 수 있다. 비지도형(좌표 없는 값 미리보기)에는 배경 레이어 자리가 없다.

---

## 영향 범위

- **사용자·화면**: 업로드 모달 장면2 좌측 미리보기(`PreviewPanel.tsx`), 데이터셋 상세 미리보기 구역(`DatasetPreviewSection.tsx`) 및 그 상위 레이아웃(`DatasetDetailPage.tsx`).
- **서비스·스키마·계약**: 항목 ①②는 FE(CSS·컴포넌트 배치)만으로 닫힐 가능성이 높다. 항목 ③은 `services/viz-render`의 `COLAB_VIZ_WORK_MAX_BYTES` 운용값·복구 경로(`RenderTarget.fileIds`) 조정, 항목 ④는 FE 선택 UI + (목록 조회 엔드포인트가 없으므로) `contracts/seams/core-viz.yaml` 확장 가능성이 있다.
- **계약 파괴 여부**: 항목 ①②는 계약 파괴 없음(전망). 항목 ③은 `TOO_LARGE_MESSAGE`·상한값이 바뀌면 사용자 노출 문구·거절 조건이 바뀌므로 계약 파괴는 아니되 정본 문구 변경이 필요할 수 있다. 항목 ④는 목록 조회 엔드포인트 신설 시 `core-viz.yaml` 신규 스키마 추가(파괴적이지 않은 첨가) 가능성 — 확정은 설계 단계.

## 제약

- 존치 규칙(§0.3-5, `R-B-3-frontend.md:71`) — 2단 등록 게이트·기준 격자 파일 흐름·이어올리기 배너는 이번 intent 로 걷지 않는다.
- ㈎ 확장보기(A9R/R-A′ 이관, `PreviewPanel.tsx:238-248,472-482`)와 격자 업로드 블록(`gridFlow.ts`)은 같은 컨테이너 안에 남는다 — 자리 재설계 시 이 둘의 도달 가능성을 유지한다.
- `Policy_데이터셋_상세 §1.3-5` 「시각화는 한 번에 값 하나만 그린다」(`DatasetPreviewSection.tsx:5`) — 항목 ④의 선택 UI 는 겹쳐 보기가 아니라 **바꿔 그리기**로 설계해야 정본과 충돌하지 않는다.
- `CLAUDE.md §0` stage 표 — 「타일 서빙은 요구가 아니라 선택 갈래, 기본값은 「한 장」」(`〈240〉`) — 500MB 대응을 타일 서빙 강제로 풀지 않는다.
- core-api 에 geo 라이브러리 금지(`CLAUDE.md §3-4`) — 항목 ③·④의 서버측 변경은 `viz-render`에만 놓인다.

## 설계 트리 (grill-me 결과)

- **① 자리 선점**
  - ⓐ FE 만 — `.mapstage`/`.dt-preview`에 고정 `min-height` 또는 `aspect-ratio`를 부여하고, 장면1에서도(또는 상세 최초 진입 즉시) 그 틀을 먼저 그린 뒤 내부만 상태별로 바꾼다. 서버 계약 변경 없음.
  - ⓑ 장면1에도 미리보기 틀을 세우려면 PRD-260905:385(「장면1엔 미리보기가 화면에 없다」)를 개정해야 한다 — 이것이 사실상 미해결 질문의 핵심(아래).
  - → **A(2026-09-08 Ted)**: **ⓐ** — 업로드는 장면2 진입(파일 선택) 즉시, 상세는 열자마자 고정 틀. PRD-260905:385 무개정(장면1 무변). 틀 비율 = **4:3**(⑤ 에서 따라옴 · `aspect-ratio`). 두 화면 모두 대상.
- **② 좌우 배치**
  - 업로드 모달은 변경 불필요(이미 충족).
  - 상세는 ⓐ `.infogrid`(기본 정보)와 `.dt-preview`를 감싸는 새 grid 컨테이너를 만들어 좌-이미지·우-정보로 재배치 vs ⓑ 현재처럼 세로 유지하고 폭이 넓을 때만 좌우로 나누는 반응형 규칙 추가. 계약 변경 없음.
  - → **A(2026-09-08 Ted)**: **상세 ⓐ** — 새 grid 컨테이너 · 좌 = 미리보기(sticky) · 우 = 기본 정보 ＋ 파일 목록 · 계보·활용은 아래 전폭. 960px 미만 = 한 열 · 미리보기 먼저. `SectionMenu` 앵커 3개(`sec-lineage`·`sec-preview`·`sec-usage`) 유지. 업로드 모달 무변.
- **③ 500MB 초과**
  - ⓐ 상한 자체를 올린다(`COLAB_VIZ_WORK_MAX_BYTES` 값 변경) — 디스크·처리 시간 재실측 필요.
  - ⓑ 상한을 유지하고 초과 시 자동으로 `RenderTarget.fileIds` 복구 경로(조각 하나)를 타게 하거나, 사용자가 조각을 고르게 한다(④와 결합).
  - ⓒ 스트리밍/다운샘플링으로 상한 자체를 없앤다 — `viz-render` 내부 구조 변경, 이번 조사로는 실현 가능성 미측정.
  - → **A(2026-09-08 Ted)**: **ⓑ** — 상한 유지. 초과 거절 시 FE 가 `RenderTarget.fileIds` 로 **첫 renderable 조각을 자동 재요청**하고, ④ 선택 UI 로 다른 조각을 고른다. 계약 변경 0. `COLAB_VIZ_WORK_MAX_BYTES` 배포값 실측은 배포 창 항목(레포 밖 `/opt/colab-v2/dev.env`).
- **④ 대상 선택**
  - ⓐ FE 만 — 목록 조회 엔드포인트가 이미 있다면(이번 조사로는 못 찾음) 그 값으로 드롭다운/탭을 만들고 `createRender` 호출에 `fileIds`·`variable`을 싣는다.
  - ⓑ 계약 추가 필요 — 「이 업로드/데이터셋에 그릴 수 있는 파일·변수(·시점) 목록」 조회 엔드포인트를 `core-viz.yaml`에 신설한다(21차 동결 해제 대상 여부는 미해결).
  - → **A(2026-09-08 Ted)**: **ⓑ 축소형** — 선택 축 = 파일·변수·시각 셋. 파일 목록은 기존 `GET /uploads/{id}/files`·`GET /datasets/{id}/files`(`contracts/seams/fe-core.yaml:574,1070` · `renderable` 플래그)로 충족. 시각은 기존 `RenderRequest.instant`(`core-viz.yaml:425-431` · 생략 시 첫 시각). **변수＋시각 목록만 없다** → core-viz 에 「대상 기술(describe)」 조회 1건 비파괴 첨가 = **21차**. 서버 변경은 viz-render 만.

- **⑤ 축척 기준**
  - (a) 기본 배율 크기 등급 — ⓐ CSS 상한만(컨테이너 `max-width`/`aspect-ratio`를 지리 폭에 맞는 값으로 고정하고 `object-fit`으로 앉힘) vs ⓑ 실제 배율 컨트롤(`useZoomPan`류 `transform: scale()` 을 업로드·확장보기에도 도입해 세 화면이 같은 훅을 공유) — ⓑ 를 권고(상세가 이미 이 구조이므로 재사용 비용이 낮다).
  - → **A(2026-09-08 Ted)**: **(a) ⓑ** — `useZoomPan`/`.pv-zoom` 을 세 화면(상세·업로드·확장보기)이 공유. **기본 배율 = 데이터 `bounds` 중심 ＋ 표준 축척 사다리 스냅**(데이터 폭을 담는 가장 작은 단 · 예 100·300·1,000·3,000·10,000 km — 단 값은 시스템 상수 한 자리 · 레인이 확정 `[미측정]`). 한반도 고정 프레임 안은 철회(Ted 원문 「다른지역이 나올수도있는데 데이터를 읽고 그걸 맞추지 못하나?」). 틀 4:3. 비지도형(`bounds` 없음)은 현행. 작은 유역 = 배경 위 `bounds` 외곽선 사각형 ＋ 더블클릭 맞춤.
  - (b) 배경 지도 레이어 — ⓐ **자립형 벡터 해안선**(Natural Earth 1:110m/1:50m 축약 GeoJSON을 레포에 반입해 SVG/Canvas로 래스터 아래에 그림, 외부 CDN·타일 서버 요청 0 — 이 레포의 자립·오프라인 원칙과 양립) vs ⓑ **외부 타일 배경**(네트워크·CDN 필요 — POL-021 「바탕 지도도 쓰지 않는다」와 정면 충돌, CSP·오프라인 요구와도 충돌) vs ⓒ **viz-render 서버측 합성**(래스터와 해안선을 한 이미지로 구워 보냄 — 클라이언트 코드는 그대로지만 서버가 지리 데이터셋을 새로 소유해야 함). 이번 조사에서 지도 라이브러리(Leaflet·MapLibre 등) 사용 흔적은 찾지 못했다(`[미확인]` — 전수 조사는 아님) — 반입 흔적이 없다면 ⓐ가 기존 정책(POL-021, 타일 서버·CDN 금지)과 가장 잘 맞는다.
  - → **A(2026-09-08 Ted)**: **(b) ⓐ** — 자립형 Natural Earth 1:110m 해안선＋국경(Public Domain) 반입 · 도시 표기 없음 · 파일 용량 상한 500KB(초과 시 간략화 · 레인 실측 `[미측정]`) · FE SVG 로 래스터 아래 · 외부 요청 0. 정책 반전 2건 = POL-021 「바탕 지도도 쓰지 않는다」 **부분 반전**(타일 서버 금지는 유지 · 자립형 벡터 배경만 허용) ＋ PLAN-SoT ㉴ 「B-2 해안선 오버레이 미채택」 반전 → 〈N〉 기록(번호는 병합 직전 재실측 · 현 최대 374). 레포 실측 = 지도 라이브러리·geo 자산 0건(`frontend/package.json` · `services/viz-render/requirements.txt:27` rasterio 만).

## 미해결 질문 → 판정(2026-09-08)

> ⭑ 16건 전부 grill-me 3라운드(4＋4＋1 문항)로 닫혔다. 프론티어 공집합. 축자는 `## 확인`.

1. (①) 자리 선점을 **두 화면 모두**에 적용하는가, 아니면 이미 컨테이너가 즉시 서는 상세만 대상인가 — 업로드는 장면1(파일 없음)에도 자리를 만들 것인가, 아니면 장면2 진입 즉시(파일 선택 직후)부터로 충분한가? → **판정**: 장면2 진입 즉시(업로드) · 열자마자(상세). 두 화면 모두. 장면1 무변 · PRD-260905:385 무개정.
2. (①) 자리 크기 기준 — 고정 `aspect-ratio`인가, 최소 `min-height`(px)인가, 데이터 종류(이미지 vs 타일)에 따라 달라지는가? → **판정**: 고정 `aspect-ratio` **4:3**(⑤ 틀에서 도출). 데이터 종류 무관 · 비지도형도 같은 틀.
3. (①) 못 그림 문면의 정본 텍스트 — 현재 `UNAVAILABLE`(업로드)·`UnavailableNotice`(상세) 두 문구가 다르다. Ted 발의의 「지금 못그린다는 표현」이 이 둘을 그대로 쓰는 것인지, 새 통일 문구가 필요한지. → **판정**: 현행 두 문구(`UNAVAILABLE`·`UnavailableNotice`) 유지 · 신설 0.
4. (①) 진행 단계 문구가 「지금 띄우는 표현」(`파일 읽는 중…`→`지도 그리는 중…`→`범례 만드는 중…`) 그대로인지, 자리 선점 목적에 맞춰 문구를 더 추가(예: 「자리 확보됨」류 0단계)할지. → **판정**: 현행 3단계 그대로 · 0단계 신설 없음. 그리기 전에는 「아직 그리지 않았어요」(`.vizph`)가 선점된 자리 안에 선다.
5. (②) 상세 페이지 좌우 배치의 반응형 폴백 — 좁은 화면에서 세로로 접히는 분기점(px)과 순서(이미지 먼저인가 정보 먼저인가). → **판정**: 분기점 **960px** · 좁으면 한 열 · 미리보기 먼저.
6. (③) 500MB 상한을 **철폐**할지 **상향(구체 값)**할지, 대용량 렌더 방식(ⓐⓑⓒ) 중 무엇을 쓸지, 서버 자원(디스크·메모리·시간) 재실측 없이 결정 가능한지. → **판정**: 상한 유지 ＋ 조각 폴백 자동화(ⓑ). 서버 자원 재실측 불요 · 배포값 실측은 배포 창.
7. (④) 선택 축이 파일·변수·시점 중 무엇까지인지 — 계약에 `variable`은 있으나 시점(time) 파라미터는 이번 조사로 못 찾았다. 시점 선택이 필요하면 계약 신설 대상. → **판정**: 파일·변수·시각 셋. 시각은 기존 `RenderRequest.instant` · 파일은 기존 files 조회 · **변수(＋시각) 목록 조회만 신설**(21차).
8. (④) 기본 선택 규칙 — 대표 파일/대표 변수를 무엇으로 정하는가(첫 파일? 대표 지정값?). → **판정**: 서버 기본값 그대로(첫 renderable 파일 · 첫 2D 변수 `readers.py:_pick_default` · 첫 시각) · 고른 값을 화면에 표시.
9. (④) 선택을 업로드·상세 양쪽에 다 두는지, 선택 상태를 URL/컴포넌트 상태 중 어디에 유지하는지. → **판정**: 업로드·상세 양쪽 · 컴포넌트 상태 · URL 미반영.
10. (③④) 계약 변경이 필요하면 21차 동결 해제 대상으로 올릴지, 이번 라운드에서 함께 처리할지. → **판정**: 21차 한 묶음 — 우산 intent `2026-09-08-r-c.md` 에서 승인.
11. (⑤) 기본 배율의 정확한 값 — km/px 또는 지리 폭(경도·위도 범위)을 시스템 상수로 어떻게 못박을지. Ted 의 「대한민국·중국 우측·일본 간사이」 서술에서 「중국 우측」이 한반도를 기준으로 화면 좌측(서쪽, 중국 동해안)을 뜻하는지, 다른 배치를 뜻하는지 확인 필요 — 「그냥 이정도의 축척」으로 크기 등급만 확정되고 정확한 배치·수치는 열려 있다. → **판정**: 고정 프레임 **아님** — 데이터 중심 ＋ 표준 축척 사다리 스냅. 「중국 우측」 해석·경위도 수치는 폐기(Ted 원문 「다른지역이 나올수도있는데 데이터를 읽고 그걸 맞추지 못하나?」).
12. (⑤) 확대/축소/기본 배율 컨트롤의 위치·형태를 세 화면(상세·업로드·확장보기)이 공유할지, 화면별로 다른 UI를 둘지. → **판정**: 세 화면 공유(`useZoomPan`·`.pv-zoom`).
13. (⑤) 배경 지도 레이어의 상세도 — 해안선만인지, 국경·주요 도시 표기까지 포함하는지. → **판정**: 해안선＋국경만 · 도시 표기 없음.
14. (⑤) 자립형 벡터 해안선 반입 시 라이선스·레포 용량 제약을 통과하는지(Natural Earth 는 Public Domain 이나 실물 파일 크기·간략화 수준 확인 필요). → **판정**: Natural Earth = Public Domain · 용량 상한 500KB · 초과 시 간략화 · 레인 실측 `[미측정]`.
15. (⑤) 래스터가 화면상 작은 유역 하나뿐일 때, 배경 지도 위에서 「지금 어디를 보고 있는지」를 표시하는 방식(하이라이트 사각형? 화살표?). → **판정**: 배경 위 `bounds` 외곽선 사각형 ＋ 더블클릭으로 데이터에 맞춤.
16. (⑤) `bounds` 응답 열쇠는 이미 있으나 배경 지도 합성/렌더링을 FE 만으로 끝낼지 서버(viz-render)가 관여할지에 따라 21차 계약 변경 여부가 갈린다. → **판정**: FE 만 · viz-render 무관 · 계약 영향 0.

## 범위 밖 (명시 제외)

- 미리보기 렌더 성능 개선(그리기 자체의 속도).
- 새 시각화 종류(격자·경계·점 외 추가 표현) — 정본이 이미 「무엇으로 그릴지는 사람이 고르지 않는다」로 못박은 영역(`DatasetPreviewSection.tsx:6-8`)과 충돌하지 않도록, ④의 「대상 선택」은 **같은 표현 안에서 그릴 파일·변수를 바꾸는 것**이지 표현 종류 선택이 아니다.
- 겹쳐 보기(overlay) — 정본 근거·완료 정의 미확정(`DatasetPreviewSection.tsx:16`).
- 해안선 지도 레이어의 상세도(국경·도시 등 확장 표기)는 요구 아님 — 필요성은 별건.

## 확인

⛔ Ted 가 채워 커밋하기 전에는 정본이 아니다(커밋이 곧 승인).

- 프론티어 공집합 확인: 2026-09-08 — grill-me 3라운드(4＋4＋1 문항) · Ted 답 전부 권고(A) · 예외 1 = ⑤ 기본 틀(권고 철회 → 3라운드에서 재판정).
- **R1(4문항)** → Ted 확인 문장(원문 그대로 · 선택지 라벨): "장면2 진입 즉시 · 상세는 열자마자" / "상한 유지 ＋ 조각 폴백 자동화" / "자립형 벡터 해안선 · POL-021 부분 반전" / "R-C 한 intent · 두 축 ＋ 21차 한 묶음"
- **R2(4문항)** → Ted 확인 문장(원문 그대로): "파일·변수·시각 셋 · 변수 목록 조회 신설 = 21차" / "다른지역이 나올수도있는데 데이터를 읽고 그걸 맞추지 못하나?"(⑤ 틀 — 한반도 고정 프레임 권고 **철회**) / "좌 미리보기(sticky) · 우 기본정보＋파일 · 계보·활용은 아래 전폭" / "6건 전부 권고대로"(① 못그림 문면 현행 ② 진행 문구 현행 ③ 기본 선택 서버값 ④ 컴포넌트 상태 ⑤ 해안선＋국경 ⑥ NE 110m · 500KB)
- **R3(1문항)** → Ted 확인 문장(원문 그대로): "데이터 중심 ＋ 표준 축척 사다리에 스냅"
- 계약 동결 해제 **21차** · 등급 = ㉮(비파괴 첨가 전망 · `contract-breaking` 출력으로 병합 직전 확정) · 승인 자리 = 우산 intent `2026-09-08-r-c.md ## 확인`. 승인 없이 `contracts/` 를 고치지 않는다.
- 재개봉 금지: **예** — 2026-09-05 확정 16 · 2026-09-06 확정 12 · 2026-09-08 R-B 61건 판정 · 위 9 문항.

**Ted 원문 (2026-09-08, ⑤ 관련, 순서대로)**

1. 「사이즈가 미리보기 뒤죽박죽인데, 축적은 어느정도 우리시스템에서 기준을 갖고 가야하지 않을까? 각 화면에서 확대/축소/기본배율 뭐 이렇게 하고,」
2. 「기본적으로 대한민국 나오고 중국 우측 좀 나오고 일본 간사이 쪽 까진 나오는 형태면 좋을거같은데」
3. 「그냥 이정도의 축척」 — ②는 정확한 지리 프레임 요구가 아니라 **기본 배율의 크기 등급**(대략 1,500~2,000km 폭)을 말로 그린 것이라는 정정. 이 정정으로 「배경 해안선 지도」 요구는 배율 서술에서 분리됐다.
4. 「지도 레이어 반입은 왜빠져 배경해주면 좋을거같은데, 위치 축척 같은걸 데이터에서 뽑아낼수있지않아?」 — 배경 지도 레이어 자체는 여전히 원함(③에서 배제된 것은 「배율=지리 프레임」 해석이지, 배경 레이어 요구 자체가 아니다).

## 참조

- frontend/src/components/upload/PreviewPanel.tsx
- frontend/src/components/upload/UploadModal.tsx
- frontend/src/components/upload/upload.css
- frontend/src/components/datasetpreview/DatasetPreviewSection.tsx
- frontend/src/components/preview/PreviewPanels.tsx
- frontend/src/components/preview/types.ts
- frontend/src/routes/DatasetDetailPage.tsx
- frontend/src/components/detail/detail.css
- services/viz-render/src/colab_viz/domains/d7_visualization/jobs.py
- services/viz-render/src/colab_viz/domains/d7_visualization/failures.py
- services/viz-render/src/colab_viz/kernel/config.py
- services/viz-render/src/colab_viz/ports/source.py
- services/viz-render/src/colab_viz/domains/d7_visualization/source_digest.py
- contracts/seams/core-viz.yaml
- dev-package/prd/PRD-260905-적용전기획.md
- dev-package/prd/rounds/R-B-3-frontend.md
- frontend/src/components/preview/useZoomPan.ts
- frontend/src/components/preview/preview.css
- frontend/src/components/upload/PreviewExpandOverlay.tsx
