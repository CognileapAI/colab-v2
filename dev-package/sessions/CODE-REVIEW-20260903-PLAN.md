# CODE-REVIEW-20260903-PLAN — 개선 집행 계획·기록 (lane-review-clean)

> 근거 — `CODE-REVIEW-20260903.md`(15건 + 부록). 목적 — 에이전트 개발 최적화(클린아키텍처·클린코드 판단기준).
> 경계 — 다른 세션이 로컬 `main` 에 병행 커밋 중. 이 회차는 `lane-review-clean` 과 그 하위 레인 브랜치에서만 작업. **main 병합·main push·대장 번호 발급 없음**(등재문은 초안으로만).
> 어드바이저 게이트 ① — 2026-09-03 승인(수정 조건부). 반영 내용은 §2 각 레인에 표기.

## 1. 공통 규칙 (모든 레인)

- 워크트리 `.claude/worktrees/lane-rc-<x>` · 브랜치 `lane-rc-<x>` · 기준 `lane-review-clean`. 체크아웃 하나에 쓰기 에이전트 하나.
- 편집 면은 레인별 고정. 읽기는 자유. 병합·순서·충돌 해소는 오케스트레이터만.
- 편집 금지 — `contracts/**`(동결 규약) · `dev-package/{PLAN-SoT.md,work-items.yaml,03-HANDOFF.md,DEPLOY-CURRENT.md}` · `infra/**` · compose 파일. 계약 변경이 필요하면 **멈추고 보고** + 레인 기록에 계약 델타 초안.
- 결함마다 **실패 시험 먼저**, 그다음 수정. 기준선(수정 전) 계수를 먼저 기록. 기존 실패는 보고만, 레인에서 고치지 않음.
- 핫 파일(`routes/catalog.py`·`domains/d3_catalog.py`·`routes/ingestion.py`·`frontend/test/upload.test.tsx`)은 최소 diff. 재포맷·import 재정렬 금지. 떼어낼 수 있는 변경은 **별도 커밋**.
- 운영 `colab_v2_staging_*` — 읽기 전용, 컨테이너 조작 금지, 접속 문자열 출력 금지. 일회용 Postgres 는 `--rm` + tmpfs + `PGDATA` + 호스트 포트 미공개(core-api 는 `tests/fixtures/setup-db.sh`).
- 산출 — `dev-package/sessions/CODE-REVIEW-20260903-<x>.md`(신규): 변경(파일:앵커) · 추가 시험 · 계수 전/후 · 못 잰 것 `[미확인]` · 유보 항목 · 등재문 초안(번호 없음). 커밋은 한국어, 자기 브랜치에만. push 없음.
- 지시가 실물과 어긋나면 멈추고 보고.

## 2. 레인

