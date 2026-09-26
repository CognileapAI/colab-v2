### L5
- 판정: ⓐ (접두 검사의 판정 기준을 「첫 와일드카드 앞 구간의 dirname 이 작업 트리에 존재」로 고정 · 거부 메시지에 출구 2개 명기)
- 확신: 높음
- 사실 확인: 파일 경로 정정 — `scripts/harness/lifecycle_contract.py` 는 없고 `scripts/harness/hooks/lifecycle_contract.py` 다. `check_scope_declarations` :81–93 확인 — 거절은 끝 `/`(:89) · 와일드카드 없는 기존 디렉터리(:91) 두 형태뿐, `frontend/scr/**` 는 통과. 병합 문제 확인 — 변경 원천은 셋: baseline 내용 snapshot 대조(:403–405) + `diff started..HEAD`(:414) + `diff --cached` vs `started_index`(:415). begin 뒤 develop 병합 파일은 **세 원천 중 두 곳**(snapshot · started..HEAD)에 잡힌다 → ⓑ 가 말하는 「started..HEAD 에서 병합 부모와 같은 파일 제외」만으로는 snapshot 쪽이 여전히 범위 밖으로 낸다(ⓑ 설계 정정). `test_task_runtime.py:319–343` 확인 — 병합은 begin 이전 충돌 거절 시험, begin 뒤 병합 커밋 시험 0. 기록 2/204 scoped · 둘 다 literal 경로(findings R4-9).
- 이유: 오타 glob 은 begin 하는 주체(lane)가 즉시 고쳐 재-begin 할 수 있어 begin 시점 거절이 가장 싼 자리다 · 기존 디렉터리 아래 새 파일(`docs/new.md` → dirname `docs` 존재)은 통과하므로 정상 사용을 막지 않는다. 병합 제외(ⓑ)는 세 원천 모두를 고쳐야 하고 판정이 병합 토폴로지에 종속돼 추론이 어렵다. 더 근본적으로 병합 뒤 handoff 증거는 병합된 HEAD 기준 gate 결과여야 하므로 「병합 뒤 새 task + gate 재실행」은 비용이 아니라 올바른 형태다 — 문서화가 곧 정답이다.
- 위험·전제: 범위가 아직 없는 새 디렉터리(`frontend/src/newdir/**`)는 ⓐ 규칙에 거절된다 → 메시지에 「빈 디렉터리를 먼저 mkdir(추적 대상 아님 · baseline 불변) 하거나 부모 glob 선언」 출구를 적는다. B1 ⓒ 채택 전제 — 유지 시에도 문서 문장으로 처리 가능.
- 뒤집힐 조건: B1 ⓒ 가 기각돼 PR 브랜치에 develop 병합이 정규 절차로 남고 scoped lane 이 자주 그 절차를 타는 실측(월 수 회)이 나오면 ⓑ 를 세 원천 공통 필터로 다시 설계. scoped task 가 계속 literal 경로만 쓰면(와일드카드 0) 접두 검사 자체의 가치가 낮아 문서만(ⓒ)으로 후퇴 가능.

