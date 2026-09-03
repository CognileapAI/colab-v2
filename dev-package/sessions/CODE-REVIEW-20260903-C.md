# CODE-REVIEW-20260903-C — 레인 C `viz-render`

> 기준 — `CODE-REVIEW-20260903-PLAN.md §2` 레인 C 행 · 결함 `CODE-REVIEW-20260903.md` #1·#2·#3·#11 + 부록(`_FILE` 부재).
> 편집 면 — `services/viz-render/**` 만. `contracts/**`·`infra/**`·다른 서비스·프론트 무접촉(실측 — 아래 §6).
> 브랜치 `worktree-agent-a9df4b7601bb30d66` · 기준 커밋 `d4d11b5` · push 없음 · main 병합 없음.

## 1. 계수 — 전/후

| 시점 | 명령 | 결과 |
|---|---|---|
| 기준선(수정 전, `d4d11b5`) | `.venv/bin/python -m pytest -q -m "not e2e and not perf"` | **199 passed · 40 deselected** |
| 항목 1 뒤 | 같음 | 211 passed · 40 deselected |
| 항목 2 뒤 | 같음 | 217 passed · 40 deselected |
| 항목 3 뒤 | 같음 | 231 passed · 40 deselected |
| 항목 4 뒤 | 같음 | 240 passed · 40 deselected |
| 항목 5 뒤(최종) | 같음 | **250 passed · 40 deselected** |

- 계수 기준 — 시험 **함수** 수(파라미터화 전개 포함). 실행 시점 2026-09-03, 이 워크트리, 병렬 없음(단독).
- **기존 실패 0건** — 기준선이 이미 전건 green 이었다. 이 레인이 고친 것 중 「기존에 red 였던 시험」은 없다(결함 넷 다 시험이 없었다).
- 신설 45 · 개정 1(`test_아는_종류에_모르는_트리거가_실려_오면_거절한다` → `…격리한다`).

## 2. 항목별 — 변경 · 시험 · 전/후

### 항목 1 — 테넌트 경계 (#1) · 커밋 `67c04d1`

- **결함** — `grep -rn 'X-CoLAB' services/viz-render/src` = 0건. core-api `app/relay.py:_scope_headers` 가 **모든 중계 호출에** `X-CoLAB-Lab`·`X-CoLAB-Account` 를 실어 보내는데 받는 쪽에 읽는 줄이 없었고, core-api `routes/preview.py` 는 그 응답을 경계 확인으로 삼고 있었다 — **양쪽 다 상대가 본다고 믿었다.**
- **변경**
  - `services/viz-render/src/colab_viz/app/deps.py:tenant_scope` — 경계를 읽는 한 자리. 없거나 공백이면 **400 `TENANT_SCOPE_MISSING`** + `details.header`. 401 이 아닌 근거 = `require_caller` 가 라우터 의존으로 먼저 서서 자격 증명은 이미 통과한 상태이고, 빠진 것은 요청이 말했어야 할 경계다.
  - `deps.py:same_lab_or_missing` — 불일치는 **404**, 문구는 「없다」와 **글자까지 동일**. 403 이면 그 `renderId` 가 존재한다는 사실이 샌다.
  - `app/routes/renders.py:create_render` — 경계를 **가장 먼저** 읽는다(대상 해석 뒤에 읽으면 헤더 없는 요청이 대상 존재를 404/200 으로 먼저 알려 주는 신탁이 된다). `jobs.submit(lab=, account=)`.
  - `domains/d7_visualization/jobs.py:RenderJob.lab`·`.account` — 기본값 `""`(어떤 요청과도 안 맞는다. 「전부와 맞는 값」이면 한 자리만 빠져도 조용히 열린다).
  - `app/routes/renders.py:get_render` · `app/routes/screenshots.py:create_screenshot`(층마다) — 대조.
  - `app/routes/values.py:lookup_value` — **헤더만 요구**(아래 §3 판단).
  - `jobs.py:JobStore.regenerate` — 경계를 직전 작업에서 승계.
- **시험** — `tests/test_tenant_boundary.py` 12건. 실패 확인 9건 → 수정 → green.
- **전/후** — 199 → 211.

**브라우저 대면 라우트와 중계 대면 라우트** (`app/routes/*` 실독):

