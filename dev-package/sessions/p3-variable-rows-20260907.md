# WU-B2 · 변수 행 표 — 레인 `p3-variable-rows` (2026-09-07)

- 라운드 R-B · 파일 `dev-package/prd/rounds/R-B-1-db.md` §2 WU-B2 · PRD-16 · 크기 L · 계층 DB·계약·서버·FE.
- 기준 HEAD = `3889c30`(`integration/r-b` · ff-only 확인). 브랜치 `lane/p3-variable-rows`. 선행 = WU-B1(head `0015_rb1_axes_category_type_lv`).
- 계약 개방 근거 = 20차 · 등급 ㉯ · Ted 승인 **2026-09-07**(`dev-package/sessions/R-B-C20-REQUEST-20260907.md` §Ted 승인). 승인이 `contracts/` 첫 수정보다 앞선다.

## 완료 조건 ↔ 판정 ↔ 근거

| 완료 조건 (`R-B-1-db.md §5` WU-B2) | 판정 | 근거 (파일:행) |
|---|---|---|
| `d3_dataset_variable` 이 선다 | 충족 | `db/platform/schema.sql:508`(표) · 마이그레이션 `db/platform/versions/0016_rb2_dataset_variable.py:83` · 오라클 `db/platform/tests/0016-assertions.sql` A-⑴ |
| RLS ＋ FORCE ＋ 경계 정책 한 장 | 충족 | `db/platform/schema.sql`(RLS 절 · `d3_dataset_autometa` 뒤) · `0016-assertions.sql` C-⑴·C-⑵ · `rls-coverage` green |
| 대표 1개 부분 UNIQUE | 충족 | `schema.sql` `d3_dataset_variable_representative_idx`(`WHERE is_representative`) · `0016-assertions.sql` B-⑵(둘째 대표 거부)·B-⑸(false 는 여럿 허용) |
| 배열 이관이 **순서대로** 되고 첫 행이 대표 | 충족 | `0016_rb2_dataset_variable.py` UPGRADE ⑵(`row_number() OVER w`) · `0016-existing-rows-assertions.sql` ⑴·⑵ · 드리프트 ㈑ green · 대조군 ㈑-b red |
| 마지막 행 삭제가 막힌다 | 충족 | 앞문 = `frontend/src/components/common/VariableTable.tsx` `remove()` · 뒷문 = `services/core-api/src/colab_core/app/routes/catalog.py` `_validate_variables`(0행 → 400) · 시험 `frontend/test/variable-rows-20260907.test.tsx` · `services/core-api/tests/test_variable_rows.py::test_empty_variable_list_is_rejected_with_the_copy` |
| cross-tenant 음성 0건 | 충족 | `tests/test_variable_rows.py::test_another_lab_sees_zero_variable_rows` · `0016-assertions.sql` C-⑶(비소유자 롤) · `rls-effect` green |
| 변수명 검색이 이관 전후 같은 데이터셋 | 충족(이관분) | `0016-existing-rows-assertions.sql` ⑺ — 색인식 무수정이라 `precipitation` 이 같은 데이터셋 하나를 낸다. ⚠ **새로 쓴 행은 아니다**(아래 잔여 위험) |
| D2 가 이 표를 FK 하지 않는다 | 충족 | `db-boundary` green · 스키마의 FK 는 `d3_dataset(id)`·`d1_lab(id)` 둘뿐 |
| head 가 `0015_rb1_axes_category_type_lv` 를 잇는다 | 충족 | `0016_rb2_dataset_variable.py` `down_revision` · `migration-single-head` green |

## 수용 기준 6건

