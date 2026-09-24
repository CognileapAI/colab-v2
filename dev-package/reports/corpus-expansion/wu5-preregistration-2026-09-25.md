# WU5 재측정 — 판정 기준 사전 등록 (측정 전)

- **등록 시각 = 이 파일을 처음 담은 커밋의 커밋 시각.** 이 커밋 전에 WU5 측정 출력 파일은 한 건도 없다
  (아래 §6 의 출력 경로 전부 부재 · `dev-package/reports/` 에 `k4-corpus28/` 디렉터리 없음).
- 기준 브랜치 = `origin/corpus-wu4-golden` `940075c3`(골든 12문항 v2 재박기 · 스냅샷 v2 · 골든 회귀 12/12 · 모델 호출 0).
- WU5 정의 = `dev-package/intent/2026-09-24-corpus-expansion-dev-reseed.md`(`fb89cd71`) 「WU5 ⑴~⑷」 · 완료 조건 5
  「K4 `golden_baseline.py --mode literal` · `--mode expanded` 가 78(준비 실패) 없이 끝나고, `bash gates/tools/service-tests.sh core-api k3_probe` 가 후보 JSON 을 쓴다」.
  같은 intent 원한 결과 5 — 「판정 red 여부는 이 intent 의 목표가 아니다(측정이지 게이트가 아니다).」
- **이 문서는 새 합격선을 만들지 않는다.** 과거 intent·보고서가 정한 선은 출처와 함께 인용하고, 정한 곳이 없으면
  「no threshold — descriptive only」로 적는다. 분모가 바뀐 선(6엣지 → 10엣지 등)은 §5 규칙대로만 읽는다.

## 0. 코퍼스 · 표본 (측정 전 고정값)

| 항목 | 값 | 출처 |
|---|---|---|
| 스냅샷 | `eval/k4-search/fixtures/reference/dev-data-snapshot-v2.json` · 데이터셋 28 · 계보 18(주입력 13 · 보조입력 5) · `edges_with_method` 0 · `variable_rows` 0 | 같은 파일 `counts` |
| 자동 메타 fill(28건 중) | period 28 · format 26 · grid 26 · crs 24 · variables 0 · fileName 28 | 같은 파일 `counts.autometa_fill` |
| K4 골든 | 12문항 = retrieval 9 · empty 1 · manual 2. scope 001 = 7건, 002~012 = 14건 | `eval/k4-search/golden-cases.json` · `eval/k4-search/golden-set.md:201` |
| K3 정답 | 자식 5 · 엣지 10 · 후보 모집단 28 | `eval/k3-lineage/lineage-cases.json` `sample_limits` |

과거 K3·K4 실측(참조 9건 · 엣지 6)은 **자동 메타 축이 `fileName` 하나뿐**이었다(`dev-package/reports/k3-lineage-probe/README.md:186`).
이번 코퍼스는 period·crs·grid 가 채워진 첫 측정이다. variables 는 여전히 0 이다.

## 1. 모델 · 설정 (제품 설정 그대로)

| 항목 | 값 | 제품 설정 위치 |
|---|---|---|
| 모델 | `gpt-5.6-luna` | `services/ai-service/src/colab_ai/kernel/config.py:79`·`:117`(`COLAB_MODEL_HELPER` 기본값) · `infra/dev/compose.yml:164` |
| timeout | 8.0초 | `config.py:81` · `app/interpret.py:166` · `app/suggest.py:195` |
| K4 해석 요청 | `response_format json_object` · `seed 20260826` · `temperature` 없음 | `app/interpret.py:66`·`:217-221` |
| K3 제안 요청 | `response_format json_object` · `seed 20260924` · `temperature` 없음 | `app/suggest_wire.py:32-33`·`:99-102` |
| 전송 | OpenAI chat completions · 키 = 프로세스 환경 `OPENAI_API_KEY`(값은 출력·기록하지 않는다) | `eval/k4-search/llm_interpreter_probe.py:97-112`·`:193-196` · `eval/k3-lineage/llm_lineage_probe.py:586`·`:608-613` |
| K3 후보 선정 | 전략 `filtered` · k=20 | `services/core-api/src/colab_core/app/routes/ingestion.py:545`·`:547` |
| K3 최종 제안 상한 | 20 | `services/core-api/src/colab_core/app/relay.py:488` |
| dev 운영 모드(비교 기준) | 질의 해석 `literal` | `infra/dev/compose.yml:166` |