| 라우트 | 부르는 자 | 의존 | 이 회차 |
|---|---|---|---|
| `POST /renders` · `GET /renders/{id}` | core-api 중계 | `require_caller` | 경계 새김·대조 |
| `POST /screenshots` · `POST /value-lookups` | core-api 중계 | `require_caller` | 경계 요구(스크린샷은 층마다 대조) |
| `GET /palettes` | core-api 중계 | `require_caller` | **그대로** — 연구실 자료가 아니라 이 단위 소유의 고정 목록이고, 계약이 이 op 에 400 을 두지 않았다(200·401·503) |
| `GET /renders/{id}/tiles/{z}/{x}/{y}.png` | **브라우저 지도 위젯이 CDN 을 통해 직접** | `require_caller_or_tile_signature`(별도 라우터) | **그대로 — 서명만** |

- 타일이 서명만으로 남는 근거 셋 — ⑴ 계약 `getRenderTile` 산문 축자 「**core-api 를 통과하지 않는 유일한 경로다.** 지도 위젯이 CDN 을 통해 직접 부른다」 ⑵ 브라우저의 `<img>`/타일 요청에 커스텀 헤더를 실을 수 없다 — 요구하면 계약대로인데 실배포에서 **전량 401** 이다(`renders.py` `tile_router` 주석이 이미 그 사고를 적어 두었다) ⑶ **새는 문은 타일이 아니라 `getRender`** 다. 서명된 `tileUrlTemplate` 이 나가는 자리가 거기 하나뿐이라, 거기서 막으면 타일도 함께 막힌다. 음성 시험 `test_타일은_경계_헤더_없이도_서명만으로_열린다` 가 이 자리를 잠근다.

### 항목 2 — 무효화가 실제로 돈다 (#2) · 커밋 `a2c8edd`

- **결함** — `regenerate` 가 `submit()` **직후** `job.invalidation` 을 읽었는데 기본 실행기(`COLAB_VIZ_EXECUTION=thread`)에서 그 필드는 렌더가 끝난 뒤에 채워진다. **운영에서는 언제나 `None`** 이었고 `invalidation.apply` 호출처가 레포에 그 한 곳뿐이라 낡은 미리보기가 **한 번도 지워지지 않은 채** 트리거만 ack 됐다. 오류가 없어 아무도 몰랐다 — 레이스가 아니라 상시.
- **변경**
  - `jobs.py:JobStore._run_and_plan` — 범위 계산과 **집행**을 완료 경로에서 함께 한다. `submit` 의 inline·thread 와 `run_pending` 의 manual 셋이 **같은 자리**를 지난다(실행기마다 따로 적으면 그중 하나가 빠지고, 빠진 쪽이 하필 운영 기본값이었다).
  - 집행 조건 둘 — `plan.regenerate`(사건이 있을 때만. 아니면 스타일만 바꿔 다시 그리는 요청이 앞의 그림을 지운다) · `status == 완료`(「새 것이 선 뒤에 낡은 것을 치운다」의 나머지 절반).
  - `RenderJob.invalidation_removed` — 집행 결과. 계산과 집행은 다른 사실이고, 종전에는 집행이 0 이라는 것을 볼 자리가 없었다.
  - `RenderJob.done`(`threading.Event`) + `regenerate` 가 완료를 기다린 뒤 답한다(`manual` 제외 — 그 실행기는 시험이 순서를 정한다). 안 기다리면 「무효화 0건」 보고서가 나가고 트리거는 그 상태로 ack 된다.
  - `app/triggers.py:_collect`·`drain` — **봉투 단위 격리.** 종전 `list(port.poll())` 은 제너레이터 안의 예외 하나로 그 틱의 전 봉투를 잃었고, `regenerate` 도 `LookupError` 만 잡아 그 밖의 예외 한 건이 같은 틱의 나머지를 막았다 — 독스트링이 「한 건이 실패해도 나머지를 멈추지 않는다」인데 코드가 그것을 안 지켰다. 실패한 건은 **ack 하지 않는다**(다음 바퀴가 다시 집는다).
  - `app/trigger_bus.py:_quarantine` + `QUARANTINE_DIRNAME = "_quarantine"` — 어긋난 봉투를 **버스 안** 격리 자리로 옮기고 `port.quarantined` 에 사유를 남긴다. 지우지 않는다(증거가 남아야 한다). 옮기는 자리도 `_discard` 와 같은 울타리 검사를 지난다.
  - `trigger_bus.py:poll` — 이미 집행한 멱등 키의 재전달본을 그 자리에서 `_discard`. 종전에는 `continue` 만 해서 `_inflight` 에 등록되지 않았고, `ack` 는 `_inflight` 를 통해서만 지우므로 **영원히 못 걷었다** — at-least-once 계약에서 재전달은 정상이므로 스풀이 무한히 자라고 매 틱 재파싱됐다.
