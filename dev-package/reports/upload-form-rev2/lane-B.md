# 레인 B2 — `.npy` 미리보기 변수명이 업로드 파일 ULID 로 보이는 결함

- 결정 근거 = 사용자 결정 2026-09-13(「core-viz 계약에 파일 이름 선택 필드를 추가해 고친다」).
- 기점 = `origin/main` `b5e8e79f` · 브랜치 `worktree-agent-ad0f2a42454c70a94`.

## 1. 원인 (실측)

- `.npy` 는 파일 안에 변수 이름이 없어 이름의 stem 을 변수 이름으로 쓴다
  (`services/viz-render/src/colab_viz/domains/d7_visualization/readers.py` `_read_numpy` · `describe_field` NumPy 분기).
- 저장 배치가 본체를 `fileId` 로 이름 붙인다(`contracts/storage/layout.json` → `kernel/storage_layout.py`).
  파일시스템 어댑터가 `file_name=p.name`(`services/viz-render/src/colab_viz/ports/source.py` `FilesystemSourcePort.resolve`)라
  디스크의 stem = `fileId` ULID 26자.
- 원래 이름의 자리는 core-api 원장뿐 — `d3_file.file_name` · `d5_upload_file.file_name`.
  viz-render 가 그 표를 읽으면 불변규칙 1(도메인은 자기 표 ＋ D1) 위반.

## 2. 계약 diff 요지 (`contracts/seams/core-viz.yaml`)

- `RenderTarget` 에 **선택** 필드 `fileNames: [{fileId, fileName}]` 신설(`minItems: 1` · `additionalProperties: false`).
  `required` 무변 → `describeTarget`·`createRender` 두 op 이 같은 객체를 쓰므로 한 곳 추가로 끝난다.
- `PartialFailure.missingParts[].fileName` 에 산문 추가 — 「`fileNames` 가 주면 그 이름, 없으면 배치의 이름」.
  이름 결정 규칙을 한 자리로 모은다.
- 생성물 재생성 = `frontend/src/generated/fe-core.ts`(+25행). `fe-core.yaml` 이
  `core-viz.yaml#/components/schemas/RenderTarget` 을 `$ref` 하므로 등기부(`contracts/codegen/manifest.toml`) 대상이다.
  **`fe-core.yaml` 은 무수정**이고 프런트 소스도 무접촉 — 선택 필드라 기존 호출이 그대로 컴파일된다.

## 3. core-api 조회 경로와 경계 판정

- 자리 = `services/core-api/src/colab_core/app/routes/preview.py` `_display_file_names` · `_target_with_file_names`.
- **새 조회 경로 0건** — 데이터셋은 내려받기가 쓰는 `d3_catalog.files_for_download`,
  등록 전 업로드는 영수증이 쓰는 `d5_ingestion.UploadLedgerAdapter.files` 를 그대로 부른다. `kind == '본체'` 만 싣는다.
- **새 판정 0건** — 경계는 기존 `_require_target_access` 가 중계 전에 이미 지난다. 이름은 그 뒤에 붙는다.
- **경계 판정** = 넘지 않았다. D3·D5 는 core-api 가 이미 소유·조회하는 자리이고(같은 파일의
  `_with_original_file_names` 가 같은 원장을 이미 읽는다), viz-render 쪽으로는 **식별자와 같은 자리에 값만** 전달한다.
  Port 추가·도메인 재분할·정본 확인 어느 것도 필요하지 않다.
- `fileIds` 로 조각을 고른 요청이면 고른 것만 싣는다. 0건이면 `fileNames` 를 **넣지 않는다**(요청 무변).

## 4. viz-render 변경

- 이름 결정 함수 **하나** = `readers.numpy_variable_name(path, display_name)`.
  `describe_field`(NumPy 분기)와 `_read_numpy` 가 같은 함수를 부른다 —
  `app/routes/describe.py` 머릿말 규율 ②(「고를 수 있다고 한 이름」과 「실제로 그려지는 이름」을 가르지 않는다) 유지.
- 전달 경로 = `app/routes/renders.py` `RenderTarget.fileNames`(pydantic `FileNameHint`) → `display_names()` →
  `jobs.RenderSpec.display_names` → `_read_part` 의 `read_field(display_name=…)`.
  describe 는 라우트에서 같은 map 을 만들어 `describe_field(display_name=…)` 로 넘긴다.
- `missingParts[].fileName` = `jobs._run._missing()` 한 곳에서 같은 map 을 쓴다(종전 3곳 중복 제거).
- **무변경** — 바이트·저장 배치·캐시 키·회수 로직. `source_digest`(캐시 키의 재료)는 `SourcePart.file_name`(디스크 이름)을
  그대로 쓴다. 힌트는 `SourcePart` 를 고치지 않는다.
- 힌트가 없거나 `fileId` 가 대상에 없으면 **현행 동작 그대로**.

## 5. 시험 — red → green

