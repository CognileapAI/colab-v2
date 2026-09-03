# CODE-REVIEW-20260903-F — 레인 F `follow-ups` 집행 기록

> 근거 — 레인 A~E 수용 검토가 남긴 **작은 후속 6건**. 델타 초안의 출처는
> `dev-package/sessions/CODE-REVIEW-20260903-B.md` §7 ⑦·⑧ · 같은 문서 §4-㉲ · 레인 D 기록.
> 기준 — `lane-review-clean` `ad2fe06`(레인 A~E 병합 후 통합 트리). 브랜치 `worktree-agent-a992b5e50a78fd047`.
> **push 없음 · 병합 없음 · 대장 번호 발급 없음.**
> 경로 표기 — 레포 루트 기준. 위치는 **앵커 문자열**로 적는다(행 번호는 밀린다).

## 1. 계수 — 전/후

| 무엇 | 기준선(`ad2fe06` 실측) | 이번 회차(변경 후) | 어떻게 쟀나 |
|---|---|---|---|
| pipeline-worker `-m "not e2e and not dbint"` | 225 passed · 46 deselected · 0 failed | **231 passed · 46 deselected · 0 failed** | `services/pipeline-worker/.venv/bin/python -m pytest -q -m "not e2e and not dbint"` |
| viz-render `-m "not e2e and not perf"` | 259 passed · 40 deselected · 0 failed | **269 passed · 40 deselected · 0 failed** | `services/viz-render/.venv/bin/python -m pytest -q -m "not e2e and not perf"` |
| ai-service `-m "not dictdb"` | **125 passed** · 26 deselected · 0 failed | **130 passed** · 26 deselected · 0 failed | `services/ai-service/.venv/bin/python -m pytest -q -m "not dictdb"` |
| 게이트 `selftest` (`COLAB_GATE_JOBS=1`) | 선언 19 · 실행 17 · 면제 2 / green 15 · red(판정) 0 · red(준비) 2 | **선언 19 · 실행 17 · 면제 2 / green 15 · red(판정) 0 · red(준비) 2** | `COLAB_GATE_JOBS=1 ./gates/run.sh selftest` |
| 게이트 `service-tests-selftest` | 9케이스 전건 기대대로 · rc 0 | **9케이스 전건 기대대로 · rc 0** | `./gates/run.sh service-tests-selftest` |
| 게이트 `stage2-markers` | — | **수집 80 · skipped 0 · failed 0 · errors 0** | `./gates/run.sh stage2-markers` |
| 게이트 `import-boundary` | — | **계약 8 kept · 0 broken · green** | `./gates/run.sh import-boundary` |
| 게이트 `banned-import` | — | **`.py` 127건 · 금지 import 0 · green** | `./gates/run.sh banned-import` |

### ㈎ 지시문의 ai-service 기준값과 실측이 갈렸다 — **기준이 달랐다**

- 지시문 기준선 = 「≈94」. **이 트리의 실측 = 125**. 값을 지우지 않고 시점·단위를 붙인다.
- 갈린 이유 — 레인 D 기록 §1 의 「94」는 **6파일을 `--ignore` 한 부분집합**이다
  (`CODE-REVIEW-20260903-D.md` §1 「ai-service DB 없는 부분집합(6파일 제외)」).
  이번 값은 **표식 선택자 `-m "not dictdb"`** 로, 그 6파일 중 DB 없이 도는 함수까지 센다.
  어느 쪽이 틀린 것이 아니라 **세는 단위가 다르다.**
- 이번 회차의 판정 기준은 `-m "not dictdb"` 하나다 — 게이트(`service-tests-ai-service`)가 쓰는 선택자와 같다.

### ㈏ `selftest` 의 red(준비) 2건은 **기준선과 같고 이 회차와 무관하다**

- `frontend-typecheck-selftest` · `frontend-test-selftest` — `frontend/node_modules` 부재.
- **「main 과 같다」를 수용 근거로 쓰지 않는다**(`CLAUDE.md`). 여기서 적는 것은
  「이 회차가 만든 red 가 아니다」까지이고, **여전히 red 다** — 푸는 법은 `frontend/` 에서 `npm ci`.
