# X — Codex 역할 모델·effort 실측 (spec `S-AGENT-MODEL-TIERING-20260924` X2 1~5)

- 일시: 2026-09-24 KST · 호스트 WSL · `codex --version` → `codex-cli 0.154.0` (`~/.npm-global/bin/codex`)
- 계정: ChatGPT 로그인(구독) · 전역 `~/.codex/config.toml` = `gpt-6-astra` · `model_reasoning_effort = "low"` (변경하지 않음)
- 모든 호출: `--sandbox read-only` · 프롬프트 「Reply with exactly: OK」 또는 스폰 지시 1건 · 파일 수정 지시 없음
- 모델 식별자: `--json` 이벤트에는 모델명이 없어 세션 rollout(`~/.codex/sessions/2026/09/24/rollout-*-<thread_id>.jsonl`)의 `turn_context.payload.model`·`effort` 로 읽었다.

## 실측 1 — 모델 선택 가능 여부 (모델당 1회)

명령: `codex exec -m <model> --sandbox read-only --json "Reply with exactly: OK" < /dev/null` (저장소 워크트리 cwd)

| model | exit | 결과 | `turn_context` model · effort | thread_id |
|---|---|---|---|---|
| `gpt-6-astra` | 0 | `OK` | `gpt-6-astra` · low | `01a0d3e9-b28d-7e33-b9d3-809b542beca5` |
| `gpt-6-sol` | 1 | 400 `The 'gpt-6-sol' model is not supported when using Codex with a ChatGPT account.` (선행 경고 `Model metadata for gpt-6-sol not found`) | — | `01a0d3e9-3a62-7c02-ad4e-e5a7343811bf` |
| `gpt-6-luna` | 1 | 400 `The 'gpt-6-luna' model is not supported when using Codex with a ChatGPT account.` (선행 경고 `Model metadata for gpt-6-luna not found`) | — | `01a0d3e9-4388-7802-ba06-c68195fee7da` |
| `gpt-5.6-sol` | 0 | `OK` | `gpt-5.6-sol` · low | `01a0d3e9-cab2-7d13-8670-4ca7013bf28d` |

- exit 값은 `--ephemeral` 1차 호출 기준이다. 성공 2종은 rollout 을 남기려고 `--ephemeral` 없이 한 번 더 호출해 `turn_context` 를 읽었다(위 thread_id 가 그 2차 호출).
- **선택 가능 집합 = {`gpt-6-astra`, `gpt-5.6-sol`}**(레인 실측 1 시점 · 4후보 기준). `scripts/tests/test_agent_bridge.py` 의 `SELECTABLE_CODEX_MODELS` 가 이 집합이다. **〔2026-09-25 갱신 → 실측 3′·4〕** — terra·luna 추가 실측으로 4종이 됐고 시험 상수도 4종이다.
- 참고 `codex debug models`(CLI 카탈로그) 목록: `gpt-6-astra` · `gpt-reserve`(hide) · `gpt-5.6-sol` · `gpt-5.6-terra` · `gpt-5.6-luna` · `gpt-5.5` · `codex-auto-review`(hide). `gpt-6-sol`·`gpt-6-luna` 는 카탈로그에 없다. `gpt-5.6-sol` 기본 effort 는 low, `gpt-6-astra` 는 medium 이다.

## 실측 2 — 역할 파일 로드와 `turn_context`

named agent 스폰이 비대화형으로 가능했다(2026-09-09 probe `unavailable` 과 다름). 부모는 `codex exec --sandbox read-only --json -` 에 아래 지시를 stdin 으로 넣었다.

> Call spawn_agent exactly once with agent_type set to "gate-runner" and the task message: "Reply with exactly: OK. Do not run any commands and do not edit files." Then call wait_agent until it finishes. Do not run shell commands or edit files yourself. Finally report verbatim: the spawn_agent result or error text, and the child's final answer or error text.

부모의 `spawn_agent` 인자는 `{"agent_type":"gate-runner","task_name":…,"message":…}` 뿐이고 model·effort 를 넘기지 않았다(부모 rollout `function_call` 확인).

