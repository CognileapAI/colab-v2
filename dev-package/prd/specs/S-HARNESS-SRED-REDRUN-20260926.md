# Spec: 하네스 개선 — phase S-red (소형 PR · red-run: 실패 시험 고정 · fix 레인 편집 차단 · 인계 시 GREEN·blob 대조)
출처 intent: `dev-package/intent/2026-09-25-harness-improvement.md`
출처 절: 7라운드 Q-B ⓐ(red-run 소형 PR 을 PR 2 앞에 · 「선언한 실패 시험 blob digest 고정」) · 6라운드 격차 ②(RED 시험 고정 · Claude 미적용 · `green-by-edit`) · A2 ⓐ(`:112-116` 편집 시점 차단 · PR 2) 의 fix 레인 부분 선행. 근거(저장소 밖): `~/.claude/reports/harness-state-20260925/playbook-gap-20260926/direction.md` 격차 2 · `system-first-recut/recut.md` 2-8(PR 2 · `test-file-guard.sh` 본문 확장) · 2-4(L1 · `handoff --mode blocked`) · gate-1 판정 `master-plan-20260926/verify-e0-sred.md`(차단급 1 · 개선 3 반영). 총괄 = `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md` §2 S-red · T 번호는 총괄 Ted 행동표(T12 실측 · T16 게시 · T18 fix 레인 실측 지시).
순서: E0 병합 뒤 착수 · PR 2 전 병합(7라운드 `:609` · 대안 「S-red → E0」 는 총괄 §6 Q2 · E0 spec 우려 #6 · Ted — 이 문서는 E0 → S-red 기준). 줄 번호 기준 = 브랜치 `claude/harness-improvement` HEAD `27f7fb6c`(PR 1 병합 · 2026-09-26 재열람). 트레일러 규칙 = E0 와 같다. 훅 정의(`.claude/settings.json:68-83` `Edit|Write` matcher · `.codex/hooks.json:77-103` `apply_patch`) 무변경 → `/hooks` 재신뢰 0.
단위 규칙 = E0 spec 머리와 같다(⑴ 강제 기제 ⑵ 시험 ⑶ 병합 조건 ⑷ 지우는 산문 ⑸ 소유 PR = S-red · 장치 없는 단위는 「산문 · 맥락만」).

## 1. 문제 진술
- 편집 시점 차단이 Claude lane 에 없다: `scripts/harness/hooks/test-file-guard.sh:42` `COLAB_FIX_LANE=1` 부재 → python 전에 exit 0. env 를 넘기는 곳은 Codex 경로(`scripts/agent-bridge.py:277-279` Windows 중계 · `scripts/dev.ps1:102`)뿐 · Claude Code 는 hook env 를 lane 별로 못 준다(머리말 `:26-27` · PR 1 A2 ⓒ 문서화 완료). 남은 것은 인계 시점 scope 대조(`lifecycle_contract.py:403-427`)인데 fix 레인의 scope 에는 시험 경로가 들어가므로(`design-review/SKILL.md:107`) 시험 편집을 구분하지 못한다.
- RED 증거가 산문이다: `.agents/roles/lane-worker.md:44` 「red 를 실제로 확인 · red 로그 한 줄을 보고에 인용」 — 기계 기록 0 · 인계는 red 로그를 보지 않는다(`stop()` `:400-428` · `verify_task_report` `:328-347`).
- 인계가 「시험을 고쳐 만든 green」을 구분하지 못한다: `validate_report(:287-315)` 는 필수 게이트 ⊆ 행 · 계수 · red 0 만 본다. 시험 파일 내용 변화는 scope 안이면 통과.
- 종료 기록이 없어 「열린 task」를 정의할 수 없다(L1 · `:600-609` handoff 는 task.json 에 쓰지 않음) → 편집 시점 차단이 어느 task 를 볼지 정할 수 없다(A2 ⓐ 전제).

## 2. 원한 결과 (V-id)
- V-S1 `lifecycle begin --role lane-worker --fix --red <path>[::case]`(반복 가능)가 시험을 실제로 실행해 rc 1(실패)일 때만 task 를 열고, `task.json.fix.red[]` 에 `spec · path · case · blob(git hash-object) · runner · rc · output_sha256 · log` 를 기록한다 · rc 0(이미 green) · rc ∉ {1}(수집 오류 등) · 미지원 경로 · `--fix` 없이 `--red` · `--red` 없이 `--fix` · researcher/measurement-lane · `--legacy` → 78 + 사유 — 확인: `scripts/tests/test_task_runtime.py` ①–④.
- V-S2 fix task 가 열린 checkout(같은 git common dir · `handed_off` 없음 · checkout 경로 실존)의 기록된 red 경로에 대한 Edit/Write → `test-file-guard` exit 2 · 대조 기준 = `file_path` 가 속한 checkout(env 무관 · `agent_id` 무관 · payload `cwd` 무관 · `COLAB_ALLOW_TEST_EDIT` 무관 · 부모 세션이 lane worktree 의 잠금 경로를 고쳐도 차단) · 다른 경로 · 인계 뒤 · 다른 checkout 의 자기 파일 → 기존 동작 — 확인: `scripts/tests/test_harness_lifecycle_contract.py` 새 클래스 ⑩(a–j) · Codex 경로 ⑫.
- V-S3 `gates/run.sh task`(`run_gates`)가 선언 게이트 뒤 red 항목마다 행 `fix-red:<spec>` 을 낸다: blob 불변 ∧ rc 0 = green · blob 변경 = red_판정(실행 안 함) · rc 1 = red_판정 · 그 외 = red_준비 — 확인: ⑤–⑦.
- V-S4 `handoff --mode complete` / SubagentStop H7 는 `fix-red:*` 행 전부 green(필수 집합에 포함) ∧ 현재 blob == 기록 blob 일 때만 통과 · 위반 사유에 출구 명기 — 확인: ⑥–⑧.
- V-S5 CLI handoff 성공 시 `task.json.handed_off = {mode, run_id, at}` 기록(L1 「인계됨」 절반 · 「닫힘」·prune 은 PR 2) · red-locked 마커 제거 — 확인: ⑨.
- V-S6 fix task 없는 세션의 Edit/Write 비용: python 호출 수 불변 · fork +2(git · ls) · 증가 < 10 ms/회 — 확인: ⑩-f(마커 없음 + env 없음 → exit 0 · stderr 빈 문자열) + V-S6 `time`.
- V-S7 문서: `lifecycle-evidence.md` 「fix 레인」 절(정본) · `design-review/SKILL.md:101-102,107` · `dual-agent.md:59-60` · `lane-worker.md:44` · `test-file-guard.sh:12-14,23-29` 가 포인터/현 동작으로 교체 · 「Claude = 편집 시점 차단 없음」 문장 0건.
- V-S8 기존 시험 green(`test_harness_lifecycle_contract.py:319-327` · `:431` · `test_agent_bridge.py:559-567` · `test_task_runtime.py` 전부) · Codex `agent-bridge check` green · 훅 정의 diff 0.
- V-S9 harness-eval 면제 게이트 green — hook 본문 변경이라 E0 규칙상 S-red 최종 설정 해시의 실측 1회 필요(Q-A ⓐ 확정 · T12 · 면제 선택지 없음).
- V-S10 병합·pull 뒤 첫 fix 레인 1회에서 hook exit 2 실측(T18).

## 3. 해법 개요
- `lifecycle_contract.py`: begin `--fix/--red` · RED 러너 표 · `run_gates` 행 추가 · `verify_task_report`/`stop` 대조 · handoff 「인계됨」 기록 · `red-locked` 하위 명령. `task_state.py`: 로그 결속 · 마커 디렉터리. `test-file-guard.sh`: bash 마커 검사 → 잠금 경로 차단 분기(`:42` 앞 · `file_path` 기준 checkout). 문서 5곳. 훅 정의 0.
- PR 2 2-8 과의 경계(중복 금지): S-red = 「fix task · 기록된 red 경로」 차단 + 「인계됨」 기록 + `red-locked` 조회 헬퍼. 2-8 ⓐ(lane + 부모 checkout/보호 브랜치) · ⓑ(researcher WATCH 밖) · ⓒ(scoped task + 보호 경로 4종 scope 밖) · ⓓ(fix task 의 보호 경로 4종 · `:42` env 검사와 OR 한 분기) 은 같은 헬퍼(`open_tasks(root)`)와 같은 `handed_off` · `fix` 필드를 읽어 분기만 추가한다. 2-4 `handoff --mode blocked` 는 `handed_off.mode = blocked` 를 써서 red 잠금을 푼다(버려진 fix task 의 출구). `COLAB_AGENT_TYPE` env 는 `agent-bridge.py` 에 없고(grep 0) S-red 는 필요 없다(checkout 결속 · 신원 무관) → 2-8 이 역할 분기 때 도입.

## 4. 구현 결정

### 4.1 begin `--fix --red` (단위 S-1)
- 파일 `scripts/harness/hooks/lifecycle_contract.py` — `begin()` `:210` 시그니처에 `fix=False, red=()` · 검증(`:213-217` 뒤): `fix` ∧ role ≠ `lane-worker` → `ValueError('fix lane requires --role lane-worker')` · `fix` ⊻ `red` → `'--fix requires --red <path>[::case]' / '--red requires --fix'` · `legacy` ∧ `fix` → `'fix lane requires the colab-task/2 runtime; drop --legacy'` · 중복 spec → `'duplicate task declaration'`(`:232-233` 동일 문구).
- spec 해석: `path[::case]` · `path` 는 저장소 상대 POSIX(`check_scope_declarations` `:85-87` 와 같은 거절 규칙 재사용 · 와일드카드 금지) · 파일 실존 필수(`(root/path).is_file()`).
- 러너 표 `RED_RUNNERS`(모듈 상수 · 접두 → (cwd, argv 빌더) · 1곳): `scripts/tests/*.py` → cwd root · `[sys.executable, '-m', 'unittest', <path>]` + case 있으면 `['-k', <case>]`(`gates/run.sh:351` 과 같은 경로 인자 형식 · `scripts/tests` 패키지 가정 없음) · `frontend/test/**` → cwd `frontend` · `['node_modules/.bin/vitest', 'run', <rel path>, ('-t', case)?]`(`package.json:12` `vitest run`) · `services/<svc>/tests/**` → cwd `services/<svc>` · `['.venv/bin/python', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', <rel>[::case]]`(`gates/tools/service-tests.sh:65,205` 동일 인터프리터·옵션) · `gates/tools/*-selftest.sh` · `eval/harness/tests/*.sh` → cwd root · `['bash', path]`(case 불가). 그 외 → `ValueError('red-run: no runner for <path> — supported: …')`.
- RED 실행: `subprocess.run(argv, cwd, capture_output, timeout=900)` · rc == 1 → RED(unittest 실패/오류 · pytest 실패 · vitest 실패 모두 1) · rc 0 → `'red-run: <spec> is already green — a RED must fail before the fix'` · rc ∉ {0,1}(pytest 2/4/5 = 중단·usage·수집 0 · 인터프리터 부재 127) → `'red-run: <spec> did not run as a test (rc <n>) — readiness, not RED'` · Timeout → 같은 부류. 모두 `:611-613` 경로 78.
- 기록(`:244-247` task dict 에 `fix=dict(red=[…], recorded_at=<utc iso>)`): 항목 = `spec · path · case · blob`(`git -C root hash-object -- path` · 미추적도 계산됨) · `runner`(argv) · `cwd` · `rc` · `output_sha256`(stdout+stderr) · `log`(`<task dir>/red/<i>.log` 절대경로). 저장 순서: `runtime().save` 뒤 task 디렉터리(`task_state.directory` `:49-51`)에 `red/` 생성 · 로그 기록(`confined` 경유). 마커: `task_state.marker_dir(root)` = `<git-common-dir>/colab-harness/red-locked/` · 파일 `<task_id>` 내용 = `record_path`. CLI: `:542-550` 에 `--fix`(store_true) · `--red`(append) 추가 · `:580` 인자 전달.
- 강제 기제: lifecycle CLI(begin 이 거절 · 78) · Claude/Codex 공통(`agent-bridge.py:384-385` lifecycle 위임) · fail-closed(러너 실패 = 78 · task 미생성).
- 시험(`scripts/tests/test_task_runtime.py` · `TaskRuntimeTests` fixture `:18-26`): ① fixture repo 에 `scripts/tests/test_probe.py`(실패 1건 + 통과 1건) → `begin --fix --red scripts/tests/test_probe.py::ProbeTests.test_fails` → task.json `fix.red[0].blob == git hash-object` · `rc == 1` · 로그 파일 존재 · 로그에 `Ran 1 test` + `FAILED`(`-k` 로 1건만 red 인지 단언) · 마커 파일 존재 ② 통과하는 시험 → 78 + 'already green' ③ `--red` 만 · `--fix` 만 · `--role researcher --fix …` · `--legacy --fix` → 78 각 문구 ④ `--red docs/x.md` → 78 'no runner' · `--red scripts/tests/missing.py` → 78. 실행 게이트 = `agent-bridge`(`run.sh:351`).
- 병합 조건 = `agent-bridge` 게이트 green(①–⑫) ∧ V-S9 · 지우는 산문 = 없음(S-5 가 포인터 편집).

### 4.2 `run_gates` 행 · 인계 대조 (단위 S-2)
- `task_state.bind_paths` `:82`: logs 를 `task['gates'] + fix 행 이름` 수만큼 결속(행 로그 `logs/<n>.log` 연속 번호) — resolver 허용 목록(`:90-92`)에 자동 포함.
- `run_gates` `:466-481` 루프 뒤: `for entry in task.get('fix', {}).get('red', [])` → 이름 `fix-red:<spec>` · 현재 blob ≠ 기록 blob → `state='red_판정' · exit=1 · readiness=None` · 로그에 `recorded RED test changed: blob <a> → <b>` (실행 안 함) · 같으면 러너 실행(4.1 표 · 같은 argv) → rc 0 green · rc 1 red_판정 · 그 외 red_준비(`readiness='red-run: rc <n>'`) · 로그 기록 · stdout 에 출력. `counts` · `targets.selected`(`:485`)는 선언 게이트 그대로 · 행만 추가. `:500` 종료코드 규칙 그대로(red 행 → 1/78).
- `verify_task_report` `:335`: `validate_report(data, task['gates'] + fix_rows(task), …)` → 행 부재 = `'required gates are missing'`(`:312-313`) · red 잔존 = `'gate failures remain'`(`:314-315`). 추가 `verify_red_locked(root, task)`: 각 항목 현재 blob == 기록 blob 아니면 `ValueError('recorded RED test changed: <spec> (blob <a> → <b>) — exits: (1) restore the test file to the recorded blob and rerun gates; (2) if the test itself was wrong, hand this task off as blocked (PR 2) or let the parent begin a new task with a re-approved --red')`. 호출 위치 = `stop()` `:428` `verify_task_report` 직전(CLI handoff · SubagentStop hook `lane-gate-summary.sh` 양쪽 경유).
- 강제 기제: `gates/run.sh task`(`run_gates` `:455-500`) + H7(`lane-gate-summary.sh` SubagentStop `settings.json:48-56` · Codex bridge SubagentStop `agent-bridge.py:325-329`) + CLI handoff · fail-closed(부재·변경·red 전부 거절 · 78/2) · Claude/Codex 공통.
- 시험(`test_task_runtime.py` · `:82-108` 실제 gate 실행 fixture 꼴 재사용): ⑤ ①의 task → 시험을 green 으로 만드는 제품 수정(fixture) → `run_gates` → 행 `fix-red:…` green → `handoff --mode complete` 0 → `task.json.handed_off.mode == 'complete'` · 마커 부재 ⑥ 시험 여전히 red → 행 red_판정 · exit 1 · handoff 78 `'gate failures remain'` ⑦ 시험 파일에 `pass` 로 바꿔 green(blob 변경) → 행 red_판정 + 로그 `recorded RED test changed` · handoff 78 같은 문구 · 파일 복원 뒤 재실행 → green ⑧ 손으로 만든 report(fix 행 없음 · 나머지 green) → `verify_task_report` `'required gates are missing'` ⑨ `red-locked --checkout <root>` 출력 = ①뒤 `{"paths":["scripts/tests/test_probe.py"],"tasks":[<id>]}` · ⑤뒤 `{"paths":[],"tasks":[]}` · 마커만 남기고 task.json 에 `handed_off` 넣은 경우 → 빈 목록 + 마커 자동 제거 · task.json 부재 마커 → 무시·제거. 실행 게이트 = `agent-bridge`.
- 병합 조건 = `agent-bridge` 게이트 green(①–⑫) ∧ V-S9 · 지우는 산문 = `lane-worker.md:44`(지목 · 편집은 S-5).

### 4.3 `test-file-guard.sh` 잠금 경로 차단 (단위 S-3 · 정의 무변경)
- 삽입 위치 = `:42` 앞(recut 2-8 「l.42 앞」과 같은 자리 · 2-8 은 이 블록 뒤에 역할 분기를 더한다).
  ```
  # red-locked fast path — bash only; python runs only when a fix task is open.
  LOCKED=1
  if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
    COMMON="$(git -C "$CLAUDE_PROJECT_DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
    if [ -n "$COMMON" ] && [ -z "$(ls -A "$COMMON/colab-harness/red-locked" 2>/dev/null)" ]; then LOCKED=0; fi
  fi
  if [ "$LOCKED" = 0 ] && [ "${COLAB_FIX_LANE:-}" != "1" ]; then exit 0; fi
  ```
  `CLAUDE_PROJECT_DIR` 부재(Claude 는 항상 줌 · bridge 는 `:337` 에서 ROOT) → LOCKED=1 로 두고 python 판정(보수 방향). 부모 checkout 과 lane worktree 는 common dir 을 공유하므로 마커 색인은 하나. `:43` `COLAB_ALLOW_TEST_EDIT` 조기 exit 는 **env 분기 직전으로 이동**(잠금 판정보다 뒤) — 잠금은 사람 선언 env 로 풀리지 않는다(출구 = 인계 · PR 2 blocked · 부모의 worktree 제거).
- REL 계산(`:73-78`)을 `file_path` 기준으로(gate-1 차단급 3): `FTOP="$(git -C "$(dirname "$FP")" rev-parse --show-toplevel 2>/dev/null || true)"` · `[ -n "$FTOP" ] || FTOP="$TOP"`(대상 디렉터리가 아직 없는 Write 는 기존 cwd 기준 `TOP` 폴백) · `REL="${FP#"$FTOP"/}"`. 부모 세션이 `file_path=<lane worktree>/scripts/tests/x.py` 로 Edit 하면 payload `cwd` = 부모 checkout 이지만 FTOP = lane worktree 가 되어 잠금 대조가 성립한다(cwd 기준이면 REL 이 절대경로로 남고 task 도 checkout 불일치로 제외되어 exit 0 — 결함). 기존 보호 4종 case(`:81-87`)도 같은 REL 을 쓴다.
- `[ "$LOCKED" = 1 ]` 이면 `LOCKED_OUT="$(printf '%s' "$payload" | python3 "$(dirname "${BASH_SOURCE[0]}")/lifecycle_contract.py" red-locked --checkout "$FTOP")" || { echo 'hook readiness failure: red-locked lookup failed' >&2; exit 2; }` · `python3 -c` 로 JSON 의 `paths` 에 `REL` 포함 여부 → 포함이면 stderr `⛔ 차단(test-file-guard · red-run) — 이 checkout 의 열린 fix task <id> 가 기록한 RED 시험 <REL> 은 인계 전에 고칠 수 없다(blob <sha> 고정). 출구: 제품 코드를 고쳐 GREEN 을 만든 뒤 handoff --mode complete · 시험 자체가 틀렸으면 부모가 재승인한 --red 로 새 task(PR 2 뒤 handoff --mode blocked).` · exit 2. (python 호출은 기존 2회 + 잠금 상태에서 1회 → 잠금 없는 세션은 0 추가.)
- `red-locked` 하위 명령(lifecycle_contract.py `main()`): `--checkout <path>` → `checkout(path)` → `identity` key → 그 checkout 의 common dir `colab-harness/red-locked/*` 마커 → 각 task.json 로드(`load_task` · `task.checkout != <path>` 면 제외 · `checkout` 경로 부재면 마커 제거 · `handed_off` 있으면 마커 제거) → `{"paths": [...], "tasks": [...]}` JSON 1줄 · exit 0 · 예외 → stderr + exit 78(호출 hook 은 2 로 변환).
- 강제 기제: PreToolUse `Edit|Write`(`settings.json:68-83` 기존 등록) · Codex = bridge `dispatch_event` `:315-317` → `codex_payloads` `:246-267`(apply_patch → Edit 페이로드 · `cwd` 포함) → `registered_hooks('Edit')` `:59-73` → 같은 스크립트 · env `CLAUDE_PROJECT_DIR=ROOT`(`:337`) → 같은 fast path · fail-closed(python3 부재 · envelope 이상 · lookup 실패 = exit 2 · 잠금 상태에서만) · 비대상 = Bash 쓰기(`sed -i` 등 · A3 경계 유지 · 인계 blob 대조가 잡는다).
- 시험(`scripts/tests/test_harness_lifecycle_contract.py` 새 클래스 `RedLockedGuardTests` · `:431` hook 직접 호출 꼴 · env 에 `CLAUDE_PROJECT_DIR=self.root`): ⑩-a fix task 열림 + Edit payload(`agent_id` 없음 · env 없음) 잠금 경로 → 2 + stderr 'red-run' ⑩-b 같은 상태 `COLAB_ALLOW_TEST_EDIT=1` → 2 ⑩-c 잠금 경로 아닌 `frontend/test/x.test.ts` · env 없음 → 0(잠금은 기록 경로만) ⑩-d 같은 경로 `COLAB_FIX_LANE=1` → 2(기존 보호 4종 · 문구 기존) ⑩-e handoff 뒤 → 0 ⑩-f 마커 없음 + env 없음 → 0 · stderr '' ⑩-g 잠금 상태 + `{broken` payload → 2 ⑩-h 다른 worktree(`git worktree add` · fix task 없음)의 cwd 에서 그 worktree 자기 파일의 같은 REL → 0(checkout 결속) ⑩-i `CLAUDE_PROJECT_DIR` 제거 + 마커 없음 → python 경로 → 0 ⑩-j cwd = 부모 checkout · `CLAUDE_PROJECT_DIR` = 부모 · `file_path` = lane worktree(`git worktree add` · 그 안에 fix task 열림)의 잠금 경로 절대경로 → 2(`file_path` 기준 checkout 대조 증명). ⑫ Codex: `test_task_runtime.py:390-410` 복사 fixture(`agent-bridge.py` 포함) 에서 `codex-event` PreToolUse `apply_patch` Update File <잠금 경로> → rc 2 · stderr 'test-file-guard'(`:559-567` 꼴 · env `COLAB_FIX_LANE` 없이). 기존 `:319-327` 4 hook malformed 시험 green 유지(잠금 없음 · env 1 경로). 실행 게이트 = `agent-bridge`.
- 병합 조건 = `agent-bridge` 게이트 green(①–⑫) ∧ V-S9 ∧ V-S6 · 지우는 산문 = `test-file-guard.sh:12-14,23-29`(편집은 S-5).

### 4.4 handoff 「인계됨」 기록 (단위 S-4 · L1 첫 단)
- `main()` `:600-609`: `stop(...)` 통과 뒤 `task['handed_off'] = dict(mode=args.mode, run_id=task.get('run_id'), at=<utc iso>)` · `runtime().save`(colab-task/2) / `task_path(...).write_text`(legacy) · 마커 제거(`fix` task). SubagentStop hook 경로(`stop` 하위 명령)는 쓰지 않는다(판정 전용 · L1 「닫힘」이 PR 2 에서 담당). 옛 스키마 task(`handed_off` 키 없음)는 「열린 fix task」 대상이 아니다(`fix` 키가 없으므로 자동 제외 — L2 「옛 스키마 제외」와 같은 방향).
- 강제 기제: 기록(판정 아님 · S-3 잠금 해제와 `red-locked` 조회의 입력) · 시험 ⑤ · ⑨ · PR 2 2-4 가 `blocked` 값 추가.
- 병합 조건 = 시험 ⑤ · ⑨ green(`agent-bridge`) · 지우는 산문 = 없음.

### 4.5 문서 · 산문 (단위 S-5 · 「산문 · 맥락만」)
- `docs/development/lifecycle-evidence.md` 「인계」 절(`:71-98`) 뒤 새 절 「fix 레인」(정본): 명령 · 러너 표 · RED 조건(rc 1) · 기록 필드 · 편집 시점 차단(경로 · `file_path` 기준 checkout · 출구) · 인계 조건(행 green ∧ blob 불변) · `handed_off` 필드 · 미지원 경로 · Bash 쓰기 비대상(인계가 잡음) · 「마커 = 색인 · 판정 = task.json」 · PR 2 blocked 예정 1줄.
- `.agents/skills/design-review/SKILL.md:101-102` 3문장 → 「fix 레인은 `begin --role lane-worker --fix --red <시험>` 으로 연다 — RED 기록 · 편집 시점 차단 · 인계 시 GREEN·blob 대조(정본 `lifecycle-evidence.md` 「fix 레인」). Codex env 경로는 보조.」 · `:107` 「Claude = 편집 시점 차단 없음 … (편집 시점 차단은 PR 2 A2 ⓐ)」 → 「구현 단계 = `--fix` task(도구 무관)」 1구.
- `docs/development/dual-agent.md:59-60` → 「fix 는 `begin --fix --red` 로 RED 를 기록하고 `test-file-guard` 가 기록 경로를 막는다(Claude·Codex 동일)」.
- `.agents/roles/lane-worker.md:44` 「실패 테스트 — red 를 실제로 확인 … red 로그 한 줄을 보고에 인용」 → 「실패 테스트 — fix 과제는 `begin --fix --red <경로>` 가 RED 를 실행·기록한다(로그 = task runtime `red/`) · 보고 인용은 그 로그 경로」 · `:38` 끝에 「fix 과제의 시험 경로는 인계 전 편집 불가」 포인터 1구.
- `test-file-guard.sh:12-14`(「env 없으면 조용히 통과」) → 「두 조건: ⑴ 열린 fix task 의 기록 red 경로(도구·env 무관 · `file_path` 기준 checkout) ⑵ `COLAB_FIX_LANE=1` env 의 보호 4종」 · `:23-29` 경계 블록의 「Claude lane 에서는 통과(편집 시점 차단 없음)」 삭제 · Bash 쓰기 비대상 문장 유지.
- `README.md` A3 blockquote(hook 절): 「fix 레인(`begin --fix`)의 기록 RED 경로는 Edit/Write 시점에 차단」 1구(C2 표 삭제와 무관 · blockquote 유지 결정).
- 지우는 산문 0건 검사: `grep -n '편집 시점 차단 없음' .agents/skills/design-review/SKILL.md docs/development/dual-agent.md scripts/harness/hooks/test-file-guard.sh` 0.
- 강제 기제: 없음(문서) · 병합 조건 = V-S7.

## 5. 시험 결정 (TDD 순서)
1. `test_task_runtime.py` ①–⑨ 작성 → `bash gates/run.sh agent-bridge` RED(`--fix` 인자 없음 argparse 오류 · `red-locked` 미지원).
2. `test_harness_lifecycle_contract.py` ⑩-a…j · ⑫ 작성 → RED(⑩-a · ⑩-j 가 0 = 결함 관측).
3. 구현 커밋 ①(S-1 · S-4 · `red-locked` · task_state) → ①–④ · ⑨ GREEN · ②(S-2) → ⑤–⑧ GREEN · ③(S-3) → ⑩ · ⑫ GREEN.
4. 기존 시험 무변경 green 확인 · 시험 수 증가분 기록.
- seam: fixture repo(`:18-26`) · hook 직접 호출(`:431`) · tempdir 복사 fixture(`:400-410`) — 제품 hook 에 새 env seam 없음.

## 6. 위험 · 롤백
- fail-closed 면 확대: 잠금 상태에서 Edit/Write 마다 python 1회 추가 · lookup 실패 = exit 2. 잠금 없는 세션 = bash `git rev-parse` + `ls` 만(fork +2 · 수 ms). 마커 디렉터리 손상(수동 삭제) = fail-open(경로 차단만 사라짐 · 인계 blob 대조는 남음) → 문서에 「마커 = 색인 · 판정 = task.json」.
- 버려진 fix task 가 그 checkout 의 해당 시험 경로 편집을 계속 막는다 → 출구 = 부모가 worktree 제거(checkout 부재 = 무시) · PR 2 2-4 `blocked` · 차단 면은 기록 경로 1~n 파일뿐.
- RED 오판: unittest 는 ImportError 도 rc 1 → 「테스트 코드 오류」가 RED 로 기록될 수 있다(pytest 는 수집 오류 rc 2 → 78). 로그 · output_sha256 이 남아 리뷰에서 보인다 · 완화는 범위 밖.
- 인계 blob 대조는 fix 시험 파일 하나가 아니라 `fix.red[].path` 전부 · 같은 파일의 다른 case 추가(정당한 시험 확장)도 blob 변경 → 거절 → 새 task 로 재승인(의도 · 「시험 확장도 사람 승인」).
- 롤백 단위: 커밋 ③(hook)만 되돌리면 편집 시점 차단이 사라지고 인계 대조(②)는 남는다 · ②만 되돌리면 기록만 남는다.
- lane 자기 검증 한계: lane 의 Bash/Edit 는 `${CLAUDE_PROJECT_DIR}` 쪽 구버전 hook 이 판정(`worktree-setup.sh:31-38` 문서) → hook 검증은 시험 ⑩ 직접 호출 · 병합·pull 뒤 첫 fix 레인에서 실측(V-S10 · T18).
- E0 규칙: hook 본문 변경 → S-red 최종 설정 해시 실측 1회(≈32 USD · T12 · 면제 선택지 없음 · Q-A ⓐ 확정) 없으면 `harness-eval` 78 · 회차 뒤 해시 집합 파일 push 금지. 순서 대안(S-red → E0 · EXEMPT 창 · 총괄 §6 Q2)은 Ted 판정 · 이 문서는 E0 → S-red 기준.

## 7. 레인 지시 (PR S-red · lane-worker 1개)
- 스폰: `Agent(subagent_type: "lane-worker", isolation: "worktree")` · 기준 = E0 병합 뒤 develop · 첫 행동 `git merge --ff-only develop` · 부모 checkout 판정 정지 규칙 동일.
- begin: `python3 scripts/agent-bridge.py lifecycle begin --role lane-worker --gate agent-bridge --gate harness-contract --gate intent-ref --gate exec-bit --gate harness-eval --scope 'scripts/harness/hooks/lifecycle_contract.py' --scope 'scripts/harness/task_state.py' --scope 'scripts/harness/hooks/test-file-guard.sh' --scope 'scripts/tests/test_task_runtime.py' --scope 'scripts/tests/test_harness_lifecycle_contract.py' --scope 'docs/development/lifecycle-evidence.md' --scope 'docs/development/dual-agent.md' --scope '.agents/skills/design-review/SKILL.md' --scope '.agents/roles/lane-worker.md' --scope 'README.md' --scope 'eval/harness/results/**'`(S-red head 회차 커밋용 · T12). 이 레인 자체는 `--fix` 가 아니다(신규 기능 · 시험 먼저 작성이 정상 작업).
- 게이트: `COLAB_HARNESS_EVAL_EXEMPT=1 COLAB_TASK_ID=<id> bash gates/run.sh task` 1회 · 실측 결과 커밋 뒤(E0 규칙) · 호스트 단독 · 커밋 ⑤ 뒤 해시 집합 파일 변경 금지.
- 커밋 단위(각 트레일러): ① S-1 + S-4 + `red-locked` + `task_state.py` + 시험 ①–④·⑨ ② S-2 + 시험 ⑤–⑧ ③ S-3 hook + 시험 ⑩·⑫ + hook 머리말 ④ 문서 4곳(S-5) ⑤ `results/<run>/`(실측 · E0 규칙) — 되돌림 단위 = ③ · ②.
- 인계: `lifecycle handoff --task <id> --mode complete --summary '…'` · `COLAB_HANDOFF` · `WORKTREE= BRANCH=`. push · 게시(T16) · 병합(T13) = Ted.

## 8. 검증표
| V | 명령(worktree 루트) | 기대 | 완료 기준 |
|---|---|---|---|
| V-S1 | `COLAB_TASK_ID=<id> bash gates/run.sh agent-bridge`(①–④) · 수동: fixture 없이 `lifecycle begin --role lane-worker --gate agent-bridge --fix --red scripts/tests/test_task_runtime.py::TaskRuntimeTests.test_lane_without_scope_keeps_current_behavior` → 78 'already green' | green · 78 문구 | 4.1 |
| V-S2 | agent-bridge(⑩-a…j · ⑫) · 수동: 시험 ⑩-a 와 같은 payload 를 `bash .claude/hooks/test-file-guard.sh` 에 직접(fixture repo · `CLAUDE_PROJECT_DIR=<fixture>`) · ⑩-j 꼴로 부모 cwd + lane worktree file_path | 2 + 'red-run' 두 경우 · 마커 없는 실 repo 에서 임의 Edit payload → 0 · stderr '' | 4.3 |
| V-S3·S4 | agent-bridge(⑤–⑧) | 행 `fix-red:` 3상태 · handoff 78 문구 2종 · 복원 뒤 0 | 4.2 |
| V-S5 | 시험 ⑨ · 수동: `cat <task dir>/task.json \| python3 -c 'import json,sys; print(json.load(sys.stdin)["handed_off"])'` | `{mode, run_id, at}` | 4.4 |
| V-S6 | `time` 로 Edit payload 100회 hook 직접 호출(마커 없음) vs develop 기준 | python 호출 수 동일 · fork +2 · 증가 < 10 ms/회 | 4.3 |
| V-S7 | `grep -n '편집 시점 차단 없음' …3파일` · `grep -c 'fix 레인' docs/development/lifecycle-evidence.md` | 0 · ≥1 | 4.5 |
| V-S8 | `bash gates/run.sh agent-bridge`(전체) · `python3 scripts/agent-bridge.py check` · `git diff develop -- .claude/settings.json .codex/hooks.json` | green · green · diff 0 | 공통 |
| V-S9 | `COLAB_HARNESS_EVAL_EXEMPT=1 bash gates/run.sh harness-eval` | 0 + 일치 run id + 두 해시 동일(실측 뒤) | E0 규칙 |
| V-S10 | 병합·pull 뒤 오케스트레이터: fix 레인 1회 스폰(`--fix --red` 실제 red 과제 · T18) → 레인이 시험 파일 Edit 시도 | hook exit 2 관측 · intent 「확인」 기록(A2 ⓐ 「실제 Claude lane-worker 1회 실측」 대체) | 병합 뒤 |
| 공통 | `bash -n scripts/harness/hooks/test-file-guard.sh` · `bash gates/run.sh exec-bit` · `bash gates/run.sh intent-ref` | 0 | |

## 9. PR 본문 계획
- 파일 `~/.claude/pr-bodies/PR-BODY-harness-improvement-S-red.md` · `pr_contract.py … --mode draft` → 0 · 게시 = T16(Ted).
- 첫 줄: 「하네스 개선 S-red — fix 레인의 실패 시험을 begin 이 기록하고 hook 이 편집을 막으며 인계는 GREEN·blob 불변을 요구한다」.
- `Plan-Ref: dev-package/prd/specs/S-HARNESS-SRED-REDRUN-20260926.md`(총괄 `S-HARNESS-IMPROVEMENT-PLAN-20260926.md` §2 S-red) · 결정 = 러너 표 1곳 · RED = rc 1 · 잠금 = checkout 결속(`file_path` 기준 · 신원 무관) · 인계됨 기록(L1 첫 단) · 새 ADR 없음(lifecycle 증거 계약 확장 · ADR-0005 범위) · 검증 = V-S1–S9 표 + red→green 계수 · 남은 제약 = 버려진 fix task 출구(PR 2 2-4) · Bash 쓰기 비대상(인계가 잡음) · unittest ImportError = rc 1 · V-S10 은 병합 뒤 관측 · lane 은 자기 hook 을 라이브로 못 씀.
- 게시 뒤: Ted 병합(T13) → V-S10 관측(T18) → PR 2 착수(2-8 이 이 헬퍼 위에 분기 추가 · 2-4 가 `blocked` 추가).

## T-항목 (Ted · 번호 = 총괄 Ted 행동표)
| T | 행동 | 명령/UI | 기록 |
|---|---|---|---|
| T12 | S-red head 실측 실행 승인(≈32 USD) — 면제 선택지 없음(해시 집합 = Q-A ⓐ 확정) · 레인이 중첩 `claude -p` 를 못 돌리면 Ted 가 실행 | 대화 판정 · 실행은 E0 T12 와 같은 명령 | intent 「판정 기록」 · 「확인」(run id) |
| T16 | PR 게시 — 메인 세션 초안(`~/.claude/pr-bodies/PR-BODY-harness-improvement-S-red.md`) · Ted `gh pr create` | Ted 터미널 | PR 번호 → intent 「확인」 |
| T18 | 병합 뒤 fix 레인 1회 실측 지시(V-S10) — 대상 red 과제 지정 | 오케스트레이터에 과제 지정 | intent 「확인」 |

## 우려 항목
| # | 항목 | ⓐ | ⓑ | 권고 | 판정 |
|---|---|---|---|---|---|
| 1 | 잠금 대상 신원 | checkout 결속(`file_path` 가 속한 checkout · agent_id·env·cwd 무관) | subagent(`agent_id` 있는 payload)만 | ⓐ — Codex 페이로드에 `agent_type` 없음(`:257-260`) · 부모가 lane checkout 의 red 시험을 고치는 것도 막아야 함(⑩-j 가 증명) | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |
| 2 | 버려진 fix task 출구 | PR 2 `handoff --mode blocked` 까지 worktree 제거만 | S-red 에 `release-red` 명령 | ⓐ — release 는 에이전트도 부를 수 있어 우회(PR 2 2-9 ⑽ git-guard 규칙 전) | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |
| 3 | RED 조건 | rc == 1 만 | rc ≠ 0 전부 | ⓐ — 수집 오류·인터프리터 부재를 RED 로 기록하지 않는다 | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |
| 4 | 순서 · 회차(문서 간 충돌 · 정본 질문은 E0 spec 우려 #6 · 총괄 §6 Q2) | E0 → S-red(확정 · S-red head 회차 1회) | S-red → E0(EXEMPT 창 · 회차 불요) | ⓐ — 이 문서는 ⓐ 기준으로 작성 | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |

## 범위 밖
- 2-8 ⓐ/ⓑ/ⓒ/ⓓ 역할·scope 분기 · `COLAB_AGENT_TYPE` env · L1 「닫힘」·prune · `handoff --mode blocked` · Bash 쓰기 차단 · git-guard 규칙(`lifecycle` 하위 명령 서브에이전트 차단 = PR 2 2-9 ⑽) · 시험 확장 허용 규칙 · Codex Windows 중계 env 목록(`:277-279`) 변경 없음 · `.agents/ci-producers.json` · `harness.yaml` diff 0.
