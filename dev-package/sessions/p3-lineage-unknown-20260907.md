# WU-B8 · 계보 상태 판정식 6항 ＋ 「기록 없음」 체크박스 — 레인 `p3-lineage-unknown` (2026-09-07)

- 라운드 R-B · 파일 `dev-package/prd/rounds/R-B-2-server.md` §2 WU-B8 · PRD-27 · 크기 M · **스키마 0 · 마이그레이션 0**.
- 기준 HEAD = `5adf9b4`(`integration/r-b` · ff-only 확인) → **최종 커밋 전 `3427ec4` 로 리베이스**(형제 레인 WU-B7 이 먼저 병합). **충돌 0** — 겹치는 파일은 `d3_catalog.py` 하나이고 B7 은 `_APPLY_AUTOMETA`, 이 레인은 `lineage_state()` 로 자리가 갈렸다. 브랜치 `lane/p3-lineage-unknown`.
- 계약 개방 근거 = 20차 · 등급 ㉯ · Ted 승인 **2026-09-07**(`dev-package/sessions/R-B-C20-REQUEST-20260907.md`). 승인이 `contracts/` 첫 수정보다 앞선다.
- 선행 = WU-B1(사람 Lv `processing_level_user_set`) · WU-B3(등록 ③ 골격). 둘 다 통합 브랜치에 있다.

## 1. 완료 조건 ↔ 판정 ↔ 근거

| 완료 조건 (`R-B-2-server.md §5` WU-B8) | 판정 | 근거 |
|---|---|---|
| 6항 판정식이 `lineage_state()` 를 대체한다 | 충족 | `services/core-api/src/colab_core/domains/d3_catalog.py` `lineage_state(core, summary, *, unknown_declared=False)` — 여섯 분기가 위에서부터 순서대로 |
| 자동 `mark_unknown` 이 걷혔다 | 충족 | `services/core-api/src/colab_core/app/routes/ingestion.py` `else:` → `elif lineage_unknown:` · 시험 `test_lineage_unknown.py::test_the_automatic_mark_unknown_row_is_gone`(저장 자리를 직접 센다) |
| `lineageUnknown` 이 계약·`_ALLOWED_CREATE_FIELDS` 양쪽에 **같은 회차**에 섰다 | 충족 | `contracts/seams/fe-core.yaml` `DatasetCreate.lineageUnknown` ＋ `ingestion.py` `_ALLOWED_CREATE_FIELDS` — 한 커밋 |
| 부모 0/체크/Lv0 세 갈래가 갈린다 | 충족 | `test_lineage_unknown.py` 3건(아래 §2 ①②③) |
| **부모 ≥1 경로 회귀 green** | 충족 | 신규 2건 ＋ 기존 5건(§3) |
| 라벨 축자 ＋ 종전 문면 **0건** | 충족 | `frontend/src/components/lineage/LineageStep.tsx` `LINEAGE_UNKNOWN_LABEL` · FE ㈑ 가 `src`·`test` 전 파일(**1,000건 이상** 훑고 0건) |
| 부모 1건 ＋ `true` 전송 **400** | 충족 | `ingestion.py`(부모 존재 판정 **앞**에서 즉시 400) · `test_a_parent_plus_lineage_unknown_true_is_a_400` |
| 홈 타일 숫자와 링크 목록 건수가 **같다** | 충족 | `dashboard/SummaryTiles.tsx` `UNSETTLED_LINEAGE_STATES` 한 상수를 `LINEAGE_TODO_PATH` 와 `dashboardSource.ts` 가 나눠 쓴다 · FE ㈒ 2건 |
| 존치 6종 untouched (AI 계보 제안 포함) | 충족 | `ai-no-lineage-write` green · `LineageStep` 의 제안·`lin-ask`·빈 상태 3분기 코드 변경 0 |
| 스키마 0 · 마이그레이션 0 | 충족 | `db/` 변경 0건 |

## 2. 수용 기준 7 ↔ 시험

