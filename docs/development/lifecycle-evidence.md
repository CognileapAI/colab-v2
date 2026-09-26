# 작업별 시작·검증·인계 증거

Claude와 Codex는 `scripts/harness/hooks/lifecycle_contract.py`의 같은 판정을 사용한다.
이 계약은 작업 증거 검증이다. OS 쓰기 차단이나 증거 서명을 제공하지 않는다.
기존 H6의 모든 미추적 파일 차단과 H7의 mtime 선택·깨진 JSON/준비 실패 허용은
2026-09-09 승인된 동등성 수용 기준에 따라 아래 계약으로 대체한다.

## 시작

`researcher` 또는 `lane-worker` 역할의 작업은 수정 전에 지정 사본 루트에서 시작 기록을 만든다.
이 역할 계약을 일반 부모 문서 작성자의 권한으로 해석하지 않는다. 부모가 승인된 intent로 spec을
직접 작성할 때 `researcher`로 가장해 등록하지 않는다. `dev-package/prd/specs/`는 감시 경로 안의
산출물이며, 쓰는 주체는 부모다. researcher는 `colab-task/2`에서도 `begin --legacy`에서도 이 경로를
산출물로 선언하지 못하고, 선언하면 시작 시점에 거절된다. 감시는 신규 추가만이 아니라 수정까지 본다.
다만 훅이 발화하는 자리는 researcher 종료뿐이므로, 사람이나 부모가 spec을 손으로 고치는 것은 훅 대상이
아니다. 부모의 spec 인계는 승인 범위·파일 경로·실제 내용 hash를 확인한다 — 이 확인은 현재 사람의
절차이며 기계 판정으로 구현돼 있지 않다.
Windows에서는 `scripts/dev.ps1 bridge lifecycle <인자>`로 같은 WSL 경로를 쓴다.
Linux에서는 `python3 scripts/agent-bridge.py lifecycle <인자>`다.
신규 `colab-task/2` 기록과 산출물은 Git common 디렉터리의
`colab-harness/<checkout-id>/<task-id>/<run-id>/`에 보관한다. checkout-id는 사본 경로와 private Git 경로에 결합된다.
작업 기록 `task.json`은 task-id 디렉터리에 두며, 제품 파일을 만들지 않는다.
기존 private Git의 `colab-task/1` 기록은 명시 호환 읽기를 유지한다.
기존 저장소 출력 방식의 새 호출이 꼭 필요하면 `begin --legacy`를 명시한다. 자동 fallback은 없다.

```bash
python3 scripts/agent-bridge.py lifecycle begin --role researcher
python3 scripts/agent-bridge.py lifecycle begin --role researcher --agent-id <실제-agent-id> --artifact runtime:artifacts/new-draft.md
python3 scripts/agent-bridge.py lifecycle begin --role lane-worker --gate contract-lint
```

위 명령은 서로 다른 작업 예시다. 자신의 작업에 맞는 명령 하나를 실행하고 반환된 `task_id`를 보존한다.
부모가 필수 산출물·게이트·사본을 지정하며, 작업자가 이를 줄여 성공시키지 않는다.
`--agent-id`를 실제로 알고 있으면 함께 제공한다. 이 값이 있으면 종료 이벤트의 ID도 대조한다.
등록 자체가 자동 시작 기록 생성을 뜻하지 않는다. 역할은 이 명령을 실제로 실행해야 한다.
시작 뒤 baseline을 재설정해 이 작업의 미인계 파일을 기존 파일처럼 만들지 않는다.
이전 작업 기록을 새 작업에 재사용하지 않는다. 실제 런타임의 agent_id 제공 여부는 별도 검증 대상이다.

researcher는 예외로 자동 시작 기록이 있다. SubagentStart 훅 `researcher-task.sh`(matcher `researcher`)가
스폰 시 cwd의 체크아웃 루트에서 `lifecycle begin --role researcher`를 **`--agent-id` 없이** 실행하고,
`task_id`·`run_id`·payload `agent_id`·`handoff --task <task_id> --mode read-only` 명령을 맥락에 싣는다.
SubagentStart와 SubagentStop payload의 agent_id 일치가 증명되지 않았으므로 자동 task는 정지 시 ID를 대조하지 않는다.
파일 산출물이 필요하면 출력된 agent_id로 `begin --role researcher --agent-id <agent_id> --artifact runtime:artifacts/<파일>`
task를 하나 더 열고 그 task로 인계한다. 자동 task가 열린 동안 같은 체크아웃에 커밋하면 인계가 거부된다.
begin이 실패하면 훅은 exit 0으로 「researcher-task: begin 실패 · 사유 · 직접 begin 명령」을 출력하고, researcher는 위 명령을 직접 실행한다.