- 이 회차가 만든 red: **0건.**

## 2. 항목별 — 변경 · 시험 · 전후

### ⑴ `DATA_ERRORS` 를 좁힌다 — 맨 `ValueError`·`IndexError` 제거

- **자리** — `services/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py:DATA_ERRORS`
  (앵커 `#: **파일 내용이 이상한 것** — 배관이 깨진 것이 아니다`).
  소비처는 `services/pipeline-worker/src/colab_pipeline/app/worker.py:drive_uploads`
  의 `except DATA_ERRORS as e:`.
- **무엇이 있었나** — 집합에 맨 `ValueError`·`IndexError` 가 들어 있었다. 두 형은
  **프로그래밍·설정 결함의 형이기도 하다** — 같은 모듈의 원장 불변식 둘
  (`d5_ingestion.py` 의 `raise ValueError("축이 빈 기준 격자 파일 행을 만들지 않는다 (〈66〉)")` ·
  `raise ValueError(f"업로드 상태에 없는 열: {sorted(bad)}")`)과 `kernel/storage_layout` 의
  설정 오류가 전부 `ValueError` 다. 그것이 여기 잡히면 **업로드마다 영구 실패
  `내부 오류`／`영구` 가 원장에 적히고**, 사람에게 남는 단서는 `print` 한 줄이다 —
  고칠 수 있는 결함이 「그 파일이 이상했다」로 굳는다.
- **무엇을 했나** — 형이 있는 D5 예외 5종(`AxisUndeterminedError`·`GridUnavailableError`·
  `HsrParseError`·`ParseError`·`CogConversionError`)은 그대로 두고, 맨 두 형을 빼고
  **numpy 전용 형과 `struct.error`** 를 넣었다 —
  `np.exceptions.AxisError`(`ValueError`·`IndexError` 의 자식이지만 numpy 전용) ·
  `np.linalg.LinAlgError` · `struct.error`(`d5/detect.py`·`d5/hsr.py`·`d5/tiff_probe.py` 가
  `struct` 로 헤더를 읽는다). **좁힌 것이지 줄인 것이 아니다.**
- **시험** — `services/pipeline-worker/tests/test_worker_data_error_isolation.py`
  - 레인 D 가 주입하던 맨 `ValueError("배열 형상이 이상하다")` →
    `GridUnavailableError("기준 격자를 못 세운다")` 로 교체
    (앵커 `test_실패한_업로드를_다음_바퀴가_다시_집지_않는다`).
  - 신규 `test_맨_ValueError_는_데이터가_아니라_배관이라_그대로_올라온다` — 원장 불변식의
    실제 문구를 주입해 **`pytest.raises(ValueError)`** 이고 `failed_at is None` 임을 잠근다.
  - 신규 `test_맨_IndexError_도_그대로_올라온다`.
  - 신규 `test_numpy_전용_예외는_데이터_오류로_잡힌다` — **줄이지 않았다는 증명.**
- **전/후** — 전: 신규 2건이 `DID NOT RAISE` 로 red. 후: 전건 green. pipeline-worker 231 passed.
- **`record_data_failure` 의 로깅 채널** — **그대로 두었다.** 실측 결과 이 단위의 로깅
  채널은 `print` 하나다: `app/worker.py` 3자리(`103`·`255`·`364` 인근) ·
  `domains/d5_ingestion.py` 릴레이 1자리. `logging` 은 이 단위에 **한 자리도 없다.**
  `record_data_failure` 의 메시지는 이미 `worker.py` 의 `print(f"upload.failed — ...")`
  로 나가므로 **다른 것들과 같은 채널**이다. 지시문의 「`print` 면 두고 적는다」를 따랐다.

### ⑵ 홀로 있는 1차원 격자의 거절 사유 — 「짝 불일치」 → 「축 판별 실패」

- **자리** — `services/pipeline-worker/src/colab_pipeline/d5/axis.py:detect_axes_for_upload`
  (앵커 `# ── 남은 거절에 **구조화된 사유**를 붙인다`).