- `llm_interpreter_probe.py` 의 `--provider anthropic`(`:171`·`:187-191`)은 **쓰지 않는다.** `--provider openai --model gpt-5.6-luna` 기본값만 쓴다
  (`AGENTS.md` — 「모델을 부르는 eval은 로컬에서 실제 사용 모델로 실행한다」). Claude 결과로 대체하지 않는다.
- 러너 인자는 기본값 그대로다 — `--timeout 8.0` · `--repeats 2` · `--base-url` 기본. 프롬프트·파서·검증기는 바꾸지 않는다.
  결과 JSON 의 `system_prompt_sha256`·`suggester_sha256`·`verifier_sha256`·`interpreter_sha256`·`local_sha` 로 동일성을 확인한다.

## 2. 「측정됨」 과 「측정 실패(78)」 — 공통 정의

| 판정 | 조건 |
|---|---|
| **측정됨** | 러너·시험의 종료코드가 0 이고, §6 의 출력 JSON 이 새 경로에 생겼다. `golden_baseline.py` 는 종료코드 **1**(자동 포함 검사 실패 1건 이상)도 측정됨이다 — `golden_baseline.py:4`「Exit 1: at least one retrieval check fails」는 판정 결과이고 준비 실패가 아니다 |
| **측정 실패(78 · 준비 실패)** | 러너가 78 로 끝남(항목별 원인은 각 절). 또는 `service-tests.sh` 가 78(venv·파이썬 부재 · 일회용 DB 기동 실패 — `gates/tools/service-tests.sh:20-21`) |
| **측정 불성립(구조 단언 실패 · 78 아님)** | 측정 시험(`k4_probe`·`k3_probe`)이 종료코드 1. 이 시험들은 수치를 판정하지 않고 구조만 단언한다(`test_k4_interpreter_probe.py:90-91` · `test_k3_lineage_probe.py:342-368`). 1 이면 수치를 쓰지 않고 원인을 적는다 |

- 모델 timeout·전송 예외는 78 이 아니다. 측정값이다(J8 · K4 `fell_back_to_literal`).
- 78 이 나면 **자동 재시도하지 않는다.** 원인을 고친 뒤 새 출력 경로로 다시 돌리고, 78 회차를 기록에서 지우지 않는다.

## 3. K4

### 3-1. K4-L 낱말 검색 (`golden_baseline.py --mode literal`) — 모델 호출 0

- 경로: 로컬 `LiteralInterpreter` → dev 의 D3 `search_datasets` 를 **읽기 전용**으로 호출(`golden_baseline.py:95-127` · `read_only_scope` · `SHOW transaction_read_only` 가 `on` 이어야 한다 `:203`). dev 에 쓰지 않는다.
- 반복: 1회.

| 지표 | 계산 위치 | 합격선 |
|---|---|---|
| retrieval pass/fail/not_applicable 건수 | `golden_baseline.assess` `golden_baseline.py:58-72` → `counts` `:208` | no threshold — descriptive only (판정 대상 10 = retrieval 9 + empty 1 · manual 2 제외 — `dev-package/intent/2026-09-22-k4-luna-interpreter-probe.md` 「합격선」 ①) |
| 필수 정답 순위 `required_ranks` | `golden_baseline.py:71-72` | no threshold — descriptive only |
| 범위 밖 결과 `outside_ids` 건수 | `golden_baseline.py:70` | no threshold — descriptive only |
| D3 호출 시간 `sql_seconds` | `golden_baseline.py:122-124` | no threshold — descriptive only(`eval/k4-search/README.md:23` — LLM 지연·체감 속도가 아니다) |
| 의미 판정(C1~C6 등) | 러너 밖 — `semantic='unassessed'` `:69`·`:221` | 이번 WU5 범위 밖 · 미판정으로 적는다 |