| # | 기준 (축자) | 판정 | 근거 |
|---|---|---|---|
| 1 | 변수 3행에 각각 다른 단위 → 상세가 세 행을 각자의 단위와 함께 낸다 | **충족** | 서버 `tests/test_variable_rows.py::test_three_rows_keep_their_own_units`·`test_detail_read_path_returns_the_rows` · 화면 `test/variable-rows-20260907.test.tsx` 「상세의 읽기 전용 표」 · 시드 `services/core-api/tests/fixtures/seed.sql`(DSA1 = mm·℃·m3/s) |
| 2 | 대표를 고르지 않으면 첫 행이 대표 | **충족** | 서버 `d3_catalog.replace_variables`(`chosen = next(... , 0)`) · `test_variable_rows.py::test_first_row_becomes_representative_when_nobody_is_chosen` · 화면도 같은 규칙(`VariableTable.remove`) |
| 3 | 행 1개에서 삭제 → 막히고 「변수는 하나 이상 있어야 해요」 | **충족** | 문면 한 자리 = `frontend/src/components/common/toastCopy.ts` `AT_LEAST_ONE_VARIABLE` ＋ 서버 `catalog.py` `AT_LEAST_ONE_VARIABLE` · 시험 화면 2건 · 서버 1건(생성·수정 두 경로가 같은 문면) |
| 4 | 3원소이던 기존 행 → 3행이 순서대로, 첫 행만 대표 | **충족** | 드리프트 오라클 `db/platform/tests/0016-drift.sh` ㈑ green · 대조군 ㈑-b(대표를 둘째로 옮김) red |
| 5 | 다른 연구실 계정 → 0건 | **충족** | `test_variable_rows.py::test_another_lab_sees_zero_variable_rows` · `0016-assertions.sql` C-⑶ · B-⑷(쓰기 음성) |
| 6 | 검색어 `precipitation` → 이관 전후 같은 데이터셋 | **충족(이관분) · 제한 1** | `0016-existing-rows-assertions.sql` ⑺. **새로 쓴 변수 행에는 성립하지 않는다** — 아래 「받아들인 잔여 위험」 |

## RED → GREEN

- RED 선실측 축자 (구현 전 · `services/core-api/tests/test_variable_rows.py`) —
  ```
  FAILED tests/test_variable_rows.py::test_three_rows_keep_their_own_units - AssertionError: {"code":"BAD_REQUEST","message":"변수 목록은 빈 문자열 없는...
  FAILED tests/test_variable_rows.py::test_detail_read_path_returns_the_rows - KeyError: 'datasetId'
  FAILED tests/test_variable_rows.py::test_first_row_becomes_representative_when_nobody_is_chosen - AssertionError: {"code":"BAD_REQUEST","message":"변수 목록은 빈 문자열 없는...
  FAILED tests/test_variable_rows.py::test_empty_variable_list_is_rejected_with_the_copy - AssertionError: {"datasetId":"01M1WTSE8P8NJMMPPG4VYCNNM1","fileName":"a.nc"...
  FAILED tests/test_variable_rows.py::test_update_replaces_the_whole_row_set - KeyError: 'datasetId'
  FAILED tests/test_variable_rows.py::test_registration_does_not_write_autometa_variables - KeyError: 'datasetId'
  6 failed, 3 passed in 5.18s
  ```
  통과한 3건 = 대표 둘 400 · 빈 이름 400 · cross-tenant 음성. **앞 둘은 그 시점에 오라클이 아니었다** — 「계약에 없는 필드」가 아니라 「문자열 배열이 아니다」로 400 이 났고, 구현 뒤 뜻이 값 검사로 바뀌어 green 이다.
- GREEN — `tests/test_variable_rows.py` **9건 전부 통과** · `service-tests-core-api` 전체 **852 실행 전건 통과 · 0 실패**(직접 `pytest` 는 858 · 게이트가 6건을 deselect 한다).
- 화면 — `frontend/test/variable-rows-20260907.test.tsx` **8건** · 전체 **876 통과 / 63 파일**.
- 드리프트 오라클의 red 는 스크립트가 스스로 만든다 — ㈏(0016 없음) · ㈐(downgrade 뒤) · ㈑-b(대표 이동) 셋이 red 여야 green 이다.
- 기존 시험 개정 4건(계약 소비자) — `test_dataset_detail.py`(구성 칸 오라클을 객체 배열로) · `test_dataset_registration.py`(요청 형상 ＋ 저장 자리가 `d3_dataset_variable` 로 옮겨짐) · `test_autometa_from_events.py` 2건(아래 「받아들인 잔여 위험」) · `frontend/test/upload.test.tsx` 3건(입력 칸 → 표).

## 마이그레이션

