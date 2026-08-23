# P2 · W2 `P2-api` 실행 보고

> **레인** `P2-api` (물결 2 · `P2-pipeline`·`P2-viz` 와 병렬) · **일자** 2026-08-23 · **실행 위치** 워크트리 `.claude/worktrees/p2-exec`
> **커밋하지 않았다.** 커밋·`03-HANDOFF`·`PLAN-SoT` 갱신은 메인 세션 몫이다 (`P2-EXEC §7`).
> **계약을 고치지 않았다** — `contracts/` diff 0줄 (동결, `〈61〉-㉢`).
> **staging 을 건드리지 않았다.** 일회용 컨테이너는 `p2api_pg` 하나이고 **호스트 포트를 하나도 열지 않았다**(컨테이너 IP 로만 붙었다). 끝나고 지웠다 — `§H-3` 에 확인 출력.
>
> **서술 규약** — `§A`~`§F` 는 **증거**(명령 + 실제 출력)다. `[잠정]`·`[해석]` 이 붙은 것은 해석이다 (`DATA-REFERENCE §0 M-5`).
> 행 번호는 `cat -n` 으로 확인하고 옮겼다 (`M-7`). 절대경로를 적지 않는다 (`CLAUDE.md §3-8`).
> **재지 않은 것은 `[미측정]` 이라 적었다** (`M-4`).

---

## 0. 한 눈에

| 항목 | 결과 |
|---|---|
| 501 → 실구현 | **12 op** — 업로드 6 · 계보 확정 3 · 중계 3 |
| 501 표 | **36 → 24** (지시서의 목표치는 28. **차이의 이유를 `§E` 에 적었다 — 숨기지 않는다**) |
| 계보 오염 방지 음성 시험 8종 | **8/8 구현 · 전건 RED → GREEN 관측** (㉮㉯㉰㉱㉲㉳㉴㉵) |
| 음성 ② (확장자 ≠ 실제 포맷) | ✅ RED → GREEN |
| **`NB-A` 동일성 단언** | ✅ 존재하고 green — `tests/test_dataset_registration.py::test_file_id_identity_is_preserved` |
| **처리 중 업로드가 만료를 넘겨 살아남는 시험** (`〈67〉` 이행 제약 ㉡) | ✅ 존재하고 green — `test_uploads.py::test_an_upload_still_being_processed_survives_its_expiry_time` |
| `〈60〉` 활동 기록 | ✅ 실물 관측 — `§D` (교체 1행 · `마지막 수정` 불변 · 자동메타 재계산) |
| `upload.accepted` 실발행 (`P2-EXEC §6-7`) | ✅ 원장 outbox 행을 눈으로 봤다 — `§B-2` |
| 시험 | **224 passed** (착수 시점 166 → **+58**) · 연속 3회 재실행 green |
| 게이트 | 18종 green · `planning-freshness` **red(기존 · 워크트리 부작용)** · `schema-diff` **[미실행]** — `§F` |
| **닫지 못한 것** | **격자 파일 후주입(`addDatasetFile` 의 `기준 격자 파일`)** — 축을 채울 주체가 어디에도 없다. `§G-1` 경계 멈춤 |

---

# 증거

## A. 무엇을 만들었나 — 12 op

### A-1. 업로드 6 op (`P2-EXEC §4 W2 P2-api ⑴`)

| op | 자리 | 지킨 것 |
|---|---|---|
| `createUpload` POST `/uploads` | `app/routes/ingestion.py` | **`upload.accepted` 를 내는 유일한 자리**(`source='core-api'` 를 DB CHECK 가 강제) · `UploadReceipt` 가 `uploadId`·`fileId` 를 FE 표면에 처음 내린다 · **D3 에 행을 만들지 않는다** |
| `getUploadStatus` GET `/uploads/{uploadId}` | 〃 | 이벤트 ②~⑦ 의 **결과만** 읽는다(새 사실 0) · 만료 404 · **아직 모르면 `null`**(0/false 로 안 채운다) |
| `createDataset` POST `/datasets` | 〃 | **등록 전환** · `lineageParents[]`+`projectIds[]` 한 요청 · **`fileId` 동일성** · 404 만료 · 409 이미 전환 |
| `addDatasetFile` POST `/datasets/{datasetId}/files` | 〃 | 본체 후주입 동작 · `〈60〉` 활동 1행. **격자는 `§G-1` 로 막혔다** |
| `replaceDatasetGridFile` PUT | 〃 | 격자만 · 본체 **409** · `〈60〉` 활동 1행 · `fileId` 유지 |
| `deleteDatasetGridFile` DELETE | 〃 | 격자만 · 본체 **409** · `〈60〉` 활동 1행 |

