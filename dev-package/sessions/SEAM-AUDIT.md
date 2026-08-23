# SEAM-AUDIT — 네 seam 간 정합 전수 감사 (`DR-7` 입력)

> **범위** `contracts/seams/{fe-core,core-viz,core-ai}.yaml` · `contracts/events/{envelope,core-pipeline}.json` · `contracts/schemas/common.json` · `contracts/README.md` · `gates/**` · `services/core-api/**`(실측 대조).
> **성격** 조사 + 소견. **아무것도 고치지 않았다** — `contracts/**` 는 동결이고 어느 seam 이 정본인지는 Ted 결정이다.
> **방법** 각 seam 의 op·스키마 전수 열람 → 식별자 도달성 · 능력 주장 · 생명주기 대칭 · 어휘 4축으로 교차 대조 → `services/core-api` 라우트 테이블 실측 대조.
> **표기** 측정 = 파일:줄 인용. 추론은 `[추론]`. 정본이 정하지 않은 것은 `[정본 무근거]`.

---

## 0. 한 줄 결론

- **`DR-7` 의 「두 seam 이 갈렸다」는 서술은 좁다.** 갈린 것은 두 seam 이 아니라 **`fe-core.yaml` 하나가 나머지 셋과 다른 세계를 그린 것**이고, 그 원인이 계약 본문에 문장으로 적혀 있다 — `fe-core.yaml:13-16` 이 **자기가 안 하는 일 셋을 다른 seam 에 넘겼는데, 셋 다 그 일을 받을 수 없는 seam 이다.**
- 그래서 이것은 **누락 3건이 아니라 위임 3건의 오배정**이다. op 을 셋 더해도 위임 문장이 남아 있는 한 다음 WU 가 같은 벽을 만난다.

---

## 1. 발견 목록 (심각도 순)

> `[K]` = 이미 알려진 3건 · `[N]` = 이번 감사 신규.