- **무엇이 있었나** — 사유 판정이 `REASON_AXIS_UNDECIDED if len(members) == 2 else
  REASON_PAIR_MISMATCH`. 1차원 `.npy` 는 `_read_npy` 가 판별 실패로 바꾸므로 `stats` 에
  들어가지 못하고 → `shape is None` → `members = []` → **「짝 불일치」** 로 떨어졌다.
- **왜 고쳐야 하나** — 사유 3값(`contracts/schemas/common.json#GridRejectionReason`)은
  사람이 읽고 **다음 행동을 고르는 값**이다. 「짝 불일치」는 「짝을 맞춰 다시 올려라」로
  읽히는데, 1차원 격자는 짝을 붙여도 서지 않는다. 원인은 처음부터 끝까지 축 판별이다.
- **무엇을 했나** — 조건을 `REASON_AXIS_UNDECIDED if shape is None or len(members) == 2`
  로 바꿨다. **형상을 읽었는데 같은 형상이 2건이 아닌 경우는 그대로 「짝 불일치」다** —
  그 자리는 실제로 짝의 문제다. 계약 변경 0(세 값 중 이미 있는 값으로 옮겼을 뿐).
- **시험**
  - 레인 D 가 못 박아 둔 것 수정 —
    `tests/test_worker_data_error_isolation.py:test_1차원_격자_업로드가_틱을_죽이지_않는다`
    의 `assert [...] == ["짝 불일치"]` → `["축 판별 실패"]`.
  - `tests/test_axis_data_errors.py` 신규 3건 —
    `test_홀로_있는_1차원_격자의_사유는_축_판별_실패다`(고침) ·
    `test_짝이_없는_2차원_격자는_여전히_짝_불일치다`(**줄이지 않았다는 증명**) ·
    `test_같은_형상_2건인데_못_갈린_것은_축_판별_실패다`(종전 동작 유지).
- **전/후** — 전: 2건 red(`'짝 불일치' != '축 판별 실패'`). 후: 전건 green.

### ⑶ ai-service — `degradedReason` 의 원시 예외 제거 (레인 B §7 ⑦ 델타)

- **자리(실측)** — 레인 B 가 지목한 두 파일 중 실제 누출은 **한 자리**였고,
  **형제가 다른 파일에 하나 더** 있었다.
  - `services/ai-service/src/colab_ai/domains/d10_ai_services.py:SearchService.search`
    — `except Exception as e:` 뒤 `reason = reason or f"온톨로지 사전을 읽지 못해 ... : {e}"`.
      사전은 DB 에서 읽으므로(`app/dictionaries.SqlDictionaries`) 이 `{e}` 는 대개 psycopg
      접속 예외이고, 그 문구에는 **호스트·주소·포트·롤**이 들어 있다.
  - **형제** `services/ai-service/src/colab_ai/app/interpret.py:LlmQueryInterpreter.interpret`
    — `f"질의 해석 모델에 닿지 못했다({e}) — ..."`. urllib 예외라 **내부 주소·포트**를 담고,
      이 문구는 `Interpretation.degraded_reason` → `SearchService` → **같은 `degradedReason`
      칸**으로 나간다. 한쪽만 고치면 나머지가 그대로 남는다(`CLAUDE.md §4` 「형제를 찾는다」).
  - ⚠ **`d10_suggestion.py:164` 는 누출 자리가 아니었다.** 그 줄은
    `body["degradedReason"] = reason` 이고 `reason` 은 `empty_declaration` 에서 온다.
    유일한 호출자(`app/main.py`)가 **상수 문자열**을 넘긴다 — 원시 예외가 여기 닿는 경로가
    이 트리에 없다. **지어내 고치지 않았다.** 이 자리에 손댈 근거가 생기면 그때 연다.
