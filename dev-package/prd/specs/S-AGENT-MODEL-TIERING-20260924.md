# Spec: 역할별 모델·effort·maxTurns 재설정과 Codex 배정 정렬
출처 intent: `dev-package/intent/2026-09-24-agent-model-tiering.md` (승인 2026-09-24 · 「판정」 절 Ted 원문).
근거: `dev-package/reports/harness/20260924-agent-model-tiering/`(M1 실사용 · M2 Codex 설정 · M3 GPT·Claude 등급 대응 · S 세션 관측). advisor ① 2026-09-24 approve-with-changes — 차단급 2 · 개선 4 반영.
선행: PR #130(`claude/harness-consolidation`). 이 브랜치는 그 위에 쌓였다. PR 은 #130 병합 뒤 연다(판정 ⑧).

## 문제 진술
- Claude 역할 기본값이 실사용과 어긋난다(researcher opus 로 바꿔 부름 98/118 · 한도 도달 58% · advisor 30%). measurement-lane effort 가 비어 있다.
- Codex 는 역할 성격 기준 배정이라 Claude 난이도 순서와 뒤집혔고, 역할 파일에 effort 가 없으며(전역 low), 현행 Codex 문서에 없는 `gpt-5.6-sol` 을 쓴다(M3). 역할 배정이 실제로 적용되는지 실측이 없다(M2 · 2026-09-09 probe `unavailable`).

## 구현 결정
### C1 Claude frontmatter (오케스트레이터 직접 · 5파일 수치)
| 역할 | model | effort | maxTurns | 바뀜 |
|---|---|---|---|---|
| researcher | **opus** | medium | **50** | sonnet→opus · 30→50 (판정 ①②) |
| lane-worker | opus | high | 200 | 없음 |
| advisor | fable | high | **16** | 12→16 (판정 ③) |
| measurement-lane | sonnet | **low** | 60 | effort 명시 (판정 ⑤) |
| gate-runner | haiku | low | 20 | 없음 — Haiku 4.5 는 effort 미지원이라 명목값(M3) |

### C2 행동 규칙 (오케스트레이터 직접 · 역할 본문·스킬 한두 줄씩)
- `.agents/roles/advisor.md` 규칙: 「한도는 12턴이다」 → 16턴. 「도구 호출 8회 이하 뒤 판정」은 유지.
- `.agents/roles/lane-worker.md`: 「다른 레인을 기다리며 턴을 쓰지 않는다. 게이트 대기는 호스트 뮤텍스가 한다. 기다려야 하면 green 상태로 커밋하고 인계한다」.
- `.agents/roles/gate-runner.md`: 「게이트 하나만 돌린다. 여러 게이트·전수는 measurement-lane 이다」.
- `.agents/roles/measurement-lane.md`: 「게이트 실행 중 짧은 간격으로 상태를 묻지 않는다. 백그라운드로 돌리고 완료를 기다린다」.
- `.agents/skills/colab-v2-work/SKILL.md` §1: 「advisor 는 스폰 때 model 을 넘기지 않는다(frontmatter fable · Fable 은 Opus 5.5 보다 상위 — Ted 2026-09-24)」 · 「gate-runner 에 게이트 여러 개를 맡기지 않는다」.
- `.agents/skills/colab-v2-work/SKILL.md` §1 한 줄 더: 「researcher 기본은 opus. 계수·추출·목록만인 조사는 스폰 때 `model: sonnet` 을 넘길 수 있다(전역 규칙 「기계적 작업 sonnet」)」.
- 복제 문장: `.agents/skills/design-review/SKILL.md` 「모델 = `researcher`(sonnet)」 → 「`researcher`(기본 opus)」. `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` 는 날짜 박힌 설계 이력이라 고치지 않는다. `.agents/rules/colab-rules.md` §1-3 은 researcher 모델을 적지 않아 충돌 없음(그 절이 가리키는 `model-roles-fable-advisor.md` 부재는 기존 결함 · 범위 밖).

### X1 Codex 등급 대응 (M3 · 출처는 가격·포지셔닝 · 공식 동급 선언 없음 = 추론)
| 등급 | Claude | Codex |
|---|---|---|
| 1 | Fable 5.1 | `gpt-6-astra` |
| 2 | Opus 5.5 | `gpt-6-sol` |
| 3 | Sonnet 5 | `gpt-6-sol` · Claude effort 그대로 |
| 4 | Haiku 4.5 | `gpt-6-luna` |

| 역할 | Claude (C1) | Codex model · `model_reasoning_effort` |
|---|---|---|
| advisor | fable · high | `gpt-6-astra` · high · read-only 유지 |
| lane-worker | opus · high | `gpt-6-sol` · high |
| researcher | opus · medium | `gpt-6-sol` · medium |
| measurement-lane | sonnet · low | `gpt-6-sol` · low |
| gate-runner | haiku · low | `gpt-6-luna` · low (Luna 기본은 high 라 명시 필수 · M3) |

