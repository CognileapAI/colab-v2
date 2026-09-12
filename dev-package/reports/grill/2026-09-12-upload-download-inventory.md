# 업로드·다운로드 기능 전수 목록 (grill-me 입력)

- 작성 2026-09-12 · 작성자 researcher 서브에이전트 · 승인 **미승인**(조사 산출물, 판정 아님)
- 목적 = Ted 설계 인터뷰(grill-me)의 사실 입력. **판정·권고 없음.**
- 근거 표기 = 「코드에 존재」(파일:행 직접 확인) / 「테스트 존재」(시험 파일 존재 · 통과 여부 별도) / 「대장 상태」(`work-items.yaml` 값) / 「미확인」.
- ⚠ **대장 status 는 동작 증거가 아니다.** 이 문서는 셋을 섞지 않는다.
- 조사 기준 = 작업 브랜치 `codex/design-style-repair` 워킹트리(미커밋 변경 다수 존재).

---

## 1 업로드 화면

### 1-1 파일 구성 (코드에 존재)

`frontend/src/components/upload/` 27 파일 · 6,491행(`wc -l` 실측).

| 파일 | 행수 | 역할(파일 상단 주석 근거) |
|---|---|---|
| `UploadModal.tsx` | 1614 | 모달 골격 · 단계 상태 · 전송 · 재개 · 접수 (`UploadModal.tsx:3`) |
| `RegisterArea.tsx` | 1183 | 등록 3단계 ①분류 ②소속 프로젝트 ③연결 (`RegisterArea.tsx:1`) |
| `PreviewPanel.tsx` | 746 | 미리보기 패널 |
| `FileDropCard.tsx` | 288 | 드롭 · 확장자 선별 |
| `PeriodCalendarPopover.tsx` | 285 | 기간 달력 팝오버 |
| `gridFlow.ts` | 283 | 기준 격자 후주입 흐름 |
| `transferSource.ts` | 258 | 전송 op 바인딩 |
| `uploadSource.ts` | 238 | 업로드 op 바인딩 |
| `GridUploadBlock.tsx` · `GridAttachEntry.tsx` | 181 · 64 | 격자 파일 업로드·부착 |
| `UnfinishedUploads.tsx` | 109 | 끊긴 전송 목록 배너 |
| `xhrPut.ts` | 65 | S3 PUT (XHR · 진행률 · 스톨 감지) |
| `PreviewExpandOverlay.tsx` | 62 | 확장보기 |
| 그 외 | — | `axisDict` `backoff` `dropTree` `escLayer` `normalizeName` `openUpload` `pendingStore` `periodParts` `previewResult` `previewSource` `projectSource` `scheduler` `types` `upload.css` |

### 1-2 단계 구조 (코드에 존재)

- 등록 단계 = **3단**. `RegisterArea.tsx:53` — `export type Step = 1 | 2 | 3;`
- 라벨 원본 = `RegisterArea.tsx:76` `STEP_LABELS`
- ①분류(분류·유형·가공 단계) `RegisterArea.tsx:123` / ②소속 프로젝트 / ③연결(계보 부모 ＋ 원천 표기 ＋ 연관 프로젝트·논문) `RegisterArea.tsx:834`
- 규칙 축자 인용 — `RegisterArea.tsx:8-9`
  > - **한 번에 한 단계만 보인다.** 나머지 둘은 화면에서 빠진다.
  > - **막지 않는다** — 앞 단계를 채웠는지 검사하지 않는다.
- 「확인」 별도 단계 **없음** — 단계는 3개이고 4번째 확인 단계는 코드에 없다(`RegisterArea.tsx:53`).
- ③ 의 알맹이는 슬롯 주입 — `UploadModal.tsx:661-662` 이 `LineageStep` 을 기본 렌더러로 넘긴다.
- 장면 구분 = 파일 선택 전 → 전송·분석 → 등록 입력. 근거 = `dev-package/reports/upload-layout-preview/verification.md:10`(장면 캡처 `01-empty.png`~`07-connections.png`).

### 1-3 다중 파일 (코드에 존재)

- 드롭 순간 **확장자 한 종류만 통과** — `FileDropCard.tsx:145` 주석 축자
  > 놓는 순간 확장자를 세어 **한 종류만** 위로 올린다 (PRD-32 · `VAL-002`).
- 「가장 먼저 놓인 파일의 확장자만 남긴다」 — `FileDropCard.tsx:75-76`
- 등록 가능 확장자와 미리보기 가능 확장자는 **분리** — `FileDropCard.tsx:41` / `:43` / `:44`
  - 등록: `어떤 포맷이든 올려요 · 같은 확장자면 여러 개를 한 데이터셋으로 묶어요`
  - 지도 미리보기: `*.nc *.nc4 *.tif *.tiff *.hdf *.h5 *.hdf5 *.bin *.bin.gz *.npy *.grib *.grib2 *.grb *.grb2`
  - 미지원 안내: `이 확장자는 지도로 못 그려요` — **막지 않고 문구만 다르다**(`FileDropCard.tsx:210` 주석).
- 폴더 업로드 트리 = `dropTree.ts`(71행) · 경로는 원장 메타 `relative_path`(§3 참조).

### 1-4 진행·오류·취소·재개 (코드에 존재)

- 전송 진행 막대 = `UploadModal.tsx:1212-1214` `<progress data-testid="up-transfer-progress">`
- 진행률 정수 반올림 — `UploadModal.tsx:378` 주석 축자
  > 정수 퍼센트가 바뀔 때만 상태를 옮긴다 — `xhr.upload.onprogress` 는 초당 수십 번 온다.
- PUT 은 **XHR 고정** — `xhrPut.ts:1-4` 축자
  > S3 로 나가는 PUT — 반드시 XMLHttpRequest. fetch 는 업로드 진행 이벤트가 없다. Blob 을 그대로 보낸다 … 타임아웃 대신 스톨 감지(30초간 loaded 정지 → abort)
