## PR 1 · 막는 장치 바로잡기
- 주체: spec phase 1 → lane 1개(격리 worktree) 구현 → PR 1 게시·병합은 Ted. PR 2·3 은 이 PR 병합 뒤 순차 착수. 판정은 그룹 A 단위 /grill-me(A1–A4 일괄).

### A1 git-guard 명령 해석 — quote-aware tokenizer + 대상 checkout 브랜치 해석  (출처: R1-hooks-missed(공백 `-C` 우회 · `pull`) · R1-4 · R1-5 · R1-21 · R5-19 정정)
- 문제:
  - 우회: `scripts/harness/hooks/git-guard.sh:167` 비인용 `set -- $seg` → 공백 든 경로의 `git -C "<repo>"` 에서 `-C` 가 첫 조각만 소비(`:193` `shift 2`), 다음 조각이 subcommand 로 읽혀 모든 규칙을 건너뜀. 메인 재현 2026-09-25(develop · payload cwd = 저장소 루트): `-C "<repo>"` 를 붙인 `push --force origin develop` · `branch -D develop` · subagent `push origin develop` · subagent `push origin main` → 모두 rc=0. 같은 명령 `-C` 없이 → rc=2. 공백 없는 `-C /tmp` 강제 push → rc=2. 저장소 절대경로·lane worktree 경로에 공백 포함, AGENTS.md 가 작업 디렉터리 명시를 요구 → 이 형태가 일상 명령 형태.
  - 대상 오판(R1-4 · 코드 확인): 보호 브랜치 판정 근거는 payload `cwd` 하나(`:143`). `-C`·`--git-dir`·`--work-tree` 대상, 같은 명령 안 `cd <dir>` 뒤 명령의 브랜치는 보지 않음 → refspec 없는 push(`:234` · `:242`)·merge(`:257`)가 다른 checkout 기준으로 판정.
  - argv 형태 누락(R1-5 · 코드 확인): gh 는 첫 두 인자가 정확히 `pr` `merge` 일 때만(`:182`) → `gh -R <o/r> pr merge` · `gh api …/pulls/<n>/merge` 통과. force 는 정확 토큰만(`:207`) → 묶은 `-fu` 통과. develop 위 subagent 의 `push origin HEAD` 통과(`HEAD` 를 브랜치로 풀지 않음 `:151-156`, `:242` 는 refspec 없을 때만).
  - `pull` 분기 없음(`:202-274`): 메인 재현 2026-09-25 — develop 위 `pull --no-ff origin develop` · `pull --no-rebase origin develop` rc=0, 같은 자리 `merge --no-ff origin/feature` rc=2.
  - 오탐(R1-21 · R5-19 정정): 개행을 ` ; ` 로 바꾸고(`:106`) `&&`·`||`·`;`·`|` 를 인용과 무관하게 분리(`:149`) → heredoc 본문·인용 인자 안에서 줄 또는 segment 시작에 오는 git/gh 병합 문구를 명령으로 판정. 줄·segment 시작일 때만 해당(문자열 어디서나 아님). 초안 작성 중 재현 1회(2026-09-25): grep -E 패턴 인자 안 `|` 뒤에 온 gh 병합 문구가 ⑷ 로 차단.
  - 시험: rule 시험은 `scripts/tests/test_agent_bridge.py:463` · `:483-507`(bridge `guard-command` 경유). 공백 경로 `-C` · heredoc · `pull` · gh 변형 · `-fu` · `HEAD` 형태 시험 0건(grep).
- 선택지:
  - ⓐ python quote-aware tokenizer(heredoc 본문 제외 · 인용 밖 연산자만 segment 분리) + 대상 checkout 해석(`-C`/`--git-dir`/`--work-tree`/선행 `cd`, 없으면 payload cwd) + 누락 argv 형태를 기존 규칙 ⑴–⑷ 에 편입(gh 전역 플래그 건너뛰기 · `gh api` 는 `-X`/`--method PUT` 인 merge 경로만 · 묶은 short flag 의 `f` · `HEAD`/`@` 를 대상 브랜치로 해석 · 보호 브랜치 위 `pull --no-ff`/`--no-rebase`).
  - ⓑ tokenizer + 대상 해석만(우회·오탐 해소). argv 형태 편입은 후속 PR.
  - ⓒ 현 bash 구조 유지 · `-C` 인자만 인용 처리 + `pull` 분기 추가. heredoc 오탐 · 대상 오판 · gh/`-fu`/`HEAD` 형태 잔존.