- **무엇을 했나** — 응답 사유를 **안정된 문구 상수**로 고정하고 원시 예외는 **서버 로그로만** 보낸다.
  - `d10_ai_services.DICTIONARY_UNAVAILABLE_REASON` = 「온톨로지 사전을 읽지 못해 질문의
    낱말 그대로 찾았다.」 · 로그 `event=search.dictionary.unavailable labId=… exc=…`.
  - `interpret.MODEL_UNREACHABLE_REASON` = 「질의 해석 모델에 닿지 못했다 — 질문의 낱말
    그대로 찾았다.」 · 로그 `event=search.interpreter.unreachable exc=…`.
  - 로거 이름은 `colab_ai.degraded` 하나(`DEGRADED_LOGGER`/`INTERPRETER_LOGGER`).
    규약(로거 이름·`event=`·사유)은 core-api `app/relay.py:_record_suggest_failure` 의 것을
    그대로 쓴다. **계약 변경 0** — `degradedReason` 은 자유 문자열이다(`core-ai.yaml Degradable`).
  - ⚠ **이 단위에는 `logging` 이 한 자리도 없었다** — 이번에 처음 선다(`print` 도 없었다).
- **시험 (DB 없음)**
  - `services/ai-service/tests/test_search_service.py` 신규 3건 — 실물 무늬 psycopg 문구
    (`connection to server at "…" (…), port 5432 failed: FATAL: …`)를 던지는 대역 사전으로
    ① 사유 칸에 누출 문자열 5종이 없고 상수와 같다 ② **봉투 전체를 직렬화해도** 없다
    (다른 칸으로 새는 것을 막는다) ③ 원시 예외는 `caplog` 에 남는다.
  - `services/ai-service/tests/test_query_interpreter.py` 신규 2건 — 형제 자리에 같은 세 축.
- **전/후** — 전: import 단계에서 red(상수 부재). 후: ai-service 130 passed.

### ⑷ viz-render — 투영 밖 좌표는 500 이 아니다 (레인 B §7 ⑧ 델타)

- **자리** — `services/viz-render/src/colab_viz/domains/d7_visualization/value_lookup.py:read_point`
  (앵커 `xs, ys = warp_transform("EPSG:4326", ds.crs, [lon], [lat])`).
- **무엇이 있었나** — LCC 처럼 평면 전체를 덮지 않는 투영에서 정의역 밖 좌표를 넣으면
  proj 가 거절한다. **실측(2026-09-03 · rasterio 1.5.1)** — `+proj=lcc +lat_1=30 +lat_2=60
  +lat_0=38 +lon_0=126` 래스터에 위경도 `(-90.0, 0.0)` 을 주면
  `rasterio._err.CPLE_AppDefinedError: Point outside of projection domain`. 그 예외가 그대로
  올라가 표면이 **500** 을 냈다 — 화면은 「서버 오류」를 띄우고 그 요청은 장애 계수에 섞인다.
- **무엇을 했나** — `warp_transform` ＋ `ds.index` 두 줄을 `try` 로 감싸고 변환 예외에서
  `LookupOutcome(available=False, unavailable_reason=OUT_OF_RANGE,
  exactness=_exactness(used_reference_grid))` 를 돌려준다. **같은 파일 아래쪽의 격자 밖
  분기와 답이 같아졌다** — 같은 사실에 두 답을 두지 않는다.
  **계약·스키마 변경 0** — `OUT_OF_RANGE = "범위 밖이다"` 상수와
  `core-viz.yaml ValueLookupResult.unavailableReason` enum 이 이미 있었다.
- **잡는 예외를 어떻게 정했나** — `_transform_errors()` 로 `rasterio.errors.RasterioError`
  ＋ `rasterio._err.CPLE_BaseError` 를 모은다. ⚠ `CPLE_*` 는 **공개 이름이 없다**
  (`rasterio.errors` 는 `RasterioError`·`RasterioIOError`·`TransformError`·`WarpOperationError`
  만 노출 · 1.5.1 실측). 사설 모듈이 없는 판에서는 `ImportError` 를 받아 `RasterioError`
  하나로 두고 **지어내지 않는다** — 못 잡은 것은 500 으로 올라가 눈에 띈다.
  `Exception` 으로 넓히지 않았다.
- **비대상 실측** — `ds.index(inf, inf)` 는 예외가 아니라 `(-2147483648, -2147483648)` 을
  돌려주므로 **기존 `0 <= row < ds.height` 분기가 이미 잡는다.** 그 갈래에 손대지 않았다.
