# Intent: 하네스 개선 — 막는 장치 · 판정·증거 · 문서 drift (잔여 H1–H15 흡수)
메타 — 발의자: Ted · 작성 2026-09-25 (agent 초안 · 하네스 분석 원자료 ~/.claude/reports/harness-state-20260925/ 는 저장소 밖) · 승인: 그룹 A — Ted 2026-09-25 원문 "전부 권고대로"(A1–A5 권장안) · 그룹 B · L · C · T 판정은 끝의 「판정 기록」 절에 줄로 추가한다
- 대체 — dev-package/intent/2026-09-25-harness-design-round-residuals.md(미승인 초안)의 H1–H15 를 흡수한다(H11·H12·H13·H15 는 제외 절).
- 구성 결정(Ted 2026-09-25 원문 "좋아 그렇게해보자"): umbrella intent 1 · spec 1(3 phase) · PR 3 순차 · 그룹 단위 /grill-me · H11·H12·H13·H15 제외 · GitHub 설정 등은 Ted 몫(그룹 T).
- 표기: 줄 번호 기준 develop `67a03a05` · 2026-09-25. 「메인 재현 2026-09-25」 = 오케스트레이터 재현. 「probe 재현」 = 격리 clone · payload-only 재현. 「문서 근거」 · 「관측 1회」 · 「미검증」 은 실측이 아님. 출처 칸의 R<n>-… = 저장소 밖 findings-verified.md 항목 ID, 「초안 H<n>」 = 흡수 초안 항목. 본문의 H6/H7 = lifecycle 인계 검사 hook.
- `-missed` 출처 항목은 adversarial verify 를 거치지 않은 판독자 추가 발견이다. 공백 `-C` 우회 · `pull`(메인 재현) · task 결속(L2 · probe 재현) 외에는 섹션 작성자가 코드를 다시 열어 확인한 줄만 적고 「verified」로 표기하지 않는다.

