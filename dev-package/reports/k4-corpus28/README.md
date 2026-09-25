# WU5 K4 재측정 — 28건 코퍼스 (2026-09-25)

> ⚠ K4-I 「충분」 판정은 일회용 DB 한정 — dev 와 일회용 DB 의 literal 결과가 같은 28 ID 에서 갈린다(005·010, 원인 미확인). 근거 §4 문항별 표 · §5-2 · §7-2.

- 사전 등록: `dev-package/reports/corpus-expansion/wu5-preregistration-2026-09-25.md`(커밋 `82ecf733` · 2026-09-25T08:07:10+09:00). 이 보고서는 그 §3(K4)의 표 순서를 따른다.
- 범위: K4 세 갈래(K4-L · K4-E · K4-I)만. **K3(§4)는 이 레인에서 돌리지 않았다.**
- 측정 커밋(`local_sha`): `646131c9`(사전 등록 `82ecf733` + 아래 §0 러너 수정 1건). 결과 JSON 네 건 모두 같은 값을 싣는다.
- 모델 호출 합계 **24회**(K4-I 모델 절반만). K4-L·K4-E·K4-I 검색 절반은 0회.
- 판정: 사전 등록 §2 기준 **4건 모두 「측정됨」**. 최종 회차 중 78 로 끝난 것은 없다. 단 K4-L 첫 회차 1건이 78 이었다(§0).

## 0. 78 회차와 측정 후 러너 수정 (기록에서 지우지 않는다)

| 시각(+09:00) | 실행 | 종료코드 | 출력 |
|---|---|---|---|
| 08:09:04 | `golden_baseline.py --mode literal --output …/k4-corpus28/literal-01.json` | **78** (`Preparation failure: RuntimeError`) | 파일 없음(러너는 78 에서 쓰지 않는다) |

- 원인: `REMOTE` 의 `assert subject in known.values(), 'subject absent'`. dev core-api 의 주체 토큰 표(`COLAB_CORE_SUBJECTS_FILE`)가 **`{}`(0건)** 이었다. 재시드 뒤 토큰 표가 비었고, 스냅샷 v2 주체(연구실 `…HYMETS`)는 그 표에 없다.
  읽기 전용 진단(키·주소 미출력)으로 확인했다 — 토큰 표 `dict 0`. dev 에 쓰지 않았다.
- 수정(`646131c9`): 주체 확인을 토큰 표 대신 **같은 읽기 전용 스코프 안에서 `d1_account(id, lab_id)` 가 정확히 1행**인지로 바꿨다. 토큰 표는 인증 수단이고 계정 존재의 증거가 아니다.
  판정 함수(`assess`)·질의·출력 형식·골든·스냅샷은 바꾸지 않았다. 시험 `eval/k4-search/test_golden_baseline.py::RemoteSubjectCheckTests` 2건 — 수정 전 red(`AssertionError: 'COLAB_CORE_SUBJECTS_FILE' unexpectedly found in …`) → 수정 후 green(ai-service venv 로 `test_*.py` 68건 OK).
- 이 수정은 사전 등록 §7 에 없던 **사후 수정**이다. 근거는 사전 등록 §2 「78 이 나면 … 원인을 고친 뒤 새 출력 경로로 다시 돌리고, 78 회차를 기록에서 지우지 않는다」. 그래서 K4-L 은 `literal-01.json` 이 아니라 **`literal-02.json`** 이다.
- `llm_interpreter_probe.py` 는 같은 `REMOTE` 를 재사용하지만 `--skip-remote` 로 돌렸으므로 이 수정의 영향을 받지 않는다.

## 1. 실행 명령 (키·접속값은 프로세스 환경으로만 · 출력·기록 없음)

`<env>` = 운영자 로컬 환경 스크립트(`COLAB_DEV_SSH`·`COLAB_DEV_KEY_FILE`·`OPENAI_API_KEY` 를 환경으로 싣는 래퍼). 값은 이 문서에 적지 않는다.

