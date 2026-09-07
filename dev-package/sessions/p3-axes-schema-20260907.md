# WU-B1 · 분류 3축 스키마·계약·서버 — 레인 `p3-axes-schema` (2026-09-07)

- 라운드 R-B · 파일 `dev-package/prd/rounds/R-B-1-db.md` §2 WU-B1 · PRD-01·02·03 · 크기 L.
- 기준 HEAD = `f6b9c48`(`integration/r-b` · ff-only 확인). 브랜치 `lane/p3-axes-schema`.
- 계약 개방 근거 = 20차 · 등급 ㉯ · Ted 승인 **2026-09-07**(`dev-package/sessions/R-B-C20-REQUEST-20260907.md` §Ted 승인). 승인이 `contracts/` 첫 수정보다 앞선다(커밋 순서 `235e1c8` → `29ef43f`).

## 완료 조건 ↔ 판정 ↔ 근거

| 완료 조건 (`R-B-1-db.md §5` WU-B1) | 판정 | 근거 (파일:행) |
|---|---|---|
| 5값·6값·4값 CHECK 가 선다 | 충족 | `db/platform/schema.sql:420`(category) · `:427`(data_type) · `:363`(processing_level_user_set) · 마이그레이션 `db/platform/versions/0015_rb1_axes_category_type_lv.py:102`·`:108`·`:119` |
| 계약에 세 열쇠가 있다 | 충족 | `contracts/seams/fe-core.yaml:3439`(Create) · `:3556`(Update) · `:3865`(BasicInfo) |
| 값 집합 밖은 400(500 아님) | 충족 | `services/core-api/src/colab_core/app/routes/catalog.py:564`·`:569`·`:577`(상수 3) · `:685`~`:695`(400 ＋ `allowed`) · 시험 `services/core-api/tests/test_axes_three.py:50`·`:67`·`:94` |
| 기존 행 3열 NULL · `topic` 무변 | 충족 | `db/platform/tests/0015-existing-rows-assertions.sql` ⑴~⑸ · 드리프트 ㈑ green |
| 사람 Lv ↔ 파생 Lv 불일치는 경고만 | 충족 | `catalog.py:593`(`warn_if_level_mismatch`) · `ingestion.py:642` · `catalog.py:830` · 시험 `test_axes_three.py:110` |
| 유형↔Lv 조합 제약 없음 | 충족 | 검사 코드 부재(의도) · 시험 `test_axes_three.py:83` · 오라클 `0015-assertions.sql` C-⑷ |
| `〈194〉` 반전이 원문을 지우지 않고 덧붙는다 | 충족 | `db/platform/schema.sql:331-335`(0011 삭제 근거 원문 유지) ＋ `:336-340`(반전 증보 · 원문 5줄 무삭제) · `contracts/schemas/common.json:161`(ProcessingLevel description 증보) |
| head 가 `0014_merge_ra1_and_topic_vocab` 를 잇는다 | 충족 | `0015_rb1_axes_category_type_lv.py:87`(`down_revision`) · `migration-single-head` green |

## 수용 기준 6건