| 레인 | 편집 면 | 항목 | 완료 정의 |
|---|---|---|---|
| A `ci-honesty` | `.github/workflows/ci.yml` · `gates/run.sh` · `gates/tools/service-tests.sh`(신규) · `gates/tools/_expect_pool.sh` 및 rc=78 을 「기대한 red」로 세는 셀프테스트 · `gates/README.md` · `services/ai-service/pyproject.toml` + ai-service 시험 6파일의 `dictdb` 마커 | 서비스 pytest 4종을 **게이트 스크립트**로 CI 에 연결(수집 0·skip·fail → red, deselected 계수 출력). 대상 — viz `not e2e and not perf` · pipeline `not e2e and not dbint` · ai `not dictdb` · core-api 전체(일회용 Postgres + `setup-db.sh`). 각 서비스 필터 또는 contracts 변경 시 실행. frontend 게이트 2종은 `frontend` 변경에도 실행(중복 실행 없음). `run.sh selftest` 가 18종 전부 또는 명시 면제 + 계수(3상태). rc=78 준비실패와 기대 red 를 가르고 실패 픽스처로 증명. `artifact-ownership.toml tolerate` 는 보고만. | 새 CI 명령 전부 로컬 green 계수 기록 후 연결. `selftest` 집합 green. YAML 파싱 검증. `setup-db.sh`·타 서비스 pyproject 는 편집 금지. |
| B `core-api` | `services/core-api/**` | 입력오류 전용 예외형 → 400, IntegrityError → 409 핸들러 · 가드 5(`access.py` ULID, `session_token.py` 비ASCII → 401, 기간 자유문자열 → 400, `validate_human_metadata` topic, `project.py` 생성 이름 strip) · `update_project` 기간 `YYYY-MM` → date · `relay.py` viz 4xx 상태·본문 통과(연결·5xx 만 503) · `preview.py` lat/lon 범위·bool · 로그인 제한 = 접근코드 해시 버킷 + 클라이언트(`X-Forwarded-For`) 버킷 동일 5/900, `throttle.py` `blocked()` 무쓰기 + 정리 · `config.py` `_FILE`(session_secret·viz_service_token) · `ingestion.py` `_store` 를 kind 검사 뒤로 · 업로드 3라우트 `async`→`def` + 스트리밍 복사(**별도 커밋**) · `d10_*` degradedReason 원시 예외 제거 · `value_lookup.py` 투영 밖 → 200+사유 · relay 5호출 전부 `_scope_headers` 적용을 **시험으로 고정** · `not_implemented.py` 문서 계수 | 기준선 후 전체 suite 일회용 DB 에서 green(계수). `import-boundary`·`banned-import`·`ai-no-lineage-write`·`db-boundary` green. 스키마 변경 없음. |
| C `viz-render` | `services/viz-render/**` | 테넌트 경계 — POST/GET `/renders`·screenshot·lookupValue 에서 `X-CoLAB-Lab` 을 job 에 저장·대조(불일치 404, 헤더 없음 400). **타일은 서명만**(브라우저 직접 호출, 헤더 없음) · `regenerate` 무효화를 렌더 완료 뒤 `_run_and_plan` 안에서 적용, removed 를 job 에 기록 · `_read_netcdf` `instant` 존중(정확 일치, 없으면 NOT_RENDERABLE 사유) + 캐시 키에 instant · `_grid_digest` 강화 · JobStore 만료(`expires_at`) 후에만 축출(410 유지, **완료 직후 해제 금지** — 타일이 메모리 래스터를 읽음) + `_produced_for` 색인 · 스크린샷 레이어 상한 = 선언된 400 + `details.maxLayers`(계약 델타 초안: `maxItems`) · `triggers.py` 봉투 단위 격리 + `_done` 키 ack · `_FILE`(서비스 토큰·타일 서명 비밀) | suite `not e2e and not perf` green(≥199+신규). e2e/perf 시험에도 헤더 추가 후 `[미확인]` 표기. |
| D `pipeline-worker` + ai 1행 | `services/pipeline-worker/**` · `services/ai-service/src/**`(별도 커밋 1건) | `axis.py` ndim 검사 선행, `np.load` 실패 → `AxisUndeterminedError` · `process_upload` 데이터 오류를 `upload.failed` 로 분류(틱 전체 롤백·크래시 루프 제거) + `serve()` 보호 · `parse.py` NetCDF 격자 (rows, cols) 를 축 역할로 · `cog.py` NaN 좌표 마스킹 + 퇴화 경도 범위 검사 · `hsr.py` 0블록 → `HsrParseError` · `d5_ingestion.py` attempt 증가 + `redelivery` 사실화(DLQ 유보) · ai-service `search_datasets` `async def`→`def` | suite `not e2e and not dbint` green(≥200+신규). `stage2-markers` green. dbint 는 일회용 DB 가능 시 실행, 아니면 단위 + `[미확인]`. `upload.failed` 에 새 필드·enum 이 필요하면 **멈추고 보고**. |
| E `frontend` | `frontend/**` | 픽스처 폴백 제거(catalog/detail/project/graph Source) — 401 은 기존 인증 경로로, 그 외는 오류 상태 + 다시 시도, 픽스처는 명시 주입(시험)만 · `AuthGate` `/me` 실패 → 오류 상태 + 재시도 · `ValueLookupPanel` 순서 보호 · `PreviewPanel` `Number('')` · `visits.ts` 일 경계 · 업로드 `PreviewPanel` 폴링 취소(**별도 커밋**, 중복 제거는 유보) | vitest + `tsc --noEmit` green. `frontend-typecheck`·`frontend-test` green. |
| G `codegen-ids` | `contracts/codegen/**` · `services/*/kernel/ids.py` | A~E 병합 뒤에만 착수. 전제 — B/C/D 가 `ids.py` 를 건드리지 않았을 것 · `contracts/codegen/**` 은 동결 표면이 아닌 도구라는 명시. 시간 부족 시 작업항목 #1 로 유보. | `generated-up-to-date` green + 4서비스 suite green. |

