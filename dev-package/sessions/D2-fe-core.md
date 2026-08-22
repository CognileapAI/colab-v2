# WU-D2 세션 기록 — ② seam `FE ↔ core-api` 동결

> **범위** `contracts/seams/fe-core.yaml` 한 파일. 다른 seam(`core-viz`·`core-ai`)·이벤트·`contracts/schemas/` 는 이 조각에 없다.
> **근거 규칙** `DOMAINS §4`(core-api = D1 D2 D3 D4 D6 D8) · `CLAUDE.md §3-2·§3-5·§3-6` · `PLAN-SoT §9-⑳` · `PERMISSION-PRINCIPLES` P-9·P-12·P-13·P-25·P-26·P-31·P-34.
> **검증** `python3 -c "import yaml; yaml.safe_load(...)"` green · `npx @redocly/cli@1 lint` → **valid**(warning 2건: license 없음 · 다운로드가 302 뿐) · `bundle --dereferenced` 로 `common.json` `$ref` 21종 실제 해석 확인.
> **규모** path 29 · operation **34**.

---

## 1. 엔드포인트 목록과 정본 근거

### D1 Identity & Lab

| operationId | 메서드 · 경로 | 정본 근거 |
|---|---|---|
| `getCurrentAccount` | `GET /me` | `IA_사이트맵 §3`(GNB 아바타 — 현재 사용자·역할·계정) · P-6(판정은 스위치 기준) |
| `getLab` | `GET /lab` | `Policy_홈_대시보드 §5·§8`(연구실 정보 읽기 모달 8항목) · `DataModel §2` |
| `updateLab` | `PATCH /lab` | `DataModel §2`(고치는 화면 = `연구실 설정 > 연구실 정보`) · P-2 행동표 |

### D2 Access & Policy

| operationId | 메서드 · 경로 | 정본 근거 |
|---|---|---|
| `listLabMembers` | `GET /lab/members` | P-18(스위치를 고치는 유일한 자리) · **P-31 재위임 금지** → `editablePermissions` |
| `saveLabMemberPermissions` | `PUT /lab/members/permissions` | P-19(실시간 저장 아님 · 확인 모달 1회 = 요청 1회) · P-33(스위치 1개 = 이력 1줄) |
| `createAccessRequest` | `POST /datasets/{id}/access-requests` | `Policy_승인_처리 §5`(요청 사유 0~300 선택) · P-13 |
| `listPendingAccessRequests` | `GET /access-requests/pending` | `Policy_승인_처리 §8`(홈 할 일 함 · 받은 접근 요청) · `Policy_홈_대시보드 §8`(오래된 순) |
| `approveAccessRequest` | `POST /access-requests/{id}/approval` | P-25(데이터 1건 · 승인일+6개월) · `§7.2` |
| `rejectAccessRequest` | `POST /access-requests/{id}/rejection` | P-26(사유 1~300 **필수**, 그대로 전달) |
| `requestVerification` | `POST /datasets/{id}/verification-request` | `Policy_승인_처리 §1.2·§7.1`(올린 사람·소유자가 헤더에서 직접) |
| `listPendingVerificationRequests` | `GET /verification-requests/pending` | `§8`(교수 전용 그룹 · 링크만) · P-5·P-22(위임 불가) |
| `approveVerification` | `POST /datasets/{id}/verification` | `§7.1`(교수가 **상세에서** 승인) |
| `cancelVerification` | `POST /datasets/{id}/verification-cancellation` | P-28 · `§5`(취소 사유 0~120 선택) · `§7.1`(막지 않는다) |

### D3 Catalog