### A-2. 계보 확정 3 op (`⑵`)

`app/routes/lineage.py` — `addLineageParent` · `removeLineageParent` · `confirmLineage`.
**Lv 는 파생 계산이고 저장하지 않는다** — `(주입력 부모 중 최대 Lv) + 1`, 보조입력 제외, 부모 없으면 Lv0.
계산은 P0 이 이미 세운 `domains/d4_lineage.py` 의 재귀 질의(`parent_role = '주입력'` 필터)가 하고, P2 는 **쓰기 쪽**을 더했다.

### A-3. 중계 3 op (`⑴-2` · `〈63〉-㉮`)

`app/routes/preview.py` — `createPreviewRender` · `getPreviewRender`.
`app/routes/ingestion.py` — `listUploadLineageSuggestions`.
**요청/응답을 재선언하지 않는다**(`core-viz.yaml#RenderRequest`/`RenderJob` · `core-ai.yaml#LineageSuggestionResponse`).
**타일 URL 을 중계하지 않는다** — core-api 에 타일 경로가 하나도 없음을 시험이 단언한다.
전송은 **표준 라이브러리 `urllib`** 다 — HTTP 클라이언트를 새로 얹지 않으려고 그렇게 했다.

### A-4. Port 신설 (`〈63〉-㉱`)

`ports/ingestion.py` — `UploadLedgerReadPort` + `UploadLedgerWritePort` (`ports/lineage.py` 의 Protocol 패턴 승계).
`ports/relay.py` — `PreviewRenderPort` · `LineageSuggestionPort`.
유일한 D5 구현은 `domains/d5_ingestion.py` 하나이고, **그것이 유일함을 시험이 검사한다**(`test_upload_ledger_hidden.py::test_only_one_module_in_core_api_touches_the_d5_tables`).

---

## B. RED 를 눈으로 봤다 — 그리고 GREEN

**방법** — `git archive HEAD services/core-api` 로 **변경 전 소스 트리**를 따로 풀고, 새 시험 8파일을 그 위에서 그대로 돌렸다. 워킹트리를 되돌리지 않았으므로 형제 레인(`P2-pipeline`·`P2-viz`)의 작업에 손대지 않았다.

### B-1. RED 판정 줄 (그대로)

```
67 failed, 4 passed, 1 error in 7.58s
```

`4 passed` 는 **정적 스캔 시험 넷**이다 — HEAD 에는 검사 대상 코드가 아예 없어서 통과했다. **이 넷은 RED→GREEN 을 주장하지 않는다.** 넷의 이름:

```
PASSED tests/test_uploads.py::test_no_extension_to_format_table_exists_in_core_api
PASSED tests/test_lineage_confirm.py::test_lv_is_derived_and_never_stored
PASSED tests/test_upload_ledger_hidden.py::test_only_one_module_in_core_api_touches_the_d5_tables
PASSED tests/test_ai_no_lineage_write.py::test_no_module_in_core_api_writes_d4_except_the_owning_domain
```

`1 error` = `tests/test_dataset_files.py` 수집 실패(`ACTION_GRID_CHANGED` 부재) — 그 파일의 전건이 RED 였다는 뜻이다.

### B-2. 음성 시험 8종 — **하나씩** RED → GREEN

