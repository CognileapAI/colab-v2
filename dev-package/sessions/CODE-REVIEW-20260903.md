# CODE-REVIEW-20260903 — colab-v2 전수 코드리뷰 (클린아키텍처·클린코드 판단기준)

> 회차 목적 — 에이전트 개발 최적화. 다른 세션이 main 에 병행 커밋 중이므로 이 회차는 `lane-review-clean` 브랜치에서만 작업하고 main 병합·대장 번호 발급은 하지 않는다.
> 기준 커밋 — main `d9e89a3`(2026-09-03, 〈300〉 등재 직후). 리뷰 실행 — `/code-review` xhigh(찾기 12갈래 + 스윕 → 후보 100 → 중복 제거 72 → 검증 1표 → CONFIRMED 69 · PLAUSIBLE 4 · REFUTED 1). 파일 수정 0.
> 경로 표기 — 레포 루트 기준 상대 경로. 행 번호는 기준 커밋 시점 값이며 편집 중 밀릴 수 있다 — 앵커 문자열로 찾는다.
> 개선 계획·실행 기록 — `CODE-REVIEW-20260903-PLAN.md`(같은 폴더).

## 검토 결과 — colab-v2 (읽기 전용 · 파일 수정 0)

**근본 원인 4갈래에 15건이 걸린다**
- 경계·검증이 엉뚱한 서비스에 있다 — 1(viz 가 경계 헤더를 안 읽음), 12(계약 생성 모델 0 → 손검사 47곳), 15(비밀값 `_FILE` 미적용)
- 커널·규칙이 손사본이다 — 13(D5/D7 쌍둥이 모듈 3쌍 + NetCDF 해석), 부록의 `ids.py` ×4 등 (codegen 은 `storage_layout.py` 3벌에만 걸려 있다)
- 검사기가 판정하지 않는다(green-by-skip) — 6(서비스 pytest 1102 중 871 미실행 · frontend 전용 PR 게이트 0 · tolerate=true)
- 화면이 「정직한 빈 상태」를 어긴다 — 9(픽스처 폴백), 14(페이징 반쪽), 8(415→503)

