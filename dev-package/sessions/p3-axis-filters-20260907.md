# WU-B7 — 3축 목록 필터·상세 3행 ＋ `M-10` 색인 재정의 (레인 `p3-axis-filters` · R-B)

> 회차 = R-B · 라운드 파일 `dev-package/prd/rounds/R-B-2-server.md` · 근거 PRD-05·06·21 ·
> 계약 동결 해제 **20차 · 등급 ㉯ · Ted 승인 2026-09-07**.
> 기준 sha(Step 0 · `git merge --ff-only integration/r-b`) = `b9821007975716ae6a3378746187b6c52cbc4861`.

---

## 1. 완료 조건 ↔ 판정 ↔ 근거

| 완료 조건 (라운드 §5 축자) | 판정 | 근거 |
|---|---|---|
| 3축이 **AND** | green | `tests/test_axis_filters.py::test_the_three_axes_are_combined_with_and` |
| 각 축에 `미지정` 항목이 있어 재선택 대상을 찾을 수 있다 | green | 같은 파일 `test_unspecified_*` 3건 · 화면 `axis-filters-20260907.test.tsx` ㈎-2 |
| 상세 3행이 이 순서이고 값 문자열이 목록 필터와 같다 | green | `test_detail_carries_the_three_axis_values_as_the_filter_strings` · 화면 ㈐ |
| `topic` 파라미터가 살아 있고 description 에 「이관 중 · 신규 사용 금지」 | green | `test_the_topic_parameter_is_kept_for_one_release` · `contracts/seams/fe-core.yaml` `FilterTopic` |
| `M-10` — `nc` 로 잡힌다 | green | `db/platform/tests/0019-assertions.sql` C-⑴ · `0019-existing-rows-assertions.sql` ① |
| `M-10` — `netcdf` 가 종전과 같이 잡힌다(회귀) | green | 같은 두 파일 C-⑵ · ② |
| `M-10` — 변수명 검색이 종전과 같이 잡힌다(회귀) ＋ **새 행도** | green | C-⑶ · ③④⑦ |
| `M-10` — 색인 재생성이 **1회** | green | `0019-drift.sh` ㈒ (생성 컬럼 ADD 1 · GIN CREATE 1) · `migration-single-head` |
| 존치 6종 · `topic`·`variables`·`format` 열 무변 | green | `0019-assertions.sql` E-⑴ |
| B3/B4/B5/B6 회귀 | green | `service-tests-core-api` 902건 · `frontend-test` |

## 2. 수용 기준 표 (라운드 WU-B7 · `M-10`)

| # | Given / When / Then | 시험 |
|---|---|---|
| B7-⑴ | `category=수문 인자` → 그 분류만 | `test_category_filter_returns_only_that_category` |
| B7-⑵ | 세 축 동시 지정 → AND | `test_the_three_axes_are_combined_with_and` |
| B7-⑶ | 유형 NULL 행 ＋ `dataType=미지정` → 그 행이 나온다 | `test_unspecified_data_type_finds_the_null_rows` |
| B7-⑷ | 상세 3행 순서 ＋ 값 문자열 일치 | 서버 1건 ＋ 화면 3건 |
| M-10-⑴ | `nc` 검색 | `0019-*` C-⑴ · ① |
| M-10-⑵ | `netcdf` 회귀 | C-⑵ · ② |
| M-10-⑶ | 변수명 회귀 ＋ 새 행 | C-⑶ · ③④⑦ |
| M-10-⑷ | 재계산·재생성 1회 | `0019-drift.sh` ㈒ |

## 3. RED → GREEN

- **서버** — `services/core-api/tests/test_axis_filters.py` 13건 작성 → 선실측 **red 8 / pass 5**.
  red 한 줄 축자: `FAILED tests/test_axis_filters.py::test_category_filter_returns_only_that_category - AssertionError: {...}`.
  구현 뒤 **13/13 green**.
- **화면** — `frontend/test/axis-filters-20260907.test.tsx` 9건. 구현을 걷어 낸 트리에서 재측정 →
  `Error: Failed to resolve import "../src/components/catalog/axisFilters"` · `Test Files 1 failed`.
  구현 복원 뒤 **9/9 green**.