## 게이트

```bash
COLAB_TASK_ID=<task_id> bash gates/run.sh contract-lint
python3 scripts/agent-bridge.py verify-report --task <task_id> --report <현재-run의-report-절대경로> --gate contract-lint
```

복수 필수 게이트는 `begin --gate A --gate B`로 선언하고
`COLAB_TASK_ID=<task_id> bash gates/run.sh task` 한 명령으로 실행한다.
Windows에서는 환경값을 설정한 뒤 `scripts/dev.ps1 gate task`다. 이 실행은 선언된 게이트를 각각 한 번만 실행하고 한 run_id 아래 전수 결과를 낸다.
독립된 부분 실행들을 사후 합산하지 않는다. 기존 `gates/run.sh <게이트>`와 `all` 인터페이스도 유지한다.

보고서와 로그는 현재 run 디렉터리에만 쓴다. 매 실행 시작에 새 run_id와 출력 경로를 결합한다.
이전 runtime 보고서는 기존 run 디렉터리에 그대로 보존한다. 현재 경로는 `lifecycle gate-snapshot --task <task_id>`로 조회한다.
legacy 기록만 이전 보고서를 private Git history로 옮긴다.
배출이 실패해도 이전 green을 읽을 수 없고, 옛 JSON을 되돌려 놓아도 run_id 불일치로 차단한다.
실행기는 게이트 시작 전과 종료 후의 추적/미추적 비무시 파일 전체를 hash로 묶는다.
신규 runtime 출력 때문에 제품 파일의 검사 제외 범위를 넓히지 않는다.
legacy에서만 지정 보고서 디렉터리를 제외하며 Git이 무시하는 런타임 의존·생성물은 기존대로 취급한다.
검사 코드·fixture는 제외하지 않는다. 최대 8개 파일을 병렬로 읽되 매 검사마다 전체 내용 hash를 다시 계산한다. 숨겨진 외부 입력·실행 도구 버전의 동일성을 이 hash만으로 주장하지 않는다.
파일이 검사 중 또는 검사 후 바뀌었거나 필수 게이트·유효한 3계수·성공 종료코드가 없으면 H7은 차단한다.
미커밋 작업도 실제 파일 내용으로 검증되므로 검사를 위해 임의 커밋할 필요가 없다.
`--task` 없는 기존 `verify-report`는 clean checkout과 HEAD tree 대조를 유지한다.

## 인계

```bash
python3 scripts/agent-bridge.py lifecycle handoff --task <task_id> --mode read-only --summary '실제 조사 결과와 근거'
python3 scripts/agent-bridge.py lifecycle handoff --task <task_id> --mode draft-return --summary '미승인 초안 내용과 열린 질문'
python3 scripts/agent-bridge.py lifecycle handoff --task <task_id> --mode artifacts --summary '작성한 파일, 미승인 상태, 전달 대상'
python3 scripts/agent-bridge.py lifecycle handoff --task <task_id> --mode complete --summary '구현 결과와 실제 검증 결과'
```

해당하는 명령 하나를 실행한다. 출력된 `COLAB_HANDOFF {…}` 한 줄을 최종 메시지에 그대로 포함한다.
`read-only`와 `draft-return`은 작업 파일 무변경을 요구한다. 초안 본문도 부모가 사용할 수 있게 반환한다.
`artifacts`는 시작 시 선언한 파일의 실존·현재 hash와 이 작업 변경 파일을 대조한다.
기존 무관한 미추적 파일은 허용하고 이 작업의 누락·미인계 산출물과 범위 밖 변경은 차단한다.
파일 인계는 승인이나 커밋이 아니다. 다음 사본에 파일을 복사하면 부모가 hash를 대조한다.
`complete`는 lane-worker의 현재 작업 게이트 증거를 요구한다.

