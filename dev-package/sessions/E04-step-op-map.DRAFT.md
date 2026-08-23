# E-04 단계 ↔ op/이벤트 대응표 — 〈61〉-㉡ 흐름 완주 검사의 사람 고정 픽스처

> **status = DRAFT.** 사용자(Ted) 검토 후 `gates/fixtures/seam-consistency/` 의 fixture 로 고정할 예정이다.
> **성격** — `〈61〉-㉡`(`PLAN-SoT.md:322`)의 전제물. 기계는 「E-04 의 단계가 무엇인가」라는 분해 자체를 못 한다(정본이 md 산문이라 — `DR-8` 이 막힌 것과 같은 이유). 그래서 사람이 이 표를 한 번 손으로 세워 fixture 로 고정해야 ㉡ 게이트를 만들 수 있다.
> **⚠ PLAN-SoT 의 경고 그대로** — **「그 표가 틀리면 ㉡ 은 틀린 흐름을 완주로 판정한다.」** 이 표의 오류는 게이트의 오류가 된다. 그래서 검토 없이 fixture 로 승격하지 않는다(㉢ 는 별도 — 이 표의 승인이 계약 동결 승인을 대신하지 않는다).
> **정본 원천** — `01 CoLAB-Plan/reference/v2_1차마일스톤_기획_260808/에픽/E-04_업로드와_계보_확정/documents/Policy_업로드와_계보_확정.md`(이하 `Policy`). 계약 원천 — `contracts/seams/fe-core.yaml`(rev 전 34 op) · `contracts/events/core-pipeline.json`·`envelope.json` · `contracts/seams/core-viz.yaml`.
> **작성** 2026-08-23. 편집한 기존 파일 없음 — 이 파일이 유일한 신규 산출이다.

---

## 0. 식별자 규약 (표를 읽는 전제)

- **`uploadId`** — 이벤트 seam 의 집계 루트(`envelope.json` Envelope.uploadId — 「7종 전부가 여기에 매달린다」). 업로드 진입점 op(신설)이 발급하고, 등록 전 세계의 모든 단계가 이 값으로 이어진다. `core-viz` `RenderTarget.uploadId` 가 같은 값을 쓴다.
- **`fileId`** — 업로드 안의 파일 하나(ULID, `core-pipeline.json` FileRef). **`fileId` 동일성(NB-A): 업로드 발급 시점부터 데이터셋 확정(등록 전환) 후의 `d3_file.id` 까지 같은 값을 유지한다 — 새로 만들지 않는다.** 근거는 `D2c.md §2-10`(계약 구조 연역 — 봉투가 `datasetId`·`projectId` 를 금지하므로 업로드↔등록을 잇는 값이 `fileId` 뿐). **`[정본 무근거]` — 사용자 승인 2026-08-23 확보. 단 그 승인이 Ted 본인인지 미확인이므로 NB-A 는 ㉢ 제출 목록에 그대로 남긴다. 계약 문장 확정은 ㉢ 뒤.**
- **`datasetId`** — 사람이 「데이터셋 만들기」를 누른 순간에만 태어난다(`Policy §7.2` · `envelope.json` — 봉투에 없는 이유). 등록 전환 op(신설)의 **출력**이다.
- **`renderId`** — `core-viz` 렌더 작업 식별자. FE 는 중계 op(신설)로만 도달한다(`core-viz.yaml:39-40` 내부 표면).

---

## 1. 단계 ↔ op/이벤트 대응표

범례 — **[부재-n]** = `[계약 부재 — D2c 개정 대상, D2c.md §2-n 이 신설]`. seam 열: FE↔core = `fe-core.yaml` / core↔pipe = `contracts/events/core-pipeline.json` / core↔viz = `core-viz.yaml`.