- **78**: 출력 경로 존재(`:139-141`) · `COLAB_DEV_SSH`/`COLAB_DEV_KEY_FILE` 부재(`:143`·`:146`) · 문항 수 ≠ 12(`:149-150`) · 스냅샷·골든 검증 실패(`validate_suite` `:75-92`) ·
  원격 조회 실패(`:200-201` — dev 에 골든 ID 부재 `missing gold dataset` `:117`, 이름 변경 `gold name changed` `:120` 포함) · 읽기 전용 아님·결과 수 불일치(`:203-206`).

### 3-2. K4-E 확장 검색 (`golden_baseline.py --mode expanded`) — 모델 호출 0

- 경로: dev ai-service 의 낱말 해석·기능어 제거·사전·그래프 확장(`AI_REMOTE` `:34-55`) → dev D3 읽기 전용. LLM 을 부르지 않는다(`eval/k4-search/README.md:24`).
- 반복: 1회. `--omit-topic-filter` 는 쓰지 않는다(진단용 · `README.md:25`).
- 지표·합격선: K4-L 과 같은 표(같은 `assess`). 추가 기록 = `expansion.responses[].interpretation`(확장 terms·topic) · `dictionary`·`graph` 원자료 · `source_sha256`.
- **78**: K4-L 의 조건 전부 + 사전 조회 실패(`:187-188`) · 확장 `degraded` 가 false 가 아님(`expanded_cases` `:25-26`) · 확장 terms 형식 오류(`:28-29`).
- 비교: 같은 회차 K4-L 과 나란히 적는다. 합격선 없음 — descriptive only.

### 3-3. K4-I 해석기 프로브 — 모델 절반(모델 호출 24) + 검색 절반(모델 호출 0)

과거 방식 그대로(`dev-package/reports/k4-luna-probe/README.md:66-73`):
모델 절반 `llm_interpreter_probe.py --repeats 2 --skip-remote` → 검색 절반 `COLAB_K4_PROBE_INTERP`·`COLAB_K4_PROBE_OUT` 을 준 `bash gates/tools/service-tests.sh core-api k4_probe`
(일회용 Postgres · 스냅샷 v2 28건 고정 ID · `seed_reference_corpus` · `test_k4_interpreter_probe.py:68-91`).

- 반복: 모델 해석 2회(12문항 × 2 = **24회 호출**). 검색 절반은 기록된 두 회차 + literal 을 각각 1회 재생.

| 지표 | 계산 위치 | 합격선 (출처) |
|---|---|---|
| retrieval pass 건수 (luna 회차별 · literal) | `test_k4_interpreter_probe._assess` `:25-35` → `_summary.passed/judged` `:59-65` | 「충분」 ① **luna 의 retrieval pass 건수 ≥ literal 의 pass 건수**(판정 대상 = retrieval 9 + empty 1, manual 2 제외) — `2026-09-22-k4-luna-interpreter-probe.md` 「합격선」 |
| 필수 정답 순위 중앙값 | `_summary.rank_median` `:61`·`:64` | 「충분」 ② **필수 정답 순위의 중앙값 ≤ literal** — 같은 곳 |
| 모델 timeout 건수 | 모델 절반 `calls[].seconds`(`llm_interpreter_probe.py:105-112`) > 8.0 · `fell_back_to_literal` `:200` | 「충분」 ③ **모델 timeout 0/24** — 같은 곳. 셋 동시 충족 = 「충분」 |
| 응답 읽기 실패 → literal 폴백 | `fell_back_to_literal` `:200`·`:213` | no threshold — descriptive only |
| 기능어 혼입 | `lint.function_words` `:127-136`(목록 `:33`) | **0건** — 같은 intent 「판정 기준」 표 「기능어 혼입」 |
| 질문에 없는 낱말 | `lint.not_in_query` `:133` | **0건** — 같은 표 「동의어 날조」 |
| topic | `lint.topic_valid` `:134` | 유효값 건수만 기록. 정오 판정 안 함 — 골든셋에 topic 정답이 없다(`k4-luna-probe/README.md:21`) |
| 지연 | `calls[].seconds` 최소·중앙·최대 | **제품 timeout 8초 안** — 같은 표 「지연」 |
| 결정성 | `determinism_distinct_term_sets` `:202` | 기록만(보증 대상 아님) — 같은 표 「결정성」 |

