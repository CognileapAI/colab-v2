# recon-B — 미리보기·지도 (B-1 ~ B-5) 근본 원인 조사

읽기 전용. **레포·staging 무접촉.** 재현은 로컬 원천 + viz-render `.venv`.

---

## 0. 한 줄 결론

| # | 판정 | 근본 원인 | 고치는 배포 단위 |
|---|---|---|---|
| B-1 | **확정 (로컬 재현)** | `warp_to_3857` 이 **전방 산란(forward scatter)** 리샘플이라, 원본 격자가 출력(1024 px)보다 성기면 출력 픽셀의 대부분이 결측(알파 0)으로 남는다 | **viz-render** |
| B-2 | 검토 결과 = **정책 안에서 가능** (아래 옵션표) | 기능 부재 | frontend (＋스크린샷 정합을 원하면 viz-render) |
| B-3 | **확정** — **버그다. 미구현이 아니다** (`P3` = `done`) | `maxScale = 산출물 PNG 폭 / 뷰포트 폭` 이라 실측 ≈ **1.00**. 세 버튼 전부 무동작 | **frontend** |
| B-4 | **확정** | 같은 산출물을 두 화면이 **다른 CSS 규칙**으로 놓는다(`max-width:100%` vs `width:100%`). 가로 흰 줄은 B-1 과 **같은 원인**의 경증형 | frontend (흰 줄은 viz-render) |
| B-5 | **가설(강) — 렌더는 정상, 화면을 잘못 읽었다** | 그림은 `DEM_100m.tif`(D-02) 이고 **그 페이지가 D-02 다**. 범례 `2 ~ 521.1` 이 파이프라인 실행값과 소수 4자리까지 일치 | frontend (계보 줄·범례 표기) |

---

## 1. B-1 — Lv1 가공본이 회색 바탕 + 점 격자

### 근본 원인 (확정)

`services/viz-render/src/colab_viz/domains/d7_visualization/preview.py:142-152` —
`warp_to_3857` 은 **원본 셀 중심 하나하나를 출력 격자에 던져 넣는(scatter/binning)** 방식이다.

```
cols = clip(((xs - minx) / px).astype(i8), ...)   # preview.py:142
rows = clip(((maxy - ys) / py).astype(i8), ...)   # preview.py:143
np.add.at(sums, flat, vals)                       # preview.py:147
out = full(w*h, nan); out[counts>0] = ...         # preview.py:149-151
```

출력 크기는 **항상 긴 변 1024 로 고정**(`preview.py:104` `max_side=DETAIL_SIDE`)인데 원본은 그보다 성길 수 있다. 그러면 원본 셀 수만큼만 채워지고 **나머지는 NaN → RGBA 알파 0** 이다.

### 근거 (로컬 실측 · 실제 코드 경로 그대로)

`readers.read_field(max_side=1024)` → `_mesh_from_bounds` → `preview.warp_to_3857` 을 그대로 태운 값:

| 원천 | 원본 shape | warp 출력 | **채워진 픽셀** | 전 결측 행 | 전 결측 열 | 대응 스크린샷 |
|---|---|---|---:|---:|---:|---|
| `GK-2A_NDVI_20240615_bilinear_1km.tif` (D-04) | 128×126 | 1024×808 | **1.91 %** | 896 | 682 | **bug04** (점 격자) |
| `GK-2A_NDVI_20240615_2km.tif` (D-01) | 727×1024 | 951×1024 | **17.91 %** | 224 | 31 | **bug06** (점으로 된 한반도) |
| `DEM_100m.tif` (D-02) | 1024×1024 | 1024×821 | 99.80 % | **2** | **0** | **bug11** (가로 흰 줄 2개) |
| `GK2A_NDVI_mean_202305.tif` (D-16) | 1024×1024 | 1024×821 | 99.80 % | **2** | **0** | **bug10** (가로 흰 줄) |

- 배제 — ⓐ 「안 구웠다/낡은 이벤트」 아니다(범례 `0.3601~0.7983` = D-04 10파일 2–98 % 백분위와 정확 일치) ⓑ NaN 처리 아니다(원본 NaN 1.9 %) ⓒ CSS 아니다(PNG 자체가 98 % 투명).
- **세로 줄이 없는 이유** = lon→x 는 선형, lat→y 는 메르카토르 비선형이라 **행 간격만** 불균등해진다. Ted 관찰과 일치.

