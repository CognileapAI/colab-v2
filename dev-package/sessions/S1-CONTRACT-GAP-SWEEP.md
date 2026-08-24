# S1 계약 구멍 전수 스윕 — 4차 동결 해제를 마지막으로 만들기 위한 점검표

> **읽는 순서** — 이 문서는 `PLAN-SoT §9-〈87〉-㉮` 가 적은 실패 원인(「실패한 것은 의지가 아니라 **점검표의 범위**」)에 대한 답이다.
> 세 회차가 각각 **직전 묶음이 세지 않은 것**을 닫았다: `〈80〉`은 ③지도형만 셌고 · `〈85〉`는 ②비지도형을 닫았고 · `〈87〉`은 `core-ai` 산문을 닫았다.
> 이 스윕은 **①썸네일 · 등록 전 격자 · 팔레트 · 산문 잔여**까지 축을 넓혀 다시 셌다.
>
> **조사 전용이다. 이 세션은 계약·코드를 한 줄도 고치지 않았다.**
> `[EVIDENCE]` 는 `cat -n`/`grep -n` 으로 실물을 확인한 사실이고, `[RECOMMENDATION]` 은 이 문서의 판단이다. 섞지 않는다.

---

## 0. 한 장 결론

| | |
|---|---|
| 발견 | **16건** (A 3 · B 4 · C 3 · D 4 · E 3 · F 1 · G 1 — 일부는 두 부류에 걸쳐 무거운 쪽으로 셌다) |
| **⛔ 치명 (조용히 틀린 값·닫힌 완료 정의)** | **5건** — `D-1` `D-2` `D-3` `A-1` `C-1` |
| 🟧 완료 정의를 막는 것 | 4건 — `B-1` `B-2` `D-4` `F-1` |
| ⬜ 정리 사안 | 7건 |
| **계약 개정이 필요한 것** | **7건** → 묶음 항목 11개 |
| 코드·문서만으로 닫히는 것 | **9건** |
| 최악 | **`D-1` — `listPalettes` 중계가 없어 실서버에서 미리보기 렌더가 단 한 번도 시작되지 않는다.** 완료 정의 2·15·16·18 이 통째로 닫힌다 |

> **⚠ 이 스윕이 새로 세운 축 하나** — 앞의 세 회차는 전부 **「응답이 무엇을 담는가」**만 셌다.
> 이번에 드러난 무거운 것 넷(`D-1`~`D-4`)은 **「그 응답을 부를 op 이 있는가」** 쪽이다. 축이 달랐기 때문에 세 번 다 안 보였다.

---

## A. 성공 산출물인데 실을 자리가 없는 것

### ⛔ A-1 `RenderResult` 에 **①썸네일을 실을 필드가 없다** — 성공 산출물이 실패 봉투로만 나간다

**`[EVIDENCE]`**

- `services/viz-render/src/colab_viz/domains/d7_visualization/jobs.py:313-316` — `preview.build_value_layers(...)` 가 **①썸네일과 ②비지도형을 항상 함께 굽는다**. `PreviewArtifacts.thumbnail` 은 `| None` 이 아니다(`:145`) — **없는 경우가 없다.**
- 같은 파일 `:100-114` — 성공 응답(`result`) 조립부. 실리는 것은 `legend`·`precisionBadge`·`colorRangeStage` 와 **`imageUrl` 하나**뿐이다.
  - `:104-108` ③지도형이 있으면 `imageUrl = map_image.url` → **②비지도형 URL 도 함께 버려진다.**
  - `:110` ③이 없으면 `imageUrl = detail.url`(②) → **①썸네일 URL 이 버려진다.**
  - **어느 갈래에서도 `thumbnail.url` 이 성공 응답에 실리지 않는다.**
- 같은 파일 `:343-348` — **실패 봉투에서만** `details["thumbnailUrl"]`·`details["valuePreviewUrl"]` 로 나간다.
- `contracts/seams/core-viz.yaml:396-455` — `RenderResult` 의 `additionalProperties: false` ＋ 속성 8개. **썸네일 필드가 없다.**
- `frontend/src/components/upload/previewResult.ts:9` 주석이 그 사실을 그대로 적었다 — 「viz-render 는 **실패 봉투의 `details.thumbnailUrl` 로만** 그 자리를 말한다」. `:51-59` 가 실패 봉투를 파싱한다.
- `frontend/src/components/upload/PreviewPanel.tsx:286-294` — 화면은 `salvage.thumbnailUrl` / `salvage.valuePreviewUrl`, 즉 **실패 경로**에서만 썸네일을 그린다.

**무엇이 언제 깨지는가** — `〈85〉` 가 ②를 「완료」로 만든 뒤 **성공 경로에서 썸네일이 화면에 도달할 길이 사라졌다.** 렌더가 성공할수록 썸네일이 안 보인다. 이것은 `〈83〉-㉮` 가 닫았다고 선언한 **「성공 산출물이 실패 봉투로 나가는」 모양 그대로**이고, 같은 버그가 한 필드 옆에 그대로 남아 있다.

**`[RECOMMENDATION]`** `RenderResult` 에 `thumbnailUrl`(①, 128 px WEBP)과 `valuePreviewUrl`(②, 1024 px PNG)을 **선택 속성**으로 더한다. `imageUrl` 의 `oneOf` 는 손대지 않는다 — 「무엇을 주 화면에 그릴 것인가」와 「어떤 층들이 함께 구워졌는가」는 다른 질문이다. **필수로 만들지 않는다**(타일 갈래에는 없다).

### 🟧 A-2 `DatasetRow.thumbnailUrl` 은 **선언만 있고 아무도 만들지 않는다** — `A-1` 이 원인이다

**`[EVIDENCE]`**
- `contracts/seams/fe-core.yaml:2061-2071` — `K-2`(`〈80〉-㉯ 2`)로 신설된 목록 썸네일 필드.
- `grep -rn thumbnail services/core-api db` = **0건.** 생산자가 없다.
- `grep -rn thumbnail frontend/src` = 생성물(`fe-core.ts:1310`)과 업로드 모달의 `salvage` 뿐. **카탈로그 화면에 소비자도 없다.**

**무엇이 언제 깨지는가** — 지금은 아무 일도 안 난다(`null` 이 정상값이다). 문제는 **만들 방법이 없다**는 것이다: 썸네일 URL 은 `A-1` 때문에 viz-render 의 성공 응답에서 나오지 않는다. **`A-1` 을 안 고치면 `K-2` 는 영구히 죽은 필드다.**

**`[RECOMMENDATION]`** 계약 개정 **불요**. `A-1` 이 닫히면 core-api 가 렌더 성공 시 그 값을 카탈로그에 도장 찍는 **코드**만 남는다. stage 1 완료 정의에 목록 썸네일이 없으므로 **stage 2 로 미뤄도 된다** — 미룬다면 필드 설명에 그 사실을 적는다(문서만).

### ⬜ A-3 `PreviewArtifacts.sidecar`·`world_file` 이 ②에 없다 — 정상

**`[EVIDENCE]`** `jobs.py:318-328` · `core-viz.yaml:413-427`. `DR-9` 대로 좌표 없는 산출물에 좌표 파일을 안 붙인다. **소음이다. 조치 없음.**