| 시도 | `gate-runner.toml` 값 | 부모 exit | 자식 `session_meta` | 자식 `turn_context` model · effort | 결과 |
|---|---|---|---|---|---|
| 2-a (spec 지정) | `gpt-6-luna` · low | 0 | `agent_role = "gate-runner"` · `thread_spawn.depth = 1` | `gpt-6-luna` · low | 자식 400 `gpt-6-luna … not supported` |
| 2-b (effort 구분용 보강) | `gpt-5.6-sol` · medium | 0 | `agent_role = "gate-runner"` · `thread_spawn.depth = 1` | `gpt-5.6-sol` · medium | 자식 응답 `OK.` |

- 부모 `turn_context` 는 두 시도 모두 `gpt-6-astra` · low(전역 값).
- ⑴ 역할 로드: `model_reasoning_effort` 키가 있는 역할 파일이 로드됐고 모르는 키 오류는 없었다.
- ⑵ 적용: 2-a 는 effort 가 전역 low 와 같아 구분이 안 되므로 2-b 로 전역과 다른 값(medium)을 넣었다. 자식 `turn_context` 가 역할 파일 값(`gpt-5.6-sol` · medium)과 같고 부모(`gpt-6-astra` · low)와 다르다.
- **역할 배정 적용 = 검증됨** (gate-runner 역할 1개 · 2-b 기준). 나머지 4역할은 같은 로더 경로를 쓰지만 역할별 스폰은 하지 않았다.
- 2-a·2-b 뒤 `gate-runner.toml` 은 HEAD 로 되돌린 다음 실측 3 값을 적용했다.
- rollout: 2-a 부모 `01a0d3ea-a962-7a93-aceb-fa72f49590ee` · 자식 `01a0d3ea-c024-7361-af2b-ebbf9434e3c6` / 2-b 부모 `01a0d3eb-ca24-7642-baa7-0e34feb24626` · 자식 `01a0d3eb-e4be-7c42-b355-7b1701ccb023`

## 실측 3 — 5개 역할 파일 적용과 가드 (레인 · 2026-09-24) **〔2026-09-25 갱신 → 실측 3′·4〕** — measurement-lane·gate-runner 의 「적용」 값과 가드 2행은 terra·luna 로 바뀌었다

대체 순서(spec X2-3): luna 불가 → `gpt-6-sol`·low · `gpt-6-sol` 불가 → 실측 1 에서 선택된 `gpt-5.6-sol` · 그것도 불가 → `gpt-6-astra`·low. effort 키는 실측 2 에서 수용·적용되어 넣었다.

| 역할 | X1 목표 | 적용 | 사유 |
|---|---|---|---|
| advisor | `gpt-6-astra` · high | `gpt-6-astra` · high · read-only 유지 | 목표 선택 가능 |
| lane-worker | `gpt-6-sol` · high | `gpt-5.6-sol` · high | `gpt-6-sol` 400 → 대체 2단 |
| researcher | `gpt-6-sol` · medium | `gpt-5.6-sol` · medium | `gpt-6-sol` 400 → 대체 2단 |
| measurement-lane | `gpt-6-sol` · low | `gpt-5.6-sol` · low | `gpt-6-sol` 400 → 대체 2단 |
| gate-runner | `gpt-6-luna` · low | `gpt-5.6-sol` · low | `gpt-6-luna` 400 → `gpt-6-sol` 400 → 대체 2단 |

가드: 각 toml 의 `model` 값을 `tomllib` 로 읽어 `codex exec -m <값> --sandbox read-only --json "Reply with exactly: OK"` 1회씩. effort 는 `-m` 만 넘겨 전역 low 로 돌았다(가드는 모델 선택만 확인).