### 최소 수정 방향 (viz-render)

1. **역방향 매핑으로 바꾼다** — 출력 픽셀마다 원본 인덱스를 역산해 값을 읽는다(규칙 격자면 정확, 곡선 격자면 KD-tree/근접). 지금의 `np.add.at` 평균은 **원본이 출력보다 촘촘할 때만** 옳다.
2. 또는 **출력 크기를 원본 해상도로 상한**한다 — `max_side = min(DETAIL_SIDE, 원본 긴 변)`. 한 줄 변경이고 B-1 의 점 격자는 즉시 사라지지만(126×128 → 126 px PNG), **가로 흰 줄(D-02·D-16)은 안 없어진다**(원본=출력=1024 인데도 2행이 빈다). 둘 다 필요하다.

### 실패 테스트 초안 (viz-render)

`tests/test_preview_warp_gaps.py` (신규) —
- `test_warp_leaves_no_hole_when_source_is_coarser_than_output` : 128×126 · bbox `126.70~127.96 / 36.08~37.36` 를 `warp_to_3857(max_side=1024)` → `np.isfinite(out).mean() > 0.95` 와 「전 결측 행 0」. **지금 0.0191 / 896행 → red.**
- `test_warp_leaves_no_empty_row_at_equal_resolution` : 1024×1024 원본 → 전 결측 행 0. **지금 2 → red.**

---

## 2. B-2 — 위경도 자료에 바탕 지도(육지 윤곽)가 없다 · 타당성 검토

`POL-021` 축자 = 「**타일 서버도 바탕 지도도 쓰지 않는다**」(`CLAUDE.md:19` · `dev-package/PLAN-SoT.md:591` · `WORK-UNITS.md:420`). 그런데 그 문장이 막는 것은 **외부 타일 서비스에 붙는 것**이고, 「지금 보는 그림이 어디인지 알 수 없다」는 문제는 그것 없이도 풀린다.

| # | 안 | 정책 준수 | 외부 요청 | 스크린샷에 실리나 | 노력 | 권고 |
|---|---|---|---|---|---|---|
| ⓐ | **경위도 격자선 + 눈금 라벨**을 뷰포트에 SVG 로 겹친다 (bounds 네 값만 쓴다) | ✅ 완전 준수 | 0 | ❌ (FE 전용) | **0.5 d** | **1순위 — 즉시** |
| ⓑ | **내장 정적 해안선**(Natural Earth 1:50 m 한국 부분, 단순화 GeoJSON ≈ 30–80 KB, Public Domain)을 FE 가 bounds 로 투영해 `pv-layers` 안에 SVG 로 겹친다 | ✅ 준수(자산 동봉 · 요청 0) | 0 | ❌ | **1.5–2 d** | **2순위 — 권고** |
| ⓒ | 같은 해안선을 **viz-render 가 ③지도형 PNG 에 구워 넣는다** | ✅ 준수 | 0 | ✅ | **2–3 d** (캐시 키 파라미터 1개 추가 · 색 간섭 검토 · 값 조회 무영향 확인) | 스크린샷 정합이 필요하면 ⓑ와 **함께** |
| ⓓ | 지도 라이브러리(leaflet/maplibre) + 외부 타일 basemap | ❌ **POL-021 위반** | 있음 | — | 3 d + 정본 개정 | **하지 않는다** |

- **⚠ 스크린샷은 서버가 그린다**(`ScreenshotButton.tsx:9-10`). ⓐ·ⓑ만 하면 **화면에는 윤곽이 있고 저장한 PNG 에는 없다.** 이 불일치를 받아들일지가 Ted 판정 사항이다.

---

## 3. B-3 — 「확대 · 축소 · 기본 배율로」가 동작하지 않는다

### 판정 = **버그다. stage 2 미구현이 아니다.**

- 대장 `dev-package/work-items.yaml` `P3`(계보 그래프 · 2D 시각화 3종 · createScreenshot · 렌더 표현 확장) = **`status: done`**, 완료 정의에 「확대·`createScreenshot` 은 완료 정의 그대로다」가 축자로 있다. 확대 전용 `PV-*` 항목 없음(`PV-1` 은 뒷단이고 `done`). → **닫힌 항목의 회귀**다.

### 근본 원인 (확정)

