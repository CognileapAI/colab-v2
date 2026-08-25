# WU-V2-INPUTS — 격자 후주입 선택지의 `[미확인]` 4건 조사

> **성격 = 읽기 전용 조사.** 코드·계약·마이그레이션 무수정 · 커밋 0건.
> **판정자 = Ted.** 이 문서는 결정하지 않는다. 권고는 **★** 로 구분한다.
> 상위 문서 = `dev-package/sessions/WU-V2-GRID-POSTINJECT-OPTIONS.md`.
> 근거 표기 = `file:line`(`cat -n`·`sed -n` 확인) · 미측정은 `[미확인]`.

---

## 1. HSR 기준 격자 파일 실측 바이트

### 1.1 측정값

| 파일 | 바이트 | dtype | 배열 형상 | 헤더 |
|---|---|---|---|---|
| `Lat_HSR.npy` | **26,562,948** | `<f4` | `(2881, 2305)` | NPY v1.0 · 128 B |
| `Lon_HSR.npy` | **26,562,948** | `<f4` | `(2881, 2305)` | NPY v1.0 · 128 B |
| **위·경도 쌍 합계** | **53,125,896** | — | — | — |
| `rdr_500m_latlon.nc` | **11,471,526** | `<f4`(변수 `lat`·`lon`) | `(2881, 2305)` 각각 | HDF5 시그니처 `\x89HDF\r\x1a\n` = NetCDF4 |

- 위치 = `03 Reference-Data/02.File-format/file_format_3_bin/04.Lat_Lon_info/`(원천 루트 = `DATA-REFERENCE.md:38` · `PLAN-SoT.md:297` `㊾`)
- 측정 명령 —
  - 바이트 = `find "<원천>/03 Reference-Data" \( -name "Lat_HSR.npy" -o -name "Lon_HSR.npy" -o -name "rdr_500m_latlon.nc" \) -printf "%s\t%p\n"`
  - dtype·형상 = `head -c 128 <파일> | cat -v` → `{'descr': '<f4', 'fortran_order': False, 'shape': (2881, 2305), }`
  - `.nc` 매직 = `head -c 400 <파일> | cat -v` → `\x89HDF` · 내부 객체명 `nx`·`ny`·`lon`·`lat` 관측
- 산술 대조 = `128 + 2881 × 2305 × 4 = 26,562,948` — **파일 크기와 정확히 일치**. `DATA-REFERENCE.md:44` 의 형상·dtype 기재와 일치
- `.nc` 는 비압축 환산 `2 × 26,562,820 = 53,125,640 B` 대비 **11,471,526 B** — 압축률 약 **4.6 : 1**. ⚠ 다만 **압축 해제 후 상주 메모리는 약 53 MB** 이고, `DATA-REFERENCE.md:76` 이 「HSR 격자의 정본은 `.npy` 쌍」으로 판정해 둔 상태다(`.nc` 는 표준위도 부재로 불완전)

### 1.2 요청 본문 적재 비용 — 계약별

| 경로 | 인코딩 | 실적재량(쌍 기준) |
|---|---|---|
| `createUpload`·`addUploadFile`·`addDatasetFile` (FE → core-api) | `multipart/form-data`(`fe-core.yaml:222-224`·`:290-297`·`:767-769`) | **53,125,896 B** — 바이너리 그대로 |
| core-api → worker 동기 중계 (권고안 ㈑ 가상) | **`relay.py` 는 JSON 전용** — `_request` 가 `json.dumps(body)` 로만 본문을 만든다(`services/core-api/src/colab_core/app/relay.py:34`) | base64 환산 **약 70,834,528 B**(4/3 배 + 개행 없음 기준) · ⚠ **[미측정]** — 실제로 보낸 적이 없다 |

- ⚠ **현행 중계 계층에 바이너리 전송 경로가 없다.** `_request` 시그니처가 `body: dict[str, Any] | None`(`relay.py:32-33`)이고 `Content-Type` 을 `application/json` 으로 고정한다(`relay.py:37`). 격자 바이트를 동기 중계에 실으려면 **멀티파트 지원 신설 또는 base64 승격**이 필요하다 — 어느 쪽도 현행 코드에 없다
- **대안 = 바이트를 안 싣는다.** core-api 와 worker 가 **같은 named volume `uploads`** 를 공유한다(`infra/staging/compose.i2.yml` worker 블록 `volumes: uploads:/var/lib/colab/uploads` · core-api 동일 볼륨). 즉 동기 요청 본문에는 **`storage_key` 문자열만** 실으면 되고, 바이트는 볼륨을 통해 전달된다. 이 경우 본문 크기는 수백 바이트다
- 타임아웃 관점 — `RELAY_TIMEOUT_SECONDS = 10`(`relay.py:25`), 재시도 로직 **0건**. 축 판별 소요시간은 **`[미확인]`**(`axis.py` 를 격자 실물에 대해 시간 측정한 기록 없음)