- head 이름 = `0016_rb2_dataset_variable` (25자 · `alembic_version_platform.version_num` `varchar(32)` 상한 안).
- `down_revision = "0015_rb1_axes_category_type_lv"`. `migration-single-head` = platform 리비전 20건 · head 1개.
- 담은 것 = `M-5` 하나. 표 ＋ 색인 2 ＋ 경계 정책 ＋ **이관 INSERT**. ⛔ `search_vector` 무수정 · 트리거 0(그 둘은 `M-10` · `R-B-2-server.md` WU-B7).
- 이관식 = `unnest(variables) WITH ORDINALITY` → 공백 원소 제거 → `row_number() OVER (PARTITION BY dataset_id ORDER BY ord)`. `ordinal` **1부터** · 첫 행만 `is_representative`. 빈 배열은 0행.
- **정책은 이관 INSERT 뒤에 켠다** — 먼저 켜면 FORCE 아래에서 소유자 세션도 정책을 받아 이관이 0행으로 조용히 끝난다.
- 되돌림 = **표 DROP → 사람 입력 3칸＋대표 소실 · 정규 경로는 소비 중단**. `DROP TABLE d3_dataset_variable`. **이관된 이름은 안 사라진다**(원본 배열 존치). ⚠ 배포 뒤 사람이 적은 **단위·값 범위·결측률·대표**는 그 배열에 자리가 없어 사라진다 — 그때의 정규 경로는 소비를 멈추는 쪽이고, 표까지 지우는 것은 그 세 칸이 전 행 NULL 일 때만.
- 드리프트 시험 출력 축자 —
  `0016-drift green — ㈎ 적용 green · ㈏ 0016 없으면 red · ㈐ downgrade 실물 동작 + 0015 복원 · ㈑ 기존 행 순서·대표 이관(대조군 red).`

## 계약 파괴 — `contract-breaking` 축자 (기준 ref `3889c30`)

```
14 changes: 14 error, 0 warning, 0 info
error	[new-required-request-property] in API POST /datasets
		added the new required request property `variables/items/name`
error	[request-property-became-not-nullable] in API POST /datasets
		the request property `variables` became not nullable
error	[request-property-min-items-increased] in API POST /datasets
		the `variables` request property's minItems was increased to `1`
error	[request-property-type-changed] in API POST /datasets
		the `variables/items/` request property `type` changed from `string` to `object`
error	[response-property-min-length-decreased] in API POST /datasets
		the `basicInfo/…/DatasetBasicInfo]/variables/items/` response property's minLength was decreased from `1` to `0` for the response status `201`
error	[response-property-type-changed] in API POST /datasets
		the `basicInfo/…/DatasetBasicInfo]/variables/items/` response's property `type` changed from `string` to `object` for status `201`
… GET /datasets/{datasetId} 2건 · PATCH /datasets/{datasetId} 6건(같은 6종) …
::error::contract-breaking red — 기준(3889c30) 대비 파괴적 변경이 있다 (oasdiff exit 1).
```
전문은 위 명령을 다시 돌려 얻는다(`COLAB_BREAKING_BASE_REF=3889c30 bash gates/run.sh contract-breaking`) — 여기 옮긴 것은 14건 중 종류 6종의 축자이고 나머지 8건은 같은 6종이 다른 op 에 반복된 것이다.

⚠ **게이트 계수의 기준을 갈라 읽는다.** `dev-package/reports/R-B/p3-variable-rows/gate-summary.json` 의 `contract-breaking` green 은 **기본 기준(`HEAD`)** 이고, 그것은 「이 커밋 이후로 더 깬 것이 없다」를 잰다. **20차 승인이 필요한 파괴는 위 축자이고 `3889c30` 기준에서만 보인다** — 두 값이 다른 것은 기준이 다르기 때문이지 판정이 갈린 것이 아니다.

## 소비자 수

- 이번 회차 열쇠 — `grep -rn 'variables' contracts/ services/ frontend/src | wc -l` = **178**(기준 `3889c30` 실측 **128**).
- 라운드 ㉰ 문안의 20차 전체 측정법 — `grep -rn 'variables\|accessState\|lineageUnknown\|category' contracts/ services/ frontend/src | wc -l` = **256**(기준 `3889c30` 실측 **206**). 라운드 파일 기재값 163 은 R-B 착수 전 실측이고 B1·B2 의 추가분이 그 차이에 든다.

