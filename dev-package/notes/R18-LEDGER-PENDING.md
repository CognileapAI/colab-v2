# R-18 — 대장 반영 대기분 (레인 `lane-r18` · 2026-09-05)

✅ **등재 완료 → `§9 〈319〉`·`〈320〉`** (2026-09-05 병합 준비 회차 · `origin/main` 최대 `〈318〉` ＋1 로 실측 배정).
초안은 지우지 않는다 — 원장 행은 이 초안의 축약이고 값·근거의 전문은 여기에 있다.

⛔ ~~**결정 번호를 예약하지 않았다.** 아래 `〈N〉`·`〈N+1〉` 은 자리 표시이고, 실번호는~~ **⟨배정 2026-09-05⟩ `〈N〉` = `〈319〉` · `〈N+1〉` = `〈320〉`.** 종전 문면 ↓ 실번호는
**병합 직전 `origin/main` 최대 ＋1 로 오케스트레이터가 실측해 채운다**(선례 = 이 레포의 번호 규약).
레인은 `PLAN-SoT.md §9` 에 직접 쓰지 않는다.

⚠ ~~**이 브랜치는 창 5 가 닫히기 전에 병합되지 않는다 — 다음 창을 타고 간다.**~~
⭑ **⟨정정 2026-09-05⟩ 창 5 는 닫혔다**(`§9 〈318〉` = 단독 창 5b 단계 B 등재) — **이 병합이 그 다음 창이다.**
단독 창 5(레인 `lane-window-a5b`)의 A 단계가 도는 중이고 이 레인은 그 창에 접촉하지 않았다
(staging 0 · 배포 0 · push 0 · `gates/run.sh all` 0회 — pg 슬롯 경합 회피).

전제 = Ted 판정 2026-09-05 두 건 · 출처 = 대장 `work-items.yaml` `CR-2` 완료 정의 ⑴·⑷ ·
원 발견 = `sessions/CODE-REVIEW-20260903-B.md §6`(계약 델타 초안) · `PLAN-SoT §9 〈307〉`-㉷⑴·⑷.
회차 행 = `sessions/X2-FREEZE-PROTOCOL.md §1` **18차**.

---

## 1. 〈319〉 — 판정 ① 계약 동결 해제 18차 (**집행**)

> **제목안** — 「계약 동결 해제 18차 — `createPreviewRender` 가 이미 내고 있던 413·415 를 계약이 뒤따라 선언한다」

**등급 = ㉯**(`X2 §5`). **규칙 줄 = §5-㉮ 조건 3 「소비자 0건 — `frontend/src/` ＋ 서비스 코드
전수 grep 으로 해당 op·필드 호출 0건임을 출력으로 증명」 미충족.** §5-㉮ 는 5조건 AND 이고
「하나라도 미충족이면 ㉯ 로 간다」. 실측 소비자 —

```
$ grep -rn "'/previews'" frontend/src | grep -v generated/
frontend/src/components/datasetpreview/datasetPreviewSource.ts:66
frontend/src/components/preview/previewSource.ts:59
frontend/src/components/upload/previewSource.ts:38
$ grep -rn "status === 415" frontend/src | grep -v generated/ | wc -l
4
```

⭑ **17차(`〈303〉`)가 같은 모양의 선례다** — `getDataset` 에 `410` 하나를 더한 순수 가산인데
`contract-breaking` ERR 0 · 마이그레이션 0 이면서도 **등급 ㉯** 였다(소비자 ≥ 1).
「가산이면 ㉮」가 아니라 **「소비자 0건이면 ㉮」**가 규칙이다.
**인가 = Ted 판정 2026-09-05 「계약에 선언 · 18차 · 가산」 그 자체.**

### 1-1. ⛔ 실측이 지시문·초안보다 좁다 — 12 쌍이 아니라 **2 쌍**이다

