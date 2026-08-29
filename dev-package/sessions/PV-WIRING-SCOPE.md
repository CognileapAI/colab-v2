# PV-WIRING-SCOPE — 미리보기 뒷단 배선의 범위를 확정한다

> **조사 회차 산출 · 2026-08-29 · 읽기 전용.** 구현 0건. `contracts/**`·`db/**`·`services/**`·
> `dev-package/PLAN-SoT.md`·`03-HANDOFF.md`·`work-items.yaml` **무접촉**(다른 에이전트 소유).
> 운영 스택 `colab_v2_staging_*` 은 **조회만** 했다(정지·재기동·DDL·쓰기 0건 · 컨테이너에 파일 남기지 않음).
> 값의 정본은 `PLAN-SoT §9` 다 — 이 문서는 등재 전 회차 기록이다.

---

## 0. 실측 재확인 (2026-08-29 · staging · 세는 단위를 밝힌다)

오케스트레이터 확인분을 **다시 쟀다.** 세는 단위 = `colab_platform` DB 의 행 · 시점 2026-08-29.

| 잰 것 | 값 | 질의 |
|---|---|---|
| `d5_pipeline_event` 유형별 | `upload.accepted` **15** · `file.format-detected` **3** · `upload.failed` **3** · **나머지 4종 각 0** | `select event_type, count(*) … group by 1` |
| 미발행(`published_at IS NULL`) | **0건** — 21건 전부 릴레이됨 | 같은 표 |
| `d3_dataset_autometa` | 행 **12** · `format` **0** · `crs` **0** · `grid` **0** · `variables` 비어있지 않은 행 **0** · `period_start` **0** | `count(col)` |
| `d5_upload_file.detected_format` | **129행 전건 NULL** (본체 123 · 격자 6) | `group by detected_format, kind` |
| `d5_upload` | **15**건 · `ready=true` **0** · `registered_at IS NOT NULL` **15** | — |
| `d3_dataset` / `d3_file` | **12** / **129** | — |

⚠ **오케스트레이터 요약에 없던 것 둘을 덧붙인다 — 둘 다 뒤 절의 판정을 바꾼다.**
① **`detected_format` 이 129행 전건 NULL** 이다. 즉 `format` 이 비어 있는 것은 사건 미발행 때문만이 아니다 —
등록 시점에 `core-api` 가 읽는 원장 열 자체가 비어 있었다(`app/routes/ingestion.py:445`·`:451`).
② **업로드 15건이 전부 `registered_at` 이 찍혀 있고 `ready=false`** 다. 이 조합이 §6 의 결론을 정한다.

---

## 1. 사건 셋의 계약 — **필요한 값을 담는다. 계약 개정 불요.** 단, 조건이 하나 붙는다

정본 = `contracts/events/core-pipeline.json` · 봉투 = `contracts/events/envelope.json`.

### 1.1 장부가 요구하는 값 ↔ 사건이 나르는 값

장부 = `db/platform/schema.sql:319` `d3_dataset_autometa`
(`format`·`variables`·`period_start`·`period_end`·`crs`·`grid`·`total_size_bytes`·`bundle_file_name`).

| 장부 열 | 나르는 사건 | 계약 필드 | 담기는가 |
|---|---|---|---|
| `format` | **`file.format-detected`** | `FormatDetectedPayload.format` (`string|null`, enum 없음) | ✅ |
| `variables` | `file.header-parsed` | `HeaderParsedPayload.variables` (`array|null`) | ✅ |
| `period_start`/`period_end` | `file.header-parsed` | `.period` (`Period{start,end}|null`) | ✅ |
| `crs` | `file.header-parsed` | `.crs` (자유 문자열 — enum 을 만들지 않는다고 계약이 명시) | ✅ |
| `grid` | `file.header-parsed` | `.grid` (자유 문자열) | ✅ |
| `total_size_bytes` | `file.header-parsed` | `.byteSizeTotal` (`integer≥0`, 합계) | ✅ |
| `bundle_file_name` | — | **없다** | ⚠ 사건에 없다. 지금도 등록 시점에 `core-api` 가 정한다(`ingestion.py:446` 계열) — **사건이 채울 값이 아니다** |