---

## 2. 동기 호출 대 비동기 호출 — 판단기준

### 2.1 정본 근거 — 존재한다

`dev-package/PLAN-SoT.md:75-78` seam 표 —

| seam | 성격 | 계약 형식 |
|---|---|---|
| FE ↔ core-api | sync, 드리프트 최다 발생 지점 | OpenAPI 3.1 |
| core-api ↔ viz-render | sync | OpenAPI 3.1 |
| core-api ↔ ai-service | sync, 실패 허용 | OpenAPI 3.1 + degraded 응답 규격 필수 |
| **core-api ↔ pipeline-worker** | **async** | 이벤트 봉투 JSON-Schema + 멱등 키 + DLQ |

- ⭑ **권고안 ㈑(core-api 가 worker 에 동기 요청)는 이 표의 마지막 행과 정면으로 충돌한다.** 표는 이 seam 을 `async` 로 못 박았다
- `dev-package/DOMAINS.md:68` — D5 만 outbox·워커·별도 런타임을 갖는 근거 = **작업량 프로파일**(버스티·고 CPU·고 메모리)
- `PLAN-SoT.md:66` — 「AI 응답 대기가 업로드 트랜잭션을 잡고 있지 않는다」. 이는 **화면 대기 UX** 규정이고 배선 방식 규정이 아니다
- `PLAN-SoT.md:348` `〈79〉` — **㈏(core-api 가 동기로 축 판별) 기각 완료**. 근거 = `gates/config/boundaries.toml:13-17` 이 core-api 에 `h5py`·`netCDF4` 등을 금지해 **통합 `.nc` 격자를 열지 못한다**. ⚠ **권고안 ㈑ 는 ㈏ 와 다르다** — ㈑ 는 core-api 가 직접 열지 않고 worker 에 묻는 형태라 `boundaries.toml` 은 위반하지 않는다. **기각 사유가 그대로 옮겨붙지는 않는다**
- ⭑ **「어떤 성질이면 동기인가」를 명문화한 문서는 없다** — `[정본 무근거]`. seam 표는 **대상별 열거**이지 판단기준이 아니다. 아래 §2.3 은 이 조사가 귀납한 제안이며 정본이 아니다

### 2.2 현행 실물 — 귀납 근거

**동기 중계 5건** (전부 `relay.py` · `urllib.request` · 타임아웃 10 s · 재시도 0)

| op | 대상 | 실패 시 사용자가 보는 것 | 근거 |
|---|---|---|---|
| `listPalettes` | viz-render `GET /palettes` | 503 `RENDER_UNAVAILABLE` | `routes/preview.py:56-57`·`:65-67` |
| `createPreviewRender` | viz-render `POST /renders` | 503 `RENDER_UNAVAILABLE` | `routes/preview.py:79`·`:99-101` |
| `getPreviewRender` | viz-render `GET /renders/{id}` | 원격 404 → 404 · 미도달 → 503 | `routes/preview.py:119-130` |
| 검색 해석 | ai-service `POST /searches` | 503 `SEARCH_UNAVAILABLE` | `routes/catalog.py:237-248` · `relay.py:190-224` |
| 계보 제안 | ai-service `POST /lineage-suggestions` | **200 + 빈 제안 + `degraded: true`** | `relay.py:113-121`·`:297-315`·`:266-278` (`〈87〉-㉯`) |

**비동기(outbox) 1건**

- core-api 가 발행하는 이벤트는 **`upload.accepted` 하나뿐**(`d5_ingestion.py:22-24`·`:227`). 멱등 키 = `<type>:<uploadId>`(`d5_ingestion.py:145-147`), 삽입은 `ON CONFLICT DO NOTHING`(`d5_ingestion.py:106-113`)
- `upload.failed`·`upload.ready` 는 **worker 가 발행**하고 core-api 는 읽기만 한다(`d5_ingestion.py:66-72`·`:190-211`)
- 결과 회수 창구 = `getUploadStatus`(`fe-core.yaml:379-395` · `routes/ingestion.py:226-251`) — `ready`·`gridRejections`·`failure`
- ⚠ `reap_expired()`(`d5_ingestion.py:254`)는 core-api 안에 **생산 호출자가 없다** — 회수는 worker 의 `reap_expired_uploads` 가 한다(§4)

**귀납 — 무엇이 동기이고 무엇이 비동기인가**