| # | 기준 (축자) | 판정 | 근거 |
|---|---|---|---|
| 1 | 5값 밖 → **400** ＋ 응답에 `allowed` | **충족** | `test_axes_three.py:50`·`:67`·`:94` (3축 각각) |
| 2 | 마이그레이션 후 전 행 `category IS NULL` · `topic` 그대로 | **충족** | `0015-existing-rows-assertions.sql` ⑴·⑷ · `0015-drift.sh` ㈑ green · 대조군 ㈑-b red |
| 3 | `category` NULL 행에 「분류를 아직 안 골랐어요」 | **인계 WU-B3** | 표시층 문자열이라 서버에 자리가 없다. 서버는 `basicInfo.category = null` 을 그대로 내리고 화면이 깨지지 않음을 `test_dataset_detail.py:83` 이 잰다 |
| 4 | `관측 기반 산출물` ＋ `Lv1` → 성공 | **충족** | `test_axes_three.py:83` · `0015-assertions.sql` C-⑷ |
| 5 | 사람 Lv ↔ 파생 Lv 불일치 → 성공 ＋ 경고 | **충족(경고 자리 = 로그)** | `test_axes_three.py:110` · `catalog.py:593`. ⚠ **응답 열쇠는 만들지 않았다** — `processingLevelMismatch`·`processingLevelDerived` 는 PRD-10 이고 `R-B-2-server.md:54` 가 **WU-B5** 에 배정했다 |
| 6 | 기존 13행이 `processingLevel` 종전 값 ＋ `자동` 표기 | **서버분 충족 · 표기 인계 WU-B3** | 서버 = `processing_level_user_set` 이 NULL 인 동안 파생 `processingLevel` 무변경(`catalog.py` 의 `processing_level(summary)` 호출 무수정 · `test_axes_three.py:126` 이 `processingLevel == 0` 을 잰다). `자동` 칩은 화면 몫 |

## RED → GREEN

- RED 선실측 축자 (구현 전 · `tests/test_axes_three.py`) —
  `AssertionError: {"code":"BAD_REQUEST","message":"계약에 없는 필드다: ['category']"}` / `assert 400 == 201`
  계 = **11 failed · 1 passed** (통과한 1건 = `test_update_rejects_values_outside_the_sets_with_400` — 그 시점에는 「계약에 없는 필드」 400 이라 **오라클로서는 무효**였고, 구현 뒤 값 집합 400 으로 뜻이 바뀌어 green 이다).
- GREEN — `tests/test_axes_three.py` **12건 전부 통과**. 전체 `service-tests-core-api` = **842 통과 · 0 실패**.
- 기존 시험 1건 개정 = `tests/test_dataset_detail.py:83` `test_basic_info_is_the_nine_cells` — `basicInfo` 열쇠 집합 오라클에 세 열쇠를 더했다. **화면 칸 수(아홉)는 세지 않는다** — 상세 3행은 PRD-06 · WU-B7 이다.

## 마이그레이션

- head 이름 = `0015_rb1_axes_category_type_lv` (30자 · `alembic_version_platform.version_num` `varchar(32)` 상한 안).
- `down_revision = "0014_merge_ra1_and_topic_vocab"`.
- 담은 것 = `M-1`(category) · `M-2`(data_type) · `M-3`(processing_level_user_set 재신설). **backfill 0** · `UPDATE` 0줄 · `NO FORCE ROW LEVEL SECURITY` 구간 없음(고칠 행이 없다).
- 드리프트 시험 = `db/platform/tests/0015-drift.sh` (＋ `0015-assertions.sql` · `0015-existing-rows-seed.sql` · `0015-existing-rows-assertions.sql`).
  출력 축자 — `0015-drift green — ㈎ 적용 green · ㈏ 0015 없으면 red · ㈐ downgrade 실물 동작 + 0014 복원 · ㈑ 기존 행 전 행 NULL(대조군 red).`
  ⚠ 대조군의 방향이 `0013-drift.sh` 와 **반대**다 — 거기서는 「안 채우면 red」였고 여기서는 **「채우면 red」**다(미결-3 ⓐ 가 금지한 것이 자동 매핑이다).

## 되돌림 경로

- `downgrade` = 세 열과 세 CHECK 를 지운다(`0015_rb1_axes_category_type_lv.py` `DOWNGRADE`). 배포 직후에는 전 행 NULL 이라 **잃는 값 0**.
- ⚠ 값이 쌓인 뒤에는 다르다 — 세 칸 다 **사람이 고른 값**이라 `M-6`·`M-7` 과 같은 부류다. 그때의 정규 경로는 **소비를 멈추는 쪽**(계약·서버·화면에서 세 열쇠를 되돌리면 열은 남은 채 아무도 안 읽는다). 열까지 지우는 것은 값이 0 행일 때만.
- `topic`·`variables`·`format` 은 지우지 않았다 — 되돌림 경로이자 이관 대조 근거.

