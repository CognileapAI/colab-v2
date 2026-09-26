## PR 2 · lifecycle 증거 정확도
- PR 2(판정·증거 정확도) 둘째 묶음 · PR 1 병합 뒤 lane 1개가 구현한다 · 판정은 Ted(/grill-me 그룹 B 단위) · PR 게시는 Ted · 코드 줄 번호는 develop `67a03a05` 에서 2026-09-25 재확인.
- 이 묶음의 lifecycle 경로(H6/H7 · task 결속)는 이번 분석에서 `COLAB_TASK_ID` 없이 측정돼 실행 경로로는 확인되지 않았다 — 근거는 코드 읽기와 단위 시험(`test_task_runtime.py` 31 · `test_harness_lifecycle_contract.py` 29)이다.

### L1 task 종료 상태·정리 수단 없음  (출처: R4-11, R4-12)
- 문제: lifecycle 하위 명령은 begin · write-artifact · run-bound-gate · gate-snapshot · gate-start · run-gates · validate-input · handoff · stop 뿐이다 — close · prune 없음(`scripts/harness/hooks/lifecycle_contract.py:539`–`569`). handoff 는 `COLAB_HANDOFF` 줄을 출력하고 `stop()` 으로 자기검증만 하며 task.json 에 쓰지 않는다(`:600`–`609`). 보존·정리 규칙 문서 0(`docs/development/lifecycle-evidence.md` · `dual-agent.md` grep).
- 문제(측정): `.git/colab-harness` 153 MB · task.json 204 · checkout key 42(메인 재현 2026-09-25 · 본 초안 재계측 동일). 사라진 checkout 의 task 74건 · 보고서 없는 gate 역할 task 12건(R4 census · 검증 confirmed). task 당 약 700 KB 는 baseline 이 저장소 전 파일 hash 를 담기 때문이다(`lifecycle_contract.py:137`–`158`, `:244`–`247`) — 저장 형식 축소는 이 항목 범위 밖.
- 선택지: ⓐ `stop()` 통과 시점(CLI handoff · SubagentStop 훅 각각)에 task.json 에 종료 기록(mode · run_id · 판정 H6/H7 · 시각)을 남기고 열린/닫힌 task 조회 명령을 둔다 ⓑ `lifecycle prune` — 기본 dry-run · `git worktree list` 에 없는 checkout 의 task 와 종료 뒤 N일 지난 task 를 대상으로 출력 · `--apply` 로만 삭제 ⓒ 문서만 — lifecycle-evidence.md 에 보존 규칙·수동 삭제 절차
- 권장: ⓐ+ⓑ — ⓐ 없이는 ⓑ 가 인계된 task 와 버려진 task 를 가르지 못한다. ⓐ 는 L2 ⓑ · L3 ⓑ 의 전제다. 현재 store 에 대한 `--apply` 실행은 Ted 승인 뒤(되돌릴 수 없는 삭제).
- 완료 기준: `test_task_runtime.py` 에 ① handoff 성공 뒤 task.json 종료 기록 존재 ② `stop()` 실패 시 종료 기록 없음 ③ prune dry-run 이 사라진 checkout 의 task 를 나열하고 파일을 지우지 않음 ④ `--apply` 뒤 대상 디렉터리 부재 — 시험이 추가되고 `agent-bridge` gate green. 현재 store 에 대한 dry-run 대상 건수를 PR 요약에 기록.
- 판정 질문: 권장안 수용? 수용 시 보존 기간 N 을 며칠로 할지 · prune `--apply` 를 누가 실행할지.