- **시험** — `services/viz-render/tests/test_value_lookup.py` 신규 4건
  - `test_투영_밖_좌표는_500_이_아니라_사유가_붙은_없다다` — LCC 픽스처 · 단위 수준.
  - `test_투영_밖_좌표가_먼저_예외로_터지는지_확인한다` — **픽스처가 실제로 그 갈래를 밟는지**
    날것 rasterio 로 확인한다(밟지 않으면 위 시험은 대상 0건 green 이다).
  - `test_투영_밖_좌표에_표면이_200_으로_답한다` — HTTP 200 ＋ `unavailableReason: 범위 밖이다`.
  - `test_투영_안_좌표는_여전히_값을_돌려준다` — **줄이지 않았다는 증명.**
- **전/후** — 전: 2건이 `CPLE_AppDefinedError` 로 red. 후: viz-render 269 passed.

### ⑸ viz-render 토큰 공백 처리 — **이미 동일했다. 시험으로 못 박았다.**

- **실측** — `services/viz-render/src/colab_viz/kernel/config.py:resolve_env_or_file` 과
  `services/core-api/src/colab_core/kernel/config.py:resolve_env_or_file` 의 **본문을 기계로
  대조**했다(독스트링·빈 줄 제외). 차이는 **둘뿐이고 의미가 아니다** —
  줄바꿈 위치와 `pathlib.Path` ↔ `Path`. 두 곳 다 생 env 는 `.strip()`, 파일은 `rstrip()`.
- **판정** — 레인 B §4-㉲ 가 적은 「core-api 만 strip 한다」는 **레인 C 의 손사본이 서면서
  이미 닫혔다.** 이 회차에 **코드 변경 0.** 지어내 고치지 않는다.
- **무엇을 했나** — 그 사실이 흐트러지는 날을 잡는 시험을 넣었다.
  `services/viz-render/tests/test_secret_from_file.py` 신규 6건(파라미터 2×3) —
  ① 생 env 앞뒤 공백은 벗겨진다(`"  tok\n"` → `"tok"`) ② 파일은 **끝의 공백만** 벗긴다
  (`"  tok  \n"` → `"  tok"` — 규칙이 다른 것이 의도임을 이름으로 갈라 둔다)
  ③ 공백뿐인 생 env 는 `None`(배선 안 됨 · 503) — 빈 문자열 토큰이 서면 401 과 503 이 섞인다.
- **red 증명** — 시험이 무엇을 잡는지 확인했다. `direct = (env.get(name) or "").strip()`
  에서 `.strip()` 을 떼자 **4건이 red**(`'  tok\n' == 'tok'` · `'   ' is None`).
  되돌린 뒤 `git diff` 0 확인.
- ⭑ **손사본이라는 사실을 기록에 남긴다** — 같은 함수가 두 단위의 `kernel/config.py` 에
  두 벌로 산다. 배포 단위 독립(`CLAUDE.md §3-1`) 때문에 공유 라이브러리로 빼지 않는 것이
  규율이므로, **이 중복을 없애는 것은 codegen 통일 작업항목의 몫이다**
  (`CODE-REVIEW-20260903-PLAN.md §4` 유보 1 — `ids.py`·`errors.py` 와 같은 묶음).
  그 항목이 이 자리를 **흡수해야 한다.**

### ⑹ 게이트 — `_expect.sh` 의 rc 0 구멍 (필수)

- **자리** — `gates/tools/_expect.sh:expect_classify`.
- **무엇이 있었나** — 준비 갈래의 조건이 `[ "$rc" = 78 ] || 출력에 표식이 있으면` 이라
  **종료코드를 보지 않고 표식만으로** 접었다. 그래서 **표식을 찍고 종료 0 으로 나가는
  검사기**가 `ready`(`cause=입력미선언` 이면 `미선언`)로 분류됐다. 그 조합의 뜻은
  「검사기가 자기 입으로 못 돌았다고 적어 놓고 실행기에는 다 됐다고 말했다」이고,
  **그것 자체가 결함**인데 분류기가 그것을 「환경이 없어 못 돌았다」로 바꿔 적었다 —
  그 상태에서는 red 를 기대한 케이스가 「red(준비) OK」로 세어져 **판정된 적 없는 보호
  장치가 증명된 것처럼** 보인다(`CLAUDE.md §4` green-by-skip 의 분류기판).