## 게이트 (배출처 `dev-package/reports/R-B/p3-axes-schema`)

| 게이트 | 출력 축자 |
|---|---|
| `schema-diff` | `schema-diff green — 두 체인 각각 선언 = 적용.` |
| `migration-single-head` | `migration-single-head green — 두 체인 모두 head 1개.` |
| `contract-lint` | `contract-lint green — seam 3건, 룰 위반 0.` |
| `contract-breaking` | `No breaking changes to report, but the specs are different.` / `Run 'oasdiff diff' to see structural differences.` / `contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.` |
| `generated-up-to-date` | `generated-up-to-date green — 등기부 10건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.` |
| `db-boundary` | `db-boundary: green — 단위 7개 · 스캔 대상 338건 · 위반 0` |
| `service-tests-core-api` | `service-tests-core-api green — 실행 842건 전부 통과 (skipped 0 · deselected 6 은 요약줄에 드러나 있다).` |
| `frontend-typecheck` | `frontend-typecheck green — tsc --noEmit(frontend/tsconfig.json · include=src·test) 오류 0건.` |

계 = **green 8 / red(판정) 0 / red(준비) 0.** `all` 은 돌지 않았다(레인 규약 §3-1).

⚠ **`contract-breaking` 이 green 인 것은 이번 회차의 열쇠가 전부 optional 이기 때문이다.** 20차 승인이 필요 없었다는 뜻이 **아니다** — 등급 ㉯ 판정의 근거는 파괴성 하나가 아니라 「마이그레이션 ≥1 ＋ 소비자 다수 ＋ 설계 판단 다수」이고, 라운드가 20차에 묶은 값 5종 중 파괴적인 것(`variables` 객체 배열 · `AccessState` 3값)은 **WU-B2·WU-B4** 에 있다. 〈N〉 행의 ④ 칸에는 위 축자를 그대로 쓴다.

## 소비자 수

- 이번 회차 세 열쇠 — `grep -rn 'category\|dataType\|processingLevelUserSet' contracts/ services/ frontend/src | wc -l` = **83**.
- 라운드 ㉰ 문안의 20차 전체 측정법 — `grep -rn 'variables\|accessState\|lineageUnknown\|category' contracts/ services/ frontend/src | wc -l` = **201** (2026-09-07 기준 · 라운드 파일 기재값 163 은 R-B 착수 전 실측이고 이 레인의 추가분이 그 차이에 든다).

## 자기 표시

- **의존한 오케스트레이터 가정 ⓐ** — 3축 컬럼의 자리는 `d3_dataset_description`(사람 입력)이고, 색인 반영(`M-10`)은 WU-B7 에서 미러/생성 열로 한다. 근거 = `dev-package/intent/2026-09-07-r-b.md` §확인 A-2 ＋ `sessions/R-B-C20-REQUEST-20260907.md` §Ted 승인. **Ted 원문은 「(없음)」이고 이것은 오케스트레이터 가정이다** — 번복되면 이 레인의 컬럼 자리 판단부터 다시 연다.
  ⚠ 단, `processing_level_user_set` 만 `d3_dataset` 이다 — `0007` 이 세우고 `0011` 이 지운 **그 자리**여야 반전이 성립하고, PRD-03 도 `d3_dataset` 을 명시했다. 오라클 `0015-assertions.sql` C-⑸ 가 그 자리를 붙잡는다.
