# CODE-REVIEW-20260903-B — 레인 B `core-api` 실행 기록

> 근거 — `dev-package/sessions/CODE-REVIEW-20260903.md`(#5·#7·#8·#10·#12·#15 + 부록) ·
> `dev-package/sessions/CODE-REVIEW-20260903-PLAN.md` §1·§2 B 행.
> 편집 면 — `services/core-api/**` 만. 계약·스키마·compose·infra·타 서비스·프론트 편집 0.
> 브랜치 — `worktree-agent-ac72b799fc10afb59` (기준 `lane-review-clean` `d4d11b5`). push 없음.

## 1. 계수 — 전/후

| 시점 | passed | failed | skipped | deselected | 시간 |
|---|---|---|---|---|---|
| 기준선(무수정 트리) | 553 | 5 | 0 | 0 | 108.58s |
| 종료(전체) | 614 | 5 | 0 | 0 | 116.11s |
| 종료(`-m "not e2e"`) | 613 | 0 | 0 | 6 | 100.48s |

- 계수 기준 — `services/core-api` 에서 일회용 Postgres 1대(`--rm` · tmpfs · `PGDATA` 지정 ·
  호스트 포트 미공개 · 이름 `laneB_pg_rc`)에 붙여 `pytest -q` 전체. 병렬도 1. 측정 2026-09-03.
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

## 3. 커밋 (오래된 순)

| sha | 항목 | 비고 |
|---|---|---|
| `b7ad4f7` | 입력오류 400 · IntegrityError 409 · 가드 5 (#12) | |
| `6d44f64` | `update_project` 기간 date 변환 (#7) | |
| `dc26829` | relay 4xx 통과 · 위경도 범위·bool · 경계 헤더 고정 (#8) | **계약 델타 필요** — §6 |
| `f634948` | 로그인 제한 두 버킷 · `throttle` 무쓰기·정리 (#5) | **Ted 판정 대기** — §5 |
| `a91de2b` | `_FILE` — 세션 비밀값·viz 토큰 (#15) | **Ted 판정 대기**(compose) — §5 |
| `4599ab5` | 거절 격자 미저장 (부록) · `not_implemented` 계수 (부록) | |
| `9aed645` | 업로드 3라우트 `def` + 스트리밍 (#10) | ⚠ **병합 시 떼어낼 수 있는 커밋** |
| (마지막) | 이 기록 | |

`9aed645` 는 핫 파일(`routes/ingestion.py`)을 크게 만지므로 **단독 커밋으로 격리**했다.
떼어내도 앞 커밋(`4599ab5`)의 바이트 무결성 시험 3건은 남아 그물이 유지된다.

## 4. 항목별 — 변경 · 시험 · 전/후

### ㉮ 입력오류 → 400 · IntegrityError → 409 (#12) — `b7ad4f7`

- **예외형 신설** — `services/core-api/src/colab_core/kernel/errors.py:InputError`.
  `ValueError` 를 통째로 매지 않는다: 넓은 형까지 400 으로 접으면 **서버 결함이 「네 요청이
  틀렸다」로 위장**해 감시에서 사라진다. `input_error_response` · `integrity_error_response`
  가 봉투를 만든다.
- **핸들러 등록** — `src/colab_core/app/main.py:create_app` 안, 기존 `HTTPException`·
  `RequestValidationError` 핸들러 옆. 409 본문은 코드 + 고정 문구뿐(`INTEGRITY_MESSAGE`) ·
  SQL·표·열·제약 이름 0 · 사유는 로거 `colab_core.integrity` 로만.
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
- **시험** — `tests/test_upload_streaming.py` 6건.
  - 거절본 미저장 1 · 수용본 저장 1(넓히지 않았음).
  - 바이트 무결성 3 — 5 MiB+ 단건 sha256 일치 · 2파일 묶음 상호 오염 없음 · 격자 교체.
    자리마다 다른 바이트를 써서 **청크 순서가 어긋나면 해시가 깨지게** 했다.
  - 구조 1 — `ast` 로 `AsyncFunctionDef` 0 · `Await` 0 · `shutil.copyfileobj` 호출 존재.
    **문자열이 아니라 구문을 본다** — 문자열로 재면 주석 한 줄이 시험을 뒤집는다.

### ㉴ 미구현 계수 (부록) — `4599ab5`

- `src/colab_core/app/routes/not_implemented.py:1` — 「23 개」 → **4 개**.
  아래 문단들이 23→22→20→19→16→9→12→4 를 한 줄씩 적어 내려가는 동안 첫 줄만 안 따라갔다.
- `tests/test_not_implemented.py` 시험 이름 「5」 → 「4」(단언은 처음부터 `== 4` 였다).

## 5. Ted 판정 대기

### ㈎ 로그인 제한 정책 — 두 갈래

1. **한도·창의 값.** 지금 두 버킷 모두 기존 값(창 900초에 실패 5회)을 그대로 쓴다.
   근거는 그 값 하나뿐이고 정본에 없다(`kernel/config.py` 산문이 「[정본 무근거]」로 명시).
2. **클라이언트 버킷의 열쇠.** 지시대로 `X-Forwarded-For` **첫 홉**으로 세웠다.
   ⚠ **실물과 어긋나는 지점을 그대로 적는다** — `infra/staging/nginx.i2.conf:61` 은
   `$proxy_add_x_forwarded_for` 를 쓴다. 들어온 헤더 **뒤에** `$remote_addr` 를 덧붙이는
   변수라, 클라이언트가 헤더를 실어 보내면 **그 값이 첫 홉이 되고 nginx 가 실제로 본 주소는
   마지막 홉**이다. 그러므로 이 버킷이 늦추는 것은 **헤더를 안 만지는 열거**뿐이고,
   헤더를 돌리는 상대에게는 브레이크가 아니다.
   - 고르는 것 — ⓐ 지금대로(첫 홉, 순진한 열거만 브레이크) · ⓑ 마지막 홉(신뢰 가능,
     다만 프록시 홉 수 가정이 배포에 박힌다) · ⓒ nginx 가 **단독으로 세팅하는 별도 헤더**
     (예: `X-Real-IP` 를 `$remote_addr` 로) — 가장 정직하나 **배포 설정 변경**이라 이 레인 밖.
   - 권고 — ⓒ. 되돌리는 비용은 nginx 한 줄 + core-api 한 줄.
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

## 8. `[미확인]`

1. **업로드 스트리밍의 메모리 사용량을 재지 않았다.** 잰 것은 **바이트 무결성**(sha256
   일치 · 길이 일치 · 묶음 상호 오염 없음)과 **구조**(`async def` 0 · `copyfileobj` 존재)뿐이다.
   → 푸는 법 — 수 GB 파일 하나를 올리며 프로세스 RSS 를 표본화하고, 같은 동안
   `/healthz` 응답 시간을 잰다. 회귀의 본체(「다른 요청이 멈춘다」)는 그 두 번째 값이다.
2. **`X-Forwarded-For` 첫 홉의 실제 신뢰도를 배포에서 재지 않았다.** nginx 설정 문자열
   (`$proxy_add_x_forwarded_for`)로 판정했고 실요청으로 확인하지 않았다.
   → 푸는 법 — staging 에 헤더를 실어 요청 하나를 보내 core-api 가 무엇을 열쇠로 잡는지 본다.
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