`file.crs-normalized`·`preview.cog-built` 은 **장부 열을 하나도 채우지 않는다**
(`CrsNormalizedPayload` = `sourceCrs`·`targetCrs`·`transformed`·`fileIds` / `CogBuiltPayload` = `fileIds`·`overviewLevels`·`referenceGridAvailable`).
이 둘은 **진행 사실**이지 장부 값이 아니다. 유실 감지의 대조 대상으로는 쓰이고, 되쓰기 대상은 아니다.

**→ 판정: `format`·`crs`·`grid` 셋은 계약이 이미 담는다. 이벤트 계약 개정은 필요 없다.**
⚠ **단, 한 사건이 아니라 둘에 걸쳐 있다** — `format` 은 ②, `crs`·`grid` 는 ③ 이다. 소비자는 **두 사건을 받는다.**

### 1.2 개정이 필요할 뻔했는데 아닌 것 — **대상 식별자**

봉투 산문 축자(`envelope.json` `description`):
> 「페이로드는 D5 가 소유한 `uploadId`·`fileId` 와 D1 의 `labId`·`actorAccountId` 만 싣는다.
> **다른 도메인 테이블을 직접 가리키는 식별자(`datasetId`·`projectId`·계보 관계 ID)를 두지 않는다**(`CLAUDE.md §3-1`).」

그런데 장부의 키는 `d3_dataset_autometa.dataset_id` 다. **사건은 `datasetId` 를 나를 수 없고, 날라서도 안 된다.**

- `d3_dataset` 에 `upload_id` 열이 **없다**(스키마 실측).
- `d5_upload.registered_at` 은 **시각만** 있고 `dataset_id` 가 없다 — `core-api/domains/d5_ingestion.py` 모듈 산문이 그 이유를 적어 뒀다(축자: 「`registered_at` 은 **시각만** 있고 `dataset_id` 가 없다 … 필요한 것은 여부이지 대상이다」).
- 실물로 남은 유일한 다리 = **파일 ID 동일성**. `d3_catalog.py:474` 산문 축자:
  「업로드 세계의 `fileId` ULID 가 `d3_file.id` 로 **그대로** 온다 … `d5_upload_file.id → d3_file.id` 에
  **FK 가 없으므로(불변규칙 1 이 금지한다) 이 동일성을 지키는 것은 여기 코드와 그 시험뿐이다.**」

**→ 소비자는 사건의 `uploadId` 로 곧장 장부 행을 못 찾는다. `payload` 안의 `fileId` → `d3_file.id` → `dataset_id` 로 되짚어야 한다.**
이것이 이 회차가 새로 세우는 **설계 판단**이고, `〈190〉-㉲` 가 「수신 창구의 형태 = 집행 회차의 판정 자리」로 남긴 자리에 정확히 해당한다.
⚠ `upload.accepted`·`upload.ready` 는 `fileId` 를 나르지만 **`file.header-parsed` 페이로드에는 `fileId` 가 없다**
(`unreadableFiles[].fileId` 는 **못 읽은** 조각뿐이다). `file.crs-normalized`·`preview.cog-built` 만 `fileIds` 전건을 싣는다.
→ **되짚는 재료는 같은 `uploadId` 의 `upload.accepted` 페이로드**에서 온다(그 표를 읽는 코드가 이미 있다 — `SqlLedger.accepted_files`).

---

## 2. 발행하는 쪽 — **기구가 이미 있다. 관례를 따르면 된다**

| 항목 | 실물 |
|---|---|
| 봉투 만들기 | `services/pipeline-worker/src/colab_pipeline/d5/events.py` — `make_envelope()` · `idempotency_key()`(`<타입>:<uploadId>`) · 타입별 페이로드 생성기 7종 |
| 발행 한 줄 | `domains/d5_ingestion.py:IngestionService._emit()` — 봉투를 만들고 `ledger.append_event()` 로 적는다 |
| 적히는 자리 | `SqlLedger.append_event()` — `INSERT … ON CONFLICT (idempotency_key) DO NOTHING` (`domains/d5_ingestion.py:389`) |
| 내보내기 | `app/worker.py:relay_unpublished()` → `published_at` 을 찍는다. `publish` 기본값 = **`stdout_publish`**(`worker.py:68`) |
| 발행 자리 셋 | `d5_ingestion.py` — `file.header-parsed`·`file.crs-normalized`·`preview.cog-built` 를 `stage1=False` 경로에서 **이미 `_emit` 한다** |