- 실패 종류 3 = `xhrPut.ts:6` `'network' | 'stall' | 'aborted'`
- 403 도 그대로 반환, 재발급 판단은 호출자 — `xhrPut.ts:23`
- 오류 표시 3자리 = `up-status-error`(`UploadModal.tsx:1265`) · `up-intake-error`(`:1293`) · `grid-attach-error`(`:1418`)
- 취소 = `abortTransfer` 호출 `UploadModal.tsx:1182`
- 재개 = 배너 항목 버튼 `up-resume-{uploadId}`(`UploadModal.tsx:1166`) · 실패 자동 무장 `resumeFromRef.current = 'failure'`(`:435-436`) · 요청에 `resumeUploadId` 적재(`:383`)
- 끊긴 전송 목록의 출처 = 서버 op — `UnfinishedUploads.tsx:6` 축자
  > 이 끊긴 것 — 전송 원장(72시간). 서버가 목록으로 준다(`listIncompleteUploadTransfers`).
- 대표 그림 저장 실패 분기 = `UploadModal.tsx:106-110` `representativeFailure` · `retryBlocked`

### 1-5 계보 AI 제안 · LV-2 (코드에 존재)

- **자동 호출은 현재 코드에 없다.** `LineageStep.tsx:146` 주석 축자
  > 제안 조회 — **버튼이 부른다.** 마운트·`uploadId` 변화로는 돌지 않는다(완료 정의 ⓐ·ⓔ).
- 버튼 자리 = `LineageStep.tsx:617` 축자
  > `LV-2` — **부르는 주체가 사용자다.** 호출은 업로드 1건당 1회가 아니라 누른 횟수만큼.
- 파일 머리 규약 = `LineageStep.tsx:5` `[모두 승인] 이 없다` · `:11` `AI 제안은 사용자가 눌러 받는 보조다 (PLAN-SoT §9 〈197〉·〈203〉 · LV-2)`
- 확신도 = enum 칩 · 숫자 없음 — `LineageStep.tsx:96-97` 주석 `확신도에 퍼센트가 없다 (common.json#AiConfidence)`
- ⚠ **`CLAUDE.md` 상단 표는 「`LineageStep.tsx:90` 이 업로드 1건당 1회 자동 조회를 걸고 있다」로 적는다.** 실물 `LineageStep.tsx:90` 은 `ConfidenceChip` 선언 구역이고 자동 조회는 없다 — **`CLAUDE.md` 기재가 코드보다 낡았다**(grill 대상).
- 「기록 없음」 체크박스 2성질 = `LineageStep.tsx:80-86` · 확정 부모 ≥1 → 비활성 ＋ 사유 · 자기 Lv0 → 미표시

### 1-6 `frontend/audit-upload.tsx` (코드에 존재)

- 42행. **로컬 시각 검수 전용 진입점** — `audit-upload.tsx:2` 축자
  > 로컬 시각 검수 전용 진입점. 실제 네트워크·저장 API를 사용하지 않는다.
- 구성 = `MemoryRouter` ＋ 모의 `UploadSources`(`create`/`status`/`register`) ＋ 모의 `preview` 소스 ＋ 모의 `CurrentAccount`.
- `register` 는 의도적 throw — `audit-upload.tsx:28` `throw new Error('시각 검수 전용: 저장하지 않습니다')`
- 쿼리 파라미터 2 = `theme`(light/dark) · `scene=detail`(상세 화면으로 전환).
- **제품 번들 진입점 아님** — 진입점은 `frontend/index.html` ＋ `src/main.tsx`. 현재 워킹트리에서 수정 상태(`git status` M).

### 1-7 시험 (테스트 존재)

`frontend/test/` 중 업로드 관련 — `upload.test.tsx` · `upload-transfer.test.tsx` · `upload-droptree.test.tsx` · `upload-progress-recovery.test.tsx` · `upload-preview-poll-20260903.test.tsx` · `multipart-upload-progress.test.ts` · `unfinished-uploads.test.tsx` · `grid-preview.test.tsx` · `preview-slot-4x3.test.tsx` · `preview-pick-and-fallback.test.tsx` · `lineage-unknown-20260907.test.tsx` · `lineage-fix-20260907.test.tsx` · `lineage-continuation.test.tsx` · `lineage-graph.test.tsx`.
**이 회차에 실행하지 않았다 — 통과 여부 `[미확인]`.**

---

## 2 다운로드

### 2-1 진입점 3자리 (코드에 존재)

| 자리 | 파일:행 | 대상 |
|---|---|---|
| 상세 「어떻게 쓰였나 · 가져가기」 | `frontend/src/components/detail/UsageSection.tsx:97` `data-testid="detail-download"` | 데이터셋 전체(묶음) |
| 상세 파일 목록 건별 | `frontend/src/components/detail/FileList.tsx:112-119` `dt-file-download-{fileId}` | 파일 1건 |
| 카탈로그 표 빠른 작업 | `frontend/src/components/catalog/CatalogTable.tsx:226-227` | 데이터셋 1행 |

- 표시 조건 = `props.detail.actions.canDownload && props.downloadHidden !== true` (`UsageSection.tsx:92`) — 서버가 건별 판정(`FileList.tsx:8` `actions.canDownload` · `ActionGate` · P-7).
- 편집 중 숨김 = `UsageSection.tsx:45-49` · `DatasetEditForm.tsx:209-210`(취소/저장이 그 자리를 받는다).
- 접근 출처 한 줄은 **다운로드 권한과 무관하게 보인다** — `UsageSection.tsx:84-85`.

### 2-2 200 티켓 방식 (코드에 존재)

- 티켓 도입 근거 = `frontend/src/api/download.ts:11-16` 축자
  > ⭑ **⟨개정 병합 창 8-a · `〈339〉`-(다) · Ted 판정 `〈334〉`-㉳-⑥⟩ 응답이 302 가 아니라 티켓이다.** … 병합된 계약 `fe-core.yaml` 의 `downloadDataset` 은 **200 ＋ `DownloadTicket`** 이다: `fetch` 는 302 를 따라갈 때 자격을 잃고 `<a href>` 는 Bearer 를 못 싣는다 — 그래서 티켓이다.
