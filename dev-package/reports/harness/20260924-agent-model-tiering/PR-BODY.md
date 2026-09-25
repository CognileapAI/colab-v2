# 역할별 모델·effort·maxTurns 재설정 · Codex 배정을 Claude 난이도 등급에 맞춘다

base: `develop`(PR #130 병합 뒤) · head: `claude/agent-model-tiering`

## 왜
- Claude 는 일의 난이도로, Codex 는 역할 성격으로 모델을 나눠 순서가 뒤집혀 있었다(가장 단순한 gate-runner 가 Codex 최상위 astra · 가장 어려운 lane-worker 가 sol).
- Claude 기본값이 실사용과 어긋났다: researcher 118건 중 98건을 opus 로 바꿔 불렀고 30턴 한도에 58% 가 걸렸다. advisor 는 12턴에 30%. measurement-lane effort 는 비어 있었다(M1).
- Codex 역할 파일에 effort 가 없어 전역 low 로 돌았고, 역할 배정이 실제로 적용되는지 확인된 적이 없었다(M2).

## 무엇이 바뀌나 (Ted 판정 2026-09-24)
| 역할 | Claude model · effort · maxTurns | Codex model · effort |
|---|---|---|
| advisor | fable · high · **16** | `gpt-6-astra` · high · read-only |
| lane-worker | opus · high · 200 | `gpt-5.6-sol` · high |
| researcher | **opus** · medium · **50** | `gpt-5.6-sol` · medium |
| measurement-lane | sonnet · **low** · 60 | `gpt-5.6-terra` · low |
| gate-runner | haiku · low · 20 | `gpt-5.6-luna` · low |

- 등급 대응(M3 · 가격·포지셔닝 기반 추론): Fable 5.1 = `gpt-6-astra` · Opus 5.5 = `gpt-5.6-sol` · Sonnet 5 = `gpt-5.6-terra` · Haiku 4.5 = `gpt-5.6-luna`. GPT-5.6 안의 순서 Luna < Terra < Sol.
- 이 계정(ChatGPT 로그인)에서 `gpt-6-sol`·`gpt-6-luna` 는 400 으로 선택되지 않는다. 선택 가능 4종으로 등급을 맞췄다.
- spec 의 대체 순서(X2-3)는 measurement-lane·gate-runner 를 `gpt-5.6-sol` 로 두는 것이었다. `gpt-5.6-terra`·`gpt-5.6-luna` 가 선택 가능함을 실측한 뒤 판정 ⑦(「수준에 상응하게」)에 따라 두 역할을 terra·luna 로 좁혔다 — Ted 확인 2026-09-25 "권고대로".
- 규칙: advisor 스폰 때 model 을 넘기지 않는다 · researcher 수집만이면 sonnet 허용 · gate-runner 는 게이트 하나(전수 허용 문장 제거) · lane-worker 는 다른 레인을 기다리며 턴을 쓰지 않는다 · measurement-lane 은 짧은 간격 폴링을 하지 않는다.
- `scripts/agent-bridge.py check` 가 역할 4개만 보던 것(measurement-lane 누락)을 5개로 고쳤다.
- `docs/development/dual-agent.md` 배정 문단을 난이도 기준 표로 바꿨다.

## 검증
- Codex 5역할 스폰 실측: 자식의 마지막 `turn_context` 가 역할 파일의 model·effort 와 5역할 모두 같다(부모는 astra·low). 자식 thread_id·부모 thread_id 는 `X-codex-smoke.md` 「실측 4」.
- 시험: 수정 전 red(레인 5건 · terra·luna 조정 2건) → 수정 후 `test_agent_bridge` OK.
- 게이트(이 브랜치): agent-bridge · harness-contract · harness-contract-selftest · exec-bit · planning-freshness · work-item-consistency 모두 green 1 / 0 / 0.
- advisor ① approve-with-changes(차단급 2 · 개선 4) · advisor ② 두 번(intent · Codex) 모두 반영.

## 원한 결과 대조
1 Claude frontmatter 값 · 빈 값 0 — 충족. 2 역할 1개 실측 — 충족(gate-runner). 3 5역할 toml·시험 — 충족. 4 dual-agent 표 — 충족. 5 역할·스킬 규칙 — 충족. 6 평가 재실행 — **제외**(Ted 2026-09-25 · 아래). 7 대응표·수준 배정 — 충족(M3 · X3). 8 병합 뒤 재측정 — 후속.

## 제외 — Codex 40과제 평가 재실행 (Ted 2026-09-25 "권고대로")
러너 `scripts/codex-harness-eval.py` 는 역할 지정 없이 `codex exec` 를 불러 늘 전역 config(astra)로 돈다. 재실행해도 새 배정을 재지 못한다. 배정 검증은 위 5역할 스폰 실측이 맡았다.

## 미검증
- 새 Claude frontmatter 는 새 세션부터 반영된다. 병합 뒤 한도 도달률 재측정(원한 결과 8)은 후속이다.
