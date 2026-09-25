# 하네스 서브에이전트 역할별 실사용 통계 (2026-09-10 이후)

집계 방법: `~/.claude/projects/*CoLAB*/*/subagents/agent-*.jsonl` + `.meta.json`(agentType) 스트리밍 파싱.
turn = assistant message.id 고유 개수(재개분 포함, 파일 합계), call = tool_use 누계, model = message.model 최빈값(런 단위).
`/mnt/f/...` 경로와 `~/workspace/...` 경로에 동일 agent-id 가 중복 존재(2026-09-14 WSL ext4 이전으로 인한 미러) 확인 —
전량 id 기준 중복 제거 후 집계(원본 381행 → 중복 제거 316행, 역할별 n 은 아래 표).
frontmatter 기본값: researcher=sonnet/maxTurns 30, lane-worker=opus/maxTurns 200, measurement-lane=sonnet/maxTurns 60,
gate-runner=haiku/maxTurns 20, advisor=fable/maxTurns 12.

## 역할별 표

| 역할 | n | 실사용 모델(런 수) | turn 중앙값/p90/max | call 중앙값/p90/max | 한도(maxTurns) 도달(turn≥한도) 런 수 | out_tokens 중앙값 | wall(중앙값, 분) |
|---|---|---|---|---|---|---|---|
| researcher | 118 | opus 89, opus-5-5 9(합 98), sonnet(기본값) 20 | 30.0 / 49.8 / 128 | 37.0 / 56.3 / 137 | 68 (한도 30) | 5509 | 7.0 |
| lane-worker | 102 | opus(기본값) 90, opus-5-5 12 | 91.5 / 222.8 / 800 | 95.5 / 246.0 / 797 | 14 (한도 200) | 15816 | 23.9 |
| advisor | 73 | fable(기본값) 52, opus 6, opus-5-5 14(합 20), synthetic 1 | 8 / 13.8 / 23 | 12 / 21.8 / 35 | 22 (한도 12) | 314 | 3.1 |
| gate-runner | 18 | haiku(기본값) 18 | 9.0 / 30.6 / 84 | 9.0 / 27.9 / 81 | 4 (한도 20) | 20 | 5.5 |
| measurement-lane | 5 | sonnet(기본값) 5 | 48 / 62.4 / 64 | 48 / 67.2 / 70 | 2 (한도 60) | 1435 | 12.1 |

주: turn 수치는 파일 내 재개(재스폰) 구간을 합산한 값이며, `A2-turn-cuts.md`(2026-09-24, 31-checkout)가 확인한 바로는
turn≥한도인 런 다수가 "1차 절단 → 재개 → 추가 turn 소모"의 결과다. 즉 turn≥한도 건수는 1회성 초과가 아니라
"최소 1회 이상 한도 절단을 겪은 런"의 근사치다.

## 역할별 한도 도달 런 (최대 3건, 원인 1줄)

### researcher (한도 30, 도달 68/118건)
`A2-turn-cuts.md`(2026-09-24, 31-checkout) 재사용.
- aee2b255 (58턴): read-before-write — 34 call 째까지 조사만 하고 첫 쓰기가 c35. 1차 절단 후 재개에서 stop-hook 13회 반송, 26턴 추가 소모, 성공적 정지 없이 종료(prompt 에 lifecycle begin 누락).
- af51a789 (54턴): read-before-write — "EARLY 작성" 지시에도 c33까지 보고서 경로 쓰기 0건. 재개 후 stop-hook 11회 반송.
- a7a32208 (30턴): stop-hook bounce — 29 call 만에 작업을 끝내고 t30에 정지 시도, H6 훅이 정지를 막아 다음 턴이 한도를 넘겨 절단.

### lane-worker (한도 200, 도달 14/102건)
`A2-turn-cuts.md`(2026-09-24, 31-checkout) 2건 + 자체 확인 1건.
- ae3fe841 (P2a, 275턴): scope — 200턴에 4단계까지만 진행, 절단 자체는 훅 무관(1차 절단 전 차단 0), 재개 후 H7 10회 반송.
- a176c2f6 (P2b, 212턴): scope — 200턴에 7단계까지 진행, 1차 절단 전 차단 0, 재개 후 H7 1회 반송.
- acce59788677c2640 (800턴, 32-checkout f19831c9 세션): other — 마지막 메시지가 "형제 레인이 머신을 반납할 때까지 최종 게이트 대기 중"으로, 구현이 아니라 병렬 레인 간 대기로 턴을 소모.