```
# K4-L (dev D3 읽기 전용 · 모델 0) — 08:12:13
<env> services/ai-service/.venv/bin/python eval/k4-search/golden_baseline.py --mode literal --output dev-package/reports/k4-corpus28/literal-02.json      # exit 1
# K4-E (dev ai-service 낱말 해석·사전·그래프 → dev D3 읽기 전용 · 모델 0) — 08:12:19
<env> services/ai-service/.venv/bin/python eval/k4-search/golden_baseline.py --mode expanded --output dev-package/reports/k4-corpus28/expanded-01.json   # exit 1
# K4-I 모델 절반 (gpt-5.6-luna 실호출 24회) — 08:12:29
<env> services/ai-service/.venv/bin/python eval/k4-search/llm_interpreter_probe.py --repeats 2 --skip-remote --output dev-package/reports/k4-luna-probe/interp-02.json   # exit 0
# K4-I 검색 절반 (일회용 Postgres · 스냅샷 v2 28건 고정 ID · 모델 0) — 08:14:10 종료
COLAB_K4_PROBE_INTERP=$PWD/dev-package/reports/k4-luna-probe/interp-02.json COLAB_K4_PROBE_OUT=$PWD/dev-package/reports/k4-luna-probe/retrieval-02.json \
  bash gates/tools/service-tests.sh core-api k4_probe   # exit 0 · 수집 1 · 실행 1 · failed 0 · errors 0
```

- `golden_baseline.py` 종료코드 1 = 「retrieval 자동 검사 1건 이상 fail」(`golden_baseline.py:4`) — 사전 등록 §2 에서 「측정됨」이다.
- 러너 인자는 기본값 그대로(`--timeout 8.0` · `--repeats 2` · `--provider openai` · `--model gpt-5.6-luna`). `--omit-topic-filter` 미사용.

## 2. 동일성 확인 (결과 JSON 기록값)

| 항목 | 값 |
|---|---|
| `suite_sha256`(golden-cases.json) | `ef5227126c80…` (K4-L·K4-E·K4-I 동일) |
| `snapshot_sha256`(dev-data-snapshot-v2.json) | `171ddd497a41…` (동일) |
| `search_code_sha256`(dev 배포 `d3_catalog`) | `353ca83d2214…` (K4-L·K4-E 동일) |
| `read_only` | `on` (K4-L·K4-E) |
| dev 코퍼스 건수(`corpus`) | 28 (K4-L·K4-E) · 일회용 DB `corpus_size` 28 |
| K4-E `degraded` | 12/12 `false` |
| `system_prompt_sha256` | `9b5069c7a0dc…` — `interp-01.json`(2026-09-22)과 **같다** |
| `interpreter_sha256`(interpret.py) | `6f80c7ec260c…` — `interp-01.json` 과 **다르다**(프롬프트 문자열은 같고 파일이 바뀌었다 · 차이 내용은 이 측정에서 보지 않았다) |
| `runner_sha256`(llm_interpreter_probe.py) | `interp-01.json` 과 같다 |

## 3. K4-L 낱말 검색 — `literal-02.json` (모델 0 · 1회)

| 지표 | 값 | 합격선(사전 등록 §3-1) |
|---|---|---|
| retrieval pass / fail / N/A | **7 / 3 / 2** (판정 대상 10 중 pass 7 · fail = 004·005·010) | no threshold — descriptive only |
| 필수 정답 순위 | 찾음 9/14 · 중앙값 **2** | no threshold — descriptive only |
| 범위 밖 결과 `outside_ids` | 합계 38건 (001 12 · 004 7 · 006 2 · 007 9 · 011 8) | no threshold — descriptive only |
| D3 `sql_seconds` | 최소 0.003 · 중앙 0.004 · 최대 0.017초 | no threshold — descriptive only |
| 의미 판정 | 12/12 `unassessed` | 이번 범위 밖 |

## 4. K4-E 확장 검색 — `expanded-01.json` (모델 0 · 1회)

