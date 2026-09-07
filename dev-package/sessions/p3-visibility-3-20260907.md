# WU-B4 · 공개 범위 3값 — 레인 `p3-visibility-3` (2026-09-07)

- 라운드 R-B · 파일 `dev-package/prd/rounds/R-B-1-db.md` §2 WU-B4 · PRD-11 · 크기 M · 계층 DB·계약·서버·FE.
- 기준 HEAD = `3e2dcd8`(`integration/r-b` · ff-only 확인). 브랜치 `lane/p3-visibility-3`. 선행 = WU-B3(done · 슬롯 `reg-visibility-slot`) ＋ WU-B2(head `0016_rb2_dataset_variable`).
- 계약 개방 근거 = 20차 · 등급 ㉯ · Ted 승인 **2026-09-07**(`dev-package/sessions/R-B-C20-REQUEST-20260907.md`). 승인이 `contracts/` 첫 수정보다 앞선다.

## 완료 조건 ↔ 판정 ↔ 근거

| 완료 조건 (`R-B-1-db.md §5` WU-B4) | 판정 | 근거 (파일) |
|---|---|---|
| `state` 3값 ＋ `default_visibility` 3값이 **둘 다** 선다 | 충족 | `db/platform/schema.sql:105`·`:174` · 마이그레이션 `db/platform/versions/0017_rb4_access_state_3.py` UPGRADE ⑴ · 오라클 `db/platform/tests/0017-assertions.sql` A-⑴·B-⑴ · `schema-diff` green |
| 자동 매핑 후 기존 허용자의 접근이 종전과 같다(양성·음성) | 충족 | `0017_rb4_access_state_3.py` UPGRADE ⑵ · `0017-existing-rows-assertions.sql` ⑴·⑸ · 드리프트 ㈑ green · 대조군 ㈑-b·㈑-c red |
| 승인이 상태를 **같은 트랜잭션에서** 올린다 | 충족 | `services/core-api/src/colab_core/domains/d2_access.py` `decide_access_request`(`_RAISE_LOCKED_TO_DESIGNATED` ＋ 연구실 기본값 갈래) · `tests/test_access_state_three.py::test_approval_flips_locked_to_designated_and_opens_the_body` |
| `state='잠김'` ∧ 유효 grant ≥1 인 행이 **어느 시점에도 0건** | 충족 | 이관 시점 = 0017 DO 블록 단언 ⑵ · 실행 시점 = `d2_access.set_access_state`(만료 먼저 · 상태 나중) · 시험 `test_no_locked_dataset_ever_holds_a_valid_grant` · `0017-existing-rows-assertions.sql` ⑶ |
| cross-tenant 음성 0건 (RLS 무개방) | 충족 | `test_another_lab_sees_no_access_rows` · `0017-assertions.sql` C-⑶ · `0017-existing-rows-assertions.sql` ⑹ · `rls-effect`·`rls-coverage` green · 드리프트 델타에 `CREATE/DROP/ALTER POLICY` 0건(스크립트가 잰다) |
| 접근 판정 함수 무수정 | 충족 | `d2_access.py` `dataset_access`(`body_accessible = open_ or granted`) 무변 · `schema.sql` `body_access` 정책 무변 · `test_designated_rides_the_grant_path`(양성·음성) · `0017-assertions.sql` C-⑴·C-⑵ |
| head 가 `0016_rb2_dataset_variable` 를 잇는다 | 충족 | `0017_rb4_access_state_3.py` `down_revision` · `migration-single-head` green |

## 수용 기준 6건

| # | 기준 (축자) | 판정 | 근거 |
|---|---|---|---|
| 1 | 마이그레이션 적용 → 유효 grant 를 가진 잠김이 `지정 공개` 이고 그 사람의 접근이 종전과 같다(양성·음성) | **충족** | `0017-existing-rows-assertions.sql` ⑴(매핑) ＋ ⑸(허용자 본체 1행 · 만료자 0행 · 비소유자 롤) · 드리프트 ㈑ green |
| 2 | `나만 보기` 승인 → `지정 공개` ＋ 본체 열림 (같은 트랜잭션) | **충족** | `test_access_state_three.py::test_approval_flips_locked_to_designated_and_opens_the_body`(응답 `accessState` ＋ DB 행 ＋ `bodyAccessible`) · `test_approval.py`(승인 응답 열쇠 6종) |
| 3 | `지정 공개` ＋ 유효 grant 2건에서 `나만 보기` 로 내림 → `2명` 문면 ＋ grant 2건 만료 | **충족** | 서버 `test_lowering_to_locked_expires_every_valid_grant_and_reports_the_count` · 화면 `frontend/test/visibility-three-20260907.test.tsx` §4(문면 축자 · 확인 전 저장 0회) |
| 4 | 어느 시점이든 `state='잠김'` ∧ 유효 grant = 0건 | **충족** | `test_no_locked_dataset_ever_holds_a_valid_grant`(승인 왕복 뒤 전수 셈) · 0017 DO 블록 단언 ⑵ · `0017-existing-rows-assertions.sql` ⑶ |
| 5 | `나만 보기` 데이터셋도 접근 요청을 접수한다 (`0010` 회귀) | **충족** | `test_a_locked_dataset_still_accepts_access_requests` ＋ `test_a_designated_dataset_also_accepts_access_requests`(전이표 두 줄) |
| 6 | 연구실 밖 계정 → 어느 상태든 안 보인다 (cross-tenant 음성 0건) | **충족** | `test_another_lab_sees_no_access_rows`(404 ＋ 상태 행 0건 ＋ **대조 A 세션 ≥2**) · `0017-assertions.sql` C-⑶ |