- 권장: ⓐ — 편입 형태는 모두 기존 열거 ⑴–⑷ 의 다른 argv 이고 새 규칙이 아님(머리말 `:11` 「명시 열거 — 넓히지 않는다」 유지). 시험을 새 tokenizer 기준으로 한 번에 작성.
  - fail-closed 위험: 모든 Bash 호출이 이 hook 를 거침(`.claude/settings.json:58-66`). envelope 이상 · python3 부재는 이미 exit 2(`:81-83`). tokenizer 결함 1건 = 이 스크립트를 쓰는 모든 세션의 Bash 정지.
  - 대응(권장안에 포함): command 텍스트 파싱 실패(짝 없는 인용 등) 시 현행 분리 규칙(`:149` · `:167`)으로 판정 → 현행 대비 차단 회귀 0. envelope 계약(`:81-83`) 무변경.
  - 복구 경로: Edit/Write 는 git-guard matcher 밖(`.claude/settings.json:68-84`) → Edit 로 되돌림 가능. `COLAB_HOOKS=0` 은 세션 재시작 필요(`README.md:79-98`).
  - lane 자기 검증 한계(문서 근거 — `scripts/harness/hooks/worktree-setup.sh:31-38` 의 hooks 문서 인용): hook 는 `${CLAUDE_PROJECT_DIR}` 쪽 스크립트를 실행 → lane worktree 의 수정본은 lane 자신의 Bash 호출에 적용되지 않음. 검증은 worktree 스크립트 직접 호출로 함.
  - `.claude/settings.json` · `.codex/hooks.json` 훅 정의 무변경이 전제. wrapper 내부 변경의 코드 snapshot 비교(`docs/development/dual-agent.md:86`)는 그룹 T 확인 항목.
- 완료 기준: 새 unittest(agent-bridge gate 가 실행하는 파일 · `gates/run.sh:308-310`)가 다음을 모두 보이면 끝.
  - ⑴ 공백 경로 `-C "<…>"` · `-C '<…>'` 로 ⑴–⑸ · product 규칙 각각 rc=2, 허용형(기능 브랜치 push · 기능 브랜치 위 `merge --ff-only` · `pull --rebase` · `worktree` · 기능 브랜치 원격 삭제) rc=0.
  - ⑵ 기능 브랜치 cwd 에서 `-C <develop checkout>` 또는 `cd <develop checkout>` 뒤 non-ff merge · subagent 의 refspec 없는 push → rc=2.
  - ⑶ heredoc 본문 · 인용 인자 안에 git merge · gh 병합 · 강제 push 문구가 든 쓰기 명령 → rc=0.
  - ⑷ `gh -R o/r pr merge` · `gh api -X PUT …/merge` · develop 대상 `push -fu` · develop 위 subagent `push origin HEAD` · develop 위 `pull --no-ff`/`--no-rebase` → rc=2. `gh api …/merge`(GET) · `pull --ff-only` → rc=0.
  - ⑸ 짝 없는 인용 입력의 rc 가 현행 규칙 결과와 같음.
  - ⑹ 기존 시험(`test_agent_bridge.py:463` · `:483-507` · `test_harness_lifecycle_contract.py:319-346`) green · 메인 재현 명령 6종을 lane worktree 스크립트로 재실행해 rc=2.
  - ⑺ `README.md:73` git-guard 행 · 머리말 허용 목록(`:22-24`)이 편입 형태와 일치.
- 판정 질문: 권장안 수용? — ① argv 형태 편입을 PR 1 에 넣을지(ⓐ) 후속으로 뺄지(ⓑ) ② 파싱 실패 = 현행 규칙 폴백 수용?