## 문제
- 현재 기준선: develop `67a03a05` 에서 harness-contract · `agent-bridge check` · agent-bridge gate(unit test 156 · skip 10) · adr-records(ADR 9) 가 green 이다(분석 실측 2026-09-25 · plain mode). 아래는 그 green 이 잡지 못하는 것이다.
- 막는 장치가 일상 명령 형태에서 꺼진다. 저장소 경로에 공백이 있어 `git -C "<repo>" …` 형태에서 git-guard 가 모든 규칙을 건너뛴다(`scripts/harness/hooks/git-guard.sh:167` 비인용 `set -- $seg`). develop 위 `push --force origin develop` · `branch -D develop` · subagent `push origin develop` · `push origin main` 이 모두 rc=0, 같은 명령 `-C` 없이는 rc=2(메인 재현 2026-09-25). develop 위 `pull --no-ff` · `pull --no-rebase` 도 rc=0(같은 자리 `merge --no-ff` 는 rc=2).
- 원격 방어선이 없다. develop branch protection 은 `required_status_checks` null · `required_pull_request_reviews` null(force push · 삭제 금지만), 규칙셋은 23379713 product-promotion-policy(product) 하나, `docs/development/github-ruleset.json` 은 존재하지 않는 `refs/heads/main` 을 대상으로 한다(메인 재현 2026-09-25) → develop 에서 red CI 가 병합을 막지 않는다.
- test-file-guard 는 Claude lane 에서 켜지지 않는다. `test-file-guard.sh:32` 는 `COLAB_FIX_LANE=1` 이 없으면 exit 0 이고 `.claude/` · 역할 파일에서 이 값을 주는 곳이 0건(메인 재현 2026-09-25). 문서(design-review SKILL `:101` · `:106`, `dual-agent.md:60`)는 편집 시점 차단을 기술한다 → Claude 에서 남는 것은 인계 시점 H7 scope 대조뿐이다.
- 게이트 호출 실수가 신호 없이 지나간다. `gates/run.sh:9` 는 `$1` 만 읽어 `run.sh a b c` 는 a 만 실행하고, 알 수 없는 gate 는 host mutex 를 잡은 뒤 exit 2(0/1/78 밖)로 끝난다. 집계기마다 1 과 78 의 우선순위가 달라 같은 결과가 경로마다 다르게 보고된다(B3).
- 거짓 red 가 반복된다. PR 을 연 뒤 develop 이 앞서면 `required-gates` 가 병합 부모 대조(`verify_evidence.py:57-58`, 메인 재현 2026-09-25)로 red — 재발 3회(#141 · #151 · #160). 해소 절차(develop 수동 병합)는 사용자 메모리에만 있다.
- 판정 증거가 틀리게 모일 수 있다. frontend-visual probe 파일 이름 60자 절단으로 증거가 덮이고 게이트는 선언 URL 수가 아니라 파일 수를 센다(B7). researcher H6 은 에이전트가 최종 메시지에 적은 task 로 판정해, 제품 파일을 고친 뒤 새 begin 으로 연 task 로 read-only 인계가 통과한다(L2 · probe 재현 2026-09-25 · payload-only).
- lifecycle 기록이 쌓이기만 한다. `.git/colab-harness` 153 MB · task.json 204 · checkout key 42 · 사라진 checkout 의 task 74건이고 close · prune 수단이 없다(메인 재현 2026-09-25 · L1).
- 문서 · 설정이 코드와 어긋나고 해소 절차가 저장소 밖에 있다. measurement-lane 역할 본문 「프로세스 간 뮤텍스가 없다」(코드는 serial 게이트에 host mutex), README 「훅 7개」(등록 11), decision-number-guard 가 로컬에 없는 `origin/main` 을 기준으로 삼는다(C1 · C2 · C5). develop 병합 · researcher `runtime:artifacts` · StructuredOutput 우회는 사용자 메모리에만 있고, #130 병합 뒤 할 일(`/hooks` 재신뢰 · researcher 스모크)의 저장소 기록은 0건이다.

## 원한 결과 (proposed outcome)
- 그룹 A(PR 1): 공백 경로 `-C` · 인용 경로 · 대상 checkout 형태에서 git-guard 규칙 ⑴–⑷ 가 unittest 로 rc=2 고정되고, 메인 재현 명령 6종을 수정본 스크립트로 재실행하면 rc=2 다. Claude lane 의 보호 경로 편집이 판정한 방식(A2)대로 막히고 문서가 그 동작과 일치한다. `run.sh` 여분 인자 · 빈 인자 · 알 수 없는 gate 는 78 + stderr 이고 host mutex 획득 기록이 0 이다.
- 그룹 B(PR 2 전반): develop 이 앞선 PR 이 develop 병합 커밋 없이 `required-gates` green 이다(관측 1회). 입력 조합 표 {1 · 78 · 1+78 · 111 · 표식만}에서 모든 집계기가 같은 exit code 를 낸다(unit test). `gates.required` 가 생산자 등록부와 대조된다. frontend-visual 페이지 수 == 선언 URL 수다. service-tests 실행 뒤 `/tmp/service-tests-*` 수가 늘지 않는다.
- 그룹 L(PR 2 후반): handoff 성공 task 에 종료 기록이 남고 prune dry-run 이 사라진 checkout 의 task 를 나열한다. 「제품 파일 변경 → 새 researcher begin」 이 거부되는 시험이 green 이다. lane 이 부모 checkout 에서 스폰되면 구현 전에 정지한다. `harness-contract-selftest` 가 lifecycle 시험을 돈다.
- 그룹 C(PR 3): 각 항목 완료 기준의 drift 문자열 grep 이 0건이고, ruleset JSON · guard 기준 ref 가 develop 을 가리키며, Claude skill adapter 의 명시 호출 플래그가 본문과 일치하는지 agent-bridge check 가 검사한다.
- 그룹 T(Ted): T1 · T3 · T4 · T5 · T6 의 판정과 실행 결과(`gh api …/branches/develop/protection` 출력 · 브랜치 목록 · 재신뢰 기록)가 이 intent 확인 절에 기록된다.

## 가치 가설
- Ted 와 에이전트는 막는 장치가 명령 형태와 무관하게 동작하고(A), 게이트 red 가 결함일 때만 나고(B), 인계 증거가 스폰 task 에서 벗어나지 않으면(L) 우회 · 재실행 · 수동 병합에 쓰는 턴이 줄고 green 을 제품 상태로 읽을 수 있다.
- 에이전트는 역할 본문 · README · 규칙 문서가 코드와 일치하면(C) 틀린 전제(뮤텍스 없음 · origin/main 기준 등)로 절차를 고르지 않는다.
- 확인 방법: 세 PR 병합 뒤 PR 요약 「원한 결과 ↔ 실제 ↔ 근거」 표로 센다 — ⑴ 메인 재현 명령 6종 · pull 2종 rc ⑵ develop 수동 병합 커밋 수(기준: 재발 3회) ⑶ `run.sh` 인자 오류의 exit code ⑷ 사용자 메모리에만 있던 우회 절차(develop 병합 · runtime:artifacts · StructuredOutput)의 다음 회차 사용 건수 ⑸ `.git/colab-harness` task 수 · 용량 추이(prune 적용 시).

## 영향 범위
- 사용자 / 화면: 없음 — 개발 하네스.
- 서비스 · 스키마 · 계약: hooks(`scripts/harness/hooks/*`) · gates(`gates/run.sh` · `gates/tools/*` · `gates/README.md`) · CI workflows(`.github/workflows/ci.yml` · 새 workflow 후보) · harness scripts(`scripts/harness/*.py` · `scripts/agent-bridge.py` · `.agents/ci-producers.json` · `.agents/harness.yaml`) · 시험(`scripts/tests/*`) · design-review 스크립트(`live_audit.sh` · `live_probe.js`) · 역할 · 스킬 · 문서(`.agents/**` · `.claude/skills` adapter · `.codex/agents` · `docs/development/*` · `README.md`). 제품 코드(`frontend/src` · `services/**` · `contracts/**`)와 `frontend/scripts/visual-baseline/` 은 변경 0.
- 계약 파괴 여부: 아니오 — 제품 API · 스키마 · `contracts/**` 무변경. 바뀌는 것은 하네스 내부 판정 규칙(A4 알 수 없는 gate 2 → 78 · B1 병합 부모 기준 · B3 집계 우선순위)이고, B3 규칙은 새 ADR(판정 대기)로 기록한다.

## 제약
- fail-closed guard 가 세션을 멈추면 안 된다. git-guard 는 모든 Bash 호출이 거친다(`.claude/settings.json:58-66`) → tokenizer 결함 1건 = Bash 정지. 파싱 실패는 현행 분리 규칙으로 폴백하고 envelope 계약(`git-guard.sh:81-83`)은 바꾸지 않는다(A1). 새 차단(A2 · L2 ⓑ · C5)은 거부 메시지에 출구를 적는다. Edit/Write 복구 경로는 git-guard matcher 밖으로 유지한다.
- hook 수정본은 lane 자신의 호출에 적용되지 않는다(`${CLAUDE_PROJECT_DIR}` 쪽 스크립트 실행 · 문서 근거 `worktree-setup.sh:31-38`) → lane 검증은 worktree 스크립트 직접 호출로 한다.
- 게이트 도는 lane 은 한 번에 하나(postgres 슬롯 호스트 전역). 세 PR 은 순차이고 lane 병렬 게이트를 돌리지 않는다.
- 승인 intent 는 append-only(intent_ref) — `2026-09-24-harness-lane-hygiene.md` · `2026-09-25-external-harness-gap.md` · `2026-09-24-agent-model-tiering.md` 를 다시 열지 않는다. 잔여는 이 intent 에 둔다.
- ADR 이력은 고치지 않는다(superseded ADR-0002 diff 0). 새 규칙은 새 ADR.
- PR 게시 · 병합은 Ted. GitHub 설정(branch protection · ruleset) · 브랜치 삭제 · 형제 체크아웃 · `/hooks` 신뢰는 Ted(그룹 T) — 에이전트는 질문 · 선택지만 기록한다.
- 훅 정의(`.claude/settings.json` · `.codex/hooks.json`)를 바꾸면 PC 마다 `/hooks` 재신뢰가 필요하다(`dual-agent.md:87-89` · 문서 근거) → 권장안은 정의 무변경을 전제로 한다.
- 09-15 운영 범위(`R-HARNESS-PR-CENTRIC.md:4` 「전면 전환·추가 고도화는 보류한다」)는 이 intent 의 그룹 A · B · L · C 목록에 한해 다시 연다. 목록 밖 고도화는 계속 범위 밖이다.
- 게이트 종료코드 = 성공 0 · 판정 실패 1 · 준비 실패 78(AGENTS.md).

## 구현 형태
- spec 1개(3 phase) → PR 1(그룹 A) → PR 2(그룹 B + L) → PR 3(그룹 C), 엄격 순차. PR 마다 격리 worktree lane 1개가 구현하고, 다음 PR 은 앞 PR 병합 뒤 develop 기준으로 착수한다(`gates/run.sh` · `lifecycle_contract.py` · `README.md` · SKILL 문서를 PR 사이에 공유). PR 2 는 B → L 순서로 한 lane 이 구현한다(`lifecycle_contract.py` · `test_task_runtime.py` 공유).
- PR 1 크기: A1 ⓐ(argv 형태 편입 포함 · Ted 판정 2026-09-25). A2 는 분할(Ted 판정)이라 PR 1 에는 문장 정리(ⓒ)만 들어가고 편집 시점 차단(ⓐ)은 PR 2(L1 ⓐ 뒤)로 간다.
- 판정 순서: /grill-me 를 그룹 단위로 A → B → L → C → T. 그룹 A 가 승인되면 spec phase 1 · PR 1 lane 이 바로 착수하고, 나머지 그룹 판정은 PR 1 진행 중에 한다. 그룹 T 는 Ted 행동이라 PR 과 독립이며 T1 적용은 PR 2 병합 뒤, T5 는 PR 3 병합 뒤.

### 흡수 대응 (초안 H → 이 intent)
| 초안 | 이 intent | 초안 대비 바뀐 것 |
|---|---|---|
| H1 · H2 | B7 | 선택지에 공통 교정(선언 URL 수 대조 · 전체 배열 · `$OUT` 비움) 추가 |
| H3 · H14 | A2 | 초안 H3 ⓐ(task 선언 읽기) · ⓑ(문서) 틀 재사용. H14 문장 분리를 같은 항목에 편입 |
| H4 · H5 | L4 | 초안 H4 ⓐ/ⓑ/ⓒ 틀 재사용. 「researcher 끼리 막는다」는 초안에서도 추론 · 미실측 |
| H6 | B1 | 부모 대조 도입 커밋은 `414f51e7`(초안의 「#140」 정정) |
| H7 | A4 | 여분 인자는 「exit 0」 이 아니라 첫 gate 의 exit code 반환(초안 정정) · 알 수 없는 gate 추가 |
| H8 | L7 | 한도 변경(advisor maxTurns 12 → 16) 뒤 재현 먼저 |
| H9 | L3 | 부모 checkout 실행 관측 1회와 묶음 |
| H10 | T5 · L8 | 재신뢰(Ted) · 스모크(agent) 분담 |
| H11 · H12 · H13 · H15 | 범위 밖 | 디자인 시스템 후속 intent |
| A39 남은 일 | 없음 · T3 | ①(주 체크아웃 갱신)은 해소 — 31 은 `67a03a05`(#130 포함). ③(30 · 31 저장소)은 낡음 — 노출 체크아웃은 32 · 33 |

## 그룹 A · PR 1 — 막는 장치 바로잡기
- 주체: spec phase 1 → lane 1개(격리 worktree) 구현 → PR 1 게시·병합은 Ted. PR 2·3 은 이 PR 병합 뒤 순차 착수. 판정은 그룹 A 단위 /grill-me(A1–A5 일괄).

### A1 git-guard 명령 해석 — quote-aware tokenizer + 대상 checkout 브랜치 해석  (출처: R1-hooks-missed(공백 `-C` 우회 · `pull`) · R1-4 · R1-5 · R1-21 · R5-19 정정)
- 문제:
  - 우회: `scripts/harness/hooks/git-guard.sh:167` 비인용 `set -- $seg` → 공백 든 경로의 `git -C "<repo>"` 에서 `-C` 가 첫 조각만 소비(`:193` `shift 2`), 다음 조각이 subcommand 로 읽혀 모든 규칙을 건너뜀. 메인 재현 2026-09-25(develop · payload cwd = 저장소 루트): `-C "<repo>"` 를 붙인 `push --force origin develop` · `branch -D develop` · subagent `push origin develop` · subagent `push origin main` → 모두 rc=0. 같은 명령 `-C` 없이 → rc=2. 공백 없는 `-C /tmp` 강제 push → rc=2. 저장소 절대경로·lane worktree 경로에 공백 포함, AGENTS.md 가 작업 디렉터리 명시를 요구 → 이 형태가 일상 명령 형태.
  - 대상 오판(R1-4 · 코드 확인): 보호 브랜치 판정 근거는 payload `cwd` 하나(`:143`). `-C`·`--git-dir`·`--work-tree` 대상, 같은 명령 안 `cd <dir>` 뒤 명령의 브랜치는 보지 않음 → refspec 없는 push(`:234` · `:242`)·merge(`:257`)가 다른 checkout 기준으로 판정.
  - argv 형태 누락(R1-5 · 코드 확인): gh 는 첫 두 인자가 정확히 `pr` `merge` 일 때만(`:182`) → `gh -R <o/r> pr merge` · `gh api …/pulls/<n>/merge` 통과. force 는 정확 토큰만(`:207`) → 묶은 `-fu` 통과. develop 위 subagent 의 `push origin HEAD` 통과(`HEAD` 를 브랜치로 풀지 않음 `:151-156`, `:242` 는 refspec 없을 때만).
  - `pull` 분기 없음(`:202-274`): 메인 재현 2026-09-25 — develop 위 `pull --no-ff origin develop` · `pull --no-rebase origin develop` rc=0, 같은 자리 `merge --no-ff origin/feature` rc=2.
  - 오탐(R1-21 · R5-19 정정): 개행을 ` ; ` 로 바꾸고(`:106`) `&&`·`||`·`;`·`|` 를 인용과 무관하게 분리(`:149`) → heredoc 본문·인용 인자 안에서 줄 또는 segment 시작에 오는 git/gh 병합 문구를 명령으로 판정. 줄·segment 시작일 때만 해당(문자열 어디서나 아님). 초안 작성 중 재현 1회(2026-09-25): grep -E 패턴 인자 안 `|` 뒤에 온 gh 병합 문구가 ⑷ 로 차단.
  - 시험: rule 시험은 `scripts/tests/test_agent_bridge.py:463` · `:483-507`(bridge `guard-command` 경유). 공백 경로 `-C` · heredoc · `pull` · gh 변형 · `-fu` · `HEAD` 형태 시험 0건(grep).
- 선택지:
  - ⓐ python quote-aware tokenizer(heredoc 본문 제외 · 인용 밖 연산자만 segment 분리) + 대상 checkout 해석(`-C`/`--git-dir`/`--work-tree`/선행 `cd`, 없으면 payload cwd) + 누락 argv 형태를 기존 규칙 ⑴–⑷ 에 편입(gh 전역 플래그 건너뛰기 · `gh api` 는 `-X`/`--method PUT` 인 merge 경로만 · 묶은 short flag 의 `f` · `HEAD`/`@` 를 대상 브랜치로 해석 · 보호 브랜치 위 `pull --no-ff`/`--no-rebase`).
  - ⓑ tokenizer + 대상 해석만(우회·오탐 해소). argv 형태 편입은 후속 PR.
  - ⓒ 현 bash 구조 유지 · `-C` 인자만 인용 처리 + `pull` 분기 추가. heredoc 오탐 · 대상 오판 · gh/`-fu`/`HEAD` 형태 잔존.
- 권장: ⓐ — 편입 형태는 모두 기존 열거 ⑴–⑷ 의 다른 argv 이고 새 규칙이 아님(머리말 `:11` 「명시 열거 — 넓히지 않는다」 유지). 시험을 새 tokenizer 기준으로 한 번에 작성.
  - fail-closed 위험: 모든 Bash 호출이 이 hook 를 거침(`.claude/settings.json:58-66`). envelope 이상 · python3 부재는 이미 exit 2(`:81-83`). tokenizer 결함 1건 = 이 스크립트를 쓰는 모든 세션의 Bash 정지.
  - 대응(권장안에 포함): command 텍스트 파싱 실패(짝 없는 인용 등) 시 현행 분리 규칙(`:149` · `:167`)으로 판정 → 현행 대비 차단 회귀 0. envelope 계약(`:81-83`) 무변경.
  - 복구 경로: Edit/Write 는 git-guard matcher 밖(`.claude/settings.json:68-84`) → Edit 로 되돌림 가능. `COLAB_HOOKS=0` 은 세션 재시작 필요(`README.md:79-98`).
  - lane 자기 검증 한계(문서 근거 — `scripts/harness/hooks/worktree-setup.sh:31-38` 의 hooks 문서 인용): hook 는 `${CLAUDE_PROJECT_DIR}` 쪽 스크립트를 실행 → lane worktree 의 수정본은 lane 자신의 Bash 호출에 적용되지 않음. 검증은 worktree 스크립트 직접 호출로 함.
  - `.claude/settings.json` · `.codex/hooks.json` 훅 정의 무변경이 전제. wrapper 내부 변경의 코드 snapshot 비교(`docs/development/dual-agent.md:86`)는 그룹 T 확인 항목.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (Ted 판정과 일치) + 보강 2건 — ① tokenizer 예외 시 현행 `sed` 분리(`:149`)로 폴백하고 exit 2 로 올리지 않는다 ② `pull` 규칙은 명시 플래그(`--no-ff` · `--no-rebase` · `--rebase=false` · `--ff=false`)만 잡고 플래그 없는 `git pull` 은 통과시킨다 · 확신 높음
- 완료 기준: 새 unittest(agent-bridge gate 가 실행하는 파일 · `gates/run.sh:308-310`)가 다음을 모두 보이면 끝.
  - ⑴ 공백 경로 `-C "<…>"` · `-C '<…>'` 로 ⑴–⑸ · product 규칙 각각 rc=2, 허용형(기능 브랜치 push · 기능 브랜치 위 `merge --ff-only` · `pull --rebase` · `worktree` · 기능 브랜치 원격 삭제) rc=0.
  - ⑵ 기능 브랜치 cwd 에서 `-C <develop checkout>` 또는 `cd <develop checkout>` 뒤 non-ff merge · subagent 의 refspec 없는 push → rc=2.
  - ⑶ heredoc 본문 · 인용 인자 안에 git merge · gh 병합 · 강제 push 문구가 든 쓰기 명령 → rc=0.
  - ⑷ `gh -R o/r pr merge` · `gh api -X PUT …/merge` · develop 대상 `push -fu` · develop 위 subagent `push origin HEAD` · develop 위 `pull --no-ff`/`--no-rebase` → rc=2. `gh api …/merge`(GET) · `pull --ff-only` → rc=0.
  - ⑸ 짝 없는 인용 입력의 rc 가 현행 규칙 결과와 같음.
  - ⑹ 기존 시험(`test_agent_bridge.py:463` · `:483-507` · `test_harness_lifecycle_contract.py:319-346`) green · 메인 재현 명령 6종을 lane worktree 스크립트로 재실행해 rc=2.
  - ⑺ `README.md:73` git-guard 행 · 머리말 허용 목록(`:22-24`)이 편입 형태와 일치(C2 ⓑ 로 PR 3 에서 README 훅 표를 지우면 이 행은 그때 정본 링크로 대체).
- 판정 질문: 권장안 수용? — ① argv 형태 편입을 PR 1 에 넣을지(ⓐ) 후속으로 뺄지(ⓑ) ② 파싱 실패 = 현행 규칙 폴백 수용?

### A2 test-file-guard 가 Claude lane 에서 켜지지 않음 · 관련 문장 정리(H14 포함)  (출처: R1-2 정정 · R5-7 · H3 · H14)
- 문제:
  - `scripts/harness/hooks/test-file-guard.sh:32` — hook 프로세스 env 에 `COLAB_FIX_LANE=1` 이 없으면 exit 0. 값을 넘기는 곳은 `scripts/agent-bridge.py:278`(Codex) · `scripts/dev.ps1:102` 뿐, `.claude/` · 역할 파일 설정 0건(grep). hook env 는 Claude Code 프로세스 env 이므로 lane 별로 다르게 줄 수 없음.
  - 대체 수단: `begin --role lane-worker --scope <glob>` → handoff `complete` · H7 이 범위 밖 변경 차단(`docs/development/lifecycle-evidence.md:87-98`). 차단 시점 = 인계(편집 순간 아님). `.agents/roles/lane-worker.md:38` 은 지시문이 범위를 줄 때만 선언.
  - 문서 불일치: `.agents/skills/design-review/SKILL.md:101` · `:106`, `docs/development/dual-agent.md:60` 은 fix 구현 단계가 `COLAB_FIX_LANE=1` 로 돌고 hook 가 막는다고 기술. `SKILL.md:101` 은 두 문장이 붙어 있음(「…편집을 막는다보호된 fix 구현 단계에서…」, 재확인). 생성 커밋 `c1de5e31` 은 초안 조사 근거(재확인 안 함).
  - 초안 H3 대비: 상태 서술 유효. design-fix 20260924 lane 6개의 「규율로 지켰다」 기록은 초안 근거(재확인 안 함).
- 선택지:
  - ⓐ test-file-guard 가 env 외에 task 선언을 읽음(초안 H3 ⓐ): payload 에 `agent_id` 가 있는 Edit/Write 이고 payload cwd checkout 에 `--scope` 를 선언한 열린 lane-worker task 가 있으면, 대상이 보호 경로 4종(`:17-20`)이면서 그 scope 밖일 때 exit 2. 시험 작성 단계 task 는 scope 에 시험 경로를 넣어 통과. settings.json 정의 무변경.
  - ⓑ SubagentStart(lane-worker)가 `agent_id` 별 marker 를 쓰고 test-file-guard 가 PreToolUse payload `agent_id` 로 marker 를 찾음(역할 기반). 한계: 같은 lane 이 RED→GREEN 을 한 세션에서 진행(`SKILL.md:106`) → 단계 구분 불가 · SubagentStart 와 PreToolUse 의 `agent_id` 일치 미증명(`scripts/harness/hooks/researcher-task.sh:9-11` 과 같은 전제) · 새 hook 정의면 `/hooks` 재신뢰(그룹 T).
  - ⓒ hook 는 Codex 전용(env)으로 두고 `SKILL.md:101` · `:106` · `dual-agent.md:60` 을 `--scope` 절차(인계 시점 차단)로 고침(초안 H3 ⓑ).
- 권장: 분할 — PR 1 = ⓒ(문장 정리 · H14 분리 포함, 초안 H3 ⓒ), PR 2 = ⓐ(L1 ⓐ 종료 기록 위). ⓐ 의 「열린 task」는 종료 기록이 있어야 정확히 정의된다(L1 ⓐ 는 PR 2). PR 1 에서 ⓐ 를 하려면 「같은 checkout 의 가장 최근 scoped lane-worker task」로 정의해야 하고, 인계가 끝난 옛 task 가 뒤의 subagent 편집을 막는 오차단이 남는다(메인 스레드 편집은 payload 에 `agent_id` 가 없어 대상 밖). ⓐ 자체의 이점(단계 구분이 task 경계로 표현됨 `lifecycle-evidence.md:87-98` · 새 hook 정의 불필요 · 실패 면은 Edit/Write 한정)은 PR 2 에서 그대로 얻는다.
  - 전제·미검증: lane-worker task 에 `agent_id` 가 기록되지 않음(`lane-worker.md:35-38` begin 에 `--agent-id` 없음 · 기록 자리 `scripts/harness/hooks/lifecycle_contract.py:245`) → task 는 checkout 키로 찾음. lane 이 부모 checkout 에서 돈 관측 1회(R2-2) · 같은 checkout 에 이전 미인계 task 가 남은 경우 오차단 가능 → 「열린 task」 = L1 ⓐ 종료 기록 없는 scoped lane-worker task(PR 2). Workflow `agent()` 로 스폰한 lane 에서 PreToolUse hook 실행 여부 미검증.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓒ(PR 1) → ⓐ(PR 2, L1 ⓐ 뒤) 조합(Ted 분할과 일치) + 새 선택지 ⓒ′: ⓒ 문서 수정에 「fix 레인은 task 2개(시험 작성 task = scope 에 시험 경로 포함 → handoff / 구현 task = scope 에서 `frontend/test/**`·`services/*/tests/**`·`gates/**`·`contracts/**` 제외 → handoff)」 절차를 적어 코드 없이 단계 구분을 만든다 · 확신 높음
- 완료 기준(PR 1 · ⓒ): `SKILL.md:101` 두 문장 분리 · `:101` · `:106` · `dual-agent.md:60` 이 Claude lane 의 실제 동작(env 없음 → 편집 시점 차단 없음 · `--scope` 인계 시점 차단)을 기술 · `grep -n 'COLAB_FIX_LANE=1' .agents/skills/design-review/SKILL.md` 결과가 Codex/env 조건과 함께만 나옴.
- 완료 기준(PR 2 · ⓐ):
  - unittest ⑴ `COLAB_FIX_LANE` 없이 scope `frontend/src/**` 인 lane-worker task + `agent_id` 있는 Edit payload → `frontend/test/…` · `gates/…` · `contracts/…` rc=2, `frontend/src/…` rc=0 ⑵ scope 에 `frontend/test/**` 가 든 task → 시험 경로 rc=0 ⑶ `agent_id` 없는 payload · scope 미선언 task → rc=0 ⑷ 기존 env 시험(`test_agent_bridge.py:509-512` · `:537-540` · `test_harness_lifecycle_contract.py:394`) green.
  - ⑸ 종료 기록 있는 scoped task 만 있는 checkout → 시험 경로 rc=0(옛 task 오차단 없음).
  - 문서를 ⓐ 동작(env 또는 종료 기록 없는 scope 선언 task)으로 다시 갱신.
  - 실제 Claude lane-worker 1회 실측: 구현 단계 task 에서 시험 파일 Edit 가 편집 시점에 차단(초안 H3 「모을 증거」 대체).
- 판정 질문: 분할(PR 1 = ⓒ · PR 2 = ⓐ) 수용? 또는 PR 1 에 ⓐ 를 「최근 scoped task」 정의로 넣을지 · ⓒ 만 하고 ⓐ 를 버릴지?

### A3 Edit/Write guard 는 Bash 쓰기를 보지 않음 — 경계 표기  (출처: R1-7)
- 문제: migration-guard · decision-number-guard · test-file-guard 는 `Edit|Write` matcher 에만 등록(`.claude/settings.json:68-84`). git-guard 는 git/gh 만 판정(`git-guard.sh:181` · `:188`). `sed -i` · redirect · python 쓰기는 세 guard 를 거치지 않음. `README.md:116` 은 「마찰 장치이지 보안 경계가 아니다」를 `bash -c` 감싸기 예로만 적고 Bash 쓰기 경로는 적지 않음. 사용자 메모리(저장소 밖)는 Edit 차단 시 Bash 로 쓰도록 안내.
- 선택지: ⓐ 경계 표기 — README hook 절 · test-file-guard 머리말(PR 1 파일)에 「Edit/Write 도구만 대상 · Bash 쓰기는 대상 아님 · 사후 검사 수단」 명시. migration-guard · decision-number-guard 머리말의 같은 문장은 C10(PR 3 · 파일 소유) ⓑ PreToolUse(Bash)에서 쓰기 형태(`sed -i` · `>` · `tee` · `python -c`) × 보호 경로 대조 — 형태 열거 불완전 · 오탐 면 증가 · fail-closed 면이 git-guard 와 같음 ⓒ PostToolUse(Bash)에서 보호 경로 변경 감지 — 실행 후라 차단 불가, 안내만.
- 권장: ⓐ — scope 선언 task 의 handoff/H7 대조는 begin 시점 파일 전체 내용 hash 기준이라 Bash 쓰기도 드러남(`lifecycle-evidence.md:92` 문서 근거). ⓑ 는 A1 의 fail-closed 면을 키움. migration · 결정 번호의 Bash 편집에 대한 사후 검사 수단 유무는 이 초안에서 미확인 → 표기 전에 확인해 「있음/없음」으로 적음.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ + 보강 — 「사후 검사 수단」을 추상어로 두지 않고 `begin --scope` handoff/H7(baseline = 전 파일 내용 hash, `lifecycle-evidence.md:91`) 을 지명한다. 이 검사는 Edit/Write/Bash 무관하게 변경을 잡으므로 Bash 쓰기의 실제 경계다. ⓑ·ⓒ 기각. · 확신 높음
- 완료 기준: `README.md` hook 절과 test-file-guard 머리말에 대상 도구 · 비대상 경로 · 사후 검사 수단(없으면 「없음」)이 적히고 harness-contract gate green. 코드 변경 0. 나머지 두 guard 머리말은 C10 완료 기준.
- 판정 질문: 권장안 수용?

### A4 `gates/run.sh` 여분 인자 무시 · 알 수 없는 gate 가 mutex 를 잡은 뒤 exit 2  (출처: R3-5 · R5-6 정정(medium) · R3-9 일부 · H7)
- 문제:
  - `gates/run.sh:9` `GATE="${1:-}"`, `$#` 검사 없음 → `run.sh a b c` 는 a 만 실행하고 b · c 를 말없이 버린 뒤 a 의 exit code 반환(초안 H7 의 「exit 0」 은 부정확). task 결합 경로도 `$GATE` 만 전달(`:52`). `all` 은 `$2` 가 정확히 `-j` 일 때만 병렬도를 읽음(`:795`) → `all -j4` · 뒤 토큰은 말없이 -j 2.
  - 알 수 없는 gate: 미선언 gate 는 serial 취급(`:787-788`) → host mutex 획득(`:163-170`) 뒤 dispatch 에서 exit 2(`:975-977`). 인자 없음도 exit 2(`:971-973`). 2 는 0/1/78 밖(AGENTS.md), 요약기는 red_판정으로 셈(R3-9). 측정 관측 1회: 오타 gate 이름이 mutex 획득 뒤 exit 2(advisor2 §2) — 코드 경로 재확인.
  - 저장소 안 호출부 중 gate 이름을 둘 이상 넘기는 곳 0건(R5-6 정정 · git grep) → 노출은 에이전트 · 사람의 수동 실행.
- 선택지: ⓐ 인자 검사를 mutex · task 결합 앞에 둠 — 단독 gate = 인자 1개, `all` = 없음 또는 `-j <양의 정수>`, `task` = 추가 인자 없음. 위반 · 빈 인자 · 알 수 없는 gate → 버린 토큰/이름을 stderr 에 적고 78 ⓑ 여러 gate 순차 실행 허용 + 집계 exit code(초안 H7 선택지) — 집계 우선순위(R3-9 나머지, PR 2)와 얽힘 ⓒ ⓐ 와 같되 알 수 없는 gate 는 1(판정 실패).
- 권장: ⓐ — 「환경·입력 부재로 판정할 수 없는 준비 실패 = 78」(AGENTS.md)과 일치. 새 집계 규칙 불필요. 다중 인자 호출부 0건이라 호환 부담 없음.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (알 수 없는 gate 도 78). ⓒ 기각 · ⓑ 기각. · 확신 높음
- 완료 기준: 시험이 ⑴ `run.sh a b` · `run.sh all -j4` · `run.sh all -j 4 x` · `run.sh task x` → 78 + stderr 에 버린 토큰 ⑵ `run.sh no-such-gate` · 인자 없음 → 78, host mutex 획득 기록 0 ⑶ 단독 gate · `all -j N` · `task` 기존 동작 무변경을 보임. exit 2 에 기대는 기존 시험 · 도구 0건 확인(`scripts/tests` 3파일 grep 0건 — 전수 아님, `gates/tools/*selftest*` 는 spec 단계에서 확인).
- 판정 질문: 권장안 수용? (알 수 없는 gate 를 78 로 볼지 1 로 볼지)

### A5 git-guard · test-file-guard 머리말 「exit 1 은 통과」 drift  (출처: R1-9 · CT 초안 C10 에서 이관 — 파일 소유 PR 1)
- 문제: `scripts/harness/hooks/git-guard.sh:71` · `scripts/harness/hooks/test-file-guard.sh:27` 머리말 「exit 1 은 통과다 · 판정을 못 하면 통과가 기본값」. 실제는 envelope 이상 · python3 부재 시 exit 2(`git-guard.sh:81-83` · `test-file-guard.sh:38`)이고, 뒤의 `command -v python3 … || exit 0`(`git-guard.sh:90` · `test-file-guard.sh:42`)은 도달 불가(조립 시 재열람 2026-09-25).
- 선택지: ⓐ 머리말을 현행 fail-closed(envelope · python3 부재 = exit 2) 기준으로 교정 + 도달 불가 줄 삭제 ⓑ 머리말만 교정
- 권장: ⓐ — A1 · A2 가 두 파일을 고치므로 같은 커밋에 얹는다. A1 의 「파싱 실패 = 현행 분리 규칙 폴백」도 git-guard 머리말에 적는다. `migration-guard.sh` · `worktree-setup.sh` 쪽은 C10(PR 3).
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ · 확신 높음
- 완료 기준: `grep -n 'exit 1 은 통과' scripts/harness/hooks/git-guard.sh scripts/harness/hooks/test-file-guard.sh` 0건 · 도달 불가 줄 삭제 뒤 A1 · A2 시험과 기존 시험(`test_agent_bridge.py` · `test_harness_lifecycle_contract.py`) green.
- 판정 질문: 권장안 수용?

### 그룹 A 공통 · 범위 밖
- 커밋 단위: A1 + A5(git-guard 머리말)는 단독 커밋(되돌림 단위). A2(ⓒ) · A3 · A5(test-file-guard 머리말)는 `test-file-guard.sh` · `README.md` · SKILL 문서를 공유 → 한 커밋. A4(`gates/run.sh`) 단독 커밋. `README.md` 는 A1 ⑺ 과 A3 이 함께 고친다(같은 PR 안 순서 커밋).
- 전제: 권장안은 `.claude/settings.json` · `.codex/hooks.json` 훅 정의를 바꾸지 않음. 바뀌는 선택지(A2 ⓑ 등)를 고르면 `/hooks` 재신뢰가 그룹 T 로 추가됨.
- 범위 밖:
  - R1-17 reseed ACK 할당 검사(`git-guard.sh:134`)의 따옴표 · `read` · `printf -v` · Write 경로 누락 — 머리말(`:131-133`)이 보안 경계 아님을 명시. A1 tokenizer 가 인용 제거 뒤 토큰을 보면 `export "…"` 형태가 같이 잡힐 수 있으나 완료 기준에 넣지 않음.
  - 한 겹 감싼 명령(`bash -c` · `eval`) — 머리말 `:74-76` 알려진 한계 유지.
  - exit code 우선순위 불일치(R3-9 나머지: lifecycle run_gates 의 78 우선 · `all` 이 78 을 내지 않음) → PR 2(B3).
  - decision-number-guard 기준 ref `origin/main`(`decision-number-guard.sh:67`)이 로컬에 없음(`git rev-parse` rc=1, 2026-09-25) → 항상 워킹트리 폴백(`:69-72`). `README.md:74-75` 는 두 guard 기준을 `origin/main` 으로 적으나 migration-guard 코드는 `origin/develop`(`migration-guard.sh:72`) → PR 3(C2 · C5 — C5 판정 질문에 PR 1 이관 여부 포함).
  - develop required checks · ruleset · `/hooks` 재신뢰 → 그룹 T(T1 · T5 · Ted).

## 그룹 B · PR 2 전반 — CI 판정 정확도
- 대상: PR 2(판정·증거 정확도) 전반부 · PR 1 병합 뒤 착수 · 구현 = lane 1개(spec 3단계 중 2단계) · PR 게시·GitHub 설정 = Ted · 줄 번호 기준 develop `67a03a05`.

### B1 develop 이 움직이면 `required-gates` 병합 부모 대조가 red  (출처: R3-1(corrected · medium) · R5-9 · H6)
- 문제: `scripts/harness/verify_evidence.py:57`–`58` 이 PR 병합 커밋 부모 == [이벤트 `base.sha`, `head.sha`] 를 요구한다(메인 재현 2026-09-25). PR 을 연 뒤 develop 이 앞서면 `EvidenceError` → exit 1(`:362`–`365`). 재발 3회: #141(`dc0446fd`) · #151(`4e4a5a0b`) · #160(`791f7c7c`). 해소 절차(develop 을 PR 브랜치에 병합해 push)는 저장소 문서 0건 · 사용자 메모리에만 있다. `scripts/tests/test_harness_evidence.py:164`–`183` 이 엄격 대조를 고정한다.
  - 심각도 medium: fail-closed 오탐이다. develop 은 required status check 가 없어(메인 재현 2026-09-25) develop 병합을 막지는 않는다. 비용 = 반복 red + 수동 develop 병합.
  - 초안 H6 정정: 부모 대조 도입 커밋은 `414f51e7`(2026-09-15 「PR 검사 증거를 실제 병합 커밋에 결속」 · `git log -S` 기준). 초안의 「#140 이 넣은 코드」와 다르다. 「develop 병합 뒤 base.sha 가 갱신된다」는 문서 근거(PR #141 기록 · 사용자 메모리)이고 이번 분석의 실측이 아니다.
- 선택지: ⓐ 해소 절차를 `colab-v2-work` PR 절차에 문서화(코드 무변경 · red 는 계속 난다) ⓑ 부모 불일치를 `EvidenceReadinessError`(78)로 재분류(분류만 바뀌고 병합 차단·수동 병합은 그대로) ⓒ 대조 기준 변경 — 둘째 부모 == 이벤트 head(현행 유지) · 첫째 부모 = 이벤트 base 의 자손이면서 `base_ref` 이력 안의 커밋
- 검토 후 제외: ⓓ `required-gates` 재실행 — 재실행은 원래 이벤트 payload(`base.sha`)를 그대로 쓰고, base 브랜치 이동은 `pull_request` 이벤트를 만들지 않는다(`synchronize` 는 head 갱신 때만 · GitHub 문서 근거 · 미실측).
- 권장: ⓒ — 수동 develop 병합 단계 자체를 없앤다. 둘째 부모 정확 대조가 남아 head 트리 결속은 유지된다. `required-gates` checkout(`.github/workflows/ci.yml:812`)은 fetch-depth 기본 1 이라 조상 대조용 base 이력 fetch 가 추가로 필요하다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓒ(정의를 좁힌 형태) + ⓐ(잔여 사례 문서화) · 확신 중간
- 완료 기준: `test_harness_evidence.py` 에 「첫째 부모가 이벤트 base 의 자손」 사례 green 추가 · 기존 부정 사례(부모 순서 뒤바뀜 · head 불일치 · 단일 부모 · tree 불일치) EvidenceError 유지 · `base_ref` 이력 밖 첫째 부모 사례 EvidenceError 신설 · PR 을 연 뒤 develop 이 앞선 실 PR 1건이 develop 병합 커밋 없이 `required-gates` green(관측 1회).
- 판정 질문: `414f51e7` 의 결속 기준(첫째 부모 정확 일치)을 「이벤트 base 의 자손 · base_ref 이력 안」으로 푸는 ⓒ 수용?

### B2 ai-service · pipeline-worker 단독 PR 의 잠복 false red  (출처: R3-4(confirmed · medium))
- 문제: `.github/workflows/ci.yml:491` `RUN` 식은 ai-service 또는 pipeline-worker 만 바뀌어도 core-api 행을 돌려 `service-tests-core-api` 증거를 남긴다. 등록부 `.agents/ci-producers.json:398`–`403` 의 이 생산자 filters 는 `core-api` · `contracts` 뿐이다 → `verify_evidence.py:207`–`214` 가 「N/A 인데 증거 있음」 EvidenceError → `required-gates` exit 1.
  - 도입 `9adaf4db`(2026-09-18). 이후 ai 계열 병합(#151 · #154 · #160)은 모두 core-api 경로도 건드려 발현 0건(R3 기록).
- 선택지: ⓐ 등록부 filters 에 `ai-service` · `pipeline-worker` 추가(RUN 식과 일치) ⓑ RUN 식에서 core-api 추가 절 제거 ⓒ ⓐ + RUN 식과 등록부 filters 를 대조하는 시험 추가
- 권장: ⓐ — `9adaf4db` 본문 「게이트는 AI DB 를 기본 판정 범위에 넣는다」의 의도를 유지하고 등록부만 맞춘다. ⓑ 는 그 의도와 충돌한다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): 새 선택지 ⓓ — ⓐ 를 포함하되 적용 판정을 등록부에서 **한 번만** 계산: `changes` 잡에 `verify_evidence.py applicable`(가칭) 단계를 두어 생산자별 `run-service-tests-<svc>` 출력을 내고, `RUN` 은 `needs.changes.outputs[format('run-service-tests-{0}', matrix.service)]` 를 읽는다. 폴백(예산 부족 시) = ⓐ 단독. · 확신 중간
- 완료 기준: `test_harness_evidence.py` 에 filters {ai-service: true, 나머지 false} + core-api 증거 존재 사례 green · 같은 조건 증거 부재는 red(준비) 유지 · harness-contract green.
- 판정 질문: 권장안 수용? (ⓒ 대조 시험까지 넣을지 함께)

### B3 0/1/78 집계 우선순위 불일치 · 판정/준비 분류 뒤바뀜  (출처: R3-9(confirmed · medium) · R4-15(confirmed · low) · R3-gates-ci-missed(record→78) · R4-judges-evidence-missed(lifecycle ValueError→78))
- 문제: 집계기마다 우선순위가 다르다 — 판정 우선: `verify_evidence.py:137`–`143` `verdict` · `gates/run.sh:743`–`744` selftest / 준비 우선: `scripts/harness/hooks/lifecycle_contract.py:500` `run_gates` / 78 없음: `run.sh:900` · `:969` `all`(모든 비0 → 1). 111 을 준비로 세는 곳은 `run.sh:103`–`108` 뿐이다(`lifecycle_contract.py:480` 은 78 · 표식만).
  - 분류 뒤바뀜: `verify_evidence.py` `ci` 는 OSError · JSONDecodeError · SubprocessError → 1(`:362`–`365`). `record` 는 명령 불일치 · `GITHUB_SHA` 불일치(`:288`–`293`, 판정 결함) → 78(`:404`–`408`). lifecycle CLI 는 begin · handoff · run-bound-gate 의 모든 ValueError → 78(`:611`–`613`) — scope 위반 handoff 의 78 을 `scripts/tests/test_task_runtime.py:379`–`380` 이 고정한다.
  - ADR-0004 는 세 상태와 「두 red 모두 병합 차단」만 정하고 집계 우선순위는 정하지 않았다. lifecycle 경로는 이번 분석에서 실측 없음(unit test 근거). `stop` · `validate-input` 의 exit 2 는 hook 차단 코드라 대상 밖. 알 수 없는 게이트 exit 2(`run.sh:971`–`977`)는 PR 1(A4)에서 정한 값을 따른다.
- 선택지: ⓐ 판정 우선(1 > 78 > 0)으로 전 집계기 통일 + 분류 뒤바뀜 교정 + 규칙을 새 ADR 로 기록 ⓑ 준비 우선(78 > 1 > 0)으로 통일 ⓒ 현행 유지 + 집계기별 규칙 문서화
- 권장: ⓐ — exit 1 은 끝난 판정이라 다른 게이트의 준비 실패와 무관하게 결함이 있다는 뜻이다. 준비 우선은 결함을 환경 실패로 표시한다. 현행 4곳 중 2곳(`verdict` · selftest)이 이미 판정 우선이다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ — 판정 우선(1 > 78 > 0) 통일 + 분류 교정 + 새 ADR. 단 lifecycle CLI 교정은 판정성 raise 지점에만 `JudgementError(ValueError)` 를 도입하는 부분 적용. · 확신 높음(우선순위) · 중간(lifecycle 분류 범위)
- 완료 기준: 입력 조합 {1만 · 78만 · 1+78 · 111 · 표식만} 표를 unit test 로 고정 — `run_gates` · `run.sh all` · selftest · `verdict` 가 같은 값 · `record` 명령 불일치 → 1 · `ci` JSON 해독 실패 → 78 · scope 위반 handoff → 1(`test_task_runtime.py:380` 갱신) · 78 을 해석하는 호출부(스킬 · 역할 · hook) grep 대조 결과를 PR 에 첨부 · adr-records green.
- 판정 질문: 판정 우선 규칙 수용? 기록 자리는 새 ADR(0010)인지 `gates/README.md` 정본 절인지.

### B4 `gates.required` 미강제 · harness-contract · agent-bridge 미등록 생산자  (출처: R3-2(corrected · medium) · R4-2(corrected · medium))
- 문제: `.agents/harness.yaml:16`–`29` `gates.required` 12개는 문자열 · 중복만 검사하고(`scripts/harness/config.py:71`–`73`) green 줄에 개수만 찍힌다(`scripts/harness/check.py:113`). 12개 중 10개는 `.agents/ci-producers.json` 생산자에 있고 `harness-contract` · `agent-bridge` 는 0건(2026-09-25 grep) — path filter 가 걸린 PR 전용 `.github/workflows/agent-bridge.yml` 에서만 돌고 증거 기록이 없다.
  - develop 은 required status check 가 없다(메인 재현 2026-09-25) → CI red 가 develop 병합을 막지 않는다.
- 선택지: ⓐ 두 게이트를 ci-producers 생산자로 등록 · `ci.yml` 에서 `verify_evidence.py record` 로 실행 + harness-contract 가 「gates.required ⊆ 등록부 gate 집합」 대조 ⓑ 'required' 표현 제거(키 이름 변경 · green 줄 개수 삭제) ⓒ 대조만 추가하고 두 게이트는 required 에서 뺌
- 권장: ⓐ — 이름이 약속하는 것을 기계가 확인하게 한다. 추가 등록분은 2개다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ — 두 게이트를 ci-producers 생산자로 등록해 `ci.yml` 새 잡에서 `record` 로 실행 + `check.py` 에 「`gates.required` ⊆ 등록부 `checks[*].gates` 합집합」 대조. 부수: `agent-bridge.yml` 은 폐지(또는 `workflow_dispatch` 만). · 확신 중간~높음
- 완료 기준: harness-contract 가 생산자 없는 required 게이트를 red(판정)로 내는 fixture test · 두 게이트 증거가 `required-gates` 대조에 포함된 PR 1건 green · 대상 경로 밖 PR 에서 두 생산자 N/A 처리.
- 판정 질문: 권장안 수용? — 병합 차단 효과는 T1 「develop required check 지정」 판정에 달린다(지정 없으면 red 가 develop 병합을 막지 않는다).

### B5 intent-ref job 이 증거 사슬 밖 · `ci-required` 의 사유 대조 없는 skipped  (출처: R3-gates-ci-missed · R3-12(corrected) · low)
- 문제: `.github/workflows/ci.yml:665`–`679` intent-ref 는 `./gates/run.sh intent-ref` 를 record 없이 실행한다(ci-producers 등록 0 · gate-summary 0). `ci-required`(`ci.yml:843`–`872`)는 `always_required`(`:860`) 밖 job 의 `skipped` 를 사유 대조 없이 받는다.
  - 다른 job 은 모두 등록부 job 이라 `required-gates` 가 path filter 로 skip 사유를 대조한다(`verify_evidence.py:207`–`214`). 사유 대조가 없는 skip 은 intent-ref 1건이다. 현재 `if` 식으로는 develop 대상 PR 에서 skipped 가 나지 않는다 — 노출은 `if` 식이 바뀔 때 조용히 통과하는 경로다.
- 선택지: ⓐ intent-ref 를 생산자로 등록 + record 로 감쌈(적용 판정이 path filter 만 보므로 등록부에 이벤트 조건 필드 신설 필요) ⓑ `ci-required` 가 intent-ref 의 `skipped` 를 `event != pull_request` 또는 `base_ref == product` 일 때만 허용 ⓒ 현행 유지
- 권장: ⓑ — 사유 대조가 없는 유일한 skip 을 닫고 등록부 스키마는 건드리지 않는다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓑ (보강: 허용 조건을 `event_name != 'pull_request' || base_ref == 'product'` 로 job `if` 와 거울상으로 두고, `workflow_dispatch` 도 같은 식에 포함) · 확신 높음
- 완료 기준: `ci-required` 인라인 판정을 `scripts/harness/` 스크립트로 옮기고 unit test — pull_request(develop 대상) + intent-ref skipped → 1 · push + skipped → 0 · product 대상 PR + skipped → 0.
- 판정 질문: 권장안 수용?

### B6 pr_contract 가 CI 에서 돌지 않음 · `<…>` placeholder 오탐  (출처: R4-5(confirmed · medium) · R4-judges-evidence-missed(low) · CT 초안 T2 병합)
- 문제: `scripts/harness/pr_contract.py` 는 로컬 CLI 뿐이다 — `.github/` · `gates/` 에 실행 0건(`gates/run.sh:316` 은 `test_pr_contract.py` unit test 실행). 병합 PR #140 · #144 · #159 · #160 본문은 `검증 상태: 부분 검증` 이라 complete 모드 경로 사용 0건(R4-5 기록 · 판독, 재현 안 함).
  - `pr_contract.py:47` 은 필수 섹션 본문에 `<[^>]+>` 가 한 번이라도 있으면 placeholder 로 본다(조립 시 재열람 2026-09-25 · 코드 확인) → `<task_id>` · `Array<string>` 같은 정상 본문이 실패한다. 실제 PR 본문 대상 실행 재현은 없음.
- 선택지: ⓐ 별도 workflow(`pull_request` types opened · edited · synchronize · reopened)에서 `--mode draft` 실행 ⓑ 로컬 CLI 유지 + `colab-v2-work` PR 요약 절차에 실행 1줄 ⓒ pr_contract 폐기
  - placeholder 교정(ⓐ · ⓑ 공통): 줄 전체 또는 표 칸 전체가 `<…>` 일 때만 placeholder. `.github/pull_request_template.md:1`–`34` 의 자리표시는 모두 이 형태다.
- 권장: ⓐ + placeholder 교정(B 초안) — 교정 없이 ⓐ 를 켜면 정상 본문이 red 다. `ci.yml:6` 은 types 미지정(기본 opened · synchronize · reopened)이라 edited 를 넣으면 본문 수정마다 전체 CI 가 돌므로 별도 workflow 로 둔다.
  - 반론(CT 초안 T2 · ⓑ 권장): PR 게시는 Ted 몫(AGENTS.md) → CI 가 게시된 본문을 red 로 내면 게시 뒤 본문 수정 루프가 생긴다. 새 workflow 는 required 지정(T1)이 없으면 병합을 막지 않는 표시로만 남는다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ + ⓑ 조합 + 새 선택지 보강: CI 실행은 `--mode draft` 이되 Head-SHA 불일치를 구조 실패와 분리 보고(`--stale-head warn` 류 플래그 → `::warning::` + step summary, 종료 0) · 구조·placeholder 실패만 exit 1 · 확신 중간
- 완료 기준: `test_pr_contract.py` 에 인라인 `<task_id>` · `Array<string>` 본문 통과 사례 · 템플릿 원문 본문 실패 사례 추가(ⓐ · ⓑ 공통). ⓐ 면 게시된 PR 1건에서 새 workflow green(관측 1회), ⓑ 면 `colab-v2-work` 에 실행 1줄(grep 1건).
- 판정 질문: CI workflow(ⓐ)와 로컬 절차(ⓑ) 중 무엇? placeholder 교정은 공통으로 수용?

### B7 frontend-visual 증거 무결성 — 파일 덮어쓰기 · 80행 절단 · 잔존 증거 · `@layer` 미계수  (출처: H1 / R3-6(confirmed · medium) · R3-7(corrected · low) · R3-gates-ci-missed(low) · H2 / R3-8(confirmed · low))
- 문제: `.agents/skills/design-review/scripts/live_audit.sh:29` 가 slug 를 `cut -c1-60` 으로 자르고 `:35` 에서 `<slug>.probe.json` 을 써서 앞 60자가 같은 URL 끼리 덮인다. `gates/tools/frontend-visual.sh:108`–`112` 는 디스크의 probe 파일 수를 페이지 수로 세고 선언 URL 수와 대조하지 않는다(`:147` 은 0건만 red) → 덮인 페이지의 위반이 판정에서 빠진다(false green 가능).
  - `live_probe.js:56` 이 small · lowContrast 를 80행으로 자르고 게이트는 잘린 배열에 allowlist 를 적용한다(`frontend-visual.sh:126`–`127`). `gates/fixtures/frontend-visual/allow.txt` 활성 항목 0건(2026-09-25 grep)이라 현재는 잠복이다.
  - `frontend-visual.sh:67`–`75` 는 `$OUT` 을 `mkdir -p` 만 하고 비우지 않는다 → 같은 `COLAB_GATE_REPORT_DIR` 재사용 때 이전 run probe 가 합산된다.
  - H2: `live_probe.js:38`–`44` 는 최상위 `cssRules` 만 돈다 → `@layer` · `@media` 안 규칙 미계수 · `activeRules` 등 열 과소. 게이트 판정은 이 열을 읽지 않는다(design-review 보고서만 영향).
- 선택지(파일 이름): ⓐ URL sha256 앞 12자 + 짧은 slug, `index.md` 에 URL↔파일 대응 ⓑ 절단 없는 전체 slug ⓒ 절단 유지 + 충돌 검출 시 78
  - 공통 교정(이름 선택과 무관): 페이지 수 == 선언 URL 수 대조(불일치 red(판정)) · probe 가 전체 배열을 내거나 게이트가 `counts` 와 배열 길이 대조 · 게이트 시작 때 `$OUT` 비움
  - 선택지(H2 열): ⓓ `cssRules` 를 가진 규칙(`@layer` · `@media` · `@supports`) 재귀 순회 ⓔ 게이트가 쓰지 않는 열 삭제
- 권장: ⓐ + 공통 교정 + ⓓ — 파일 이름 길이가 URL 길이와 무관해지고, 선언 URL 수 대조가 덮어쓰기 · 잔존 증거를 함께 잡는다. ⓓ 는 초안 H2 의 `:active` 계측 용도를 복구한다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (slug 앞 40자 + `-` + sha256 12자) + 공통 교정 3건 + ⓓ · 확신 높음
- 완료 기준: `gates/tools/frontend-visual-selftest.sh`(실브라우저 없음)에 사례 추가 — 앞 60자가 같은 URL 2개 → probe 2개 · 페이지 수 == URL 수 · 81번째 비허용 위반 → red · 이전 run probe 잔존 → 세지 않음. `@layer` 재귀는 agent-browser 1회 실측으로 `frontend/src` 화면의 `activeRules` > 0 확인.
- 판정 질문: 권장안 수용?

### B8 `_pg.sh` trap 대체로 임시 디렉터리 누수 · operator-notifications 표식 없는 78  (출처: R3-10(confirmed · low) · R3-gates-ci-missed(low))
- 문제: `gates/tools/_pg.sh:193` `pg_start` 가 `trap pg_cleanup EXIT INT TERM` 으로 호출자 trap 을 대체한다 → `gates/tools/service-tests.sh:81`–`82` `SVC_CLEAN`(`rm -rf "$TMP"`)이 사라진다. 호스트 `/tmp/service-tests-*` 329개(2026-09-25 재측정).
  - `gates/tools/operator-notifications.sh:7` trap 도 `:10` `pg_start` 로 대체된다. `:8` · `:9` · `:11` · `:12` · `:14` 는 `::gate-readiness-failure::` 표식 없는 `exit 78` 이라 요약에 원인이 남지 않는다. CI runner 는 일회용이라 누수는 로컬 호스트 한정.
- 선택지: ⓐ `pg_start` 가 기존 EXIT trap(`trap -p EXIT`)을 읽어 `pg_cleanup` 과 이어 붙임 ⓑ `pg_start` 는 trap 을 걸지 않고 호출자 전원이 `pg_cleanup` 을 부름 ⓒ `_pg.sh` 에 정리 함수 등록 목록을 두고 trap 1개가 목록 실행
- 권장: ⓐ — 호출자 무수정 · 기존 trap 보존. ⓑ 는 호출자 하나라도 빠뜨리면 컨테이너가 남는다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓒ (보강: 등록 함수 `pg_on_cleanup` 자체가 `trap pg_cleanup EXIT INT TERM` 을 멱등 설치 · `pg_cleanup` 은 등록 목록을 역순 실행 뒤 컨테이너·슬롯 정리) + operator-notifications 5개 exit 에 `_readiness.sh` 표식 · 확신 높음
- 완료 기준: `_pg.sh` 대상 selftest(docker stub)에서 호출자 trap 과 `pg_cleanup` 이 둘 다 실행 · `operator-notifications.sh` 의 78 경로 전부 표식 출력(grep 으로 표식 없는 `exit 78` 0건) · service-tests 로컬 1회 실행 뒤 `/tmp/service-tests-*` 수 불변. 기존 329개 정리는 범위 밖(호스트 정리 — Ted 판정).
- 판정 질문: 권장안 수용?

## 그룹 L · PR 2 후반 — lifecycle 증거 정확도
- PR 2(판정·증거 정확도) 둘째 묶음 · PR 1 병합 뒤 lane 1개가 구현한다 · 판정은 Ted(/grill-me 그룹 L 단위) · PR 게시는 Ted · 코드 줄 번호는 develop `67a03a05` 에서 2026-09-25 재확인.
- 이 묶음의 lifecycle 경로(H6/H7 · task 결속)는 이번 분석에서 `COLAB_TASK_ID` 없이 측정돼 실행 경로로는 확인되지 않았다 — 근거는 코드 읽기와 단위 시험(`test_task_runtime.py` 31 · `test_harness_lifecycle_contract.py` 29)이다. 예외: L2 task 결속은 probe 재현 2026-09-25(격리 clone · payload-only).

### L1 task 종료 상태·정리 수단 없음  (출처: R4-11, R4-12)
- 문제: lifecycle 하위 명령은 begin · write-artifact · run-bound-gate · gate-snapshot · gate-start · run-gates · validate-input · handoff · stop 뿐이다 — close · prune 없음(`scripts/harness/hooks/lifecycle_contract.py:539`–`569`). handoff 는 `COLAB_HANDOFF` 줄을 출력하고 `stop()` 으로 자기검증만 하며 task.json 에 쓰지 않는다(`:600`–`609`). 보존·정리 규칙 문서 0(`docs/development/lifecycle-evidence.md` · `dual-agent.md` grep).
- 문제(측정): `.git/colab-harness` 153 MB · task.json 204 · checkout key 42(메인 재현 2026-09-25 · 본 초안 재계측 동일). 사라진 checkout 의 task 74건 · 보고서 없는 gate 역할 task 12건(R4 census · 검증 confirmed). task 당 약 700 KB 는 baseline 이 저장소 전 파일 hash 를 담기 때문이다(`lifecycle_contract.py:137`–`158`, `:244`–`247`) — 저장 형식 축소는 이 항목 범위 밖.
- 선택지: ⓐ `stop()` 통과 시점(CLI handoff · SubagentStop 훅 각각)에 task.json 에 종료 기록(mode · run_id · 판정 H6/H7 · 시각)을 남기고 열린/닫힌 task 조회 명령을 둔다 ⓑ `lifecycle prune` — 기본 dry-run · `git worktree list` 에 없는 checkout 의 task 와 종료 뒤 N일 지난 task 를 대상으로 출력 · `--apply` 로만 삭제 ⓒ 문서만 — lifecycle-evidence.md 에 보존 규칙·수동 삭제 절차
- 권장: ⓐ+ⓑ — ⓐ 없이는 ⓑ 가 인계된 task 와 버려진 task 를 가르지 못한다. ⓐ 는 L2 ⓑ · L3 ⓑ · A2 ⓐ(분할 시 PR 2)의 전제다. 현재 store 에 대한 `--apply` 실행은 Ted 승인 뒤(되돌릴 수 없는 삭제).
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ + ⓑ (ⓒ 는 두 선택지의 부속 문서로 흡수) · 추가: ⓐ 의 종료 기록에 Stop payload `agent_id` 를, `researcher-task.sh` 자동 begin 에 spawn `agent_id` 를 **정보 필드**(대조 없음)로 남긴다 · 확신 높음
- 완료 기준: `test_task_runtime.py` 에 ① handoff 성공 뒤 task.json 종료 기록 존재 ② `stop()` 실패 시 종료 기록 없음 ③ prune dry-run 이 사라진 checkout 의 task 를 나열하고 파일을 지우지 않음 ④ `--apply` 뒤 대상 디렉터리 부재 — 시험이 추가되고 `agent-bridge` gate green. 현재 store 에 대한 dry-run 대상 건수를 PR 요약에 기록.
- 판정 질문: 권장안 수용? 수용 시 보존 기간 N 을 며칠로 할지 · prune `--apply` 를 누가 실행할지.

### L2 H6 이 agent 가 지목한 task 로 판정됨 — 제품 파일 변경 뒤 새 begin 이 baseline 을 재설정  (출처: R4-judges-evidence-missed 1 · probe 재현 2026-09-25)
- 문제(코드 · 조립 시 재열람 2026-09-25): `stop()` 은 최종 메시지의 `COLAB_HANDOFF` 줄 1개(`scripts/harness/hooks/lifecycle_contract.py:365`)의 `task_id` 로 task 를 읽는다(`:369`) — 스폰 때 연 task 와의 결속 없음. agent 신원 대조는 task 에 `agent_id` 가 있을 때만 한다(`:377`). researcher 자동 task 는 `--agent-id` 없이 열린다(`scripts/harness/hooks/researcher-task.sh:9`–`11` 주석 · `lifecycle-evidence.md:42`). researcher 변경 판정은 그 task 의 begin 시점 baseline 대비다(`:386`–`389`). 「baseline 재설정 금지」는 문장뿐이다(`lifecycle-evidence.md:36`). 어느 task 가 spawn 시점 task 인지 기록도 없다(L1).
- 재현 결과: **재현됨** — probe 재현 2026-09-25(격리 로컬 clone @ `67a03a05` · payload-only · task 기록은 clone 의 `.git/colab-harness` · 메인 checkout task.json 204 → 204 · clone 삭제).
  - ① `researcher-task.sh` 에 SubagentStart payload(agent_id 지정) → rc=0 · 자동 task T1(task.json agent_id 없음) ② README.md 1줄 추가(`git status` ` M README.md`) ③ `lifecycle begin --role researcher` → rc=0 · T2 ④ `handoff --task T2 --mode read-only` → rc=0 · `COLAB_HANDOFF` 출력 ⑤ `uncommitted-artifacts.sh` 에 T2 marker 를 담은 stop payload → **rc=0**(「H6 — current task evidence and handoff verified」) · README.md 는 미커밋 변경 그대로.
  - 대조군: T1 로 handoff → rc=78, T1 marker 로 hook → **rc=2**(「read-only/draft-return requires unchanged files and no file artifacts」) → baseline 비교 자체는 동작한다. 우회 경로는 task 교체다.
  - 변형: 편집 뒤 `begin --role researcher --agent-id <같은 id>`(T3) → handoff · hook 모두 rc=0 → `:377` agent_id 대조는 task 교체를 막지 않는다.
  - 미검증: 실제 Claude Code SubagentStop 이벤트가 `last_assistant_message` · `agent_id` · `cwd` 를 이 형태로 주는지(payload 는 코드가 읽는 필드로 구성) · 실제 researcher 가 이 경로를 밟은 사례 · H7(lane) 쪽 같은 기제.
- 문제(lane · 문서 근거): scoped lane 의 출구 ⑴(범위를 넓힌 새 task)은 범위 밖 변경을 새 baseline 에 흡수한다 — 문서화된 동작이며 `--summary` 에 사유를 적게 한다(`lifecycle-evidence.md:95`–`96`).
- 선택지: ⓐ spawn 결속 — SubagentStart 훅이 연 자동 task 를 agent_id 별 spawn task 로 runtime 에 기록하고, SubagentStop 의 `stop()` 이 handoff task 의 baseline 과 spawn task baseline 사이 변경을 선언 산출물 밖이면 거부(전제: Start/Stop agent_id 일치 — L8) ⓑ begin 연쇄 차단 — 같은 checkout 에 종료 기록 없는 researcher task 가 있고 그 baseline 대비 변경이 있으면 researcher begin 을 거부(전제: L1 ⓐ · agent_id 불필요 · lane 출구 ⑴ 은 대체한 task_id 를 새 task 에 기록하는 형태로 유지) ⓒ 문서만 — `lifecycle-evidence.md:36` 을 「기계 강제 없음 · 부모가 인계 뒤 `git status` 로 확인」으로 고침
- 권장: ⓑ — 재현됨. L1 ⓐ 위에서 agent_id 증명 없이 성립하고, 변형(`--agent-id` 새 task)도 같은 규칙으로 막힌다. ⓐ 는 L8 에서 Start/Stop agent_id 일치가 확인된 뒤 추가 여부를 다시 따진다.
  - 기존 task 처리: 현재 store 의 task 204건은 종료 기록 스키마가 없다. ⓑ 는 종료 기록 스키마(L1 ⓐ)를 가진 task 만 「종료 기록 없는 task」로 센다 → PR 2 병합 전 task 는 대상 밖. 이 규칙 없이 켜면 병합 직후 거의 모든 researcher begin(SubagentStart 자동 begin 포함)이 거부된다.
  - 산출물 순서: `runtime:artifacts/<파일>` 은 git-common-dir 아래라 checkout snapshot(`lifecycle_contract.py:137`–`143` `git ls-files`) 밖이다 → artifact task begin 전에 쓴 산출물도 「baseline 대비 변경」에 들어가지 않는다. checkout 안 경로(`dev-package/**` 등)에 먼저 쓴 경우는 거부된다(의도).
  - 오차단 면: 「baseline 대비 변경」에는 같은 checkout 의 다른 writer(메인 · 형제 레인) 변경도 들어간다(L4 와 같은 전제). 인계 실패로 남은 task 가 이후 researcher begin 을 계속 막을 수 있다 → 거부 메시지에 출구(L1 종료 · prune 명령)를 적고, 적용 대상(SubagentStart 자동 begin 포함 여부)은 spec 에서 정한다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓑ(L1 ⓐ 뒤) + ⓒ(문장 정정은 병행) · ⓐ 는 L8 측정 결과가 나올 때까지 보류 · 확신 중간
- 완료 기준: `test_task_runtime.py` 에 ① 「제품 파일 변경 → 새 researcher begin → read-only handoff」 시나리오가 begin 단계에서 거부 ② 같은 시나리오의 `--agent-id` 변형도 거부 ③ 변경 없는 상태의 artifact task 추가 begin(`lifecycle-evidence.md:43` 절차) 통과 ④ 거부 메시지에 출구 명령 포함 ⑤ 종료 기록 스키마 없는 옛 task 만 있는 checkout 에서 researcher begin 통과 ⑥ `runtime:artifacts` 에 먼저 쓴 뒤 artifact task begin 통과 — green · probe 절차 ①–⑤ 를 격리 clone 에서 재실행해 ③ 단계 거부 · `lifecycle-evidence.md:36` 문장이 기계 강제 지점(file:line)을 가리킴.
- 판정 질문: ⓑ(begin 연쇄 차단) 수용? SubagentStart 자동 begin 에도 적용할지? 옛 task(종료 기록 스키마 없음) 제외 규칙 수용?

### L3 lane 이 자기 전용 worktree·고유 브랜치에서 도는지 확인하지 않음  (출처: R2-2 corrected, H9)
- 문제(문서 갈림): `.agents/skills/executing-plans/SKILL.md:17` · `.agents/skills/writing-plans/SKILL.md:166` · `.agents/skills/VENDORED.md:87` 은 lane-worker 격리를 「(자동)」으로 적고, `.agents/skills/design-review/SKILL.md:106` 은 frontmatter `isolation: worktree` 에 기댄다. `.agents/skills/colab-v2-work/SKILL.md:48` · `.agents/rules/colab-rules.md:63` · `writing-plans/SKILL.md:14` 는 명시 `Agent(isolation: "worktree")` 를 지시한다.
- 문제(검사 부재): `.agents/roles/lane-worker.md:27` 은 HEAD 만 대조하고 `:31` 은 「자기 워크트리 밖 경로를 편집하지 않는다」 문장뿐이다 — 자기 checkout 이 부모와 다른지 확인하는 단계가 없다. 관측 1회: `dev-package/sessions/design-fix-followups-20260925-E.md:5` 「레인 L1 · L2 는 워크플로 안에서 통합 워크트리에 바로 커밋했다」(직렬 · 겹침 0). 원인(Workflow `agent()` 가 frontmatter isolation 을 받지 않음)은 사용자 메모리에만 있다 — 미검증. Agent 도구 스폰에서 같은 일이 생기는지도 미검증.
- 문제(H9): 지시문의 공용 브랜치 이름 `fixlane-work` 로 다른 레인의 `checkout -B` 가 이 레인의 ref 를 되돌렸다(`dev-package/sessions/design-fix-20260924-F-preview.md:114`–`117` · 커밋 손실 0). `.agents` · `.claude` · `docs` 에 이 이름 0건 — 지시문 쪽 문제. 발생 조건은 미재현.
- 선택지: ⓐ lane-worker 첫 줄 검사 — 지시문이 준 부모 checkout 경로와 `git rev-parse --show-toplevel` 이 같거나, 현재 브랜치를 다른 worktree 도 체크아웃하고 있으면(`git worktree list --porcelain`) 구현하지 않고 정지 · `colab-v2-work` 지시문 체크리스트에 「부모 경로 전달 · 레인별 고유 브랜치 이름」 추가 ⓑ 기계 검사 — `lifecycle begin --role lane-worker` 가 같은 checkout_id 에 종료 기록 없는 lane-worker task 가 있으면 거부(전제: L1 ⓐ) ⓒ 문서만 — 「(자동)」 3곳을 「스폰 시 isolation 명시(Workflow `agent()` 포함)」로 고치고 E.md:5 관측을 근거로 적음
- 권장: ⓐ+ⓒ — 관측된 형태(부모 worktree 에서 실행)를 스폰 직후 구현 전에 잡는다. `--git-dir` 대 `--git-common-dir` 비교는 부모가 linked worktree(통합 worktree)인 E.md:5 경우를 잡지 못해 선택지에서 뺐다. ⓑ 는 L1 ⓐ 채택 시 같은 PR 에 넣을지 따로 판정.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): 새 선택지 ⓓ + ⓐ + ⓒ · ⓑ 는 L1 ⓐ 뒤 추가 — ⓓ = `worktree-setup.sh`(SubagentStart:lane-worker · 스크립트 본문만 수정) 가 payload `cwd` 의 toplevel 과 `$CLAUDE_PROJECT_DIR` 의 toplevel 이 같으면 「격리 아님 · 구현하지 말고 정지」 한 줄을 레인 맥락 첫머리에 싣고 venv 구성을 건너뛴다 · 확신 중간
- 완료 기준: `executing-plans` · `writing-plans` · `VENDORED.md` 에서 lane-worker 「(자동)」 문구 grep 0건 · `lane-worker.md` 에 검사 명령 · 재현 기록 — 부모 경로를 준 lane-worker 를 isolation 없이 스폰하면 구현 전 정지를 보고하고, isolation 명시 스폰은 통과(Workflow `agent()` 1회 · Agent 도구 1회)가 PR 요약에 있다.
- 판정 질문: 권장안(ⓐ+ⓒ) 수용? ⓑ 를 같은 PR 에 넣을지.

### L4 researcher·lane 인계가 checkout 전체를 대조 — 같은 checkout 의 다른 writer 변경이 인계 판정에 들어감(코드) · researcher 끼리 막는 경우는 추론  (출처: R4-13 corrected, R4-judges-evidence-missed 3, H4, H5)
- 문제(코드): `snapshot()` 은 checkout 전체(`git ls-files --cached --others --exclude-standard`)를 hash 한다(`lifecycle_contract.py:137`–`158`). researcher `stop()` — HEAD 변경 거부(`:384`–`385`) · read-only/draft-return 은 변경 0(`:387`–`389`) · artifacts 는 WATCH 밖·선언 밖 변경 거부(`:390`–`397`). lane H7 — 보고서 `task_evidence` before/after 를 인계 시점 checkout 전체 hash 와 대조(`:322`, `:345`) → gate 실행과 인계 사이 부모·형제의 편집 1건이 범위와 무관하게 gate 재실행을 부른다.
- 문제(기록): 초안 H4 의 design-fix 레인 `L3` · `L4a` · `L4b` 인계 거부는 형제 레인 파일이 「this task has unhanded output」로 잡힌 것이고 `L4a` 는 begin/write-artifact 실패(초안 H5)가 겹쳤다. 자동 read-only task 가 동시 편집으로 거부된다는 것은 H4 에서도 「추론 · 미실측」이다. 커밋 경우는 `lifecycle-evidence.md:44` 에 문서화돼 있다.
- 문제(H5 문서 불일치): `.agents/roles/researcher.md:27` 은 쓰기 자리를 `dev-package/sessions/` · `reports/` · `intent/` 로, `design-review/SKILL.md:63`(§2-2 항목 5)은 `dev-package/sessions/design-review-<YYYYMMDD>-L<n>.md` 쓰기를, `:65`(항목 7)은 같은 worktree 에서 레인 n개 구성을 지시한다. 새 task 는 산출물을 `runtime:artifacts/<파일>` 로만 받는다(`scripts/harness/task_state.py:66`–`68`).
- 선택지(H4 틀 재사용): ⓐ `design-review` §2-2 · `researcher.md` 를 「`runtime:artifacts` 로 쓰고 메인이 hash 대조로 반입」으로 바꾼다(문서) ⓑ 레인마다 `isolation: worktree`(문서 · L3 과 결합) ⓒ 감시 범위를 task 선언 산출물·scope 로 좁힌다(코드)
- 권장: ⓐ(researcher) + ⓑ(lane · L3 ⓐ 로 확인) — 코드 변경 없이 다른 writer 를 checkout 에서 뺀다. ⓒ 는 선언 밖 제품 파일 편집 탐지를 빼므로 H6 의 목적과 충돌한다. 현행 우회(researcher 병렬 산출 → runtime:artifacts)는 사용자 메모리에만 있어 저장소 문서로 올린다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ + ⓑ(조건부 규칙 · L3 과 결합) · ⓒ 반대 · 확신 높음
- 완료 기준: `design-review/SKILL.md` §2-2 에 `dev-package/sessions/design-review-<YYYYMMDD>-L<n>.md` 쓰기 지시 grep 0건 · `researcher.md` 쓰기 범위에 runtime:artifacts 절차 · 재현 기록 1회 — 같은 checkout 에서 researcher 2건이 runtime:artifacts 로 쓰고 각각 `handoff --mode artifacts` 로 H6 통과.
- 판정 질문: 권장안(ⓐ+ⓑ · ⓒ 기각) 수용?

### L5 lane scope 판정 경계 — 오타 glob 통과 · task 중 병합  (출처: R4-9 corrected, R4-10)
- 문제: `check_scope_declarations` 는 끝 `/` 와 와일드카드 없는 기존 디렉터리 이름만 거절한다(`lifecycle_contract.py:81`–`93`). `frontend/scr/**` 같은 오타 glob 은 begin 을 통과하고 handoff 에서 모든 변경이 범위 밖으로 거부된다 → 새 task · gate 재실행(fail-closed · 거짓 green 아님). 기록 204건 중 scoped task 2건(2026-09-25).
- 문제: scope 판정은 begin 시점 커밋..HEAD 전체 diff 를 센다(`:410`–`419`). scoped lane 이 task 중 develop 을 병합하면 병합으로 들어온 파일이 전부 범위 밖이 된다. `test_task_runtime.py:319`–`343` 의 merge 는 begin 이전 충돌 생성용 — begin 뒤 병합 커밋 시험 0. B1 ⓒ 채택 시 PR 브랜치에 develop 을 병합하는 절차가 없어져 이 경우의 한 원인이 빠진다(B1 연동).
- 선택지: ⓐ begin 에서 glob 의 첫 와일드카드 앞 디렉터리 접두가 없으면 거절(기존 디렉터리 아래 새 파일은 통과) · lifecycle-evidence.md 범위 절에 「scoped task 중 병합하면 병합 파일이 범위 밖 — 병합 뒤 새 task」 문장 · 현재 병합 동작을 고정하는 시험 ⓑ ⓐ + `stop()` 이 begin 뒤 병합 커밋의 병합 부모와 HEAD 내용이 같은 파일을 레인 변경에서 뺌(코드) ⓒ 현행 유지 · 문서만
- 권장: ⓐ — 두 경우 모두 fail-closed 라 거짓 green 은 없다. ⓑ 는 병합 충돌 해소 편집을 레인 변경에서 빼는 경로를 새로 만든다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (접두 검사의 판정 기준을 「첫 와일드카드 앞 구간의 dirname 이 작업 트리에 존재」로 고정 · 거부 메시지에 출구 2개 명기) · 확신 높음
- 완료 기준: `test_task_runtime.py` 에 ① 없는 접두 glob begin 거절 ② 기존 디렉터리 아래 새 파일 glob 통과 ③ begin 뒤 병합 커밋 → 병합 파일이 범위 밖 목록에 포함(현재 동작 고정) — green · lifecycle-evidence.md 범위 절에 병합 문장 1건.
- 판정 질문: 권장안 수용?

### L6 lifecycle 판정기 시험 공백 — selftest 제외 · parallelism 검사 직접 시험 0  (출처: R4-3 corrected, R4-18)
- 문제: `gates/run.sh:315`–`316` `harness-contract-selftest` 는 시험 5파일만 돌리고 `test_harness_lifecycle_contract.py` · `test_task_runtime.py`(60 시험)를 뺀다. 두 파일은 `agent-bridge` gate(`gates/run.sh:308`–`310`)가 돌린다 → lifecycle 코드를 고친 lane 이 selftest 만 선언하면 lifecycle 시험 없이 green(검증 후 심각도 low).
- 문제: `check_gate_parallelism`(`scripts/harness/check.py:25`–`75`) 직접 시험 0 — `scripts/tests/test_harness_config.py:240` 이 lambda 로 대체한다. 미선언 gate 통과 · `ALL_GATES` 정규식 파손 회귀는 live 저장소 대상 gate 실행으로만 드러난다.
- 선택지: ⓐ selftest 에 두 lifecycle 시험 파일 추가 + `check_gate_parallelism` fixture 시험(미선언 gate · `ALL_GATES` 부재 · 없는 gate 선언 · serial/parallel 외 값) ⓑ fixture 시험만 추가하고 문서에 「lifecycle 파일 변경 lane 은 `agent-bridge` gate 선언」 ⓒ 문서만
- 권장: ⓐ — run.sh 한 줄과 시험 추가로 끝난다. `all` 에서 60 시험이 두 번 도는 추가 시간은 측정해 PR 요약에 적는다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (두 lifecycle 시험 파일을 `harness-contract-selftest` 에 추가 · `agent-bridge` 에서는 빼지 않음 · `check_gate_parallelism` fixture 시험 4종) + ⓑ 의 문서 문장을 `.agents/roles/lane-worker.md`·`colab-v2-work` 에 1줄 · 확신 높음
- 완료 기준: `gates/run.sh harness-contract-selftest` 로그에 두 lifecycle 시험 모듈 실행 · 새 fixture 시험이 결함 fixture 에서 errors 비어 있지 않고 정상 fixture 에서 0 — green · 시험 수 증가분 기록.
- 판정 질문: 권장안 수용?

### L7 Workflow advisor·measurement-lane 에 schema 를 걸면 StructuredOutput 실패  (출처: H8)
- 문제: 저장소 기록 0 — `StructuredOutput` 은 `.agents` · `.claude` · `docs` 에 0건, 흡수 대상 초안 intent 에만 있다. 사용자 메모리(저장소 밖)에 「`agentType: 'advisor'` · `'measurement-lane'` 에 `schema` → 'completed without calling StructuredOutput' 로 워크플로 정지(3회)」. 원인(maxTurns · measurement-lane 종료 형식 · 플랫폼 동작)은 미검증. 당시 advisor maxTurns 12 → 현재 16(`.claude/agents/advisor.md:7` · 커밋 `0e33ce02`) · measurement-lane 60(`.claude/agents/measurement-lane.md:7`).
- 선택지: ⓐ 문서 — Workflow 판정·측정 단계는 schema 없이 첫 줄 `VERDICT:` 텍스트로 받는 현행 우회를 `colab-v2-work` 절차로 올림 ⓑ 재현 먼저 — 현재 정의에서 schema 를 건 advisor · measurement-lane 각 1회 실행 → 재현되면 ⓐ, 아니면 결과만 기록 ⓒ measurement-lane 종료 형식을 StructuredOutput 호출과 양립하게 변경 — 원인 확인 전 보류
- 권장: ⓑ → ⓐ — 한도 변경(#131) 뒤 재현 여부가 없다. 재현 2회는 작은 비용이고 결과로 문서 문장이 정해진다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓑ → ⓐ (재현 2회를 먼저 · 재현 설계는 원인 판별형 · 결과와 무관하게 현행 텍스트 `VERDICT:` 우회를 colab-v2-work 에 「현행 관행」으로 1줄 기록) · 확신 중간
- 완료 기준: 재현 2회의 결과(StructuredOutput 호출 여부 · 도구 호출 수 · 종료 사유)가 기록되고, 재현 시 `colab-v2-work` 에 규칙 1줄(grep 1건).
- 판정 질문: 권장안(재현 뒤 문서화) 수용? 이 항목을 PR 3(문서 drift)으로 옮길지.

### L8 researcher 라이브 스모크 — Start/Stop agent_id 일치 기록  (출처: 초안 H10 · R1-19 · R5-10 · T5 와 분담)
- 문제: #130 병합 뒤 할 일인 researcher 라이브 스모크 결과가 저장소에 없다 — `lifecycle-evidence.md:42` 는 「agent_id 일치가 증명되지 않았으므로 자동 task 는 정지 시 ID 를 대조하지 않는다」를 유지하고, `dev-package/prd/specs/S-HARNESS-LANE-HYGIENE-20260924.md:44` 는 계획 문장뿐이다. `/hooks` 재신뢰 실시 여부는 저장소에서 확인할 수 없다(기록 없음 · 미검증). 설계는 일치 없이 동작한다(`researcher-task.sh:9`–`11`) — 빠진 것은 기록이다(검증 후 심각도 low).
- 분담: `/hooks` 재신뢰는 Ted 행동(T5). 이 항목은 재신뢰 뒤 agent 가 실행하는 스모크와 기록이다.
- 선택지: ⓐ T5 뒤 agent 가 researcher 1건 스모크 — 훅 출력 agent_id 로 `begin --role researcher --agent-id <id> --artifact runtime:artifacts/<파일>` task 를 열고(`lifecycle-evidence.md:43`) 그 task 로 인계. `stop()` 은 task agent_id 와 SubagentStop payload agent_id 를 대조하므로(`lifecycle_contract.py:377`) H6 통과 = 일치 ⓑ 스모크 생략 · 문서 유지
- 권장: ⓐ — L2 ⓐ(spawn 결속) 추가 여부가 이 결과에 달린다. 실행 시점 = T5 직후(T5 권장 ⓑ 면 PR 3 병합 뒤) · PR 2 diff 에 들어가지 않는 관측 항목. L2 변형이 보인 대로 agent_id 일치만으로는 task 교체를 막지 못한다 → 이 스모크는 L2 ⓑ 를 대체하지 않는다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): 새 선택지: ⓐ 를 T5 뒤가 아니라 **지금 먼저** 실행 — 스모크 자체가 재신뢰 여부의 관측이다. 훅 출력이 있으면 일치 판정 기록 · 없으면 「이 PC 훅 비활성」 기록 후 T5 → 재실행 · 확신 높음
- 완료 기준: 스모크 1회의 훅 출력 agent_id · 인계 task_id · H6 결과(통과/「task role or agent identity differs」)가 기록되고, 통과면 `lifecycle-evidence.md:42` 문장 갱신 · 거부면 L2 ⓐ 제외 기록.
- 판정 질문: 권장안 수용? 기록 위치(이 intent 확인 절 · `lifecycle-evidence.md`) 중 어디.

## 그룹 C · PR 3 — 문서·설정 drift
- 행위자: PR 3 · lane 구현 · PR 2 병합 뒤 develop 기준으로 시작. 그룹 T 는 아래 「그룹 T」 절, 제외(X1–X4)는 「범위 밖」 절.
- 재검증 기준: develop `67a03a05` · 2026-09-25. 아래 file:line 은 이 트리에서 다시 열어 확인한 값이다. 판독자 보고만 있고 다시 열지 않은 사실은 「판독 · 재현 안 함」으로 적는다.

### C1 measurement-lane 역할 본문의 「프로세스 간 뮤텍스가 없다」  (출처: R2-1 corrected · R5-governance-missed)
- 문제: `.agents/roles/measurement-lane.md:13` 이 ADR-0002 를 「첫 번째 규율」 근거로 들고 `:17-18` 에 「`gates/run.sh` 에 프로세스 간 뮤텍스가 없다」고 적는다. `.codex/agents/measurement-lane.toml:12` 도 "gates/run.sh has no cross-process mutex". 코드는 `serial` 게이트에 호스트 뮤텍스를 건다(`gates/tools/_lock.sh` `gate_host_mutex_acquire` · 커밋 `9ece9104`). `.agents/roles/lane-worker.md:52` 「게이트 대기는 호스트 뮤텍스가 한다」와 두 역할 본문이 어긋난다.
- 유지되는 것: `parallel` 게이트는 뮤텍스 밖이고 postgres 슬롯은 호스트 전역이다 → 「게이트 도는 레인은 한 번에 하나」 규율 자체는 유지. ADR-0002 는 superseded(→ ADR-0005) 이력 문서라 고치지 않는다.
- 선택지: ⓐ 전제 문장만 사실(serial = 호스트 뮤텍스 · parallel 제외 · postgres 슬롯 호스트 전역)로 교체, 규율 유지, ADR-0002 인용 옆에 superseded 표기 ⓑ 규율까지 완화(측정 레인 동시 실행 허용) ⓒ 현행 유지
- 권장: ⓐ — 규율의 근거(슬롯 호스트 전역)는 남아 있고 틀린 것은 전제 문장이다. ⓑ 는 동시 실행 시 슬롯 고갈 78 재발 여부 실측이 없다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (＋ 근거 ADR 을 ADR-0005·spec `2026-09-18-gate-host-mutex.md` 로 바꾸고 ADR-0002 는 「superseded · 이력」으로만 인용) · 확신 높음
- 완료 기준: `grep -rnE '뮤텍스가 없다|no cross-process mutex' .agents/roles .codex/agents` 0건 · `python3 scripts/agent-bridge.py check` · `gates/run.sh harness-contract` green · `docs/decisions/0002-*.md` diff 0.
- 판정 질문: 권장안 수용?

### C2 README.md 하네스 훅 절  (출처: R1-12 corrected · R1-10 corrected)
- 문제: `README.md:64` 「훅 7개」(등록 11) · `:73` git-guard 를 main/master 기준으로 설명(코드 보호 집합 = main|master|develop|product) · `:74`·`:75` migration-guard·decision-number-guard 기준을 `origin/main` 으로 설명(migration-guard 코드 = `origin/develop` · `scripts/harness/hooks/migration-guard.sh:72-77`) · `:76-77` H6/H7 을 미추적 파일·`gate-summary.json` 부재 검사로 설명(현재 lifecycle task runtime 증거 판정) · `:9`·`:60` 「최신 `R-*.md` 하나만 읽는다」.
- `README.md:105` 「모든 훅 스크립트의 첫 줄이 이 값(COLAB_HOOKS=0)을 보고 즉시 통과」 — `uncommitted-artifacts.sh`·`lane-gate-summary.sh`·`lifecycle_contract.py` 의 COLAB_HOOKS 참조 0건. `docs/development/dual-agent.md:56` 「H6 자체를 끄거나 성공으로 위장하지 않는다」 → 동작은 의도, README 쪽 drift(결함 아님).
- 선택지: ⓐ 훅 표를 현재 등록(`.claude/settings.json`·`.agents/harness.yaml`) 기준으로 다시 쓰고 COLAB_HOOKS 예외(H6/H7) 1줄 추가 ⓑ 훅 표를 지우고 정본 링크(`.agents/harness.yaml` 훅 목록 · `docs/development/dual-agent.md`) + COLAB_HOOKS 절(H6/H7 예외 포함)만 남김 ⓒ 표 유지 · 수치·ref 이름만 교정
- 권장: ⓑ — 같은 목록을 두 곳에 두어 생긴 drift 다. 정본을 한 곳으로 줄이면 다음 훅 추가 때 README 를 고칠 일이 없다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓑ (표 삭제 · 정본 링크 ＋ `COLAB_HOOKS` 절 교정) — 단 `:75` decision-number-guard `origin/main` 은 **현재 코드와 일치**하므로 C5 ⓐ 와 같은 PR 에서만 바꾼다 · 확신 중간
- 완료 기준: `grep -nE '훅 7개|origin/main|최신 .R-\*\.md' README.md` 0건 · COLAB_HOOKS 절에 H6/H7 예외 문장 1건 · `gates/run.sh harness-contract` green.
- PR 1 연동: A1 완료 기준 ⑺ 이 `README.md:73` git-guard 행을, A3 이 README hook 절 경계 문장을 고친다. ⓑ 를 고르면 표는 지우되 A3 경계 문장은 COLAB_HOOKS 절과 함께 남긴다.
- 판정 질문: 표 삭제(ⓑ)와 표 갱신(ⓐ) 중 무엇?

### C3 gates/README.md CI 표 · ci.yml 낡은 주석  (출처: R3-15)
- 문제: `gates/README.md:233-245` 표에 `search-golden`·`product-safety`·`required-gates`·`ci-required` 잡 행 없음(`.github/workflows/ci.yml` 잡 16개 중 11개만 수록 · `changes` 제외) · `agent-bridge.yml` 언급 0건 · `:236` frontend-gates 행에 `frontend-fixture-reach` 누락(`ci.yml:324` 실행) · `:244` harness-eval 행 「시크릿 참조」 ↔ 잡은 면제 모드.
- `ci.yml:167-171` 「WU-D3에서 실제 검사를 채운다 · 지금은 골격」 주석 잔존 · `:641` harness-eval 면제 설명이 `repo-hygiene` 잡(`:629`) 구간에 위치.
- 선택지: ⓐ 표를 ci.yml 기준으로 갱신 + 주석 삭제·이동 ⓑ ⓐ + 표의 잡 이름 집합과 ci.yml 잡 이름 집합 대조를 harness-contract 에 추가 ⓒ 표 삭제 · 「정본 = ci.yml」 한 줄
- 권장: ⓐ — 조건·게이트 매핑은 ci.yml 만으로 읽기 어려워 표를 둔다. 대조 검사(ⓑ)는 코드 추가라 Ted 판정.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (＋ 잘못 놓인 주석은 3곳) · 확신 높음
- 완료 기준: 표 잡 이름 집합 = ci.yml 잡 이름 집합 − `changes`(대조 결과 PR 본문 기재) · `grep -n '골격' .github/workflows/ci.yml` 0건 · ci.yml diff 가 주석 줄뿐(`git diff -U0` 확인).
- 판정 질문: 권장안 수용? 잡 이름 대조 검사(ⓑ) 추가 여부?

### C4 계획·인계 문서 포인터 — #130 · #131 · #140 · 이 intent  (출처: R5-5 corrected · R2-10 일부)
- 문제: `AGENTS.md:18` 은 전환 실행 계획으로 `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md` 를 가리킨다. 그 파일(`:4` 「전면 전환·추가 고도화는 보류」)과 `docs/development/harness-transition-handoff.md`(`:28` 같은 문장) · `AGENTS.md` 의 #130 · #131 · #140 언급 0건. `harness-transition-handoff.md:162`·`:175` 「native hook 허용·차단 미확인」은 같은 문서 `:51-66`(2026-09-15 실측 기록 · 판독)과 어긋난다.
- 범위 기록: 각 하네스 PR 은 Ted 승인 intent 에 근거한다 → 빠진 것은 계획 포인터 갱신이다. 이 intent 는 09-15 「추가 고도화 보류」 범위를 다시 연다 → 그 사실을 계획 문서에 적는다.
- 선택지: ⓐ `R-HARNESS-PR-CENTRIC.md` `:4` 아래에 「2026-09-24~ 재개: #130 · #131 · #140 · 이 intent」 절 추가 + handoff 문서 머리에 이후 이력 포인터 + `:162`·`:175` 정정 ⓑ `AGENTS.md:18` 을 하네스 intent 목록으로 바꾸고 두 문서를 이력으로 동결 표기 ⓒ 현행 유지
- 권장: ⓐ — `AGENTS.md` 는 always-on 120줄 상한 문서라 변경을 두지 않는다. 계획 문서 한 절 추가로 포인터가 닿는다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): 새 선택지: ⓑ 의 포인터 이동 ＋ ⓐ 의 append 포인터 — `AGENTS.md:18` 은 `harness-transition-handoff.md` 머리의 신설 「이후 이력」 절(#130 · #131 · #140 · 이 intent · PR 1-3)을 가리키고, `R-HARNESS-PR-CENTRIC.md:4` 아래엔 그 절로 가는 1줄만 · `:162`·`:175` 본문은 고치지 않고 그 위 「당시 기록」 표지에 날짜·해소 범위를 덧붙인다 · 확신 중간
- 완료 기준: `grep -cE '#130|#131|#140' dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md docs/development/harness-transition-handoff.md` 각 ≥1 · 이 intent 경로 인용 1건 · `AGENTS.md` diff 0 · `gates/run.sh harness-contract` green.
- 판정 질문: 권장안 수용?

### C5 존재하지 않는 `main` 을 가리키는 설정·문서·guard 기준  (출처: R3-3 corrected · R4-17 · R1-13 · R1-hooks-missed(ref guard 실패 방향))
- 문제: `docs/development/github-ruleset.json:6` 대상 `refs/heads/main` — 원격 main 없음 · 적용 규칙셋은 product 하나(메인 재현 2026-09-25). `docs/development/release-evidence.md:43`·`:45` main PR 제안 문구. `scripts/harness/hooks/decision-number-guard.sh:63-73` 기준선 `origin/main` — 로컬 ref 부재(2026-09-25 `git rev-parse --verify origin/main` 실패) → 매번 워킹트리 `max-decision.sh` 로 물러서고, 그것도 못 읽으면 `:73` exit 0(통과). migration-guard 는 `origin/develop` 부재 시 준비 실패로 막는다(`migration-guard.sh:72-74`) → 두 ref 기반 guard 의 실패 방향이 반대. `migration-guard.sh:5`·`:10-11`·`:55`·`:70` 주석은 여전히 `origin/main`. PLAN-SoT 는 legacy 읽기 호환 자료(AGENTS.md) → low.
- 선택지: ⓐ ruleset JSON 을 T1 결론대로 `refs/heads/develop` 대상으로 다시 쓰고 release-evidence 문구 동기화 · decision-number-guard 기준을 `origin/develop` 로, 기준 부재 시 migration-guard 와 같은 준비 실패(차단) · migration-guard 주석 교정 ⓑ ruleset JSON 에 「폐기 · 원격 설정은 T1」 표기 · guard 는 주석만 교정 ⓒ 현행 유지
- 권장: ⓐ(ruleset 부분은 T1 판정 뒤) — 없는 ref 를 기준으로 삼는 상태를 끝내고, 「선언하면 검사」 원칙과 어긋나는 exit 0 경로를 없앤다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (ruleset JSON 의 required check 이름은 T1·B1 결론에 맞춰 PR 3 시점에 확정 · guard 기준 `origin/develop` ＋ 기준 부재 = 준비 실패) · 확신 중간
- 완료 기준: `grep -nE 'refs/heads/main|origin/main' docs/development/github-ruleset.json docs/development/release-evidence.md scripts/harness/hooks/decision-number-guard.sh scripts/harness/hooks/migration-guard.sh` 0건 · decision-number-guard 「기준 ref 부재 → exit 2」 시험 1건 red→green · `gates/run.sh agent-bridge` green · T1 이 「적용 안 함」이면 JSON 에 폐기 표기.
- 판정 질문: decision-number-guard 기준 부재 시 차단(ⓐ) 수용? 이 guard 수정을 PR 1(막는 장치)로 옮길지?

### C6 Claude skill adapter — 명시 호출 플래그 · parity 검사 한 방향 · VENDORED.md  (출처: R2-3 · R2-4 corrected · R2-17 · R2-15 corrected)
- 문제: 본문 4종(`.agents/skills/{agent-browser,apple-design,grill-me,to-spec}/SKILL.md`)은 `disable-model-invocation: true`, Claude adapter 17개 중 이 키 0건(예: `.claude/skills/grill-me/SKILL.md:1-4`) → Claude 에서 모델 호출 목록에 오른다. `scripts/agent-bridge.py:101-111` 은 본문 → adapter 한 방향만 검사: 본문 없는 adapter · 플래그 불일치 미검출.
- adapter description 은 「Claude에서 공통 X 절차를 연결한다」로 본문 「Use when…」 트리거가 빠짐(R2-4 · low · 본문은 한 번 더 읽어서 닿는다).
- `.agents/skills/VENDORED.md:5` 「전 8종 명시 호출 전용」(본문 기준으로도 사실 아님) · `:98` 재대조 diff 대상이 9줄 adapter(`.claude/skills/<name>/SKILL.md`) → 본문 경로(`.agents/skills/<name>/SKILL.md`)여야 한다.
- 선택지: ⓐ adapter 에 본문의 `disable-model-invocation` 값을 싣고 agent-bridge check 가 두 값 일치 + adapter → 본문 역방향 존재를 검사 · description 은 현행 ⓑ ⓐ + adapter description 에 본문 트리거 문구 복사(검사 포함) ⓒ VENDORED.md 만 정정
- 권장: ⓐ + VENDORED.md `:5`·`:98` 정정 — 명시 호출 정책을 Codex(`agents/openai.yaml` `allow_implicit_invocation: false`)와 맞춘다. 트리거 복사(ⓑ)는 자동 호출 범위를 넓혀 ⓐ 와 방향이 반대라 따로 판정.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ ＋ ⓒ (adapter 에 `disable-model-invocation` 값 승계 · agent-bridge 양방향 검사 · VENDORED.md `:5`·`:98` 정정) · description 복사(ⓑ)는 하지 않음 · 확신 높음
- 완료 기준: agent-bridge 부정 fixture 시험 2건(플래그 불일치 · 본문 없는 adapter) red→green · `python3 scripts/agent-bridge.py check` green · 새 Claude 세션 스킬 목록에서 4종 제외 여부 1회 관측 기록.
- 판정 질문: ⓐ 수용? 트리거 문구 복사(ⓑ)는 하지 않는 것으로 확정?

### C7 Claude role frontmatter 값 자동 검사 없음  (출처: R2-5)
- 문제: `scripts/harness/config.py:160-165` 는 `.claude/agents/*.md` 의 frontmatter 를 떼고 본문(2줄 포인터)만 비교한다. `scripts/agent-bridge.py:82-92` 는 Codex toml 만 검사하고, Codex model/effort 는 `scripts/tests/test_agent_bridge.py:35` 가 단언한다. Claude 쪽 기대값 검사는 수동 grep(`dev-package/prd/specs/S-AGENT-MODEL-TIERING-20260924.md:62`) → model·effort·maxTurns·isolation·disallowedTools 를 바꿔도 모든 gate 통과.
- 선택지: ⓐ `.agents/harness.yaml` 에 역할별 기대값 선언 + check 가 Claude frontmatter · Codex toml 양쪽 대조 ⓑ 단위 시험에 Claude frontmatter 기대값 단언 추가(Codex 방식과 같은 형태) ⓒ 현행 유지
- 권장: ⓑ — Codex 쪽과 대칭을 맞추는 최소 변경(시험 파일 1개). ⓐ 는 선언 구조 신설이라 범위가 늘어난다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (범위 한정형) — `.agents/harness.yaml` 에 역할별 기대값을 두 도구 몫으로 선언하고 `check_contract` 가 Claude frontmatter · Codex toml 양쪽을 대조. 기존 `test_agent_bridge.py:35-59` 의 Codex 기대 dict 는 하드코딩 대신 harness.yaml 을 읽어 단언(선택 가능 모델 집합 단언은 시험에 유지). · 확신 중간
- 완료 기준: frontmatter 값 1개(예: advisor maxTurns)를 바꾼 사본에서 시험 red, 원복 후 green(`gates/run.sh agent-bridge`).
- 판정 질문: 권장안 수용?

### C8 docs/development 사실 갱신 — dual-agent.md · lifecycle-evidence.md  (출처: R2-10 · R2-roles-codex-missed(정의 변경 3회) · R2-14 · R4-16)
- 문제: `docs/development/dual-agent.md:70` 「5개 이벤트」 · `:83`·`:85` 「7개 등록 항목」 ↔ `.codex/hooks.json` 6 이벤트 · 9 항목(2026-09-25 재계수). 마지막 신뢰 기록은 2026-09-09(7 항목 · `:82-83`), 그 뒤 정의 변경 3회 — `012df481` 09-12 Stop · `4c07f1ea` 09-18 SubagentStop 대상 확대 · `faff6734` 09-24 SubagentStart researcher(`git log -- .codex/hooks.json`). 재신뢰 요청 문장(`:87-89`)은 09-24 정의만 든다.
- `dual-agent.md:54` 「lane-worker frontmatter 스킬 4개」 ↔ `.claude/agents/lane-worker.md:7` 5개(colab-ponytail 포함).
- `docs/development/lifecycle-evidence.md` measurement-lane 언급 0건 · `:10` 역할을 researcher·lane-worker 로만 적음 ↔ `scripts/harness/hooks/lifecycle_contract.py:55` `MEASURING_ROLES = ('measurement-lane',)` · `:254`.
- 선택지: ⓐ 수치·역할 사실 교정 ⓑ 개수 수치를 문서에서 빼고 「정본 = `.codex/hooks.json`」 참조 + 재신뢰 대상에 09-12 · 09-18 · 09-24 정의 명시 + measurement-lane 절 추가 ⓒ 현행 유지
- 권장: ⓑ — 개수는 정의 추가마다 다시 어긋난다. 재신뢰 대상 목록은 T5 결과를 적을 자리가 된다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓑ (현재형 문장만) — 개수 수치는 현재형 문장에서 제거하고 「정본 = `.codex/hooks.json`」 참조 · 재신뢰 대상에 `012df481`(09-12 Stop) · `4c07f1ea`(09-18 SubagentStop 대상 확대) · `faff6734`(09-24 SubagentStart researcher) 명시 · lane-worker 스킬 수 교정 · lifecycle-evidence 에 measurement-lane 절 추가. 2026-09-09 날짜가 붙은 관측 기록(`:82-83`)은 이력이므로 그대로 둔다. · 확신 높음
- 완료 기준: `grep -nE '[0-9]+개 (이벤트|등록 항목)|스킬 [0-9]+개' docs/development/dual-agent.md` 0건 · `grep -c measurement-lane docs/development/lifecycle-evidence.md` ≥1 · 재신뢰 대상 3개 정의 명시.
- 판정 질문: 권장안 수용?

### C9 규칙·역할 본문의 낡은 문장  (출처: R2-18 corrected · R2-roles-codex-missed(launch 로드 · baseRef · advisor 쓰기) · R2-11 corrected)
- 문제:
  - `.agents/rules/colab-rules.md:4` 「`paths` frontmatter 없음 → launch 때 로드」 — 현재 launch 로드는 5줄 포인터 `.claude/rules/colab-rules.md` 뿐, 본문은 필요한 절만 읽는다(AGENTS.md 「작업에 필요한 절을 읽는다」).
  - `:28` §1-3 「Sonnet 하강 없이 Fable 로 재시도」 — 현재 역할 등급(lane-worker opus · measurement-lane sonnet · S-AGENT-MODEL-TIERING)과 어긋남. 앵커 파일명 부재는 설계(`:5`)라 결함 아님.
  - `:62` §2-3 「P-A 에이전트 정의로 강제 예정」 — `.claude/agents/lane-worker.md` 에 `isolation: worktree` 이미 있음.
  - `:65` §2-3 · `.agents/roles/lane-worker.md:27` 「워크트리 기본 기준은 `origin/<default>`」 — `.claude/settings.json:4` `baseRef: "head"`(ADR-0001). `git merge --ff-only` 첫 줄 자체는 유지, 이유 문장만 낡음.
  - `.agents/roles/advisor.md:39` 「쓰기 도구가 없으므로」 — Claude advisor 는 `disallowedTools: Edit, Write, NotebookEdit`(`.claude/agents/advisor.md:6`)라 Bash 가 남는다. Codex 는 `sandbox_mode = "read-only"`.
- 선택지: ⓐ 문장별 사실 교정(§1-3 은 역할 등급 spec 참조로 대체 · advisor 는 「파일을 수정하지 않는다 — Claude 에서는 Bash 가 남아 있어 규율이다」) ⓑ ⓐ + Claude advisor frontmatter 에서 Bash 제거(전제를 도구 제한으로 참으로 만듦) ⓒ 현행 유지
- 권장: ⓐ — advisor 는 판정 근거 확인에 Bash 읽기 명령을 쓴다. ⓑ 는 advisor 동작 범위를 바꾸는 별도 판정이다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ — 문장별 사실 교정. ⓑ(Claude advisor 에서 Bash 제거)는 그룹 T 질문으로 넘긴다(Ted 판정 항목). · 확신 중간
- 완료 기준: 인용 문자열 5종(`loaded at launch` 주장 · `Fable 로 재시도` · `강제 예정` · `기본 기준은 \`origin/<default>\`` · `쓰기 도구가 없으므로`) grep 0건 · `python3 scripts/agent-bridge.py check` · `gates/run.sh harness-contract` green.
- 판정 질문: 권장안 수용?

### C10 hook 머리말·안내 문구 drift  (출처: R1-9 · R1-16)
- 문제: `scripts/harness/hooks/git-guard.sh:71` · `migration-guard.sh:21` · `test-file-guard.sh:27` · `decision-number-guard.sh:27` 「exit 1 은 통과다 · 판정 못 하면 통과가 기본값」 — 실제는 python3 부재 · envelope 이상 시 exit 2(`git-guard.sh:82` · `migration-guard.sh:28` · `test-file-guard.sh:38` · `decision-number-guard.sh:34`–`35`)이고 뒤의 `command -v python3 … || exit 0`(`:90` · `:32` · `:42` · `decision-number-guard.sh:38`)은 도달 불가(메인 재열람 2026-09-25).
- A3 이관분: migration-guard · decision-number-guard 머리말에 「Edit/Write 도구만 대상 · Bash 쓰기는 대상 아님 · 사후 검사 수단」 명시(A3 ⓐ 와 같은 문장).
- `scripts/harness/hooks/worktree-setup.sh:247-259` 「`baseRef: fresh` … origin/main · P-E 브랜치」 안내 + `~/.colab-v2-test.env` 만 확인 ↔ `.claude/settings.json:4` `baseRef: "head"` · `gates/run.sh:264` `COLAB_TEST_ENV_FILE` 우선.
- 선택지: ⓐ 주석·안내 교정 + 도달 불가 줄 삭제 + worktree-setup 이 `COLAB_TEST_ENV_FILE` 을 run.sh 와 같은 규칙으로 확인 ⓑ 주석만 교정
- 권장: ⓐ — `git-guard.sh`·`test-file-guard.sh` 는 PR 1 이 고치는 파일이므로 두 파일 머리말은 A5(PR 1)로 옮겼고, 이 항목(PR 3)은 `migration-guard.sh` · `decision-number-guard.sh` · `worktree-setup.sh`. decision-number-guard 는 C5 와 같은 파일 → 한 커밋.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (문장 정정형) — 「exit 1 은 통과」 자체는 Claude Code 사실이라 남기고, 「판정 못 하면 통과가 기본값」을 2단 규칙으로 교체: 준비 실패(python3 부재 · envelope 이상) = exit 2 차단(2026-09-09 계약), envelope 통과 뒤 판정 불가(tokenizer 실패 등 · A1) = 통과. 도달 불가 `|| exit 0` 4줄 삭제. A3 이관 문장(Edit/Write 전용 · Bash 쓰기 비대상 · 사후 검사) 추가. worktree-setup 은 `${COLAB_TEST_ENV_FILE:-$HOME/.colab-v2-test.env}` 로 run.sh 와 같은 규칙 · P-E/origin/main 문단 삭제. · 확신 높음
- 완료 기준: `grep -n 'exit 1 은 통과' scripts/harness/hooks/*.sh` 0건(A5 가 PR 1 에서 두 파일을 먼저 고친 뒤) · migration-guard · decision-number-guard 머리말에 A3 경계 문장 · `grep -nE 'fresh|P-E' scripts/harness/hooks/worktree-setup.sh` 0건 · `COLAB_TEST_ENV_FILE` 만 있는 환경에서 worktree-setup 이 「있음」을 출력하는 시험 1건 · `gates/run.sh agent-bridge` green.
- 판정 질문: 권장안 수용? (git-guard · test-file-guard 머리말은 A5 에서 판정)

### C11 bootstrap-diet 의 mtime legacy 라운드 출력  (출처: R5-governance-missed(bootstrap-diet))
- 문제: `scripts/harness/hooks/bootstrap-diet.sh:70-71` 이 `dev-package/prd/rounds/R-*.md` 를 mtime 순으로 골라 `:84` 「legacy 참고 후보(mtime) … 신규 task 선택 근거 아님」을 지정 라운드가 없는 매 세션 시작에 출력한다. AGENTS.md 「mtime으로 다음 작업을 결정하지 않는다」.
- 선택지: ⓐ 라벨 유지(현행) ⓑ 지정 라운드(`SELECTED`)가 없으면 후보 줄을 출력하지 않음 ⓒ 후보 파일 대신 「legacy 라운드 위치 = `dev-package/prd/rounds/`」 한 줄
- 권장: ⓑ — 출력과 AGENTS.md 원칙이 어긋나고, 후보 줄이 없어도 `:75-76` 신규 작업 안내는 남는다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓑ + ⓒ 결합 — mtime `find` 삭제, SELECTED 없으면 후보 줄 없음, 기존 `:80` 「legacy 대장·라운드는 읽기 호환 자료」 줄 끝에 위치(`dev-package/prd/rounds/` · 지정은 `COLAB_ROUND`/payload `round`)만 덧붙임(새 줄 추가 없음). · 확신 높음
- 완료 기준: SELECTED 없는 SessionStart 출력에 `mtime` 문자열 0건 — bootstrap-diet 시험 갱신 후 `gates/run.sh agent-bridge` green.
- 판정 질문: ⓑ(출력 삭제)와 ⓐ(라벨 유지) 중 무엇?

### C12 css-edit-audit PostToolUse 출력이 Claude 모델에 닿는지 — 관측 먼저  (출처: R1-3 · 문서 근거 · 미측정)
- 문제: `scripts/harness/hooks/css-edit-audit.sh:21` 머리말 「PostToolUse 의 stdout 은 맥락으로 실려 들어간다」, `:74` `echo "$OUT"` 평문 출력. 저장소가 인용한 Claude hook 문서(`bootstrap-diet.sh:24-26`)는 평문 stdout 이 모델 맥락에 들어가는 이벤트를 SessionStart·SubagentStart 로 든다 → Claude 에서 감사 행이 모델에 닿지 않을 가능성(문서 근거 · 미측정). `ponytail-inject.sh:76` 은 `hookSpecificOutput.additionalContext` JSON 을 쓴다. Codex 는 bridge 가 평문을 감싼다(판독).
- 선택지: ⓐ 관측 1회(`frontend/src` CSS 파일 1건 Edit → 모델 맥락에 감사 행이 보이는지) 후 결과로 ⓑ 여부 판정 ⓑ 출력을 additionalContext JSON 으로 변경(ponytail-inject 방식) ⓒ 현행 유지
- 권장: ⓐ → 닿지 않으면 ⓑ. 관측 없이 바꾸면 전후 차이를 확인할 수단이 없다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓑ — 출력을 `hookSpecificOutput.additionalContext` JSON 으로(ponytail-inject 방식 · JSON 인코딩은 이미 기동하는 python3 `json.dumps` 로), 머리말 `:21` 교정. ⓐ 관측은 판정 선행 조건이 아니라 PR 검증 단계(병합 뒤 메인 세션에서 `frontend/src` CSS Edit 1회)로 둔다. · 확신 높음
- 완료 기준: 관측 기록 1건(날짜 · Claude Code 버전 · 결과). ⓑ 채택 시 css-edit-audit JSON 출력 시험 + Codex bridge 시험(`scripts/tests/test_agent_bridge.py`) green.
- 판정 질문: 관측을 PR 3 lane 에 맡길지(권장안 수용?)

## 그룹 T · Ted 결정·행동
- 에이전트는 질문 · 선택지만 기록한다. GitHub 설정 · 브랜치 · 형제 체크아웃 · `/hooks` 신뢰를 바꾸지 않는다. T2 는 B6 으로 병합(ID 유지).

### T1 develop 필수 status check · PR 규칙  (출처: R3-3 corrected · R3-2 corrected · R4-2 corrected)
- 문제(메인 재현 2026-09-25): develop branch protection `required_status_checks` null · `required_pull_request_reviews` null · force push·삭제 금지만. 규칙셋은 23379713 product-promotion-policy(product) 하나. → develop 에서 red CI 가 병합을 막지 않는다. 저장소 문서는 미적용을 밝혀 두었다(`harness-transition-handoff.md:191` · `release-evidence.md:45`) → 공개된 미적용 상태. `.agents/harness.yaml` `gates.required` 12개는 모양·개수만 검사(R4-2).
- 연결: `ci-required` 는 `required-gates` 를 needs 에 포함한다(`ci.yml:848`). PR 2 가 병합 부모 거짓 red(B1 · 초안 H6 · R3-1)를 고치기 전에 필수로 걸면 develop 이 움직일 때마다 병합이 막힌다 → 적용 시점은 PR 2 병합 뒤. harness-contract 는 path-filtered `agent-bridge.yml` 에서만 돌아 `ci-required` 밖이다.
- 선택지: ⓐ develop 필수 check = `ci-required` 1개 + PR 필수(승인 0) ⓑ `ci-required` + `required-gates` 2개 ⓒ 현행 유지(미적용 공개 상태)
- 권장: ⓐ — `ci-required` 가 `required-gates` 결과를 이미 포함한다. PR 필수는 git-guard 우회(PR 1 대상) 같은 로컬 사고의 원격 방어선이 된다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓐ (+ `strict_required_status_checks_policy: true` · 관리자 우회 없음). 시점은 PR 2 병합 뒤 유지 가능하나, strict 를 켜면 PR 2 전 적용도 무해 · 확신 높음(ⓐ > ⓑ) · 중간(시점)
- 완료 기준: Ted 적용 후 `gh api repos/CognileapAI/colab-v2/branches/develop/protection` 의 required_status_checks 에 선택한 이름이 보이고, C5 의 ruleset JSON 이 같은 내용을 기록.
- 판정 질문: 어느 check 를 필수로(ⓐ/ⓑ/ⓒ)? 적용 시점 = PR 2 병합 뒤로 확정?

### T2 → B6 로 병합  (출처: R4-5 · R4-judges-evidence-missed)
- pr_contract 를 CI 에서 돌릴지는 저장소 workflow · 스크립트 변경이라 파일 소유 PR 2 의 B6 에서 판정한다. CT 초안의 권장(ⓑ 로컬 절차)과 근거는 B6 의 반론 줄로 옮겼다. 새 workflow 의 required 지정 여부만 T1 에서 다룬다.

### T3 형제 체크아웃 32 · 33  (출처: R5-12 · R5-governance-missed(33))
- 문제(2026-09-25 재확인): 30 · 31 · 32 · 33 이 호스트 잠금 경로 `${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host` 를 공유한다(`gates/tools/_lock.sh:78`). `32 CoLAB-v2` HEAD `02d251d8` — `gate_mutex_spawn` 0건 → frontend-visual 데몬이 잠금 fd 를 물려받는 이전 코드. `33 CoLAB-v2` HEAD `cb30d344` — `gate_host_mutex` 0건 → 게이트가 호스트 잠금을 잡지 않고 postgres 슬롯은 공유. 33 사용 여부 미검증. `30 CoLAB-v2` 는 `67a03a05` · 수정 포함.
- 선택지: ⓐ 32·33 을 develop 로 갱신 ⓑ 은퇴(삭제·보관) ⓒ 유지 + 그 체크아웃에서 게이트 실행 금지
- 권장: 사용 중이면 ⓐ, 아니면 ⓑ — 사용 여부는 Ted 만 안다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): 조합 — 32 는 ⓐ(develop ff-only 갱신, 열린 task 없는 시점) · 33 은 ⓑ(은퇴) · 확신 높음(33) · 중간(32)
- 완료 기준: 결정 기록 1줄 · ⓐ 면 두 체크아웃 `gates/tools/_lock.sh` 에 `gate_mutex_spawn` 존재 확인.
- 판정 질문: 32·33 을 지금 쓰는가?

### T4 낡은 브랜치 · f3846f32  (출처: R5 §5 브랜치 표)
- 문제(2026-09-25 재확인: 존재): 로컬 `worktree-agent-a06b599e…` · `worktree-agent-a20a6e57…`(git cherry 기준 고유 커밋 0 — 판독 · 재현 안 함) · `worktree-agent-abe5bbb8…`(`f3846f32` 포함 — #130 이 뺀 handoff JSON 계약 변경) · 원격 `origin/worktree-ponytail-systemic`(#130 본문이 삭제 요청 — 판독).
- 선택지: ⓐ 네 브랜치 삭제 ⓑ `f3846f32` 만 태그로 보관 후 삭제 ⓒ 유지
- 권장: ⓐ — 둘은 develop 에 이미 반영, 하나는 #130 이 채택하지 않은 작업, 원격 하나는 삭제 요청분. 삭제는 비가역이라 Ted 가 실행.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓑ (`f3846f32` 를 로컬 네임스페이스 태그로 보관 후 네 브랜치 삭제) · 확신 높음
- 완료 기준: `git branch -a --list '*worktree-agent*' '*worktree-ponytail*'` 출력이 결정과 일치.
- 판정 질문: 권장안 수용? `f3846f32` 보관(ⓑ) 필요?

### T5 `/hooks` 재신뢰  (출처: 초안 H10 · R1-19 corrected · R5-10 corrected · R2-roles-codex-missed(정의 변경 3회) · 스모크는 L8)
- 문제: #130 병합 뒤 할 일(이 PC `/hooks` 재신뢰)의 저장소 기록 0건. 재신뢰 여부는 저장소로 판정할 수 없다 → 「안 했다」가 아니라 「기록 없음」. 정의별 재신뢰 필요는 문서 근거(`dual-agent.md:87-89`). Codex 는 09-09 신뢰 기록 뒤 정의 변경 3회(C8 · `git log -- .codex/hooks.json`). researcher 라이브 스모크(Start/Stop agent_id 일치)는 재신뢰 뒤 agent 가 실행한다 → L8.
- 선택지: ⓐ 지금 재신뢰 ⓑ PR 3 병합 뒤 한 번에(A 권장안은 훅 정의 무변경 전제지만, A2 ⓑ 처럼 정의가 바뀌는 선택지를 고르면 재신뢰 대상이 늘어남) ⓒ 기록 없이 진행
- 권장: ⓑ — 정의 변경을 모아 한 번에 신뢰한다. 결과는 C8 이 만든 자리(`dual-agent.md` 재신뢰 대상 목록)에 기록하고, 직후 L8 스모크.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): 새 선택지: ⓐ 를 지금 하되 기록을 남기고, 정의를 바꾸는 PR 이 있으면(A2 ⓑ 경로 등) 그 PR 병합 뒤 1회 더. ⓑ(PR 3 뒤 일괄)는 채택 불가 · 확신 중간
- 완료 기준: 기록 1건 — 날짜 · PC · 도구(Claude/Codex) · 신뢰한 정의 목록. 스모크 agent_id 두 값은 L8 완료 기준.
- 판정 질문: 권장안 수용?

### T6 #131 원한 결과 8 — 한도 도달률 재측정  (출처: R2-13)
- 문제: `dev-package/intent/2026-09-24-agent-model-tiering.md:38` 「병합 뒤 재측정 … 기록을 남긴다(후속 · 병합 조건 아님)」. 저장소에는 병합 전 기준(`dev-package/reports/harness/20260924-agent-model-tiering/M1-role-usage.md` · 09-24)과 후속 표기(`PR-BODY.md:39`)만 있고 재측정 기록 없음(2026-09-25 `git grep 도달률`).
- 선택지: ⓐ 유지 — 별도 측정 회차 ⓑ 폐기(원한 결과 8 삭제 사유 기록) ⓒ 이 intent 의 세 PR 동안 생기는 advisor·researcher·measurement-lane 스폰을 표본으로 M1 방식 집계
- 권장: ⓒ — 별도 회차 없이 표본이 생긴다.
- Fable 판정(권고를 가린 독립 판정 · 2026-09-26): ⓒ (창 고정 · n 공개 · 병합 조건 아님) — L7 재현을 같은 표본에서 처리 · 확신 중간
- 완료 기준: 역할별 스폰 수 · 한도 도달 수 표 1개가 PR 3 본문 또는 reports 에 기록.
- 판정 질문: 권장안 수용, 또는 폐기(ⓑ)?

### T7 사용자 메모리(저장소 밖) 갱신 담당  (출처: R5-1 ~ R5-4 · R2-18 · R3-16 · advisor2 §4-7)
- 문제: 사용자 메모리 색인 · 본문이 코드와 어긋났다(뮤텍스 없음 · advisor 12 / researcher 30 · 하네스 고도화 보류 · worktree 훅 없음). 저장소 밖이라 PR 이 고치지 못한다.
- 처리: 메인 세션 담당. 2026-09-25 분석 직후 1차 정정 완료(6파일 · 색인 4줄). 남은 것 — B1 ⓒ 병합 뒤 `required-gates-stale-pr-base.md` 폐기 또는 갱신 · L4 ⓐ 병합 뒤 `lifecycle-handoff-shared-worktree-collision.md` 갱신 · L7 결과 뒤 `workflow-advisor-model-and-schema.md` 갱신.
- 완료 기준: 각 PR 병합 뒤 해당 메모리 파일 갱신 1건씩 · MEMORY.md 색인 줄 일치.
- 판정 질문: 없음(보고만).

## 설계트리 (grill-me 결과)
- QA 그룹 A(PR 1) — A1–A5 권장안 · 각 판정 질문(A1 argv 편입 범위 · 파싱 실패 폴백, A2 분할(ⓒ PR 1 · ⓐ PR 2), A4 78/1) → A 전부 권고대로(Ted 2026-09-25) — A1 ⓐ(argv 형태 편입) · 파싱 실패 = 현행 규칙 폴백 · A2 분할(PR 1 = ⓒ · PR 2 = ⓐ) · A3 ⓐ · A4 ⓐ(알 수 없는 gate = 78) · A5 ⓐ
- QB 그룹 B(PR 2 전반) — B1–B8 권장안 · 각 판정 질문(B1 결속 기준 완화, B3 판정 우선 · ADR 자리, B6 CI/로컬) → 판정은 「판정 기록」 절
- QL 그룹 L(PR 2 후반) — L1–L8 권장안 · 각 판정 질문(L1 보존 기간 · prune 실행 주체, L2 ⓑ 적용 대상 · 옛 task 제외, L7 PR 3 이관) → 판정은 「판정 기록」 절
- QC 그룹 C(PR 3) — C1–C12 권장안 · 각 판정 질문(C2 표 삭제/갱신, C5 PR 1 이관, C11 출력 삭제/유지) → 판정은 「판정 기록」 절
- QT 그룹 T(Ted) — T1 필수 check · T3 형제 체크아웃 · T4 브랜치 · T5 재신뢰 시점 · T6 재측정 → 판정은 「판정 기록」 절

## 미해결 질문
- L2 probe 한계: 실제 SubagentStop payload 형태(`last_assistant_message` · `agent_id` · `cwd`) · 실제 researcher 사용 사례 · H7(lane) 같은 기제 — 미검증.
- L2 ⓐ(spawn 결속) 추가 여부 — L8 스모크 결과 뒤.
- A2 ⓐ(PR 2) 전제: Workflow `agent()` 로 스폰한 lane 에서 PreToolUse hook 실행 여부 미검증 · 「열린 task」 = L1 ⓐ 종료 기록 없는 scoped lane-worker task.
- A3: migration · 결정 번호의 Bash 편집에 대한 사후 검사 수단 유무 — 미확인(표기 전에 확인).
- B1: 「develop 병합 뒤 이벤트 base.sha 가 갱신된다」는 문서 근거(PR #141 기록 · 사용자 메모리) · 실측 아님. B1 ⓒ 채택 시 사용자 메모리 `required-gates-stale-pr-base.md` 가 낡음(저장소 밖 · Ted/메인 갱신).
- C5 decision-number-guard 수정(기준 부재 시 차단)을 PR 1 로 옮길지.
- C12 · L7 은 관측 · 재현 결과로 선택지가 정해진다.
- L3: lane 부모 checkout 실행의 원인(Workflow `agent()` 가 frontmatter isolation 을 받지 않음)은 관측 1회 · 원인 기록은 사용자 메모리뿐 — 미검증.

## 범위 밖 (명시 제외)
- X1 초안 H11 캡처 장면 사각 — 대상 `frontend/scripts/visual-baseline/scenes.json` · 장면 추가는 기준 재촬영 동반(`dev-package/reports/design-system/20260924/architecture.md` §7 후속 4) → 디자인 시스템 후속 intent(Ted 결정 2026-09-25).
- X2 초안 H12 `tsconfig.audit.json` gate 편입 — frontend 타입 검사 범위 결정(§7 후속 5) → 같은 후속 intent.
- X3 초안 H13 시각 대조 gate 승격 — 캡처 시간 · agent-browser · 기준 보관 위치가 디자인 쪽 결정(§7 후속 6) → 같은 후속 intent.
- X4 초안 H15 `frontend-test` 부하 시 대기 초과 — 원인 후보가 렌더 비용(제품 코드) · 시험 대기 한도 · 미검증 → 같은 후속 intent.
- R1-17 reseed ACK 할당 검사(`git-guard.sh:134`)의 따옴표 · `read` · `printf -v` · Write 경로 누락 — 머리말(`:131-133`)이 보안 경계 아님을 명시.
- 한 겹 감싼 명령(`bash -c` · `eval`) — git-guard 머리말 `:74-76` 알려진 한계 유지.
- task 저장 형식 축소(baseline 이 저장소 전 파일 hash · task 당 약 700 KB) — L1 은 종료 기록 · prune 만.
- 기존 `/tmp/service-tests-*` 329개 정리 · 현재 `.git/colab-harness` 에 대한 prune `--apply` — 호스트 정리 · 비가역 삭제라 Ted 판정.
- design-review 스크립트 수정(B7)은 `frontend/scripts/visual-baseline/` 을 건드리지 않는다.

## 확인
- 그룹 판정: A 승인(Ted 2026-09-25 "전부 권고대로") · B · L · C · T 는 「판정 기록」 절
- 프론티어 공집합 확인: 〈판정 대기〉
- Ted 확인 문장(원문 그대로): 구성 결정 2026-09-25 "좋아 그렇게해보자" · 그룹 A 판정 2026-09-25 "전부 권고대로" · 그룹 B · L · C · T 는 「판정 기록」 절
- 재개봉 금지: 〈판정 대기〉

## 참조
- 기획 원본: 없음(개발 하네스)
- spec: 작성 예정(3 phase · 그룹 A 승인 뒤 phase 1 부터)
- 분석 원자료(저장소 밖): `~/.claude/reports/harness-state-20260925/`(findings-verified.md · R1-hooks.md · R2-roles-codex.md · R3-gates-ci.md · R4-judges-evidence.md · R5-governance.md · advisor2.md)
- 흡수 대상 초안: `dev-package/intent/2026-09-25-harness-design-round-residuals.md`(미승인 · 대체 표기 · 삭제 안 함)
- 관련 intent: `dev-package/intent/2026-09-24-harness-lane-hygiene.md` · `dev-package/intent/2026-09-25-external-harness-gap.md` · `dev-package/intent/2026-09-24-agent-model-tiering.md`
- 관련 PR: #130 · #131 · #140 · #144
- 제외 이관 근거: `dev-package/reports/design-system/20260924/architecture.md` §7
- 라운드 파일: `dev-package/prd/rounds/R-HARNESS-PR-CENTRIC.md`(C4 가 재개 절 추가)
- 결정: 〈N〉 (병합 시 기입) · B3 새 ADR 후보(판정 대기)

## 판정 기록
- 승인 뒤 이 절은 줄 추가만 한다(intent_ref ⑵). 그룹마다 날짜 · Ted 원문 · 항목별 결론을 적는다.
- 2026-09-25 그룹 A(PR 1) — Ted 원문 "전부 권고대로". A1 ⓐ — quote-aware tokenizer · 대상 checkout 해석 · 누락 argv 형태(gh -R · gh api PUT merge · 묶은 -fu · HEAD · 보호 브랜치 위 pull --no-ff/--no-rebase) 편입. A1 파싱 실패 = 현행 분리 규칙 폴백. A2 분할 — PR 1 = ⓒ 문장 정리(H14 포함) · PR 2 = ⓐ 편집 시점 차단(L1 ⓐ 종료 기록 위). A3 ⓐ 경계 표기(코드 0). A4 ⓐ 인자 검사를 mutex 앞에 · 여분 인자 · 빈 인자 · 잘못된 -j · 알 수 없는 gate = 78. A5 ⓐ 머리말 교정 + 도달 불가 줄 삭제.
- 2026-09-26 Fable 재판정(Ted 원문 "권고안들은 어드바이저가 동작해야 최상 아닌가? 페이블로 조사해야될거같은제 하네스가") — 권장안 39건을 Fable 8명이 권고를 가린 채 다시 판정하고 Fable 1명이 교차 점검했다(원문 `~/.claude/reports/harness-state-20260925/fable-judges/`). 각 항목의 「Fable 판정」 줄이 결과다. 같은 결론 29 · 다른 권고 10(B2 · B6 · B8 · L3 · L8 · C4 · C7 · C12 · T4 · T5). 그룹 A 5건은 모두 Ted 판정과 같은 결론.
- 2026-09-26 그룹 A 보강(Fable 판정 · 교차 점검 · 메인 코드 확인) — A1: `pull` 규칙은 명시 플래그(`--no-ff` · `--no-rebase` · `--rebase=false` · `--ff=false`)만 잡고 플래그 없는 `git pull` 은 통과 · `-C` · cwd 불일치 시험은 bridge `guard()`(cwd 고정 `agent-bridge.py:170`)가 아니라 hook 직접 호출로 작성 · 차단 문구 `git-guard.sh:271` 「main|master」 를 보호 집합 전체로 교정 · tokenizer 예외 = 현행 분리 규칙 폴백을 fault-injection 시험으로 고정. A2: Fable 제안 ⓒ′(시험 작성 task 를 따로 인계)는 기각 — `lifecycle_contract.py:312`–`315` 가 선언 gate 없음 · red 잔존 인계를 거절하고 red 허용은 measurement-lane 뿐(`:335`, 메인 확인). A2 ⓐ(PR 2)의 선결에 L8 스모크(PreToolUse `agent_id` 와 task `agent_id` 일치)를 더한다. A3: 「사후 검사 수단」 = `begin --scope` handoff/H7 로 지명. A4: 인자 검사는 `run.sh:9` 직후(`:42` gate-start 증거 기록보다 앞) · 비정수 `-j` 도 78. A5: git-guard 머리말은 C10 의 2단 문장(준비 실패 = exit 2 · envelope 통과 뒤 판정 불가 = 통과)으로 쓴다.
- 2026-09-26 2라운드(그룹 A 범위 1 · T1 · 그룹 B 7) — Ted 원문 "페이블 권고대로 젖부"(= 전부). 모두 Fable 권고로 확정.
  - A6 신설(PR 1): decision-number-guard 기준 `origin/main` → `origin/develop` · 기준 부재 = 준비 실패(exit 2) · 머리말 2단 문장 · 도달 불가 줄(`:38`) 삭제. C5 의 guard 부분과 C10 의 decision-number-guard 부분은 PR 1 로 이관(PR 3 에는 ruleset JSON · release-evidence 문구 · README 만 남음).
  - T1: develop 필수 status check `ci-required` + PR 필수(승인 0) + strict(병합 전 최신 develop 반영 필수) + 관리자 우회 없음. 적용 = Ted · 시점 = PR 1 병합 뒤. C5 ruleset JSON 의 required check 이름은 `ci-required`.
  - B2 ⓓ: 서비스 시험 적용 판정을 등록부 한 곳에서 계산(`changes` 잡이 등록부를 읽어 생산자별 출력 · 서비스 시험 잡 `RUN` · `if:` 가 그 출력을 읽음). PR 2 범위 압박 시 ⓐ(등록부 filters 2줄)로 축소.
  - B3 ⓐ: 판정 우선(1 > 78 > 0) 통일 · 분류 기준 「입력을 못 읽음 = 78 · 읽었는데 규율 위반 = 1」 · lifecycle 은 판정성 raise 지점에만 판정 예외 클래스 · 새 ADR. B3 는 B1 · L 그룹보다 먼저 구현.
  - B4 ⓐ: `harness-contract` · `agent-bridge` 를 ci-producers 생산자로 등록 · `ci.yml` 에서 record 로 실행 · harness-contract 가 「gates.required ⊆ 등록부 gates 합집합」 대조 · `.github/workflows/agent-bridge.yml` 폐지(또는 workflow_dispatch 전용).
  - B5 ⓑ: `ci-required` 가 intent-ref 의 skipped 를 push · workflow_dispatch · product 대상 PR 일 때만 허용 · job `if` 와 허용식의 일치를 harness-contract 가 대조.
  - B6(Fable 조합): 별도 PR workflow 에서 `pr_contract --mode draft` — 필수 절 · Plan-Ref · placeholder 실패 = red · Head-SHA 불일치 = 경고(종료 0) · 로컬 게시 전 검사 1줄 · placeholder 오탐 교정(줄 · 표 칸 전체 `<…>` 만). Claude 세션 PR 본문 틀을 이 형식에 맞춘다(저장소 밖 · 메인 세션).
  - B7 ⓐ: probe 파일 이름 = slug 앞 40자 + sha256 12자 · 선언 URL(중복 제거) 수 ≠ 페이지 수 → red(판정) · probe 전체 배열 + counts 대조 · 시작 때 이전 probe/png/index 만 삭제 · ⓓ `@layer` 등 grouping rule 재귀.
  - B8 ⓒ: `_pg.sh` 에 정리 함수 등록 목록(`pg_on_cleanup`)과 멱등 trap 1개 · 깨진 호출자 2곳 치환 · operator-notifications 의 표식 없는 `exit 78` 5곳에 readiness 표식.
  - B1 은 T1 strict 에 종속 → 3라운드.
- 2026-09-26 3라운드(B1 · 그룹 L · 새 항목 A7 · spec 세부) — Ted 가 3라운드 재검토 요청(원문 "페이블 어드바이저로 재검코") → Fable advisor 5명 반박 재검토 + spec gate ① 2명 + 교차 점검(원문 `~/.claude/reports/harness-state-20260925/fable-recheck-r3/`) → Ted 원문 "구ㅜㄴ규대로 하자"(= 권고대로). 결론:
  - B1 ⓐ: 코드 로직 유지 · `verify_evidence.py:58` 오류 문구에 「Update branch(develop 병합 push)가 새 이벤트 run 을 만든다 · 기존 run Re-run 은 계속 red」 · PR 절차 문서 1줄 · 완료 = 실 PR 1건에서 Update branch 1회 뒤 green 관측. B1 ⓒ(조상 대조)는 구현하지 않는다.
  - A7 신설(PR 1 · 새 사실 2026-09-26: SubagentStart hook 은 2/2 발화했으나 평문 stdout 이 서브에이전트에 0회 도달 · Claude Code 문서상 평문 stdout 이 모델에 가는 이벤트는 UserPromptSubmit · UserPromptExpansion · SessionStart · PostModelSwitch 뿐): `scripts/harness/hooks/researcher-task.sh` · `worktree-setup.sh` 출력을 `hookSpecificOutput.additionalContext` JSON 1줄로 · 출력 단언 시험 갱신 · `scripts/harness/hooks/bootstrap-diet.sh` · `worktree-setup.sh` 의 「SubagentStart 평문」 주석 · `dual-agent.md` · `README.md` 해당 문장 정정 · worktree-setup 에 「격리 아님」 권고 문구(차단 아님). css-edit-audit(C12 ⓑ)는 PR 1 의 별도 커밋. 완료 = 병합 · pull 뒤 researcher 1회 스폰 → 첫 턴에 task id 노출 관측. 「열린 자동 task 조회 · 재사용」과 자동 begin 존폐는 PR 2(L 그룹)에서 한 번에 정한다. 수정 병합 전까지 오케스트레이터는 researcher 지시문에 직접 begin 을 싣는다.
  - L3: lane-worker 자기검사를 `.agents/roles/lane-worker.md` 첫 동작(`git merge --ff-only`) 앞에 둔다 · 판정 = 지시문이 준 부모 checkout 경로 == `git rev-parse --show-toplevel` 이면 정지(Fable 재검토의 `--git-dir` = `--git-common-dir` 판정식은 부모가 linked worktree 인 관측 사례 `design-fix-followups-20260925-E.md:5` 를 못 잡아 메인이 기각) · 「같은 브랜치」 조건 삭제 · 스킬 문서 「(자동)」 3곳 교정 + 「Workflow agent() 스폰은 isolation 명시」 규칙 · PR 2.
  - L1: 종료 기록 2단 — 「인계됨」(CLI handoff 통과) · 「닫힘」(SubagentStop/bridge stop 판정 통과 또는 메인 `lifecycle close`) · prune 은 「닫힘」만 · 보관 14일 · 실제 삭제는 Ted 가 대화에서 명시 지시할 때만 · 삭제 기록 · 현재 store 첫 정리는 별도 판정 · 서브에이전트의 `lifecycle close` · `stop` · `prune --apply` 는 git-guard 규칙으로 차단(PR 2).
  - L2: 명시 begin 거부 조건의 「닫히지 않은」 = 「닫힘」 기록 없음(인계 뒤 편집 → 새 begin 우회 차단) · SubagentStart 자동 begin 은 막지 않고 같은 checkout 의 가장 오래된 열린 researcher task baseline 을 이어받아 연다(거부 메시지 출구 = 메인 `lifecycle close <옛 task>`) · 옛 스키마 task 제외.
  - L4: ⓐ + ⓑ + `design-review/SKILL.md` 항목 7(메인 순차 커밋) → 「모든 레인 인계 뒤 반입 · 커밋」 · 산출물 task 는 hook 출력 비의존 직접 begin(`--agent-id` 없이) · 격리 스폰 때 기준 브랜치 확인 1줄.
  - L5 ⓐ: glob 접두 검사 · 문서 순서 「scoped task 열린 동안 병합 금지 → Update branch 는 인계 뒤 PR 브랜치에서 → 불가피하면 병합 뒤 새 task」.
  - L6 ⓐ: selftest 편입 없음 · `check_gate_parallelism` fixture 시험 4종 · 역할 문서 1줄 · 조건: B4 로 옮기는 `agent-bridge` gate 가 `scripts/harness/**` · `scripts/tests/**` 변경에도 반드시 실행. 정정: 이 intent 「원한 결과」 그룹 L 의 「`harness-contract-selftest` 가 lifecycle 시험을 돈다」 문장은 이 판정으로 대체된다. 메인 확인 — lifecycle 시험은 현재도 `.github/workflows/agent-bridge.yml` 의 `unittest discover -s scripts/tests` 로 CI 에서 돈다(경로 필터 · 필수 아님).
  - L7: 재현 3회(사소 과제) — ① advisor+schema ② measurement-lane+schema ③ measurement-lane+schema · 도구 허용목록 변경 정의 — 결과로 문서 또는 frontmatter · 현행 우회(`VERDICT:` 텍스트)는 지금 `colab-v2-work` 1줄.
  - L8 · T5: L8 스모크는 A7 병합 뒤 1회(출력 전달 O/X · Start/Stop agent_id 일치 O/X/미관측 2축 기록). T5 Claude = 재신뢰 불요(이 PC · 이 경로 · hook 등록 무변경 조건 · 발화 관측 task 45fad2b0 · e4797bd0). T5 Codex 는 유지.
  - spec 세부: git-guard 시험용 교체 경로 env 는 제품 hook 에 두지 않는다(첫 줄만 내는 가짜 해석기가 규칙을 비울 수 있음) · 결함 주입은 hook 폴더 임시 복사본 · run.sh 알려진 gate = `ALL_GATES` + 「모든 case 라벨이 KNOWN 통과」 시험.
  - spec gate ①(GO-WITH-CHANGES) 반영 확정: 미종결 heredoc 은 본문 EOF 까지로 보고 폴백하지 않음(폴백 입력 = `bash -n` 도 거부하는 입력만) · 해석기 레코드는 JSON lines · 시험 fixture 모순 수정 · A6 준비 실패는 결정 번호 후보를 담은 편집에만.
- 2026-09-26 4라운드(그룹 C · T) — Fable advisor 4명 반박 재검토 + 교차 점검(원문 `~/.claude/reports/harness-state-20260925/fable-recheck-r4/`) → Ted 원문 "모두 권고대로 괜찮아". 결론:
  - C1: measurement-lane 역할 본문 · Codex toml 의 전제 문장 교체(serial = 호스트 뮤텍스 · parallel 은 뮤텍스 밖 · postgres 슬롯 호스트 전역) · 근거 ADR-0005 · PR 3 · C7 커밋에 합침.
  - C2 ⓐ: README hook 표 삭제 · 정본 링크(`.agents/harness.yaml` hook 목록 · `dual-agent.md`) · COLAB_HOOKS 절에 H6/H7 예외 1줄 · PR 1 이 표에 싣는 사실은 삭제 전 정본으로 옮김 · A3 blockquote 유지 · `README.md:74` migration-guard 행은 PR 3 · PR 3.
  - C3: `ci.yml` 낡은 주석은 PR 2 B4 커밋 · `gates/README.md` CI 표는 PR 2 병합 뒤 최종 잡 집합 기준으로 PR 3 · 잡 이름 집합 대조(ⓑ)는 B4 뒤 재판정.
  - C4 ⓐ: `AGENTS.md:18` 포인터를 `harness-transition-handoff.md` 머리 새 「이후 이력」 절(#130 · #131 · #140 · PR 1–3 번호 · SHA)로 교체(줄 수 불변) · `R-HARNESS-PR-CENTRIC.md:4` 아래 1줄 · 옛 본문 무변경 + 「당시 기록」 표지 · PR 3 마지막 커밋.
  - C5: `docs/development/github-ruleset.json` 은 T1 적용 뒤 실제 상태 기록(ruleset 형식 1개) · `release-evidence.md:43` · `:45` 정정 · T1 미적용이면 제안 형식 retarget 폴백 · PR 3.
  - C6 ⓐ+ⓒ: adapter 4종 `disable-model-invocation` 승계 · `agent-bridge check` 양방향 · 플래그 일치 · VENDORED.md 정정 · PR 3(C6 → C7 순).
  - C7 ⓐ: `.agents/harness.yaml` 에 역할별 기대값(스칼라 키) 선언 · Claude frontmatter = `check.py` · Codex toml = `agent-bridge check` 기존 로더 · 값 확정 = L7 · T10 뒤 · PR 3 마지막.
  - C8: PR 3 은 `dual-agent.md` 만(개수 수치 → 정본 참조 · 재신뢰 대상 Codex 3 정의 · Claude 재신뢰 불요 기록) · `lifecycle-evidence.md` measurement-lane 절은 PR 2.
  - C9: 문장 교정 PR 3 · `lane-worker.md:27` 이유 문장은 PR 2 L3 커밋 · `advisor.md:39` 문안은 T10 판 · 완료 grep 은 한국어 문자열.
  - C10: `migration-guard.sh` 머리말 + 주석 `origin/main` 5곳 → `origin/develop` · 완료 기준 = 「판정을 못 하면 통과가 기본값」 0건 · `worktree-setup.sh` 잔여는 A7 병합 diff 뒤 재판정 · PR 3.
  - C11 ⓑ+ⓒ: bootstrap-diet mtime 후보 줄 삭제 · 위치 안내 덧붙임 · 종속 시험 2곳 · `agent-bridge.py` Codex 문장 · PR 3.
  - T1 적용 방식 = ruleset(product 와 같은 방식 · 우회자 없음 · JSON 내보내기로 C5 기록) · PR 1 병합 뒤 · PR 2 open 전 · Ted 가 GitHub 에서 적용.
  - T3: 32 = PR 3 병합 뒤 develop 갱신(그 전 32 에서 게이트 실행 금지) · 33 = `_worktree-archive-*` 이동 — 사용 여부를 Ted 가 확인하기 전까지 실행 보류(2026-09-26 관측: `a2_pg_32` · `ai_pg_32` 컨테이너 12일째 가동).
  - T4 실행 완료 2026-09-26: `git cherry` 로 포함 확인 뒤 태그 `archive/f3846f32-handoff-evidence-key` · 로컬 `worktree-agent-a06b599e…` · `worktree-agent-a20a6e57…` · `worktree-agent-abe5bbb8…` 삭제 · 원격 `worktree-ponytail-systemic` 삭제.
  - T5: Codex 재신뢰 = 32 갱신 직후 1회 · 기록 = 이 intent 확인 절.
  - T6: 그룹 T 에서 제외 → PR 3 measurement 항목(세 PR 동안의 spawn 기록 표본 · 역할별 n 공개).
  - T8: 첫 `lifecycle prune --apply` = PR 2 병합 뒤 메인 세션 · Ted 지시 · PR 2 L1 spec 에 「checkout 경로 부재 = 닫힘 상당(기록 남김)」 1줄.
  - T9: 2026-09-26 확인 — gate 임시 postgres 없음(상시 컨테이너만) · `/tmp/service-tests-*` 341개 · 115 MB · 이틀 넘은 것 210개(09-13–09-21) · 삭제는 Ted 승인 대기.
  - T10: Claude advisor Bash 유지 · C9ⓑ 흡수 · 재판정 = L7 뒤.
  - PR 2 반입 5건(phase 2 상세화 때 반드시 포함): C3 ①(`ci.yml` 주석 → B4) · C8 ③(`lifecycle-evidence.md` measurement-lane 절) · C9 ①(`lane-worker.md:27` → L3) · T8(L1 spec 1줄) · T10(L7 입력).
  - spec 정정(레인 병합 뒤 반영): V14 의 README 검사 = decision-number-guard 행만(`README.md:74` migration-guard 행은 PR 3 · 레인 통지 2026-09-26).