## ㈓ 「공개 범위 값 재동기 재검증」 (WU-B3 이관분)

- **재검증 결과 = 충족.** 3값을 각각 저장하면 **다시 읽지 않고** 헤더 칩과 공개 범위 설명이 그 값으로 다시 선다.
- 근거 = `frontend/test/visibility-three-20260907.test.tsx` §5 — 값마다 ⑴ 상세 조회는 **처음 한 번**뿐이고 ⑵ 저장 호출이 정확히 1회(`{ accessState: <값> }`) ⑶ 칩이 `null·나만 보기·지정한 사람만` ⑷ 설명이 같은 표기.
- 재동기 경로 = `useDatasetEdit.submit` 의 왕복 하나다(낙관 → 서버 200 상세로 갈아탄다). 값이 안 바뀌면 `toPatch` 가 `accessState` 를 **안 싣는다**(같은 시험 마지막 건) — 뜻 없는 `잠김` 내림 경로를 안 탄다.

## RED → GREEN

- RED 선실측 축자 (구현 전 · `services/core-api/tests/test_access_state_three.py`) —
  ```
  FAILED tests/test_access_state_three.py::test_registration_writes_the_chosen_state - AssertionError: {"code":"BAD_REQUEST","message":"계약에 없는 필드다: ['acce...
  FAILED tests/test_access_state_three.py::test_registration_can_choose_the_designated_state - AssertionError: {"code":"BAD_REQUEST","message":"계약에 없는 필드다: ['acce...
  FAILED tests/test_access_state_three.py::test_a_value_outside_the_three_is_a_400 - assert '지정 공개' in '{"code":"BAD_REQUEST","message":"계약에 없는 필드다:...
  FAILED tests/test_access_state_three.py::test_approval_flips_locked_to_designated_and_opens_the_body - KeyError: 'accessState'
  FAILED tests/test_access_state_three.py::test_lowering_to_locked_expires_every_valid_grant_and_reports_the_count - sqlalchemy.exc.IntegrityError: (psycopg.errors.CheckViolation) new row for ...
  FAILED tests/test_access_state_three.py::test_no_locked_dataset_ever_holds_a_valid_grant - assert 1 == 0
  FAILED tests/test_access_state_three.py::test_a_designated_dataset_also_accepts_access_requests - sqlalchemy.exc.IntegrityError: (psycopg.errors.CheckViolation) new row for ...
  FAILED tests/test_access_state_three.py::test_designated_rides_the_grant_path - sqlalchemy.exc.IntegrityError: (psycopg.errors.CheckViolation) new row for ...
  8 failed, 4 passed in 10.61s
  ```
  ⭑ **`assert 1 == 0` 이 이 회차의 결함 그 자체다** — 승인 왕복 한 바퀴만 돌면 「`잠김` ∧ 유효 grant 1건」이 성립했다. 종전 2값에서는 그것이 정상이었고, 3값에서 그 상태가 곧 `지정 공개` 다.
  통과한 4건 = 열쇠 부재 시 연구실 기본값 · 거절이 상태 무변 · 잠김 요청 접수(0010 회귀) · cross-tenant 음성. **넷 다 「종전과 같아야 한다」를 재는 회귀**라 구현 전에도 green 인 것이 정상이다.
