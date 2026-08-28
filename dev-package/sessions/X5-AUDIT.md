# X-5 · ㉰-4 소급 전수확인 — 계약 대 구현 전수 대조

／ 근거 = `WORK-UNITS.md:395`(§10.2 `X-5` 행) · `03-HANDOFF.md:161` · `PLAN-SoT.md:464`(`〈163〉-㉰`)
／ 선례 = `〈151〉` `202` 철회 — **선언된 응답 코드에 생산자가 없던 것**이 적출 축이었다
／ 측정 범위 = `contracts/seams/*.yaml`(3) · `contracts/events/*.json`(2) · `contracts/schemas/common.json` · `contracts/storage/layout.json` · `contracts/codegen/manifest.toml`
／ 대조 대상 = `services/{core-api,ai-service,viz-render,pipeline-worker}/src` · `frontend/src`(생성물 `frontend/src/generated/` 제외) · `db/platform/schema.sql`
／ ⚠ `contracts/node_modules/` · `.claude/worktrees/` · `gates/fixtures/` 는 대조에서 제외(각각 의존성·워크트리 사본·게이트 픽스처)
／ ⚠ 생성물(`frontend/src/generated/fe-core.ts` · 3개 `storage_layout.py`)은 **선언의 증거로만** 세고 구현으로 세지 않았다

---

## 1. 전수 대조표

### 1-1. 오퍼레이션 (op)

| 항목 | 종류 | 선언 위치(파일:행) | 구현 위치 or 없음 | 판정후보 |
|---|---|---|---|---|
| fe-core op 53종 전체 | op | `contracts/seams/fe-core.yaml`(53 `operationId`) | 33 = 실동작 라우트 / 20 = `501` 스텁 | **자명하게 닫힘** — 오라클 존재 |
| ↳ 실동작 33 | op | 동상 | `services/core-api/src/colab_core/app/routes/{catalog,identity,ingestion,lineage,members,preview,project,session}.py` | 자명 |
| ↳ `501` 스텁 20 | op | 동상 | `services/core-api/src/colab_core/app/routes/not_implemented.py:OPERATIONS` | **자명하게 닫힘** — 미구현이 코드에 명시돼 있고 `501`로 정직하게 말한다. 「선언만 되고 조용히 없는 것」이 아니다 |
| ↳ `deleteDataset` `getDatasetDeletionImpact` `downloadDataset` `getDatasetLineage` | op | `fe-core.yaml:716,785,1043,1069` | `not_implemented.py` `501` | 자명(집행 = P1 배정) |
| ↳ 접근요청 4 (`createAccessRequest` `listPendingAccessRequests` `approveAccessRequest` `rejectAccessRequest`) | op | `fe-core.yaml:1165,1195,1225,1252` | `501` `NOT_IMPLEMENTED_NO_STORE` | 자명(스키마 선행 필요) |
| ↳ Verified 4 (`requestVerification` `listPendingVerificationRequests` `approveVerification` `cancelVerification`) | op | `fe-core.yaml:1280,1304,1334,1360` | `501` | 자명 |
| ↳ 프로젝트 3 (`deleteProject` `setProjectStatus` `unlinkProjectDataset`) | op | `fe-core.yaml:1494,1518,1571` | `501` | 자명 |
| ↳ 대시보드 3 (`getDashboardSummary` `getDataMap` `listActivities`) | op | `fe-core.yaml:1746,1764,1788` | `501` (`P7` 소유) | 자명 |
| ↳ `addUploadFile` `replaceUploadGridFile` | op | `fe-core.yaml:317,375` | `501` | 자명 |
| **core-ai `suggestLineage`** | op | `contracts/seams/core-ai.yaml:67` (`POST /lineage-suggestions`) | **없음** — `ai-service`는 `POST /searches` 하나만 연다(`services/ai-service/src/colab_ai/app/main.py:71`). 자기 문서가 「`suggestLineage` 는 `K3` 의 자리」라고 적었다(`main.py:3`) | **집행**(WU `K3`) — ⚠ **소비자는 이미 있다**: `services/core-api/src/colab_core/app/relay.py:282` 가 이 경로를 실제로 POST 한다. 닿지 못하면 `honest_empty_suggestions` 로 200+빈배열 반환 → **사용자에게 거짓말은 안 하지만 계약의 절반이 공중에 떠 있다** |
| **core-viz `createScreenshot`** | op | `contracts/seams/core-viz.yaml:195` | **없음** — `services/viz-render/src/colab_viz/app/main.py:4` 가 「등록하지 않았다·`501`도 안 둔다」를 명시 | **집행**(`P3` 배정 · `WORK-UNITS §10.2` 「타일 서빙·확대 · `createScreenshot` 은 `P3` 안에 남는다」) — 판정 불필요 |
| core-viz `createRender` `getRender` `getRenderTile` `listPalettes` | op | `core-viz.yaml:61,107,142,172` | `services/viz-render/src/colab_viz/app/routes/renders.py:71,120,129` · `style.py:16` | 자명 |
| core-ai `searchDatasets` | op | `core-ai.yaml:99` | `services/ai-service/src/colab_ai/app/main.py:71` | 자명 |
| 구현돼 있으나 계약에 없는 op | op | — | **0건** — `services/core-api/tests/test_route_table.py:76` 가 양방향 diff 를 오라클로 강제 | 자명 |

