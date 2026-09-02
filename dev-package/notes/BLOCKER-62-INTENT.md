# 블로커 #62 — `DatasetCreate` 의 `variables`·`crs`·`period` 계약↔런타임 드리프트, 의도 조사

> 읽기 전용 조사 (2026-09-02 · `main` @ `bde2f0d`). **고친 파일 0.** 게이트 미실행(호스트 슬롯 공유 — 쓰기 레인 가동 중).
> 근거 서열 = `PLAN-SoT.md §9` · `work-items.yaml` > `03-HANDOFF.md` · `WORK-UNITS.md`.

---

## 1. 실측 현상 — 비대칭의 정확한 모양

**⑴ 계약 선언 자리**

| 필드 | `DatasetCreate` | `DatasetUpdate` | 응답 |
|---|---|---|---|
| `variables` | `contracts/seams/fe-core.yaml:2628` | `:2699` | `DatasetBasics` 경유 — `d3_catalog.py:78`·`:100`·`:165` |
| `crs` | `:2634` | `:2703` | 같음 |
| `period` | `:2637` (`oneOf` → `DataPeriod`) | `:2706` | 같음 |

`DatasetCreate` 는 `additionalProperties: false` 이고 `required: [uploadId, name]` (`fe-core.yaml:2601`~).

**⑵ 서버 수용 목록**

- `services/core-api/src/colab_core/app/routes/ingestion.py:390`
  `_ALLOWED_CREATE_FIELDS = {"uploadId","name","topic","summary","sourceLabel","lineageParents","projectIds"}` — **세 필드 없음.**
- 강제 자리 = `ingestion.py:445`~`447` — `unknown = set(body) - _ALLOWED_CREATE_FIELDS` → `errors.bad_request("계약에 없는 필드다: …")`.
  ⟹ **코드로 확인된 400.** 조용한 무시가 아니라 명시적 거부다.
- 같은 무늬의 기존 시험 = `services/core-api/tests/test_dataset_registration.py:102`~`112` (`processingLevel` 을 실으면 400 을 단언). 세 필드에 대한 시험은 **없다**.

**⑶ UPDATE 경로는 셋 다 받는다**

- `services/core-api/src/colab_core/app/routes/catalog.py:418`~`419`
  `_UPDATE_FIELDS = ("name","topic","summary","sourceLabel","representativeFileId","variables","crs","period")`
- 저장 대응표 = `services/core-api/src/colab_core/domains/d3_catalog.py:655`~`657` (`variables`·`crs` → `d3_dataset_autometa`), `period` 는 `:678`~`:682` 에서 `period_start`·`period_end` 두 열로 갈라 쓴다.

**⑷ 그 외 경로**

- 자동완성 질의 `listDatasetFieldSuggestions` — `catalog.py:200` · `d3_catalog.py:202` `SUGGESTABLE_FIELDS = ("sourceLabel","variables","crs")`. **`variables`·`crs` 는 이미 「사람이 치는 자유 입력 칸」 전제로 서버가 서 있다.**
- 응답에는 셋 다 있다 (`d3_catalog.py:78` SELECT · `:165` 행 매핑).

⟹ **비대칭 = 계약 CREATE ✅ / 계약 UPDATE ✅ / 서버 UPDATE ✅ / 서버 CREATE ❌ / 응답 ✅.**
`LV-1`(`〈276〉`)이 닫은 `processingLevel` 과 같은 무늬지만 **방향이 반대다** — 그때는 계약만 열려 있고 **양쪽 서버가 다 막혀** 있었다. 여기는 **UPDATE 만 구현돼 있다.**

---

## 2. 의도 — 판정 = **누락(omission)**

**근거 ㉮ — 계약 확대는 명시적 판정이었다.**
`PLAN-SoT.md:434` `〈138〉` (Ted 2026-08-27) = 정본 `POLICY-20260825-001` 핵심규칙 1 「자동으로 읽는 값은 **포맷과 용량뿐**」 · `VAL-006` 「변수·기간·좌표계는 **자유 입력 · 선택 입력**」. 즉 **세 필드를 사람이 적는 값으로 옮긴다**가 판정 본문이다.
계약 서술이 그 반전을 축자로 적고 있다 — `fe-core.yaml:2583`~`2589`.