- **기존 시험 2건 개정** — `detail.test.tsx`·`interval-period-20260906.test.tsx` 의 「기본 정보 아홉 칸」
  오라클을 **열두 칸**으로. 근거 = WU-B1 세션 노트 §인계 축자 「화면 칸 수(아홉)는 세지 않는다 —
  상세 3행은 PRD-06 · WU-B7」. **아홉 칸의 라벨·순서는 무변**이다(앞에 셋이 붙었다).
- **`test_registration_does_not_write_autometa_variables` 개정** — §6 참조.

## 4. `M-10` 설계 선택 — **㈏(미러 열)**

생성 컬럼은 **같은 행의 열만** 참조한다. `category` 는 `d3_dataset_description` 에, 색인은
`d3_dataset_autometa` 에 있다. 두 갈래 중 ㈏ 를 골랐다.

- ㈎ **트리거가 유지하는 평범한 tsvector 열** — `format`·`variables`·`crs`·`grid`·
  `bundle_file_name`·`file_extension` **여섯 열 전부**의 갱신을 트리거가 떠맡는다. 한 열이라도
  빠지면 색인이 조용히 낡고, **그 낡음은 오류를 내지 않는다**.
- ㈏ **미러 열 `d3_dataset_autometa.category_mirror` ＋ 생성 컬럼 유지** ← 고른 쪽.
  트리거가 보는 것은 **사본 두 칸**(`category_mirror`·`variables`)뿐이고 나머지는 DB 가
  하던 대로 유지한다. **작은 변경**이고 실패 표면이 좁다.

쓰기 정본은 원천 표 하나다 — 미러를 사람·응용이 직접 쓰지 않는다.

**트리거 3개** — `d3_dataset_variable_mirror`(행 표 → 배열 · insert/update/delete) ·
`d3_dataset_description_category_mirror`(분류 → 미러) ·
`d3_dataset_autometa_pull_mirrors`(메타 행이 **뒤에** 생기는 등록 경로를 `BEFORE INSERT` 로 덮는다).

## 5. 마이그레이션

- head = `0019_rb7_search_index_m10` · 24자 (`alembic_version_platform.version_num` 은 `varchar(32)`).
- `down_revision = "0018_rb6_lv0_source"` · `0019-drift.sh` `PREV_REV` 도 같다.
  ⚠ **작업 중에는 `0018` 이 `integration/r-b` 에 없었다** — 그동안 `0017` 에 이어 두고
  드리프트 오라클을 green 으로 실측했고, `0018` 이 내려온 뒤(`integration/r-b` `5adf9b4`)
  **리베이스 ＋ 두 줄 재연결 ＋ 재실측**을 했다. head 이름은 겹치지 않는다(`0019` ↔ `0018`).
- 순서가 **1회**를 강제한다 — ① 색인 DROP ② 생성 컬럼 DROP ③ 미러 열 ADD ④ **백필**
  ⑤ 생성 컬럼 ADD(전 행 재계산 1회) ⑥ GIN CREATE(1회) ⑦ 트리거.
  백필을 ⑤ 앞에 두는 것이 요점이다 — 뒤에 두면 백필 UPDATE 가 생성 컬럼을 **다시** 계산한다.
- **GIN 재생성 계수 = 1** · **생성 컬럼 재정의 계수 = 1**. 델타 SQL 에서 세고(`0019-drift.sh` ㈒)
  `migration-single-head` 가 head 1개를 잰다.
- **NO FORCE 창** — `d3_dataset_autometa`·`d3_dataset_description`·`d3_dataset_variable` 셋 다
  FORCE 다. 마이그레이터 롤은 `colab_owner`(NOSUPERUSER·NOBYPASSRLS)이고 `app.current_lab` 이
  없어 백필이 **오류 없이 0행**으로 끝난다(`0013`·`0016` 이 배운 자리). 백필 구간만 내리고
  곧바로 되올리며, 되올림과 백필 정확성은 **DO 블록 단언 셋**이 DB 에게 되묻는다.
