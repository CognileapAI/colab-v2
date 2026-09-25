# Intent: K3/K4 측정 코퍼스를 dev 재생성 28건으로 넓히고 골든 ID 를 다시 박는다

메타 — 발의자: Ted(「권고대로 해」 · 2026-09-24) · 정리 Claude(researcher) · 작성 2026-09-24 · 승인 **사용자 서명 2026-09-25 — ① 옛→새 대응 9행 + 이름→ID 28행 · ② 12문항 scope·required**(`dev-package/reports/corpus-expansion/wu4-golden-proposal-2026-09-25.md` §1·§2 서명 줄). 이 서명을 적은 커밋이 승인이다(`README.md` 「승인 = 커밋」). 아래 「제약」의 dev 상시 승인은 2026-09-25 개정된 `.agents/rules/deploy.md` 11번이 대신한다 — 비어 있지 않은 dev 의 reset 은 회차별 명시 GO 와 사용자 터미널 토큰이 필요하다.

## 문제

- K3·K4 실측이 서 있는 코퍼스는 참조 스냅샷 **9건 · 계보 6간선**이다(`eval/k4-search/fixtures/reference/dev-data-snapshot.json`).
  그 9건의 **자동 메타가 전부 비어 있다** — 실측으로 확인한 값은 `file_extension`·`bundle_file_name` 둘뿐이고
  `format`·`variables`·`period_start/end`·`crs`·`grid` 는 9건 전건 `null` 이다.
  그 사실은 제품 시험이 축자로 적고 있다 — `services/core-api/tests/test_k3_lineage_probe.py:96-112`
  「⚠ 값을 **지어내지 않는다** … dev 에서도 `crs`·`grid`·`variables`·기간은 전부 비어 있고 `bundle_file_name` 만 있다.
  그 빈곤 자체가 실측의 표본 한계」.
- 그래서 K3 축 대조는 **비교할 값이 애초에 없는 상태**를 재고 있고, K4 검색은 자동 메타 벡터가 빈 채로 세 벡터 중 하나를 잃는다.
- 그 9건이 비어 있는 까닭 = 적재 경로가 **API 직적재**(`infra/staging/load-seed.py` · `infra/staging/manifest-refdata.json` 의 `LD-*` 14묶음)라
  업로드 분석(pipeline-worker)을 타지 않았다. 출처는 `dev-package/sessions/20260912-ai-search-data-readiness.md`
  「dev 실측 — 2026-09-12 후속」 절의 매니페스트 키→dev dataset ID 표다.
- 한편 **dev 플랫폼 DB 는 지금 비어 있다** — 데이터셋 0 · 계정 0 · 연구실 1 · 자동메타 0 · 계보 0(2026-09-24 읽기 전용 확인).
  즉 `01M1SC…` 고정 ID 는 **이미 아무것도 가리키지 않는다.** 골든셋·계보 정답·픽스처가 죽은 ID 를 박고 있다.

## 원한 결과 (proposed outcome)

검증 가능한 문장으로 — 전부 실측으로 센다.

1. dev 플랫폼에 **데이터셋 28 · 프로젝트 4 · 계보 간선 18 · 「미지정」 가공 단계 0 · 프로젝트 미연결 0** 이 선다
   (기대값의 정본 = `dev-package/tools/dev-seed/plan-manifest.yaml` 의 `expected: {datasets: 28, edges: 18, data_bytes: 3641736593}`).
2. 28건의 `d3_dataset_autometa` 가 **채워진 칸 수로** 보고된다 — 축별 실측 fill 표(아래 「판정 기준」 §2).
3. `eval/k4-search/fixtures/reference/dev-data-snapshot.json` 이 **v2**(자동 메타·변수 행·계보를 실은 형식)로 다시 잡히고,
   그 안의 ID 가 전부 재조회 시점의 dev 실물이다.
4. 아래 「영향 범위」의 ID 고정 파일이 **한 건도 남김없이** 새 ID 로 다시 박히고, 이름→새 ID 대응표에 Ted 서명이 있다.
5. K4(`golden_baseline.py --mode literal` · `--mode expanded`)와 K3(`k3_probe` 두 시험 + `llm_lineage_probe.py`)가
   **새 코퍼스에서 준비 실패 0건으로 완주**한다. 판정 red 여부는 이 intent 의 목표가 아니다(측정이지 게이트가 아니다).

## 영향 범위