- **이력은 티켓 발급 시점에 쌓인다** (바이트 시점 아님) — `api/download.ts:16` · `components/detail/types.ts:70`.
- 소비 경로 **2벌** — `api/download.ts:18-20` 축자
  > ⚠ **바이트 한 바퀴는 여기서도 `fetch` 다** … `detail/download.ts` 의 `startDownload` 는 같은 일을 **내비게이션**으로 하고, 이 자리는 **blob 저장**으로 한다. 둘 다 티켓을 입력으로 받으므로 계약은 하나다.
- 저장 이름 = 티켓 `fileName` → 없으면 `Content-Disposition` → 없으면 데이터셋 ID. 지어내지 않음 — `api/download.ts:21-22` · `fileNameFrom()` `:27-39`.
- 티켓 URL 2형태 — `detail/download.ts:4` 축자
  > 티켓 URL 은 둘 중 하나다 — 저장 모드 local 과 묶음(zip)은 이 seam 의 상대 경로(`/downloads/{ticket}`),
- `<a download>` 생성·클릭 = `detail/download.ts:20-27`.
- 티켓 op 선택 = `detail/fileSource.ts:47-52` — `fileId` 있으면 `/datasets/{id}/files/{fileId}/download`, 없으면 `/datasets/{id}/download`.

### 2-3 묶음(bulk) (코드에 존재)

- 데이터셋 단위 zip 묶음 **존재** — `detail/types.ts:70` 축자
  > `fileId` 가 있으면 파일 하나, 없으면 묶음(zip) 티켓. 이 응답 시점에 다운로드 이력이 쌓인다.
- 서버측 zip 스트리밍 = `services/core-api/src/colab_core/app/routes/download.py:214` `_bundle` · `:280` `zip_stream` · `:225` `entry_names`.
- **부분 다운로드 없음** — `UsageSection.tsx:10` 축자
  > ⑵ 다운로드 (`§8` 다운로드 행) — 원본 파일 그대로, 부분 다운로드 없음.
- **여러 데이터셋 선택 일괄 다운로드는 코드에서 확인되지 않음** — 카탈로그는 행 1건 단위(`CatalogTable.tsx:226`). `[미확인]`(부재 증명은 하지 않았다).

### 2-4 시험 (테스트 존재)

`frontend/test/catalog-download.test.tsx` · `services/core-api/tests/test_download.py`. 실행 `[미확인]`.

---

## 3 core-api 전송 계층

### 3-1 업로드 전송 op 10 (코드에 존재 · `services/core-api/src/colab_core/app/routes/upload_transfers.py`)

| op name | 메서드·경로 | 행 |
|---|---|---|
| `initiateUploadTransfer` | POST `/uploads/transfers` (201) | `:136-137` |
| `listIncompleteUploadTransfers` | GET `/uploads/transfers/incomplete` | `:242-243` |
| `getUploadTransfer` | GET `/uploads/transfers/{uploadId}` | `:261-262` |
| `issueUploadUrls` | POST `/uploads/transfers/{uploadId}/put-urls` | `:290-291` |
| (multipart init) | POST `/uploads/transfers/{uploadId}/files/{fileId}/multipart` | `:320-322` |
| (part urls) | POST `/uploads/transfers/{uploadId}/files/{fileId}/part-urls` | `:339-341` |
| (file complete) | POST `/uploads/transfers/{uploadId}/files/{fileId}/complete` | `:372-374` |
| (early preview) | POST `/uploads/transfers/{uploadId}/early-preview` | `:408-410` |
| `completeUploadTransfer` | POST `/uploads/transfers/{uploadId}/complete` | `:456-458` |
| `abortUploadTransfer` | DELETE `/uploads/transfers/{uploadId}` | `:493-495` |

상수 (`upload_transfers.py:40-46`) — `MAX_GRID_FILES = 2`(〈58〉 기준 격자 0~2건) · `MAX_PART_URL_BATCH = 16` · `MAX_URL_BATCH = 50` · `SINGLE_PUT_MAX = 16 MiB`(미만은 단일 PUT) · `MIN_PART = 8 MiB` · `MAX_PARTS = 10_000`.
파트 크기 산식 = `choose_part_size()` `:49-55` — 8 MiB 에서 배로 키워 파트 수 상한 이하로.

### 3-2 다운로드 op 3 (코드에 존재 · `services/core-api/src/colab_core/app/routes/download.py`)

| op name | 경로 | 행 |
|---|---|---|
| `downloadDataset` | GET `/datasets/{datasetId}/download` | `:135-136` |
| `downloadDatasetFile` | GET `/datasets/{datasetId}/files/{fileId}/download` | `:147-148` |
| `getDownloadBytes` | GET `/downloads/{ticket}` | `:176-177` |

내부 = `_signer`(`:70` `DownloadTicketSigner`) · `_accessible_dataset`(`:82`) · `_issue`(`:95`) · `_bytes_url`(`:129`) · `_claims`(`:165`) · `_single`(`:202` StreamingResponse) · `_bundle`(`:214`).
서명·클레임 커널 = `services/core-api/src/colab_core/kernel/download_ticket.py`.

### 3-3 저장 계층 (코드에 존재)

`kernel/s3.py`(S3Client) · `kernel/sigv4.py`(자작 서명) · `kernel/storage_backends.py` · `kernel/storage_layout.py` · `ports/storage.py`(저장 Port) · `app/storage_maintenance.py` ＋ `app/storage_maintenance_cli.py` · `domains/d3_download.py` (모두 `services/core-api/src/colab_core/` 아래).

### 3-4 운영 규칙 — `.claude/rules/s3-upload.md` (28행 전문 확인)

각 1줄 요약(요지, 문면은 해당 행):