- **되돌림** — `downgrade` 가 트리거·함수·미러 열을 걷고 색인식을 `0018` 형태로 되돌린다
  (같은 순서로 재계산·재생성 1회). **잃는 값이 0** — 미러는 사본이고 원천 두 표가 그대로다.
  되돌린 순간 다시 「`nc` 안 잡힘 · 새 변수 행 색인 밖」으로 간다.
- **선언 순서** — `ALTER TABLE ADD COLUMN` 이 열을 뒤에 붙이므로 `schema.sql` 의
  `d3_dataset_autometa` 에서 `search_vector` 가 **맨 뒤로** 내려갔고 그 앞이 `category_mirror` 다.
  선언이 이 순서와 다르면 `schema-diff` 가 red 다.
- 드리프트 오라클 `db/platform/tests/0019-drift.sh`(소유자 롤 `t_owner` 로 델타 적용) ＋
  `0019-assertions.sql` · `0019-existing-rows-seed.sql` · `0019-existing-rows-assertions.sql`.
  대조군 둘 — ㈑-b **백필을 뺀 델타 → red**(「색인식을 바꿨다」와 「기존 행이 실제로 잡힌다」를 가른다) ·
  ㈑-c **NO FORCE 를 뺀 델타 → 백필 0행 → red**.

## 6. `contract-breaking` 축자

```
COLAB_BREAKING_BASE_REF=b9821007975716ae6a3378746187b6c52cbc4861 ./gates/run.sh contract-breaking
No breaking changes to report, but the specs are different.
Run 'oasdiff diff' to see structural differences.
contract-breaking green — 기준 b9821007975716ae6a3378746187b6c52cbc4861 (3건) 대비 파괴적 변경 없음.
```

⚠ **`DatasetBasicInfo.required` 승격은 응답 쪽이라 oasdiff 가 파괴로 세지 않는다.** 그래도
20차 ㉯ 승인 범위 안에서 집행했다(라운드 ㉰ · Ted 2026-09-07). 승격한 것은 **값이 아니라 열쇠**이고
두 열쇠는 `[string, "null"]` 그대로라 **전 행 NULL 이 계약을 안 깬다**(미결-3 ⓐ 유지).

## 7. 계약 변경 목록

- 질의 파라미터 `category`·`dataType` **신설**.
- `processingLevel` 은 **있던 것을 그대로 쓴다**(PRD-05 축자 「새로 만들지 않는다」) — 정수 조건의
  판정은 한 글자도 안 바뀌었고(WU-B5 회귀) 파수꼴 `미지정` 하나만 더 받는다
  (`items: anyOf[integer, enum["미지정"]]`).
- `FilterTopic` description 에 「이관 중 · 신규 사용 금지」.
- `FacetSet.axes` **신설(선택 열쇠)** — 3축은 표의 **열이 아니다**(정렬 대상이 아니라
  `CatalogColumn` enum 에 넣지 않았다). 옛 소비자는 이 열쇠를 안 본다.
- `DatasetBasicInfo.required` += `category`·`dataType`.

## 8. 파수꼴 `미지정` — 정본은 한 곳

서버 `services/core-api/src/colab_core/app/routes/catalog.py` 의 `UNSPECIFIED` 상수 하나가 정본이고,
계약 산문(`FilterCategory`)과 화면(`frontend/src/components/catalog/axisFilters.ts`)이 그것을 옮겨 적는다.
세 축의 저장값(5·6·4값)에 이 글자가 없어 겹치지 않는다. 가공 단계 축의 파수꼴은 **표시용 값이 아니라
사람이 고른 값(`processingLevelUserSet`)이 NULL 인 행**을 고른다 — 표시용은 파생값으로 채워져
NULL 이 되는 법이 없어 그 행을 표현할 수단이 없다.

## 9. 게이트 (`COLAB_GATE_REPORT_DIR=dev-package/reports/R-B/p3-axis-filters`)