| # | 발견 | 근거 (file:line) |
|---|---|---|
| **I-01** `[K]` | **업로드 입구 부재 vs 이벤트 필수 발행.** `fe-core.yaml` 34 op 어디에도 업로드 진입점이 없다(`uploadId` grep 0건). 이벤트 계약은 `upload.accepted` 를 「core-api 가 내는 유일한 이벤트이며 파이프라인의 입구」로 선언하고 `source` 를 상수로 못 박았다 | `contracts/seams/fe-core.yaml:172`(`/datasets` get only) · `contracts/events/core-pipeline.json:33` · `:223` |
| **I-02** `[N]` | **위임 3줄이 전부 오배정이다 — 이게 뿌리다.** `fe-core.yaml:13-16` 은 ① 검색·계보제안을 `core-ai` 로 ② 업로드·파일파싱·**프로젝트 연결 생성**을 「이벤트/업로드 seam」으로 ③ 미리보기·타일·스크린샷을 `core-viz` 로 넘긴다. 그런데 `core-ai`·`core-viz` 는 **core-api 가 소비자인 내부 표면**이지 FE 표면이 아니고(`core-ai.yaml:50` · `core-viz.yaml:40`), 「업로드 seam」은 **존재하지 않는다**(`contracts/README.md:23-30` seam 목록 4개에 없음). **셋 다 FE 에서 도달할 길이 없는 곳으로 기능을 보냈다** | `fe-core.yaml:13-16` · `core-ai.yaml:50` · `core-viz.yaml:39-40` · `contracts/README.md:23-30` |
| **I-03** `[K]` | **`link`/`unlink` 비대칭.** `unlinkProjectDataset`(DELETE) 만 있고 `linkProjectDataset` 없음. 같은 계약이 `createProject` 는 준다 | `fe-core.yaml:830-836`(unlink) · `:717-719`(createProject) |
| **I-04** `[N]` | **위임받은 seam 이 그 일을 명시적으로 거부한다.** `fe-core.yaml:16` 이 「프로젝트 연결 생성」을 이벤트 seam 으로 넘겼는데, 이벤트 봉투는 `projectId`·`datasetId` 를 **싣지 않는다고 문장으로 금지**한다. 즉 위임 대상이 위임받은 일을 할 수 없다고 스스로 선언한 상태 | `fe-core.yaml:16` · `contracts/events/envelope.json:5`("`datasetId`·`projectId`… 를 두지 않는다") |
| **I-05** `[K]` | **`source: core-api` 능력 주장.** `UploadAccepted.source` 가 `core-api` 상수인데 core-api 의 자기 seam 에 그것을 촉발할 op 이 없다. `envelope.json:163` 은 `datasetId` 부재를 「사람이 데이터셋 만들기를 눌러야 생긴다」로 설명하지만 **그 버튼에 해당하는 op 도 없다** | `core-pipeline.json:223` · `envelope.json:163` |
| **I-06** `[N]` | **`uploadId` 는 FE 에 도달할 경로가 아예 없다.** `core-viz.yaml:257` 의 `RenderTarget.uploadId`(S-08)와 `envelope.json:162-163` 의 집계 루트가 같은 값을 쓰지만, `fe-core.yaml` 은 `uploadId` 를 **주지도 받지도 않는다**. → S-08 미등록 미리보기는 FE 에서 촉발 불가. **DR-7 의 「viz 도 같은 전제인가」에 대한 답 = 그렇다. viz·events 는 같은 업로드 세계를 쓰고, `fe-core` 만 다른 세계다** | `core-viz.yaml:255-259` · `envelope.json:162-163` · `fe-core.yaml`(grep `uploadId` 0건) |
| **I-07** `[N]` | **렌더 세계 전체가 FE 도달 불가 — 업로드와 무관하게도 깨져 있다.** `fe-core.yaml` 에 렌더·타일·스크린샷·팔레트 중계 op 이 **0건**이다. **등록된 데이터셋(`RenderTarget.datasetId`)의 미리보기조차** FE 가 요청할 자리가 없고, `renderId`(스크린샷 입력, `core-viz.yaml:483-486`)를 FE 가 얻을 길도 없다. E-03 상세 미리보기가 계약상 미도달 | `fe-core.yaml:16`(위임만) · `core-viz.yaml:58-61` · `:192-195` · `:483-486` |
| **I-08** `[N]` | **AI seam 도 같은 모양.** `searchDatasets`·`suggestLineage` 는 core-api 소비 전용인데 `fe-core` 에 검색 op 도 계보제안 op 도 없다. S-06(데이터 찾기) 화면이 FE→core 진입점을 못 갖는다 | `core-ai.yaml:67` · `:99` · `fe-core.yaml:14` |
| **I-09** `[N]` | **AI 계보제안 입력이 통째로 데드코드.** `UploadedFileMeta` 는 헤더 파싱 결과에서만 나오고(`HeaderParsedPayload`), `datasetNameDraft`·`subject` 는 등록 폼 값이다. 업로드 세계와 등록 폼이 없으면 `suggestLineage` 는 채울 수 없는 요청이다 | `core-ai.yaml:177-187` · `:189-195` · `core-pipeline.json:83` |
| **I-10** `[N]` | **데이터셋 생명주기에 C 도 U 도 없다.** `/datasets` 는 GET 뿐이고, `/datasets/{id}` 는 GET·DELETE 뿐이다. **`createDataset` 뿐 아니라 수정 op 자체가 없다** — 이름·주제·요약은 정본이 「사람이 적는 정보」로 못 박은 값인데(`DATAMODEL-BASELINE.md:58`) 쓰는 길이 계약에 없다. 프로젝트는 C·R·U·D + 상태전환이 전부 있다 | `fe-core.yaml:172` · `:234-257` · `:675-807` · `DATAMODEL-BASELINE.md:58` |
| **I-11** `[N]` | **`accessState`(열림↔잠김) 전환 op 없음.** 값은 응답 3곳에 실리는데(`DatasetRow`·`DatasetDetail`·`ProjectDatasetRow`) 바꾸는 자리가 없다. `updateLab` 은 연구실 기본값만 바꾼다 | `common.json:66` · `fe-core.yaml:1390` · `:1510` · `:1747` · `:1202` |
| **I-12** `[N]` | **`usageNote` 쓰기 경로 없음.** 「연결마다 붙는 활용 의미 문장」이 응답에만 있다. `link` op 이 없으니 필연이지만, **`link` 를 「op 하나 더하기」로 끝낼 수 없는 이유**를 이 필드가 증명한다 — 본문 있는 N:N 연결이다 | `fe-core.yaml:1751` · `:1481`(DatasetProjectUse.usageNote) |
| **I-13** `[N]` | **계보 관계 수정(U) 없음.** `addLineageParent`·`removeLineageParent` 뿐이라 `method`(가공 방식 한 줄)를 고치려면 관계를 지웠다 다시 만들어야 하고, 그러면 `confirmedAt`·`origin` 기록이 갈린다 | `fe-core.yaml:380` · `:414` · `:1631-1641` |
| **I-14** `[N]` | **접근 허용(`AccessGrant`) 조회·회수 op 없음.** 만료일만 계약에 있고 목록·조기 회수 자리가 없다 | `fe-core.yaml:1280-1294` |
| **I-15** `[N]` | **⚠ 어휘 드리프트 — `〈51〉`·`F-2` 가 계약에 도달하지 않았다.** 이벤트 계약이 그릴 수 있는 포맷으로 **`GRIB … HDF5`** 를 그대로 적어 두고 있고 예시 목록도 `grib`·`HDF5` 다. v2 지원은 `NetCDF·Binary·HDF4·GeoTIFF`(`〈51〉`), `.hdf` 는 HDF4(`F-2`). **`P2.md:150`(STOP-2)은 정본 문구만 지적했고 계약 쪽은 아무도 안 봤다** | `core-pipeline.json:59` · `:54` ↔ `PLAN-SoT.md:301` · `SEED-DATA.md:21` · `P2.md:150` |
| **I-16** `[N]` | **포맷 표기가 세 seam 에서 세 가지다.** 이벤트는 소문자 확장자 + `HDF5` 혼재, AI seam 예시는 `NetCDF`, FE 는 자유 문자열. 같은 값이 표기를 바꿔 가며 흐른다 | `core-pipeline.json:54` · `core-ai.yaml:206` · `fe-core.yaml:1442` |
| **I-17** `[N]` | **주제 4값이 어느 계약에도 닫혀 있지 않다.** 정본은 고정 목록 4값인데 `common.json` 에 `Topic` 정의가 없고 네 자리 전부 자유 문자열이다. `CLAUDE.md §3-6`(값 집합은 한 곳) 관점에서 빈 자리 | `fe-core.yaml:1362` · `:983-986` · `:1852` · `core-ai.yaml:184` · `ONTOLOGY-SCOPE.md:59` |
| **I-18** `[N]` | **실패 사유 8값이 FE 로 갈 자리가 없다.** `FailureReason` 은 「화면이 문구를 그린다」를 전제로 이벤트에만 두었는데, 업로드 상태를 FE 에 전하는 op 이 없으므로 그 전제가 성립하지 않는다 | `envelope.json:85-97` · `fe-core.yaml`(업로드 상태 op 0건) |
| **I-19** `[N]` | **렌더 실패 3종이 값 집합으로 없다.** `RenderJob.failure.code` 가 「정본의 실패 종류를 구분한다」고 하지만 `ErrorEnvelope.code` 는 자유 문자열이고 3종을 세는 곳이 없다 | `core-viz.yaml:348-353` · `common.json:28` |
| **I-20** `[N]` | **`fileId` 의 세계 간 동일성이 규정되지 않았다.** 이벤트의 `fileId` 는 「등록 전이라 D3 파일 레코드가 아직 없다」고 명시하는데, `core-viz` 는 `datasetId` 대상이든 `uploadId` 대상이든 같은 `fileIds` 필드를 쓴다. 등록 시 같은 ULID 가 승계되는지 아무 계약도 말하지 않는다 → `[정본 무근거]` | `core-pipeline.json:9` · `:14` · `core-viz.yaml:260-265` · `fe-core.yaml:1559` |
| **I-21** `[N]` | **능력 주장 — 계약이 자기 방어 장치를 있다고 말한다.** `contracts/README.md:18-19` 는 emit 충돌을 CI 가 거부하고 생성물 최신성을 diff 로 검증한다고 단정하는데, `generated-up-to-date` 게이트는 **미구현(red)** 이다 | `contracts/README.md:18-19` ↔ `gates/README.md:40` |
| **I-22** `[N]` | **없는 화면에 위임하는 코드가 이미 배포돼 있다.** `getProject` 가 `datasets: []` 를 하드코딩하고 주석이 「업로드 화면(E-04)이 맡는다」고 적었다. 계약은 이 배열을 required + 「전부 담는다」로 규정한다 — 스키마 위반은 아니지만 **항상 거짓인 응답**이다 | `services/core-api/src/colab_core/app/routes/project.py:78` · `fe-core.yaml:1770` |
| **I-23** | **구현 ↔ 계약은 정확히 1:1 이다(드리프트 0).** 34 op ↔ 34 라우트, 고아 라우트 0, 미등록 계약 op 0. 라이브 9 · 501 스텁 25(`㊹` 두 코드 준수). `/healthz` 만 스키마 밖 | `services/core-api/src/colab_core/app/routes/not_implemented.py:34` · `:80` · `app/main.py:19` · `:40` |
| **I-24** | **이벤트 소비자가 존재하지 않는다.** `pipeline-worker` 는 헬스 서버뿐이고 `d5_ingestion.py` 는 1줄, outbox 는 README 산문뿐. core-api 에도 outbox·publish 코드 0건 | `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py` · `services/pipeline-worker/README.md:9`·`:25` |
| **I-25** | **드리프트 아님(확인용).** `labId` 는 이벤트·AI seam 이 명시 전달, FE seam 은 금지 — 셋 다 근거를 적어 뒀고 일관된 설계다 | `envelope.json:154-155` · `core-ai.yaml:23-29` · `fe-core.yaml:24-25` |