**본보기로 삼을 기존 사건 = `file.format-detected`.** 같은 `_emit` 을 쓰고 staging 에서 **실제로 3건 발행됐다**(§0).
새 발행 기구를 만들 필요가 없다 — **파이프라인 쪽에 새로 쓸 코드는 0 줄**이다.

⚠ **브로커가 없다.** `publish` 가 stdout 이고 `d5_pipeline_event` 가 곧 outbox 이자 큐다.
따라서 「받아 적는 쪽」은 메시지를 구독하는 것이 아니라 **그 표를 읽는다.** 이 사실이 §3·§4 를 정한다.

---

## 3. 받아 적는 쪽 — **소비 기구가 없다. 새로 만들어야 한다**

### 3.1 지금 `d5_pipeline_event` 를 만지는 코드 전건 (실측)

| 자리 | 무엇을 하나 | 소비 경로인가 |
|---|---|---|
| `core-api/domains/d5_ingestion.py:106` | `upload.accepted` **발행**(outbox INSERT) | 발행 |
| 같은 파일 `:47` `_PROCESSING` | 「② 이후 사건이 수명 창 안에 있는가」 — **존재 여부만** 본다 | 소비 아님(수명 판정) |
| 같은 파일 `:77` `_READY_PAYLOAD` | **`upload.ready` 페이로드를 읽어** 격자 판정을 seam 형태로 옮긴다 | ⭑ **사건을 읽어 행동하는 유일한 실물** — 다만 **조회 시점 lazy read** 이고 장부에 쓰지 않는다 |
| `core-api/tests/test_uploads.py:177`·`:199` | `file.header-parsed`·`file.crs-normalized` 를 **INSERT** | ❌ **시험 픽스처다.** 수명 규칙 ②(처리 중은 만료되지 않는다)·reaper 규칙 ㉠ 을 재현하려고 「파이프라인이 방금 한 발짝 나갔다」를 만드는 것뿐이고, 페이로드는 `'{}'::jsonb` 다. **소비 코드가 아니다** |
| `test_upload_grid_status.py`·`test_dataset_registration.py`·`test_upload_ledger_hidden.py` | 같은 성격(픽스처·계수 확인) | ❌ |

**→ 보고된 「`test_uploads.py` 가 사건을 다루는 코드를 갖고 있다」는 사실이다. 그러나 그것은 픽스처다.**
장부에 쓰는 소비자는 **레포 전체에 0건**이다(`pipeline-worker` 에 `autometa` 문자열 0건 · `core-api` 의 `_INSERT_AUTOMETA` 는 **등록 시점 1회**뿐).

### 3.2 지금 `format` 이 채워지는(채워졌어야 하는) 실제 경로 — 사건이 아니다

`app/routes/ingestion.py:445` 축자 무늬:
```
formats = {f.detected_format for f in files if f.detected_format}
… detected_format=(formats.pop() if len(formats) == 1 else None)
```
즉 **등록 전환 시점에 `d5_upload_file.detected_format` 을 읽어 한 번 넣는다.**
그 열은 워커가 `record_detected_format()` 으로 채운다. **staging 에서 그 열이 129행 전건 NULL** 이므로(§0)
등록은 언제나 `format=None` 으로 갔다. → **`format` 이 빈 것은 「사건이 없어서」가 아니라 「워커가 그 업로드를 돌지 않아서」다.**

---

## 4. 도메인 경계 — 사건 경유가 무엇을 지키는가

- `CLAUDE.md §3-1` = 「도메인은 자기 테이블 + D1 만 참조한다. 타 도메인 테이블 직접 FK·접근 금지」.
- `CLAUDE.md §3-4` = core-api 에 geo 라이브러리 금지 → **`core-api` 는 파일을 못 읽는다.**
- 따라서 값을 **만드는 쪽**(D5 / `pipeline-worker`)과 값을 **소유한 표**(D3 / `core-api`)가 갈린다.