### L2 H6/H7 이 agent 가 지목한 task 에 결속됨 — 새 begin 이 baseline 을 재설정  (출처: R4-judges-evidence-missed 1)
- 문제(코드): `stop()` 은 handoff JSON 의 `task_id` 로 task 를 읽는다(`lifecycle_contract.py:369`). agent 신원 대조는 task 에 `agent_id` 가 있을 때만 한다(`:377`). researcher 자동 task 는 `--agent-id` 없이 열린다(`scripts/harness/hooks/researcher-task.sh:9`–`10` · `lifecycle-evidence.md:42`). 「baseline 재설정 금지」는 문장뿐이다(`lifecycle-evidence.md:36`). 코드 읽기상 경로: researcher 가 제품 파일을 고친 뒤 새 `begin --role researcher` 를 열고 그 task 로 `handoff --mode read-only` 하면 H6 이 통과한다. 어느 task 가 spawn 시점 task 인지 기록도 없다(L1).
- 문제(lane): scoped lane 의 출구 ⑴(범위를 넓힌 새 task)은 범위 밖 변경을 새 baseline 에 흡수한다 — 문서화된 동작이며 `--summary` 에 사유를 적게 한다(`lifecycle-evidence.md:95`–`96`).
- 재현 결과: (오케스트레이터 기입 — probe 결과에 따라 아래 두 갈래 중 하나로 확정)
- 선택지: ⓐ spawn 결속 — SubagentStart 훅이 연 자동 task 를 agent_id 별 spawn task 로 runtime 에 기록하고, SubagentStop 의 `stop()` 이 handoff task 의 baseline 과 spawn task baseline 사이 변경을 선언 산출물 밖이면 거부(전제: Start/Stop agent_id 일치 — L8) ⓑ begin 연쇄 차단 — 같은 checkout 에 종료 기록 없는 researcher task 가 있고 그 baseline 대비 변경이 있으면 researcher begin 을 거부(전제: L1 ⓐ · agent_id 불필요 · lane 출구 ⑴ 은 대체한 task_id 를 새 task 에 기록하는 형태로 유지) ⓒ 문서만 — `lifecycle-evidence.md:36` 을 「기계 강제 없음 · 부모가 인계 뒤 `git status` 로 확인」으로 고침
- 권장: 재현되면 ⓑ — L1 ⓐ 위에서 agent_id 증명 없이 성립한다. ⓐ 는 L8 에서 agent_id 일치가 확인된 뒤 추가 여부를 다시 따진다. 재현되지 않으면 막은 지점(file:line)을 `lifecycle-evidence.md` 에 적고 ⓒ 로 종결.
- 완료 기준: (재현 시) `test_task_runtime.py` 에 「제품 파일 변경 → 새 researcher begin → read-only handoff」 시나리오가 begin 단계에서 거부되는 시험, 변경 없는 상태의 artifact task 추가 begin(`lifecycle-evidence.md:43` 절차)은 통과하는 시험 — 둘 다 green. (미재현 시) 재현 명령·결과·막은 지점이 lifecycle-evidence.md 에 기록.
- 판정 질문: 재현 결과를 본 뒤 ⓑ(재현) / ⓒ(미재현) 수용?

### L3 lane 이 자기 전용 worktree·고유 브랜치에서 도는지 확인하지 않음  (출처: R2-2 corrected, H9)
- 문제(문서 갈림): `.agents/skills/executing-plans/SKILL.md:17` · `.agents/skills/writing-plans/SKILL.md:166` · `.agents/skills/VENDORED.md:87` 은 lane-worker 격리를 「(자동)」으로 적고, `.agents/skills/design-review/SKILL.md:106` 은 frontmatter `isolation: worktree` 에 기댄다. `.agents/skills/colab-v2-work/SKILL.md:48` · `.agents/rules/colab-rules.md:63` · `writing-plans/SKILL.md:14` 는 명시 `Agent(isolation: "worktree")` 를 지시한다.
- 문제(검사 부재): `.agents/roles/lane-worker.md:27` 은 HEAD 만 대조하고 `:31` 은 「자기 워크트리 밖 경로를 편집하지 않는다」 문장뿐이다 — 자기 checkout 이 부모와 다른지 확인하는 단계가 없다. 관측 1회: `dev-package/sessions/design-fix-followups-20260925-E.md:5` 「레인 L1 · L2 는 워크플로 안에서 통합 워크트리에 바로 커밋했다」(직렬 · 겹침 0). 원인(Workflow `agent()` 가 frontmatter isolation 을 받지 않음)은 사용자 메모리에만 있다 — 미검증. Agent 도구 스폰에서 같은 일이 생기는지도 미검증.
- 문제(H9): 지시문의 공용 브랜치 이름 `fixlane-work` 로 다른 레인의 `checkout -B` 가 이 레인의 ref 를 되돌렸다(`dev-package/sessions/design-fix-20260924-F-preview.md:114`–`117` · 커밋 손실 0). `.agents` · `.claude` · `docs` 에 이 이름 0건 — 지시문 쪽 문제. 발생 조건은 미재현.
- 선택지: ⓐ lane-worker 첫 줄 검사 — 지시문이 준 부모 checkout 경로와 `git rev-parse --show-toplevel` 이 같거나, 현재 브랜치를 다른 worktree 도 체크아웃하고 있으면(`git worktree list --porcelain`) 구현하지 않고 정지 · `colab-v2-work` 지시문 체크리스트에 「부모 경로 전달 · 레인별 고유 브랜치 이름」 추가 ⓑ 기계 검사 — `lifecycle begin --role lane-worker` 가 같은 checkout_id 에 종료 기록 없는 lane-worker task 가 있으면 거부(전제: L1 ⓐ) ⓒ 문서만 — 「(자동)」 3곳을 「스폰 시 isolation 명시(Workflow `agent()` 포함)」로 고치고 E.md:5 관측을 근거로 적음
- 권장: ⓐ+ⓒ — 관측된 형태(부모 worktree 에서 실행)를 스폰 직후 구현 전에 잡는다. `--git-dir` 대 `--git-common-dir` 비교는 부모가 linked worktree(통합 worktree)인 E.md:5 경우를 잡지 못해 선택지에서 뺐다. ⓑ 는 L1 ⓐ 채택 시 같은 PR 에 넣을지 따로 판정.
- 완료 기준: `executing-plans` · `writing-plans` · `VENDORED.md` 에서 lane-worker 「(자동)」 문구 grep 0건 · `lane-worker.md` 에 검사 명령 · 재현 기록 — 부모 경로를 준 lane-worker 를 isolation 없이 스폰하면 구현 전 정지를 보고하고, isolation 명시 스폰은 통과(Workflow `agent()` 1회 · Agent 도구 1회)가 PR 요약에 있다.
- 판정 질문: 권장안(ⓐ+ⓒ) 수용? ⓑ 를 같은 PR 에 넣을지.

