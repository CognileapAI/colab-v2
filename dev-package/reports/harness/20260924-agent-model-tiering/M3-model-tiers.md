# M3 모델 등급 대응표 조사 (Claude ↔ OpenAI/Codex)

- 조회일: 2026-09-24 (모든 출처 동일)
- task_id: 1aea1eec6fe7425f82d24d111968c899 (researcher, read-only)
- 표기: [출처] = 공개 문서 기재, [추론] = 출처 없이 가격·포지셔닝으로 짝지음, 「미확인」 = 확인 못 함

## 0. 핵심 결론 (요지)

1. **astra > sol 확인됨.** OpenAI Codex 모델 문서가 GPT-6 Astra를 "our most capable model", Sol을 "complex coding and agentic workflows"용으로 구분하고, DataCamp는 Astra가 GPT-5.6 Sol의 후속 flagship이라고 쓴다. 가격도 Astra $10/$50, GPT-6 Sol $2/$10, GPT-5.6 Sol $4/$20. → "Ted 확인 · 공개 출처로도 확인".
2. **주의: 현재 Codex의 sol은 `gpt-6-sol`이다.** 2026-09-22 GPT-6 Sol·Luna 출시 후 Codex 모델 문서에 나오는 현행 모델은 GPT-6 Astra / GPT-6 Sol / GPT-6 Luna이다. GPT-5.5는 legacy(2026-10-14 퇴역). `gpt-5.6-sol`(및 Terra·Luna 5.6)은 현재 Codex 모델 문서에 없음. Codex에서 아직 선택할 수 있는지는 「미확인」.
3. 대응표: 1등급 Fable 5.1 ↔ GPT-6 Astra (가격 $10/$50 동일), 2등급 Opus 5.5 ↔ GPT-6 Sol (5.6 Sol과는 가격 $4/$20 동일), 3등급 Sonnet 5 ↔ GPT-6 Sol (가격 $2/$10 동일, effort 한 단계 낮춤), 4등급 Haiku 4.5 ↔ GPT-6 Luna. 벤더 간 등가를 명시한 공식 문장은 없다. 짝은 모두 [추론]이고 근거는 가격·포지셔닝·일부 벤치마크다.

## 1. 모델별 사실

### 1-1. OpenAI (Codex에서 쓸 수 있는 모델)

| 모델 | 포지셔닝 | 용도 (벤더 문구) | reasoning effort | API 가격 입력/출력 ($/1M) | 출시일 | 출처 |
|---|---|---|---|---|---|---|
| `gpt-6-astra` | flagship (최상위) | "our most capable model, built for the hardest end-to-end work" · 복잡 추론·코딩·computer use·연구 | API: low, medium, high, xhigh, max (none 없음). Codex 앱 표기: Light(CLI low), Medium, High, Extra High, Max, Ultra | $10 / $50 (cached $1), Fast mode 약 2배 | 2026-09-03 전후 (DataCamp·9to5Mac 2026-09-04 보도). OpenAI 원문 403으로 정확한 날짜는 「미확인」 | https://developers.openai.com/api/docs/models/gpt-6-astra ; https://learn.chatgpt.com/docs/models ; https://www.datacamp.com/blog/gpt-6-astra ; https://9to5mac.com/2026/09/04/openai-releasing-major-upgrade-to-chatgpt-and-codex-with-gpt-6-astra-details-here/ |
| `gpt-6-sol` | 중상위 (Astra 아래, 현행 Codex 기본 계열) | "Built for complex coding and agentic workflows" · Codex: "ambiguous, difficult, or high-value tasks" | none, low, medium(기본), high, xhigh, max. Codex 앱 표기에 Ultra 추가 | $2 / $10 (cached $0.2) | 2026-09-22 | https://developers.openai.com/api/docs/models/gpt-6-sol ; https://learn.chatgpt.com/docs/models ; https://thenewstack.io/openai-gpt-6-sol-luna-release/ |
| `gpt-6-luna` | 소형·저가 | "most efficient model for focused, high-volume tasks" · 요약·추출·분류·범위가 좁은 코딩 | none, low, medium(API 기본), high, xhigh, max (Ultra 없음). Codex 문서의 기본값은 High. API 문서의 기본값 medium과 다름 | $0.10 / $0.50 (cached $0.01) | 2026-09-22 | https://developers.openai.com/api/docs/models/gpt-6-luna ; https://learn.chatgpt.com/docs/models ; https://thenewstack.io/openai-gpt-6-sol-luna-release/ |
| `gpt-5.6-sol` | 이전 세대 flagship (Astra 이전 최상위) | "Flagship model for complex professional work" · GPT-5.6 계열은 Luna < Terra < Sol | none, low, medium(기본), high, xhigh, max | $4 / $20 (cached $0.4). 검색 스니펫의 $2/$10은 모델 페이지와 달라 채택하지 않음 | 2026-07-09 (프리뷰 2026-06-26) | https://developers.openai.com/api/docs/models/gpt-5.6-sol ; https://en.wikipedia.org/wiki/GPT-5.6 |
| `gpt-5.6-terra` / `gpt-5.6-luna` | 5.6 계열의 중간 / 소형 | Terra "competitive with GPT-5.5 at half the cost", Luna "fastest, budget" | 「미확인」 | Terra 「미확인」 · 5.6 Luna $0.20/$1.20 (New Stack 비교 문장) | 2026-07-09 | https://en.wikipedia.org/wiki/GPT-5.6 ; https://thenewstack.io/openai-gpt-6-sol-luna-release/ ; https://codex.danielvaughan.com/2026/09/03/gpt-6-astra-codex-cli-configuration-context-notes-safety/ |
| `gpt-5.5` | legacy flagship | "flagship model for the most complex professional work" (출시 당시 문구) · Codex에서 2026-10-14 퇴역 예정 | none, low, medium(기본), high, xhigh | $5 / $30 | 스냅샷 2026-04-23 | https://developers.openai.com/api/docs/models/gpt-5.5 ; https://learn.chatgpt.com/docs/models |
| `gpt-5.4-mini` | 과거 소형 | 2026-08-31 퇴역 | — | — | — | https://learn.chatgpt.com/docs/models |

