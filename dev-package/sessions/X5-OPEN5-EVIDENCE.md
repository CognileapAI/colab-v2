# X-5 잔여 판정 5건 — 실물 근거 (계약 대 구현 재확인)

／ 작성 2026-08-28 · **읽기 전용 조사** — 편집·커밋·컨테이너 접촉 없음
／ 기준 리비전 = `main` `72e90cc` (워킹트리 clean 가정 · git 상태는 조회만)
／ 근거 원문 = `dev-package/sessions/X5-AUDIT.md` (⚠ 지시문의 `dev-package/X5-AUDIT.md` 경로는 실재하지 않는다 — `sessions/` 아래다)
／ 방법 = 계약 파일 직접 판독 ＋ `services/*/src`·`frontend/src`(생성물 제외)·`db/platform/schema.sql`·`gates/` grep 전수

---

## 0. 「5건」의 정체 — 감사 문서는 7건을 적었다

`X5-AUDIT.md §2-1` 은 판정 대상을 **7건**(①~⑦)으로 적는다. 그중 **③ `updateDataset` 403 · ④ `updateProject` 403** 은
이미 판정·집행됐다 — 브랜치 `x5-403-enforce` `ab06bec` 「계약이 선언한 403 을 updateDataset·updateProject 가 실제로 낸다」.

- 실물 확인 = `git diff main origin/x5-403-enforce --stat` → `routes/catalog.py` +6 · `routes/project.py` +6 · `tests/test_dataset_update.py`·`test_lab_and_project_update.py` 각 ±20
- **⚠ 감사 이후 갱신된 `03-HANDOFF.md` 산문이 이 브랜치를 「미푸시·미병합」으로 적는데, 절반이 낡았다** — `origin/x5-403-enforce` 가 실재하므로 **푸시는 됐고 병합만 안 됐다**
- **⚠ 그리고 `main` 에는 아직 그 6+6 줄이 없다** — `main` 의 `routes/catalog.py`·`project.py` 갱신 경로에 `errors.forbidden(` 0건(현재 `forbidden(` 도달점은 `catalog.py:345` · `ingestion.py:173` · `lineage.py:42` · `members.py:47,123` · `project.py:117,356` 뿐)

따라서 **열린 5건 = ① ② ⑤ ⑥ ⑦** 이다. 아래는 그 5건만 다룬다.

---

## ① core-viz `createRender` 의 `422`

**정체** — `POST /renders`(`operationId: createRender`)가 「본문이 문법상 맞으나 의미상 처리 불가」를 뜻하는 `422` 를 응답 목록에 선언한 것.

| 축 | 실물 |
|---|---|
| 선언 | `contracts/seams/core-viz.yaml:98` — `"422": { $ref: "#/components/responses/Error" }` (같은 op 이 `400`·`404`·`413`·`415`·`401`·`503` 도 선언) |
| 구현 | **0건.** `services/viz-render/src` 전체에 문자열 `422` **0회**(전 서비스·frontend 전체로 넓혀도 `422` 0회) |
| 실제 동작 | `services/viz-render/src/colab_viz/app/main.py:50-53` — `@app.exception_handler(RequestValidationError)` 가 `errors.bad_request(...)` 를 돌려준다 → **`400`** |
| 생산자 | 0 |
| 소비자 | 0. `core-api` 중계(`app/relay.py`)에 422 분기 없음 · `frontend/src` 에 422 분기 없음 |

**철회하면 깨지는 것** — 없음.
- 계약 게이트 `contract-lint`(spectral) 는 `colab-operation-has-error-response` 를 `anyOf`(`400`·`401`·`403`·`404`·`409`·`422`·`500`·`503`) 로 요구한다(`contracts/.spectral.yaml:47-64`). `400` 이 남으므로 green 유지.
- 생성물 영향 없음 — `contracts/codegen/manifest.toml` 의 4 엔트리 중 seam 기반은 `fe-core.yaml → frontend/src/generated/fe-core.ts` 하나뿐이고 `core-viz.yaml` 은 코드젠 입력이 아니다.
- `[미확인]` — `contract-breaking` 게이트(oasdiff, `--fail-on ERR`, `gates/tools/contract-breaking.sh:82-84`). 비성공 응답 코드 제거가 oasdiff 에서 ERR 인지 WARN 인지 이번 회차에 실행으로 재지 않았다. **재는 법 = 제거 후 `gates/run.sh contract-breaking` 1회.** WARN 이면 green.

