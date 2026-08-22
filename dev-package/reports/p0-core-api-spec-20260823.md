# P0 — core-api 엔드포인트 골격 빌드 스펙

> 대상: `dev-package/sessions/P0.md §4` 산출물 #4. `services/core-api/`는 현재 README뿐.
> 이 문서는 실행 계획이 아니라 **작성에 필요한 사실 취합**이다. 결정이 필요한 항목은 ⑥에 모았다.

---

## ① 계약 오퍼레이션 표 (`contracts/seams/fe-core.yaml`, 전체 27 op)

D1 8 · D2(access) 8 · D3(catalog) 6 · D4(lineage) 3 · D6(project) 6 · D8(insight) 3 — 태그 합은 access(2·5·1=8이 아니라 D2 8), 아래 표가 정본.

| 도메인 | operationId | method/path | 요청/응답 스키마 | P0 백킹 |
|---|---|---|---|---|
| D1 | getCurrentAccount | GET /me | → CurrentAccount | ✅ `d1_account` |
| D1 | getLab | GET /lab | → Lab | ✅ `d1_lab`+`d1_lab_profile` |
| D1 | updateLab | PATCH /lab | LabUpdate → Lab | ✅ 동일 |
| D2 | listLabMembers | GET /lab/members | → ListEnvelope\<LabMember\> | ✅ `d1_account`+`d2_member_role`+`d2_permission_switch` |
| D2 | saveLabMemberPermissions | PUT /lab/members/permissions | PermissionSaveRequest → ListEnvelope\<LabMember\> | ✅ `d2_permission_switch`+`d2_permission_change`(append-only 이력) |
| D3 | listDatasets | GET /datasets | params → ListEnvelope\<DatasetRow\> | ✅ `d3_dataset`+`d3_dataset_description`+`d3_dataset_autometa`+파생 계보상태(D4 조회) |
| D3 | listDatasetFacets | GET /datasets/facets | params → FacetSet | ✅ 동일 소스 집계 |
| D3 | getDataset | GET /datasets/{id} | → DatasetDetail | ✅ 위 3테이블 + D4 요약 + D6 활용 프로젝트 조회(Port) |
| D3 | deleteDataset | DELETE /datasets/{id} | → 204 | ✅ 묘비(`deleted_at`) — 단 §7-⑤ 「본체 1건 이상」 제약은 DB가 못 막음, 앱 로직 필요 |
| D3 | getDatasetDeletionImpact | GET /datasets/{id}/deletion-impact | → DeletionImpact | 🟧 파생 N·Verified는 가능. **대기 중 접근 요청 건수는 큐 테이블이 없어 불가**(§7-④) |
| D3 | listDatasetFiles | GET /datasets/{id}/files | → ListEnvelope\<DatasetFile\> | ✅ `d3_file` |
| D3 | downloadDataset | GET /datasets/{id}/download | → 302 | ✅ 302 자체는 골격으로 가능. 실제 스토리지 리다이렉트 대상(presigned URL 등)은 별도 인프라 결정 필요(⑥) — 다운로드 이력은 `d8_download`에 적재 |
| D4 | getDatasetLineage | GET /datasets/{id}/lineage | → LineageGraph | ✅ `d4_lineage_edge`+`d4_lineage_unknown`. **원천(점선) 노드는 저장 안 되고 `d3_dataset.source_label`에서 응답 조립 시 합성**(§7-⑦, 계약 nullable ↔ 저장 NOT NULL 차이 의도됨) |
| D4 | addLineageParent | POST /datasets/{id}/lineage/parents | LineageParentCreate → LineageGraph | ✅ `d4_lineage_edge` insert, `confirmed_by/at` NOT NULL이 "사람이 직접 연결"을 강제 |
| D4 | removeLineageParent | DELETE /datasets/{id}/lineage/parents/{parentDatasetId} | → LineageGraph(추정, 확인 필요) | ✅ `d4_lineage_edge` delete |
| D2 | confirmLineage(주의: yaml상 tag는 lineage) | POST /datasets/{id}/lineage/confirmation | → ? | ✅ 계보 확정일 갱신(`d3_dataset.lineage_confirmed_at`) |
| D2 | createAccessRequest | POST /datasets/{id}/access-requests | → AccessRequest | ⛔ **저장처 없음.** `d2_access_request` 큐가 없다(P0-schema.md §7-④, P6이 추가) |
| D2 | listPendingAccessRequests | GET /access-requests/pending | → ListEnvelope\<AccessRequest\> | ⛔ 동일 |
| D2 | approveAccessRequest | POST /access-requests/{id}/approval | → AccessRequest | ⛔ 동일. 승인 결과는 `d2_dataset_access_grant`에 쓸 수 있으나 요청 자체가 없어 요청→승인 흐름 불가 |
| D2 | rejectAccessRequest | POST /access-requests/{id}/rejection | → AccessRequest | ⛔ 동일 |
| D2 | requestVerification | POST /datasets/{id}/verification-request | → VerificationRequest | ⛔ 큐 없음. 결과 저장처(`d2_verified`)는 있으나 "요청" 자체가 저장되지 않음 |
| D2 | listPendingVerificationRequests | GET /verification-requests/pending | → ListEnvelope\<VerificationRequest\> | ⛔ 동일 |
| D2 | approveVerification | POST /datasets/{id}/verification | → Dataset(추정) | ✅ `d2_verified` insert (요청 큐 없이 직접 승인도 가능하다면 — 확인 필요, ⑥) |
| D2 | cancelVerification | POST /datasets/{id}/verification-cancellation | → ? | ✅ `d2_verified`의 cancelled_by/at/reason |
| D6 | listProjects | GET /projects | → ListEnvelope\<Project\> | ✅ `d6_project` |
| D6 | createProject | POST /projects | ProjectCreate → Project | ✅ 동일 |
| D6 | getProject | GET /projects/{id} | → ProjectDetail | ✅ `d6_project`+`d6_project_dataset` |
| D6 | updateProject | PATCH /projects/{id} | → Project | ✅ |
| D6 | deleteProject | DELETE /projects/{id} | → 204 | ✅ |
| D6 | setProjectStatus | PUT /projects/{id}/status | → Project | ✅ (project 상태 컬럼 존재 가정 — schema.sql 확인 필요, ⑥) |
| D6 | unlinkProjectDataset | DELETE /projects/{id}/datasets/{datasetId} | → 204 | ✅ `d6_project_dataset` delete |
| D8 | getDashboardSummary | GET /dashboard/summary | → DashboardSummary | ✅ `d8_activity`+`d3_dataset`+`d6_project` 집계 |
| D8 | getDataMap | GET /dashboard/data-map | → DataMap | 🟧 자료 있음이나 P0.md §2 "비워 둘 자리"에 해당할 가능성 — 정본 확인 필요(⑥) |
| D8 | listActivities | GET /dashboard/activities | → ListEnvelope\<Activity\> | ✅ `d8_activity` |

