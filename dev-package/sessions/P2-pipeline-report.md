# P2 · W2 `P2-pipeline` 실행 보고

> **레인** `P2-pipeline` (W2, 병렬 3 중 하나) · **일자** 2026-08-23 · **소유 디렉터리** `services/pipeline-worker/`
> **커밋하지 않았다** — 커밋·`03-HANDOFF`·`PLAN-SoT` 갱신은 메인 세션 몫(`P2-EXEC §7`).
>
> **증거와 해석을 가른다**(`DATA-REFERENCE §0 M-5`). `§2`·`§3`·`§4`·`§7` 의 명령·출력은 **실측 그대로**이고,
> `해석` 이라 적힌 자리는 **잠정**이다. **관측하지 않은 수는 적지 않았다**(`M-4`). 인용한 `파일:행` 은
> 전부 `cat -n`/`grep -n` 으로 확인했다(`M-7`).

---

## 0. 한눈에 — 5개 산출의 상태

| # | 지시 | 상태 | 근거(이 문서 안) |
|---|---|:--:|---|
| ⑴ | outbox/워커 골격 · **이벤트 7종 실발행** · 멱등 키 · 릴레이 · reaper | ✅ | `§3`(행복·실패 두 경로 · 원장 실측 7종) |
| ⑵ | `renderable` 판정 신설 (목록을 계약에 박지 않음) | ✅ | `§4.1` |
| ⑶ | 축 판별 (`〈63〉-㉰` ⓐ~ⓓ + `〈65〉` + `〈66〉`) | ✅ | `§4.2`(실물 16건 전건 green) |
| ⑷ | `§6-2` 음성 시험 3부류를 파이프라인 경로에 연결 | ✅ | `§4.3`(세 부류 **RED → GREEN** 실물) |
| ⑸ | `DR-1` README 포맷표 | ✅ **(이미 목록이었다)** | `§4.4` — 고친 것은 **다른 줄**이다(멱등 키 드리프트) |
| + | **결손 정정** — `grid.py` 의 `.npy` 전용 glob 이 결합축 `.nc` 를 조용히 무시 | ✅ | `§4.5` |

**하지 않은 것과 새 위험은 `§5`·`§6` 에 따로 적었다. 감추지 않았다.**

---

## 1. 진입조건 확인 (구현 전)

| 전건 | 실측 |
|---|---|
| 계약 동결 | `contract-lint` · `event-lint` · `event-breaking` · `contract-breaking` green (`§7`). **계약을 한 글자도 고치지 않았다** — `git status` 에 `contracts/` 변경 0건 |
| W1 `d5_*` 원장 | `db/platform/schema.sql:433-532` 에 `d5_upload` · `d5_upload_file` · `d5_pipeline_event` 실재. 마이그레이션 `0004_p2_grid_axis_and_d5.py` 실재 |
| D5 기존 시험 | **착수 기준선 32건 green** (단위 26 + 실데이터 E2E 6). `§2` |
| 원천 데이터 | `03 Reference-Data` 마운트 확인 — tif 62건 · 격자 16건 실재 |
| 축 판별 입력 | `〈65〉`(ⓐ 충족·유권해석) · `〈66〉`(두 불리언·거절 의미론) 판정문을 그대로 구현했다 |

---

## 2. 기준선 (EVIDENCE · 구현 전)

```
$ .venv/bin/python -m pytest tests/ -m "not e2e" -q
26 passed, 6 deselected, 8 warnings in 2.54s

$ COLAB_REFERENCE_DATA=<원천> .venv/bin/python -m pytest tests/ -q
32 passed, 8 warnings in 5.45s
```

> `.venv` 는 이 레인이 만들었다(`requirements-dev.in` 기준). 착수 시점에 레포에 가상환경이 없었다.

---

## 3. 이벤트 7종 — **행복 경로 + 실패 경로** (`P2-EXEC §6-7`)

### 3.1 RED 먼저 (EVIDENCE)

```
$ .venv/bin/python -m pytest tests/ -m "not e2e" -q
ModuleNotFoundError: No module named 'colab_pipeline.d5.events'
ModuleNotFoundError: No module named 'colab_pipeline.d5.axis'
ModuleNotFoundError: No module named 'colab_pipeline.d5.renderable'
ImportError: cannot import name 'IngestionService' from 'colab_pipeline.domains.d5_ingestion'
Interrupted: 7 errors during collection
6 deselected, 7 errors in 1.96s
```