- GREEN — `tests/test_access_state_three.py` **12건 전부 통과** · `service-tests-core-api` 전체 **871 실행 전건 통과 · 0 실패**(deselected 6).
- 화면 — `frontend/test/visibility-three-20260907.test.tsx` **12건** ＋ `test/register-steps-20260907.test.tsx` 증보 **2건** · 전체 **922 통과 / 65 파일**.
- 드리프트 오라클의 red 는 스크립트가 스스로 만든다 — ㈏(0017 없음) · ㈐(downgrade 뒤) · ㈑-b(만료 grant 를 유효로) · ㈑-c(NO FORCE 없는 델타) 넷이 red 여야 green 이다.
- 기존 시험 개정 5건(계약 소비자) — `test_approval.py`(승인 응답에 `accessState`) · `test_dataset_detail.py`(상세 열쇠에 `activeGrantCount`) · `frontend/test/detail.test.tsx`(칩 문면 `잠김`→`나만 보기`) · `detail-edit.test.tsx`(셀렉트 2→3 · 「R-B 가 더할 칸」에서 `공개 범위` 제외) · `upload.test.tsx`(등록 본문 열쇠에 `accessState`).

## 마이그레이션

- head 이름 = `0017_rb4_access_state_3` (22자 · `alembic_version_platform.version_num` `varchar(32)` 상한 안).
- `down_revision = "0016_rb2_dataset_variable"`. `migration-single-head green — 두 체인 모두 head 1개.`
- 담은 것 = `M-4` 하나 · **두 표**. `d2_dataset_access_state_check` ＋ `d1_lab_profile_default_visibility_check` 를 3값으로 교체 ＋ **매핑 UPDATE**. ⛔ RLS 정책 0건 수정 · `body_access` 무변.
- 매핑식 = `UPDATE d2_dataset_access SET state='지정 공개' WHERE state='잠김' AND EXISTS(유효 grant)`. `열림`→`열림` · `잠김` ∧ 유효 grant 0 → `잠김` · NULL → 행 없음 그대로.
- **NO FORCE 창** = `d2_dataset_access` ＋ `d2_dataset_access_grant` 둘 다. 마이그레이터 롤이 `colab_owner`(NOSUPERUSER · NOBYPASSRLS)이고 `current_lab_id()` 가 NULL 이라, 창이 없으면 UPDATE 가 **오류 없이 0행**으로 끝난다(`0016` advisor ② 와 같은 자리). 단언 3종은 **창 안**에 뒀다 — 밖에 두면 양쪽이 RLS 에 막혀 `0 = 0` 으로 green 이 된다.
- 단언 = ⑴ 건수(`ROW_COUNT` = 사전 계산 `want`) ⑵ 불변식(이관 뒤 「잠김 ∧ 유효 grant ≥1」 0건) ⑶ FORCE 복구(`pg_class.relforcerowsecurity` 두 표).
- **되돌림 손실** — `downgrade` 는 좁히기 **전에** 두 표의 `지정 공개` 를 `잠김` 으로 되돌린다. ⚠ **「지정한 사람만」과 「나만 보기」의 구별이 사라진다.** 허용 줄(`d2_dataset_access_grant`)은 **그대로 남으므로** 접근 자체는 유지되고(`body_access` 의 grant 갈래), 다시 올리면 이 파일의 매핑이 유효 grant 를 근거로 `지정 공개` 를 **되살린다**. 되살아나지 않는 것은 **유효 grant 0건인 `지정 공개`** 뿐이고, 그 상태는 사람에게 `나만 보기` 와 같은 범위였다.
- 게이트 DB(`colab_platform_applied`) 매핑 건수 = **0행**(그 DB 는 스키마 전용이라 `d2_dataset_access` 가 0행이다 · 단언은 `0 = 0` 으로 통과). **매핑이 실제로 재어진 자리는 드리프트 오라클 ㈑** — 심은 4행 중 `1행`이 `지정 공개` 로 옮겨졌고(DSC1), `잠김` 1행(DSC2 · 만료 grant)·`열림` 1행(DSC3)·행 없음 1건(DSC4)이 그대로였다.
- 드리프트 시험 출력 축자 —
  ```
  [0017-drift] ㈎ 0017 적용 후 — 구조 오라클 → green OK
  [0017-drift] ㈏ 0017 없음 — 오라클이 red 를 내는가 → red OK
  [0017-drift] ㈐ downgrade 후 — 오라클이 red 를 내는가 → red OK
  [0017-drift] ㈐ downgrade 결과 = 0016 상태 (pg_dump 동일) → OK
  [0017-drift] ㈑ 기존 행(소유자 롤 적용) — 유효 grant 가 있는 잠김만 지정 공개가 되는가 → green OK
  [0017-drift] ㈑-b 만료된 grant 를 유효로 바꿈 — 오라클이 red 를 내는가 → red OK
  [0017-drift] ㈑-c 수정 전 델타(소유자 롤) — 매핑 0행으로 오라클이 red 를 내는가 → red OK
  0017-drift green — ㈎ 적용 green · ㈏ 0017 없으면 red · ㈐ downgrade 실물 동작 + 0016 복원 · ㈑ 소유자 롤 매핑 green(대조군 ㈑-b 만료 grant 유효화 red · ㈑-c 수정 전 델타 0행 red).
  ```

