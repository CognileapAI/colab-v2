# CODE-REVIEW-20260903-A — 레인 A `ci-honesty` 실행 기록

> 근거 — `dev-package/sessions/CODE-REVIEW-20260903.md` 결함 #6(`.github/workflows/ci.yml`) ＋ 그 「형제 green-by-skip」 목록.
> 집행 계획 — `dev-package/sessions/CODE-REVIEW-20260903-PLAN.md` §1 공통 규칙 · §2 레인 A 행.
> 워크트리 `.claude/worktrees/agent-a26a95673bf502c9e` · 브랜치 `worktree-agent-a26a95673bf502c9e` · 기준 `lane-review-clean`(`d4d11b5`). push 없음 · main 병합 없음 · 대장 번호 발급 없음.
> 경로는 레포 루트 기준. 행 번호로 가리키지 않는다 — `파일:앵커` 로 적는다.

## 1. 무엇이 문제였나 (실측)

| 자리 | 실측 | 무엇이 감춰졌나 |
|---|---|---|
| `.github/workflows/ci.yml` | `grep -rn pytest .github/` = 0 | 서비스 pytest 를 도는 잡이 없다. CI 가 도는 pytest 는 `stage2-markers` 의 `stage2 and not e2e` 부분 집합 하나 — 서비스 측 시험 함수 1102 중 **871 미실행** |
| `ci.yml:contract-gates` | `frontend-typecheck`·`frontend-test` 가 `contracts` 필터 잡 안 · `outputs.frontend` 소비처 0 | `frontend/` 만 바꾼 PR 은 **게이트 잡 0개** |
| `ci.yml` | `db-boundary` 호출 0 (셀프테스트만 CI 에 있음) | 판정기는 있는데 **판정을 아무도 안 한다** — `work-item-consistency` 가 겪은 모양 |
| `gates/run.sh:selftest` | 손목록 14 vs `ALL_GATES` 안 `*selftest` 18 | 넷이 목록의 부재로만 존재 — 아무도 세지 않는다 |
| 셀프테스트 12종의 자체 `expect()` | 10종이 rc 78 을 그냥 red 로 접음 | **판정된 적 없는 케이스가 「red OK」로 찍힌다** |

## 2. 기준선 (수정 전 · 이 워크트리 실측 2026-09-03)

서비스 venv 는 이 체크아웃에 없었다(gitignore). `.github/workflows/ci.yml:dormant-tests` 의 판을 따라 넷 다 새로 지었다 —
`python3 -m venv .venv` ＋ `requirements.txt`(＋ 있으면 `requirements-dev.txt`) ＋ `pip install -e .`.

| 묶음 | 명령 | 통과 | 실패 | skip | deselected | 소요 |
|---|---|---|---|---|---|---|
| viz-render | `-m "not e2e and not perf"` | 199 | 0 | 0 | 40 | 11.98초 |
| pipeline-worker | `-m "not e2e and not dbint"` | 200 | 0 | 0 | 41 | 10.76초 |
| ai-service | `pytest -q` (표식 도입 **전**) | 119 | **26 errors** | 0 | 0 | 8.15초 |
| core-api | `pytest -q` (일회용 pg · 전건) | 553 | **5 failed** | 0 | 0 | 90.22초 |
| core-api | `-m "not e2e"` (일회용 pg) | 552 | 0 | 0 | 6 | 89.95초 |

- ai-service 26 errors = `COLAB_AI_TEST_DICT_DB_URL` 부재. `tests/conftest.py:_require` 가 **skip 이 아니라 fail** 을 낸다(옳은 동작).
- core-api 5 failed = `tests/test_e2e_s3_real.py:_root` 가 `COLAB_REFERENCE_DATA` 부재를 fail 로 낸다(옳은 동작). **기존 실패이고 이 레인에서 고치지 않는다.**
- `./gates/run.sh selftest` → **rc 1** · 실행 14 · green 12 · red(준비) 2
  (`frontend-typecheck-selftest`·`frontend-test-selftest` — 이 체크아웃에 `frontend/node_modules` 가 없었다. `npm ci --prefix frontend` 뒤 둘 다 green).

## 3. 바꾼 것

### 3-1. 서비스 시험 게이트 신설 — `gates/tools/service-tests.sh`

