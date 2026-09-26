# Probe R4-missed-1 — H6 task 결합 (2026-09-25)

판정: REPRODUCED (payload-only probe · 격리 clone)

## 환경
- main 체크아웃 task.json 수: 시작 204 → 종료 204 (변경 없음)
- clone: <home>/.claude/jobs/aa678208/tmp/intent-draft/probe-clone (`git clone` 로컬, 자체 .git) @ 67a03a05 — 종료 후 삭제
- task 기록 위치: clone/.git/colab-harness/8e76bf3b…/<task_id>/task.json (main .git 미사용 확인)
- COLAB_TASK_ID 미설정. gate 미실행.

## 코드 근거 (clone @ 67a03a05 에서 재확인)
- lifecycle_contract.py:365 — stop() 은 payload `last_assistant_message` 의 `COLAB_HANDOFF {...}` 한 줄을 찾는다.
- :369 — `load_task(root, handoff.get('task_id'))` : 검사 대상 task = 에이전트가 marker 에 적은 task_id. 스폰 시 연 task 와의 결합 없음.
- :377 — `task.get('agent_id')` 가 있을 때만 payload agent_id 대조. 자동 task(agent_id None)는 대조 생략.
- :383-389 (변경 판정 :386) — researcher 변경 = 그 task 의 begin 시점 baseline 대비. 새 begin 은 편집 후 파일을 baseline 으로 잡는다.
- researcher-task.sh:9-10 (주석) · :67 실행 — 자동 task 는 `--agent-id` 없이 begin.
- lifecycle-evidence.md:36 「시작 뒤 baseline을 재설정」, :42 「자동 task는 정지 시 ID를 대조하지 않는다」, :95-96 (lane scope 출구 ⑴) 「새 task의 baseline은 그 시점 파일을 담아 이미 한 범위 밖 변경을 다시 보지 못하므로」 — 문서가 lane 쪽 baseline 재설정을 출구로 명시.

## 실행 (cwd = clone 루트)
| 단계 | 명령 | 결과 |
|---|---|---|
| a | `printf '{"agent_type":"researcher","cwd":"<clone>","agent_id":"probe-agent-xyz"}' \| bash scripts/harness/hooks/researcher-task.sh` | rc=0 · T1=6ff2ee1e… · task.json agent_id=None |
| b | `echo probe-edit-R4 >> README.md` | `git status`: ` M README.md` |
| c | `python3 scripts/agent-bridge.py lifecycle begin --role researcher` | rc=0 · T2=9499f77a… |
| d | `python3 scripts/agent-bridge.py lifecycle handoff --task T2 --mode read-only --summary 'probe summary'` | rc=0 · `COLAB_HANDOFF {"task_id": "9499f77a…", "mode": "read-only", …, "artifacts": {}, "run_id": "c6646642…"}` |
| e | `bash scripts/harness/hooks/uncommitted-artifacts.sh < payload(agent_type=researcher, cwd=<clone>, agent_id=probe-agent-xyz, last_assistant_message="findings…\n<T2 marker>")` | **rc=0** · stdout `H6 — current task evidence and handoff verified; no automatic commit` |
| 대조 1 | `lifecycle handoff --task T1 --mode read-only …` | rc=78 · `lifecycle evidence blocked: read-only/draft-return requires unchanged files and no file artifacts` |
| 대조 2 | 같은 hook, 손으로 만든 T1 marker(run_id=T1 run) | **rc=2** · 같은 차단 문구 |
| 변형 | 편집 후 `begin --role researcher --agent-id probe-agent-xyz` → T3 handoff read-only → 같은 hook(agent_id=probe-agent-xyz) | handoff rc=0 · H6 rc=0 |

종료 시 clone 작업 트리: ` M README.md` (미커밋 제품 파일 변경이 남은 채 H6 통과)

## 기제
- H6 는 「스폰 때 연 task」가 아니라 「최종 메시지 marker 의 task_id」를 판정한다(:369). 열린 task 수 제한·이전 task 종료 확인 없음.
- 편집 뒤 새 begin 은 편집된 파일을 baseline 에 담으므로(:386 대비 기준) read-only 판정의 변경 집합이 비고, 자동 task 는 agent_id 가 없어 :377 대조가 생략된다.
- `--agent-id` 를 붙여 새 task 를 열어도(변형) 같은 agent_id 로 새 baseline 이 생기므로 통과한다 — agent_id 대조는 task 교체를 막지 않는다.
- 대조군(T1)은 차단되므로 baseline 비교 자체는 작동한다. 우회 경로는 task 교체다.

## 한계 (미검증)
- payload-only: 실제 Claude Code SubagentStop 이벤트가 `last_assistant_message`·`agent_id`·`cwd` 를 이 형태로 주는지는 이 probe 에서 확인하지 않았다(코드가 읽는 필드로 payload 구성).
- 실제 researcher 가 이 경로를 밟은 사례는 확인하지 않았다(가능성 재현만).
- H7(lane) 쪽 동일 기제는 이 probe 범위 밖 — 미검증.