| 시험 | red 근거 (구현 전) | green |
|---|---|---|
| `services/viz-render/tests/test_target_describe.py::test_npy_변수_이름은_fileNames_가_준_원래_이름의_stem_이다` | `KeyError: 'variables'` (라우트 400 — `extra="forbid"` 가 `fileNames` 를 거절) | 통과 |
| 같은 파일 `::test_읽기가_고르는_이름도_같은_값이다` | `TypeError: read_field() got an unexpected keyword argument 'display_name'` | 통과 |
| 같은 파일 `::test_fileNames_가_없으면_현행_그대로다` | 회귀 방지용 — 구현 전에도 통과(선택 필드의 「없을 때 무변」을 고정) | 통과 |
| `services/core-api/tests/test_preview_relay.py::test_describe_target_carries_the_original_file_names` | `KeyError: 'fileNames'` | 통과 |
| 같은 파일 `::test_create_preview_render_carries_the_original_file_names` | `KeyError: 'fileNames'` | 통과 |

- core-api 두 건의 red 는 **구현분만 되돌린 상태**(`git stash push -- …/routes/preview.py`)에서 측정했다 —
  `2 failed, 16 passed`. 되돌림 해제 뒤 같은 파일 `18 passed`.
- 기존 시험 2건의 단언을 고쳤다(`test_create_preview_render_relays_the_request_untouched` ·
  `test_describe_target_relays_request_and_response_untouched`) — 「덧붙는 것은 표시용 이름 하나뿐」으로
  좁혔고 나머지 요청이 그대로인지는 계속 전량 대조한다(`_without_file_names`).

## 6. 게이트 요약줄

| 게이트 | 결과 |
|---|---|
| `contract-lint` | green — `contract-lint green — seam 3건, 룰 위반 0.` |
| `contract-breaking` | green — `contract-breaking green — 기준 HEAD (3건) 대비 파괴적 변경 없음.` (oasdiff: "No breaking changes to report, but the specs are different") |
| `generated-up-to-date` | green — `generated-up-to-date green — 등기부 13건 전부 재생성 일치, 등기부 밖 자칭 생성물 0건.` ／ 재생성 전에는 red 1건(`fe-core.ts`) |
| `service-tests-viz-render` | green — `선택자 «not e2e and not perf» · 수집 447 · 실행 447 · skipped 0 · deselected 42 · failed 0 · errors 0 · 소요 9.9초` |
| `service-tests-core-api` | **준비 red** — 일회용 postgres(`gates/tools/_pg.sh`)가 이 맥 호스트에서 서지 않는다. 아래 §7 |

- 위 4종은 각 1회 단독 실행의 요약줄이다(`COLAB_GATE_REPORT_DIR=dev-package/reports/upload-form-rev2/lane-B`).
- 앞서 선언 5종을 `gates/run.sh task` 한 실행으로도 돌렸고 그 계는 `green 4 / red(판정) 1 / red(준비) 0` 이었다.
  그 1건의 **판정 red 표기는 실체와 다르다** — 게이트가 junit 부재로 그렇게 적었을 뿐 원인은 환경이다(§7).
- `service-tests-core-api` 대신 **직접 실행한 미리보기 중계 시험** — `pytest tests/test_preview_relay.py -q` →
  **`18 passed in 12.03s`** (선언 시험 DB `~/.colab-v2-test.env` 사용).

## 7. `service-tests-core-api` 가 이 호스트에서 서지 않는 이유

- 실측 — 게이트가 세우는 일회용 postgres 의 주소는 도커 기본 브리지 IP(`172.17.0.x`)이고
  (`services/core-api/tests/fixtures/setup-db.sh` 가 `docker inspect … .IPAddress` 로 만든다 · 포트는 미공개),
  **이 맥 호스트에서 그 대역으로 가는 경로가 없다** — 같은 컨테이너에 `docker exec pg_isready` 는 성공하는데
  호스트에서 `socket.connect(('172.17.0.3', 5432))` 는 `TimeoutError`.
- 결과 — DB 를 쓰는 시험이 전부 접속 대기에 걸리고, 게이트는 junit 부재로 **판정 red** 로 표시한다.
  값의 실체는 **준비 red** 다(환경 미구성). 갈라 적지 않으면 코드 결함으로 오독된다.
- 어느 검사에 걸리는가 = `gates/tools/service-tests.sh` 의 core-api 갈래 하나. 게이트 밖(Dockerfile·배포)에는
  같은 검사가 없다. `_pg.sh` 에 `COLAB_PG_NETWORK` 자리는 있으나 기본값이 기본 브리지다.
- **대체 측정** — 이 기계에 선언된 시험 DB(`~/.colab-v2-test.env` 의 `COLAB_CORE_TEST_DATABASE_URL`,
  `127.0.0.1:5432/colab_platform_test`)로 같은 선택자(`not e2e`)를 직렬 실행 —
  **1211 passed / 12 failed / 6 deselected / 321초**.
  실패 12건은 전부 미리보기 밖이고(`test_admin_account_flow` 2 · `test_operator_designation` 1 ·
  `test_ownership_snapshot_publisher` 1 · `test_storage_maintenance` 7 · `test_tracked_sessions` 1),
  로그의 사유는 `password authentication failed for user "postgres"` — 관리자 롤 접속값이 이 로컬 DB 와 맞지 않는다.
  이 12건도 **준비 실패**이고 이번 변경과 무관하다. 미리보기 관련 시험은 전건 통과.