- 미달 시 읽는 법(인용): 「미달이면 「불충분」이 아니라 「판정 보류 · 표본 확장」으로 적는다」 — 같은 intent 「합격선」.
- **78(모델 절반)**: 출력 경로 존재(`:176-178`) · `OPENAI_API_KEY` 부재(`:193-195`) · 문항 수 ≠ 12(`:182-183`) · 그 밖 예외(`:239-241`).
- **검색 절반**: 두 환경변수 부재는 skip 이 아니라 error(`test_k4_interpreter_probe.py:7`·`:69-70`) → 측정 불성립. 출력 존재도 같다(`:71`).
- ⚠ `test_k4_interpreter_probe.py:82` 의 `kind` 문자열에 「9 datasets」가 남아 있다. 수치에는 영향이 없고(`corpus_size` 는 실제 건수 `:86`) 이 문서는 고치지 않는다 — 결과 해석 때 `corpus_size` 를 쓴다.

## 4. K3

두 절반(`eval/k3-lineage/README.md:13-21`): 후보 절반 = `COLAB_K3_PROBE_OUT`·`COLAB_K3_CANDIDATES_OUT` 을 준 `bash gates/tools/service-tests.sh core-api k3_probe`(모델 호출 0 · 일회용 DB) →
모델 절반 = `services/ai-service/.venv/bin/python eval/k3-lineage/llm_lineage_probe.py --arm both --repeats 2 --candidates <후보 JSON> --output <새 JSON>`.

### 4-1. 후보 절반 — J1 recall@k (`test_k3_candidate_recall.py`)

| 지표 | 계산 위치 | 합격선 (출처) |
|---|---|---|
| 전략별(`recent`·`filtered`) recall@5·@10·@20 | `select_lineage_candidates(k=100)` `test_k3_candidate_recall.py:148-150` → `summary.recall` `:173-178`(`K_VALUES` `:26`) | `2026-09-24-k3-lineage-suggestion-resume.md` J1 「**6/6.** 미달이면 모델이 아니라 후보 선정의 결함이다」 = 당시 엣지 전건. 이번 분모는 10 — §5 규칙 ① |
| missed@20 · 자식별 모집단 | `:177-178` | descriptive only. recall@20 이 모집단 전체면 동어반복임을 함께 적는다(`k3-lineage-probe/README.md:21`·`:49`) |

### 4-2. 후보·대조군 기록 (`test_k3_lineage_probe.py`)

- 제품 함수 `_lineage_candidates(..., upload_level=)` `:241` 로 본군 후보를 고르고, 스냅샷 계보에서 대조군 4종을 **생성**한다(`GROUPS` `:52`).
- 스냅샷의 실제 자동 메타를 일회용 DB 에 덮어 쓴다 — `apply_snapshot_autometa` `:104-133`. 축별 채워진 건수 `autometa_axes_present` `:327-330` 를 결과에 싣는다(기대: 스냅샷 fill 그대로 · 지어내지 않는다).
- 형제 정의: `graph`(부모 공유) 우선, 0건이면 `same_level` 로 떨어지고 그 사실을 `sibling_rules` 에 적는다(`:55-56`·`:81-99`). 어느 규칙이 쓰였는지 기록한다 — 과거 S6 는 `same_level` 이었다.
- 구조 단언(수치 판정 아님): 자식 수·엣지 수 = `sample_limits`(`:342-343`) · 후보 1~20(`:344`) · 자식 자신 없음(`:345`) · 군별 무결성(`:349-368`).

### 4-3. 대조군 4종 (정의 = `test_k3_lineage_probe.py:14-18` · 판정 = `llm_lineage_probe.py:75-80`·`:552-570`)

| 군 | 정의 | 판정 규칙 (출처) |
|---|---|---|
| ⑴ `removed` | 정답 부모 제거 | **기록**(참인 인용의 비부모는 반려 사유 아님) — `2026-09-24-k3-abstention-by-structure.md` 「판정 기록 2회차」 1 · `RANKING_GROUPS` `:80` |
| ⑵ `descendants` | 자식의 후손만 | **빈 제안이 전건이 아니면 구조 누수 → red** — 같은 곳 · `STRUCTURAL_GROUPS` `:78` · `verdict` `:561-563` |
| ⑶ `siblings` | 형제만 | **기록**(구조로 못 막는 군) — 같은 곳 |
| ⑴′ `removed_and_siblings` | 정답+형제 제거 | **빈 제안이 전건이 아니면 구조 누수 → red** — 같은 곳 · `:78` |