| # | 기준 (축자) | 판정 | 시험 |
|---|---|---|---|
| ① | 부모 0 · 미체크 · 사람 Lv=`Lv1` ⟹ `확인 필요` | green | `test_no_parents_unchecked_with_a_human_level_is_needs_check` |
| ② | 부모 0 · 체크함 ⟹ `기록 없음` | green | `test_no_parents_checked_is_no_record` ＋ `test_a_declaration_writes_the_row`(행 존재) |
| ③ | 부모 0 · 미체크 · 사람 Lv=`Lv0` ⟹ `원천` | green | `test_no_parents_unchecked_at_lv0_is_origin` |
| ④ | 사람 Lv NULL ∧ unknown 행 있음 ⟹ `기록 없음` (회귀) | green | `test_a_human_level_of_null_with_an_unknown_row_stays_no_record`(등록 응답 ＋ 상세 재조회 둘 다) |
| ⑤ | 부모 ≥1 경로 판정이 종전과 동일 (회귀 증명) | green | 신규 `test_the_parent_path_is_unchanged` · `test_the_parent_path_ignores_lv0_and_the_source_label` ＋ 기존 5건(§3) |
| ⑥ | 부모 1 확정 ⟹ 체크박스 비활성 ＋ 사유 ＋ **칸 존재** | green | FE ㈏ (`disabled`·`lin-unknown-why` 축자·`lin-card` 1건 잔존·요청에 열쇠 미전송) |
| ⑦ | 라벨 축자 ＋ 옛 문면 0건 / 부모1 ＋ `true` ⟹ 400 / 홈 타일 = 링크 목록 | green | FE ㈎·㈑·㈒ · 서버 `test_a_parent_plus_lineage_unknown_true_is_a_400` |

## 3. 부모 ≥1 회귀 — 재사용한 기존 시험 5건

이 개정은 판정 ①② 를 **한 글자도 고치지 않았다**. 그 사실을 아래 기존 시험이 그대로 증명한다(전건 green).

| 시험 | 재는 것 |
|---|---|
| `test_dashboard.py::…` (`:37` 주석 「확정일이 마지막 수정보다 뒤라 **확정**」) | 부모 있는 시드 행 `DSA2` 의 `확정` |
| `test_dataset_files.py::test_replacing_a_grid_file_does_not_fold_the_lineage_state` | 격자 교체가 `확정` 을 접지 않는다 |
| `test_dataset_files.py::test_a_body_change_moves_last_modified_and_folds_the_lineage_state` | 본체 변경 → 판정 ① `확인 필요` |
| `test_dataset_facets.py::test_the_four_lineage_states_never_disappear` | 패싯 4값이 사라지지 않는다 |
| `test_lineage_confirm.py::test_adding_a_parent_clears_the_unknown_mark` | 관계가 붙으면 표시가 사라진다 (**표시를 세우는 방법만** `lineageUnknown=True` 선언으로 바뀌었다 · 재는 것 무변) |

## 4. 마이그레이션 전 선실측 — 게이트 DB

- 질의 = `부모 0건 ∧ d4_lineage_unknown 행 없음` 건수. 재는 자리 = 일회용 postgres(`gates/tools/_pg.sh`)에 `db/platform/schema.sql` ＋ `services/core-api/tests/fixtures/seed.sql` 적용.
- **결과 = 2건**(라운드 파일의 기대값 `0` 과 다르다). 실측표 —

| dataset_id | source_label | 부모 | unknown 행 |
|---|---|---|---|
| `…DSA1` | `기상청` | 0 | 없음 |
| `…DSA2` | (없음) | 1 | 없음 |
| `…DSB1` | `환경부` | 0 | 없음 |

- **화면 값이 바뀌는 기존 행 = 0.** 부모 0건인 두 행이 **둘 다 `source_label` 을 갖는다** — 종전 판정식 ③(`source_label` → `원천`)을 타던 자리를 개정 판정식 ⑸ 가 그대로 받는다. `확인 필요` 로 넘어가는 행은 없다.
- ⚠ **기대값 `0` 이 어긋난 이유는 시드가 자동 `mark_unknown` 을 지나지 않기 때문이다** — 시드는 SQL 로 직접 넣어 등록 경로를 밟지 않는다. 운영 DB(등록 경로를 지난 행)에서는 라운드 파일의 「부모 0건 행에 `d4_lineage_unknown` 이 빠짐없이 붙어 있다」가 성립하고, 그 행들은 판정 ⑶ 을 타 종전과 같이 `기록 없음` 이다. **운영 DB 실측은 이 레인의 자리가 아니다** — §9 후속으로 올린다.

## 5. RED → GREEN

- 서버 `services/core-api/tests/test_lineage_unknown.py` **14건** — RED **10 failed / 4 passed**.
  축자 ㈎ `AssertionError: assert '기록 없음' == '확인 필요'` · ㈏ `{"code":"BAD_REQUEST","message":"계약에 없는 필드다: ['lineageUnknown']"}`.
  ⚠ RED 시점 통과 4건 중 **400 시험 1건은 「계약에 없는 필드다」 400 으로 통과한 가짜 green** 이다 — 구현 뒤에는 「모른다」와 「부모」의 동시 전송을 막는 400 으로 통과한다.
  GREEN = **14 passed**.