- 사용자 / 화면: dev 환경 한정. staging·product 무접촉. dev 화면의 카탈로그·계보·검색 결과가 전부 바뀐다.
- 서비스 · 스키마 · 계약: **스키마 변경 0.** 제품 코드 변경 0 을 목표로 한다(픽스처·평가 재료·도구만 바뀐다).
- ID 를 박고 있는 자리(전수) —
  | 파일 | 무엇이 박혀 있나 |
  |---|---|
  | `eval/k4-search/fixtures/reference/dev-data-snapshot.json` | 데이터셋 9 · 파일 ID · `parents` 6간선. **모든 것의 뿌리** |
  | `eval/k4-search/golden-cases.json` | 12문항의 `scope`·`required` 에 `01M1SC…` |
  | `eval/k3-lineage/lineage-cases.json` | 자식 4 · 부모 6 의 `child_dataset_id`·`parent_dataset_id` |
  | `eval/k4-search/fixtures/reference/expanded-normalized-02.json` | `01M1SC…` **228 회**(소비되는 것은 `expansion.responses[].interpretation`·`dictionary`·`graph` 뿐이라 기능 영향은 작지만 낡은 ID 를 남기지 않는다) |
  | `eval/k4-search/fixtures/reference/stage-evidence-packet-02.json` | **ID 0건** — `dataset_name`·`file_name` 으로 묶는다(`test_search_reference_evidence.py:56-58`). ⭑ **이름이 유지되면 재박기 불요** |
  | `services/core-api/tests/test_search_reference_evidence.py` | 위 셋을 읽어 일회용 DB 에 재생(`seed_reference_corpus`) |
  | `services/core-api/tests/test_k4_interpreter_probe.py` · `test_k3_lineage_probe.py` · `test_k3_candidate_recall.py` | 같은 `seed_reference_corpus` 를 공유 |
  | `eval/k4-search/golden_baseline.py:134` | `if len(expected) != 9: raise ValueError('expected nine datasets')` — **건수가 코드에 박혀 있다** |
  | `dev-package/reports/stage3-ai-search-plan/*.json` · `dev-package/reports/k3-lineage-probe/*.json` · `dev-package/reports/k4-luna-probe/*` | **과거 실측 기록** — 고치지 않는다(기록은 그때의 사실이다) |
- `01M2F4…`(DR-4 5회차가 등록한 gpkg 2건)를 박은 자리 = `dev-package/sessions/DR-4-run-20260914T050442Z.md` 와
  보고서 JSON 들뿐. **실행 경로에 박힌 곳은 없다**(grep 실측).
- 계약 파괴 여부: **아니오**(스키마·API 무변). 단 **골든셋 편집**이므로 Ted 서명이 따로 필요하다(§판정 기준 §4).

## 제약

- **dev 재생성 승인 = 상시.** `.agents/skills/dev-reseed/SKILL.md:113` 축자 —
  「**dev 한정 상시 승인**이다 — `.agents/rules/deploy.md` 11번 증보 문단(2026-09-14 개정). 회차별 Ted GO 가 필요 없다.」
  같은 문서 117-118 축자 — 「⛔ **에이전트가 몰아서 실행할 때는 `reset` 앞에 advisor 게이트 ③(go/no-go)을 붙인다.**
  상시 승인은 회차별 Ted GO 를 대체하지 advisor 판정을 대체하지 않는다(`R-DATA-CANON §7`).」
- 게이트 넷(SKILL.md:114-115) — `--target dev`＋`--yes-reset-dev` · 버킷 정확 일치 · 두 DB URL **호스트**에 `-dev` ·
  계획 키가 `uploads/`·`previews/` 안. 하나라도 어긋나면 아무것도 지우지 않고 비영 종료.
- 계정 정본 = 비공개 `~/.config/colab-platform/dev-reseed-accounts-approved.json`(0600 · 5행).
  **칸 이름만** 적는다 — `email`·`name`·`admin`·`role`·`lab`·`initial_password_strategy`. 값은 어디에도 적지 않는다.
  구성 = 연구실 미소속 서비스 운영자 4 ＋ 정본 연구실 교수 1(SKILL.md:65).
- **골든셋은 검색 결과에서 뽑지 않는다.** 대응은 **이름**으로만 건다(`eval/k4-search/README.md:6` 「의미 판정의 정본은 Markdown이다」 ·
  같은 문서 20행 「필수 정답 포함 여부/빈 후보 검사는 자동」). 새 ID 를 검색 결과 상위에서 고르면 평가가 자기 자신을 채점한다.
