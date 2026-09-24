# Intent: 역할별 모델·effort·maxTurns 재검토와 Codex 배정 정렬 (승인 2026-09-24)
메타 — 발의자: Ted · 작성 2026-09-24 · 승인: **Ted 2026-09-24 — 「판정」 절 참조**
- Ted 원문 1: "gpt가 클로드와 유사한 모델로 세팅되어있어야 하는데 좀 뒤죽박죽인데 어떻게 생각해? claude로 하이쿠 low돌리는데, gpt는 astra로 돌리잖아" (2026-09-24)
- Ted 원문 2: "1. 리서처 뿐만아니라 각 역할에 적절한 모데로가 이포트 등 여기 있는 기준을 다시 재검토 하고 2. 코덱스 권고도 같이 개선하자. 이내용 인텐트로 같이 질의해보자" (2026-09-24)
- 근거 폴더: `dev-package/reports/harness/20260924-agent-model-tiering/`(M1 역할별 실사용 · M2 Codex 사실 · S 이 세션 관측) · `dev-package/reports/harness/20260924-lane-hygiene-review/A2-turn-cuts.md`

## 문제
- **Claude 와 Codex 가 다른 기준으로 모델을 나눴다.** Claude 는 일의 난이도(`.claude/agents/*.md`), Codex 는 역할 성격(`docs/development/dual-agent.md` 「실행·지원 = gpt-5.6-sol · 검증·검토 = gpt-6-astra」). 그래서 가장 단순한 gate-runner(Claude haiku·low)와 measurement-lane 이 Codex 에서 astra 를 쓰고, 가장 어려운 lane-worker(Claude opus·high)가 sol 을 쓴다.
- **Codex 역할 파일에 추론 강도가 없다.** 사용자 전역 `~/.codex/config.toml` 이 `model = "gpt-6-astra"` · `model_reasoning_effort = "low"` 다(M2). 역할 파일이 덮지 않으면 lane-worker·advisor 도 low 로 돌 수 있다. 서브에이전트의 실효 기본은 `features.multi_agent_v2.default_subagent_reasoning_effort`(M2)일 수도 있으며 값은 미측정이다.
- **Codex 역할 배정이 실제로 적용되는지 확인된 적이 없다.** 2026-09-09 `role-model-activation-probe` 는 `status: unavailable` · `spawned_roles: []` 였다(M2). Codex 에는 maxTurns 대응 키도 없다(M2).
- **Claude 기본값이 실사용과 어긋난다**(M1 · 2026-09-10 이후 · 중복 65건 제거):

| 역할 | 설정 | 실행 수 | 기본 모델이 바뀐 호출 | 턴 p90 / max | 한도 도달 |
|---|---|---|---|---|---|
| researcher | sonnet · medium · 30 | 118 | opus 로 98 | 49.8 / 128 | 68 (58%) |
| lane-worker | opus · high · 200 | 102 | 0 | 222.8 / 800 | 14 (14%) |
| advisor | fable · high · 12 | 73 | opus 로 20 | 13.8 / 23 | 22 (30%) |
| gate-runner | haiku · low · 20 | 18 | 0 | 30.6 / 84 | 4 (22%) |
| measurement-lane | sonnet · **(effort 없음)** · 60 | 5 | 0 | 62.4 / 64 | 2 (40%) |

  턴 수는 재개 구간을 합친 값이다. 「한도 도달」은 「한 번 이상 절단된 실행」의 근사다(M1 주).
- measurement-lane 의 effort 는 비어 있고, 빈 값의 동작은 Claude Code 문서에 없다(S §2).