### L6
- 판정: ⓐ (두 lifecycle 시험 파일을 `harness-contract-selftest` 에 추가 · `agent-bridge` 에서는 빼지 않음 · `check_gate_parallelism` fixture 시험 4종) + ⓑ 의 문서 문장을 `.agents/roles/lane-worker.md`·`colab-v2-work` 에 1줄
- 확신: 높음
- 사실 확인: `gates/run.sh:315–316` selftest 5파일 · `:308–310` agent-bridge 6모듈(두 lifecycle 파일 포함) 확인. 시험 수 60 = 29(`test_harness_lifecycle_contract.py`) + 31(`test_task_runtime.py`) 확인. `check.py:27–75` · `test_harness_config.py:240` lambda 대체 확인 · `COLAB_GATE_PARALLELISM_MANIFEST` env(:39) 와 `root` 인자로 fixture 화 가능. 추가 사실: `.agents/harness.yaml:16–28` required 에 `agent-bridge` 는 있고 `harness-contract-selftest` 는 없다. `ci.yml` 은 `gates/run.sh agent-bridge` 를 어디서도 돌리지 않는다 — lifecycle 시험이 CI 에 닿는 경로는 `agent-bridge.yml:64` `unittest discover`(경로 필터 워크플로 · required check 아님)뿐. `ci.yml:795` `selftest` 집합은 `ALL_GATES` 의 `*-selftest` 를 모두 돌린다(`run.sh:679–697`). `dual-agent.md:283` 에 「훅·lifecycle 바꿨으면 agent-bridge」 문장은 이미 있으나 role·skill 문서에는 없다.
- 이유: selftest 에 넣으면 `ci.yml` `gate-selftest` 잡(required-gates needs 포함) 을 통해 lifecycle 시험이 **required 경로에 처음 들어간다** — 지역 선언 누락과 CI 비필수 워크플로 두 구멍을 한 번에 메운다. 중복 실행 비용은 60 시험(tempdir git)으로 bounded. fixture 시험은 미선언 gate · `ALL_GATES` 부재 · 없는 gate 선언 · serial/parallel 외 값 4종을 temp root + `COLAB_GATE_PARALLELISM_MANIFEST` 로 직접 검증 — lambda 대체가 가리던 회귀를 드러낸다.
- 위험·전제: `harness-contract-selftest` 는 `parallelism.toml:38` `parallel` 선언 — 추가 시험이 호스트 전역 자원·벽시계 단언을 갖지 않는지 근거 줄을 다시 적는다(agent-bridge 의 serial 사유는 `test_deploy_release`·`test_agent_bridge` 이지 lifecycle 파일이 아님 · `toml:250–259`). `gates/run.sh all` 벽시계 +1회분.
- 뒤집힐 조건: lifecycle 시험이 parallel pool 에서 흔들리는 실측(red 가 배선에서 남)이 나오면 selftest 를 serial 로 바꾸거나 ⓑ 로 후퇴. develop protection 에 required check 가 생겨 `agent-bridge.yml` 이 필수화되면 selftest 편입의 CI 이득이 사라져 fixture 시험 + 문서(ⓑ)로 충분.

### L7
- 판정: ⓑ → ⓐ (재현 2회를 먼저 · 재현 설계는 원인 판별형 · 결과와 무관하게 현행 텍스트 `VERDICT:` 우회를 colab-v2-work 에 「현행 관행」으로 1줄 기록)
- 확신: 중간
- 사실 확인: 저장소 0건 확인(`.agents`·`.claude/agents`·`docs/development` grep 0). advisor `maxTurns: 16`(`.claude/agents/advisor.md:7`) · measurement-lane `maxTurns: 60`(`measurement-lane.md:7`) 확인. 메모리 `workflow-advisor-model-and-schema.md` 내용 확인(3회 · maxTurns 12 시절). 추가 사실: measurement-lane 은 `tools: Bash, Read` **허용목록**(`measurement-lane.md:6`), advisor 는 `disallowedTools: Edit, Write, NotebookEdit`(`advisor.md:6`)뿐 — schema 가 subagent 의 `StructuredOutput` 도구 호출을 요구한다면 허용목록에 없는 measurement-lane 은 maxTurns 와 무관하게 결정적으로 실패하고, advisor 는 다른 원인(턴 소진)일 수 있다. 두 역할의 실패 원인이 같다는 전제는 근거 없음. `.agents/roles/measurement-lane.md:61` 종료 형식은 「최종 메시지에 gate-summary 절대경로」 텍스트 계약.
- 이유: 원인 미확인 상태로 ⓐ 만 하면 검증 안 된 우회가 절차로 굳는다 · 재현 비용은 작다(advisor: 게이트 없는 사소 질문 1건 · measurement-lane: `exec-bit-selftest` 같은 짧은 parallel gate 1건, 각각 schema 부착). 재현 시 transcript 에서 `StructuredOutput` 도구 존재 여부를 확인하면 `tools:` 허용목록 가설이 갈린다. 우회 자체는 무해(측정 결과는 `gate-summary.json` 을 오케스트레이터가 직접 읽으면 되므로)라 기록은 지금 해도 된다.
- 위험·전제: Workflow 스크립트는 저장소 밖(`~/.claude`)이라 저장소 측 레버는 문서뿐 · 재현이 워크플로 1회를 실제로 멈출 수 있어 독립 실행으로 한다. ⓒ 는 원인 확인 전 보류 유지.
- 뒤집힐 조건: measurement-lane 재현에서 `StructuredOutput` 이 도구 목록에 없음이 확인되면 새 선택지 — spec C1 frontmatter 개정으로 `tools:` 에 추가(또는 허용목록 제거)가 ⓐ 보다 근본 수정. 두 역할 모두 현 정의에서 재현 0 이면 문서에 「12턴 시절 관측 · 현재 미재현」만 남기고 우회 절차화는 하지 않는다.