- 일회용 DB 규율 — 게이트 안에서 모델을 부르지 않는다(`eval/k3-lineage/README.md:17-18`, `test_k4_interpreter_probe.py` 머리말).
- 기간은 근거 있는 값만(`SKILL.md:25`). 등록일·파일 수정일을 관측일로 대체하지 않는다.

## 설계트리 (grill-me 결과)

- **Q1 재적재를 UI 로 하나 API 로 하나** → **A UI(화면) 경로.** 권장안 수용.
  근거 ⑴ 자동 메타는 **업로드 분석 사건**으로만 들어온다 — `routes/ingestion.py:1004` 의 `d3_catalog.apply_autometa(...)` 가
  `ledger.held_auto_metadata(upload_id)` 의 값을 `COALESCE` 로 빈 칸에만 쓴다(`d3_catalog.py:1331-1352`).
  API 직적재(`load-seed.py`)는 그 사건을 만들지 않아 **오늘의 9건이 빈 이유**가 된다.
  ⑵ 등재표·러너가 이미 있다(`dev-package/tools/dev-seed/{plan-manifest.yaml,build_plan.py,runner.py}`).
  ⑶ 반대 관점 = UI 경로는 느리고(DR-4 실측 데이터셋 1건 ≈ 21~23 초 · 28건이면 등록만 10~15분 + 업로드 3.6 GB) 브라우저 의존이 붙는다.
  그래도 **자동 메타가 목적**이므로 속도를 이유로 API 로 돌아가면 이 intent 가 성립하지 않는다.
- **Q2 계보를 UI 로 다나 SQL 로 심나** → **A UI(＋공식 계보 API).** 러너에 이미 있다 —
  `runner.py:1186 do_lineage()` 가 부모를 화면에서 붙이고, 역할이 붙는 자리는 `runner.py:1289 lineage_api()`(공식 PATCH/POST)다.
  **DB 직접 수정 금지**(`SKILL.md:42`). 18간선의 정본은 `plan-manifest.yaml` 의 `parents` 이고,
  `보조입력` 은 `canonical-metadata.json` 의 `auxiliaryParents` 2건(Prediction(공간상세화) ← DEM · Aspect)뿐이며
  나머지 16간선은 `주입력` 이다(`build_plan.py:168-181` 이 그 2건 말고는 거부한다).
- **Q3 스냅샷 형식** → **A v2 로 올린다.** 오늘 형식에 이미 `autometa`·`variable_rows`·`parents` 열쇠가 있으므로
  **열쇠를 늘리지 않고 값만 채우는 것**이 가능하다. 더할 것은 `processing_level`(가공 단계) 하나 —
  오늘은 없어서 K3 가 **이름의 「(Lv.n)」 에서 읽고 있다**(`test_k3_lineage_probe.py:44-48` 축자
  「⚠ **가공 단계의 출처는 이름의 「(Lv.n)」 이다** … 참조 스냅샷의 데이터셋 항목에는 가공 단계 열이 **아예 없고**」).
  28건 이름에는 「(Lv.n)」 이 없으므로(`plan-manifest.yaml` 의 이름은 `HSR 레이더 반사도 원자료` 꼴) **이 열은 필수**다.
- **Q4 일회용 DB 를 dev 읽기로 바꾸나** → **A 아니다.** `test_k4_interpreter_probe.py`·`test_k3_lineage_probe.py` 는
  일회용 Postgres 를 유지하고, **더 풍부해진 스냅샷을 그대로 재생**한다. dev 접속을 시험에 넣으면
  게이트가 네트워크·환경에 묶이고 재현이 깨진다. 바꾸는 것은 **스냅샷의 내용**이지 시험의 경로가 아니다.
- **Q5 9건을 28건 안에 보존할 수 있나** → **A 아니다 · [미확인 아님 · 실측].** 두 코퍼스는 **다른 자료 묶음**이다 —
  9건은 `LD-*` 매니페스트 묶음(예 `강수 — HSR 레이더 합성 반사도 (Lv.0)`), 28건은 파일 트리 기준 분해(예 `HSR 레이더 반사도 원자료` · `hsr_sample`).
  이름도 경계도 다르므로 **9건은 28건의 부분집합이 아니다.** 따라서 골든 12문항은 **질문은 그대로 두되 `scope`·`required` 를 28건 위에서 다시 정해야 한다** —
  그것이 이 작업에서 Ted 서명이 필요한 진짜 이유다(단순 ID 치환이 아니다).

