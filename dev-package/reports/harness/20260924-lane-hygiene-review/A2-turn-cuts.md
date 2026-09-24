# A2 — 2026-09-24 design-structure 세션의 턴 한도 절단 원인 (stop-hook bounce 가설 검증)

출처: `~/.claude/projects/-home-ttlhi10-workspace-00-Project-00-CoLAB-31-CoLAB-v2--claude-worktrees-design-system-plan/aa678208-.../subagents/agent-*.jsonl`
계측 스크립트: `/home/ttlhi10/.claude/jobs/d406d55c/tmp/a2.py`, `a2b.py`
- turn = assistant message.id 고유 개수, call = tool_use 누계
- hook 차단 = 사용자 메시지 `Stop hook feedback: [bash ".../.claude/hooks/<훅>.sh"]: lifecycle evidence blocked: one final COLAB_HANDOFF JSON is required`
- 이 세션(31 체크아웃)의 훅 경로는 `.claude/hooks/uncommitted-artifacts.sh`(researcher)와 `.claude/hooks/lane-gate-summary.sh`(lane-worker)다. advisor 와 general-purpose 에는 차단 기록이 0건이다.

## Q1. 절단된 6개 에이전트 (첫 절단 = 메인 알림 시점)

| agent | 역할 | 첫 절단 지점 (turn/call) | 첫 절단 전 hook 차단 | 전체 turn / call (재개 포함) | 재개 후 차단 횟수 | 첫 차단 뒤 소비 turn | 산출 파일 첫 쓰기 (call 번호) |
|---|---|---|---|---|---|---|---|
| aee2b255 | researcher (opus) | t30 / c34, 00:33 | 0 | 58 / 49 | 13 (t32~t55) | 26 (t32→t58) | c35: heredoc 으로 `frontend-styling-survey.md` 작성. 첫 절단 뒤다 |
| a03dc9e8 | advisor (opus, 12-turn) | t12 / c12, 00:43 | 0 | 15 / 14 | 0 | 0 | 해당 없음(판정문 반환). 재개 뒤 t15 에 끝남 |
| af51a789 | researcher (opus) | t30 / c33, 03:10 | 0 | 54 / 48 | 11 (t42~t54) | 12 (t42→t54) | c39: `/tmp` 에서 조립한 뒤 `cp` 로 `p2-design-system-map.md` 작성. 첫 절단 뒤다 |
| a7a32208 | researcher (sonnet) | t30 / c29, 03:56 | **1 (t30, 마지막 turn)** | 30 / 29 | 해당 없음 | 0. 차단 직후 한도에 걸림 | **c10**: `p3-literal-map.md` 작성. 절단 전이다 |
| ae3fe841 | lane-worker P2a | t200 / c253, 05:04 | 0 | 275 / 330 | 10 (t254~) | 21 (t254→t275, t264 의 coordinator 승인 1건 포함) | 코드 Write 는 c20 부터 |
| a176c2f6 | lane-worker P2b | t200 / c255, 08:45 | 0 | 212 / 270 | 1 (t211) | 1 | 코드 Write 는 c32 부터. 구현은 절단 전에 커밋됨 |

추가 사실:
- 6건 중 5건은 첫 절단 전 hook 차단이 0건이다. 차단 1건 직후 한도에 걸려 절단된 경우는 a7a32208 1건이다. 이 에이전트는 29 call 만에 작업을 끝냈고 t30 에 정지를 시도했다. H6 가 그 정지를 막았고, 다음 turn 이 한도를 넘어 절단 알림이 나갔다.
- 재개된 researcher 2건은 bounce loop 에 빠졌다. aee2b255 는 13회 차단됐고 t47~t58 에 tool call 없이 정지만 반복했다. af51a789 는 11회 차단됐다.
  - 두 에이전트는 COLAB_HANDOFF 를 만들 수 없었다. prompt 에 `lifecycle begin` 이 없어 task_id 가 없었기 때문이다.
  - aee2b255 는 훅과 스크립트를 읽는 데 6 call 을 썼고, c47 에는 general-purpose(a7f9b7cc)를 스폰해 begin 을 대신 실행하려 했다.
  - 두 에이전트는 성공한 정지 없이 끝났다.