## 계약 — `contract-breaking` 축자 (기준 ref `3e2dcd8`)

```
11 changes: 0 error, 11 warning, 0 info
warning	[response-property-enum-value-added] at /w/rev/contracts/seams/fe-core.yaml
	in API GET /datasets/{datasetId}
		added the new `지정 공개` enum value to the `accessState` response property for the response status `200`
		Adding new enum values to a response can be unexpected for clients; use x-extensible-enum instead.
… 같은 종류 10건이 더 있다 — POST /datasets(201) · PATCH /datasets/{datasetId} · GET·PATCH /lab(`defaultVisibility`) ·
  POST /projects(201) · GET·PATCH /projects/{projectId} · PUT /projects/{projectId}/status(`datasets/items/accessState`) …
contract-breaking green — 기준 3e2dcd8 (3건) 대비 파괴적 변경 없음.
```

⚠ **판정과 승인 범위가 어긋나지 않는다는 것을 갈라 읽는다.** 20차 ㉯ 승인이 덮은 것은 「`AccessState` 2→3값」이고, **`oasdiff` 는 그 확장을 error 가 아니라 warning 으로 분류한다**(응답 enum 값 추가 = 클라이언트가 못 보던 값을 받는 것이라 경고이고, 요청 쪽은 오히려 넓어졌다). 그래서 이 회차의 `contract-breaking` 은 **기준을 `3e2dcd8` 로 옮겨도 green** 이다 — WU-B2 가 `error 14` 를 낸 것과 다른 이유는 그쪽이 `variables` 를 **문자열 → 객체**로 바꿨기 때문이다. **승인이 불필요했다는 뜻이 아니다** — 소비자가 못 보던 값을 받는 변경이고, 그 판정은 게이트가 아니라 20차가 한다.

- 넓힌 자리 = `contracts/schemas/common.json` `AccessState`(enum 3값 · `default '열림'` 유지 · description **덧붙임**). `LabDefaultVisibility` 는 그것을 `$ref` 하므로 **두 표가 함께 움직였다** — 두 번째 enum 을 만들지 않았다.
- 신설 열쇠 3 = `DatasetCreate.accessState`([string,"null"]) · `DatasetUpdate.accessState`([string,"null"]) · `AccessGrant.accessState`($ref · **required**) · `DatasetDetail.activeGrantCount`(integer · **required**).
- 생성물 재생성 = `frontend/src/generated/fe-core.ts`(`generated-up-to-date` green).

## 소비자 수

- `grep -rn 'accessState\|AccessState' contracts/ services/ frontend/src | wc -l` = **121**(기준 `3e2dcd8` 실측 **39**).

## 서버 규칙 (이 회차가 세운 것)

- **값 집합 검사 한 벌** = `catalog.validate_access_state` — 등록(`createDataset`)과 수정(`updateDataset`)이 같은 함수를 쓴다. 3값 밖은 **400** ＋ 봉투 `allowed`(IntegrityError 500 로 떨어뜨리지 않는다). 코드 층 사본은 `d2_access.ACCESS_STATES` 한 자리이고 정본은 DB CHECK 두 표다.
- **등록** — 열쇠가 있고 `null` 이 아닐 때만 `d2_dataset_access` 에 쓴다. ⛔ 기본값을 복사해 넣지 않는다 — 넣으면 그 뒤 연구실 기본값을 바꿔도 그 데이터셋만 옛 값으로 굳는다.
- **수정** — `accessState` 는 D3 변경분에서 **떼어 내** D2 경로(`d2_access.set_access_state`)로 쓴다. `null` 은 **행을 지우지 않고** `state = NULL` 로 되돌린다(「한 번도 안 정했다」와 「기본값으로 되돌렸다」를 `updated_at` 이 가른다).
- **내림 = 만료 먼저, 상태 나중.** 순서를 뒤집으면 같은 트랜잭션 안이라도 「잠김인데 유효 grant 가 있다」는 중간 상태가 생기고 그 사이에 도는 정책이 그것을 본다.
- **승인 = 상태 승격.** `잠김` → `지정 공개`(`WHERE state='잠김'`). 상태 행이 없고 **연구실 기본값이 `잠김`** 인 갈래는 데이터셋 쪽에 `지정 공개` 를 **명시**해 불변식을 지킨다(데이터셋 값이 기본값을 이긴다 · P-27).
- **불변식 집행 자리 = 응용 층 ＋ 회귀 시험.** DB CHECK 로는 못 건다(`d2_dataset_access` 와 `d2_dataset_access_grant` **두 표에 걸친 조건**이라 행 단위 CHECK 의 사정거리 밖이다 · PRD-11 축자). 트리거도 안 썼다 — 상태를 바꾸는 쓰기 경로가 `decide_access_request`·`set_access_state` **둘뿐**이고 둘 다 D2 안이다. 「스키마 변경 = CHECK 확장」 범위를 넘지 않았다.
- **접근 판정 함수 무수정** — `지정 공개` 는 `body_access` 의 grant 갈래를 그대로 탄다. 시험이 양성·음성 둘 다 잰다.