---

## 2. 사용자가 준 3건의 검증 결과

| 주장 | 판정 | 보정 |
|---|---|---|
| ① `fe-core` 29 path / 34 op · 업로드 입구·`createDataset` 없음 · `/datasets` GET-only | **확인** | path·op 수는 `D2-fe-core.md:7` 과 실측 일치. **다만 더 넓다** — 없는 것은 `createDataset` 만이 아니라 **데이터셋의 U(수정) 전체와 잠금 전환**이다(I-10·I-11) |
| ② `upload.accepted` 의 `source` 가 `core-api` 상수 · `envelope.json` 이 `uploadId` 를 집계 루트로 두고 `datasetId` 부재를 설명 | **확인** | 상수는 `core-pipeline.json:223`, 설명은 `envelope.json:163`. **보정 — 이건 단발이 아니라 계열이다**(§3) |
| ③ `unlinkProjectDataset` 만 있고 `linkProjectDataset` 없음 · `createProject` 는 있음 | **확인** | 보정 — **누락이 아니라 위임**이다. `fe-core.yaml:16` 이 연결 생성을 이벤트 seam 으로 넘겼고, 그 seam 은 `projectId` 를 싣지 않는다고 선언한다(I-04). 즉 「빠뜨렸다」가 아니라 **「보냈는데 받을 곳이 없었다」** |

