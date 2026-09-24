# Spec v2: 하네스 고도화 — researcher 자동 task · 브라우저 세션 종료 · 잠금 미상속 · 지시·역할 규칙
출처 intent: `dev-package/intent/2026-09-24-harness-lane-hygiene.md` (승인 2026-09-24 · Ted 원문 "전부 권고대로 할게,"). v1(1차 권고 기준 초안)은 git 이력.
근거: `dev-package/reports/harness/20260924-lane-hygiene-review/`(A2 · A3 · B2 · C · `lock-inherit-repro.sh`). advisor ① 2026-09-24 approve-with-changes — 차단급 4 · 개선 5 전부 반영.

## 문제 진술
- researcher 가 `lifecycle begin` 없이 스폰되면 H6 가 모든 정지를 막아 턴 한도까지 반송한다(재개 researcher 24회·38턴 · 이번 세션 2/2 절단). 절차는 지시문 기억에 맡겨져 8건 중 5건에서 빠졌다.
- serial 게이트 안에서 처음 뜬 agent-browser 데몬·chrome 이 호스트 뮤텍스 fd 를 상속해 게이트가 끝난 뒤에도 잠금을 쥔다. `live_audit.sh` 는 세션을 닫지 않는다.
- advisor ② 가 게이트 증거를 스스로 연 기록 0 · advisor ① 결함 등급 기록 0 · 레인 범위 과대로 200턴 절단 2건.

## 해법 개요
- 코드: researcher `SubagentStart` 훅 1개(R1) · `live_audit.sh` 자기 세션 종료(F2) · 잠금 fd 를 데몬을 띄우는 자식에 넘기지 않음(F1).
- 문서: 지시문 체크리스트(R2·R4·②·④) · 역할 본문(R3·②·④). handoff JSON 계약·`maxTurns`·advisor ① 생략 기준은 바꾸지 않는다.

## 구현 결정
### R1 researcher 자동 task (레인 A)
- 새 훅 `scripts/harness/hooks/researcher-task.sh`(원본) + `.claude/hooks/researcher-task.sh`(어댑터 · 기존 어댑터와 같은 한 줄 꼴). 첫 줄 `[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0`. **항상 exit 0**(비차단 · `worktree-setup.sh` 원칙).
- stdin JSON 에서 `cwd`·`agent_id`·`agent_type` 을 읽는다. `agent_type != researcher` 면 조용히 exit 0. cwd 의 체크아웃 루트에서 `python3 scripts/agent-bridge.py lifecycle begin --role researcher` 를 실행한다 — 자동 task 는 **`--agent-id` 를 넣지 않는다**(`stop()` 은 task 에 agent_id 가 있을 때만 payload 와 대조한다. SubagentStart·SubagentStop payload 의 `agent_id` 일치가 미증명인 상태에서 그것을 정지 조건에 걸지 않는다). payload `agent_id` 는 출력에만 찍어 researcher 가 산출물 task 를 열 때 쓴다. intent R1 의 `--agent-id` 문구를 안전한 쪽으로 좁힌 것이다(advisor ① 차단급 1).
- 출력(평문 · SubagentStart stdout 은 맥락에 실린다) 한 화면 이내: `task_id` · `run_id` · **`agent_id`** · 마지막 단계 명령 `python3 scripts/agent-bridge.py lifecycle handoff --task <task_id> --mode read-only --summary '<요지>'` · 「출력된 COLAB_HANDOFF 줄을 최종 메시지 마지막 줄에 그대로」 · 「파일 산출물이 필요하면 `begin --role researcher --agent-id <agent_id> --artifact runtime:artifacts/<파일>` 로 task 를 하나 더 열고 그 task 로 handoff」 · 「이 task 가 열린 동안 같은 체크아웃에 커밋하면 인계가 거부된다」.
- begin 실패(비 git cwd · python3 부재 · 오류) → 「researcher-task: begin 실패 · 사유 <한 줄> · 직접 begin 명령 <명령>」을 찍고 exit 0.
- 등록: `.claude/settings.json` `SubagentStart` 에 matcher `researcher` 항목 추가 · `.codex/hooks.json` `SubagentStart` 에 matcher `researcher` 항목 추가(기존 `lane-worker` 항목과 같은 명령 · timeout 65초 — begin 실측 1.6초, `lane-worker` 항목 580초는 의존성 준비용) · `.agents/harness.yaml` `hook_names`·어댑터 목록 · `scripts/tests/test_harness_source_layout.py` 이름 목록 · 새 `.sh` 2개 `git update-index --chmod=+x`(규칙 `4-3`).
- 문서: `docs/development/dual-agent.md` 「자동 훅 등록 상태」 훅 수(10 → 11)와 재신뢰 안내 · `docs/development/lifecycle-evidence.md` researcher 시작 절에 자동 task 한 문단 · `.agents/roles/researcher.md` 「작업별 시작·종료 증거 (H6)」에 자동 task 사용법 + R3 문장(「산출 파일을 8번째 도구 호출 전에 쓴다(뼈대 포함) · 질문이 3개를 넘으면 부모에게 분할을 요청한다」).