### L8
- 판정: 새 선택지: ⓐ 를 T5 뒤가 아니라 **지금 먼저** 실행 — 스모크 자체가 재신뢰 여부의 관측이다. 훅 출력이 있으면 일치 판정 기록 · 없으면 「이 PC 훅 비활성」 기록 후 T5 → 재실행
- 확신: 높음
- 사실 확인: `lifecycle-evidence.md:42–43` 문장 확인. `S-HARNESS-LANE-HYGIENE-20260924.md:44` 「병합 뒤 라이브 스모크(후속 기록 · 병합 조건 아님) … 일치 확인되면 다음 intent 에서 `--agent-id` 부착 재검토」 확인. 경로 정정 — `.claude/hooks/researcher-task.sh` 는 3줄 어댑터, 인용 `:9–11` 은 `scripts/harness/hooks/researcher-task.sh:9–11`(`--agent-id` 생략 사유 주석). `lifecycle_contract.py:377` 확인 — task 에 agent_id 가 있을 때만 payload 와 대조 · `stop()` 은 `COLAB_HANDOFF` 의 task_id 로 task 를 고르므로(`:365–369`) `--agent-id` 붙인 두 번째 task 로 인계해 H6 통과 = Start(훅 출력)·Stop payload 일치 증명 성립. `dual-agent.md:87–89` 재신뢰 전 자동 task 미개설 확인. 순서 모순 발견: context 는 T5 를 PR 3 병합 뒤로 두는데 L8 은 PR 2 그룹이고 「T5 뒤」를 전제 — #130 정의는 이미 병합돼 재신뢰는 PR 3 과 무관하다.
- 이유: 스모크는 agent 단독 행동(researcher 1 스폰 · 질문 1개)이라 Ted 의존이 없고, 훅 발화 여부와 agent_id 일치를 한 번에 관측한다 → T5 대기 때문에 L8 이 PR 3 뒤로 밀리는 순서 문제를 푼다. 설계는 일치 없이 동작하므로 기록만 채우면 되며(ⓑ 는 spec :44 의 후속 약속을 영구 미이행으로 남김) 기록은 `.git/colab-harness`(저장소 밖)에 남으므로 문서에 task_id·run_id·훅 출력 줄을 인용해야 한다.
- 위험·전제: Claude 경로 한정(Codex 는 bridge 가 additionalContext 로 옮김 · 별도) · 자동 task 가 열린 채로 두 번째 task 인계 시 read-only 라 커밋 충돌 없음. 09-25 오케스트레이터 probe(격리 clone · H6 통과)가 훅 발화를 이미 관측했는지 확인하면 스모크 1회를 아낄 수 있다.
- 뒤집힐 조건: 스모크에서 Start·Stop agent_id 가 불일치하면 `lifecycle-evidence.md:42` 유지 + `--agent-id` 부착 재검토 취소. 훅이 발화하는데 auto task 가 두 개 열리는 등 다른 이상이 나오면 스모크가 아니라 hook 결함 항목으로 승격.

### 묶음 메모
- L5 ⓐ 는 B1 ⓒ 채택을 전제하지만 의존은 약하다 — B1 이 병합 절차를 남겨도 「병합 뒤 새 task」 문장 하나로 흡수된다.
- L6 selftest 편입은 PR 2 lane 자신에게 바로 적용된다 — PR 2 가 `lifecycle_contract.py`·`test_task_runtime.py` 를 고치므로 그 lane 의 선언 gate 에 `agent-bridge` 를 명시하고, L6 병합 전까지는 dual-agent.md:283 문장이 유일한 근거다.
- L7 재현과 L8 스모크는 코드 변경이 아니라 agent 실행이라 PR 순서와 독립 — 둘 다 PR 1 진행 중에 돌릴 수 있고 결과만 PR 2 문서 편집으로 들어간다.
- L8 의 T5 의존을 풀면 그룹 T 의 T5 시점(PR 3 뒤)은 「스모크가 훅 비활성을 관측한 경우」로만 좁혀진다.
- L7 에서 `tools:` 허용목록이 원인이면 spec C1 frontmatter 개정이 필요해 그룹 C(문서·설정 drift · PR 3)로 이동한다.