---

## B. 계약이 선언하지 않은 필드를 코드가 읽거나 쓴다 / 선언만 있고 아무도 안 쓴다

### 🟧 B-1 `/previews` 두 op 이 **503 을 내는데 계약에 `"503"` 이 없다** — `〈87〉` 이 그 코드를 *선례로 인용까지 했다*

**`[EVIDENCE]`**

- `services/core-api/src/colab_core/app/routes/preview.py:32` — `RENDER_UNAVAILABLE = "RENDER_UNAVAILABLE"`.
- 같은 파일 `:69` `:77` `:91` `:96` — **네 자리에서 `errors.ApiError(503, RENDER_UNAVAILABLE, …)`.**
- `services/core-api/tests/test_preview_relay.py:179` — `assert r.json()["code"] == "RENDER_UNAVAILABLE"` (실동작 시험이 있다).
- `contracts/seams/fe-core.yaml:1282-1337` — `createPreviewRender`·`getPreviewRender` 의 `responses` = **400·401·403·404·500.** `"503"` 이 **없다.**
- ⚠ `contracts/seams/fe-core.yaml:484` — `〈87〉` 이 신설한 `searchDatasets` 의 503 설명이 **「`createPreviewRender` 의 `RENDER_UNAVAILABLE` 과 같은 모양이다」**라고 적었다. **없는 선례를 근거로 인용했다.**

**무엇이 언제 깨지는가** — `DR-7` 의 정확한 모양이다: **소비되는 표면인데 계약 어디에도 없다.** 계약을 믿는 다음 구현자는 `/previews` 에서 503 을 예상하지 않는다. 생성 타입에도 503 갈래가 없어 FE 는 `r.data` 부재로만 알아채고(`previewSource.ts:33`) **「미리보기를 시작하지 못했어요」라는 일반 문구**로 접는다 — `〈87〉-㉯` 가 검색에서 명시적으로 금지한 **「못 닿았다와 0건을 접는」 처리**와 같은 모양이다.

**`[RECOMMENDATION]`** **계약 개정 필요.** 두 op 에 `"503"` ＋ `ErrorEnvelope` 를 더하고 설명에 `RENDER_UNAVAILABLE` 을 못 박는다. `〈87〉` 의 검색 503 과 **같은 문장 구조**로 쓴다.

### 🟧 B-2 `getUploadStatus` 가 **격자 파일의 축 배정·수용 여부를 말할 자리가 없다** — 그런데 그것이 `〈79〉` 가 `ready` 의 뜻에 넣은 사실이다

**`[EVIDENCE]`**

- `contracts/seams/fe-core.yaml:1878-1917` — `UploadStatus` 속성 전수: `uploadId`·`files`·`ready`·`renderable`·`metadataComplete`·`expiresAt`·`failure`. `additionalProperties: false`.
- `contracts/seams/fe-core.yaml:1849-1862` — `UploadFileRef` 는 `fileId`·`fileName`·`kind`·`byteSize` **넷뿐**이다. `gridAxis` 가 없다.
- 반면 `contracts/seams/fe-core.yaml:2321-2329` — **등록 뒤의** `DatasetFile` 에는 `gridAxis` 가 있고 설명이 이유를 적었다: 「**화면이 뒤집기 버튼을 그리려면 지금 배정이 무엇인지 알아야 한다**」.
- `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:291-293` — 축 거절은 `res.rejected[file_id] = why` 라는 **파이썬 딕셔너리 안의 산문**으로만 남는다. 어떤 이벤트 페이로드에도 실리지 않는다.
- `contracts/events/core-pipeline.json:185-203` — `UploadReadyPayload` = `renderable`·`metadataComplete`·`expiresAt`. **격자 판정 결과를 실을 자리가 없다.**
- `services/core-api/src/colab_core/domains/d5_ingestion.py:60-65`(`_FILES`) ＋ `app/routes/ingestion.py:198` — `getUploadStatus.files` 는 `d5_upload_file` 을 그대로 읽는다.

**⚠ 여기서 파생하는 조용한 오작동** — `services/core-api/src/colab_core/domains/d5_ingestion.py:103-115`(`accept()`)는 **`기준 격자 파일` 행을 아예 만들지 않고 `continue` 한다**(축을 모르면 `0004` CHECK 를 못 지나므로 의도된 것이다). 그런데 `createUpload` 의 **201 응답**(`app/routes/ingestion.py:182`)은 `records` 전체 = **격자 포함**을 돌려준다.
**결과 — 접수 직후 `UploadReceipt.files` 에 있던 격자 파일이, 곧이어 부른 `getUploadStatus.files` 에서 사라진다.** 워커가 축을 확정하면 다시 나타나고, **거절하면 영영 안 나타난다.** 화면 입장에서 **파일이 조용히 사라졌다 나타났다 한다.**

**무엇이 언제 깨지는가** — `S1-PLAN-REFOUND §E.2` 의 상태 **③격자 확인 중 · ⑤위치 확인 · ⑥⑦⑧ 거절 3종**은 전부 「워커가 이 격자를 어떻게 판정했는가」를 알아야 서는데, **그 사실이 seam 을 건너오지 않는다.** 지금 화면이 그 상태들을 만드는 유일한 근거는 **viz-render 의 렌더 실패 문장**이다(→ `C-1`). 즉 **판정자(워커)와 화면이 인용하는 근거(렌더러)가 다른 기계**다. 두 기계의 격자 검증 사다리가 갈라지는 순간(**이미 갈라져 있다** — `C-1`⑵) 화면이 틀린 사유를 말한다.

**`[RECOMMENDATION]`** **계약 개정 필요.** 최소 형태로:
- `UploadFileRef` 에 `gridAxis`(`GridAxisAssignment`, `kind = 기준 격자 파일` 일 때만) — `DatasetFile` 과 **같은 모양**을 쓴다. 새 스키마를 만들지 않는다.
- `UploadStatus` 에 `gridRejections`(배열, 각 항목 = `fileName` ＋ **구조화된 사유 코드**) — 사유 코드는 `C-1` 이 세우는 것과 **같은 enum** 을 쓴다. 두 번 만들지 않는다.

### ⬜ B-3 `metadataComplete` 가 stage 1 에서 **언제나 `false`** 다 — 「읽어 보고 아니었다」와 「안 읽었다」가 접혔다

**`[EVIDENCE]`**
- `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:192-202` — `stage1` 분기는 `metadata_complete=False` **고정**이다.
- 같은 파일 `:194-196` 주석이 스스로 적었다 — 「**「읽어 보고 아니었다」와 「안 읽었다」를 갈라 적을 자리가 계약에 없어서**, 원장 열은 NULL 로 남긴다」.
- `contracts/events/core-pipeline.json:195-197` — 계약은 그 값을 「자동 메타 다섯 값을 **모두 읽었는가**」로 정의하고, `false` 의 뜻을 화면 동작(자동 칸 → 입력 칸)에 묶었다.

**무엇이 언제 깨지는가** — 화면 동작 자체는 우연히 옳다(stage 1 은 자동 메타가 없으니 입력 칸이 맞다). **깨지는 것은 stage 2 다** — 헤더 파싱이 켜지는 순간 `false` 가 두 뜻을 갖고, 그때 이 값을 읽는 코드가 어느 쪽인지 알 수 없다.