- **시험** — `tests/test_auto_invalidation.py` +3(thread 실행기 집행 · 수동 경로가 안 지우는 음성 · 실패한 재생성이 안 지우는 음성), `tests/test_trigger_intake.py` +4·개정 1. 실패 확인 7건 → 수정 → green.
- **전/후** — 211 → 217.

### 항목 3 — NetCDF `instant` · 캐시 키 · 격자 digest (#3) · 커밋 `5de693f`

- **결함 ⑴** — `readers.py:_read_netcdf` 가 `instant` 를 **받기만 하고 본문에서 한 번도 쓰지 않은 채** `while raw.ndim > 2: raw = raw[0]` 로 늘 첫 시각을 그렸다. 계약은 「그릴 시각. 층마다 따로 고른다 … 생략하면 첫 시각이다」인데 **지정해도 첫 시각**이었다. `render_cache_key` 에도 `instant` 가 없어 24시각 파일의 24개 요청이 **같은 키·같은 PNG** 를 나눠 썼다 — 시각을 바꿔도 그림이 안 바뀌는 것이 캐시로 굳었다.
- **변경 ⑴** — `readers.py:_time_index`·`_parse_instant`·`_instant_labels` 신설. 값 변수의 `dimensions` 에서 시각 축(`time`·`times`·`t`·`valid_time`·`forecast_time`)을 찾아 `netCDF4.num2date` 로 편 뒤 **정확 일치**로 고른다. 생략 → 0(계약 축자). 없는 시각·시각 축 없는 파일에 지정 → `FieldReadError` + 사유(요청값 + 파일에 있는 값 목록).
  - **예외형 판단** — 「그럴 값이 없다」(`variable` 부재)가 이미 `FieldReadError` 이고 시각 부재는 그 형제라 같은 형을 썼다. `NotRenderableError` 는 **파일의 성질**에서 오는 실패(`failures.is_retry_pointless` 가 그것으로 재시도 무의미를 판정한다)이고, 틀린 `instant` 는 요청을 고치면 되는 자리라 성질이 다르다.
  - **표면 노출** — 이 실패는 `_run` 의 마지막 그물을 지나 `failure.code = RENDER_UNKNOWN_ERROR` + `details.detail` 에 사유로 나간다. 전용 실패 코드 신설은 `ErrorEnvelope.code` 가 자유 문자열이라 계약 개정 없이 가능하지만 **이 회차 범위 밖**으로 두었다(§5 유보).
- **변경 ⑵** — `cache.py:render_cache_key(instant=…)` + `jobs.py:_build_artifacts` 의 `key_params`. `selection` 이 「어느 변수」면 이것은 「어느 시각」이고 둘은 같은 자격으로 산출물을 가른다.
- **결함 ⑶ · 변경** — `jobs.py:_grid_digest` 가 lat 의 shape · `nanmin(lat)` · `nanmax(lon)` **세 값만** 해시했다. 그 셋이 같은 다른 격자로 갈아 끼우면 키가 같아지고 `invalidation` 의 `keep_keys` 가 구 산출물을 「신선」으로 보존한다. → `_array_fingerprint` 로 **위도·경도 둘 다** 형상 + 양 끝(전량 실측) + 값을 접는다. 값은 `_DIGEST_FULL_MAX_ELEMENTS`(65,536 = f8 512 KB) 이하면 전량, 그 위는 균등 보폭 `_DIGEST_SAMPLE_COUNT`(4,096)점. NaN 은 표식(`_DIGEST_NAN_SENTINEL`)으로 바꿔 **비트 표현에 기대지 않는다**.
  - **한계(적어 둔다)** — 표본 구간에서 「표본에 안 걸린 한 점」은 잡지 못한다. 검사합이 아니라 digest 이고, 막는 것은 **격자 교체가 같은 키를 내는 것**이다(종전 세 통계는 격자를 통째로 갈아도 같은 키를 냈다). 시험 독스트링에 같은 문장을 적었다.