1. 저장 모드 분기점은 `ports/storage.py` 와 `routes/upload_transfers.py` 둘뿐이고 s3 모드는 `COLAB_CORE_STORAGE_MODE=s3` ＋ 버킷·리전, 반쪽 설정은 기동 거부 (`:14-15`).
2. SigV4 는 표준 라이브러리 자작(`kernel/sigv4.py`) · boto3 없음 · 본문 있으면 `content-type: application/xml` 명시 (`:16-17`).
3. **에뮬레이터(MinIO 등) 검증 금지** — 관대한 통과가 진짜 S3 의 403 을 숨긴다 (`:18`).
4. **파트의 정본은 S3 ListParts** — 재개·완료 검증에서 클라이언트 자기 보고 불신 (`:19`).
5. **완결이 곧 접수** — `completeUploadTransfer` 전에는 `d5_upload` 도 `upload.accepted` 도 없다 (`:20`).
6. 만료 전송 정리는 원장이 아는 것만 · 버킷 루트 스캔 금지 · 백스톱은 라이프사이클 abort-7d (`:21-22`).
7. 폴더 업로드 경로는 저장 키가 아니라 원장 메타 `relative_path`(d5→d3 승계) · 키 규약 불변 (`:23`).
8. **다운로드는 302 가 아니라 200 티켓** · 바이트 op 은 `security: []` 지만 티켓 클레임으로 `apply_scope` → RLS 재판정 · `session_secret` 없으면 500 `DOWNLOAD_UNAVAILABLE` · 조용한 폴백 없음 (`:24-26`).
9. AWS 검증은 콘솔이 아니라 `services/core-api` 의 `ops/s3_doctor.py` / `ops/s3_smoke.py` (`:27`).
10. 시크릿 키는 채팅·커밋에 넣지 않는다 (`:28`).

### 3-5 운영 정본 `dev-package/S3.md` 절 구성

`:1` 표제 · `:6` §0 구조 한 장 · `:17` §1 dev·prod 벌 신설 런북 · `:40` §2 운영 진단 도구(`services/core-api/ops/`, 배포 이미지 미포함) · `:51` §3 s3 모드 동작 요약 · `:74` §4 열린 갭.

§4 열린 갭 6건(요지 1줄씩) —
- worker·viz 가 로컬 경로만 읽어 s3 모드에선 포맷 감지·축 판별·미리보기 미동작 (= `V-4`) (`S3.md:76-79`).
- s3 모드 묶음 다운로드가 core-api 트래픽을 만든다 · 대용량 실측(현 166 MB)은 I-D 몫 (`:81`).
- 본체 전송 진행률 막대는 섰고 **문구만** 정본 개정 대기 (`:83-84`).
- S3 고아 바이트를 치우는 주체 없음 · 09-02 실측 3건 26,579,847 B 손 삭제 · 판별식 = `d3_dataset`·`d5_upload`·열린 전송 셋 다 없어야 고아 · **별도 WU** (`:85-87`).
- 완결된 전송 원장 행 미삭제 — 만료 스윕이 `completed_at IS NULL` 만 고름(`〈342〉`-㊂-⑶) (`:88-89`).
- 「상태 2 목록 op 이 없다 — 브라우저 저장으로 우회」 (`:90`).