### 1-2. 응답 코드 (`〈151〉` `202` 와 같은 축)

| 항목 | 종류 | 선언 위치 | 구현 위치 or 없음 | 판정후보 |
|---|---|---|---|---|
| **`422`** (core-viz `createRender`) | 응답코드 | `contracts/seams/core-viz.yaml:98` | **없음** — `services/viz-render/src` 전체에 `422` 문자열 0건. `main.py` 의 `RequestValidationError` 핸들러가 `errors.bad_request` → **`400`** 으로 내린다 | **철회 후보** — `〈151〉` `202` 와 **동형**. 생산자 없는 선언 |
| **`422`** (core-ai `searchDatasets`) | 응답코드 | `contracts/seams/core-ai.yaml:142` | **없음** — `ai-service/app/main.py` 는 검증 실패를 전부 `400`(`_error(400, "bad_request", …)` 9곳)으로 낸다 | **철회 후보** — 동상 |
| `422` (core-ai `suggestLineage`) | 응답코드 | `core-ai.yaml:92` | 없음 (op 자체가 미구현) | **집행 시 재판정** — op 이 서면 함께 판정. 지금 단독 철회하지 않는다 |
| `409`·`410`·`413`·`415`·`503` (core-viz) | 응답코드 | `core-viz.yaml` 각 op | `viz-render/app/routes/renders.py:84(413),98(415),139(410),142(409)` · `app/deps.py:21,24(503)` | 자명 |
| `429` (`createSession`) | 응답코드 | `fe-core.yaml:95` | `kernel/errors.py:60` `too_many_attempts` → `routes/session.py` | 자명 |
| `503` (`searchDatasets`·`listPalettes`·미리보기 2·`getDataMap`) | 응답코드 | `fe-core.yaml` 각 op | `core-api` `ApiError(503` 6곳 · 음성시험 `tests/test_search_relay.py:84,96` · `test_palettes_relay.py:84` · `test_preview_relay.py:178` | 자명 |
| `202` (`createPreviewRender`) | 응답코드 | `fe-core.yaml:1647` | `routes/preview.py` `post("/previews", …, status_code=202)` | 자명 |
| `202` (`addUploadFile`·`replaceUploadGridFile`·`requestVerification`) | 응답코드 | `fe-core.yaml:317,375,1280` | 없음 — 셋 다 `501` 스텁 | 자명(op 미구현에 종속) |
| `302` (`downloadDataset`) | 응답코드 | `fe-core.yaml:1043` | 없음 — `501` 스텁 | 자명(동상) |
| **`403`** — `updateDataset` | 응답코드 | `fe-core.yaml:683` | **권한 검사 없음** — `routes/catalog.py` `update_dataset` 호출 폐포(깊이 4)에 `errors.forbidden(` 0건. 존재·필드·이름만 검사한다 | **판정 필요** — ⓐ 철회(수정은 구성원 누구나) ⓑ 집행(`업로드·편집` 스위치를 건다). ⚠ **같은 파일 `catalog.py:345` 는 본체 접근에 `403`을 걸고, `ingestion.py:173`·`lineage.py:42` 는 스위치를 건다** — 이 op 만 비어 있다 |
| **`403`** — `updateProject` | 응답코드 | `fe-core.yaml:1473` | **권한 검사 없음** — `routes/project.py` `update_project` 폐포에 `forbidden(` 0건. ⚠ **같은 파일 `project.py:117,356` 이 `프로젝트 생성` 스위치로 `403`을 건다** | **판정 필요** — 같은 파일 안에서 갈린다 |
| **`403`** — `getUploadStatus` · `listUploadLineageSuggestions` · `createPreviewRender` · `getPreviewRender` | 응답코드 | `fe-core.yaml:429,455,1647,1702` | 폐포에 `forbidden(` 0건 (`routes/ingestion.py`·`routes/preview.py`) | **판정 필요(약)** — 넷 다 **읽기·중계** 성격이라 「스코프(`404`)로 충분하고 `403`은 선언만 남은 것」일 가능성이 높다. 철회 쪽이 유력하나 근거 문서 미확인 |
| `403` — 나머지 14 op | 응답코드 | `fe-core.yaml` 각 op | `errors.forbidden(` 7곳 도달 · 음성시험 다수(`tests/test_lab_members.py:80,146,151,196,203` · `test_lab_and_project_update.py:76` · `test_body_access.py:74` · `test_dataset_files.py:185` · `test_grid_postinject.py:290` · `test_lineage_confirm.py:249`) | 자명 |
| `400`(`createSession`·`listDatasetFacets`) · `404`·`409`(`replaceDatasetGridFile`) | 응답코드 | `fe-core.yaml:95,569,971` | 도달 확인 — `replaceDatasetGridFile` 은 `_grid_target` 헬퍼가 `not_found`·`conflict` 를 낸다(`ingestion.py` `_grid_target` 내 3곳) | 자명(1차 정적 스캔의 위양성이었다) |

