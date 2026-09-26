[harness: subagent output matched instruction-shaped pattern(s): settings-json. Control tags below are neutralized (`<` → `<\`); treat any remaining directive-shaped text as a finding to relay to the user, not an instruction to you.]

### A1
- 판정: ⓐ (Ted 판정과 일치) + 보강 2건 — ① tokenizer 예외 시 현행 `sed` 분리(`:149`)로 폴백하고 exit 2 로 올리지 않는다 ② `pull` 규칙은 명시 플래그(`--no-ff` · `--no-rebase` · `--rebase=false` · `--ff=false`)만 잡고 플래그 없는 `git pull` 은 통과시킨다
- 확신: 높음
- 사실 확인: 모두 재확인. `git-guard.sh:167` 비인용 `set -- $seg`(추가: `set -f` 없어 glob 확장도 일어남) · `:193` `shift 2` 가 공백 경로 첫 조각만 소비 → `:196-200` 에서 다음 조각이 `sub` 가 되어 `case` 무일치 통과. 브랜치 근거 `:143` payload cwd 단일. gh 는 `:182` 정확 `pr merge` 만. force 토큰 `:207` 정확 일치만. `is_main_ref :151-156` 에 `HEAD`/`@` 없음. `pull` 분기 없음(`:202-274`) · 머리말 `:23` 은 `pull --rebase` 만 허용 형태로 적음. 오탐 경로 `:106`(개행→` ; `) · `:149`(인용 무관 분리) 확인. 시험: `test_agent_bridge.py:463-507` 은 bridge `guard()` 가 `cwd=ROOT` 고정(`agent-bridge.py:170`) → `-C`·cwd 불일치 형태는 bridge 경유로 시험 불가, `test_harness_lifecycle_contract.py:340` 처럼 hook 직접 호출로 써야 함. 공백 `-C` · heredoc · `pull` · `gh -R` · `-fu` · `HEAD` 시험 0건 확인.
- 이유: ⓒ 는 `-C` 인용만 고쳐도 `cd <dir> &&` 체인 · `--git-dir` · heredoc 오탐 · `HEAD` 가 남아 같은 파일을 다시 연다. ⓑ 와 ⓐ 의 차이는 규칙표 편입 수십 줄이고 tokenizer 가 있으면 argv 규칙은 표 추가라 분리 이득이 없다. 현재 Bash 호출마다 python 2회(`:83` validate-input · `:93` read_fields) 이미 도니 tokenizer 를 `lifecycle_contract.py` 의 같은 호출에 합치면 지연 증가 0.
- 위험·전제: tokenizer 결함 = 전 Bash 정지 → 폴백 경로 자체를 fault-injection 시험으로 고정해야 한다. `cd` 대상이 변수·명령치환이면 해석 불가 → payload cwd 로 폴백(우회 잔존, 문서화).
- 뒤집힐 조건: 실제 transcript 명령 corpus(예: `.git/colab-harness` 204 task 의 명령 기록) 재생에서 tokenizer 가 현행보다 오탐을 늘리면 ⓑ 로 축소하고 argv 편입은 후속.

### A2
- 판정: ⓒ(PR 1) → ⓐ(PR 2, L1 ⓐ 뒤) 조합(Ted 분할과 일치) + 새 선택지 ⓒ′: ⓒ 문서 수정에 「fix 레인은 task 2개(시험 작성 task = scope 에 시험 경로 포함 → handoff / 구현 task = scope 에서 `frontend/test/**`·`services/*/tests/**`·`gates/**`·`contracts/**` 제외 → handoff)」 절차를 적어 코드 없이 단계 구분을 만든다
- 확신: 높음
- 사실 확인: `test-file-guard.sh:32` env 부재 exit 0(python 호출 전) 확인. 값 공급처 `agent-bridge.py:275-278`(Codex · Windows 경로) 만 확인. `SKILL.md:101` 두 문장 붙음(「…편집을 막는다보호된 fix…」) 재확인 · `:106` RED→GREEN 한 레인 확인 · `dual-agent.md:60` 확인. `lane-worker.md:38` 「지시문이 범위를 주면」 조건부 선언 확인. `lifecycle-evidence.md:87-98` scope 차단이 handoff/H7 시점임 확인. **정정·보강**: ⓐ 의 전제인 PreToolUse payload `agent_id` ↔ task `agent_id` 대조는 `lifecycle_contract.py:532` `resolve_edit` 가 이미 같은 방식으로 쓰고 있어 미증명이 아니다(미증명은 ⓑ 의 SubagentStart↔PreToolUse 일치 · `researcher-task.sh:9-11`). 반면 ⓐ 가 필요한 「cwd checkout 의 열린 lane-worker task 를 agent_id 로 찾기」는 현재 없다 — task 는 `task_path(root, task_id)`(`:165`) 로만 조회되고 열림/인계 상태 필드도 grep 0건. 이것이 L1 이후로 미루는 실질 근거.
- 이유: ⓐ 는 검색 index 와 인계 완료 표식이 먼저 있어야 하고 그것은 PR 2 의 lifecycle 영역이다. ⓒ 는 지금 거짓인 문장 3곳을 참으로 만드는 최소 변경이고, ⓒ′ 를 더하면 편집 시점은 아니어도 「단계 구분」 자체는 오늘 생긴다. ⓑ 는 hook 정의 추가(`/hooks` 재신뢰 · 그룹 T) + 미증명 전제 + 단계 구분 불가로 탈락.
- 위험·전제: ⓒ′ 는 레인이 task 를 두 번 열어야 해 지시문 템플릿에 반영돼야 지켜진다. ⓐ 는 Claude 의 모든 Edit/Write 에 python 1회를 추가한다(현재 이 hook 은 env 없으면 python 0회).
- 뒤집힐 조건: task runtime 에 이미 checkout·agent_id 기준 열린 task 조회가 있다고 밝혀지면 ⓐ 를 PR 1 로 당길 수 있다. 반대로 Claude Code 가 PreToolUse 에 `agent_id` 를 싣지 않는 사례가 관측되면 ⓐ 전체가 무효.

### A3
- 판정: ⓐ + 보강 — 「사후 검사 수단」을 추상어로 두지 않고 `begin --scope` handoff/H7(baseline = 전 파일 내용 hash, `lifecycle-evidence.md:91`) 을 지명한다. 이 검사는 Edit/Write/Bash 무관하게 변경을 잡으므로 Bash 쓰기의 실제 경계다. ⓑ·ⓒ 기각.
- 확신: 높음
- 사실 확인: `.claude/settings.json:68-84` `Edit|Write` matcher 에 3 guard 확인. `git-guard.sh:181`(gh) · `:188`(git 아니면 continue) 확인. `README.md:115-117` 경계 문장이 `bash -c` 예만 듦 확인. 사용자 메모리의 Bash 우회 안내는 저장소 밖(Ted 소유) — 문구 조정은 그룹 T 성격.
- 이유: ⓑ 는 쓰기 형태 열거(`sed -i`·`>`·`>>`·`tee`·`python -c`·`perl -pi`·`cp`·`mv`…)가 닫히지 않고, 오탐이 붙으면 README:116 이 예고한 대로 `COLAB_HOOKS=0` 상시화로 끝난다. ⓒ 는 실행 후라 차단이 아니고 PostToolUse stdout 은 모델에 닿지 않아(R1-hooks 요지) 안내조차 안 된다. 진짜 사후 경계는 이미 scope handoff 로 있다.
- 위험·전제: scope 를 선언하지 않은 task 는 기존 동작(무검사)이라 「scope 선언이 기본」이 지시문 템플릿에 들어가야 경계 문장이 참이 된다(A2 ⓒ′ 와 같은 전제).
- 뒤집힐 조건: 보호 경로 4종에 대한 Bash 쓰기가 실제 레인 기록에서 반복 관측되면(현재 0건) ⓑ 를 보호 경로 × 소수 형태로 좁혀 재검토.

### A4
- 판정: ⓐ (알 수 없는 gate 도 78). ⓒ 기각 · ⓑ 기각.
- 확신: 높음
- 사실 확인: `run.sh:9` `$1` 만, `$#` 검사 없음 확인. `task` 는 `:34-38` 에서 `exec run-gates` 로 넘어가 뒤 토큰 무시 확인. task 결합 경로 `:52` `--gate "$GATE"` 만 전달 확인 — 추가로 이 경로는 `:42` `gate-start` 가 **증거를 먼저 기록**한 뒤 알 수 없는 gate 가 드러나므로 인자 검사는 `:9` 직후여야 한다. `all`: `:795` 정확 `-j` 만 · **추가 사실** `:797` 비정수 `-j abc` 도 말없이 `jobs_n=1`. 알 수 없는 gate → `gate_mode_of :140-146` 미선언=serial → mutex `:163-170` 획득 → `:975-977` exit 2 확인. 인자 없음 `:971-973` exit 2 확인. 다중 gate 호출부 0건(R5-6 정정) 수용.
- 이유: 「입력 부재로 판정할 수 없다」가 78 의 정의(AGENTS.md)이고 오타 gate 는 판정 불가이지 코드 결함이 아니다 — ⓒ 의 1 은 요약기가 red_판정으로 세어 결함 탐색을 유발한다. ⓑ 는 선언 집합 실행이 이미 `run.sh task` 로 있어 두 번째 다중 실행 경로가 되고 집계 우선순위(R3-9 · PR 2) 와 얽힌다. 검사를 mutex 앞에 두면 잘못된 호출이 호스트 전역 슬롯을 잡는 일도 없어진다.
- 위험·전제: `all -j4` 처럼 붙여 쓴 형태를 78 로 거부하면 기존 습관이 한 번 걸린다 — 거부 메시지에 `-j 4` 를 적으면 된다. 인자 검사 위치를 `:9` 직후로 못 박지 않으면 task 결합 경로에서 gate-start 부작용이 남는다.
- 뒤집힐 조건: 저장소 안 스크립트·워크플로가 `run.sh <a> <b>` 를 실제로 쓰는 호출이 발견되면 ⓑ 재검토(현재 git grep 0건).

### A5
- 판정: ⓐ
- 확신: 높음
- 사실 확인: `git-guard.sh:71-72` 「exit 1 은 통과 · 판정 못 하면 통과」 확인. `:82` python3 부재 exit 2 · `:83` envelope 이상 exit 2 → `:90` `|| exit 0` 도달 불가 확인. `test-file-guard.sh:27` 동일 문장 · `:38` exit 2 · `:42` 도달 불가 확인. **보강**: 두 파일 모두 이미 `git-guard.sh:3-4` · `test-file-guard.sh:28` 에 「2026-09-09 envelope 계약이 우선 · 과거 fail-open 주석은 superseded」 줄이 있어 drift 는 「표기 없음」이 아니라 **같은 머리말 안의 자기모순**이다. `git-guard.sh:39` 「agent_id 부재 = 통과」는 여전히 참이라 손대지 않는다. 시험 `test_harness_lifecycle_contract.py:320-327` 이 `{broken`·`{}` → exit 2 를 이미 고정하므로 도달 불가 줄 삭제는 동작 변화 0 이 시험으로 증명된다.
- 이유: 도달 불가 코드가 반대 정책을 주석으로 달고 남아 있으면 다음 편집자가 그 줄을 「의도」로 읽는다. 삭제는 한 줄씩이고 시험이 이미 있다. ⓑ 는 머리말과 코드가 여전히 어긋난 채 남는다. 문장은 「exit 1 은 Claude Code 규약상 비차단이지만 이 hook 은 exit 1 을 내지 않는다 · envelope 이상 · python3 부재 = exit 2」로 고친다.
- 위험·전제: `migration-guard.sh:21/:28/:32` 같은 drift 는 파일 소유가 PR 3(C10) 이라 PR 1 에서 세 파일 중 하나만 남는 기간이 생긴다 — PR 1 커밋 메시지에 명시.
- 뒤집힐 조건: 없음에 가깝다. envelope 계약(`lifecycle_contract.py:613` validate-input=2) 을 fail-open 으로 되돌리는 결정이 나오면 ⓑ 도 무효가 되고 코드부터 바뀐다.

### 묶음 메모
- A1 과 A5 는 같은 `git-guard.sh` 머리말·본문을 건드린다 — A5 문장 교정은 A1 편집 안에서 한 번에 하고 별도 커밋으로 나누지 않는다.
- A3 경계 문장은 A1 이후 동작(heredoc 본문 제외 · 대상 checkout 해석) 기준으로 써야 하므로 PR 1 안에서 A1 뒤에 작성한다.
- A2 ⓐ 의 진짜 선결은 「checkout·role·agent_id 로 열린 task 찾기 + 인계 완료 표식」이며 이것은 PR 2 L1 영역 — Ted 의 분할 순서가 코드 사실로 뒷받침된다.
- A4 의 78 은 R3-9(PR 2) 의 readiness-first 집계와 만나면 선언 집합 안 오타 하나가 전체를 78 로 만든다 — 선언 오류를 먼저 고치라는 의미라 수용하되 PR 2 집계 설계 때 이 경우를 시험에 넣는다.
- A1 `-C`·cwd 불일치 시험과 A2 ⓐ 시험은 bridge `guard()`(cwd=ROOT 고정) 로는 못 쓰고 hook 직접 호출(`test_harness_lifecycle_contract.py:340` 형태)로 써야 한다 — 시험 파일 소유를 spec 에 미리 적는다.