| 지표 | 값 | 합격선 |
|---|---|---|
| retrieval pass / fail / N/A | **8 / 2 / 2** (fail = 005·010) | no threshold — descriptive only |
| 필수 정답 순위 | 찾음 10/14 · 중앙값 **2.0** | 〃 |
| 범위 밖 결과 | 합계 35건 (001 8 · 004 8 · 006 2 · 007 9 · 011 8) | 〃 |
| D3 `sql_seconds` | 최소 0.002 · 중앙 0.004 · 최대 0.010초 | 〃 |
| 확장이 더한 것 | 004 `GK-2A` · 008 `가뭄지수`·`가뭄` · 009 `가뭄` · 010 `가뭄` · topic `가뭄` = 008·009·010. 기능어 제거는 `자료` 만 빠졌고 `찾아줘` 는 남았다 | 기록 |

### K4-L · K4-E 문항별 (dev · 28건)

| # | mode | K4-L 결과 (총·범위 밖·필수 순위) | K4-E 결과 (총·범위 밖·필수 순위) |
|---|---|---|---|
| 001 | retrieval | pass · 19 · 12 · [4] | pass · 15 · 8 · [3] |
| 002 | retrieval | pass · 11 · 0 · [2] | pass · 5 · 0 · [3] |
| 003 | retrieval | pass · 12 · 0 · [10] | pass · 5 · 0 · [5] |
| 004 | retrieval | **fail** · 15 · 7 · [—] | pass · 18 · 8 · [2] |
| 005 | retrieval | **fail** · 3 · 0 · [—,—,—,—] | **fail** · 3 · 0 · [—,—,—,—] |
| 006 | retrieval | pass · 12 · 2 · [4, 2] | pass · 9 · 2 · [5, 2] |
| 007 | retrieval | pass · 17 · 9 · [2] | pass · 17 · 9 · [2] |
| 008 | retrieval | pass · 7 · 0 · [1, 2] | pass · 2 · 0 · [1, 2] |
| 009 | retrieval | pass · 7 · 0 · [1] | pass · 2 · 0 · [1] |
| 010 | empty | **fail** · 9 · 0 · 범위 안 9건 | **fail** · 2 · 0 · 범위 안 2건 |
| 011 | manual | N/A · 19 · 8 | N/A · 15 · 8 |
| 012 | manual | N/A · 11 · 0 | N/A · 7 · 0 |

## 5. K4-I 해석기 프로브 — `../k4-luna-probe/interp-02.json` · `../k4-luna-probe/retrieval-02.json`

> ⚠ K4-I 「충분」 판정은 일회용 DB 한정 — dev 와 일회용 DB 의 literal 결과가 같은 28 ID 에서 갈린다(005·010, 원인 미확인). `interp-02.json`(모델 절반)은 dev 를 거치지 않고, `retrieval-02.json`(검색 절반)은 일회용 DB 결과다.

### 5-1. 모델 절반 (gpt-5.6-luna · 24회 호출 · 1회 실행)

| 지표 | 값 | 합격선(사전 등록 §3-3) |
|---|---|---|
| 모델 호출 | 24 (`model_calls`) | — |
| 응답 읽기 실패 → literal 폴백 | **0/24** (`fell_back_to_literal` = []) · `degraded` 0/24 | descriptive only |
| 지연 `calls[].seconds` | 최소 1.65 · 중앙 2.44 · 최대 5.48초 · **8초 초과 0/24** | 「충분」 ③ timeout 0/24 · 제품 timeout 8초 안 |
| 기능어 혼입 | **0/24** 해석 | 0건 |
| 질문에 없는 낱말 | **0/24** 해석 | 0건 |
| topic | 24/24 유효값. 회차마다 식생·NDVI 7 · 가뭄 3 · 강우·강수 2 | 유효값 건수만 기록 |
| isDataQuery | 24/24 true | — |
| 결정성 | 2회 terms 집합이 갈린 문항 **8/12** (001·002·003·005·006·007·009·010) · 같은 문항 4 (004·008·011·012) | 기록만 |