| operationId | 메서드 · 경로 | 정본 근거 |
|---|---|---|
| `listDatasets` | `GET /datasets` | `Policy_데이터_찾기 §5`(8열 · 조건 5열 · 기본 정렬 수정일 최신순) · `§8` |
| `listDatasetFacets` | `GET /datasets/facets` | `§5 값별 건수`(다른 열 조건을 먼저 적용한 뒤 센다) · `§8 열 메뉴` |
| `getDataset` | `GET /datasets/{id}` | `Policy_데이터셋_상세 §5`(기본 정보 9칸) · `§7`(상태) · `Policy_승인_처리 §8` |
| `listDatasetFiles` | `GET /datasets/{id}/files` | `DataModel §4.3` · `Policy_데이터셋_상세 §5`(`보기` 누를 때만 목록) |
| `downloadDataset` | `GET /datasets/{id}/download` | `Policy_데이터셋_상세 §2·§8`(원본 그대로 · 묶음은 한 번에 · 이력 기록) |
| `getDatasetDeletionImpact` | `GET /datasets/{id}/deletion-impact` | `Policy_데이터셋_상세 §8·§9`(확인 모달이 말할 파급 3종) |
| `deleteDataset` | `DELETE /datasets/{id}` | `DataModel §4.1`(묘비) · `Policy_데이터셋_상세 §6`(소유자 또는 교수) |

### D4 Lineage

| operationId | 메서드 · 경로 | 정본 근거 |
|---|---|---|
| `getDatasetLineage` | `GET /datasets/{id}/lineage` | `Policy_데이터셋_상세 §8`(그래프 축 · 상세 행 · 원천/묘비/잠긴 노드) · `DataModel §4.2` |
| `addLineageParent` | `POST /datasets/{id}/lineage/parents` | `Policy_데이터셋_상세 §8`(계보 수정·추가 → **직접 연결로 저장**) |
| `removeLineageParent` | `DELETE …/parents/{parentDatasetId}` | 같은 행(수정) · `Policy_프로젝트`식 "연결만 끊는다" 원리 |
| `confirmLineage` | `POST /datasets/{id}/lineage/confirmation` | `Policy_데이터셋_상세 §2`(계보 다시 확인 → 확정일 갱신 · 표시 사라짐) |

### D6 Project

| operationId | 메서드 · 경로 | 정본 근거 |
|---|---|---|
| `listProjects` | `GET /projects` | `Policy_프로젝트 §5`(필터 2종 · 정렬 4값 · 기본값) · `§8`(툴바 한 벌) |
| `createProject` | `POST /projects` | `§5`(필수 = 유형·이름) · `§6`(`프로젝트 생성` 스위치) |
| `getProject` | `GET /projects/{id}` | `§2·§5`(개요 · 연결 주소 · 소속 데이터셋 **전부**) |
| `updateProject` | `PATCH /projects/{id}` | `§2`(유형은 고치지 않는다) |
| `setProjectStatus` | `PUT /projects/{id}/status` | `§7`(닫기·다시 열기 전이 표) |
| `deleteProject` | `DELETE /projects/{id}` | `§1.3-6`(데이터셋 0건일 때만 · 아니면 버튼이 사라진다 → 409) |
| `unlinkProjectDataset` | `DELETE /projects/{id}/datasets/{datasetId}` | `§7`(소속 해제 = 연결만 끊는다) |

### D8 Insight

| operationId | 메서드 · 경로 | 정본 근거 |
|---|---|---|
| `getDashboardSummary` | `GET /dashboard/summary` | `Policy_홈_대시보드 §5`(요약 지표 4개 · 계보 확정 = 확정+원천 · 퍼센트 금지) |
| `getDataMap` | `GET /dashboard/data-map` | `§5`(계보 상태별·주제별 두 묶음) · `§9`(집계 실패 → 503) |
| `listActivities` | `GET /dashboard/activities` | `DataModel §6.1`(바꾼 일만 · **열람은 서버에 없다**) · `§5 최근 활동 항목` |

---

## 2. 판단한 것 (정본이 직접 값을 주지 않았고, 근거를 대고 정한 것)

1. **잠김을 403 이 아니라 200 + `bodyAccessible: false` 로 표현했다.**
   403 으로 접으면 목록·상세에서 이름·요약이 사라져 `P-13`이 깨지고 **접근 요청 흐름 자체가 죽는다**.
   반대로 연구실 경계 밖은 **404** 다 — 경계는 존재를 알리지 않는다(P-9·P-10). 두 축을 한 메커니즘으로 합치지 않는다(P-14).
   `DatasetRow`·`DatasetDetail`·`ProjectDatasetRow`·`LineageNode` 네 곳이 같은 필드 이름을 쓴다.