- 사용 `service-tests.sh <단위> <표식 선택자>`. **인자 둘 다 필수** — 빈 선택자를 「전부」로 읽지 않는다(`service-tests.sh:⑴ 인자`).
- red 조건 여섯 — 인자 부재 · 단위/`tests/` 자리 부재 · **수집 0건** · **실행 0건(전부 skip)** · failed·errors · pytest 비영 종료.
- skipped·deselected 는 막지 않고 **요약줄에 건수로** 낸다. deselected 를 pytest 요약줄에서 못 읽으면 `0` 이 아니라 **`미상`** 으로 적는다.
- venv 부재 = **red(준비 · 78)** ＋ `::gate-readiness-failure::` 표식(`_pg.sh` 의 것을 그대로 씀).
- `core-api` 는 게이트가 **일회용 Postgres 를 스스로 세운다**(`service-tests.sh:⑶ core-api`) — `_pg.sh:pg_start` ＋ 기존 `services/core-api/tests/fixtures/setup-db.sh`. 포트 미공개 · `PGDATA` tmpfs · `--rm` ＋ trap · 이름 `colab_v2_gatepg_*`. **접속 문자열을 어디에도 출력하지 않는다.** `setup-db.sh` 실패는 `pg_is_readiness_error` 로 준비/판정을 가른다.
- `--strict-markers` · `-p no:cacheprovider` · `-o junit_family=xunit1`(다른 junit 게이트와 같은 판).

### 3-2. 셀프테스트 — `gates/tools/service-tests-selftest.sh` ＋ `gates/fixtures/service-tests/`

케이스 9. 픽스처 트리 넷(`pass`·`fail`·`empty`·`allskip`)을 `mktemp -d` 사본에서 돌린다 — `services/**` 에 한 글자도 쓰지 않고 서비스 묶음을 다시 돌리지 않는다.

| 케이스 | 기대 |
|---|---|
| ⓐ 통과 시험 1건 (대조군) | green |
| ⓑ 시험 1건 실패 | red |
| ⓒ **수집 0건** | red |
| ⓓ **실행 0건(전부 skip)** | red |
| ⓔ venv·파이썬 부재 | **red(준비 · 78)** |
| ⓕ 표식 선택자 인자 없음 / ⓖ 단위 이름 인자 없음 | red |
| ⓗ 단위 자리 부재 | red |
| ⓘ 요약줄이 수집·실행·skipped·deselected·failed 를 계수로 낸다 | 문자열 대조 |

### 3-3. `gates/run.sh` — 등록과 집합 파생

- `ALL_GATES` 에 `service-tests-{core-api,ai-service,viz-render,pipeline-worker}` ＋ `service-tests-selftest` 추가(총 48 · 그중 `*selftest` 19).
- **표식 선택자의 정본은 `run.sh` 의 case 한 곳**(`run.sh:service-tests-core-api|…`). 스크립트에 기본값을 두면 두 곳이 갈리고 갈린 쪽이 조용히 이긴다.
- `selftest` 집합을 **손목록에서 `ALL_GATES` 파생**으로 바꿨다(`run.sh:selftest`). 세 상태 — 선언되면 돈다 · **명시 면제는 이름·사유·건수를 드러낸 채** 넘어간다 · 아무 말 없으면 red. 요약줄 = `선언 N · 실행 M · 면제 K` ＋ `green / red(판정) / red(준비)`. 케이스가 78 이면 집합도 78.
- 면제 2건(`SELFTEST_EXEMPT`) — `stage2-markers-selftest`(pipeline-worker 런타임 · CI 는 `dormant-tests` 잡) · `service-tests-selftest`(서비스 venv · CI 는 `service-tests` 잡). **`gates/run.sh all` 은 면제 없이 전부 돈다.**
- `gates/config/parallelism.toml` — 서비스 넷 `serial`(부하가 판정을 흔든다 · `frontend-test` 와 같은 배치 · core-api 는 pg 슬롯도 잡는다), `service-tests-selftest` `parallel`.

### 3-4. rc 78 정직성 — `gates/tools/_expect.sh` 신설

