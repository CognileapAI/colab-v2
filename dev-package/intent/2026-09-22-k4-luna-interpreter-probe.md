# Intent: 확정 헬퍼 `gpt-5.6-luna` 를 질의 해석기로 K4 골든 12건 실측한다 (결정 ㊷ 잔여 조건 · 제품 무변경)
메타 — 발의자: Ted(「haiku를 기준으로 검색을 검토」 → 「gpt로 하자」, 세션 model-change(haiku)) · 정리: Claude · 작성 2026-09-22 · 승인 **미승인**

## 문제
- 결정 `PLAN-SoT §9-㊷` 는 헬퍼(질의 해석)를 `gpt-5.6-luna` 로 확정했고, 잔여 조건을 「**K3·K4 평가셋에서 luna 품질 실측** — "충분"은 아직 가설」로 남겼다. 그 실측이 아직 없다.
- 지금까지의 K4 실측(`eval/k4-search/README.md`)은 전부 **모델 호출 0회**다. `golden_baseline.py` 의 세 mode 모두 `LiteralInterpreter` 만 쓴다. LLM 해석기가 검색 결과를 어떻게 바꾸는지 아무 수치도 없다.
- 이 실측이 ㊷ 의 잔여 조건 그 자체다. 제품 확정 모델(`gpt-5.6-luna`)을 제품 프롬프트·제품 파서 그대로 12문항에 돌려 literal 대비 수치를 낸다.

## 원한 결과 (proposed outcome)
- O1. 골든 12문항 각각에 대해 **luna 해석 결과(`isDataQuery`·`terms`·`topic`) 와 그 terms 로 dev D3 를 조회한 결과**가 JSON 으로 남는다. 제품과 같은 세 값만 읽고, 나머지는 읽지 않는다(`interpret.py` 규율 유지).
- O2. 같은 회차의 `--mode literal` 결과와 나란히 둔 비교표가 남는다 — 문항별 retrieval pass/fail · 필수 정답 순위 · terms 차이 · 기능어 혼입 여부 · topic 오판 여부 · 모델 지연(초).
- O3. 결과가 결정 ㊷ 를 바꾸지 않는다. 「무너지는 작업만 terra 로 승격」 판단은 Ted 몫이고, 이 intent 의 산출은 수치와 재사용 가능한 러너다(`--provider anthropic` 으로 다른 모델 비교도 같은 러너로 된다).

## 판정 기준 (실측 전에 못 박는다)
| 항목 | 어떻게 세나 | 어느 쪽이 나은가 |
|---|---|---|
| retrieval | `golden_baseline.assess()` 그대로 — 필수 정답 ⊆ 범위 안 결과 | pass 건수 많은 쪽. 12건 중 `manual` 2건은 판정 제외 |
| 정답 순위 | `required_ranks` | 낮을수록(앞일수록) 좋다 |
| 기능어 혼입 | terms 에 「자료」·「데이터」·「찾아줘」 류가 있는가 | 0건이어야 한다(SYSTEM_PROMPT 명시 지시) |
| 동의어 날조 | terms 중 질문 원문에 없는 낱말 수 | 0건이어야 한다(SYSTEM_PROMPT 명시 지시) |
| topic | 6값 중 하나 또는 null | 골든셋 `golden-set.md` 의 주제와 어긋나면 오판 |
| 지연 | 모델 왕복 초 | 제품 timeout 8초 안이어야 한다 |
| 결정성 | 같은 12문항 2회 실행 | terms 집합이 갈리는 문항 수를 기록만 한다(보증 대상 아님, `〈112〉`) |

### 합격선 — 어드바이저 지적(2026-09-23) 반영, 검색 절반 실측 **전에** 고정
- **「충분」** = 아래 셋을 동시에 만족. ① luna 의 retrieval pass 건수 ≥ literal 의 pass 건수(판정 대상 = `retrieval` 9건 + `empty` 1건, `manual` 2건 제외) ② 필수 정답 순위의 중앙값 ≤ literal ③ 모델 timeout 0/24.
- **미달이면 「불충분」이 아니라 「판정 보류 · 표본 확장」**으로 적는다. 10문항·2회로 terra 승격을 결정하지 않는다(1문항 차이가 결론을 뒤집는 표본이다).
- 개선 항목화 규칙: 복합어 구 질의 문제(001·002·006·007·008·012)는 **그 문항들이 실측에서 literal 보다 떨어질 때만** 항목으로 세운다. `d3_catalog.py:719` 가 구 질의를 설계로 명기했으므로(〈89〉) 실측 없이 계약 문제로 부르지 않는다.

