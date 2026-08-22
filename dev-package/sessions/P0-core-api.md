# WU-P0 산출물 #4 — core-api 엔드포인트 골격 (레인 A1)

> 계약 정본 `contracts/seams/fe-core.yaml` 의 **34 오퍼레이션 전부**를 등록했다.
> 실질의 5 개만 DB 를 읽고, 나머지 29 개는 **501 + ErrorEnvelope** 다.
> 설계 판단은 `sessions/NIGHT-20260823.md §3` 이 이미 확정했다 — 이 세션은 그것을 코드로 옮겼다.
> `contracts/` · `gates/` · `db/` 는 **한 글자도 고치지 않았다.**

---

## ① 만든 것

| 경로 | 무엇 |
|---|---|
| `services/core-api/src/colab_core/kernel/ids.py` | **정규 ID `Ulid`** — 코드 쪽 유일한 정의 자리 (CLAUDE.md §3-6). 26자 Crockford Base32, 생성·검증 |
| `.../kernel/scope.py` | **스코프 커널** — 트랜잭션 스코프 `SET LOCAL`(=`set_config(...,true)`) 로 `app.current_lab`·`app.current_account` 주입 |
| `.../kernel/db.py` · `config.py` | 엔진·세션 팩토리 · 환경변수 설정 (접속 문자열 기본값을 코드에 두지 않는다) |
| `.../kernel/auth.py` | `sessionSubject` bearer → 주체. **`labId` 를 요청에서 받는 경로가 없다** |
| `.../kernel/errors.py` | `ErrorEnvelope` 한 형태 · 501 두 종 코드 |
| `.../ports/{lineage,access,project_link}.py` | cross-domain 인터페이스 3종. 구현은 소유 도메인, 조립은 `app` |
| `.../domains/d1_identity.py` | 연구실·계정 조회 (shared kernel) |
| `.../domains/d2_access.py` | 역할·권한 스위치 4종 · 접근 상태/Verified Port 구현 |
| `.../domains/d3_catalog.py` | 데이터셋·파일 조회 + **계보 상태·Lv 계산**(저장하지 않는다) |
| `.../domains/d4_lineage.py` | 주입력 부모 최대 Lv 재귀 집계 Port 구현 (읽기 전용) |
| `.../domains/d6_project.py` | 프로젝트 생성 · 데이터셋 연결 Port 구현 |
| `.../domains/d8_insight.py` | 자리만. 집계 3종은 P1 |
| `.../app/main.py` · `deps.py` · `routes/*.py` | 조립 루트. 34 라우트 등록 · 요청 경계 = 트랜잭션 경계 |
| `services/core-api/ops/app-role.sql` | **앱 DB 롤 부트스트랩** (NOBYPASSRLS · 비소유자). `db/` 에 두지 않은 이유는 ③ |
| `services/core-api/requirements{,.in,-dev,-dev.in}.txt` | 전이 의존까지 **전부 `==`**. `frontend/package-lock.json` 과 같은 역할 |
| `services/core-api/tests/` | 오라클 4벌 (②·③ 참조). **86 케이스 전부 green** |
| `services/{pipeline-worker,viz-render,ai-service}/src/` | 빈 패키지 자리. 이유는 ⑤-6 |

모듈 경로는 `sessions/D3-boundary.md §2` 관례 그대로다 — `app > domains > ports > kernel`.

## ② 34 오퍼레이션 처리 표

### 실질의 5 — DB 를 읽는다

| operationId | method · path | 읽는 것 | 이 5 개를 고른 이유 |
|---|---|---|---|
| `getCurrentAccount` | GET `/me` | D1 계정 + D2 역할·스위치 | 주체 → 경계 주입의 전 구간을 지난다 |
| `getLab` | GET `/lab` | D1 연구실·프로필 + 구성원 수 | 테넌트 루트 읽기 |
| `listDatasets` | GET `/datasets` | D3 + D2·D4·D6 (Port) | **읽기 · 자식 · 미스코프** 세 음성을 HTTP 층에서 덮는다 |
| `listDatasetFiles` | GET `/datasets/{datasetId}/files` | D3 파일 + D2 접근 | 두 번째 층(`body_access` RESTRICTIVE)의 실효 |
| `createProject` | POST `/projects` | D6 쓰기 | **쓰기 WITH CHECK** 를 덮는다 |