## 판정 기준

1. **계수** — `result.json` 의 `counts` 가 데이터셋 28 · 프로젝트 4 · 간선 18 · 「미지정」 0 · 프로젝트 미연결 0
   (`SKILL.md:126`). `previewJudgment[]` 의 **「판정불가」는 통과로 세지 않는다**(`SKILL.md:128`).
2. **자동 메타 fill** — 28건 × 5축(`format`·`period`·`crs`·`grid`·`variables`)을 세어 표로 남긴다.
   **기대치(코드 근거에 따른 예측 · 실측으로 확정할 것)** —
   | 축 | 기대 fill | 근거 |
   |---|---|---|
   | `period_start/end` | **28/28** | 파일이 아니라 **사람이 폼에 넣는다** — `canonical-metadata.json` 이 28행 전건의 `start`·`end`·`granularity`·`basis` 를 들고 있고 `runner.py:1038 fill_period()` 가 등록 카드에서 채운다. `apply_autometa` 의 `COALESCE` 가 사람 값을 덮지 않는다(`ingestion.py:984-990`) |
   | `crs` | **26/28** | GeoTIFF 7 · GRIB 1 은 파일 내장(`parse.py:132`·`236`), NetCDF 3 은 좌표 변수/내부 격자(`parse.py:58`·`90-94`), HDF4 2 는 `describe_internal_grid`(`parse.py:116`), npy 11 · bin 2 는 **기준 격자 파일이 붙으면** `WGS84 (기준 격자 파일)`(`pipeline.py:231-232`). 못 붙으면 `[미상]`. **제외 = GeoPackage 2**(SPI·SPEI) |
   | `grid` | **26/28** | 같은 파서들이 `(rows, cols)` 를 세운다. 제외 = GeoPackage 2 |
   | `format` | **26/28** | 분석이 성립한 것만. gpkg 2 는 DR-4 §5 실측 축자 「형식 인식 실패 — 지도로 못 그려요 · 등록은 됩니다」 |
   | `variables` | **[미확인]** | ⛔ `apply_autometa` 는 `variables` 를 **넘기지 않는다**(`ingestion.py:1007` 축자 「`held.variables` 는 넘기지 않는다」). 정본은 `d3_dataset_variable` 행 표이고 배열은 `0019` 트리거의 사본이다(`d3_catalog.py:1325-1330`). **그 행이 등록 경로에서 실제로 서는지**를 확인할 자리 = `services/core-api/tests/test_variable_rows.py` 와 `routes/ingestion.py` 의 변수 행 삽입부 |
   ⚠ **이 표는 코드에서 읽은 예측이지 실측이 아니다.** WU3 이 실제 값을 세어 이 표를 덮어쓴다.
3. **계보** — 재적재 뒤 `d4_lineage_edge` 18행. 역할은 `보조입력` 2 · `주입력` 16.
   ⛔ `method`(가공 방법 문장)는 **[미확인]** — 오늘의 9건 정답에는 `method` 가 있으나(`lineage-cases.json`)
   28건 등재표에는 그 칸이 없다. 확인할 자리 = `dev-package/tools/dev-seed/plan-manifest.yaml` 의 `parents` 스키마와
   `runner.py:1289 lineage_api()` 의 본문 칸. 없으면 K3 정답에서 `method` 를 **비운 채로** 두고 그 사실을 보고서 첫 줄에 적는다.
4. **서명** — Ted 가 서명하는 것은 **두 가지**다.
   ㉮ **이름 → 새 ID 대응표**(28행 · 이름·seq·새 ID·프로젝트·Lv).
   ㉯ **골든 12문항의 새 `scope`·`required`**(Q5 때문에 단순 치환이 아니다). `golden-set.md` 의 의미 기준은 그대로 두고
   28건 위에서 어느 것이 정답인지만 다시 고른다. **검색을 돌려서 고르지 않는다.**
5. **완주** — K4 `golden_baseline.py --mode literal` · `--mode expanded` 가 78(준비 실패) 없이 끝나고,
   `bash gates/tools/service-tests.sh core-api k3_probe` 가 후보 JSON 을 쓴다. 게이트 3계수를 그대로 적는다.