- **PRD 문면과 라운드 파일이 갈린 자리 2건 — 라운드 파일을 따랐다**(`R-B-1-db.md §0` 「이 파일에 옮겨 적힌 문면이 우선」).
  ⑴ PRD-01 「`search_vector` 의 B 가중치 항을 `topic` 에서 `category` 로 교체」 → **하지 않았다.** 라운드 「마이그레이션 — 한 head」절이 색인 작업을 `M-10`(R-B-2 · WU-B7)으로 넘겼고, 앞당기면 생성 컬럼 재계산이 두 번 돈다.
  ⑵ PRD-03 「계약 `DatasetCreate`·`DatasetUpdate` 에 `processingLevel`」 → 열쇠 이름을 **`processingLevelUserSet`** 으로 했다. 라운드 §2 가 그 이름을 쓰고, `processingLevel` 은 응답의 파생 정수로 이미 점유돼 있다(같은 이름에 두 뜻을 붙이면 갈린다).
- **불일치 경고의 자리를 로그로 정했다** — 라운드·PRD-03 은 「경고만」이라고만 적고 모양을 정하지 않았다. 응답 열쇠를 새로 만들면 이번 회차의 계약 열쇠가 셋을 넘고, 그 열쇠(`processingLevelMismatch`)는 `R-B-2-server.md:54` 가 이미 WU-B5 에 배정했다. **모양은 `[미상]` 이고 지어내지 않았다.**
- **환경 조치 1건** — 워크트리 `services/core-api/.venv` 에 `alembic` 이 없어 드리프트 시험이 못 돌았다. `uv pip install alembic`(1.19.2)로 채웠다. 레포 파일 변경 0.

## 하지 않은 것

- **색인 재정의 · `search_vector`** — `M-10` · WU-B7(R-B-2). `0015-assertions.sql` D-⑵ 가 「이번 회차가 색인을 안 건드렸다」를 붙잡는다.
- **`DatasetRow`·`SearchHit` 확장 · `DatasetBasicInfo` required 승격 · 3축 질의 파라미터·필터** — **WU-B7**. 기존 행이 전부 NULL 이라 지금 required 로 올리면 그 행의 상세가 계약 위반이 된다.
- **`processingLevelDerived` · `processingLevelMismatch` · 응답 `processingLevel` 의 사람 값 우선 · `LV_CAP` 조정** — PRD-10 · **WU-B5**. `LV_CAP`(파생 상한 2)은 한 글자도 안 건드렸다.
- **화면** — 분류·유형·Lv 셀렉트 · 국문＋영문 병기 · 「분류를 아직 안 골랐어요」 · `자동` 칩 · 기본 선택값(`기상·기후 인자`·`재분석자료`·`Lv2`) 전부 **WU-B3**. `frontend/src` 손수정 0(생성물 `fe-core.ts` 재생성만).
- **ai-service `d9_topic_synonym` 4값 이관 · 픽스처 주제 값** — PRD-01 「영향 범위」가 지목했으나 라운드 WU-B1 절 범위 밖이고 체인이 분리돼 있다(`CLAUDE.md §3-3`). **후속 항목으로 올린다.**
- **`PLAN-SoT §9` 〈N〉·〈N+1〉 등재** — 병합 직전 오케스트레이터 몫(§4-1). 착수 시점 최대값 실측 = **372**(발급하지 않았다).
- **`03-HANDOFF.md` 수정** — 레인이 하지 않는다.

## 후속 항목

1. **`db/platform/tests/*-drift.sh` 가 어느 게이트에도 안 걸린다** — `grep -rn "drift.sh" gates/ .github/` = 0건. 마이그레이션 오라클 4벌(`0004`·`0005`·`0006`·`0008`·`0009`·`0013`·`0015`)이 사람이 손으로 부를 때만 돈다. 「검사가 게이트 밖에만 있으면 그 자체가 결함」(`colab-rules §3-3`-⑷)에 해당하므로 게이트 승격 대상이다.
2. **`alembic` 이 어느 `requirements*.txt` 에도 없다** — 루트 체크아웃 `services/core-api/.venv` 에만 임시로 들어 있어 새 워크트리에서 마이그레이션 도구가 없다. 위 1번을 게이트로 올리면 그 게이트가 red(준비)로 항상 뜬다.
3. **`ai-service` 주제 4값 ↔ 분류 5값 이관**(PRD-01 영향 범위) — 소유 WU 미지정.