**`[RECOMMENDATION]`** **계약 개정 불요 · 문서만.** stage 1 에서 이 값이 언제나 `false` 이고 **그것이 「안 읽었다」의 뜻**임을 `UploadReadyPayload` 설명에 한 줄로 적는다. 값 집합을 3값으로 넓히는 것은 **stage 2 의 일**이다.

### ⬜ B-4 `HeaderParsed`·`CrsNormalized`·`CogBuilt` 세 이벤트가 stage 1 에서 **선언만 있고 발행되지 않는다** — 의도된 것이다

**`[EVIDENCE]`** `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:192-202` 가 `stage1` 에서 ⑥으로 직행한다. `d5/events.py:19-26` 는 7종을 그대로 들고 있고 `contracts/events/core-pipeline.json:300-311` 의 `AnyEvent` 도 7종이다.

**무엇이 언제 깨지는가** — **아무 일도 안 난다.** `〈73〉` 이 「건너뛴 구간을 지우지 않는다」로 못 박은 자리다. **소음으로 표시한다.** 조치 없음.

---

## C. 산문으로 인코딩된 구조 — 조용한 파손 생성기

### ⛔ C-1 격자 거절 사유가 **한 코드 아래 한국어 문장**으로 오고 FE 가 정규식으로 가른다 — 그리고 **지금 이미 두 군데가 틀렸다**

**`[EVIDENCE]`**

계약 쪽:
- `services/viz-render/src/colab_viz/domains/d7_visualization/failures.py:24` — 사다리 1·2·3단(형상 불일치 · 짝 불일치 · 축 판별 실패)이 **전부 `REFERENCE_GRID_MISSING` 한 코드**로 나간다.
- `contracts/schemas/common.json:22-32` — `ErrorEnvelope.details` 는 `{"type": "object"}` = **자유 객체.** 구조를 요구하지 않는다.
- `contracts/seams/fe-core.yaml:1327-1329` — `getPreviewRender` 설명이 「실패 종류의 `code` 값 라벨은 `[정본 무근거]` 로 **아직 신설하지 않았다** (…Ted 답 대기)」. 그런데 FE 는 이미 그 코드들에 **하드 의존**한다.

화면 쪽:
- `frontend/src/components/upload/gridFlow.ts:88-92` — `FAILURE_CODE` 3값에 하드 의존.
- 같은 파일 `:145` — `const SHAPE = /\(([0-9,\s]+)\)/g;`
- 같은 파일 `:155-180` — `classifyGridRejection()` 이 **서버 문장을 정규식으로** 가른다: `/축을 판별하지 못했다/` → `/형상 불일치|짝이 아니다/` → `/격자 형상이 데이터와 안 맞는다/`.
- `:150-153` 주석이 인정했다 — 「**⚠ 가르는 근거가 서버 문장뿐이다.** … 계약에는 그것을 나눌 필드가 없다」.

**⚠ 실측한 오작동 둘 — 가정이 아니다.**

**⑴ 정규식 순서가 복합 문장에서 뒤집힌다.**
`services/viz-render/src/colab_viz/domains/d7_visualization/grid.py:195-197` —
```
f"격자 형상이 데이터와 안 맞는다: 데이터 {tuple(expect_shape)} vs 격자 {shapes}"
+ (f" ({'; '.join(errors)})" if errors else "")
```
`errors` 에는 `_check_pair`(`:42`)의 **`위도/경도 형상 불일치(...)`** 나 `_order_axes`(`:124`·`:127`)의 **`축을 판별하지 못했다(...)`** 가 그대로 들어간다.
`gridFlow.ts:156-157` 은 `축을 판별하지 못했다` → `형상 불일치` 순으로 **먼저 맞는 것에서 멈춘다.** 즉 **「데이터와 형상이 안 맞는다(＋딸린 사유)」가 화면에는 `축 판별 실패` 또는 `짝 불일치` 로 뜬다.** 사용자는 「형상을 맞춘 격자를 올리라」 대신 **엉뚱한 안내**를 받는다. 에러는 안 난다.

**⑵ 같은 문장의 인자 순서가 두 서비스에서 반대다.**
- `services/viz-render/src/colab_viz/domains/d7_visualization/grid.py:196` — `데이터 {expect} vs 격자 {shapes}`
- `services/pipeline-worker/src/colab_pipeline/d5/grid.py:146` — `격자 {grid.shape} vs 데이터 {expect}`
- `gridFlow.ts:167-175` ＋ `:210-218`(`fillBody`)은 **첫 번째 괄호를 `{데이터}`, 두 번째를 `{격자}`** 로 채운다.
→ **워커 쪽 문장이 화면에 닿으면 두 형상이 맞바뀐다.** 화면이 「이 파일은 **격자의 형상**이고, 올리신 격자는 **본체의 형상**입니다」라고 말한다. **거짓말이고 에러가 안 난다.**
*(오늘 워커 문장이 이 화면에 닿는 경로가 있는지는 `[미확인]` — 그러나 `B-2` 를 닫으면 **바로 그 문장을 화면에 실어 나르게 된다.** 즉 `B-2` 의 수정이 이 버그를 활성화한다.)*

**무엇이 언제 깨지는가** — **서버 문장을 한 글자만 다듬어도 화면이 조용히 다른 상태로 넘어간다.** `S1-PLAN-REFOUND §E.2` 가 상태마다 다른 **행동 버튼**(다른 파일 올리기 / 파일 확인 / 등록 계속)을 붙였으므로 오분류는 **사용자를 다른 행동으로 보낸다.**

**`[RECOMMENDATION]`** **계약 개정 필요.**
- `common.json` 에 `GridRejectionReason` **enum** 신설 — `형상 불일치` · `짝 불일치` · `축 판별 실패` **3값.** (`§E.2` 의 ⑥⑦⑧ 과 1:1. **네 번째를 만들지 않는다** — 사다리 4단은 「여기까지 안 온다」이고 5단은 `MAP_BOUNDS_IMPLAUSIBLE` 이다.)
- `core-viz.yaml` 에 `GridRejection` 스키마(`reason` 필수 ＋ `dataShape`·`gridShape`·`latShape`·`lonShape` **정수 배열**)를 세우고, `RenderJob` 에 선택 속성 `gridRejection` 을 둔다. **형상을 문자열로 나르지 않는다** — 숫자를 문장으로 만들었다 되파싱하는 것이 이 항의 원인이다.
- `B-2` 의 `UploadStatus.gridRejections` 는 **같은 enum·같은 형상 표현**을 쓴다.
- ⭑ **`fe-core.yaml:1327-1329` 의 「code 라벨을 아직 신설하지 않았다 — Ted 답 대기」를 같은 회차에 닫는다.** FE 가 이미 3개 코드에 의존하므로 **「대기 중」이 사실이 아니다.**

### 🟧 C-2 `REFERENCE_GRID_MISSING` 한 코드가 **세 가지 다른 사실**을 뜻한다