| # | 무엇 | 시험 함수 | HEAD 에서 | 지금 |
|:--:|---|---|:--:|:--:|
| **㉮** | 사람이 올린 파일이 **우리 산출물(COG)로 기록되지 않는다** · 계보에 파생물로 서지 않는다 | `test_dataset_registration.py::test_a_human_uploaded_file_is_never_recorded_as_our_product` | **RED** | **GREEN** |
| **㉯** | **계보 순환·자기부모 금지** (`DR-15`) | `test_lineage_confirm.py::test_self_parent_is_refused`<br>`::test_a_two_hop_cycle_is_refused`<br>`::test_a_three_hop_cycle_is_refused`<br>`::test_a_cycle_through_a_secondary_parent_is_also_refused`<br>`::test_registration_time_parents_are_cycle_checked_too` | **RED ×5** | **GREEN ×5** |
| **㉰** | **등록 원자성** — 중간 실패 시 D3 반쪽 행 없음 | `test_dataset_registration.py::test_a_mid_way_failure_leaves_no_half_row_in_d3` | **RED** | **GREEN** |
| **㉱** | **재전달 멱등** — 같은 이벤트 2회에도 D3·D4 중복 0 | `test_dataset_registration.py::test_delivering_the_accepted_event_twice_creates_one_outbox_row`<br>`::test_registering_the_same_upload_twice_is_409_and_creates_one_dataset` | **RED ×2** | **GREEN ×2** |
| **㉲** | 등록 없이 나간 파일이 **D3 에 한 행도 없다** (`〈64〉`) | `test_dataset_registration.py::test_a_file_that_left_without_registering_leaves_no_row_in_d3` | **RED** | **GREEN** |
| **㉳** | **만료된 업로드는 전환되지 않는다**(404) | `test_dataset_registration.py::test_an_expired_upload_does_not_convert`<br>`test_uploads.py::test_an_expired_upload_answers_404` | **RED ×2** | **GREEN ×2** |
| **㉴** | **`d5_*` 가 어느 읽기에도 안 비친다** + reaper 정리 | `test_upload_ledger_hidden.py::test_ledger_identifiers_never_appear_in_any_read_path`<br>`::test_the_ledger_row_is_not_visible_through_the_lineage_read`<br>`::test_the_reaper_deletes_expired_rows_and_their_children`<br>`::test_the_reaper_does_not_reach_across_the_lab_boundary` | **RED ×4** | **GREEN ×4** |
| **㉵** | `ai-no-lineage-write` — **D10 이 D4 에 쓸 경로 없음** | `test_ai_no_lineage_write.py::test_d4_writes_all_require_a_human_confirmer`<br>`::test_the_ai_relay_cannot_reach_the_lineage_write_path`<br>`::test_a_request_cannot_forge_the_ai_confirmed_origin`<br>`::test_the_suggestion_op_never_writes_anything` | **RED ×4** | **GREEN ×4** |
| **음성 ②** | 확장자 ≠ 실제 포맷(`.nc`=HDF5 · `.hdf`=HDF4) 에서 확장자 기반 감지 red | `test_uploads.py::test_core_api_never_infers_a_format_from_the_extension[×2]` | **RED ×2** | **GREEN ×2** |

**㉵ 의 정직한 단서 `[해석]`** — `test_the_ai_relay_cannot_reach_the_lineage_write_path` 의 HEAD RED 는 「금지 심볼을 찾았다」가 아니라 **「`relay.py` 가 없다」**였다. 그 파일이 P2 산출물이라 그렇다. **이 한 건의 RED 는 다른 여덟보다 약하다** — 대신 `§F` 의 게이트 `ai-no-lineage-write` green 과 함께 읽어야 한다.

**㉴ 의 정직한 단서 `[해석]`** — 위 표의 넷은 RED→GREEN 이지만, 「문이 하나뿐임」을 보는 `test_only_one_module_in_core_api_touches_the_d5_tables` 는 §B-1 의 정적 넷 중 하나라 **RED 를 못 냈다**. 그 시험은 **앞으로 문이 둘이 되는 것을 막는** 장치이지 지금을 증명하는 장치가 아니다.

### B-3. `upload.accepted` 실발행 — **원장 outbox 행 실물** (`P2-EXEC §6-7`)

파이프라인 레인이 「이 한 종만은 시험이 core-api 자리를 대신 세웠다」고 남긴 자리다. 실제로 `createUpload` 가 기입하는 것을 관측했다:

```
=== ① createUpload → UploadReceipt
201 {"uploadId": "01M0QG16YGP3CHC6KNBDAJ2G1M", "files": [{"fileId": "01M0QG16YGXWSBGJKQZKPH2BEP", "fileName": "gk2a.nc", "kind": "본체", "byteSize": 40}]}

=== ② upload.accepted 가 원장 outbox 에 실제로 기입됐다
{"event_type": "upload.accepted", "source": "core-api", "schema_version": "1.0",
 "idempotency_key": "upload.accepted:01M0QG16YGP3CHC6KNBDAJ2G1M", "published_at": null,
 "attempt": 1, "max_attempts": 5,
 "payload": {"files": [{"kind": "본체", "fileId": "01M0QG16YGXWSBGJKQZKPH2BEP", "byteSize": 40, "fileName": "gk2a.nc"}]}}
```