## 화면 규칙

- **표기 대응표 한 자리** = `frontend/src/components/common/accessState.ts`. 등록 셀렉트 · 상세 헤더 칩 · 공개 범위 설명 · 수정 폼이 전부 그것을 읽는다.
- **표기 3값은 rev1 축자다** — `40 COLAB-기획/10_적용전/업로드_계보_260826_rev1_이태헌.html` 의 `<option>` 세 줄(`연구실 구성원 전체`·`나만 보기`·`지정한 사람만`)이고 `VAL-007b` 가 기본값을 `연구실 구성원 전체` 로 못 박는다. ⛔ **rev2 의 3값(`비공개`·`조건부 공개`·`전체 공개`)을 쓰지 않았다** — 기준축이 연구실 **밖**이라 한 칸씩 어긋나고, 미결-1 ⓐ 가 rev1 을 확정했다(PRD-11 대응표).
- **되묻는 문면**은 rev1·rev2 **어디에도 없다**(`grep '끊'` = rev1 0건 · rev2 1건이고 그 1건은 무관한 산문). 그래서 정본은 PRD-11 상태 전이표의 한 줄이고 그대로 썼다 — `지금 볼 수 있는 사람 N명의 접근이 끊깁니다`. **지어내지 않았다.**
- 헤더 칩은 **`열림` 이 아닌 두 값**에만 선다. `열림` 에 배지를 붙이면 모든 상세에 칩이 서고 판단에 안 쓰인다.
- 끊길 사람이 **0명이면 되묻지 않는다** — 잃을 것이 없는 확인은 반사가 된다.

## 게이트 (배출처 `dev-package/reports/R-B/p3-visibility-3`)

| 게이트 | 출력 |
|---|---|
| `schema-diff` | `schema-diff green — 두 체인 각각 선언 = 적용.` |
| `migration-single-head` | `migration-single-head green — 두 체인 모두 head 1개.`(head `0017_rb4_access_state_3`) |
| `contract-lint` | `contract-lint green — seam 3건, 룰 위반 0.` |
| `contract-breaking`(기준 `3e2dcd8`) | `contract-breaking green — 기준 3e2dcd8 (3건) 대비 파괴적 변경 없음.` — warning 11건(위 축자) |
| `generated-up-to-date` | `generated-up-to-date green — 등기부 10건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.` |
| `db-boundary` | `green  db-boundary` |
| `rls-coverage` | `rls-coverage green — allow-list 밖 테이블 전부 FORCE RLS + 연구실 경계 정책, 본체 테이블은 본체 정책까지.` |
| `rls-effect` | `rls-effect green — 본체 음성 · 메타 양성(P-13) · cross-tenant 셋 다 엔진이 막는다. 판정 롤은 우회 불가.` |
| `service-tests-core-api` | `service-tests-core-api green — 실행 871건 전부 통과 (skipped 0 · deselected 6 은 요약줄에 드러나 있다).` |
| `frontend-typecheck` | `frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.` |
| `frontend-test` | `frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 922건 · 실패 0건.` |
| `work-item-consistency` | `work-item-consistency: green — 대장과 산문의 불일치 0` |
| `0017-drift.sh` | 위 GREEN 축자(게이트 밖 — 아래 후속 1) |

계 = **green 12 / red(판정) 0 / red(준비) 0**. 마지막 커밋 뒤에 12건을 다시 돌렸다 — `all` 은 돌지 않았다(레인 규약 §3-1).

## 자기 표시