---

## 3. 능력 주장은 계열이다 (사건 목록이 아니라 클래스)

> **정의** — 계약이 어떤 단위가 무엇을 한다고 단정하는데, 그 단위의 자기 seam 에 그것을 할 수단이 없는 상태.

| 사례 | 주장 | 수단 부재 |
|---|---|---|
| **C-1** | core-api 가 `upload.accepted` 를 낸다 (`core-pipeline.json:223`) | 촉발할 HTTP op 0건 (I-01) |
| **C-2** | 이벤트/업로드 seam 이 프로젝트 연결 생성을 맡는다 (`fe-core.yaml:16`) | 그 seam 이 존재하지 않고, 이벤트 봉투는 `projectId` 를 금지 (I-04) |
| **C-3** | `core-ai`·`core-viz` 가 검색·계보제안·미리보기를 맡는다 (`fe-core.yaml:14`·`:16`) | 둘 다 core-api 전용 내부 표면이라 FE 요청을 받을 수 없다 (I-07·I-08) |
| **C-4** | 그림은 `createRender(RenderTarget.uploadId)` 가 그린다 (`core-pipeline.json:163`) | `uploadId` 가 FE·core-api 표면에 존재하지 않는다 (I-06) |
| **C-5** | 화면이 정본 §9 실패 문구를 그린다 (`envelope.json:86`) | 실패를 FE 로 전하는 op 0건 (I-18) |
| **C-6** | CI 가 emit 충돌을 거부하고 생성물 최신성을 검증한다 (`contracts/README.md:18-19`) | `generated-up-to-date` 미구현 (I-21) |
| **C-7** | `getProject.datasets` 는 전부 담는다 (`fe-core.yaml:1770`) | 담는 op 이 없어 구현이 `[]` 하드코딩 (I-22) |