| 게이트 | 계 |
|---|---|
| `contract-lint` | green 1 / red(판정) 0 / red(준비) 0 |
| `contract-breaking` (`COLAB_BREAKING_BASE_REF=b982100…`) | green 1 / 0 / 0 |
| `generated-up-to-date` | green 1 / 0 / 0 |
| `schema-diff` | green 1 / 0 / 0 (§12 — 적용 DB 를 `0019` 로 올린 뒤) |
| `migration-single-head` | green 1 / 0 / 0 |
| `db-boundary` | green 1 / 0 / 0 |
| `autometa-loss` | green 1 / 0 / 0 |
| `rls-effect` | green 1 / 0 / 0 |
| `service-tests-core-api` | green 1 / 0 / 0 (실행 902 · skipped 0 · deselected 6) |
| `frontend-typecheck` | green 1 / 0 / 0 |
| `frontend-test` | green 1 / 0 / 0 |
| `work-item-consistency` | green — 대장과 산문의 불일치 0 |
| `db/platform/tests/0019-drift.sh` | green (게이트 목록 밖 · 이 회차가 신설) |

⚠ **`schema-diff` 는 두 번 red 였다가 green 이 됐다** — 판독은 아래이고, 둘 다 이 레인의
코드 결함이 아니었다.

- **⑴ `0018` 병합 전** — 호스트가 공유하는 「적용 DB」(`COLAB_APPLIED_DB_URL_PLATFORM` ·
  `colab_platform_applied`)가 이미 `alembic_version_platform = 0018_rb6_lv0_source` 로 찍혀
  있는데(**WU-B6 레인이 올렸다**) 그 `0018` 이 `integration/r-b` 에도 이 워크트리에도 없었다.
  그래서 적용 DB 에만 있는 `d3_dataset.source_url`·`source_downloaded_on` 두 열이
  `schema.sql` 에 없었다. `0018` 을 리베이스로 받으면서 사라졌다.
- **⑵ 리베이스 뒤** — 적용 DB 가 `0018` 에 멈춰 있어 이 회차의 `category_mirror`·새 색인식·
  미러 트리거 3개가 적용 DB 에 없었다. **게이트가 요구하는 준비 절차**(`schema-diff.sh` 산문
  「체인마다 DB 를 만들고 → alembic 으로 upgrade head」)를 밟았다 —
  `alembic upgrade head`(스탬프 `0018` → `0019`, 스키마 전용 DB) → **green**.
  ⛔ staging 도 데이터 DB 도 아니다. `0018` 스탬프 위에 `0018` 을 down_revision 으로 갖는
  체인을 올린 것이라 순서가 어긋나지 않는다.

## 10. 자기 표시

- **의존한 오케스트레이터 가정 ⓐ** — `M-10` 색인 재정의의 실체 = **A-1 ⓐ(추가)** ·
  A-2 = 3축은 `d3_dataset_description`(사람 입력)이고 색인 반영은 WU-B7 에서 **미러/생성 열**.
  근거 = `dev-package/intent/2026-09-07-r-b.md` §확인 ＋ `sessions/R-B-C20-REQUEST-20260907.md`.
  **Ted 원문은 「(없음)」이고 이것은 오케스트레이터 가정이다** — 번복되면 `category_mirror` 열과
  `0019` 의 색인식부터 다시 연다. `topic` 은 **애초에 색인식에 없었다**(실측) — 그래서 이 회차가
  한 것은 「재정의」가 아니라 **추가**다.
- **상세 3행의 수정 진입 유도 문면이 `[미상]`** — 라운드 파일·PRD-06 이 「수정 진입 유도」라고만
  적고 축자를 안 줬다. 형제 자리(`설명이 아직 없어요 — 수정에서 채워 주세요.`)의 형식을 따라
  `아직 안 골랐어요 — 수정에서 골라 주세요.` 를 `axisFilters.ts` **한 곳**에 뒀다. 정본 문면이
  오면 그 한 줄만 바꾼다.
- **`FacetSet.axes` 는 라운드 파일이 「패싯 집계」라고만 적은 자리의 구현 선택**이다 —
  `CatalogColumn` enum 을 넓히면 3축이 **정렬 가능한 열**이 되어 계약이 사실과 갈린다.