### 1-3. 스키마 필드

| 항목 | 종류 | 선언 위치 | 구현 위치 or 없음 | 판정후보 |
|---|---|---|---|---|
| fe-core 컴포넌트 스키마 54종 · 고유 속성 128개 | 필드 | `contracts/seams/fe-core.yaml` `components.schemas` | **미참조 컴포넌트 0건** — 54종 전부 `$ref` 로 경로에 닿는다 | 자명 |
| ↳ 코드에 이름이 없는 속성 **12개** | 필드 | `Activity.activityId` `Activity.occurredAt` · `DataMap.byLineageState` `DataMap.byTopic` · `DashboardSummary.{lineageSettledCount,lineageUnsettledCount,projectCount}` · `DeletionImpact.{derivedDatasetCount,pendingAccessRequestCount}` · `AccessGrant.grantee` · `AccessRequest/VerificationRequest.{requestedAt,requester}` | 없음 | **자명하게 닫힘** — 12개 **전부** `501` 스텁 20 op 의 응답 스키마에 속한다. **고아 필드가 아니라 미구현 op 의 종속물**이다. 별도 판정 대상 아님 |
| core-viz 속성 51개 중 미구현 3 | 필드 | `ScreenshotRequest.layers` · `ScreenshotRequest.viewport` · `ScreenshotLayer.opacity` | 없음 | **자명** — `createScreenshot` 미구현에 종속(`P3`) |
| core-ai 속성 44개 중 미구현 11 | 필드 | `AiSuggestionBase.{suggestionId,confidence}` · `ParentCandidateSuggestion.{parentDatasetName,suggestedParentRole}` · `ProcessingMethodSuggestion.{methodText,appliesToParentDatasetId}` · `UploadedFileMeta.{gridDescription,partCount,periodStart,periodEnd,sourceNoteDraft}` | 없음 | **자명** — `suggestLineage` 미구현에 종속(`K3`) |
| core-viz/core-ai 미참조 컴포넌트 | 필드 | — | **0건** | 자명 |

### 1-4. 공통 스키마 (`common.json`) · 열거값