- 원문 합격선: J5' 「대조군 3종 빈 제안 **각 4/4**(구조 보장이므로 100% 가 기준)」(`2026-09-24-k3-abstention-by-structure.md` 「판정 기준」),
  범위 한정: 「「없다」를 구조가 보장하는 범위는 후손·자기 자신·후보 밖 ID·인용 오류 넷이다」(같은 문서 「판정 기록 2회차」 1).
  러너는 이를 「`empty < len(rows)` 이면 red」로 이미 코드에 갖고 있다(`:561-563`) — 분모 변화에 따라 달라지지 않는다.
- 공허(`vacuous` · 후보 0건) 건수를 군마다 함께 적는다(`:565`). 과거 ⑵ 4/4 중 2건은 공허였다(`k3-lineage-probe/README.md:258`).
- 누수 갈래: `self`·`descendant`·`outside_candidates`·`citation_error`·`other`(`leak_kind` `:227-244`).

### 4-4. 두 팔

| 팔 | 무엇 | 반복 | 모델 호출 |
|---|---|---|---|
| 규칙 팔 `rules` | 제품 `rule_suggest.RuleBasedLineageSuggester`(`services/core-api/src/colab_core/app/rule_suggest.py:70`)를 같은 적격 집합에 — `run_rule_case` `llm_lineage_probe.py:439-456` | **1회**(결정적 · `:619-624`) | 0 |
| 규칙+모델 팔 `model` | 제품 `LlmLineageSuggester` → 제품 파서 → core-api `relay._within_candidates`(`relay.py:460`) → `relay._verified_suggestion`(`relay.py:491`) → `[:SUGGESTION_LIMIT]` — `run_model_case` `:419-436` · `verify_like_relay` `:395-416` | **2회**(`--repeats 2` · intent WU5 ⑶) | 상한 = 자식 5 × 군 5 × 2 = 50. 후보 0건인 칸은 부르지 않으므로 실제 수는 결과 `model_calls` 로 적는다(과거 S6 = 40칸 중 30회) |

### 4-5. J1~J9 (계산 = `llm_lineage_probe.judge` `:494-549`, 팔별)

| # | 지표 | 계산 위치 | 합격선 (출처) |
|---|---|---|---|
| J1 | 적격 필터 뒤 정답 포함률 | `J1_recall` `:512-516` | 「6/6 미만이면 `WU-S1` 반려」(`k3-lineage-probe/README.md:215`) · 원 기준 J1 「6/6」(`...-suggestion-resume.md`) = 엣지 전건 — §5 규칙 ① |
| J2 | hit@1 · hit@3 (회차별) | `edge_hits` `:140-153` → `J2_hit` `:517-520` | 「기록만. 다만 `hit@3 < 4/6` 이면 「판정 보류·표본 확장」」(`...-suggestion-resume.md` J2 · `...-abstention-by-structure.md` 「보류 기준은 hit@3 < 4/6」). 분모 10 — §5 규칙 ② |
| J3' | 최종 응답 인용 오류 | `citation_errors` `:246-262` → `final_citation_errors` `:524-525` · `red` `:547-548` | **1건이라도 red** — `...-abstention-by-structure.md` 「최종 응답의 인용 오류 0」 · 러너 머리말 `:24` |
| J3' | 검증기 폐기율 | `discard_rate` `:522-523` | 기록 — 같은 문서 「폐기율을 기록」. 분모(`evidence_claimed`)를 먼저 적는다(`k3-lineage-probe/README.md:243-252`) |
| J3 | 근거 hard 토큰 | `grounding` `:110-131` → `grounding_hard` `:527-528` | 「**위반 0건.** 후보·파일 메타에 없는 고유명사·수치가 근거에 나오면 red」(`...-suggestion-resume.md` J3). ⚠ `WU-S2` 뒤 근거 한 줄은 core-api 가 다시 쓴 고정 서식이다(`k3-lineage-probe/README.md:241`) — 수치는 적되 J3' 와 섞지 않는다 |
| J4' | 「확실」 제안의 정확도 | `calibration` `:265-275` → `J4_calibration` `:529` | 기록 — `...-abstention-by-structure.md` 「파생이라 보정표 대신 「확실 제안의 정확도」만 기록」. 확신도 파생 규칙 = 검증된 근거 종류 ≥2 확실 · 1 애매 · 0 제안 없음(같은 문서 「판정 기록」 Q4) |
| J5' | 군별 빈 제안 | `_group_judgement` `:552-570` → `J5_groups` `:530` | §4-3 |
| J6 | 후보 밖 ID | `outside_ids` `:220-224` → `J6_outside` `:531-533` | **0건.** 「1건이라도 나오면 core-api 가 버린 건수도 함께 적는다」(`...-suggestion-resume.md` J6) → `dropped_by_relay` `:533` |
| J7 | 규격 위반 | `format_violations` `:172-218` → `J7_format` `:534-536` | **0건** — `...-suggestion-resume.md` J7 |
| J8 | 지연 · timeout 초과 | `J8_latency` `:537-542`(timeout 8.0) | 「제품 timeout 안. 초과 건수를 적는다」(`...-suggestion-resume.md` J8) · 「8초 안」(`...-abstention-by-structure.md`) |
| J9 | 결정성 | `determinism` `:278-288` → `:543` | 「갈린 자식 수를 **기록만** 한다(보증 대상 아님)」(`...-suggestion-resume.md` J9) |