`CR-2` ⑴ 축자는 「`createPreviewRender`·`listPalettes`·`lookupDatasetValue` 의 410/413/415/422 선언」이고
**op × 코드 대응을 적고 있지 않다**(3 × 4 = 12 쌍으로 읽힐 수 있다). 원 발견
(`CODE-REVIEW-20260903-B.md §6`)도 「세 op 의 `responses` 에 415·413·410·422 를 더한다」로 뭉뚱그렸다.
**「op 이 내지 않는 코드를 더하지 않는다」**는 규율로 12 쌍을 전수 실측한 결과 —

| op | 410 | 413 | 415 | 422 |
|---|---|---|---|---|
| `createPreviewRender` | ✗ | **✓** | **✓** | ✗ |
| `listPalettes` | ✗ | ✗ | ✗ | ✗ |
| `lookupDatasetValue` | ✗ | ✗ | ✗ | ✗ |

**선언한 것 = 2 쌍.** 나머지 10 쌍을 안 넣은 근거는 아래 실측이다.

| (op, 코드) | 내는 자리 (file:line) | 봉투 `code` |
|---|---|---|
| `createPreviewRender` · **413** | `services/viz-render/src/colab_viz/app/routes/renders.py:88` (`total > settings.max_render_bytes`) | `RENDER_TOO_LARGE` (`viz kernel/errors.py:22`) · `details.limitBytes`·`targetBytes` · 문구 `d7_visualization/failures.py TOO_LARGE_MESSAGE` |
| `createPreviewRender` · **415** | `services/viz-render/src/colab_viz/app/routes/renders.py:102` (`drawable == 0`) | `NOT_RENDERABLE` (`viz kernel/errors.py:24`) · `details.renderableFormats` · 문구 `failures.py NOT_RENDERABLE_MESSAGE` |

**넣지 않은 10 쌍의 근거 (전부 실측 · 추정 0)**

1. **410 은 세 op 중 어느 것도 내지 않는다.** viz 에서 `410` 을 내는 자리는
   `renders.py:148`(`getRenderTile` · `RENDER_EXPIRED`) **하나**이고, **타일은 core-api 를
   통과하지 않는다**(`app/relay.py` 머리말 축자 「타일 URL 을 중계하지 않는다」 ·
   `HttpPreviewRelay` 에 타일 메서드 0건). core-api 의 `errors.gone()`(410 `GONE`)을 부르는
   자리도 `routes/catalog.py:755` **하나**이고 그 op 은 `getDataset`(17차가 이미 선언).
2. **422 도 세 op 중 어느 것도 내지 않는다.** viz 의 `RequestValidationError` 핸들러가
   `main.py:106-108` 에서 **400 `BAD_REQUEST` 로 바꾼다**(core-api 도 `main.py:112-115` 동일).
   서비스 소스 전체에서 `422` 를 내는 줄은 0건이다(`grep -rn "422" services/*/src/` = 통과 집합
   상수 1줄 ＋ 주석 2줄뿐).
   ⭑ `preview.py:270-273` 주석이 그 이력을 적어 두었다 — 「종전에는 타입만 봐서 `{"lat": 200}`
   이 viz 의 pydantic 에서 422 가 됐다」. **`〈307〉` 회차가 그 자리를 core-api 400 으로 이미 닫았다.**
3. **`listPalettes`** — viz `GET /palettes`(`routes/style.py:16-20`)는 200 밖에 없다.
   경계 헤더도 안 읽고(`require_caller` 만) 본문·파라미터가 없어 검증 실패 경로 자체가 없다.
4. **`lookupDatasetValue`** — viz `POST /value-lookups`(`routes/values.py:52-79`)가 내는 것은
   404(`TargetNotFound`) ＋ 400(경계 헤더 없음 · 검증) 뿐이고, `value_lookup.lookup_timed` 는
   **`raise` 가 0건**이다(자리에 산출물이 없어도 `available:false` 로 **200**).
   게다가 이 op 의 viz 요청 본문은 **core-api 가 검증된 값으로 직접 조립한다**
   (`preview.py:290-293` — ULID·`fileId`·범위검사 통과 `lat`/`lon`) ⟹ 422 유발 입력이 도달할 수 없다.