- **`DatasetDetail.activeGrantCount` 를 신설했다(요청되지 않은 초과분에 가깝다).** 지시문은 「API 가 되묻는 문면용 수를 돌려준다」까지만 적었고 그 자리를 지정하지 않았다. 되묻기는 **저장 전에** 일어나므로 수정 응답만으로는 늦다 — 상세가 그 수를 갖고 있어야 화면이 물을 수 있다. **사람 목록은 안 내렸다** — 필요한 것은 범위가 아니라 수다.
- **되묻기를 `window.confirm` 이 아니라 화면 요소로 만들었다** — 저장 행(`DatasetEditActions`)이 확인/취소 두 갈래로 바뀐다. 브라우저 대화상자는 시험이 잡지 못하고 문면도 조절할 수 없다.
- **`updateDataset` 에 공개 범위 칸을 열었다** — 「소유자가 내린다」를 집행할 경로가 그것뿐이다. 편집 폼 셀렉트가 함께 섰고, 그래서 `detail-edit.test.tsx` 의 「R-B 가 더할 칸」 목록에서 `공개 범위` 가 빠졌다(나머지 넷은 그대로 R-B 다른 WU 몫).
- ~~**`null` 을 화면에서 못 고르게 했다**~~ ⭑ **⟨advisor ② ㊁ 로 뒤집혔다 — 아래 「advisor ② 반영」 절⟩** 등록 셀렉트 첫 칸이 「연구실 기본값」(미조작)이고, 그 상태로 등록하면 요청에서 열쇠가 빠진다. 종전 기재(「rev1 셀렉트가 3값이고 기본 선택이 있어 빈 상태가 없다」)는 PRD-11 「NULL = 연구실 기본값(현행 의미 유지)」와 어긋났다.
- **수정에서 `null` 이 행을 안 지우게 했다** — 지우면 `updated_at` 이 사라져 「한 번도 안 정했다」와 구별이 없어진다. 라운드가 그 갈래를 정하지 않아 여기서 정했다.
- **거절 전이(잠김 ＋ 거절 → 잠김)에 시험을 하나 더 붙였다** — 라운드 수용 기준 6건에 없다. 승인이 상태를 올리는 코드가 거절 경로에도 새면 불변식이 반대 방향으로 깨진다.
- **환경 조치 2건** — ⑴ 워크트리 `services/core-api/.venv` 에 `alembic` 부재 → `uv pip install alembic`(1.19.2) ⑵ 시험 DB `colab_platform` 을 `tests/fixtures/setup-db.sh` 로 재구성(선언 스키마가 바뀌었다) ＋ `colab_platform_applied` 에 `alembic upgrade head`(schema-diff 의 「적용 DB」). 둘 다 레포 파일 변경 0.
- **`conftest.py` 에 되돌림 2줄을 더했다** — `d2_dataset_access` 청소(시드 데이터셋 제외) ＋ 시드 두 행 복원. 없으면 「DSA2 는 잠김」을 오라클로 삼는 시험 전부가 순서에 따라 갈린다.

## 하지 않은 것

- **RLS 경계 확대** — 연구실 밖 공개는 PRD-37 · `WU-C5` 범위 밖(미결-1 ⓐ). 델타에 정책 문장 0건이고 드리프트 스크립트가 그것을 잰다.
- **`body_access` 정책·접근 판정 함수 수정** — `지정 공개` 는 grant 갈래를 그대로 탄다(PRD-11 축자).
- **DB 층 불변식 가드(트리거·제약)** — 두 표에 걸친 조건이라 CHECK 밖이고, 「스키마 변경 = CHECK 확장」 범위를 지켰다. 자리는 응용 층 두 함수 ＋ 회귀 시험이다.
- **`지정 공개` 의 허용자 목록 화면** — 이 회차 범위 밖. 상세는 **수**만 내린다.
- **연구실 설정 화면의 `default_visibility` 셀렉트 3값화** — CHECK·계약은 함께 넓혔고(`LabDefaultVisibility` 가 `$ref`), 그 화면(`LabInfoPanel.tsx`)은 안 건드렸다. 라운드 문면이 지목한 FE 는 등록 ②·상세 헤더·공개 범위 설명 셋이다. **후속 항목 4.**
- **`PLAN-SoT §9` 〈N〉 등재 · `03-HANDOFF.md` 수정 · 대장 `done` 전환** — 병합 직전 오케스트레이터 몫.

## 후속

1. **`db/platform/tests/*-drift.sh` 가 어느 게이트에도 안 걸린다** — `grep -rn "drift.sh" gates/` = 0건. `0017-drift.sh` 도 같다. 게이트 승격 대상(`colab-rules §3-3`-⑷). WU-B1·B2 후속 1번과 같은 항목이고 이번 회차가 한 벌 더 쌓았다.
2. **`alembic` 이 어느 `requirements*.txt` 에도 없다** — 새 워크트리마다 손으로 채운다(B2 후속 2와 같다).
3. **`colab_platform_applied`(schema-diff 의 「적용 DB」)를 최신 head 로 올리는 절차가 게이트 밖에 있다** — 마이그레이션을 더한 레인이 손으로 `alembic upgrade head` 를 돌려야 하고, 안 돌리면 `schema-diff` 가 **선언 쪽 변경을 드리프트로 읽어** 판정 red 를 낸다. 실측으로 이번 회차가 밟았다. 절차를 게이트나 `RESTART.md` 에 세울 대상.
4. **연구실 설정 화면이 `지정 공개` 를 못 고른다** — `frontend/src/components/lab/LabInfoPanel.tsx:30` `VISIBILITIES = ['열림', '잠김']` (실측). 계약·DB 는 3값이라 값을 받으면 표시는 되고 **고르는 자리**만 없다. 어느 게이트도 이것을 red 로 내지 않는다 — 화면 상수는 계약 enum 을 참조하지 않고 손으로 적힌 배열이라 `frontend-typecheck` 가 좁은 쪽(2값)을 그대로 허용한다. 소유 WU 미지정.
5. **`지정 공개` 를 연구실 기본값으로 고르면 새 데이터셋이 허용 목록 0건으로 시작한다**(PRD-11 ⚠). ⚠ **등록 셀렉트 아래 한 줄은 그 사실을 적지 않는다** — 실제 문면은 `허용 목록에 오른 사람만. 만료 = 승인일 + 6개월`(`ACCESS_NOTE['지정 공개']`)이고 「0건으로 시작」 언급이 없다(advisor ② 지적 · 종전 기재는 과장이었다). 0건 시작 안내는 등록 화면과 **연구실 설정 화면** 둘 다에 없다(4번과 한 묶음).