- **공통 모양** — 주장은 **산문**에, 부재는 **op 표**에 있다. 게이트가 op 표만 보므로 전부 통과한다.
- **`[추론]`** — C-2·C-3 이 같은 문단(`fe-core.yaml:13-16`)에서 나온 것을 보면, 이 계열은 **seam 동결 시점에 「내 것이 아닌 것」을 목록으로 밀어내고 받는 쪽을 확인하지 않은 한 번의 습관**에서 왔을 가능성이 크다. 측정이 아니라 추론이다.

---

## 4. 결정 선택지 (Ted 몫 — 나는 고르지 않는다)

### 선행 질문 — 업로드 세계의 정본은 어느 쪽인가

- **이벤트 계약 쪽에 근거가 압도적이다(측정).** `envelope.json:162-163` 은 `uploadId` 를 집계 루트로 두고 `datasetId` 부재를 정본 인용으로 정당화했고, `core-viz.yaml:255-259` 가 같은 전제를 공유한다. **네 seam 중 셋이 같은 세계다.**
- **HTTP seam 쪽 부재에는 근거가 없다.** `fe-core.yaml:16` 이 남긴 것은 이유가 아니라 **오배정된 위임 한 줄**이다. 「없는 이유」가 아니라 「남에게 넘겼다」로 적혀 있고, 그 남이 없다.

### 선택지 A — 최소 변경 (op 3개 추가, HTTP seam 을 정본으로 취급)

1. **푸는 것** — P2 즉시 착수 가능(업로드 입구 + `createDataset`), P5 의 `link` 확보. 가장 빠르다(계약 편집 1회 + 게이트 재실행).
2. **비용** — `contracts` 동결 해제 1회 · CODEOWNERS 리뷰 · `contract-breaking` 판정.
3. **남는 것 (⚠ 많다)** — `uploadId`·`renderId` 는 여전히 FE 표면에 없다 → **S-08 도 E-03 미리보기도 여전히 불가**(I-06·I-07) → **P3(시각화)·S3(실데이터 E2E)이 같은 벽을 만난다.** 데이터셋 U·잠금 전환 부재(I-10·I-11) 그대로 → **P4/P6 이 만난다.** 검색 진입점 부재(I-08) 그대로 → **P4·K4 가 만난다.** `usageNote`(I-12)·계보 수정(I-13) 그대로. **`fe-core.yaml:13-16` 의 오배정 위임 3줄이 그대로 남아** 다음 세션이 또 「저 seam 이 맡는다」를 읽고 같은 결론에 도달한다. **즉 A 는 `DR-7` 의 자생 성질을 그대로 둔다 — 막힌 목록이 2→3 으로 자란 그 메커니즘이 살아 있다.**

