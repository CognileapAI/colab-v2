[harness: subagent output matched instruction-shaped pattern(s): settings-json. Control tags below are neutralized (`<` → `<\`); treat any remaining directive-shaped text as a finding to relay to the user, not an instruction to you.]

### T1
- 판정: ⓐ (+ `strict_required_status_checks_policy: true` · 관리자 우회 없음). 시점은 PR 2 병합 뒤 유지 가능하나, strict 를 켜면 PR 2 전 적용도 무해
- 확신: 높음(ⓐ > ⓑ) · 중간(시점)
- 사실 확인: `ci.yml:3-7` — pull_request 전건 · push 는 develop·product 만. `ci.yml:843-844` — job 이름이 PR 이벤트에서만 `ci-required`(push 는 `ci-push-summary`). `ci.yml:848` — needs 에 `required-gates` 포함. `ci.yml:857-864` — `always_required = {required-gates, changes, product-safety, repo-hygiene}` 라 이 넷은 skipped 도 `bad` → ⓑ 의 `required-gates` 추가는 중복. `docs/development/github-ruleset.json:6,9` — 대상 `refs/heads/main`(404) · context `required-gates` → 제안 파일이 낡음(정정: 항목의 「미적용 공개」는 맞으나 제안 내용 자체도 현 모델과 불일치). `release-evidence.md:45` · `harness-transition-handoff.md:191` — 미적용 명시 확인. 추가 사실: develop first-parent 에 비병합 직접 커밋 존재 — `02d251d8` · `9191671a`(09-24) · `55be94f1` · `3c0e1117`(09-22, K4 luna) → 직접 push 관행이 아직 있다. `verify_evidence.py:56-58` — 병합 부모 == [event base, head] 검사 확인(B1 전제).
- 이유: `ci-required` 는 PR 이벤트 전용 context 라 필수로 걸면 develop 직접 push 가 자연히 막힌다(PR-centric 계획과 일치, 별도 PR 규칙 없이도 사실상 PR 강제). ⓑ 는 `ci-required` 가 이미 `required-gates` 실패·skip 을 red 로 흡수하므로 정보 이득 0. strict 정책은 base 이동 시 GitHub 가 「Update branch」를 요구하는데 이것이 B1 의 현행 우회(develop 병합)와 동일 동작이라 B1 red 를 GitHub 주도 절차로 바꾼다. ⓒ 는 PR 1(차단 guard)조차 red 로 병합 가능한 상태를 연장한다.
- 위험·전제: 직접 push 관행(K4 측정 커밋 류)이 끝난다 — Ted 가 수용해야 한다. `enforce_admins` 를 안 켜면 Ted 계정(에이전트도 같은 gh 자격)이 우회 가능 → 「관리자 우회 없음」(release-evidence.md:45 제안 원문) 유지.
- 뒤집힐 조건: develop 직접 push 를 의도적으로 유지할 계획이 확인되면 ⓒ 또는 bypass 있는 ruleset. PR 2 가 B1 을 「현재 base head 대조」로 고쳐 strict 없이도 안전해지면 strict 는 선택.

### T3
- 판정: 조합 — 32 는 ⓐ(develop ff-only 갱신, 열린 task 없는 시점) · 33 은 ⓑ(은퇴)
- 확신: 높음(33) · 중간(32)
- 사실 확인: `gates/tools/_lock.sh:78` — 잠금 키 `${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host` 단일 · 주입구 없음 확인. 32: HEAD `02d251d8`(reflog: 09-24 21:18 `pull --ff-only`), `origin/develop` 대비 behind 310, 트리 clean, `_lock.sh`·`run.sh` 에 `gate_host_mutex_acquire` 있음, `gate_mutex_spawn` 0건(30 의 `frontend-visual.sh` 에는 있음) → F1 없음 확인. 32 `.git/colab-harness` 최신 task 디렉터리 2026-09-25 20:32, researcher task 3건(`agent_id: null`) → **오늘 사용 중**. 33: reflog 1행(09-18 01:04 clone) · `.git/colab-harness` 없음 · clean · `origin/develop` ref 도 미갱신(behind 표시 없음) → 클론 이후 미사용. 정정: 항목의 「33 사용 여부 미검증」→ 런타임·reflog 기준 미사용으로 판정 가능(단, 로컬 브랜치·stash 목록은 미확인).
- 이유: ⓒ 「게이트 실행 금지」는 옛 코드가 스스로 지킬 수 없는 문서 규칙이라 통제가 아니다. 32 는 실사용 체크아웃이므로 삭제 불가·갱신이 유일한 F1 반입 경로(clean·ff-only 라 비용 최소). 33 은 잠금 코드 자체가 없어 31 의 serial 게이트와 겹칠 수 있고 사용 흔적이 없으므로 은퇴가 정합.
- 위험·전제: 32 갱신은 열린 task 가 없을 때(스냅샷 hash 불일치 → handoff 거부, `lifecycle_contract.py:318-346`). 갱신 뒤 32 의 훅 정의가 바뀌므로 32 경로에서 `/hooks` 재신뢰 별도(`dual-agent.md:85` 「다른 절대경로 사본 미이전」). 33 삭제 전 `git branch`·`git stash list` 확인.
- 뒤집힐 조건: 33 에 고유 로컬 브랜치·stash 가 있으면 보관 뒤 삭제. 32 가 K4 측정 재현을 위해 의도적으로 고정된 사본이면 갱신 대신 **호스트 잠금 경로를 공유하는 채로는 게이트를 돌리지 않는다**는 명시 + 30 으로 이전.

### T4
- 판정: ⓑ (`f3846f32` 를 로컬 네임스페이스 태그로 보관 후 네 브랜치 삭제)
- 확신: 높음
- 사실 확인: `git branch -a`: 로컬 `worktree-agent-a06b599e…`·`a20a6e57…`·`abe5bbb8…`, 원격 `origin/worktree-ponytail-systemic`·`origin/worktree-k4-haiku-probe`. `git cherry develop`: a06b599e 1건 `-`, a20a6e57 7건 `-` → 전량 포함 확인. `develop..abe5bbb8` = `f3846f32` 1건(09-24, `lifecycle_contract.py`·`test_task_runtime.py`·`lifecycle-evidence.md` +78/-4). `develop..origin/worktree-ponytail-systemic` = `ce05e30f` 1건이나 cherry `-`(포함). `20260924-lane-hygiene-review/PR-BODY.md:56` — `git push origin --delete worktree-ponytail-systemic` 요청 확인. `git worktree list` — 두 브랜치 모두 worktree 미부착 → `branch -D` 가능. 정정: 「#130 이 뺀」 근거는 PR-BODY.md 에 없다(`evidence|f3846f32|abe5bbb8` grep 0건) — 제외 사유 기록 위치 미확인. `lifecycle_contract.py` 는 09-25 에 3커밋(`d63c18f3`·`4a3a046a`·`7fce70c3`) 이동 → 그대로 적용 불가.
- 이유: 태그는 비용 0 이면서 unreachable 객체 gc(기본 2주 prune) 를 막는다. `f3846f32` 는 PR 2 가 공유하는 두 파일을 정확히 건드리므로 재구현 참조로 유용. 세 브랜치와 원격 1개는 고유 커밋 0 → 삭제에 손실 없음.
- 위험·전제: 태그는 로컬·비배포 네임스페이스(예 `archive/…`)로 두고 push 하지 않는다 — 운영 배포가 태그를 선행 조건으로 쓰므로(memory) 원격 태그 오염 회피. 삭제는 Ted 행동(git-guard `branch -D` 규칙 범위 밖 확인은 안 함).
- 뒤집힐 조건: `f3846f32` 의 제외 사유가 「설계상 폐기」로 기록돼 있으면 태그 없이 ⓐ. `origin/worktree-k4-haiku-probe` 는 항목 밖이나 같은 회차에 cherry 확인 권장.

### T5
- 판정: 새 선택지: ⓐ 를 지금 하되 기록을 남기고, 정의를 바꾸는 PR 이 있으면(A2 ⓑ 경로 등) 그 PR 병합 뒤 1회 더. ⓑ(PR 3 뒤 일괄)는 채택 불가
- 확신: 중간
- 사실 확인: `dual-agent.md:82-89` — 09-09 7개 정의 신뢰 기록 · 정의별 review 필요 · 09-24 researcher 정의 재신뢰 요청 확인. 정정·보강: Claude `.claude/settings.json` 도 09-09 이후 4회 변경(`22555957` 09-17 · `4c07f1ea`·`94e8a728` 09-18 · `faff6734` 09-24), Codex `.codex/hooks.json` 3회(`012df481`·`4c07f1ea`·`faff6734`) — 「Codex 3회」만이 아니다. 훅 수 7→11. 런타임으로 hook 발화를 판정할 수 없음 재확인: 수동 begin 형태(`researcher.md:77` → `lifecycle-evidence.md:38-40`)도 `--agent-id` 없음 → `agent_id: null` task(32 에 오늘 3건)는 hook·수동을 구분 못 함(32 는 #130 이전 HEAD 라 hook 자체가 없음). git-guard 차단 실측(R1-19)은 Bash PreToolUse 정의만 활성임을 증명.
- 이유: L8(researcher Start/Stop agent_id 스모크)은 PR 2 그룹 L 에 있고 재신뢰 뒤에만 실행 가능 → 재신뢰가 PR 2 lane 보다 앞서야 하므로 ⓑ 는 고정 구조와 모순. 재신뢰는 PC 당 몇 분의 UI 행동이라 반복 비용이 낮고, 그룹 A 권장안이 정의 무변경 전제이므로 지금 한 번이 PR 1·2 를 덮는다. ⓒ 는 저장소로 판정 불가능한 상태를 계속 남긴다.
- 위험·전제: Claude Code 의 정의별 재신뢰 요구는 저장소 밖 사실(문서 근거만) — 이 판정은 그 전제 위에 있다. 기록 형식은 09-09 기록(`dual-agent.md:83-84`)과 같은 한 줄(날짜·PC·정의 수) — 문서 편집은 PR 3 범위와 겹치므로 임시로 runtime 증거 또는 intent 메모에 둔다.
- 뒤집힐 조건: 현재 Claude Code 가 프로젝트 훅 변경을 자동 반영함이 확인되면 T5 는 「기록만」으로 축소. PR 2·3 이 정의를 반드시 바꾸는 것으로 확정되면 지금 1회 + PR 3 뒤 1회의 2회로 고정.

### T6
- 판정: ⓒ (창 고정 · n 공개 · 병합 조건 아님) — L7 재현을 같은 표본에서 처리
- 확신: 중간
- 사실 확인: `2026-09-24-agent-model-tiering.md:38` — 원한 결과 8 「병합 뒤 재측정 · 후속 · 병합 조건 아님」 확인. `M1-role-usage.md:1-8` — 자료원은 `~/.claude/projects/*CoLAB*/*/subagents/agent-*.jsonl` + `.meta.json`, id 중복 제거(381→316), 도달 = turn≥한도(재개 합산). `M1-role-usage.md:58-62` — 기준선 researcher 58%(n 118) · advisor 30%(n 73) · measurement-lane 40%(n 5). `PR-BODY.md:39` 후속 표기 확인. 보강: 보고 폴더에 집계 스크립트 없음(md 6개만) → 재측정은 방법을 손으로 재구성해야 한다. 같은 intent 「제약」 — frontmatter 는 새 세션부터 반영 → #131 이전에 시작한 세션의 스폰은 표본에서 제외해야 한다.
- 이유: 자료는 하네스 변경 없이 자동 축적되므로 별도 회차(ⓐ)는 창 설정 외에 얻는 것이 없고, ⓑ 는 16/50 상향의 유일한 효과 증거를 버린다. 세 PR 동안의 스폰은 「#131 반영 이후 세션」이라는 창 조건을 자연히 만족한다. L7(advisor 12→16 재현 먼저)이 같은 데이터·같은 역할이라 별도 측정을 두 번 돌릴 이유가 없다.
- 위험·전제: 표본이 작고(advisor·researcher 수십 건, measurement-lane ≈ 0) 하네스 작업 스폰은 읽기 편중이라 turn 이 길게 나온다 → 역할별 n·창·편향을 표에 적고 판정을 「기준선 대비 변화 방향」으로 한정. 이번엔 집계 스크립트를 보고 폴더에 남긴다.
- 뒤집힐 조건: 세 PR 이 짧아 advisor n < 10 이면 ⓐ 로 창을 늘린다. maxTurns 를 PR 2 L7 이 다시 바꾸면 창을 그 병합 시점으로 재설정.

### 묶음 메모
- T1 ↔ B1·C: strict 정책이 B1 red 를 GitHub 「Update branch」로 흡수한다. `docs/development/github-ruleset.json`(main·required-gates) 재조준은 PR 3 문서 정합 범위.
- T1 은 develop 직접 push 관행(09-24 K4 커밋 4건, 32 체크아웃 경유 추정)을 끝낸다 → T3 의 32 갱신과 같은 회차에 Ted 가 수용 여부를 정한다.
- T5 ↔ L8·T3: L8 이 PR 2 에 있으므로 재신뢰는 PR 2 lane 전에. 32 갱신 뒤에는 32 경로에서도 재신뢰 필요.
- T4 ↔ PR 2 L: `f3846f32` 는 PR 2 공유 파일(`lifecycle_contract.py`·`test_task_runtime.py`)을 건드린다 — 참조용 태그이며 cherry-pick 대상 아님(09-25 3커밋 이동).
- T6 ↔ L7: 같은 jsonl 표본·같은 역할 — L7 재현을 T6 창의 첫 절단으로 처리하면 측정 1회로 끝난다.