## 단계별 절차 (WU 분할 · 게이트 · advisor 게이트 ③ 자리)

**⚠ dev 에 쓰는 단계는 WU2 뿐이다.** 나머지는 전부 읽기 전용이거나 레포 편집이다.

- **WU0 — 사전 대조 (dev 무접촉 · 레인 1)**
  ⑴ `python3 dev-package/tools/dev-seed/build_plan.py --md-root dev-package/reports/reference-data/datasets-md --dry-run`
     (레포 사본으로 표↔블록 대조 · 아무것도 쓰지 않는다 · `dev-seed/README.md §1-ⓐ`).
  ⑵ `COLAB_REF_ROOT=<참조자료 뿌리> bash gates/run.sh seed-plan-drift` — 참조자료가 없으면 `COLAB_SEED_PLAN_NO_FILES=1` 로 **명시 면제**.
     ⭑ **참조자료 뿌리의 실제 위치는 [미확인]** — 기본값은 `build_plan.py:129` 의 「본 체크아웃과 나란한 `03 Reference-Data`」이고,
     `~/workspace` 에는 그 이름의 폴더가 보이지 않았다. 확인할 자리 = `dev-package/tools/dev-seed/README.md §0` 와 실제 마운트.
     **참조자료가 없으면 WU2 는 시작하지 않는다**(3.6 GB 의 원본이 없으면 등록할 것이 없다).
  ⑶ `bash dev-package/tools/dev-reseed/reseed.sh --preflight-only` — **읽기만 한다**(`SKILL.md:81`).
  ⑷ `bash gates/run.sh dev-reseed-selftest` — dev 무접촉 검사기(`SKILL.md:136`).
  ⑸ **현재 dev AI 사전 DB 계수를 먼저 적어 둔다**(읽기 전용 · 2026-09-24 실측) —
     `d9_concept 49 · d9_concept_edge 19 · d9_method_term 13 · d9_place_alias 4 · d9_topic_synonym 18`.
     재생성 뒤 같은 수가 서지 않으면 그 자리에서 멈춘다.
- **WU1 — 리허설 (dev 무접촉 · 바꾸는 단계 0건)**
  `bash dev-package/tools/dev-reseed/reseed.sh --rehearse`. 원격 원시동작 10 을 실모드로 한 번씩 낸다(`SKILL.md:83-91`).
  ⛔ `COLAB_DEV_SECRETS_DIR` 를 이 도구에 주지 않는다(`SKILL.md:101-106`).
- **★ advisor 게이트 ③ (go/no-go) — WU2 의 `reset` 직전. 이 자리 하나다.**
  붙이는 근거 = `SKILL.md:117-118`. 판정 재료 = WU0·WU1 의 결과 · `approval-record.json` 이 실행 자리에 섰는지 ·
  게이트 넷 충족 · 참조자료 실재 · AI 사전 DB 계수 기록. **no-go 면 아무것도 지우지 않는다.**
- **WU2 — 재생성 (⛔ dev 에 쓰는 유일한 단계 · 레인 1 · 다른 레인과 동시 금지)**
  `bash dev-package/tools/dev-reseed/reseed.sh` — 10단계 `preflight → deploy → reset → bootstrap → up → s3 → prelude → seed → verify → report`.
  ⑴ `reset` 이 **두 체인 스키마를 DROP·CREATE 한다**(`services/core-api/ops/reset_dev_environment.py` 머리말 ⑵) — 플랫폼과 **AI 사전이 함께** 지워진다.
  ⑵ `migrate-ai`(`stages.sh:283`)가 사전을 되세운다 — 온톨로지 시드가 **마이그레이션 안에 실려 있기 때문**이다
     (`db/ai/versions/0003_k2_ontology_seed.py` → `db/ai/seed/k2_ontology_seed.sql` · `0005_k2b_concept_graph_seed.py`).
     ⚠ **마이그레이션 밖에서 손으로 넣은 행은 돌아오지 않는다.** WU0-⑸ 의 계수로 대조한다.
  ⑶ 멈추면 **자동 재시도하지 않는다**(`SKILL.md:142`). `--from <단계>` 로만 잇는다.
  ⑷ 예상 소요 = **[미확인 · 1회차 무인 완주 전례 없음]**. DR-4 §9 축자 「`reseed.sh` 전 10단계를 한 프로세스로 밟은 회차는 아직 없다.」
     참고치 = 등록 28건 × 21~23초 ＋ S3 업로드 3.6 GB ＋ verify ≈ 200초.