- 기능어·날조 계수는 러너 자신의 `llm_interpreter_probe.lint` 를 두 회차 24건에 적용한 값이다. `--skip-remote` 이면 러너가 `judge` 를 건너뛰어 `lint` 를 JSON 에 싣지 않는다(과거 `interp-01.json` 도 같다). 재계산:
  `services/ai-service/.venv/bin/python -c` 로 `eval/k4-search` 를 `sys.path` 에 넣고 `interp-02.json` 의 `passes[*][*]` 에 `llm_interpreter_probe.lint` 를 적용한다.
- 문항별 terms(1회차 / 2회차) — 전문은 `interp-02.json` `passes`:
  - 004 `GK2A_NDVI_mean_202305.tif`·`천리안` (두 회차 같음 · 「원자료」는 버림 — interp-01 과 같은 양상)
  - 009 1회차 `시군구별`·`주간`·`SPI-4weeks`·`SPI` / 2회차 `…`·`SPEI`·`SPI` — **2회차는 「SPEI 말고」의 부정을 반영하지 않았다**(검색 결과는 두 회차 모두 pass · 총 1건)
  - 010 1회차 `U-Net`·`가뭄지수` / 2회차 `U-Net`·`예측한`·`가뭄지수`

### 5-2. 검색 절반 (일회용 DB · 스냅샷 v2 28건 · 모델 0)

| 실행 | retrieval pass (판정 10) | 실패 문항 | 필수 순위 중앙값 (찾음/전체) |
|---|---|---|---|
| luna 1회차 | **10/10** | — | **2.0** (14/14) |
| luna 2회차 | **10/10** | — | **2.0** (14/14) |
| literal | 9/10 | 010 (「없는 산출물」에 범위 안 7건) | 3.0 (14/14) |

| # | luna#1 (총·범위 밖·순위) | luna#2 | literal |
|---|---|---|---|
| 001 | pass · 4 · 0 · [1] | pass · 5 · 0 · [3] | pass · 9 · 4 · [3] |
| 002 | pass · 5 · 0 · [3] | pass · 4 · 0 · [1] | pass · 9 · 0 · [2] |
| 003 | pass · 1 · 0 · [1] | pass · 1 · 0 · [1] | pass · 7 · 0 · [5] |
| 004 | pass · 3 · 0 · [3] | pass · 3 · 0 · [3] | pass · 13 · 8 · [5] |
| 005 | pass · 5 · 0 · [3,4,5,2] | pass · 5 · 0 · [3,4,5,2] | pass · 6 · 0 · [3,4,5,6] |
| 006 | pass · 6 · 2 · [4,2] | pass · 6 · 2 · [4,2] | pass · 13 · 4 · [3,2] |
| 007 | pass · 7 · 2 · [2] | pass · 2 · 0 · [2] | pass · 8 · 2 · [2] |
| 008 | pass · 2 · 0 · [1,2] | pass · 2 · 0 · [1,2] | pass · 7 · 0 · [1,2] |
| 009 | pass · 1 · 0 · [1] | pass · 1 · 0 · [1] | pass · 6 · 0 · [1] |
| 010 | pass · 0 | pass · 0 | **fail** · 7 · 0 |
| 011 | N/A · 7 | N/A · 7 | N/A · 11 |
| 012 | N/A · 7 | N/A · 7 | N/A · 11 |

### 5-3. 「충분」 조건 대조 (2026-09-22 intent · 사전 등록 §3-3)

| 조건 | 결과 |
|---|---|
| ① luna pass ≥ literal pass | 10 ≥ 9 (두 회차) — 충족 |
| ② luna 순위 중앙값 ≤ literal | 2.0 ≤ 3.0 (두 회차) — 충족 |
| ③ 모델 timeout 0/24 | 0/24 (최대 5.48초) — 충족 |

- 셋 동시 충족 = 이 코퍼스(**일회용 DB 한정** · 28건)에서 「충분」 — dev 에서의 「충분」은 이 측정이 보이지 않는다(§7-2). 이번 실행은 한 번(24회)이다 — 2026-09-22 에는 미보존 첫 실행에서 2/24 timeout 이 있었다(`../k4-luna-probe/README.md`). 이번에는 버린 실행이 없다.
- 검색 절반은 dev 가 아니라 일회용 DB 다. 사전·그래프 확장은 넣지 않았다(순수 해석기 ↔ 검색).