### 501 · `NOT_IMPLEMENTED_NO_STORE` — 7 건 (저장처 자체가 P0 스키마에 없다)

| operationId | method · path |
|---|---|
| `createAccessRequest` | POST `/datasets/{datasetId}/access-requests` |
| `listPendingAccessRequests` | GET `/access-requests/pending` |
| `approveAccessRequest` | POST `/access-requests/{requestId}/approval` |
| `rejectAccessRequest` | POST `/access-requests/{requestId}/rejection` |
| `requestVerification` | POST `/datasets/{datasetId}/verification-request` |
| `listPendingVerificationRequests` | GET `/verification-requests/pending` |
| `downloadDataset` | GET `/datasets/{datasetId}/download` |

접근 요청 4 · Verified 요청 2 는 **요청 큐 테이블이 없다**(`P0-schema.md §7-④` — P6 소관).
`downloadDataset` 은 302 의 목적지(스토리지 presigned URL)가 아직 정해지지 않았다 (⑤-3).

### 501 · `NOT_IMPLEMENTED_P1` — 22 건 (저장 자리는 있고 로직이 P1)

| operationId | method · path |
|---|---|
| `updateLab` | PATCH `/lab` |
| `listLabMembers` | GET `/lab/members` |
| `saveLabMemberPermissions` | PUT `/lab/members/permissions` |
| `listDatasetFacets` | GET `/datasets/facets` |
| `getDataset` | GET `/datasets/{datasetId}` |
| `deleteDataset` | DELETE `/datasets/{datasetId}` |
| `getDatasetDeletionImpact` | GET `/datasets/{datasetId}/deletion-impact` |
| `getDatasetLineage` | GET `/datasets/{datasetId}/lineage` |
| `addLineageParent` | POST `/datasets/{datasetId}/lineage/parents` |
| `removeLineageParent` | DELETE `/datasets/{datasetId}/lineage/parents/{parentDatasetId}` |
| `confirmLineage` | POST `/datasets/{datasetId}/lineage/confirmation` |
| `approveVerification` | POST `/datasets/{datasetId}/verification` |
| `cancelVerification` | POST `/datasets/{datasetId}/verification-cancellation` |
| `listProjects` | GET `/projects` |
| `getProject` | GET `/projects/{projectId}` |
| `updateProject` | PATCH `/projects/{projectId}` |
| `deleteProject` | DELETE `/projects/{projectId}` |
| `setProjectStatus` | PUT `/projects/{projectId}/status` |
| `unlinkProjectDataset` | DELETE `/projects/{projectId}/datasets/{datasetId}` |
| `getDashboardSummary` | GET `/dashboard/summary` |
| `getDataMap` | GET `/dashboard/data-map` |
| `listActivities` | GET `/dashboard/activities` |

**404 를 쓰지 않는다.** 404 는 「경계 밖」의 뜻으로 이미 예약돼 있다 (`PLAN-SoT §9-㊱`).
미구현이어도 **인증은 건다** — 인증 없이 501 을 내리면 경계 밖에서 오퍼레이션 목록을 읽게 된다.

### 오라클 두 벌

| 파일 | 무엇을 오라클로 삼나 |
|---|---|
| `tests/test_route_table.py` | 앱의 라우트 표를 `fe-core.yaml` 과 **diff** 한다. 사람이 34 를 세지 않는다. 경로·메서드가 한 글자만 달라도 red |
| `tests/test_not_implemented.py` | 29 개가 **각각 어떤 code 로** 501 을 내는지 고정. 나중에 누가 501 을 가짜 200 으로 바꾸면 red. 「404 를 쓰지 않는다」도 여기서 지킨다 |

## ③ 스코프 커널 · DB 롤이 무엇을 막는가