### X2 Codex 적용 순서 (레인 · 실측 먼저)
1. **실측 1**: 이 호스트 Codex CLI(0.154.0)와 계정에서 `gpt-6-astra`·`gpt-6-sol`·`gpt-6-luna`·`gpt-5.6-sol` 4종이 선택되는지 `codex exec -m <model>` 최소 호출로 확인한다(모델당 1회 · 응답의 모델 식별자 기록).
2. **실측 2**: `gate-runner.toml` 하나에 `model = "gpt-6-luna"` · `model_reasoning_effort = "low"` 를 넣고 Codex 에서 그 역할을 스폰해 ⑴ 역할이 로드되는지(모르는 키 거부 여부) ⑵ `turn_context` 의 model·effort 가 파일 값과 같은지 기록한다. named agent 스폰 수단이 없으면(2026-09-09 probe 와 같음) 그 사실과 시도한 명령을 기록하고 `codex exec -c model_reasoning_effort=low` 로 키 수용만 확인한다 — 이 경우 「역할 배정 적용」은 미검증으로 적는다.
3. 실측 1·2 결과대로 5개 toml 을 X1 표로 고친다. 선택 불가 대체 순서: luna 불가 → `gpt-6-sol`·low · `gpt-6-sol` 불가 → 실측 1 에서 선택된 `gpt-5.6-sol` · 그것도 불가 → `gpt-6-astra`·low. 사유를 적는다. effort 키가 거부되면 effort 는 넣지 않는다. **가드**: 5파일 수정 뒤 각 toml 의 `model` 값으로 `codex exec -m <값>` 최소 호출을 한 번씩 해 5역할 모델명이 실측 1 통과 집합 안에 있음을 `X-codex-smoke.md` 에 5행으로 기록한다.
4. `scripts/tests/test_agent_bridge.py` `test_role_models_are_explicit_and_do_not_claim_parent_inheritance` 의 `expected` 를 5역할(measurement-lane 포함)로 넓히고 effort 를 넣었으면 effort 도 단언한다. `expected` 의 모델 값이 실측 1 통과 집합의 부분집합임도 단언한다(집합은 시험 안 상수 · 출처 X-codex-smoke.md). 수정 전 red(새 값 불일치)를 보인다.
5. `docs/development/dual-agent.md` 「`.codex/agents/*.toml`에 `model`이 지정된 역할」 문단을 난이도 기준 문장 + X1 역할 표로 바꾼다. 표 아래 한 줄: 「lane-worker 품질 미달 시 `gpt-6-sol`·xhigh → `gpt-6-astra`·medium 순으로 올린다(M3 §3 · Opus 5.5 가 GPT-6 Sol 보다 벤치마크가 높다)」. `dev-package/prd/rounds/R-CODEX-PARITY.md` 머리에 「2026-09-24 배정 변경 — 이 문서의 모델명은 2026-09-09 기준」 한 줄.
6. **평가 재실행(판정 ⑧) — 보류 · Ted 재확인**: advisor ① 확인 결과 40과제 러너 `scripts/codex-harness-eval.py` 는 `-m`·역할 지정 없이 `codex exec` 를 불러 늘 전역 config(astra) 로 돈다(2026-09-09 결과 `models: ["gpt-6-astra"]`). 역할 toml 을 읽지 않으므로 재실행해도 새 배정을 재지 못하고 2026-09-09 와 같은 조건(최대 약 2시간)을 반복한다. 판정 ⑧의 전제(평가가 배정을 검증한다)가 달라져 Ted 에게 다시 묻는다. 실행하기로 하면 레인이 아니라 병합 뒤 오케스트레이터가 배경 1회 돌리고 결과 표제를 「부모 모델(전역 config) 회귀 확인 · 배정 검증 아님」으로 고정한다. 역할 배정의 실제 검증은 실측 2(역할 스폰)가 맡는다.

### X3 실측 뒤 조정 (2026-09-25 · 오케스트레이터)
- 이 계정(ChatGPT 로그인)에서 `gpt-6-sol`·`gpt-6-luna` 는 선택 불가(400). 선택 가능 = `gpt-6-astra`·`gpt-5.6-sol`·`gpt-5.6-terra`·`gpt-5.6-luna`(X-codex-smoke 실측 1·3).
- GPT-5.6 안의 순서 Luna < Terra < Sol(M3 22행)로 판정 ⑦을 적용해 **measurement-lane = `gpt-5.6-terra`·low · gate-runner = `gpt-5.6-luna`·low** 로 좁혔다. X2-3 대체 순서는 두 모델의 선택 가능 여부를 모를 때 쓴 것이다.
- 5역할 스폰 실측(실측 4)에서 자식 마지막 `turn_context` 가 역할 파일 값과 모두 같다 — 원한 결과 2·3 충족.
- 상향 경로는 `gpt-5.6-sol`·xhigh → `gpt-6-astra`·medium.
- `scripts/agent-bridge.py check` 가 역할 4개만 검사하던 것(measurement-lane 누락 · 「4 role mappings」 고정 문구)을 5개로 고쳤다.

## 시험 결정
- C1: `grep -E '^(model|effort|maxTurns):' .claude/agents/*.md` 가 위 표와 같다 · 빈 effort 0.
- X2: 실측 1·2 증거 파일(`dev-package/reports/harness/20260924-agent-model-tiering/X-codex-smoke.md`) · 시험 수정 전 red → 후 green · 평가 결과 파일.
- 게이트: `agent-bridge` · `harness-contract` · `harness-contract-selftest` · `exec-bit` · `planning-freshness` · `work-item-consistency`.

## 범위 밖
- `~/.codex/config.toml`(사용자 전역 · 현재 astra·low) 변경 · 새 역할 · 도구 목록 · Claude 평가(`eval/harness/run.sh`) 재실행 · 제품 코드.

## 산출 계획
- C1·C2 = 오케스트레이터 직접(수치·문장 몇 줄).
- X2 = 레인 1건(`lane-worker` · 격리 워크트리 · 기준 `origin/claude/agent-model-tiering`) · 파일 계열 2개(Codex 설정·시험 / 문서) + 실측 1·2 + 가드. 레인은 1~5 와 게이트 green 커밋으로 끝난다. 평가 재실행(6)은 레인 밖.
- 병합 뒤 재측정(원한 결과 8)은 후속 기록.
