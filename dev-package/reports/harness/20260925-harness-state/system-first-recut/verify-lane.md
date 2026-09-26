VERDICT: ACCEPT-WITH-CHANGES

점검 근거(도구 결과): `scripts/harness/hooks/lifecycle_contract.py` :401 lane 은 `mode != 'complete'` 거절 · :365-367 `COLAB_HANDOFF` 1줄 · :403-427 scope 밖 차단 · `stop_hook_active` grep 0 · :64-70 scope_regex 가 `**` 처리 · :358 stop() 이 payload `agent_type` 을 읽음 → 확인. `git-guard.sh` :26-38 「⑴ 은 agent_id 실린 호출만 · ⑵ 강제 push(`--force-with-lease` 포함)·⑷ `gh pr merge` 는 오케스트레이터도 차단」 + 문서 축자 인용(서브에이전트 훅 입력에 `agent_id`·`agent_type` 실림) → N4 Claude 측 전제 확인. `gates/run.sh` :30 `COLAB_TASK_ID` 없으면 78 · :46 `COLAB_GATE_REPORT_DIR` 가 runtime 경로와 다르면 별도 처리 · :177 「잠글 수 없으면 판정하지 않는다 · 78」 → 확인. 주의: 훅 스크립트 3종은 메인 체크아웃 경로에서 읽었고(워크트리와 행번호 차이 있음 — 설계의 `:286`·`:227-231` 은 실측 `:239`·`:180-183`), `agent-bridge.py` 는 추정 경로에 없어 Codex 페이로드 주장(`agent_type` 미전달 · `--worker` 주입)은 **[미확인]**.

