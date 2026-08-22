# WU-P0 저장 형태 — `db/platform` · `db/ai` 스키마 기록

> P0 의 첫 조각. **저장 형태 정본을 코드로 옮긴 결과**와 그 근거를 남긴다.
> 화면·엔드포인트·FE 셸은 이 문서의 범위가 아니다(P0 의 나머지 조각).
>
> 정본 = `에픽/E-00_공통_기반/documents/DataModel_공통_기반.md` **v1.8**
> 기준표 = `dev-package/DATAMODEL-BASELINE.md` (G5)
> 어긋나면 **정본이 이긴다.**

---

## 1. 만든 것

| 경로 | 내용 |
|---|---|
| `db/platform/schema.sql` | 선언 스키마 정본(SoT). 테이블 **20개** · 도메인 1 · 함수 4 · 트리거 4 · RLS 정책 **19개** |
| `db/platform/alembic.ini` · `env.py` · `script.py.mako` | 체인 설정. `version_table = alembic_version_platform` |
| `db/platform/versions/0001_p0_platform.py` | 초기 리비전 1건. head 1개 |
| `db/ai/schema.sql` | **빈 골격** — 체인 상태 테이블 하나뿐. D9·D10 테이블 0건 |
| `db/ai/alembic.ini` · `env.py` · `script.py.mako` | `version_table = alembic_version_ai` — **이름이 다른 것이 체인 분리의 실물이다** |
| `db/ai/versions/0001_p0_ai.py` | 초기 리비전 1건(테이블 생성 없음). head 1개 |
| `gates/config/rls-allowlist.toml` | `body_tables` 에서 `d7_viz_source` 를 **주석으로 내렸다**(아래 §6) |

접속 URL 은 어디에도 적지 않았다 — `COLAB_PLATFORM_DB_URL` · `COLAB_AI_DB_URL` 환경변수로만 들어온다.

---

## 2. 테이블 목록과 정본 근거

`(면제)` = RLS 면제, `(본체)` = 파일 본체 테이블. 그 밖은 전부 `lab_boundary` 정책 + FORCE RLS.

### D1 Identity & Lab — 정본 §2 §3

| 테이블 | 컬럼 | 정본 근거 |
|---|---|---|
| `d1_lab` **(면제)** | `id` · `name` · `opened_at` · `created_at` | §2 「연구실 — 이름·개설일」. **테넌트 루트 자신이 경계**라 RLS 를 걸지 않는다 |
| `d1_lab_profile` | `lab_id`(PK=1:1) · `university` · `department` · `principal_investigator` · `research_field` · `introduction` · `default_visibility` | §2 「연구실 정보 — 소속 대학·학부/학과·책임교수·연구 분야·한 줄 소개」 · 「데이터 공개 범위 = 기본값 한 값」. 값 집합 2값은 `㉗`·`P-32` |
| `d1_account` | `id` · `lab_id` · `name` · `email` · `UNIQUE(lab_id,email)` | §3 「이름·메일」. 역할·스위치는 D2 가 소유한다 |

### D2 Access & Policy — 정본 §3 §4.1 · `PERMISSION-PRINCIPLES`

| 테이블 | 컬럼 | 정본 근거 |
|---|---|---|
| `d2_member_role` | `account_id`(PK) · `lab_id` · `role` CHECK `교수\|연구원` | §3 「역할」 · `P-2` |
| `d2_permission_switch` | PK`(account_id, switch)` · `switch` CHECK 4값 · `enabled` | §3 「권한 스위치 4종」 · `P-3`·`P-4`. **스위치 하나 = 한 행** — 다섯 번째 열이 생길 수 없다 |
| `d2_permission_change` | `id` · `changed_at` · `actor_account_id` · `target_account_id` · `switch` · `direction` CHECK `켬\|끔` | **정본에 항목이 없다.** `PLAN-SoT §9-㉘`·`P-33` 의 레포 결정. append-only 는 트리거로 강제 |
| `d2_dataset_access` | `dataset_id`(PK) · `state` **nullable** CHECK `열림\|잠김` | §4.1 「접근 상태」. NULL = 「따로 정하지 않음」 → 연구실 기본값 적용. 값이 있으면 데이터셋이 이긴다(`P-27`) |
| `d2_dataset_access_grant` | `id` · `dataset_id` · `grantee_account_id` · `approver_account_id` · `approved_at` · `expires_at` | §4.1 「볼 수 있는 사람 목록 · 만료일 = 승인일+6개월」 · `P-24`·`P-25` |
| `d2_verified` | `dataset_id`(PK) · `verified` · `approver_account_id` · `approved_at` · `cancelled_by_account_id` · `cancelled_at` · `cancellation_reason` | §4.1 「Verified 기록 — 승인 여부·승인 교수·승인 시각, 취소 시 취소한 사람·시각·사유」 |

