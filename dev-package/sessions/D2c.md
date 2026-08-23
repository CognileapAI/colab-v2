# WU-D2c — 계약 개정: `fe-core` 를 이벤트 seam 에 맞춘다 (`〈54〉` 이행)

> **읽는 순서** `CLAUDE.md` → `contracts/README.md` → 이 문서 → 해당 레인 절. 이 문서가 D2c 의 작업 정본이다.
> **성격** 이것은 화면 WU 가 아니라 **계약 개정 WU** 다. `contracts/**` 는 D2 에서 동결됐고, 이 문서만이 그 동결을 한 번 여는 권한을 갖는다 — `〈54〉`(`PLAN-SoT.md:307`)가 그 권한의 근거다.
> **선행** `DR-7` 은 **진단·결정 완료 · 이행 대기** 상태다(`03-HANDOFF.md §5.5`). 이 WU 가 그 이행이다.
> **왜 D2c 인가** — `D2`(seam 동결) · `D2b`(이벤트 게이트) 와 같은 T-D 계약 트랙이고, 여기서 하는 일이 그 둘의 산출물을 고치는 것이기 때문이다. P 번호가 아니다 — 화면을 만들지 않는다.

---

## 0. 이 WU 가 푸는 것 (한 줄)

- **`fe-core.yaml:13-16` 이 자기가 안 하는 일 셋을 위임했는데 셋 다 받을 수 없는 곳이다.** 그래서 업로드 세계가 FE 표면에서 통째로 사라졌고, 그 결과 **P2 · S2 가 막혀 있고 P5 가 잠재적으로 막혀 있다**(`03-HANDOFF.md §5.5 DR-7` · `P2.md §7 STOP-1`).
- **이 WU 가 닫히면 `P2.md` 의 `STOP-1` 이 닫힌다.** 그것이 이 WU 의 유일한 성공 기준이다.

---

## 1. 범위

정본 결정 `〈54〉`(`PLAN-SoT.md:307`) + 감사 `sessions/SEAM-AUDIT.md` + 해소 `sessions/OPEN-ITEMS-RESOLUTION.md` 셋이 입력이다.

| 대상 | 무엇을 한다 | 근거 |
|---|---|---|
| **`contracts/seams/fe-core.yaml`** | 위임 산문 정정 + 업로드·렌더 중계 op 신설 + `linkProjectDataset` + 데이터셋 U | `〈54〉-②` · `SEAM-AUDIT.md` I-01~I-03·I-06·I-10 |
| **`contracts/schemas/common.json`** | 신설 enum 이 필요한 자리만 (`RenderFailureCode` — 아래 `§2-11`) | `OPEN-ITEMS-RESOLUTION.md §3.2` |
| **`services/core-api/`** | 신설 op 을 **라우트로 등록**하고 501 로 세운다 + 501 표 갱신 | `§9-㊹` · `SEAM-AUDIT.md` I-23(34 op ↔ 34 라우트 **정확히 1:1**) |
| **`gates/`** | **seam 정합 게이트 신설** (`DR-7` 의 나머지 절반) | `03-HANDOFF.md §5.5 DR-7` · `SEAM-AUDIT.md §5` |

### 범위 밖 — 손대지 않는다

- **어휘 드리프트(`core-pipeline.json:54`·`:59` 의 `grib`·`HDF5`)** — **`§2-12` 를 반드시 읽는다.** 계약이 낡은 정본을 **충실히 인용**하고 있는 것이라, 계약을 고치면 **계약이 정본과 어긋난다**(`DR-8`). 고칠 것은 정본이다.
- **`contracts/events/**` 전체** — `〈54〉` 가 이벤트 seam 을 **정본**으로 확정했다. 정본은 맞추는 쪽이 아니라 맞춰지는 쪽이다. 이벤트 계약을 한 글자도 고치지 않는다.
- **`contracts/seams/core-ai.yaml` · `core-viz.yaml`** — 다만 `§2-9` 의 `RenderTarget` 주소지정 판정 하나는 **판정만 하고 편집 여부는 멈춤 규칙을 탄다**(아래).
- **구현** — 신설 op 의 **실동작은 P2 가 만든다.** 이 WU 는 라우트를 501 로 세우는 데까지다.
- **`frontend/`** — 화면 없음. `topic` 픽스처 드리프트(`OPEN-ITEMS-RESOLUTION.md §2.3`)도 여기가 아니다(FE 레인 소유).
- **`db/`** — D5 저장 형태·`grid_axis` 제약 교체(`〈58〉-㉠`)는 P2-db 소유다.
- **`generated-up-to-date` 게이트** — 별건(`I3`·별도 착수 후보).
- **`03-HANDOFF.md`·`PLAN-SoT.md`·`WORK-UNITS.md`·`SEED-DATA.md`·`DATA-REFERENCE.md` 갱신** — 메인 세션 소관(`CLAUDE.md §6`).

---

## 2. 확정된 설계 (레인이 임의로 바꾸지 않는다)

> 아래 값은 **이미 결정된 것**이다. 다르게 하는 편이 낫다고 판단되면 **고치지 말고 멈추고 보고한다**.

### 2-1. 방향은 단방향이다 — `fe-core` 가 이벤트 seam 에 맞춘다

- **근거** `〈54〉-①②`(`PLAN-SoT.md:307`). 이벤트·viz 두 계약은 **근거를 적어 가며** 같은 업로드 세계를 그렸고(`envelope.json:162-163` · `core-viz.yaml:255-259`), `fe-core` 의 부재만 근거가 없다 — 남은 것은 **오배정된 위임 한 줄**(`fe-core.yaml:16`)이다.
- **함의** — 개정 중에 「이벤트 쪽을 바꾸면 더 쉽다」가 나오면 **그것이 멈춤 신호다**(`§5-7`).

### 2-2. 새 seam 파일을 만들지 않는다 — `fe-core.yaml` 안의 op 이다

- **근거** `OPEN-ITEMS-RESOLUTION.md §4`. ① `contracts/README.md:16` 「seam 은 손으로 쓴다 — 수가 적고 값이 높다」 ② `README.md:23-30` seam 목록의 단위는 **도메인이 아니라 배포 단위 쌍**이다 — 업로드의 동기 절반은 **FE ↔ core-api** 다 ③ 파일을 쪼개면 FE 가 같은 서버에 클라이언트 2벌을 갖는다(`README.md:19` 소비자는 생성물만 쓴다).
- **tag 2종을 신설한다** — `ingestion`(D5 중계) · `visualization`(D7 중계). 기존 tag 는 `identity·access·catalog·lineage·project·insight` 6종(`fe-core.yaml:35-46`).
- **경계는 tag·라우터가 지키지 파일 이름이 지키지 않는다.** `CLAUDE.md §3-4` 는 core-api 에 **geo 라이브러리 import** 금지이지 중계 op 금지가 아니다.

### 2-3. 위임 산문 자체를 고친다 (`fe-core.yaml:13-16`)

