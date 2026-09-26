VERDICT: ACCEPT-WITH-CHANGES

**실측 대조(4건 + 부수 2건)** — 경로는 `WT/` 기준
- G1(A-5) 유지 — `scripts/harness/pr_contract.py:36-38` Plan-Ref 는 placeholder 정규식만. head 트리 존재·scope diff 대조 없음. 주장 정확.
- G2(A-4) 유지 — `scripts/harness/hooks/lifecycle_contract.py` 에 `approved`·`locked`·`max_open` 0건. spec 은 WATCH 경로(`:25-26`)·researcher 금지(`:261-266`)로만 등장. `--spec` 자체가 2-5 계획분이라 G2 는 중복 아닌 확장.
- G3(A-9) 유지·조정 — `.claude/skills/to-spec/SKILL.md:3` description 평탄화 · `disable-model-invocation` 부재 확인(원본 `:3-4`). 이 세션의 skill 목록에도 「Claude에서 공통 to-spec 절차를 연결한다」로 도달 → 결과 실증. **단** `scripts/agent-bridge.py:98-110` 이 이미 adapter 존재·원본 참조·길이를 대조한다 → `check.py` 에 `check_skill_adapters()` 신설은 중복. 그 루프에 description 동일성·플래그 승계 2조건을 얹는 것으로 조정(3-3 C6 과 같은 자리).
- G8(A-13) 유지 — `scripts/harness/` 에 metrics 류 파일 없음. 비차단·PR 4 뒤 그룹 M 배치는 적절. PR 2/3/4 병합 조건에 넣지 않는다.
- A-12 조정 — 「`harness.yaml` 에 role 키 0건」은 오기. `.agents/harness.yaml:46` `"roles": [advisor, gate-runner, lane-worker, measurement-lane, researcher]` 존재(이름만 · 기대값 없음). 격차 자체는 성립, 문장만 정정.
- A-7 유지 — `harness.yaml:97-99` 집합 = AGENTS.md·CLAUDE.md·`.claude/rules/*.md` 확인. AGENTS.md 가 `dual-agent.md` 선독을 지시하는 것도 확인.
- A-2 유지 — `intent_ref.py:41-49` 「승인」 문자열 판별 확인. 단 G2 의 ⑴도 같은 `classify()` 에 의존하므로 G2 의 강도 = 문자열 강도. 제안문에 이 한계를 명기.

**격차/제안 판정**
- G4(RED 시험 lock) 조정·보류 — 선행 advisor 가 기각한 ⓒ′ 의 재상정. 2-8(test-file-guard 역할·scope 분기)과 기능 중첩 · lifecycle `--lock` + hook 분기 + handoff 대조 3곳 신설은 PR 2 범위 초과. 분석자 자신이 「Stage 4 그룹 신설」을 대안으로 적었으니 그쪽으로 넘기고 PR 2 에서 제거.
- G5 ⑶(`lanes.max_open`) 기각 — 열린 task 계수는 `.git/colab-harness/<checkout>/` 단위라 clone 30–33 간 상호 불가시 → 명시한 위험(타 clone 게이트 오염)을 못 막는다. 게이트 동시성은 이미 host mutex(`cb30d344`)가 담당. 오케스트레이터 1인 구성에서 레인 수 상한 게이트는 플레이북 anti-pattern(사람을 임계 경로에 되돌림)에 가깝다. ⑴⑵ advisory 는 유지.
- G6(Advisor-1-Ref) 유지·조정 — 2-2 `VERDICT:` 행과 같은 형식이므로 비용 낮음. 단 ① 원문은 관행상 저장소 밖(`~/.claude/reports/…`)이고 `dev-package/reports/` 는 lifecycle WATCH 경로라 레인 선언이 추가로 필요. 헤더 값에 「저장소 경로 또는 sha256+절대경로」 둘 다 허용으로 조정.
- G7 유지·조정 — `always_on_files` 에 dual-agent.md(303행) 추가는 즉시 red(예산 120). 실효 대안은 AGENTS.md:10 지시 축소이며 이는 PR 4 문서 축소와 동일 파일 → 별도 항목 대신 PR 4 에 흡수. 새 게이트 없음.
- G1·G2 는 PR 2 같은 파일 확장이라 유지. 단 G1 ⑶「spec 최초 커밋 ≤ 첫 non-doc 커밋」은 rebase·squash 로 시각이 뒤집혀 오탐 → 경고 전용으로 한정.
- 충돌표 1·2·3·5·7·8 유지. 6 은 G5 ⑶ 기각과 함께 「사람 절차」로 판정 변경. 4 는 Stage 4 소관 기록 유지.

**분석자가 건너뛴 플레이북 항목(Build 단계) 3건**
1. formatter/linter PostToolUse hook — A-10 에 「0」이라 적고 제안 없음. 플레이북이 가장 싼 deterministic hook 으로 드는 항목이며 CI red 턴 소모를 직접 줄인다.
2. 커밋 단위 = plan 단계 단위 · 에이전트 커밋 메시지 규약(트레일러 전수) — 충돌 7 에 `[미확인]` 으로만 남기고 대조표 행 없음. `git log --format=%(trailers)` 한 줄로 실측 가능.
3. Codex 경로의 permission allowlist/deny 부재(recut §5-7) — 「미적용」만 기록, 대응 layer 지정 없음. Workflow 레인 bypass 에서 `deny` 적용 여부 시험은 PR 3 병합 조건에 반드시 포함.

**Risks**: G4 를 PR 2 에 넣으면 2-8 과 이중 분기로 hook 판정이 갈린다 · G3 를 `check.py` 에 별도 신설하면 agent-bridge 와 두 판정기가 drift 한다.
**Fixes**: 차단급 — G5 ⑶ 삭제 · G4 PR 2 에서 제거 · A-12 문장 정정. 개선 — G3 를 agent-bridge 루프 확장으로 · G6 헤더 값 형식 · G1 ⑶ 경고 전용 · G7 을 PR 4 로 흡수 · 위 3건 행 추가.