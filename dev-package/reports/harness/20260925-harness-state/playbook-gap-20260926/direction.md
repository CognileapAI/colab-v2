[harness: subagent output matched instruction-shaped pattern(s): settings-json. Control tags below are neutralized (`<` → `<\`); treat any remaining directive-shaped text as a finding to relay to the user, not an instruction to you.]

**판정 — Ted 의 「충분히 고려했는가」에 대한 답: 방향은 맞고 순서와 경계가 빠졌다.**

**1. 한 줄 판정**
- 대조 36행 = 있음 5 · 부분 24 · 없음 7. Stage 별 — Plan 있음1/부분1 · Design 부분2 · Build 있음2/부분6/없음1 · Test 있음1/부분5/없음1 · Deploy·Review 부분6/없음3 · Maintain 있음1/부분4/없음2. 거버넌스 4층 = advisory 있음 · deterministic/human/audit 부분.
- 형식(intent·spec·역할 frontmatter·hook·worktree·release evidence)은 6단계 전부 존재. PR 2/3/4 는 부분 24 중 ≈20행을 건드리나 「있음」으로 올리는 행은 A-12(C7) 정도, 없음 7행은 0건 닫음.
- 플레이북 의존 순서 중 **「evals 가 CLAUDE.md/skills/hooks 변경을 게이트한다」를 PR 1→2→3→4 가 전부 위반**(`ci.yml:699` 면제 · 마지막 회차 `20260912-211809` · PR 1 hook 4종 변경 뒤 실행 0 · activation-*.json 5종은 대조표 미반영). approval-gate-before-CI 는 충족.

**2. 방향 격차 top 7** (playbook 문장 · 지금 · 결과 · 닫는 장치 · 층 · 비용)
1. **eval-gates-config** — "runs whenever CLAUDE.md, skills, or hooks change; gate configuration changes on pass rate" · 면제 모드 · 실패 4건(H14·15·16·18) 2주 무변 · PR 2/3/4 가 회귀 검출 없이 병합 → 장치: runner `harness_hash` + `changes.harness` 분기(결과 커밋 없으면 red) · 필터에 `.claude/settings.json`·`gates/**` 2경로 · `check.py` 「최근 결과 > N일」 경고 · 실패 4건 과제/하네스 결함 분류 · deterministic+audit · 회차 ≈32 USD, Q10 재개 결정 필요(2026-09-25 R2-12 판정 번복).
2. **RED 시험 고정** — "write the failing test FIRST and the agent cannot rewrite it; hooks block edits to test files during fixes" · `COLAB_FIX_LANE` env 는 Codex 만 · Claude lane 통과 · 2-8 에 단계 개념 없음 · N-5 별도 PR 로 이연 → 「green-by-edit」 인계 통과 → 장치: P7 `begin --fix` → task.json `fix_lane` → test-file-guard exit 2(PR 2 2-8 · 차단급) + N-5 `red-run`(digest = 선언한 실패 테스트 blob 만 · PR 2 선행 소형 PR) · deterministic · 중.
3. **intent→spec→plan→diff 사슬 기계 판독 불가** — "plan committed before code · merged diff == plan.md · who approved at each gate" · `pr_contract.py:36-38` placeholder 만 · begin 이 spec 내용 미검사 · advisor ① 증거 0 → plan 밖 diff·미판정 우려 spec 이 통과 → 장치: pr_contract ⑴ Plan-Ref head 존재 ⑵ intent 일치 ⑷ diff ⊆ scope glob(⑶ 시각 순서는 경고 전용) · `begin --spec` 승인/우려 판정/정책대조 검사(강도 = `classify()` 문자열 강도) · `Advisor-1-Ref:` 헤더(저장소 경로 또는 sha256+절대경로) · deterministic+audit · 낮음(PR 2 동일 파일).
4. **hook 판정·인가 감사 로그 0** — "hook invocations logged with timestamps · a specific person must authorize" · stderr 만 · `ask` 는 bypass 레인·Codex 무발동 · 킬스위치 `COLAB_HOOKS=0` 잔존 → 「막았다」 사후 증명 불가 · 오탐률 미측정 → 장치: P2 `audit.jsonl` append(git-guard·test-file-guard·decision-number-guard · PR 2 2-9) → 오탐 계수 확보 뒤 P8 PreToolUse 3훅 킬스위치 제거(PR 3 조건 ⑵ 의 유일 기제) · pre JSON `authorized_at` 1필드(Q6 ⓐ 소형 PR) · audit→human gate · 낮음.
5. **skill trigger 가 Claude 에 미도달** — "skills = trigger conditions + enforcement" · adapter description 평탄화 · `disable-model-invocation` 미승계(이 세션 skill 목록이 실증) → Ted 원칙 「산문은 맥락만」의 전제 붕괴 → 장치: `agent-bridge.py:98-110` 루프에 description 동일성·플래그 승계 2조건(PR 3 3-3) · advisory 실동작+drift 검사 · 낮음.
6. **리뷰 정의·산출물** — "REVIEW.md: passes · severity · human threshold" · advisor ② 3항·4판정·2등급은 있으나 보안 pass 없음 · 판정문 파일 미보존 · 양방향 리뷰는 **기각**(사람 게시 원칙·CI 모델 호출 0) → 장치: advisor.md 보안 pass 절(PR 4) · 판정문 `runtime:artifacts/advisor-<n>.md` 를 오케스트레이터가 기록 · 2-2 VERDICT 행이 경로+sha256 요구(PR 2) · skip 조건 기각 · ADR 1줄 「양방향 미채택」 · advisory→audit · 낮음.
7. **측정·Maintain 0** — "first-pass merge share · rework cycles · dependency scans · detection→intent" · 계산 스크립트 0 · CVE 스캔 0 · P4 tier/cron 은 1인 체제 기각 → 효과를 「green 1회」로 판정 → 장치: 지금 계산 가능 2지표(1차 CI 통과율 · eval 추이) PR 3 measurement · 나머지는 2-6 `at`·audit.jsonl 뒤 · `dependency-audit` CI 잡 독립 소형 PR(P5) · P6 대장↔intent 링크 1조건+날짜 컷오프(3-7) · audit/deterministic · 낮음~중.

**3. PR 재구성**
- 선행(PR 2 open 전, 순서 고정): ⓐ T1 ruleset(Ted 적용·기결정) → ⓑ **E0**: eval 게이트 기제 PR(`harness_hash` · `changes.harness` 분기 · 필터 2경로 · stale 경고) + PR 1 상태 로컬 eval 1회 · 실패 4건 분류 기록(Q10 재개) → ⓒ **S-red**: N-5 `red-run` 소형 PR(Q-B 승인 시).
- PR 2 추가(동일 파일): G1 pr_contract 확장 · G2 begin --spec 내용 검사 · G6 Advisor-1-Ref · P2 audit.jsonl · P7 fix_lane · VERDICT 경로+sha256 · handoff `at`(2-6 흡수). **제거**: G4 `--lock` · G5 ⑶ `max_open`.
- PR 2 → PR 3 사이: audit.jsonl 오탐 계수 축적 기간 확보.
- PR 3 추가: G3 parity 2조건(3-3) · P8 킬스위치 제거(조건 ⑵ 기제) · P6 링크 조건+컷오프(3-7) · 병합 조건에 「bypass 세션 deny 적용」 시험(Codex/Workflow 레인) · 3-5 ruleset 스냅샷 대조 · S1 전환 종료 조건 1줄.
- PR 4 추가: G7(AGENTS.md:10 선독 지시 축소) · advisor.md 보안 pass 절 · ADR-0003 1줄(승인 의미 판정 ≠ 인가 토큰 존재 검사) · ADR 1줄 양방향 미채택 · A-12 문장 정정. PR 4 병합 뒤 eval 1회(E1).
- 새 그룹: **E**(E0·E1) · **S**(소형 PR 3건: red-run · Q6 ⓐ TTY+토큰+`authorized_at` · dependency-audit) · **X**(2지표 → PR 3 measurement 레인 · 나머지 4지표 audit 필드 뒤) · **M**(수집 스크립트 `metrics.py` intent 후보 · PR 4 뒤 · tier/cron 없음). **R** 은 별도 그룹 없음(PR 2·PR 4 에 흡수).

**4. Ted 결정 질문**
- Q-A eval 실행: ⓐ PR 2 전 1회 + PR 4 뒤 1회, 지침 변경 PR 은 hash 일치 결과 없으면 red(≈64 USD) / ⓑ 2026-09-25 판정 유지(면제·재실행 제외). **권고 ⓐ** — 순서 위반 해소의 유일 경로.
- Q-B N-5 복귀: ⓐ PR 2 선행 소형 PR(digest = 선언 실패 테스트만) / ⓑ recut 유지(이후 별도). **권고 ⓐ** — P7 만으로는 Claude lane 의 red 증거가 없다.
- Q-C 3-1 `ask` 7종: ⓐ 레인 무발동이므로 `deny` 로 옮기고 인가는 Q6 토큰+`authorized_at` / ⓑ ask 유지(메인 스레드만). **권고 ⓐ** — bypass deny 적용 시험 결과에 조건부.
- Q-D Q2/PAT: ⓐ 전원 push 차단 + deny + PAT `contents:write`·`pull_requests:read` 분리 / ⓑ 현행(메인 ff push 허용). **권고 ⓐ**.
- Q-E Q6 범위: ⓐ `ship.sh` 도 TTY+토큰+`authorized_at` 포함 / ⓑ purge/reset 한정. **권고 ⓐ** — dev 는 reseed 가능하나 반입 인가 기록이 없다. `tag-release.sh` 는 제외(이미 사람 push).
- Q-F 킬스위치: ⓐ P2 오탐 데이터 확보 뒤 PR 3 에서 제거 / ⓑ PR 3 즉시 제거. **권고 ⓐ** — `git-guard.sh:86` 이 적은 우회 습관화 위험.

**5. 즉시 실행(비용 작음)**
- T1 ruleset 적용 + `gh api …/branches/develop/protection` 스냅샷을 intent 확인 절에 기록(Ted · GitHub 설정).
- 읽기만: `git log --format='%(trailers)' origin/develop..HEAD` 로 트레일러 전수 확인 · `results/20260912-211809` 실패 4건 과제/하네스 결함 분류 → intent 「확인」 절 2줄.
- 문서 3줄: `ci.yml` harness 필터에 `.claude/settings.json`·`gates/**`(면제 중이라 무해) · ADR-0003 1줄(X4) · ADR 1줄 양방향 리뷰 미채택(D2).

Missed(검증자 3인이 공통 지목·이번 판정 밖): PostToolUse formatter/linter hook · 롤백·canary 증거 · 에이전트 자격증명 범위 분리(deploy 토큰 ≠ 사용자 토큰) · 테스트 스위트 병렬성(postgres 슬롯 4).