**`[EVIDENCE]`** `failures.py:22-24` 와 `jobs.py:61-69`. 같은 코드가 ⓐ HSR 에 `withoutReferenceGrid` 를 건 경우(`DR-9`, 진짜 실패) ⓑ 붙인 격자를 못 쓰는 경우(거절) ⓒ 사다리 각 단의 실패에 모두 쓰인다. FE 는 `gridFlow.ts:193-194` 에서 이 코드 하나를 받아 **5개 상태 중 하나**로 갈라야 한다.

**`[RECOMMENDATION]`** `C-1` 이 근본이다. **`C-1` 에 흡수 — 별도 항목으로 묶음에 넣지 않는다.** 코드 자체는 남긴다(지우면 `DR-9` 의 진짜 실패가 갈 자리가 없다).

### ⬜ C-3 `HeaderParsedPayload.crs`·`grid` 가 자유 문자열이다

**`[EVIDENCE]`** `contracts/events/core-pipeline.json:97-105`. 설명이 이유를 명시했다 — **D9(수문학 도메인) 소유의 어휘라 플랫폼이 enum 을 만들지 않는다.** stage 1 은 이 이벤트를 발행하지 않는다(`B-4`). **소음이다.** 조치 없음.

---

## D. 화면이 필요로 하는데 어떤 seam 도 열지 않은 조작

### ⛔ D-1 `listPalettes` 중계가 없어 **실서버에서 미리보기 렌더가 시작되지 않는다** — 최악의 발견

**`[EVIDENCE]`**

- `contracts/seams/core-viz.yaml:172` — `operationId: listPalettes` 는 **`core-viz`(내부 표면)에만** 있다.
- `contracts/seams/fe-core.yaml:1282-1337` — `/previews` 두 op 뿐. **팔레트 중계가 없다.**
- `contracts/seams/fe-core.yaml:1296-1297` — 그 사실이 계약 본문에 적혀 있다: 「`style.palette` 값 집합의 FE 도달 경로(`listPalettes` 중계)는 **이 개정이 열지 않는다 — 열린 항목으로 보고한다**」.
- `contracts/seams/core-viz.yaml:309` — `RenderStyle.required: [palette]`. **팔레트 없이는 렌더 요청 자체가 400 이다.**
- `frontend/src/components/upload/previewSource.ts:26-28` — `async palettes() { throw new PalettesUnreachable(...) }` — **실서버 구현이 항상 던진다.**
- `frontend/src/components/upload/PreviewPanel.tsx:61-80` — `.catch()` 에서 `setPalettes([])` ＋ `setError(UNAVAILABLE)`. `palette` 는 `''` 로 남는다.
- 같은 파일 `:84-85` — `async function draw(...) { if (!uploadId || !palette) return; }` — **즉시 반환한다. `createRender` 가 절대 불리지 않는다.**
- `frontend/src/components/preview/PreviewControls.tsx:3-9` — 상세 쪽도 같은 사실을 적었다: 「⚠ 팔레트 목록의 출처는 `listPalettes` 인데 **그 op 이 FE 표면에 없다**」 · `:29` 화면에 「고를 수 있는 팔레트 목록을 아직 불러올 수 없어요」.
- `frontend/src/routes/UnregisteredPreviewPage.tsx:58,69` — S-08 은 **완료된 렌더의 `legend.palette` 를 되쓴다.** 즉 **첫 렌더를 시작할 수 없고**, 이어받은 `renderId` 가 있어야만 산다.

**무엇이 언제 깨지는가** — 첫 렌더를 거는 자리는 **업로드 모달의 `PreviewPanel` 하나뿐**이고 그 자리가 막혀 있다. 실서버에서:
- `S1-PLAN-REFOUND §F` **완료 정의 2** — 「5 포맷 각 1건에서 **①썸네일·②비지도형이 화면에 뜬다**」 → **뜨지 않는다.**
- **완료 정의 15**(미리보기 3층이 사양대로) · **16**(HSR 격자 흐름 완주) · **18**(색 범위 단계가 화면에서 읽힌다) → **전부 도달 불가.**
- `§E` 의 11 상태 중 ③④⑤⑥⑦⑧⑪ **일곱 개가 도달 불가**다(전부 렌더 결과·실패를 필요로 한다).

**⚠ 왜 시험이 안 잡았나** — 프런트 시험은 전부 픽스처 소스를 주입한다(`frontend/test/upload.test.tsx` 등). **실서버 구현(`previewSource.ts`)만 죽어 있고 시험은 그 파일을 지나지 않는다.** `〈87〉-㉯` 의 「서버가 200 을 내는 바람에 그 자리가 도달 불능이었을 뿐이다」와 **정확히 같은 무늬**다.

**`[RECOMMENDATION]`** **계약 개정 필요 · 4차 묶음의 최우선 항.** `fe-core.yaml` 에 `GET /palettes` → `listPalettes` 중계 op 을 신설한다(`core-viz.yaml#/components/schemas/PaletteOption` 배열을 **재선언 없이 참조** — `createPreviewRender` 와 같은 방식).
**501 표 영향 = +1.** 그것이 옳다 — 지금은 「계약에 없어서 501 표에도 없는」 상태이고, 그 침묵이 이 구멍을 세 회차 동안 감췄다.
*⚠ 대안(팔레트 키를 계약에 박기)은 **기각**한다 — `core-viz.yaml:314` 이 「이름을 계약에 박지 않는다」로 못 박았고, 박으면 팔레트 정본이 화면으로 옮겨 앉는다.*

### ⛔ D-2 등록 전 격자 추가에 op 이 없어, **격자를 붙일 때마다 본체 전체가 재전송되고 업로드가 새로 만들어진다**

**`[EVIDENCE]`**

- `contracts/seams/fe-core.yaml:199-250` — `createUpload` 는 **파일 전건을 한 번에** 받는 것이 유일한 형태다.
- 「업로드에 파일을 더한다」는 op 은 **등록 뒤**에만 있다 — `addDatasetFile`(`fe-core.yaml:611`, 경로가 `/datasets/{datasetId}/files`).
- `frontend/src/components/upload/UploadModal.tsx:153-160` — `pickGrid()` 는 `picked` 배열에 **추가**한다.
- 같은 파일 `:69` — `const signature = picked.map(...).join('|')` · `:70-93` — **`signature` 가 바뀌면 `upload.create(picked)` 를 다시 부른다.**
- `frontend/src/components/upload/uploadSource.ts:11-23` — `create()` 는 `picked` **전건**을 `POST /uploads` 로 보낸다.
- `services/core-api/src/colab_core/app/routes/ingestion.py:157` — `upload_id = Ulid.generate()` — **매번 새 업로드다.**

**무엇이 언제 깨지는가** — HSR 격자 한 장이 실측 26,562,948 B 이고(`S1-PLAN-REFOUND §E.3`) 본체는 조각 묶음이면 훨씬 크다. 격자 2장을 붙이는 순간:
1. **본체 전체가 다시 올라간다** — 화면은 「격자 파일을 받는 중입니다」라고 말하는데 실제로는 본체를 다시 보낸다. **화면이 하는 말이 사실이 아니다.**
2. **`uploadId` 가 바뀐다.** 앞 업로드에 붙어 있던 계보 제안 화면 상태(`UploadModal.tsx:137-146` 의 `lineageCtx.uploadId`)와 이미 그린 미리보기(`renderId`)가 **전부 무효가 된다.**
3. 버려진 업로드가 만료까지 원장에 남는다(reaper 범위 안이라 새는 것은 아니다).