**근거 ㉯ — 계약 개방 커밋이 서버 구현을 「다음 커밋」으로 미뤘다.**
`869ee64` 「계약을 한 번 연다 — 「올리고 고친다」를 한 벌로 (Ted 판정 ㈏)」 (2026-08-27 02:22) 커밋 본문:
- 「⑴ `DatasetCreate` — `processingLevel`·`variables`·`crs`·`period` **추가**」
- 「**마이그레이션 0 · 서버 구현 0** — 이 커밋은 계약과 생성물뿐이다. **소비자는 다음 커밋.**」

**근거 ㉰ — 다음 커밋은 UPDATE 만 구현했다.**
`fff3034` 「updateDataset 을 구현한다 — 501 표가 23 → 22 로 준다 (〈127〉)」 (2026-08-27 02:46). 본문 = 「대상은 Ted 판정 ㈏로 넓어졌다 — … 원천 표기·가공 단계·대표 조각·**변수·좌표계·기간**까지」. **CREATE 경로는 이 커밋에도, 이후 어느 커밋에도 없다** (`git log 869ee64..HEAD -- routes/ingestion.py` 에 해당 변경 없음).

**근거 ㉱ — 뒤집은 판정이 없다.**
`PLAN-SoT.md §9` 〈1〉~〈278〉 전수 검색에서 `DatasetCreate` 의 세 필드를 **빼기로 한 항목은 없다.** `work-items.yaml` 에도 없다. `〈276〉`-㉸ 는 이 자리를 **「고치지 않았다 · 소유·처분 미정」**으로 세운 것이 전부다 (`PLAN-SoT.md:627`).

**근거 ㉲ — 동결 프로토콜이 바로 이 모양을 사후에 금지했다.**
`sessions/X2-FREEZE-PROTOCOL.md:139` ㉰-4 = 「**집행 없는 신설** — 계약만 열고 구현을 다음 회차로 미루는 것」 = **승인으로도 열지 않는 금지 항목.** 이 규약은 `〈163〉`(2026-08-27, `869ee64` 와 같은 날 뒤)로 효력을 얻었다.

⚠ **부수 발견 — `869ee64` 는 동결 해제 회차 번호를 못 받았다.** `X2-FREEZE-PROTOCOL.md §1` 회차표(1~13차)에 `〈138〉`·`〈140〉`·`869ee64` 가 **없다**. 8차는 `〈180〉`(2026-08-28)이다. 이 자리가 이력에서 빠진 것 자체가 누락의 방증이다.

**⟹ 판정 = 의도적 미구현이 아니라 누락.** 계약 확대는 Ted 판정으로 의도됐고, 서버 집행이 UPDATE 절반에서 멈춘 뒤 아무도 나머지 절반을 세우지 않았다.

**단, 「지금도 그 판정이 유효한가」는 `[미확인]` 이다** — §5 를 보라. 등록 화면이 세 칸을 아직 **읽기 전용 `자동`** 으로 그리고 있어, 정본(`VAL-006`)과 화면이 어긋난 채로 남아 있다. 이 어긋남을 어느 쪽으로 맞출지는 사람 판정이다.

---

## 3. 오늘 이 값을 채우는 것은 누구인가

**⑴ 저장 자리** — `db/platform/schema.sql:397`~`400`: `d3_dataset_autometa.variables text[] NOT NULL DEFAULT '{}'` · `period_start`·`period_end timestamptz` · `crs text`. **열은 이미 있다.**

**⑵ 등록 시** — `d3_catalog.py:485`~`489` `_INSERT_AUTOMETA` 는 `format`·`bundle_file_name`·`total_size_bytes` **셋만** 넣는다. 세 필드는 등록 시점에 **아무도 안 채운다.**

