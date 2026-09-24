# M2 조사 — Codex 모델·설정 스키마·테스트 고정값

## Q1. 사용 중인 Codex 모델과 티어

- `.codex/agents/*.toml`에서 발견된 실제 모델 값 (grep 결과):
  - `advisor.toml:2` `model = "gpt-6-astra"`
  - `gate-runner.toml:4` `model = "gpt-6-astra"`
  - `lane-worker.toml:2` `model = "gpt-5.6-sol"`
  - `measurement-lane.toml:4` `model = "gpt-6-astra"`
  - `researcher.toml:2` `model = "gpt-5.6-sol"`
- `docs/development/dual-agent.md:103-105` (역할별 모델 배정 서술):
  > `.codex/agents/*.toml`에 `model`이 지정된 역할은 그 값을 부모보다 우선한다.
  > 실행·지원 역할인 `lane-worker`와 `researcher`는 `gpt-5.6-sol`, 검증·검토 역할인
  > `gate-runner`와 `advisor`는 `gpt-6-astra`를 사용한다. 모델을 지정하지 않은 다른 역할만
  > 부모 설정을 상속한다.
- `docs/development/dual-agent.md:126` (Codex 버전 단락):
  > Codex는 사용자 npm 설치와 앱 번들을 탐색해 확인된 Astra 대응 버전인 0.153.0 이상 중
  > 가장 높은 버전을 선택한다(동일 버전이면 정식판 우선).
- `dev-package/prd/rounds/R-CODEX-PARITY.md` 최상단 요약: 2026-09-09 기준 "실제 CLI `0.153.4` / `gpt-6-astra`"로 40/40 통과했다고 기록. `evidence/codex-final-40-h08-v2`(38/40)와 `evidence/codex-final-40-env-restored`(38/40)는 이전 실행 이력으로 별도 보존.
- `eval/harness/results/role-model-activation-probe-20260909.json`: `cli_version: "0.153.4"`. `requested_roles`는 `researcher→gpt-5.6-sol`, `advisor→gpt-6-astra`를 요청했으나, `status: "unavailable"`, `spawned_roles: []` — "현재 CLI의 spawning tool에서 named custom agents researcher/advisor를 선택할 수 없었고 shell read도 policy에 차단되어 실제 역할을 호출하지 못했다"고 기록되어 있어 이 측정 시점에는 named-agent 스포닝 자체가 실패 상태였음.
- `scripts/tests/test_agent_bridge.py:31-35` — 테스트가 고정한 기대값(위 Q3에서 재인용): `lane-worker`/`researcher` → `gpt-5.6-sol`, `gate-runner`/`advisor` → `gpt-6-astra`.
- 호스트 실측:
  - `codex --version` → `codex-cli 0.154.0` (dual-agent.md가 말하는 "0.153.0 이상 중 최고 버전" 조건을 만족하는 실제 설치본. 문서 기준 최소값보다 높음).
  - `~/.codex/config.toml` (비밀값 제외, 최상위): `model = "gpt-6-astra"`, `model_reasoning_effort = "low"`. 프로젝트 신뢰 목록에 이 저장소(`/home/ttlhi10/workspace/00_Project/00 CoLAB/32 CoLAB-v2`) 포함.
  - `~/.codex/config.toml`의 `[tui.model_availability_nux]` 섹션: `"gpt-5.5" = 2`, `gpt-6-astra = 4`. 이 숫자는 UI 노출/가용성 관련 값으로 보이며 "티어" 또는 "비용"이라는 명시적 라벨은 없음 — **미기재**(추정 금지).
  - 설치된 Codex CLI 바이너리(`~/.npm-global/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/.../bin/codex`)의 문자열에서 `"astra"`, `"gpt-5.6-sol"`, `"mini"` 리터럴을 직접 검색했으나 **매치 없음** — 이 모델 이름들은 CLI 바이너리에 내장된 카탈로그가 아니라 이 저장소의 `.codex/agents/*.toml`·사용자 `config.toml`에서만 나온다.
  - 모델 카탈로그 관련 CLI 내부 필드명은 존재: `modelSpecialty`, `hidden`, `supportedReasoningEfforts`, `defaultReasoningEffort`, `inputModalities`, `additionalSpeedTiers`, `serviceTiers`, `defaultServiceTier`, `isDefault` 등(문자열 상수). 다만 이 필드들이 채우는 실제 모델별 값(카탈로그 JSON, `model_catalog_json` 설정으로 로드되는 듯)은 로컬에서 직접 확인하지 못했다 — **모델별 정확한 티어/비용 문자열은 미기재**.