| 성질 | 동기 5건 | 비동기 1건 |
|---|---|---|
| 응답이 요청의 결과인가 | 그렇다 — 팔레트 목록·렌더 핸들·해석·제안이 곧 응답 본문 | 아니다 — `uploadId`·`fileId` 만 즉시 응답, 나머지는 나중 |
| 소요 시간 | 10 s 상한 안(`relay.py:25`) | 상한 없음 — 파일 크기에 비례 |
| 자원 프로파일 | 요청 스레드 한 개 | 버스티·고 CPU·고 메모리(`DOMAINS.md:68`) |
| 실패 시 화면 | 즉시 503 또는 degraded 200 | 상태 폴링이 실패 사유를 말함 |
| 재시도 주체 | 사람(다시 누른다) — 코드 재시도 0건 | 기계(멱등 키 + DLQ) |

### 2.3 ★ 제안 — 판정 가능한 판단기준

> 다섯 문항. **①이 「아니다」면 그 시점에 비동기 확정**이고 나머지는 안 묻는다.
> ②~⑤ 중 **하나라도 「비동기」면 비동기**다 — 동기는 다섯 개가 모두 동기를 가리킬 때만 성립한다.

| 문항 | 동기 조건 | 비동기 조건 |
|---|---|---|
| **① 결과 필요성** — 호출 응답이 이번 HTTP 응답 본문·상태코드를 정하는 데 필요한가 | 필요하다 | 불필요하다 |
| **② 시간 상한** — 최악 소요가 `RELAY_TIMEOUT_SECONDS`(10 s) 안에 결정적으로 들어가는가 | 들어간다 | 들어가지 않거나 **입력 크기에 비례해 상한이 없다** |
| **③ 자원 프로파일** — 대상 작업이 요청 스레드 하나로 끝나는가 | 끝난다 | 버스티·고 CPU·고 메모리 |
| **④ 실패 표현** — 실패했을 때 사용자에게 보일 정직한 즉답(503 또는 degraded 200)이 있는가 | 있다 | 없다 — 「처리 중」을 거쳐야만 말할 수 있다 |
| **⑤ 재시도 주체** — 실패를 사람이 같은 버튼을 다시 눌러 복구하는가 | 사람 | 기계(멱등 키 필수) |

**대조 검증 — 현행 6건에 적용**

| 대상 | ① | ② | ③ | ④ | ⑤ | 판정 | 실물 |
|---|---|---|---|---|---|---|---|
| 팔레트 목록 | 동 | 동 | 동 | 동 | 동 | **동기** | 동기 ✅ |
| 미리보기 생성 요청 | 동 | 동 | 동 | 동 | 동 | **동기** | 동기 ✅ |
| 검색 해석 | 동 | 동 | 동 | 동 | 동 | **동기** | 동기 ✅ |
| 계보 제안 | 동 | 동 | 동 | 동 | 동 | **동기** | 동기 ✅ |
| 업로드 접수 후 포맷 감지 | **비** | 비 | 비 | 비 | 비 | **비동기** | 비동기 ✅ |
| 만료 업로드 회수 | **비** | 동 | 동 | 비 | 비 | **비동기** | 비동기 ✅ |

**부칙 2건**

- **부칙 A — 경계 금칙 우선.** ①~⑤ 가 동기를 가리켜도 그 작업이 `gates/config/boundaries.toml` 상 호출자 배포 단위에 금지된 라이브러리를 요구하면 **동기 직접 실행은 불가**다. 남는 선택지는 ㈑(다른 단위에 동기로 묻기) 또는 비동기다
- **부칙 B — 본문 크기.** 동기로 판정돼도 요청 본문이 **1 MB 를 넘으면 바이트를 싣지 않는다** — 공유 볼륨의 `storage_key` 를 싣는다. 근거 = `relay.py:34` 가 JSON 전용이라 바이너리는 base64 로 4/3 배가 된다

### 2.4 ★ 격자 판별 요청의 판정

| 문항 | 값 | 근거 |
|---|---|---|
| ① 결과 필요성 | **동기** — `d3_file`·`d5_upload_file` 의 CHECK 가 축 없는 행을 거부하므로(`〈79〉-⑵` · `0004:184`) 축이 없으면 이번 응답이 `201` 을 낼 수 없다 | `PLAN-SoT.md:348` |
| ② 시간 상한 | **비동기** — 26.6 MB `.npy` 2장 또는 압축 `.nc` 를 열어 `np.diff` 통계를 낸다(`d5/axis.py:89-98`). 소요 시간 **`[미측정]`** 이고, 격자 크기 상한이 계약에 없어 **10 s 결정적 보장이 없다** | `d5/axis.py:89-98`·`relay.py:25` |
| ③ 자원 프로파일 | **비동기** — 배열 전량 적재 + 인접차 평균. `DR-11`(전체 파일 메모리 적재 금지)이 겨냥한 프로파일 | `03-HANDOFF.md:255` |
| ④ 실패 표현 | **동기 가능** — 거절 3값(`형상 불일치`·`짝 불일치`·`축 판별 실패`)이 이미 enum 으로 존재해 즉답으로 낼 수 있다 | `common.json:107-111` |
| ⑤ 재시도 주체 | **동기** — 거절되면 사람이 올바른 격자를 다시 올린다. 기계 재시도가 축을 바꾸지 않는다 | `〈75〉-㉲` |