### 3.2 GREEN — 실 DB(`d5_*`) 에 남은 것 (EVIDENCE)

일회용 postgres `p2pipe_pg`(**호스트 포트 publish 0개**, `--tmpfs`)에 `db/platform/schema.sql` +
`app-role.sql` + 시드를 적용하고, **`colab_app`(NOSUPERUSER·NOBYPASSRLS) 롤**로 접속해 돌렸다.

```
행복 경로 발행: ['file.format-detected', 'file.header-parsed', 'file.crs-normalized', 'preview.cog-built', 'upload.ready']
  격자 축: {'01M0QCR1M60QGJ751VQ2QRJFMQ': (False, True)}
실패 경로 발행: ['file.format-detected', 'upload.failed']
  실패 페이로드: {"failure": {"failedAt": "file.format-detected", "class": "영구", "reason": "형식 인식 실패", "willRetry": false, "detail": "본체 전건이 알려진 매직바이트가 아니다"}}

=== d5_pipeline_event 원장 실측 ===
  file.crs-normalized    pipeline-worker  1건  예: file.crs-normalized:01M0QCR14N6JSCA9YEJPHNZV7J
  file.format-detected   pipeline-worker  2건  예: file.format-detected:01M0QCR14N6JSCA9YEJPHNZV7J
  file.header-parsed     pipeline-worker  1건  예: file.header-parsed:01M0QCR14N6JSCA9YEJPHNZV7J
  preview.cog-built      pipeline-worker  1건  예: preview.cog-built:01M0QCR14N6JSCA9YEJPHNZV7J
  upload.accepted        core-api         2건  예: upload.accepted:01M0QCR14N6JSCA9YEJPHNZV7J
  upload.failed          pipeline-worker  1건  예: upload.failed:01M0QCR290YM7VRX4AS92PM2T0
  upload.ready           pipeline-worker  1건  예: upload.ready:01M0QCR14N6JSCA9YEJPHNZV7J
  서로 다른 이벤트 타입 수: 7

=== 릴레이 ===
  내보낸 건수 9 · 남은 미발행 0
```

**어떻게 실패 경로를 만들었나** — 알려진 매직바이트가 없는 2 KB 파일을 본체로 넣었다.
`detect_format` 이 `None` 을 내고 **본체 전건이 미상**이므로 `upload.failed`(사유 `형식 인식 실패`,
분류 `영구`, `willRetry=false`)가 나간다. 행복 경로 한 번만으로는 이 이벤트가 **구조적으로 안 나온다**.

**정직하게 — `upload.accepted` 는 이 레인이 낸 것이 아니다.** 봉투가 `source` 를 `core-api` 상수로
못박았고 `d5_pipeline_event_source_matches_type` CHECK 가 DB 에서 강제한다. 위 증거에서 그 2건은
**core-api 자리를 시험이 대신 세운 것**이고, 워커가 그것을 만들려 하면 코드가 거부한다
(`d5/events.py:86` `WorkerCannotEmitError` · 시험 `test_worker_refuses_to_emit_upload_accepted`).
**즉 「7종이 원장에 있다」는 실측이고, 「7종을 워커가 낸다」는 거짓이다 — 워커 소관은 ②~⑦ 이다.**

### 3.3 멱등 키·릴레이·reaper (EVIDENCE · 실 DB 시험 6건)

```
$ COLAB_PIPELINE_DB_URL=... .venv/bin/python -m pytest tests/test_outbox_db.py -q
6 passed in 3.64s
```

| 시험 | 무엇을 세웠나 |
|---|---|
| `test_worker_writes_all_stage_events_into_the_w1_ledger` | ②~⑥ 이 `d5_pipeline_event` 에 실제 행으로 남고 `published_at` 은 아직 NULL · `source` 가 타입별로 갈린다 |
| `test_redelivery_does_not_duplicate_rows` | 같은 업로드 2회 처리 → 행 수 불변(`ON CONFLICT (idempotency_key) DO NOTHING`) |
| `test_relay_marks_published_and_is_the_only_thing_that_does` | 릴레이 뒤 미발행 0 · 2회차 릴레이는 0건 |
| `test_reaper_deletes_expired_uploads` / `..._leaves_registered_uploads_alone` | 만료 미등록만 지우고 이벤트도 CASCADE 로 함께 사라진다(`〈64〉-ⓒ`) · **등록된 것은 안 지운다** |
| `test_axis_row_is_two_booleans_and_empty_axis_is_refused_by_the_db` | 축 행이 `(false, true)` 두 불리언 · **축이 빈 격자 행은 DB 가 거부**(`IntegrityError`) |