## 6. 과거 기준선과 나란히 (사전 등록 §6 · §5 ③ — 차이를 개선·악화로 읽지 않는다)

과거 기준선은 코퍼스(dev 25건 · 참조 9건)·골든 scope·required(10 → 14)가 다르다.

| 측정 | 과거 (경로 · 값) | 이번 (경로 · 값) |
|---|---|---|
| K4-L | `stage3-ai-search-plan/literal-baseline-02.json` · dev 25건 · pass 7 · fail 3(003·005·010) · N/A 2 · 순위 중앙값 2.0(8/10) · 범위 밖 16 | `k4-corpus28/literal-02.json` · dev 28건 · pass 7 · fail 3(004·005·010) · N/A 2 · 중앙값 2(9/14) · 범위 밖 38 |
| K4-L (정규화) | `literal-normalized.json` · pass 8 · fail 2(005·010) | — (이번 대응 실행 없음) |
| K4-E | `expanded-baseline-01.json` · pass 6 · fail 4(003·004·005·010) · 중앙값 2(7/10) | `k4-corpus28/expanded-01.json` · pass 8 · fail 2(005·010) · 중앙값 2.0(10/14) |
| K4-E 참고 | `expanded-no-topic-01.json` pass 7 · `expanded-normalized-02.json`(`local-expanded`) pass 8 | — |
| K4-I 모델 절반 | `k4-luna-probe/interp-01.json` · 24회 · 폴백 0 · 기능어 0 · 날조 0 · timeout 0/24 · 지연 1.42/2.74/5.79초 · 결정성 갈림 4/12 | `k4-luna-probe/interp-02.json` · 24회 · 폴백 0 · 기능어 0 · 날조 0 · timeout 0/24 · 지연 1.65/2.44/5.48초 · 갈림 8/12 |
| K4-I 검색 절반 | `k4-luna-probe/retrieval-01.json` · 9건 · luna 10/10·10/10 중앙값 1.0 · literal 9/10 · 2.0 | `k4-luna-probe/retrieval-02.json` · 28건 · luna 10/10·10/10 중앙값 2.0 · literal 9/10 · 3.0 |

## 7. 이상 사항

1. **K4-L 첫 회차 78**(§0) — dev 토큰 표 `{}`. 러너 수정 뒤 새 경로로 완주.
2. **같은 literal 해석이 dev 와 일회용 DB 에서 다르게 나온다.** 005: dev K4-L 총 3건·필수 4건 모두 없음(fail) / 일회용 DB literal 총 6건·필수 4건 모두 찾음(pass). 010: dev 범위 안 9건 / 일회용 DB 7건. 두 코퍼스는 같은 28 ID 이지만 적재 경로가 다르다(일회용 DB = `seed_reference_corpus` + 근거 패킷 · dev = 재시드 실데이터). 차이의 원인은 이 측정에서 **[미확인]**.
3. `retrieval-02.json` 의 `kind` 문자열이 「reference corpus (9 datasets …)」다 — `test_k4_interpreter_probe.py:82` 의 낡은 문자열(사전 등록 §3-3 ⚠). 실제 건수는 `corpus_size` 28.
4. `interpreter_sha256` 이 2026-09-22 와 다르다(§2). 프롬프트 hash 는 같다.
5. K4-E 기능어 제거가 `찾아줘` 를 남긴다(12문항 모두 `찾아줘` 가 terms 에 있다). 기록만.
6. luna 2회차 009 가 부정(「SPEI 말고」)을 반영하지 않았다(§5-1). 검색 결과에는 영향이 없었다.

## 8. 돌리지 않은 것

- K3 전부(사전 등록 §4 — J1 recall@k · 후보·대조군 · 두 팔). 이 레인의 범위 밖이다. K3 모델 절반은 사전 등록 §7 의 선행 수정(`llm_lineage_probe.py:600-601`) 없이는 78 이다.
- K4 의미 판정(C1~C6) — 사전 등록 §3-1 에서 범위 밖.