---

## advisor ② 반영 (검토문 `advisor2-b4.md` · verdict = approve-with-changes)

### ㊀ [필수] 경합 잠금 — 데이터셋 단위 `pg_advisory_xact_lock`

- **지적** = 완료 조건 「`잠김` ∧ 유효 grant ≥1 이 **어느 시점에도** 0건」을 직렬 경로만으로 증명했다. READ COMMITTED 에서 승인(T1)과 내림(T2)이 겹치면 T2 의 만료가 T1 의 미커밋 grant 를 못 보고, T2 의 상태 UPSERT 가 `잠김` 으로 덮는다.
- **조치** = `services/core-api/src/colab_core/domains/d2_access.py` — `set_access_state` 와 `decide_access_request` 의 **첫 문장**이 `SELECT pg_advisory_xact_lock(hashtext(...))` 을 잡는다. 상수 `_LOCK_DATASET`(데이터셋 id) ＋ `_LOCK_REQUEST_DATASET`(요청 줄에서 데이터셋 id 를 읽어 잠근다). **행 없는 케이스도 덮는다** — 상태 행이 아직 없는 데이터셋(NULL = 연구실 기본값)에는 잠글 행이 없어 행 잠금으로는 못 막는다. `xact` 판이라 트랜잭션 종료 시 자동 해제다.
- **시험 = 진짜 동시성이다**(잠금 존재 확인으로 갈음하지 않았다). `session_factory` 가 독립 커넥션을 주므로 두 트랜잭션을 실제로 겹쳤다 — T1 승인(커밋 전) → 스레드로 T2 내림 → `worker.is_alive()` 로 **막혔음**을 확인 → T1 커밋 → T2 완주 → 끊긴 사람 수 1 ＋ 불변식 0건.
- **RED 축자** — `AssertionError: 끊긴 사람 수가 1 이 아니다: [0]` / `assert [0] == [1]` (`tests/test_access_state_three.py:283`).
  잠금 없이도 T2 는 `d2_dataset_access` **행 잠금**에 막혀 기다렸으나, 그 사이 이미 돈 만료 UPDATE 가 0행이라 `잠김` ∧ 유효 grant 1건이 성립했다 — advisor 가 적은 파손 경로 그대로다.
- **GREEN** — `services/core-api/tests/test_access_state_three.py`:13건(증보 1건 `test_approval_and_lowering_cannot_interleave`).

### ㊁ [필수 · 판정] 미조작 시 `accessState` 생략 — **오케스트레이터 채택 (a) · Ted 추인 대기**

- **지적** = `UploadModal` 이 `accessState` 를 늘 실어, 연구실 기본값 경로가 UI 등록분에서 소멸했다. 기본값 `잠김` 인 연구실에서 파일만 올린 사람의 데이터셋이 `열림` 으로 저장된다(개방 방향 회귀 · PRD-11 「NULL = 연구실 기본값(현행 의미 유지)」와 어긋남).
- **판정** = advisor 선택지 **(a) 채택** — 사용자가 공개 범위 셀렉트를 **건드리지 않으면 열쇠를 생략**한다. ⚠ **오케스트레이터 채택이고 Ted 추인 대기다.**
- **조치**
  - `frontend/src/components/upload/UploadModal.tsx` — 상태가 `AccessState | null` 이고 초기값 `null`. 제출 본문은 `...(accessState === null ? {} : { accessState })`. `hasHumanInput` 도 `accessState !== null` 로 바뀌었다(고른 순간부터 「잃을 것」).
  - `frontend/src/components/upload/RegisterArea.tsx` — 셀렉트 **첫 칸이 `연구실 기본값`**(값 `''` = 미조작)이고 그 아래 한 줄은 `연구실 설정의 데이터 공개 범위를 그대로 따른다`.
  - `frontend/src/components/common/accessState.ts` — `LAB_DEFAULT_LABEL`·`LAB_DEFAULT_NOTE` 신설.