## 서버 규칙 (이 회차가 세운 것)

- 등록·수정이 행 집합을 **통째로 교체**한다 — `d3_catalog.replace_variables`(delete-then-insert · `update_dataset` 의 UPDATE 와 같은 트랜잭션).
- `ordinal` 은 **서버가 1부터 다시 매긴다** — 화면이 보낸 순서가 값이고, 클라이언트가 번호를 지어 보내면 구멍·중복이 그대로 저장된다.
- 대표 = **정확히 하나**. 아무도 안 고르면 첫 행(자동 보정) · 둘 이상은 **400**(뒷문은 부분 UNIQUE 색인).
- **0행은 400** ＋ 「변수는 하나 이상 있어야 해요」. 생성·수정이 같은 검사기(`validate_human_metadata` → `_validate_variables`) 한 벌을 쓴다.
- 읽기 = 행 표가 정본이고 **0행일 때만** `d3_dataset_autometa.variables` 로 퇴행(이름만 · 첫 이름이 대표). 쓰기 정본은 표 하나뿐이다.

## 받아들인 잔여 위험 — `M-10` 전까지의 검색 드리프트

- **등록·수정 경로는 `d3_dataset_autometa.variables` 를 직접 쓰지 않는다**(PRD-16 축자 「트리거만 쓴다」). 그 배열을 행 표의 미러로 유지하는 트리거는 `M-10` 이고 `R-B-2-server.md`(WU-B7) 소속이다.
- ⟹ **`M-10` 전까지 새로 쓴 변수 행은 검색 색인에 안 들어간다.** 이관된 기존 행의 검색은 그대로다(배열이 그 자리에 남아 있다) — 그래서 수용 기준 6은 **이관 데이터에 대해** 성립하고, 그 사실을 오라클도 이관 데이터로 잰다.
- 이 잔여 위험을 **문서가 아니라 코드가 붙잡는다** — `tests/test_variable_rows.py::test_registration_does_not_write_autometa_variables` 가 「그 배열이 비어 있음」을 단언한다. `M-10` 이 서면 이 시험이 **먼저 red** 를 내고, 그 자리에서 기대값을 미러로 바꾼다.
- 같은 이유로 `test_autometa_from_events.py` 2건의 뜻이 바뀌었다 — ⑴ 「사람 값을 사건이 안 덮는다」의 확인처가 행 표로 옮겨졌다 ⑵ 「빈 배열은 안 적은 것」이 「**열쇠의 부재**가 안 적은 것」으로 바뀌었다(빈 배열은 이제 400).

## 게이트 (배출처 `dev-package/reports/R-B/p3-variable-rows`)

| 게이트 | 출력 |
|---|---|
| `schema-diff` | `schema-diff green — 두 체인 각각 선언 = 적용.` |
| `migration-single-head` | `migration-single-head green — 두 체인 모두 head 1개.`(platform 리비전 20 · head `0016_rb2_dataset_variable`) |
| `contract-lint` | `contract-lint green — seam 3건, 룰 위반 0.` |
| `contract-breaking`(기본 기준 `HEAD`) | `contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.` — 기준을 `3889c30` 로 옮기면 **red 14건**(위 축자 · 20차 승인분) |
| `generated-up-to-date` | `generated-up-to-date green — 등기부 10건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.` |
| `db-boundary` | `db-boundary: green — 단위 7개 · 스캔 대상 339건 · 위반 0` |
| `rls-coverage` | `rls-coverage green — allow-list 밖 테이블 전부 FORCE RLS + 연구실 경계 정책, 본체 테이블은 본체 정책까지.` |
| `rls-effect` | `rls-effect green — 본체 음성 · 메타 양성(P-13) · cross-tenant 셋 다 엔진이 막는다. 판정 롤은 우회 불가.` |
| `autometa-loss` | `autometa-loss green — 반영 6 / 발행 6 · 면제 0` |
| `service-tests-core-api` | `service-tests-core-api green — 실행 852건 전부 통과 (skipped 0 · deselected 6 은 요약줄에 드러나 있다).` |
| `frontend-typecheck` | `frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.` |
| `frontend-test` | `frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 876건 · 실패 0건.` |