### 검색 절반의 코퍼스 — dev 재시드가 아니라 일회용 DB
- 골든 정답 ID(`01M1SC…`, 2026-09-05 생성)는 DR-4(2026-09-14) 재적재 뒤 dev 에 없다(dev 는 `01M2F4…`). 재시드는 화면 업로드 경로라 ID 가 다시 나므로 **dev 를 채워도 `missing gold dataset` 에서 준비 실패한다.** 2026-09-22 보고서의 「DB 가 비어서」는 원인 오인이었다.
- 따라서 검색 절반은 `services/core-api/tests/test_search_reference_evidence.py` 가 쓰는 **일회용 Postgres + 스냅샷 9건 고정 ID** 코퍼스에서 잰다. dev 접속·재시드·승인이 필요 없다. 한계 = 후보 9건뿐이라 dev 의 나머지 distractor 가 없다. 보고서에 명기한다.
- 어드바이저가 짚었지만 이 회차가 열지 않는 것: K3 절반(㊷ 조건의 나머지) · 비용/지연 SLO 수치 · prod parity · terra 승격 기준. ㊷ 추기 문안에 「K3 미실측」을 명시한다.

## 영향 범위
- 사용자 / 화면: 없음.
- 서비스 · 스키마 · 계약: **없음.** `services/**`·`infra/**`·`config.py` 기본값·`SYSTEM_PROMPT` 무변경. 스크립트는 `eval/k4-search/` 에만 놓는다.
- 계약 파괴 여부: 아니오.
- dev 환경: **읽기 전용** 조회만(`golden_baseline.py` 의 REMOTE 와 같은 `read_only_scope`). 적재·삭제 0건.

## 제약
- 전송은 제품 `LlmQueryInterpreter._http_transport`(OpenAI chat completions, `response_format json_object`, 고정 seed) 그대로, 파싱도 제품 `_read` 그대로다. 러너가 더하는 것은 지연 측정과 D3 조회뿐이다.
- `AGENTS.md` — 「모델을 부르는 eval은 로컬에서 실제 사용 모델로 실행한다.」 실제 사용 모델 = luna 다. 모델 ID·응답 model 값을 결과 JSON 에 박는다.
- 키·접속: `OPENAI_API_KEY`, `COLAB_DEV_SSH`, `COLAB_DEV_KEY_FILE` 을 프로세스 환경으로 받는다. 값은 출력하지 않는다. 없으면 준비 실패 78.
- 비용: 12문항 × 2회, 입력 약 400 토큰·출력 약 60 토큰. luna 단가($0.20/$1.20 per MTok, ㊷ 기재값)로 **$0.01 미만**.
- legacy 대장·세션·결정번호를 추가하지 않는다(`AGENTS.md`).

## 설계트리
- Q1 제품 코드를 건드리나 → **아니오.** 러너가 `LlmQueryInterpreter` 를 그대로 인스턴스화하고 `transport` 만 감싸 지연을 잰다.
- Q2 골든 12건만 하나, 실무자 조건 14건도 하나 → **골든 12건만.** 14건은 판정 대부분이 자료 메타데이터(후속 2번)에 걸려 `blocked` 라 모델 비교에 값이 없다.
- Q3 dev D3 조회를 하나, 해석 결과만 보나 → **둘 다.** 해석 결과만 보면 「terms 가 그럴싸하다」에서 끝난다. retrieval 까지 가야 골든셋 판정이 선다.
- Q4 Haiku 비교도 같은 회차에 하나 → **아니오.** Ted 가 「gpt로 하자」로 닫았다. 러너의 `--provider anthropic` 경로는 남겨 두되 이 회차엔 쓰지 않는다.

## 미해결 질문
- 로컬 셸·`~/.config/colab-platform` 어디에도 `OPENAI_API_KEY` 가 없다(staging compose 는 `${OPENAI_API_KEY:-}` 로 호스트 환경에서 받는다). `COLAB_DEV_SSH` 값도 셸에 없다. Ted 가 둘을 프로세스 환경으로 넘겨야 실행된다.

## 범위 밖 (명시 제외)
- 제품 config 기본값·`SYSTEM_PROMPT`·`query_interpretation` 변경.
- 결정 ㊷ 재개봉. 이 문서는 수치를 만들고 판단은 Ted 에게 남긴다.
- 프롬프트 튜닝. 제품 프롬프트 그대로만 잰다.

## 확인
- Ted 확인 문장(원문 그대로): 「haiku를 기준으로 검색을 검토해줄수있나?」 · 「Haiku 를 질의 해석 모델로 실측」(선택지 응답) · 「아 미안하다 gpt로 하자」
- 재개봉 금지: 아니오

## 참조
- 결정: `dev-package/PLAN-SoT.md §9-㊷` (모델 공급자 GPT 통일 · 잔여 조건 = K4 실측)
- 해석기: `services/ai-service/src/colab_ai/app/interpret.py` (`SYSTEM_PROMPT` · `LlmQueryInterpreter._read`)
- 골든셋: `eval/k4-search/golden-set.md` · `golden-cases.json` · `golden_baseline.py`