**멱등 키 = `<이벤트 타입>:<uploadId>`** (`envelope.json#IdempotencyKey` 그대로. `d5/events.py:58`).
난수를 쓰지 않으므로 outbox 행이 다시 만들어져도 같은 키가 나온다.

---

## 4. 나머지 산출

### 4.1 `renderable` 판정 (`d5/renderable.py`)

- `RENDERABLE_FORMATS` 는 `formats.SUPPORTED_FORMATS` **에서 파생**한다(`renderable.py:19`) — 두 곳에 적으면 갈라진다.
- 감지 실패(`None`) → `false`. 계약 문구 그대로.
- **`NB-3` 준수** — 목록을 계약에 박지 않았다. 그것을 시험이 지킨다
  (`test_contract_does_not_pin_the_list` 가 `contracts/events/core-pipeline.json` 을 직접 읽는다).
- ⚠ **해석(잠정)**: 「지원 4종 = 그릴 수 있는 4종」은 **오늘의 값**이지 정본 판정이 아니다.
  정본이 미리보기 지원 범위를 §11 미결로 남겼으므로, 갈라지는 날 `renderable.py` 한 줄이 갈라진다.

### 4.2 축 판별 (`d5/axis.py`) — **실제로 구현된 규칙**

| 순서 | 신호 | 단독 판정 | 근거 |
|:--:|---|:--:|---|
| ① | 컨테이너 내부 변수명(`lat`·`lon`, HDF5 매직으로 판별) | **가능** | 측정 §2.2 · 값 범위로 교차검증 |
| ② | **`max > 90` 또는 `min < -90` → 경도** | **가능** | **`〈65〉` 유권해석**. `axis.py:181` |
| ③ | 쌍 정합 — **형상 같은 격자가 정확히 2건**일 때만. 하나가 ②로 서면 나머지는 여집합, 둘 다 모호하면 max·범위 큰 쪽이 경도 | 1차 신호 | `〈63〉-ⓑ` · 측정 §3.3 · `axis.py:236,250` |
| ④ | 이방성(`mad↓` vs `mad→`) | **불가 — 기록만** | 측정 §3.2(단독 14/16) |
| ⑤ | 파일명 | **불가 — 대조만** | 측정 §3.4 |
| ⑥ | 못 정하면 **`AxisUndeterminedError` → 그 파일 거절** | — | `〈66〉` 유권해석 |

- **출력은 `carries_lat`/`carries_lon` 두 불리언**이다. `AxisDetection` 에 `grid_axis` 속성이
  **없다는 것까지** 시험이 단언한다.
- **파일명이 단독으로 아무것도 못 정한다**를 시험에 박았다 — `lat_seoul.npy`·`lon_seoul.npy`
  둘 다 값이 모호하면 **예외**다(`test_filename_never_decides_alone`). 이름이 「위도」인데 값이
  133 이면 **값을 따르고 불일치를 경고로 남긴다**.
- **거절은 등록을 막지 않는다**(`〈63〉-ⓒ`) — 격자 파일 하나가 거절돼도 업로드는 `upload.ready`
  까지 간다(`test_grid_file_with_undetermined_axis_is_rejected_but_upload_continues`).

**실물 16건 전건 (EVIDENCE)**

```
$ COLAB_REFERENCE_DATA=<원천> .venv/bin/python -m pytest tests/test_axis_detect_real.py -q
5 passed in 14.43s
```

- `test_all_sixteen_real_grid_files_resolve` — 쌍 7건(=14 파일) + 결합축 `.nc` 2건 = **16 파일 전건 확정, 거절 0**
- `test_every_real_longitude_npy_is_settled_by_value_range_alone` — 경도 `.npy` 7건이 **② 한 단계**로 확정
  (`method == "값 범위(물리적 불가)"`). ⓑ 를 문면대로 구현했다면 이것들이 쌍 정합으로 내려갔을 자리다