- 두 팔 비교(규칙 vs 규칙+모델): 「「규칙만」 vs 「규칙+모델」 두 팔을 나란히 실측해 모델의 기여를 숫자로 가른다」(`...-abstention-by-structure.md` 「판정 기록」 Q5). 가르는 선은 정하지 않았다 — descriptive only.
- 모델 침묵률(모델 팔 왕복 중 빈 배열 비율): 과거 29/30(`k3-lineage-probe/README.md:3`). 이번 축이 채워진 코퍼스에서 다시 적는 것이 이 측정의 목적이다(같은 문서 `:266`). 선 없음 — descriptive only.
- **78(모델 절반)**: 출력 경로 존재(`:589-590`) · 모르는 군 이름(`:593-595`) · **자식 수·엣지 수 불일치 `:600-601`** · `OPENAI_API_KEY` 부재(`:608-610`) · 후보가 계약 밖(`:422-423`) · 그 밖 예외(`:667-669`).

## 5. 분모가 바뀐 선을 읽는 규칙 (새 선을 만들지 않는다)

- ① **「전건」 선(J1 6/6 · J5' 각 4/4)** — 원문은 당시 분모의 전건이다. 이번에는 같은 뜻으로 **전건(J1 = 10/10 · J5' = 군별 자식 전건)** 으로 읽는다.
  J5' 는 러너 코드(`llm_lineage_probe.py:561-563`)가 이미 전건으로 판정하고, J1 은 이 문서가 원문의 「6/6」을 「엣지 전건」으로 옮긴 것이다 — 그 옮김을 여기 적어 둔다.
- ② **비율 선(J2 `hit@3 < 4/6`)** — 10엣지 분모의 대응값을 정한 문서가 없다. **환산하지 않는다.** 이번 J2 는 **no threshold — descriptive only** 로 적고,
  원문 4/6 선은 인용만 한다. 「10엣지로 승격·확대를 결정하지 않는다. 미달은 「판정 보류 · 표본 확장」」(`eval/k3-lineage/README.md:45-47`)은 그대로 적용한다.
- ③ **과거 수치와의 비교** — 과거 기준선은 코퍼스(9건·25건)·골든 scope·required·엣지가 다르다. 나란히 적되 차이를 개선·악화로 읽지 않는다
  (「9건 코퍼스의 결과를 25~28건 코퍼스로 외삽하지 않는다」 — `dev-package/reports/k4-luna-probe/README.md:88`).

## 6. 비교 기준선(과거 실측 · 읽기만) · 이번 출력 경로(새 파일)