**결론 = 비동기.** ②③이 비동기를 가리키므로 §2.3 규칙(하나라도 비동기면 비동기)에 따라 **비동기**다. 그리고 이는 `PLAN-SoT.md:75-78` seam 표(core-api ↔ pipeline-worker = async)와 `〈79〉-㈎`(워커가 축을 확정한 뒤 원장 행을 만든다)와 **일치한다.**

- ⭑ **따라서 권고안 ㈑(동기 중계 신설)를 권고하지 않는다.** 근거 넷 — ⓐ seam 표 위반 ⓑ `relay.py` 에 바이너리·멀티파트 경로 0건 ⓒ 축 판별 소요시간이 `[미측정]` 인데 10 s 상한을 걸어야 한다 ⓓ `〈79〉-㈎` 가 이미 「저장 → 워커 축 확정 → 워커가 행 생성」을 채택했고 그 경로가 등록 전(`upload`) 세계에서 이미 설계돼 있다
- ⭑ **대신 권고 = `addDatasetFile` 의 격자 분기를 `addUploadFile`(`fe-core.yaml:290-317`)과 같은 모양으로 맞춘다** — 저장만 하고 **`202`**, 축은 워커가 확정, 결과는 상태 조회가 말한다. 계약은 이미 `202` 를 정의해 뒀다(`fe-core.yaml:778-793`). ⚠ 이때 필요한 것은 **등록 뒤 세계에도 「행 없이 저장된 격자」를 담을 자리와 그 결과를 말할 조회 창구**이고, 이는 §3 설계와 함께 판정해야 한다
- ⚠ **①이 「동기」인데 결론이 비동기인 것이 이 문제의 핵심**이다. 「지금 `201` 을 못 낸다」는 사실이 ㈑ 를 부른 것인데, **해법은 동기화가 아니라 응답 코드를 `202` 로 내리는 것**이다 — 계약이 이미 그렇게 적혀 있다

---

## 3. 위·경도 「함께 전송」 설계

### 3.1 현행 계약 — 4 op 의 요청 모양

| op | 경로 | 요청 | 파일 수 | 응답 | 집행 상태 |
|---|---|---|---|---|---|
| `createUpload` | `POST /uploads` | multipart `files[]` + `fileKinds[]` | **N 건 · 한 요청** | `201 UploadReceipt` | 구현됨(`routes/ingestion.py:166`) |
| `addUploadFile` | `POST /uploads/{uploadId}/files` | multipart `file` + `kind` | **1 건** | `202 UploadFileRef` | **501**(`not_implemented.py:97`) |
| `addDatasetFile` | `POST /datasets/{datasetId}/files` | multipart `file` + `kind` | **1 건** | `201` / `202`(격자) | 구현됨 · **격자는 400**(`routes/ingestion.py:459-464`) |
| `replaceUploadGridFile` | `PUT /uploads/{uploadId}/files/{fileId}` | `GridFileReplacement` | 1 건 | `202` | **501**(`not_implemented.py:98`) |
| `replaceDatasetGridFile` | `PUT /datasets/{datasetId}/files/{fileId}` | `GridFileReplacement`(`file` xor `flipAxes`) | 1 건 | `200`/`202` | 구현됨(`routes/ingestion.py:472`) |

- `FileKind` = `["본체", "기준 격자 파일"]` 2값(`contracts/schemas/common.json:78-82`)
- `〈58〉` = 격자 **0~2건** · 등록 뒤 후주입 가능(`PLAN-SoT.md:317` · `common.json:79`)
- `GridAxisAssignment` = `carriesLat`·`carriesLon` 두 불리언(`common.json:96-105`) — 통합 파일(둘 다 true)이 실재하므로 enum 하나가 아니다

### 3.2 ★ 핵심 관찰 — 「함께 전송」은 이미 계약에 있다