레인 범위: 부모가 파일 범위를 정하면 `begin --role lane-worker --gate … --scope <glob>`(여러 번)로 선언한다.
`**`는 디렉터리를 건너고 `*`·`?`는 건너지 않는다. 저장소 상대 POSIX 경로만 받고 `..`·절대경로·역슬래시는 거절한다.
아무 파일과도 맞지 않는 형태(`src/`처럼 `/`로 끝나거나 와일드카드 없는 디렉터리 이름)는 begin에서 거절하고 `src/**`를 안내한다.
범위는 `colab-task/2` runtime 에서만 쓴다 — `--legacy` 와 함께 쓰면 begin 이 거절한다(begin 시점 커밋이 없어 커밋 변경을 대조할 수 없다).
범위를 선언한 task의 `handoff --mode complete`와 H7은 baseline 대비 변경 파일 중 범위 밖을 목록으로 내고 차단한다.
baseline은 begin 시점의 추적·미추적(무시 제외) 파일 전체의 내용 hash다. 여기에 begin 시점 커밋..HEAD 사이에 커밋된 변경과, begin 시점 index 트리(`git write-tree` · task 의 `started_index`) 대비 스테이징 변경을 더해 센다 — 범위 밖 변경을 커밋·스테이징한 뒤 작업 파일만 되돌려도 드러나고, begin 이전부터 스테이징돼 있던 항목은 레인의 변경으로 세지 않는다. 삭제도 변경이다.
범위를 선언한 begin 은 index 를 트리로 기록해야 한다. 병합 충돌이 남은 index 는 「충돌을 먼저 해결하라」로 거절하고, 그 밖의 실패(예: 다른 git 프로세스의 `index.lock`)는 git 의 메시지를 그대로 담아 거절한다.
선언 없이 허용되는 경로는 `dev-package/reports/**`·이 문서다. task runtime은 Git common 디렉터리에 있어 대조 대상에 나타나지 않는다.
차단 메시지의 출구는 둘이다. ⑴ 범위를 넓힌 새 task를 `begin --scope`로 열고 게이트를 다시 돌려 그 task로 인계한다.
새 task의 baseline은 그 시점 파일을 담아 이미 한 범위 밖 변경을 다시 보지 못하므로, 넓힌 경로와 사유를 `--summary`에 적는다.
⑵ 범위 밖 변경을 되돌리고 게이트를 다시 돌려 같은 task로 인계한다. 범위를 선언하지 않은 task는 기존 동작 그대로다.
시험 fixture의 승인 응답은 시험 데이터다. 실제 제품 승인 기록으로 옮기지 않는다.

CLI `handoff`가 통과하면 task.json에 `handed_off = {mode, run_id, at}`을 기록한다(「인계됨」).
SubagentStop H6/H7 경로는 판정만 하고 기록하지 않는다. 「닫힘」과 정리는 PR 2 몫이다.

## fix 레인

결함 수정 과제는 실패 시험을 먼저 기록하고 연다. 이 절이 fix 레인의 정본이다.

```bash
python3 scripts/agent-bridge.py lifecycle begin --role lane-worker --gate <게이트> [--scope <glob>] \
  --fix --red <시험 경로>[::<case>] [--red …]
```

- begin이 선언한 시험을 실제로 실행해 **rc 1(실패)일 때만** task를 연다. rc 0(이미 green)은 「a RED must fail before the fix」,
  그 밖의 rc(수집 오류 · 인터프리터 부재 · 시간 초과 900초)는 「readiness, not RED」로 78 거절하고 task를 만들지 않는다.
  `--fix`와 `--red`는 함께만 받는다. `lane-worker` 외 역할과 `--legacy`는 거절한다.
- 러너 표(`scripts/harness/hooks/lifecycle_contract.py` `RED_RUNNERS` 한 곳 · 각 시험 묶음을 도는 게이트와 같은 인터프리터·옵션):

  | 경로 | cwd | 명령 | `::case` |
  |---|---|---|---|
  | `scripts/tests/*.py` | 저장소 루트 | `python3 -m unittest <경로>` | `-k <case>` |
  | `frontend/test/**` | `frontend` | `node_modules/.bin/vitest run <경로>` | `-t <case>` |
  | `services/<svc>/tests/**` | `services/<svc>` | `.venv/bin/python -m pytest -q -p no:cacheprovider <경로>` | `<경로>::<case>` |
  | `gates/tools/*-selftest.sh` · `eval/harness/tests/*.sh` | 저장소 루트 | `bash <경로>` | 불가 |

  그 밖의 경로는 「no runner」로 거절한다. 와일드카드·절대경로·`..`는 받지 않는다.