`frontend/src/components/preview/useZoomPan.ts:192`
```ts
setMaxScale(Math.max(1, nativeWidth.current / size.width));
```
`nativeWidth` 는 **산출물 PNG 의 폭**이다(`useZoomPan.ts:213` `naturalWidth`, 타일 갈래는 사이드카 `width`). 산출물 긴 변은 **항상 1024** 이고 세로로 긴 그림은 폭이 **808~821 px** 다(위 실측표). 상세 뷰포트 폭은 실측 **≈ 820 px**(bug04·bug10 스크린샷 기준).

| 데이터셋 | PNG 폭 | 뷰포트 | **maxScale** | 결과 |
|---|---:|---:|---:|---|
| D-04 Bilinear | 808 | ~820 | **1.00** | 확대 완전 무동작 |
| D-02 DEM / D-16 | 821 | ~820 | **1.001** | 사실상 무동작 |

- `zoomIn` 은 `view.scale >= maxScale` 에서 즉시 `return`(`useZoomPan.ts:115-119`) → 아무 일도 안 일어난다.
- `reset` 은 이미 `{1,0,0}` 이라 무동작(`:128-131`).
- **왜 시험이 못 잡았나** — `frontend/test/dataset-preview-zoom.test.tsx:86` 의 픽스처가 `measure(naturalPx = 4096, boxPx = 512)` 라 `maxScale = 8` 이다. **파이프라인이 절대 만들지 않는 해상도**를 가정하고 green 이다(13/13 통과 실측).

### 최소 수정 방향 (frontend)

- 정본 조건 ⑷ 「데이터가 가진 해상도가 한계」의 **해상도 출처가 틀렸다** — 산출물 PNG 가 아니라 **원본 배열의 크기**여야 한다. 그 값은 서버만 안다 → 계약에 `nativeWidth`(원본 픽셀 수) 또는 사이드카에 필드 하나가 필요할 수 있다(**계약 개정 여부는 advisor 게이트**).
- 원본이 정말 뷰포트보다 작을 때(126×128)는 확대할 것이 실제로 없다 → **무반응이 아니라 「원본 해상도까지 봤어요」를 처음부터 세운다.** 지금은 `atLimit` 이 `view.scale > 1 || blocked` 를 요구해(`:237`) **첫 클릭 전에는 아무 말도 안 한다.**
- **스크린샷 버튼**은 별건이다 — `ScreenshotButton.tsx:72-77` 이 `a.click()` 직후 같은 tick 에 `URL.revokeObjectURL(url)` 을 부르고 앵커를 문서에 붙이지 않는다. 크롬에서 다운로드가 취소되는 알려진 무늬다. **회수는 `setTimeout`/`load` 뒤로 미룬다.**

### 실패 테스트 초안 (frontend)

`dataset-preview-zoom.test.tsx` 에 **`measure(808, 820)`**(실제 파이프라인 값) 케이스를 더한다 —
① 「확대」를 눌러도 `pv-layers` 의 `transform` 이 `scale(1)` 그대로다 → red ② 확대할 수 없으면 **첫 클릭 전에** `zoom-limit` 이 서야 한다 → red.

---

## 4. B-4 — 업로드 미리보기 ≠ 상세 미리보기 · 「기본 배율」 규칙 부재 · 가로 흰 줄

### 근본 원인 ⑴ 배율 (확정) — **같은 PNG, 다른 CSS 규칙**

| 화면 | 규칙 | 파일:행 | 실효 기본 배율 |
|---|---|---|---|
| 업로드(S-04 모달) | `.mapcanvas .tile { max-width: 100%; }` | `frontend/src/components/upload/upload.css:139` | **원본 1 px = 1 CSS px**(컨테이너를 넘을 때만 축소) |
| 데이터셋 상세(S-05) | `.pv-layers .pv-tile { width: 100%; image-rendering: pixelated; }` | `frontend/src/components/preview/preview.css:198-206` | **항상 뷰포트 폭에 맞춤**(확대도 한다) |

- 산출물이 작을수록 격차가 커진다. **정본에 「기본 배율」의 정의가 없다** — 두 화면이 각자 정했다.

### 근본 원인 ⑵ 가로 흰 줄 (확정) — **타일 이음새가 아니다**