## 3. 병합·검증 순서 (오케스트레이터)

1. 게이트 ② — 레인별 산출을 실물과 대조(주장 ≠ 실측).
2. 병합 D → C → B → E → A(CI 는 최종 트리에 대해 마지막).
3. 최신 `main` 병합 → `./gates/run.sh all -j 1` → 서비스 suite 4종 + `tsc` + `vitest` 를 병합 트리에서 재실행, 계수 기록(`run.sh all` 은 pytest/vitest 를 돌리지 않음).
4. `lane-review-clean` push → **draft PR**(Actions 실행 확인 목적. main 병합 아님). core-api CI 잡이 환경 사유로 red 면 그 잡을 제거하고 사유 기록.
5. 전부 green 일 때만 G 착수.

## 4. 유보 — 다음 회차 작업항목 초안 (번호 없음, 순서 = 권고 착수 순서)

1. 커널 손사본 → codegen 통일(`ids.py`×4 · `errors.py`×2 · FileKind 리터럴 · ULID 정규식 · 권한 스위치 · 봉투 해석 · `NotImplemented`) — 레시피 = `gen_storage_layout.py` + `manifest.toml` 항목 추가.
2. 쓰기 라우트 권한 가드 존재를 판정하는 게이트(현재 0).
3. 백엔드 pydantic 모델을 seam 에서 생성(손검사 47곳·`body: dict` 19곳 대체).
4. 페이징 — 서버 `totalCount` 실값 + 클라이언트 cursor + 더 보기.
5. ai-service 계약 정렬(serviceToken · `/ai/v1` 접두).
6. compose 비밀값 `_FILE` 전환(배포 변경, Ted go/no-go).
7. `artifact-ownership.toml tolerate=true` 기한(Ted 판정).
8. 계보 수정 UI 배선(서버 4 op 있음, 화면 호출 0).
9. D5/D7 격자 탐색 알고리즘 통일(등록 수용 기준 변경 → 상품 판정).
10. 효율(원본 전체 sha256 매 클릭 · 산출물 재사용 0 · `_compose` 전량 적재 · 5초 엔진 재생성 · 노드당 1쿼리).
11. 발행 재시도 DLQ · 문서 절대경로 게이트 · 업로드 PreviewPanel 중복 제거.
12. `upload.failed reason=내부 오류` 비율 경보 · pipeline-worker `print` → logging 통일 · `_produced` 색인 정리 · NOT_RENDERABLE 시각 불일치 전용 문구(정본).
13. CI 인프라 — `schema-gates` 에 일회용 DB 기동·마이그레이션·URL export 스텝 · `planning-gates` 정본 폴더 체크아웃(둘 다 main 사전존재 red, §5-7).

## 5. 실행 기록 (2026-09-03 실측)

### 5-1. 하네스 사고와 우회 없는 재기동
- 손으로 만든 형제 워크트리 `lane-rc-a..e` 에서 서브에이전트 Bash·git 전부 거부(부모 세션의 워크트리 핀 상속). 레인 5개 편집 0 으로 정지.
- 재기동 = `Agent(isolation:"worktree")` + 첫 명령 `git merge --ff-only lane-review-clean`(기준 `d4d11b5`). 손 워크트리·브랜치 삭제. 이후 레인 브랜치 이름은 `worktree-agent-<id>`.

### 5-2. 레인 결과 (게이트 ② = 어드바이저 수용 검토 · 수정 회차 = 별도 에이전트가 레인 브랜치 위에 적용)