**집행하면 드는 일** — `viz-render` 의 검증을 두 층으로 가른다(문법 오류 = `400`, 의미 불가 = `422`). `main.py` 핸들러 분기 ＋ `d7` 판정 경로 수정 ＋ 음성시험. 그리고 **중계 층까지 번진다** — `core-api` `routes/preview.py` 가 422 를 FE 로 어떻게 옮길지 정해야 하고, `fe-core.yaml#createPreviewRender` 에는 `422` 가 선언돼 있지 않아 계약 개정이 추가된다.

---

## ② core-ai `searchDatasets` 의 `422`

**정체** — `POST /searches`(`operationId: searchDatasets`)의 `422` 선언.

| 축 | 실물 |
|---|---|
| 선언 | `contracts/seams/core-ai.yaml:142` |
| 구현 | **0건.** `services/ai-service/src` 에 `422` 0회 |
| 실제 동작 | `services/ai-service/src/colab_ai/app/main.py` — 검증 실패를 전부 `_error(400, "bad_request", …)` 로 낸다. 실측 **9곳**(`main.py:76,78,82,85,90,97,106,109` ＋ `def _error` `:36`) |
| 생산자 | 0 |
| 소비자 | 0. `core-api` `relay.py` 는 `status != 200` 이면 코드를 가리지 않고 접는다 |

**철회하면 깨지는 것** — 없음. ① 과 동일한 논리(`400` 이 남아 spectral green · 코드젠 무관). `contract-breaking` 의 ERR/WARN 은 ① 과 같은 `[미확인]`.

**집행하면 드는 일** — `ai-service` 의 400 9곳을 「문법 대 의미」로 재분류. ⚠ 다만 `core-ai.yaml:130-140` 산문이 「이 표면이 하는 일은 해석 하나다」라고 못 박아 두었고, 실패 축이 사실상 「본문 파싱 실패 · 경계 불일치 · 길이 초과」뿐이라 **422 로 갈 자연스러운 갈래가 코드에 없다.**

> ⚠ **감사 문서와 실물이 어긋나는 곳 없음** — ①② 는 문서 주장 그대로다. 선례(`〈151〉` `202` 철회 = 생산자 없는 선언은 철회)와 **동형**임도 실물로 확인된다.

---

## ⑤ 읽기·중계 4 op 의 `403` — `getUploadStatus` · `listUploadLineageSuggestions` · `createPreviewRender` · `getPreviewRender`

**정체** — 네 op 이 「권한이 없다」의 `403` 을 선언하는데, 핸들러 어디서도 권한 스위치를 보지 않는다.

| op | 선언 | 핸들러 | 실제 경계 판정 |
|---|---|---|---|
| `getUploadStatus` | `fe-core.yaml:429`(op)·`:442`(403) (`GET /uploads/{uploadId}`) | `services/core-api/src/colab_core/app/routes/ingestion.py:290` | `_live_upload()` 가 없으면 **404** — 주석이 「없는 업로드 · **경계 밖** · 수명이 다한 것을 **같은 404** 로 낸다」고 명시(`ingestion.py:299-301`) |
| `listUploadLineageSuggestions` | `fe-core.yaml:455`(op)·`:484`(403) (`GET /uploads/{uploadId}/lineage-suggestions`) | `ingestion.py:319` | 동일하게 **404** (`ingestion.py:337`). 그 뒤는 중계만 |
| `createPreviewRender` | `fe-core.yaml:1647`(op)·`:1678`(403) (`POST /previews`) | `routes/preview.py:74` | `_target_in_lab()` 실패 시 **404** 「그릴 대상이 없거나 연구실 경계 밖이다」(`preview.py:91`) |
| `getPreviewRender` | `fe-core.yaml:1702`(op)·`:1722`(403) (`GET /previews/{renderId}`) | `preview.py:108` | 중계 결과 `None` 이면 **404** (`preview.py:125`) |