## 11. 하지 않은 것 (§후속)

- ⛔ **홈 데이터 맵의 주제 축 → 분류 축 교체를 하지 않았다** — **손이 닿지 않는다.**
  막대의 값은 서버가 주는 `LabDataMap.byTopic`(`contracts/seams/fe-core.yaml` ·
  `services/core-api/src/colab_core/app/routes/insight.py:89`)이고, 분류 축으로 바꾸려면
  **`byCategory` 집계를 계약·서버에 신설**해야 한다. 그것은 20차 승인 범위(3축 질의 파라미터 ＋
  `DatasetBasicInfo` required)에 **없다**. 지금 `onOpen` 만 `category` 로 바꾸면 주제 값이 분류
  조건으로 나가 **0건**이 된다(조용한 오작동). **받는 쪽만 세워 뒀다** — `DatasetsPage` 가
  `?category=`·`?dataType=`·`?processingLevel=` 를 첫 조건으로 읽는다. 후속 WU 필요.
- ⛔ `DatasetRow`·`SearchHit` 에 3축 열쇠를 **더하지 않았다** — 라운드 파일의 WU-B7 계약 변경
  목록에 없다(그 목록은 질의 파라미터 3종 ＋ required 승격 둘뿐이다). 표 8열이 이 값을 안 그리므로
  조건은 밑줄 열쇠로 걸고 응답에서 뗀다(`_lastModifiedAt` 과 같은 규율). B1 세션 노트가 이것을
  WU-B7 몫으로 적었으나 **라운드 파일 축자가 이긴다** — 필요하면 후속으로 연다.
- ⛔ 등록 화면(`RegisterArea.tsx`·`UploadModal.tsx`·`LineageStep.tsx`)·`ingestion.py` 의
  수용 목록을 **건드리지 않았다**(WU-B6 병렬 레인 회피).
- ⛔ **staging 실물 platform DB 에 `0016`~`0019` 를 올리지 않았다**(§9 ⛔). 병합자 몫이다.
  ⭑ ⟨정정 · advisor ② ③⟩ 종전 문면 ~~「공유 적용 DB 에 마이그레이션을 올리지 않았다」~~ 는 대상을
  틀리게 가리켰다. **스키마 전용 적용 DB(`COLAB_APPLIED_DB_URL_PLATFORM`)는 이 회차에
  `alembic upgrade head` 로 올렸고**(그래서 `schema-diff` 가 green 이다), 안 올린 것은
  `autometa-loss` 의 대조 정본인 **staging 실물 DB** 다(`COLAB_AUTOMETA_STAGING_DB_URL`).
  두 DB 는 `〈237〉` 로 선언이 분리돼 있다.
- ⛔ 이관 항목 3건 · `40 COLAB-기획/` · `03-HANDOFF.md` · `PLAN-SoT.md` 무접촉. 〈N〉 미발급.
- ⭑ **라운드 종료 보고 문안** — 「**R-A 이월 1건(PRD-21 `nc` 검색) 닫힘**」. 근거 =
  `0019-assertions.sql` C-⑴ ＋ `0019-existing-rows-assertions.sql` ①(기존 행) ·
  대조군 ㈏(0018 까지만 → red)가 「종전에는 안 잡혔다」를 함께 잰다.


## 12. advisor ② 반영 (2026-09-07 · 검토 `approve-with-changes`)

### ① `autometa.variables` 의 두 번째 작성자 제거 — **[필수]**

- 결함 = `_APPLY_AUTOMETA` 가 `variables` 를 썼다. 등록 경로 순서(autometa INSERT →
  `replace_variables` → `apply_autometa`)에서 **변수 행이 0 개면 헤더 유래 이름이 미러 배열에
  들어가고**, 이후 변수 행이 한 번만 바뀌면 트리거가 그 값을 `'{}'` 로 덮는다. 색인이 등록
  순서에 따라 갈린다 — PRD-16 축자 「행 표가 정본 · 트리거만 쓴다」 위반.