- **시험** — `tests/test_instant_and_grid_digest.py` 14건(실 NetCDF 3시각 픽스처 · 라우트까지 내려가는 키 시험 포함). 실패 확인 7건 → 수정 → green.
- **전/후** — 217 → 231.

### 항목 4 — JobStore 메모리 · 스크린샷 층 (#11) · 커밋 `3bfa99c`

- **결함** — `JobStore._jobs` 에 삽입·조회·전체 스캔만 있고 `del`/`pop`/`clear` 가 한 자리도 없었다. 완료된 작업이 `rendered.values`(f4 2D 래스터)를 프로세스 수명 내내 붙들고, `_produced_for` 는 submit 마다 전 작업을 순회했다(1000번째 submit 은 그리기 전 1000회). `screenshots.layers` 에는 상한이 없었다.
- **변경**
  - `jobs.py:JobStore._evict_expired` — 축출 조건은 `expires_at` **하나**다. **완료 시점이 아니다** — 타일(`getRenderTile`)과 스크린샷이 `job.rendered` 를 메모리에서 읽으므로 완료 직후에 놓으면 성공한 렌더가 곧바로 못 쓰는 렌더가 된다. 만료 순서 = submit 순서(TTL 상수)라 `deque` 앞만 보면 되고, 축출이 다시 전체 스캔이 되지 않는다. `submit`·`get` 이 부른다.
  - 묘비 — 축출은 같은 객체에서 `rendered`·`artifacts`·`partial`·`invalidation` 만 놓아 만료된 id 가 계약이 요구하는 **410** 을 계속 답한다. 묘비 개수는 `_MAX_TOMBSTONES = 4096` 으로 묶고 넘으면 가장 오래된 것부터 `_jobs` 에서 제거 — 그때는 404 이고, 「그 id 에 대해 아는 것이 없다」는 뜻이라 정직하다.
  - `jobs.py:JobStore._produced`·`_remember_produced`·`_produced_for` — 대상별 색인. **작업에 매달지 않는다** — 작업이 축출돼도 디스크의 산출물은 그대로라, 함께 잊으면 영원히 무효화되지 않는 파일이 남는다. 색인 갱신은 `_plan_for` **앞**이다(방금 구운 것도 후보에 들어야 `keep_keys` 가 그것을 살린다).
  - `screenshot.py:MAX_LAYERS = 8` + `routes/screenshots.py` 의 **400 `TOO_MANY_LAYERS` + `details.maxLayers`·`details.layers`**.
  - 뷰포트 — **손대지 않았다.** 계약 `Viewport.width`·`height` 의 `maximum` 이 이미 4096 이고 `screenshot.MAX_SIDE` 가 같은 값이다. 더 좁히면 계약대로 부르는 쪽이 이유 없이 거절당한다. 음성 시험으로 값 일치를 고정했다.
- **왜 400 이고 413 이 아닌가** — `createScreenshot` 의 계약 응답은 **200·400·401·404·409·503** 이고 413 이 없다(`createRender` 에만 있다). 없는 상태 코드를 지어내면 부르는 쪽이 처음 보는 상태를 만난다.
- **왜 8 인가 — `[정본 무근거]`** — 정본 `Policy_데이터셋_상세 §8` 은 「이 데이터」 층에 **얹은 층**을 겹쳐 비교한다고만 적고 개수를 말하지 않는다. 실측 근거는 비용이다: 최대 뷰포트(4096×4096)에서 층 하나가 지나는 전이 할당이 `_sample_rgba` 의 RGBA(u1 67 MB) · 표본값(f4 67 MB) · 색인(i8 134 MB) 과 `_over` 의 f4 중간판(≈340 MB)이라 **층당 수백 MB** 이고, 층 수가 자유면 그 배수가 그대로 한 프로세스에 들어온다(스레드풀 기본 40 이 그것을 동시에 통과시킨다). 8 = 밑판 1 + 얹은 층 7 로 화면이 실제로 비교하는 수를 넉넉히 덮는 값. **기존 상수 중에 쓸 것이 없어**(`MAX_SIDE` 는 한 변, `palettes.MAX_CLASS_COUNT` 는 구간 수) 새로 두었다.
- **시험** — `tests/test_job_retention.py` 9건(완료 시점에 안 놓는 음성 · 만료 뒤 축출 + 410 · 수명 남은 것 음성 · 묘비 상한 · 색인 · 축출 뒤 후보 잔존 · 층 상한 400 · 상한까지 200 · 뷰포트 음성). 실패 확인 6건 → 수정 → green.
- **전/후** — 231 → 240.