- **`forbidden(` 도달 0건** — 네 핸들러의 호출 폐포에 없다. 위 §0 의 `forbidden(` 전수 7곳 목록에 이 경로들이 없다.
- **경계는 RLS 가 먼저 건다** — 네 핸들러 모두 `Depends(scoped_db)` 를 쓴다.
- **소비자 0** — `frontend/src`(생성물 제외)에서 403 을 분기하는 곳은 3곳뿐이고 **전부 이 4 op 과 무관**하다: `components/members/MemberPermissionGrid.tsx:101`(권한 저장) · `routes/LabSettingsPage.tsx:3`(주석) · `components/preview/previewSource.ts:87`(계약 밖 **타일 URL** raw fetch — `api.*` op 호출이 아니다).
- **음성시험 0** — `services/core-api/tests` 에 이 4 op 의 403 을 단언하는 시험 없음.

**설계 대칭 근거(감사 문서가 「못 찾았다」고 한 것)** — 이번에 하나 나왔다. `fe-core.yaml` 에서 `403` 을 선언한 op 은 **36종**인데, 같은 `routes/preview.py` 안의 `listPalettes` 는 `403` 을 선언하지 **않고** 코드 주석이 그 이유를 적는다 — 「**경계 판정이 없다** — 팔레트는 연구실에 딸린 값이 아니라 렌더러의 능력이다」(`preview.py:57-58`). 즉 「중계·읽기에는 403 을 안 건다」는 판단이 이미 한 번 내려져 있고, **네 op 의 403 선언이 그 판단과 어긋나 있다.**

**철회하면 깨지는 것** — 런타임 0. 다만 **생성물 재생성이 필요하다** — `frontend/src/generated/fe-core.ts` 에 `403` 39회. `manifest.toml` `fe-core-ts` 엔트리가 `generated-up-to-date` 게이트에서 byte-diff 되므로, 계약 수정 시 `cd frontend && npm run generate` 를 함께 돌리지 않으면 그 게이트가 red 다. `contract-breaking` ERR/WARN 은 ①②와 같은 `[미확인]`.

**집행하면 드는 일** — 어느 스위치를 걸지부터 정해야 한다. 후보는 `업로드·편집`(`_require_upload_edit` — `ingestion.py:163`)이나, **네 op 의 성격이 갈린다**: 앞 둘은 업로드 흐름의 **읽기**, 뒤 둘은 미리보기 **중계**다. 미리보기에 `업로드·편집` 을 걸면 **권한이 없는 구성원이 데이터셋 미리보기를 못 보게 된다** — 이는 조회 권한 축소이고 `PERMISSION-PRINCIPLES` 의 스위치 4종(`업로드·편집`·`프로젝트 생성`·`승인 위임`·`연구실 설정`) 중 어디에도 「보기」 축이 없다. ⚠ **집행 쪽을 고르면 새 권한 축을 만들거나 기존 축을 조회에 전용하게 된다.**

---

## ⑥ `common.json:60` `PermissionSwitchChange` — seam 참조 0

**정체** — 권한 변경 이력 한 줄의 방향(`켬`/`끔`) 열거값. 공통 스키마에 정의돼 있으나 **어느 seam 도 `$ref` 하지 않는다.**

| 축 | 실물 |
|---|---|
| 선언 | `contracts/schemas/common.json:60-64` — `enum: ["켬","끔"]` |
| seam 참조 | **0건.** 레포 전체(`node_modules` 제외)에서 문자열 `PermissionSwitchChange` 가 **`common.json:60` 단 1회**만 나온다 |
| 구현(쓰기) | `services/core-api/src/colab_core/domains/d2_access.py:155-165` `apply_switch()` — 스위치 upsert 와 이력 append 를 **한 트랜잭션**으로 묶고 `"direction": "켬" if enabled else "끔"` 을 넣는다 |
| 저장 | `db/platform/schema.sql:152-165` `d2_permission_change` — `direction text NOT NULL CHECK (direction IN ('켬','끔'))` ＋ `d2_permission_change_append_only` 트리거(`BEFORE UPDATE OR DELETE` → `deny_update_delete()`) |
| 읽기 표면 | **없음** |