- **WU3 — 새 스냅샷 재포획 (dev 읽기 전용 · 레인 2)**
  `golden_baseline.py` 의 `REMOTE` 패턴(88-106행)을 그대로 본뜬 **재포획 도구 1건**을 만든다 —
  `eval/k4-search/recapture_snapshot.py`(가칭). 규율 —
  ㉮ `read_only_scope` ＋ `SHOW transaction_read_only` 가 `on` 이어야 진행(`golden_baseline.py:93-94`).
  ㉯ **이름으로만 대응**한다 — `plan-manifest.yaml` 의 28 이름 → dev 의 `d3_dataset_description.name`.
  ㉰ **이름 충돌 검사** — 같은 이름이 2건 이상이거나 0건이면 **그 자리에서 78**(임의 선택 금지 ·
     `d3_catalog.py:901` 「같은 이름으로 두 번 세우면 뒤에 선 쪽이 앞을 조용히 덮고」와 같은 규율).
  ㉱ 실어 오는 것 = 데이터셋 코어 ＋ `autometa` 5축 ＋ `variable_rows` ＋ `parents`(역할·method) ＋ **`processing_level`**(Q3).
  ㉲ 출력은 **결정적**이다 — 데이터셋은 `id` 오름차순, 파일·부모도 고정 순서, `indent=2`·`ensure_ascii=False`(기존 스냅샷과 같은 모양).
  ㉳ 산출물 = ⓐ 새 `dev-data-snapshot.json` ⓑ **대응표 Markdown 28행**(Ted 서명 대상 ㉮).
  ⛔ 이 도구는 **쓰기 SQL 을 한 줄도 갖지 않는다.**
- **★ Ted 서명 자리 ㉮·㉯ — WU4 시작 전.** 대응표와 새 `scope`/`required` 를 받고서야 골든셋을 만진다.
- **WU4 — 골든셋·정답 재박기 (레인 3 · dev 무접촉)**
  ⑴ `golden-cases.json` 12문항의 `scope`·`required` 를 서명본대로 교체. 질문 문장은 **무수정**.
  ⑵ `golden_baseline.py:134` 의 `!= 9` 를 새 건수로 바꾸고, 그 수를 **스냅샷에서 읽게** 고친다(다시 박지 않는다).
  ⑶ `eval/k3-lineage/lineage-cases.json` 을 새 스냅샷의 `parents` 에서 **다시 생성**한다.
     대조는 기존 시험이 이미 한다 — `test_k3_candidate_recall.py::test_계보_정답이_참조_스냅샷과_한_글자도_어긋나지_않는다`.
  ⑷ `expanded-normalized-02.json` 은 `golden_baseline.py --mode expanded` 재실행 산출물로 **갈아 끼운다**(손으로 고치지 않는다 · `README.md:107`).
  ⑸ `stage-evidence-packet-02.json` 은 **이름 기준이라 그대로 쓴다** — 단 28건 이름 체계가 바뀌었으므로
     `dataset_name`·`file_name` 이 새 코퍼스에 실제로 있는지 검사하고, 없으면 그 항목을 **드러낸 채** 빼거나 다시 모은다
     (`reference_evidence.py --reference-root … --verify`).
  ⑹ `golden-set.md` 의 의미 기준은 원문 유지. 바뀐 것은 **어느 데이터셋이 그 답인가**뿐이고 그 근거를 문항마다 한 줄로 적는다.
  게이트 = `python3 -m unittest discover -s eval/k4-search -p 'test_*.py'` ＋ `bash gates/run.sh <search-golden 계열>`.
- **WU5 — 재측정 (레인 4 · 모델 호출 있음)**
  ⑴ K4 검색 — `golden_baseline.py --mode literal` · `--mode expanded`(새 출력 경로 · 기존 경로면 78).
  ⑵ K4 해석기 — `COLAB_K4_PROBE_INTERP`·`COLAB_K4_PROBE_OUT` 를 준 `k4_probe` 시험(일회용 DB 유지 · 모델 0회).
     모델 절반은 `eval/k4-search/llm_interpreter_probe.py` 가 따로 부른다.
  ⑶ K3 — `COLAB_K3_PROBE_OUT`·`COLAB_K3_CANDIDATES_OUT` 를 준 `bash gates/tools/service-tests.sh core-api k3_probe`
     → `eval/k3-lineage/llm_lineage_probe.py --repeats 2 --candidates <그 파일> --output <새 JSON>`.
     ⭑ 자동 메타가 채워지면 `apply_snapshot_autometa`(`test_k3_lineage_probe.py:96`)가 **처음으로 실제 축을 싣는다** — 이것이 이 작업의 본래 목적이다.
  ⑷ 결과는 `dev-package/reports/k4-*/`·`k3-lineage-probe/` 에 **새 파일로** 둔다. 과거 기록을 덮지 않는다.