### 항목 5 — `_FILE` 간접참조 (부록) · 커밋 `39a4fb2`

- **결함** — core-api 는 DB 접속 문자열에 `_FILE` 을 두었는데(`docker inspect` 의 환경변수 목록에 접속 문자열이 통째로 들어 있어 그 값이 작업 기록에 남았다) **viz-render 의 kernel 에는 그 장치 자체가 없었다.** `COLAB_VIZ_TILE_SIGNING_SECRET_FILE` 을 설정해도 오류 없이 무시돼 표면이 조용히 503 만 냈고, 무시된 변수 이름은 어디에도 안 나왔다.
- **변경** — `kernel/config.py:resolve_env_or_file` + `FILE_SUFFIX`. core-api 와 **같은 규칙 다섯**: `_FILE` 이 있으면 끝 공백만 벗겨 읽고 · 못 읽거나 비면 죽고 · 둘 다 설정되면 죽고 · 둘 다 없으면 `None`(표면 503) · 값을 예외 메시지에 싣지 않는다. `load_settings` 의 `COLAB_VIZ_SERVICE_TOKEN`·`COLAB_VIZ_TILE_SIGNING_SECRET` 이 이 판독기를 지난다.
- **codegen 통일 후보** — 이 함수는 core-api 의 같은 함수와 글자까지 거의 같은 **손사본**이다. 배포 단위 독립 규율상 공유 라이브러리로 빼지 않지만, `PLAN §4` 유보 1(`ids.py`×4 · `errors.py`×2 …)과 **같은 묶음**이다. 함수 독스트링에도 같은 문장을 남겼다.
- compose 전환은 이 레인의 편집 면이 아니다(`infra/**` 금지 · `PLAN §4` 유보 6, Ted go/no-go). **값은 어디에도 출력하지 않았다.**
- **시험** — `tests/test_secret_from_file.py` 10건. 실패 확인 8건 → 수정 → green.
- **전/후** — 240 → 250.

## 3. 계약 델타 초안 — **적용하지 않았다** (`contracts/**` 동결)

`contracts/seams/core-viz.yaml` 에 넣을 것 셋. 값은 이 회차에 **박지 않았고**, 코드는 계약이 이미 선언한 상태 코드 안에서만 움직였다.

1. **경계 헤더 선언** — `grep -rn "X-CoLAB" contracts/` = **0건**. core-api 가 실제로 보내고 viz 가 이제 판정하는 값인데 계약에 이름이 없다.
   ```yaml
   components:
     parameters:
       LabScope:
         name: X-CoLAB-Lab
         in: header
         required: true
         description: 이 요청이 어느 연구실의 것인가. core-api 가 중계에 싣는다(사람의 세션이 아니다).
         schema: { $ref: "../schemas/common.json#/$defs/Ulid" }
       AccountScope:
         name: X-CoLAB-Account
         in: header
         required: true
         description: 누가 불렀는가. 경계 판정에는 쓰지 않는다 — 출처 표시다.
         schema: { $ref: "../schemas/common.json#/$defs/Ulid" }
   ```
   거는 자리 — `createRender` · `getRender` · `createScreenshot` · `lookupValue`. **`getRenderTile` 에는 걸지 않는다**(브라우저 직접 호출) · `listPalettes` 는 판정 대상이 없어 보류.
2. **`getRender` 응답에 `"400"`** — 지금 선언은 200·404·401·503 뿐이다. 헤더 없는 요청을 400 으로 내는 것이 이 회차의 판정인데(계획 §2 레인 C 행 「헤더 없음 400」) 그 코드가 계약에 없다. `createRender`·`createScreenshot`·`lookupValue` 는 이미 400 을 선언하고 있어 그대로 맞는다.
3. **`ScreenshotRequest.layers` 에 `maxItems: 8`** — 지금은 `minItems: 1` 만 있다.
   ```yaml
   layers:
     type: array
     minItems: 1
     maxItems: 8      # 층 하나가 뷰포트 한 판을 통째로 훑는다 — 층당 전이 할당이 수백 MB
     items: { $ref: "#/components/schemas/ScreenshotLayer" }
   ```