| # | 단계 (정본 인용: 파일+절) | 담당 seam | op / event id | 입력 식별자 | 출력 식별자 | 다음 단계와의 연결 |
|---|---|---|---|---|---|---|
| 1 | **파일 업로드** — 「파일을 끌어다 놓는다 → 업로드하고 헤더에서 메타데이터를 읽는다」(`Policy §2` 규칙 맵 1행 · `§7.1` 열어보는 중) | FE↔core | **[부재-4]** 업로드 진입점 op — 「`upload.accepted` 를 발행하는 유일한 자리」로 산문 명기(`D2c §2-4`) | (없음 — 파일 바이트) | **`uploadId` 발급 · `fileId[]` 발급**(본체 1+ · 기준 격자 0~2, `〈58〉-①`) | ✅ `uploadId`·`fileId[]` 가 2 의 봉투·payload 로 그대로 |
| 2 | **업로드 접수 (파이프라인 입구)** — 「core-api 가 내는 유일한 이벤트」(`core-pipeline.json` ① · `Policy §2` 1행) | core↔pipe | `upload.accepted` (source: `core-api` const — ㉡-3 촉발점 = 단계 1 op) | `uploadId`(봉투) · `fileId[]`(FileRef) | 동일 (전달) | ✅ 같은 `uploadId` 로 3~7 |
| 3 | **포맷 감지** — 「형식 제한 없음, 헤더 인식만 형식별」이라 파서 선택에 포맷이 먼저(`Policy §5` 파일 행 · `core-pipeline.json` ②) | core↔pipe | `file.format-detected` (source: pipeline-worker) | `uploadId` · perFile `fileId` | `uploadId` + 포맷 판정 | ✅ |
| 4 | **헤더 파싱** — 자동 메타(변수·기간·좌표계·격자·용량), 「못 읽어도 등록은 막지 않는다」(`Policy §9` · `§3.3` · `core-pipeline.json` ③) | core↔pipe | `file.header-parsed` | `uploadId` · unreadableFiles `fileId` | `uploadId` + 메타 | ✅ |
| 5 | **좌표계 정규화** — ⚠ 정본 E-04 직접 근거 없음, `DOMAINS §2 D5` 소유물 열거가 근거(계약 자기 명기, `core-pipeline.json` ④) | core↔pipe | `file.crs-normalized` | `uploadId` · `fileIds` | 동일 | ✅ |
| 6 | **COG 변환** — ⚠ 정본에 `COG` 라는 말 없음; 정본 근거는 「미리보기는 서버가 그린다·GB 급」(`Policy §8` 미리보기 그리기)까지, COG 는 레포 판단(계약 자기 명기, `core-pipeline.json` ⑤) | core↔pipe | `preview.cog-built` | `uploadId` · 본체 `fileIds` | 동일 (미리보기 파생물 준비) | ✅ `uploadId`(·본체 `fileIds`)가 9 의 RenderTarget 으로 |
| 7 | **준비 완료** — 등록 결정 게이트(「보기만 할게요 / 연구실에 등록」)를 볼 수 있는 상태, 저장된 것 없음(`Policy §7.1`·`§8` · `core-pipeline.json` ⑥) | core↔pipe | `upload.ready` (`datasetId` 없음 — 의도적) | `uploadId` | `uploadId` + expiresAt | ✅ |
| 7′ | **실패 (어느 단계에서든)** — `Policy §9` 오류와 예외 표 1:1 (`envelope.json` FailureReason 8값) | core↔pipe | `upload.failed` | `uploadId` | 실패 사유 | ⚠ 8 이 없으면 화면 도달 불가 |
| 8 | **업로드 상태·실패 사유 조회** — 실패 8값이 화면에 갈 자리(`Policy §9` 안내 문구 · `SEAM-AUDIT` I-18·C-5) | FE↔core | **[부재-4]** 업로드 상태 조회 op | `uploadId` | 상태 + FailureReason | ✅ 2~7′ 의 결과를 FE 가 소비 |
| 9 | **미리보기 렌더** — 「미리보기를 그린다 — 사람이 고른 변수·시간·값 범위로 지도를 그린다」(`Policy §2` 2행 · `§8` 미리보기 그리기) | FE↔core 중계 → core↔viz | FE측 **[부재-9]** 렌더 생성·조회 중계 op (`visualization` tag) · viz측 기존 `createRender`(`core-viz.yaml:248-268` RenderTarget `oneOf datasetId\|uploadId`, `fileIds`=본체 한정) · 타일 URL 은 중계 없이 FE 직결(`core-viz.yaml:40`) | `uploadId`(미등록, S-08) 또는 `datasetId`(등록 후) + 본체 `fileIds` | `renderId` → 타일 URL | ✅ 6 의 출력이 입력으로. ⚠ 기준 격자 파일의 렌더러 소비 방식은 D7 구현 몫(NB-D 해소 · `P2.md NB-7`) |
| 10 | **AI 계보 제안 확인·수정·거절** — 「AI 제안을 확인한다 → 계보 관계로 확정 예약」·확신도 3단·일괄 없음(`Policy §2` 규칙 맵 · `§8` 제안 카드) | (core-ai 는 내부 seam — 소비자는 core-api 뿐, `core-ai.yaml:50`) | ⚠ **FE 중계 op 미정** — `D2c §2-3` 은 `:14` 위임 산문 정정까지만 확정, 계보 제안 중계 op 신설 여부는 §2 항목에 없다. **열린 질문 Q1** | `uploadId`(제안 맥락) + 부모 후보 `datasetId` | 확정 예약된 계보 관계(클라이언트 상태 — 저장 안 됨, `Policy §7.1` 등록 중=저장 안 됨) | ✅ 확정 관계가 12 의 입력에 실림 |
| 11 | **직접 검색으로 부모 추가** — 「직접 추가 → 이름·주제·기간으로 연구실 데이터셋 검색」(`Policy §2`·`§8` 직접 추가 버튼) | FE↔core | **[계약 부재 — D2c 범위 밖, P4 가 연다]** (`D2c §2-3`·`§10-3` — 산문에 「P4 가 연다」 명기) · 임시 대안: `listDatasets`(`fe-core.yaml:175`)로 근사 가능 여부는 판정 안 함 | 검색어 | 부모 후보 `datasetId` | ✅ 12 의 입력에 |
| 12 | **계보 확정 = 등록 전환** — 「데이터셋 만들기를 누른다 → 데이터셋과 확정된 계보 관계를 저장하고 상세로 이동」(`Policy §2` 마지막 행 · `§7.2` 등록 중→등록됨) | FE↔core | **[부재-5]** `createDataset` POST `/datasets` — 의미는 「`uploadId` 를 D3 데이터셋으로 등록 전환」. `topic` 4값(`〈55〉`)도 이 op 이 받는다 | **`uploadId`** + 이름·주제·설명 + 확정 계보 관계(부모 `datasetId`+가공 방식 문장) + 소속 프로젝트 `projectId[]`(0+, `Policy §5`) — **Q2 참조** | **`datasetId` 발급** · **`fileId` 는 업로드 값 그대로 `d3_file.id` 로 (NB-A)** | ✅ `datasetId` 가 13·14 의 입력으로. `fileId` 동일성이 업로드 세계↔D3 세계의 유일한 다리 |
| 13 | **프로젝트 연결** — 소속 프로젝트 복수 지정(`Policy §5` 소속 프로젝트 · `§12` v1.2 다중 연결) | FE↔core | **[부재-8]** `linkProjectDataset` — 본문 있는 op(`usageNote` required 를 채운다, `fe-core.yaml:1731`) · 끊기는 기존 `unlinkProjectDataset`(`:836`) | `projectId` + `datasetId` + usageNote | 연결 | ✅ `getProject.datasets` 하드코딩 `[]` 도 닫힘(`D2c §2-8`) |
| 14 | **상세 이동·계보 확인** — 「상세 화면으로 이동한다」(`Policy §7.2`) | FE↔core | 기존 `getDataset`(`fe-core.yaml:239`) · `getDatasetLineage`(`:358`) | `datasetId` | 상세·계보 그래프 | (흐름 종료) |