⚠ **`relay.py:PASS_THROUGH_STATUSES = (400, 404, 410, 413, 415, 422)` 는 그대로 둔다.**
그 집합은 **중계의 규율**(저쪽 판정을 두 번 판정하지 않는다)이지 op 별 발생 목록이 아니다.
계약을 그 집합에 맞춰 넓히면 **아무도 내지 않는 코드를 계약이 약속**하게 되고, 그것은
`〈299〉` 가 세운 「생산자 없는 것을 계약에 박지 않는다」를 정확히 어긴다.

### 1-2. 무엇이 바뀌었나

| 층 | 변경 | 파일 |
|---|---|---|
| 계약 | `createPreviewRender` 에 `"413"`·`"415"` **2건**. **스키마 신설 0 — 기존 `ErrorEnvelope` 재사용**(`common.json#/$defs/ErrorEnvelope`) · op 총계 **55 그대로** | `contracts/seams/fe-core.yaml` |
| 생성물 | 재생성 **+44 −0** | `frontend/src/generated/fe-core.ts` |
| 서버 | **0 줄** — 코드가 먼저 내고 있었고 계약이 뒤따르는 자리다(`DR-7`) | — |
| 시험 | core-api 신설 1 · viz 단언 강화 3 (아래 §1-4) | `services/core-api/tests/test_relay_status_passthrough.py` · `services/viz-render/tests/test_errors.py` |
| 마이그레이션 | **0** (`db/platform`·`db/ai` diff 0) | — |
| 정본 | **무개정** — 두 코드의 근거는 이미 `Policy_데이터셋_상세 §8`(500MB 상한 `[가정]` · 그릴 수 있는 형식 안내)에 있고 `core-viz.yaml#createRender` 가 이미 선언한 값이다 | — |

### 1-3. 게이트 실측

```
contract-breaking : 2 changes: 0 error, 0 warning, 2 info
  info [response-non-success-status-added] fe-core.yaml  POST /previews  status `413`
  info [response-non-success-status-added] fe-core.yaml  POST /previews  status `415`
  → 게이트 출력: "No breaking changes to report, but the specs are different."
                 "contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음."
contract-lint        green — seam 3건, 룰 위반 0
generated-up-to-date green — 등기부 4건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건
frontend-typecheck   green — tsc --noEmit 오류 0건
frontend-test        green — vitest 38파일 / 595건 통과 · 실패 0
op 총계             55 → 55 (fe-core `grep -c "operationId:"`)
```

### 1-4. 시험 — 신설 1 · 인용 2 · 강화 3

⚠ **red 선확인이 성립하지 않는 회차다 — 숨기지 않고 적는다.** 이 회차는 **서버 0 줄**이고
계약·생성물만 움직였다. 「구현 전 red」는 동작을 바꿀 때의 오라클이므로, 여기서 red 를
만들려면 **일부러 코드를 부수는 수밖에 없고** 그것은 오라클이 아니다.
대신 **단언이 살아 있음을 변이(mutation)로 증명**했다.

| (op, 코드) | 시험 | 상태 |
|---|---|---|
| `createPreviewRender` · 415 | `services/core-api/tests/test_relay_status_passthrough.py:105` `test_a_415_from_viz_reaches_the_screen_with_its_renderable_formats` — 봉투 전문 대조(`code == "NOT_RENDERABLE"` 포함) ＋ `details.renderableFormats` 비어 있지 않음 | **인용**(중복 신설 안 함) |
| `createPreviewRender` · 415 | `services/viz-render/tests/test_errors.py:49` `test_그릴_수_없는_포맷은_415_…` — **실파일**(`메모.txt`)로 실제 415 를 유발 | **인용 ＋ 단언 강화** (`body["code"] == "NOT_RENDERABLE"` 한 줄 추가 — 종전엔 키 존재만 쟀다) |
| `createPreviewRender` · 413 | `services/core-api/tests/test_relay_status_passthrough.py` `test_a_413_from_viz_reaches_the_screen_with_its_render_too_large_envelope` — 봉투 전문 대조 ＋ `details.limitBytes` | **신설 1** |
| `createPreviewRender` · 413 | `services/viz-render/tests/test_errors.py:31` `test_렌더_상한을_넘으면_413` — `max_render_bytes=1024` 로 실제 413 유발 | **인용 ＋ 단언 강화** (`code == "RENDER_TOO_LARGE"` ＋ `limitBytes`·`targetBytes` — 종전엔 「코드가 비어 있지 않다」까지) |