**사건 경유가 경계를 지키는 구조 (지켜야 할 세 줄).**

1. **파이프라인은 `d3_*` 를 쓰지 않는다.** 자기 표 `d5_pipeline_event` 에 사실을 적는 것으로 끝난다 — 지금 `_emit` 이 하는 그대로.
2. **카탈로그는 `d5_*` 를 오직 한 파일에서만 만진다.** `core-api/domains/d5_ingestion.py` 모듈 산문 축자:
   「**`d5_*` 를 만지는 core-api 코드는 이 파일 하나뿐이다.** 라우트·D3·D4 는 Port 타입으로만 말한다.」
   → **새 소비자도 이 파일(또는 그 Port) 안에 서야 한다.** D3 코드가 `d5_pipeline_event` 를 직접 읽으면
   `tests/test_upload_ledger_hidden.py` 가 red 를 낸다(그 시험이 실물로 있다).
3. **두 도메인은 서로를 부르지 않는다.** HTTP 호출도, 주기 조회도 없다 — `〈190〉-㉯` 가 둘 다 기각했다.

**본보기로 지목할 기존 사건 = `upload.ready`.**
발행은 워커(`d5_ingestion.py` ⑥) · 소비는 core-api 의 `_READY_PAYLOAD`(같은 표를 읽어 seam 형태로 옮긴다) ·
판정은 하지 않는다(축자: 「**core-api 는 판정하지 않는다** — 이벤트가 말한 것을 읽어 seam 형태로 옮길 뿐이다」).
**같은 모양이 이미 돌고 있고**, 새 소비자는 그 모양에 「읽어서 seam 이 아니라 **장부에 적는다**」와
「조회 시점이 아니라 **워커 바퀴/전용 바퀴 시점**에 돈다」 둘만 더한다.

⚠ **경계상 갈리는 지점 하나 — 어느 배포 단위가 소비 바퀴를 도는가.**
`core-api` 는 HTTP 요청 위에서만 돌고 상시 바퀴가 없다(reaper 도 `UploadLedgerAdapter.reap_expired()` 를 부르는 쪽이 따로 있다).
`pipeline-worker` 에 소비 바퀴를 두면 **워커가 `d3_*` 를 쓰게 되어 불변규칙 1 을 깬다** — 기각.
→ **소비 바퀴는 `core-api` 쪽에 서야 한다.** 그 형태(요청 위 lazy 반영 / 별도 바퀴 / 등록 전환 시 일괄 반영)는 §7-㉮ 의 내용이다.

---

## 5. 유실 감지를 어디에 두는가 — 후보 셋

완료 조건 축자(`〈190〉-㉱`): 「**사건이 발행되고도 장부에 반영되지 않으면 red 를 낸다 — 발행 건수와 기록 건수를
대조해 어긋나면 실패로 계수한다. 대상 0건도 red 다(green-by-skip 금지).**」

| 후보 | 실물 근거 | 무엇을 대조하나 | 못 잡는 것 |
|---|---|---|---|
| **ⓐ 게이트** (`gates/run.sh` 24종 옆에 한 줄 · 무늬 본보기 = `stage2-markers.sh` 의 fail-closed 3조건) | `gates/tools/stage2-markers.sh` 가 **「수집 0건 · skipped · failed 전부 red」** 를 이미 구현했고 `stage2-markers-selftest.sh` 가 그 셋을 red fixture 로 증명한다 | 적용 DB 에서 `d5_pipeline_event` 의 `file.format-detected`·`file.header-parsed` 건수 ↔ `d3_dataset_autometa` 의 채워진 행 건수 | **DB 접속이 필요하다** — `schema-diff` 처럼 URL 이 없으면 red 로 떨어지게 해야 한다(관대한 기본값 금지). CI 에서 상시 돌리려면 적용 DB 가 있어야 하고, **로컬 시험 DB 에는 대상이 0건**이라 그 자체로 red 가 된다(=「대상 0건도 red」와 일치하지만, 개발 중 상시 red 를 뜻한다) |
| **ⓑ 워커/소비자 자체 검사** (소비 한 바퀴가 끝날 때 반영 건수를 세어 어긋나면 예외) | `worker.py:run_once` 가 이미 `(처리, 릴레이, reaper)` 삼중 계수를 돌려준다 — 계수를 돌려주는 자리가 있다 | 그 바퀴에서 **읽은 사건 수 ↔ UPDATE 된 행 수** | **바퀴가 안 도는 것을 못 잡는다.** 지금 실패가 정확히 그것이다(워커가 대상 0건이라 아무 일도 안 하고 조용히 성공). 「대상 0건도 red」를 여기서 만들면 **정상 유휴 상태가 상시 red** 가 된다 |
| **ⓒ 원장 대조 스크립트** (시험 안에서 도는 대조 · `-m dbint` 계열) | `services/core-api/tests/` 에 실 DB 를 쓰는 시험 묶음이 이미 있다(`conftest.py` 가 `d5_pipeline_event` 를 정리 대상에 넣는다) | 픽스처로 사건을 넣고 **소비 후 장부가 채워졌는가**를 1:1 로 | **staging 실물의 유실을 못 잡는다.** 시험은 자기가 만든 데이터만 본다 — 운영에서 반영이 밀리는 것은 보이지 않는다 |