### F2 브라우저 세션 종료 · F1 잠금 미상속 (레인 B)
- F2 `.agents/skills/design-review/scripts/live_audit.sh`: `AB_SESSION` 을 호출자가 주면 **호출자 소유** — 닫지 않는다(로그인 선행 흐름 보존). 없으면 고유 이름(`la-<pid>-<epoch>` 꼴)을 만들고, 설치 확인(`command -v agent-browser`) **뒤에** `AB_SESSION` 이 비었을 때만 `trap 'agent-browser --session "$S" close >/dev/null 2>&1 || true' EXIT` 를 건다. 머리말 사용법과 `.agents/skills/design-review/SKILL.md` 의 로그인 안내(「`agent-browser --session design auth login`」 문단)를 둘 다 「로그인 세션을 쓰려면 `AB_SESSION=design scripts/live_audit.sh …` 처럼 넘긴다 — 넘기지 않으면 새 세션(로그아웃 상태)으로 잰다」로 고친다.
- F2 실효: `frontend-visual-selftest` 는 실브라우저 ⓐ·ⓑ 뒤 판정부가 연 `la-…` 세션(`index.md` 머리)의 프로세스가 남지 않았음을 단언한다(⑸ · advisor ② 차단급). 가짜 ⑶⑷ 는 close 호출만 잰다.
- F2 안전망: `gates/tools/frontend-visual.sh` 가 판정부를 부를 때 `AGENT_BROWSER_IDLE_TIMEOUT_MS` 가 비어 있으면 `600000`(10분)으로 둔다 — trap 이 돌지 않는 SIGKILL·절단 경로용. 호출자가 준 값은 존중한다. 이 값은 게이트가 새로 띄우는 데몬에만 든다. 호출자가 준 `AB_SESSION` 의 기존 데몬과 스킬의 수동 호출에는 trap 만 작동한다.
- F1 `gates/tools/_lock.sh`: 잠금을 잡은 직후 fd 번호를 `COLAB_GATE_MUTEX_FD` 로 export 하고, 해제 시 unset 한다. 단독 경로는 본체가 잠금 보유자이므로(`gates/run.sh` 의 `gate_host_mutex_acquire "$GATE"` 뒤 exec) 본체는 fd 를 쥔 채로 둔다. 데몬을 띄우는 자식 호출에서만 닫는다: `frontend-visual.sh` 의 판정부 호출을 `{COLAB_GATE_MUTEX_FD}>&-` 로(변수가 있을 때만) · `gates/run.sh` 의 `run_one` solo 자식 `run.sh "$g"` 호출도 같은 방식(부모가 잠금을 쥔 채 기다리므로 자식은 fd 가 필요 없다) — 단 **자식 env 의 `COLAB_GATE_MUTEX_FD` 는 비운다**(닫힌 번호가 자식에서 재할당된 뒤 손자가 무관한 fd 를 닫는 것을 막는다). 두 호출부는 `_lock.sh` 의 헬퍼 하나로 통일한다: `gate_mutex_spawn() { local fd="${COLAB_GATE_MUTEX_FD:-}"; if [ -n "$fd" ]; then COLAB_GATE_MUTEX_FD='' "$@" {fd}>&-; else "$@"; fi; }`. 「변수가 있을 때만」은 「비어 있지 않을 때만」으로 읽는다(`set -u` 아래 빈 `{var}>&-` 는 오류). `frontend-visual.sh` 는 `_lock.sh` 를 source 해 이 헬퍼를 쓴다. 본체 exec 구조 개편(`flock -o` 형)은 하지 않는다. `all` 경로에서 `run_one` 이 서브셸로 도는지, 잠금을 쥔 동안 다른 게이트 자식(pool)이 fd 를 물려받는 경로가 있는지 레인이 확인하고, 있으면 같은 방식으로 닫고 보고한다.
- 시험: `gates/tools/gate-host-mutex-selftest.sh` 에 케이스 추가 — 잠금 보유 중 데몬성 자식(`exec -a` 가짜 · `sleep`)을 ⑴ 그대로 띄우면 해제 뒤에도 다음 잠금 실패 ⑵ `gate_mutex_spawn` 으로 띄우면 해제 뒤 다음 잠금 즉시 획득 · 자식이 보는 `COLAB_GATE_MUTEX_FD` 가 빈 값이고 자식 fd 목록(`/proc/self/fd`)에 잠금 파일이 없다. `live_audit.sh` 는 PATH 앞자리의 **가짜 `agent-browser`**(호출 인자를 파일에 적는 스크립트)로 ⑶ `AB_SESSION` 없음 → 고유 세션으로 `close` 1회 ⑷ `AB_SESSION=x` → `close` 0회를 판정한다. 가짜 `agent-browser` 는 `eval` 호출에 `{"success":false,"error":"fake"}` 를 내고 나머지는 exit 0 — 정상 완주 경로에서 close 1회를 센다. 이 판정은 기존 selftest 안에 두고 새 게이트는 만들지 않는다(둘 곳은 레인이 고르고 보고).
- 문서 면: 레인 B 는 `.agents/skills/design-review/SKILL.md` 의 로그인 안내만 고친다. `docs/**`·`.agents/roles/**`·`.agents/skills/colab-v2-work/**` 는 건드리지 않는다.