`published_at: null` 은 **미발행**이라는 뜻이고 정상이다 — 릴레이가 채운다(`0004` 주석). core-api 의 몫은 **기입**까지다.

---

## C. `NB-A` 동일성 — 유일한 방어선

**왜 단언이 필요한가** — `d5_upload_file.id → d3_file.id` 에는 **FK 가 없다**(불변규칙 1 이 금지한다). 등록 코드가 ULID 를 새로 뽑아도 **DB 는 아무 말도 하지 않는다.** 동일성이 조용히 깨지고, 그 뒤로 업로드 세계의 `fileId` 로는 아무것도 못 찾는다. `DATA-REFERENCE §0` 이 반복해 말한 「에러 없이 그럴듯한 값」의 정확한 자리다.

실측:

```
=== ④ createDataset → NB-A 동일성
발급 fileId : 01M0QG16YGXWSBGJKQZKPH2BEP
d3_file.id  : ['01M0QG16YGXWSBGJKQZKPH2BEP']
Lv / 계보상태: 0 기록 없음
```

시험 `test_file_id_identity_is_preserved` 는 **파일 2건**으로 같은 것을 단언하고, `listDatasetFiles` 응답까지 대조한다.
코드 쪽 장치 — `d3_catalog.insert_file` 은 **`file_id` 를 인자로만 받는다.** 그 함수 안에서 ULID 를 뽑지 않는다.

---

## D. `〈60〉` 활동 기록 — 실물 관측

```
=== ⑤ 〈60〉 — 격자 교체 전/후
PUT 200 {"fileId": "00000000000000000000000FA2", "fileName": "new-grid.nc", "kind": "기준 격자 파일"}
마지막 수정  전: 2026-01-02 00:00:00+00:00 후: 2026-01-02 00:00:00+00:00
자동메타     전: {'crs': 'EPSG:5179', 'grid': None} 후: {'crs': None, 'grid': None}
활동 행 수   전: 0 후: 1
활동 행: [{'action': '좌표계·격자 변경', 'target_kind': '데이터셋', 'actor_account_id': '000000000000000000000000A1'}]
```

| `〈60〉` 요구 | 관측 |
|---|---|
| ① `마지막 수정` 을 건드리지 않는다 → `계보 상태` 가 안 접힌다 | **동일**(`2026-01-02 00:00:00+00:00` 전후 같음) |
| ② `자동으로 읽은 정보`(좌표계·격자) 재계산 | `crs: EPSG:5179 → None` |
| ③ `d8_activity` 에 `좌표계·격자 변경` 한 행 · 스키마 무변경 | **0 → 1행**, 문자열 그대로 |

**②의 판단 `[해석]`** — core-api 는 파일을 읽지 못한다(`CLAUDE.md §3-4`). 그래서 **재계산의 결과로 「모른다」(NULL)를 쓴다.** 낡은 값을 그대로 두면 **지워진 파일에서 읽은 좌표계가 화면에 남는다.** 새 값은 파일을 읽는 쪽(pipeline-worker)이 채운다. **이것은 「재계산했다」의 절반이다** — 나머지 절반(새 값 채우기)의 소유는 `§G-2` 에 미결로 올린다.

`addDatasetFile`(본체)·`deleteDatasetGridFile` 도 같은 셋을 지키며 각각 활동 1행을 남긴다 — `tests/test_dataset_files.py` 8건.

---

## E. 501 표 — 36 → **24** (지시서 목표 28과 다르다)

### E-1. 뺀 것 12 (뺀 자리마다 실동작 시험이 있다)

| op | 시험 파일 |
|---|---|
| `createUpload` · `getUploadStatus` | `tests/test_uploads.py` |
| `createDataset` | `tests/test_dataset_registration.py` |
| `addDatasetFile` · `replaceDatasetGridFile` · `deleteDatasetGridFile` | `tests/test_dataset_files.py` |
| `addLineageParent` · `removeLineageParent` · `confirmLineage` | `tests/test_lineage_confirm.py` |
| `createPreviewRender` · `getPreviewRender` | `tests/test_preview_relay.py` |
| `listUploadLineageSuggestions` | `tests/test_lineage_suggestions.py` |