### A2 test-file-guard 가 Claude lane 에서 켜지지 않음 · 관련 문장 정리(H14 포함)  (출처: R1-2 정정 · R5-7 · H3 · H14)
- 문제:
  - `scripts/harness/hooks/test-file-guard.sh:32` — hook 프로세스 env 에 `COLAB_FIX_LANE=1` 이 없으면 exit 0. 값을 넘기는 곳은 `scripts/agent-bridge.py:278`(Codex) · `scripts/dev.ps1:102` 뿐, `.claude/` · 역할 파일 설정 0건(grep). hook env 는 Claude Code 프로세스 env 이므로 lane 별로 다르게 줄 수 없음.
  - 대체 수단: `begin --role lane-worker --scope <glob>` → handoff `complete` · H7 이 범위 밖 변경 차단(`docs/development/lifecycle-evidence.md:87-98`). 차단 시점 = 인계(편집 순간 아님). `.agents/roles/lane-worker.md:38` 은 지시문이 범위를 줄 때만 선언.
  - 문서 불일치: `.agents/skills/design-review/SKILL.md:101` · `:106`, `docs/development/dual-agent.md:60` 은 fix 구현 단계가 `COLAB_FIX_LANE=1` 로 돌고 hook 가 막는다고 기술. `SKILL.md:101` 은 두 문장이 붙어 있음(「…편집을 막는다보호된 fix 구현 단계에서…」, 재확인). 생성 커밋 `c1de5e31` 은 초안 조사 근거(재확인 안 함).
  - 초안 H3 대비: 상태 서술 유효. design-fix 20260924 lane 6개의 「규율로 지켰다」 기록은 초안 근거(재확인 안 함).
- 선택지:
  - ⓐ test-file-guard 가 env 외에 task 선언을 읽음(초안 H3 ⓐ): payload 에 `agent_id` 가 있는 Edit/Write 이고 payload cwd checkout 에 `--scope` 를 선언한 열린 lane-worker task 가 있으면, 대상이 보호 경로 4종(`:17-20`)이면서 그 scope 밖일 때 exit 2. 시험 작성 단계 task 는 scope 에 시험 경로를 넣어 통과. settings.json 정의 무변경.
  - ⓑ SubagentStart(lane-worker)가 `agent_id` 별 marker 를 쓰고 test-file-guard 가 PreToolUse payload `agent_id` 로 marker 를 찾음(역할 기반). 한계: 같은 lane 이 RED→GREEN 을 한 세션에서 진행(`SKILL.md:106`) → 단계 구분 불가 · SubagentStart 와 PreToolUse 의 `agent_id` 일치 미증명(`scripts/harness/hooks/researcher-task.sh:9-11` 과 같은 전제) · 새 hook 정의면 `/hooks` 재신뢰(그룹 T).
  - ⓒ hook 는 Codex 전용(env)으로 두고 `SKILL.md:101` · `:106` · `dual-agent.md:60` 을 `--scope` 절차(인계 시점 차단)로 고침(초안 H3 ⓑ).
- 권장: ⓐ + ⓒ 의 문장 정리(H14 분리 포함, 초안 H3 ⓒ 에 해당) — 단계 구분이 task 경계(시험 작성 task / 구현 task)로 이미 표현됨(`lifecycle-evidence.md:87-98`). 편집 시점 차단을 새 hook 정의 없이 얻음. 실패 면은 Edit/Write 한정(Bash 로 복구 가능).
  - 전제·미검증: lane-worker task 에 `agent_id` 가 기록되지 않음(`lane-worker.md:35-38` begin 에 `--agent-id` 없음 · 기록 자리 `scripts/harness/hooks/lifecycle_contract.py:245`) → task 는 checkout 키로 찾음. lane 이 부모 checkout 에서 돈 관측 1회(R2-2) · 같은 checkout 에 이전 미인계 task 가 남은 경우 오차단 가능 → 「열린 task」 정의를 PR 2(task close/GC)와 맞춤. Workflow `agent()` 로 스폰한 lane 에서 PreToolUse hook 실행 여부 미검증.