### advisor (한도 12, 도달 22/73건)
`A2-turn-cuts.md` 1건 + 자체 확인 2건.
- a03dc9e8 (15턴, 2026-09-24): read-before-write/한도 과소 — 12 call 전부가 읽기이고 판정문 산출 0건 상태로 한도 도달.
- aa0edb0734f25a234 (23턴, cf916fed 세션): scope — 근거 확인·대안 제시(교수 케이스 복원 여부)까지 상세 검토가 이어져 정상 종료 문장까지 23턴 소요.
- a0398aba526b769d8 (16턴, ff466cc1 세션): scope — 게이트 판정 + main 반영 절차(ff, 브랜치 삭제)까지 다단계 후속 지시를 이어 답하며 한도 초과.

### gate-runner (한도 20, 도달 4/18건)
자체 확인.
- a9f3c62bb2e38bfad (84턴, 32-checkout f19831c9 세션): other — "메모리 제약으로 백그라운드 모니터가 강제 종료됨"이라고 보고. 게이트 자체는 63 green/0 red(판정)/1 red(준비)로 완료됐으나 모니터링 프로세스 처리에 턴을 추가 소모.
- a5a591026c7faff51 (32턴, 동일 세션): scope — "Report complete... FINAL_RC=1(red-judgment 게이트 2건)"까지 보고. 선언 게이트 수가 많아 정상 완료도 한도를 넘김.
- a21e3c8162afd018e (30턴, 31-checkout dc4e93db 세션): scope — "모든 게이트 실행 결과를 제출" 정상 완료, 게이트 수가 한도 대비 많음.

### measurement-lane (한도 60, 도달 2/5건)
자체 확인.
- a19e91873bcf31a56 (64턴, 31-checkout 5fdc4e57 세션): other — `lifecycle begin --gate` 인자가 셸 변수 확장 시 파싱 실패하는 문제를 재현·우회하느라(2·3·72개 인자 케이스 비교) 턴 소모.
- ab1cf59cefaaefb1b (60턴, 이 워크트리 d406d55c 세션): scope — "Bad file descriptor / ambiguous redirect / unbound variable 0건" 전 로그 검사까지 마치고 한도 근접 종료.

## 결론 요약

(1) maxTurns 과소/과다 관측
- researcher: p90 49.8 · max 128, 한도 30. 도달률 68/118(58%). 한도 과소.
- advisor: p90 13.8 · max 23, 한도 12. 도달률 22/73(30%). 한도 과소(단, 정상 종료 케이스도 다수 포함되어 lane-worker/researcher만큼 심하지 않음).
- lane-worker: p90 222.8 · max 800, 한도 200. 도달률 14/102(14%). p90이 한도를 넘어 과소 신호가 있으나, 도달 사례 다수가 병렬 레인 대기(acce597) 등 구현 외 턴 소모를 포함 — 한도 자체보다 대기 처리 설계 문제와 겹쳐 있음.
- gate-runner: p90 27.9 · max 84, 한도 20. 도달률 4/18(22%). 도달 런은 게이트 선언 수가 많거나(정상 완료) 모니터 프로세스 처리가 끼어든 경우로, median 9 는 한도 20 대비 여유 — 과소 신호는 p90/max 국한.
- measurement-lane: p90 62.4 · max 64, 한도 60. 도달률 2/5(40%, n 작음). p90/max 가 한도에 근접 — 과소 신호.
- 과다로 판정할 역할 없음(모든 역할이 median < 한도이며, 한도를 median 기준으로 넉넉히 초과 배정한 경우 없음).

(2) 오케스트레이터의 기본 모델 override
- researcher: 기본 sonnet → opus 계열(opus 89 + opus-5-5 9) 98/118건.
- advisor: 기본 fable → opus 계열(opus 6 + opus-5-5 14) 20/73건.
- lane-worker(opus 기본, opus/opus-5-5 계열만 관측), gate-runner(haiku 기본, haiku만 관측), measurement-lane(sonnet 기본, sonnet만 관측): override 없음.