- **무엇을 했나** — 조건을 `[ "$rc" = 78 ] || { [ "$rc" != 0 ] && 표식 }` 로 좁혔다.
  종료 0 은 무슨 말을 찍었든 `green` 이다. **좁힌 것이지 줄인 것이 아니다** —
  진짜 준비 실패(78 · 비영＋표식)는 종전 그대로 갈린다.
- **픽스처 — 왜 `backup-cron-streak-selftest.sh` 안에 있나** — `_expect.sh` 는 게이트가
  아니라 **모든 셀프테스트가 source 하는 판정부**라 자기 게이트 자리가 없고,
  `gates/run.sh ALL_GATES` 는 이 회차의 편집 면 밖이다. 그것을 source 하는 셀프테스트
  안에 두면 `selftest` 묶음이 이 증명을 **매번** 돈다.
- **시험** — `gates/tools/backup-cron-streak-selftest.sh` 신규 8케이스(ⓘ~ⓟ). 게이트 8건은 그대로.
  - **가짜 검사기 실물** — 표식을 `echo` 하고 `exit 0` 하는 스크립트를 `$TMP` 에 짓고
    그 종료코드·출력으로 분류한다(ⓘ).
  - ⓘ 표식＋0 → green · ⓙ 표식(`cause=입력미선언`)＋0 → green
    (**`want=미선언` 케이스가 rc 0 이면 이제 어긋나 red 다**) ·
    ⓚ 78 → ready · ⓛ 78＋`cause=입력미선언` → 미선언 · ⓜ 표식＋1 → ready ·
    ⓝ 표식 없음＋1 → red · ⓞ 표식 없음＋0 → green.
  - ⓟ **그리고 셀프테스트가 그 케이스에서 실제로 red 로 간다** — 부분 셸에서
    `expect_intercept_readiness … ready` 가 **가로채지 않고** `EXPECT_READINESS` 도 비는지 본다.
    가로채면 「판정 못 함」 면제를 받아 red 가 안 뜬다.
- **전/후** — 전: **ⓘ·ⓙ·ⓟ 3건 red**(`분류가 「ready」다(기대 「green」)` 외), ⓚ~ⓞ 5건은
  이미 green(= 좁히기가 기존 갈래를 건드리지 않았다는 증명). 후: 16건 전건 green.

#### ⑹-㉮ 선택 항목 ⓐ — 세 셀프테스트의 `FAILED=1` 한 줄 제거 (**했다**)

- **자리** — `gates/tools/backup-cron-streak-selftest.sh` ·
  `gates/tools/e2e-format-coverage-selftest.sh` · `gates/tools/render-latency-selftest.sh`
  의 `expect()` 안 `[ "${#EXPECT_READINESS[@]}" -eq 0 ] || FAILED=1`.
- **왜** — 이 줄이 서면 아래 `[ "$FAILED" -ne 0 ] && exit 1` 이 먼저 걸려 종료가
  **1(판정 red)** 이 되고, 준비 실패를 말하는 `expect_readiness_verdict`(종료 78)까지 못 간다.
  실행기는 1 을 「셀프테스트가 게이트의 결함을 찾았다」로 세므로 **「고칠 결함」과
  「환경이 없다」가 다시 섞인다** — `_expect.sh` 가 갈라 놓은 것을 이 한 줄이 도로 접었다.
  **어느 쪽이든 red 다** — 색이 아니라 사유가 바뀐다.
- **전/후** — 세 셀프테스트 전부 green 유지(16건 · 11건 · 12건).

#### ⑹-㉯ 선택 항목 ⓑ — `gates/README.md` 의 「선언 19」 (**했다**)

- **자리** — `gates/README.md` §자기 증명 표의 `selftest` 행.
- **무엇을 했나** — 하드코딩 「선언 19 = 실행 17 ＋ 명시 면제 2」를 지우고
  **`ALL_GATES` 의 `*selftest` 전부 ＋ 명시 면제 2** 로 적었다. 원문은 지우지 않고 취소선
  인용으로 남겼다(개정 표시 · `CLAUDE.md §7`). 「세는 명령은 게이트의 요약줄이지 이 표가
  아니다」를 명령줄과 함께 박았다 — 셀프테스트를 하나 더하는 순간 숫자가 조용히 낡는 자리였다.

