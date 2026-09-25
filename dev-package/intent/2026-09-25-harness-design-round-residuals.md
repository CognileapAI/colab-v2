# Intent: design-review·design-fix 20260924 회차에서 드러난 하네스 잔여 — 무엇을 따지고 어떤 증거를 모을지
메타 — 발의자: agent(PR #141 병합 뒤 잔여 수집 · 초안) · 작성 2026-09-25 · 승인 미승인(초안)

## 문제
- design-review 20260924 회차와 design-fix(PR #141 · 병합 커밋 `a808a56f`) 동안 하네스 결함·공백이 여러 건 드러났다. 기록은 PR 본문 「하네스 후속」, 레인 보고(`dev-package/sessions/design-fix-20260924-*.md`), 판정 기록(`dev-package/sessions/design-review-20260924.md` §10), 사용자 메모리(저장소 밖)에 흩어져 있다.
- 승인 intent `dev-package/intent/2026-09-24-harness-lane-hygiene.md` 는 「재개봉 금지: 예(잔여 결함은 새 intent)」다. 그 intent 가 다루지 않았거나 일부만 다룬 결함을 담을 intent 가 develop 에 없다(2026-09-25 intent 는 design-fix · external-harness-gap · reset-nonempty-gate 셋).
- 결함 일부는 판정을 틀리게 만든다: 증거 파일이 서로 덮여 `frontend-visual` 페이지 수가 적게 나온다(A37) · 계측 열이 늘 0 이다(`live_probe.js`) · 선언한 게이트 인자가 조용히 버려진다(`gates/run.sh`) · develop 이 움직였을 뿐인데 판정 실패(1)가 난다(`required-gates`).

## 원한 결과 (proposed outcome)
- 아래 항목마다 develop(`a808a56f`) 대조 상태(해소 · 부분 · 미해소)와 근거가 한 곳에 있다.
- 항목마다 「따질 것」에 Ted 판정이 기록되고, 채택한 것은 spec(advisor ① → 레인)으로 넘어간다. 이 문서는 구현하지 않는다.
- 「모을 증거」가 채워져, 판정이 추론이 아니라 실측에 기대게 된다.

## 가치 가설
- 오케스트레이터와 레인은 증거 덮어쓰기·조용한 인자 무시·거짓 red 가 사라지면 재실행과 우회에 쓰는 턴·토큰이 준다.
- Ted 는 게이트 결과(green/red)를 제품 상태로 그대로 읽을 수 있게 된다.
- 확인 방법: 다음 design-review 회차에서 같은 우회(질의 순서 바꾸기 · develop 병합 push · 규율로 대신한 test-file-guard · 격리 워크트리로 피한 handoff)가 필요했는지 건수로 센다.

## 영향 범위
- 사용자 / 화면: 없음(하네스만).
- 파일(판정 뒤 구현 시 후보): `.agents/skills/design-review/scripts/{live_audit.sh,live_probe.js}` · `.agents/skills/design-review/SKILL.md` · `.agents/roles/researcher.md` · `.agents/skills/colab-v2-work/SKILL.md` · `scripts/harness/hooks/{test-file-guard.sh,lifecycle_contract.py}` · `scripts/harness/verify_evidence.py` · `gates/run.sh` · `gates/tools/*` · `frontend/scripts/visual-baseline/*` · `docs/development/*.md`.
- 서비스 · 스키마 · 계약: 없음.
- 계약 파괴 여부: 아니오.
- 이 초안 자체는 문서만 바꾼다. 코드 변경 0.

## 제약
- 승인 intent `2026-09-24-harness-lane-hygiene.md` 를 다시 열지 않는다. 그 intent 가 일부만 다룬 항목(H4 · H5 · H8)은 「그 intent 가 다룬 것 / 남은 것」을 가른다.
- 훅 정의를 바꾸면 PC 마다 `/hooks` 재신뢰가 필요하다(사용자 몫 · `docs/development/dual-agent.md:87`–`89`).
- 판정은 CLI·게이트에서 한다(ADR-0003). 게이트 종료코드 규칙 = 성공 0 · 판정 실패 1 · 준비 실패 78(AGENTS.md).
- 게이트는 호스트 단독 순차로 돌린다. 레인 병렬 게이트는 판정을 오염시킨다.

## 항목 (develop `a808a56f` 대조)

| # | 항목 | 상태 |
|---|---|---|
| H1 | A37 `live_audit.sh` 파일 이름 60자 절단 | 미해소 |
| H2 | `live_probe.js` 가 `@layer` 안 규칙을 세지 못함 | 미해소 |
| H3 | `COLAB_FIX_LANE` 이 Claude 레인 훅 환경에 닿지 않음 | 미해소(훅) · 대체 수단 있음(#140 `--scope`) |
| H4 | 같은 워크트리를 쓰는 researcher 들의 lifecycle handoff 거부 · SKILL §2-2 항목 7 충돌 | 미해소 |
| H5 | lifecycle begin(`runtime:artifacts`) 대 스킬·역할의 `dev-package/sessions` 지시 | 부분 |
| H6 | develop 이 움직이면 `required-gates` 병합 부모 대조 red | 미해소(저장소 문서 0) |
| H7 | `gates/run.sh` 가 여분 인자를 조용히 버림 | 미해소 |
| H8 | 워크플로 advisor · measurement-lane 의 StructuredOutput 실패 | 부분 |
| H9 | 레인 로컬 브랜치 이름 충돌(`fixlane-work`) | 미해소 |
| H10 | #130 병합 뒤 할 일(`/hooks` 재신뢰 · researcher 라이브 스모크) 기록 없음 | 미해소(기록 0) |
| H11 | 캡처 장면 사각 | 미해소 |
| H12 | `tsconfig.audit.json` 이 어느 게이트에도 없음 | 미해소 |
| H13 | 시각 대조 게이트 승격 | 판정 대기 |
| H14 | `design-review/SKILL.md:101` 붙어 버린 문장 | 미해소 |
| H15 | `frontend-test` 부하 시 대기 초과 — flake 와 결함을 가르지 못함 | 미해소 |
| — | A39 게이트 잠금 fd 상속 | **해소(#130)** |

### H1 A37 `live_audit.sh` 파일 이름 60자 절단
- 상태: 미해소. `.agents/skills/design-review/scripts/live_audit.sh:29` 가 develop 에서도 `cut -c1-60` 이다. #130 · #131 · #138 · #140 어느 것도 이 줄을 고치지 않았다.
- 증상: 다크 URL 이 라이트 짝이나 다른 다크 URL 과 같은 파일 이름이 되어 증거가 덮인다. `index.md` 행은 URL 마다 남지만 `gates/tools/frontend-visual.sh:108` 은 디스크에 남은 `*.probe.json` 만 센다 → 덮인 페이지의 small · lowContrast 가 판정에서 빠지고 페이지 수가 적게 나온다(34 URL → 「페이지 18」). 딸린 사실: audit 장면에는 `set media dark` 가 먹지 않아 다크 URL 을 따로 선언해야 한다(acceptance A37).
- 이번 회차의 우회: `theme=dark` 를 질의 맨 앞에 둠.
- 근거: `dev-package/sessions/design-fix-20260924-acceptance.md` A37 · `-integration.md` 「게이트」 · `-F-final.md` §3 · `dev-package/prd/specs/S-DESIGN-FIX-20260924.md` 「통합 수정」 · PR #141 「하네스 후속」.
- 따질 것: 이름을 URL 해시로 만들지 · 전체 slug 로 둘지 · 충돌을 검출해 78 로 둘지. 페이지 수를 파일 수가 아니라 선언 URL 수와 대조할지.
- 모을 증거: 현재 선언 URL 집합에서 60자 절단 충돌 건수 · 해시 이름으로 바꿨을 때 `index.md` 와 파일의 대응.

### H2 `live_probe.js` 가 `@layer` 안 규칙을 세지 못함
- 상태: 미해소. `.agents/skills/design-review/scripts/live_probe.js:38`–`44` 는 최상위 `ss.cssRules` 만 돌고 `CSSLayerBlockRule` 안으로 들어가지 않는다. `frontend/src` CSS 가 P2a 이후 `@layer` 로 감싸여 `activeRules`·`reducedMotionBlocks`·`keyframes` 열이 실제보다 적게(`:active` 는 늘 0) 나온다.
- 영향: design-fix intent 원한 결과 1(「`:active` 규칙 수가 기준값 2 보다 늘어난다」)을 이 계측으로 판정하지 못했다(vitest 원문 단언과 실브라우저 a1–a8 계산값으로 대신 확인). `frontend-visual` 판정은 small · lowContrast 만 보므로 게이트 판정에는 영향이 없다. lane-hygiene intent 의 「jsdom `@layer` 미계산」은 `frontend-test` 쪽 일이라 이것과 다르다.
- 근거: `dev-package/sessions/design-fix-20260924-L1.md` §6 · spec 「통합 수정」 · PR #141 「하지 않은 것」·「하네스 후속」.
- 따질 것: 재귀 순회(`@layer` · `@media` · `@supports` 안) 로 고칠지 · 열 자체를 없앨지(게이트가 쓰지 않는 열).
- 모을 증거: 재귀 순회로 센 값과 `css_audit.py` 정적 계수의 대조.

### H3 `COLAB_FIX_LANE` 이 Claude 레인 훅 환경에 닿지 않음
- 상태: 미해소(훅) · 대체 수단 있음. `scripts/harness/hooks/test-file-guard.sh:32` 는 환경 변수만 읽는다. `scripts/agent-bridge.py:278` 은 Codex 쪽 env 전달만 한다. Claude 레인 세션의 훅 환경에 이 값을 넣을 수단이 없다.
- 이번 회차: 레인 6개 모두 「훅을 걸 수 없어 규율로 지켰다」고 적었다. 확인 근거는 구현 커밋별 변경 파일 목록(시험 · `gates/` · `contracts/` 0)이다. 그런데 `.agents/skills/design-review/SKILL.md:101`·`:106` 은 여전히 `COLAB_FIX_LANE=1` 로 돈다고 적는다.
- 대체 수단(#140): `begin --role lane-worker --scope <glob>`(`docs/development/lifecycle-evidence.md:87`–`95`)으로 구현 단계 task 를 `frontend/src/**` 로 열면 시험 편집은 인계 때 거부된다. 막는 시점이 편집 순간이 아니라 인계다.
- 근거: `dev-package/sessions/design-fix-20260924-{L1,L2,L3,F-css,F-preview,F-upload}.md` 「하지 않은 것」 · spec 「통합 수정」 · PR #141 「하네스 후속」.
- 따질 것: ⓐ `test-file-guard` 가 env 대신 task 선언(역할 · scope)을 읽게 할지 ⓑ SKILL 문구를 `--scope` 절차로 바꾸고 훅은 Codex 전용으로 둘지 ⓒ 둘 다.
- 모을 증거: `--scope` 로 연 레인에서 시험 파일 편집이 인계 때 실제로 거부되는지 1회 실측.

### H4 같은 워크트리 researcher 들의 lifecycle handoff 거부 · SKILL §2-2 항목 7 충돌
- 상태: 미해소. `scripts/harness/hooks/lifecycle_contract.py:26`(`WATCH`) · `:384`–`385`(HEAD 변경 거부) · `:387`–`389`(read-only 는 변경 0) · `:390`–`394`(artifacts 모드 · `this task has unhanded output`)가 감시 경로 전체를 begin baseline 과 비교한다. 같은 워크트리의 다른 레인 파일도 「내 변경」으로 잡힌다. 줄 번호 `:325`·`:332`–`333`(`design-review-20260924.md` §10)은 audit 당시 값이다.
- 충돌: `.agents/skills/design-review/SKILL.md` §2-2 항목 7(「같은 워크트리에서 … 레인은 파일만 쓰고 경로를 돌려준다」 · 커밋은 메인이 순차로)이 바로 이 공유 워크트리 구성을 지시한다.
- 이번 회차 사실: L3 · L4a · L4b 인계가 거부됐다. L1 은 우회 task `463994a2` 를 열어 자기가 쓰지 않은 L2 · L3 · L4b 파일을 산출물로 선언했다(출처 기록 오류). fix 단계는 레인을 격리 워크트리로 나눠 피했다(spec).
- lane-hygiene intent 가 다룬 것: R2(researcher 실행 중 같은 체크아웃 커밋 금지 · 커밋이 필요하면 `isolation: worktree`). 다루지 않은 것: 형제 레인 파일 충돌.
- 추론(코드 읽기 · 미실측): #130 의 R1 훅은 모든 researcher 에 read-only task 를 자동으로 연다. 그러면 같은 체크아웃에서 다른 레인이나 메인이 파일을 하나만 바꿔도 read-only 인계까지 거부된다.
- 근거: `dev-package/sessions/design-review-20260924.md` §10 · PR #141 「하네스 후속」.
- 따질 것: ⓐ SKILL §2-2 를 「레인은 `runtime:artifacts/` 로 쓰고 메인이 저장소로 옮긴다」로 바꿀지 ⓑ 레인마다 `isolation: worktree` 로 돌릴지 ⓒ 감시 범위를 task 선언 산출물 기준으로 좁힐지(코드 변경).
- 모을 증거: 같은 워크트리에서 researcher 2건을 동시에 돌려 R1 자동 task 의 인계 결과 1회 실측.

### H5 lifecycle begin(`runtime:artifacts`) 대 스킬·역할의 저장소 경로 지시
- 상태: 부분. `scripts/harness/task_state.py:66`–`68` 은 새 산출물을 `runtime:artifacts/<파일>` 로만 받는다(저장소 경로는 `--legacy` 명시 때만 · `docs/development/lifecycle-evidence.md:24`·`:102`).
- 해소된 쪽(#130): R1 훅이 agent_id 와 `begin --agent-id <id> --artifact runtime:artifacts/<파일>` 명령을 출력한다. `lifecycle write-artifact`(`lifecycle-evidence.md:107`)로 L4a 를 막았던 identity 문제를 넘을 길이 생겼다.
- 남은 쪽: `.agents/roles/researcher.md:27` 은 쓰기 허용 자리를 `dev-package/sessions/`·`reports/`·`intent/` 로 적고, `.agents/skills/design-review/SKILL.md` §2-2 항목 5(`:63`)는 `dev-package/sessions/design-review-<YYYYMMDD>-L<n>.md` 에 쓰라고 지시한다. 둘 다 새 task 규칙과 맞지 않는다.
- 이번 회차 사실: L4a begin 실패 · write-artifact 「external edit requires assigned task and agent identity」 · L4b `--legacy`(`design-review-20260924.md` §10).
- 따질 것: H4 와 뿌리가 같다 — 같은 판정에서 문구를 정리한다.
- 모을 증거: R1 훅 출력대로 `runtime:artifacts` 에 쓴 researcher 1건의 인계 성공 여부(H10 스모크와 함께).

### H6 develop 이 움직이면 `required-gates` 병합 부모 대조 red
- 상태: 미해소(저장소 문서 0). `scripts/harness/verify_evidence.py:57`–`58` 은 PR 병합 커밋의 부모가 이벤트의 base/head 와 정확히 같아야 통과한다. GitHub 의 PR base SHA 는 PR 을 연 시점 값에 머문다(PR #141 실측: base `23cdf03c` 고정 · 병합 커밋 부모 `bf261d4a`). PR 을 연 뒤 develop 에 무엇이 병합되면 `required-gates`·`ci-required` 가 매 push 마다 red 다.
- 분류: `EvidenceError` 는 판정 실패(1)로 나간다(`verify_evidence.py:362`–`365`). 준비 실패(78)가 아니라서 제품 실패처럼 보이고, 같은 PR 의 진짜 실패(`frontend-gates`)와 섞여 보였다.
- 해소 절차(이번 회차): develop 을 PR 브랜치에 병합해 push(커밋 `dc0446fd` · `Intent-Ref` 트레일러 포함) → base 갱신 → 전 검사 green. 이 절차는 저장소 문서에 없고 사용자 메모리 `required-gates-stale-pr-base.md`(저장소 밖)에만 있다. #140 이 넣은 코드라 lane-hygiene 범위 밖이다.
- 근거: 커밋 `dc0446fd` 메시지 · PR #141 「추가 — CI 실패 대응」 2차 실패.
- 따질 것: ⓐ `colab-v2-work` PR 절차에 해소 절차를 문서화 ⓑ 부모 불일치를 78 로 재분류 ⓒ 대조 기준을 이벤트 base 대신 현재 base 브랜치 머리로.
- 모을 증거: #140 이후 이 오류로 red 가 난 PR 건수 · 대조 기준을 바꿀 때 막으려던 위조 경로가 다시 열리는지(#140 설계 근거).

### H7 `gates/run.sh` 가 여분 인자를 조용히 버림
- 상태: 미해소. `gates/run.sh:9` `GATE="${1:-}"` — `run.sh a b c` 는 a 만 돌리고 b · c 를 버린 채 exit 0 을 낸다(2026-09-24 lane-hygiene 검토에서 실측).
- 근거: `dev-package/intent/2026-09-24-harness-lane-hygiene.md` 「부수 발견」(범위 밖으로 둠).
- 따질 것: 여분 인자를 준비 실패 78 로 처리할지 · 여러 게이트 순차 실행을 허용할지. 「선언하면 검사한다」 규칙과의 정합.
- 모을 증거: 저장소 안 `gates/run.sh` 호출부 중 인자를 둘 이상 넘기는 곳의 수(스킬 · 문서 · CI).

### H8 워크플로 advisor · measurement-lane 의 StructuredOutput 실패
- 상태: 부분. 저장소 기록 0 · 사용자 메모리 `workflow-advisor-model-and-schema.md`(저장소 밖)에만 있다 — `agentType: 'advisor'`·`'measurement-lane'` 에 `schema` 를 걸면 「completed without calling StructuredOutput」로 워크플로가 멈췄다(3회).
- 해소된 쪽: 커밋 `0e33ce02`(#131)가 한도를 바꿨다 — `.claude/agents/advisor.md:7` maxTurns 16(PR #141 레인 기준 트리 `783095c7` 에서는 12) · `researcher.md:7` 50 · `measurement-lane.md:7` 60. lane-hygiene R3 의 「도구 8회 이하 뒤 판정」도 들어갔다.
- 남은 쪽: 워크플로 schema 호출과 measurement-lane 종료 훅(최종 메시지 형식)의 상호작용을 다루는 규칙·문서가 없다. 원인이 그 상호작용인지는 검증하지 않았다.
- 따질 것: schema 없이 「첫 줄 `VERDICT:`」 텍스트로 받는 현행 우회를 규칙으로 올릴지 · 종료 훅이 schema 호출을 허용하게 할지.
- 모을 증거: 주 체크아웃 pull(에이전트 정의 16 반영) 뒤 schema 를 건 advisor · measurement-lane 각 1회 재현.

### H9 레인 로컬 브랜치 이름 충돌(`fixlane-work`)
- 상태: 미해소. 수정 레인 지시문이 모든 레인에 같은 로컬 브랜치 이름 `fixlane-work` 로 `checkout -B` 를 시켜, 레인 간 ref 가 되돌려졌다(F-preview · 커밋 손실 0). 저장소의 `.agents/`·`.claude/agents/`·`docs/` 에는 이 이름이 없다(grep 0) — 지시문 쪽 문제다.
- 근거: `dev-package/sessions/design-fix-20260924-F-preview.md` 「브랜치 이름 충돌」 · PR #141 「하네스 후속」(추가 관찰).
- 따질 것: `colab-v2-work` 지시문 체크리스트에 「레인마다 고유 브랜치 이름(워크트리 이름 기반)」 한 줄로 충분한지 · 레인 워크트리 생성 쪽에서 강제할지.
- 모을 증거: 공유 git common dir 에서 `checkout -B` 가 다른 워크트리의 체크아웃된 브랜치를 건드리는 조건 재현 1회.

### H10 #130 병합 뒤 할 일 기록 없음
- 상태: 미해소(기록 0). #130 PR 본문이 병합 뒤 할 일로 둔 두 가지 — 이 PC `/hooks` 재신뢰(SubagentStart researcher · PostToolUse ponytail)와 researcher 1건 라이브 스모크(첫 정지 H6 통과 · Start/Stop agent_id 일치) — 의 결과가 저장소에 없다. 「agent_id 일치」는 계획 문장으로만 있다.
- 근거: `dev-package/reports/harness/20260924-lane-hygiene-review/PR-BODY.md:37`·`:53` · `dev-package/prd/specs/S-HARNESS-LANE-HYGIENE-20260924.md:44` · `docs/development/lifecycle-evidence.md:42`(「agent_id 일치가 증명되지 않았으므로 … 대조하지 않는다」) · `docs/development/dual-agent.md:87`–`89`.
- 선행: 주 체크아웃 develop pull(현재 `7acd0fce` · `git worktree list`) → 사용자가 `/hooks` 재신뢰.
- 따질 것: 스모크 결과를 어디에 기록할지(이 intent 의 판정 절 · lifecycle-evidence 문서). 일치가 확인되면 다음 intent 에서 `--agent-id` 부착을 다시 따진다(spec :44).
- 모을 증거: 스모크 1회의 훅 출력 agent_id · Stop payload agent_id.

### H11 캡처 장면 사각
- 상태: 미해소. 캡처 대조가 보지 못하는 상태: 편집 모드 · `.vfilter.on` · 확대 미리보기 · 모자이크 · 오류·로딩 · `AppLayout`/`AuthGate` 분기 · hover/focus/`:active` · dragover · 계정 모달 · `.colmenu` · 상세 편집 상태. audit 의 preview · detail 장면에는 확대 요소가 없다(`[data-zoom-scale]` 0). upload-metadata · upload-link 장면은 마지막 click 뒤 포인터가 남아 다음 기준부터 hover 상태가 섞인 채 비교된다.
- 근거: `dev-package/reports/design-system/20260924/architecture.md` §7 후속 4 · `dev-package/reports/design-review/20260924/fix/capture-diff.md` §6 · §8 · `fix/live/index.md` §0 예외 · PR #141 「캡처에 드러나지 않는 항목」.
- 대상 파일: `frontend/scripts/visual-baseline/scenes.json`. 장면을 추가하면 명세 sha256 이 바뀌어 `--subset` 또는 기준 재촬영이 필요하다.
- 따질 것: 어느 상태부터 장면으로 만들지(디자인 후속 intent `2026-09-25-design-fix-followups.md` (b)-6 의 「재지 못한 상태」를 대신할 수 있는지) · 포인터 잔류는 장면 끝에 포인터를 치우는 단계로 풀지.
- 모을 증거: 장면 추가 1건당 캡처 시간 증가분.

### H12 `tsconfig.audit.json` 이 어느 게이트에도 없음
- 상태: 미해소. audit 진입점(갤러리 포함)의 타입 검사는 `frontend/package.json` `audit:build`(`tsc --noEmit -p tsconfig.audit.json`)에만 있고 `gates/`·`.github/` 에는 `tsconfig.audit` 참조가 없다(grep 0).
- 근거: `architecture.md` §7 후속 5(P0 후속).
- 따질 것: `frontend-typecheck` 게이트에 합칠지 · 별도 게이트로 둘지.
- 모을 증거: 현재 트리에서 `tsc --noEmit -p tsconfig.audit.json` 결과와 소요 시간.

### H13 시각 대조 게이트 승격
- 상태: 판정 대기. `visual:capture`·`visual:diff` 는 단계마다 수동 실행이다(캡처 약 8분 · agent-browser 필요). 계산값 대조 도구(`dev-package/reports/design-system/20260924/p2b/states/cdump.py`·`compare.py`)를 `frontend/scripts/visual-baseline/` 로 옮길지도 함께 열려 있다.
- 근거: `architecture.md` §7 후속 6(P1 우려 4 · P2a 후속 3 · P3 후속 7).
- 선행이던 A39(같은 도구 경로의 잠금 fd 누수)는 #130 으로 해소됐다(아래).
- 따질 것: 게이트로 올릴지 · 올린다면 기준 캡처를 어디에 둘지(무시 파일 `frontend/.visual/` 은 워크트리를 지우면 사라진다).
- 모을 증거: 호스트 단독 순차 조건에서 캡처 1회 소요 시간 · 기준 세트 크기(이번 `fix0924-*` 세트 34MB).

### H14 `design-review/SKILL.md:101` 붙어 버린 문장
- 상태: 미해소. `.agents/skills/design-review/SKILL.md:101` 에 「…편집을 막는다보호된 fix 구현 단계에서…」로 두 문장이 붙어 있다. 커밋 `c1de5e31`(공통 경로 이전)에서 생긴 것으로 조사됐다 — 이번 회차 잔여가 아니다.
- 따질 것: H3 의 SKILL 문구 정리와 한 커밋으로 고칠지.

### H15 `frontend-test` 부하 시 대기 초과 — flake 와 결함을 가르지 못함
- 상태: 미해소. `frontend/test/dataset-preview-source-grid.test.tsx` 의 `findByTestId('preview-map')` 이 부하가 걸리면 1000ms 를 넘기고, 합친 트리에서 unhandled error 1 이 났다. 단독 실행과 최종 run 은 green 이다. 게이트에서는 `frontend-test` red 로만 드러나 flake 와 결함이 구분되지 않는다.
- 근거: 디자인 후속 intent `2026-09-25-design-fix-followups.md` (c)-5 · 설계트리 Q8c(2026-09-25 Ted 판정으로 이 intent 에 옮김) · `dev-package/sessions/design-fix-20260924-F-upload.md` §5 · §6 · `dev-package/sessions/design-fix-20260924-acceptance.md` 머리(병합 검사) · PR #141 「알려진 한계」 마지막 줄.
- 따질 것: 부하를 어떻게 재현할지(레인 동시 실행 · CPU 제한) · 대기 한도를 늘릴지, 원인(렌더 비용)을 고칠지 · 게이트가 재시도 없이 flake 를 따로 표시할 방법.
- 모을 증거: 부하 조건별 실패율(단독 · 동시 N) · 실패 때의 소요 시간 분포.

### 해소 확인 — A39 게이트 잠금 fd 상속
- 상태: **해소(코드 · #130)**. `frontend-visual` 이 띄운 agent-browser 데몬이 호스트 게이트 잠금 fd 를 물려받아 게이트가 끝난 뒤에도 쥐던 결함은 develop 에서 고쳐졌다 — F1 `b549d75d`(`gates/tools/_lock.sh:143` `gate_mutex_spawn` · `gates/tools/frontend-visual.sh:84`) · F2 `ab3de17e`(`live_audit.sh:20` EXIT trap) · #130 병합 `b50047f4`.
- 이번 회차에 재현된 이유: design-fix 레인의 기준 트리가 develop `7acd0fce`(#130 이전)였다. `dc0446fd` 병합으로 이 브랜치와 develop 에 F1 · F2 가 모두 들어 있다.
- 남은 일(결함 아님): ① 주 체크아웃이 아직 `7acd0fce` 라 거기서 돌리는 게이트에는 수정이 없다 — develop pull ② 수정 뒤 실제 레인에서 재발하지 않는지는 아직 관측하지 않았다 — 다음 게이트 run 에서 관찰 ③ F1 이 없는 다른 체크아웃(30 · 31 저장소)도 같은 `/tmp/colab-v2-gate-host-mutex/host` 를 쓴다(#140 PR 본문 「남은 제약」).
- 근거: PR #141 「하네스 후속」 A39 · `dev-package/sessions/design-fix-20260924-acceptance.md` A39 · `dev-package/reports/harness/20260924-lane-hygiene-review/C-browser-cleanup.md`.

## 설계트리 (grill-me 결과)
- 미실시 — 초안이다. Ted 판정 뒤에 채운다.

## 미해결 질문
- Q1 H1 · H2 · H7 · H12 는 판정이 단순한 결함 수정이다 — 한 spec 으로 묶을지.
- Q2 H3 ⓐ/ⓑ/ⓒ 중 무엇.
- Q3 H4 · H5 ⓐ/ⓑ/ⓒ 중 무엇. design-review 스킬의 레인 구성 자체가 바뀐다.
- Q4 H6 ⓐ/ⓑ/ⓒ 중 무엇. 재분류(ⓑ)와 기준 변경(ⓒ)은 #140 의 설계 판단을 다시 따지는 일이다.
- Q5 H8 · H10 은 관측부터 할지(주 체크아웃 pull → `/hooks` 재신뢰 → 스모크).
- Q6 H11 · H13 을 이 intent 에서 다룰지, 디자인 시스템 쪽 별건으로 뺄지.
- Q7 H9 · H14 는 문서 한 줄 — 다른 항목 spec 에 얹을지.

## 범위 밖 (명시 제외)
- 구현. 이 문서는 무엇을 따지고 어떤 증거를 모을지만 적는다.
- 승인 intent `2026-09-24-harness-lane-hygiene.md` 가 이미 다룬 것: A39(③ F1 · F2 · 해소) · 턴 한도 재단(① R1–R4) · 증거 경로 규격(②) · advisor ① 생략 기준(④).
- 디자인 후속 — `dev-package/intent/2026-09-25-design-fix-followups.md`.
- 워크트리 · 브랜치 · 임시물 정리, 주 체크아웃 pull(사용자 작업 공간).

## 확인
- 프론티어 공집합 확인: (미실시)
- Ted 확인 문장(원문 그대로): (없음 — 미승인 초안)
- 재개봉 금지: 아니오(초안)

## 참조
- PR #141 — 병합 커밋 `a808a56f`(2026-09-25) · 「하네스 후속」·「추가 — CI 실패 대응」 · 본문 사본 `~/.claude/pr-bodies/PR-BODY-design-fix-20260924.md`(저장소 밖)
- 승인 intent: `dev-package/intent/2026-09-24-harness-lane-hygiene.md` · spec `dev-package/prd/specs/S-HARNESS-LANE-HYGIENE-20260924.md`
- 회차 기록: `dev-package/sessions/design-review-20260924.md` §10 · `dev-package/sessions/design-fix-20260924-{integration,acceptance,L1,L2,L3,F-css,F-upload,F-preview,F-final,F-int,F-ci}.md`
- 계획: `dev-package/reports/design-system/20260924/architecture.md` §7 후속 4–6
- 하네스 문서: `docs/development/lifecycle-evidence.md` · `docs/development/dual-agent.md` · ADR-0007 `docs/decisions/0007-intent-ref-trailer-and-append-only-approved-intents.md`
- 결정: 신규 legacy 결정번호 발급 없음(AGENTS.md).