- `test_anisotropy_would_flip_the_two_modis_longitudes` — MODIS 경도 2건에서 `mad↓ > mad→` 임을
  **다시 재서** 확인하고, 구현이 그것을 따르지 않고 「경도」를 유지하는 것을 단언
- `test_four_same_shape_files_in_one_upload_are_rejected_not_guessed` — 한 폴더 4파일을 한 업로드로
  주면 위도 2건이 **거절**된다(짝짓기 미정의). 지어내지 않는다

> **해석(잠정)** — 위 16건에서 모호가 0인 것은 **표본의 성질**이다(`〈65〉` 가 이미 적었다).
> 동경 90° 미만·서반구 자료는 이 표본에 없다. `〈63〉-ⓓ`(축 수동 지정 폴백 부재)는 **실질 위험으로 그대로 살아 있다**.

### 4.3 음성 시험 3부류 — **RED → GREEN 을 눈으로 봤다**

**RED (EVIDENCE)** — 「타일링 있으면 COG」 규칙을 주입해 돌렸다(임시 플러그인, 레포에 남기지 않음):

```
$ PYTHONPATH=/tmp pytest tests/test_tiff_classes_pipeline_real.py -q -p naive_rule_plugin
FAILED test_source_corpus_splits_into_the_three_measured_cohorts - assert (22, 0, 40) == (6, 16, 40)
FAILED test_tiling_alone_rule_disagrees_on_exactly_the_sixteen   - assert 0 == 16
FAILED test_negative_real_cog_six_are_never_recorded_as_our_artifact - AssertionError: assert 22 == 6
FAILED test_negative_tiled_only_sixteen_are_normal_input_not_our_product - assert 0 == 16
4 failed, 1 passed in 8.42s
```

**이 출력이 지시서의 경고를 그대로 실증한다** — 순진한 규칙 아래서 **양성 ①-㉰(스트립 40건)만
green 으로 남는다**(`1 passed`). 부류 ① 만으로 세운 시험이었다면 규칙을 작동시키지 못했을 것이다.

**GREEN (EVIDENCE)**

```
$ COLAB_REFERENCE_DATA=<원천> pytest tests/test_tiff_classes_pipeline_real.py -q
5 passed in 15.72s
```

| 부류 | 실측 | 파이프라인 경로에서 단언한 것 |
|---|:--:|---|
| 음성 ①-㉮ 진짜 COG | **6건** | `res.artifacts == []` — **우리 산출물이 기록되지 않는다**(`DR-2`). 그래도 `preview.cog-built` 는 나가고 `upload.ready` 로 끝난다 |
| 음성 ①-㉯ 타일만 | **16건** | 순진한 규칙은 전건을 `cog` 라 부른다(시험이 그것도 단언한다). 구현은 `tiled-only` 로 부르고 **정상 입력으로 우리 COG 를 만든다**(`〈63〉-㉯`) |
| 양성 ①-㉰ 스트립 | **40건** | 정상 통과 · 산출물 1건 생성 |

판정 규칙 실물 = `d5/tiff_probe.py:79-83`(`main_tiled and ifd_count >= 2` → `cog`).
**규칙을 고치지 않았다** — 이 레인이 한 것은 그것을 **파이프라인 경로(`IngestionService`)에 문** 것이다.

### 4.4 `DR-1` — 확인 결과 **이미 목록이었다**

`services/pipeline-worker/README.md:11-21` 은 착수 시점에 이미
`지원 포맷 — NetCDF · Binary · HDF4 · GeoTIFF` 목록 + 4행 표였다(D5 세션이 닫았고
`03-HANDOFF.md:79` 에 `DR-1 ✅` 로 적혀 있다). **없는 결손을 고쳤다고 적지 않는다**(`M-6`).

**대신 같은 파일에서 진짜 드리프트를 하나 찾아 고쳤다** — 「규칙」 절의
**`멱등 키 = 처리 실행 ID + 스테이지`** 는 **동결 계약과 어긋난다.** `envelope.json#IdempotencyKey`
는 「발행자가 난수를 쓰지 않으므로 outbox 행이 다시 만들어져도 같은 키가 나온다」이고,
실행 ID 를 섞으면 재적재 때 키가 달라져 **중복 제거가 뚫린다.** 계약을 따르고 그 사실을 README 에 남겼다.

### 4.5 결손 정정 — 결합축 `.nc` 격자가 조용히 무시되던 자리

