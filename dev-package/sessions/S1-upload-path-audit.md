# 업로드 경로 실측 감사 — stage 1 에서 비동기 장치는 자리값을 하는가 (S1-upload-path-audit)

> **작성** 2026-08-24 · **조사 전용 레인**(수정 0 · 커밋 0 · staging 무접촉). 워크트리 HEAD `7b51a33`.
> **왜 이 문서가 있는가** — `〈70〉-㉴` 가 Ted 의 근거를 정본에 넣었다:
> 「**데이터 가공의 단계가 업로드에 들어가면 분기와 처리 시간이 계속 발생한다. 그래서 미리보기나 가공이 없는 형태로 하려고 한다.**」
> 그 근거는 **범위 목록보다 강한 판정 기준**이고, `〈70〉-㉴` 스스로 「outbox·워커·릴레이·reaper·이벤트 7종·「처리 중」 상태·만료 경합 규칙은
> **처리 시간이 길기 때문에** 세운 장치이므로 재검이 필요하다」고 적었다. 이 문서가 그 재검이다.
>
> **EVIDENCE 와 INTERPRETATION 을 갈라 적었다**(`DATA-REFERENCE §0 M-5`). 계측값은 **이 세션이 실제로 돌린 것만** 적었고
> 안 잰 것은 `[미측정]` 이다(`M-4`). 인용한 `파일:행` 은 `cat -n` 으로 확인했다(`M-7`). 절대경로를 적지 않는다(`CLAUDE.md §3-8`).
> **계약은 동결이다**(`〈61〉-㉢`) — 아래에서 계약 수정이 필요한 자리는 **제안이 아니라 멈춤·보고**로 표시했다.

---

## 0. 한 장 요약

| 물음 | 실측 답 |
|---|---|
| stage1 업로드 경로에 **처리 시간**이 있는가 | **있다. 단 그것은 가공이 아니라 바이트 저장이다** — `createUpload` 가 파일 전체를 메모리로 읽고 디스크에 쓴다(동기). 27.0 MB 실측 **read 78–145 ms + write 7 ms** |
| 포맷 감지는 얼마인가 | **감지는 그 저장 비용의 1/5 이하다.** 실측 **1.6 ms(GeoTIFF·HDF4) ~ 23 ms(NetCDF4/HDF5 컨테이너)**. 그리고 **지금 업로드 경로에서 감지는 아예 안 돌아간다**(아래 A-3) |
| 비동기 장치가 stage1 에서 하는 일 | **거의 없다.** 배포된 워커는 헬스 서버만 돈다 — `Dockerfile:18` 이 `colab_pipeline.app.health` 를 CMD 로 걸었고 릴레이·reaper 루프(`app/worker.py`)는 **어떤 배포 경로에서도 기동되지 않는다** |
| `upload.accepted` 소비자 | **없다.** `IngestionService.process_upload` 의 호출자는 **시험 5파일뿐**이고 production 호출자가 0건이다 |
| 그러면 지금 업로드는 이미 동기인가 | **사실상 그렇다.** 다만 **비동기인 척하는 잔재가 남아 「대기」를 만든다** — FE 가 `ready` 를 기다리며 **1초마다 무한 폴링**한다(`UploadModal.tsx:30`·`:102`). 이것이 Ted 가 없애려던 「대기」의 실물이다 |
| 계약이 강제하는 것 | **이벤트 7종 선언 · `upload.accepted.source = "core-api"` const · `UploadStatus.ready` required · `createUpload` 산문의 이벤트 촉발 주장** — 이 넷은 동결이라 못 건드린다 |
| 권고 | **㈏ 변형(㈏′)** — 원장·outbox·`upload.accepted` 는 살리고, **워커 프로세스·릴레이·reaper 를 core-api 안으로 접는다**. 상세 §D |

---

## A. 업로드 경로에 지금 무엇이 남아 있는가 — 실제 제어 흐름

### A-1. EVIDENCE — `createUpload` 한 요청 안에서 일어나는 일 (전부 동기)

`services/core-api/src/colab_core/app/routes/ingestion.py`

| 순서 | 하는 일 | `파일:행` | 동기/지연 | 분기? | 사람이 기다리나 |
|:--:|---|---|:--:|:--:|:--:|
| ⑴ | 권한 판정 `업로드·편집` | `:141` → `:78-87` | 동기 | 있음(403) | 쿼리 2회 |
| ⑵ | `files` 비었나 | `:142-143` | 동기 | 있음(400) | 무시 가능 |
| ⑶ | `fileKinds` 정합 · 2값 검사 · 본체 1건 이상 | `:145-155` | 동기 | **분기 4갈래**(400) | 무시 가능 |
| ⑷ | **파일 바이트 전체를 메모리로 읽음** `await upload_file.read()` | `:163` | 동기 | 없음 | **O(파일 크기)** |
| ⑸ | **디스크 기록** `_store` (`sha256(key)` 파일명) | `:166` → `:68-70` | 동기 | 없음 | **O(파일 크기)** |
| ⑹ | 축은 `False` 고정 · 포맷은 `None` 고정 | `:171`·`:173` | — | 없음 | — |
| ⑺ | 원장 INSERT — `d5_upload` 1행 + `d5_upload_file` N행 | `:177-179` → `domains/d5_ingestion.py:162-178` | 동기 | **격자 파일은 행을 안 만들고 `continue`**(`:170-172`) | 쿼리 1+N |
| ⑻ | outbox INSERT — `upload.accepted` 1행 | `:180-181` → `domains/d5_ingestion.py:180-200` | 동기 | 멱등 `ON CONFLICT DO NOTHING` | 쿼리 1 |
| ⑼ | 201 + `uploadId`·`files` 응답 | `:182` | 동기 | — | — |