**권고 = ⓐ 를 판정처로 두고 ⓒ 를 그 게이트의 selftest 로 붙인다.** ⓑ 는 단독으로 완료 조건을 만족하지 못한다.
⚠ **셋 다 「대상 0건도 red」를 만족시키려면 세 상태를 코드로 갈라야 한다**(`CLAUDE.md §4`) —
**대조 대상이 선언되면 검사한다 · 명시적으로 면제하면 건수를 드러낸 채 넘어간다 · 아무 말도 없으면 실패한다.**

⚠ **오늘 staging 에 ⓐ 를 걸면 즉시 red 다** — 발행 3건(`file.format-detected`) 대비 장부 `format` 0건이고,
나머지 두 사건은 발행 0건이라 「대상 0건」이다. **그것이 옳은 동작이다.**

---

## 6. 워커 스위치 — 켜는 순서와, 켜도 **지금은 아무것도 안 돈다**는 실측

스위치 = `services/pipeline-worker/src/colab_pipeline/app/worker.py` `drive_uploads()` 안
`service.process_upload(UploadWork(…), stage1=True)` **한 줄**(env 토글 없음).

### 6.1 켜면 무엇이 돌기 시작하는가 — **대상 0건이다**

대상 집합은 `SqlLedger.pending_uploads()` 가 정한다. 조건 축자 넷 —
「접수됐고 · 아직 `ready` 가 아니고 · 실패하지 않았고 · **등록 전환 전이다**(`u.registered_at IS NULL`)」.

**staging 실측 = 업로드 15건 전부 `registered_at IS NOT NULL`**(§0). → **pending 집합 = 0.**

**→ `stage1=False` 로 바꿔도 파일 123건은 한 건도 돌지 않는다. 부하는 0 이고, 값도 안 채워진다.**
⚠ 「켜면 123건이 돈다」는 **틀렸다.** 이 문서 이전의 어느 요약도 이 조건을 세지 않았다 — 여기서 정정한다.

### 6.2 그래서 순서는 이렇게 갈린다

1. **먼저 소비자가 서 있어야 한다.** 소비자 없이 켜면 사건만 쌓이고 장부는 그대로다 —
   `〈190〉-㉱` 축자 「없으면 **지금 상태가 그대로 재현된다**」가 그 말이다.
2. **유실 감지가 소비자와 같은 회차에 붙어야 한다.** 나중에 붙이면 그 사이 기간은 검사되지 않은 채 green 으로 흐른다.
3. **스위치는 마지막이다.** 그리고 켠 직후 검증은 **새 업로드 1건**으로만 성립한다 — 기존 15건은 대상 밖이다.

### 6.3 위험