- 프런트 `frontend/test/lineage-unknown-20260907.test.tsx` **8건** — RED **7 failed / 1 passed**(구현 6파일을 `git stash` 한 트리에서 실측).
  축자 ㈎ `TestingLibraryElementError: Unable to find an element by: [data-testid="lin-unknown-check"]` · ㈏ `TypeError: UNSETTLED_LINEAGE_STATES is not iterable`.
  ⚠ RED 시점 통과 1건 = 종전 문면 0건 — 그 문자열은 **이 회차 전에도 코드에 없었다**(폐기 문면의 재유입 방지 시험이라 처음부터 green 인 것이 정상이다. 오라클로 쓰지 않는다).
  GREEN = **8 passed**.
- 기존 시험 2건이 개정으로 red 를 냈고 **둘 다 종전 판정을 단언하던 자리**라 문면과 함께 고쳤다(§3 표 마지막 줄 · `test_dataset_registration.py` 의 `기록 없음` → `확인 필요`). ⛔ 재는 것을 줄이지 않았다.

## 6. 계약 — `contract-breaking` 축자

```
No breaking changes to report, but the specs are different.
```
기준 `COLAB_BREAKING_BASE_REF=5adf9b4` · 대상 seam 3건. 여는 값 = `DatasetCreate.lineageUnknown` **1건**(optional boolean · 20차 범위 안).

## 7. 게이트 — 리베이스된 트리에서 재실행

배출처 `dev-package/reports/R-B/p3-lineage-unknown` · 기록본 `gate-summary.<게이트>.record.json` **7개**.

| 게이트 | 요약줄 |
|---|---|
| `contract-lint` | `contract-lint green — seam 3건, 룰 위반 0.` |
| `contract-breaking` | `contract-breaking green — 기준 5adf9b4 (3건) 대비 파괴적 변경 없음.` |
| `generated-up-to-date` | `generated-up-to-date green — 등기부 10건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.` |
| `service-tests-core-api` | `service-tests-core-api green — 실행 929건 전부 통과 (skipped 0 · deselected 6 은 요약줄에 드러나 있다).` |
| `ai-no-lineage-write` | `ai-no-lineage-write green` — 존치 6종 중 AI 계보 제안이 그대로임의 근거 |
| `frontend-typecheck` | `frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.` |
| `frontend-test` | `frontend-test green — vitest run(frontend/vite.config.ts · jsdom) 통과 966건 · 실패 0건.` |

**계 = green 7 / red(판정) 0 / red(준비) 0.** ⛔ 전수 `all` 은 돌리지 않았다(병합 직전 1회 · 오케스트레이터 몫).

⚠ **`frontend-typecheck` 가 한 번 red 였다** — 새 시험이 `__dirname`·`process` 를 타입 선언 없이 썼다(`error TS2304`·`TS2591` 2건). 「기존」이 아니라 **이 레인이 만든 결함**이고, **게이트가 잡았다**(Dockerfile 밖 · 배포 밖 아님). 형제 시험 `lv-rules-20260907` 과 같은 규율(`declare const process`)로 닫았다.

## 8. 자기 표시

- **`lineage_state()` 는 DB 를 보지 않는다.** 판정 ⑶ 의 입력을 인자(`unknown_declared`)로 받게 했다 — 함수 안에서 `is_unknown` 을 부르면 카탈로그 목록이 행 수만큼 질의를 여는 N+1 이 된다. 목록 두 자리(`catalog.py._compose` · `project.py._dataset_facts`)는 새 `d4_lineage.unknown_dataset_ids` 로 **한 번에** 읽는다.
- **`lineage.py` 는 같은 사실을 두 번 묻지 않는다.** 그 응답은 `lineageState` 와 `unknownParents` 를 **함께** 싣는데, 둘이 각자 질의하면 한 응답 안에서 갈릴 자리가 생긴다. `is_unknown` 을 한 번 재서 둘이 나눠 쓴다.
- **체크박스의 유효값을 모달이 계산한다**(`lineageUnknownEffective`). 확정 부모가 붙거나 ① 에서 Lv0 을 고른 뒤 **옛 `true` 가 그대로 실려 서버 400** 이 되는 경로가 실재했다 — ③ 은 단계 이동마다 언마운트되고 값은 모달에 남기 때문이다. 화면 비활성이 유일한 방어선이 아니게 서버 400 도 그대로 둔다.
- **홈 모수는 두 값 쪽으로 맞췄다.** 서버 타일(`routes/insight.py` `SETTLED_STATES = ("확정","원천")` 의 여집합)이 정본 `Policy_홈_대시보드 §4` 를 이미 집행하고 있고, PRD-27 은 그 §4 를 개정하지 않는다. 한 값(`확인 필요`) 쪽으로 맞추려면 서버 타일까지 고쳐야 하며 그것은 §4 개정이라 이 WU 범위 밖이다. 상수를 **한 곳**(`SummaryTiles.UNSETTLED_LINEAGE_STATES`)에 두고 링크와 조회가 나눠 쓰게 했다 — 값이 두 곳에 적혀 있던 것이 갈림의 원인이었다.
- **`URLSearchParams` 에 객체를 넘기지 않는다.** 두 값이 되면서 객체 리터럴은 같은 열쇠를 한 번만 담아 뒤엣값이 앞엣값을 지운다. 쌍의 배열로 넘겨 `lineageState` 를 반복시킨다.
- **`ingestion.py` 의 400 은 부모 존재 판정보다 앞이다.** 「모른다」와 「이것이 부모다」가 함께 온 요청은 부모가 실재하는지와 무관하게 모순이라, 뒤에 두면 없는 부모를 먼저 나무라게 된다.