`〈66〉-ⓒ` 가 이 레인 결손으로 등재한 것. 예전 `find_reference_grid` 는 `*.npy` 만 훑어서
`rdr_500m_latlon.nc`(=`〈66〉` 이 **HSR 정본 격자**로 판정한 파일)를 **실패도 성공도 없이 무시**했다.

- `grid.py:58 load_combined_grid` 신설 — 한 파일이 `lat`·`lon` 을 다 담는 격자를 읽는다
- `grid.py:105` — `.npy` 쌍이 없으면 컨테이너(`.nc`/`.h5`)를 본다. **못 읽으면 경성 실패**다(무시 아님)
- RED 확인: `GridUnavailableError: 위도/경도 npy 쌍을 찾지 못했다 (lat 0 · lon 0)` → 정정 후 green
- 실물 확인: `test_real_combined_nc_grid_actually_drives_the_pipeline` — `rdr_500m_latlon.nc` **단독**으로
  HSR 실파일이 감지→파싱→좌표→COG 를 완주하고 산출물이 생긴다(격자 `(2881, 2305)`)
- `.npy` 쌍이 함께 있으면 **`.npy` 가 이긴다**(기존 동작 보존). ⚠ 이것은 **기존 동작 유지**이지
  `〈66〉`(정본 격자는 `.nc`)의 이행이 아니다 — `§6-4` 참조

---

## 5. 하지 않은 것 (요구받지 않았거나, 내 권한 밖이거나, 정본 근거가 없어서)

| # | 하지 않은 것 | 왜 |
|---|---|---|
| 1 | **커밋** | 메인 세션 몫(`P2-EXEC §7`) |
| 2 | **`Dockerfile` 갱신** — 워커 진입점(`app/worker.py`)이 **이미지에 배선되지 않았다.** 현재 CMD 는 여전히 `app.health` 이고 이미지에 런타임 의존이 0이다 | 배포 스크립트가 **워킹트리를 굽는다**(`DR-4`). 이미지를 바꾸면 staging 배포 모양이 바뀌는데 **staging 은 8 컨테이너가 실서비스 중**이다. 배포 배선은 W5(메인)의 판단 자리 |
| 3 | **실제 큐·브로커 연결** | `[정본 무근거]` — 전송 수단을 정본도 계약도 정하지 않았다. 릴레이의 기본 발행자는 표준출력 한 줄이고 `publish` 를 갈아 끼우게 뒀다 |
| 4 | **`upload.accepted` 발행** | core-api 소관(`〈63〉-㉱`). 워커가 만들려 하면 거부한다 |
| 5 | **격자 파일 행의 접수 시점 삽입** | `§6-1` 참조 — 이건 **cross-lane 미결**이라 이 레인이 정할 수 없다 |
| 6 | **50 GB 스트리밍 규모 실측** | 이번에 다룬 최대 실파일은 HSR 13.28 MB 급·HLS 3660² 다. `P2-EXEC §8-6` 위험 그대로 |
| 7 | **`d5/` 파서 9모듈 개정** | 금지 사항. 한 줄도 고치지 않았다 — `grid.py` 는 **결손으로 명시 배정된 자리**라 추가만 했다 |
| 8 | **DLQ 재처리 경로** | `dead_lettered` 열은 읽어 봉투에 싣지만, **상한 초과분을 DLQ 로 옮기는 고리는 만들지 않았다.** 전송 수단이 없기 때문이다(3번과 같은 뿌리) |

---

## 6. 새로 드러난 것 · 막힌 것 (W3·메인 세션이 볼 자리)

### 6-1. ⚠ **격자 파일 행은 접수 시점에 만들 수 없다** (cross-lane · 판정 필요)

`d5_upload_file` 의 CHECK `d5_upload_file_grid_carries_an_axis` 는 「기준 격자 파일이면 축 하나 이상
true」를 요구한다(`schema.sql:480-481`). 그런데 **축은 워커가 파일을 열어야 안다**(`〈63〉-㉰`).
→ `createUpload` 가 접수 시점에 격자 파일 행을 넣으려 하면 **DB 가 트랜잭션을 죽인다.**

**실측** — `services/core-api/src/colab_core/ports/ingestion.py:68` 의
`accept(..., files: list[UploadFileRecord])` 는 `carries_lat`·`carries_lon` 을 **접수 시점에 받는다**
(`:36-37`). 값의 출처가 계약에 없다(`FileRef`·`UploadFileRef` 4값).