- 완료 기준:
  - unittest ⑴ `COLAB_FIX_LANE` 없이 scope `frontend/src/**` 인 lane-worker task + `agent_id` 있는 Edit payload → `frontend/test/…` · `gates/…` · `contracts/…` rc=2, `frontend/src/…` rc=0 ⑵ scope 에 `frontend/test/**` 가 든 task → 시험 경로 rc=0 ⑶ `agent_id` 없는 payload · scope 미선언 task → rc=0 ⑷ 기존 env 시험(`test_agent_bridge.py:509-512` · `:537-540` · `test_harness_lifecycle_contract.py:394`) green.
  - `SKILL.md:101` 두 문장 분리. `:101` · `:106` · `dual-agent.md:60` 이 실제 arm 조건(env 또는 scope 선언 task)과 인계 시점 검사를 기술.
  - 실제 Claude lane-worker 1회 실측: 구현 단계 task 에서 시험 파일 Edit 가 편집 시점에 차단(초안 H3 「모을 증거」 대체).
- 판정 질문: ⓐ(편집 시점 · scope 기반)로 갈지, ⓒ(문장만 · 인계 시점 차단 유지)로 PR 1 을 줄일지?

### A3 Edit/Write guard 는 Bash 쓰기를 보지 않음 — 경계 표기  (출처: R1-7)
- 문제: migration-guard · decision-number-guard · test-file-guard 는 `Edit|Write` matcher 에만 등록(`.claude/settings.json:68-84`). git-guard 는 git/gh 만 판정(`git-guard.sh:181` · `:188`). `sed -i` · redirect · python 쓰기는 세 guard 를 거치지 않음. `README.md:116` 은 「마찰 장치이지 보안 경계가 아니다」를 `bash -c` 감싸기 예로만 적고 Bash 쓰기 경로는 적지 않음. 사용자 메모리(저장소 밖)는 Edit 차단 시 Bash 로 쓰도록 안내.
- 선택지: ⓐ 경계 표기 — README hook 절 · 세 guard 머리말에 「Edit/Write 도구만 대상 · Bash 쓰기는 대상 아님 · 사후 검사 수단」 명시 ⓑ PreToolUse(Bash)에서 쓰기 형태(`sed -i` · `>` · `tee` · `python -c`) × 보호 경로 대조 — 형태 열거 불완전 · 오탐 면 증가 · fail-closed 면이 git-guard 와 같음 ⓒ PostToolUse(Bash)에서 보호 경로 변경 감지 — 실행 후라 차단 불가, 안내만.
- 권장: ⓐ — scope 선언 task 의 handoff/H7 대조는 begin 시점 파일 전체 내용 hash 기준이라 Bash 쓰기도 드러남(`lifecycle-evidence.md:92` 문서 근거). ⓑ 는 A1 의 fail-closed 면을 키움. migration · 결정 번호의 Bash 편집에 대한 사후 검사 수단 유무는 이 초안에서 미확인 → 표기 전에 확인해 「있음/없음」으로 적음.
- 완료 기준: `README.md` hook 절과 세 guard 머리말에 대상 도구 · 비대상 경로 · 사후 검사 수단(없으면 「없음」)이 적히고 harness-contract gate green. 코드 변경 0.
- 판정 질문: 권장안 수용?