- **`createUpload` 가 그것이다.** `files[]` 배열 + 같은 순서의 `fileKinds[]`(`fe-core.yaml:222-243`), 「순서가 `fileKinds` 와 짝이다」(`:220`), 「생략하면 전부 `본체`」(`:228`). `〈79〉` 가 **「계약이 이미 ㈎ 를 지원한다 — 계약 개정 0건」**으로 명시했다(`PLAN-SoT.md:348`)
- **판별 코드도 이미 쌍 단위다.** `d5/axis.py:226` `detect_axes_for_upload(paths: list[Path])` — **업로드 안의 격자 파일들을 함께 본다. 짝은 형상으로 짓는다**(`:227-230`), `:253-267` 이 형상으로 그룹핑해 2건이 아니면 짝짓기 미정의로 거절한다. 거절 사유 `REASON_PAIR_MISMATCH = "짝 불일치"`(`:220`)
- ⭑ **즉 「순차 후주입」은 계약의 성질이 아니라 `addDatasetFile`·`addUploadFile` 두 op 에만 있는 「1 요청 = 1 파일」 제약이다.** 등록 전 세계는 이미 한 번에 받는다

### 3.3 ★ 설계 — `가` 최소 개정안 (권고)

**요지 = 후주입 op 두 개의 요청 모양을 `createUpload` 와 같은 배열형으로 넓힌다.**

**요청 모양** (`addDatasetFile` · `addUploadFile` 공통)

```
POST /datasets/{datasetId}/files    multipart/form-data
  files      : 파일 바이트 파트 배열   (minItems 1, maxItems 2)
  fileKinds  : files 와 같은 순서·같은 개수의 FileKind
```

- `createUpload` 의 필드명·순서 규약을 **그대로 재사용**한다 — 새 규약을 만들지 않는다
- 1건만 보내는 기존 호출은 `files` 길이 1 로 표현된다

**쌍 정합 검증 시점과 방법**

| 단계 | 시점 | 검증 | 실패 시 |
|---|---|---|---|
| ⒜ 개수·종류 | core-api · 동기 | `len(files) == len(fileKinds)` · `fileKinds ⊂ FileKind` · 격자 파트 ≤ 2 · `〈58〉` 의 데이터셋당 총합 0~2 초과 여부 | `400` — 파일을 읽지 않고도 판정된다 |
| ⒝ 저장 | core-api · 동기 | 공유 볼륨에 `storage_key` 로 기록. **원장 행은 만들지 않는다**(`〈79〉-ⓑⓒ`) | — |
| ⒞ 형상 일치 | **worker · 비동기** | `detect_axes_for_upload` 가 형상으로 그룹핑(`axis.py:253-257`) | `형상 불일치` |
| ⒟ 쌍 정합 | **worker · 비동기** | 그룹 크기 2 검사 · 여집합 축 배정(`axis.py:264-267`) | `짝 불일치` |
| ⒠ 값 범위 | **worker · 비동기** | 절댓값 최대 > 90 → 경도(`〈75〉-㉲`, 실측 14/14) · 내장 좌표 · 파일명 순 사다리 | `축 판별 실패` |
| ⒡ 사람의 눈 | 화면 | 지도 표시 후 **[맞습니다]** 전까지 배지 `확인 대기` · **[위도·경도 뒤집기]** | — |

- 거절 3값은 신설이 아니다 — `GridRejectionReason` enum 이 이미 그 셋이다(`common.json:107-111`)
- ⚠ **값 범위 규칙이 14/14 라도 최종 확인은 사람이다**(`〈75〉-㉲` — 위경도가 뒤바뀌면 에러 없이 빈 지도가 나온다)

**한쪽만 전송된 경우**

- **거절하지 않는다.** `〈58〉` 이 **0~2건**을 허용하므로 1건 업로드는 계약상 정상이다
- 처리 = 저장은 되고, 워커가 짝을 못 지어 **`짝 불일치` 로 원장 행을 만들지 않는다**(`axis.py:257` — 「짝짓기 미정의 — 거절 상태로 둔다」). 화면은 `getUploadStatus.gridRejections`(`routes/ingestion.py:243-245`)로 그 사실을 본다
- ⚠ **통합 파일(`.nc`)은 1건이 정상 완결이다** — `carriesLat`·`carriesLon` 둘 다 true(`common.json:97`). 따라서 「1건 = 미완」이 아니라 **「1건이고 축이 하나만 잡히면 미완」**이다. 판정은 파일 내용이 하고 개수가 하지 않는다
- ⭑ ⚠ **`maxItems: 2` 를 요청에 거는 것과 「데이터셋당 총 0~2건」은 다른 제약**이다. 후자는 기존 파일 수를 세어야 하고, 그 검사가 지금 `addDatasetFile` 에 있는지는 **`[미확인]`**

**계약 개정 필요 여부 — ⚠ 필요하다**

| 대상 | 개정 내용 | 성격 |
|---|---|---|
| `fe-core.yaml` `addDatasetFile` requestBody(`:764-770`) | `file`+`kind` → `files[]`+`fileKinds[]` | **동결 해제 필요** |
| `fe-core.yaml` `addUploadFile` requestBody(`:290-297`) | 동일 | **동결 해제 필요** |
| `common.json` | **불요** — `FileKind`·`GridAxisAssignment`·`GridRejectionReason` 무변경 | — |
| `db/platform` 마이그레이션 | **불요** — `0004` 무수정(`〈75〉-㉳`·`〈79〉`) | — |
| `contracts/events/` | **불요** — 이벤트 7종·`FileRef` 무변경 | — |