**변이 증명** — 기대 문자열을 `RENDER_TOO_LARGE_XX`·`NOT_RENDERABLE_XX` 로 바꾸자
`test_errors.py` 가 **2 failed, 6 passed** 로 red. 되돌린 뒤 **8 passed**.
⟹ 단언이 진짜로 값을 재고 있다(공허하지 않다).

**실행 결과** — core-api `test_relay_status_passthrough.py` ＋ `test_palettes_relay.py` ＋
`test_preview_relay.py` **38 passed** · viz-render `test_errors.py` **8 passed**.

### 1-5. 이 회차가 재지 않은 것 (다음 회차의 진입조건)

- **staging 무접촉 · 배포 0 · push 0 · 병합 0.** 실서버에서 413·415 가 나는 것은 배포 뒤에만 잰다.
- **`gates/run.sh all` 0회** — 창 5 의 A 단계와 pg 슬롯이 겹쳐 돌리지 않았다. 나머지 게이트 종은 `[미확인]`.
- **화면에 `413` 전용 분기가 0건이다**(`grep -rn "413" frontend/src` 비생성물 0건 · 415 는 4곳).
  413 은 지금 일반 오류 경로로 떨어지고 봉투의 문구(「미리보기는 500MB까지 그려요…」)만 노출된다.
  **결함이 아니라 미측정 축이다** — 「조각 하나를 골라 그린다」 안내를 화면이 따로 세울지는 판정 대상.
- **`CR-2` ⑴ 의 나머지 셋은 이 회차가 열지 않았다** — `core-viz.yaml` 경계 헤더 선언 ·
  `getRender` 400 · `ScreenshotRequest.layers maxItems 8`. **판정을 받지 않은 것이 아니라
  이 지시문의 범위가 `fe-core.yaml` 세 op 이었다.** 다음 해제 회차가 진다.

---

## 2. 〈320〉 — 판정 ② 렌더 산출물 영구 보존 유지 (**기록만 · 코드 0 · 계약 0**)

> **제목안** — 「등록된 데이터셋의 렌더 산출물에 수명을 두지 않는다 — 데이터셋엔 만료일이 없고 회수는 소유 판정이 맡는다」

⭑ **별도 행을 권고한다** — 근거 셋. ⑴ 판정 대상이 다르다(§1 은 계약 표면, 여기는 **보존 정책**).
⑵ **계약·코드 0 인 판정**이라 18차 회차 행에 섞으면 「18차가 무엇을 열었나」가 두 뜻을 갖는다
(`X2 §1` 축자 「발급 이력을 고치는 것은 이력 파괴다」와 같은 선). ⑶ 선례 = `〈306〉`(정본·판정 전용 행).
**최종 판단은 오케스트레이터가 한다.**

### 2-1. 문면 정정 — 「만료일을 안 적은 것」이 아니라 **「만료일이 없다」**

⛔ **지시문 초안의 전제(「`expires_at` 없이 등록된 데이터셋」)가 실물과 다르다.**
`expires_at` 이 실재하는 자리는 **셋뿐**이고 **데이터셋은 그중에 없다** —

| 자리 | 근거 |
|---|---|
| 접근 허가 | `db/platform/schema.sql:188` `d2_dataset_access_grant.expires_at`(＋`:189` `CHECK (expires_at > approved_at)`) · 계약 `fe-core.yaml:2444` |
| 세션 | `fe-core.yaml:2207/2213` `required: [token, expiresAt]` |
| 임시 업로드 | `db/platform/schema.sql:601` `d5_upload.expires_at` · 계약 `fe-core.yaml:2615-2616` 축자 「임시 업로드의 수명(`upload.ready.expiresAt` — 이 화면을 벗어나면 사라진다)」 |