### A4 `gates/run.sh` 여분 인자 무시 · 알 수 없는 gate 가 mutex 를 잡은 뒤 exit 2  (출처: R3-5 · R5-6 정정(medium) · R3-9 일부 · H7)
- 문제:
  - `gates/run.sh:9` `GATE="${1:-}"`, `$#` 검사 없음 → `run.sh a b c` 는 a 만 실행하고 b · c 를 말없이 버린 뒤 a 의 exit code 반환(초안 H7 의 「exit 0」 은 부정확). task 결합 경로도 `$GATE` 만 전달(`:52`). `all` 은 `$2` 가 정확히 `-j` 일 때만 병렬도를 읽음(`:795`) → `all -j4` · 뒤 토큰은 말없이 -j 2.
  - 알 수 없는 gate: 미선언 gate 는 serial 취급(`:787-788`) → host mutex 획득(`:163-170`) 뒤 dispatch 에서 exit 2(`:975-977`). 인자 없음도 exit 2(`:971-973`). 2 는 0/1/78 밖(AGENTS.md), 요약기는 red_판정으로 셈(R3-9). 측정 관측 1회: 오타 gate 이름이 mutex 획득 뒤 exit 2(advisor2 §2) — 코드 경로 재확인.
  - 저장소 안 호출부 중 gate 이름을 둘 이상 넘기는 곳 0건(R5-6 정정 · git grep) → 노출은 에이전트 · 사람의 수동 실행.
- 선택지: ⓐ 인자 검사를 mutex · task 결합 앞에 둠 — 단독 gate = 인자 1개, `all` = 없음 또는 `-j <양의 정수>`, `task` = 추가 인자 없음. 위반 · 빈 인자 · 알 수 없는 gate → 버린 토큰/이름을 stderr 에 적고 78 ⓑ 여러 gate 순차 실행 허용 + 집계 exit code(초안 H7 선택지) — 집계 우선순위(R3-9 나머지, PR 2)와 얽힘 ⓒ ⓐ 와 같되 알 수 없는 gate 는 1(판정 실패).
- 권장: ⓐ — 「환경·입력 부재로 판정할 수 없는 준비 실패 = 78」(AGENTS.md)과 일치. 새 집계 규칙 불필요. 다중 인자 호출부 0건이라 호환 부담 없음.
- 완료 기준: 시험이 ⑴ `run.sh a b` · `run.sh all -j4` · `run.sh all -j 4 x` · `run.sh task x` → 78 + stderr 에 버린 토큰 ⑵ `run.sh no-such-gate` · 인자 없음 → 78, host mutex 획득 기록 0 ⑶ 단독 gate · `all -j N` · `task` 기존 동작 무변경을 보임. exit 2 에 기대는 기존 시험 · 도구 0건 확인(`scripts/tests` 3파일 grep 0건 — 전수 아님, `gates/tools/*selftest*` 는 spec 단계에서 확인).
- 판정 질문: 권장안 수용? (알 수 없는 gate 를 78 로 볼지 1 로 볼지)

### 그룹 A 공통 · 범위 밖
- 커밋 단위: A1 은 단독 커밋(되돌림 단위). A2–A4 는 파일이 겹치지 않아 각 1커밋.
- 전제: 권장안은 `.claude/settings.json` · `.codex/hooks.json` 훅 정의를 바꾸지 않음. 바뀌는 선택지(A2 ⓑ 등)를 고르면 `/hooks` 재신뢰가 그룹 T 로 추가됨.
- 범위 밖:
  - R1-17 reseed ACK 할당 검사(`git-guard.sh:134`)의 따옴표 · `read` · `printf -v` · Write 경로 누락 — 머리말(`:131-133`)이 보안 경계 아님을 명시. A1 tokenizer 가 인용 제거 뒤 토큰을 보면 `export "…"` 형태가 같이 잡힐 수 있으나 완료 기준에 넣지 않음.
  - 한 겹 감싼 명령(`bash -c` · `eval`) — 머리말 `:74-76` 알려진 한계 유지.
  - exit code 우선순위 불일치(R3-9 나머지: lifecycle run_gates 의 78 우선 · `all` 이 78 을 내지 않음) → PR 2.
  - decision-number-guard 기준 ref `origin/main`(`decision-number-guard.sh:67`)이 로컬에 없음(`git rev-parse` rc=1, 2026-09-25) → 항상 워킹트리 폴백(`:69-72`). `README.md:74-75` 는 두 guard 기준을 `origin/main` 으로 적으나 migration-guard 코드는 `origin/develop`(`migration-guard.sh:72`) → PR 3 후보.
  - develop required checks · ruleset · `/hooks` 재신뢰 → 그룹 T(Ted).