**이 요청 안에 헤더 파싱·좌표·COG 는 처음부터 없다.** `createUpload` 는 파일을 열지 않는다 —
`:172-173` 주석이 「확장자로 포맷을 정하지 않는다 — **매직바이트 판정은 파이프라인의 일이다**」라고 못 박고 `detected_format=None` 을 넣는다.

### A-2. EVIDENCE — 접수 뒤에 무엇이 일어나야 하는가 (설계상) vs 무엇이 일어나는가 (실제)

**설계상 (`gates/fixtures/seam-consistency/e04-flow.json`, 14단계)**
`createUpload` → `upload.accepted` → `file.format-detected` → `file.header-parsed` → `file.crs-normalized` → `preview.cog-built` → `upload.ready` → `getUploadStatus` → 미리보기 → AI 제안 → `createDataset` → …

**실제 — 세 지점에서 끊긴다.**

1. **소비자가 없다.**
   `grep -rn "process_upload\|IngestionService" services infra gates --include='*.py' --include='*.yml'` →
   정의 2건(`services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:107`·`:137`) + **호출 전건이 `tests/` 안**
   (`test_outbox_db.py`·`test_worker_events.py`·`test_worker_creates_grid_row.py`·`test_tiff_classes_pipeline_real.py`).
   **production 호출자 0건.**

2. **워커 루프가 기동되지 않는다.**
   `services/pipeline-worker/Dockerfile:18` — `CMD ["python", "-m", "colab_pipeline.app.health"]`.
   `app/worker.py:29 run_once` · `:58 serve` 를 부르는 곳은 `worker.py` 자기 자신(`:60`)뿐이고
   compose 에도 override 가 없다(`infra/staging/compose.i2.yml:92-102` — build·image·healthcheck 만, `command` 없음, 환경변수 0건).
   `worker.py:31-33` 은 `COLAB_PIPELINE_DB_URL` 없으면 `RuntimeError` 를 던지는데 **그 변수가 compose 에 없다.**

3. **발행자가 표준출력이다.**
   `app/worker.py:25-26 stdout_publish` — 큐·브로커 미선정(`:7-9` 「발행 대상은 아직 고르지 않았다」).
   그래서 릴레이가 돈다 해도 이벤트는 **아무 데도 안 간다.**

**따라서 `d5_pipeline_event` 는 지금 `upload.accepted` 만 담기는, 아무도 읽지 않고 아무도 비우지 않는 표다.**

### A-3. EVIDENCE — 그 결과 사람에게 보이는 것

- `d5_upload.ready` 는 `0004:145` 에서 `NOT NULL DEFAULT false` 이고, 이것을 `true` 로 바꾸는 유일한 코드가
  워커의 `record_status(..., ready=True)`(`pipeline-worker …domains/d5_ingestion.py:227`)다. **워커가 안 도니 영원히 `false`.**
- `getUploadStatus` 는 그 값을 그대로 내린다 — `routes/ingestion.py:202` `"ready": record.ready`.
- FE 는 그것을 기다린다 — `frontend/src/components/upload/UploadModal.tsx:30` `STATUS_POLL_MS = 1000`,
  `:102` `if (!s.ready && !s.failure) statusTimer.current = window.setTimeout(tick, STATUS_POLL_MS);`
  → **모달이 열려 있는 내내 초당 1회 `GET /uploads/{id}` 가 영원히 나간다.**
- **다행히 등록은 막히지 않는다** — `RegisterArea.tsx:9` 「**막지 않는다** — 앞 단계를 채웠는지 검사하지 않는다」.
  `ready` 를 등록 버튼의 조건으로 쓰는 코드는 없다(`grep` 로 `UploadModal.tsx`·`RegisterArea.tsx` 전건 확인 — `ready` 참조는 `:102` 한 자리뿐).
- `renderable`·`metadata_complete` 는 `0004:146-147` 상 NULL 가능이고 채우는 코드가 워커뿐이라 **영영 NULL**.
- 「자동 메타데이터 확인」 단계(`RegisterArea.tsx:19` `① 자동 메타데이터 확인`)에 채워질 값이 **하나도 없다.**

### A-4. INTERPRETATION (잠정)

- **Ted 의 판정 기준을 지금 코드에 그대로 대면, 걸리는 것은 「가공」이 아니라 「가공을 기다리는 척」이다.**
  분기와 대기가 실제로 발생하는 자리는 셋이다 — ⑴ FE 무한 폴링 ⑵ 영원히 `false` 인 `ready` ⑶ 채워지지 않는 자동 메타 칸.
  **가공 코드를 빼는 것만으로는 이 셋이 안 없어진다.** 셋 다 「비동기 완료 신호를 기다린다」는 형태 자체에서 나온다.