## 판정 (Ted 2026-09-24 · 원문 그대로)
- "1. 리서처 모델은 opus 로 바꾼다. 2. b로 올리고 측정한다. 3. 어드바이저는 b로 올린다. (fable이 opus 위 등급이 맞다, opus 5.5 도 나왔지만 그럼에도 fable이 위다) 4. 권고대로 한다. 5. 해당 추론강도로 턴한도 60 두고 재자. 6. astra가 sol보다 상위 모델이 맞다. (검색해서 정리해서 기록) 7. 코덱스 배정은 난이도 순서로 맞춘다. (gpt, claude 난이도에 따른 대응표 확보해서 수준에 상응하게 맞추기) 8. 권고대로" (2026-09-24)
- 정리: ① researcher 기본 모델 opus(ⓑ) ② researcher maxTurns 30 → 50 · 재측정(ⓑ) ③ advisor fable·high 유지 · maxTurns 12 → 16 · 스폰 때 model 을 넘기지 않는다 · fable 은 opus 5.5 보다 상위(Ted 확인) ④ lane-worker·gate-runner 설정 유지 + 행동 규칙(ⓐ) ⑤ measurement-lane effort low · maxTurns 60 · 재측정(ⓐ) ⑥ astra > sol(Ted 확인) · 공개 출처를 조사해 기록 ⑦ Codex 배정 = GPT·Claude 난이도 대응표로 수준에 맞춘다 ⑧ #130 병합 뒤 별도 PR · 평가 재실행 포함(ⓐ).

## 원한 결과 (proposed outcome)
1. Claude 역할 5개 frontmatter 에 `model`·`effort`·`maxTurns` 가 모두 적혀 있고 판정 ①②③⑤ 값과 같다(빈 값 0 · grep 으로 잰다): researcher opus·medium·50 · lane-worker opus·high·200 · advisor fable·high·16 · measurement-lane sonnet·low·60 · gate-runner haiku·low·20.
2. 역할 1개(gate-runner)에 `model_reasoning_effort` 를 넣고 Codex 에서 스폰해, 역할이 로드되는지(모르는 키 거부 여부)와 `turn_context` 의 model·effort 가 바뀌는지 먼저 증거 파일로 남긴다. 스폰이 안 되면 그 사실과 대체 경로를 남긴다(성공으로 적지 않는다).
3. 2 가 통과했을 때만 역할 5개 `.codex/agents/*.toml` 에 `model`·`model_reasoning_effort` 를 적고 배정 순서를 Claude 의 난이도 순서에 맞춘다. `scripts/tests/test_agent_bridge.py` 가 5역할(measurement-lane 포함)의 model·effort 를 단언한다. 2 가 실패하면 effort 키는 넣지 않고 model 만 바꾼다.
4. `docs/development/dual-agent.md` 의 배정 문단이 난이도 기준과 표로 바뀐다.
5. `.agents/skills/colab-v2-work/SKILL.md` 와 역할 본문에 판정 ③④⑤의 규칙이 있다 — advisor 스폰 때 model 을 넘기지 않는다 · lane-worker 는 다른 레인을 기다리며 턴을 쓰지 않는다 · gate-runner 는 게이트 하나 · measurement-lane 은 짧은 간격 폴링을 하지 않는다.
6. 모델 호출 평가(`harness-eval`)를 바뀐 Codex 배정으로 다시 돌린 결과가 있다(AGENTS.md 「실제 사용 모델로」 · 구독 사용). named agent 스폰이 안 되면 이 결과는 역할 배정 검증이 아니라 부모 모델 회귀 확인이며 그렇게 적는다.
7. GPT·Claude 난이도 대응표(출처 URL · 조회일)가 근거 폴더에 있고, Codex 역할 5개의 model·effort 가 그 표에서 역할의 Claude 설정과 같은 수준으로 정해진다.
8. 병합 뒤 재측정: researcher·measurement-lane·advisor 의 한도 도달률을 같은 방식(M1)으로 다시 잰 기록을 남긴다(후속 · 병합 조건 아님).

## 영향 범위
- 사용자·화면: 없음. 서비스·스키마·계약: 없음. 계약 파괴: 아니오.
- 하네스: `.claude/agents/*.md`(frontmatter) · `.agents/roles/{measurement-lane,gate-runner,lane-worker}.md`(행동 규칙 한두 줄) · `.agents/skills/colab-v2-work/SKILL.md` · `.codex/agents/*.toml` · `docs/development/dual-agent.md` · `scripts/tests/test_agent_bridge.py` · `dev-package/prd/rounds/R-CODEX-PARITY.md`(모델명 서술) · 평가 결과 파일.