**⑶ 파이프라인** — 워커가 `file.header-parsed` 를 발행한다 (`services/pipeline-worker/src/colab_pipeline/d5/events.py:151`~`155` — `variables`·`period`·`crs`·`grid`). core-api 가 `_APPLY_AUTOMETA` (`d3_catalog.py:499`~`519`)로 반영하되 **비어 있는 칸만 채운다** (`COALESCE` · `variables` 는 `cardinality > 0` 이면 보존). 주석 축자 = 「사람이 고친 값(`update_dataset` 의 `crs`·`variables`)을 사건이 덮으면 사용자의 수정이 조용히 사라진다」.

**⑷ 사람** — `PATCH /datasets/{datasetId}` 뿐이다 (`catalog.py:418`).

**⑸ staging 실측 (2026-09-02 · 읽기 전용 조회 · `d3_dataset_autometa` 전수)**

| 지표 | 값 |
|---|---|
| 전체 행 | **13** |
| `cardinality(variables) > 0` | **1** |
| `crs` 비-NULL | **1** |
| `period_start` 비-NULL | **0** |
| `period_end` 비-NULL | **0** |

⟹ **파이프라인이 이 셋을 사실상 채우지 못하고 있다** (13건 중 1·1·0·0). 기간은 **한 건도 없다.** 「파이프라인이 채우니 생성 수용은 설계상 틀렸다」는 반대 가설은 **실측이 지지하지 않는다.**

---

## 4. 두 방향의 비용

### ⓐ 서버를 넓힌다 (수용 목록에 셋을 넣는다)

| 축 | 값 |
|---|---|
| 계약 변경 | **0** ⟹ **동결 해제 불요** |
| 마이그레이션 | **0** — 열이 이미 있다 (`schema.sql:397`~`400`) |
| 파일 | `routes/ingestion.py`(`_ALLOWED_CREATE_FIELDS:390` ＋ 검증 블록 ＋ `create_dataset` 인자 전달) · `domains/d3_catalog.py`(`_INSERT_AUTOMETA:485` 열 4 추가 · 등록 호출부 `:833`~`:850` 대응) |
| 검증 | `variables` = 문자열 배열 · 빈 문자열 금지(계약 `minLength: 1`) · `crs` = 문자열/`null` · `period` = `DataPeriod` 형상 ＋ `period_start <= period_end` CHECK (`schema.sql:405`) 선제 검사 |
| 시험 | `tests/test_dataset_registration.py` — 양성 1(셋 실어 등록 → 상세에 반영) ＋ 음성 1(`period_start > period_end` 400) |
| 파이프라인 충돌 | **없다.** `_APPLY_AUTOMETA` 가 이미 「비어 있는 칸만」이라 등록 시 넣은 사람 값을 헤더 파싱이 덮지 않는다. **단, 「폼 기본값 통과 ≠ 사람이 적었다」를 지켜야 한다** — 빈 배열·빈 문자열을 값으로 저장하면 자동 반영이 영영 막힌다(`〈140〉`-㉱ 와 같은 실패형). |
| 남는 것 | 등록 화면이 세 칸을 아직 읽기 전용으로 그린다 (`RegisterArea.tsx:71`~`74`) — 서버만 넓히면 **쓰는 사람이 여전히 0** 이다. 화면 레인이 따로 필요하다. |

### ⓑ 계약을 좁힌다 (`DatasetCreate` 에서 셋을 뺀다)

| 축 | 값 |
|---|---|
| 동결 해제 | **필요 — 14차** (직전 13차 = `〈276〉`) |
| 등급 | **㉯ (Ted 승인 필수)** — 마이그레이션 0 · 소비자 0 이지만 **㉮-4 「설계 판단 0건」을 못 채운다**(`〈138〉` Ted 판정과 정본 `VAL-006` 을 뒤집는 판단이다). `X2-FREEZE-PROTOCOL.md:115`~`130` |
| 게이트 예측 | `contract-breaking` = `[request-property-removed]` × 3 · **ERR 0 · WARN 3** (13차 `〈276〉` 의 필드 2 제거가 WARN 2 였다 — 같은 규칙) |
| 파일 | `contracts/seams/fe-core.yaml`(`:2628`~`:2650` 3필드 ＋ `DatasetCreate` 서술 개정) · 생성물 `frontend/src/generated/fe-core.ts` 재생성 |
| 소비자 파괴 | **없다** — §5 참조(보내는 소비자 0) |
| 제품 손실 | 등록 화면에서 변수·좌표계·기간을 적을 계약상 자리가 사라진다. 사람이 채우려면 **등록 후 `PATCH` 한 번을 더** 해야 한다. `〈138〉`-㉱(자유 입력 ＋ 자동완성)의 절반이 영구히 닫힌다. |