| 위험 | 내용 |
|---|---|
| **기존 12 데이터셋은 이 경로로 채워지지 않는다** | 등록 전환된 업로드는 영영 pending 이 아니다. 소급 반영은 **별건**이고 원장 되쓰기라 판정이 필요하다. 지금 범위에 넣지 않는다 |
| **`upload.ready` 발행 0건의 정체가 미해소** | 15건이 `ready=false` 인 채 등록됐다 — 사람이 화면에서 등록을 눌렀는데 파이프라인은 완주 표시가 없다. `〈190〉-㉴`-⑵ 가 남긴 `[미확인]` 그대로다 |
| **COG 산출물이 여전히 임시 자리에 떨어진다** | `d5/pipeline.py:95` `out_path = workdir / (… + ".cog.tif")`. `preview.cog-built` 는 「준비됐다」만 말하고 **어디 있는지는 말하지 않는다**(계약에 경로 필드 없음 — 저장 배치는 배포 내부 사정이라 계약에 싣지 않는다는 것이 정본 입장) |
| **켜면 좌표계·COG 단계가 실제로 도는 부하가 생긴다** | 다음 새 업로드부터다. 오늘 잰 값 = `d5-grid` 회차의 **149/149** 통과(파일 내부 격자 산출까지). COG 변환 자체의 산출 생성은 여전히 `[미확인]`(`D5-STAGE2-SCOPE §7-㉠`) |

---

## 7. 조각 분해 — 독립 착지 단위 넷. 먼저 할 하나는 ㉮

**범위를 늘리지 않는다.** 아래는 `〈190〉`(사건 경유 되쓰기)이 요구한 것 안에서만 쪼갠 것이고,
`〈191〉`/`PV-STORAGE`(산출물의 자리)는 **이 분해에 넣지 않았다** — 다른 결정 항목이다.

| # | 조각 | 의존 | 파일 면 | 판정 필요 | 오라클 |
|---|---|---|---|---|---|
| **㉮** | **사건 → 장부 소비자.** `core-api` 쪽 한 파일 안에서 `file.format-detected`·`file.header-parsed` 를 읽어 `d3_dataset_autometa` 의 `format`·`crs`·`grid`(＋`variables`·`period`·`total_size_bytes`)를 채운다. **대상 행 찾기는 `payload.fileId → d3_file.id → dataset_id`** | **없음** | `services/core-api/src/colab_core/domains/d5_ingestion.py`(＋`ports/ingestion.py`) · `d3_catalog.py` 쓰기 한 자리 · 시험 | ⚠ **하나 있다 — 반영 시점**(§7-보론) | 픽스처로 두 사건을 넣고 소비를 돌리면 `autometa` 세 열이 NULL 이 아니게 된다. **지금은 red 다**(소비자 0건) |
| ㉯ | **유실 감지 게이트 ＋ selftest.** 발행 건수 ↔ 반영 건수 대조. 세 상태(검사·명시 면제·무언 실패) | ㉮ | `gates/tools/` 새 파일 2 · `gates/README.md` 표 한 줄 · `gates/run.sh` 등록 | 불요(완료 조건이 축자로 확정돼 있다) | red fixture 셋 — ⓐ 반영 0건 ⓑ 건수 어긋남 ⓒ **대상 0건**. 셋 다 red 여야 한다 |
| ㉰ | **워커 스위치 해제** `stage1=True` → 조건부/제거 | ㉮·㉯ | `app/worker.py` 한 줄 | 불요 | 새 업로드 1건에서 `file.header-parsed`·`file.crs-normalized`·`preview.cog-built` 가 각 1건 발행되고 장부가 채워진다 |
| ㉱ | **COG 산출물을 `미리보기 산출물` 자리에 놓기** | ㉰ · **PV-STORAGE 후속** | `d5/pipeline.py` · `kernel/storage_layout.preview_key()` | ⚠ **판정 필요** — `preview_key(contentKey, ext)` 의 `contentKey` 는 **viz-render 의 렌더 파라미터 다이제스트**(`d7_visualization/cache.py#render_cache_key`)이고, **파이프라인의 COG 에는 그 다이제스트를 만드는 자리가 없다** | 산출물이 임시 workdir 밖 정해진 자리에 놓인다 |

### 지금 착수할 하나 = **㉮ 사건 → 장부 소비자**