### 선택지 B — 이벤트 seam 을 정본으로 확정하고 업로드 세계를 FE 표면에 연다

1. **푸는 것** — P2·S2 + **S-08 · P3 · S3 까지 한 번에**. 업로드 표면(입구 · `uploadId` 상태 조회 · 등록 전환 = `createDataset` · 렌더 중계)을 한 벌로 설계한다.
2. **비용** — 계약 편집 범위가 A 의 3~4배(op 6~9개 `[추론]`), 화면(E-04·S-08) 정본 재확인 필요, `fileId` 승계 규칙을 정해야 한다(I-20 `[정본 무근거]` → Ted 답 필요).
3. **남는 것** — 업로드·렌더 밖의 비대칭은 **그대로**다: 데이터셋 U·잠금 전환(I-10·I-11) → P6·P8 이 만난다. `linkProjectDataset`·`usageNote`(I-03·I-12) → **B 에 명시적으로 넣지 않으면 P5 가 그대로 막힌다** — 업로드 세계 결정으로는 안 풀리는, 성질이 다른 항목이다. 어휘 드리프트(I-15~I-19) 미해소. 위임 3줄 중 ①③은 고쳐지지만 ②의 「업로드 seam」 표현은 명시 정정 필요.

### 선택지 C — 전면 재조정 (도달성 기준으로 seam 경계를 다시 긋는다)

1. **푸는 것** — 위 전부. 판정 기준을 하나로 세운다: **「FE 가 이 기능에 도달할 수 있는가」** — `fe-core.yaml:13-16` 을 폐기하고, 내부 seam(`core-ai`·`core-viz`)의 기능마다 FE 중계 op 을 명시한다.
2. **비용** — 가장 크다. seam 3개 동시 개정 + 동결 재선언. P2 착수가 최소 한 세션 밀린다 `[추론]`.
3. **남는 것** — 어휘 드리프트(I-15~I-19)는 **자동으로 안 풀린다**(별도 항목). `fileId` 승계·주제 4값 정본 내부 불일치(`ONTOLOGY-SCOPE.md:64`)는 **Ted 답 없이는 C 로도 못 닫는다.** 그 둘을 빼면 남는 계약 비정합은 없다.

### 선택지 D — 결정 유예 · 게이트 먼저

1. **푸는 것** — 아무 WU 도 안 푼다. 대신 **다음 오배정을 기계가 잡는다.**
2. **비용** — P2·S2 차단 지속.
3. **남는 것** — I-01~I-22 전부. **게이트는 이미 난 사고를 red 로 만들 뿐 고르지 않는다.** 다만 D 는 A·B·C 어느 것과도 병행 가능하다.

### 권고

**B 를 정본 결정으로 삼되, 같은 결정문에 C 의 판정 기준 한 줄(「FE 도달성」)과 `linkProjectDataset`+`usageNote` 를 함께 못 박고, D 의 게이트를 D2b 로 병행하는 것을 권한다.** 이벤트·viz·events 세 계약이 이미 같은 업로드 세계를 근거와 함께 그렸고 `fe-core` 의 부재만 근거가 없으므로, 정본을 HTTP 쪽으로 잡으면 **근거 있는 셋을 근거 없는 하나에 맞춰 되돌리게 된다.** A 는 `DR-7` 의 자생 성질(막힌 WU 2→3)을 손대지 않은 채 세 칸만 메우므로, P3·P4·P5 에서 같은 결정을 다시 해야 한다 — 가장 싸 보이지만 결정 횟수는 늘어난다. **다만 어느 선택지도 어휘 드리프트(I-15)와 `fileId` 승계(I-20)를 자동으로 닫지 못한다 — 별도 두 줄의 결정이 필요하다.**

---

## 5. seam 정합 게이트는 무엇을 봐야 하나 (`DR-7` 의 나머지 절반)

### 기계화 가능 (권고 — 이 5종이면 I-01~I-08·I-21 이 전부 red 였다)