## 3. 멈춘 항목 — **없다.** 다만 두 자리는 「고칠 것이 없었다」다

| 지시 항목 | 판정 | 근거 |
|---|---|---|
| ⑶ `d10_suggestion.py` 의 `degradedReason` | **누출 자리 아님 — 손대지 않았다** | `reason` 은 `empty_declaration` 에서 오고 유일한 호출자(`app/main.py`)가 상수를 넘긴다. 원시 예외가 닿는 경로가 이 트리에 없다 |
| ⑸ viz 토큰 공백 처리 | **이미 동일 — 코드 변경 0** | 두 `resolve_env_or_file` 본문 기계 대조 결과 차이는 줄바꿈과 `Path` 별칭뿐. 시험으로 못 박고 손사본 사실을 §2-⑸ 에 남겼다 |
| ⑴ `record_data_failure` 로깅 채널 | **`print` 그대로 — 지시문의 단서 그대로** | 이 단위의 로깅 채널이 `print` 하나이고(`logging` 0자리) 이 메시지는 이미 같은 채널로 나간다 |

- `./gates/run.sh all` 은 **돌리지 않았다**(지시 금지).
- 운영 스택(`colab_v2_staging_*`)에 **한 글자도 닿지 않았다.** 일회용 Postgres도 **띄우지 않았다** —
  이번 항목 전부가 DB 없이 판정된다.

## 4. `[미확인]`

1. **`dbint` 를 안 돌렸다** — `-m "not e2e and not dbint"` 로만 쟀다. ⑴ 이 건드린
   `DATA_ERRORS` 는 `test_worker_data_error_dbint.py` 가 실 DB 로 다시 보는 자리다.
   그 파일의 `record_data_failure(work, ValueError(...))` 한 줄은 **`DATA_ERRORS` 분류가
   아니라 `detail` 문구 형식**을 재는 자리라 그대로 두었다 — 그 판단을 실 DB 로 확인하지 않았다.
   → 푸는 법 — `COLAB_PIPELINE_DB_URL` 을 일회용 인스턴스로 걸고 `-m dbint` 를 돈다.
2. **`e2e`·`perf` 표식은 이 회차에도 안 돌렸다** — 원천 마운트·성능 환경 부재.
   → 푸는 법 — `COLAB_REFERENCE_DATA` 를 마운트하고 같은 명령을 다시 돈다.
3. **`frontend-*-selftest` 2건을 못 돌렸다** — `frontend/node_modules` 부재(기준선과 동일).
   → 푸는 법 — `frontend/` 에서 `npm ci`.
4. **⑷ 의 500 → 200 전환을 실서버에서 안 봤다** — TestClient 로만 쟀다.
   중계하는 core-api 가 이 200 을 어떻게 통과시키는지는 레인 B 기록의 서술(`dc26829` 이후
   그대로 통과)로만 알고 **요청 하나로 확인하지 않았다.**
5. **⑶ 의 실제 유출 값을 실서버 응답으로 재지 않았다** — 대역 사전이 던지는 psycopg
   **모양의** 문구로만 쟀다. 진짜 접속 실패 문구가 다른 필드로 새는 경로는 안 봤다.
6. **⑹ 의 rc 0 구멍이 실제로 어느 셀프테스트에서 발화한 적이 있는지 안 셌다.** 고친 것은
   분류기이고, **그 구멍을 밟는 검사기가 지금 레포에 있는지는 세지 않았다.**
   → 푸는 법 — 전 셀프테스트를 돌려 `expect_classify` 가 `rc=0 ＋ 표식`을 받는 횟수를 센다.
7. **`_expect_pool.sh`(병렬판)를 병렬로 안 돌렸다** — 같은 `_expect.sh` 를 source 하므로
   분류기 변경이 그대로 적용되지만, 판정은 `COLAB_GATE_JOBS=1` 에서만 확인했다.
   (병렬도 높은 단발 결과를 병합 근거로 쓰지 않는 규율과 같은 이유로 1 을 골랐다.)