**`[RECOMMENDATION]`** **계약 개정 필요.** `POST /uploads/{uploadId}/files` → `addUploadFile`(multipart: `file` ＋ `kind`)을 신설한다. **`addDatasetFile` 의 등록 전 짝**이고 모양을 그대로 쓴다. **501 표 +1.**
*기각한 대안 = `createUpload` 를 여러 번 부르되 `uploadId` 를 요청에 싣기 — 「접수 = 새 집계 루트」라는 이벤트 계약의 성질(`envelope.json`)을 흐린다.*

### ⛔ D-3 `addDatasetFile` 이 **기준 격자 파일을 400 으로 거절한다** — 계약 요약문이 정반대를 약속한다

**`[EVIDENCE]`**

- `contracts/seams/fe-core.yaml:612` — `summary: 파일 추가 (후주입) — **기준 격자 파일은 나중에 와도 된다**`
- 같은 곳 `:614-615` — 「**`〈58〉-②` 가 요구한 후주입 경로다** — 기준 격자 파일은 나중에 구해서 더할 수 있어야 하고, 없으면 … 계보가 끊긴다」
- 같은 곳 `:631-632` — 요청의 `kind` 는 `FileKind` **2값 전부**를 받는다.
- `services/core-api/src/colab_core/app/routes/ingestion.py:414-419` —
```python
if kind == GRID:
    raise errors.bad_request(
        "기준 격자 파일의 축(위도·경도)은 서버가 파일에서 판별한다 — "
        "그 판별 경로(pipeline-worker)가 아직 이 op 에 연결되지 않았다.")
```
- **이 op 이 존재 이유로 삼은 단 하나의 `kind` 를 거절한다.** 통과하는 것은 `본체` 뿐이고, 본체 후주입은 `〈59〉-③` 이 **금지한** 조작이다.

**무엇이 언제 깨지는가**
- `S1-PLAN-REFOUND §E.1-㈏`(「등록한 뒤 언제든 후주입·교체·삭제」)가 **막혀 있다.**
- **완료 정의 16-ⓑ** — 「나중에 격자를 붙여 **지도형만** 새로 생김」 → **불가능하다.**
- `§E.2-⑨` 의 건너뛰기 안내문(「나중에 데이터셋 상세에서 격자를 올리면…」, `gridFlow.ts:74-76`)이 **거짓 약속**이 된다. **건너뛰기는 `§E.1` 이 지정한 기본 경로다** — 즉 다수 사용자가 이 거짓말을 만난다.

**`[RECOMMENDATION]`** **주로 코드 · 계약은 한 줄.** 축 판별을 워커에 맡기는 비동기 경로 연결이 본체(코드)이고, 계약 쪽에서는 **`addDatasetFile` 에 `202` 응답**이 필요하다 — 격자는 축이 정해지기 전까지 `DatasetFile` 을 낼 수 없으므로 `201 + DatasetFile` 로 답할 수 없다.
*⚠ 지금처럼 400 을 유지하는 선택지도 정직하지만, 그러려면 `:612-615` 의 요약·설명과 `gridFlow.ts:74-76` 의 화면 문구를 **같은 회차에** 되돌려야 한다. 그것은 완료 정의 16-ⓑ 를 포기하는 것이다 — **Ted 판정 사안**이고 이 문서는 「연다」를 권고한다.*

### 🟧 D-4 등록 전 **축 뒤집기**를 부를 계약 경로가 없다 (`§E.2-⑤`)

**`[EVIDENCE]`**

- `contracts/seams/fe-core.yaml:651-711` — `flipAxes` 는 `replaceDatasetGridFile`(`PUT /datasets/{datasetId}/files/{fileId}`) **안에만** 있다. `datasetId` 를 요구하므로 **등록 전에는 부를 수 없다.**
- `frontend/src/components/upload/GridUploadBlock.tsx:18-23` — 주석이 그대로 적었다: 「**⚠ 등록 전에는 부를 계약 경로가 없다** — … 그래서 이 자리는 **핸들러가 있을 때만** 버튼이 선다. 없는 길을 버튼으로 만들지 않는다.」
- `frontend/src/components/upload/UploadModal.tsx:241-248` — 모달이 넘기는 `grid` prop 에 **`onFlipAxes` 가 없다.** → `PreviewPanel.tsx:92` 의 스프레드가 비고 → **버튼이 서지 않는다.**
- `S1-PLAN-REFOUND §E.2-⑤` 는 그 자리에 **[맞습니다] [위도·경도 뒤집기]** 두 버튼을 규정하고, `§E.3` 사다리 **6단(사람의 눈)** 이 이것 없이 성립하지 않는다.

**무엇이 언제 깨지는가** — 등록 전에는 뒤집을 수 없으므로 축이 뒤바뀐 격자를 올린 사람은 **엉뚱한 지도를 본 채 등록하고 나서** 상세에서 고쳐야 한다. `PREVIEW-IMPLEMENTATION §10-16`(「보여주고 뒤집기 버튼을 준다」)이 **등록 전에는 성립하지 않는다.** 완료 정의 16-ⓓ(「뒤집기가 동작」)는 등록 후 경로로 만족되므로 **완료 정의를 막지는 않는다** — 그래서 ⛔ 가 아니라 🟧 다.

**`[RECOMMENDATION]`** **계약 개정 필요 — 단 새 조작을 만들지 않는다.** `D-2` 가 신설하는 `POST /uploads/{uploadId}/files` 의 **짝으로** `PUT /uploads/{uploadId}/files/{fileId}` → `replaceUploadGridFile`(`file` | `flipAxes` 택일)을 둔다. 요청 스키마를 `replaceDatasetGridFile` 과 **공유**한다.
*⚠ `〈80〉-㉯ 3` 이 기각한 `flipGridAxes` 신설과 다르다 — 그 기각의 근거는 「축을 바꾸는 길이 둘이 되어 정본 경로가 흐려진다」였다. 여기서는 **대상 세계가 다르다**(등록 전 업로드 vs 등록된 데이터셋). `addDatasetFile` ↔ `addUploadFile` 과 같은 짝 관계이고, 두 세계가 갈라져 있는 것은 `〈79〉-㈎` 가 이미 세운 사실이다.*
*⭑ 더 작은 대안 — 등록 전 뒤집기를 **포기**하고 `§E.2-⑤` 의 버튼을 「등록 뒤 상세에서 고칠 수 있어요」 안내로 바꾼다. 계약 개정 0. **`S1-PLAN-REFOUND` 개정이 선행**해야 한다(`CLAUDE.md §5`).*

---

## E. 낡은 산문 — 뒤집힌 사실이 계약에 그대로 남아 있는 자리

### ⛔ E-1 `〈87〉` 이 정정한 그 문장이 **같은 파일 다른 세 곳에 그대로 살아 있다**

**`[EVIDENCE]`** `〈87〉-㉮` 는 「`fe-core.yaml#searchDatasets` 의 **낡은 산문 두 문단을 정정했다**」고 적었다. 실물을 세면:

