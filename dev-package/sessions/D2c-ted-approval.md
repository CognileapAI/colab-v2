# D2c ㉢ 제출 패키지 — 계약 동결 전 Ted 승인 요청 (2026-08-23)

> **성격** — `〈61〉-㉢`(`PLAN-SoT.md:322`) · `D2c.md §7-8` 의 사람 승인 단계 제출물. **㉠·㉡ 기계 검사가 green 이어도 이 승인 없이 동결하지 않는다**(`03-HANDOFF.md:134`).
> **⚠ 명시 승인 규칙(§7-8-㉢-3) — 침묵은 승인이 아니다.** 이 문서를 읽었다는 사실·답이 없다는 사실은 승인으로 세지 않는다. 승인·수정 지시·거절 중 하나의 **명시 답변**이 있어야 동결로 간다.
> **현재 상태** — 계약 개정(C1)·게이트(C2)는 워킹트리에 있고 **커밋·동결 전**이다. 501 라우트(D2c-api)도 이 승인과 별개로 남아 있다.

---

## 1. 무엇을 승인하는가 — 신설 전량 (fe-core.yaml 34 → 45 op)

**위임 산문 정정** — `fe-core.yaml:13-16` 의 「이벤트/업로드 seam」(존재하지 않는 위임처, `DR-7`) 산문을 실제 op 로 대체하고, 판정 기준 문장(「없다고 적으려면 받는 곳에 FE 가 도달할 수 있어야 한다」)을 명기. `:14` 검색 진입점은 산문 정정까지 — **「P4 가 연다」 명기**(`D2c.md §10-3`). `unlinkProjectDataset` 의 거짓 산문(「담는 동작은 이 seam 에 없다」) 정정. tag 2종 신설(`ingestion`·`visualization`).

### 신설 op 11 (근거 인용 포함 — 전량 ㉠ 통과)

| op | 경로 | 근거 |
|---|---|---|
| `createUpload` | POST `/uploads` | `D2c §2-4` · `core-pipeline.json` ①(source=core-api const) · Policy §2·§8 — `upload.accepted` 발행 유일 자리 |
| `getUploadStatus` | GET `/uploads/{uploadId}` | `§2-4` · SEAM-AUDIT I-18·C-5 — 실패 사유 `envelope.json#FailureReason` $ref |
| `listUploadLineageSuggestions` | GET `/uploads/{uploadId}/lineage-suggestions` | **추기-2 — 범위 확장 1건**(아래 §2-④) · Policy §2 규칙 맵 · 응답 `core-ai.yaml#LineageSuggestionResponse` $ref |
| `createDataset` | POST `/datasets` | `§2-5` · Policy §7.2 · 〈55〉 — 등록 전환, `projectIds` 접힘(Q2 판정) |
| `updateDataset` | PATCH `/datasets/{datasetId}` | `§2-7` · DATAMODEL-BASELINE(이름·주제·요약만) · DR-14 |
| `addDatasetFile` | POST `/datasets/{datasetId}/files` | `§2-6` · 〈58〉-② 후주입 · 〈59〉 · 〈60〉 |
| `replaceDatasetGridFile` | PUT `/datasets/{datasetId}/files/{fileId}` | 〈59〉-①·③(본체 대상 아님 → 409) |
| `deleteDatasetGridFile` | DELETE `/datasets/{datasetId}/files/{fileId}` | 〈59〉-①·③ |
| `linkProjectDataset` | PUT `/projects/{projectId}/datasets/{datasetId}` | `§2-8` · DATAMODEL-BASELINE — 본문 있는 op(`usageNote` required-but-nullable) |
| `createPreviewRender` | POST `/previews` | `§2-9` · SEAM-AUDIT I-06·I-07·C-4 — `core-viz.yaml#RenderRequest/RenderJob` $ref, 타일 URL 중계 안 함 |
| `getPreviewRender` | GET `/previews/{renderId}` | `§2-9` — `RenderFailureCode` 는 미신설(아래 NB-B) |

### 신설 스키마·파라미터