```json
[
  {
    "file": "services/viz-render/src/colab_viz/app/routes/renders.py",
    "line": 123,
    "summary": "viz-render 가 렌더 조회·스크린샷에서 `renderId` 만으로 `jobs.get()` 하고 core-api 가 실어 보내는 `X-CoLAB-Lab`/`X-CoLAB-Account` 를 어디서도 읽지 않아, core-api `preview.py:174-186` 이 「유일한 정직한 경계 확인」으로 삼는 응답이 경계를 전혀 검사하지 않는다 — 타 연구실 renderId 로 지도·타일 서명·스크린샷을 받는다.",
    "failure_scenario": "연구실 B 사용자가 연구실 A 의 renderId 로 `GET /previews/{renderId}` 또는 `POST /preview-screenshots` → viz `renders.py:123 job = request.app.state.jobs.get(renderId)` / `screenshots.py:66 store.get(layer.renderId)` 가 200 으로 A 의 job(서명된 tileUrlTemplate·imageUrl·legend·bounds) 반환 또는 A 의 래스터를 PNG 로 합성. `grep -rn 'X-CoLAB' services/viz-render/src` = 0건, `RenderJob`/`JobStore` 에 lab 필드 없음, viz 의 유일한 인증은 연구실 공통 서비스 토큰. 고칠 자리는 viz-render(헤더를 읽어 job 에 lab 을 박고 대조) — core-api 는 의도적으로 위임하고 있다."
  },
  {
    "file": "services/viz-render/src/colab_viz/domains/d7_visualization/jobs.py",
    "line": 649,
    "summary": "`regenerate` 가 `submit()` 직후 `plan = job.invalidation` 을 읽는데 기본 `execution=\"thread\"` 에서는 `_run_and_plan`(565-568) 이 렌더가 끝난 뒤에야 그 필드를 채우므로 운영에서는 항상 None — 낡은 미리보기 삭제 `invalidation.apply` 가 한 번도 실행되지 않고 트리거는 ack 된다(레이스가 아니라 상시).",
    "failure_scenario": "D5 가 `preview.grid-changed` 발행 → `triggers.drain` → `JobStore.regenerate` → `submit` 이 `threading.Thread(target=self._run_and_plan).start()`(561-562) 후 즉시 반환 → 649 `plan = job.invalidation` None → 650 `removed = ()` → `triggers.py:31 port.ack(event)`. `invalidation.apply` 호출처는 레포에 이 한 곳뿐, 기본값 `config.py:124 COLAB_VIZ_EXECUTION=\"thread\"`. 결과: 격자 교체 뒤 구 PNG/WEBP/PGW/JSON 영구 잔류, 오류 없음. 같은 경로의 형제 — `triggers.py:24 list(port.poll())` 는 `payload.trigger` 가 어긋난 봉투 하나가 제너레이터 안(`trigger_bus.py:96-97`)에서 UnknownTrigger 를 던지면 그 틱의 전 봉투를 실행·ack 못 하고 매 틱 반복(격리·폐기 경로 0, 버전 스큐·수동 투입 시); `trigger_bus.py:93-94` 는 `_done` 키를 `_inflight` 등록 없이 continue 해 ack 불가 → 스풀 파일 영구 잔류·매 틱 재파싱."
  },
  {
    "file": "services/viz-render/src/colab_viz/domains/d7_visualization/readers.py",
    "line": 274,
    "summary": "`_read_netcdf(path, variable, instant, max_side)` 가 `instant` 를 받기만 하고 본문에서 한 번도 쓰지 않은 채 `while raw.ndim > 2: raw = raw[0]` 로 항상 첫 시각을 그리고, `jobs.py:376-378` 캐시 키에도 `instant` 가 없어 잘못된 시각의 영상이 모든 시각에 대해 캐시·서빙된다.",
    "failure_scenario": "24시각 NetCDF 에 `POST /renders {\"instant\":\"2026-06-01T12:00:00Z\"}` → `grep -n instant readers.py` = 245·425·434(서명·전달만) → 274-275 에서 인덱스 0 → 계약 core-viz.yaml:423 「생략하면 첫 시각」과 달리 지정해도 첫 시각. `render_cache_key`(cache.py:41-52) 는 source/fills/palette/selection 만 접어 T1·T2 요청이 같은 키·같은 PNG. 형제: `jobs.py:296-303 _grid_digest` 가 lat shape·nanmin(lat)·nanmax(lon) 세 값만 해시 — 그 세 값이 모두 같은 다른 격자로 교체하면(전제 3개 동시 충족 시) 같은 키·같은 파일명이 되고 `invalidation` 의 keep_keys 가 구 산출물을 「신선」으로 보존."
  },
  {
    "file": "services/pipeline-worker/src/colab_pipeline/d5/axis.py",
    "line": 90,
    "summary": "`arr[:_MAX_SAMPLE, :_MAX_SAMPLE]` 가 `ndim` 검사(91) 앞에서 실행돼 1차원 격자 `.npy` 가 `AxisUndeterminedError` 대신 IndexError 로 탈출하고, `worker.py:236 process_upload` 에 보호가 없어 `_lab_pass` rollback·raise → `serve()` 종료 → 재기동 후 같은 업로드를 다시 집는 크래시 루프로 전 연구실이 정체된다.",
    "failure_scenario": "업로드에 shape `(2881,)` 인 `Lat_*.npy`(또는 `np.load` 가 거부하는 object-dtype/절단 `.npy`, axis.py:102) 포함 → `detect_axes_for_upload` 239 가 `except AxisUndeterminedError` 만 잡음 → `d5_ingestion.py:355` → `worker.py:236` → `worker.py:304-306 except BaseException: session.rollback(); raise` → `run_once` 는 finally 만 → `serve()` 376-379 무보호 → 프로세스 종료. rollback 으로 `ready=false` 유지 → `pending_uploads`(ORDER BY created_at) 가 같은 건을 먼저 반환. 같은 틱의 다른 업로드·`relay_unpublished`·reaper 도 롤백. 레포 venv numpy 2.5.2 로 `np.arange(10)[:4096,:4096]` → IndexError 재현. 고칠 자리: axis.py 검사 순서 + `process_upload` 가 데이터 오류를 `upload.failed` 로 분류(worker.py:209-211 이 문서화한 계약 「예외는 배관이 깨진 경우뿐」) — serve() 보호는 보조."
  },
  {
    "file": "services/core-api/src/colab_core/kernel/authn.py",
    "line": 50,
    "summary": "`LoginAttempt.key` 가 접근코드 로그인 전부를 상수 `\"code:*\"` 한 버킷에 세어 누구든 5회 실패시키면 15분간 모든 접근코드 사용자가 429 이고 성공 1회가 전원의 카운터를 지운다; 같은 `AttemptLimiter` 는 `blocked()` 가 `setdefault` 로 쓰기를 해 계정명 로그인 쪽은 키가 무한 증가한다.",
    "failure_scenario": "비인증 `POST /api/v1/sessions {\"accessCode\":\"x\"}` ×5 (`session.py:64 record_failure`, `config.py:81-82` 5회/900초) → 이후 정상 접근코드도 `session.py:57 limiter.blocked` 에서 429; `session.py:69 clear(\"code:*\")` 가 전원 초기화라 유효 코드 하나를 섞는 추측 공격은 늦춰지지 않음. 형제: `throttle.py:33 bucket = self._failures.setdefault(key, deque())` 가 `blocked()` 경로(38-39, 자격 검사 전)에서 실행되고 삭제는 성공 로그인 `clear()` 뿐 → 무작위 `accountName`(최대 128자) 요청마다 영구 dict 항목 추가, nginx.i2.conf 에 `limit_req`/`limit_conn` 0건."
  },
  {
    "file": ".github/workflows/ci.yml",
    "line": 16,
    "summary": "CI 가 core-api(51파일·533함수)·ai-service(13·133)·viz-render(28·205) 의 pytest 를 어느 잡에서도 돌리지 않고 pipeline-worker 만 `-m \"stage2 and not e2e\"` 부분 실행 — 서비스 측 테스트 함수 1102 중 871 이 CI 에서 한 번도 실행되지 않으며, 프론트 게이트 2개는 `contracts` 필터 잡 안에 있어 frontend 만 바꾼 PR 은 게이트 잡이 0개다.",
    "failure_scenario": "`grep -rn pytest .github/` = 0. gates 중 pytest 호출은 `e2e-format-coverage.sh:52`·`render-latency.sh:46`(viz, ci.yml 의 run: 에 없음)·`stage2-markers.sh:41`(pipeline-worker) 뿐; `rls-effect.sh` 는 docker+psql 만이라 `services/core-api/tests/`(test_cross_tenant.py·test_scope_kernel.py·test_password_login.py 포함) 를 어느 잡도 실행하지 않음. `ci.yml:75 if: needs.changes.outputs.contracts == 'true'` 잡 안에 `frontend-typecheck`(138)·`frontend-test`(144) 가 있고 `outputs.frontend`(27) 소비처 0 → e935db2(frontend 1파일)·d0c6aa4·05a4b2e(신규 테스트 154·302줄 포함)는 게이트 0개로 병합(git show 실측). 형제 green-by-skip: `db-boundary` 는 `run.sh db-boundary` 호출 0(셀프테스트만); `run.sh:237` selftest 집합이 18 중 14(autometa-loss·preview-tile-slot·artifact-ownership 은 CI 어디에도 없음); `artifact-ownership.toml:23 tolerate = true` 로 전건 UNDECIDABLE 인데 `artifact-ownership.sh:334-335` 가 그때만 red 라 0건 판정·green·기한 없음; 자체 `expect()` 를 가진 셀프테스트 12개 중 10개가 rc=78 준비실패를 「기대한 red」로 셈(`_expect_pool.sh:58` 만 가름)."
  },
  {
    "file": "services/core-api/src/colab_core/domains/d6_project.py",
    "line": 90,
    "summary": "`update_project` 가 계약 `ProjectPeriod` 의 `YYYY-MM` 문자열을 `date` 컬럼(schema.sql:712-713)에 그대로 바인딩 — 라우트 `project.py:108` 이 `_period()` 로 변환한 값을 버리고(주석 「형식 검사만 — 저장은 도메인이 한다」) 도메인은 변환하지 않아, 기간이 실린 모든 `PATCH /projects/{id}` 가 500 이다.",
    "failure_scenario": "`PATCH /api/v1/projects/{id} {\"period\":{\"start\":\"2026-01\",\"end\":\"2026-12\"}}` → `columns[\"period_start\"] = ... period.get(\"start\")` → `UPDATE d6_project SET period_start = :period_start` → staging DB 에 읽기 전용으로 재현 `SELECT '2026-01'::date` → `invalid input syntax for type date`. `main.py:93/97` 핸들러는 HTTPException·RequestValidationError 뿐 → 500, 같은 요청의 name·description 도 롤백. `create_project` 는 `_period()` → `dt.date(y,m,1)` 로 정상. `test_lab_and_project_update.py` 에 period 케이스 0."
  },
  {
    "file": "services/core-api/src/colab_core/app/relay.py",
    "line": 119,
    "summary": "`HttpPreviewRelay.create` 가 `status not in (200, 201, 202)` 를 전부 `RelayUnavailable` 로 뭉개 viz-render 의 415 NOT_RENDERABLE(`details.renderableFormats`)·413·400 이 core-api 에서 503 RENDER_UNAVAILABLE 「연결하지 못했다」가 되고, 프론트의 `status === 415` 분기 4곳이 죽은 코드다.",
    "failure_scenario": "GRIB 등 비지원 파일 미리보기 → viz `renders.py:99-100 ApiError(415, NOT_RENDERABLE, ...)` → relay 119-120 raise → `preview.py:101-105` 503 → 사용자는 그릴 수 없는 파일을 「서버 장애」로 반복 재시도, 지원 형식 목록은 도달 못 함; `previewSource.ts:41/67`·`datasetPreviewSource.ts:74/87` 의 NotRenderableError 분기 도달 불가. `palettes`(133)·`lookup_value`(148) 동일. 상태 통과는 `create_preview_screenshot`(preview.py:194-197) 한 곳뿐. 형제: `preview.py:227-229` 가 lat/lon 의 타입만 검사(bool 도 통과) → `{\"lat\":200}` 이 viz pydantic(ge=-90) 422 → 같은 경로로 503 — 클라이언트 오류가 장애 계수에 섞임."
  },
  {
    "file": "frontend/src/components/catalog/catalogSource.ts",
    "line": 59,
    "summary": "`defaultCatalogSource` 의 빈 `catch {}` 가 401·500·네트워크 오류 전부를 픽스처 6행(업로더 호랑이·표범, `nakdong_precip_2025_Lv2.nc`) 으로 바꿔 운영 화면에 실데이터처럼 그리고, 같은 모양이 `detailSource.ts:41`(실존 데이터셋을 「이 주소에는 화면이 없어요」로)·`projectSource.ts:114`·`graphSource.ts:33` 에 반복된다 — 근거였던 501 은 해당 op 가 전부 구현돼 죽은 사유다.",
    "failure_scenario": "세션 만료 → `GET /datasets` 401 → `catalogSource.ts:34 if (!body) throw` → 56-61 catch → `stub.list(q)` → 카탈로그에 가짜 6행·집계, `AuthGate` 는 통보받지 못해 로그인으로 돌아가지 않음; 행 클릭은 서버에 없는 id 로 이동. `not_implemented.py` OPERATIONS 4개(deleteDataset·getDatasetDeletionImpact·addUploadFile·replaceUploadGridFile)에 listDatasets/getDataset/listProjects/getProject 없음 → 501 분기(32/40) 도달 불가. `import.meta.env` 0건 — 빌드 분기 없음. `detail/fixture.ts:210` 은 모르는 id 에 `DatasetGone` → `useDatasetDetail.ts:27 status:'gone'`; 픽스처 id 6개는 남의 메타데이터를 그린다. `localEngine.ts` 가 서버 정렬을 재구현하며 프로젝트(52: 이름 vs 서버 개수)·계보(58: 정책 순서 vs 서버 사전순) 두 곳이 이미 다름."
  },
  {
    "file": "services/core-api/src/colab_core/app/routes/ingestion.py",
    "line": 251,
    "summary": "`create_upload`(213)·`add_dataset_file`(599)·`replace_dataset_grid_file`(743) 세 라우트만 `async def` 인데 `await upload_file.read()` 로 파일 전체를 메모리에 올린 뒤 `path.write_bytes` 와 동기 SQLAlchemy 를 이벤트 루프에서 실행 — nginx 상한 8g(`nginx.i2.conf:53`) 까지 RSS 가 파일 크기를 따라가고 그동안 프로세스의 모든 요청(/healthz 포함)이 멈춘다; ai-service 도 같은 모양이다.",
    "failure_scenario": "5GB NetCDF 업로드 → 251 `payload = await upload_file.read()` → 255 `_store` → `write_bytes`(68) 를 루프 스레드에서 → `kernel/db.py:12` 동기 엔진의 `ledger.accept`/`publish_accepted` 도 루프에서 → 카탈로그·세션·헬스 정체. `run_in_threadpool|to_thread` 0건, 형제 라우트는 전부 `def`(스레드풀). 형제: ai-service `main.py:87 async def search_datasets` → 128 `service.search` → `dictionaries.py:81 _read()` 5 SELECT(기본 `literal` 모드에서도 무조건) + llm 모드 `interpret.py:142 urlopen(timeout=8)` 루프 차단, uvicorn 단일 워커 → `compose.i2.yml:382` healthz 3초 초과."
  },
  {
    "file": "services/viz-render/src/colab_viz/domains/d7_visualization/jobs.py",
    "line": 530,
    "summary": "`JobStore._jobs` 는 삽입·조회·전체 스캔만 있고 `del/pop/clear` 가 없어 완료 job 이 `job.rendered.values`(f4 2D 래스터)를 프로세스 수명 내내 붙들며 `_produced_for`(607) 가 매 submit 마다 전 job 을 순회한다; `screenshots.py:56 layers` 도 상한이 없어 4096² 뷰포트 × N 레이어가 층당 ~1GB 를 일시 할당한다.",
    "failure_scenario": "`grep -nE 'del self._jobs|_jobs.pop|_jobs.clear'` = 0; `get()`(595) 은 만료 job 을 그대로 반환(`expired` 는 410 판단에만 씀). 하루 500 렌더 × 2048변 f4 ≈ 수 GB 상주 → 컨테이너 OOM; 1000번째 submit 은 그리기 전 1000회 순회. 형제: `Field(min_length=1)` 만 있고 `maxItems` 도 계약(core-viz.yaml:755)에 없음, 같은 renderId 반복 허용, `_over`(screenshot.py:63-73) 가 (4096,4096,3) f4 3벌 + i8 인덱스 134MB → 8 레이어 요청 1건이 ~8GB 를 스레드풀(기본 40)에서 통과, core-api `preview.py:148-150` 도 개수 제한 없이 레이어마다 relay.get."
  },
  {
    "file": "services/core-api/src/colab_core/app/main.py",
    "line": 39,
    "summary": "`openapi_url=None` 이고 codegen manifest 4항목(fe-core.ts + storage_layout.py ×3) 중 백엔드 모델은 0 이라 라우트가 `body: dict` 19곳·`isinstance` 47곳(8파일)으로 손검사하고 viz-render 는 pydantic 9클래스로 core-viz.yaml 을 재진술 — 그 틈으로 사용자 입력 5경로가 400 대신 500 이 된다.",
    "failure_scenario": "확인된 5경로 — `access.py:65 Ulid(datasetId)` 무검사 → `ids.py:29-31` ValueError(catalog.py:474 는 검사함); `session_token.py:80 self._mac(payload)` 가 try(82) 밖이고 `_mac` 이 `.encode(\"ascii\")`(57) → 비ASCII Bearer 로 비인증 500; `d3_catalog.py:714 period.get(\"start\")` 자유문자열 → timestamptz 파싱 오류(검사는 catalog.py:615-617 `isinstance(str)` 뿐); `catalog.py:585 validate_human_metadata` 가 `topic` 을 안 봐 DB CHECK(schema.sql:370) IntegrityError; `project.py:132` 가 strip 없이 길이만 봐 공백 이름이 `CHECK (length(btrim(name)) > 0)`(710) 에 걸림(102 update 는 strip). `main.py:93/97` 핸들러가 HTTPException·RequestValidationError 뿐. 지금 고칠 것: 가드 5줄 + IntegrityError/ValueError 핸들러. 뒤에 고칠 것: `gen_storage_layout.py` 와 같은 방식으로 seam → pydantic 생성(`preview.py:80-88/156-167/228-230` 이 viz 모델과 같은 필드를 다시 검사한다)."
  },
  {
    "file": "services/pipeline-worker/src/colab_pipeline/d5/grid.py",
    "line": 135,
    "summary": "기준 격자 탐색이 pipeline-worker `d5/grid.py`(파일명 접두 `lat*/lon*`, 값 검사 없음)와 viz-render `d7 grid.py`(stem 짝 + `LAT_LIMIT=90` 수치 판정, 거절 사유 3종) 두 알고리즘으로 갈려 같은 디렉터리를 두 서비스가 다르게 읽고, 같은 D5/D7 쌍둥이 `cog.py`/`raster.py`·`hsr.py`×2 와 NetCDF 차원 해석도 동작이 다르다 — `storage_layout.py` 는 codegen 으로 3벌 동일(md5 일치)인데 이 모듈들은 손사본이다.",
    "failure_scenario": "`Latitude.npy`+`Longitude.npy` → pipeline 통과(135-136 `startswith`), viz `_pair_key` 'itude'/'gitude' → REASON_PAIR_MISMATCH → 등록은 됐는데 미리보기 거절. 경도가 든 `lat_*.npy` → pipeline 이 조용히 전치 수용, viz 는 값으로 바로잡음 → COG 와 미리보기가 픽셀 단위로 다름. `cog.py:86 valid = np.isfinite(d)` vs `raster.py:72 ... & isfinite(la) & isfinite(lo)` → NaN 좌표 셀에서 pipeline 은 clip→astype 순서로 INT64_MIN IndexError → 「COG 변환 실패」, viz 는 렌더; `cog.py:74` 는 `lon_min == lon_max` 미검사(raster.py:59-60 은 4값 검사). `hsr.py` 0블록: pipeline 정상 반환 → `pipeline.py:128 hsr.blocks[0]` IndexError, viz 는 `HsrParseError`. `parse.py:59 meta.grid = (dims[spatial[0]], dims[spatial[1]])` 가 NetCDF 차원 선언 순서를 따라 lon 선행 파일에서 (nx, ny) 로 전치 → `grid.py:128/144` 형상 불일치 → 맞는 격자가 있어도 「좌표/격자 없음」 실패, 사용자 표시 `grid_text` 도 전치(형제 핸들러 63/95/120/130 은 전부 (rows, cols))."
  },
  {
    "file": "frontend/src/components/catalog/catalogSource.ts",
    "line": 35,
    "summary": "목록·검색 페이징이 양쪽에 반만 서 있다 — 서버는 `PAGE_SIZE=20` 으로 자르고 `nextCursor` 를 내는데(catalog.py:190-191, project.py:290-296) 클라이언트는 cursor 를 보내지도 받지도 않고(`queryParams` 12-26, `CatalogList` types.ts:26) 더 보기 컨트롤도 없어 20건 넘는 연구실은 헤더 「N건」 아래 20행만 보이고 나머지는 도달 불가; 검색은 `totalCount: len(items)` 라 건수 자체가 페이지 크기다.",
    "failure_scenario": "데이터셋 50건 연구실 → `DatasetsPage.tsx:38 totalCount` 「50건」 + `CatalogTable.tsx:73` 20행, 21~50 도달 불가. `grep -rn cursor frontend/src`(generated 제외) = 0. 검색: `catalog.py:328 matches, total = search_datasets(...)` 의 total 은 cursor 계산에만 쓰이고 386 `\"totalCount\": len(items)` 반환(verified 분기도 `len(kept)` 아님), `SearchResultsPage.tsx:162 found={shown.length}` → 100건 일치가 「20건을 찾았어요」, 21건째부터 도달 불가. 계약 `ListEnvelope.totalCount`(common.json:212) 는 결과 헤드가 반드시 표시하는 값."
  },
  {
    "file": "services/core-api/src/colab_core/kernel/config.py",
    "line": 151,
    "summary": "`_FILE` 간접참조 `resolve_env_or_file` 이 DB URL(142)에만 걸려 있고 `session_secret`(151)·`viz_service_token`(167) 은 생 env 라 `compose.i2.yml:194/183` 이 세션 서명 HMAC 키와 서비스 토큰을 `docker inspect` 로 보이는 컨테이너 env 로 넘기고, `COLAB_CORE_SESSION_SECRET_FILE` 을 설정하면 오류 없이 무시돼 `POST /sessions` 가 500 SESSION_UNAVAILABLE 만 낸다; viz-render kernel 에는 `_FILE` 지원 자체가 없다.",
    "failure_scenario": "호스트에서 `docker inspect colab_v2_staging_core_api` → 세션 서명 키 노출 → `SessionSigner` 로 임의 accountId/labId 토큰 위조 가능 → 모든 연구실 경계 무력(DB 비밀번호가 작업 로그에 새어 `_FILE` 을 도입했던 바로 그 경로; 같은 compose 의 DB URL 5곳은 전부 `_FILE`). `_FILE` 설정 시 `main.py:54-56 if settings.session_secret` 로 signer 미생성 → `session.py:47-52` 500, 무시된 변수 이름은 어디에도 안 나옴. viz-render `config.py:120/123`(`COLAB_VIZ_SERVICE_TOKEN`·`COLAB_VIZ_TILE_SIGNING_SECRET`) 도 생 env(`compose.i2.yml:313/315`), 그 kernel 에 `resolve_env_or_file` 0건. (값은 출력하지 않았다.)"
  }
]
```

**정원 밖 — 검증은 끝났고 15에 못 든 것** (한 줄씩, 전부 CONFIRMED · 표시한 1건만 PLAUSIBLE)
- ai-service 계약 이탈: `core-ai.yaml:60` 전역 serviceToken 인데 `main.py` 는 ULID 모양 헤더만 검사(Authorization 읽기 0건), `relay.py:307/376` 도 토큰 미전송, 라우트는 루트인데 계약은 `/ai/v1`(compose 가 접두 없이 맞춤). 호스트 포트 없음 → 잠재 — 계약대로 코딩하는 에이전트가 양쪽 다 틀린다
- `ingestion.py:624` `_store` 가 `if kind == GRID` 400 앞에 실행 → 거절된 격자 파일이 `uploads/{id}/grid/` 에 잔류(viz 는 폴더가 사실)
- `AuthGate.tsx:36` `/me` 에 `.catch` 없음 → 서버 불통 시 `auth-pending` 빈 화면 영구, 재시도 없음
- `upload/PreviewPanel.tsx:125` poll 취소 불가·구 렌더가 새 렌더를 덮음 — 그리고 `preview/usePreviewRender` 와 중복(업로드 사본은 404/410/415/503 을 한 문장으로 뭉갬)
- `d5_ingestion.py:479` `attempt` 증가·DLQ 경로 없음 → 실패한 발행 영구 재시도, 소비자에 `redelivery:false` 거짓
- `value_lookup.py:132` LCC 등 투영 밖 좌표에서 `warp_transform` 이 CPLE 예외 → 500(계약은 200+사유). rasterio 1.5.1 로 재현
- `d10_ai_services.py:152`(+`d10_suggestion.py:164`) 원시 예외를 `degradedReason` 에 실어 DB 호스트·포트·롤이 응답 본문까지 감(화면엔 안 그림, 네트워크 탭엔 보임)
- 화면 소결함: `ValueLookupPanel.tsx:39` 순서 보호 없음(느린 이전 클릭 값이 최신을 덮음); `LineageStep.tsx:174` 마지막 카드 거절 후 「1 / 1」 잔류; `PreviewPanel.tsx:208` `Number('')` → classCount 0; `visits.ts:49` 24시간 창 계산(어제 23시가 「오늘」); `download.ts:48`/`ScreenshotButton.tsx:77` 동기 revoke — PLAUSIBLE(브라우저 의존)
- 효율: `value_lookup.py:91` 클릭마다 원본 전체 sha256(+격자 폴더 재해시); `preview.py:264` 산출물 재사용 0(같은 페이지 재방문마다 전체 재렌더); `catalog.py:82 _compose` 가 연구실 전체를 5곳에서 적재 후 파이썬 정렬·절단; `dictionaries.py:81` 검색마다 5 SELECT; `worker.py:357` 5초마다 엔진 생성·폐기; `readers.py:356` 코드값별 전배열 비교(데드라인은 스테이지 경계에서만 검사); `lineage.py:68` 노드당 1 쿼리
- 손사본 커널: `ids.py` 4벌 API 불일치(viz 는 비문자열에 TypeError); `errors.py` 2벌(기본 문구 이미 다름); FileKind 리터럴 5곳+SQL 7곳; ULID 정규식 viz 라우트 3곳+`d10_suggestion.py:37`; 권한 스위치 전문 6곳(`.get(sw, False)` vs `.get(sw)` 혼재, 쓰기 라우트에 가드 있음을 확인하는 게이트 0); 봉투 해석 6모듈; `NotImplemented` 4벌; `RegisterArea` props 30
- `LineageSection.tsx:362` 계보 수정 버튼 onClick 없음 — addLineageParent·removeLineageParent·confirmLineage·linkProjectDataset 은 서버에 있고 화면 호출처 0
- 규칙: `d4_lineage.py:40` 와 `schema.sql:551/552/574` 가 D3 테이블 직접 조회·FK(§3-1, 게이트 미검출 — `deleted_at` 필터 누락 주장은 REFUTED: 묘비 노드는 의도); 문서 절대경로 35줄(게이트 없음); `not_implemented.py:1` 「23개」 vs 실제 4, 테스트명 「5」

**이번에 재지 않은 것**: 프론트 브라우저 실동작(Firefox/Safari 다운로드), 격자 digest 충돌의 실데이터 발생 빈도, 이벤트 스풀 잔류량 — 각각 무엇을 하면 풀리는지는 해당 항목에 적었다.