- **WU6 — dev 쪽 온톨로지 후속(선택 · 별건)**
  28건의 실제 이름·변수·방법 어휘로 `d9_*` 보강을 재검토한다. **이 intent 의 완료 조건이 아니다.**

## 미해결 질문

1. **참조자료 뿌리가 지금 어디에 마운트돼 있는가** — 없으면 WU2 자체가 불가. 확인 자리 = `dev-package/tools/dev-seed/README.md §0`.
2. **`variables` 가 등록 경로에서 실제로 서는가** — `apply_autometa` 가 안 쓰므로 `d3_dataset_variable` 행 생성 경로를 봐야 한다.
   확인 자리 = `services/core-api/src/colab_core/app/routes/ingestion.py` 변수 행 삽입부 · `tests/test_variable_rows.py`.
3. **계보 `method`(가공 방법)를 28건 재적재가 기록하는가** — `plan-manifest.yaml` 에 그 칸이 안 보인다.
   없으면 K3 정답에서 `method` 는 빈 값이 되고, 「근거 문장」 항목의 재료가 줄어든다.
4. **골든 12문항이 28건 위에서 여전히 의미가 성립하는가** — 예: 「GK2A_NDVI_mean_202305.tif 를 만든 원자료」는
   28건에서 seq 7 ← seq 6 으로 **더 정확히** 성립한다. 반대로 9건에서 한 데이터셋이던 SPI/SPEI 는 28건에서 2건으로 갈린다(seq 13·14).
   문항별 판단이 필요하고 그것이 서명 ㉯ 다.
5. **다른 소비자가 dev 를 보고 있는가** — 32 체크아웃의 이슈 레인, `codex/ai-search-next` 를 포함해
   **재생성 시점에 dev 를 쓰는 사람이 없는지**를 사람이 확인해야 한다. 도구가 막아 주지 않는다.
6. **1회 완주 소요 시간** — 전례가 없다(DR-4 §9).

## 범위 밖 (명시 제외)

- staging · product 재생성. **dev 상시 승인을 staging 에 적용하지 않는다**(`SKILL.md:119`).
- 제품 스키마·API·화면 변경. 자동 메타 추출기(pipeline-worker) 개선.
- `dev-package/reports/**` 의 과거 실측 기록 수정.
- 게이트 안에서의 모델 호출. K3/K4 를 합격/불합격 게이트로 승격하는 일(`eval/k3-lineage/README.md:44` 「합격/불합격 게이트가 아니다」).
- DR-4 가 남긴 도구 결함 2건(`project_index` 앵커 의존 · 미리보기 순회기 대기 조건)의 수정 — 선행 조건으로 다루되 이 intent 가 고치지 않는다.
- `01M2F4…` 를 쓰는 과거 세션 기록의 정정.

## 확인

- 프론티어 공집합 확인: [미확인]
- Ted 확인 문장(원문 그대로): "권고대로 해"
- 재개봉 금지: 아니오 — 서명 ㉮·㉯ 가 오기 전까지 WU4 이후는 열려 있다.

## 참조

- 재생성 절차: `.agents/skills/dev-reseed/SKILL.md` · 실행기 `dev-package/tools/dev-reseed/reseed.sh`
- 지난 회차: `dev-package/sessions/DR-4-run-20260914T050442Z.md`
- 등재표 정본: `dev-package/tools/dev-seed/plan-manifest.yaml` · `canonical-metadata.json` · `build_plan.py` · `runner.py`
- 승인 근거: `.agents/rules/deploy.md` 11번 증보 문단 · `services/core-api/ops/reset_dev_environment.py`
- 평가 재료: `eval/k4-search/README.md` · `eval/k3-lineage/README.md` · `eval/k4-search/golden-set.md`
- 오늘의 코퍼스 출처: `dev-package/sessions/20260912-ai-search-data-readiness.md`
- 결정: 〈N〉 (병합 시 기입)