### 문서 규칙 (오케스트레이터 직접)
- `.agents/skills/colab-v2-work/SKILL.md` §1 지시문 체크리스트: R2(재개 지시문에 task_id·handoff 명령 재기재 · researcher 실행 중 같은 체크아웃 커밋 금지 — 커밋이 필요한 구간이면 researcher 를 `isolation: worktree` 로 스폰한다) · R4(레인 1건 = 파일 계열 2~3개) · ②(advisor ② 프롬프트에 gate-summary **절대경로**와 3계수). §2: ④(① 결과는 항목마다 `차단급`/`개선` 등급을 남긴다 · 생략 기준 없음).
- `.agents/roles/advisor.md`: 「도구 8회 이하 뒤 판정 · 깨끗하면 깨끗하다고」 · 입력에 「오케스트레이터가 준 gate-summary 절대경로를 Read 로 연다 · 게이트를 재실행하지 않는다」 · ① 출력 항목마다 등급.
- `.agents/roles/lane-worker.md`·`measurement-lane.md` 완료 보고: gate-summary **절대경로**와 3계수를 최종 메시지에 적는다.

## 시험 결정
- 레인 A: 훅 단위 시험(`scripts/tests/` 기존 파일 중 하네스 훅 시험 자리) — ⓐ researcher payload → begin 성공 · 출력에 task_id·agent_id·handoff 명령 ⓑ 출력한 task 로 `lifecycle handoff --mode read-only` 가 `COLAB_HANDOFF` 를 낸다 ⓑ′ 그 marker 를 `scripts/tests/test_task_runtime.py` 의 Stop payload 꼴(`agent_type=researcher` · `agent_id` 를 훅이 받은 값과 **다르게**)로 H6 판정(`lifecycle_contract.py stop --role researcher`)에 넣어도 통과한다 · 같은 payload 로 `--agent-id` 를 준 산출물 task 는 거부된다(대조군) ⓒ 같은 agent_id 로 둘째 task(artifacts) 를 열어도 첫 task handoff 가 통과 ⓓ 비 git cwd → exit 0 · 「begin 실패」 문구 ⓔ `COLAB_HOOKS=0` → 출력 0 ⓕ `agent_type` 이 researcher 가 아니면 출력 0. Codex: bridge SubagentStart 로 researcher 이벤트를 흘려 같은 출력이 `additionalContext` 에 실리는지 · Codex payload 에 `agent_id` 가 없을 때 `--agent-id` 없이 begin 하는지.
- 레인 B: 위 ⑴~⑷. `frontend-visual-selftest` 는 실브라우저 게이트다 — 돌리고, 준비 실패(78)면 그 사실을 보고한다.
- 게이트(레인 A): `agent-bridge` · `harness-contract` · `harness-contract-selftest` · `exec-bit`. (레인 B): `gate-host-mutex-selftest` · `frontend-visual-selftest` · `harness-contract` · `exec-bit`. 병합 뒤 오케스트레이터가 합집합 + `work-item-consistency` · `planning-freshness` 를 다시 돈다.
- green-by-skip 방지: selftest 케이스는 각자 ✗ 를 셀 수 있어야 한다(가짜 `agent-browser` 가 안 불리면 red). 레인 B 는 ⑴·⑶ 의 수정 전 red 를 보이고, ⑵·⑷ 는 수정 후 대조군으로 적는다. 레인 A 는 A3 실측(H6 반송 루프)을 red 근거로 인용하고 ⓐ~ⓕ·ⓑ′ 의 수정 후 green 을 보고한다.

## 정책 대조
- `product.md §3·§5`: 제품 코드 0 · 게이트 우회 0. handoff·gate-summary 계약 무변. 훅 정의 변경 → 병합 뒤 이 PC `/hooks` 재신뢰(사용자 몫).
- 병합 뒤 라이브 스모크(후속 기록 · 병합 조건 아님): `/hooks` 재신뢰 뒤 researcher 1건을 질문 1개로 스폰해 첫 정지에서 H6 통과와 훅 출력 agent_id · Stop 시점 agent_id 일치 여부를 기록한다. 일치가 확인되면 다음 intent 에서 `--agent-id` 부착을 다시 따진다.
- 대상 화면: 해당 없음.

## 범위 밖
- F3(잠금 보유 pid 진단) · handoff JSON `evidence` 키 · `maxTurns` 변경 · advisor ① 생략 기준 · `gates/run.sh` 여분 인자 처리(부수 발견 · 별도 후보) · 30·31 저장소 · 커밋 외 push·PR 게시(오케스트레이터·사용자).

## 산출 계획
- 레인 A · 레인 B 병렬(`lane-worker` · `isolation: worktree` · 기준 = `origin/claude/harness-consolidation`). 파일 면 무겹침. serial 게이트는 호스트 뮤텍스가 직렬화한다.
- 레인은 자기 브랜치 커밋까지. 병합·문서 규칙·최종 게이트는 오케스트레이터.