| 장치 | 막는 사고 | 증명 |
|---|---|---|
| **트랜잭션 스코프 `SET LOCAL`** | 풀 커넥션에 비-LOCAL `SET` 을 쓰면 커넥션이 풀로 돌아간 뒤 **다음 요청이 앞 요청의 lab_id 를 물려받는다.** 한 줄로 경계 전체가 무너지는 자리 | `test_scope_kernel.py::test_scope_makes_rows_visible_then_forgets_them` — 같은 `pg_backend_pid()` 를 다시 받아 2건 → **0건** 확인 |
| **GUC 미설정 = 기본 거부** | 스코프 주입을 빠뜨린 경로가 전부를 보는 것 | 같은 파일 `test_no_guc_sees_nothing` — `current_lab_id()` NULL, `d3_dataset` **0행** |
| **주체에서만 오는 경계** | `labId` 를 헤더·쿼리로 주입하는 임시 경로 | `test_live_endpoints.py::test_lab_id_cannot_be_injected` — `?labId=` 를 붙여도 자기 연구실만 보인다 |
| **정규 ID 검증 후 바인딩** | GUC 값에 문자열을 끼워 넣는 주입 | `test_scope_rejects_non_canonical_ids` |
| **앱 롤 NOBYPASSRLS** | BYPASSRLS 롤이면 정책이 통째로 무시되고 음성 테스트가 **거짓 green** 이 된다 | `test_app_role_is_nobypassrls_and_not_the_owner` |
| **앱 롤 = 비소유자** | 소유자는 `ENABLE` 만 된 RLS 를 건너뛴다. `schema.sql` 이 `FORCE` 까지 켜 뒀지만, 소유자와 접속 주체를 갈라 두면 그 실수의 여지 자체가 없다 | 같은 테스트 — `pg_tables.tableowner = current_user` 가 **0건** |
| **앱 롤에 DDL 없음** | 앱이 스키마를 바꾸는 경로 | `ops/app-role.sql` 이 `CREATE` 권한을 회수한다 |

### 롤 부트스트랩을 `db/` 에 두지 않은 이유

`db/platform` 은 **선언 스키마 ↔ 적용 DB 의 일치**를 증명하는 체인이다(`schema-diff` 게이트).
롤·GRANT 는 데이터베이스가 아니라 **클러스터** 단위 객체라 그 diff 의 대상이 아니고,
거기 넣으면 배포 환경 값(비밀번호)이 스키마 정본에 섞인다.
`infra/` 가 아니라 `services/core-api/ops/` 인 이유는 이 롤이 **이 배포 단위 하나의 접속 주체**라서다 —
배포 단위가 늘면 롤도 그 단위 옆에 하나씩 선다.

### 인증

계약이 이미 답했다 — `sessionSubject` bearer, 「개발자가 계정을 심어 제공한다」(P-17), 실제 수단은 P1.
그래서 **로그인 흐름을 만들지 않았고**, 심어 둔 토큰 표(`COLAB_CORE_SUBJECTS_FILE`)를 읽기만 한다.
DB 에서 주체를 조회하지 않는 이유는 구조적이다 — `d1_account` 는 RLS 아래에 있어서
**경계를 알기 전에는 계정을 읽을 수 없다.** 그 순환을 깨려면 BYPASSRLS 롤이나 `SECURITY DEFINER`
함수가 필요한데, 둘 다 방금 막은 것을 다시 여는 일이다.

## ④ 게이트 실행 결과

| 게이트 | 이 세션 전 | 지금 | 비고 |
|---|---|---|---|
| `import-boundary` | 🔴 red (패키지 0건) | 🟢 **green** | 45 파일 · 50 의존 · 계약 **8/8 KEPT** |
| `banned-import` | 🔴 red (`.py` 0건) | 🟢 **green** | core-api 27 · ai 6 · pipeline 6 · viz 6 = 45건, 금지 import 0 |
| `ai-no-lineage-write` | 🔴 red (⑧ 코드 0건) | 🟢 **green** | L1 계약 · L2 코드 · L3 체인 세 층 전부 |
| `boundary-selftest` | 🟢 green | 🟢 green | 30 케이스 그대로 |
| `contract-lint` | 🟢 green | 🟢 green | seam 3건 · 위반 0 |
| `contract-selftest` | 🟢 green | 🟢 green | fail-closed 증명 유지 |

**red 3 개가 green 으로 돌아선 것이 그 게이트들의 인수 시험이었다** (`D3-boundary.md §7`).
게이트는 한 줄도 고치지 않았다.