`dataset_id` 는 전부 **bare 컬럼**이다 — D2 가 D3 테이블을 직접 FK 하지 않는다(`CLAUDE.md §3-1`).

### D3 Catalog — 정본 §4.1 §4.3

| 테이블 | 컬럼 | 정본 근거 |
|---|---|---|
| `d3_dataset` | `id` · `lab_id` · `owner_account_id` **NOT NULL** · `uploader_account_id` **불변** · `source_label` · `uploaded_at` · `last_modified_at` · `lineage_confirmed_at` · `deleted_at` · `deleted_by_account_id` | §4.1 「소유자 빈 값 불가」(`P-29`) · 「올린 사람 바뀌지 않는다」(`P-30`, 트리거) · 「원천 표기」 · 「레코드 시점 3종」 · 「삭제 기록(묘비)」 |
| `d3_dataset_description` | `dataset_id`(PK) · `name` NOT NULL · `topic` · `summary` | §4.1 「사람이 적는 정보 — 이름·주제·설명」 |
| `d3_dataset_autometa` | `dataset_id`(PK) · `format` · `variables[]` · `period_start/end` · `crs` · `grid` · `total_size_bytes` · `bundle_file_name` | §4.1 「자동으로 읽은 정보」 + §4.3 합치는 규칙의 **결과**를 담는다. `bundle_file_name` 은 §4.3 「묶음 이름」 |
| `d3_file` **(본체)** | `id` · `dataset_id` FK · `kind` CHECK `본체\|기준 격자 파일` · `file_name` · `size_bytes` · `storage_key` | §4.3. **데이터셋 1:N.** 기준 격자 0~1건은 부분 UNIQUE 인덱스로 강제. **계보 컬럼이 없는 것**이 「파일에는 계보가 없다」의 저장 형태 |

### D4 Lineage — 정본 §4.2

| 테이블 | 컬럼 | 정본 근거 |
|---|---|---|
| `d4_lineage_edge` | `id` · `child_dataset_id` · `parent_dataset_id` · `parent_role` CHECK `주입력\|보조입력` DEFAULT `주입력` · `method` · `origin` CHECK 2값 · `confirmed_by_account_id` **NOT NULL** · `confirmed_at` **NOT NULL** · `UNIQUE(child,parent)` · `CHECK(child<>parent)` | §4.2 전 행. **가공 방식이 관계에 붙는다**(소급 §3-②) · 부모 여럿 가능 · 확인 기록이 NOT NULL 인 것이 「사람이 확인한 관계만 저장한다」 |
| `d4_lineage_unknown` | `dataset_id`(PK) · `marked_at` · `marked_by_account_id` | §4.2 「기록 없음 표시」. 관계가 붙으면 행을 지운다 |

### D6 Project — 정본 §5

| 테이블 | 컬럼 | 정본 근거 |
|---|---|---|
| `d6_project` | `id` · `type` CHECK `국가과제\|논문` · `name` · `description` · `period_start/end` · `link_url` · `status` CHECK `진행 중\|닫힘` | §5. 삭제는 없다 — soft-delete 컬럼조차 두지 않았다 |
| `d6_project_dataset` | `id` · `project_id` FK · `dataset_id`(bare) · `usage_note` · `UNIQUE(project_id,dataset_id)` | §5 **N:N** + 「활용 의미 문장은 연결마다 따로」(소급 §3-⑥) |