2. **권한 판정을 서버가 응답에 실어 준다** (`DatasetDetail.actions` · `ProjectDetail.canManage` · `LineageGraph.canEdit` · `LabMember.editablePermissions`).
   근거는 P-7(화면이 조건을 임의로 정하지 않는다)·P-8(같은 사람·같은 기능은 모든 화면에서 같은 결과). 화면이 역할로 다시 계산하면 P-6 위반이 화면마다 재발한다.
3. **P-31(재위임 금지)을 `editablePermissions` 배열로 표현했다.** 열을 지우지 않고 "값은 보이되 편집 불가"를 그릴 수 있어야 하므로 `permissions`(값)와 `editablePermissions`(편집 가부)를 분리했다. 서버는 범위 밖 변경을 403 으로 막는다(P-11).
4. **`labId` 를 어떤 요청에도 두지 않았다.** 대신 `securitySchemes.sessionSubject` 를 두어 "모든 오퍼레이션이 주체를 요구한다"를 계약으로 못 박았다. 자격증명 발급 방식은 정본에 없다(P-17, P1 보류) — `bearer` 표기는 레포 결정이며 P1 에서 정한다.
5. **목록 봉투는 전부 `ListEnvelope` + `allOf` 로 items 타입만 좁혔다.** `additionalProperties: false` 를 우회하지 않는 유일한 확장 방식이다.
6. **프로젝트 목록의 "숨은 닫힘 N건"은 봉투 필드로 만들지 않았다.** 같은 조건에 `status=닫힘` 만 바꿔 부른 `totalCount` 로 읽는다 — `ListEnvelope` 를 깨지 않기 위해서다.
7. **다운로드를 core 경유(302)로 뒀다.** 다운로드 이력이 D8 소유이고 본체 접근이 RLS 로 막히는 층이라(P-34), 프런트가 스토리지를 직접 부르면 두 규칙이 동시에 샌다. `2XX` 가 없다는 린트 warning 은 의도한 것이다.
8. **`계보 확인` 할 일 함 그룹에 전용 엔드포인트를 만들지 않았다.** `GET /datasets?lineageState=확인 필요&lineageState=기록 없음` 이 같은 목록이고, 홈의 `계보 확인 필요 전체 보기`도 같은 곳으로 간다(`Policy_홈_대시보드 §8`). 엔드포인트를 하나 더 만들면 같은 판정이 두 곳에 생긴다.
9. **파생값 2종은 응답에만 있다.** `ProcessingLevel`·`LineageState` 는 어떤 요청 바디에도 없다. 다만 **카탈로그 조건**으로는 쿼리 파라미터에 실린다 — 정본이 Level·계보를 조건 열로 지정했기 때문이다(`Policy_데이터_찾기 §5`). 쓰기와 조건은 다른 축이다.
10. **seam 안에서 새로 연 enum 은 5개뿐이고 전부 화면 어휘다** — `CatalogColumn`(열 이름) · `SortOrder`(오름/내림) · `ProjectSort`(정렬 4값) · `LineageNode.kind`(원천/가공 전/이 데이터/파생/묘비) · `Activity.target.kind`. 값은 전부 정본 표기 그대로이며, **`common.json` 의 값 집합을 다시 선언한 곳은 하나도 없다**(bundle 로 확인).
11. **다른 seam 으로 보낸 것** — 자연어 검색(S-06)·AI 근거·탐색 범위는 `core-ai`(D10), 미리보기·겹쳐 보기·스크린샷은 `core-viz`(D7, `CLAUDE.md §3-4`), 업로드와 **프로젝트 연결 생성**은 D5/E-04(`Policy_프로젝트 §1.3-9` — "담는 것은 업로드 화면이 맡는다"). 프런트가 직접 부른다.

---

## 3. 정본에 근거가 없어 **빼고 올리는 것**