**이 대응을 시험이 검사한다** — `test_not_implemented.py::test_every_op_p2_took_out_has_a_behavioural_test_behind_it` 가 파일 존재와 op 이름 등장을 함께 본다. 표만 줄이고 시험이 없으면 red 다.

### E-2. **왜 28 이 아니라 24 인가 — 지시서 내부의 불일치다**

`P2-EXEC §4 W2 P2-api` 는 한 문서 안에서 두 가지를 말한다:

- `⑴`+`⑴-2`+`⑸` — 「업로드 6 + 미리보기 중계 2 → 36 → **28**」
- `⑵` — 「`addLineageParent`·`removeLineageParent`·`confirmLineage` 를 구현한다」
- 「`listUploadLineageSuggestions` 는 **중계 구현까지** 하되 0건으로 완결한다」

**뒤의 둘을 지키면 28 이 될 수 없다.** 구현한 op 을 501 표에 남기는 것은 **가짜 501** 이고, `P2.md §2-19`(목록이 줄어드는 것이 진척의 계측)를 정면으로 거스른다.
**그래서 실제 구현을 따라 24 로 적었다.** 목표치를 못 맞춘 것이 아니라 **목표치가 구현 지시와 어긋난다** — 판정이 필요하면 `§G-4`.

### E-3. 남긴 24 와 이유

| op | 남긴 이유 |
|---|---|
| `updateDataset` | **상세 편집**이라 P2 화면(S-04·S-08) 범위 밖 (`P2-EXEC`) |
| `linkProjectDataset` | **P5**. P2 는 `createDataset.projectIds` 만 다룬다. `usageNote` 는 정본 업로드 폼에 자리가 없다(`D2c` C1 Q2) |
| `getDatasetLineage` | **P1 배정**이다. 그래프를 만드는 함수는 P2 가 만들었지만(`routes/lineage.py::lineage_graph`) 조회 op 을 여는 것은 **범위 늘리기**라 하지 않았다 (`CLAUDE.md §5`). ⚠ **다음 세션에 남는 어색함이다** — 만들어 둔 함수가 501 뒤에 있다 |
| `downloadDataset` · 접근 요청 4 · Verified 요청 2 | 저장처가 P0 스키마에 없다 — **P6** |
| `deleteDataset` · `getDatasetDeletionImpact` · `approveVerification` · `cancelVerification` · `updateLab` · 프로젝트 5 · 대시보드 3 | **P1 로 등재된 것 그대로.** P2 가 건드리지 않았다 |

---

## F. 게이트 — 판정 줄 그대로

전부 워크트리 루트에서 `./gates/run.sh <게이트>` 1회씩.

| # | 게이트 | 판정 줄 (그대로) | 판정 |
|---|---|---|:--:|
| 1 | `import-boundary` | `import-boundary green — 계약 전부 통과.` (`Contracts: 8 kept, 0 broken.`) | **green** |
| 2 | `banned-import` | `banned-import green — .py 90건, 금지 import 0.` | **green** |
| 3 | `ai-no-lineage-write` | `ai-no-lineage-write green — 계약·코드·체인 세 층 모두에서 쓰기 경로가 없다.` | **green** |
| 4 | `contract-lint` | `contract-lint green — seam 3건, 룰 위반 0.` | **green** |
| 5 | `contract-breaking` | `contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.` (`No changes detected`) | **green** |
| 6 | `event-lint` | `event-lint green — 스키마 2건 컴파일 · valid 5건 통과 · invalid 8건 거부.` | **green** |
| 7 | `event-breaking` | `event-breaking green — 기준 HEAD (2건) 대비 파괴적 변경 없음.` | **green** |
| 8 | `seam-consistency` | `seam-consistency green — G-e 258건 · G-b 7건 · ㉠ 0건 · ㉡ 15건.` | **green** |
| 9 | `generated-up-to-date` | `generated-up-to-date green — 등기부 1건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.` | **green** |
| 10 | `migration-single-head` | `migration-single-head green — 두 체인 모두 head 1개.` | **green** |
| 11 | `rls-coverage` | `rls-coverage green — allow-list 밖 테이블 전부 FORCE RLS + 연구실 경계 정책, 본체 테이블은 본체 정책까지.` | **green** |
| 12 | `rls-effect` | `rls-effect green — 본체 음성 · 메타 양성(P-13) · cross-tenant 셋 다 엔진이 막는다. 판정 롤은 우회 불가.` (`③ lab_id 보유 표 21개 전수 — 남의 연구실 0행`) | **green** |
| 13 | `boundary-selftest` | `boundary-selftest green — 경계 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).` | **green** |
| 14 | `contract-selftest` | `contract-selftest green — 두 게이트 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).` | **green** |
| 15 | `event-selftest` | `event-selftest green — event-lint · event-breaking 이 틀린 것을 틀렸다고 말한다 (fail-closed 증명).` | **green** |
| 16 | `generated-selftest` | `generated-selftest green — 9 케이스 전부 기대대로 (green 1 · red 8).` | **green** |
| 17 | `seam-consistency-selftest` | `seam-consistency-selftest green — 13 케이스 전부 기대대로 (green 4 · red 9).` | **green** |
| 18 | `db-selftest` | `db-selftest green — DB 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).` | **green** |
| 19 | `rls-effect-selftest` | `rls-effect-selftest green — 보호 장치를 하나씩 떼면 실제로 red 가 난다. 틀린 롤도 red 다.` | **green** |
| 20 | `planning-freshness` | `::error::planning-freshness red — 1건` / `  - 정본 폴더가 없다 (위치 확인 — planning/README.md §1): …/.claude/worktrees/40 COLAB-기획/…` | **red (기존)** |
| 21 | `schema-diff` | **[미실행]** | — |