**⚠ 감사 문서와 어긋난다 — 문서가 낡았다.** `X5-AUDIT.md §2-1 ⑥` 은 이 항목을 **「집행(이력 조회 op 신설) vs 현상 유지」의 열린 판정**으로 올렸다. 그런데 **읽기 표면을 두지 않는다는 결정은 이미 두 곳에 명문화돼 있다.**

- `dev-package/PERMISSION-PRINCIPLES.md:93` **P-33** — 「…수정·삭제 경로를 만들지 않는다. **v2 에 조회 화면은 두지 않는다.**」
- `db/platform/schema.sql:151` 주석 — 「…append-only, 스위치 하나당 한 줄(㉘ · P-33). …**v2 에 조회 화면은 두지 않는다.**」
- 그 결정의 등재 = `PLAN-SoT §9-㉘` (`PERMISSION-PRINCIPLES.md:161` 이 「⑧ 권한 변경 감사 기록 → `P-33`·`§9-㉘`」로 2026-08-22 Ted 해소분에 넣었다)

즉 이것은 **미판정 항목이 아니라 판정이 끝난 항목**이고, 정합한 상태는 「구현·저장 O · 계약 읽기 표면 X」다. 감사 문서가 「근거를 못 찾았다」고 한 것이 사실과 다르다.

**남는 진짜 질문은 하나** — 「seam 이 아무도 참조하지 않는 `$def` 를 `common.json` 에 두는 것이 옳은가」. 두 갈래:
- 유지 = DB `CHECK` 제약과 도메인 코드의 값 집합에 대한 **계약 상의 유일한 명세**로 남긴다(`schema.sql` 과 `d2_access.py` 두 곳이 갈라지는 것을 막는 자리).
- 철회 = `common.json` 에서 지운다 → **`켬`/`끔` 값 집합의 정본이 DB 스키마와 파이썬 코드 두 곳에만 남는다.** 계약이 도는 원장을 부정하는 모양이 된다.

**철회하면 깨지는 것** — 런타임 0(참조가 0이므로). 잃는 것은 값 집합의 단일 정본. `contract-lint`·`seam-consistency` 영향 없음(미참조 `$def` 를 red 로 세는 룰 없음 — `gates/tools/seam_consistency.py` 의 4검사 `ge`·`gb`·`citation`·`flow` 중 어디에도 없다).

**집행(조회 op 신설)하면 드는 일** — `fe-core.yaml` 에 이력 조회 op 신설 ＋ `d2_access` 읽기 어댑터 ＋ FE 화면. **그리고 P-33 을 뒤집는 판정이 선행돼야 한다** — 지금 집행하면 명문 결정 위반이다.

---

## ⑦ core-ai `suggestLineage` — 소비자만 서 있는 비대칭

**정체** — 계약이 선언한 `POST /lineage-suggestions` 를 `ai-service` 가 열지 않는데, `core-api` 는 이미 그 경로로 나간다.