> ⭑ **이 개정은 임의로 실행하지 않는다.** 계약 동결 해제는 `〈80〉`·`〈88〉` 과 같은 **Ted 판정 사안**이다. 이 문서는 개정 범위만 명시한다. 개정 회차 = **동결 5회 해제 · 2 op · requestBody 만**.

**4 op 의 운명**

| op | 처분 | 근거 |
|---|---|---|
| `createUpload` | **유지 · 무변경** | 이미 배열형이다 |
| `addUploadFile` | **개정 후 유지** — 배열화 + 501 해제 | `〈88〉` 묶음 5 가 신설한 목적(본체 재전송·`uploadId` 무효화 방지)이 그대로 살아 있다 |
| `addDatasetFile` | **개정 후 유지** — 배열화 + 격자 400 → 202 | `〈58〉-②`(후주입)의 유일한 집행 지점 |
| `replaceDatasetGridFile` · `replaceUploadGridFile` | **유지 · 무변경** | 교체·뒤집기는 **대상 `fileId` 가 하나로 특정되는 조작**이라 배열이 의미를 갖지 않는다. `flipAxes` 는 이미 두 파일을 **한 트랜잭션에서 맞바꾼다**(`fe-core.yaml:346-350` · `routes/ingestion.py:492-495`) — 이미 「함께」다 |
| **폐기** | **0건** | — |

### 3.4 `〈75〉`·`〈79〉`·`〈88〉` 과의 정합

| 판정 | 조항 | 정합 여부 |
|---|---|---|
| `〈75〉`-㉮ | 격자 수용·짝짓기·축 판별·정합 확인 화면·뒤집기가 stage 1 안 | **정합** — 이 설계가 그 다섯을 전부 담는다 |
| `〈75〉`-㉯㉰ | 격자 없어도 ①② 생성 · 등록은 격자에 인질이 아니다 | **정합** — 격자 거절이 본체 등록을 막지 않는다 |
| `〈75〉`-㉲ | 사용자에게 축을 묻지 않는다 · 서버 사다리 + 뒤집기 버튼 | **정합** — 요청에 `gridAxis` 를 싣지 않는다 |
| `〈75〉`-㉳ | `0004` 무수정 · 워커가 축 확정 뒤 원장 행 | **정합** — 마이그레이션 0건 |
| `〈75〉`-㉴ | 격자는 매번 직접 올린다 · 자동 짝짓기 금지 | **정합** — 짝짓기는 **그 요청 안의 파일들** 사이에서만 한다. 서버 로컬 탐색·다른 데이터셋 참조 없음 |
| `〈79〉`-ⓐⓑⓒ | 요청이 `kind` 선언 · core-api 는 본체만 행 생성 · 워커가 격자 행 생성 | **정합** — 등록 뒤 세계에 같은 규칙을 적용한다 |
| `〈79〉`-㈏ 기각 | core-api 동기 축 판별 불가(`boundaries.toml:13-17`) | **정합** — 이 설계는 core-api 가 파일을 열지 않는다 |
| `〈79〉`-⑷ | `upload.ready` = 본체 감지 완료 + 격자 축 확정·거절 | **정합** — 단계 수 무변동 |
| `〈88〉` 묶음 5·6 | `addUploadFile`·`replaceUploadGridFile` 신설 | **정합** — 폐기하지 않고 개정 후 유지 |
| `〈88〉` 묶음 7 | 확정 결과는 `getUploadStatus.files[].gridAxis`·`gridRejections` | **정합** — 회수 창구 재사용 |
| ⚠ `〈70〉`-㉴ | 「업로드 경로에 분기나 대기를 더하는가」 | **⚠ 판정 필요** — 배열화는 **분기를 줄인다**(2회 요청 → 1회). 다만 격자 `202` 는 대기를 만든다. `〈73〉` 이 그 대기의 원인을 「워커 미가동」으로 확정했고 워커는 현재 가동 중이다(§4) |

- ⚠ **`〈58〉` 과의 긴장 1건** — `〈58〉-②`(후주입)는 「나중에 격자를 구해 붙인다」를 상정한다. 위·경도를 **동시 전송으로만** 받으면 「위도만 먼저 구했다」가 표현 불가가 된다. **이 설계는 동시 전송을 강제하지 않고 허용한다**(`minItems: 1`) — 강제하면 `〈58〉` 을 깬다

### 3.5 ⚠ 기각한 대안