- **초기 표시가 실제 기본값 라벨이 아니라 중립 문면인 이유** = `CurrentAccount` 에 `defaultVisibility` 가 **없다**(`frontend/src/generated/fe-core.ts` CurrentAccount 정의 · 계약 동결). 등록 화면은 `GET /labs/{id}` 를 부르지 않는다 — API 를 지어내지 않고 advisor 지시의 **중립 옵션** 갈래를 택했다. 실제 기본값 라벨 표시는 계약·화면 배선이 필요해 후속.
- **RED 축자** — 4건.
  `expected [ <option value="열림"></option>, …(2) ] to have a length of 4 but got 3` ·
  `expected '열림' to be ''` ·
  `expected true to be false`(미조작인데 열쇠가 실렸다) ·
  `expected [ 'accessState', 'category', …(9) ] to deeply equal [ 'category', 'dataType', …(8) ]`
- **GREEN** — `frontend/test/register-steps-20260907.test.tsx`(증보 2건 · 기존 2건 개정) ＋ `frontend/test/upload.test.tsx`(열쇠 목록 개정 ＋ `'accessState' in body === false`) → **136건 통과 / 실패 0**.
- **서버 쪽 짝은 이미 있다** — `test_registration_without_the_key_falls_back_to_the_lab_default`(열쇠 없이 만들면 `d2_dataset_access` 행을 **만들지 않고** 응답이 연구실 기본값을 싣는다).

### 작은 항목 (§Missed)

- `db/platform/versions/0017_rb4_access_state_3.py` — **downgrade 창에 FORCE 복구 단언 추가**(upgrade 와 같은 형태 · `pg_class.relforcerowsecurity` 로 `d2_dataset_access`·`d1_lab_profile` 두 표). 종전엔 upgrade 에만 있어 되돌린 DB 가 RLS 풀린 채 남을 수 있었다.
- `db/platform/schema.sql` — `d2_dataset_access_grant` 머리 주석 「잠김일 때만 쓰인다」를 고쳤다(`지정 공개` 가 쓰는 표다 ＋ 3값 뒤 `잠김` 의 뜻). **주석만이라 `schema-diff` green 유지**(실측).
- 이 노트 후속 5번 — 「등록 셀렉트 아래 한 줄이 0건 시작을 적는다」는 과장이었다. 실제 문면을 인용하고 「그 안내가 없다」로 고쳤다.
- 이 노트 「자기 표시」의 `null` 항목 — ㊁ 로 뒤집혔으므로 그 자리에 표시했다.

### 게이트 재실행 (배출처 `dev-package/reports/R-B/p3-visibility-3` · 마지막 커밋 뒤)

| 게이트 | 출력 |
|---|---|
| `schema-diff` | `green  schema-diff` — 계 green 1 / red(판정) 0 / red(준비) 0 |
| `service-tests-core-api` | `green  service-tests-core-api` — 계 green 1 / red(판정) 0 / red(준비) 0 |
| `rls-effect` | `green  rls-effect` — 계 green 1 / red(판정) 0 / red(준비) 0 |
| `frontend-typecheck` | `green  frontend-typecheck` — 계 green 1 / red(판정) 0 / red(준비) 0 |
| `frontend-test` | `green  frontend-test` — 계 green 1 / red(판정) 0 / red(준비) 0 |

계 = **green 5 / red(판정) 0 / red(준비) 0**. `gates/run.sh` 는 한 번에 한 게이트라 `gate-summary.json` 은 **마지막 실행분**이 남는다(위 다섯을 순서대로 돌린 뒤 `frontend-test` 분).

### 남은 위험 (advisor §Risks 중 미해소 — 후속)

- **Risk 3 이관 빈틈** — 상태 행 NULL ＋ 연구실 기본값 `잠김` ＋ 유효 grant 인 조합은 이관 후에도 실효 `잠김` 인데 허용자가 있다. 라운드 spec(NULL→NULL)의 빈틈이라 이 레인이 정하지 않는다.
- **Risk 4 내림 권한** — `_require_upload_edit`(업로드·편집 스위치 보유자 전원)이 PRD 문면 「소유자」보다 넓다. 설계 판정 대상.
- **Risk 5** — `_EXPIRE_GRANTS` 의 `expires_at = now()` 와 CHECK `expires_at > approved_at` 이 같은 tx 시각에서 충돌할 수 있다. 두 경로가 같은 tx 에 없어 현재는 이론상이다.