- 집행 = **기본값(제거)** 을 골랐다. 대안(배열을 「행 표 ∪ 헤더」로 재정의)은 설계 변경이라
  Ted 판정 몫이고, 이 레인은 열지 않았다.
  - `d3_catalog.py` `_APPLY_AUTOMETA` — `variables` SET 절 ＋ `has_variables` RETURNING 제거.
  - `d3_catalog.apply_autometa` — `variables` 인자 ＋ `text[]` 리터럴 조립 블록 제거.
  - `d3_catalog.AUTOMETA_FROM_EVENTS` — `"variables"` 제거(7 → 6). **튜플이 RETURNING 열쇠와
    한 짝**이라 한쪽만 고치면 `KeyError` 다. 여기 두면 「반영했다」를 세는 자리에 **쓰지 않는
    칸**이 섞인다.
  - `routes/ingestion.py` — `apply_autometa(..., variables=held.variables, ...)` 인자 제거.
- `autometa-loss` 게이트 영향 = **없다.** 그 게이트가 대조하는 칸은 `format`·`crs`·`grid`
  셋뿐이고(`gates/tools/autometa-loss.sh:214-222`), `gates/config/autometa-loss.toml` 은
  **면제 데이터셋 목록**이지 칸 목록이 아니다 — 즉 「toml 에 `variables` 가 없다」는 대조 칸의
  부재가 아니라 그 파일이 칸을 아예 안 적는다는 뜻이다. 튜플 정렬은 게이트가 아니라
  `apply_autometa` 의 반환 계약 때문에 필요했다.
- RED 선실측 (`tests/test_autometa_from_events.py::test_header_variables_do_not_reach_the_mirror_array`) —

```
E       AssertionError: 등록 경로가 헤더 유래 변수명을 미러 배열에 직접 썼다 — 쓰는 곳이 둘이다.
E       assert ['LST', 'QC'] == []
```

- GREEN = `tests/test_autometa_from_events.py` **11건** · `tests/test_axis_filters.py` **14건** ·
  `tests/test_variable_rows.py` 포함 3파일 **34건** 전건 통과.
- ⚠ 같은 파일의 기존 시험 **2건**이 옛 동작(배열에 헤더 값이 들어옴)을 오라클로 들고 있었다 —
  `..._are_applied_at_registration` · `test_empty_form_defaults_are_not_stored_as_human_values`.
  둘 다 `== []` 로 고쳤다. **시험이 결함을 못 잡은 게 아니라 결함을 못 박고 있었다.**

### ①-b 0019 백필 손실 계수 — **실측**

| 대조 대상 | 데이터셋 | 배열 비어 있지 않은 행 | `d3_dataset_variable` | **손실 대상** |
|---|---|---|---|---|
| `autometa-loss` 대조 정본 = staging 실물 platform DB (`COLAB_AUTOMETA_STAGING_DB_URL`) | 14 | 13 | 표 부재(`0016` 미적용) | **0** |
| 스키마 전용 적용 DB (`COLAB_APPLIED_DB_URL_PLATFORM`) | 0 | 0 | 0행 | **0** |
| 실 dev DB | `[미측정]` | `[미측정]` | `[미측정]` | `[미측정]` |

- 손실이 **0** 인 사유 = `0016` 이 **배열 원소를 전수 행으로 이관한 뒤**(`unnest … WITH
  ORDINALITY` · 제외 조건은 공백 이름뿐) `0019` 가 그 행에서 배열을 되쓴다. 두 마이그레이션이
  한 사슬로 도는 한 「행 0 개 ＋ 배열 비어 있지 않음」인 행은 백필 시점에 **존재하지 않는다**.
- 손실이 생기는 유일한 창 = `0016` 적용 **뒤** `0019` 적용 **전**에, 방금 제거한 그 경로로
  헤더 유래 이름이 배열에 새로 들어가는 것. 그 창은 이 수정으로 닫혔다.
- 접근은 읽기 전용(`BEGIN READ ONLY`) · 쓰기 0건.