- **역으로, `〈70〉` 이 잘라 낸 것들(파싱·좌표·COG)은 업로드 경로에 지금 아무 시간도 더하고 있지 않다.**
  연결돼 있지 않기 때문이다. 그래서 「가공을 빼면 빨라진다」는 **stage1 현재 코드에서는 참이 아니다** — 이미 안 돌고 있다.
  **가공을 빼서 얻는 것은 속도가 아니라 「완주하지 못하는 흐름을 완주하는 흐름으로 바꾸는 것」이다.**
- `S1-scope-cut-inventory §C-2` 는 「outbox 릴레이·워커·reaper 는 반드시 살아남아야 한다」로 적었다.
  **그 판단은 「이 장치들이 지금 돌고 있다」는 전제 위에 있었고, 이 감사는 그 전제가 틀렸음을 실측했다.**
  reaper 의 근거였던 「미등록 업로드가 눌러앉는다」는 여전히 참이지만, **지금 reaper 도 안 돌므로 그 위험은 이미 실재한다** — 없애는 문제가 아니라 **켜는 문제**다.

---

## B. 각 비동기 장치가 stage 1 에서 무엇을 위해 존재하는가

**세 번째 칸이 판정을 가른다** — 동결 계약(`〈61〉-㉢`)이 요구하는 것과, 이전 설계가 요구했을 뿐인 것.