Astra > Sol 근거 (조회일 2026-09-24):
- OpenAI Codex 문서: Astra는 "the hardest end-to-end work", Sol은 "ambiguous, difficult, or high-value tasks", Luna는 "specific, high-volume tasks"에 쓰라고 구분 — https://learn.chatgpt.com/docs/models
- DataCamp: Astra가 GPT-5.6 Sol의 뒤를 잇는 "new frontier flagship". OSWorld 2.0에서 72.6% vs 65.7%, FrontierMath Tier 4에서 97.6% vs 83.0% — https://www.datacamp.com/blog/gpt-6-astra
- Kingy AI: 공개 벤치마크 5종 모두 GPT-6 Astra > GPT-6 Sol. AutomationBench 41.4 vs 33.2, OSWorld 2.0 73.5 vs 64.4 — https://kingy.ai/blog/gpt-6-sol-luna-specs-benchmarks-pricing-comparison/
- 판정: **Ted 확인 · 공개 출처로도 확인**

### 1-2. Anthropic

| 모델 | 포지셔닝 | 용도 (벤더 문구) | effort | API 가격 입력/출력 ($/MTok) | 출시일 | 출처 |
|---|---|---|---|---|---|---|
| Claude Fable 5.1 (`claude-fable-5-1`) | 최상위 (Mythos급, Opus 위) | "For demanding reasoning and long-horizon agentic work". 지연은 Slower | low, medium, high(기본), xhigh, max | $10 / $50 | 2026-09-01 (DataCamp 기재. 퇴역 약정 "not sooner than 2027-09-01"과 정합) | https://platform.claude.com/docs/en/about-claude/models/overview ; https://platform.claude.com/docs/en/build-with-claude/effort ; https://www.datacamp.com/blog/gpt-6-astra |
| Claude Opus 5.5 (`claude-opus-5-5`) | 상위 (권장 시작점) | "For long-running agentic coding and knowledge work". Anthropic은 "start with Opus 5.5 for most workloads"를 권장 | low, medium(기본), high, xhigh, max | $4 / $20 | 2026-09-22 | https://platform.claude.com/docs/en/about-claude/models/overview ; https://platform.claude.com/docs/en/build-with-claude/effort ; https://techcrunch.com/2026/09/22/anthropic-releases-opus-5-5-with-lower-prices-and-fable-level-performance/ |
| Claude Sonnet 5 (`claude-sonnet-5`) | 중간 | "The best combination of speed and intelligence". Opus 4.8에 근접 | low, medium, high(기본), xhigh, max | $2 / $10 | 2026-06-30 | https://platform.claude.com/docs/en/about-claude/models/overview ; https://www.anthropic.com/news/claude-sonnet-5 |
| Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) | 소형 | "The fastest model with near-frontier intelligence" | effort 미지원 (extended thinking만) | $1 / $5 | 2025-10 (ID 20251001 기준. 정확한 공개일 「미확인」) | https://platform.claude.com/docs/en/about-claude/models/overview |

참고: TechCrunch는 Opus 5.5가 "outpaces the larger Fable model in many benchmarks"라고 보도했다. Anthropic 문서는 Fable 5.1을 계속 상위 등급("demanding reasoning… or when your evals on Opus 5.5 at higher effort still fall short")으로 둔다 — https://techcrunch.com/2026/09/22/anthropic-releases-opus-5-5-with-lower-prices-and-fable-level-performance/ ; https://platform.claude.com/docs/en/about-claude/models/overview

## 2. 등급 대응표 (1 = 최상위)