계 = **green 13 / red(판정) 0 / red(준비) 0**(위 12 ＋ `work-item-consistency`). 마지막 커밋 뒤에 13건을 다시 돌렸다 — `all` 은 돌지 않았다(레인 규약 §3-1).

## 자기 표시

- **「≥1 행 요구」의 범위를 좁혀 읽었다** — 지시문 축자는 「등록·수정에 ≥1 행 필요」이고, 이 레인은 **`variables` 열쇠를 실었을 때만** ≥1 로 구현했다(열쇠 부재 = 「안 적었다」는 종전대로 통과). 근거 = PRD-16 이 여는 자리가 「마지막 행 삭제를 막는다」이고, 언제나 필수로 올리면 변수를 한 줄도 안 적고 등록하던 기존 경로가 전부 400 이 된다(그 승격은 `DatasetCreate.required` 문제이고 라운드가 **WU-B3** 에 배정했다). 계약에도 `minItems: 1` 로 그 해석을 못 박았다.
- **읽기 퇴행 1건을 더했다(요청되지 않은 초과분)** — 변수 행이 0개면 `autometa.variables` 로 퇴행해 이름만 그린다. 없으면 파이프라인이 헤더에서 읽어 채운 데이터셋의 구성 칸이 이유 없이 빈다(등록·수정이 그 배열을 안 쓰므로). **쓰기 정본은 여전히 표 하나**이고, `M-10` 이 서면 이 퇴행은 무해한 잉여가 된다.
- **`ordinal` 을 1부터 매겼다** — 라운드·PRD 는 「배열 순서」라고만 적고 시작값을 정하지 않았다. `unnest … WITH ORDINALITY` 와 같은 셈이라 이관식이 한 겹 단순해진다. 0부터로 바꾸는 것은 마이그레이션 1건이므로 지금 정해 둔다.
- **`DatasetCreate.variables` 에서 `null` 을 뺐다** — 종전 `[array, "null"]` 이었고 `null`·`[]` 둘 다 「0행」이라 두 표현을 남기면 검사기가 둘로 갈린다. 이 축소도 `contract-breaking` 의 `request-property-became-not-nullable` 1건으로 잡혀 있다.
- **문면을 두 층에 각각 뒀다** — `frontend/.../toastCopy.ts` 와 `services/.../catalog.py`. 층이 달라 한 파일에 못 모으고, 두 벌임을 각 자리 주석이 서로 가리킨다. **PRD-43 의 21행에는 넣지 않았다** — 그 표는 R-A 회차 목록이고 계수 21 이 그 시험의 오라클이다.
- **시드 5행을 더했다**(`services/core-api/tests/fixtures/seed.sql`) — DSA1 3행(단위 3종)·DSA2 1행·DSB1 1행. DSB1 이 없으면 cross-tenant 음성이 「안 보였다」와 「아예 없다」를 못 가른다.
- **환경 조치 2건** — ⑴ 워크트리 `services/core-api/.venv` 에 `alembic` 부재 → `uv pip install alembic`(1.19.2). ⑵ **시험 DB `colab_platform` 이 호스트에 부재**했다 — `docker exec a2_pg createdb` 뒤 `services/core-api/tests/fixtures/setup-db.sh` 로 재구성. 둘 다 레포 파일 변경 0.

## 하지 않은 것

- **`M-10` — 색인 재정의 ＋ 변수명 미러 트리거.** `R-B-2-server.md` · WU-B7 소속이고 라운드에 한 번만 돈다. `search_vector` 를 한 글자도 안 건드렸고 `0016-assertions.sql` D-⑵·D-⑶ 가 그 사실을 붙잡는다.
- **`d3_dataset_autometa.variables` 열 삭제** — 되돌림 경로이자 이관 대조 근거(§3-㉴).
- **`DatasetRow`·`SearchHit` 의 변수 확장 · 변수 기준 필터** — 이 회차 범위 밖.
- **상세 편집 모드에서 변수 고치기** — WU-A3R 편집 폼은 무수정(변수 칸이 원래 없다). 상세의 표는 **읽기 전용**이고 수정은 계약상 `updateDataset` 으로 열려 있다.
- **R-B 의 다른 칸**(B3/B4/B6 — 분류·유형 셀렉트 · 공개 범위 · Lv0 출처) — 그리지 않았다. 존치 6종 무수정.
- **`PLAN-SoT §9` 〈N〉 등재 · `03-HANDOFF.md` 수정** — 병합 직전 오케스트레이터 몫.