- **이것은 부수 작업이 아니라 작업 항목이다.** 올바른 op 을 넣고 산문을 그대로 두면, 다음 세션이 「저 seam 이 맡는다」를 읽고 **같은 결론에 다시 도달한다** — `DR-4` 와 같은 계열(주석이 자기 코드에 대해 거짓말한다)이다.
- **세 줄 각각의 처분** (`SEAM-AUDIT.md` I-02 · `OPEN-ITEMS-RESOLUTION.md §4.4-1):

| 현행 | 판정 | 개정 |
|---|---|---|
| `:14` 검색·계보제안 → `core-ai` | **오배정** — `core-ai.yaml:50` 「외부에 노출하지 않는다 — 소비자는 core-api 뿐이다」 | **FE 중계 op 을 통해 이 파일이 맡는다**(검색 진입점 자체의 신설은 P4 범위이므로, 이 개정은 **위임처를 바로잡는 문장**까지만 — `§6-위험 3`) |
| `:16` 업로드·파일 파싱·**프로젝트 연결 생성** → 「이벤트/업로드 seam」 | **존재하지 않는 위임처** — `contracts/README.md:23-30` seam 목록 4종에 없다 | **셋으로 가른다**: 업로드 HTTP 입구·상태·등록 전환 = **이 파일** · 파싱·변환의 **비동기 절반만** `events/core-pipeline.json` · **프로젝트 연결 생성 = 이 파일**(봉투가 `projectId` 를 금지한다 — `envelope.json:5`) |
| `:16` 미리보기 렌더·타일·스크린샷 → `core-viz` | **부분 오배정** — `core-viz.yaml:39-40` 「viz-render 내부 표면. **타일 경로만 CDN 뒤에 선다**」 | **렌더 작업 생성·조회는 core-api 중계**, **타일 URL 소비만 FE 직결**. 이 구분을 문장으로 적는다 |

- **판정 기준 한 줄을 같은 절에 못 박는다 — 「이 seam 에 없다고 적으려면, 그것을 받는 곳에 FE 가 도달할 수 있어야 한다」.** 이 문장이 없으면 다음 세션이 같은 습관을 반복한다(`SEAM-AUDIT.md §4` 선택지 C 의 판정 기준).

### 2-4. 업로드 진입점 — `upload.accepted` 의 유일한 촉발자

- **측정** `fe-core.yaml` 34 op / 29 path 어디에도 업로드 진입점이 없다(`uploadId` grep **0건**, 이 세션 실측). 반면 `core-pipeline.json:33` 은 `upload.accepted` 를 「**core-api 가 내는 유일한 이벤트**이며 파이프라인의 입구」로 선언하고, `:223` 이 `source` 를 **`core-api` 상수**로 못 박았다.
- **즉 계약이 core-api 에 능력을 단정해 두고, 그 능력을 행사할 수단을 자기 seam 에 주지 않았다**(`SEAM-AUDIT.md §3` C-1).
- **확정** — 업로드 진입점 op 을 신설하고, **그 op 이 `upload.accepted` 를 발행하는 유일한 자리임을 계약 산문에 적는다.** 이벤트 계약이 상수로 못 박은 `source` 와 동기 seam 의 op 이 **문장으로 서로를 가리키게** 만든다 — 그래야 `§2-13` 의 `G-b` 가 볼 간선이 생긴다.
- **조각(part) 단위 상태를 계약에 넣지 않는다** — 정본이 이어올리기를 범위 밖으로 뒀다(`core-pipeline.json:33` · `P2.md §9 NB-4`).
- **업로드 상태 조회 op 이 함께 필요하다** — 실패 사유 8값(`envelope.json:85-97`)이 화면에 갈 자리가 지금 없다(`SEAM-AUDIT.md` I-18 · C-5).

### 2-5. `createDataset` — 등록 전환

- **측정** `/datasets` 는 **GET 전용**이다(`fe-core.yaml:172`). `createDataset` grep **0건**.
- **확정** — `/datasets` 에 POST 를 얹는다. 의미는 「새 데이터셋을 만든다」가 아니라 **「업로드 세계의 `uploadId` 를 D3 데이터셋으로 등록 전환한다」** 다 — 정본이 「사람이 `데이터셋 만들기` 를 눌러야 생긴다」로 못 박았고(`envelope.json:163` 인용 `Policy §7.2`), 등록 전에는 **아무것도 저장되지 않는다**(`P2.md §2-7`).
- **주제(`topic`)는 이 op 이 받는다** — 컬럼은 있는데 채울 길이 없던 자리다(`OPEN-ITEMS-RESOLUTION.md §2.4` 말미 · `db/platform/schema.sql:244`). 값 집합은 `〈55〉` 가 DB CHECK 로 못 박은 4값이다.

### 2-6. 기존 데이터셋에 파일 추가 (후주입)

- **`〈58〉` 이 요구한다** — 「기준 격자 파일은 **후주입이 가능해야** 한다」(`PLAN-SoT.md`, `〈58〉-②`). `〈59〉` 가 「추가·교체·삭제는 **정상 동작**이다」로 넓혔고, `〈60〉` 이 「후주입은 계보를 접지 않고 `d8_activity` 에 남긴다」로 닫았다.
- **⚠ 이 항목이 없으면 `〈58〉` 은 나머지가 다 끝나도 여전히 막힌다.** 그리고 나중에 좌표를 구한 사람은 **다시 올리는 수밖에 없고, 그러면 계보가 끊긴다** — `〈58〉` 이 후주입을 요구한 이유가 정확히 이것이다.
- **확정** — 데이터셋에 파일을 더하는 op 과 **기준 격자 파일을 교체·삭제하는 경로**를 함께 연다. `〈59〉-①` 이 교체·삭제를 정상 동작으로 못 박았으므로 추가만 여는 것은 결정의 절반만 이행하는 것이다.
- **판정은 `업로드·편집` 스위치가 한다** — `〈59〉-②`(열린 결정 ⑳ 해소). 「소유자」를 별도 관문으로 만들지 않는다(`P-6`·`P-3`).
- **본체 파일은 이 경로의 대상이 아니다** — `〈59〉-③`. 본체를 갈아 끼우는 것은 **다른 데이터**다.

### 2-7. 데이터셋 수정 (U)

- **측정** 데이터셋의 U 가 **통째로 없다**(`SEAM-AUDIT.md` I-10). `/datasets/{datasetId}` 는 GET 뿐이고(`fe-core.yaml:234`), 삭제·삭제 영향은 있다(`:271`).
- **CRUD 의 C·U 가 둘 다 없고 D 만 있는 상태**다. `〈55〉` 가 주제를 DB 열거값으로 못 박았는데 **주제를 고칠 길이 없다**.
- **확정** — 「사람이 적는 정보」(이름·주제·요약 — `DATAMODEL-BASELINE.md:58` · `db/platform/schema.sql:238`)를 고치는 op 을 연다. **「자동으로 읽은 정보」는 이 op 의 대상이 아니다** — 파일에서 읽는 값이다(`DATAMODEL §4.1` · `DR-14`).

### 2-8. `linkProjectDataset` — 본문 있는 op 이다

- **측정** `unlinkProjectDataset`(DELETE)만 있고(`fe-core.yaml:830-836`) `linkProjectDataset` 은 **없다**(이 세션 grep 실측 — 유일한 매치는 `unlink` 의 부분문자열이다). 같은 계약이 `createProject` 는 준다(`:717-719`).
- **끊는 길은 있는데 잇는 길이 없다.** 그리고 그 부재의 근거로 적힌 것이 `:836` 의 「**담는 동작은 이 seam 에 없다 — 업로드 화면(E-04)이 맡는다**」인데, 그 화면이 부를 op 이 이 계약에 없다.
- **확정 — 본문 있는 op 이다. 맨 PUT 이 아니다.** `DATAMODEL` 상 프로젝트:데이터셋은 **N:N 이고 연결마다 활용 의미 문장이 붙는다**(`DATAMODEL-BASELINE.md:133`·`:168`·`:104`). 계약에도 이미 그 자리가 있다 — `usageNote`(`fe-core.yaml:1481`·`:1751-1752` 「이 연결의 활용 의미 문장」)가 `ProjectDetail.datasets` 행의 **required**(`:1731`)다.
- **즉 required 로 읽히는 값을 쓸 수단이 없는 상태다.** 이 op 이 그것을 채운다.
- **`getProject.datasets` 하드코딩 `[]` 도 이 항목이 닫는다** — `services/core-api/.../routes/project.py:78` 이 「업로드 화면(E-04)이 맡는다」는 주석과 함께 빈 배열을 고정하고 있고, 계약은 그 배열을 「전부 담는다」로 규정한다(`fe-core.yaml:1770`). **스키마 위반은 아니지만 항상 거짓인 응답**이다(`SEAM-AUDIT.md` I-22 · C-7).

### 2-9. 도달성 — `uploadId`·`renderId` 를 FE 표면에 올린다

- **측정** 두 식별자 모두 `fe-core.yaml` 에 **0건**(이 세션 실측). 그런데 `core-viz.yaml:250` 은 렌더 대상을 「등록된 데이터셋이면 `datasetId`, 아직 등록하지 않은 업로드면 `uploadId`」로 두고 **둘 중 정확히 하나**를 요구한다.
- **결과 — S-08(미등록 미리보기)만 막힌 것이 아니다. `datasetId` 쪽 경로도 함께 막혀 있다.** `core-viz` 는 core-api 전용 내부 표면이고(`core-viz.yaml:39-40`), FE 가 렌더를 **시작·조회**할 중계 op 이 `fe-core` 에 없다. 즉 **E-03 등록 데이터셋 미리보기도 계약상 도달 불가**다(`SEAM-AUDIT.md` I-06·I-07 · C-4).
- **확정** — 렌더 생성·조회 중계 op 을 `visualization` tag 로 신설하고, `uploadId` 를 업로드 표면의 응답으로 FE 에 내린다. **타일 URL 은 중계하지 않는다** — CDN 뒤에 서므로 FE 가 직접 소비한다(`core-viz.yaml:40`).
- **⚠ `RenderTarget` 주소지정은 `〈58〉` 로 전제가 바뀌었다 — 판정만 하고 편집은 멈춤 규칙을 탄다.**
  - **⟨2026-08-23 정정 — 실물 확인⟩** 초안이 「`RenderTarget` 은 `uploadId` **하나**로 가리킨다」고 적었으나 **틀렸다.** `core-viz.yaml:248-268` 은 **`oneOf: [datasetId] | [uploadId]`** 이고 설명이 **「등록된 데이터셋이면 `datasetId`(+ 조각 선택), 아직 등록하지 않은 업로드면 `uploadId`(S-08). 둘 중 정확히 하나」**라고 명시한다. 그릴 조각은 `fileIds` 이며 **「그릴 조각(**본체 파일**)들」**로 한정된다. **즉 파일 3개짜리 데이터셋은 `datasetId` 로 가리키면 되고, 격자는 애초에 「그릴 조각」 후보가 아니다 — 계약이 이미 갈라 뒀다.**
  - 그런데 `〈58〉` 이 데이터셋을 **최대 세 파일(본체 + 기준 격자 2)** 로 만들었고, `〈57〉-②` 가 기준 격자 파일을 **본체와 다른 종류**로 못 박았다. **기준 격자 파일은 그리는 대상이 아니라 좌표를 읽는 수단**인데(`〈60〉` 근거), `fileIds` 주석은 「그릴 조각(**본체 파일**)들」이라 이미 본체로 한정하고 있다.
  - **따라서 주소지정은 이미 풀려 있다 — 이 WU 가 `RenderTarget` 을 고칠 이유가 없다.** 남는 질문은 **「어떻게 가리키나」가 아니라 「렌더러가 격자 파일을 어떻게 받아 쓰나」**이고, 그것은 **계약 표면이 아니라 D7 구현일 수 있다**(`P2.md NB-7` — 그 일을 어느 단계가 맡는지가 정본에 없다). **`core-viz` 편집이 필요하다는 결론이 나오면 멈추고 보고한다**(`§5-6`) — 전제가 바뀌었어도 이 멈춤은 유지한다.
  - **이 WU 의 몫 = 판정과 등재까지다.** `core-viz.yaml` 을 고쳐야 한다는 결론이 나오면 **멈추고 보고한다**(`§5-7` — `〈54〉` 는 `fe-core` 개정을 승인했지 `core-viz` 재설계를 승인하지 않았다).

### 2-10. `fileId` 동일성 — `[정본 무근거]`

- **`[정본 무근거]`.** 정본에 `파일 ID`·`fileId`·`업로드 ID` 어휘가 **한 건도 없다**(`OPEN-ITEMS-RESOLUTION.md §1.1` 전수 grep).
- **권고 = 승계한다.** 개정문에 들어갈 문장은 — **「등록 시 D3 파일 레코드는 업로드 세계의 `fileId` ULID 를 자기 PK 로 그대로 쓴다. 새로 만들지 않는다.」** + 근거 한 줄.
- **근거** ① 봉투가 `datasetId`·`projectId` 를 **금지**한 상태에서(`envelope.json:5`) 업로드↔등록을 잇는 값이 `fileId` 밖에 없다 ② `d3_file.dataset_id NOT NULL`(`db/platform/schema.sql:275`)이라 「등록 전 파일 행」은 애초에 만들 수 없다 — **ID 충돌이 발생하지 않는다** ③ D5 스키마가 아직 없어 비용이 0 이다(`schema.sql:4`).
- **⚠ 용어 주의** — 정본에서 「승계」는 **소유권 승계(P1, A-06)** 를 가리킨다(`E-00/documents/DataModel_공통_기반.md:70-71`). 개정문에서는 **`fileId` 동일성** 같은 다른 말을 쓴다.
- **⚠ Ted 확인 필요.** 이 권고는 **계약 구조에서 연역한 것이지 정본 인용이 아니다.** 답이 오기 전에는 계약에 문장을 박지 않고 **`[정본 무근거]` 로 등재한 채 멈춘다**(`§5-6`).

### 2-11. `RenderFailureCode` — 종류는 확정, **표기만** `[정본 무근거]`

- **종류 3개는 정본이 준다** — 그리는 서버 연결 불가 · 시간 초과 · 알 수 없는 오류(`Policy_데이터셋_상세.md:202-204`). 계약이 이미 산문으로 정확히 인용한다(`core-viz.yaml:351-353`).
- **무근거인 것은 `code` **값 라벨** 하나뿐이다** — 정본은 문장을 주지 라벨을 주지 않고, `ErrorEnvelope.code` 는 자유 문자열이다(`contracts/schemas/common.json:28`).
- **권고** `common.json` 에 `RenderFailureCode` 를 **정본 상황 문구 그대로** 신설(`common.json:4` · `§9-㉗` — 영문 코드값을 만들면 매핑 테이블이 생긴다). **`[정본 무근거]` — Ted 한 줄 확인.** 답이 없으면 신설하지 않고 등재만 한다.
- **축을 합치지 않는다** — 이벤트의 `FailureReason` 8값(`envelope.json:85-97`)은 **파이프라인 처리 실패**로 다른 축이다. 4xx 거부(`그릴 수 없는 형식`·`기준 격자 파일 없음`·`파일이 너무 큼`)와 `partialFailure`(`core-viz.yaml:355-359`)도 각각 다른 축이다.

### 2-12. ⚠ 어휘 드리프트를 「고치지」 않는다 — `core-pipeline.json` 은 옳다

- **`core-pipeline.json:54` 의 `grib`·`:59` 의 `HDF5` 를 지우지 않는다.**
- **근거 `DR-8`(`03-HANDOFF.md §5.5`)** — 「**계약이 틀린 게 아니라 정본이 낡았다**」. `〈51〉`(지원 포맷 = `NetCDF·Binary·HDF4·GeoTIFF`)이 고친 것은 **`dev-package/` 문서뿐**이고, 기획 정본 `Policy §9` 는 여전히 GRIB·HDF5 를 말한다. 계약은 **그 정본을 충실히 인용**하고 있다.
- **처방을 틀리기 쉬운 자리다** — 계약에서 지우면 **정본과 어긋난 계약**이 된다. **고칠 것은 정본이고 계약은 따라온다.** 이 WU 는 정본을 고칠 권한이 없다.
- **덧붙여** `format` 필드에 enum 을 만들지 않는 것도 의도적 개방이다 — 「정본이 `등` 으로 열어 뒀고, 값 집합을 여기서 닫으면 정본에 없는 어휘를 계약이 만든다」(`core-pipeline.json:54` 원문). **`§2-13` 의 `G-d` 가 이 자리를 red 로 만들면 allow-list 로 가른다 — 계약을 고치지 않는다.**

### 2-13. seam 정합 게이트 — `DR-7` 의 나머지 절반

- **왜 필요한가** — 게이트 배선을 실측했다: `contract-lint`·`contract-breaking` 은 `contracts/seams/*.[yj]*` 만 보고(`gates/tools/contract-breaking.sh:82`), `event-lint`·`event-breaking` 은 `contracts/events/**` 만 본다(`gates/README.md`). **둘 사이를 보는 게이트가 하나도 없다.** `DR-7` 은 게이트를 통과해서가 아니라 **게이트가 없어서** 살아남았다.
- **공통 모양** — 주장은 **산문**에 있고 부재는 **op 표**에 있다. 게이트가 op 표만 보므로 전부 통과한다(`SEAM-AUDIT.md §3`).
- **신설 게이트 이름 = `seam-consistency`.** 검사 5종(`SEAM-AUDIT.md §5`):

| 검사 | 무엇을 본다 | 이번에 잡혔어야 할 것 |
|---|---|---|
| **G-a 식별자 도달성** | 네 계약의 모든 ID 필드를 모아, 각 ID 에 **생산 op/이벤트**와 **소비 op/이벤트**가 최소 1개씩 있는지 그래프로 판정 | I-01·I-06·I-07 (`uploadId`·`renderId` 가 소비만 있고 생산이 없다) |
| **G-b `const` 능력 주장** | 이벤트의 `source: {const: X}` 마다, X 의 seam 파일에 op 이 있고 그 op 이 해당 집계 루트 ID 를 다루는지 | I-01·I-05 (`source: core-api` 인데 촉발 op 0건) |
| **G-c 짝 op 대칭** | 경로 패턴에서 `create↔delete`·`link↔unlink` 쌍을 뽑아 한쪽만 있는 자원을 red. 예외는 **이유와 함께** allow-list 등재 | I-03·I-10·I-11 (`unlink` 만 있고 `link` 없음) |
| **G-d 공유 값 집합 재선언** | `common.json` 의 enum 과 의미가 같은 필드가 다른 계약에서 자유 문자열로 등장하는지(필드명 사전 기반) | I-16·I-17·I-19 |
| **G-e 산문 위임 참조 검증** | 계약 주석·description 안의 **seam 파일명·op 이름 언급**을 뽑아 **실재하는 파일/op 인지** 확인 | **I-02 — `fe-core.yaml:16` 이 이 검사 하나로 red 였다** |

- **⚠ 최소 채택선 = `G-e` · `G-b` 둘이다.** 다섯을 다 만들지 못하면 이 둘을 먼저 만든다 — `DR-7` 의 뿌리를 직접 때리는 것이 이 둘이고, 나머지 셋은 파생 증상을 잡는다. **다섯을 못 채웠다는 사실은 감추지 않고 게이트 README 와 완료 보고에 적는다.**
- **`selftest` 를 반드시 함께 만든다** — 각 게이트는 red fixture 로 자기가 fail-closed 임을 증명해야 한다(`CLAUDE.md §4` · `gates/README.md`). **증명 없는 게이트는 게이트가 아니다.** 기존 세트(`contract-selftest` 15 · `event-selftest` 33 · `boundary-selftest` 30 · `db-selftest` 43 · `rls-effect-selftest` 18)와 같은 형태로 `seam-consistency-selftest` 를 세운다.
- **fixture 는 자기 allow-list 를 들고 다닌다** — `db-selftest` 가 레포 allow-list 를 읽지 않는 것과 같은 이유다(`gates/README.md` 말미 · `WU-D3b`). 레포에 정당한 예외가 추가되면 기준 케이스가 red 가 되기 때문이다.
- **⚠ 이 게이트를 red 인 채로 두지 않는다** — 개정이 끝난 시점에 `seam-consistency` 는 **green 이어야 한다**. 만들자마자 red 라면 개정이 덜 끝난 것이다.

### 2-14. **기계화 불가 — 게이트가 못 하는 것 (정직하게 적는다)**

> **이 절을 게이트 README 에 그대로 옮긴다.** 능력을 실제보다 크게 말하는 것이 `DR-4`·`DR-6` 이 만든 사고다.

- **어느 seam 이 정본인가** — 값 판단이다. 게이트는 **「갈렸다」까지만** 말한다. `〈54〉` 같은 결정을 대신하지 않는다.
- **자유 문자열이 의도적 개방인지 누락인지** — `core-pipeline.json:54` 는 **이유가 붙은 의도적 개방**이고 `fe-core.yaml:1362` 의 `topic` 은 이유가 없다. **둘의 차이는 산문에만 있다.** `G-d` 는 둘 다 red 로 만들고 **사람이 allow-list 로 가른다**.
- **정본 문구 ↔ 계약 어휘 대조(`DR-8`)** — 정본이 md 산문이라 값 집합을 기계가 못 뽑는다. **결정 → 계약 반영 체크리스트(사람 절차)로 갈 수밖에 없다 `[추론]`.** `planning-freshness` 는 **임베드↔원본**만 보지 **결정↔정본**은 아무도 안 본다.
- **화면 요구 충족 여부** — op 이 있어도 그 화면을 그릴 수 있는지는 판정 불가.
- **`G-e` 의 근본 한계** — 정규식이 산문에서 **파일명·op 이름처럼 생긴 것**을 뽑는다. 「이벤트/업로드 seam」처럼 **이름이 아닌 서술**로 위임하면 놓칠 수 있다. 이번 사례가 잡히는 것은 그 문장에 `seam` 이라는 어휘가 있어서다 — **다음 번 같은 실수가 다른 문장으로 오면 못 잡는다.**

### 2-15. 501 표는 계약과 함께 움직인다

- **측정** 현재 구현↔계약은 **정확히 1:1** 이다 — 34 op ↔ 34 라우트, 고아 라우트 0, 미등록 계약 op 0(`SEAM-AUDIT.md` I-23 · `services/core-api/src/colab_core/app/routes/not_implemented.py`). 라이브 9 · 501 스텁 25.
- **따라서 계약에 op 을 더하면 그 즉시 1:1 이 깨진다.** 계약만 고치고 라우트를 안 세우면 **다음 세션이 「고아 계약 op」을 발견한다.**
- **확정** — **신설 op 은 전부 `NOT_IMPLEMENTED_NO_STORE` 501 로 라우트를 세운다**(저장처가 아직 없다 — D5 스키마가 P2 몫이다, `schema.sql:4`). `501` 은 계약이 아니라 **배포 상태**이므로 **계약에 501 을 박지 않는다**(`§9-㊹-③`).
- **501 표가 이 개정으로 25 → 늘어난다.** 그것이 정상이다 — **표가 줄어드는 것이 진척인 것은 구현 WU 에서이고, 계약 개정 WU 에서는 늘어난 만큼이 P2 에 넘긴 일감이다.** 이 사실을 완료 보고에 숫자로 적는다.

---

## 3. 순서 — 바꾸지 않는다

`CLAUDE.md §4` 그대로. **red 를 눈으로 본 뒤에 고친다.**

1. **진입조건 확인**(`§4`). 미충족이면 **구현하지 말고 보고한다**
2. **개정 전 기준선 확보** — 현행 전 게이트를 돌려 **지금 무엇이 green 인지 실측**한다(`generated-up-to-date` red 는 설계대로). 개정 뒤 비교 대상이 없으면 「내가 깬 것」과 「원래 red 였던 것」이 구분되지 않는다
3. **게이트를 먼저 만들고, red 를 본다** — `seam-consistency` 를 **현행 계약 위에서** 돌려 **`fe-core.yaml:16` 이 실제로 red 를 내는 것을 눈으로 본다.** 이것이 이 WU 의 오라클이다. **개정을 먼저 하면 게이트는 처음부터 green 이 되고, 그 게이트가 무엇을 막는지 아무도 모른다**(`㊺`·`㊽` 과 같은 이유)
4. **계약을 개정한다** — 산문(`§2-3`) 먼저, op 나중. 순서가 중요하다: 산문이 판정 기준을 세우고 op 이 그 기준을 따른다
5. **`contract-lint` green · `contract-breaking` green**(`§6-1` 의 additive 판정)
6. **라우트를 501 로 세우고 시험을 고정한다**(`§2-15`) — `tests/test_not_implemented.py` 형태로 op 별 code 를 못 박는다
7. **`seam-consistency` 가 green 이 되는 것을 본다** + `seam-consistency-selftest` green
8. **전 게이트 green + `selftest` green + staging 배포 green**(`§6`)

---

## 4. 진입조건

| 조건 | 확인 방법 | 상태 |
|---|---|---|
| **`〈54〉` 확정** | `PLAN-SoT.md:307` · `03-HANDOFF.md §5.5 DR-7`「결정됨·이행 대기」 | ✅ |
| **`SEAM-AUDIT.md` · `OPEN-ITEMS-RESOLUTION.md` 존재** | `dev-package/sessions/` | ✅ |
| **D2 · D2b 게이트 green** | `./gates/run.sh contract-lint` 외 | 착수 시 실측 |
| **`contracts/**` 를 다른 세션이 쥐고 있지 않다** | 워킹트리 상태 확인 — `DR-4` 때문에 **트리를 두 세션이 쥐면 검증 안 한 변경이 배포에 섞인다** | 착수 시 확인 |
| **`fileId` 동일성 Ted 답** | `§2-10` | ⛔ **미확보 — 그 문장만 보류하고 나머지는 진행한다** |

---

## 5. 레인 표

각 레인은 **자기 디렉터리만** 만진다. 남의 파일을 고쳐야 하면 멈추고 보고한다.

| 레인 | 소유 디렉터리 | 산출 |
|---|---|---|
| **D2c-contract** | `contracts/seams/fe-core.yaml` · `contracts/schemas/common.json` | 위임 산문 정정(`§2-3`) · `ingestion`·`visualization` tag · 업로드 표면 · `createDataset` · 파일 추가·격자 교체 · 데이터셋 U · `linkProjectDataset` · 렌더 중계 · `RenderFailureCode`(Ted 답이 오면) |
| **D2c-gate** | `gates/tools/seam-consistency.sh` · `gates/tools/seam-consistency-selftest.sh` · `gates/fixtures/seam-consistency/` · `gates/config/seam-consistency-allowlist.toml` | 검사 5종(최소 `G-e`·`G-b`) + red fixture 자기 증명 + allow-list · **`〈61〉` 추가분 — ㉠ 근거 칸 공란 red 검사(`§7-6`) + ㉡ `E-04` 흐름 완주 검사(`§7-7`, `G-a` 재사용이 아니라 **별도 검사** — 축이 다르다) + 둘의 red fixture** |
| **D2c-api** | `services/core-api/src/colab_core/app/routes/` · `services/core-api/tests/` | 신설 op 을 501 라우트로 등록 · op 별 code 고정 시험 · 라우트↔계약 1:1 diff 시험 갱신 |

### 공유 파일 — 명시된 한 줄만 만진다

- **`gates/run.sh`** — **D2c-gate 만.** `case` 분기 **2개**(`seam-consistency` · `seam-consistency-selftest`) 추가 + `selftest)` 묶음 목록에 **1개** 추가. `planning-freshness` 와 같은 `exec` 위임 형태를 그대로 따른다(`gates/run.sh:12-15`)
- **`gates/README.md`** — **D2c-gate 만.** 게이트 표에 **1행** + 현재 상태 표에 **1행** + `§2-14`(기계화 불가) 절
- **`contracts/README.md`** — **D2c-contract 만.** seam 목록 표(`:23-30`)는 **손대지 않는다**(4종 그대로 — 새 파일을 만들지 않으므로). 고칠 것이 있다면 `:18-19` 의 **능력 주장**뿐이다(`generated-up-to-date` 미구현인데 「CI 가 검증한다」고 단정 — `SEAM-AUDIT.md` I-21·C-6). **이 한 줄 정정은 선택이며, 하려면 보고하고 한다**
- **`services/core-api/src/colab_core/app/routes/not_implemented.py`** — **D2c-api 만.** 501 표 갱신

---

## 6. 멈춤 규칙

1. **게이트를 우회하거나 끄지 않는다.** **검사 대상을 줄여서 green 을 만들지 않는다** — 이 WU 는 게이트를 **만드는** WU 라 특히 위험하다. 자기가 만든 검사의 범위를 좁혀 green 을 얻는 것이 가장 쉬운 실패 경로다
2. **서브에이전트는 커밋하지 않는다.** 커밋과 `03-HANDOFF`·`PLAN-SoT` 갱신은 **메인 세션만**
3. **일회용 컨테이너는 레인 접두사(`d2c*_`)로 짓고 호스트 포트를 공개하지 않는다**(`RESTART.md §2④`)
4. **staging 을 건드리는 명령을 레인이 돌리지 않는다** — `deploy.sh`·`rollback.sh`·`docker compose up/down`·마이그레이션 실행은 메인 세션 소관. **8 컨테이너가 실서비스 중이다**
5. **정본이 값을 주지 않으면 만들지 않는다** — `[정본 무근거]` 로 남기고 **멈춘다**. 지어내지 않는다(`㊴-②`)
6. **⛔ 기존 동결 op 의 의미를 바꾸는 변경이면 멈추고 보고한다.** `〈54〉` 가 승인한 것은 **정합(더하기)** 이지 **재설계**가 아니다. 판정선 —
   - **더하기다(진행)** — 새 path·새 op·새 optional 필드·새 tag·산문 정정
   - **바꾸기다(멈춤)** — 기존 op 의 `operationId`·경로·응답 스키마 변경 · required 추가·제거 · enum 값 축소 · 기존 필드의 의미 재정의 · **`core-viz.yaml`·`core-ai.yaml`·`contracts/events/**` 편집**
   - 애매하면 **바꾸기로 간주하고 멈춘다.** `contract-breaking` 이 red 를 내면 그것이 이 규칙의 기계적 확인이다
7. **이벤트 계약을 고치고 싶어지면 그것이 멈춤 신호다**(`§2-1`)
8. **`core-pipeline.json` 의 `grib`·`HDF5` 를 지우지 않는다**(`§2-12`). 지우고 싶어지면 `DR-8` 을 다시 읽는다

---

## 7. 완료 정의

**여덟 다 충족해야 닫힌다.** 부분 완료로 닫지 않는다(`CLAUDE.md §5` 「나중에」 금지).

> **`7-6`·`7-7`·`7-8` 은 `〈61〉`(`PLAN-SoT.md:322`)이 이 문서의 `§10-1` 위험을 요구로 승격시킨 것이다** — **계약 동결 전에 「설계가 옳은가」를 판정한다. 도달성 green 은 옳음의 증거가 아니다.** 셋은 순서를 갖는다: ㉠·㉡(기계) → ㉢(사람). **㉠·㉡ 이 green 이어도 ㉢ 없이 동결하지 않는다**(`03-HANDOFF.md:134`).

### 7-1. `contract-breaking` — additive 임을 증명한다

- **이 개정은 전부 additive 다.** 그러므로 **`contract-breaking` 은 green 이어야 하고, red 가 나면 그것은 게이트의 오탐이 아니라 이 WU 가 범위를 넘었다는 증거다.**
- **게이트는 `oasdiff breaking -c --fail-on ERR` 로 기준 ref 대비 `contracts/seams/*` 를 비교한다**(`gates/tools/contract-breaking.sh:81-84`). `WARN` 은 red 로 세지 않는다.
- **breaking 으로 셀 것 — 일어나면 안 된다:** 기존 op 삭제·경로 변경 · 기존 응답에서 필드 제거 · 기존 요청에 required 추가 · enum 값 제거 · 응답 타입 변경 · 기존 `operationId` 변경.
- **⚠ 특히 조심할 자리 둘** — ① `ProjectDetail.datasets[].usageNote` 는 **이미 required 다**(`fe-core.yaml:1731`). `linkProjectDataset` 을 더하면서 이 required 를 건드리면 breaking 이다 ② `DatasetRow.fileCount` 는 `minimum: 1` 이다(`:1355-1359`) — 후주입·파일 추가로 이 하한을 손대고 싶어지면 **`㊼` 를 다시 읽고 멈춘다**.

### 7-2. 501 표 — 늘어난 만큼이 P2 에 넘긴 일감이다

- **신설 op 이 하나도 빠짐없이 501 표에 등재된다**(`§2-15`). 등재되지 않은 계약 op 이 있으면 red — 라우트↔계약 1:1 diff 시험이 그것을 잡는다.
- **각 op 이 어떤 `code` 로 501 을 내는지 시험이 고정한다** — 나중에 누가 가짜 200 으로 바꾸면 red(`P0-core-api.md:96`).
- **표가 이 WU 에서 25 → N 으로 는다. 그 뒤 P2 가 구현할 때마다 줄어드는 것이 진척 계측이다**(`§9-㊹-④`). **완료 보고에 개정 전후 숫자를 둘 다 적는다.**

### 7-3. 게이트

- **전 게이트 green + `selftest` green.** `generated-up-to-date` 미구현 red 는 설계대로 — **우회하지 않는다**(`gates/run.sh:100-102`).
- **`seam-consistency` green** + **`seam-consistency-selftest` green(exit 0)**. 자기 증명 케이스 수를 보고에 적는다.
- **`§3-3` 의 red 를 눈으로 봤다는 기록** — 개정 전 게이트가 `fe-core.yaml:16` 에 red 를 낸 출력. 이것이 없으면 게이트가 무엇을 막는지 증명되지 않았다.

### 7-4. staging 배포 green — **`docker compose ps` 가 아니다**

- **컨테이너 8개 전부 `healthy`**
- **헬스 6종 전부 200** — 루트 + 단위 5(`core-api`·`frontend`·`pipeline-worker`·`viz-render`·`ai-service`)
- **⚠ 본문 대조** — **루트 200 만으로 판정하지 않는다. 자리표시 오리진도 루트에 200 을 낸다**(`RESTART.md §1`·`§2②`). 단위별 `/healthz/<unit>` **5개의 응답 본문이 v2 오리진의 것인지**를 확인해야 I2 가 서 있다는 증거가 된다
- **⚠ 정직한 한계** — 엣지에서 토큰 없이 보면 **구현 op 과 미구현 op 이 둘 다 401 이라 구별되지 않는다**(인증이 501 핸들러보다 먼저 걸린다 — `03-HANDOFF.md:83` P1 실측). **따라서 501 표 증명은 로컬 시험과 검증된 트리로 하는 것이지 staging 에서 독립 증명되지 않는다.** 이 사실을 보고에 그대로 적는다
- **배포 전 `docker tag … :prev` 로 직전 이미지를 보존한다** — `rollback.sh` 는 직전 릴리스가 아니라 **I2 이전 자리표시로 간다**(`DR-5`). 기계가 아니라 사람이 하는 일이다

### 7-5. `contracts/README.md` 규칙 5 — 필수 리뷰

- **규칙 5** 「`contracts/` 변경은 **필수 리뷰**(CODEOWNERS)」(`contracts/README.md:20`).
- **배선은 실재한다** — `.github/CODEOWNERS` 가 `/contracts/` 와 `/gates/` 를 명시적으로 소유자에 배정한다(`# 계약 권위체 — 변경 시 필수 리뷰. 여기가 드리프트의 유일한 발원지다.`).
- **따라서 이 개정은 `main` 직push 로 들어가지 않는다** — **브랜치 → PR → CODEOWNERS 리뷰**를 탄다. `CLAUDE.md §7` 의 「게이트가 red 인 상태로 `main` 에 직접 push 하지 않는다」와 같은 줄에 선다.
- **⚠ 소유자가 실인물 1인(`@sungwooHa`)이다.** 팀 핸들 교체는 R1 몫이고, **현재 리뷰는 절차이지 다중 승인이 아니다.** 이 사실을 감추지 않는다 — 「리뷰를 받았다」가 「두 사람이 봤다」를 뜻하지 않는다.
- **한 커밋 = 계약 + 그 소비자**(`CLAUDE.md §7`) — 계약 개정과 501 라우트 등록은 **같은 커밋**이다. 모노레포의 이점을 버리지 않는다.

### 7-6. ㉠ 정본 근거 대조 — 기계 (`〈61〉-㉠`)

- **신설되는 op·필드마다 정본 인용을 단다.** 못 다는 것은 **지어내지 않는다** — `[정본 무근거]` 로 표시하고 `§9` 표에 등재한다(`㊴-②` · `§6-5`).
- **게이트가 보는 것은 「근거 칸이 비어 있으면 red」까지다.** 근거의 **내용이 옳은지는 못 본다.** 그래도 **근거 없이 슬쩍 들어온 것**은 잡는다.
- **`〈54〉` 가 「어느 seam 이 정본인가」를 정했지만 「그 세계가 옳은가」는 아무도 판정하지 않던 자리를 여기가 메운다**(`PLAN-SoT.md:322`).

| # | 검사 항목 | red 조건 | 증거 |
|---|---|---|---|
| **㉠-1** | 신설 op **전수**에 정본 인용 또는 `[정본 무근거]` 표기가 붙는다 | 근거 칸 **공란** 1건이라도 | 근거 표 + 게이트 출력 |
| **㉠-2** | 신설 필드 **전수**에 같은 규칙 | 근거 칸 **공란** 1건이라도 | 위와 같음 |
| **㉠-3** | `[정본 무근거]` 로 표시된 것은 `§9` 표에 **빠짐없이** 등재된다 | 표기는 있는데 등재 없음 | `§9` 표 |
| **㉠-4** | `[정본 무근거]` 항목은 **계약에 문장을 박지 않은 채** 멈춰 있다 | 무근거인데 계약에 확정 문장 | `NB-A`·`NB-B`(`§2-10`·`§2-11`) |

### 7-7. ㉡ 흐름 완주 검사 — 기계 (`〈61〉-㉡`) · **셋 중 실질**

- **도달성 게이트는 「op 이 있다」만 본다. 「흐름이 끝까지 간다」는 안 본다.**
- **`E-04`(업로드 → 파싱 → COG → 계보 확정) 한 흐름을 계약만으로 처음부터 끝까지 호출 가능한지 종이 위에서 재생한다.** 각 단계의 **출력이 다음 단계의 입력 자리에 실제로 들어가는지**(식별자 종류가 맞는지)까지 본다.
- **`DR-7` 이 정확히 이 검사가 없어서 살아남았다** — 이벤트가 `upload.accepted` 를 요구하는데 그것을 낼 HTTP 입구가 없는 것을, **양쪽 게이트가 각자 green 을 내면서 아무도 사이를 안 봤다**(`§2-13` 첫 항목 · `03-HANDOFF.md §5.5 DR-7`).
- **⚠ `G-e` 와 축이 다르다 — 섞지 않는다.** **`G-e` 는 산문의 정적 참조가 해소되는지**를 보고(`§2-13` 표 마지막 행), **㉡ 은 흐름이 완주하는지**를 본다. `G-e` green 이 ㉡ green 을 뜻하지 않고 그 반대도 아니다.

| # | 검사 항목 | red 조건 | 증거 |
|---|---|---|---|
| **㉡-1** | `E-04` 각 단계에 **호출 가능한 op/이벤트가 실재**한다 | 한 단계라도 부재 | 단계↔op 대응표 |
| **㉡-2** | 각 단계의 **출력 식별자 종류**가 다음 단계의 **입력 식별자 종류**와 일치한다 | 종류 불일치 · 어디서도 생산되지 않는 ID 를 입력으로 요구 | 식별자 연결 그래프 |
| **㉡-3** | 이벤트가 요구하는 `source` 촉발점이 **HTTP 입구로 실재**한다(`DR-7` 재발 방지) | 촉발 op 0건 | `G-b` 출력 + ㉡ 그래프 |
| **㉡-4** | 완주 재생 결과를 **끊긴 자리 목록과 함께** 보고에 적는다 — 끊긴 곳이 없으면 「없음」이라고 적는다 | 기록 누락 | 완료 보고 |

### 7-8. ㉢ 사람 승인(Ted) — **동결 전** (`〈61〉-㉢`)

- **동결 전에 Ted 가 본다.** `㊵`(staging 에서 사람이 본 것만 prod 로 간다)의 **계약판**이다.
- **근거 = 계약은 되돌리는 비용이 코드보다 크다.** 코드는 고치면 되지만 **동결된 계약은 `oasdiff` 가 파괴적 변경으로 막고**(`§7-1`), 그 위에 **P2·P3·S2 가 이미 올라가 있다**.
- **⛔ ㉠·㉡ 이 green 이어도 ㉢ 없이 동결하지 않는다.** 기계 green 은 **사람이 볼 것을 먼저 걸러 준 것**이지 **사람의 판단을 대신한 것이 아니다**(`§10-12`).

| # | 검사 항목 | red 조건 | 증거 |
|---|---|---|---|
| **㉢-1** | ㉠·㉡ 결과와 **신설 op·필드 전체 목록**을 Ted 에게 제출한다 | 미제출 상태로 동결 | 제출 기록 |
| **㉢-2** | `[정본 무근거]` 항목(`NB-A`·`NB-B`)을 **따로 세워** 제출한다 | 본문에 섞어 흘려보냄 | `§9` 표 |
| **㉢-3** | **Ted 의 명시 승인**을 받고 동결한다 — 침묵은 승인이 아니다 | 승인 없이 PR merge·동결 | 승인 문구 인용 |
| **㉢-4** | 승인이 **실질**이었음을 적는다 — 무엇을 보고 승인했는지 | 「승인함」 한 줄만 | 완료 보고 |

---

## 8. ⛔ `DR-13` — 이 WU 가 닫을 수 없고, 그래서 P2 착수 판정이 아직 안 선다

> **이 절을 건너뛰지 않는다. 이 WU 가 다 끝나도 P2 는 열리지 않을 수 있다.**

- **측정** `WORK-UNITS §6`(T-D)이 정의하는 작업 단위는 **`D1` · `D2` · `D2b` · `D3` · `D3b` 다섯**뿐이다. 표에 `D4`~`D10` 행이 **없다**.
- **그런데 `§7` 이 그것들을 진입조건으로 건다** — **P2 → `D5 D4`** · **P3 → `D4 D7`** · **P5 → `D6`**.
- **즉 정의되지 않은 작업 단위가 관문으로 쓰이고 있다.** 「`D5` 가 닫혔는가」를 판정할 **오라클이 존재하지 않는다.** `DOMAINS.md` 에 D4~D10 이 있지만 **그것은 경계 정의이지 작업 단위가 아니다**.
- **`D2` 가 유령 `A3` 를 참조하던 것과 같은 부류다**(2026-08-22 삭제됨 — `WORK-UNITS §6` 주석). **그때는 없는 것을 참조했고, 이번은 정의 안 된 것을 참조한다.**
- **둘 중 하나다** — ⓐ T-D 가 「경계·계약」만 WU 로 세우고 도메인 구현은 P·K 번호로 흡수한 것이라면 **P2 의 `D5` 표기가 착오**다 ⓑ 정말 D4~D10 WU 가 필요하다면 **표에 다섯 줄이 빠진 것**이다.
- **⛔ 이 WU 는 그것을 고칠 수 없다.** `WORK-UNITS.md` 는 **다른 세션이 소유**하고, 그 판정은 **트랙 구조의 값 판단**이다(소유 = `D1` 또는 기획 — `03-HANDOFF.md §5.5 DR-13`).
- **⛔ 따라서 — `STOP-1` 이 닫혀도 P2 의 착수 판정은 서지 않는다.** `P2.md §5 진입조건` 은 `P1 ✅`·`G4 ✅`·`I2 ✅`·`STOP-1 닫힘` 넷을 열거하지만, **`WORK-UNITS §7` 의 진입조건 원문은 `D5 D4` 다.** 두 문서가 다른 조건을 말하고 있고, 그 차이가 정확히 `DR-13` 이다.
- **이 WU 의 종료 보고는 이렇게 적어야 한다** — **「`STOP-1` 은 닫혔다. `DR-13` 은 열려 있다. P2 착수 판정은 메인 세션이 `DR-13` 을 닫은 뒤에 선다.」** 「P2 를 열었다」라고 적지 않는다.

---

## 9. `[정본 무근거]` — 지어내지 않고 비운 것

| # | 무엇 | 정본이 말한 데까지 | 처분 |
|---|---|---|---|
| **NB-A** | **`fileId` 동일성** — 업로드 `fileId` ULID 가 `d3_file.id` 로 이어지는가 | 정본에 `파일 ID`·`fileId`·`업로드 ID` 어휘가 **0건**(`OPEN-ITEMS-RESOLUTION.md §1.1`). 인접 사실은 「등록 전에는 저장하지 않는다」 하나뿐(`Policy_업로드와_계보_확정.md:227`) | **권고 = 승계한다(`§2-10`). Ted 답 전까지 계약에 문장을 박지 않는다.** D5 스키마가 P2 에서 생기는 순간 이 결정은 강제되므로 **미룰 수 있는 항목이 아니다** |
| **NB-B** | **`RenderFailureCode` 의 값 표기** | 정본은 **문장**을 주지 `code` 라벨을 주지 않는다(`Policy_데이터셋_상세.md:202-204`). **종류 3개는 확정이다 — 확인 대상이 아니다** | **표기만 Ted 한 줄. 답 없으면 신설하지 않고 등재만 한다**(`§2-11`) |
| **NB-C** | **「업로드 seam」이 별도 파일이어야 하는가** | 정본은 계약 파일 구성을 말하지 않는다. 답을 좁힌 것은 **`contracts/README.md:16`·`:23-30` 의 계약 규칙**이지 정본이 아니다 | **권고 = 단일 파일(`§2-2`). 연역이지 정본 인용이 아니다.** 반대 근거도 정직하게 — `fe-core.yaml` 은 이미 34 op 이고 개정 뒤 45 op 안팎이 된다 `[추론]`. **파일이 커지는 것은 사실이고 그것이 유일한 반대 근거다** |
| **NB-D** ✅**해소** | **`〈58〉` 아래서 렌더 대상을 무엇으로 주소지정하는가** | **정본이 아니라 계약이 답했다** — `core-viz.yaml:248-268` 이 `oneOf: [datasetId] | [uploadId]` 이고 `fileIds` 를 **본체 파일**로 한정한다. 파일 3개짜리 데이터셋은 `datasetId` 로 가리킨다 | **무근거가 아니었다. 초안이 계약을 안 열고 인용만 보고 좁게 넘겨짚은 것이다.** 남는 것은 주소지정이 아니라 **렌더러가 격자를 어떻게 소비하는가**이고 그것은 `NB-7`(담당 단계 미정)로 넘어간다 |
| **NB-E** | **데이터셋 주제를 계약 층에서도 좁힐 것인가** | `〈55〉` 는 **DB CHECK** 를 확정했다. **계약 `topic` 은 여전히 자유 문자열**이고(`fe-core.yaml:1362`) `common.json` 에 `Topic` 정의가 없다 | **`〈55〉` 는 DB 를 말했지 계약을 말하지 않았다.** 계약 층 enum 신설은 **이 WU 가 임의로 하지 않는다** — `G-d` 가 이 자리를 red 로 만들면 그때 사람이 판정한다 |

---

## 10. 위험·한계 — 정직하게

**이 작업지시서가 보장하지 못하는 것.**

1. **가장 위험한 것 — 이 WU 는 「계약을 늘리는 일」로 위장한 「설계하는 일」이다.** 업로드 표면 6~9 op 을 새로 그리는 것은 `[추론]` 규모 추정이지 실제 설계가 아니고(`SEAM-AUDIT.md §6`), **한 번 동결하면 그것이 P2·P3·S2 가 살아갈 세계가 된다.** `DR-7` 이 태어난 경위 — 「내 것이 아닌 것을 목록으로 밀어내고 받는 쪽을 확인하지 않은 한 번의 습관」(`SEAM-AUDIT.md §3` `[추론]`) — 이 **정확히 이 자리에서 반복될 수 있다.** 게이트를 먼저 만들라고 `§3-3` 이 요구하는 이유가 이것이고, **그래도 게이트는 도달성만 보지 설계의 옳음을 보지 않는다**.
   - **`〈61〉` 이 덮은 부분** — 이 위험이 요구로 승격됐다(`PLAN-SoT.md:322`). **근거 없이 들어오는 것**(㉠)과 **이어지지 않는 흐름**(㉡)은 이제 기계가 red 로 잡고, **동결 자체가 사람 승인 뒤로 밀렸다**(㉢ · `§7-6`~`§7-8`).
   - **그래도 남는 부분 — 이 항목을 지우지 않는 이유다.** **이 WU 가 「설계하는 일」이라는 사실 자체는 그대로다.** ㉠·㉡ 은 **빠진 것·안 이어지는 것**을 잡지 **잘못 그린 것**은 못 잡는다(`§10-12`). **한 번 동결하면 P2·P3·S2 가 살아갈 세계가 된다는 것도 그대로다.**
2. **`fe-core.yaml` 이 커진다.** 34 → 45 op 안팎 `[추론]`. 단일 파일 권고의 **유일한 반대 근거**이고, 이 WU 가 그 대가를 치르기로 한 것이다(`NB-C`).
3. **검색 진입점(I-08)은 이 WU 가 닫지 않는다.** `§2-3` 은 `:14` 의 **위임처를 바로잡는 문장**까지만 하고 검색 op 을 만들지 않는다 — 그것은 P4 범위다. **따라서 P4 는 이 개정 뒤에도 같은 벽을 만날 수 있다.** 산문만 고치고 op 을 안 만든 자리가 **`DR-7` 의 반대 모양**(op 없이 산문만 옳음)이 되지 않도록, **그 문장에 「P4 가 연다」를 명시**해야 한다.
4. **`seam-consistency` 는 이미 난 사고를 red 로 만들 뿐 고르지 않는다**(`SEAM-AUDIT.md §4` 선택지 D). 다음번 오배정을 **잡을 수는 있어도 옳은 배정을 정해 주지는 않는다.**
5. **`G-e` 는 이번 문장을 잡지만 다음 문장을 못 잡을 수 있다**(`§2-14` 마지막 줄). 이름이 아닌 서술로 위임하면 정규식이 놓친다. **게이트를 만들었다는 사실이 「이 계열이 닫혔다」를 뜻하지 않는다.**
6. **staging 배포 판정 자체가 아직 fail-open 이다.** `deploy.sh` 는 앱 5종에 헬스 대기가 없어 `health: starting` 인 채로 성공을 반환하고(`DR-6`), **커밋이 아니라 워킹트리를 굽는다**(`DR-4`). **`§7-4` 의 6종+본문 대조는 사람이 따로 하는 확인이지 스크립트가 판정하는 것이 아니다.** `I3` 이 닫히기 전까지 이 자리는 관례로 막혀 있다.
7. **직전 이미지가 남지 않아 되돌릴 것이 없다**(`DR-5`). 배포 전 `:prev` 태그 보존이 필요하고, 이것도 기계가 아니라 사람이 한다.
8. **`DR-13` 이 열려 있는 한 이 WU 의 성공이 P2 의 착수로 이어지지 않는다**(`§8`). **막힌 것이 하나 줄어든 것이지 열린 것이 아니다.**
9. **정본(260818) 원문을 이 문서가 열지 않았다.** 인용은 전부 `contracts/**` · `dev-package/**` 경유다. `P2.md §7 STOP-2` 가 이미 **정본 ↔ 결정 불일치 한 곳**을 보고했고, `DR-8` 이 그것을 계약 층에서 확인했다 — **정본이 낡은 자리가 더 있을 수 있다.**
10. **`frontend/` 를 보지 않았다.** FE 가 실제로 무엇을 호출하는지 미측정 — 「FE 도달 불가」는 **계약상 판정**이고 코드 실측이 아니다(`SEAM-AUDIT.md §6`).
11. **`OPEN-ITEMS-RESOLUTION.md §2.3` 의 FE 픽스처 드리프트가 이 개정으로 안 고쳐진다** — `frontend/src/components/{catalog,detail}/fixture.ts` 가 `유출·수문` 을 쓰고 **테스트가 그 값을 단언한다.** 소유는 FE 레인이다. **계약을 고쳐도 저절로 안 고쳐진다.**

12. **⚠ `〈61〉` 의 ㉠·㉡ 이 알리바이가 되는 것 — 이 한계를 적지 않으면 그렇게 된다.** **㉠·㉡ 은 「빠진 것」과 「안 이어지는 것」을 잡지 「잘못 그린 것」은 못 잡는다.** **근거를 달았는데 그 근거가 엉뚱해도 ㉠ 은 통과하고, 흐름이 이어지는데 그 흐름이 이상해도 ㉡ 은 통과한다.** 그래서 **㉢ 이 형식이 아니라 실질이어야 하고, 기계가 green 을 냈다는 사실이 사람의 판단을 대신하지 않는다**(`PLAN-SoT.md:322`).
    - **이 프로젝트가 반복해서 밟는 무늬다** — `dc ps` green 이 배포 성공을 뜻하지 않았고(`DR-6`), 타일이 있다는 것이 COG 를 뜻하지 않았다(`DR-2`). **공통 줄기는 「판정 도구가 실제로 검사한 것보다 큰 것을 주장한다」이다.**
    - **배포 쪽에서 같은 줄기를 이름 붙인 것이 `sessions/I3.md:12` 의 「배포가 자기 자신에 대해 참말을 하게 만든다」이고, `〈61〉` 은 그 문장을 계약 쪽에 그대로 얹은 것이다.**


---

## 추기 (2026-08-23 · 메인 세션) — 착수 전 반영 사항

1. **`NB-A`(`fileId` 동일성) 답이 나왔다 — 동일 ID 유지.** 업로드 시 발급된 `fileId` 가 계보 확정(등록 전환) 후 `d3_file.id` 로 **그대로 유지**된다. 별도 uploadId→fileId 변환 지점을 만들지 않는다. *(사용자 승인 2026-08-23 — Ted 본인 승인 여부 미확인. 정본 근거가 아니라 사용자 결정이므로 `[정본 무근거]` 로 취급하고 `§7-8-㉢-2` 제출 목록에 유지한다 — 계약 본문에는 이 결정을 산문 명기하되 근거 표기를 정직하게 남긴다.)*
2. **신설 항목 추가 — AI 계보 제안 조회 중계 op.** `E04-step-op-map.DRAFT.md` 단계 10 이 지적한 구멍: `core-ai` 는 core-api 내부 seam 이라 FE 가 계보 제안에 도달할 계약 경로가 없다 — `§2` 신설 목록에 **FE↔core 중계 op(계보 제안 조회)** 를 추가한다(§2-3 의 위임 산문 정정과 별개 항목). `DR-7` 과 같은 모양의 구멍을 개정 회차에 알고도 남기지 않는다. **㉢ 제출 목록에 「범위 확장 1건」으로 명시한다.** *(사용자 승인 2026-08-23)*
3. **`DR-13`·`STOP-4` 는 닫혔다**(제3안 — D5 만 WU 승격). `§8` 의 마감 보고 문구 중 「`DR-13` 은 열려 있다」 부분은 **「`DR-13` 은 닫혔다(2026-08-23)」로 바꿔 적는다.** P2 착수 판정은 `STOP-1` 닫힘만 남는다.
4. **`DR-8`·`STOP-2` 는 닫혔다** — 정본 갱신 완료(계약 무변경, `§2-12` 처방대로). 개정 시 `core-pipeline.json` 의 포맷 표기는 **갱신된 정본**(`NetCDF·Binary·HDF4·GeoTIFF`) 기준으로 정합을 본다.
5. **단계↔op 대응표 초안이 있다** — `sessions/E04-step-op-map.DRAFT.md`(〈61〉-㉡ 전제물). ㉡ 검사는 이 표를 fixture 로 쓰되, 표의 열린 질문 Q2(usageNote 시점)·Q3(㉡ 검사 범위)·Q4(CRS·COG 정본 무근거 ⚠ 표기 유지)는 개정 중 판정해 표를 갱신·고정한다.

---

## C1 실행 기록 (2026-08-23 · D2c-C1 레인 — 계약 개정만)

> 범위 = 계약 개정(§2)만. seam-consistency 게이트(§2-13)·㉠/㉡ 증거표·501 라우트 등록(D2c-api)은 **후속 레인** 몫.
> 커밋 없음(오케스트레이터 소관). 동결 선언 없음 — ㉢(Ted 승인)은 사람 단계로 남아 있다.

### 개정 전 기준선 (§3-2 · §7-3)

- `contract-lint` green · `contract-breaking` green · `event-lint` green · `event-breaking` green (착수 시 실측).
- **`fe-core.yaml:13-16` 개정 전 원문(§7-3 요구 기록)** — seam-consistency 게이트가 아직 없어 기계 red 출력은 없다. 산문 red 의 실물은 아래 원문 그대로다:
  ```
  이 seam 에 **없는 것**과 그 이유 —
  - 자연어 검색(S-06)·계보 제안: D10. `core-ai` seam 이 맡는다 (`DOMAINS §2`).
  - 업로드·파일 파싱·프로젝트 연결 생성(E-04 가 주인): D5. 이벤트/업로드 seam.
  - 미리보기 렌더·타일·스크린샷: D7. `core-viz` seam (`CLAUDE.md §3-4` — core 에 geo 라이브러리 금지).
  ```

### 무엇을 개정했나 — fe-core.yaml 34 → 45 op (+11)

위임 산문(`:13-16`)을 §2-3 표대로 정정하고 판정 기준 문장(「이 seam 에 없다고 적으려면, 그것을 받는 곳에 FE 가 도달할 수 있어야 한다」)을 같은 절에 박았다. `:14` 검색 진입점은 산문 정정까지만 — **「P4 가 연다」 명기**(§10-3). tag 2종 신설(`ingestion`·`visualization`).

| op | 경로 | 근거 |
|---|---|---|
| `createUpload` | POST `/uploads` | §2-4 · `core-pipeline.json` ①(source=core-api const) · Policy §2·§8 — `upload.accepted` 발행 유일 자리 산문 명기. **전송 형태(파일 바이트가 이 op 으로) = `[정본 무근거]` 레포 결정**(E04-map 단계 1 형태 승계) |
| `getUploadStatus` | GET `/uploads/{uploadId}` | §2-4 · SEAM-AUDIT I-18·C-5. 실패 사유는 `envelope.json#FailureReason` $ref — 재선언 없음 |
| `listUploadLineageSuggestions` | GET `/uploads/{uploadId}/lineage-suggestions` | **추기-2(범위 확장 1건, 사용자 승인 2026-08-23)** · Policy §2 규칙 맵. 응답 = `core-ai.yaml#LineageSuggestionResponse` $ref(중계라 재선언 안 함) |
| `createDataset` | POST `/datasets` | §2-5 · Policy §7.2 · 〈55〉(topic 은 받되 계약 enum 없음 — NB-E). **fileId 동일성 산문 명기 + `[정본 무근거 · 사용자 승인 2026-08-23 — Ted 본인 승인 여부 미확인]` 표기**(추기-1) |
| `updateDataset` | PATCH `/datasets/{datasetId}` | §2-7 · DATAMODEL-BASELINE(이름·주제·요약만) · DR-14 |
| `addDatasetFile` | POST `/datasets/{datasetId}/files` | §2-6 · 〈58〉-② 후주입 · 〈59〉-①·② · 〈60〉 |
| `replaceDatasetGridFile` | PUT `/datasets/{datasetId}/files/{fileId}` | 〈59〉-①·③(본체 대상 아님 → 409) |
| `deleteDatasetGridFile` | DELETE `/datasets/{datasetId}/files/{fileId}` | 〈59〉-①·③ |
| `linkProjectDataset` | PUT `/projects/{projectId}/datasets/{datasetId}` | §2-8 · DATAMODEL-BASELINE(연결마다 의미 문장) — 본문 있는 op(`usageNote` required-but-nullable). `unlinkProjectDataset` 의 거짓 산문(「담는 동작은 이 seam 에 없다」)도 정정 |
| `createPreviewRender` | POST `/previews` | §2-9 · SEAM-AUDIT I-06·I-07·C-4. 요청/응답 = `core-viz.yaml#RenderRequest/RenderJob` $ref. 타일 URL 은 중계 안 함 |
| `getPreviewRender` | GET `/previews/{renderId}` | §2-9. RenderFailureCode 는 신설 안 함(NB-B — Ted 답 대기, 등재만) |

신설 스키마: `UploadFileRef`(이벤트 FileRef 와 동일 4값) · `UploadReceipt` · `UploadStatus`(필드마다 원천 이벤트 명기) · `UploadLineageParent` · `DatasetCreate` · `DatasetUpdate` · `ProjectDatasetLinkCreate`. 신설 파라미터: `UploadId`·`FileId`·`RenderId`. `common.json` **무변경**(RenderFailureCode 미신설 — NB-B). `contracts/events/**` **무변경**. `core-viz.yaml`·`core-ai.yaml` **무변경**($ref 소비만).

`contracts/README.md` — seam 목록 표 무변경(§5 대로). **규칙 3 능력 주장 한 줄 정정**(선택 항목, 보고와 함께): 「CI가 검증한다」→ 「`generated-up-to-date` 미구현 red — 관례로만 서 있다」(SEAM-AUDIT I-21·C-6).

### `[정본 무근거]` 추가 등재 (㉠-3 대비)

- 업로드 전송 형태(파일 바이트가 `createUpload` 로 직접) — 정본은 「끌어다 놓는다」까지. E04-map 단계 1 형태 승계.
- `UploadLineageParent.confirmedMethodText` — 제안 확인 결과가 등록 요청의 어느 필드로 실리는지 정본 무형태.
- Q2 판정 — `createDataset.projectIds` 로 접힘(Policy §5 폼 한 화면 제출 + §7.1 등록 전 저장 없음 → 등록 전 link 호출 불가). **usageNote 는 폼에 자리가 정본에 없어 등록 후 `linkProjectDataset` 으로** — E04-map 표 갱신은 레인 편집권 밖이라 미반영(오케스트레이터 몫).
- NB-A·NB-B 는 §9 표 그대로 유지 — ㉢ 제출 목록에 남는다.

### 501 표 (§2-15 · §7-2)

- **개정 전 25 → 개정 후 목표 36**(+11). 라우트 등록·`not_implemented.py` 갱신·1:1 diff 시험은 **D2c-api 레인 몫 — 이 레인은 services/ 를 만지지 않았다.** 현재 워킹트리는 「고아 계약 op 11건」 상태다 — D2c-api 가 닫기 전까지 커밋하지 않는 것이 맞다(한 커밋 = 계약 + 소비자, §7-5).

### 게이트 결과 (개정 후 실측)

- `contract-lint` **green** (seam 3건, 룰 위반 0 — 중간에 `colab-id-must-ref-ulid` red 1건을 보고 고쳤다: `DatasetCreate.uploadId` allOf → 직접 $ref).
- `contract-breaking` **green** (「No breaking changes to report, but the specs are different」— additive 증명). 중간 red 1건: oasdiff composed 모드가 `/renders` 를 core-viz 와 중복 엔드포인트로 거부 → FE 중계 경로를 `/previews` 로 개명해 해소(core-viz 무변경 유지).
- `event-lint` green · `event-breaking` green (이벤트 무변경 확인) · `contract-selftest` green(fail-closed 증명 15케이스).

### §7-1 두 함정 점검

- `ProjectDatasetRow.usageNote` required — **건드리지 않음**(required 목록 원형 유지, `linkProjectDataset` 은 별도 요청 스키마).
- `DatasetRow.fileCount minimum: 1` — **건드리지 않음**(후주입 op 은 하한과 무관).

### 열린 항목 (닫지 않고 보고)

1. `listPalettes` FE 중계 부재 — `createPreviewRender.style.palette` 값의 출처가 FE 표면에 없다. §2-9 가 생성·조회 2 op 만 확정해 범위 확장하지 않았다. 계약 산문에 명기해 둠.
2. 기준 격자 건수 불일치 — `common.json#FileKind`·`UploadAcceptedPayload` 는 「0~1건」(DataModel §4.3 인용), 〈58〉·E04-map 은 「0~2건」. 이벤트·common 은 이 레인이 못 고친다(§2-12 계열 — 정본/결정 정합은 별도 판정 필요).
3. NB-A ㉢ 제출 유지(Ted 본인 승인 미확인) · NB-B RenderFailureCode 미신설(Ted 답 대기).
4. E04-step-op-map.DRAFT.md 의 Q2 판정 반영·단계 10 op 명 기입 — 레인 편집권 밖(파일이 허용 목록에 없음), 오케스트레이터가 갱신.
5. seam-consistency 게이트·㉠/㉡ 기계 검사·501 라우트 — 후속 레인.

**STOP-1 판정 문구(§8 · 추기-3 반영)** — 계약 표면 기준으로 업로드 세계가 FE 에 도달 가능해졌다. `DR-13` 은 닫혔다(2026-08-23). P2 착수 판정은 STOP-1 의 나머지(501 라우트 1:1 복원 + 게이트 레인) 뒤에 선다. **동결 아님** — ㉢ 전.

---

## C2 실행 기록 (2026-08-23 · D2c-C2 레인 — seam-consistency 게이트)

> 범위 = §2-13 게이트 신설 + 〈61〉-㉠·㉡ 기계 검사 + C1 열린 항목 ② 판정. 커밋 없음(오케스트레이터 소관).
> D2c-api(501 라우트)와 ㉢(Ted 승인)은 여전히 남아 있다 — 이 기록은 동결 선언이 아니다.

### 구현한 검사 — 4종 (`gates/tools/seam_consistency.py` · 진입 `gates/tools/seam-consistency.sh`)

| 검사 | 무엇을 본다 | 비고 |
|---|---|---|
| **G-e** 산문 위임 참조 | 계약 산문 속 ① 계약 파일명 ② 백틱 op 이름(동사 접두 camelCase) ③ 이벤트 타입 점 표기 ④ 「X seam」 위임 문구 — 전부 실재 대상인지. 검사 258건 | 「이벤트/업로드 seam」(DR-7 실물)을 `업로드` 미등록 별칭으로 red 낸다 |
| **G-b** `const` 능력 주장 | 이벤트 `source: {const: X}` 마다 X 의 HTTP seam(allow-list `http-sources`)에 그 이벤트 타입을 명시하는 촉발 op 실재 + 그 op 이 집계 루트 `uploadId` 를 다루는지. 검사 7건 | `pipeline-worker` 는 `internal-sources` 에 이유와 함께 등재(HTTP 표면 없음). C1 의 `createUpload` 가 `upload.accepted` 촉발점으로 잡힌다 |
| **〈61〉-㉠** 정본 근거 대조 | git HEAD(또는 지정 기준선) 대비 **신설** op·스키마·파라미터 전수 — description 공란 red, 인용·`[정본 무근거]`/`[사용자 승인]` 표기 없음 red. 이번 개정분 신설 검사 대상 50건 전수 통과 | **근거의 내용이 옳은지는 안 본다**(㉠ 명세 그대로). 인용으로 세는 것에 **계약 상호 인용**(envelope.json·core-pipeline.json·core-viz.yaml·core-ai.yaml·common.json)을 포함시켰다 — 〈54〉 가 이벤트 seam 을 정본으로 확정했으므로 정본격 계약 인용도 근거다. 커밋 뒤에는 신설분이 기준선 안으로 들어가 대조 0건이 된다 — ㉠ 은 개정 회차 게이트이지 소급 감사가 아니다 |
| **〈61〉-㉡** 흐름 완주 | 사람 고정 fixture `gates/fixtures/seam-consistency/e04-flow.json`(E04-step-op-map.DRAFT 승계 + C1 개정분 반영, Q2 = `createDataset.projectIds` 접힘 판정 반영) 재생 — ㉡-1 op/이벤트 실재 · ㉡-2 식별자 종류 연결(+op 블록 실측 대조: fixture↔계약 드리프트도 red) · ㉡-3 source 촉발점 HTTP 실재 · ㉡-4 끊긴 자리 목록 출력 | **G-e 와 별도 검사·별도 fixture 다**(§7-7 — 축이 다르다) |

**미구현 — 감추지 않는다**: G-a(식별자 도달성)·G-c(짝 op 대칭)·G-d(공유 값 집합 재선언). §2-13 최소 채택선(G-e·G-b)대로이며 `gates/README.md` 게이트 표·상태 표·기계화 불가 절에 명기했다.

### 배선

- `gates/run.sh` — `seam-consistency` · `seam-consistency-selftest` 분기 2개 + `selftest)` 묶음에 1개 추가.
- `.github/workflows/ci.yml` contract-gates 잡에 `seam-consistency` 스텝 1개 추가.
- `gates/README.md` — 게이트 표 1행 · selftest 표 1행 · 상태 표 1행 · **§2-14 기계화 불가 절 이관**(+㉡ fixture 의존·㉠ 기준선 의존 한계 추가).
- allow-list — `gates/config/seam-consistency-allowlist.toml` (ge 별칭 · gb http/internal-sources · 집계 루트). fixture 는 자기 allow-list(`gates/fixtures/seam-consistency/allowlist.toml`)를 들고 다닌다(WU-D3b 와 같은 이유).

### 자기 증명 (`seam-consistency-selftest`) — 13 케이스 (green 4 · red 9), green

red fixture 목록 (`gates/fixtures/seam-consistency/red/`):
1. `ge-old-prose/` — **개정 전 `fe-core.yaml:13-16` 위임 산문 원문**(C1 §7-3 보존분 그대로) → G-e red. §3-3 이 요구한 오라클의 고정판이다.
2. `ge-ghost/` — 실재하지 않는 op(`createGhostUpload`)·파일(`upload-seam.yaml`) 참조 → G-e red.
3. `gb-no-trigger/` — `source: core-api` const 인데 촉발 op 0건 → G-b red (I-01·I-05 의 실물 모양).
4. `gb-no-root/` — 촉발 op 은 있는데 집계 루트 `uploadId` 를 안 다룸 → G-b red.
5. `citation-empty/`(+기준선 `citation-baseline/`) — 신설 op description 자체 없음 → ㉠ red.
6. `citation-nocite/` — description 은 있는데 인용·무근거 표기 없음 → ㉠ red.
7. `flow/missing-op.json` — 단계가 호출 불가능한 op 을 가리킴 → ㉡ red.
8. `flow/id-break.json` — 어느 단계도 생산 안 한 식별자를 입력 요구 → ㉡ red.
9. fixture 부재 → ㉡ red (skip 아님).

**개정 전 red 실측(§7-3 요구 기록)** — HEAD 판 seam 3종 위에서 게이트를 돌려 눈으로 봤다:
- G-e: `fe-core.yaml: 「이벤트/업로드 seam」 위임 — '업로드' 은 등록된 seam 이 아니다 (DR-7 · SEAM-AUDIT I-02)` — red.
- G-b: `upload.accepted 은 source 가 core-api const 인데 fe-core.yaml 에 그 이벤트를 촉발한다고 말하는 op 이 0건이다 (I-01·I-05)` — red.
개정 후 워킹트리에서는 둘 다 green — C1 의 산문 정정과 `createUpload` 가 정확히 이 red 를 닫는다.

### ㉡ 완주 재생 결과 (㉡-4)

- 단계 15건 재생(1 · 2~7·7′ 이벤트 · 8 · 9 · 10 · 11 · 12 · 13 · 14) — **끊긴 자리: 없음.**
- 의도적 이월 1건: **단계 11(직접 검색으로 부모 추가) — 계약 부재, P4 이월**(fe-core 위임 산문에 「P4 가 연다」 명기, §10-3). 끊김이 아니라 명시된 이월로 분류했다.
- 흐름 밖 외부 입력 2건(fixture 에 이유 명기): 단계 12·13 의 `projectId`(기존 프로젝트 — E-04 밖에서 이미 존재).

### 게이트 전 수트 결과 (개정 후 워킹트리 실측, 2026-08-23)

green — `planning-freshness` · `contract-lint` · `contract-breaking`(additive 증명) · `event-lint` · `event-breaking` · **`seam-consistency`** · `import-boundary` · `banned-import` · `ai-no-lineage-write` · `migration-single-head` · `rls-coverage` · `rls-effect` · `selftest`(6셋: contract 15 · event 33 · boundary 30 · db 43 · rls-effect 18 · **seam-consistency 13**).

red 2건 — 둘 다 이 레인과 무관하게 설계·환경 조건이다:
- `generated-up-to-date` — 미구현 red, 설계대로(§7-3 — 우회하지 않는다).
- `schema-diff` — 체인별 적용 DB URL(`COLAB_APPLIED_DB_URL_PLATFORM`·`_AI`) 이 이 세션에 없다. README 대로 URL 둘 다 주면 green 이 되는 환경 조건 red 이며, 이 레인 착수 전에도 같았다. 레인이 staging·DB 를 세우지 않았다(멈춤 규칙 3·4).

### C1 열린 항목 ② 판정 — 기준 격자 건수 불일치 (0~1 vs 〈58〉 0~2)

- **실측**: `common.json:79` `FileKind` description 이 「기준 격자 파일은 데이터셋당 0~1건」(DataModel §4.3 인용), `core-pipeline.json:39` `UploadAcceptedPayload.files` description 도 「0~1건」. **기계 제약은 어느 쪽에도 없다**(maxContains/maxItems 부재) — 갈린 것은 산문뿐이고, 스키마 자체는 이미 0~2 를 허용한다.
- **처분**: `common.json` 의 산문을 〈58〉 인용과 함께 **0~2건(+grid_axis·후주입 명기)** 으로 갱신했다 — description-only 라 additive 이고, 갱신 후 `contract-lint`·`contract-breaking`·`event-lint`·`event-breaking` 전부 green 실측.
- **남긴 것**: `core-pipeline.json:39` 의 「0~1건」 산문은 **이벤트 계약 동결(§2-1 — 한 글자도 안 고친다) 때문에 이번 회차에 고치지 않았다.** common.json 쪽 산문에 그 사실과 사유를 명기해 뒀다 — 다음 이벤트 개정 권한이 열리는 회차의 일감이다.

### 열린 항목 (닫지 않고 보고)

1. G-a·G-c·G-d 미구현 — 후속 회차. G-e·G-b 는 파생 증상이 아니라 DR-7 의 뿌리를 때리는 둘이라 먼저 세웠다(§2-13).
2. `core-pipeline.json:39` 「0~1건」 산문 드리프트 — 이벤트 개정 권한 필요(위 ② 판정).
3. ㉡ fixture(`e04-flow.json`)는 E04-step-op-map.DRAFT 승계본이다 — DRAFT 의 Ted 검토(㉢ 와 별도)가 아직이며, 표가 틀리면 ㉡ 이 틀린 흐름을 완주로 판정한다(〈61〉 경고 그대로).
4. D2c-api(501 라우트 11건 등록·1:1 diff 시험) 미착수 — 워킹트리는 여전히 「고아 계약 op 11건」 상태다(C1 기록 그대로).
5. ㉢(Ted 승인) 전 — 동결 아님.

---

## 마감 보고 (C1~C3) (2026-08-23 · D2c-C3 레인 — 마감 문서화)

> 커밋 없음(오케스트레이터 소관). **동결 선언 없음 — ㉢ 전이다.** ㉢ 제출 패키지 = `sessions/D2c-ted-approval.md`.

**판정 문구(§8 · 추기-3 반영)** — **「`STOP-1` 은 닫혔다. `DR-13` 은 닫혔다(2026-08-23). P2 착수 판정은 메인 세션/사용자의 몫으로 남는다 — 동결(㉢) 미실시·staging 미실측의 유보를 안고 선다.」** 「P2 를 열었다」라고 적지 않는다.

### 완료 정의 8항 대조 — 충족 5 · 미충족 3 (부분 완료로 「닫힘」이라 적지 않는다)

| 항 | 판정 | 근거 |
|---|---|---|
| 7-1 additive 증명 | ✅ | `contract-breaking` green(「No breaking changes … but the specs are different」) · 두 함정(`usageNote` required · `fileCount minimum:1`) 원형 유지 — C1 기록 |
| 7-2 501 표 | 🟧 부분 | **표 등재는 25 → 36(+11) 완료. 그러나 라우트 등록·`not_implemented.py`·1:1 diff 시험은 D2c-api 레인 몫으로 미착수** — 워킹트리는 **고아 계약 op 11건** 상태다. 커밋 불가 사유이기도 하다(한 커밋 = 계약 + 소비자, §7-5) |
| 7-3 게이트 | ✅ | 전 수트 green + `seam-consistency` green + selftest 13케이스(green 4 · red 9) + **개정 전 red 실측 기록**(G-e·G-b 둘 다 눈으로 봄 — C2 기록). 무관 red 2건은 설계·환경 조건(`generated-up-to-date` 미구현 red 설계대로 · `schema-diff` DB URL 부재) |
| 7-4 staging 배포 green | ⛔ **미실측** | 레인이 staging 을 건드리지 않았다(멈춤 규칙). 컨테이너 8 healthy·헬스 6종 200 은 **측정하지 않았다** — 커밋·배포 뒤 메인 세션 몫 |
| 7-5 `contracts/README.md` 규칙 5 리뷰 | ⛔ **미실시** | 커밋이 없어 PR 자체가 없다 — CODEOWNERS 리뷰는 커밋 이후 |
| 7-6 ㉠ 정본 근거 대조 | ✅ | 기계 검사 구현·신설 50건 전수 통과(근거의 **내용** 옳음은 안 본다 — ㉠ 명세 그대로) |
| 7-7 ㉡ 흐름 완주 | ✅ | 15단계 재생 · 끊긴 자리 0 · P4 이월 1건 명시. **단 fixture 는 E04-map DRAFT 승계본 — Ted 검토 전**(표가 틀리면 ㉡ 이 틀린 흐름을 완주로 판정한다) |
| 7-8 ㉢ Ted 승인 | ⛔ **미실시** | **동결하지 않았다.** ㉠·㉡ green 은 ㉢ 을 대신하지 않는다(§7-8 · `03-HANDOFF.md:134`). 제출 패키지를 `sessions/D2c-ted-approval.md` 로 마련했다 — **침묵은 승인이 아니다** |

### 남은 것 (이 WU 가 닫히려면)

1. **D2c-api** — 신설 11 op 라우트 501 등록 + 1:1 diff 시험 (고아 op 11건 해소).
2. **㉢** — Ted 명시 승인(`D2c-ted-approval.md` 제출) → 그 뒤에야 동결.
3. **커밋 → CODEOWNERS PR 리뷰(7-5) → staging 배포 green 실측(7-4)** — 전부 메인 세션 소관.
4. 이월 기록 유지 — G-a·G-c·G-d 미구현 · `core-pipeline.json:39` 「0~1건」 산문 드리프트(이벤트 개정 권한 필요) · `listPalettes` FE 중계 부재 · 검색 진입점 P4 · E04-map DRAFT 의 Ted 검토.


### ㉠ baseline 기록 (커밋 시점 재현성 — advisor 보완 3)

- **㉠(정본 근거 대조) 검사의 baseline ref = `0f6641b`** (개정 직전 HEAD). 이번 회차 신설 50건(op 11 · 스키마 7 · 파라미터 3 외)의 전수 대조는 이 ref 대비로 수행됐다. 개정 커밋이 들어가면 ㉠ 의 「신설」 집합이 비므로, 이 회차 감사의 재현은 `git diff 0f6641b -- contracts/seams/fe-core.yaml contracts/schemas/common.json` 으로 한다.
- `core-pipeline.json:39` 산문 드리프트는 **`DR-16`** 으로 등재됐다(`03-HANDOFF §5.5`).

## D2c-api 실행 기록 (2026-08-23)

C1 신설 11 op 의 고아 상태 해소 — 라우트 501 등록 + 1:1 diff 시험. 계약(`contracts/**`)·게이트 도구는 무수정.

### 라우트 11건 (`not_implemented.py` — 전부 `NOT_IMPLEMENTED_NO_STORE`, §5-확정 그대로)

| op | 라우트 |
|---|---|
| `createUpload` | POST `/uploads` |
| `getUploadStatus` | GET `/uploads/{uploadId}` |
| `listUploadLineageSuggestions` | GET `/uploads/{uploadId}/lineage-suggestions` |
| `createDataset` | POST `/datasets` |
| `updateDataset` | PATCH `/datasets/{datasetId}` |
| `addDatasetFile` | POST `/datasets/{datasetId}/files` |
| `replaceDatasetGridFile` | PUT `/datasets/{datasetId}/files/{fileId}` |
| `deleteDatasetGridFile` | DELETE `/datasets/{datasetId}/files/{fileId}` |
| `linkProjectDataset` | PUT `/projects/{projectId}/datasets/{datasetId}` |
| `createPreviewRender` | POST `/previews` |
| `getPreviewRender` | GET `/previews/{renderId}` |

### 501 표 25 → 36

- `OPERATIONS` 25 → **36** (NO_STORE 7 → 18 · P1 18 그대로). 오라클 갱신:
  `test_the_36_unimplemented_operations_are_exactly_these`(len==36) ·
  `test_operation_count_is_45`(계약 45 op) · `test_app_route_table_equals_contract` 1:1 diff green.
- 문서 정합: `services/core-api/README.md` 34→45 op · 실질의 5→9 · 501 29→36 (구 기록이 P1 이후에도 5/29 로 낡아 있었다 — 함께 바로잡음).

### 수트 결과

- **core-api pytest 166 passed** (일회용 `d2capi_pg` postgres:16-alpine + `setup-db.sh`, RESTART.md §④ 절차. 실행 후 컨테이너 폐기).
- **게이트 20종: green 18 · red 2** — red 는 예상 그대로: `generated-up-to-date`(미구현, 설계대로) · `schema-diff`(체인별 DB URL 부재 — 환경 조건). `seam-consistency`·selftest 전부 green.

### 남은 것

- 커밋(계약 + 소비자 한 커밋, §7-5) · ㉢ Ted 승인 · staging 배포 green 실측 — 메인 세션 소관 (변경 없음).
