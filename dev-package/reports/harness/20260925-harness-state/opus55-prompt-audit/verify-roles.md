[harness: subagent output matched instruction-shaped pattern(s): settings-json. Control tags below are neutralized (`<` → `<\`); treat any remaining directive-shaped text as a finding to relay to the user, not an instruction to you.]

VERDICT: ACCEPT-WITH-CHANGES

- `.agents/roles/lane-worker.md:13-14` · `researcher.md:15-16` (F1 · H1·H2) — 조정 — 인용 원문 일치 확인. 4패턴 명명 재작성은 타당하나 H1 마지막 문장 「handoff 뒤 또는 오케스트레이터 없이는 못 움직일 때만 종료」가 같은 파일의 승인된 정지 3종(:27 HEAD 불일치 → 정지·보고, :42 진입조건 미충족 → 보고, :63 경계)과 문면상 충돌한다. 대체: 「End the turn only after `handoff --mode complete` has run, or at one of the sanctioned stops: entry condition unmet (순서 1), HEAD mismatch (첫 줄), a 경계 case, or an irreversible/destructive action.」 H2 는 그대로 수용.
- `lane-worker.md:10-11` · `researcher.md:12-13` (F2 · H3·H4) — 조정 — 인용 일치. 단 prompt-audit.md:109 는 Opus 5 over-verification 계열을 「keep as the starting point and test each removal」로 규정하므로 rewrite 전에 Step 7 프로브(스크래치 사본에서 lane 1건 전후 비교)가 선행 조건. 문안 자체는 정책 보존이라 수용 가능. Codex(gpt-5.6-sol)가 같은 본문을 읽으므로 프로브는 Claude 만이 아니라 bridge 경로도 1회.
- `.claude/settings.json:2` · `.claude/agents/lane-worker.md:5` (F3 · A2) — 유지 — frontmatter `effort: high` 실측 확인. 값 미변경·측정 설계로 두는 판단이 맞다. A2 규모(3과제×2레벨×2회 = Opus lane 12회)는 과하니 lane 2과제로 줄여 시작.
- `lane-worker.md:72` (F4 · H5) — 조정 — 인용 일치. 대체문의 「오케스트레이터가 읽지 않은 채 advisor ② 에 넘기는」은 사실이 아니다(:73 은 gate-summary 경로·3계수를 넘긴다는 뜻이고 최종 메시지는 메인이 읽는다). 그 절 삭제 후 「항목마다 판정에 필요한 값 한 줄씩 · 과정 서술·반복 요약 제외」만 남긴다.
- `researcher.md:87` (F4 · H6) — 유지 — 사용자 전역 규칙 「경로 + 한 줄 요지」와 정합.
- `scripts/harness/hooks/worktree-setup.sh` (F5 · H7) — 조정 — 행 번호 오기: 인용 문구는 :267-269 에 있다(:254-256 은 report 호출부). 문안 교체는 수용. `gates/run.sh:330-336` 에 `COLAB_TEST_ENV_SOURCED` 있음 확인 — else 분기는 낡은 base 트리에서만 도달하므로 「병합 전까지」 제거가 맞다.
- `scripts/harness/hooks/css-edit-audit.sh` (F6 · H8) — 조정 — 이 트리는 C12 전환이 이미 적용됨(:76 이 printf→JSON, `echo "$OUT"` 없음). H8 diff 는 그대로 적용 불가. 대체: :76 의 `sys.stdin.read()` 앞에 범례 문자열을 붙이는 형태(`"[css-audit] 칸 = 파일 · <13px … 대비<4.5. 판정은 frontend-visual 게이트가 한다.\n" + row`). 범례 내용은 :74-75 주석과 일치.
- `lane-worker.md:52` (F7) — 유지 — flag 무변경. intent 인용은 추적성 규약.
- `researcher.md:75` (F8) — 유지 — 「8번째」는 maxTurns 50 절단 대비이므로 어떤 모델에서도 유효. 선택 부기 「— 턴 한도 절단 시 산출물이 남도록」 채택 권고.
- `ponytail-inject.sh:12-13,71` (F9) — 유지 — flag. 근거가 compaction 이라 해로움 미입증.
- `bootstrap-diet.sh:89-91` (F10) — 유지 — 이유 부착 1건.
- `lane-worker.md:16-23` (F11) — 유지 — 코드 강제(`test-file-guard.sh`)·사용자 규칙과 일치.
- `researcher.md:20` (F12) — 유지 — flag. 뒤 문장은 저장소 고유 실패 사례.
- `advisor.md:49` · `measurement-lane.md:4-11` (F13) — 유지 — 범위 밖 기록.
- A1 시간 신호 (lane-worker 추가) — 기각 — 후반 「Waiting on another lane is never a use of time」은 :52 와 중복(keep 8). 전반 「the earlier a green narrow gate the better」는 순서 3 「red 를 실제로 확인」과 충돌해 red 확인 생략을 유도할 수 있고, 공식 문서의 time signal 은 하네스가 실제 경과 시간을 붙일 때 효과가 있는 것이지 프롬프트 한 문장이 아니다. 하네스가 elapsed 를 주입하는 변경(Workflow 스크립트 그룹)과 함께 재검토.
- A3 보류 — 유지.

누락 findings:
1. `lane-worker.md:38` 「사용자 승인 없는 커밋은 하지 않는다」 vs `:52` 「green 상태로 커밋하고 인계」 · `:70` 「커밋 = 한 WU 의 한 논리적 단계」 — 같은 파일 안의 모순. Opus 5.5 는 문면을 그대로 따르므로 「커밋 승인을 묻는 비차단 질문으로 턴 종료」(F1 이 막으려는 4패턴 중 하나)를 유발한다. F1 보다 조기 종료에 직접적. 대체: :38 을 「push·병합·원장 등재는 승인 범위를 따르고, 자기 브랜치 커밋은 WU 단계마다 한다」로 정리(1c near-duplicate/충돌 · High).
2. `researcher.md:75` 「질문이 3개를 넘으면 부모에게 분할을 요청한다」 — 수치 트리거로 턴을 끝내고 되묻는 규칙. Opus 5.5 조기 종료 패턴(계속할지 묻기)과 같은 형태. 대체: 「질문은 우선순위 순으로 답하고, 턴 한도에 걸린 나머지는 산출 파일에 `미조사` 로 남긴다」(Medium).
3. `researcher.md:12-16` 와 `lane-worker.md:10-14` 는 두 파일에 거의 동일 문장(자동 인용 규칙 + 조기 종료 규칙)이 복제돼 있다 — H1–H4 적용 시 한쪽만 고치면 Codex bridge 와 Claude 가 서로 다른 문안을 읽는다. 감사는 두 hunk 를 각각 냈지만 「동시 적용·문안 동일 유지」 조건을 diff 에 명시해야 한다(keep 8 · 절차 지적).

검증 한계: `model-migration.md:1860-2061` 은 출력이 33KB 로 절단돼 첫 문단만 확인(「Opus 5 prompts perform well out of the box · Opus 5 patterns remain a starting point」). 공식 페이지의 4패턴 원문·`medium ≥ Opus 5 high` 수치는 감사자 인용에 의존 `[미확인]`.