| # | 항목 | 상태 | 어디서 닫히나 |
|---|---|---|---|
| 1 | **접근 요청 상태 enum**(`검토 대기 / 승인됨 / 거절됨 / 만료됨`) | `Policy_승인_처리 §7.2` 에 값이 있으나 **`common.json` 에 정의가 없다.** seam 이 인라인 선언하면 `CLAUDE.md §3-6` 위반이라, 상태를 노출하지 않는 형태(`/access-requests/pending` + `DatasetDetail.accessRequestPending`)로 화면 요구만 덮었다 | `common.json` 보강 (D2 후속 조각) — 다만 회수(§10-①)·재요청(§10-②) 미결이 닫히기 전에는 값 집합이 확정되지 않는다 |
| 2 | **활동 종류 enum** | `DataModel §6.1` 은 "올림·계보 고침·승인·프로젝트 만듦·지움"을 **예시로** 열거할 뿐 값 집합으로 닫지 않았다. `Activity.action` 을 문자열로 뒀다 | 기획 확인 후 `common.json` |
| 3 | **가공 방식 어휘** | `LineageEdge.method`·`LineageParentCreate.method` 를 자유 문자열로 뒀다. `sessions/D2.md §3-①` 과 같은 이유 — HYD 협의 사항 | HYD 협의 → 별도 WU |
| 4 | **페이지 크기 파라미터** | 정본이 값을 주지 않는다. `cursor` 만 노출하고 크기는 서버가 정한다 | 화면 실측(P1·P4) |
| 5 | **접근 승인 조기 회수 · 거절 후 재요청** | `PERMISSION-PRINCIPLES §10-①②` 미결. 회수 엔드포인트·재요청 제한을 만들지 않았다 | 기획 · P6 |
| 6 | **다중 연구실 소속 · 연구실 전환기** | `§10-⑤` 미정. `/me` 는 단일 `labId` 다. 전환 엔드포인트를 만들지 않았다 | P1 |
| 7 | **소유자 승계** | `§10-⑥` — v2 에 화면·API 없음. `PATCH` 로 소유자를 바꾸는 경로를 만들지 않았다 | P1 |
| 8 | **활용 의미 문장 편집** | 연결마다 문장이 따로라는 것만 정본에 있고, **고치는 화면이 어디인지 정본에 없다.** 읽기(`usageNote`)만 뒀다 | 기획 · P5 |
| 9 | **Verified 취소 파급 조회 전용 엔드포인트** | 파급 3종(정렬 하락·활용 프로젝트·파생 건수)이 전부 상세 화면에 이미 있는 값이라 만들지 않았다. 삭제 파급만 별도 엔드포인트인 이유는 **대기 중인 접근 요청 건수**가 상세에 없는 값이기 때문 | — (판단, 근거는 §2) |
| 10 | **조각 요약의 `간격`** | `DataModel §4.3` 이 요약 한 줄에 `간격`을 넣었으나 **저장 형태에 그 필드가 없다**(`DATAMODEL-BASELINE` D3 표). 파일 응답에 넣지 않았다 | 기획 · P1 |
| 11 | **파일별 용량** | 정본은 용량을 데이터셋 단위 **합계**로만 말한다. `DatasetFile` 에 크기를 두지 않았다 | 필요해지면 기획 |
| 12 | **알림·통지** | "요청자에게 통지"가 정본에 있으나 수단은 `[가정] 제품 안 통지`(`Policy_승인_처리 §10`). 통지 엔드포인트를 만들지 않았다 | 기획 |

---

## 4. 다음 조각의 진입조건

- **계약 게이트가 검사해야 하는 것 2가지** — ① seam 안에 `common.json` 값 집합의 재선언이 없는가(지금은 사람 눈으로만 확인했다) ② 쓰기 바디에 `LineageState`·`ProcessingLevel` 이 없는가(`PLAN-SoT §9-⑳`). 게이트 규칙은 아직 없다.
- `codegen/` 은 이 파일과 `common.json` 을 함께 물어야 한다 — 외부 `$ref` 가 걸려 있어 seam 단독으로는 해석되지 않는다.
- 위 §3-①(접근 요청 상태 enum)이 닫히기 전에는 **요청자 쪽 상태 화면**을 구현할 수 없다. P6 진입 전에 해소해야 한다.