| 역할 | toml `model` | exit | 응답 | `turn_context` model | thread_id |
|---|---|---|---|---|---|
| advisor | `gpt-6-astra` | 0 | `OK` | `gpt-6-astra` | `01a0d3ec-efc6-7f52-b068-35c332e9bc4b` |
| lane-worker | `gpt-5.6-sol` | 0 | `OK` | `gpt-5.6-sol` | `01a0d3ed-0a75-7d50-815a-12f156ff24fb` |
| researcher | `gpt-5.6-sol` | 0 | `OK` | `gpt-5.6-sol` | `01a0d3ed-1efa-7433-b9e9-603ab8d511ab` |
| measurement-lane | `gpt-5.6-sol` | 0 | `OK` | `gpt-5.6-sol` | `01a0d3ed-32f9-7b30-9c5d-e41b23d75805` |
| gate-runner | `gpt-5.6-sol` | 0 | `OK` | `gpt-5.6-sol` | `01a0d3ed-4cce-7263-96a5-8a8e67c2b3cd` |

5역할 모델명이 모두 실측 1 통과 집합 안에 있다.

## 4 — 시험

`python3 -m unittest scripts.tests.test_agent_bridge.AgentConfigurationTests`

- toml 수정 전(시험만 수정): `FAILED (failures=5)` — advisor `None != 'high'` · lane-worker `None != 'high'` · researcher `None != 'medium'` · measurement-lane `'gpt-6-astra' != 'gpt-5.6-sol'` · gate-runner `'gpt-6-astra' != 'gpt-5.6-sol'`
- toml 수정 후: `Ran 1 test … OK`

## 5 — 문서

- `docs/development/dual-agent.md` 모델 문단을 난이도 기준 문장 + X1 역할 표(목표·적용 두 열) + 상향 경로 한 줄로 바꿨다.
- `dev-package/prd/rounds/R-CODEX-PARITY.md` 머리에 「2026-09-24 배정 변경 — 이 문서의 모델명은 2026-09-09 기준」.

## 남은 위험·후속 (레인 시점) **〔2026-09-25 갱신 → 실측 3′·4〕**

- 난이도 순서가 Codex 쪽에서 모델로는 2단(astra / 5.6-sol)만 구분되고 lane-worker·researcher·measurement-lane·gate-runner 는 effort 로만 갈린다. → **해소**: 실측 3′ 로 4단(astra / 5.6-sol / terra / luna).
- 상향 경로 첫 단(`gpt-6-sol`·xhigh)은 현재 계정에서 선택 불가다. 실제 상향은 다음 단(`gpt-6-astra`·medium)부터 가능하다.
- 카탈로그에 `gpt-5.6-luna`·`gpt-5.6-terra` 가 있으나 spec 대체 순서에 없어 쓰지 않았다. gate-runner 를 `gpt-5.6-luna` 로 둘지는 Ted 판정 대상이다(미호출·미실측). → **해소**: 실측 3′·4 에서 선택·적용 확인, 판정 ⑦로 배정(PR 요약에 Ted 확인 요망으로 표시).

## 실측 3′ (오케스트레이터 · 2026-09-25) — GPT-5.6 Terra·Luna

레인 후속(「카탈로그에 `gpt-5.6-luna`·`gpt-5.6-terra` 가 있으나 미실측」)을 확인했다. 저장소 밖 폴더에서 읽기 전용 샌드박스로 호출했다.

| 명령 | exit | 응답 |
|---|---|---|
| `codex exec -m gpt-5.6-luna --sandbox read-only --skip-git-repo-check "Reply with exactly: OK"` | 0 | `OK` |
| `codex exec -m gpt-5.6-terra --sandbox read-only --skip-git-repo-check "Reply with exactly: OK"` | 0 | `OK` |
| `codex exec -m gpt-5.6-luna -c model_reasoning_effort=low --sandbox read-only --skip-git-repo-check --json …` | 0 | `turn.completed` · reasoning_output_tokens 0 |
| `codex exec -m gpt-5.6-terra -c model_reasoning_effort=low --sandbox read-only --skip-git-repo-check …` | 0 | `OK` |