---

## 5. 소비자 — 세 필드를 생성에 싣는 곳: **0건**

- `frontend/src/components/upload/UploadModal.tsx:279`~`287` — `createDataset` 바디는 `uploadId`·`name`·`topic`·`summary`·`sourceLabel`·`lineageParents`·`projectIds` **7개뿐**. 세 필드 **없음**.
- 호출부 = `frontend/src/components/upload/uploadSource.ts:42`~`43` (`api.POST('/datasets', { body })`) — 바디를 그대로 넘긴다.
- 등록 화면 = `frontend/src/components/upload/RegisterArea.tsx:71`~`74` — `변수`·`기간`·`좌표계` 를 **`AutoField`(읽기 전용 · `자동` 배지 · `value=""`)** 로 그린다 (`:30`~`:40`). **사람이 칠 칸이 아예 없다.**
- `frontend/src` 전체에서 `variables` 참조는 **상세 화면 읽기 1건 ＋ 픽스처 2건** (`components/detail/BasicInfoGrid.tsx:10` · `components/detail/fixture.ts:65`·`:98`).
- 자동완성 op `listDatasetFieldSuggestions` 는 **서버만 서 있고 프런트 소비자가 0** 이다 (`catalog.py:200` · `frontend/src` grep 0건).

⟹ **`〈138〉` 의 화면 절반이 통째로 미구현이다.** 서버 CREATE 누락은 그 미구현의 한 조각이지, 독립 사건이 아니다.

---

## 6. 권고

**권고 = ⓐ 서버를 넓힌다. 다만 지금 당장이 아니라, 등록 화면 레인과 같은 회차에 묶는다.**

**결정적 사실 하나** — `〈138〉`(Ted 2026-08-27)이 정본 `VAL-006` 을 근거로 세 필드를 **「사람이 적는 값」으로 확정했고, `§9` 〈1〉~〈278〉 어디에도 그것을 뒤집은 항목이 없다.** 계약이 넓은 것은 그 판정의 결과이며 실수가 아니다. 좁히는 것은 **판정을 뒤집는 일**이라 14차 해제 ＋ Ted 승인이 필요하고, 넓히는 것은 **계약 무변경 · 마이그레이션 0** 이다. 비용도 되돌림 가능성도 ⓐ 가 싸다.

**보강 사실** — staging 13건 중 `variables` 1 · `crs` 1 · `period` 0 (2026-09-02). 파이프라인이 채우지 못하고 있으므로 **사람 입력 경로를 닫으면 이 세 칸은 사실상 영구 공란이 된다.**

**⚠ 지금 권고를 집행으로 바꾸지 못하게 막는 것 — 사람 판정 1건.**
서버만 넓히면 **쓰는 소비자가 0인 표면이 하나 더 생긴다**(`RegisterArea.tsx` 가 읽기 전용). 이는 `X2-FREEZE-PROTOCOL §5-㉰-4` 가 금지한 「집행 없는 신설」과 같은 모양이다. 그래서 물어야 할 것은 「넓히나 좁히나」가 아니라 —

> **등록 화면의 변수·좌표계·기간을 `자동` 읽기 전용에서 자유 입력 ＋ 자동완성으로 바꾸는가** (= `〈138〉`-㉱ 를 마저 집행하는가), **아니면 등록은 이름 위주로 두고 세 값은 상세에서 고치게 하는가.**
> 전자면 ⓐ · 후자면 ⓑ 다. **이 한 문장이 방향을 결정하고, 기록은 이것을 정하지 않았다 — `[미확인]` 이다.**

소유 WU 는 그 판정 뒤에 정한다 — 화면이 걸리면 등록 화면 레인, 서버만이면 카탈로그·등록 레인이다.