## 후속

1. **`db/platform/tests/*-drift.sh` 가 어느 게이트에도 안 걸린다** — `grep -rn "drift.sh" gates/ .github/` = 0건. `0016-drift.sh` 도 같다. 게이트 승격 대상(`colab-rules §3-3`-⑷). WU-B1 후속 1번과 같은 항목이고 이번 회차가 한 벌 더 쌓았다.
2. **`alembic` 이 어느 `requirements*.txt` 에도 없다** — 새 워크트리마다 손으로 채운다. 위 1번을 게이트로 올리면 그 게이트가 늘 red(준비)다.
3. **시험 DB `colab_platform` 이 호스트에서 사라져 있었다** — 재구성 절차는 `services/core-api/tests/fixtures/setup-db.sh` 이고 `dev-package/RESTART.md` 가 그 자리를 적는다. 어느 게이트도 「그 DB 가 있는가」를 미리 말해 주지 않고 `service-tests-core-api` 가 red(준비)로만 드러낸다.
4. **`M-10` 착수 시 이 회차의 시험 2건이 먼저 red 를 낸다** — `test_registration_does_not_write_autometa_variables` 와 `test_autometa_from_events.py::test_human_values_sent_at_registration_survive_the_header_parsed_event`. 기대값을 미러로 바꾸는 것이 그 WU 의 일부다.
5. **`d3_catalog.SUGGESTABLE_FIELDS` 의 `variables` 자동완성이 아직 `autometa.variables` 를 훑는다**(`unnest`) — 이관분은 맞고 새 행은 안 잡힌다. `M-10` 이 미러를 세우면 저절로 맞고, 안 세우면 그 자리를 행 표로 옮겨야 한다.

## advisor ② 반영

- **결함(축자)** — 「이관이 실배포에서 0행이다. `0016` UPGRADE ⑵ 는 `d3_dataset_autometa`(FORCE RLS · `schema.sql:1085-1086`)를 읽는데 마이그레이터 롤은 `colab_owner NOSUPERUSER NOBYPASSRLS`(`infra/dev/db-bootstrap.sh:33`). `app.current_lab` 미설정 → `current_lab_id()` NULL → SELECT 0행 → INSERT 0행, 오류 없음.」 **거짓 green 의 원인** = 드리프트 ㈑ 가 `psql -U postgres`(superuser · RLS 무조건 우회)로 델타를 적용했다 — 실배포 롤에서 0행이 되는 자리를 시험이 못 쟀다.
- **RED 선실측**(수정 전 마이그레이션 · 소유자 롤 `t_owner` NOSUPERUSER NOBYPASSRLS 로 델타 적용) 축자 —

```
[0016-drift] ㈑ 기존 행(소유자 롤 적용) — 3원소가 순서대로 3행이 되고 첫 행이 대표인가 → red (기대 green) ✗
           ERROR:  0016 기존 행 오라클 실패 — DSV1 의 변수 행이 NULL 다 (기대 '1:precipitation,2:temperature,3:runoff') — 배열 순서가 ordinal 로 안 옮겨졌다
::error::0016-drift red — 델타에 원천 d3_dataset_autometa 의 NO FORCE 구간이 없다 — 마이그레이션이 FORCE 원천을 그대로 읽는다(실배포 0행 이관).
```