| # | 장치 | ⑴ 지금 하는 일 | ⑵ **stage1 에서 없으면 무엇이 깨지나** | ⑶ **동결 계약이 요구하는가** |
|:--:|---|---|---|---|
| 1 | **`d5_upload`·`d5_upload_file` 원장** (`0004:136-195`) | `createUpload` 가 쓰고(`ingestion.py:177-179`) `getUploadStatus`·`createDataset` 가 읽는다 | **업로드 자체가 깨진다.** 접수와 등록이 두 요청으로 갈린 이상 그 사이 상태를 둘 자리가 필요하다. `createDataset` 는 `ledger.files(upload_id)`(`ingestion.py:317`)로 파일 목록을 얻는다 | **간접적으로 그렇다.** 계약이 `createUpload`→`createDataset` 를 두 op 으로 갈랐으므로(`fe-core.yaml:196`·`:1776 UploadStatus`) 중간 상태 저장은 불가피. **표 형태는 계약 밖 = 레포 결정** |
| 2 | **`d5_pipeline_event` outbox** (`0004:199-235`) | `upload.accepted` 1행만 쌓인다. **아무도 안 읽는다** | **직접 깨지는 것은 없다.** 단 ⓐ `0004` 되돌리기는 `schema-diff` red(`인벤토리 B-4`) ⓑ **「처리 중」 판정이 이 표를 읽는다**(`_PROCESSING`, 아래 #9) | **표는 계약 밖.** 그러나 **`upload.accepted` 를 어딘가에 쓰긴 써야 한다면**(#7) 지금 그 자리는 여기뿐이다 |
| 3 | **워커 프로세스**(`app/worker.py` 65줄) | **아무것도 안 한다** — `Dockerfile:18` 이 헬스만 띄운다 | **아무것도 안 깨진다.** 지금 상태에서 이 파일을 지워도 런타임 동작이 변하지 않는다(시험 제외) | **아니다.** allowlist 가 `pipeline-worker` 를 **`internal-sources`** 로 등재해(`gates/fixtures/seam-consistency/allowlist.toml:20`) HTTP 촉발 op 을 **요구하지 않는다** |
| 4 | **릴레이** (`…domains/d5_ingestion.py:436-447`) | 미발행 이벤트를 `stdout_publish` 로 내보내고 `published_at` 을 찍는다. **기동 안 됨** | **아무것도.** `published_at` 을 읽는 코드가 릴레이 자신의 쿼리(`:333`)뿐이다 | **아니다.** 봉투의 `delivery.publishedAt`(`envelope.json`)은 **발행 시점의 값**이지 저장 열을 요구하지 않는다 |
| 5 | **reaper** (`…domains/d5_ingestion.py:412-432` · core-api `domains/d5_ingestion.py:108-113`·`:207-208`) | 만료 미등록 업로드 삭제. **양쪽 다 기동 안 됨** | **켜면 필요한 것이 맞다** — 미등록 업로드의 바이트·행이 무한 누적된다(`〈64〉-ⓒ`). **끄면 지금 상태 그대로**(=이미 새고 있다) | **아니다.** `UploadStatus` 의 404(「수명이 다해 사라졌다」, `fe-core.yaml:265-266`)는 **`_live_upload`(`ingestion.py:100-114`)의 시각 비교만으로도 참**이 된다 — 물리 삭제는 계약 요구가 아니다 |
| 6 | **이벤트 7종 선언** (`core-pipeline.json:300-311 AnyEvent`) | 코드 쪽 거울 = `d5/events.py:19-27 EVENT_TYPES`, DB CHECK = `0004:208-210` | 4종(`header-parsed`·`crs-normalized`·`cog-built`)은 **발행자가 없어졌으니 죽은 값**이 된다. 값이 남아 있어도 아무것도 안 깨진다 | **✅ 그렇다 — 7종 전부.** `AnyEvent.oneOf` 가 7개 `$ref` 를 열거하고 `:301` 산문이 「새 타입을 추가하면 여기에도 한 줄이 늘고 그 diff 가 계약 리뷰에 걸린다」고 적었다. **줄이는 것도 계약 변경**이다 → **줄이려면 멈춤·보고** |
| 7 | **`upload.accepted` 발행** (`ingestion.py:180-181`) | outbox 1행. 소비자 없음 | **런타임은 안 깨진다.** 깨지는 것은 시험 — `tests/test_uploads.py:51 test_create_upload_emits_exactly_one_accepted_event` | **✅ 계약이 「낼 수 있다」를 강제한다.** `core-pipeline.json:223` `"source": {"const": "core-api"}` + allowlist `http-sources.core-api = fe-core.yaml`(`allowlist.toml:16`) → `seam_consistency.py:283-285`(G-b)·`:441-449`(㉡-3)이 **fe-core.yaml 안에 그 이벤트를 촉발한다고 말하는 op** 을 요구한다. `fe-core.yaml:199-201` 이 그 문장이다. **⚠ 단 게이트가 보는 것은 계약 산문이지 코드가 아니다** — 코드가 발행을 멈춰도 게이트는 green |
| 8 | **`upload.ready` / 「처리 중」 상태** | `ready` 는 영원히 `false`(A-3). FE 가 그것을 기다린다 | **지금 이미 깨져 있다.** 「처리 중」 표시는 화면 문구로 존재하지 않는다(`frontend/src` 에 `처리 중` 문자열 **0건**, grep 확인) — 존재하는 것은 **폴링 루프뿐** | **✅ `ready` 는 계약 required.** `fe-core.yaml:1782` `required: [uploadId, files, ready, failure]`, `:1790-1792` `ready: boolean`(널 불가). **필드를 없애는 것은 계약 변경** → 멈춤·보고. **다만 「무엇을 `true` 로 볼 것인가」는 계약 밖**이다 |
| 9 | **만료 경합 규칙 `〈67〉-㉠`** (`_PROCESSING`, core-api `domains/d5_ingestion.py:40-50` · worker `:287-294`) | 「`upload.accepted` **이후의** 이벤트가 수명 창 안에 있으면 만료돼도 살아 있다」 | **stage1 에서 이 규칙은 절대 발화하지 않는다.** `:47` `AND e.event_type <> 'upload.accepted'` 가 접수 이벤트를 제외하는데, **stage1 outbox 에는 접수 이벤트밖에 없다.** → `processing` 은 **항상 false** | **아니다 — 순수한 레포 판단.** 워커 코드 주석 `:285-286` 이 스스로 「「처리 중」의 정의 자체는 정본에 없다 … 이것은 레포 판단이다」라고 적었다 |
| 10 | **`getUploadStatus`** (`ingestion.py:186-207`) | 원장을 읽어 계약 형태로 내린다. `ready:false`·`renderable:null`·`metadataComplete:null`·`failure:null` 고정 | **없으면 FE 가 만료·경계 밖을 알 방법이 없다**(404 창구). 그리고 `expiresAt` 을 화면에 줄 자리가 사라진다 | **✅ 계약 op 이다.** `fe-core.yaml:251 operationId: getUploadStatus`, `e04-flow.json` 단계 8. **없애려면 계약 변경** → 멈춤·보고 |

### B-1. INTERPRETATION (잠정) — 세 무더기로 갈린다

- **㉠ 계약이 못 박아 뺄 수 없는 것 (4)** — 이벤트 7종 선언 · `upload.accepted` 를 낼 수 있다는 주장 · `UploadStatus.ready` · `getUploadStatus`.
  **이 넷은 stage1 에서 행동적으로 거의 무의미한데도 계약상 필수다.** `〈70〉-㉴` 이 예감한 자리가 정확히 여기다.
- **㉡ 계약 밖이고 stage1 에서 실동작이 0 인 것 (4)** — 워커 프로세스 · 릴레이 · 「처리 중」 판정(`_PROCESSING`) · 죽은 이벤트 4종의 발행 코드.
  **이 넷은 지우든 두든 런타임이 같다.** 지우면 깨지는 것은 **시험뿐**이다.
- **㉢ 계약 밖이지만 켜야 하는 것 (2)** — reaper · 원장.
  **reaper 는 「없애도 되는가」가 아니라 「왜 안 켜져 있는가」가 물음이다.** 지금 만료 회수가 0건이므로 업로드 바이트가 무한 적재된다.

> **가장 날카로운 관찰** — `_PROCESSING`(`〈67〉-㉠`)은 **stage1 에서 논리적으로 죽은 조건**이다.
> 두 서비스에 같은 SQL 을 복제해 두고(「한쪽만 고쳐지는 일을 막으려고」, core-api `:38-39`) 시험 8건이 지키는데,
> **그 조건이 참이 되는 경로가 stage1 에는 존재하지 않는다.** 접수 이후 이벤트를 낼 발행자가 없기 때문이다.
> 이것은 「휴면」이 아니라 **「부재」**다 — 그리고 `〈71〉-㉰` 의 CI 유지 규칙은 이 차이를 구분하지 않는다.

---

## C. 동기 업로드가 가능한가 — 그리고 무엇을 잃는가

### C-1. EVIDENCE — 포맷 감지 실측

**무엇을 쟀나.** `services/pipeline-worker/.venv/bin/python` 으로 `colab_pipeline.d5.detect.detect_format` 를 원천 실파일에 7회 반복 호출.
원천 = `03 Reference-Data/02.File-format/` (환경변수 `COLAB_REFERENCE_DATA` 가 가리키는 자리).

| 파일 크기 | min | median | max | 판정 결과 | 파일 |
|---:|---:|---:|---:|---|---|
| 27.0 MB | **1.624 ms** | 1.797 ms | 12.428 ms | `GeoTIFF` | `…B04.tif` |
| 11.5 MB | **22.554 ms** | 23.237 ms | 680.574 ms | `NetCDF` / HDF5 컨테이너 | `rdr_500m_latlon.nc` |
| 10.1 MB | **1.656 ms** | 1.699 ms | 9.451 ms | `HDF4` | `MOD15A2H…hdf` |
| 2.1 MB | **14.821 ms** | 15.410 ms | 30.296 ms | `NetCDF` / HDF5 컨테이너 | `gk2a_ko020lc_latlon.nc` |
| 1.3 MB | **3.500 ms** | 3.666 ms | 11.748 ms | `Binary` / gzip | `RDR_CMP_HSR_PUB_…bin.gz` |
| 0.4 MB | **12.893 ms** | 13.366 ms | 13.905 ms | `NetCDF` / HDF5 컨테이너 | `gk2a_ami_le2_lst_ko_…nc` |

**왜 두 무리로 갈리나 — 코드가 설명한다.**
- **매직바이트만 보는 경로**(GeoTIFF·HDF4): `detect.py:208-209` `f.read(64)` — **64 바이트만 읽는다.** → **1.6 ms 대**, 크기와 무관(27 MB 파일이 10 MB 파일보다 빠르다).
- **try-open 경로**(NetCDF4/HDF5 컨테이너): `detect.py:192-201 _resolve_hdf5_container` 가 `netCDF4.Dataset(path,"r")` 로 **파일을 실제로 연다.** → **13–23 ms.**
  `detect.py:119` 이 이유를 적어 뒀다 — 「`\x89HDF` 만으로는 NetCDF4 와 순수 HDF5 를 못 가른다 — **try-open 이 필수다**」.
- gzip 경로(`detect.py:214-220`)는 **압축 헤더 64 바이트만 해제**한다 → 3.5 ms.
- `max` 열의 이상치(680 ms·12 ms)는 **1회차의 콜드 캐시 + `netCDF4` 지연 임포트**다. 정상 상태 값은 min/median.

**`[미측정]`** — GB 급 NetCDF4 의 try-open 시간. 원천 최대 `.nc` 가 11.5 MB 라 외삽 근거가 없다.
관측 3점(0.4/2.1/11.5 MB → 13/15/23 ms)은 「고정비 ~13 ms + 크기 항」처럼 보이지만 **3점으로 50 GB 를 말하지 않는다.**
`DR-11` 이 가정한 50 GB 에 대해 이 문서는 값을 갖지 않는다.

### C-2. EVIDENCE — 전송 시간과 처리 시간을 가른다

**둘을 섞으면 이 결정이 틀린다.** 실측으로 갈라 놓는다.

| 항목 | 실측 | 성격 |
|---|---|---|
| `await upload_file.read()` 등가 — 27.0 MB 전량을 메모리로 | **read 77.6 / 78.6 / 144.5 ms** (317 / 320 / 178 MB/s) | **전송·I/O.** 파일 크기에 선형. **stage1 축소와 무관하게 남는다** |
| `_store` 디스크 기록 27.0 MB | **write 6.5 / 6.9 / 7.3 ms** | 동상 |
| 합계 | **84.4 / 85.1 / 151.8 ms** | 동상 |
| **포맷 감지** 27.0 MB GeoTIFF | **1.6 ms** | **처리.** 크기와 무관 |

> **비율** — 같은 27 MB 파일에서 **저장 85 ms : 감지 1.6 ms ≈ 53 : 1**.
> **감지를 업로드 경로에 넣는 비용은 이미 그 경로가 치르고 있는 비용의 2 % 미만이다.**
> (측정 환경: WSL2, 원천은 `/mnt/f` drvfs 읽기, 기록은 리눅스 tmp. 컨테이너 실환경 수치는 `[미측정]`.)

**1.3 GB 번들과 50 GB 로 올라가면.** 위 표에서 **커지는 것은 전송 항뿐이다.**
- 매직바이트 경로는 **64 바이트**라 50 GB 여도 1.6 ms 대다(코드가 그렇게 쓰여 있다 — `detect.py:209`).
- **유일한 위험은 NetCDF4 try-open** — `netCDF4.Dataset` 이 헤더만 읽는지 크기에 따라 커지는지 **이 세션은 재지 못했다**`[미측정]`.
- **전송은 어차피 사람이 기다린다.** 지금도 `createUpload` 가 동기로 전량을 읽고 쓴다(`:163`·`:166`).
  ⚠ **그리고 그것은 전량을 RAM 에 올린다** — 1.3 GB 번들 하나가 core-api 워커 프로세스 메모리 1.3 GB 다. **이것은 감지와 무관한 기존 위험이고, 이 감사가 새로 발견한 것이다.**

### C-3. 동기 업로드를 구체적으로 모델링하면

**모양** — `createUpload` 안에서 ⑷⑸(전송·저장) 직후에 `detect_format` 을 파일마다 부르고,
`d5_upload_file.detected_format` 을 채우고, `ready=true` 로 도장 찍고, `upload.accepted` 는 **그대로 outbox 에 넣는다**(계약 유지).

| 물음 | 답 |
|---|---|
| **응답 시간이 얼마나 늘어나나** | 본체 파일당 **+1.6 ms(매직바이트) ~ +23 ms(NetCDF4)**. 27 MB 기준 총 응답의 **+2 %**. `[미측정]` = GB 급 NetCDF4 |
| **분기가 늘어나나** | **늘지 않고 줄어든다.** 지금은 `ready` 를 기다리는 폴링 분기가 있고, 동기화하면 응답 시점에 `ready:true`·`failure` 가 확정돼 **폴링 루프가 사라진다**(`UploadModal.tsx:102` 조건이 첫 tick 에서 종료) |
| **`upload.failed` 는 어떻게 되나** | **동기 400/201 로 접힐 수 있지만 접지 않는 편이 낫다.** 계약 `UploadStatus.failure` 가 required(`fe-core.yaml:1782`)라 자리가 이미 있고, `0004:150-152` 의 사유 8값 중 **「형식 인식 실패」·「조각이 서로 다름」** 두 개는 stage1 감지가 실제로 낼 수 있다. 접수는 201 로 받고 `failure` 를 채워 내리면 계약·DB 양쪽에 맞는다 |
| **여전히 비동기여야 하는 것이 있나** | **하나뿐 — reaper.** 만료 회수는 요청 경로에 붙일 수 없다(요청이 안 오면 안 돈다). 다만 **별도 프로세스일 필요는 없다** — cron/스케줄러 1개, 또는 core-api 의 백그라운드 태스크로 충분하다. **릴레이는 소비자가 없으므로 필요 없다** |
| **원장·outbox 는 남기고 워커만 죽이면 더 단순한가, 더 헷갈리는가** | **지금보다는 단순하다.** 지금은 「워커가 있다」는 코드·문서·시험이 있는데 **실물이 안 돈다** — 이것이 가장 헷갈리는 상태다. 남길 거면 **왜 남는지가 한 줄로 말해져야 한다**: 「outbox 는 stage2 의 접속구고, stage1 에서는 `upload.accepted` 만 적재한다」 |

### C-4. 동기화로 **잃는 것** (정직하게)

1. **큰 파일에서 응답이 감지 시간만큼 더 길어진다** — 다만 실측상 전송 대비 2 % 미만이고, **GB 급 NetCDF4 는 `[미측정]`.**
   *완화* — 감지를 본체 **첫 1건**에만 걸면 파일 수에 선형이 되지 않는다. 단 계약 `FormatDetectedPayload.uniform`(`core-pipeline.json:62-64`)이 **조각 전건 비교**를 전제하므로, stage2 에서 이벤트를 살릴 때 의미가 어긋난다.
2. **재시도가 사라진다.** 지금 outbox 는 `attempt`·`max_attempts`(`0004:218-219`)를 갖고 있다. 동기 감지가 실패하면 재시도 대상이 없다.
   *다만* — 감지 실패는 `_FAILURE_MAP:46-47` 상 **「영구」**다. 재시도해도 결과가 같다.
3. **stage2 에서 되살릴 때 `createUpload` 안에 낀 감지 코드를 다시 빼내야 한다.** §D-㈐ 참조.

---

## D. 권고 — 세 안과 그 대가

**공통 전제 셋** (어느 안에서도 변하지 않는다)
- `0004` **무수정** (`〈70〉-㉱` · `인벤토리 B-4`). 되돌리면 `schema-diff` red.
- **계약 무수정** (`〈61〉-㉢`). 이벤트 7종 · `upload.accepted.source` const · `UploadStatus.ready` · `getUploadStatus` 는 손대지 않는다.
- **휴면 코드 삭제 0건** (`〈71〉-㉰`). `stage2` 마커 격리 + CI 유지.

---

### ㈎ 지은 대로 다 둔다 (dormant-but-running)

| 항목 | 내용 |
|---|---|
| **무엇이 바뀌나** | `S1-PLAN §2.1` 배정 그대로. `#5` 의 `STAGE_ORDER` 축소만 |
| **시험** | 깨지는 것 없음 |
| **계약** | 문제 없음 |
| **stage2 재건축** | **0** |
| **비용** | ⚠ **「dormant-but-running」이 실측과 다르다.** 워커는 running 이 아니라 **not-wired**(A-2). 이 안을 고르면 **「돌고 있다고 적힌 것」을 stage1 완료 정의에 넣게 된다** — `〈71〉-㉰` 이 경계한 바로 그 부식이다. 그리고 **FE 무한 폴링과 영원한 `ready:false` 가 그대로 남는다** = Ted 가 없애려던 「대기」가 살아남는다 |
| **판정** | **권고하지 않는다.** 다만 **이 안이 「아무것도 안 한다」는 아니다** — `#5` 의 `STAGE_ORDER` 축소는 하고, 폴링 문제는 안 건드린다는 뜻이다 |

---

### ㈏ 원장·계약 이벤트는 남기고 워커/릴레이/reaper 를 동기 발행으로 접는다

| 항목 | 내용 |
|---|---|
| **무엇이 바뀌나** | ⑴ `createUpload` 안에서 `detect_format` 호출 → `detected_format` 채움 → `ready=true` ⑵ `upload.accepted` 발행은 유지(계약) ⑶ 릴레이·`stdout_publish` 휴면 ⑷ reaper 를 **core-api 쪽 구현**(`core-api …domains/d5_ingestion.py:207-208 reap_expired`)으로 일원화 ⑸ `_PROCESSING` 은 코드에 남기되 **stage1 에서 항상 false 임을 주석·시험으로 명시** |
| **깨지는 시험** | core-api: 없음(`test_uploads.py:51` 은 계속 green — 발행이 남으므로). pipeline-worker: `test_worker_events.py` 8건 · `test_outbox_db.py` 10건 · `test_reaper_skips_processing.py` 4건이 **stage1 완료 정의 밖**으로 이동 → `stage2` 마커. **CI 는 계속 돌린다** |
| **계약 금지선** | **없다.** 이 안은 계약을 한 글자도 안 건드린다. `seam_consistency` G-b·㉡-3 은 **계약 산문**만 보므로(`seam_consistency.py:283-285`) green 유지 |
| **⚠ 단 하나의 회색지대** | **core-api 에 `detect_format` 을 넣는 것이 경계 위반인가.** `CLAUDE.md §3-4` 는 「core 는 좌표를 해석하지 않는다」이고 `test_preview_relay.py:189 test_no_geo_library_is_imported_anywhere_in_core_api` 가 그것을 지킨다. **매직바이트 감지는 geo 라이브러리가 아니다** — 단 `detect.py:195` 가 **`netCDF4` 를 임포트한다.** 이 한 줄이 core-api 로 들어가면 그 음성 시험이 **red 가 날 가능성이 높다**(시험 본문 미확인 → `[미확인]`). **착수 전 확인 필요** |
| **stage2 재건축** | **중간.** 워커 프로세스 골격(65줄)·릴레이(12줄)는 그대로 남아 있으므로 **다시 배선만 하면 된다.** 다시 지어야 하는 것은 `createUpload` 에서 감지를 **빼내는** 일 |

---

### ㈐ **㈏′ — 권고안.** ㈏ 에 「경계를 안 넘는다」와 「reaper 를 실제로 켠다」를 더한다

**㈏ 의 회색지대를 피하는 변형이다.** `detect_format` 을 core-api 로 **옮기지 않는다.**

| 무엇을 | 어떻게 |
|---|---|
| **⑴ 감지 배선** | **워커 프로세스를 죽이지 말고 켠다.** `Dockerfile:18` 의 CMD 를 헬스 서버 → **헬스 + 루프**로 바꾸고, compose 에 `COLAB_PIPELINE_DB_URL`·`COLAB_WORKER_LAB_ID`·`COLAB_WORKER_ACCOUNT_ID` 를 건다(`worker.py:20-22` 가 요구). `run_once` 에 **outbox 의 `upload.accepted` 를 집어 stage1 판 `process_upload` 를 부르는 소비 한 발**을 더한다 |
| **⑵ stage1 판 파이프라인** | `IngestionService.process_upload`(`…domains/d5_ingestion.py:137-232`)에서 **`:171-222` 를 stage1 에서 건너뛴다** — 감지(②) 다음이 곧 `upload.ready`(⑥). `run_file` 호출 자체가 빠지므로 파싱·좌표·COG 가 안 돈다 |
| **⑶ `STAGE_ORDER`** | `events.py:30-36` 5단계 → 2단계(`format-detected` → `ready`). **⚠ 이 상수는 지금 어디서도 쓰이지 않는다** — `grep -rn STAGE_ORDER` 결과 정의(`events.py:30`)와 **미사용 import**(`…domains/d5_ingestion.py:22`) 둘뿐. 즉 **의미 문서일 뿐 동작을 안 바꾼다** |
| **⑷ reaper** | 같은 루프에서 계속 돈다(`worker.py:47`). **처음으로 실제로 돈다** |
| **⑸ FE 폴링** | `UploadModal.tsx:102` 는 **그대로 둔다** — 워커가 `ready=true` 를 찍으면 **첫 tick 또는 두 번째 tick 에서 자연히 멈춘다.** 대기 시간 = 워커 폴 주기(`worker.py:58` 기본 `interval_seconds=5.0`) → **이 값을 1초 이하로 낮춘다** |
| **⑹ 계약** | **무수정.** 7종 선언·`source` const·`ready`·`getUploadStatus` 전부 그대로 |

| 항목 | 내용 |
|---|---|
| **Ted 의 기준에 대한 답** | **「업로드 경로에 분기·대기를 더하는가?」 → 더하지 않는다.** 지금 `createUpload` 응답 시간은 **1 ms 도 안 늘어난다**(감지가 요청 밖에 있으므로). 대기는 **무한 → 최대 워커 주기**로 **줄어든다.** 분기는 **폴링 종료 조건이 실제로 성립하게 되어 줄어든다** |
| **깨지는 시험** | `test_worker_events.py:35 test_happy_path_emits_stages_two_to_six` · `:75 test_two_runs_cover_all_seven_event_types` 등 **stage 5단계를 단언하는 것들** → `stage2` 마커 격리 + **stage1 판 2단계 시험 신설**. `test_outbox_db.py:81` 동일. **`test_reaper_skips_processing.py` 4건은 그대로 green** |
| **계약 금지선** | **없다.** 계약 수정 요구 0건 |
| **stage2 재건축** | **최소.** `process_upload` 의 건너뛴 구간(`:171-222`)을 **다시 켜는 것**이 전부다. 워커·릴레이·reaper·outbox·이벤트 7종·`_PROCESSING` 이 **전부 제자리에 살아 있다** |
| **⚠ 가장 강한 반론** | **「지금 안 도는 것을 굳이 켜는 것이 stage1 범위를 늘리는 것 아닌가.」** 맞다 — 이 안은 **`S1-PLAN §2.1 #4`(「살린다 · 무변경」)보다 일을 늘린다.** 배선·compose·Dockerfile 변경이 붙는다. **반론에 대한 답** — `S1-PLAN §2.1 #4` 의 「무변경」은 **워커가 이미 돌고 있다는 전제** 위에 있었고 그 전제는 실측상 거짓이다(A-2). 무변경으로 두면 stage1 완료 정의가 **「업로드하면 영원히 처리 중처럼 보이는 화면」** 위에 서게 된다 |

---

### D-1. 세 안 비교

| | ㈎ 다 둔다 | ㈏ 동기 발행 | **㈐ ㈏′ (권고)** |
|---|:--:|:--:|:--:|
| `createUpload` 응답 시간 증가 | 0 | **+1.6~23 ms**(`[미측정]` GB급 nc) | **0** |
| FE 무한 폴링 해소 | ✗ | ✅ (즉시) | ✅ (≤ 워커 주기) |
| reaper 가 실제로 돈다 | ✗ | ✅ | ✅ |
| core-api ↔ geo 경계 위험 | 없음 | **⚠ `[미확인]`** | 없음 |
| 계약 변경 | 0 | 0 | **0** |
| `0004` 변경 | 0 | 0 | **0** |
| stage2 재건축량 | 0 | 중 | **최소** |
| 「분기·대기」 기준 통과 | ✗ | ✅ | ✅ |

### D-2. 어느 안에서도 **하지 말아야 할 것**

- **이벤트 7종을 4종으로 줄이는 것** — `core-pipeline.json:300-311` 수정 = 계약 변경 = **`〈61〉-㉢` 멈춤·보고.**
- **`UploadStatus.ready` 를 nullable 로 바꾸는 것** — `fe-core.yaml:1782` required. 동상.
- **`0004` 의 `event_type` CHECK 7값을 줄이는 것** — `schema-diff` red + 계약 거울 파손.
- **`_PROCESSING` SQL 을 지우는 것** — stage1 에서 죽은 조건이지만 **stage2 에서 되살아난다.** 지우면 두 서비스 복제 동기화(`:38-39`·`:282-286`)의 근거가 사라진다.
- **`e04-flow.json` 을 고치지 않고 두는 것** — `S1-PLAN §2.1 #21` 이 이미 「개정 필수」로 잡았다. 이 감사는 **개정 폭을 좁혀 준다**: ㈐ 를 택하면 **단계 4·5·6·9 네 개만 `deferred` 로 돌리면 된다**(`seam_consistency.py:420-421` 이 `deferred` 를 이월로 인정한다). **단계를 지우지 않는다.**

---

## E. 이 감사가 재지 못한 것 (`[미측정]` · `[미확인]`)

- **GB 급 NetCDF4 의 `netCDF4.Dataset` try-open 시간.** 원천 최대 `.nc` 가 11.5 MB. **50 GB(`DR-11` 가정)에 대해 이 문서는 값이 없다.**
- **컨테이너 실환경의 I/O 수치.** C-2 는 WSL2 · drvfs 읽기 · 리눅스 tmp 쓰기다. staging 무접촉 지시에 따라 실환경은 안 쟀다.
- **`test_no_geo_library_is_imported_anywhere_in_core_api`(`test_preview_relay.py:189`)의 판정 범위** `[미확인]` — 시험 본문을 읽지 않았다. ㈏ 의 회색지대 판정이 여기 달렸다(㈐ 는 이 문제를 우회한다).
- **core-api 시험 170건·pipeline-worker 시험의 실제 통과 여부** — 이 세션은 `detect_format`·파일 I/O 만 실행했고 pytest 전량은 안 돌렸다.
- **GRIB 포맷 감지 실측** — `file_format_1_grib/00.Data/` 에서 후보 파일을 못 집었다. `formats.py:243 SUPPORTED_FORMATS` 에 GRIB 이 **없다**(NetCDF·Binary·HDF4·GeoTIFF 4종)는 사실은 확인했다.
- **`upload_storage_dir` 설정 여부** — `ingestion.py:55` 가 없으면 **프로세스 임시 디렉터리**로 떨어진다(`:59-63`). staging compose 에 그 값이 걸려 있는지는 안 봤다.