### L4 researcher·lane 인계가 checkout 전체를 대조 — 같은 checkout 의 다른 writer 가 인계를 막음  (출처: R4-13 corrected, R4-judges-evidence-missed 3, H4, H5)
- 문제(코드): `snapshot()` 은 checkout 전체(`git ls-files --cached --others --exclude-standard`)를 hash 한다(`lifecycle_contract.py:137`–`158`). researcher `stop()` — HEAD 변경 거부(`:384`–`385`) · read-only/draft-return 은 변경 0(`:387`–`389`) · artifacts 는 WATCH 밖·선언 밖 변경 거부(`:390`–`397`). lane H7 — 보고서 `task_evidence` before/after 를 인계 시점 checkout 전체 hash 와 대조(`:322`, `:345`) → gate 실행과 인계 사이 부모·형제의 편집 1건이 범위와 무관하게 gate 재실행을 부른다.
- 문제(기록): H4 의 L3 · L4a · L4b 인계 거부는 형제 레인 파일이 「this task has unhanded output」로 잡힌 것이고 L4a 는 begin/write-artifact 실패(H5)가 겹쳤다. 자동 read-only task 가 동시 편집으로 거부된다는 것은 H4 에서도 「추론 · 미실측」이다. 커밋 경우는 `lifecycle-evidence.md:44` 에 문서화돼 있다.
- 문제(H5 문서 불일치): `.agents/roles/researcher.md:27` 은 쓰기 자리를 `dev-package/sessions/` · `reports/` · `intent/` 로, `design-review/SKILL.md:63`(§2-2 항목 5)은 `dev-package/sessions/design-review-<YYYYMMDD>-L<n>.md` 쓰기를, `:65`(항목 7)은 같은 worktree 에서 레인 n개 구성을 지시한다. 새 task 는 산출물을 `runtime:artifacts/<파일>` 로만 받는다(`scripts/harness/task_state.py:66`–`68`).
- 선택지(H4 틀 재사용): ⓐ `design-review` §2-2 · `researcher.md` 를 「`runtime:artifacts` 로 쓰고 메인이 hash 대조로 반입」으로 바꾼다(문서) ⓑ 레인마다 `isolation: worktree`(문서 · L3 과 결합) ⓒ 감시 범위를 task 선언 산출물·scope 로 좁힌다(코드)
- 권장: ⓐ(researcher) + ⓑ(lane · L3 ⓐ 로 확인) — 코드 변경 없이 다른 writer 를 checkout 에서 뺀다. ⓒ 는 선언 밖 제품 파일 편집 탐지를 빼므로 H6 의 목적과 충돌한다. 현행 우회(researcher 병렬 산출 → runtime:artifacts)는 사용자 메모리에만 있어 저장소 문서로 올린다.
- 완료 기준: `design-review/SKILL.md` §2-2 에 `dev-package/sessions/design-review-<YYYYMMDD>-L<n>.md` 쓰기 지시 grep 0건 · `researcher.md` 쓰기 범위에 runtime:artifacts 절차 · 재현 기록 1회 — 같은 checkout 에서 researcher 2건이 runtime:artifacts 로 쓰고 각각 `handoff --mode artifacts` 로 H6 통과.
- 판정 질문: 권장안(ⓐ+ⓑ · ⓒ 기각) 수용?

