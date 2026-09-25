# A3 — 이 검토 세션(2026-09-24)의 researcher·advisor 실행 실측

출처: 이 세션(`claude/harness-consolidation` 작업 세션)의 서브에이전트 완료 알림 `usage` 필드(도구 호출 수 · 토큰)와 최종 메시지. 모든 researcher 는 `.claude/agents/researcher.md` maxTurns 30, advisor 는 12.

| # | 역할 | 지시문의 begin/handoff 절차 | 범위 | 결과 | 도구 호출 | 서브에이전트 토큰 | 종료 방식 |
|---|---|---|---|---|---|---|---|
| A | researcher | 없음 | 질문 4개(절단 원인 전수) | **30턴 절단** · 산출 파일 뼈대+노트만 | 23 | 115,114 | 최종 메시지 "I can't produce a COLAB_HANDOFF line and won't write one by hand" — H6 반송 반복 |
| B | researcher | 없음 | 질문 6개(② 4 + ④ 2) | **30턴 절단** · B1-1 절만 작성 | 24 | 102,875 | 최종 메시지 "there is no shell and no task_id, so I can't produce a valid COLAB_HANDOFF" — H6 반송 반복 |
| C | researcher | 없음 → **도중 전달**(SendMessage 로 begin/handoff 절차) | 질문 6개 | 정상 종료 · `COLAB_HANDOFF` read-only | 50 | 134,171 | 인계 성공 |
| A2 | researcher | **첫머리에 있음** + 「8번째 도구 호출 전 쓰기」 | 질문 2개 | 정상 종료 | 9 | 75,336 | 인계 성공 |
| B2 | researcher | **첫머리에 있음** + 「8번째 도구 호출 전 쓰기」 | 질문 3개 | 정상 종료 | 23 | 104,486 | 인계 성공 |
| adv | advisor ② | 해당 없음(종료 훅 없음) · 「도구 8회 이하」 | intent 검토 | 정상 종료 · accept-with-fixes 9건 | 9 | 89,905 | — |

- 절차 없음 2/2 절단 · 절차 있음(도중 전달 포함) 3/3 정상 종료.
- C 는 도구 50회를 30턴 한도 안에서 썼다 — 한 턴에 병렬 호출이 여럿이다.
- 부수: 조사자들은 체크아웃 밖 산출 파일을 Write 도구로 쓰려다 `migration-guard` 에 막혀("lifecycle evidence blocked: invalid or missing task_id") 셸 heredoc 으로 썼다. 워크트리 격리된 이 세션에서는 주 체크아웃 셸 실행이 막혀 C 는 begin/handoff 를 `harness-consolidation` 워크트리에서 실행했다.
- 한계: 표본 5. 도구 호출 수는 알림 값이며 turn 수는 알림에 없다.