## 9. 하지 않은 것 · 후속

| # | 항목 | 사유 | 소유 후보 |
|---|---|---|---|
| 1 | **운영·staging DB 선실측** — `부모 0건 ∧ unknown 행 없음` 건수 | 레인은 게이트 DB 까지가 자리다(§4). 게이트 DB 에서는 2건이고 둘 다 `원천` 유지라 **값이 바뀌는 행 0**. 운영 DB 는 등록 경로를 지난 행이라 판정 ⑶ 을 타지만 **재지 않았다** | 배포 창 전 점검 |
| 2 | 상세 화면에서 「기록 없음」을 **나중에 선언**하는 길 | `d4_lineage_unknown` 쓰기 경로가 등록 하나뿐이다. PRD-31(상세 계보 수정)의 자리 | **B10** |
| 3 | `routes/project.py` `ProjectDatasetRow.processingLevel` 이 파생값 그대로 | WU-B5 §10 후속 1 과 같은 자리. 이 WU 는 `lineageState` 만 건드렸다 | **B10** |
| 4 | 기존 `기록 없음` 행 정리 | PRD-27 축자 「그대로 둔다 — 자동으로 붙은 것이라 어느 쪽이었는지 사후에 알 방법이 없다」 | 하지 않음(판정) |
| 5 | `.lin-unknown:has(...)` — `:has()` 지원 브라우저 전제 | 대비·판독은 `lin-unknown-why` 가 별도 색으로 이미 든다. 지원 없으면 라벨 색만 진하게 남고 기능 영향 0 | B11 검수 |
| 6 | **배포 전 staging/prod 「부모 0 ∧ unknown 행 없음 ∧ source_label NULL」 건수 실측** | 게이트 DB 는 값이 바뀌는 행 0 이었으나 운영·staging DB 는 재지 않았다(위 §9-1 과 같은 이유) — 배포 창 전에 실측해 판정 ⑹ 로 몰리는 행 수를 확인한다 | 배포 창 전 점검 |

## advisor ② 반영

`/home/ttlhi10/.claude/jobs/18e71f5e/tmp/advisor2-b8.md` 의 「병합 전 필수」 Fix 1~3 을 RED→GREEN 으로 닫았다.

1. **[병합 전 필수]** `DatasetsPage.tsx:30` `params.get('lineageState')` → `params.getAll('lineageState')`. 첫 값만 읽던 것이 두 값을 다 실었다. FE 시험 ㈒ 에 「그 링크로 카탈로그를 열면 두 값이 그대로 목록 조회에 실린다」를 더했다 — RED: `expected [ '확인 필요' ] to deeply equal [ '확인 필요', '기록 없음' ]` → GREEN: `frontend-test` 9 passed(해당 파일).
2. `test_registering_without_parents_is_recorded_as_unknown_not_as_a_guess` → `…is_needs_check_not_a_guess`(이름이 새 단언과 맞섰다). `lineage_state()` docstring ⑥ 을 「부모 0 ∧ 선언 없음 ∧ 원천 표기 없음 (사람 Lv NULL 포함)」으로 정정 — 종전 「사람 Lv ≥ Lv1」은 Lv NULL 행이 ⑹ 으로 떨어지는 사실과 어긋났다.
3. `ingestion.py:551` `sourceLabel` 을 `strip()` 하고 빈 문자열이면 `None` 으로 정규화 — 공백뿐인 값이 판정 ⑸ 의 truthiness 에 걸려 `원천` 이 되던 자리를 막았다. 새 시험 `test_whitespace_only_source_label_is_not_origin` — RED: `AssertionError: assert '원천' == '확인 필요'` → GREEN: `service-tests-core-api` 930 passed(0 failed). `d3_dataset_source_label_normalized` 류 DB 계산 컬럼은 코드베이스에 없어(grep 0건) 이 정규화는 앱 계층 단독이고 스키마·마이그레이션 영향 없음.