- **결론(모델명 전수)**: `gpt-6-astra`, `gpt-5.6-sol`(둘 다 이 저장소 설정에서만 확인), 사용자 개인 `config.toml`의 최상위 `model`도 `gpt-6-astra`. `gpt-5.5`는 `model_availability_nux` 표에만 등장(용도 불명). 어느 것도 "mini"라는 변형명이나 "고급/저가" 같은 명시적 티어 라벨이 붙어 있지 않음 → **티어는 미기재**로 보고한다.

## Q2. Codex 커스텀 에이전트 `.toml` 스키마 — `model_reasoning_effort`·턴/스텝 제한

- CLI 바이너리 문자열에서 `.codex/agents`를 로드하는 컴포넌트는 `agent-roles/src/loader.rs`, `agent-roles/src/discovery.rs`로 식별됨(strings에서 소스 경로 리터럴로 확인).
- `AgentRoleToml`(strings: `"struct AgentRoleToml with 3 elements"` 바로 뒤 `descriptionconfig_filenickname_candidates`)의 필드는 **`description`, `config_file`, `nickname_candidates`** 3개뿐으로 보인다. 이는 "역할 디스커버리 매니페스트 항목"(이 역할이 가리키는 toml 파일 경로·별칭 후보)의 스키마로 추정되며, `.toml` 파일 **내부** 키 스키마(name/model/sandbox_mode/developer_instructions)와는 다른 레이어다 — 확실하게 이 구조체 하나로 전체 커스텀 에이전트 키 목록을 단정할 수 없음.
- `developer_instructions`는 필수 키로 확인됨. strings에서 직접 나온 에러 메시지:
  - `"% must define \`developer_instructions\`"`
  - `".developer_instructions cannot be blank"`
  - `")\`additional_developer_instructions\` from "` (역할 파일 외에 상위에서 추가 지침을 합치는 `additional_developer_instructions` 경로도 존재)
- `model`, `sandbox_mode`, `model_reasoning_effort`는 모두 CLI의 메인 설정 구조체 `ConfigToml`(strings: `"struct ConfigToml with 101 elements"`)의 필드 목록에 포함되어 있음을 확인(연속 문자열 나열 중 `model_reasoning_effort`, `sandbox_mode`, `sandbox_workspace_write`, `developer_instructions`, `approval_policy`, `model_verbosity`, `plan_mode_reasoning_effort`, `model_reasoning_summary` 등이 한 블록에 나열됨). 이 저장소 실제 `.codex/agents/*.toml` 4개 파일은 `name`, `description`, `model`, `sandbox_mode`(advisor만), `developer_instructions`만 사용하며 `model_reasoning_effort`를 쓰는 파일은 없다(grep 결과 전량 재확인: 4개 파일 어디에도 `model_reasoning_effort` 없음). 반면 사용자 전역 `~/.codex/config.toml`에는 `model_reasoning_effort = "low"`가 top-level로 설정돼 있다 — 즉 이 키가 **CLI 설정 스키마상 존재하고 동작함**은 실측으로 확인되나, **역할별 `.toml`에서 개별 지정해도 적용되는지는 로컬 문서·코드로 직접 확인하지 못했다**(스키마 필드 존재 = 사용 가능성의 근거이나, 역할 오버라이드 적용 여부는 미검증).
- 턴/스텝 제한(Claude `maxTurns`에 대응하는 키): **`.codex/agents/*.toml` 4개 파일 어디에도 그런 키가 없고**, CLI 바이너리 문자열에서도 커스텀 에이전트 role 파일 스키마에 결부된 `max_turns`/`maxTurns`/`max_steps` 계열 키는 발견되지 않았음(정확 매치 검색 결과 0건). 근접한 것은 두 가지뿐이며 둘 다 다른 용도임을 명확히 해야 한다:
  1. `job_max_runtime_seconds` — `features.multi_agent_v2`(서브에이전트 스폰) 설정 블록 소속으로 보이는 필드(`max_concurrent_threads_per_session`, `max_depth`, `default_subagent_model`, `default_subagent_reasoning_effort`, `job_max_runtime_seconds`, `interrupt_message`가 한 묶음으로 반복 등장). 이는 "서브에이전트 작업의 최대 실행 시간(초)"이며 턴 횟수 제한이 아니다.
  2. `turnLimit` — `"limitturnLimitincludeOutputsmaxOutputCharsPerItemtargetstimeoutMs"`와 `"struct ListArguments with 2 elements...turnLimitincludeOutputsmaxOutputCharsPerItem...struct ReadArguments with 5 elements"` 문맥에서 등장. 이는 `codex agents list`/`thread/read` 계열 API 호출 인자로 보이며(세션 조회 시 반환할 턴 개수 제한), 에이전트 실행 자체의 스텝 상한이 아니다.
  - **결론**: 로컬에서 확인 가능한 범위 내에서 Claude `maxTurns`와 1:1 대응하는 커스텀 에이전트 `.toml` 키는 없다. `job_max_runtime_seconds`는 시간 기반 상한이라는 점에서 근사치일 수 있으나 이는 `features.multi_agent_v2`의 전역/공용 설정이지 개별 `.codex/agents/<role>.toml` 파일이 갖는 키가 아니다(4개 role toml 파일에 해당 키 없음).