⚠ **드리프트 후보** — 마지막 항목은 코드와 어긋난다. `upload_transfers.py:242-243` 에 `listIncompleteUploadTransfers` 가 존재하고 `UnfinishedUploads.tsx:40` 이 그것을 호출한다. `S3.md` 최종 수정 커밋 = `c6f5e00c`(PR #1 병합). **grill 대상.**

### 3-6 시험 (테스트 존재 · `services/core-api/tests/`)

`test_upload_transfers.py` · `test_uploads.py` · `test_upload_streaming.py` · `test_upload_grid_status.py` · `test_upload_ledger_hidden.py` · `test_download.py` · `test_s3client.py` · `test_storage_backends.py` · `test_storage_layout.py` · `test_storage_maintenance.py` · `test_e2e_s3_real.py`. 실행 `[미확인]`.

---

## 4 후처리(worker)

### 4-1 이벤트 계약 10종 — `contracts/events/core-pipeline.json`

표제 축자 (`:4`)
> "core-api ↔ pipeline-worker 이벤트 7종 ＋ pipeline-worker → viz-render 3종"

| # | type | 발행 | 소비 | 행 |
|---|---|---|---|---|
| ① | `upload.accepted` | core-api(outbox) | pipeline-worker | `:230-241` |
| ② | `file.format-detected` | pipeline-worker | core-api | `:252-253` |
| ③ | `file.header-parsed` | pipeline-worker | core-api | `:265` |
| ④ | `file.crs-normalized` | pipeline-worker | core-api | `:277` |
| ⑤ | `preview.cog-built` | pipeline-worker | core-api | `:284-289` |
| ⑥ | `upload.ready` | pipeline-worker | core-api | `:299-301` |
| ⑦ | `upload.failed` | pipeline-worker | core-api | `:311-313` |
| ⑧ | `preview.backend-rerun` | pipeline-worker(D5) | **viz-render(D7)** | `:333-335` |
| ⑨ | `preview.grid-changed` | pipeline-worker(D5) | viz-render(D7) | `:345-347` |
| ⑩ | `preview.file-added` | pipeline-worker(D5) | viz-render(D7) | `:357-359` |

봉투 = `contracts/events/envelope.json`. ⑧⑨⑩ 의 payload 는 공통 `PreviewStalePayload`(`:318`) — 담는 것은 `trigger` 하나뿐이고 `datasetId`·지울 경로·키를 싣지 않는다(설명 요지: 이벤트는 사실이고 명령이 아니다).

⑧ 의 뜻 축자 (`:332`)
> 뜻 = 「미리보기 뒷단(헤더 파싱·좌표계 통일·COG)이 **이미 준비를 마친 업로드에** 다시 돌았다」. ⚠ 첫 접수 처리는 이 사건이 아니다

### 4-2 업로드 완료 후 순서 (코드·계약 근거)

`completeUploadTransfer`(= 접수, `.claude/rules/s3-upload.md:20`) → `upload.accepted` ① 발행 → worker 가 ②③④⑤ 순으로 판별·파싱·좌표계·COG → ⑥ `upload.ready` 또는 ⑦ `upload.failed`.
**후속 무효화**는 ⑧⑨⑩ 로 viz-render 에 직접 간다.

### 4-3 시험 (테스트 존재 · `services/pipeline-worker/tests/` 42+ 파일)

업로드 직결 = `test_events.py` · `test_pipeline.py` · `test_stage1_worker.py` · `test_grid_only_upload.py` · `test_preview_stale_triggers.py` · `test_renderable.py` · `test_outbox_db.py` · `test_relay_redelivery.py` · `test_reaper_skips_processing.py` · `test_s3_kernel_mirror.py` · `test_e2e_real.py` · `test_format_declaration_parity.py`. 실행 `[미확인]`.

---

## 5 대장 항목표

기준 = `dev-package/work-items.yaml` · `yaml.safe_load` 후 `id` 또는 `name` 이 `업로드|upload|다운로드|download|multipart|S3|격자|grid` 에 매치. **계수 기준 명시: id+name 만 검색, `completion_def`·`note` 본문은 미검색.**

**매치 18 / 전체 180.**

| id | name(≤60자) | status | stage |
|---|---|---|---|
| `IS3` | staging 백업 체계 | done | stage1 |
| `ST-1` | 파일 저장처 — 원본 내려받기 경로(`downloadDataset` 501 `NOT_IMPLEMENTED_N…` | done | stage2 |
| `P2` | 업로드 전체화면 모달(S-04) · 계보 확정 ＋ 미리보기 최소 렌더 경로 · S-08 | done | stage1 |
| `S3` | 실데이터 5종 E2E(NetCDF·Binary·HDF4·GeoTIFF·NumPy) | done | stage2 |
| `2단-격자전용-워커제외` | 격자 전용 업로드를 워커 처리에서 제외 (`§10.3` 2단) | done | stage2 |
| `2단-격자전용-실패3건-처분` | 실패로 굳은 격자 전용 업로드 3건의 처분 (`〈120〉` 3건) | **deferred** | stage2 |
| `Q-D` | 데이터셋 상세 섹션3 — 활용 프로젝트 · 다운로드 · 파일 목록 · 접근 요청 | done | stage1 |
| `BF-4` | 미리보기 이름표 · 범례 변수명 · 원본 격자 캡션 | done | stage1 |
| `BF-10` | 바탕지도 대안 — 격자선·눈금 옵션 (POL-021 준수) | **deferred** | stage1 |
| `U-1` | 업로드 S3 직행 + 중단 재개 | done | stage1 |
| `U-2` | S3 고아 바이트 정리 | **partial** | stage1 |
| `F-3` | 파일 관리 — 목록·폴더 구조·다운로드·본체 변경 | done | stage1 |
| `I-D` | dev 환경(AWS · s3 모드) 신설 | done | stage1 |
| `V-4` | worker·viz S3 읽기 | done | stage1 |
| `WU-A3R` | 상세 편집 각주 2 — 편집 중 다운로드 숨김 ＋ 저장 후 칩 재동기 | done | stage2 |
| `WU-C1` | 미리보기 자리 선점 4:3 틀 (업로드 장면2＋상세) | done | stage2 |
| `WU-C11` | CSS 잔여 — .lvl-3 · .lin--none 대비 · .dt-gridact 음수 · 여백 컨테이너 | done | stage2 |
| `WU-UPV-20260909` | HTML 기준 업로드·상세 화면 재구성과 포맷별 미리보기·진행 표시 완성 | done | stage2 |

⚠ **열린 3건** = `2단-격자전용-실패3건-처분`(deferred) · `BF-10`(deferred) · `U-2`(partial).
⚠ `V-4` 는 대장 `done` 이지만 `dev-package/S3.md:76-79` 는 같은 항목을 「열린 갭 · 완료 정의 미작성」으로 적는다 — **문서 간 어긋남, grill 대상.** 어느 쪽이 최신인지 `[미확인]`.
⚠ `U-2`(partial) 와 `S3.md:85-87`(고아 바이트 주체 없음 · 별도 WU)는 같은 결함을 가리킨다 — 일치.

---

## 6 intent 대조표

### 6-1 `dev-package/intent/2026-09-09-upload-layout-preview.md`

메타 (`:2`) — 발의자 Ted · 작성 2026-09-09 · **승인 2026-09-09**(원문 `"엉 그렇게해"`).

`## 원한 결과 (proposed outcome)` 10건 (`:10-19`) 요지와 증거 판정:

| # | 요지(원문 압축) | 판정 | 증거 |
|---|---|---|---|
| 1 | 기획 HTML 의 모달·열·여백·카드·단계·파일 배지·행동 줄·상세 순서를 비교 기준으로 | **완료 주장 있음** | `dev-package/reports/upload-layout-preview/verification.md:9` — 620px 모달·장면·상세 순서 실화면 확인, 근거 `policy-map.md`·`screens/` |
| 2 | 파일 선택 전 → 전송·분석 → 등록 입력 장면 분리 · 좌 미리보기 / 우 입력 | **완료 주장 있음** | `verification.md:10` — `01-empty.png`~`07-connections.png` 1440×1000 |
| 3 | 저장 후 상세에 이름·파일·분류·유형·가공 단계·기간·좌표계·간격·원천·설명·변수 표 | **완료 주장 있음** | `verification.md:11` — HDF 등록·reload·편집 재조회 `journey.json` |
| 4 | 실파일 업로드→저장→계보·프로젝트→상세→편집→원본 다운로드 · 묶음 다운로드 포함 | **완료 주장 있음** | `verification.md:12` — HDF 25단계 · 원본 SHA256 일치 · ZIP 검증 |
| 5 | nc·tif·hdf·bin 포맷별 읽기·그림·표시 검증 · GRIB 제외를 성공으로 세지 않음 | **완료 주장 있음(부분 제외 명시)** | `verification.md:13` · `format-matrix.md` 7사례 · GRIB 행 = 「미리보기 명시적 제외」 |
| 6 | 업로드·확장·상세 미리보기의 좌표·경계·확대·이동·초기화 · 부분 표시 고지 | **완료 주장 있음** | `verification.md:14` — 확장보기·지도 확대·초기화·커서 위경도 · 손상 TIF 부분 실패 |
| 7 | 전송→분석→렌더→이미지 표시 진행 안내 끊김 없음 · 타이머 퍼센트 금지 | **완료 주장 있음** | `verification.md:15` · `progress-cases.md` · 코드 `frontend/src/components/upload/xhrPut.ts:1-4`(실바이트) |
| 8 | 전송100%/분석/렌더/표시 구분 · 미리보기 실패가 등록·계보·다운로드를 막지 않음 | **완료 주장 있음** | `verification.md:16` — 415/413 분기 · `frontend-sol/verification.md` |
| 9 | 느림·통신/서버/이미지/부분 실패·취소·재시도·늦은 응답에도 상태 누락 없음 | **완료 주장 있음** | `verification.md:17` — 오래된 응답 차단 회귀 · `browser/partial/journey.json` |
| 10 | 같은 창 크기 시각 대조 · 정책→rev2→구현→검증 근거 연결 | **완료 주장 있음** | `verification.md:18` — `policy-map.md` 정책 65행 · 정책 23/27/37~38 확장 |

⚠ **판정의 성격** — 위 10건은 전부 **보고서의 자기 주장**이고, 이 회차에 재측정하지 않았다. 대장 `WU-UPV-20260909` = `done`(stage2). **대장 상태를 동작 증거로 쓰지 않는다.** 재현 여부 `[미확인]`.
⚠ 보고서 자체가 한계를 명시 — `verification.md:47` 요지: GRIB 은 기존 미지원 안내·등록·원본 다운로드 검증이고 새 지도 렌더러 지원이 아니며, 별칭·모든 내부 구조를 무제한 지원한다고 주장하지 않는다.

`## 범위 밖 (명시 제외)` 4건 축자 (`:49-52`)
> - 데이터셋 목록·대시보드 등 이번 원본 밖 화면의 전면 재설계.
> - 기존 데이터 삭제, 공개·권한 정책의 임의 변경, 기존 기능의 무단 제거.
> - 다른 세션의 파일·브랜치·실행 환경 변경, 자동 배포, S3 정리·Google IdP 등 별도 후속 과제의 자동 편입.
> - 기획 검수 패널·빨간 번호·시연용 샘플·가짜 진행률을 제품 기능으로 복사하는 것.

### 6-2 `dev-package/intent/2026-09-10-preview-all-formats.md`

절 구성 = `## 사용자 요청`(`:3`) · `## 원하는 결과`(`:7`) · `## 구현 가정`(`:14`) · `## 완료 조건`(`:22`).
⚠ **스펙 L-1 템플릿 절 이름과 다르다**(`## 원한 결과`·`## 영향 범위`·`## 제약` 등 부재) — 별도 형식. grill 대상.

`## 완료 조건` 축자 3행 (`:24-26`)
> - 일곱 포맷의 단위·통합 시험과 실제 파일 렌더 커버리지 결과가 남는다.
> - GRIB 및 일반 HDF5의 업로드→변수 선택→이미지 표시 사용자 여정을 검증한다.
> - Docker 의존성 설치가 재현되고, 실행하지 못한 플랫폼 검증은 미완료로 남긴다.

증거 대조 —
- 1행(일곱 포맷) — `dev-package/reports/upload-layout-preview/format-matrix.md` 에 **8 사례 표** 존재(GeoTIFF 2파일 · GK2A NetCDF · MOD15 HDF4 · HSR bin 좌표없음 · HSR bin+격자 · NumPy+격자 · GRIB · 실TIF+손상TIF). 「일곱 포맷」과 계수 기준이 다름 — **일치 `[미확인]`**.
- 2행(GRIB·일반 HDF5 여정) — `format-matrix.md` GRIB 행은 「미리보기 명시적 제외」. 커밋 `70909105 GRIB과 HDF5 미리보기를 추가한다` 존재. **두 근거가 갈린다 — `[미확인]`**(어느 쪽이 최신 상태인지 미측정).
- 3행(Docker 의존성 재현) — **`[미확인]`**(재현 로그 미확인).

---

## 7 블로커

기준 = `dev-package/03-HANDOFF.md` `## 4. 블로커 (사람이 풀어야 할 것)`(`:325`) ~ `## 4.5`(`:361`). 업로드·다운로드 관련 추출.

| # | 요지 |
|---|---|
| **61** | **「업로드 재처리」를 부르는 운영 경로가 없다**(관찰 · 판정 필요 · `Y-1` 을 막지 않음). D5 트리거 3종은 이미 `ready` 인 업로드 재처리 때만 발행되는데(`d5_ingestion.py` `was_ready`) 워커 루프 대상 `pending_uploads` 는 `ready = false` 만이다 |
| **69** | 관측 — 자리에 산출물이 있는 데이터셋은 14 중 3 건(차단 아님) · staging 카탈로그 14건 전수 값 조회 · `available:true` 3건 |
| **40** | 실행 비트 결함이 `gates/` 밖 52개 `.sh` 에 남음(업로드 직접 아님, 배포 경로 공통) |
| **44** | staging 실물의 `403` 을 잴 시험 데이터 없음 — 권한 거부 경로(다운로드 포함) 음성 검증 공백 |
| **11** | staging admin 비밀번호가 저장소에 평문(`〈155〉`-㉳-ⓐ · 커밋 `59a9a64` · 이미 `origin/main`) — S3·DB 접근 경계 |

`#61` 이 업로드·미리보기 흐름에 직접 걸리는 유일한 열린 블로커다.
⚠ **§4 상단 주의** — 이 표만 보지 않고 `dev-package/PR-CHECKLIST.md` 를 함께 본다(`03-HANDOFF.md` §4 머리말). 이 회차에 PR-CHECKLIST 는 열지 않았다 — `[미확인]`.

---

## 8 기획 정본 위치

`planning/README.md` 축자 (`:3-4`)
> **이 폴더에 기획 문서를 복사해 두지 않는다.** 사본을 만들면 두 개가 갈라진다.
> 정본은 이 레포 밖 **같은 작업공간의 형제 폴더**에 있고, 이 문서는 그 위치와 상태만 가리킨다.

- 정본 루트 = `<작업공간>/40 COLAB-기획/` (`<작업공간>` = 이 레포의 부모 폴더 · `planning/README.md:6-7`).
- 2026-09-05 재편 — 패키지가 `00_기획원본/` 아래로 이동. 옛↔새 경로 대응표는 `<작업공간>/40 COLAB-기획/README.md` §「경로 대응표」 (`planning/README.md:13-16`).
- 업로드 에픽 = `00_기획원본/Co-Lab_ver2_1차마일스톤_목업패키지_260818_이태헌/에픽/E-04_업로드와_계보_확정`(documents · mockups · package) · 상세 = `E-03_데이터셋_상세` (`planning/README.md` 트리).

09-09 intent `## 참조` 가 지목한 기획 HTML (`dev-package/intent/2026-09-09-upload-layout-preview.md:61-62`) —
- rev2(화면 기준) = `40 COLAB-기획/10_적용전/업로드_계보_260905_rev2_이태헌.html` — 「프로젝트 형제 기획 폴더, 무수정」
- rev1(번호별 정책 1~65 내장 JSON) = `40 COLAB-기획/10_적용전/업로드_계보_260826_rev1_이태헌.html` — 특히 6 진행 · 8 미리보기 · 9 확장보기 · 49 행동 줄 · 51~65 상세
- 과거 결정서 = `40 COLAB-기획/20_검토/260906_업로드계보rev2/결정서_Ted_260906.md` (`:64`)

⚠ 이 회차에 `40 COLAB-기획/` 는 **열지 않았다**(읽기 전용 폴더 · 경로만 기록). 파일 실재 여부 `[미확인]`.
⚠ `10_적용전` 적용 상태의 원본은 `dev-package/prd/planning-applied.yaml`(`.claude/rules/colab-rules.md §7`) — 이 회차 미조회 `[미확인]`.

---

## 9 데이터 함정

`dev-package/DATA-REFERENCE.md` `## 0. 반복하지 말 것 — 이미 저지른 실수`(`:13`).

⚠ **계수 불일치 먼저** — `CLAUDE.md §1` 은 「이미 저지른 실수 **7건**」이라 적지만, 실물 표는 **`M-1`~`M-9`** 이고 **`M-8` 이 2행으로 중복**(각각 다른 내용)이라 행 수는 **10**이다. 본문 하단 요약은 「**아홉** 중 여덟이 「에러 없이 그럴듯한 값」」으로 적는다. **셋이 서로 다르다 — grill 대상.**

| # | 한 줄 |
|---|---|
| M-1 | 확장자로 싸잡아 분류 — `.npy` 전량 제외가 좌표 기준 파일 14건을 함께 삼킴(`〈57〉` 정정) |
| M-2 | 한 테이블만 보고 「없다」 — 주제 열이 `d3_dataset_description` 에 있었음 |
| M-3 | 선례를 「없다」 단정 — PoC 처리 세대가 둘(`backend/app/services/processors/` · `viz-service/app/decoders/`) |
| M-4 (2회) | 측정 안 한 것을 측정된 것처럼 인용 — KWRA 51건 미측정(재측정 COG 0건) · 재발 1회(`RenderTarget.uploadId` 인용만 보고 경보) |
| M-5 | 측정값과 해석을 같은 확신으로 기재 — 틀은 잠정으로, 증거는 확정으로 갈라 적을 것 |
| M-6 | 문서·주석을 실물 확인 없이 인용 — `deploy.sh` 주석은 커밋 산출, 실제는 워킹트리를 빌드 |
| M-7 | 행 번호를 눈으로 세어 옮겨 적으며 틀림 — `cat -n` 으로 확인 |
| M-8(1) | §1 표를 실물 전체 목록과 대조하지 않음 — `rdr_500m_latlon.nc` 행 누락 |
| M-8(2) | 포맷 명세 PDF 를 실물 바이트인 양 `✅확인` 등급 — HSR 헤더 36~63 B 실측 전부 0 · 재현 시 위도 0.053°(약 5.9 km) 오차 |
| M-9 | 경계(RLS) 걸린 조회의 0 을 「데이터 없다」로 읽음 — 관리자 롤로는 `d3_dataset` 13 · `d3_file` 130 · `d5_upload` 19 |

### 9-1 업로드 파일 종류 · 기준 격자 파일 (업로드 직결)

- 격자 파일 정의 — `DATA-REFERENCE.md:62` 축자
  > **⚠ 이 파일들은 `기준 격자 파일` 이다** — `d3_file.kind` 의 두 번째 값(`본체` | `기준 격자 파일`). **데이터셋당 2건까지**(위도·경도 한 쌍), **등록 뒤 후주입 가능**(`〈58〉`).
  - 코드 일치 확인 — `services/core-api/src/colab_core/app/routes/upload_transfers.py:40` `MAX_GRID_FILES = 2  # 〈58〉`
- 격자 출처는 포맷마다 다름 — `DATA-REFERENCE.md:40` 요지: 격자가 파일 안에 없는 포맷은 **바이너리(HSR) 하나**. 나머지 4종(nc·tif·hdf·grib)은 내부 정보로 계산되지만 동봉 배열 사용이 싸고 안전. §1.1(`:66`) 축자 「후주입을 모든 포맷에 요구하면 안 된다. 그러나 HSR 에는 요구해야 한다.」
- 후주입·교체는 정상 동작(`:57` `〈59〉`) · 그때 계보는 접지 않음(`:58` `〈60〉`) · `d8_activity` 에 `좌표계·격자 변경` 기록(`:59`) · `자동으로 읽은 정보`(좌표계·격자) 재계산(`:60`).
- 좌표 지어내기 금지 — `:84` 요지: PoC 는 HSR 위경도를 dummy `linspace` 로 합성하고 좌표를 못 찾으면 임의 격자로 「성공」 반환(4곳 `DR-9`). **못 읽으면 `[미상]` 이고 실패다.**
- 원천 격자 두 판 충돌 — `:55` : `rdr_500m_latlon.nc` 와 `Lat_HSR.npy`/`Lon_HSR.npy` 형상 동일 · 값 상이(lat min `30.102751` ↔ `30.107119` 등 약 0.004~0.007°). **어느 쪽이 정본인지 문서도 답하지 않음 — 열린 질문.**
- HSR 헤더 `num_data` 불신 — `:116` : 헤더는 `num_data=3` 이라 선언하는데 실파일 13,282,434 B = 1블록치. 파서는 3도 1도 가정하지 말고 `num_data` 를 읽되 크기와 대조.
- NULL 이 세 값 — `:122` §2.1 · `값 <= -20000` 으로 자르면 표시 최소값을 결측화(`:130`). **fill 은 정확일치로 판정.**
- 확장자 거짓말 3회 — `:150` 「세 번 다 확장자가 거짓말을 했다」(HDF 폴더 이름이 HDF5 인데 실구조 HDF4 등, `format-matrix.md` 「지원 범위」와 일치).
- COG 판정 기준 — `:167` : 내부 타일(태그 `322`/`323`) **그리고** 오버뷰(IFD 2개 이상). 「타일링 있으면 COG」로 판정하면 tif 62건 중 16건 오인(`:178`).
- v2 에 타일링 선례 없음 — `:203` : PoC 는 `titiler` 설치 후 import 0건, 프론트는 Leaflet `ImageOverlay` 단일 PNG.

---

## 10 최근 커밋

`git log --oneline -25` · 경로 = `frontend/src/components/upload` ＋ `services/core-api/src/colab_core/app/routes/upload_transfers.py` ＋ `.../routes/download.py` ＋ `frontend/src/components/detail/download.ts` ＋ `frontend/src/api/download.ts`. 상위 10건:

| sha | 제목 |
|---|---|
| `95773e0a` | 저장소 적용을 별도 승인 명령으로 격리한다 |
| `81f06612` | 저장소 회수를 정확한 승인 목록에 묶는다 |
| `5d9ab3cf` | 격자 편의 기능과 저장소 회수를 Stage 1·2 배포 단위로 통합한다 |
| `09e2b9b2` | fix: 멀티파트 업로드 진행률 전달 |
| `a8541b7c` | fix: 업로드 진행 상태를 명확히 표시 |
| `70909105` | GRIB과 HDF5 미리보기를 추가한다 |
| `6d1107cd` | fix upload recovery and lineage date filters |
| `71e6592f` | 생성 중 숨김 표시 규칙 보완 |
| `0039257c` | 생성 실패 뒤 업로드 설정 보존 |
| `a17e97e4` | 데이터셋 생성 중 등록 입력 잠금 |

11~25번 = `0994a152` 대표 그림 저장 복구 경합 · `4cd30d72` 대표 그림·계보 후보 UI · `02d27a38` Improve upload layout … · `88551026` 파일 변경 초기화·진행 표시 · `fa170ed9` 업로드 초기 화면·진행 조회 복구 · `2c4d335f` WU-C11 · `0d2f79fb` WU-C5 · `c351b71d` WU-C8 · `bb4f62c0` WU-C4 · `e55576c7`·`7e627129` WU-C3 · `e235f456` WU-C1 · `8db3deb4` WU-B11 · `9c92294d` WU-B8 · `7e69a596` WU-B6.

⚠ **워킹트리 미커밋** — `git status` 기준 `frontend/audit-upload.tsx` · `frontend/src/components/upload/upload.css` · `frontend/src/main.tsx` 등 다수 M. 커밋 로그가 현재 파일 상태와 다르다.

---

## 11 미확인 목록

1. 프런트·core-api·worker 시험의 **실행 결과**. 파일 존재만 확인, 이 회차 게이트 미실행 — 전건 `[미확인]`.
2. `V-4` 의 실제 상태 — 대장 `done` ↔ `dev-package/S3.md:76-79` 「열린 갭 · 완료 정의 미작성」. 어느 쪽이 최신인지 `[미확인]`.
3. `S3.md:90` 「상태 2 목록 op 이 없다」 ↔ 코드 `listIncompleteUploadTransfers` 실재. 문서가 낡았다는 것이 `[추론]`이고, 두 op 이 같은 요구를 채우는지 `[미확인]`.
4. `CLAUDE.md` 의 「`LineageStep.tsx:90` 자동 조회」 ↔ 코드 `frontend/src/components/lineage/LineageStep.tsx:146` 「버튼이 부른다」. `LV-2` 대장 stage 값 `[미확인]`(§5 검색 패턴에 id 매치 없음).
5. GRIB 미리보기 현재 상태 — 커밋 `70909105`(추가) ↔ `format-matrix.md`(명시적 제외). `[미확인]`.
6. 09-10 intent 「일곱 포맷」의 포맷 목록 정의. `format-matrix.md` 는 8 사례이고 포맷 수와 사례 수 기준이 다름 `[미확인]`.
7. 여러 데이터셋 선택 **일괄 다운로드** 기능의 부재 — 코드에서 발견하지 못함이고 부재 증명 아님 `[미확인]`.
8. `dev-package/PR-CHECKLIST.md` 내용 — §4 머리말이 함께 보라고 지시하나 미조회 `[미확인]`.
9. `40 COLAB-기획/10_적용전/` 의 rev1·rev2 HTML 실재 여부 — 읽기 전용 폴더 미개봉 `[미확인]`.
10. `dev-package/prd/planning-applied.yaml` 의 업로드 라운드 적용 상태 `[미확인]`.
11. 09-09 intent `## 참조:68-69` 가 가리키는 `dev-package/prd/specs/R-UPLOAD-PREVIEW.md`·`dev-package/prd/rounds/R-UPLOAD-PREVIEW.md` 실재 여부 `[미확인]`.
12. dev 배포 sha 와 현재 워킹트리 코드의 일치 여부 `[미확인]`.

---

## 후속 항목 (이 에이전트가 고치지 않음)

- `CLAUDE.md` 상단 표의 `LineageStep.tsx:90` 자동 조회 기재 → 코드와 대조해 정정 필요(§11-4).
- `CLAUDE.md §1` 「이미 저지른 실수 7건」 → 실물 `M-1`~`M-9`(행 10) 와 계수 불일치(§9).
- `dev-package/S3.md:90` 「상태 2 목록 op 이 없다」 → 코드 실재와 대조 필요(§11-3).
- `dev-package/intent/2026-09-10-preview-all-formats.md` 절 이름이 스펙 L-1 템플릿과 불일치(§6-2).