- 스키마 7종 — `UploadFileRef`(이벤트 FileRef 와 동일 4값) · `UploadReceipt` · `UploadStatus`(필드마다 원천 이벤트 명기) · `UploadLineageParent` · `DatasetCreate` · `DatasetUpdate` · `ProjectDatasetLinkCreate`
- 파라미터 3종 — `UploadId` · `FileId` · `RenderId`
- **무변경 확인** — `contracts/events/**` 전체 · `core-viz.yaml` · `core-ai.yaml`($ref 소비만) · `common.json` 은 산문 1건만(아래 ⑤)

---

## 2. `[정본 무근거]` 항목 — 별도 승인 필요 (지어내지 않고 비워 뒀던 것)

| # | 항목 | 상태 · 승인 요청 |
|---|---|---|
| ① **NB-A `fileId` 동일성** | 업로드 발급 `fileId` ULID 가 등록 전환 후 `d3_file.id` 로 **그대로 유지**(변환 지점 없음). 계약 산문에 명기됨(`createDataset`) | **사용자 승인 2026-08-23 확보 — 단 그 승인이 Ted 본인인지 미확인.** 그래서 이 목록에 유지한다. **Ted 본인의 확인 요망** |
| ② **NB-B `RenderFailureCode` 표기** | 실패 **종류 3개는 정본 확정**(문장으로) — `code` 라벨 표기만 무근거. **enum 을 신설하지 않고 등재만 해 뒀다**(`getPreviewRender` 는 산문 참조) | **Ted 한 줄 답 대기** — 답이 오면 `common.json` 에 신설 |
| ③ **`usageNote` 시점** | 정본 업로드 폼(Policy §5)에 usageNote 자리가 없다 → **등록 후 `linkProjectDataset` 으로 채우는 흐름**으로 판정(Q2) | 레포 판정 — 승인 요청 |
| ④ **AI 중계 op 범위 확장** | `listUploadLineageSuggestions` 는 지시서 §2 목록 밖 신설(추기-2) — `core-ai` 가 내부 seam 이라 FE 도달 경로가 없던 구멍 | **범위 확장 1건, 사용자 승인 2026-08-23** — Ted 확인 요망 |
| ⑤ **격자 0~2건 `common.json` 산문** | `FileKind` description 「0~1건」→ 「0~2건(+grid_axis·후주입)」 갱신(〈58〉 인용, description-only additive). `core-pipeline.json:39` 의 「0~1건」은 **이벤트 동결 때문에 미수정** — 사유 명기 | C2 판정 — 승인 요청(이벤트 쪽은 다음 이벤트 개정 회차) |
| ⑥ **전송 형태** | 파일 바이트가 `createUpload` 로 직접 — 정본은 「끌어다 놓는다」까지(E04-map 단계 1 형태 승계). `UploadLineageParent.confirmedMethodText` 실림 자리도 정본 무형태 | 레포 결정 — 승인 요청 |

---

## 3. ㉠·㉡ 기계 검사 결과 요약 (green — 단, 옳음의 증거가 아니라 전제)

- **㉠ 정본 근거 대조** — 기준선 대비 신설 op·스키마·파라미터 **50건 전수 통과**(description 공란 0 · 인용/무근거 표기 누락 0). **근거의 내용이 옳은지는 안 본다** — 그것이 이 문서(㉢)의 몫이다.
- **㉡ 흐름 완주** — E-04 15단계 재생, **끊긴 자리 0** · 의도적 P4 이월 1건(단계 11) · 외부 입력 2건 명기. **⚠ fixture 는 `E04-step-op-map.DRAFT.md` 승계본 — 그 표 자체가 아직 Ted 검토 전(DRAFT)** 이므로, 이 승인과 별도로 표 검토가 필요하다.
- 게이트 전 수트 green(`contract-breaking` additive 증명 포함) · `seam-consistency-selftest` 13케이스(green 4 · red 9) green · **개정 전 계약에서 G-e·G-b red 실측** 후 개정으로 닫힘.

---

## 4. 답변 형식

**①~⑥ 각각과 §1 전체**에 대해 승인 / 수정 지시 / 거절 중 하나를 명시로. 전체 일괄 승인도 명시라면 유효하다. **무응답은 어느 항목에 대해서도 승인이 아니며, 그 동안 동결하지 않는다.**