**`d3_dataset` 에는 만료 열이 0건이다**(`grep -n "expires_at" db/platform/schema.sql` = 위 둘 ＋ 인덱스·RLS 참조뿐).
⟹ **「사람이 기한을 안 준 데이터셋」이라는 대상은 존재하지 않는다.** 데이터셋은 **만료 개념이 없는 대상**이다.

### 2-2. 물음과 판정

- **원 물음**(`CODE-REVIEW-20260903` ⑷ 하위) = 「**임시 업로드는 만료되는데, 등록 뒤 렌더 산출물엔
  만료 개념이 없다 — 수명을 둘 것인가**」.
- **Ted 판정 2026-09-05 = 수명을 두지 않는다(영구 보존 유지).**
- **결정 사실** — ⑴ 데이터셋은 **만료 개념이 없는 대상**이고(§2-1), ⑵ 회수는 **소유 판정**이
  이미 맡는다(원천이 사라지면 고아 — `artifact-ownership` 네 등급 · `A-1`·`RC-1`·`TL-1` 계열).
  기한을 새로 발명하면 **회수 규칙이 두 곳**(수명 시계 ＋ 소유 판정)이 되고 그때 한쪽만 고쳐진다.
- **집행 = 0.** 계약 0 줄 · 코드 0 줄 · 마이그레이션 0 · 화면 0.

### 2-3. `CR-2` ⑷ 나머지 세 하위 항목의 처분 (이 회차가 **집행하지 않았다**)

| 하위 항목 | 처분 | 근거 |
|---|---|---|
| `artifact-ownership.toml` `tolerate=true` 기한 | **`〈315〉` 로 대체됨(superseded)** — 기한 연장이 아니라 **구판 재굽기 후 재계수**이고, **그 창(staging 창)이 집행한다** | `work-items.yaml` `RC-1` note 축자 「판정 불가 19벌 = 걸린 데이터셋을 다시 굽고 `artifact-ownership` 을 재계수한다 — `tolerate` 기한 연장이 아니다」 |
| compose 비밀값 `_FILE` 전환 | **배포개선 회차 소관** — 이 레인이 열지 않는다 | `CODE-REVIEW-20260903-B.md §5-㈏` 축자 「`compose.i2.yml` 의 `COLAB_CORE_SESSION_SECRET`·`COLAB_CORE_VIZ_SERVICE_TOKEN` 을 `*_FILE` ＋ `0600` 자격 파일로 · **둘을 동시에 두면 앱이 뜨지 않는다**」. 읽는 쪽(core-api `resolve_env_or_file`)은 `〈307〉` 이 이미 열었고 **남은 것은 compose 뿐**이다 |
| 발행 재시도 DLQ | **배포개선 회차 소관** — 이 레인이 열지 않는다 | `CR-2` 완료 정의 ⑷ 축자 |

⟹ **`CR-2` ⑷ 는 이 회차로 「전건 판정」이 아니라 「하나 판정 ＋ 셋 귀속」이다.**

---

## 3. `CR-2` 조건별 현황 (이 회차 종료 시점)

| 조건 | 상태 |
|---|---|
| ⑴ 계약 델타 | **부분 집행** — `fe-core.yaml` 세 op 의 413/415 실측분 **2 쌍 선언 완료(병합·배포 대기)** · `core-viz.yaml` 경계 헤더 · `getRender` 400 · `ScreenshotRequest.layers maxItems 8` **미착수** |
| ⑵ 로그인 제한 클라이언트 버킷 | **무변** — 지금 ⓑ(XFF 마지막 홉) · ⓒ(nginx `X-Real-IP`)는 배포측 후속 |
| ⑶ 배포 뒤 재굽기·소유 재실측 | **무변** — staging 배포 선행 요구 · 창이 진다 |
| ⑷ 넷 | **하나 판정(렌더 수명 = 영구 보존) ＋ `tolerate` 기한은 `〈315〉` 로 대체 ＋ `_FILE`·DLQ 는 배포개선 회차 귀속** |
| ⑸ CI 인프라 red 둘 | **무변** — `schema-gates`·`planning-gates` · main 사전존재 |

⟹ **`CR-2` 는 닫히지 않는다.** 다섯 중 완결은 0이고 ⑴⑷ 가 전진했다.