### L5 lane scope 판정 경계 — 오타 glob 통과 · task 중 병합  (출처: R4-9 corrected, R4-10)
- 문제: `check_scope_declarations` 는 끝 `/` 와 와일드카드 없는 기존 디렉터리 이름만 거절한다(`lifecycle_contract.py:81`–`93`). `frontend/scr/**` 같은 오타 glob 은 begin 을 통과하고 handoff 에서 모든 변경이 범위 밖으로 거부된다 → 새 task · gate 재실행(fail-closed · 거짓 green 아님). 기록 204건 중 scoped task 2건(2026-09-25).
- 문제: scope 판정은 begin 시점 커밋..HEAD 전체 diff 를 센다(`:410`–`419`). scoped lane 이 task 중 develop 을 병합하면 병합으로 들어온 파일이 전부 범위 밖이 된다. `test_task_runtime.py:319`–`343` 의 merge 는 begin 이전 충돌 생성용 — begin 뒤 병합 커밋 시험 0.
- 선택지: ⓐ begin 에서 glob 의 첫 와일드카드 앞 디렉터리 접두가 없으면 거절(기존 디렉터리 아래 새 파일은 통과) · lifecycle-evidence.md 범위 절에 「scoped task 중 병합하면 병합 파일이 범위 밖 — 병합 뒤 새 task」 문장 · 현재 병합 동작을 고정하는 시험 ⓑ ⓐ + `stop()` 이 begin 뒤 병합 커밋의 병합 부모와 HEAD 내용이 같은 파일을 레인 변경에서 뺌(코드) ⓒ 현행 유지 · 문서만
- 권장: ⓐ — 두 경우 모두 fail-closed 라 거짓 green 은 없다. ⓑ 는 병합 충돌 해소 편집을 레인 변경에서 빼는 경로를 새로 만든다.
- 완료 기준: `test_task_runtime.py` 에 ① 없는 접두 glob begin 거절 ② 기존 디렉터리 아래 새 파일 glob 통과 ③ begin 뒤 병합 커밋 → 병합 파일이 범위 밖 목록에 포함(현재 동작 고정) — green · lifecycle-evidence.md 범위 절에 병합 문장 1건.
- 판정 질문: 권장안 수용?

### L6 lifecycle 판정기 시험 공백 — selftest 제외 · parallelism 검사 직접 시험 0  (출처: R4-3 corrected, R4-18)
- 문제: `gates/run.sh:315`–`316` `harness-contract-selftest` 는 시험 5파일만 돌리고 `test_harness_lifecycle_contract.py` · `test_task_runtime.py`(60 시험)를 뺀다. 두 파일은 `agent-bridge` gate(`gates/run.sh:308`–`310`)가 돌린다 → lifecycle 코드를 고친 lane 이 selftest 만 선언하면 lifecycle 시험 없이 green(검증 후 심각도 low).
- 문제: `check_gate_parallelism`(`scripts/harness/check.py:25`–`75`) 직접 시험 0 — `scripts/tests/test_harness_config.py:240` 이 lambda 로 대체한다. 미선언 gate 통과 · `ALL_GATES` 정규식 파손 회귀는 live 저장소 대상 gate 실행으로만 드러난다.
- 선택지: ⓐ selftest 에 두 lifecycle 시험 파일 추가 + `check_gate_parallelism` fixture 시험(미선언 gate · `ALL_GATES` 부재 · 없는 gate 선언 · serial/parallel 외 값) ⓑ fixture 시험만 추가하고 문서에 「lifecycle 파일 변경 lane 은 `agent-bridge` gate 선언」 ⓒ 문서만
- 권장: ⓐ — run.sh 한 줄과 시험 추가로 끝난다. `all` 에서 60 시험이 두 번 도는 추가 시간은 측정해 PR 요약에 적는다.
- 완료 기준: `gates/run.sh harness-contract-selftest` 로그에 두 lifecycle 시험 모듈 실행 · 새 fixture 시험이 결함 fixture 에서 errors 비어 있지 않고 정상 fixture 에서 0 — green · 시험 수 증가분 기록.
- 판정 질문: 권장안 수용?