- 타일 갈래는 **기본 꺼짐**(`jobs.py:tile_branch` · `〈240〉` · staging 기본값 꺼짐)이고 bug10/bug11 은 `imageUrl` 한 장이다. → 모자이크 이음새 가설 기각.
- 실측: D-16·D-02 의 warp 출력에 **전 결측 행 정확히 2줄, 전 결측 열 0줄**. 스크린샷의 줄 개수·방향과 일치. **B-1 과 동일한 근본 원인**이다.

### 최소 수정 방향

- 상세의 기본 배율을 **「원본 1 px = 1 CSS px, 컨테이너보다 크면 맞춰 축소」**(＝ `max-width:100%`)로 통일하고, 그 문장을 정본에 한 줄 박는다. 두 화면이 같은 규칙을 인용하게 한다.
- `image-rendering: pixelated` 는 **확대 중일 때만** 건다(기본 배율에서 늘리지 않으므로 필요 없다).
- 흰 줄은 §1 수정으로 함께 사라진다.

### 실패 테스트 초안

- FE — `it('같은 산출물을 업로드 화면과 상세 화면이 같은 크기로 놓는다')` : 808×1024 PNG · 컨테이너 820 → **둘 다 808 CSS px**(지금 상세는 820).
- 흰 줄 시험은 §1 의 `test_warp_leaves_no_empty_row_at_equal_resolution` 이 그대로다.

---

## 5. B-5 — Co-Kriging(Lv1) 미리보기가 DEM 처럼 보이고 범례가 2~521

### 근본 원인 (가설 · 확신 높음) — **렌더는 정상이고, 그 페이지가 Co-Kriging 이 아니다**

증거 사슬 —

1. **범례 숫자가 DEM 과 소수 4자리까지 일치.** 실제 코드 경로(`readers.read_field(max_side=1024)` → `scale.percentile_range`)로 `DEM_100m.tif` 를 태운 값 = **`(2.0, 521.1164025878902)`**. 스크린샷 범례 = `2 ~ 88.52 … 434.6 ~ 521.1`. **일치.**
2. **다른 후보는 전부 어긋난다.** cokriging 10파일 2–98 % = `0.416 ~ 0.861`. DEM＋cokriging 11파일 혼합 = `0.46 ~ 513`. **혼합도 아니다** → 그 렌더가 읽은 파일은 **DEM 한 장뿐**이다.
3. **D-06 의 파일 목록은 깨끗하다** — `infra/staging/manifest-s2.json` 의 D-06 = `Output/04_cokriging/*.tif` 10건뿐. DEM 은 D-02 의 유일한 본체다.
4. **화면에 보이는 줄이 「파생」이다.** `frontend/src/components/lineage/graphTypes.ts:17` 축 = `원천 → 가공 전 → 이 데이터 → 파생`. **「파생」은 자식 칸**이다. 시드 계보상 Co-Kriging(D-06)의 **자식은 없고**, 부모는 D-01(주입력)·D-02(보조입력)뿐이다 → 「파생: Co-Kriging」을 보여주는 페이지는 **D-01 또는 D-02**이고, 범례가 D-02(DEM)를 가리킨다.

→ **밴드 오선택도 파일 오선택도 아니다.** viz-render 의 파일 선택 경로는 `ports/source.py:101-125`(대상 디렉터리 전량) 하나뿐이고, 그것이 틀렸다면 범례가 혼합값 `0.46~513` 이어야 한다.

### 남는 진짜 결함 (여기가 고칠 자리)

1. **계보 줄이 페이지 제목처럼 읽힌다** — `LineageSection.tsx:334-335` 의 `이 데이터` 만 `is-self` 굵은 테두리를 갖고, 나머지 줄도 같은 크기·굵기의 제목 글꼴이라 스크롤 위치에 따라 **누구의 미리보기인지 알 수 없다**. 미리보기 구역 머리(`DatasetPreviewSection.tsx:134` `<h2>미리보기</h2>`)에 **데이터셋 이름을 붙이는 것**이 최소 수정이다.
2. **범례에 변수명·단위가 없다** — `PreviewPanels.tsx:267-277` 은 `min ~ max (+unit)` 만 낸다. `job.value_variable`(`jobs.py:544`)은 서버가 이미 들고 있고 `Legend` 에도 실린다. `band1` 같은 값이라도 **NDVI 인지 고도인지**를 화면이 말해야 이 오독이 안 난다.