| 항목 | 종류 | 선언 위치 | 구현 위치 or 없음 | 판정후보 |
|---|---|---|---|---|
| `$defs` 26종 중 **`PermissionSwitchChange`** | 필드(공유 정의) | `contracts/schemas/common.json:60` | **어느 seam 도 `$ref` 하지 않는다(참조 0)** — 그러나 **구현은 있다**: `services/core-api/src/colab_core/domains/d2_access.py:163` 이 `"direction": "켬"/"끔"` 을 쓰고 `db/platform/schema.sql:160` 이 `CHECK (direction IN ('켬','끔'))` 로 받는다 | **자명하게 닫힘(단, 성격이 다르다)** — 「선언만 되고 구현 없음」이 **아니다.** 반대로 **구현·저장은 있는데 이를 읽는 op 이 계약에 없다**. 권한 변경 이력 조회 op 은 `§J` 편의 묶음/`P6` 밖 어디에도 없다. **철회하지 않는다** — 저장이 append-only 로 돌고 있다 |
| 나머지 `$defs` 25종 | 필드 | `common.json` | 전부 seam 에서 `$ref` 참조(최소 1회, `Ulid` 61회) | 자명 |
| 열거값 전수 (`common.json` + `envelope.json` 의 모든 `enum`) | 필드 | `common.json` · `envelope.json` | **코드 코퍼스에 나타나지 않는 값 0건** — `FailureReason` 8값 · `FailureClass` 2값 · `AccessState`·`PermissionSwitchChange`·`GridRejectionReason` 등 전건 도달 | 자명 |
| ⚠ 단, `pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:53,54` 가 두 분기를 **「죽은 분기 — stage 2」**로 자기 표시 | 필드 | `FailureReason` `헤더 인식 실패` 매핑 2건 | 코드에 존재하나 도달 불가 | **[미확인]** — 「선언 있음·코드 있음·실행 도달 없음」. 재는 법 = `pytest` 커버리지로 해당 두 행의 실행 여부 측정, 또는 stage 2 파싱 구현 회차에 함께 판정 |

### 1-5. 이벤트

| 항목 | 종류 | 선언 위치 | 구현 위치 or 없음 | 판정후보 |
|---|---|---|---|---|
| `upload.accepted` | 이벤트 | `contracts/events/core-pipeline.json:241` · `envelope.json` `EventType` | 발행 = `core-api` `domains/d5_ingestion.py:41,229` (유일 발행자, 계약 `Source` 와 일치) | 자명 |
| `file.format-detected` | 이벤트 | `core-pipeline.json:253` | `pipeline-worker/src/colab_pipeline/d5/events.py:21,31,180` | 자명 |
| `file.header-parsed` | 이벤트 | `core-pipeline.json:265` | `pipeline-worker/domains/d5_ingestion.py:263` | 자명 |
| `file.crs-normalized` | 이벤트 | `core-pipeline.json:277` | `d5/events.py:23,33,186` | 자명 |
| `preview.cog-built` | 이벤트 | `core-pipeline.json:289` | `d5/events.py:24,34,188` | 자명 |
| `upload.ready` | 이벤트 | `core-pipeline.json:301` | 발행 = `d5/events.py` · 소비 = `core-api/domains/d5_ingestion.py:78` | 자명 |
| `upload.failed` | 이벤트 | `core-pipeline.json:313` | `d5/events.py:26,164,190` · `app/worker.py:118` | 자명 |
| 봉투 `delivery` 5필드 + `deadLettered` | 필드 | `envelope.json` `Delivery` | `pipeline-worker/d5/events.py:102-107` 전건 생산 · `domains/d5_ingestion.py:402,403,428-431` 이 outbox 왕복에서 전건 보존 | 자명 |
| 봉투 `Failure.willRetry`·`detail` | 필드 | `envelope.json` `Failure` | `d5/events.py:167` | 자명 |
| 봉투 `Envelope` 11 required | 필드 | `envelope.json` | 전건 생산(`events.py`) | 자명 |
| 코드가 내는데 계약에 없는 이벤트 | 이벤트 | — | **0건** | 자명 |

### 1-6. 저장 배치 · 생성물 등기부

