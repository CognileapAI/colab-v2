# CODE-REVIEW-20260903-D — 레인 D `pipeline-worker` (+ ai-service 1행) 집행 기록

> 근거 — `dev-package/sessions/CODE-REVIEW-20260903.md`(#4 · #13 · 부록) · 계획 `CODE-REVIEW-20260903-PLAN.md` §2 D 행.
> 기준 — `lane-review-clean` `d4d11b5`. 브랜치 `worktree-agent-a160bc4c840f9061d`. **push 없음 · main 병합 없음 · 대장 번호 발급 없음.**
> 경로 표기 — 레포 루트 기준. 위치는 **앵커 문자열**로 적는다(행 번호는 밀린다).

## 1. 계수 — 전/후

| 무엇 | 기준선(변경 전) | 이번 회차(변경 후) | 어떻게 쟀나 |
|---|---|---|---|
| pipeline-worker `-m "not e2e and not dbint"` | 200 passed · 41 deselected · 0 failed | **225 passed · 46 deselected · 0 failed** | `.venv/bin/python -m pytest -q -p no:cacheprovider` |
| pipeline-worker `-m dbint` | 15 passed(신규 파일 제외 · base src) | **20 passed** | 일회용 postgres(아래 §5) |
| 게이트 `stage2-markers` | 수집 69 · skip 0 · fail 0 · err 0 · rc=0 | **수집 80 · skip 0 · fail 0 · err 0 · rc=0** | `./gates/run.sh stage2-markers` |
| ai-service DB 없는 부분집합(6파일 제외) | 88 passed | **94 passed** | 6파일 `--ignore` |
| ai-service 전체(사전 DB 붙임) | 145 passed(신규 파일 제외 · base src) | **151 passed** | 일회용 postgres `db/ai` 체인 |

- 기존 실패 **0건**. 이 레인이 고치지 않고 넘긴 red 없음.
- `dbint`·ai-service 전체의 기준선은 **변경 뒤에 base 소스를 되돌려 다시 잰 값**이다(`git checkout d4d11b5 -- <src>` → 측정 → `git checkout HEAD -- <src>`, 되돌린 뒤 dirty 0 확인). 시점이 다르므로 함께 적는다.
- `./gates/run.sh all` 은 **돌리지 않았다**(레인 금지). 다른 게이트도 이 레인 소관 밖.

## 2. 항목별 — 변경 · 시험 · 전후

### ⑴ `services/pipeline-worker/src/colab_pipeline/d5/axis.py` (#4)

- **무엇이 있었나** — `_stats` 가 `a = np.asarray(arr[: _MAX_SAMPLE, : _MAX_SAMPLE], ...)` 를 `ndim` 검사보다 **먼저** 실행. 1차원 격자 `.npy` 가 `AxisUndeterminedError` 가 아니라 `IndexError` 로 탈출. `_read_npy` 의 `np.load(..., allow_pickle=False)` 실패(object dtype · 절단)도 같은 자리로 샜다.
- **무엇을 했나** — `d5/axis.py:_stats` 에서 `if getattr(arr, "ndim", None) != 2:` 를 **창보다 앞에** 둔다. `d5/axis.py:_read_npy`·`d5/axis.py:_read_container` 를 `try/except` 로 감싸 적재 실패를 `AxisUndeterminedError` 로 바꾼다(`AxisUndeterminedError` 는 그대로 통과시킨다).
- **시험** — `services/pipeline-worker/tests/test_axis_data_errors.py`(신규 4건). 픽스처 = shape `(2881,)` `.npy` · 절단 `.npy` · object dtype `.npy` · 「1차원 + 정상」 혼합 업로드.
- **전/후** — 전: 4건 전부 `IndexError`/`ValueError` 로 실패. 후: 4건 pass. 기존 `test_axis_detect.py` 14건 회귀 없음.

### ⑵ `services/pipeline-worker/src/colab_pipeline/app/worker.py` · `domains/d5_ingestion.py` (#4 크래시 루프)

- **무엇이 있었나** — `drive_uploads` 의 산문이 「예외가 나는 것은 배관이 깨진 경우뿐」이라 적었으나 코드가 지키지 않았다. D5 데이터 오류가 `_lab_pass` 의 `except BaseException: session.rollback(); raise` 로 올라가 ⓐ 같은 틱의 다른 업로드·릴레이·reaper 까지 롤백 ⓑ `serve()` 무보호 → 프로세스 종료 ⓒ `ready=false` 가 남아 `pending_uploads`(ORDER BY created_at)가 같은 건을 다시 먼저 집음 → 크래시 루프.
- **무엇을 했나**
  - `domains/d5_ingestion.py:DATA_ERRORS` 신설 — `AxisUndeterminedError` · `GridUnavailableError` · `HsrParseError` · `ParseError` · `CogConversionError` · `ValueError` · `IndexError`. **여기 없는 것이 규칙의 절반이다** — `OSError`·SQLAlchemy 예외·`BaseException` 은 그대로 던진다.
  - `domains/d5_ingestion.py:IngestionService.record_data_failure` 신설 — `_fail(stage="upload.failed", reason="내부 오류", klass="영구", detail=f"{type(exc).__name__}: {exc}")`.
  - `app/worker.py:drive_uploads` 의 `service.process_upload(...)` 를 `try/except DATA_ERRORS` 로 감싸 위 메서드를 부르고 **다음 건으로 간다**. 롤백 없음 → 같은 트랜잭션의 `relay_unpublished` 가 같은 바퀴에 발행하고 `_lab_pass` 가 commit 한다. `failed_at` 이 서므로 `pending_uploads` 가 다시 집지 않는다.
- **어휘를 새로 만들지 않았다** — `내부 오류`·`영구` 는 `_classify_failure` 의 기존 폴백과 같은 값이고 둘 다 계약 enum 안이다. 격자·좌표 실패를 `좌표계 변환 실패`·`재시도 가능` 으로 **세분하지 않았다**: 정상 경로(`run_file` → `_classify_failure`)가 이미 그 분류를 하고, 여기까지 온 것은 예상 밖 갈래라 재시도를 약속할 근거가 없다.
- **`serve()` 보호는 붙이지 않았다 — 문서화한 계약과 어긋난다.** `app/worker.py:main` 의 산문이 「**루프가 죽으면 프로세스가 죽는다**(restart 정책이 집는다). 조용히 멈춘 워커가 「healthy」로 보이는 상태를 만들지 않는다」로 못 박았다. 로그를 남기고 물러서는 보호를 붙이면 루프는 죽고 프로세스는 살며, 헬스 서버는 **데몬 스레드**라 계속 200 을 낸다 — 금지한 상태 그 자체다. 붙이려면 헬스가 「루프가 죽었다」를 말할 수 있어야 하고 그것은 `app/health.py` 를 함께 고치는 일이라 **이 회차 밖**으로 둔다. 사유는 `app/worker.py:serve` docstring 에 적어 뒀다.
- **시험**
  - `tests/test_worker_data_error_isolation.py`(신규 5건) — 실물 `IngestionService` 를 상속한 `_RaisingService` 로 데이터 오류를 주입한다. 원장 대역은 `_DriveLedger`(= `MemoryLedger` + `pending_uploads`/`accepted_files`, `failed_at IS NULL` 조건을 실물과 같이 지킨다). 단언: `upload.failed` 원장 기록 · 같은 틱의 다른 업로드 처리 계속 · 두 번째 바퀴 재선택 0 · 같은 바퀴 발행 · `OSError` 는 여전히 raise.
  - `tests/test_worker_data_error_dbint.py`(신규 5건 · `dbint`) — 대역이 흉내낼 수 없는 둘을 실물 원장에서 본다: `failed_at` 이 `SqlLedger.pending_uploads` SQL 조건에 실제로 걸리는가 · `attempt = attempt + 1` 이 `CHECK (attempt >= 1)` 아래 서고 다음 봉투가 `redelivery: true` 로 나오는가. 봉투는 `event_validator`(계약 파일이 오라클)로 검증.
- **전/후** — 전: 단위 3건 실패(예외가 그대로 올라옴). 후: 단위 5 · dbint 5 pass.
- **리뷰 지시와 갈린 한 줄** — 지시문은 「1-D grid upload yields `upload.failed`」였으나, ⑴ 을 고친 뒤 1차원 `.npy` 는 **`upload.failed` 가 아니라 「그 격자만 거절」**이다(`〈63〉-ⓒ` 등록은 막지 않는다). 그 사실을 `test_worker_data_error_isolation.py::test_1차원_격자_업로드가_틱을_죽이지_않는다` 가 그대로 못 박았다(업로드 `ready` · `gridResolution` 에 `rejectionReason: 짝 불일치` · 축 빈 행 0). 「데이터 오류 → `upload.failed`」는 **주입한 예상 밖 갈래**로 시험한다.

### ⑶ `services/pipeline-worker/src/colab_pipeline/d5/parse.py` (#13 NetCDF 차원)

- **무엇이 있었나** — `_parse_netcdf` 의 `spatial = [n for n in dims if n.lower() in (...)]` → `meta.grid = (dims[spatial[0]], dims[spatial[1]])` 가 **`ds.dimensions` 선언 순서**를 따랐다. 경도 차원을 먼저 선언한 파일은 `(nx, ny)` 로 전치된다.
- **소비처 둘** — ① `d5/pipeline.py:run_file` 이 `expect_shape` 로 `d5/grid.py:find_reference_grid` 에 넘긴다 → 전치되면 **맞는 격자가 있어도** 「형상 불일치」 → 「좌표/격자 없음」. ② `domains/d5_ingestion.py` 의 `grid_text = f"{meta.grid[0]}x{meta.grid[1]}"` 가 사람에게 그대로 보인다.
- **무엇을 했나** — `d5/parse.py` 에 `_LAT_DIM_NAMES`·`_LON_DIM_NAMES` 를 두고(두 목록의 합집합 = 종전 `spatial` 목록 · **값 집합을 넓히지 않았다**) `meta.grid = (dims[lat_dim], dims[lon_dim])`. 두 역할이 다 서지 않으면 종전대로 변수 형상 `(shp[-2], shp[-1])` 로 떨어진다.
- **시험** — `tests/test_parse_netcdf_grid_axes.py`(신규 3건 · `stage2`). 픽스처 = `createDimension("lon")` 을 먼저 부른 4×5 NetCDF. 위도 선행 파일 회귀 시험 포함.
- **전/후** — 전: 2건 실패(`(5, 4)` · `'5x4'`). 후: 3건 pass. 기존 NetCDF 시험(`test_grid_canonical_nc.py`·`test_grid_combined_nc.py`·`test_detect.py`) 회귀 없음 — 픽스처가 `y`·`x` 순으로 선언해 값이 같다.
- **하류 영향(실측)** — `file.header-parsed` 의 `grid` 문자열은 `services/core-api/src/colab_core/domains/d5_ingestion.py`(`grid = payload.get("grid")`)가 **되파싱 없이 그대로** 보관·표시한다. 순서를 가정하는 코드는 core-api 에 없다(grep). 그래서 이 변경은 **틀린 값이 맞는 값으로 바뀌는 것**이고 스키마·계약 변화가 없다.

### ⑷ `services/pipeline-worker/src/colab_pipeline/d5/cog.py` (#13 NaN 좌표)

- **무엇이 있었나** — `regrid_curvilinear_nearest` 의 `valid = np.isfinite(d)` 가 **값만** 봤다. 좌표 셀이 NaN 이면 `np.rint(nan)` → `np.clip` → `.astype("i8")` 가 `INT64_MIN` 을 내고 `out[rows[valid], cols[valid]]` 가 `IndexError` → 사용자에게는 「COG 변환 실패」 한 줄. 퇴화 검사도 `lat_min == lat_max` 하나뿐이라 `lon_min == lon_max` 격자가 `lon_step = 0` 으로 같은 자리에서 터졌다.
- **무엇을 했나** — 쌍둥이 `services/viz-render/src/colab_viz/domains/d7_visualization/raster.py:regrid_nearest` 의 **거절 기준에 맞춘다**: `np.isfinite([lat_min, lat_max, lon_min, lon_max]).all()` + `lat_min == lat_max or lon_min == lon_max` → `CogConversionError`; `valid = np.isfinite(d) & np.isfinite(la) & np.isfinite(lo)`.
- **시험** — `tests/test_cog_nan_coords.py`(신규 5건 · `stage2`). 픽스처 = 좌표 한 셀 NaN · 경도 전 셀 동일 · 위도 전 셀 동일 · 좌표 전건 NaN.
- **전/후** — 전: 3건 `IndexError`. 후: 5건 pass.

### ⑸ `services/pipeline-worker/src/colab_pipeline/d5/hsr.py` (#13 0 블록)

- **무엇이 있었나** — `parse_hsr` 이 0 블록을 정상 반환 → `d5/pipeline.py:_cog_binary` 의 `hsr.blocks[0]` 이 `IndexError`.
- **무엇을 했나** — `parse_hsr` 말미에 `if not blocks: raise HsrParseError("자료 블록이 하나도 없다")`. 쌍둥이 `services/viz-render/src/colab_viz/domains/d7_visualization/hsr.py` 와 같은 문구·같은 자리.
- **경계** — 「헤더 `num_data=3` · 실물 1블록」은 실측된 배포본 무늬라 **여전히 정상**이다(`block_count_mismatch`). 막는 것은 0 블록뿐이고 회귀 시험으로 못 박았다.
- **시험** — `tests/test_hsr_zero_blocks.py`(신규 3건 · `stage2`). 픽스처 = `make_hsr_bin_gz(blocks=[], declared_num_data=3)`(헤더만). `run_file` 을 태워 실패가 `파싱 실패…` 로 **분류표가 읽을 수 있는 문구**가 되는 것까지 본다.
- **전/후** — 전: 1건 `DID NOT RAISE`. 후: 3건 pass. 기존 `test_grid_and_hsr.py` 8건 회귀 없음.

### ⑹ `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:relay_unpublished` (부록)

- **무엇이 있었나** — 발행 실패에서 ⓐ 예외가 그대로 올라가 `_lab_pass` 가 **그 바퀴의 처리·reaper 까지 롤백** ⓑ `attempt` 가 오르지 않아 재전달이 영원히 `attempt: 1 · redelivery: false` 로 나갔다. `delivery` 블록이 존재하는 이유(「재시도 여부·상한 판단을 소비자가 각자 하지 않는다」)를 어긴다.
- **무엇을 했나** — `publish(env)` 를 `try/except` 로 감싸고 실패 시 `ledger.record_delivery_failure(env["eventId"])` 뒤 다음 봉투로 간다. `SqlLedger.record_delivery_failure` = `UPDATE d5_pipeline_event SET attempt = attempt + 1 WHERE id = :id AND published_at IS NULL`. `published_at` 은 건드리지 않는다(at-least-once). Port(`ports/outbox.py:EventLedgerPort`)와 시험 대역(`tests/memory_ledger.py`)에 같은 문을 더했다 — 대역이 실물보다 헐거우면 시험이 거짓말을 한다.
- **시험** — `tests/test_relay_redelivery.py`(신규 5건) + `tests/test_worker_data_error_dbint.py` 의 2건(실물 SQL).
- **전/후** — 전: 단위 4건 실패(예외 전파). 후: 단위 5 · dbint 2 pass.
- **DLQ 는 유보** — 아래 §3 참조.

### ⑺ `services/ai-service/src/colab_ai/app/main.py` (#10 형제) — **별도 커밋**

- **무엇이 있었나** — `@app.post("/searches") async def search_datasets` 가 코루틴인 채로 막는 일을 한다: `app/dictionaries.py` 의 사전 조회는 동기 psycopg 5 SELECT, `llm` 모드는 `app/interpret.py` 의 `urlopen(timeout=8)`. 이벤트 루프가 멈추고 uvicorn 워커가 하나라 같은 프로세스의 `/healthz` 까지 답을 못 한다(compose 헬스 체크 3초).
- **무엇을 했나** — `def search_datasets(request: Request, body: bytes = Depends(_raw_body))`. `_raw_body` 는 `await request.body()` 만 하는 **비동기 의존** — 읽기는 루프에서, 판단은 스레드풀에서.
- **왜 `Body(...)` 가 아닌가** — 본문을 body 파라미터로 선언하면 FastAPI 가 요청의 `content-type` 을 보고 **먼저 JSON 으로 해석**하고 실패를 `RequestValidationError`(422)로 낸다. 이 표면이 계약대로 내던 「본문이 JSON 이 아니다」 400(`contracts/schemas/common.json#ErrorEnvelope`)이 사라진다. 바이트만 받아 오면 해석은 라우트가 그대로 하고, body 파라미터가 없으므로 `def` 가 성립한다.
- **`/lineage-suggestions` 는 그대로** — 그 경로에는 막는 호출이 없다.
- **시험** — `services/ai-service/tests/test_search_route_threadpool.py`(신규 6건 · **DB 없이 돈다**). 라우트가 코루틴이 아닌 것 · DB 없이 200 + 검색어 · 깨진 JSON 400 · 배열 본문 400 · 빈 본문 400 · 경계 검사 400/401 유지.
- **전/후** — 전: 1건 실패(코루틴). 후: 6건 pass. DB 없는 부분집합 88 → 94. **사전 DB 를 붙인 전체 151/0** 으로 `tests/test_http_search.py`(다른 레인 소유 · 편집하지 않음)까지 함께 확인했다.

## 3. 계약 델타 — **없음**. 다만 「계약이 적었는데 배선이 없는 것」 둘을 적어 둔다.

- **새로 만든 필드·enum·사유값 0건.** `upload.failed` 는 `contracts/events/envelope.json#/$defs/FailureReason` 의 `내부 오류` 와 `FailureClass` 의 `영구` 를 쓴다. `delivery.attempt`·`redelivery` 는 `#/$defs/Delivery` 에 이미 required 로 서 있다.
- **⚠ DLQ 배선 0** — `Delivery.maxAttempts` 산문은 「이 값을 넘어서면 재시도하지 않고 DLQ 로 보낸다」이고 `deadLettered` 열도 있는데, 보내는 경로가 레포에 없다. 이번 변경으로 `attempt` 가 **상한을 넘어서도 계속 오르고 재시도도 계속된다.** 숫자는 이제 사실이지만 상한의 뜻은 아직 배선이 아니다. (유보 — 계획 §4 작업항목 초안 #11)
- **⚠ `Failure.willRetry` 의 상한 조건 미구현** — 계약 산문은 「`재시도 가능` 이어도 `delivery.attempt` 가 상한에 닿았으면 false」인데 `IngestionService._fail` 은 `will_retry=(klass == "재시도 가능")` 만 본다. DLQ 와 한 묶음이라 함께 유보한다.

## 4. D5/D7 쌍둥이 — **관측했으나 통일하지 않았다** (계획 §4 작업항목 초안 #1·#9 재료)

이번 회차에서 맞춘 것은 **거절 기준**뿐이고, 두 벌로 적힌 사실 자체는 그대로다.

| 자리 | D5 (`services/pipeline-worker/src/colab_pipeline/d5/…`) | D7 (`services/viz-render/src/colab_viz/domains/d7_visualization/…`) | 이번 회차 |
|---|---|---|---|
| 기준 격자 탐색 | `grid.py` — 파일명 접두 `lat*`/`lon*`, 값 검사 없음 | `grid.py` — stem 짝 + `LAT_LIMIT=90` 수치 판정 · 거절 사유 3종 | **손대지 않았다.** 등록 수용 기준이 바뀌므로 상품 판정이 먼저다(#9) |
| 최근접 재배치 | `cog.py:regrid_curvilinear_nearest` → `CogConversionError` | `raster.py:regrid_nearest` → `RenderError(RenderFailure.UNKNOWN)` | **거절 기준만 맞췄다.** 예외형이 다르고, D7 에만 있는 `values.shape != lat.shape` 검사는 D5 에 없다 |
| HSR 판독 | `hsr.py` — `HsrResult(blocks_present=…)` | `hsr.py` — `HsrResult` 에 `blocks_present` 없음 | **0 블록 거절만 맞췄다.** 결과 자료구조가 여전히 다르다 |
| NetCDF 차원 해석 | `parse.py` — `_LAT_DIM_NAMES`/`_LON_DIM_NAMES`(이번에 신설) | `readers.py:_read_netcdf` — `while raw.ndim > 2: raw = raw[0]`(축 역할을 안 본다 · `instant` 미사용은 레인 C 소관) | **D5 만 고쳤다.** 좌표 변수명 목록이 두 서비스에 각자 있다 — codegen 후보가 하나 늘었다 |

## 5. 일회용 데이터베이스 — 어떻게 썼나

- 컨테이너 이름 `colab_v2_dbint_<pid>_<rand>` — `colab_v2_staging_` 접두와 겹치지 않는다. `--rm` · `--tmpfs /pgdata` · `-e PGDATA=/pgdata/db` · **호스트 포트 미공개**(컨테이너 IP 로만 붙는다). 패턴은 `gates/tools/_pg.sh` 와 같다.
- 적용 = `services/core-api/tests/fixtures/setup-db.sh`(`db/platform` 체인 · DB `colab_platform`) + `services/ai-service/tests/fixtures/setup-db.sh`(`db/ai` 체인 · DB `colab_ai`). **두 스크립트 모두 편집하지 않았다.**
- 운영 `colab_v2_staging_*` 는 조회조차 하지 않았다. 접속 문자열·비밀번호는 어디에도 남기지 않았다.
- 측정이 끝난 뒤 **제거를 실측 확인**했다 — 이름 접두 검사 후 `docker rm -f`, 남은 `colab_v2_dbint_*` 0개.

## 6. `[미확인]`

| 무엇 | 왜 못 쟀나 | 무엇을 하면 풀리나 |
|---|---|---|
| `-m e2e` 시험 41→46건 중 e2e 갈래 | 원천 데이터 마운트(`COLAB_REFERENCE_DATA`)가 이 워크트리에 없다 | 원천을 마운트하고 `.venv/bin/python -m pytest -q -m e2e` |
| viz-render·core-api·frontend 스위트에 미치는 영향 | 편집 면 밖이라 이 레인에서 돌리지 않았다 | 병합 트리에서 4서비스 스위트 재실행(계획 §3-3) |
| `serve()` 보호를 붙였을 때의 헬스 표현 | `app/health.py` 를 고치는 일이라 회차 밖으로 뒀다 | 「루프가 죽었다」를 헬스가 말하게 한 뒤 보호를 붙이고, 죽은 루프에서 헬스가 200 이 아닌 것을 시험으로 못 박는다 |
| `attempt` 가 `max_attempts` 를 넘긴 뒤의 소비자 동작 | DLQ 배선이 없어 관측 대상이 없다 | DLQ 경로를 세운 뒤 상한 초과 봉투의 `willRetry`·`deadLettered` 를 시험으로 고정 |
| `./gates/run.sh all` | 레인 금지 | 오케스트레이터가 병합 트리에서 `-j 1` 로 실행(계획 §3-3) |

## 7. 이번에 세지 않은 판단기준 (다음 회차 진입조건)

- D5/D7 쌍둥이 4쌍의 **동작 동치성** — 같은 입력에 같은 판정을 내는가. 이번에는 거절 기준 3자리만 맞췄고 동치성은 재지 않았다.
- 데이터 오류로 `upload.failed` 가 된 업로드의 **화면 표현** — `내부 오류`·`영구` 가 사용자에게 어떤 문구로 보이는지(정본 `Policy §9`)는 frontend 소관이라 이 레인에서 확인하지 않았다.

## 8. 대장 등재문 초안 — **번호 없음** (발급은 오케스트레이터)

> **pipeline-worker 데이터 오류의 크래시 루프 제거 · D5/D7 거절 기준 3자리 정렬 · 재전달 계수 정직화 · ai-service 검색 라우트 스레드풀 이동.**
> 근거 = `dev-package/sessions/CODE-REVIEW-20260903.md` #4 · #13 · 부록, 집행 기록 = `dev-package/sessions/CODE-REVIEW-20260903-D.md`.
> ⑴ `d5/axis.py` 가 `ndim` 을 창보다 먼저 보고 `.npy` 적재 실패를 판별 실패로 감싼다 — 1차원 격자가 `IndexError` 로 탈출하던 자리.
> ⑵ `app/worker.py:drive_uploads` 가 D5 데이터 오류를 `upload.failed`(기존 어휘 `내부 오류`·`영구`)로 분류하고 틱을 계속 돈다. 틱 전체 롤백·프로세스 종료·같은 건 재선택이 사라진다. DB·IO 는 그대로 던진다. `serve()` 보호는 **붙이지 않았다** — `main()` 이 문장으로 금지한 「멈춘 워커가 healthy 로 보이는 상태」가 되기 때문이며, 헬스 표현과 함께 고칠 일로 유보했다.
> ⑶ `d5/parse.py` 가 NetCDF 격자를 차원 선언 순서가 아니라 축 역할로 읽는다 — 경도 선행 파일에서 격자 대조와 사용자 표시가 함께 전치되던 자리.
> ⑷ `d5/cog.py` 가 비유한 좌표를 마스킹하고 경도 퇴화 범위를 거절한다(D7 `raster.py` 와 같은 기준). ⑸ `d5/hsr.py` 가 0 블록을 `HsrParseError` 로 거절한다(D7 쌍둥이와 같은 자리).
> ⑹ 발행 실패에서 `attempt` 를 올려 재전달이 `redelivery: true` 로 나간다. **DLQ 는 유보** — 상한을 넘겨도 멈추지 않는다.
> ⑺ ai-service `POST /searches` 를 `def` 로 바꿔 동기 사전·LLM 호출을 스레드풀로 옮긴다. 본문 읽기만 비동기 의존으로 남겨 400 오류 봉투를 보존했다.
> **계약 변경 0.** 계수 — pipeline-worker `not e2e and not dbint` 200→225 · `dbint` 15→20 · `stage2-markers` 69→80(skip/fail/err 0) · ai-service DB 없는 부분집합 88→94 · 사전 DB 붙인 전체 145→151.

## 9. 커밋

| sha | 제목 |
|---|---|
| `dafffcf` | pipeline-worker 데이터 오류를 크래시 루프에서 떼어낸다 — 축·격자·HSR·NetCDF·재전달 |
| `31d349d` | ai-service 검색 라우트를 스레드풀로 옮긴다 — `async def` → `def` |