- **`GridPairUpload` 전용 op 신설** — 기각. 격자 전송 경로가 둘이 되어 정본 경로가 흐려진다(`〈80〉-㉯ 3` 이 `flipGridAxes` 를 같은 근거로 기각했다) · 501 이 늘어난다
- **요청에 `gridAxis` 를 싣게 하기** — 기각. `〈75〉-㉲`(사용자에게 축을 묻지 않는다)·`〈66〉`(축을 지어내지 않는다) 위반

---

## 4. staging worker — 존재 목적과 가동 여부

### 4.1 ★ 가동 여부 = **가동 중** (실측 · `[미확인]` 해소)

```
docker ps -a
b7a306e70b28  colab-v2/pipeline-worker:i2  "python -m colab_pip…"
              Up 2 minutes (healthy)  8000/tcp  colab_v2_staging_pipeline_worker
```

- 컨테이너명 = `colab_v2_staging_pipeline_worker` · 상태 = **`Up (healthy)`** · 재시작 루프 없음
- staging 전체 8 컨테이너 전부 `Up (healthy)` — `nginx`·`core_api`·`pipeline_worker`·`frontend`·`ai_service`·`viz_render`·`pg`·`cloudflared`. `volume_init` 은 `Exited(0)`(1회성). `dev-package/RESTART.md:87,92` 의 기대 정상상태와 일치
- `docker logs --tail 50 colab_v2_staging_pipeline_worker` → **빈 출력**. 이는 정상이다 — 기본 발행기가 `stdout_publish`(`app/worker.py:58-59`)이고 outbox 에 미발행 행이 있을 때만 출력한다. **유휴 루프는 조용하다**
- ⚠ **`docker compose -f infra/staging/compose.i2.yml ps` 는 exit 1** — `COLAB_OWNER_PASSWORD` 미설정(`migrate` 프로파일 서비스 보간 실패). 가동 판정 근거는 `docker ps -a` 다
- ⚠ **한계** — `/healthz` 는 데몬 스레드가 낸다. 다만 `worker.py:189-201` 이 루프를 **메인 스레드**에서 돌리므로 루프가 죽으면 프로세스가 죽는다. 즉 `Up (healthy)` 는 루프 생존의 **간접** 증거다. 5 s 주기 사이클이 실제로 돌고 있는지의 DB 직접 확인은 **`[미측정]`**

### 4.2 worker 의 역할

- 소유 = **D5 Ingestion & Pipeline**(`services/pipeline-worker/README.md`) — presigned 업로드 · 헤더 파싱 · 포맷 자동감지 · 좌표계 변환 · COG 변환 · 오버뷰 선생성 · outbox 릴레이 · 처리 원장
- 진입점 = `app/worker.py:189-201` `main()` — 헬스 서버(데몬 스레드) + `serve()`(메인 스레드). `serve()`(`:183-186`)가 `run_once()` 를 **5 s 주기**로 무한 반복
- `run_once()`(`worker.py:142-180`) — 한 DB 트랜잭션 안에서 셋

| 단계 | 함수 | 담당 |
|---|---|---|
| ⓪ | `drive_uploads`(`worker.py:103-139`) | 대기 업로드를 `ledger.pending_uploads` 로 끌어와 `service.process_upload(..., stage1=True)` 호출 — **stage 1 은 포맷 감지까지**(`〈73〉`) |
| ① | `relay_unpublished` | outbox(`d5_pipeline_event`) 미발행 이벤트 방출. 기본 발행기 = `stdout_publish`(`worker.py:58-59`) |
| ② | `reap_expired_uploads` | TTL 만료된 미등록 업로드 회수 |

- 기동 필수 env 4종 = `COLAB_PIPELINE_DB_URL`·`COLAB_WORKER_LAB_ID`·`COLAB_WORKER_ACCOUNT_ID`·`COLAB_WORKER_UPLOAD_DIR`(`worker.py:149-160`) — 하나라도 없으면 루프 진입 전 `RuntimeError`

### 4.3 compose 구성

`infra/staging/compose.i2.yml` worker 블록(약 `:127-153`)

- `build.context: ../../services/pipeline-worker` · image `colab-v2/pipeline-worker:i2` · `container_name: colab_v2_staging_pipeline_worker`
- `restart: unless-stopped`
- `environment` = 위 4종. `COLAB_WORKER_LAB_ID`·`COLAB_WORKER_ACCOUNT_ID` 는 `:?required`
- `volumes: uploads:/var/lib/colab/uploads` — **core-api 와 같은 named volume**. core-api 가 쓴 것을 worker 가 열 수 있는 근거이자, §1.2 의 「바이트를 요청 본문에 안 싣는다」의 근거
- `depends_on` = `volume-init`(`service_completed_successfully`) · `postgres`(`service_healthy`)
- `healthcheck` = `http://127.0.0.1:8000/healthz`
- **`profiles:` 키 없음** → 기본 비활성 프로파일이 아니다. `docker compose up -d` 로 함께 기동한다(`migrate-platform`·`migrate-ai` 는 `profiles: ["migrate"]` 로 분리)
- 블록 상단 주석(약 `:121-126`)이 `〈73〉` 을 인용해 「더는 빈 단위가 아니다」를 명시