| 자리 | 문장 | 정정됐나 |
|---|---|:--:|
| `fe-core.yaml:436-438` | 「AI 는 **식별자 · 관련도 · 근거 한 줄**만 돌려주고…」 | **⚠ 지워지지 않았다.** `:451-455` 에 **정정문이 덧붙었을 뿐**이고 틀린 문단이 위에 그대로 있다 |
| `fe-core.yaml:449` | 「**`Verified 우선` 정렬은 core 가 다시 세운다** — D2 의 값이라 AI 에 권한 정책을 얹지 않는다」 | 결론은 맞지만 **AI 가 정렬을 낸다는 전제** 위의 문장이다 |
| **`fe-core.yaml:70-74`** (tag `search`) | 「AI 는 **식별자·관련도·근거 한 줄**만 내고 카탈로그 값은 core 가 붙인다」 | **⛔ 정정되지 않았다.** `searchDatasets` op 밖이라 `〈87〉` 의 점검 범위에 없었다 |
| **`fe-core.yaml:19`** (info.description) | 「검색은 `searchDatasets`(이 파일 **`POST /searches`**)가 중계한다」 | **⛔ 경로가 틀렸다.** 실제 경로는 `/dataset-searches`(`:419`)이고 `:430-434` 가 **일부러 다르게 지은 이유까지** 적어 뒀다 |

**무엇이 언제 깨지는가** — `〈87〉-㉮` 가 진단한 실패 그 자체다: 「**계약을 믿은 다음 구현자가 옛 분할을 그대로 되짓는다**」. 세 번째 해제가 op 하나만 고쳤고 **tag 와 info 를 세지 않았다.** 넷째를 부른 것과 **같은 종류의 누락이 이미 파일 안에 남아 있다.**

**`[RECOMMENDATION]`** **계약 개정 필요(산문).** ⓐ `:436-438` 의 틀린 문단을 **지운다**(덧붙이지 않는다 — 계약에 서로 반대인 두 문장이 공존하면 어느 쪽이 정본인지 없다) ⓑ `:70-74` tag 를 다시 쓴다 ⓒ `:19` 의 경로를 `/dataset-searches` 로 고친다.

### ⬜ E-2 `/previews` 산문의 「타일 URL 소비만 FE 직결」이 stage 1 사실과 어긋난다

**`[EVIDENCE]`** `fe-core.yaml:1292-1294`(「**타일 URL 은 중계하지 않는다** — 결과의 `tileUrlTemplate` 을 FE 가 직접 소비한다」) · `:26-28` · `:66-69`. 그러나 `core-viz.yaml:433` — 「**stage 1 은 이 형태를 내지 않는다** — 타일 서빙은 stage 1 밖이다(`〈74〉-㉳`)」 이고 `jobs.py:90-92` 가 실제로 싣지 않는다.

**무엇이 언제 깨지는가** — 지금은 안 깨진다(FE 도 `tiles.ts:24` 에서 `imageUrl` 을 먼저 본다). **stage 2 에 그대로 살아나는 문장**이므로 지우면 안 되고, **stage 1 에서 그 갈래가 비활성임을 한 줄로 적으면 된다.**

**`[RECOMMENDATION]`** **계약 개정 불요 · 문서 한 줄.** 싸므로 4차 묶음에 **선택 항목**으로 붙인다.

### ⬜ E-3 `getPreviewRender` 의 「Ted 답 대기」가 사실이 아니다

**`[EVIDENCE]`** `fe-core.yaml:1327-1329` vs `frontend/src/components/upload/gridFlow.ts:88-92`(FE 가 3개 코드에 하드 의존) · `services/viz-render/.../failures.py:1-6`(그 레인이 「계약을 고치지 않았고 멈출 이유도 없었다」로 닫았다).

**`[RECOMMENDATION]`** `C-1` 이 코드 enum 을 세우면 이 문장이 자동으로 낡는다. **`C-1` 과 같은 회차에 지운다.** 별도 항목 아님.

---

## F. 계약 ↔ DB 불일치

### 🟧 F-1 `topic` — 계약은 자유 문자열, DB 는 4값 CHECK, 서버는 **검사하지 않는다**

**`[EVIDENCE]`**
- `db/platform/versions/0003_p1_topic_check.py:31` — `TOPICS = "'강우·강수', '식생·NDVI', '지형·DEM', '토지피복·LULC'"` · `:83` — `CHECK (topic IS NULL OR topic IN ({TOPICS}))`.
- `contracts/seams/fe-core.yaml:1965-1967`(`DatasetCreate.topic`) — 「값 집합은 **DB CHECK 4값이 지킨다**(`〈55〉`) — 계약 층 enum 은 이 개정이 임의로 만들지 않는다」 · `type: [string, "null"]`.
- `contracts/seams/fe-core.yaml:1487-1494`(`FilterTopic`) — `items: { type: string, minLength: 1 }`.
- `grep -rn "강우·강수\|TOPIC" services/core-api/src` = **0건.** 서버에 검증이 없다.
- `services/core-api/src/colab_core/app/routes/ingestion.py:330-333` — `topic=body.get("topic")` 이 그대로 DB 로 간다.

**무엇이 언제 깨지는가** — **계약에 맞는 요청이 500 을 받는다.** `topic: "강수"` 는 스키마 통과 → CHECK 위반 → `IntegrityError` → 500. 400 이어야 할 것이 500 이고 **화면은 「알 수 없는 오류」를 보여준다.**

**`[RECOMMENDATION]`** **계약 개정 불요.** `DatasetCreate`·`DatasetUpdate` 처리 시 4값 대조 후 400 을 내는 **코드** 한 자리면 닫힌다. 값 목록의 정본은 `〈55〉` 대로 DB 다 — 계약에 enum 을 새로 만들면 정본이 두 곳에 생긴다.
*⭑ 실물 확인 — 나머지 CHECK 11종(`role`·`switch`·`state`·`default_visibility`·`origin`·`parent_role`·`kind`·`status`·`type`·`direction`·`source`)은 **`common.json` 의 enum 과 값·개수가 정확히 일치한다.** 어긋난 것은 `topic` 하나다.*

---

## G. 이벤트 계약이 필요로 하는 것

`〈73〉` 배선 후의 실제 발행은 **감지 → `file.format-detected` → `upload.ready`** 두 단계이고(`services/pipeline-worker/src/colab_pipeline/app/worker.py:15` · `domains/d5_ingestion.py:179,199`), 이벤트 계약은 7종을 그대로 들고 있다. 그 자체는 `〈73〉` 대로다(→ `B-4`, 소음).

**이벤트 쪽에서 실제로 필요한 것은 하나뿐이고 그것은 `B-2` 다** — `UploadReadyPayload` 에 「함께 올라온 격자의 축이 확정됐는가/거절됐는가」를 실을 자리가 없다. `〈79〉-⑷` 가 **`ready` 의 뜻에 그 문장을 넣었는데**(「본체 감지가 끝났고, 함께 올라온 격자 파일의 축이 확정되거나 거절됐다」) **페이로드에 그 사실이 없다.** 완료 정의 4 는 「시험으로 박혀 있다」로 만족되지만, **소비자(core-api·FE)는 이벤트만 보고는 알 수 없다.**