**요약: 27 op 중 저장 자리 없어 백킹 불가 — 6건, 전부 D2(access-request 4 + verification-request 2), 이유는 접근/검증 요청 큐가 P6 소관.**
D8 getDataMap 1건은 스키마상 백킹 가능해 보이나 "비워 둘 자리 3곳" 정본 확인 필요.

---

## ② 모듈 경로 · import 경계 (`dev-package/sessions/D3-boundary.md §2`, `gates/config/importlinter.ini`)

강제 경로 관례:
```
services/core-api/src/colab_core/
    __init__.py
    app.py                  # 조립 루트
    domains/d1_identity/ d2_access/ d3_catalog/ d4_lineage/ d6_project/ d8_insight/
    ports/                  # cross-domain 인터페이스만, 구현 없음
    kernel/                 # 스코프 커널·세션·설정
```

import-linter 계약 7개 (`gates/config/importlinter.ini`) 중 core-api에 적용되는 것:

| 계약 | 유형 | 금지 |
|---|---|---|
| units-independent | independence | colab_core가 colab_pipeline/colab_viz/colab_ai를 import |
| core-layers | layers | app > domains > ports > kernel 역전 (ports가 domains를 참조 등) |
| core-domains-independent | independence | d2_access·d3_catalog·d4_lineage·d6_project·d8_insight 상호 직접 import (D1 제외) |
| d1-knows-nobody | forbidden | d1_identity가 d2/d3/d4/d6/d8/app을 import |

→ D6(getDataset이 D4 요약과 D6 활용 프로젝트를 함께 내려야 함), D3(getDataset이 D4 계보 요약 참조), D8(대시보드가 D3/D6/D1 집계 참조) 등 **교차 조회는 반드시 `colab_core.ports`의 인터페이스를 거쳐야 하며, 도메인 모듈이 서로 직접 import하면 즉시 red.** 골격 단계부터 Port 계층을 최소 1개 이상 실제로 파야 함(빈 domains만 만들면 layers 계약이 애초에 실패 — D3-boundary.md §8-②).

`gates/config/boundaries.toml`의 core-api deny 18종(rasterio·osgeo·gdal·xarray·pyproj·shapely·fiona·geopandas·rioxarray·netCDF4·h5py·cfgrib·eccodes·pygrib·cartopy·rio_cogeo·matplotlib·affine) — core-api 코드에 이 중 하나라도 import되면 red. downloadDataset 302 리다이렉트 구현 시 파일 포맷 라이브러리를 core-api에 끌어들이지 않도록 주의(스토리지 서명 URL만 다루고 실제 파일 열기는 pipeline-worker/viz-render 몫).

---

## ③ DB 접속 · 스코프 커널 요구 (`db/platform/env.py`, `db/README.md`, `P0-schema.md §4`)