| 측정 | 과거 기준선 (경로 · 값) | 이번 출력(새 파일 · 이미 있으면 78) |
|---|---|---|
| K4-L | `dev-package/reports/stage3-ai-search-plan/literal-baseline-02.json`(2026-09-12 · dev 25건 · pass 7 · fail 3 · N/A 2) · `literal-normalized.json`(pass 8 · fail 2) | `dev-package/reports/k4-corpus28/literal-01.json` |
| K4-E | `.../stage3-ai-search-plan/expanded-baseline-01.json`(pass 6 · fail 4 · N/A 2) · `expanded-no-topic-01.json`(pass 7) · `expanded-normalized-02.json`(`local-expanded` · pass 8) | `dev-package/reports/k4-corpus28/expanded-01.json` |
| K4-I 모델 절반 | `dev-package/reports/k4-luna-probe/interp-01.json`(luna 24회 · 폴백 0/24 · 기능어 0 · 날조 0 · timeout 0/24) | `dev-package/reports/k4-luna-probe/interp-02.json` |
| K4-I 검색 절반 | `.../k4-luna-probe/retrieval-01.json`(9건 · luna 10/10·10/10 순위 중앙값 1.0 · literal 9/10 · 2.0) | `dev-package/reports/k4-luna-probe/retrieval-02.json` |
| K3 J1 recall@k | `dev-package/reports/k3-lineage-probe/j1-2026-09-24b.json`(엣지 6 · recent 3/6/6 · filtered 6/6/6) | `dev-package/reports/k3-lineage-probe/j1-<측정일>-corpus28.json` |
| K3 후보·대조군 | `.../k3-lineage-probe/candidates-2026-09-24d.json`(축 fileName 9 · 나머지 0 · `same_level`) | `dev-package/reports/k3-lineage-probe/candidates-<측정일>-corpus28.json` |
| K3 두 팔 | `.../k3-lineage-probe/luna-2026-09-24d-structure.json`(S6 · 호출 30 · J1 6/6 · J2 규칙 hit@3 2/6 · 모델 1/6·0/6 · ⑵·⑴′ 누수 0 · J3' 0 · J8 초과 0/30) | `dev-package/reports/k3-lineage-probe/luna-<측정일>-corpus28.json` |

- 재설계 전 K3 결과(`luna-2026-09-24.json`·`-24b`·`-24c-prompt`)는 파이프라인이 달라(core-api 인용 검증 이전) 기준선으로 쓰지 않는다 — 이력으로만 인용한다.
- 과거 기록 파일은 한 글자도 고치지 않는다. 읽는 표는 새 파일에 쓴다.

## 7. 측정 전 확인된 선행 결함 (측정 전에 등록)

- **K3 모델 절반은 지금 그대로 돌리면 반드시 78 이다.** `eval/k3-lineage/llm_lineage_probe.py:600-601`
  `if len(cases) != 4 or edges != 6: raise ValueError(...)` — 새 정답은 자식 5 · 엣지 10(`lineage-cases.json` `sample_limits`)이다.
  K4 쪽 같은 결함은 WU4 가 `golden_baseline.validate_suite` 로 「스냅샷에서 읽게」 고쳤다(`golden_baseline.py:75-82`). K3 러너는 아직이다.
- 이 수정은 **측정 전에, 수치를 보기 전에** 한다. 범위는 건수 검사를 후보 JSON 의 `sample_limits`(`test_k3_lineage_probe.py:317` 이 싣는 값)에서 읽게 바꾸는 것 하나로 한정한다.
  판정 함수(`judge`·`_group_judgement`·`citation_errors` 등)와 이 문서의 기준은 바꾸지 않는다. 수정 전 red(78) → 수정 후 측정 완주를 기록한다.

## 8. 실행 규율

- dev 에는 읽기만 한다(K4-L·K4-E 의 `read_only_scope`). S3 에 쓰지 않는다. K4-I 검색 절반·K3 후보 절반은 일회용 DB 다.
- 모델 호출이 있는 것은 K4-I 모델 절반(24회)과 K3 모델 팔(≤50회)뿐이다. 게이트 안에서 모델을 부르지 않는다(`eval/k3-lineage/README.md:17-18`).
- 키·접속값은 프로세스 환경으로만 준다. 출력·커밋하지 않는다.
- 결과 보고서는 이 등록 문서의 표 순서대로 적고, 등록에 없는 지표를 새로 보태면 「사후 추가」로 표시한다.