**`[RECOMMENDATION]`** `B-2` 의 `UploadStatus.gridRejections` 와 **같은 모양**을 `UploadReadyPayload` 에 선택 속성 `gridResolution`(파일별 `fileId` ＋ `gridAxis` | `rejectionReason`)으로 더한다. **⚠ `〈80〉-㉯ 8` 이 이벤트 계약을 연 유일한 회차였다** — 여기서 안 실으면 다음 해제까지 못 싣는다.

---

# 「4차 해제 묶음 — 제안」

> **체크리스트 순서 = 실행 순서다.** 앞 항이 뒤 항의 값 집합을 만든다. 순서를 바꾸면 같은 enum 을 두 번 만들게 된다.
> **⚠ 이 묶음의 점검 축** — 「갈래를 열었다」(`〈80〉`) · 「갈래마다 필수가 다르다」(`〈85〉`) · 「구현이 산문을 뒤집었다」(`〈87〉`)에 더해, 이번에는 **「그 응답을 부를 op 이 있는가」**를 세웠다.

| ☐ | 항목 | 파일 | 값 | 근거 | 501 |
|:--:|---|---|---|---|:--:|
| **1** | **`GridRejectionReason` enum 신설** | `contracts/schemas/common.json` | `형상 불일치` · `짝 불일치` · `축 판별 실패` **3값** | `C-1` — 지금 FE 가 **서버 한국어 문장을 정규식으로** 가르고, 복합 문장에서 **이미 오분류한다**(`gridFlow.ts:156-157` × `viz grid.py:195-197`). 서버가 문장을 다듬는 순간 화면이 조용히 다른 상태로 넘어간다 | — |
| **2** | **`GridRejection` 스키마 ＋ `RenderJob.gridRejection`** | `contracts/seams/core-viz.yaml` | `reason`(1의 enum, 필수) ＋ `dataShape`·`gridShape`·`latShape`·`lonShape`(**정수 배열**) | `C-1`⑵ — 두 서비스가 같은 문장의 **인자 순서를 반대로** 쓴다(`viz grid.py:196` vs `worker grid.py:146`). 숫자를 문장으로 만들었다 되파싱하는 것이 원인이므로 **숫자로 나른다** | — |
| **3** | **`RenderResult` 에 `thumbnailUrl`·`valuePreviewUrl`** | `contracts/seams/core-viz.yaml` | 둘 다 **선택 속성.** `oneOf`·`dependentRequired` 무수정 | `A-1` — ①썸네일이 **성공 응답에 실릴 자리가 없어** 실패 봉투로만 나간다. `〈83〉-㉮` 가 닫았다고 선언한 그 모양이 한 필드 옆에 남아 있다. 이것 없이는 `K-2`(`A-2`)가 영구히 죽은 필드다 | — |
| **4** | **`listPalettes` FE 중계 신설** | `contracts/seams/fe-core.yaml` | `GET /palettes` → `PaletteOption[]`. 스키마는 `core-viz.yaml` 참조(**재선언 금지**) | **`D-1` — 최악의 항.** `RenderStyle.required: [palette]` 인데 FE 가 팔레트를 얻을 계약 경로가 없어 `PreviewPanel.tsx:85` 가 `createRender` 를 **한 번도 부르지 않는다.** 완료 정의 **2·15·16·18** 이 통째로 닫힌다. 계약 본문(`fe-core.yaml:1296-1297`)이 **「열지 않는다」고 명시하고 남겨 둔** 자리다 | **+1** |
| **5** | **`addUploadFile` 신설** | `contracts/seams/fe-core.yaml` | `POST /uploads/{uploadId}/files` (multipart: `file`＋`kind`). `addDatasetFile` 과 같은 모양 | `D-2` — 없으므로 격자를 붙일 때마다 `createUpload` 가 다시 불려 **본체 전체가 재전송되고 `uploadId` 가 바뀐다**(`UploadModal.tsx:69-93` × `ingestion.py:157`). 계보 제안·미리보기 상태가 통째로 무효화된다 | **+1** |
| **6** | **`replaceUploadGridFile` 신설** | `contracts/seams/fe-core.yaml` | `PUT /uploads/{uploadId}/files/{fileId}` (`file` \| `flipAxes` **택일**). 요청 스키마를 `replaceDatasetGridFile` 과 공유 | `D-4` — `§E.2-⑤` 의 **[위도·경도 뒤집기]** 가 등록 전에 부를 경로가 없어 버튼이 서지 않는다(`GridUploadBlock.tsx:18-23`). `〈80〉-㉯ 3` 이 기각한 `flipGridAxes` 와 **다르다** — 대상 세계가 다르고(`〈79〉-㈎`), `addDatasetFile`↔`addUploadFile` 과 같은 짝이다 | **+1** |
| **7** | **`UploadFileRef.gridAxis` ＋ `UploadStatus.gridRejections`** | `contracts/seams/fe-core.yaml` | `gridAxis` = `GridAxisAssignment`(`DatasetFile` 과 동일) · `gridRejections` = `[{fileName, reason(1의 enum), shapes…}]` | `B-2` — `§E.2` 의 **③⑤⑥⑦⑧ 다섯 상태**가 seam 에 근거가 없다. 그리고 지금은 접수 201 에 있던 격자 파일이 조회 200 에서 **조용히 사라진다**(`ingestion.py:182` vs `d5_ingestion.py:103-115`) | — |
| **8** | **`UploadReadyPayload.gridResolution`** | `contracts/events/core-pipeline.json` | 파일별 `fileId` ＋ (`gridAxis` \| `rejectionReason`). 7의 값 집합 그대로 | `G` — `〈79〉-⑷` 가 **`ready` 의 뜻에 격자 판정을 넣었는데 페이로드에 그 사실이 없다.** ⚠ **`〈80〉-㉯ 8` 이 이벤트 계약을 연 유일한 회차였다 — 여기서 안 실으면 다음 해제까지 못 싣는다** | — |
| **9** | **`/previews` 두 op 에 `"503"` 신설** | `contracts/seams/fe-core.yaml` | `ErrorEnvelope` ＋ `code = RENDER_UNAVAILABLE` | `B-1` — 코드가 **네 자리에서** 내고 시험까지 있는데(`preview.py:69,77,91,96` · `test_preview_relay.py:179`) 계약에 없다. ⚠ **`fe-core.yaml:484` 가 그 없는 표면을 「같은 모양이다」로 인용했다** — `DR-7` 그 자체 | — |
| **10** | **`addDatasetFile` 에 `"202"` 추가** | `contracts/seams/fe-core.yaml` | 「격자는 축 확정 뒤 `listDatasetFiles` 에 나타난다」 | `D-3` — 요약문이 「**기준 격자 파일은 나중에 와도 된다**」인데 코드가 그 `kind` 를 **400 으로 거절한다**(`ingestion.py:414-419`). 완료 정의 **16-ⓑ** 와 `§E.2-⑨` 의 화면 약속이 거짓이 된다. ⚠ **Ted 판정 필요** — 여는 대신 접으려면 `S1-PLAN-REFOUND` 개정이 선행한다 | — |
| **11** | **낡은 산문 정정** | `contracts/seams/fe-core.yaml` | ⓐ `:436-438` 틀린 문단 **삭제**(덧붙임 아님) ⓑ `:70-74` tag `search` 재작성 ⓒ `:19` 경로 `/searches` → `/dataset-searches` ⓓ `:1327-1329` 「Ted 답 대기」 삭제 ⓔ(선택) `:1292-1294` 에 「stage 1 은 타일 갈래를 내지 않는다」 한 줄 | `E-1`·`E-3`·`E-2` — **`〈87〉` 이 op 하나만 보고 tag·info 를 세지 않았다.** 넷째를 부른 것과 **같은 종류의 누락이 이미 파일 안에 남아 있다.** ⓐ 를 삭제로 하는 이유 = 서로 반대인 두 문장이 공존하면 정본이 없다 | — |