테스트: `pytest` **86 passed** (라우트 표 diff · 501 표 · Ulid · 실엔드포인트 · 스코프 커널).
DB 는 포트를 하나도 열지 않은 일회용 postgres(`a1_pg`, unix 소켓 바인드)로 붙였고 **작업 뒤 삭제**했다.
staging 컨테이너 둘은 건드리지 않았다.

## ⑤ 정본·계약과 어긋난 것 · 못 정한 것

추측으로 메우지 않았다. 전부 나열한다.

1. **[계약 ↔ 스키마 어긋남] 잠긴 데이터셋의 `fileCount` 를 낼 자리가 없다.**
   `DatasetRow.fileCount` 는 `minimum: 1` 인데, 조각 수의 유일한 출처인 `d3_file` 은
   `body_access` RESTRICTIVE 정책이 막아 잠긴 데이터셋에서 **0 행**이 된다.
   지금은 보이는 만큼(0)을 그대로 내린다 — 1 을 지어내지 않았다.
   해소는 둘 중 하나다: ⓐ `d3_dataset_autometa` 에 조각 수 컬럼 추가(스키마 개정), ⓑ D3 이 본체
   정책 밖에서 세는 Port. **`db/` 를 고쳐야 하므로 이 세션에서 멈췄다.**

2. **[정본 무근거] 계보 상태 4값의 판정 순서.**
   정본이 준 것은 「`마지막 수정 > 계보 확정일` 이면 `확인 필요`」 하나뿐이다
   (`DATAMODEL-BASELINE §3-③`). `원천` 과 `기록 없음` 을 가르는 규칙은 정본에 없다.
   레포 판단으로 「부모 0 + 원천 표기 있음 → `원천`, 그 밖 → `기록 없음`」을 썼고
   `d3_catalog.lineage_state()` 주석에 적었다. **정본 확인이 필요하다.**

3. **[미정] `downloadDataset` 302 의 목적지.**
   presigned URL 인지 프록시인지 정본에 없다. 스토리지 인프라 결정이라 501 로 두었다.

4. **[관례 이탈] `app.py` 가 아니라 `app/` 패키지다.**
   `D3-boundary.md §2` 는 `app.py` 로 적었으나, 34 라우트를 한 모듈에 넣으면 그것이 곧 God Object 다
   (`P0.md §6` 의 첫 함정). `app/main.py` · `app/deps.py` · `app/routes/*` 로 쪼갰고
   `colab_core.app` 이라는 층 이름은 그대로여서 `import-boundary` 계약은 변하지 않는다.

5. **[한계] 카탈로그 조건·정렬을 메모리에서 건다.**
   `processingLevel` · `lineageState` 는 파생값이고 `verified` 는 D2 소유라 SQL 한 방으로 거르면
   도메인 경계를 넘게 된다. 지금은 연구실 전체를 조립한 뒤 걸고 세므로 `totalCount` 는 정확하지만
   데이터가 커지면 못 버틴다. **P1 이 Port 에 조건을 내려보내는 형태로 바꾼다.**
   커서도 같은 이유로 offset 기반 불투명 토큰이다.

6. **[범위 밖이나 필요했음] `pipeline-worker` · `viz-render` · `ai-service` 의 빈 패키지.**
   `importlinter.ini` 의 `root_packages` 가 네 패키지를 전부 요구하고, `ai-no-lineage-write` ⑧ 은
   ai-service 코드 0건을 red 로 본다. core-api 만 놓으면 게이트 셋이 계속 red 라
   **자리만** 만들었다(각 파일은 docstring 한 줄). 로직은 P2·P3·K 트랙 것이다.

7. **[남은 흔적] `/tmp/a1_sock`** — 일회용 postgres 의 소켓 디렉터리가 uid 70 소유로 남아 지워지지 않는다.
   레포 밖이고 비어 있다. 재부팅 시 사라진다.

8. **[다음이 이어받을 것]** A2 의 cross-tenant 음성 4종은 이 커널 위에서 돈다 —
   `tests/test_scope_kernel.py` 와 `tests/test_live_endpoints.py` 가 그 진입점이고,
   DB 붙이는 방법(`ops/app-role.sql` + 시드)은 `services/core-api/README.md` 에 적었다.