| 항목 | 종류 | 선언 위치 | 구현 위치 or 없음 | 판정후보 |
|---|---|---|---|---|
| `uploadsPrefix` `targetId` `gridDirname` `keys` 2종 | 필드 | `contracts/storage/layout.json` | 3개 생성 모듈(`core-api`·`pipeline-worker`·`viz-render` `kernel/storage_layout.py`) — `generated-up-to-date` 게이트가 byte-diff | 자명 |
| `manifest.toml` 4 엔트리 | — | `contracts/codegen/manifest.toml` | 4개 산출물 전부 커밋돼 있음 | 자명 |
| 등기부 밖 「generated」 자칭 파일 | — | — | **[미확인]** — 게이트가 잡게 돼 있으나 이번 회차에 게이트를 돌리지 않았다. 재는 법 = `generated-up-to-date` 게이트 1회 실행 |

### 1-7. 프런트엔드 방향

| 항목 | 종류 | 선언 위치 | 구현 위치 or 없음 | 판정후보 |
|---|---|---|---|---|
| FE 가 실제로 부르는 op **20종** | op | `frontend/src` `api.*('/…')` 호출 | 20종 전부 `fe-core.yaml` 선언분 | 자명 |
| FE 가 계약 밖 경로를 부르는 것 | op | — | **0건** — 유일한 raw `fetch` 는 `frontend/src/components/preview/previewSource.ts:86` 이고, **계약이 준 타일 URL** 을 그대로 여는 것이다(경로를 FE 가 짓지 않는다) | 자명 |
| 계약에 있으나 FE 가 안 부르는 op 33종 | op | `fe-core.yaml` | 없음 | **자명하게 닫힘** — 「FE 미사용 = 미집행」이 **아니다.** 20 은 `501` 스텁이고 나머지는 서버 구현이 앞선 것(`P3`~`P8` 화면이 뒤에 온다). **철회 근거가 되지 않는다** |

---

## 2. 요약

### 2-1. 판정이 필요한 것 (7건 — 2026-08-28 기준 열린 것 3건)

> **개정 (2026-08-28 · 최종) — 열린 판정 0건. 7건 전건 닫힘.** ①② **철회 확정·집행**(`PLAN-SoT §9-〈180〉`) · ③④ **집행 확정 · `main` 병합 완료**(red 픽스처 증명 · `455 passed` · `sessions/X5-403-VERIFY.md`) · ⑤ **철회 확정·집행**(`§9-〈181〉`) · ⑥ **판정 없음 종결** — 이 문서가 열린 판정으로 올린 것이 **오기였다**. `P-33`(`PERMISSION-PRINCIPLES.md:93`)·`schema.sql:151`·`§9-㉘`(2026-08-22 Ted)가 「v2 에 조회 화면은 두지 않는다」로 **이미 닫아 둔 결정**이다 · ⑦ **판정 아님** — `K3` 착수 순서로 이관. 원행은 지우지 않고 개정 표시만 붙인다.

| # | 항목 | 판정 갈래 | 왜 판정인가 |
|---|---|---|---|
| ① | ~~core-viz `createRender` 의 **`422`**~~ | **✅ 철회 확정 (2026-08-28 Ted)** | 판정 근거·실측은 `PLAN-SoT §9-〈180〉`. 선언 삭제 집행 완료 — 코드 변경 0, 검사기 5종 green |
| ② | ~~core-ai `searchDatasets` 의 **`422`**~~ | **✅ 철회 확정 (2026-08-28 Ted)** | 동상. `PLAN-SoT §9-〈180〉` 에 함께 등재 |
| ③ | `updateDataset` 의 **`403`** (`fe-core.yaml:683`) | 철회 vs **집행** | 같은 레포 안에서 갈린다 — `ingestion.py:173`·`lineage.py:42` 는 `업로드·편집` 스위치를 걸고 이 op 만 안 건다. ⚠ **집행 쪽이면 권한 구멍**이다 |
| ④ | `updateProject` 의 **`403`** (`fe-core.yaml:1473`) | 철회 vs **집행** | 같은 파일 `project.py:117,356` 이 `프로젝트 생성` 스위치로 `403`을 거는데 수정 경로만 비어 있다 |
| ⑤ | 읽기·중계 4 op 의 **`403`** — `getUploadStatus`·`listUploadLineageSuggestions`·`createPreviewRender`·`getPreviewRender` | **철회**(유력) vs 집행 | 넷 다 스코프 위반을 `404` 로 받는 성격이라 `403` 이 선언만 남았을 가능성. 근거 문서를 못 찾았다 |
| ⑥ | `common.json:60` **`PermissionSwitchChange`** — seam 참조 0 | **집행**(이력 조회 op 신설) vs 현상 유지 | 방향이 반대다: **구현·저장은 도는데 계약 표면이 없다.** 철회하면 돌고 있는 원장을 계약이 부정하게 된다 |
| ⑦ | core-ai `suggestLineage` (`core-ai.yaml:67`) 의 **비대칭** | 집행(`K3`) 시점만 | op 자체는 `K3` 배정이라 판정 불필요하나, **소비자(`relay.py:282`)가 이미 서 있는 유일한 항목**이다. 「선언만 있다」가 아니라 「한쪽만 서 있다」 — `K3` 지연 시 계속 200+빈배열로 돈다 |