이 레인은 **워커 쪽 해법만** 세워 뒀다 — `SqlLedger.record_file_axes_row`(`d5_ingestion.py:357`)가
축이 정해진 뒤에 행을 **세운다**(있으면 갱신). **어느 쪽이 정본인지는 P2-api·메인이 정할 일**이다.

### 6-2. `d5_upload.processing` 열이 **없다**

`ports/ingestion.py:58` 의 `UploadRecord.processing` 이 원장에 대응 열이 없다 —
`grep -n processing db/platform/schema.sql` · `… 0004_p2_grid_axis_and_d5.py` **둘 다 0건**.
파생으로 계산할 수도 있으니 결손이라 단정하지 않는다. **P2-api 레인 소관으로 넘긴다.**

### 6-3. `[정본 무근거]` 목록 (지어내지 않고 비운 것)

| 값 | 상태 |
|---|---|
| **업로드 TTL(수명)** | 정본·계약 모두 값을 안 준다(`NB-2`). 워커는 **원장에 적힌 값을 읽어** `upload.ready.expiresAt` 에 실을 뿐, 기본값을 만들지 않는다 |
| **이벤트 전송 수단(큐·브로커)** | 정본 무근거. 릴레이는 `publish` 를 주입받는다 |
| **`targetCrs` 값** | 계약이 「상수로 박지 않는다」고 명시. 발행자 값으로 `"WGS84"` 를 썼다(`d5_ingestion.py:38`) — **레포 결정이지 정본 값이 아니다** |
| **`renderable` 목록** | 정본 §11 미결(`NB-3`). 오늘은 지원 4종과 같게 뒀다 |
| **실패 사유 ↔ 단계 대응표** | `envelope.json#FailureReason` 8값은 정본이 주지만 **어느 단계가 어느 사유를 내는지는 정본에 표가 없다.** `_FAILURE_MAP`(`d5_ingestion.py:45`)은 **레포 판단**이다. 특히 **`좌표계 변환 실패`를 `재시도 가능`으로 둔 것**은 「후주입으로 격자를 붙이면 풀린다」(`〈58〉`)에 기댄 해석이다 |

### 6-4. `〈66〉` 의 「HSR 정본 격자는 `.nc`」를 **코드가 아직 이행하지 않았다**

`find_reference_grid` 는 `.npy` 쌍이 있으면 그쪽을 쓴다(기존 동작 보존). 원천 `3_bin` 폴더에는
**둘 다 있고 값이 0.004~0.007° 어긋난다**(`DATA-REFERENCE §1`). 우선순위를 뒤집는 것은
**측정 결과의 이행**이지 결손 정정이 아니라서, **판정 없이 바꾸지 않았다.** 메인 판단 요청.

### 6-5. 관측된 환경 사실

- `planning-freshness` **red** — 「정본 폴더가 없다」. 워크트리에서 정본 마운트가 안 잡히는
  경로 문제이고 **이 레인의 변경과 무관**하다(착수 전부터 같은 상태). 감추지 않고 적는다.
- 이 워크트리는 **세 레인이 함께 쓴다.** `banned-import` 가 세는 `viz-render` 파일 수가
  착수 시점 7건 → 종료 시점 23건으로 늘었다 — `P2-viz` 레인의 산출이다. `§7` 게이트 결과는
  **그 상태의 트리**에서 낸 것이다.

---

## 7. 게이트 (EVIDENCE · 출력 그대로)

```
contract-lint green — seam 3건, 룰 위반 0.
contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.
event-lint green — 스키마 2건 컴파일 · valid 5건 통과 · invalid 8건 거부.
event-breaking green — 기준 HEAD (2건) 대비 파괴적 변경 없음.
import-boundary green — 계약 전부 통과.
banned-import green — .py 82건, 금지 import 0.
  pipeline-worker  .py   24건 · deny 0개
  viz-render       .py   23건 · deny 0개
ai-no-lineage-write green — 계약·코드·체인 세 층 모두에서 쓰기 경로가 없다.
seam-consistency green — G-e 258건 · G-b 7건 · ㉠ 0건 · ㉡ 15건.
migration-single-head green — 두 체인 모두 head 1개.
rls-coverage green — allow-list 밖 테이블 전부 FORCE RLS + 연구실 경계 정책, 본체 테이블은 본체 정책까지.
::error::planning-freshness red — 1건
  - 정본 폴더가 없다 (위치 확인 — planning/README.md §1)
```