## 8. 완료 정의 대조

- 미달 — `service-tests-core-api` 게이트 green 1회(**미판정**). 막는 것 = §7 의 호스트 네트워크 경로(코드 아님).
  대체 측정에서 미리보기 시험은 전건 통과이나, 그것이 게이트 판정을 갈음하지 않는다.
- 초과 — 없음. 지시문 밖 변경은 `frontend/src/generated/fe-core.ts` 재생성 하나이고,
  이는 등기부가 요구하는 생성물이라 지시문 「계약 ＋ 생성물 재생성」 안이다.
- 무접촉 확인 — `frontend/src/**`(생성물 제외) · `services/pipeline-worker/**` · `contracts/seams/fe-core.yaml` ·
  DB 마이그레이션 0건.

## 8-a. 미완 항목

1. `service-tests-core-api` 게이트 green — **이 호스트에서 미판정**(§7). 다른 호스트(브리지 라우팅이 있는
   리눅스/WSL) 또는 후속 ①이 선행돼야 한다. 대체 증거는 위 `18 passed` 와 전수 `1211 passed / 12 failed`.
2. 인계 토큰(`COLAB_HANDOFF`) 미발급 — 아래 8-b.
3. `service-tests-core-api` 판정처 = PR CI 의 `service-tests` 매트릭스
   (`.github/workflows/ci.yml` 의 `service-tests:` 잡 — `matrix: service: [core-api, …]` ·
   같은 잡의 마지막 스텝이 `./gates/run.sh service-tests-${{ matrix.service }}` 를 실행) ·
   이 맥 호스트의 값은 **준비 red**(도커 브리지 IP 미라우팅 · §7) — 게이트 밖 검사가 아니라 CI 에서 판정된다.
4. 잔여 지적 1건 처리 — `GridRejection.fileName`(위 §9 후속 ③)을 표시 이름 맵으로 돌렸다(레인 F1).
   `jobs.display_file_name` 한 자리가 `missingParts[].fileName` 과 `GridRejection.fileName` 둘을 모두 고르고,
   힌트가 없으면 종전대로 디스크 이름이다. 시험 `test_grid_rejection_and_layer_urls.py`
   `test_거절당한_파일_이름은_fileNames_가_준_원래_이름이다` 1건 신설(red → green).

## 8-b. 인계 토큰이 발급되지 않는다 (하네스 교착)

- `lifecycle handoff --mode=complete` → `exit 78 · lifecycle evidence blocked: gate failures remain`
  (`.claude/hooks/lifecycle_contract.py:186 verify_task_report` → `validate_report`).
- lane-worker 는 `complete` 외 모드가 거부된다(같은 파일 `stop()` — `lane completion requires current gate evidence`).
  그래서 「구현 완료 · 게이트 1건 판정 불가」 상태를 기록할 모드가 없다.
- 종료 훅 `.claude/hooks/lane-gate-summary.sh` 는 최종 메시지에 `COLAB_HANDOFF` 한 줄을 요구하지만,
  그 줄은 위 도구만 발급한다. 손으로 적은 줄은 같은 검사에서 다시 거부되므로 **위조는 해결이 아니다.**
- green 으로 만들 수단 셋은 전부 금지 — 게이트 스크립트 수정(레인 소유 밖 · 우회 금지) ·
  선언 게이트 축소(「작업자가 줄여 성공시키지 않는다」) · 마커 위조.
- 재측정(기계 유휴 상태) — `172.17.0.2`(2주째 가동 중인 `colab_local_pg`)·`172.17.0.3`(일회용) 둘 다
  호스트 `socket.connect` `TimeoutError`. `gates/tools/_pg.sh` 머릿말이 「포트를 하나도 publish 하지 않는다 ·
  모든 질의는 `docker exec` 로 돈다」를 설계로 못 박았는데, `service-tests.sh` 만은 그 주소를
  **호스트 pytest** 에 넘긴다 — 리눅스/WSL 에서는 브리지가 호스트에서 라우팅되므로 성립하고 맥에서는 성립하지 않는다.
- 따라서 판정은 브리지 라우팅이 있는 호스트에서 받거나, 후속 ① 을 먼저 처리해야 한다.

## 9. 후속 항목

1. `gates/tools/service-tests.sh` 의 core-api 일회용 postgres 를 **호스트에서 닿는 주소**로 낸다
   (포트 임시 공개 또는 `COLAB_PG_NETWORK` 기본값) — 지금은 맥에서 이 게이트가 영구 준비 red 다.
2. `~/.colab-v2-test.env` 의 관리자 롤 접속값과 로컬 `colab_platform_test` 의 롤이 어긋난다 — 위 12건의 사유.
3. `GridRejection.fileName`(`jobs._read_part` 의 `e.rejection(file_name=part.file_name)`)은 아직 디스크 이름이다.
   같은 뿌리이나 이번 범위 밖이라 건드리지 않았다.