**20번은 이 레인이 만든 것이 아니다** — `P2-W0-baseline §A-1` 과 `P2-db-report §E-21` 이 착수 시점에 같은 문구로 이미 red 로 기록했다(워크트리 루트를 레포 루트로 계산하는 부작용). 내 변경에 기획 임베드가 없다.
**21번은 안 돌렸다** — 체인별 적용 DB URL 을 둘 다 세워야 하고, `db/` 를 **한 글자도 고치지 않았으므로** 이 레인이 그 판정의 주체가 아니다. `P2-db-report §E-2` 가 `0004` 적용 상태에서 green 을 기록했다. **[미측정]을 green 으로 세지 않는다.**

### F-2. 시험

```
$ python -m pytest tests -q      # 착수 시점 기준선
166 passed in 3.74s

$ python -m pytest tests -q      # 지금
224 passed in 17.39s
```

**연속 3회 재실행 green** — 시험이 자기가 만든 행을 되돌리는지 확인했다(`conftest.py` 의 `_rollback_p2_rows`). 첫 시도에서 **두 번째 실행이 red 였다**(`d3_dataset.file_count` 가 시험마다 1씩 늘었다). 그 실패를 고친 뒤 3회 연속 green 이다 — **한 번 green 은 green 의 증거가 아니다.**

---

## G. **하지 못한 것 · `[정본 무근거]` · 판정이 필요한 것**

명시하지 않으면 다음 세션이 「했겠지」로 읽는다.

### G-1. ⛔ **격자 파일 후주입이 막혔다 — 경계 멈춤** (`CLAUDE.md §4`)

**증상** — `addDatasetFile` 에 `kind='기준 격자 파일'` 로 들어오면 **400** 을 낸다. 그 op 의 본래 목적(`〈58〉-②` 후주입)이 그것이라 **op 의 절반이 안 선다.**

**원인 — 축을 채울 주체가 어디에도 없다.**
`d3_file` 의 CHECK 는 「기준 격자 파일 → `carries_lat`·`carries_lon` 중 최소 하나 true」를 요구한다(`0004` · `〈66〉`). 축은 **파일을 열어야** 나오고, 그 판별은 pipeline-worker 소관이다 — core-api 에 geo 라이브러리를 import 하지 않는다(`CLAUDE.md §3-4`).
업로드 경로에서는 워커가 뒤늦게 행을 세우면 된다(`colab_pipeline…d5_ingestion.record_file_axes_row`). **그러나 후주입은 업로드를 지나지 않는다** — 이벤트 7종이 전부 `uploadId` 에 매달려 있고, 워커가 D3 에 쓰는 경로는 불변규칙 1 이 금지한다.

**하지 않은 선택 셋과 이유** — ⓐ 축을 추측해 채운다 → `〈66〉` 이 금지(축이 빈/틀린 격자 행) ⓑ core-api 에서 `.npy` 헤더를 직접 판다 → `P2.md §2-14`(헤더 파싱은 전부 pipeline-worker) 위반이고 `d5/axis.py` 를 두 번 쓰는 일이다 ⓒ `0004` 의 CHECK 를 상태로 조건화한다 → 조율자 판정이 **`0004` 무수정**이었다.