- 접속 URL은 **환경변수 `COLAB_PLATFORM_DB_URL`로만** 주입, 파일에 하드코딩 금지 (`db/platform/env.py` 주석).
- `db/ai`(D9·D10)와 마이그레이션 체인 완전 분리 — core-api는 `db/platform`만 본다.
- 스코프 커널: 매 요청마다 PostgreSQL GUC `app.current_lab`(및 `app.current_account`)를 세팅해야 한다. `current_lab_id()` 함수가 이 GUC를 Crockford base32(ULID) 정규식으로 검증하고, 형식이 틀리거나 미설정이면 **NULL을 반환** → 모든 RLS 정책의 `lab_id = current_lab_id()`가 거짓이 되어 **기본 거부(deny-by-default)**. 즉 core-api 요청 파이프라인(미들웨어)이 인증 주체에서 lab_id를 뽑아 `SET app.current_lab = ...`를 커넥션마다 실행하지 않으면 전 테이블이 빈 결과를 반환한다.
- 정규 ID 타입은 `contracts/schemas/common.json`에서만 정의(ULID/Crockford base32, char(26)) — core-api가 재정의하지 않는다.

---

## ④ 스택 확정 여부 — **확정됨**

`PLAN-SoT.md §9-㊳`(2026-08-23, Claude 판단·Ted 비토 가능):
- 백엔드: **Python 3.12 + FastAPI + SQLAlchemy 2.x + Alembic**
- 프런트: TypeScript + React + Vite (core-api 골격과 직접 관련 없음)

근거: 계약이 OpenAPI 3.1이라 FastAPI의 스펙 우선 운용이 맞고, `banned-import` 게이트가 배포 단위별 geo 라이브러리 차단을 파이썬 AST 기준으로 전제하며, D3 게이트(import-linter·alembic `down_revision`·`colab_core` 패키지 관례)가 이미 파이썬을 정본으로 못 박아 두었음. 버전 핀은 이 결정 항목에만 있고 `requirements.txt`류의 실제 버전 고정 파일은 아직 core-api에 없음(⑥).

---

## ⑤ P0 §5 완료 판정 중 이 조각(엔드포인트 골격)의 몫

| # | 판정 | 이 산출물(#4)의 몫 |
|---|---|---|
| 1 | 스키마 diff 게이트 | 아니오 — D3b(스키마/마이그레이션) 몫, 이미 P0-schema.md에서 처리 |
| 2 | 마이그레이션 single-head | 아니오 — 동일 |
| 3 | import 경계 계약 | **예** — 엔드포인트 골격이 `colab_core.domains.*` 구조로 실제 코드를 놓아야 `import-boundary` 게이트가 대상 0건 red에서 벗어남 |
| 4 | cross-tenant 음성 테스트 | 부분 — 골격이 스코프 커널(GUC 세팅)을 실제로 호출해야 이 테스트가 의미 있는 대상을 가짐. 테스트 자체는 D3b/커널 몫 |
| 5 | RLS 커버리지 게이트 | 아니오 — DB 쪽 몫 |
| 6 | DataModel v1.8 항목 대조 | 아니오 — 스키마 몫 |
| 7 | FE 셸 | 아니오 — 별도 산출물(#5) |
| 8 | staging 배포(I2 이후) | 간접 — core-api가 기동 가능한 앱이어야 헬스체크가 성립 |

**즉 엔드포인트 골격의 직접 판정 기준은 #3(import 경계)이고, #4는 골격이 스코프 커널을 실제로 물려야 성립한다.** 나머지는 D3b 산출물의 몫.

---

## ⑥ 정본이 값을 주지 않아 결정이 필요한 것

1. **access-request / verification-request 6개 엔드포인트를 골격 단계에서 어떻게 표현할지.** 저장처가 없으므로 (a) 라우트 자체를 P6까지 미구현 상태로 비워두고 스텁만 둘지, (b) 501/기능 미구현 응답을 명시적으로 낼지 결정 필요. `CLAUDE.md §5` "나중에로 남기지 않는다"와 P0.md §2 "승인 규칙 본체는 P6"이 충돌하는 지점 — 골격이 "라우트는 존재하되 저장 로직 없음"으로 명시되면 두 원칙을 다 지킬 수 있는지 확인 필요.
2. **downloadDataset의 302 대상 — presigned URL 발급자가 core-api인지, 별도 스토리지 게이트웨이인지** 정본에 없음. core-api geo/스토리지 라이브러리 금지 규칙과 충돌하지 않는 구현 방식 결정 필요.
3. **approveVerification이 요청 큐 없이 직접 승인 가능한 것인지** — verification-request 큐가 없는데 승인 엔드포인트(approveVerification)는 백킹 가능(`d2_verified` insert)으로 분류했음. "요청 없는 승인"이 정책상 허용되는지 E-06 정본 확인 필요.
4. **getDataMap이 "비워 둘 자리 3곳"(P0.md §2 — Verified 배지·잠금 표시·할 일 함) 중 하나에 해당하는지**, 아니면 D8 실데이터로 채워야 하는지 불명.
5. **removeLineageParent·confirmLineage·approveVerification·cancelVerification의 정확한 응답 스키마명** — fe-core.yaml 발췌에서 response schema $ref를 직접 확인하지 못했음(원문 400줄 이후 절단). 골격 작성 전 전체 yaml 재확인 필요.
6. **FastAPI/SQLAlchemy/Alembic의 구체 버전 핀 파일이 아직 core-api에 없음** — `PLAN-SoT §9-㊳`는 스택만 확정했고 `requirements.txt`/`pyproject.toml` 고정은 이번 WU 산출물에 포함되는지 불명.