### ② `contract-breaking` 리베이스 후 재실행 — **[필수]** 「기준 5adf9b4」

```
COLAB_BREAKING_BASE_REF=5adf9b4 COLAB_GATE_REPORT_DIR=dev-package/reports/R-B/p3-axis-filters bash gates/run.sh contract-breaking
No breaking changes to report, but the specs are different.
Run 'oasdiff diff' to see structural differences.
contract-breaking green — 기준 5adf9b4 (3건) 대비 파괴적 변경 없음.
  ── 계 : green 1 / red(판정) 0 / red(준비) 0
```

- §6 의 축자는 **리베이스 전 기준(`b982100`)** 이다. `b982100..5adf9b4` 는 계약 +81 행(B6 추가분)
  이므로 옛 기준은 초과 검출 방향이었으나, 리베이스 후 근거가 기록에 없었다 — 이 절이 그 자리다.
- 요약을 `gate-summary.contract-breaking.record.json` 으로 덮어썼다.

### ③ 산문 정정 (`d3_catalog.py`)

- `:131-133` ~~「그 그림자를 최신으로 유지하는 트리거는 `M-10`(R-B-2 · WU-B7) 소속이라 아직 없다」~~
  → 「유지하는 것은 `0019`(M-10 · R-B-2 · WU-B7)가 세운 트리거다」. **0019 가 이 회차에 섰다.**
- `:958` ~~「그 배열의 미러 유지는 `M-10` 이다」~~ → 「그 배열은 `0019` 의 트리거가 유지한다」.
- `_APPLY_AUTOMETA` 머리글 = 「사람이 고친 값(`crs`·`variables`)」에서 `variables` 를 빼고,
  「여기서 `variables` 를 쓰지 않는다」와 그 사유(쓰는 곳이 둘이 되는 자리)를 적었다.
- §11 「공유 적용 DB …」 한 줄 = 위 §11 에서 정정(스키마 전용 적용 DB 는 `alembic upgrade head`
  로 올렸고, 안 올린 것은 staging 실물 DB).

### ④ 분류 미러 — **앱 롤 런타임 경로 시험 1건**

- `tests/test_axis_filters.py::test_a_category_edit_by_the_app_role_reaches_the_search_index`.
- 재는 것 = 앱 롤(`t_app`)의 `PATCH /datasets/{id}` `category` → 트리거가
  `description.category` → `autometa.category_mirror` → `search_vector`(B 가중치)까지 나른다.
  질의어는 분류 낱말 하나이고 그 낱말은 이름·요약 어디에도 없다 — 잡히면 **미러를 거친 것**이다.
  옛 분류 낱말이 색인에서 빠지는 것까지 함께 잰다.
- **오라클 유효성 실측** = 트리거를 끄고(`ALTER TABLE … DISABLE TRIGGER
  d3_dataset_description_category_mirror`) 같은 시험을 돌려 red 를 확인했다 —

```
E        +  where False = ..._hits('수문')
AssertionError: 등록 시점의 분류가 색인에 없다 — 미러가 처음부터 안 섰다.
```

  green-by-skip 이 아니다. 확인 뒤 트리거를 되켰다(일회용 DB).
- ⚠ `0019-assertions.sql` 은 **관리자 롤**로 돈다 — 트리거 함수가 경계에 걸리면 관리자 롤에서만
  통과하고 앱 롤에서 조용히 0행이 되는 자리가 열린다. 그 자리를 이 시험이 닫는다.

### 반영하지 않은 것

- ⑤ Ted 등재 항목(`AXIS_UNSET_NUDGE` 문면 · 홈 데이터 맵 분류 축 전환 · M-10 가정 의존) ·
  ⑥ 후속(`d3_dataset_variable_mirror` 를 statement-level 로 전환) — **레인 몫이 아니다.**
  ⛔ 〈N〉 미발급 · `PLAN-SoT.md`·`03-HANDOFF.md`·`work-items.yaml`·`contracts/` 무접촉.
- ⚠ 위험 3(`replace_variables` 의 DELETE → 행별 INSERT 로 미러 N+1 회 재작성)은 그대로다.