**판정 요청** — 후주입 격자의 축을 **누가 언제 채우는가**. 후보: ㈎ 후주입도 임시 업로드를 하나 만들어 파이프라인을 태우고, 축이 정해진 뒤 사람이 다시 「붙이기」를 누른다(계약 무수정, 화면 1단계 추가) ㈏ core-api ↔ pipeline-worker 동기 판별 seam 을 새로 연다(계약 신설). **레인이 관례로 정할 자리가 아니다.**

### G-2. `〈60〉-②` 재계산의 나머지 절반

core-api 는 좌표계·격자를 **NULL 로 되돌리는 것까지** 한다(`§D`). **새 값을 채우는 주체가 미정**이다 — 격자 파일이 바뀌었다는 사실이 파이프라인에 가는 경로가 동결 7종에 없다(전부 `uploadId` 기반). `G-1` 과 같은 뿌리다.

### G-3. `[정본 무근거]` — 지어내지 않고 표시해 둔 것

| # | 무엇 | 어디까지가 근거인가 |
|---|---|---|
| **NB-2 값** | 수명 **24시간** | **정본에 숫자가 없다**(`〈67〉-ⓐ` — 정본은 규칙 셋만). 운영 설정 `COLAB_CORE_UPLOAD_TTL_HOURS`, 초기값 `kernel/config.py:DEFAULT_UPLOAD_TTL_HOURS = 24`(Ted 승인). **판정 로직에 24 가 박혀 있지 않다** — 시험이 설정을 1시간으로 바꿔 그것을 확인한다. ⚠ **이 24 는 재 본 적 없는 최악 처리 시간 위에 얹혀 있다** — `DR-11` 의 50 GB 는 가정이고 실증된 최대는 `SEED-DATA` 의 1.3 GB 묶음이다. 값이 정본 밖에 있는 이유가 그것이다 |
| **「처리 중」의 정의** | `ready=false AND failed_at IS NULL AND (upload.accepted 아닌 이벤트가 수명 창 안에 있다)` | `〈67〉-ⓐ` 규칙 ②는 「처리 중인 업로드는 만료로 지워지지 않는다」까지다. **무엇을 「처리 중」이라 할지는 정본에 없다.** 새 숫자를 만들지 않으려고 **수명 그 자체를 창으로** 썼다 — 접수만 하고 아무 진행이 없으면 만료 시각에 정확히 죽고, 이벤트가 계속 들어오면 살아남는다. `upload.accepted` 를 진행의 증거에서 뺀 것은 **그것이 접수 순간 반드시 있어서 그것을 세면 만료가 통째로 죽기 때문**이다(구현 도중 실측으로 드러났다) |
| **저장 위치** | 접수 바이트를 로컬 디렉터리에 둔다 (`COLAB_CORE_UPLOAD_DIR`) | 계약이 「core-api ↔ 스토리지 사이는 **배포 내부 사정**」이라 적었다. **바이트를 버리고 201 을 내리지 않기 위해** 실제로 쓴다. presigned multipart 로 갈지는 배포가 정한다 |
| **`RENDER_UNAVAILABLE`** | 그리는 서버에 못 닿을 때의 `code` | `RenderFailureCode` 는 계약에 신설되지 않았다(`NB-B` — Ted 답 대기). **계약을 고치지 않고** 기존 `ErrorEnvelope.code` 로 표현했다. 이 문자열은 레포 결정이다 |
| **중계 헤더** | `X-CoLAB-Lab` · `X-CoLAB-Account` | 내부 표면 두 곳에 경계를 실어 보내는 방식이 계약에 없다. `envelope.json` 이 async 쪽에 같은 이유를 적어 둔 것을 따랐다 |

### G-4. 판정이 필요한 것

