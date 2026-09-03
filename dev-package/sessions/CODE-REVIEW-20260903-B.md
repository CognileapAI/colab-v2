# CODE-REVIEW-20260903-B — 레인 B `core-api` 실행 기록

> 근거 — `dev-package/sessions/CODE-REVIEW-20260903.md`(#5·#7·#8·#10·#12·#15 + 부록) ·
> `dev-package/sessions/CODE-REVIEW-20260903-PLAN.md` §1·§2 B 행.
> 편집 면 — `services/core-api/**` 만. 계약·스키마·compose·infra·타 서비스·프론트 편집 0.
> 브랜치 — `worktree-agent-ac72b799fc10afb59` (기준 `lane-review-clean` `d4d11b5`). push 없음.
> 수용 검토 반영 회차 — 브랜치 `worktree-agent-a5a9e4423c858ed14`
> (`bfa50c5` 위에 `9b4004b` · `0a78b76` + 이 기록). 편집 면 동일. push 없음. **§10 참조.**

## 1. 계수 — 전/후

| 시점 | passed | failed | skipped | deselected | 시간 |
|---|---|---|---|---|---|
| 기준선(무수정 트리) | 553 | 5 | 0 | 0 | 108.58s |
| 종료(전체) | 614 | 5 | 0 | 0 | 116.11s |
| 종료(`-m "not e2e"`) | 613 | 0 | 0 | 6 | 100.48s |
| **수용 검토 반영 회차 기준선**(`-m "not e2e"`) | 613 | 0 | 0 | 6 | 100.52s |
| **수용 검토 반영 회차 종료**(`-m "not e2e"`) | **620** | **0** | 0 | 6 | 91.13s |

- 계수 기준 — `services/core-api` 에서 일회용 Postgres 1대(`--rm` · tmpfs · `PGDATA` 지정 ·
  호스트 포트 미공개 · 이름 `laneB_pg_rc`)에 붙여 `pytest -q` 전체. 병렬도 1. 측정 2026-09-03.
- 수용 검토 반영 회차의 두 줄은 **별도 일회용 Postgres**(같은 규칙 · 이름 `laneBfix_pg`)에서
  `-m "not e2e"` 로만 쟀다. 전체(`e2e` 포함) 계수는 이 회차에 **재지 않았다** —
  `COLAB_REFERENCE_DATA` 원천 마운트가 여전히 없다(§8-3). 늘어난 7건은 §10 참조.
- **신규 시험 61건** — 전부 실패 먼저 확인 후 수정.
- **기존 실패 5건은 이 레인이 만든 것이 아니고 고치지도 않았다** —
  `tests/test_e2e_s3_real.py` 전건, 사유 `COLAB_REFERENCE_DATA` 원천 마운트 부재.
  이 파일은 「E2E 는 skip 하지 않는다」를 스스로 못 박아 마운트 없으면 fail 이 정상 동작.
  `-m "not e2e"` 로 빼면 0 failed.

## 2. 게이트 — 실측

| 게이트 | 결과 | 계수 |
|---|---|---|
| `./gates/run.sh import-boundary` | green | 계약 8 kept · 0 broken |
| `./gates/run.sh banned-import` | green | `.py` 127건 · 금지 import 0 (core-api deny 18) |
| `./gates/run.sh ai-no-lineage-write` | green | 계약 3 · ai 텍스트 29 · 마이그레이션 29 |
| `./gates/run.sh db-boundary` | green | 단위 7 · 스캔 270건 · 위반 0 |

`./gates/run.sh all` 은 지시대로 돌리지 않았다.

**수용 검토 반영 회차 재실측**(2026-09-03 · 커밋 `0a78b76` 시점) — 세 게이트를 다시 돌렸고
계수가 같다. `ai-no-lineage-write` 는 이 회차에 **안 돌렸다**(지시 항목 밖).

| 게이트 | 결과 | 계수 |
|---|---|---|
| `./gates/run.sh import-boundary` | green | 계약 8 kept · 0 broken |
| `./gates/run.sh banned-import` | green | `.py` 127건 · 금지 import 0 (core-api deny 18) |
| `./gates/run.sh db-boundary` | green | 단위 7 · 스캔 270건 · 위반 0 |

## 3. 커밋 (오래된 순)

| sha | 항목 | 비고 |
|---|---|---|
| `b7ad4f7` | 입력오류 400 · IntegrityError 409 · 가드 5 (#12) | |
| `6d44f64` | `update_project` 기간 date 변환 (#7) | |
| `dc26829` | relay 4xx 통과 · 위경도 범위·bool · 경계 헤더 고정 (#8) | **계약 델타 필요** — §6 |
| `f634948` | 로그인 제한 두 버킷 · `throttle` 무쓰기·정리 (#5) | **Ted 판정 대기** — §5 |
| `a91de2b` | `_FILE` — 세션 비밀값·viz 토큰 (#15) | **Ted 판정 대기**(compose) — §5 |
| `4599ab5` | 거절 격자 미저장 (부록) · `not_implemented` 계수 (부록) | 업로드 **동작 시험 5건 전부**가 여기 |
| `9aed645` | 업로드 3라우트 `def` + 스트리밍 (#10) | ⚠ **병합 시 떼어낼 수 있는 커밋** · 더하는 시험은 `ast` 1건뿐 |
| `bfa50c5` | 이 기록 | |
| `9b4004b` | 클라이언트 버킷 열쇠 = 마지막 홉 · 상한 초과 고정 버킷 (#5 수용 검토) | §10-㈎ |
| `0a78b76` | `IntegrityError` 를 SQLSTATE 로 가른다 (#12 수용 검토) | §10-㈏ |
| (마지막) | 이 기록의 수용 검토 반영 | |

`9aed645` 는 핫 파일(`routes/ingestion.py`)을 크게 만지므로 **단독 커밋으로 격리**했다.

**⚠ 정정 (수용 검토)** — 종전 이 자리에 「떼어내도 앞 커밋의 **바이트 무결성 시험 3건**이
남는다」고 적었다. 실측하면 두 커밋의 경계가 다르다 —

| 커밋 | `tests/test_upload_streaming.py` 안의 시험 |
|---|---|
| `4599ab5` | `..._rejected_grid_file_never_lands_on_disk` · `..._accepted_body_file_still_lands_on_disk` · `..._multi_megabyte_upload_is_written_byte_for_byte` · `..._two_files_in_one_upload_do_not_bleed_into_each_other` · `..._replacing_a_grid_file_streams_too` — **동작 시험 5건 전부** |
| `9aed645` | `..._upload_routes_do_not_read_whole_files_into_memory` — **`ast` 구조 시험 1건뿐** |

즉 `9aed645` 를 떼어내면 없어지는 시험은 **구조 시험 1건**이고, 동작 그물 **5건**(3건이
아니다)은 그대로 남는다. `9aed645` 가 실제로 하는 일은 **`async def` → `def` 전환과
`copyfileobj` 스트리밍**이며, 시험 파일에는 그 구조를 못 박는 `ast` 시험 하나와 산문
갱신만 더한다.

**떼어낸 상태를 실측했다** — `ingestion.py` 와 `test_upload_streaming.py` 를 `4599ab5` 판으로
되돌린 트리에서 `pytest -q tests/test_upload_streaming.py` → **5 passed**
(`async def` 3 · 시험 5건). 즉 `9aed645` 를 떼어내도 동작 그물은 살아 있고, 없어지는 것은
구조 시험 1건뿐이다. 그 5건이 `read()` 구현에서도 green 인 것이 요점이다 —
「그물은 바꾸기 **전에** 친다」.

## 4. 항목별 — 변경 · 시험 · 전/후

### ㉮ 입력오류 → 400 · IntegrityError → 409 (#12) — `b7ad4f7`

- **예외형 신설** — `services/core-api/src/colab_core/kernel/errors.py:InputError`.
  `ValueError` 를 통째로 매지 않는다: 넓은 형까지 400 으로 접으면 **서버 결함이 「네 요청이
  틀렸다」로 위장**해 감시에서 사라진다. `input_error_response` · `integrity_error_response`
  가 봉투를 만든다.
- **핸들러 등록** — `src/colab_core/app/main.py:create_app` 안, 기존 `HTTPException`·
  `RequestValidationError` 핸들러 옆. 409 본문은 코드 + 고정 문구뿐(`INTEGRITY_MESSAGE`) ·
  SQL·표·열·제약 이름 0 · 사유는 로거 `colab_core.integrity` 로만.
  ⚠ SQLSTATE 분기는 **수용 검토 회차에 좁혔다** — §10-㈏.
- **⚠ `errors.InputError` 는 지금 무동작(inert)이다 — 산출 코드에 `raise` 자리가 0 이다.**
  실측(`grep -rn "InputError" services/core-api/src/`) — 나오는 곳은 형 정의
  (`kernel/errors.py`) · 응답 생성기(`input_error_response`) · 핸들러 등록
  (`app/main.py`) 셋뿐이고, **던지는 자리는 시험의 시험용 라우트 하나뿐**이다.
  가드 다섯은 전부 `errors.bad_request`(=`ApiError`/`HTTPException`)로 400 을 낸다.
  - 왜 그래도 두는가 — 이 형의 목적은 **커널·도메인이 HTTP 를 모른 채 「입력이 틀렸다」를
    말하는 것**이다(`ApiError` 는 `HTTPException` 이라 커널이 쓰면 그 층이 교체 불가능해진다).
    이번 가드 다섯은 전부 **라우트 층**이라 `bad_request` 로 충분했고, 그래서 형은 서 있되
    쓰이지 않는 상태로 남았다.
  - **지금 상태를 그대로 적는다** — 커널·도메인에서 400 이 필요해지는 첫 자리가 이 형의
    첫 산출 사용처다. 그때까지는 「형과 핸들러가 있다」가 「그 경로가 돈다」를 뜻하지 않는다.
  - 다만 **응답 생성기 `input_error_response` 는 무동작이 아니다** — 수용 검토 회차의
    CHECK 위반 400 갈래가 이것을 쓴다(§10-㈏). 무동작인 것은 `@app.exception_handler`
    (`errors.InputError`) **경로**다.
- **가드 5**
  - `src/colab_core/app/routes/access.py:_living_dataset` — `Ulid.is_valid` 선검사.
    전: `POST /datasets/not-a-ulid/access-requests` → **500** · 후: **400**.
  - `src/colab_core/kernel/session_token.py:SessionSigner.verify` — `token.isascii()` 선검사.
    전: 비ASCII Bearer → `UnicodeEncodeError` → **500** · 후: **401**.
  - `src/colab_core/app/routes/catalog.py:_is_datetime` + `validate_human_metadata` —
    기간 자유 문자열. 전: `{"period":{"start":"어제부터"}}` → timestamptz 파싱 → **500** ·
    후: **400**. 계약 `DataPeriod` 가 `format: date-time`.
  - `src/colab_core/app/routes/catalog.py:_TOPICS` + `validate_human_metadata` — 주제 4값.
    값 정본은 **DB CHECK**(`db/platform/schema.sql:370`, 읽기 전용 조회)이고 계약 산문이
    「값 집합은 DB CHECK 4값이 지킨다 · 계약 층 enum 은 만들지 않는다」로 그 자리를 명시.
    전: **500**(IntegrityError) · 후: **400**.
  - `src/colab_core/app/routes/project.py:create_project` — 이름 `strip` 후 길이.
    수정 경로(`update_project`)는 이미 `strip` 했다 — **두 경로의 판정이 갈려 있던 것**.
    전: 공백 이름 → CHECK 위반 → **500** · 후: **400**.
- **시험** — `tests/test_input_error_paths.py` 9건(양성 대조 2건 포함).
  전 8 failed / 후 9 passed. 비ASCII 건은 **헤더를 바이트(latin-1)로** 보낸다 —
  `str` 로 주면 시험 클라이언트가 먼저 죽어 서버를 못 잰다.
- 핫 파일 `routes/catalog.py` 는 상수 1 · 헬퍼 1 · 검사 2블록만 더했다. 재포맷·import 재정렬 0.

### ㉯ `update_project` 기간 (#7) — `6d44f64`

- `src/colab_core/app/routes/project.py:update_project` — `_period()` 의 **결과를 넘긴다**.
  종전에는 「형식 검사만 — 저장은 도메인이 한다」 주석과 함께 값을 버렸다.
- `src/colab_core/domains/d6_project.py:update_project` — 문서에 「`changes["period"]` 는
  `datetime.date` 다」를 못 박았다. 바인딩 코드는 그대로(값만 date 가 됨).
- 변환 자리를 **`create_project` 와 같은 쪽(라우트)** 으로 통일. 도메인 변환은 택하지 않았다 —
  두 경로가 갈리면 한쪽만 고쳐진다.
- **시험** — `tests/test_lab_and_project_update.py` 4건 추가.
  전: 기간 실린 `PATCH` → **500**(같은 요청의 이름·설명까지 롤백) · 후: **200** + 왕복 저장.
  `period: null` 비우기 · 형식 오류 400 유지(넓히지 않았음) 포함.

### ㉰ 중계 4xx 통과 (#8) — `dc26829`

- `src/colab_core/app/relay.py:RelayRefused`(status + body) 신설 ·
  `PASS_THROUGH_STATUSES = (400, 404, 410, 413, 415, 422)` · `_refuse_if_client_error`.
  `create` · `palettes` · `lookup_value` 세 곳에서 호출.
- **401·403·5xx 는 통과시키지 않는다** — 자격 실패는 우리 서비스 토큰이 틀렸다는 뜻이라
  **우리 쪽 고장**이고, 5xx 는 「지금 못 그린다」이지 「이건 못 그린다」가 아니다. 둘 다 503 유지.
- `src/colab_core/app/routes/preview.py:_refused` — 저쪽 상태·봉투를 그대로 올린다.
  본문이 없으면 상태만 살리고 `RENDER_REFUSED` 봉투를 씌운다(상태는 저쪽이 낸 사실이다).
- `src/colab_core/app/routes/preview.py:lookup_dataset_value` — 위경도에서 `bool` 을 먼저
  뺀다(`isinstance(True, int)` 가 참이라 종전 검사를 통과했다) · -90~90 / -180~180 범위 검사.
- **시험** — `tests/test_relay_status_passthrough.py` 23건. 전 15 failed / 후 23 passed.
  - 전: 415 NOT_RENDERABLE → **503 「연결하지 못했다」** · 후: **415 + `details.renderableFormats` 원본**.
  - 전: `{"lat": 200}` → viz 422 → **503** · 후: **400**(그리는 서버까지 나가지도 않는다).
  - **경계 헤더 잠금** — `_scope_headers`(`X-CoLAB-Lab`·`X-CoLAB-Account`)와 서비스 자격
    증명이 **중계 5호출 전부**(`/renders` · `/renders/{id}` · `/palettes` · `/value-lookups` ·
    `/screenshots`)에 실림을 시험으로 못 박았다. 이미 실려 있었고 **바뀐 것은 없다** —
    레인 C 가 지금 그 헤더로 job 의 연구실을 대조하므로, 한 호출이라도 빠지면 그 표면만
    조용히 죽는다.

### ㉱ 로그인 제한 (#5) — `f634948`

- `src/colab_core/kernel/authn.py:LoginAttempt.key` — 접속 코드 버킷을
  `code:<sha256(code)[:16]>` 로 가른다(전: 상수 `"code:*"` 한 버킷).
  **원문을 키로 쓰지 않는다** — 키는 로그·덤프를 따라다니고 접속 코드는 그 자체가 자격이다.
- `src/colab_core/kernel/authn.py:client_key` 신설 — `X-Forwarded-For` 첫 홉 · 길이 상한 64.
- `src/colab_core/app/routes/session.py:create_session` — 두 버킷을 **같은 한도·창**으로
  함께 센다(`blocked` any · `record_failure` 전부 · `clear` 전부).
  어느 버킷이 걸렸는지 응답에서 말하지 않는다.
- `src/colab_core/kernel/throttle.py:blocked` — **쓰지 않는다**(읽기 전용 계산).
  `record_failure` 가 `_drop_expired` 로 창 밖 버킷을 버려 dict 를 묶는다.
- **시험** — `tests/test_login_limiter_buckets.py` 10건.
  - 전: 모르는 코드 4회 실패 후 정상 접속 코드 → **429**(전 연구실 정지) · 후: **201**.
  - 전: 남의 성공 1회가 추측 버킷의 셈을 지움 · 후: 지우지 않는다.
  - 전: `blocked()` 1000회 → dict 1000건 · 후: **0건**.
  - 전: 만료 버킷 50건 잔류 · 후: `record_failure` 1회 뒤 **1건**.

### ㉲ `_FILE` 비밀값 (#15) — `a91de2b`

- `src/colab_core/kernel/config.py:load_settings` — `session_secret` · `viz_service_token` 이
  기존 `resolve_env_or_file` 을 쓴다. 규칙 다섯이 DB URL 과 **같다**.
- **뒤로 호환** — 생 env 만 있으면 지금과 같다. compose 무변경.
- **⚠ 다만 한 자리에서 동작이 갈린다 — 생 env 값이 이제 `.strip()` 된다.**
  종전 두 줄은 `os.environ.get(NAME) or None` 이었다(가공 0). 지금은
  `resolve_env_or_file` 을 지나고, 그 함수는 첫 줄에서 `direct = (env.get(name) or "").strip()`
  을 한다 — **`_FILE` 경로만이 아니라 생 env 값도** 앞뒤 공백이 벗겨진다.
  `resolve_env_or_file` 자체는 이 회차에 한 글자도 안 바꿨다(기준 `d4d11b5` 와 동일).
  바뀐 것은 **이 두 값이 그 함수를 지나게 된 것**이다.
  - 산문과의 어긋남 — 그 함수 독스트링 ①은 `_FILE` 쪽만 두고 「끝의 공백·개행만 벗긴다」고
    적는다. 생 env 쪽 `.strip()` 은 적혀 있지 않다. **DB URL 도 처음부터 같은 동작이었다** —
    이번에 생긴 것이 아니라 이번에 두 값이 더 걸린 것이다.
  - 실효 — 앞뒤 공백이 값의 일부였다면 그 값이 **조용히 잘린다.**
  - **⚠ viz 토큰 쪽은 한쪽만 잘린다 — 두 서비스가 같은 값을 비교한다.**
    `infra/staging/compose.i2.yml:183·313` 이 **같은 `COLAB_VIZ_SERVICE_TOKEN`** 을
    core-api(`COLAB_CORE_VIZ_SERVICE_TOKEN`)와 viz-render 양쪽에 넣는다. 이제 core-api 는
    `resolve_env_or_file` 로 `.strip()` 하고, viz-render 는
    `services/viz-render/src/colab_viz/kernel/config.py:120` 이
    `os.environ.get("COLAB_VIZ_SERVICE_TOKEN") or None` — **가공 0** 이다(레인 C 의 면).
    값에 앞뒤 공백이 있으면 두 쪽이 **다른 문자열**을 쥐고, 미리보기 전 표면이
    401 → 503 으로 죽는다. 세션 서명 키는 core-api 안에서만 쓰여 이 위험이 없다.
  - `[미확인]` — 배포된 두 값에 앞뒤 공백이 있는지 **재지 않았다.** `compose.i2.yml` 은
    `${...:?}` 로 참조만 하고 값은 레포 밖 env 파일에 있다.
    → 푸는 법 — 그 env 파일에서 두 값의 **길이만** 재어 `strip()` 전후를 비교한다
    (값은 출력하지 않는다). 다르면 배포 전에 env 파일을 고치거나 viz 쪽도 `.strip()` 한다.
- **시험** — `tests/test_secret_file_refs.py` 9건. 전 7 failed / 후 9 passed.
  전: `COLAB_CORE_SESSION_SECRET_FILE` 설정 → **오류 없이 무시** → signer 미생성 →
  `POST /sessions` 500 `SESSION_UNAVAILABLE`(무시된 변수 이름은 어디에도 안 나옴) ·
  후: 값이 읽히고 signer 가 선다. 파일 부재·빈 파일·두 출처 동시는 **죽는다**(값 미출력 확인).

### ㉳ 업로드 (#10 + 부록) — `4599ab5`(㈎) · `9aed645`(㈏, 떼어낼 수 있음)

- ㈎ `src/colab_core/app/routes/ingestion.py:add_dataset_file` — `_store` 를
  `kind == GRID` 400 **뒤로** 옮겼다. 옮긴 줄 하나 + 주석뿐(핫 파일 최소 diff).
  전: 거절한 격자 파일이 `uploads/{id}/grid/` 에 잔류 · 후: 디스크 무변화.
  격자를 읽는 쪽(viz-render)에는 원장이 없어 **폴더가 곧 사실**이라, 거절했다면서 그 파일로
  그리거나 짝이 셋이 되어 멀쩡한 격자까지 통째로 거절된다.
- ㈏ `src/colab_core/app/routes/ingestion.py` — `create_upload` · `add_dataset_file` ·
  `replace_dataset_grid_file` 셋을 `async def` → `def`. `_store` 가 `UploadFile` 을 받아
  `shutil.copyfileobj` 로 1 MiB 씩 흘려 보내고 **실제로 쓴 바이트 수**를 돌려준다.
  크기를 `Content-Length` 로 믿지 않는 이유 — 원장이 적은 크기와 디스크의 실물이 갈리면
  그 어긋남은 오류를 내지 않는다. **크기 상한 로직은 원래 없었고**(상한은 nginx 가 쥔다)
  새로 만들지 않았다.
- **시험** — `tests/test_upload_streaming.py` 6건. **커밋별로 갈라 적는다**(§3 정정) —
  - **`4599ab5` 가 더하는 5건** — 거절본 미저장 1 · 수용본 저장 1(넓히지 않았음) ·
    바이트 무결성 3(5 MiB+ 단건 sha256 일치 · 2파일 묶음 상호 오염 없음 · 격자 교체.
    자리마다 다른 바이트를 써서 **청크 순서가 어긋나면 해시가 깨지게** 했다).
    ⚠ 이 5건은 ㈎ 의 시험이자 ㈏ 의 **회귀 그물**이라 ㈏ 보다 **먼저** 들어가 있다.
  - **`9aed645` 가 더하는 1건** — 구조. `ast` 로 `AsyncFunctionDef` 0 · `Await` 0 ·
    `shutil.copyfileobj` 호출 존재. **문자열이 아니라 구문을 본다** — 문자열로 재면
    주석 한 줄이 시험을 뒤집는다. `9aed645` 를 떼어내면 없어지는 시험은 **이 1건뿐**이다.

### ㉴ 미구현 계수 (부록) — `4599ab5`

- `src/colab_core/app/routes/not_implemented.py:1` — 「23 개」 → **4 개**.
  아래 문단들이 23→22→20→19→16→9→12→4 를 한 줄씩 적어 내려가는 동안 첫 줄만 안 따라갔다.
- `tests/test_not_implemented.py` 시험 이름 「5」 → 「4」(단언은 처음부터 `== 4` 였다).

## 5. Ted 판정 대기

### ㈎ 로그인 제한 정책 — 두 갈래

1. **한도·창의 값.** 지금 두 버킷 모두 기존 값(창 900초에 실패 5회)을 그대로 쓴다.
   근거는 그 값 하나뿐이고 정본에 없다(`kernel/config.py` 산문이 「[정본 무근거]」로 명시).
2. **클라이언트 버킷의 열쇠.** ~~지시대로 `X-Forwarded-For` **첫 홉**으로 세웠다.~~
   **개정 (수용 검토 · `9b4004b`) — ⓑ 마지막 홉으로 전환했다.** 아래 원문은 판정 경위를
   남기기 위해 지우지 않는다.
   > ⚠ **실물과 어긋나는 지점을 그대로 적는다** — `infra/staging/nginx.i2.conf:61` 은
   > `$proxy_add_x_forwarded_for` 를 쓴다. 들어온 헤더 **뒤에** `$remote_addr` 를 덧붙이는
   > 변수라, 클라이언트가 헤더를 실어 보내면 **그 값이 첫 홉이 되고 nginx 가 실제로 본 주소는
   > 마지막 홉**이다. 그러므로 이 버킷이 늦추는 것은 **헤더를 안 만지는 열거**뿐이고,
   > 헤더를 돌리는 상대에게는 브레이크가 아니다.
   > - 고르는 것 — ⓐ 지금대로(첫 홉, 순진한 열거만 브레이크) · ⓑ 마지막 홉(신뢰 가능,
   >   다만 프록시 홉 수 가정이 배포에 박힌다) · ⓒ nginx 가 **단독으로 세팅하는 별도 헤더**
   >   (예: `X-Real-IP` 를 `$remote_addr` 로) — 가장 정직하나 **배포 설정 변경**이라 이 레인 밖.
   > - 권고 — ⓒ. 되돌리는 비용은 nginx 한 줄 + core-api 한 줄.
   - **지금 상태** — ⓑ. `kernel/authn.py:client_key` 가 마지막 홉을 읽는다. 코드 변경 없이
     현 nginx 설정에서 곧바로 신뢰 가능한 값이 된다(§10-㈎).
   - **ⓒ 는 여전히 열려 있다 — Ted 배포 쪽 후속.** nginx 에
     `proxy_set_header X-Real-IP $remote_addr;` 를 더하고 `client_key` 가 그 헤더를 읽게 하면
     프록시 홉 수 가정이 아예 사라진다. **이 레인 밖**(`infra/**` 편집 금지)이라 안 했다.
   - **ⓑ 의 대가 — 로드밸런서가 nginx 앞에 서면 버킷이 하나로 접힌다.** 그때 nginx 가 보는
     주소는 늘 그 로드밸런서라 마지막 홉이 전원 공통값이 된다. 그 동작은 **버킷을 잃는 것이
     아니라 한 버킷으로 접히는 것**이다 — 클라이언트 버킷이 없던 시절과 같은 셈이고
     (자격 버킷은 그대로 산다) 어느 쪽으로도 **열리지 않는다**. 그 배치를 실제로 쓰게 되는
     것이 ⓒ 의 착수 조건이다.
   - 값 자체는 `kernel/authn.py:client_key` 한 자리에서만 바뀐다.
3. **성공 시 클라이언트 버킷도 지운다**(현재 동작). 같은 IP 의 정상 사용자가 남의 실패로
   계속 막히지 않게 한 선택이고, 대가는 유효 자격 하나로 자기 IP 버킷을 비울 수 있다는 것.

### ㈏ compose `_FILE` 전환 — 배포 변경

- 이번 회차는 **읽는 쪽만** 열었다. compose 는 한 글자도 안 바꿨고 뒤로 호환된다.
- 남은 일 — `compose.i2.yml` 의 `COLAB_CORE_SESSION_SECRET` ·
  `COLAB_CORE_VIZ_SERVICE_TOKEN` 을 `*_FILE` + `0600` 자격 파일로 옮기기.
  **둘을 동시에 두면 앱이 뜨지 않는다**(규칙 ③) — 옮길 때 생 env 를 반드시 제거한다.
- `PLAN §4-6`(compose 비밀값 `_FILE` 전환)에 이미 유보 항목으로 서 있다. 그 항목의 core-api
  쪽 선행 조건이 이 회차로 사라졌다.
- viz-render kernel 에는 `resolve_env_or_file` 자체가 없다(레인 C 범위).

## 6. 계약 델타 초안 — 계약은 고치지 않았다

**`contracts/seams/fe-core.yaml` — 미리보기 3 op 의 4xx 선언.**

- 현재 선언 — `createPreviewRender` 202/400/401/404/503/500 ·
  `listPalettes`·`lookupDatasetValue` 도 같은 계열. **410·413·415·422 가 없다.**
- 실물 — core-api 가 이제 그 넷을 viz 것 그대로 올린다(`dc26829`). 그리고 FE 는 **이미**
  `status === 415` 로 분기하고 있었다(`previewSource.ts:41/67` · `datasetPreviewSource.ts:74/87` —
  종전에는 도달 불가한 죽은 코드였다).
- 필요한 델타 — 세 op 의 `responses` 에 `"415"`(NOT_RENDERABLE · 본문은
  `core-viz.yaml` 의 `ErrorEnvelope`, `details.renderableFormats` 포함) · `"413"` · `"410"` ·
  `"422"` 를 더한다. **스키마 신설 0** — 전부 기존 `ErrorEnvelope` 참조다.
- 선례 — `createPreviewScreenshot` 은 **이미** viz 상태를 그대로 올리고 있으면서 계약은
  200/400/401/403/404/409/503/500 만 선언한다. 즉 이 어긋남은 이번에 생긴 것이 아니라
  **이번에 하나 더 드러난 것**이다.
- 판정이 「계약을 안 연다」로 나면 되돌릴 자리는 `app/relay.py:PASS_THROUGH_STATUSES`
  한 줄이다.

## 7. 못 한 항목 — 편집 면 밖

| 지시 항목 | 실제 파일 | 왜 멈췄나 |
|---|---|---|
| ⑦ `degradedReason` 원시 예외 제거 | `services/ai-service/src/colab_ai/domains/d10_ai_services.py` · `.../d10_suggestion.py` | **ai-service** — 레인 B 편집 면(`services/core-api/**`) 밖 |
| ⑧ 투영 밖 좌표 → 200 + 사유 | `services/viz-render/src/colab_viz/domains/d7_visualization/value_lookup.py` | **viz-render** — 레인 C 의 면 |

PLAN §2 B 행에는 둘이 적혀 있으나, 레인 지시문의 편집 면 규칙(`services/core-api/**` 만 ·
「타 서비스 편집 금지」)이 그보다 강하다. **지어내고 진행하지 않고 멈춘 뒤 델타를 적는다.**

### ⑦ 델타 초안 (ai-service)

- 자리 — `d10_ai_services.py` 의 `except Exception as e:` 뒤
  `reason = ... f"온톨로지 사전을 읽지 못해 질문의 낱말 그대로 찾았다: {e}"` ·
  `d10_suggestion.py:164` 의 `body["degradedReason"] = reason`.
- 문제 — `{e}` 가 DB 예외면 **호스트·포트·롤·DSN 조각**이 응답 본문에 실려 나간다.
  화면엔 안 그리지만 네트워크 탭에는 보인다.
- 델타 — 사유를 **안정된 문구 상수**로 고정(예: 「온톨로지 사전을 읽지 못해 질문의 낱말
  그대로 찾았다」 — `{e}` 제거)하고, **원시 예외는 서버 로그로만** 보낸다.
  core-api 의 `relay.py:_record_suggest_failure` 가 이미 같은 규약(로거 이름 · `event` ·
  `code`)을 세워 뒀으므로 그 무늬를 그대로 쓴다. 계약 변경 0(`degradedReason` 은 자유 문자열).
- ⚠ **같은 모양의 형제가 core-api 에도 있다** — `src/colab_core/app/relay.py` 의
  `honest_empty_suggestions(reason=f"... {e}")` · `unreadable_interpretation(f"... {e}")` 가
  urllib 예외 문자열(내부 주소·포트를 담을 수 있다)을 `degradedReason`/`unavailableReason`
  으로 실어 보낸다. **이번 회차에 손대지 않았다** — 지시 항목이 아니었고, 응답 문구를
  바꾸는 변경이라 FE·시험 영향을 함께 재야 한다. 다음 회차 작업항목으로 올린다.

### ⑧ 델타 초안 (viz-render)

- 자리 — `value_lookup.py:read_point` 의 `warp_transform("EPSG:4326", ds.crs, [lon], [lat])`
  과 이어지는 `ds.index(...)`.
- 문제 — LCC 등 투영 밖 좌표에서 rasterio/CPLE 예외가 그대로 올라가 **500**.
  계약은 200 + 사유다.
- 델타 — 그 두 줄을 `try` 로 감싸고 rasterio/CPLE 예외에서
  `LookupOutcome(available=False, unavailable_reason=OUT_OF_RANGE, exactness=_exactness(...))`
  를 돌려준다. **계약·스키마 변경 0** — `core-viz.yaml ValueLookupResult.unavailableReason`
  의 enum 에 「범위 밖이다」가 이미 있고 그 상수(`OUT_OF_RANGE`)도 이미 이 파일에 있다.
  같은 파일 아래쪽 범위 밖 분기(`0 <= row < ds.height` 검사)와 **답이 같아진다.**
- core-api 쪽은 이미 준비됐다 — `dc26829` 이후 viz 가 4xx 를 내면 그대로 통과하고,
  200 + 사유면 그대로 지나간다.

### ⑨ 레인 C 로 넘기는 관찰 — viz 의 입력 검증 응답이 **그대로 브라우저까지 간다**

`dc26829` 이 viz 의 4xx 를 상태·본문 그대로 올리게 되면서, viz 쪽 검증 핸들러가 내는 것이
**core-api 를 지나 화면의 네트워크 탭까지** 도달하게 됐다. 그 핸들러를 실물로 읽었다 —
`services/viz-render/src/colab_viz/app/main.py:95` (읽기만 함 · 레인 C 의 면):

```python
@app.exception_handler(RequestValidationError)
async def _validation_error(_request, exc: RequestValidationError):
    return errors.error_response(
        errors.bad_request("요청 값이 규칙에 맞지 않는다.", {"errors": str(exc.errors())}))
```

두 가지를 적는다 —

1. **상태가 400 이다 — 422 가 아니다.** FastAPI 기본값은 422 인데 viz 는 `bad_request` 로
   덮어 400 을 낸다. core-api 의 통과 집합(`PASS_THROUGH_STATUSES`)에는 400·422 가 **둘 다**
   있어 어느 쪽이든 흐르지만, 계약 델타(§6)를 쓸 때 「viz 는 422 를 낸다」로 적으면 틀린다.
   core-api 자신의 핸들러(`app/main.py`)도 같은 모양이라 **두 서비스가 같은 선택**을 했다.
2. **⚠ `details.errors` 가 `str(exc.errors())` 그대로 실린다.** pydantic 의 오류 목록은
   `loc`(필드 경로) · `msg` · **`input`(들어온 값 원문)** 을 담는다. 그것이 이제 중계를 타고
   브라우저까지 간다 — 화면에 그리지 않아도 네트워크 탭에는 보인다.
   - 뜻하는 것 둘 — ⑴ 내부 스키마의 필드 경로가 노출된다. ⑵ 요청 본문에 실린 값이
     응답으로 되돌아온다(자기 값이라 자기에게 새는 것은 아니나, 로그·에러 수집기가
     응답 본문을 담으면 그쪽으로 함께 간다).
   - **이번 회차에 손대지 않았다** — `services/viz-render/**` 는 레인 B 의 편집 면 밖이고,
     응답 본문을 바꾸는 변경이라 FE·시험 영향을 함께 재야 한다.
   - 델타 초안 — `details` 를 필드 경로 + 사유까지로 줄이고 `input` 을 뺀다.
     **형제가 core-api 에도 있다** — `app/main.py` 의 `_validation_error` 가 같은
     `str(exc.errors())` 를 쓴다. 한쪽만 고치면 나머지가 그대로 남는다(§7 ⑦ 의 「형제를
     찾는다」와 같은 계열). 다음 회차 작업항목.
   - `[미확인]` — 실제로 어떤 값이 실려 나가는지 실서버 요청으로 재지 않았다. 판정은
     두 파일의 소스 조회로만 했다.

## 8. `[미확인]`

1. **업로드 스트리밍의 메모리 사용량을 재지 않았다.** 잰 것은 **바이트 무결성**(sha256
   일치 · 길이 일치 · 묶음 상호 오염 없음)과 **구조**(`async def` 0 · `copyfileobj` 존재)뿐이다.
   → 푸는 법 — 수 GB 파일 하나를 올리며 프로세스 RSS 를 표본화하고, 같은 동안
   `/healthz` 응답 시간을 잰다. 회귀의 본체(「다른 요청이 멈춘다」)는 그 두 번째 값이다.
2. **`X-Forwarded-For` ~~첫 홉~~ 마지막 홉의 실제 신뢰도를 배포에서 재지 않았다.**
   nginx 설정 문자열(`$proxy_add_x_forwarded_for`)로 판정했고 실요청으로 확인하지 않았다.
   → 푸는 법 — staging 에 헤더를 실어 요청 하나를 보내 core-api 가 무엇을 열쇠로 잡는지 본다.
   **개정** — 열쇠는 마지막 홉으로 바뀌었으나(§10-㈎) **이 미확인은 그대로 살아 있다.**
   판정 근거가 여전히 설정 문자열이지 실요청이 아니다.
3. **`e2e` 5건은 이번에도 못 돌렸다** — `COLAB_REFERENCE_DATA` 원천 마운트 부재.
   → 푸는 법 — 원천 디렉터리를 마운트하고 같은 명령을 다시 돈다.
4. **계약 델타(§6)를 계약 게이트로 재지 않았다.** `contracts/**` 가 편집 금지라
   선언을 더해 보고 `contract-*` 게이트가 무엇을 말하는지 확인하지 못했다.
5. **`preview.py` 의 `RENDER_REFUSED` 봉투가 실제로 나가는 경로를 실서버에서 못 봤다.**
   viz 가 4xx 를 본문 없이 내는 경우에만 쓰인다 — 가짜 viz 로만 쟀다.
6. **다른 레인과의 상호작용은 재지 않았다.** 특히 레인 C 의 viz 테넌트 경계가 서면
   `dc26829` 의 통과 집합에 **404**(다른 연구실 renderId)가 실제로 흐르게 된다 —
   지금은 `getPreviewRender` 만 404 를 자체 처리하고 `create`·`lookup_value` 는 통과시킨다.
   → 푸는 법 — 병합 트리에서 두 레인의 시험을 함께 돈다.

## 9. 등재문 초안 (번호 없음 — 오케스트레이터가 발급)

> **core-api 오류 경계 정리 — 사용자 오타가 500 이던 다섯 경로와 중계 4xx 를 닫는다.**
> 입력 오류 전용 예외형과 `IntegrityError` 핸들러를 `app/main.py` 에 세우고(400 / 409,
> 409 본문에 SQL·제약 이름 0), 손검사를 빠뜨린 다섯 자리에 가드를 넣었다 — 데이터셋
> 식별자 모양 · 비ASCII Bearer(→ 401) · 데이터 기간 자유 문자열 · 주제 4값 · 프로젝트
> 생성 이름 공백. `update_project` 는 기간을 날짜로 변환해 넘긴다(종전에는 기간이 실린
> 수정이 전부 500 이었고 같은 요청의 이름·설명까지 롤백됐다).
> 미리보기 중계는 그리는 서버의 4xx(400·404·410·413·415·422)를 **상태·본문 그대로**
> 올린다 — 종전에는 「그릴 수 없는 형식」이 「서버에 못 닿았다」로 바뀌어 지원 형식 목록이
> 화면에 닿지 못했다. 자격 실패·5xx 는 그대로 503 이다. 값 조회의 위경도는 범위와
> 참·거짓을 검사해 클라이언트 오류가 장애 계수에 섞이지 않게 했다.
> 로그인 시도 제한은 접속 코드를 해시해 버킷을 가르고(종전에는 한 버킷이라 한 사람이
> 5회 실패시키면 모든 접속 코드 사용자가 15분간 막혔다) 부른 클라이언트 버킷을 함께 센다.
> 세션 서명 키와 그리는 서버 토큰을 값 대신 **파일 경로**로 받는다 — 컨테이너 환경변수
> 목록에서 읽히던 자리를 닫았고, 배포 설정은 그대로 둬도 동작한다.
> 업로드는 거절한 격자 파일을 디스크에 남기지 않고, 파일을 통째로 메모리에 올리는 대신
> 흘려 보낸다.
> 시험 61건 추가 · core-api 전체 614 통과(기준선 553) · 게이트 4종 green.
> **판정 대기 둘** — 로그인 제한의 클라이언트 열쇠(현 nginx 설정에서 첫 홉은 사용자가
> 보낸 값이다) · 배포 설정의 비밀값 파일 전환.
> **계약 델타 필요** — 미리보기 3 op 에 4xx 네 개 선언(스키마 신설 0).

**개정 (수용 검토 반영 회차)** — 위 초안의 두 자리를 고쳐 읽는다.

> 로그인 시도 제한의 클라이언트 열쇠는 **부른 쪽이 못 바꾸는 값**(nginx 가 덧붙이는
> 마지막 홉)으로 세웠다 — 종전 초안이 「판정 대기」로 남겼던 자리다. 남은 판정은
> **배포 설정의 비밀값 파일 전환 하나**다. 그리고 저장 규칙 위반 응답을 유니크 위반과
> 값 위반으로 갈랐다 — 「이미 있어요」와 「그 값이 아니에요」는 사용자가 할 일이 다르고,
> 그 둘에 해당하지 않는 위반은 **500 으로 남겨 눈에 보이게** 둔다.
> 시험 68건 추가 · core-api 620 통과(`-m "not e2e"` 기준선 613) · 게이트 3종 재실측 green.

---

## 10. 수용 검토 반영 — 레인 B 수정 회차

> 레인 B 산출물의 수용 검토에서 나온 지적 셋을 이 브랜치 위에 얹었다.
> 편집 면은 그대로 `services/core-api/**` + 이 기록. 커밋 `9b4004b` · `0a78b76` + 이 기록.
> 계수 613 → **620** · 실패 0 · 게이트 3종 green(§1 · §2).
> 각 수정은 **실패 시험을 먼저 확인**했다 — 아래 각 항에 무엇이 어떻게 실패했는지 적는다.

### ㈎ 클라이언트 버킷 열쇠 = **마지막 홉** (#5) — `9b4004b`

- **무엇이 문제였나** — `client_key` 가 `X-Forwarded-For` **첫 홉**을 읽었다. 현 nginx
  설정(`$proxy_add_x_forwarded_for`)에서 첫 홉은 **부른 쪽이 실어 보낸 값**이라 요청마다
  갈아 끼우면 버킷이 매번 새로 생겼다 — 클라이언트 버킷이 브레이크 구실을 못 했다.
- **바뀐 것 ①** — `split(",")[-1].strip()`. 마지막 홉은 nginx 가 덧붙인 `$remote_addr` 라
  부른 쪽이 못 바꾼다.
- **바뀐 것 ② (형제 결함)** — 길이 상한(64)을 넘긴 홉이 `None` 이었다. 즉 **긴 헤더 한 줄이
  클라이언트 버킷을 통째로 끄는 스위치**였다. 이제 고정 버킷 `CLIENT_OVERSIZE`
  (`"client:oversize"`)로 접힌다. 길이 상한의 목적은 열쇠가 로그·dict 를 부풀리지 않게
  묶는 것이지 셈을 면제하는 것이 아니다. 대가는 「긴 헤더를 보내는 모두가 한 버킷」인데,
  그쪽이 「긴 헤더를 보내는 모두가 무제한」보다 낫다.
- **안 바꾼 것** — 헤더가 없으면 여전히 `None`(클라이언트 버킷 없음 · 자격 버킷만 센다).
  헤더는 있는데 마지막 홉이 빈 값(`","`)인 경우도 같다 — nginx 뒤에서는 `$remote_addr` 가
  늘 붙으므로 도달하지 않는 모양이다. **한도·창 값은 손대지 않았다**(§5-㈎ 1 그대로).
- **시험** — `tests/test_login_limiter_buckets.py` 10 → **13건**.
  `test_the_client_key_reads_only_the_first_hop` 을
  `test_the_client_key_reads_the_last_hop_not_the_first` 로 뒤집고 3건을 더했다 —
  고정 버킷 단위 1 · **동작** 2(첫 홉을 갈아 끼워도 클라이언트 버킷을 못 빠져나간다 ·
  긴 헤더로 제한을 못 끈다).
  - **실패 먼저 확인** — 옛 로직(첫 홉)으로 되돌린 트리에서 그 **4건이 전부 실패**했다
    (`4 failed, 9 passed`). 임포트 오류가 아니라 **판정으로** 실패함을 봤다:
    `assert 'client:203.0.113.9' == 'client:10.0.0.2'` · `assert None == 'client:oversize'` ·
    「첫 홉을 갈아 끼워 클라이언트 버킷을 빠져나갔다」 · 「긴 헤더가 클라이언트 버킷을
    통째로 지웠다」.

### ㈏ `IntegrityError` 그물을 SQLSTATE 로 좁힘 (#12) — `0a78b76`

- **무엇이 문제였나** — 핸들러가 `IntegrityError` **전부**를 409 한 갈래로 접었다.
  가드가 놓친 사용자 오류만이 아니라 **우리 코드가 잘못 쓴 것**까지 함께 삼킨다 —
  외래키 위반(`23503`)·not-null 위반(`23502`)은 사용자가 고칠 수 있는 값이 아닌데
  「이미 있어요」로 위장한 채 5xx 계수·경보에서 사라진다. **`ValueError` 를 통째로 매지
  않기로 한 것과 같은 실패 유형**이 그물 쪽에 남아 있던 것이다.
- **바뀐 것** — psycopg 3 의 `Error.sqlstate` 로 세 갈래.

  | SQLSTATE | 뜻 | 응답 |
  |---|---|---|
  | `23505` | unique_violation | **409** `CONFLICT` (종전과 같다) |
  | `23514` | check_violation | **400** `BAD_REQUEST` + 입력 오류 봉투 |
  | 그 밖 전부 | — | **다시 던진다** → 500 으로 남아 눈에 보인다 |

  CHECK 위반을 가른 이유 — 「두 번 일어날 수 없다」가 아니라 **「그 값이 아니다」**이다.
  409 로 접으면 화면은 「이미 있어요」로 읽고 사용자는 **고칠 수 있는 값을 안 고친다.**
- **로그도 좁혔다** — `str(exc.orig)` 를 버리고 `sqlstate` + `diag.constraint_name` 만
  남긴다. psycopg 의 `DETAIL:` 줄은 **사용자가 넣은 값**(키·컬럼값)을 그대로 담고, 로그는
  덤프·티켓·화면 캡처를 따라다닌다. 남길 것은 **무엇이 안 맞았는지**이지 **어떤 값이었는지**가
  아니다. 재던지는 갈래는 로그를 남기지 않는다 — 500 의 트레이스백이 그 자리를 이미 쥔다.
- **`kernel/errors.py`** — `INTEGRITY_INPUT_MESSAGE` 상수 1개 추가(유니크 위반과 문장을
  가르되 값·제약 이름은 여기도 안 담는다). 400 봉투는 기존 `input_error_response` 를 쓴다.
- **시험** — `tests/test_input_error_paths.py` 9 → **13건**. 시험 라우트를
  `/_probe/integrity/{sqlstate}` 로 바꾸고 가짜 `orig` 가 `sqlstate` · `diag.constraint_name`
  을 싣는다. 더한 것 —
  - `23514` → 400(+ 본문 누출 0)
  - `23503` → 500(409 로 위장하지 않음)
  - **로그 내용** — SQLSTATE·제약 이름 있음 · `DETAIL`·`Key (id)=` 없음 (`caplog`)
  - **가짜가 실물과 갈리지 않게** — psycopg 예외 클래스의 선언값과 대조
    (`UniqueViolation.sqlstate == "23505"` 등). 이것이 없으면 상수가 틀려도 시험은 전부
    green 인데 실서버에서는 한 갈래도 안 걸린다.
  - **실패 먼저 확인** — 수정 전 `3 failed, 10 passed`. 23514 가 409 로, 23503 이 409 로
    나왔고 로그에는 `DETAIL: Key (id)=(01A)...` 가 그대로 찍혔다.
- **회귀 확인** — 좁힌 그물이 기존 409 를 죽이지 않았다. 전체 620 통과 · 실패 0.
  기존 409 시험들(프로젝트 이름 중복 등)은 전부 **명시 가드**(`errors.conflict`)를 타지
  이 핸들러를 타지 않는다.

### ㈐ 기록 정정 셋

| 자리 | 무엇을 고쳤나 |
|---|---|
| §3 · §4-㉳ | `4599ab5` / `9aed645` 의 **시험 귀속**. 업로드 **동작 시험 5건 전부가 `4599ab5`**, `9aed645` 가 더하는 것은 `ast` 구조 시험 1건뿐. 종전 「바이트 무결성 3건」은 계수·귀속이 함께 틀렸다. 떼어낸 트리를 **실측**했다 — 5 passed |
| §4-㉮ | `errors.InputError` 는 **산출 코드에 `raise` 자리가 0**(무동작). 가드 다섯은 `bad_request` 를 쓴다. 형을 둔 이유와 첫 산출 사용처의 조건을 함께 적었다 |
| §4-㉲ | `resolve_env_or_file` 이 **생 env 값도 `.strip()`** 한다(기준 `d4d11b5` 의 두 줄은 가공 0 이었다). viz 토큰은 두 서비스가 같은 값을 비교하는데 **core-api 만 strip** 한다 — 공백이 있으면 미리보기가 죽는다. 배포 값의 공백 유무는 `[미확인]` |
| §5-㈎ 2 | 첫 홉 → **마지막 홉** 전환을 개정 표시로 반영. 원문은 지우지 않고 인용으로 남겼다. ⓒ(`X-Real-IP`)는 **Ted 배포 쪽 후속으로 그대로 열려 있다** |
| §7 ⑨ (신설) | 레인 C 로 넘기는 관찰 — viz 의 `RequestValidationError` 가 **400**(422 아님)을 내고 `details.errors` 에 `str(exc.errors())`(들어온 값 원문 포함)를 실어 **브라우저까지 간다**. 같은 모양의 형제가 core-api 에도 있다 |

### ㈑ 이 회차의 `[미확인]`

1. **`e2e` 5건은 이 회차에도 못 돌렸다** — `-m "not e2e"` 로만 쟀다(§8-3 과 같은 사유).
2. **마지막 홉의 실제 신뢰도를 배포에서 재지 않았다** — §8-2 가 그대로 살아 있다.
   판정 근거는 여전히 nginx 설정 문자열이지 실요청이 아니다.
   → 푸는 법 — staging 에 `X-Forwarded-For` 를 실어 요청 하나를 보내고 core-api 가
   무엇을 열쇠로 잡는지 본다.
3. **재던지는 갈래(`23503` 등)를 실 DB 로 재지 않았다** — 가짜 `orig` 로만 쟀다.
   상수가 실물과 맞는 것은 psycopg 클래스 대조로 확인했으나, **실제 외래키 위반이 이
   핸들러까지 올라오는 경로**가 있는지는 안 봤다.
   → 푸는 법 — 없는 부모를 가리키는 행을 넣는 요청을 하나 만들어 500 이 나는지 본다.
4. **`ai-no-lineage-write` 게이트는 이 회차에 안 돌렸다** — 지시 항목 밖(3종만).
5. **`./gates/run.sh all` 은 지시대로 안 돌렸다.**