### 확인 (기각/확정을 가르는 한 방)

- 화면: bug11 을 **위로 스크롤해 「이 데이터」 줄의 이름**을 읽는다. `DEM 100 m 충청권` 이면 확정.
- 서버(읽기 전용): staging `https://www.colab-hydro.com` 의 `GET /api/v1/previews/{renderId}` 에서 `legend.variable`·`imageUrl`(내용 해시)을 D-02 렌더의 것과 대조한다.

### 실패 테스트 초안

- FE — `it('미리보기 구역이 어느 데이터셋의 것인지 이름으로 말한다')` : `미리보기` 머리 안에 데이터셋 이름이 있어야 한다(지금 없음).
- FE — `it('범례가 변수 이름을 함께 낸다')` : `legend.variable` 표기(지금 값 범위만).

---

## 6. 어느 경계에서 끊겼나 (frontend → core-api → viz-render → storage)

- **B-1 · B-4(흰 줄)** = **viz-render 안**(`preview.warp_to_3857`). 로컬 원천 파일로 100 % 재현 — 서버가 필요 없다. core-api·storage 무죄.
- **B-3 · B-4(배율)** = **frontend 안**(CSS ＋ `useZoomPan`). 서버 응답은 계약대로 1024 px 이고, 화면이 그것을 원본 해상도로 오인한다.
- **B-5** = 끊긴 데가 없다(가설). 범례가 파이프라인 실행값과 정확히 일치한다. 있다면 **사람이 화면을 읽는 자리**다.
- **계측이 더 필요한 곳은 B-5 하나뿐이다** — 나머지 셋은 로컬 재현으로 닫혔다.

## 7. 의존관계 — 병렬 레인 나누기

| 레인 | 만지는 파일 | 담는 버그 | 충돌 |
|---|---|---|---|
| **L1 · viz-render 리샘플** | `services/viz-render/src/colab_viz/domains/d7_visualization/preview.py` (＋`tests/`) | B-1, B-4(흰 줄) | 없음 |
| **L2 · frontend 배율/줌** | `components/preview/useZoomPan.ts` · `components/preview/preview.css` · `components/upload/upload.css` · `components/datasetpreview/ScreenshotButton.tsx` | B-3, B-4(배율) | 없음 |
| **L3 · 화면 표기** | `components/datasetpreview/DatasetPreviewSection.tsx` · `components/preview/PreviewPanels.tsx`(범례부) · `components/lineage/LineageSection.tsx` | B-5 | **PreviewPanels.tsx 를 L4 와 공유** |
| **L4 · 오버레이(B-2)** | `components/preview/PreviewPanels.tsx`(`pv-layers` 안) ＋ 신규 자산 ＋ (ⓒ 선택 시) `preview.py` | B-2 | **L3 과 `PreviewPanels.tsx`**, **L1 과 `preview.py`(ⓒ 선택 시)** |

- **L1 · L2 는 완전 독립** — 동시에 돌려도 된다.
- **L3 · L4 는 직렬**로 두거나 L4 를 뒤에 놓는다.
- B-2 의 옵션 선택과 B-5 의 「가설 → 확정」은 **advisor 게이트 뒤**에 착수한다.

---

## 8. 테스트 실행 명령

```bash
# viz-render (로컬 venv · 0.1 s)
cd services/viz-render && ./.venv/bin/python -m pytest tests -q
cd services/viz-render && ./.venv/bin/python -m pytest tests/test_preview_downsample_and_lut.py -q   # 실측 7 passed

# frontend (vitest · 파일 1건 약 25 s)
cd frontend && npm test                                        # 전량
cd frontend && npx vitest run test/dataset-preview-zoom.test.tsx    # 실측 13 passed (픽스처가 결함을 가린다)

# 근본 원인 재현 — `readers.read_field(max_side=1024)` → `_mesh_from_bounds` → `preview.warp_to_3857` 을
# 원천 tif 에 그대로 태우고 `np.isfinite(out).mean()` 을 찍는다 (레포 무접촉 · 원천만 읽는다).
# → D-04 Bilinear = 0.0191 (＝ 98.1 % 투명. bug04 의 실체)
```

**staging 은 건드리지 않았다** — B-5 확인이 필요해지면 `https://www.colab-hydro.com` 에 GET 만 건다(재기동·배포 0건).