### 공통 기록 D8 — 정본 §6

| 테이블 | 컬럼 | 정본 근거 |
|---|---|---|
| `d8_activity` | `id` · `actor_account_id` · `action` · `target_kind` CHECK `데이터셋\|프로젝트` · `target_id` · `occurred_at` | §6.1 「누가·무엇을·언제·어떤 일」. **바꾼 일만** — 열람 기록 테이블이 없는 것이 그 강제다 |
| `d8_download` | `id` · `account_id` · `dataset_id` · `downloaded_at` | §6.2 「쌓기만 하고 1차 화면에 안 쓴다」 |

### 체인 상태

`alembic_version_platform` **(면제)** · `alembic_version_ai` **(면제)** — 연구실 데이터가 아니다.

---

## 3. DataModel v1.8 §3 표 전 항목 대조 (P0 완료 판정 #6)

| # | 정본이 못 박은 것 | 스키마에서의 실물 | 판정 |
|---|---|---|:--:|
| 1 | 데이터셋 : 파일 = **1 : N** (본체 1+ · 기준 격자 0~1) | `d3_file.dataset_id` FK + `kind` CHECK 2값 + 부분 UNIQUE(`kind='기준 격자 파일'`) | ✅ |
| 2 | 계보 = 관계 기록, **부모 여럿** | `d4_lineage_edge` 행 다건, `UNIQUE(child,parent)` 만 걸었다 | ✅ |
| 3 | 가공 방식은 **관계에 붙는다** | `d4_lineage_edge.method` — 데이터셋 테이블에 없다 | ✅ |
| 4 | **사람이 확인한 것만 저장** | `confirmed_by_account_id`·`confirmed_at` NOT NULL · `origin` 에 `제안` 값 없음 | ✅ |
| 5 | **파일에는 계보가 없다** | `d3_file` 에 부모/계보 컬럼 0개 | ✅ |
| 6 | 소유자 **NOT NULL** | `d3_dataset.owner_account_id NOT NULL` | ✅ |
| 7 | 올린 사람 **불변** | `d3_dataset_uploader_immutable` 트리거 | ✅ |
| 8 | Lv = **자동 계산** | **컬럼 없음.** D4→D3 읽기 Port(`㉑`)로 계산 | ✅ |
| 9 | 계보 상태 4값 = **파생** | **컬럼 없음** | ✅ |
| 10 | 프로젝트 연결 **N:N** + 연결마다 의미 문장 | `d6_project_dataset(project_id, dataset_id, usage_note)` | ✅ |
| 11 | 다시 올리기(버전) **자리 없음** | 버전·리비전 컬럼 0개 | ✅ |
| 12 | 활동 기록 = **바꾼 일만**, 열람 안 남김 | `d8_activity` 만 있고 열람 테이블 없음 | ✅ |
| 13 | 다운로드 이력은 쌓기만 | `d8_download` — 읽는 화면 없음 | ✅ |
| 14 | 연구실 경계 = 모든 조회의 기본 필터 | 전 테넌트 테이블 FORCE RLS + `lab_boundary` (18개) | ✅ |
| 15 | 접근 상태 = 열림/잠김 + 허용자 목록, 데이터셋이 연구실 기본값을 **이긴다** | `d2_dataset_access.state` nullable + `d2_dataset_access_grant` + `body_access` 정책의 `COALESCE(데이터셋, 연구실기본값)` | ✅ |
| 16 | 삭제 = **묘비** | `deleted_at`·`deleted_by_account_id` — 행 삭제 없음. 계보·연결·Verified 는 남는다 | ✅ |
| 17 | 레코드 시점 **3종** | `uploaded_at`·`last_modified_at`·`lineage_confirmed_at` | ✅ |
| 18 | 원천 표기 | `d3_dataset.source_label` | ✅ |
| 19 | Verified 기록(취소 포함) | `d2_verified` 7컬럼 | ✅ |
| 20 | 역할 2값 · 권한 스위치 4종 | `d2_member_role.role` · `d2_permission_switch` | ✅ |
| 21 | 값 집합은 **DB 가 강제**(`⑲`) | 확정 열거값 **9종 전부** CHECK. v1 은 CHECK 가 하나도 없었다 | ✅ |
| 22 | 정규 ID = ULID | `CREATE DOMAIN ulid AS char(26)` — 전 컬럼이 이 도메인 | ✅ |
| 23 | 본체 여럿일 때 합치는 규칙 6항 | `d3_dataset_autometa` 가 **결과**를 담는다. 규칙 자체의 시행은 적재 경로(D5·P2) | 🟨 자리만 |