S-L1 — 조정 — N1 은 필요하나 「변경 파일 0」 조건은 wedge 를 만든다(scope 안 편집 뒤 경계 도달 → blocked 거절 → complete 는 gate green 필요 → 8회 상한). 「미커밋·scope 안 변경 허용 + handoff 에 dirty 목록·hash 기록」 변형을 채택하고 오남용 판별은 closed=blocked 라벨로 advisor ② 가 본다.
S-L2 — 유지 — H6/H7 실측 확인.
S-L3 — 유지 — 강제 불가 판정 타당.
S-L4 — 유지 — :403-427 확인.
S-L5 — 유지 — Claude 측 전제(PreToolUse 에 agent_type) 문서 인용으로 확인 · Codex 는 N4 항 참조.
S-L6 — 유지.
S-L7 — 유지 — `--expect-head` 는 ff-only 병합 **뒤** begin 순서를 지시문 템플릿에 고정해야 함(순서 뒤집히면 항상 거절).
S-L8 — 조정 — `git branch --show-current` 는 detached HEAD 에서 빈 문자열 → SHA 로 폴백 규정 필요.
S-L9 — 조정 — 레인 측은 타당. 그러나 git-guard :26-28 이 **메인 스레드의 `git push origin main`을 승인 경로로 열어 둠** — 「병합은 사람」 원칙과 충돌(아래 미시스템화 1).
S-L10 — 유지.
S-L11 — 유지.
S-L12 — 조정 — 마커 해제 출구가 메인 전용 `lifecycle close --spawn-marker` 뿐이면, Workflow 스크립트가 부모 체크아웃에서 레인을 돌리는 현 관행(메모리: agent() 기본 비격리)은 첫 실행부터 전부 거절됨. Workflow 지시 템플릿에 `isolation: worktree` 명시를 같은 PR 에 포함하고, SubagentStart 발화 여부 관측 1회를 병합 전 조건으로.
S-L13 — 유지 — run.sh:30 확인.
S-L14 — 유지 — `**` 파싱 확인 · begin 이 「mergeable index」(:225) 를 요구하므로 충돌 상태에서 78 나는 것을 거절 메시지에 명시.
S-L15 — 유지.
S-L16 — 유지(N1 조정에 종속).
S-L17 — 유지.
S-L18 — 유지.
S-L19 — 유지 — run.sh:46 이 이미 legacy 경로를 runtime 과 대조.
S-L20 — 조정 — 근거 오류: `_lock.sh` 는 「대기」가 아니라 **fail-fast 78**(run.sh:177). 그래서 레인이 수동 재시도 루프를 돈다. 시스템 대체 = `_lock.sh` 에 상한 있는 `flock -w <N>` 대기 + 초과 시 78 · 산문은 이유 1줄.
S-L21 — 유지.
S-L22 — 유지.
S-L23 — 유지.
S-L24 — 유지.
S-L25 — 유지.
S-L26 — 유지.
S-L27 — 유지.
S-L28 — 유지.
S-L29 — 조정 — Intent-Ref trailer 는 git-guard 가 `git commit` 시점에 검사 가능(토크나이저 있음) → CI 사후 red 대신 로컬 차단(미시스템화 3).
S-L30 — 유지(선택).
S-L31 — 유지.
S-L32 — 유지.
S-L33 — 유지 — roots 확장은 옛 보고서 red 위험 실측 뒤.
S-R1 — 유지.
S-R2 — 유지.
S-R3 — 조정 — Claude 는 즉시 · Codex 는 「지시 문장 유지」가 아니라 `--worker` 에 `COLAB_AGENT_TYPE` env 주입을 **같은 PR 2** 에 넣는다(지시문으로 남기는 것이 원칙 위반).
S-R4 — 유지 — :265 확인.
S-R5 — 유지.
S-R6 — 유지.
S-R7 — 유지.
S-R8 — 유지 — :384 확인.
S-R9 — 유지.
S-R10 — 유지.
S-R11 — 유지.
S-R12 — 유지.
S-R13 — 유지.
S-E1 — 유지.
S-E2 — 조정 — 범위 밖으로 미루지 말 것: `begin --spec <path>` 가 sha256 을 task.json 에 기록하고 N3 handoff JSON 에 실으면 advisor ② 가 대조(미시스템화 2).
N1 — 조정 — S-L1 과 동일(미커밋·scope 안 허용 변형).
N2 — 유지.
N3 — 조정 — S-L8 detached HEAD 폴백 · `counts` 는 stop() 이 이미 읽는 gate-summary 와 중복이므로 검증이 아니라 「CLI 가 채워 부모에게 전달」로 역할을 좁힌다.
N4 — 조정 — S-R3 과 동일(Codex env 주입을 PR 2 로).
N5 — 조정 — S-L12 와 동일.
N6 — 조정 — Codex `--worker` 가 서브에이전트 전용인지 미확인. 메인 구현 세션이 `--worker` 로 돌면 모든 push 가 막힌다 → bridge 코드 확인 뒤 `agent_id` 조건에 role(lane|researcher) 을 결합.
N7 — 조정 — 규칙 문법: Claude 문서의 Bash prefix 형식은 `Bash(gh pr merge:*)` 이며 `Bash(gh pr merge *)` 공백-와일드카드 매칭은 [미확인] → `:*` 형식 + 정확 일치 두 줄로 쓰고 수동 시험 1회를 병합 전 조건으로. `git push --force*` 는 git-guard ⑵ 가 이미 전원 차단하므로 파손 없음(2중 방어로 유지).
N8 — 유지.

설계자가 시스템화하지 못한 규칙 3:
1. **「병합·통합 브랜치 이동은 사람」의 메인 스레드 면** — git-guard :26-28 이 agent_id 없는 `git push origin main` 을 허용하고 ⑶ 도 main 에서의 `--ff-only` 병합을 통과시킨다. `gh` 가 Ted 의 admin 토큰이면 원격 ruleset 도 bypass 된다. N7 에 `Bash(git push origin main:*)`·`develop:*`·`product:*` deny(전원) 추가 + git-guard ⑴ 을 전원 차단으로 되돌리고 ruleset bypass 목록을 비운다.
2. **spec 인계 hash(S-E2)** — `begin --spec` + handoff JSON 으로 이번 PR 2 에 포함 가능.
3. **Intent-Ref trailer(S-L29)** — git-guard 의 `git commit` 시점 검사로 CI 앞당김.