**`selftest` 전부 green**:

```
contract-selftest green — 두 게이트 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).
event-selftest green — event-lint · event-breaking 이 틀린 것을 틀렸다고 말한다 (fail-closed 증명).
boundary-selftest green — 경계 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).
db-selftest green — DB 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명).
rls-effect-selftest green — 보호 장치를 하나씩 떼면 실제로 red 가 난다. 틀린 롤도 red 다.
seam-consistency-selftest green — 13 케이스 전부 기대대로 (green 4 · red 9).
generated-selftest green — 9 케이스 전부 기대대로 (green 1 · red 8).
```

**시험 전건 (단위 + 실데이터 E2E + 실 DB)**

```
$ COLAB_REFERENCE_DATA=<원천> COLAB_PIPELINE_DB_URL=<일회용 DB> pytest tests/ -q
82 passed, 11 warnings in 34.67s
```

착수 기준선 32건 → **82건**(+50 · 아래 분포의 합이 82 다). `pytest --collect-only -q` 실측 분포:

```
11 tests/test_axis_detect.py            5 tests/test_axis_detect_real.py     (신규)
 7 tests/test_events.py                 8 tests/test_worker_events.py        (신규)
 5 tests/test_renderable.py             5 tests/test_tiff_classes_pipeline_real.py (신규)
 3 tests/test_grid_combined_nc.py       6 tests/test_outbox_db.py            (신규)
 4 tests/test_cog_classify.py    8 tests/test_detect.py   6 tests/test_e2e_real.py
 8 tests/test_grid_and_hsr.py    6 tests/test_pipeline.py                    (기존 32건)
```

---

## 8. 만든 것 (파일 목록)

**새 파일**

| 파일 | 무엇 |
|---|---|
| `src/colab_pipeline/d5/events.py` | 봉투·멱등 키·7종 페이로드 빌더 · `WorkerCannotEmitError` |
| `src/colab_pipeline/d5/axis.py` | 축 판별(`〈65〉`·`〈66〉`) — 단독/업로드 단위 |
| `src/colab_pipeline/d5/renderable.py` | `renderable` 판정 |
| `src/colab_pipeline/ports/outbox.py` | `EventLedgerPort` · `UploadLedgerPort` Protocol |
| `src/colab_pipeline/kernel/db.py` · `kernel/ids.py` | 엔진·세션·트랜잭션 스코프 GUC · ULID |
| `src/colab_pipeline/app/worker.py` | 릴레이 + reaper 진입점 |
| `tests/` 8종 + `tests/memory_ledger.py` | 아래 시험 |

**고친 파일** — `domains/d5_ingestion.py`(1줄 스텁 → 워커·`SqlLedger`·릴레이·reaper) ·
`d5/grid.py`(결합축 `.nc` 추가) · `README.md` · `requirements*.in/txt` · `pyproject.toml`(마커 `dbint`) ·
`tests/conftest.py`(계약 검증 픽스처) · `tests/fixture_builders.py`(진짜로 읽히는 GeoTIFF 빌더).

**`d5/` 기존 판정 모듈은 한 줄도 고치지 않았다** — `detect.py` · `parse.py` · `hsr.py` · `cog.py` ·
`tiff_probe.py` · `formats.py` · `lineage.py` · `pipeline.py` 전부 무변경.

---

## 9. 재현

```bash
cd services/pipeline-worker
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.in
.venv/bin/python -m pytest tests/ -m "not e2e and not dbint" -q        # 단위
COLAB_REFERENCE_DATA=<원천 마운트> .venv/bin/python -m pytest tests/ -m "not dbint" -q

# 실 DB — 일회용 컨테이너(호스트 포트 publish 없음). staging 은 건드리지 않는다.
docker run -d --rm --name p2pipe_pg --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=gate -e POSTGRES_HOST_AUTH_METHOD=trust postgres:16-alpine
#   createdb → colab_owner 로 db/platform/schema.sql → app-role.sql → seed.sql
COLAB_PIPELINE_DB_URL=postgresql+psycopg://colab_app:gateapp@<컨테이너 IP>:5432/p2pipe \
  .venv/bin/python -m pytest tests/test_outbox_db.py -q
docker rm -f p2pipe_pg
```