## 4. `[미확인]` — 재지 못한 것

| 항목 | 무엇을 못 쟀나 | 무엇을 하면 풀리나 |
|---|---|---|
| `render-latency` 게이트 | **red(준비)** — 돌지 못했다. 판정 red 가 아니다. 실측 출력: `::gate-readiness-failure::gate=render-latency\|waited_for=원천 데이터 마운트(COLAB_REFERENCE_DATA)\|limit=대기 없음\|elapsed=0초\|detail=COLAB_REFERENCE_DATA 가 원천 디렉터리를 가리키게 하고 재실행한다. 원천이 없으면 이 검사는 돌 수 없고, 못 돈 것은 통과가 아니다.` | `COLAB_REFERENCE_DATA` 를 원천 디렉터리로 선언하고 재실행 |
| `e2e-format-coverage` 게이트 | **red(준비)** — 같은 사유. 실측 출력의 `gate=` 만 다르다(`gate=e2e-format-coverage`) | 같음 |
| `e2e`·`perf` 시험 40건 | 실행 못 함(같은 원천 데이터 사유). 내역 — `test_e2e_real.py` 10 · `test_e2e_storage_layout_real.py` 5 · `test_perf_render_latency.py` 25. **경계 헤더는 넣었다** — 이 셋 중 HTTP 를 부르는 둘(`test_e2e_real.py`·`test_perf_render_latency.py`)이 `conftest.AUTH` 를 쓰고 그 상수에 두 헤더를 넣었으므로 자동 반영이다(`test_e2e_storage_layout_real.py` 는 HTTP 호출 0건 — 배치 시험이라 손댈 것이 없다). **다만 실제로 통과하는지는 이 회차가 재지 않았다** | 위와 같이 원천 데이터를 선언하고 `-m "e2e"` · `-m "perf"` 로 실행 |
| `artifact-ownership` 게이트 | **red(미선언)** — `COLAB_ARTIFACT_OWNER_DB_URL` 미선언. 이 레인의 변경과 무관하고(기준선에서도 같다) `tolerate=true` 처리는 레인 A 소유 | staging platform DB 의 **읽기 전용** URL 선언(값은 홈의 0600 env 파일) |
| 격자 digest 충돌의 실데이터 빈도 | 리뷰 본문의 「이번에 재지 않은 것」 그대로 — 실데이터에서 세 통계가 겹치는 빈도는 재지 않았다. 이 회차는 **겹쳐도 키가 갈리게** 만든 것이고 빈도를 잰 것이 아니다 | 원천 데이터에서 격자 쌍을 전수 해시해 세 통계 충돌 건수를 센다 |
| 축출의 메모리 효과 | RSS 실측 0. 「축출이 일어난다」를 시험으로 잠갔을 뿐 **몇 MB 가 줄었는지는 안 쟀다** | 장시간 부하에서 RSS 추이 측정(스테이지 필요) |

**돌린 게이트** — `import-boundary` **green**(8 kept / 0 broken · `viz-render 층 — app > domains > ports > kernel` 포함) · `banned-import` **green**(.py 127건 · viz-render 40건 · 금지 import 0). `./gates/run.sh all` 은 지시대로 돌리지 않았다.

## 5. 유보 — 이 레인이 손대지 않은 것