### 4.4 `〈73〉` 배선 판정

`dev-package/PLAN-SoT.md:336` —

- **실측 = 비동기 기계는 배선된 적이 없었다.** Dockerfile CMD 가 헬스 서버만 띄웠고, relay·reaper 루프가 어느 배포 경로에서도 시작되지 않았으며, `process_upload` 의 생산 호출자가 **0건**(시험 5개 파일만 호출)
- **결과** = `upload.ready` 가 영구히 false → FE 가 1 초에 한 번 무한 폴링
- **판정 = 뜯어내지 않고 켠다** — 워커 루프를 실제로 배선하고, stage 1 에서는 파싱·CRS·COG 만 건너뛴다. `createUpload` 응답은 무영향, 폴링은 워커 주기 안에 해소된다
- 커밋 제목이 그대로 이 판정이다 — `1c81faa docs(S1): 판정 〈73〉 — 업로드의 대기는 가공이 아니라 안 켠 워커였다`

### 4.5 worker 가 없으면 무엇이 동작하지 않는가

| 잃는 것 | 근거 |
|---|---|
| `upload.ready` 가 영구히 false → **업로드 모달이 끝나지 않는다** | `〈73〉` 실측 |
| `file.format-detected` 미발행 → **포맷이 `[미상]` 으로 남는다** | `worker.py:103-139` |
| outbox 이벤트가 테이블에 쌓이기만 하고 방출되지 않는다 | `relay_unpublished` |
| 만료 업로드가 회수되지 않는다 — core-api 에 `reap_expired()` 생산 호출자 0건 | `d5_ingestion.py:254` |
| **격자 축이 영원히 확정되지 않는다** → 원장 행이 서지 않는다 | `〈79〉`-ⓒ |

- ⭑ **마지막 행이 §2·§3 과 이어지는 지점**이다. 격자 후주입의 비동기 경로는 **워커가 켜져 있어야만 완결**되고, 실측상 **켜져 있다**

**stage 1 범위에서 worker 가 수행하는 단계**

```
upload.accepted (core-api 발행)
   → 감지(매직바이트) → file.format-detected
   → [격자] 축 판별 사다리 → 축 확정 시 d5_upload_file 행 생성 / 실패 시 거절 3값
   → upload.ready
```

- 헤더 파싱·좌표 변환·COG 변환은 **stage 1 밖**(`〈70〉-㉯` · `〈73〉`)
- 격자는 감지·미리보기를 태우지 않고 **축 판별 사다리만** 돈다(`〈79〉-⑶`)

---

## 5. 요약 — 값만

| 항목 | 값 |
|---|---|
| `Lat_HSR.npy` · `Lon_HSR.npy` | 각 **26,562,948 B** · `<f4` · `(2881, 2305)` · 쌍 합계 **53,125,896 B** |
| `rdr_500m_latlon.nc` | **11,471,526 B** · NetCDF4(HDF5) · `lat`·`lon` 각 `(2881, 2305)` `<f4` |
| 동기 중계 본문 형식 | **JSON 전용**(`relay.py:34`) · 타임아웃 **10 s** · 재시도 **0** |
| 격자 판별 판정 | **비동기** — 판단기준 ②③ 이 비동기, seam 표(`PLAN-SoT.md:78`)와 일치 |
| 권고안 ㈑ | ★ **비권고** — 대안 = `addDatasetFile` 격자 분기를 `400` → `202` |
| 동시 전송 설계 | ★ `가` 최소 개정안 — `files[]`+`fileKinds[]` 배열화 |
| 계약 개정 | **필요** — `fe-core.yaml` 2 op requestBody. `common.json`·마이그레이션·이벤트 **불요** |
| op 폐기 | **0건** |
| staging worker 가동 | **가동 중** — `colab_v2_staging_pipeline_worker` · `Up (healthy)` · 프로파일 게이트 없음 |

**남은 `[미확인]`**

1. 축 판별 소요시간 — 26.6 MB 격자 2장 기준 실측 없음
2. `addDatasetFile` 이 「데이터셋당 격자 총 0~2건」을 실제로 세는지
3. worker `run_once()` 5 s 사이클의 DB 직접 관측
4. `storage_layout.storage_key(datasetId, …)` 의 키 접두 — 상위 문서 `E-2` 부수 관찰. 저장 배치 소유 레인 소관