## 제약
- frontmatter 변경은 Claude 세션을 새로 열어야 반영된다. Codex 역할 파일은 이 저장소의 Codex 프로젝트 신뢰가 켜져 있어야 로드된다(dual-agent.md).
- Codex 모델의 상하 관계(astra 가 sol 보다 상위)는 어느 파일에도 적혀 있지 않다(M2 「미기재」). 이 intent 는 Ted 의 설명을 전제로 쓴다 — Ted 확인 필요.
- 선행: PR #130(researcher 자동 task 훅 · 역할 규칙)이 먼저 병합된다. 한도 도달 중 종료 훅 반송분(A2)은 #130 이 줄인다.

## 설계트리 — 역할별 검토 (증거 → 권고)
### researcher
- 증거: 기본 sonnet 인데 호출 83%(98/118)를 opus 로 바꿔 불렀다. 한도 30 에 58% 도달. 도달 원인은 먼저 다 읽기(A2 · S 관측 1 — Sonnet 도 같다)와 종료 훅 반송(#130 이 해결). 이 세션에서 증거 수집(계수·추출)은 Sonnet 으로 끝났고, 판단이 드는 intent 문안은 Opus 가 썼다.
- 권고: **기본 sonnet·medium 유지 + 규칙** — 「계수·추출·목록 = 기본(sonnet) · 원인 판단·intent 문안·대안 비교가 드는 조사 = opus 지정」. maxTurns 상향 여부는 질문 2. 58%(최소 1회 절단)는 반송과 무관하므로 「30 은 모자라다」는 확정이다. 그러나 p90 49.8 은 재개 뒤 반송 턴(A2: 26·12턴)을 포함하고, 절단된 실행의 1차 구간은 30 에서 잘려 실제 필요 턴의 상한은 재지 못했다. lane-hygiene intent 의 「상향 보류」를 뒤집을 값은 #130 병합 뒤 1차 구간만으로 다시 잰다.
- 대안: 기본을 opus 로(실사용과 일치 · 수집 과제까지 비싸진다).
### lane-worker
- 증거: 102건 · 기본값 그대로 · 한도 도달 14%. 원인은 범위 과대(P2a·P2b)와 형제 레인 대기로 턴 소모(800턴 1건).
- 권고: **opus·high·200 유지 + 규칙** — 「다른 레인을 기다리며 턴을 쓰지 않는다. 게이트 대기는 호스트 뮤텍스가 한다. 기다려야 하면 green 상태로 커밋하고 인계한다」. 범위는 #130 의 「레인 1건 = 계열 2~3개」.
### advisor
- 증거: 73건 중 20건을 frontmatter(fable) 대신 opus 로 불렀다. 저장소 문서(`.agents/rules/colab-rules.md` 1-3 「advisor=fable」)에는 두 모델의 상하가 없다. Anthropic 모델 안내에는 Fable 5.1 이 Opus 위 등급으로 적혀 있다(이 세션 시스템 정보 · 저장소 밖 근거). 한도 12 에 30% 도달. 「도구 8회 이하 뒤 판정」 문구가 들어간 뒤 이 세션 advisor 4건은 7~9회로 끝났다.
- 권고: **fable·high·12 유지 · 스폰 때 model 을 넘기지 않는다**(규칙 · colab-rules 1-3 advisor=fable). 판정 규율은 #130 이 역할 본문에 넣었다.
### measurement-lane
- 증거: 5건 · effort 없음 · 60 에 2건 도달(이 세션 1건 = 전수 72게이트 뒤 전 로그 검사까지 마치고 60턴 · M1 ab1cf59 · 다른 1건 a19e918 은 `lifecycle begin` 인자 파싱 문제 우회). 표본 5라 한도 값을 정할 자료는 아니다. 일은 「한 번 돌리고 값을 옮긴다」.
- 권고: **sonnet 유지 · effort low 명시**. maxTurns 는 60 유지하고 도달을 재측정한다. 규칙 「게이트 실행 중 짧은 간격으로 상태를 묻지 않는다 — 백그라운드 실행 뒤 완료를 기다린다」는 폴링 실측 없이 예방으로 둔다.
### gate-runner
- 증거: 18건 · 중앙값 9턴 · 도달 4건은 게이트 여러 개를 한 번에 맡긴 경우(63게이트 등)와 모니터 처리.
- 권고: **haiku·low·20 유지 · 규칙** 「게이트 하나만. 전수·여러 게이트는 measurement-lane」 — 스킬 체크리스트.
### Codex 배정 (Claude 난이도 순서에 맞춘다)
(전제: astra 가 sol 보다 상위 · 질문 6 미확인. 뒤집히면 model 열의 astra·sol 을 맞바꾼다.)


| 역할 | Claude | Codex 지금 | Codex 권고 model · effort |
|---|---|---|---|
| lane-worker | opus · high | sol · (없음) | astra · high |
| advisor | fable · high | astra · (없음) · read-only | astra · high · read-only 유지 |
| researcher | sonnet · medium | sol · (없음) | sol · medium |
| measurement-lane | sonnet · low(권고) | astra · (없음) | sol · low |
| gate-runner | haiku · low | astra · (없음) | sol · low (더 가벼운 Codex 모델이 확인되면 그것) |

- maxTurns: Codex 대응 키 없음 → 역할 파일 `developer_instructions` 에 도구 호출 예산 문장을 둔다(advisor 「8회 뒤 판정」 등). 전역 `job_max_runtime_seconds` 는 역할별이 아니라 쓰지 않는다.
- 역할 파일이 `model_reasoning_effort` 를 실제로 받는지는 원한 결과 3 의 스폰 실측으로 판정한다.

## 미해결 질문 (Ted 판정 · 2026-09-24 닫힘 — 「판정」 절)
1. researcher: 기본 sonnet 유지 + 「판단·문안 조사는 opus」 규칙 ⓐ(권고) / 기본을 opus 로 ⓑ.
2. researcher maxTurns: #130 병합 뒤 1차 구간만으로 다시 재서 정한다 ⓐ(권고) / 지금 50 으로 ⓑ(p90 근거는 반송 턴 포함).
3. advisor: fable·high·12 유지 · 스폰 때 model 을 넘기지 않는다 ⓐ(권고) / 한도 12 → 16 도 함께 ⓑ. 함께 확인: fable 과 opus 의 상하(저장소 문서에는 없음).
4. lane-worker · gate-runner: 설정 유지 + 행동 규칙(레인 대기 금지 · 게이트 하나만) ⓐ(권고).
5. measurement-lane: effort low 명시 · maxTurns 60 유지 · 폴링 금지 규칙 · 도달 재측정 ⓐ(권고) / maxTurns 100 도 함께 ⓑ.
6. 전제 확인: Codex 에서 gpt-6-astra 가 gpt-5.6-sol 보다 상위 모델이 맞는가. 더 가벼운 Codex 모델(gate-runner 용)이 있는가.
7. Codex: 역할 1개 실측 → 통과 시 위 표대로 난이도 기준 정렬 + 역할별 effort ⓐ(권고) / 모델은 두고 effort 만 ⓑ.
8. 진행: #130 병합 뒤 별도 PR · 평가 재실행 포함 ⓐ(권고).

## 범위 밖 (명시 제외)
- 새 역할 신설 · 역할 통폐합 · 도구 허용 목록 변경 · Claude 사용자 전역 설정 · `~/.codex/config.toml`(사용자 전역) 변경 · 제품 코드.

## 확인
- Ted 확인 문장(원문 그대로): 위 「판정」 절.
- 재개봉 금지: 예(잔여 결함은 새 intent).

## 참조
- 설정: `.claude/agents/*.md` · `.codex/agents/*.toml` · `docs/development/dual-agent.md` 「`.codex/agents/*.toml`에 `model`이 지정된 역할」 문단 · `AGENTS.md` 「모델을 부르는 eval」 문장
- 시험: `scripts/tests/test_agent_bridge.py` `test_role_models_are_explicit_and_do_not_claim_parent_inheritance`
- 선행 intent: `dev-package/intent/2026-09-24-harness-lane-hygiene.md`(① 턴 한도 · 「maxTurns 상향 보류」)
- 사용자 규칙: 전역 CLAUDE.md 「모델은 난이도에 맞춘다: 판단·설계·문안·리뷰 opus / 기계적 작업 sonnet / 최단순 haiku」