| 검사 | 방법 | 잡히는 것 |
|---|---|---|
| **G-a 식별자 도달성** | 네 계약의 모든 ID 필드를 수집 → 각 ID 마다 「생산하는 op/이벤트」와 「소비하는 op/이벤트」가 최소 1개씩 있는지 그래프로 판정 | I-01·I-06·I-07(`uploadId`·`renderId` 소비만 있고 생산 없음) |
| **G-b `const` 능력 주장** | 이벤트의 `source: {const: X}` 마다, X 의 seam 파일에 op 이 1개 이상 존재하는지 + 그 op 이 해당 집계 루트 ID 를 다루는지 | I-01·I-05 |
| **G-c 짝 op 대칭** | 경로 패턴에서 `create↔delete` · `link↔unlink` 쌍을 뽑아 한쪽만 있는 자원을 목록으로 red (예외는 allow-list 에 **이유와 함께** 등재) | I-03·I-10·I-11·I-13·I-14 |
| **G-d 공유 값 집합 재선언** | `common.json` 에 정의된 enum 과 의미가 같은 필드가 다른 계약에서 자유 문자열로 등장하는지(필드명 사전 기반) | I-16·I-17·I-19 |
| **G-e 산문 위임 참조 검증** | 계약 주석·description 안의 seam 파일명·op 이름 언급을 정규식으로 뽑아 **실재하는 파일/op 인지** 확인 | **I-02·I-04·I-21 — `fe-core.yaml:16` 이 이 검사 하나로 red 였다** |

### 기계화 불가 (게이트가 못 하는 것 — 정직하게)

- **어느 seam 이 정본인가** — 값 판단이다. 게이트는 「갈렸다」까지만 말한다.
- **자유 문자열이 의도적 개방인지 누락인지** — `core-pipeline.json:54` 는 「정본이 `등`으로 열어 뒀다」는 이유가 붙은 의도적 개방이고, `fe-core.yaml:1362` 의 `topic` 은 이유가 없다. **둘의 차이는 산문에만 있다.** G-d 는 둘 다 red 로 만들고 사람이 allow-list 로 가른다.
- **정본 문구 ↔ 계약 어휘 대조(I-15)** — 정본이 md 산문이라 값 집합을 기계가 못 뽑는다. `〈51〉` 같은 결정을 계약에 반영하는 것은 **결정 기록 → 계약 반영 체크리스트**(사람 절차)로 갈 수밖에 없다 `[추론]`.
- **화면 요구 충족 여부** — op 이 있어도 그 화면을 그릴 수 있는지는 판정 불가.

---

## 6. 한계 — 확정하지 못한 것

- **정본(260818) 원문을 열지 않았다.** 이 감사는 `contracts/**` + `dev-package/**` 인용 기준이다. 계약이 인용한 정본 문구가 실제 정본과 같은지는 **확인하지 않았다** — `P2.md:150`(STOP-2)이 최소 한 곳의 불일치를 이미 보고했다.
- **`frontend/` 를 보지 않았다.** FE 가 실제로 무엇을 호출하는지 미측정 — I-06~I-08 의 「FE 도달 불가」는 **계약상 판정**이고 코드 실측이 아니다.
- **`db/` 스키마 대조를 하지 않았다.** I-11(`accessState` 전환)·I-20(`fileId` 승계)은 DB 쪽에 저장 자리가 있는지에 따라 심각도가 달라진다.
- **`[정본 무근거]`** — ① `fileId` 가 업로드 세계에서 D3 등록 후로 승계되는지(I-20) ② 주제 고정 목록의 4번째 값(`토지피복·LULC` vs `유출·수문`, `ONTOLOGY-SCOPE.md:64` 의 정본 내부 불일치가 미해소, I-17) ③ 렌더 실패 3종의 코드값(I-19) ④ 「업로드 seam」이 별도 seam 으로 존재해야 하는지, 아니면 `fe-core` 안의 op 이어야 하는지(I-02·선택지 B/C 의 갈림).
- **선택지의 op 개수 추정은 `[추론]`** 이다 — 실제 설계 없이 규모만 가늠했다.