**소급 위험 11건**(`DATAMODEL-BASELINE §3`) 대응 — ①1:N ②관계 부착 ③④파생 미저장 ⑤시점 3종 ⑥N:N ⑦제안 상태 없음 ⑧묘비 ⑨테넌시 컬럼 빈칸 0 ⑩ULID 도메인 1곳 ⑪CHECK — **전부 반영.**

---

## 4. RLS 정책 — 무엇을 막는가

`㉖`·`P-34` 의 두 층을 그대로 옮겼다.

| 정책 | 걸린 곳 | 막는 것 |
|---|---|---|
| `lab_boundary` (PERMISSIVE, FOR ALL, USING + WITH CHECK) | 테넌트 테이블 **18개** | 다른 연구실 행의 **읽기·쓰기 양쪽**. `WITH CHECK` 가 없으면 남의 `lab_id` 를 써 넣는 경로가 남는다 |
| `body_access` (**RESTRICTIVE**, FOR ALL) | `d3_file` **하나** | 잠긴 데이터셋의 **파일 본체**. 허용자 목록에 없거나 **만료된** 접속은 DB 층에서 0행이다 |
| — (정책 없음) | `d1_lab` · `alembic_version_*` | 면제. 테넌트 루트는 자기가 경계이고, 체인 상태는 연구실 데이터가 아니다 |
| — (**경계 정책만**) | `d3_dataset`·`_description`·`_autometa` | **일부러 본체 정책을 걸지 않았다.** 걸면 잠긴 행이 목록에서 사라져 `P-13` 이 깨지고 E-06 승인 흐름이 죽는다 |

**설계 판단 3개**

1. **FORCE 까지 켠다.** `ENABLE` 만이면 테이블 소유자로 접속했을 때 정책이 통째로 무시된다 — 애플리케이션이 소유자 롤로 붙는 순간 경계가 없어진다.
2. **`body_access` 는 RESTRICTIVE 다.** PERMISSIVE 정책은 서로 **OR** 로 합쳐진다. 본체 정책을 permissive 로 걸면 경계 밖 행이 본체 조건만 맞아도 보여 두 층이 한 층으로 무너진다.
3. **기본 거부는 스코프 커널이 만든다.** `current_lab_id()` 는 GUC 를 Crockford base32 정규식으로 검증하고 어긋나면 **NULL** 을 돌려준다 → `lab_id = NULL` = false. **GUC 를 세팅하지 않은 접속은 아무 행도 보지 못한다.** v1 에서 물려받은 유일한 기법이다(`DATAMODEL-BASELINE §4`).

**정책의 *내용* 이 맞는지는 이 스키마가 증명하지 못한다.** 커버리지 게이트는 "정책이 있는가"까지만 본다(`D3-db.md §7-4`).
`㉖` 가 요구한 **음성/양성 테스트 2종**(허용자 아님·만료됨 → 본체 0행 / 잠긴 데이터셋 메타 → 반드시 조회됨)은 **아직 없다. P0 의 다음 조각이다.**

---

## 5. 게이트 실행 결과