| 축 | 실물 |
|---|---|
| 선언 | `contracts/seams/core-ai.yaml:67` — `operationId: suggestLineage`, `POST /lineage-suggestions`, 응답 `200`·`400`·`422`·`401`·`503` |
| 생산자 | **없음.** `services/ai-service/src/colab_ai/app/main.py` 가 여는 경로는 `POST /searches`(`main.py:71`)와 `GET /healthz`(`main.py:67`) 둘뿐. 같은 파일 docstring `main.py:3` 이 「**여는 것은 `searchDatasets` 하나다.** `suggestLineage` 는 `K3` 의 자리이고 여기서 흉내 내지 않는다」로 명시 |
| 소비자 | **있다.** `services/core-api/src/colab_core/app/relay.py:282` — `HttpLineageSuggestionRelay.suggest()` 가 `f"{self._base}/lineage-suggestions"` 로 실제 POST |
| 못 닿을 때 | `relay.py:272,285,291,297` 네 자리 전부 `honest_empty_suggestions(...)` → **200 + 빈 배열 + 사유 문구**. 5xx 로 끝내지 않는다 |
| FE 도달 | `frontend/src/components/lineage/lineageSource.ts:13` 이 `GET /uploads/{uploadId}/lineage-suggestions` 를 부른다 → `routes/ingestion.py:319` → 위 중계 |
| 배정 | `dev-package/work-items.yaml:921-932` `K3` 「계보 제안 서비스」 · `status: open` · `stage: stage2` · 진입조건 `K2(✅)·D2(✅) — 열려 있다` · 완료정의 「평가셋 대비 제안 품질 ＋ D4 쓰기 경로 부재 음성 테스트 green」 |

**판정 갈래가 ①②⑤와 다르다** — 철회 대상이 아니다. `K3` 로 이미 배정돼 있고 진입조건이 열려 있다. 열린 것은 **「언제」와 「그때까지의 표기」** 다.

**현상 유지 비용** — 사용자에게 거짓말은 아니다(빈 상태를 사유와 함께 정직하게 말한다). 다만 **계약이 선언한 표면 하나가 무기한 공중에 뜬 채 남고**, 그 op 에 딸린 `core-ai` 속성 11개(`AiSuggestionBase.suggestionId`·`confidence` 등)와 응답코드 `422`(`core-ai.yaml:92`)가 함께 미구현으로 남는다. **⚠ `core-ai.yaml:92` 의 `422` 는 ①② 와 같은 축이지만 지금 단독 철회 대상이 아니다** — op 이 설 때 함께 판정한다.

**집행하면 드는 일** — `K3` 그대로. ai-service 에 `POST /lineage-suggestions` 신설 ＋ 제안 로직 ＋ 평가셋 ＋ **D4 쓰기 경로 부재 음성 시험**(완료정의). 계약 개정 0(이미 선언돼 있다). `relay.py` 수정 0(이미 부른다) — **소비자가 서 있다는 것이 집행 비용을 낮추는 쪽으로 작용한다.**

---

## `[미확인]` 목록

| 항목 | 무엇이 미확인 | 무엇을 하면 풀리나 |
|---|---|---|
| ①②⑤ 철회 시 `contract-breaking` 판정 | oasdiff 가 **비성공 응답 코드 제거**를 ERR 로 보는지 WARN 으로 보는지. `gates/tools/contract-breaking.sh:82` 가 `--fail-on ERR` 이라 WARN 이면 green | 계약 수정 후 `gates/run.sh contract-breaking` 1회 실행 (docker 필요) |
| ⑤ 철회 시 생성물 정합 | `frontend/src/generated/fe-core.ts` 재생성 후 byte-diff 결과 | `cd frontend && npm run generate` 후 `gates/run.sh generated-up-to-date` |
| ③④(참고) staging 반영 | `x5-403-enforce` 는 `origin` 에 있으나 `main` 미병합. staging 배포·frontend·DB 의존 게이트 미측정 | 브랜치 병합 판정 후 전 게이트 1회 |

## 이번 회차에 세지 않은 판단기준

- **런타임 실측 0** — 컨테이너·staging 을 건드리지 않았다. 위 판정은 전부 **정적 판독**이다.
- **게이트 실행 0** — 이번 조사에서 `gates/run.sh` 를 한 번도 돌리지 않았다. 게이트 관련 서술은 스크립트·룰셋 **판독**에 근거한 것이지 실행 결과가 아니다.
- `X5-AUDIT.md §2-3` 의 기존 미확인 2건(`d5_ingestion.py:53,54` 죽은 분기 · 등기부 밖 「generated」 자칭 파일)은 이번 범위 밖이며 **그대로 열려 있다.**