1. **501 표의 목표치 28 vs 실제 24** (`§E-2`) — 지시서 내부 불일치다. 구현한 op 을 501 로 남길 수 없어 24 로 갔다.
2. **`getDatasetLineage`** — 그래프 함수가 이미 있는데 op 은 501(P1)이다. 지금 여는 것은 범위 늘리기라 안 했다. P1 잔여로 남길지 P2 가 흡수할지.
3. **G-1 격자 후주입** — 위.
4. **⚠ reaper 조건이 두 레인에서 갈라져 있다 — 실측했다.** `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:396-400`(`cat -n` 확인):
   ```
   DELETE FROM d5_upload
    WHERE registered_at IS NULL AND expires_at <= COALESCE(:now, now())
   ```
   **처리 중 제외 조건이 없다.** 이 레인의 `reap_expired()` 는 제외한다. `〈67〉` 이행 제약 ㉠ 은 **두 곳 모두**에 걸린 요구이므로, 파이프라인 쪽도 같은 조건으로 맞춰야 한다. **[미측정]** — 그 파일은 내 소유가 아니라 고치지 않았고, 그쪽 시험도 안 돌렸다.

### G-5. 소유 디렉터리 **밖**을 만진 것 — 2파일, 명시한다

`services/core-api/requirements.in` · `requirements.txt` 에 **`python-multipart==0.0.20` 한 줄**을 더했다.
**이유** — 동결 계약이 `createUpload`·`addDatasetFile`·`replaceDatasetGridFile` 의 `requestBody` 를 `multipart/form-data` 로 못 박았고, starlette 의 폼 파서가 이 패키지 없이는 **앱이 뜨지도 않는다**(`RuntimeError: Form data requires "python-multipart"`). 손으로 multipart 를 파싱하는 쪽이 명백히 더 나쁘다.
**충돌 없음** — 이 두 파일은 다른 P2 레인의 소유 디렉터리가 아니다. 다만 **`services/core-api/Dockerfile` 은 안 만졌다** — 그 파일은 `requirements.txt` 만 쓰므로 재빌드하면 그대로 들어간다.

### G-6. 안 한 것 (범위 밖으로 남긴다)

- **커밋하지 않았다.** `03-HANDOFF`·`PLAN-SoT` 도 안 고쳤다.
- **staging 을 안 건드렸다.** `0004` 의 staging 적용 여부는 **[미측정]** 이다.
- **`db/`·`frontend/`·`services/pipeline-worker/`·`services/viz-render/`·`contracts/` 를 한 글자도 안 고쳤다.**
- **`viz-render` 실물과 붙여 보지 않았다** — 그 레인이 병렬로 도는 중이라 중계는 **가짜 viz 서버**로 쟀다. 실물 결합은 W3 이전에 한 번 해야 한다.
- **`ai-service` 실물과 붙여 보지 않았다** — 비어 있다. 0건 경로와 가짜 AI 서버 경로 둘 다 쟀다.
- **50 GB 스트리밍 미검증** — 접수 경로가 파일을 통째로 메모리에 읽는다(`await upload_file.read()`). `DR-11` 의 규모에서는 **못 버틴다.** 지금 재료(1.3 GB 묶음)에서는 돈다. **이것은 알려진 미완이지 발견이 아니다** — 청크 IO 로 바꾸는 것은 저장 방식 판정(`G-3` 저장 위치)과 같은 자리에서 함께 정해야 한다.

---

## H. 재현

### H-1. 일회용 DB (호스트 포트 0개)

```
docker run -d --rm --name p2api_pg --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=… -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine
# 이후 rls-effect.sh 와 같은 순서 — 소유자 롤 → db/platform/schema.sql →
#   services/core-api/ops/app-role.sql → services/core-api/tests/fixtures/seed.sql
```

접속은 **컨테이너 IP** 로만 했다(`docker inspect`). 포트를 publish 하지 않았다.

### H-2. 시험

```
COLAB_CORE_TEST_DATABASE_URL=postgresql+psycopg://colab_app:…@<컨테이너IP>:5432/coreapi \
COLAB_CORE_TEST_SUBJECTS_FILE=<레포>/services/core-api/tests/fixtures/subjects.json \
python -m pytest tests -q
```

### H-3. 뒷정리 확인

```
$ docker rm -f p2api_pg && docker ps --format '{{.Names}}' | sort
colab_v2_staging_ai_service
colab_v2_staging_cloudflared
colab_v2_staging_core_api
colab_v2_staging_frontend
colab_v2_staging_nginx
colab_v2_staging_pg
colab_v2_staging_pipeline_worker
colab_v2_staging_viz_render
```

**남은 것은 staging 8개뿐이다.** `p2api_*` 는 0개다.