1. **`expires_at` 이 없는 렌더는 축출 대상이 아니다.** 수명이 붙는 것은 등록 전 업로드뿐이고(정본 §8 ③ · `NB-2`), 등록 데이터셋 렌더에 수명을 지어내면 계약이 「임시로만 둔다」고 못박은 범위를 넘는다 — **Ted 판정 사안**. 지금은 서명 수명(기본 3600초)이 지나면 타일 주소가 죽으므로 그 뒤의 job 은 조회에만 쓰인다.
2. **`jobs.py:_latest_for` 는 아직 전체 스캔이다.** 리뷰가 지목한 것은 `_produced_for` 이고 그것만 색인으로 바꿨다. 대상별 「가장 최근 완료」 색인은 같은 방식으로 붙일 수 있다.
3. **틀린 `instant` 의 전용 실패 코드.** 지금은 `RENDER_UNKNOWN_ERROR` + `details.detail` 사유다. `ErrorEnvelope.code` 가 자유 문자열이라 계약 개정 없이 가를 수 있지만, 화면 문구가 따라와야 하는 일이라 범위 밖으로 두었다.
4. **`resolve_env_or_file` 손사본 통일** — `PLAN §4` 유보 1 묶음(`ids.py`×4 · `errors.py`×2 · FileKind 리터럴 · ULID 정규식 …)에 이 함수를 더한다. 레시피는 같다(`gen_storage_layout.py` + `manifest.toml`).
5. **격리된 봉투의 회수 경로 없음.** `_quarantine/` 에 쌓인 봉투를 누가 언제 보는지는 정하지 않았다(관측 자리 `port.quarantined` 만 두었다). 운영 알림에 붙이는 것은 배포 판단.
6. **compose 의 `_FILE` 전환** — `infra/**` 는 이 레인의 편집 면이 아니다. `PLAN §4` 유보 6(Ted go/no-go) 그대로.

## 6. 경계 실측

```
git diff --name-only d4d11b5..HEAD | grep -cv '^services/viz-render/'   →  0
```
`contracts/**` · `dev-package/{PLAN-SoT.md,work-items.yaml,03-HANDOFF.md,DEPLOY-CURRENT.md}` · `infra/**` · compose · `gates/**` · 다른 서비스 · 프론트 **무접촉**. 이 기록 파일만 `dev-package/sessions/` 에 새로 는다.
운영 `colab_v2_staging_*` 무접촉(컨테이너 조작 0 · DB 접속 0). 비밀값 출력 0.

## 7. 등재문 초안 — **번호 없음** (오케스트레이터가 발급·등재)

> **〈번호 미발급〉 viz-render 경계·무효화·시각·보관 4결함 해소 (코드리뷰 20260903 레인 C)**
>
> `CODE-REVIEW-20260903.md` #1·#2·#3·#11 과 부록 1건을 `services/viz-render/**` 안에서 닫았다.
> ⑴ **경계** — core-api 가 모든 중계에 싣는 `X-CoLAB-Lab` 을 viz 가 읽는 줄이 0 이었고 core-api 는 그 응답을 경계 확인으로 삼고 있었다. 접수 때 job 에 새기고 조회·스크린샷이 대조한다(불일치 404 · 헤더 없음 400 `TENANT_SCOPE_MISSING`). **타일은 서명만으로 남는다** — 브라우저가 CDN 을 통해 직접 부르는 유일한 경로라 헤더를 실을 수 없고, 서명된 주소가 나가는 문(`getRender`)을 닫아 함께 막았다.
> ⑵ **무효화** — 집행이 `submit()` 직후에 있어 기본 실행기에서 **한 번도 돌지 않았다**(상시). 완료 경로로 옮겨 thread·inline·manual 셋이 같은 자리를 지난다. 트리거는 봉투 단위로 격리하고(어긋난 하나가 틱 전체를 막지 않는다) 재전달본을 걷는다(종전엔 스풀에 영구 잔류).
> ⑶ **시각** — `_read_netcdf` 가 `instant` 를 받기만 하고 안 썼다. 정확 일치로 고르고 캐시 키에 실었다. 격자 digest 는 세 통계에서 값 표본으로 강화.
> ⑷ **보관** — 만료 뒤에만 축출(완료 시점 아님 — 타일·스크린샷이 메모리를 읽는다), 묘비로 410 유지·개수 상한, `_produced_for` 를 대상별 색인으로. 스크린샷 층 상한 8 = 선언된 400 + `details.maxLayers`.
> ⑸ 비밀값 `_FILE` 간접참조(core-api 와 같은 규칙 · 손사본은 codegen 통일 후보).
>
> 계수 — `pytest -m "not e2e and not perf"` **199 → 250 passed**(신설 45 · 개정 1 · 기존 실패 0). 게이트 `import-boundary`·`banned-import` green. `render-latency`·`e2e-format-coverage` 는 **red(준비 · `COLAB_REFERENCE_DATA` 미선언)** 로 `[미확인]`.
> 계약 개정 0건 — 델타 초안 셋(경계 헤더 선언 · `getRender` 의 400 · `layers.maxItems`)은 `CODE-REVIEW-20260903-C.md §3`.