| 레인 | 브랜치(＋수정) | 커밋 | 시험 계수 전 → 후 | 게이트 | ② 판정 |
|---|---|---|---|---|---|
| D | `worktree-agent-a160bc4c840f9061d` | 3 | pipeline `not e2e and not dbint` 200 → 225 · dbint 15 → 20(일회용 PG) · ai 88 → 94 | stage2-markers green | accept(후속 2건 → F) |
| C | `…a9df4b7601bb30d66` ＋ `…a122ec91d6f0834c0` | 6 ＋ 3 | viz `not e2e and not perf` 199 → 250 → 259 | import-boundary·banned-import green · render-latency·e2e-format-coverage red(준비, 원천 마운트 부재) | accept-with-fixes 3건 적용 |
| B | `…ac72b799fc10afb59` ＋ `…a5a9e4423c858ed14` | 8 ＋ 3 | core-api 전체 553P/5F → 614P/5F(5F = e2e 원천 부재, 기존) · `not e2e` 613 → 620 | import-boundary·banned-import·ai-no-lineage-write·db-boundary green | accept-with-fixes 2건 적용 |
| E | `…a146c87cfdffbbbf2` ＋ `…a717df09dcc28689b` | 4 ＋ 2 | vitest 32파일/520 → 35/563 · tsc 0 | frontend-typecheck·frontend-test green | accept-with-fixes 2건 적용 |
| A | `…a26a95673bf502c9e` | 6 | CI 에 실리는 서비스 pytest 케이스 69 → 1070 · selftest 선언 14/실행 14 → 선언 19/실행 17/명시 면제 2 | service-tests ×4 green · service-tests-selftest 9케이스 · db-boundary green | accept-with-fixes 1건 → F |
| F(후속) | `…a992b5e50a78fd047` | 5 | pipeline 225 → 231 · viz 259 → 269 · ai(`not dictdb`) 125 → 130 | selftest 집합 동일 · stage2-markers green | D·B·A 후속 6항목 |
| G2 | `frontend-fixture-reach` 게이트 등재 — 결과는 §5-6 | | | | |

### 5-3. 병합 (오케스트레이터 직렬, 전부 `--no-ff`, 텍스트 충돌 0)
D `11462b5` → C `660f8fe` → E `80296b6` → B `21cfb1f` → A `ad2fe06` → F `3deba47` → `main` `1a26372`(main 측 10커밋 = 문서·대장만, 겹치는 파일 0).
**main 병합 대상 = `lane-review-clean` 하나** — 레인 브랜치 전부와 수정 회차를 포함한다. 대장 번호 미발급. draft PR #2 = GitHub Actions 실행 확인용.

### 5-4. 통합 트리 `1a26372` 실측 (오케스트레이터 재실행)
- pipeline-worker 231 passed · viz-render 269 · ai-service 130(`not dictdb`) · core-api 620 passed / 6 deselected(`service-tests-core-api` 게이트, 일회용 PG, 86초) · tsc 0 · vitest 35파일/563.
- `./gates/run.sh all -j 1`(게이트 입력 env 주입) — **green 47 · red(판정) 0 · red(준비) 1**(`rls-effect-selftest`, 일회용 postgres 준비 대기). 단독 재실행(`COLAB_GATE_JOBS=1`) **green**. 게이트 총수 43 → 48(service-tests 4 ＋ selftest 1). `contract-breaking` green.
- 병합 지도 노트(`dev-package/notes/REFACTOR-MERGE-MAP-20260903.md` §3) ⓐ 에 대한 답 — core-api relay 5호출 전부 `_scope_headers`(`relay.py` 152·168·184·200·207, 시험 5파일) · 프론트는 viz 를 `tileUrlTemplate`(서명) 로만 접근 · 〈304〉 경로는 core-api op → `values.py` 경계 요구 유지. ⓒ 501 계수 23 → 4 는 대장 한 줄 정정. ⓓ 는 G2 로 등재.