### L7 Workflow advisor·measurement-lane 에 schema 를 걸면 StructuredOutput 실패  (출처: H8)
- 문제: 저장소 기록 0 — `StructuredOutput` 은 `.agents` · `.claude` · `docs` 에 0건, 흡수 대상 초안 intent 에만 있다. 사용자 메모리(저장소 밖)에 「`agentType: 'advisor'` · `'measurement-lane'` 에 `schema` → 'completed without calling StructuredOutput' 로 워크플로 정지(3회)」. 원인(maxTurns · measurement-lane 종료 형식 · 플랫폼 동작)은 미검증. 당시 advisor maxTurns 12 → 현재 16(`.claude/agents/advisor.md:7` · 커밋 `0e33ce02`) · measurement-lane 60(`.claude/agents/measurement-lane.md:7`).
- 선택지: ⓐ 문서 — Workflow 판정·측정 단계는 schema 없이 첫 줄 `VERDICT:` 텍스트로 받는 현행 우회를 `colab-v2-work` 절차로 올림 ⓑ 재현 먼저 — 현재 정의에서 schema 를 건 advisor · measurement-lane 각 1회 실행 → 재현되면 ⓐ, 아니면 결과만 기록 ⓒ measurement-lane 종료 형식을 StructuredOutput 호출과 양립하게 변경 — 원인 확인 전 보류
- 권장: ⓑ → ⓐ — 한도 변경(#131) 뒤 재현 여부가 없다. 재현 2회는 작은 비용이고 결과로 문서 문장이 정해진다.
- 완료 기준: 재현 2회의 결과(StructuredOutput 호출 여부 · 도구 호출 수 · 종료 사유)가 기록되고, 재현 시 `colab-v2-work` 에 규칙 1줄(grep 1건).
- 판정 질문: 권장안(재현 뒤 문서화) 수용? 이 항목을 PR 3(문서 drift)으로 옮길지.

### L8 researcher 라이브 스모크 — Start/Stop agent_id 일치 기록  (출처: H10 · R1-19 · R5-10)
- 문제: #130 병합 뒤 할 일인 researcher 라이브 스모크 결과가 저장소에 없다 — `lifecycle-evidence.md:42` 는 「agent_id 일치가 증명되지 않았으므로 자동 task 는 정지 시 ID 를 대조하지 않는다」를 유지하고, `dev-package/prd/specs/S-HARNESS-LANE-HYGIENE-20260924.md:44` 는 계획 문장뿐이다. `/hooks` 재신뢰 실시 여부는 저장소에서 확인할 수 없다(기록 없음 · 미검증). 설계는 일치 없이 동작한다(`researcher-task.sh:9`–`10`) — 빠진 것은 기록이다(검증 후 심각도 low).
- 선택지: ⓐ Ted 의 `/hooks` 재신뢰(T 그룹) 뒤 agent 가 researcher 1건 스모크 — 훅 출력 agent_id 로 `begin --role researcher --agent-id <id> --artifact runtime:artifacts/<파일>` task 를 열고(`lifecycle-evidence.md:43`) 그 task 로 인계. `stop()` 은 task agent_id 와 SubagentStop payload agent_id 를 대조하므로(`lifecycle_contract.py:377`) H6 통과 = 일치 ⓑ 스모크 생략 · 문서 유지
- 권장: ⓐ — L2 ⓐ(spawn 결속) 채택 가능 여부가 이 결과에 달린다. 스모크는 재신뢰 뒤에만 의미가 있어 PR 2 병합 뒤 관측 항목으로 둔다.
- 완료 기준: 스모크 1회의 훅 출력 agent_id · 인계 task_id · H6 결과(통과/「task role or agent identity differs」)가 기록되고, 통과면 `lifecycle-evidence.md:42` 문장 갱신 · 거부면 L2 ⓐ 제외 기록.
- 판정 질문: 권장안 수용? 기록 위치(이 intent 판정 절 · lifecycle-evidence.md) 중 어디.