**고른 이유 셋.**
1. **선행 의존 0.** 계약·DB 스키마·워커 스위치를 한 글자도 안 건드린다. 파일 면이 `core-api` 한 파일과 그 Port 안에서 닫힌다.
2. **red 를 먼저 볼 수 있다.** 오늘 장부 세 열이 0건이라는 것을 §0 에서 실측했다 — 통과·불통과가 값으로 갈린다.
3. **㉯ 의 대조 대상을 만든다.** 소비자가 없으면 유실 감지는 「반영이 없는 것이 정상」과 「유실」을 구분하지 못한다.

⚠ **㉮ 가 스위치를 켜는 것이 아니다.** ㉮ 뒤에도 사건 셋 중 둘은 여전히 발행 0건이다 — 켜는 것은 ㉰ 다.
**착지 단위를 늘리지 않는다.**

### 보론 — ㉮ 안에서 반드시 갈라야 할 판정 하나 (**반영 시점**)

사건은 **등록 전에** 난다(계약 축자: `upload.ready` 에 「**저장된 것은 아무것도 없다**」 · 그래서 `datasetId` 가 없다).
장부 행 `d3_dataset_autometa` 는 **등록 전환 시점에** 생긴다(`d3_catalog.py:_INSERT_AUTOMETA`).
**둘의 순서가 고정돼 있지 않다** — staging 실물은 오히려 반대다(등록 15 / `ready` 0).

→ 소비자는 **대상 행이 아직 없는 사건**을 반드시 만난다. 그때 무엇을 하는가가 갈림이다.
**ⓐ 그냥 버린다 = 값이 영영 안 들어간다**(지금 상태의 재현) · **ⓑ 미반영으로 남겨 두고 등록 전환 때 다시 읽는다**
· **ⓒ 등록 전환이 사건을 읽어 함께 채운다**(그러면 「사건 경유」가 등록 경로에 흡수된다).
**여기서 고르지 않는다** — 이것이 `〈190〉-㉲` 가 「수신 창구의 형태 = 집행 회차의 판정 자리」로 남긴 바로 그 자리이고,
근거 없이 박으면 다음 세션의 잘못된 전제가 된다. **㉮ 착수 시 첫 판정으로 올린다.**

---

## 8. `[미확인]` — 이번에 못 잰 것

| # | 못 잰 것 | 무엇을 하면 풀리나 |
|---|---|---|
| ㉠ | **`upload.ready` 가 한 번도 발행되지 않은 채 15건이 등록된 경위** | `d5_upload` 의 시각 열과 `d3_dataset.uploaded_at` 을 대조해 등록이 어느 경로로 들어왔는지 확인. 화면 경로인지 시드인지 갈린다 |
| ㉡ | **`detected_format` 129행 전건 NULL 의 원인** | 발행된 `file.format-detected` 3건의 `payload.perFile` 을 읽어 `format:null` 인지 확인. null 이면 감지 실패이고, 값이 있는데 열이 비었으면 `record_detected_format` 쪽 결함이다 |
| ㉢ | **소비 바퀴를 무엇이 돌리는가** | `core-api` 에 상시 바퀴가 없다. reaper 를 부르는 쪽을 찾아 같은 자리에 얹을 수 있는지 확인 |
| ㉣ | **COG 산출물의 `contentKey`** | `preview_key()` 가 요구하는 다이제스트를 파이프라인이 무엇으로 만들지 — `render_cache_key` 를 재사용할 수 있는지(도메인 경계 위반 여부 포함) 실물 대조 |
| ㉤ | **유실 감지 게이트가 CI 에서 어떤 DB 를 보는가** | `schema-diff` 의 체인별 URL 무늬를 그대로 쓸 수 있는지 확인. 없으면 red 로 떨어져야 한다 |
| ㉥ | **기존 12 데이터셋의 소급 반영** | 별건. 원장 되쓰기라 목록을 고정한 뒤 판정 |

## 9. 이번에 세지 않은 판단기준 (다음 회차의 진입조건)

- 게이트 전량(`gates/run.sh all`) — **이번 회차는 코드를 안 고쳤으므로 돌릴 대상이 없다.** 돌리지 않았다.
- COG 변환의 실제 산출 생성 — `D5-STAGE2-SCOPE §7-㉠` 그대로 남는다.
- `stage2-markers` — 이 회차에 재측정하지 않았다. 마지막 실측은 `D5-GRID §7`(17 passed · skipped 0).