- **수정 ⑴ 마이그레이션**(`db/platform/versions/0016_rb2_dataset_variable.py`) — 이관 INSERT 앞 `ALTER TABLE d3_dataset_autometa NO FORCE ROW LEVEL SECURITY;` · INSERT 뒤 `FORCE` 복원(`0013_ra1_ext_interval_period.py:38-40, 116-117` 과 같은 자리). 원천은 그 한 표뿐이다 — 이관 SELECT 가 다른 표를 조인하지 않고 `lab_id` 도 `d3_dataset_autometa` 에서 온다. 대상 표는 이관 시점에 정책이 없다(⑶ 이 켠다).
- **수정 ⑴ 단언 2건**(둘 다 `0013` 식 DO 블록) — ⓐ **건수** `count(d3_dataset_variable)` = `공백 제외 배열 원소 수` 불일치 시 `RAISE EXCEPTION` ⓑ **복원** `pg_class.relforcerowsecurity = true` 아니면 `RAISE EXCEPTION`. ⚠ ⓐ 는 **NO FORCE 구간 안 · 정책 켜기 전**에 뒀다 — 밖에 두면 원천·대상이 다 RLS 에 막혀 `0 = 0` 으로 green 이 되고 단언이 결함을 못 잡는다. 선언 변경 0 → `schema.sql` 무수정(`schema-diff` green).
- **수정 ⑵ 드리프트 오라클**(`db/platform/tests/0016-drift.sh`) — 롤 `t_owner`(`LOGIN NOSUPERUSER NOBYPASSRLS`) 를 만들고 `handover()` 가 public 객체·스키마·DB 소유권을 넘긴 뒤 ㈑·㈑-b 델타를 그 롤로 적용한다(`REASSIGN OWNED BY postgres` 는 부트스트랩 superuser 라 거부되므로 객체별 `ALTER … OWNER`). 대조군 **㈑-c** 추가 = 델타에서 원천 `NO FORCE` 한 줄을 지운 **수정 전** 텍스트를 같은 롤로 적용 → 이관 0행 → 오라클 red 기대.
- **GREEN**(수정 후) 축자 —

```
[0016-drift] ㈎ 0016 적용 후 — 구조 오라클 → green OK
[0016-drift] ㈏ 0016 없음 — 오라클이 red 를 내는가 → red OK
[0016-drift] ㈐ downgrade 후 — 오라클이 red 를 내는가 → red OK
[0016-drift] ㈐ downgrade 결과 = 0015 상태 (pg_dump 동일) → OK
[0016-drift] ㈑ 기존 행(소유자 롤 적용) — 3원소가 순서대로 3행이 되고 첫 행이 대표인가 → green OK
[0016-drift] ㈑-b 대표를 둘째 행으로 옮김 — 오라클이 red 를 내는가 → red OK
[0016-drift] ㈑-c 수정 전 델타(소유자 롤) — 이관 0행으로 오라클이 red 를 내는가 → red OK
0016-drift green — ㈎ 적용 green · ㈏ 0016 없으면 red · ㈐ downgrade 실물 동작 + 0015 복원 · ㈑ 소유자 롤 이관 green(대조군 ㈑-b 대표 이동 red · ㈑-c 수정 전 델타 0행 red).
```

- **권고 3건 반영** — ⑴ `d3_catalog.replace_variables` 첫 줄에 `_LOCK_DATASET`(`FOR UPDATE`) 잠금(동시 PATCH 2건의 PK 충돌 500 차단). 시험은 안 붙였다 — 레포에 동시성 시험 패턴이 없다(`grep -rn "lock_dataset\|FOR UPDATE" services/core-api/tests` = 0건). ⑵ `routes/ingestion._human_metadata` 의 `variables: null` 을 `[]` 와 같이 400 으로 통일 ＋ 시험 `test_null_variable_list_is_rejected_like_the_empty_one`. ⑶ `frontend/test/rev1-keep-regression.test.tsx:212` 를 객체 배열 `[{ name: '강수량', representative: true }]` 로 교정 — `as unknown as` 캐스트는 **존치**(제거하면 `files.hasReferenceGridFile` 누락으로 `TS2741`, 변수 때문에 붙은 캐스트가 아니다).

### 게이트 재실행 (배출처 `dev-package/reports/R-B/p3-variable-rows` · 마지막 커밋 뒤)

| 게이트 | 요약줄 축자 |
|---|---|
| `schema-diff` | `green  schema-diff` |
| `migration-single-head` | `green  migration-single-head` |
| `service-tests-core-api` | `service-tests-core-api green — 실행 853건 전부 통과 (skipped 0 · deselected 6 은 요약줄에 드러나 있다).` |
| `db-boundary` | `green  db-boundary` |
| `rls-effect` | `green  rls-effect` |
| `frontend-typecheck` | `green  frontend-typecheck` |
| `frontend-test` | `green  frontend-test` |
| `0016-drift.sh` | 위 GREEN 축자 |

계 = **green 7 / red(판정) 0 / red(준비) 0**.