### 5-5. Ted 판정 대기 (코드로 결정하지 않은 것)
1. 계약 델타 — `fe-core.yaml` `createPreviewRender`·`listPalettes`·`lookupDatasetValue` 에 410/413/415/422 선언(코드는 이미 통과, 되돌릴 자리 `relay.py:PASS_THROUGH_STATUSES`) · `core-viz.yaml` 경계 헤더 선언 · `getRender` 400 · `ScreenshotRequest.layers maxItems 8`.
2. 로그인 제한 클라이언트 버킷 = `X-Forwarded-For` **마지막 홉**(nginx 관측값). nginx 앞에 LB 가 생기면 단일 버킷(= 기준선 동작). 배포측 후속 = nginx 가 `X-Real-IP` 세팅.
3. 캐시 키에 시각·격자 digest 추가 → 배포 뒤 기존 산출물 미스 → 재굽기 ＋ 소유 네 등급 재실측(병합 지도 ⓑ).
4. `artifact-ownership.toml tolerate=true` 기한 · compose 비밀값 `_FILE` 전환 · `expires_at` 없는 등록 데이터셋 렌더 수명 · DLQ.
5. 미확인 — GitHub Actions 실제 실행(draft PR #2 로 확인) · e2e/perf/dbint/dictdb 미실행 집합(원천 마운트·DB) · 업로드 스트리밍 RSS·`/healthz` 실측 · 각 레인 기록의 `[미확인]` 절.

### 5-6. G2 결과 (`worktree-agent-ac42c923277ef05d0`, 병합 `7d57028`)
- `frontend-fixture-reach` 게이트 신설(`gates/tools/frontend-fixture-reach.sh` + selftest 6케이스 + 픽스처) · `ALL_GATES` 등록 · CI `frontend-gates` 잡에 연결 · `reachable-from-entry.mjs` 에 진입점 인자 1줄.
- 오케스트레이터 재실행 — 게이트 green(진입점 `src/main.tsx` 에서 도달 128 · 금지 모듈 0) · selftest green(red 3 · red(준비) 2 · green 1). selftest 집합 선언 19 → 20, 면제 2 유지. 게이트 총수 48 → 50.
- `gates/README.md` CI 표의 고정 계수(「실행 17」)를 파생 표기로 정정(오케스트레이터).
- draft PR #2 첫 Actions 실행 — `changes`·`boundary-gates`·`contract-gates`·`dormant-tests` pass · `frontend-gates`·`planning-gates`·`schema-gates`·`service-tests`×4 fail(6~30초) → 원인 진단은 §5-7.

### 5-7. Actions 실패 진단 (run 33732752341, 서브에이전트 실측 `tmp/ci-diagnosis.md`)
- **이 브랜치 신규 결함** — `service-tests` ×4 · `frontend-gates`: exit 126 `Permission denied`. 게이트 스크립트 20개가 인덱스에 100644(실행비트 없음). 이 호스트는 NTFS 마운트(`core.filemode=false`)라 로컬 chmod 가 추적되지 않아 로컬 `run.sh` 는 통과했다. 그중 12개는 main 에도 100644 로 있으나 그 게이트를 exec 하는 CI 잡이 main 에서 실행된 적이 없어 드러나지 않았다. 조치 = `update-index --chmod=+x` 20건(오케스트레이터), 재실행으로 확인.
- **main 사전존재(이 회차 변경 아님)** — `schema-gates`: `schema-diff` 가 `COLAB_APPLIED_DB_URL_PLATFORM/_AI` 미선언으로 exit 78(잡에 DB 기동·마이그레이션·URL export 스텝 자체가 없음, main run 33703687384 동일). `planning-gates`: `planning-freshness` 가 「정본 폴더가 없다」 exit 1(정본이 레포 밖 형제 폴더, CI 는 레포만 체크아웃 — main run 33715144510 동일). 둘 다 인프라 결정 필요 → §4 유보 13.
- `gate-selftest`: 첫 실행에서 `in_progress` 로 남음(도커 기반 셀프테스트 3종이 Actions 에서 처음 도는 회차). 재실행에서 관찰 → 결과는 §5-8.

### 5-8. Actions 재실행 결과
- 실행비트 수정 후 run 33733366974(f300fe1) — `service-tests` ×4 success(core-api 일회용 Postgres 러너에서 동작 확인) · `frontend-gates` failure(vitest 563 전건 통과인데 `frontend-test.sh` 건수 추출 정규식이 ANSI 색 코드에 걸림) · `gate-selftest` failure(39종 중 35 green, red 4 = 위 정규식 1 ＋ `gate-selftest` 잡에만 pyyaml 설치 스텝 부재로 `db-boundary`·`seam-consistency`·`work-item` 셀프테스트 import 실패). 진단 `tmp/ci-diagnosis-2.md`.
- 조치 f5f8440 — `frontend-test.sh` vitest 호출에 `NO_COLOR=1 FORCE_COLOR=0` ＋ 출력에서 ESC 시퀀스 제거 후 판정(로컬 증명: 색 섞인 요약줄 → 제거 전 빈 값, 제거 후 563) · `gate-selftest` 잡에 boundary-gates 와 같은 pyyaml 설치·확인 스텝.
- f5f8440·빈 커밋 2f86587 두 push 모두 `pull_request` 실행이 생성되지 않음 → `[미확인]`(원인). `workflow_dispatch` 로 수동 실행 33737748503(head 2f86587).
- **최종 — success 10 / failure 2**: success = changes · contract-gates · boundary-gates · dormant-tests · frontend-gates · service-tests(core-api·ai-service·viz-render·pipeline-worker) · gate-selftest. failure = `schema-gates`(적용 DB URL 미선언) · `planning-gates`(정본 폴더 미체크아웃) — 둘 다 main 사전존재, §4 유보 13.
- 이 회차가 CI 에 새로 실은 것: 서비스 pytest 1070 케이스(core-api 620 · viz 269 · pipeline 231 · ai 130 은 로컬, 러너 계수는 잡 로그) · frontend 게이트 3종(typecheck·test·fixture-reach) · selftest 집합 20(면제 2) · db-boundary.

### 5-9. 등재문 초안 → **발급 완료 `〈307〉`** (2026-09-03 · `PLAN-SoT §9` 직렬 발급 · 발급 직전 최댓값 306 실측)
> ⚠ **아래는 초안이고 정본이 아니다.** 병합 커밋 `a1ff6af` · 최종 트리 실측 · Actions 결과 · main 17차 충돌 해소를 반영한 **확정 문면은 `PLAN-SoT §9 〈307〉`** 에 있다. 값이 갈리면 정본이 이긴다.

| 〈307〉 | **코드리뷰 개선 회차 — 경계·검증·정직한 빈 상태·검사기 판정 (레인 6 ＋ 후속 2)** | **집행 ＋ 실측 (2026-09-03 · `lane-review-clean` · `sessions/CODE-REVIEW-20260903{,-PLAN,-A,-B,-C,-D,-E,-F,-G2}.md` · draft PR #2 · main 병합은 Ted 승인 대기)** ㉮ 근거 = `/code-review` xhigh 15건 ＋ 부록(CONFIRMED 69 · PLAUSIBLE 4 · REFUTED 1). ㉯ A ci-honesty — 서비스 pytest 4종을 게이트 `service-tests-*` 로 CI 연결(CI 케이스 69 → 1070) · frontend 게이트가 frontend 변경에도 실행 · `db-boundary` CI 연결 · selftest 3상태(선언 20 · 실행 18 · 면제 2) · rc=78 준비실패를 기대 red 로 세지 않음 · 실행비트 20건 인덱스 명시. ㉰ B core-api — 입력오류 400 · IntegrityError sqlstate 분기(23505→409 · 23514→400 · 그 외 500) · 가드 5 · `updateProject` 기간 date · viz 4xx 통과 · 로그인 제한 코드해시 ＋ 클라이언트(XFF 마지막 홉) 버킷 · `_FILE`(session_secret · viz token) · 업로드 스트리밍. ㉱ C viz-render — 테넌트 경계(타일은 서명만) · 무효화를 완료 경로에서 · NetCDF `instant`(축 위치) ＋ 캐시 키 · 만료 뒤 축출(410 유지) · 스크린샷 층 상한 400 · 트리거 봉투 격리 · `_FILE`. ㉲ D pipeline-worker — 데이터 오류 → `upload.failed`(크래시 루프 제거) · axis ndim 선행 · NetCDF (rows, cols) · COG NaN 좌표 · HSR 0블록 · 재전달 attempt/redelivery · ai-service `search_datasets` 스레드풀. ㉳ E frontend — 픽스처 폴백 제거(401 → 인증 경로 · 그 외 오류 상태 ＋ 다시 시도 · 실패 자리 「0건」 없음) · AuthGate 재시도 · 값 조회 순서 보호 · 폴링 취소 · G2 `frontend-fixture-reach` 게이트. ㉴ 통합 트리 실측 — core-api 620 · viz 269 · pipeline 231 · ai 130 · vitest 563 · tsc 0 · `run.sh all -j 1` green 47 / 판정 0 / 준비 1(단독 green) · 게이트 43 → 50. ㉵ 판정 대기 = PLAN §5-5 · 유보 = PLAN §4(13). | 2026-09-03 |

### 5-10. main 17차 병합 충돌 해소 (오케스트레이터, 병합 커밋 `f6d2af8`)
- 대상 — `main` `6fa0694`(17차 〈303〉 자기 연구실 묘비 410 · 〈306〉 「담당」 열 정본 하차)를 `lane-review-clean` `0bbed01` 에 `--no-ff`. 텍스트 충돌 3파일 · 자동 병합 16파일.
- `frontend/src/components/detail/detailSource.ts` — 양쪽 보존. 픽스처 폴백 0건(레인 E) ＋ 410 → `DatasetTombstone`(17차, 404 검사보다 앞). `defaultDetailSource` = `apiDetailSource()` 한 줄 · `fixture.ts` import 0건.
- `frontend/src/components/detail/useDatasetDetail.ts` — `DetailState` 다섯: loading · ready · gone · tombstone · error. 묘비 아닌 실패를 `loading` 으로 되돌리던 main 측 갈래는 `error` 로 둔다(레인 E 의 영구 빈 화면 수정 유지).
- `frontend/src/routes/DatasetDetailPage.tsx` — 자리 셋을 나란히 세운다: `detail-gone`(404 · `Policy_공통_기반 §2.4` 중립 문구) · `detail-tombstone`(410 · `Policy_데이터셋_상세 §9` 축자) · `detail-error`(`LoadFailure` ＋ 다시 불러오기). 한 응답은 한 자리만 세운다.
- 「담당」 열 — 프론트 코드·계약에 애초 0건(〈306〉 은 정본 문서만 고쳤고 자동 병합). `UsageSection.tsx` 의 「계약 `DatasetProjectUse` 에 담당이 없다」 주석이 여전히 실물과 일치.
- 시험 실측(2026-09-03) — `tsc --noEmit` 오류 0건 · `vitest run` 36파일 570건 통과(563 → +7 = `r17-tombstone`) · 실패 0건. `honest-source-20260903`·`screen-guards-20260903`·`r17-tombstone` 전부 통과.
- 게이트 8종 green — frontend-typecheck(오류 0) · frontend-test(570) · frontend-fixture-reach(도달 128 · 금지 모듈 0) · generated-up-to-date(등기부 4건 일치) · seam-consistency(G-e 380 · G-b 10 · ㉠ 0 · ㉡ 18) · contract-lint(seam 3 · 위반 0) · service-tests-core-api(실행 624 전건 통과 · skipped 0 · deselected 6 · 85.2초 · 일회용 Postgres) · import-boundary(8 kept · 0 broken).
- push 0 · `main` 병합 0 · 대장 번호 발급 0 · 운영 스택 무접촉.
- `[미확인]` — `./gates/run.sh all` 전량과 GitHub Actions 는 이 병합 뒤로 재지 않았다. 푸는 법 = 통합 트리에서 `./gates/run.sh all -j 1` 재실행 · PR 재실행.
- 최종 트리 `ae322b6` 게이트 전량 — `./gates/run.sh all -j 1`(게이트 입력 env 주입) **green 50 · red(판정) 0 · red(준비) 0**(19:45). main `6fa0694` 대비 병합 시뮬레이션 충돌 0. main 병합은 Ted 가 main 체크아웃에서 `git merge --no-ff lane-review-clean` 로 실행.