| 게이트 | 결과 |
|---|---|
| `migration-single-head` | 🟢 **green** — 두 체인 각각 리비전 1건·head 1개 |
| `rls-coverage` | 🟢 **green** — 조사 21건. 면제 3건 외 전부 FORCE RLS + `lab_boundary`, `d3_file` 은 정책 2개 |
| `schema-diff` | 🟧 **체인별로는 green, 한 번의 실행으로는 red** — §7-①. 선언 = 적용을 **두 체인 모두 실측 확인**했다 |
| `db-selftest` | 🟢 green (38 케이스 유지) |
| `planning-freshness` · `contract-lint` · `boundary-selftest` · `contract-selftest` | 🟢 green — 깨지 않았다 |
| `ai-no-lineage-write` | 🟧 red 하나 남음 — **⑨⑩⑪⑫ 는 이번에 green 이 됐고**, 남은 것은 `⑧ ai-service 코드 0건`(P0 범위 밖) |

적용 DB 는 `alembic upgrade head --sql` 로 뽑아 일회용 컨테이너에 넣어 만들었다 — **포트를 하나도 공개하지 않았고**(도커 내부 IP 로만 접속) 끝나고 지웠다.
staging 두 컨테이너는 무변경, `https://www.colab-hydro.com/healthz` = **200**.

---

## 6. `rls-allowlist.toml` 에 한 일

**면제를 늘리지 않았다.** `allow_no_rls` 는 손대지 않았다(`alembic_version_*` 2건 · `d1_lab` 1건 그대로).

바꾼 것은 `body_tables` 한 줄 — `d7_viz_source` 를 **주석으로 내렸다.**
D7 시각화 저장 형태는 DataModel v1.8 범위 밖이고 P3 가 정한다. 테이블이 없는데 목록에 남으면 게이트가 「낡은 면제」로 red 를 낸다.
**지우지 않고 주석으로 남긴 이유**는 P3 가 테이블을 만들 때 되살릴 자리를 남기기 위해서다 — 지우면 그때 이 요구가 있었다는 사실이 사라진다.

---

## 7. 정본·게이트와 어긋난 것 · 못 정한 것

**추측으로 메우지 않았다.** 아래는 전부 다음 세션이 판단해야 할 것이다.

### ① ~~`schema-diff` 는 지금 구조로 green 이 될 수 없다~~ — **해소 (2026-08-23, 실측)**

> **이 항목은 더 이상 P0 의 열린 블로커가 아니다.** 게이트가 체인별 URL(`COLAB_APPLIED_DB_URL_PLATFORM`·`_AI`)을 받도록 고쳐졌고,
> 구 변수 `COLAB_APPLIED_DB_URL` 단독은 이제 **설정 오류로 red** 를 낸다 — 어느 체인의 DB 인지 알 수 없는 채로 검사 범위가 조용히 줄어드는 것을 막는다.
> **단일 실행에서 두 체인 모두 green 임을 실측으로 확인했다.** 증명 = `dev-package/reports/p0-schema-verify-20260823.md`.
> 아래 원문은 당시 판단의 기록으로 남긴다.

<details><summary>당시 기록</summary>


게이트는 `COLAB_APPLIED_DB_URL` **하나**를 받아 **두 체인 모두**와 비교한다. 체인이 둘이고 선언이 서로 다르므로
한 번의 실행에서 둘 다 green 이 되려면 두 `schema.sql` 이 같아야 한다 — 체인 분리(`§3-3`)와 정면으로 모순이다.
`D3-db.md §7-①` 이 이미 「배포 형태가 정해지는 WU 에서 정한다」로 기록해 둔 한계이고, **P0 에서 실물로 터졌다.**

실측으로는 **두 체인 모두 드리프트 0** 이다:

| 적용 DB | `db/platform` | `db/ai` |
|---|---|---|
| `colab_platform` (platform 체인 upgrade) | 🟢 green | red (비교 상대가 틀렸다) |
| `colab_ai` (ai 체인 upgrade) | red (비교 상대가 틀렸다) | 🟢 green |

**필요한 조치 = 게이트가 체인별 URL 을 받게 고치는 것**(`COLAB_APPLIED_DB_URL_PLATFORM` · `_AI`).
`gates/` 수정은 이 작업의 금지 범위라 **손대지 않았다.** 이것이 P0 의 열린 블로커다.

</details>

### ② 정본 §2 가 `연구실 이름`을 두 곳에 적는다