**끊긴 자리 요약(현행 계약 기준, ㉡-4 형식)** — 단계 1·8·9(FE측)·12·13 이 **[계약 부재]** 로 끊겨 있고, 전부 D2c §2-4·§2-9·§2-5·§2-8 이 신설 예정이다. 단계 10 은 신설 항목 미배정(Q1), 11 은 의도적 P4 이월. 이벤트 구간(2~7′)은 현행 계약만으로 완주한다.

---

## 2. 표에 반영한 확정 사항

- **fileId 동일성(NB-A)** — 「등록 시 D3 파일 레코드는 업로드 세계의 `fileId` ULID 를 자기 PK 로 그대로 쓴다. 새로 만들지 않는다.」 사용자 승인 2026-08-23. **Ted 본인 승인 여부 미확인 — ㉢ 제출 목록 유지, 계약 문장 확정 보류**(`D2c §2-10`·`§9 NB-A`).
- **기준 격자 파일 0~2건·후주입 정상 동작**(`〈58〉`·`〈59〉`) — 후주입 경로(파일 추가·격자 교체·삭제, `D2c §2-6`)는 E-04 최초 등록 흐름 밖이라 본표에 행을 두지 않았다. ㉡ 이 최초 흐름만 검사하는 것이 맞는지는 **Q3**.
- **RenderTarget 은 이미 풀려 있다**(NB-D 해소) — `core-viz` 편집 불요. 격자 소비 방식만 D7 구현 미정.

## 3. 열린 질문 (fixture 고정 전에 답이 필요)

| # | 질문 |
|---|---|
| **Q1** | 단계 10(AI 계보 제안)의 FE 도달 경로 — `D2c §2` 신설 목록에 계보 제안 **중계 op 이 없다**(§2-3 은 `:14` 산문 정정까지). E-04 정본 흐름의 핵심 단계인데 D2c 뒤에도 계약상 도달 불가로 남는가, 아니면 §2-3 정정에 op 신설이 포함되는가? (P4=검색 진입점과는 별건이다) |
| **Q2** | 단계 13 이 단계 12 안에 접히는가 — 정본은 소속 프로젝트를 **업로드 등록 폼 안에서** 복수 지정한다(`Policy §5`). `createDataset` 요청 본문이 `projectId[]`(+usageNote?)를 받는지, 등록 후 `linkProjectDataset` 을 N 회 부르는지에 따라 ㉡ 의 간선이 달라진다. usageNote 를 업로드 화면이 받는 자리는 정본에 없다 — `[정본 무근거]` 후보. |
| **Q3** | ㉡ 의 검사 범위 — 최초 등록 흐름만인가, 후주입(`〈58〉`)·미등록 미리보기(S-08)·실패 경로(7′→8)도 「완주」에 포함하는가? 본표는 최초 흐름 + 7′/8 실패 표시까지만 세웠다. |
| **Q4** | 단계 5·6 은 정본 E-04 에 직접 근거가 없다(계약이 스스로 명기 — DOMAINS 열거가 근거). ㉡ fixture 가 「정본 단계」와 「레포 판단 단계」를 구분 표기해야 ㉠ 과 축이 섞이지 않는다 — 본표는 ⚠ 로 구분해 뒀다. 유지 여부 확인. |