판정 갈래를 한 곳에 두고 **네 갈래**로 낸다: `green` · `red` · `ready`(환경을 기다리다 못 떴다) · `미선언`(`cause=입력미선언`).
기대가 `ready`·`미선언` 이 아닌데 78 이 오면 **통과로도 실패로도 세지 않고** `EXPECT_READINESS` 에 쌓았다가 셀프테스트 전체를 78 로 내보낸다(`expect_readiness_verdict`).

- 물린 곳 13 — `artifact-ownership-`·`autometa-loss-`·`backup-cron-streak-`·`db-boundary-`·`e2e-format-coverage-`·`generated-`·`preview-tile-slot-`·`render-latency-`·`seam-consistency-`·`work-item-selftest`(리뷰가 센 10) ＋ **형제 3**: `stage2-markers-selftest`(자체 `expect_red`) · `db-selftest`(손사본을 정본으로 교체) · `_expect_pool.sh`(정의를 `_expect.sh` 로 옮김).
- **또 다른 형제 3** — `contract-`·`event-`·`boundary-selftest` 는 풀이 쌓아 둔 준비 실패를 **한 번도 읽지 않아** 못 돈 케이스가 조용히 사라진 채 green 이 나갈 수 있었다. `expect_readiness_verdict` 를 물렸다.
- 실측으로 뒤집힌 케이스 **16건** — `autometa-loss-selftest` 4(ⓐⓑⓑ'ⓛ) · `preview-tile-slot-selftest` 5(ⓐⓑⓑ'ⓒⓓ) · `artifact-ownership-selftest` 7(ⓐⓑⓑ'ⓑ''ⓒⓓⓝ). 전부 「red OK」로 찍히던 자리이고 **재는 것이 실제로는 입력 미선언**이었다 — 기대를 `미선언` 으로 바로잡았다. 각 셀프테스트의 요약 문장도 `red N · 미선언 M` 으로 갈라 적었다.

### 3-5. `services/ai-service` — `dictdb` 표식

- `pyproject.toml:[tool.pytest.ini_options] markers` 에 `dictdb` 등록.
- `pytestmark = pytest.mark.dictdb` 를 **세 파일**에 — `tests/test_dictionaries_db.py` · `tests/test_concept_graph_db.py` · `tests/test_http_search.py`.
- ⚠ **지시문과 어긋난 자리** — 지시문은 6파일을 지목했으나 실측 대상은 셋이다. `test_db_url_file.py`(`Settings.from_env` · 임시 파일) · `test_dictionary_expansion.py`(순수 `expand`) · `test_search_service.py`(`FakeDictionaries`)는 DB 를 쓰지 않는다. 붙였다면 **돌던 시험을 CI 밖으로 밀어내는 것**이라 붙이지 않았다. 근거 = 표식 전 `pytest -q` 의 26 errors 전건이 위 세 파일 안에 있다.

### 3-6. `.github/workflows/ci.yml`

| 잡 | 조건 | 도는 것 |
|---|---|---|
| **`service-tests`** ⭑신설 | 단위별 `<단위> \|\| contracts` (matrix 4 · `fail-fast: false`) | `service-tests-selftest` → `service-tests-<단위>` |
| **`frontend-gates`** ⭑신설 | `frontend \|\| contracts` | `frontend-typecheck` · `frontend-test` |
| `boundary-gates` | core-api ∥ ai-service ∥ **viz-render ∥ pipeline-worker ∥ infra ∥ contracts** ⭑확대 | 기존 3종 ＋ **`db-boundary`** ⭑신설 |
| `contract-gates` | `contracts` | 프런트 2종을 **뺐다**(두 번 돌지 않는다). `generated-up-to-date` 때문에 `npm ci --prefix frontend` 는 남는다 |

- `service-tests` 잡은 pytest 를 직접 부르지 않고 **게이트를 부른다** — 선택자·red 조건이 두 곳에 적히면 갈린다.
- 이 회차의 대상이 아닌 단위는 첫 스텝이 `::notice::` 로 그 사실을 이름으로 찍는다 — 조용히 건너뛴 것과 「대상이 아니다」를 로그에서 가른다.
- `boundary-gates` 조건 확대 이유 — `db-boundary` 가 단위 7개의 Dockerfile·`src`·`tests` 와 `infra/staging/compose.i2.yml` 을 전부 훑는다(`gates/config/db-boundaries.toml` 이 정본). **검사 대상이 줄지 않는 방향의 변경**이다.
- `db-boundary` 는 compose 를 읽으려고 pyyaml 을 쓴다(없으면 red — 옳은 동작). 설치·존재 확인 스텝을 `planning-gates` 와 같은 판으로 세웠다(핀은 `gates/requirements.txt` 하나).
- YAML 파싱 확인 — `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` 통과. 게이트 호출 중복 0(잡별 호출표를 파싱해 대조).

## 4. 계수 — 개정 후 (전부 이 워크트리 실측)

| 게이트 | 결과 | 요약줄 |
|---|---|---|
| `service-tests-core-api` | green | 수집 552 · 실행 552 · skipped 0 · deselected 6 · failed 0 · errors 0 · 84.7초 |
| `service-tests-viz-render` | green | 수집 199 · 실행 199 · skipped 0 · deselected 40 · failed 0 · errors 0 · 9.9초 |
| `service-tests-pipeline-worker` | green | 수집 200 · 실행 200 · skipped 0 · deselected 41 · failed 0 · errors 0 · 7.3초 |
| `service-tests-ai-service` | green | 수집 119 · 실행 119 · skipped 0 · deselected 26 · failed 0 · errors 0 · 3.3초 |
| `service-tests-selftest` | green | 케이스 9 전건 기대대로 |
| `db-boundary` | green | 단위 7 · 스캔 대상 265건 · 위반 0 |
| `frontend-typecheck` | green | 오류 0건 |
| `frontend-test` | green | 통과 520건 · 시험 파일 32 |
| `stage2-markers` | green | 수집 69 · skipped 0 · failed 0 |
| `stage2-markers-selftest` | green | 0건·skip·fail 셋 다 red |
| `selftest` 집합 (`COLAB_GATE_JOBS=1`) | green | **선언 19 · 실행 17 · 명시 면제 2 · green 17 · red(판정) 0 · red(준비) 0** |

**CI 에 실린 서비스 pytest** — 세는 단위 = **게이트가 실행한 시험 케이스 1건**, 시점 = 2026-09-03 이 워크트리.

- 개정 전 : `stage2-markers` **하나**뿐이고 실측 수집 **69건**(pipeline-worker 의 `stage2 and not e2e`).
- 개정 후 : **1070건**(core-api 552 ＋ viz-render 199 ＋ pipeline-worker 200 ＋ ai-service 119). `stage2-markers` 의 69 는 pipeline-worker 200 의 부분집합이라 중복 계수하지 않았다.
- ⚠ 리뷰가 적은 「1102 중 871 미실행」은 **다른 단위**(시험 *함수* 수)다. 이번에 다시 세지 않았으므로 위 값과 직접 빼고 더하지 않는다 — `[미확인]` §5-6.

### rc 78 실패 픽스처 — 개정 전/후 (같은 주입)

주입 = `COLAB_STAGE2_PY=/없는/파이썬` (pipeline-worker venv 부재를 흉내낸다).

```
── 개정 전 (git show HEAD:gates/tools/stage2-markers-selftest.sh) ──
  ✓ ⓐ 마커 0 건 — red
  ✓ ⓑ skip — red
  ✓ ⓒ fail — red
  rc=0                       ← **게이트를 한 번도 판정하지 않은 채 green**

── 개정 후 (gates/run.sh stage2-markers-selftest) ──
  [selftest] ⓐ 마커 0 건 → red(준비) — 검사기가 못 돌았다. **판정하지 못했다**(기대 red)
  [selftest] ⓑ skip     → red(준비) — …
  [selftest] ⓒ fail     → red(준비) — …
  ::error::stage2-markers-selftest red(준비) — 아래 케이스를 판정하지 못했다. 통과로 세지 않는다
  rc=78
```

**정밀도 대조(범위 축소가 아님을 잠근다)** — 같은 셀프테스트를 venv 가 있는 상태로 돌리면 세 케이스가 그대로 red 이고 green(rc 0)이다. `autometa-loss-`·`preview-tile-slot-`·`artifact-ownership-selftest` 도 기대를 바로잡은 뒤 전건 green(rc 0)이며, 진짜 위반 케이스(유실 3건 · 못 쓰는 타일 · 고아 1벌 등)는 여전히 red 다.

### 지시문 전제 하나를 정정한다

지시문은 「`COLAB_PG_FORCE_UNAVAILABLE=1` 로 셀프테스트를 돌리면 개정 전에는 (잘못) 통과한다」고 적었다. **재현되지 않았다** — 그 셋(`autometa-loss-`·`preview-tile-slot-`·`artifact-ownership-selftest`)은 케이스 실행 **전에** 자기 일회용 컨테이너를 띄우다 `pg_start` 에서 78 로 나간다(개정 전에도 rc 78, 실측 3/3). 결함은 **케이스 단위**에 있었고, 그 자리를 그대로 재현한 것이 위의 `stage2-markers-selftest` 픽스처와 §3-4 의 16건이다.

## 5. `[미확인]` — 무엇을 하면 풀리나

1. **GitHub Actions 실제 실행** — 로컬에서 workflow 를 돌릴 수 없다. 특히 `needs.changes.outputs[matrix.service]`(인덱스 표기)와 잡 수준 `env: RUN` → 스텝 `if: env.RUN == 'true'` 는 **YAML 파싱과 문서로만** 확인했다. → `lane-review-clean` push 후 **draft PR 1회**(계획 §3-4).
2. **Actions 러너에서 core-api 일회용 Postgres** — 로컬 도커에서만 확인. 같은 배치를 `schema-gates` 의 `rls-effect` 가 이미 쓰지만 **이 잡에서의 실행은 미확인**. → 같은 draft PR. 환경 사유로 red 면 계획 §3-4 대로 그 잡을 떼고 사유를 적는다.
3. **`gates/run.sh all` 전체** — 이 레인에서 돌리지 않았다(지시문 금지 · 오케스트레이터 몫).
4. **뺀 표식의 판정** — 이번 회차가 판정하지 않은 시험: core-api `e2e` 6 · viz-render `e2e`/`perf` 40 · pipeline-worker `e2e`/`dbint` 41 · ai-service `dictdb` 26. 표식은 **붙어 있고 취소되지 않았다.** → 각각 `COLAB_REFERENCE_DATA` 원천 마운트 · `COLAB_PIPELINE_DB_URL` · `db/ai` 체인 일회용 DB＋시드가 있는 호스트에서 실행.
5. **`rls-effect-selftest` 의 간헐 준비 red** — 병렬도 4 · 호스트 load average 8.09 에서 케이스 3건이 78(판정 못 함). `COLAB_GATE_JOBS=1` 에서 green(rc 0). **판정부가 아니라 환경이 낸 red** 다(`CLAUDE.md §1-b ⑸`). → 병합 트리에서 낮은 병렬도로 재현하거나 `COLAB_PG_MAX_CONCURRENT` 를 실측으로 다시 잡는다. 이 레인은 값을 바꾸지 않았다.
6. **기준선의 「871 미실행」** — 리뷰가 센 값(1102 중 871)을 그대로 인용했다. 이번에 다시 세지 않았다 — 세는 단위가 「시험 함수」이고 이 레인이 센 것은 「게이트가 실행한 케이스」다. → 두 값을 같은 단위로 맞추려면 `--collect-only` 전수 계수가 필요하다.
7. **병합 트리에서의 계수** — 이 레인의 기준점은 `d4d11b5` 다. 그 뒤 `lane-review-clean` 에 다른 레인이 들어왔고(회수 시점 `660f8fe`), 그중 C(viz-render)·D(pipeline-worker)·B(core-api)·E(frontend)가 **시험을 늘린다.** 위 §4 의 199·200·552·119 는 **`d4d11b5` 시점의 값**이고 병합 뒤에는 달라진다. → 계획 §3-3 대로 오케스트레이터가 병합 트리에서 `service-tests-*` 넷을 다시 돌려 계수를 갱신한다. **게이트의 판정 규칙은 계수와 무관하다** — 늘어난 시험은 그대로 판정 대상이 된다.

## 6. 손대지 않은 것 (보고만)

- **`gates/config/artifact-ownership.toml` `[legacy] tolerate = true`** — 지시대로 **바꾸지 않았다.** 현재 전건 UNDECIDABLE 이고 `artifact-ownership.sh` 는 `tolerate=false` 일 때만 red 를 내므로 이 게이트는 **0건 판정으로 green** 이며 기한이 없다. 이것은 「구판을 고아로 세어 지우는 오삭제」를 막으려고 의도적으로 켠 값이라 게이트 쪽에서 결정할 수 없다. → **Ted 판정 필요**(계획 §4 유보 7). 판정에 필요한 것 = 구판 사이드카(`sidecarVersion`·`baked_for` 없음)를 언제까지 보류할지의 기한 하나.
- `services/core-api/tests/fixtures/setup-db.sh` · 타 서비스 `pyproject.toml` · `contracts/**` · `infra/**` · compose · `dev-package/{PLAN-SoT,work-items,03-HANDOFF,DEPLOY-CURRENT}` — 편집 0.
- core-api `e2e` 5건의 기존 실패 — 원천 마운트 부재가 원인이고 **고치지 않았다**(계획 §1: 기존 실패는 보고만).

## 7. 등재문 초안 (번호 없음 — 오케스트레이터가 발급)

> **CI 가 서비스 시험을 판정한다 — 실행 69 → 1070 케이스 · selftest 집합 손목록 폐지 · rc 78 을 「기대한 red」로 세지 않는다**
> 코드리뷰 #6. ⑴ `service-tests-{core-api,ai-service,viz-render,pipeline-worker}` 게이트 신설 ＋ CI `service-tests` 잡(단위별 `<단위> || contracts`). 수집 0건·실행 0건(전부 skip)·failed 는 red, skipped·deselected 는 요약줄에 건수로 드러낸다. core-api 는 게이트가 일회용 Postgres 를 세운다(포트 미공개·tmpfs·`--rm`·접속 문자열 미출력). 실측 green — core-api 552 · viz-render 199 · pipeline-worker 200 · ai-service 119, 실패 0 · skip 0.
> ⑵ 프런트 게이트 2종을 `contracts` 필터 잡에서 떼어 `frontend || contracts` 잡으로 옮겼다 — 종전에는 `frontend/` 만 바꾼 PR 의 게이트 잡이 0개였다. ⑶ `db-boundary` 를 CI 에 실었다 — 종전에는 셀프테스트만 있고 판정을 아무도 하지 않았다.
> ⑷ `run.sh selftest` 집합을 손목록(14)에서 `ALL_GATES` 파생(19 = 실행 17 ＋ 명시 면제 2)으로 바꿨다. 면제는 이름·사유·건수를 드러낸 채 넘어가고, 아무 말 없는 누락은 구조적으로 불가능하다.
> ⑸ 셀프테스트 16종의 판정 갈래를 `gates/tools/_expect.sh` 한 곳으로 모아 rc 78(준비 실패)을 「기대한 red」로 세지 않게 했다 — 실측으로 뒤집힌 케이스 16건. 실패 픽스처 — venv 부재를 주입하면 개정 전 rc 0(세 케이스 「✓ red」), 개정 후 rc 78.
> ⑹ ai-service 에 `dictdb` 표식 등록(대상 3파일 26건 — 지시문이 지목한 6파일 중 셋은 DB 를 쓰지 않아 제외).
> `[미확인]` — Actions 실제 실행(draft PR 1회로 풀린다) · 러너에서의 core-api 일회용 Postgres · 뺀 표식 113건(원천 마운트·dbint·dictdb 환경 필요). `artifact-ownership.toml tolerate=true` 는 손대지 않았고 **Ted 판정 대기**다.

## 8. 커밋 (자기 브랜치에만 · push 없음)

| sha | 제목 |
|---|---|
| `2f9a1d8` | 서비스 pytest 묶음을 판정하는 게이트 4종과 그 셀프테스트를 세운다 |
| `2750a63` | 셀프테스트가 준비 실패(rc 78)를 「기대한 red」로 세지 않게 한다 |
| `6c2cf40` | selftest 집합을 손목록에서 파생으로 바꾸고 게이트 5종을 등록한다 |
| `4b0b269` | ai-service 에 dictdb 표식을 등록해 DB 필요 시험을 이름으로 뺀다 |
| `0d234f2` | CI 가 서비스 시험·프런트 게이트·DB 경계를 실제로 판정하게 배선한다 |