- `sandbox_mode`는 `.codex/agents/advisor.toml:3`에서 `"read-only"`로 실사용 중이고, `codex exec --help`의 `-s, --sandbox` 옵션이 허용하는 값은 `read-only`, `workspace-write`, `danger-full-access` 세 가지로 CLI 도움말에서 직접 확인.

## Q3. 테스트가 고정한 Codex 모델명과 변경 시 요구사항

- `scripts/tests/test_agent_bridge.py:29-40` (`AgentConfigurationTests.test_role_models_are_explicit_and_do_not_claim_parent_inheritance`):
  ```python
  expected = {
      'lane-worker': 'gpt-5.6-sol',
      'researcher': 'gpt-5.6-sol',
      'gate-runner': 'gpt-6-astra',
      'advisor': 'gpt-6-astra',
  }
  for role, model in expected.items():
      with self.subTest(role=role):
          config = tomllib.loads(
              (bridge.ROOT/f'.codex/agents/{role}.toml').read_text(encoding='utf-8')
          )
          self.assertEqual(config.get('model'), model)
          instructions = config['developer_instructions'].lower()
          self.assertNotIn("inherit the parent's model", instructions)
          self.assertNotIn("inherit the parent's settings", instructions)
  ```
  → `.codex/agents/*.toml` 4개 파일의 `model` 키 값을 정확히 이 문자열로 단언하며, `developer_instructions` 본문에 "부모 모델/설정 상속" 문구가 없어야 한다는 것도 함께 단언한다.
- `scripts/tests/test_codex_harness_eval.py`에서 `gpt-6-astra`가 하드코딩된 지점(전부 JSONL 합성 이벤트의 모델 값으로 사용):
  - `:48` `'{"type":"turn_context","payload":{"model":"gpt-6-astra"}}\n'`
  - `:53` `self.assertEqual(runner.runtime_model(raw, Path(tmp))['models'], ['gpt-6-astra'])`
  - `:61` `{'type':'turn_context','payload':{'model':'gpt-6-astra','cwd':'a'+separator+'b'}}`
  - `:64` `self.assertEqual(evidence['models'], ['gpt-6-astra'])`
  - `:93` `runner.runtime_model('{"type":"item.completed","item":{"type":"agent_message","text":"model gpt-6-astra"}}', Path('.'))`
  - `:101` `{'type':'turn_context','payload':{'model':'gpt-6-astra'}}` → `:103` `self.assertEqual(evidence['models'], ['gpt-6-astra'])`
  → 이 파일은 `runner.runtime_model()`이 Codex JSONL 이벤트 스트림(`turn_context.payload.model`, 또는 `agent_message` 텍스트 내 "model <name>" 패턴)에서 모델 식별자를 올바르게 추출하는지를 검증하는 것이 목적이며, `gpt-6-astra`는 "실제 기대 모델명" 자체가 아니라 파서 로직 검증용 고정 샘플 문자열로 쓰인다.
- **모델 매핑을 바꿀 때 그린을 유지하려면**:
  1. `.codex/agents/{lane-worker,researcher,gate-runner,advisor}.toml`의 `model` 값을 새 이름으로 바꾸고, `scripts/tests/test_agent_bridge.py:31-35`의 `expected` 딕셔너리 값을 동일하게 갱신해야 함(안 하면 `assertEqual(config.get('model'), model)`이 즉시 실패).
  2. `developer_instructions` 문구에 "부모 모델을 상속한다"는 식의 문장을 넣지 않아야 함(`assertNotIn` 두 건이 계속 통과해야 함).
  3. `scripts/tests/test_codex_harness_eval.py`의 `gpt-6-astra` 리터럴들은 실제 CLI 모델명과 무관하게 파서 회귀 고정값이므로, 모델명이 바뀌어도 이 테스트 자체는 그대로 둬도 green을 유지할 수 있음(파서가 "임의 문자열"을 추출하는지 검증하는 테스트이지 실제 운영 모델명과 동기화된 단언이 아님) — 다만 이 파일이 별도로 실제 운영 모델명을 검증하는 다른 assert를 추가로 갖게 될 경우엔 재확인 필요(이번 조사에서는 그런 추가 assert를 발견하지 못했다).
  4. `dev-package/prd/rounds/R-CODEX-PARITY.md`와 `docs/development/dual-agent.md:103-105`의 모델명 서술은 테스트가 아니라 문서이므로 게이트를 깨지는 않지만, 모델을 바꾸면 이 두 문서도 실제와 어긋나므로 같이 갱신해야 문서-코드 불일치가 남지 않는다.