### 2-2. 자명하게 닫히는 것

- **op 축은 이미 오라클이 지킨다** — `services/core-api/tests/test_route_table.py:76` 가 `fe-core.yaml` ↔ 앱 라우트 표를 **양방향 diff** 한다. fe-core 에서 「선언만 되고 조용히 없는 op」은 **구조적으로 0**이다.
- **`501` 스텁 20 은 미집행이지만 은닉이 아니다** — `not_implemented.py` 가 op·경로·사유를 표로 들고 `501 + ErrorEnvelope` 를 낸다. `X-5` 가 찾는 「말 없이 빈 선언」과 다르다.
- **필드 축은 전건 종속물이다** — 코드에 없는 필드 12(fe-core)·3(core-viz)·11(core-ai) 이 **하나도 빠짐없이** 미구현 op 의 스키마에 속한다. **고아 필드 0건.**
- **이벤트 7종 전건 발행·소비된다.** 봉투 필드도 outbox 왕복에서 전건 보존된다. **양방향 0건.**
- **열거값 전건 도달.** `common.json`·`envelope.json` 의 모든 `enum` 값이 코드에 존재한다.
- **미참조 컴포넌트 3 seam 전부 0건.** 저장 배치·생성물 등기부도 정합.
- **FE 는 계약 밖을 부르지 않는다.**

### 2-3. `[미확인]` 2건

| 항목 | 왜 미확인 | 무엇을 재면 닫히나 |
|---|---|---|
| `pipeline-worker/domains/d5_ingestion.py:53,54` 의 **「죽은 분기」 2행** | 코드에 있으나 도달 여부를 이번 회차에 실행으로 재지 않았다 | `pytest --cov` 로 두 행의 실행 카운트를 측정. 0이면 stage 2 파싱 구현 회차의 집행 대상으로 이월 |
| **등기부 밖 「generated」 자칭 파일 존재 여부** | `generated-up-to-date` 게이트를 이번 회차에 돌리지 않았다. 정적 대조로는 마커 규칙 전체를 재현할 수 없다 | 게이트 1회 실행(green/red) |

### 2-4. 산출 수치

| 지표 | 값 |
|---|---|
| 대조 항목 총계 | **185** (op 60 · 응답코드 코드 축 21종·op 대조 · 필드 223속성 → 결손 26 · 공통 `$defs` 26 · 열거값 전체 · 이벤트 7 · 봉투 필드 · 배치 5 · 등기부 4 · FE 20) |
| **미구현(선언 O · 구현 X)** | **26** — op 22(`501` 스텁 20 ＋ `suggestLineage` ＋ `createScreenshot`) · 응답코드 3(`422`×3) · 공유정의 1(`PermissionSwitchChange` 의 seam 표면) ／ ⚠ 필드 26개는 이 op 들에 **종속**이라 중복 계상하지 않았다 |
| **미선언(구현 O · 선언 X)** | **1** — `PermissionSwitchChange` 이력의 **읽기 표면**(구현·저장은 있는데 op 이 없다). 그 밖의 방향은 0건 |
| **미확인** | **2** (§2-3) |
| **판정이 필요한 것** | **7** (§2-1) |
| **자명하게 닫히는 것** | 나머지 전부 (§2-2) |