| 등급 | Claude | OpenAI/Codex | 짝지은 근거 | 성격 |
|---|---|---|---|---|
| 1 | Fable 5.1 ($10/$50) | `gpt-6-astra` ($10/$50) | 가격 완전 동일. 두 모델 모두 벤더 최상위이며 "hardest / long-horizon" 포지셔닝. 벤치마크: FrontierMath T4 Astra 97.6 vs Fable 87.8 (DataCamp). Kingy 표에서는 DeepSWE Astra 74.1 vs Fable 69.9, FrontierCode 53.3 vs 50.9 | [추론] (등가를 말한 벤더 문장 없음) |
| 2 | Opus 5.5 ($4/$20) | `gpt-6-sol` (현행 권장) · `gpt-5.6-sol` ($4/$20, 가격 동일하나 현행 Codex 목록에 없음) | 포지셔닝: 두 모델 모두 "기본으로 쓰는 고성능 agentic coding" 모델. 벤치마크: Opus 5.5가 GPT-6 Sol보다 높음 (AutomationBench 40.0 vs 33.2, FrontierCode 54.4 vs 49.3). FrontierCode는 Astra 53.3보다도 높음 (Kingy) | [추론]. 성능은 Opus 5.5 ≥ GPT-6 Sol이므로 같은 등급에 두면 Codex 쪽이 약간 낮을 수 있음 |
| 3 | Sonnet 5 ($2/$10) | `gpt-6-sol` (effort 한 단계 낮춤) | 가격 완전 동일 ($2/$10). GPT-5.6 Terra("GPT-5.5와 경쟁, 반값")가 중간 등급 짝 후보이나 현행 Codex 목록에 없고 가격 「미확인」 | [추론]. Sonnet 5와 GPT-6 Sol을 직접 비교한 벤치마크는 「미확인」 |
| 4 | Haiku 4.5 ($1/$5) | `gpt-6-luna` ($0.10/$0.50) | 포지셔닝 일치 (fastest / most efficient, high-volume). 가격은 Luna가 1/10 | [추론]. 직접 비교 벤치마크는 「미확인」. Luna 공개 점수(DeepSWE 66.6 등)로 보아 Haiku 4.5보다 낮지 않을 가능성이 크나 확인되지 않음 |

Codex에 Haiku급 전용 모델이 따로 있는가: 현행 Codex 목록에서 가장 작은 모델은 GPT-6 Luna이다. mini/nano는 퇴역했다 (gpt-5.4-mini, 2026-08-31). 따라서 4등급 짝은 Luna이다 — https://learn.chatgpt.com/docs/models

## 3. CoLAB 역할별 Codex 배정 (Ted 결정 Claude 설정 → Codex)

| 역할 | Claude 설정 (Ted 결정) | Codex 모델 · reasoning effort | 근거 | 성격 |
|---|---|---|---|---|
| advisor | fable · high | `gpt-6-astra` · high | 1등급 짝. Fable 기본 effort가 high이고, Astra도 Codex CLI 해설이 "high is a reasonable default" | [추론] + 출처 (https://codex.danielvaughan.com/2026/09/03/gpt-6-astra-codex-cli-configuration-context-notes-safety/ ; https://platform.claude.com/docs/en/build-with-claude/effort) |
| lane-worker | opus · high | `gpt-6-sol` · high | 2등급 짝. effort 그대로 유지. Opus 5.5가 Sol보다 벤치마크가 높으므로, 레인 품질이 모자라면 xhigh로 먼저 올리고 그다음 astra · medium을 검토 | [추론] |
| researcher | opus · medium | `gpt-6-sol` · medium | 2등급 짝. medium은 Opus 5.5와 GPT-6 Sol 모두의 기본값 | [추론] + 출처 (https://developers.openai.com/api/docs/models/gpt-6-sol) |
| measurement-lane | sonnet · low | `gpt-6-sol` · low | 3등급 짝 (가격 동일). 게이트를 재기만 하는 기계적 역할이라 `gpt-6-luna` · medium으로 낮춰도 되는지는 실측 전 「미확인」 | [추론] |
| gate-runner | haiku · low | `gpt-6-luna` · low | 4등급 짝이며 Codex 최소 모델. Haiku 4.5는 effort를 지원하지 않으므로 Claude 쪽 low는 명목값. Luna는 Codex 기본이 High이므로 low를 명시해야 함 | [추론] + 출처 (https://learn.chatgpt.com/docs/models) |

적용 시 주의:
- effort 값 이름: API·CLI 값은 `low|medium|high|xhigh|max`이다. Codex 앱의 "Ultra"에 대응하는 CLI 값은 「미확인」. Astra는 `none`을 지원하지 않는다.
- `gpt-5.5`는 2026-10-14 퇴역 예정이므로 배정하지 않는다. `gpt-5.6-sol`은 현행 Codex 문서에 없고 GPT-6 Sol보다 가격이 2배이므로 `gpt-6-sol`로 대체할 것을 권장 [추론]. Codex에서 아직 쓸 수 있는지는 「미확인」.
- 모든 짝은 가격·포지셔닝 기반 추론이다. 모델 호출 eval은 AGENTS.md 규칙대로 실제 사용 모델로 로컬에서 따로 실행해야 한다.
- OpenAI 1차 페이지 중 openai.com/index/* 와 help.openai.com 은 WebFetch 403으로 본문을 읽지 못했다. 해당 사실은 developers.openai.com·learn.chatgpt.com 및 2차 출처로 대신 확인했다.