- 선택 가능 집합 = {`gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`}.
- GPT-5.6 안의 순서 Luna < Terra < Sol 은 M3 22행(출처 https://en.wikipedia.org/wiki/GPT-5.6). 판정 ⑦(「수준에 상응하게」)에 따라 Sonnet 급 measurement-lane = `gpt-5.6-terra`·low, Haiku 급 gate-runner = `gpt-5.6-luna`·low 로 좁혔다. spec 의 대체 순서는 두 모델의 선택 가능 여부를 모를 때 쓴 것이다.

## 실측 4 (오케스트레이터 · 2026-09-25) — 5역할 스폰 · 적용 확인

방법은 실측 2 와 같다. 이 작업 사본(`claude/agent-model-tiering`)에서 부모 `codex exec --sandbox read-only --json -` 가 `spawn_agent(agent_type=<역할>)` 를 한 번 부르고, 자식 rollout(`~/.codex/sessions/2026/09/25/`)의 **마지막** `turn_context` 를 읽었다.

| 역할 | 역할 파일 | 자식 마지막 `turn_context` model · effort | 자식 thread_id | 부모 thread_id |
|---|---|---|---|---|
| gate-runner | `gpt-5.6-luna` · low | `gpt-5.6-luna` · low | `01a0d3f2-49cf-7a10-8113-484063fd1635` | `01a0d3f2-327e-7a01-9f40-297c3edeada4` |
| researcher | `gpt-5.6-sol` · medium | `gpt-5.6-sol` · medium | `01a0d3f3-374f-7782-9d65-a629b32fd9fc` | `01a0d3f3-2271-7573-9c9a-0d689baf5940` |
| measurement-lane | `gpt-5.6-terra` · low | `gpt-5.6-terra` · low | `01a0d3f5-461e-79d3-9ff8-845daf9d0fa9` | `01a0d3f5-2e3c-7ed0-b011-ecb74706f8e0` |
| advisor | `gpt-6-astra` · high | `gpt-6-astra` · high | `01a0d3f5-9332-7cb2-b8b5-4f70310bab48` | `01a0d3f5-7a5e-7582-85c6-bb6a6a9c6dc5` |
| lane-worker | `gpt-5.6-sol` · high | `gpt-5.6-sol` · high | `01a0d3f5-ce9f-75d0-bbcd-d7fe3a35e1a0` | `01a0d3f5-b846-7403-b9f2-5416f9723f70` |

- **역할 배정 적용 = 5역할 모두 검증됨.** 부모는 모두 `gpt-6-astra` · low(전역). 부모 5개의 `spawn_agent` 인자는 `agent_type`·`task_name`·`message` 뿐이고 model·effort 를 넘기지 않았다(부모 rollout `function_call` 확인). 자식 스폰 뒤 작업 사본의 파일 변경 0(`git status`).
- ⚠ 함정: 자식 rollout 에는 `turn_context` 가 2개 있다. **첫 번째는 부모에게서 물려받은 값**(astra · low)이고 두 번째가 역할 파일 값이다. 첫 번째만 읽으면 「적용 안 됨」으로 오판한다(이 실측 중 한 번 오판했다).
- 역할 파일은 신뢰 등록된 주 체크아웃이 아니라 **작업 사본(cwd)의 `.codex/agents`** 에서 읽혔다(작업 사본 값 luna·terra 가 적용 · 주 체크아웃 develop 은 astra·sol).

## 시험 red (오케스트레이터 · 2026-09-25 · 실측 3′ 기준)
- measurement-lane·gate-runner 의 toml 을 잠시 `gpt-5.6-sol` 로 되돌려 `AgentConfigurationTests` 실행: `FAILED (failures=2)` — `'gpt-5.6-sol' != 'gpt-5.6-terra'` · `'gpt-5.6-sol' != 'gpt-5.6-luna'`. 원복 뒤 `test_agent_bridge` 전체 `OK (skipped=10)`.
- 시험은 역할 집합을 `scripts/agent-bridge.py` `CODEX_ROLES` 와 같게 단언한다(목록 두 곳의 표류 방지).