「연구실 = **이름**·개설일」과 「연구실 정보 = … 연구실을 정의하는 **유일한** 자리 … 여기 적은 **이름**을 전환기와 업로드 모달 헤더가 읽는다」가 같은 절에 있다.
**판단: `d1_lab.name` 한 곳에 뒀다.** 근거 — ⓐ 연구실 정보는 `d1_lab` 1:1 이라 어느 쪽에 두든 「유일한 자리」는 성립한다 ⓑ `d1_lab_profile` 은 테넌트 경계 안이고 `d1_lab` 은 경계 자신이라, 이름을 profile 에 두면 **연구실 목록·전환기가 RLS 에 걸린다** ⓒ `contracts/seams/fe-core.yaml` 의 `CurrentAccount.labName` 이 경계 판정 전에 필요한 값이다.
**정본이 두 곳에 적은 사실 자체는 남는다.** 기획이 한쪽으로 정리해 주는 것이 맞다.

### ③ 잠긴 데이터셋의 본체를 **소유자·교수**가 볼 수 있는지 정본이 말하지 않는다

정본 §4.1 은 잠김이면 「볼 수 있는 사람 목록」만 말한다. 소유자 예외·교수 예외·업로더 예외가 **어디에도 없다.**
`body_access` 정책은 **정본에 적힌 것만** 구현했다 — `열림`(데이터셋 값 또는 연구실 기본값) **또는** 만료되지 않은 허용 줄.
그 결과 **자기가 올린 데이터를 잠그면 소유자 본인도 DB 층에서 본체를 못 받는다.** 안전한 쪽(fail-closed)으로 닫았지만
**운영상 거의 확실히 틀린 형태다.** 값의 정본은 E-06(`Policy_승인_처리`)이고 **P6 전에 기획 확인이 필요하다.**

### ④ 접근 요청·Verified 요청 **큐**를 만들지 않았다

`fe-core.yaml` 은 `AccessRequest`(requestId·요청 사유·거절 사유)·`VerificationRequest` 를 이미 요구한다.
그러나 DataModel v1.8 §4.1 이 저장 형태로 적은 것은 **접근 상태·허용자 목록·Verified 기록**까지이고, 요청 큐는 E-06 규칙 본체다(P0.md §2 「승인 규칙 본체는 P6」).
**범위를 늘리지 않기 위해 만들지 않았다.** P6 이 `d2_access_request` 를 더한다. 그때까지 해당 엔드포인트는 구현할 저장 자리가 없다.

### ⑤ 「본체 1건 이상」은 DB 가 강제하지 못한다

행 제약으로 표현할 수 없다(마지막 본체 삭제를 막는 일은 행 하나의 성질이 아니다). 애플리케이션과 묘비 규칙의 몫으로 남겼다 — **DB 가 못 막는다는 사실을 여기 적어 둔다.**

### ⑥ §4.3 「합치는 규칙」 6항의 시행 위치

`d3_dataset_autometa` 는 규칙의 **결과**를 담는 자리일 뿐이다. 「모든 조각이 같아야 한다」를 누가 언제 검사하는가는 적재 경로(D5)의 일이고 **P2 가 정한다.**

### ⑦ `d4_lineage_edge.parent_dataset_id` 는 NOT NULL 인데 계약은 nullable 이다

`fe-core.yaml` 의 `LineageEdge.parentDatasetId` 는 「원천 표기가 부모 자리인 관계」를 위해 null 을 허용한다.
저장 쪽은 정본을 따랐다 — **원천은 데이터셋이 아니라 `d3_dataset.source_label` 표기**이고(§4.1), 그래프의 점선 노드는 그 값에서 **합성**한다. 관계 행을 만들지 않는다.
계약과 저장의 이 차이는 의도된 것이고, **응답 조립 시점에 합성한다**는 사실을 P1 이 알아야 한다.

### ⑧ 인덱스는 최소만 걸었다

경계 컬럼·FK·본체 정책이 쓰는 조회 경로까지다. 성능 인덱스는 `DATAMODEL-BASELINE §6` 대로 P1 이후다.