**501 표 예상 변동 = 21 → 24** (항목 4·5·6). **퇴행이 아니다** — 세 op 전부 **지금 화면이 필요로 하는데 계약이 침묵해서 표에도 없던** 것이고, 그 침묵이 이 구멍들을 세 회차 동안 감췄다. `P2.md §2-19` 의 「목록이 줄어드는 것이 진척의 계측」은 **표에 이미 있던 행**에 대한 말이다.

**⚠ 묶음의 완결성 근거** — 항목 **1·2·7·8** 은 **같은 값 집합(격자 거절 사유·축 배정)** 을 네 표면에 세우는 하나의 일이다. 넷 중 하나라도 빼면 그 표면만 다시 문장으로 말하게 되고 **다섯 번째 해제의 씨앗이 된다.** 항목 **4·5·6** 은 **등록 전 세계의 op 셋**이고, 셋이 함께 있어야 `§E` 의 11 상태가 닫힌다.

---

# 「이 묶음 밖 — 그리고 왜」

| 발견 | 왜 밖인가 |
|---|---|
| **`A-2` `DatasetRow.thumbnailUrl` 이 죽은 필드** | **항목 3 이 원인을 닫는다.** 필드는 이미 있고 남는 것은 생산자 코드뿐이다. stage 1 완료 정의에 목록 썸네일이 없으므로 **stage 2 로 미뤄도 된다** — 미룬다면 필드 설명 한 줄(문서) |
| **`B-3` `metadataComplete` 가 언제나 `false`** | **문서만.** 값 집합을 3값으로 넓히는 것은 헤더 파싱이 켜지는 **stage 2 의 일**이다. 지금 넓히면 stage 1 소비자가 쓰지 않는 값을 다뤄야 한다 |
| **`B-4` ③④⑤ 이벤트 미발행** | **`〈73〉` 이 「건너뛴 구간을 지우지 않는다」로 이미 판정했다.** 계약 변경 0 |
| **`C-2` `REFERENCE_GRID_MISSING` 의 과부하** | **항목 1·2 에 흡수된다.** 코드 자체는 남겨 둔다 — 지우면 `DR-9` 의 진짜 실패(HSR ＋ `withoutReferenceGrid`)가 갈 자리가 없어진다 |
| **`C-3` `crs`·`grid` 자유 문자열** | 어휘 소유자가 **D9(수문학 도메인)** 이다. 플랫폼이 enum 을 만들면 `DOMAINS §3-③` 위반이다. **소음** |
| **`F-1` `topic` 이 500 을 낸다** | **계약이 아니라 코드다.** 값 목록의 정본은 `〈55〉` 대로 DB 이고, core-api 가 4값 대조 후 400 을 내면 닫힌다. 계약에 enum 을 만들면 정본이 두 곳에 생긴다 |
| **업로드 전송 퍼센트 막대에 바이트 출처가 없음** | **⭑ 계약 사안이 아니다 — 클라이언트 아키텍처다.** `gridFlow.ts:103` · `PreviewPanel.tsx:34,312` · `GridUploadBlock.tsx:26-38` 이 `transfer` 를 **끝까지 배관해 뒀는데 생산자만 없다** — `UploadModal.tsx:241-248` 이 `transfer` 를 안 넘긴다. 원인은 `fetch`(openapi-fetch)가 **업로드 진행 이벤트를 노출하지 않는** 것이고, `XMLHttpRequest.upload.onprogress` 또는 스트림 요청 본문으로 **FE 안에서** 닫힌다. **서버가 줄 수 있는 사실이 아니므로 계약에 실을 것이 없다.** ⚠ 지금 `§E.2-②`(「격자 파일을 받는 중입니다」＋퍼센트 막대)는 **실서버에서 도달 불가**하다 — 다만 `Progress`(`GridUploadBlock.tsx:28-31`)가 **퍼센트를 지어내지 않고 불확정 표시로 떨어지므로 거짓말은 하지 않는다.** 그래서 ⛔ 가 아니다 |
| **`A-3` 사이드카·월드파일이 ②에 없음** | `DR-9` 대로다. **소음** |

---

## 다섯 번째 해제를 아직 부를 수 있는 것 — 감추지 않는다

1. **⭑ 항목 10(`addDatasetFile` 202)이 Ted 판정 사안이다.** 「연다」가 아니라 「접는다」로 판정되면 완료 정의 16-ⓑ 와 `§E.2-⑨` 화면 문구를 **같은 회차에** 되돌려야 하고, 그것은 계약이 아니라 `S1-PLAN-REFOUND` 개정이다. **판정 전에 항목 10 을 실행하면 안 된다.**
2. **stage 2 를 열 때 `RenderResult` 의 타일 갈래가 다시 열린다.** 그때 `thumbnailUrl`(항목 3)이 타일 갈래에도 붙는지, `dependentRequired` 에 새 줄이 필요한지는 **이 스윕이 세지 않았다** — stage 1 범위 밖이라 일부러 안 셌다. **stage 2 첫 회차의 점검 항목으로 넘긴다.**
3. **`listPalettes` 를 열면 팔레트 3종의 라벨이 화면에 선다.** 그 라벨(`PaletteOption.label`)은 viz-render 소유이고 **정본에 팔레트 이름이 없다**(`P2-viz-report §8 V-1`). 화면에 서는 한국어 라벨이 필요해지면 **정본 확장 판정**이 먼저다 — 계약이 아니라 정본의 문제이므로 다섯 번째 해제를 부르지는 않는다.
4. **`eval/` 이 0건이라 검색 품질 회귀를 잴 수 없다**(`03-HANDOFF §4 #13`). 검색 계약은 `〈87〉` 로 정합됐지만 **`interpretation.terms` 가 실제로 쓸모 있는지**는 `[미측정]` 이다. 계약이 아니라 평가셋의 문제다.
5. **`〈81〉-㉲` 의 `ts_config = 'simple'` 이 Ted 판정 자리로 열려 있다.** 값이 바뀌면 생성 열 전 행이 재생성되지만 **계약 표면은 안 바뀐다.**

**⭑ 이 스윕이 자신에 대해 말할 수 있는 것** — 세 회차가 놓친 축(「op 이 있는가」)을 이번에 세웠고 그 축에서 **네 건**(`D-1`~`D-4`)이 나왔다. 그러나 **「축을 하나 더 세웠다」가 「모든 축을 세웠다」는 아니다.** 위 5건 중 1번이 판정으로 닫히면 4차가 마지막일 **가능성이 높다**고 말할 수 있고, **그 이상은 말할 수 없다.**