## 5. 이번에 세지 않은 판단기준 (다음 회차 진입조건)

1. **core-api 의 같은 계열 누출 2자리** — `app/relay.py` 의
   `honest_empty_suggestions(reason=f"... {e}")` · `unreadable_interpretation(f"... {e}")`
   가 urllib 예외 문자열을 `degradedReason`/`unavailableReason` 으로 실어 보낸다
   (레인 B §7 ⑦ 이 이미 지목). **이 회차의 편집 면 밖이라 손대지 않았다** — ⑶ 이 ai 쪽
   두 자리를 닫았으므로 **남은 것은 core 쪽 둘이다.**
2. **`RequestValidationError` 의 `str(exc.errors())`** — viz 와 core-api 양쪽에 같은 모양이
   있다(레인 B §7 ⑨). 들어온 값 원문이 브라우저까지 간다. 이번 회차 항목 밖.
3. **`kernel/config.resolve_env_or_file` 손사본 2벌** — §2-⑸ 참조. codegen 통일 항목이
   흡수해야 한다. 지금은 **시험 하나가 두 벌의 일치를 지키고 있을 뿐**이다.
4. **`ownership.scan()`·`grade()` 가 `tile-` 벌을 안 본다** — `value_lookup.py` 머리말이
   스스로 적어 둔 별건. ⑷ 가 그 자리를 건드리지 않았다.

## 6. 대장 등재문 초안 — **번호 없음** (발급은 오케스트레이터)

> **코드리뷰 후속 6건 — 데이터 오류의 경계·응답 사유·검사기 분류를 좁힌다.**
> 파이프라인 워커가 「데이터 오류」로 삼키던 집합에서 맨 `ValueError`·`IndexError` 를 뺐다 —
> 원장 불변식과 저장 배치 설정의 결함이 업로드마다 영구 실패 `내부 오류` 로 굳고 단서는
> 로그 한 줄뿐이던 자리다. numpy 전용 형과 헤더 판독 오류는 그대로 데이터 오류로 남는다.
> 홀로 올라온 1차원 기준 격자의 거절 사유를 「짝 불일치」에서 「축 판별 실패」로 옮겼다 —
> 짝을 붙여도 서지 않는 파일에 「짝을 맞춰 다시 올려라」로 읽히는 사유가 나가고 있었다.
> AI 서비스가 사전·해석 모델 고장을 알릴 때 응답에 싣던 원시 예외 문구를 고정 문구로 바꾸고
> 원인은 서버 로그로 옮겼다 — 데이터베이스 접속 실패 문구에는 호스트·포트·롤이 들어 있고
> 그것이 응답 본문으로 나가고 있었다. 렌더 서비스의 값 조회는 투영 정의역 밖 좌표에
> 서버 오류 대신 「범위 밖이다」를 200 으로 답한다 — 같은 파일의 격자 밖 분기와 답이 같아졌다.
> 셀프테스트 판정부는 종료코드를 먼저 본다 — 「못 돌았다」 표식만 찍고 정상 종료한 검사기를
> 준비 실패로 접던 자리라, 판정된 적 없는 보호 장치가 증명된 것처럼 세어지고 있었다.
> 검사기 목록 문서의 하드코딩된 건수는 목록 자체에서 나오는 표현으로 바꿨다.

## 7. 커밋

| sha | 제목 |
|---|---|
| `bb124aa` | 파이프라인 워커 — 데이터 오류 집합을 좁히고 1차원 격자 거절 사유를 바로잡는다 |
| `6849f50` | AI 서비스 — 원시 예외를 응답 사유에서 빼고 서버 로그로 옮긴다 |
| `8909677` | 렌더 서비스 — 투영 밖 좌표에 200 과 사유로 답하고, 토큰 공백 처리를 시험으로 못 박는다 |
| `25800d2` | 셀프테스트 판정부 — 종료코드를 먼저 본다, 표식만으로 준비 실패로 접지 않는다 |
| (이 기록) | 레인 F 집행 기록 |

- 브랜치 `worktree-agent-a992b5e50a78fd047` · 기준 `ad2fe06`. **push 없음 · 병합 없음.**