- lane-worker 2건의 200-turn 절단은 hook 과 무관하다(차단 0). 재개 뒤에 H7 가 P2a 를 10회, P2b 를 1회 차단했다. prompt 에 begin/handoff 가 있었고 초기(c10, c9)에 bridge 를 호출했다.

## Q2. prompt 의 begin/handoff 포함 여부와 대조군

| agent | 역할 | 절단 | prompt 에 begin/handoff/COLAB_HANDOFF | 예산 문구 | turn / call | hook 차단 |
|---|---|---|---|---|---|---|
| aee2b255 | researcher | 예 | 없음 / 없음 / 없음 | 없음 | 58 / 49 | 13 |
| af51a789 | researcher | 예 | 없음 | "30-turn limit", "WRITE THE REPORT FILE EARLY" | 54 / 48 | 11 |
| a7a32208 | researcher | 예 | 없음 | "report file BEFORE ..." | 30 / 29 | 1 |
| a03dc9e8 | advisor | 예 | 없음 | 없음 | 15 / 14 | 0 |
| a692d42d | advisor ① P0 | 아니오 | 없음 | 없음 | 8 / 7 | 0 |
| a5e5cf45 | advisor ① P1 | 아니오 | 없음 | "at most 8 tool calls" | 11 / 10 | 0 |
| (참고) a6d03657, af2f8a6a, a4a4f364 | advisor | 아니오 | 없음 | a6d0·a4a4 에 "at most 8" | 8/8, 7/8, 7/8 | 0 |
| (참고) a7f9b7cc | general-purpose (aee2b255 가 스폰) | 아니오 | 없음 | 없음 | 8 / 7 | 0 |
| ae3fe841, a176c2f6 | lane-worker | 예 | **있음** | 없음 | 위 표 | 10, 1 |

- 이 세션의 researcher 는 3개이고 3개 모두 절단됐다. 절단되지 않은 researcher 대조군은 이 세션에 없다.
- advisor 는 절단 여부와 상관없이 전원 begin/handoff 없이 실행됐고 hook 차단이 0건이다. advisor 절단은 hook 과 무관하다.

## 원인 판정 (에이전트별)

| agent | (a) 범위 과대 | (b) 읽고 나서 쓰기 | (c) 한도 과소 | (d) stop-hook bounce |
|---|---|---|---|---|
| aee2b255 | 부분. 8개 절 조사 | **주원인**. 34 call 동안 쓰기 0건, c35 에 첫 쓰기 | 부분. 30 turn | 첫 절단에는 0. 재개 후 13회 차단, 26 turn 소모 |
| a03dc9e8 | 약함 | **주원인**. 12 call 이 모두 읽기, 판정문 0 | **주원인**. 12-turn | 0 |
| af51a789 | 부분. 전 규칙 대응표 | **주원인**. "EARLY" 지시에도 c33 까지 신고 경로에 쓰기 0건(`/tmp` 중간 파일만) | 부분 | 첫 절단에는 0. 재개 후 11회 차단, 12 turn 소모 |
| a7a32208 | 부분. 29 call 사용 | 아님. c10 에 씀 | 부분 | **주원인**. 정지 시도 1회가 막혀 한도를 넘음 |
| ae3fe841 | **주원인**. 200 turn 에 step 4 까지만 진행 | 해당 없음 | 부분 | 첫 절단에는 0. 재개 후 10회 차단 |
| a176c2f6 | **주원인**. 200 turn 에 step 7 까지 진행 | 해당 없음 | 부분 | 첫 절단에는 0. 재개 후 1회 차단 |

결론:
- 새 가설 (d) 가 첫 절단을 직접 일으킨 경우는 6건 중 1건(a7a32208)이다.
- 나머지 5건의 첫 절단은 차단 0건 상태에서 일어났다. 원인은 (b)+(c) 3건(aee2b255, af51a789, a03dc9e8)과 (a) 2건(lane-worker)이다.
- (d) 는 재개 이후에 크게 드러났다. researcher 2건이 합계 24회 차단됐고 38 turn 을 소모했으며, 성공한 정지 없이 끝났다. 원인은 prompt 에 begin/handoff 가 빠져 COLAB_HANDOFF 를 만들 수 없었던 데 있다.
- lane-worker 는 protocol 이 있었는데도 재개 후 11회 차단됐다. 재개 prompt 가 handoff 를 다시 지시하지 않은 것으로 보이며, 이 부분은 미검증이다.