- 기록: task.json `fix.red[]` = `spec · path · case · blob`(`git hash-object`) `· runner · cwd · rc · output_sha256 · log`.
  실행 출력은 task runtime `red/<i>.log`에 남는다. 보고에 RED를 인용할 때는 이 로그 경로를 적는다.
- 편집 시점 차단: 열린 fix task가 기록한 경로에 대한 Edit/Write는 `test-file-guard`가 exit 2로 막는다(Claude·Codex 동일).
  대조 기준은 `file_path`가 속한 checkout이다. env · agent_id · payload cwd · `COLAB_ALLOW_TEST_EDIT`와 무관하고,
  부모 세션이 lane worktree의 기록 경로를 고치는 것도 막는다. 다른 checkout의 같은 상대경로와 기록하지 않은 경로는 막지 않는다.
- 인계: `gates/run.sh task`는 선언 게이트 뒤 기록마다 `fix-red:<spec>` 행을 낸다. 시험 파일 blob이 기록과 같으면
  같은 명령으로 다시 돌려 rc 0 green · rc 1 red(판정) · 그 밖 red(준비), 다르면 실행하지 않고 red(판정)이다.
  `handoff --mode complete`와 H7은 이 행 전부 green과 현재 blob == 기록 blob을 요구한다.
- 출구: 제품 코드를 고쳐 GREEN을 만든 뒤 `handoff --mode complete`(`handed_off` 기록 · 잠금 해제).
  시험 자체가 틀렸으면 시험 파일을 기록 blob으로 되돌리고, 부모가 재승인한 `--red`로 새 task를 연다.
  버려진 fix task의 잠금은 부모가 그 worktree를 제거하면 풀린다(checkout 부재 = 무시). PR 2에서 `handoff --mode blocked`가 추가된다.
- 같은 파일에 case를 더하는 정당한 시험 확장도 blob 변경이라 거절된다 — 시험 확장도 새 task로 재승인한다.
- Bash 쓰기(`sed -i` · 리다이렉션 등)는 편집 시점 차단 대상이 아니다. 인계의 blob 대조가 잡는다.
- 마커 `<git common dir>/colab-harness/red-locked/<task_id>`는 색인이고 판정은 task.json이 한다.
  마커를 손으로 지우면 편집 시점 차단만 사라지고 인계 대조는 남는다. 조회: `lifecycle_contract.py red-locked --checkout <경로>`.
- unittest는 import 오류도 rc 1이라 RED로 기록될 수 있다. 로그와 `output_sha256`이 남으므로 리뷰에서 확인한다.

## Runtime 산출물 쓰기와 경계

신규 산출물은 `runtime:artifacts/<파일>`로 정확히 선언한다. begin은 실제 절대경로를 반환한다.
일반 checkout 밖 편집 보호는 유지한다. 직접 편집 예외는 현재 task-id·run-id·실제 agent-id와 선언 경로가 모두 일치할 때만 적용한다.
다른 사본·다른 작업·이전 run·미선언 파일·symlink 이탈은 거절한다. 인계는 현재 내용 hash와 미선언 출력까지 검사한다.
이벤트가 이 식별 정보를 주지 않으면 직접 apply_patch를 허용했다고 주장하지 않는다.
명령문 안 `COLAB_TASK_ID=...`는 앞서 실행되는 훅 프로세스의 환경을 바꾸지 않는다.
실제 owner 정보를 확보한 작업은 `lifecycle write-artifact --task <id> --run-id <run> --agent-id <owner> --artifact runtime:artifacts/<파일>`의 stdin으로 내용을 전달할 수 있다.
이 CLI도 같은 resolver를 사용한다. task 등록은 OS 접근 통제나 에이전트 신원 서명이 아니다.
신규 handoff에는 run-id가 포함된다. Slack 준비는 같은 task resolver·현재 run·파일 hash를 재검증하며,
외부 완료 본문은 증거로 지정한 task에 선언된 artifact만 허용한다. 준비나 검증이 실제 전송 권한을 부여하지 않는다.
