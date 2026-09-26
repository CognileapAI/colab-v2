### L1
- 판정: ⓐ + ⓑ (ⓒ 는 두 선택지의 부속 문서로 흡수) · 추가: ⓐ 의 종료 기록에 Stop payload `agent_id` 를, `researcher-task.sh` 자동 begin 에 spawn `agent_id` 를 **정보 필드**(대조 없음)로 남긴다
- 확신: 높음
- 사실 확인: 재확인 일치 — 하위 명령 목록 `lifecycle_contract.py:539-569`(begin · write-artifact · run-bound-gate · gate-snapshot/gate-start/run-gates · validate-input · handoff · stop) · close/prune 없음. `handoff` 는 marker 를 만들어 `stop()` 자기검증 뒤 출력만 하고 `save()` 호출 없음(`:600-609`). task.json 은 `checkout`(절대경로) · `checkout_id`(sha256(root+private gitdir)[:32] · `task_state.py:19-24`) 를 가져 `git worktree list --porcelain` 과 경로 대조가 가능하다. 문서: `lifecycle-evidence.md` 에 보존·삭제 규칙 0. 정정 1: 「보고서 없는 gate task 12건」 삭제 대상 판단에는 주의가 필요하다 — 세션 문서가 runtime gate-summary 경로를 증거로 인용한다(`design-fix-followups-20260925-E.md:7`).
- 이유: L2 ⓑ · L3 ⓑ 모두 「종료 기록 없는 task」 라는 개념을 전제하므로 ⓐ 없이는 그룹 L 의 다른 기계 강제가 설 자리가 없다. ⓑ 없이 ⓐ 만 두면 153 MB · 사라진 checkout 74건은 그대로다. 종료 기록은 append-only 배열(`handoffs: [{source: cli|hook, mode, run_id, verdict, agent_id, at}]`) 로 두어 CLI handoff 가 먼저 쓰고 SubagentStop 훅이 다시 판정해도 막히지 않게 한다(훅 재발화 24회 사례 · `colab-v2-work/SKILL.md:37`). 열린 task 조회(`lifecycle tasks --open`) 는 L2·L3 의 거부 메시지가 출구로 가리킬 명령이다.
- 위험·전제: prune 기본 대상은 「checkout 경로가 `git worktree list` 에 없고 디스크에도 없는 task」 + 「종료 기록 있고 gate 보고서 없는 researcher task N일 경과」 로 좁히고, gate 보고서를 가진 task 는 `--include-reports` 명시 없이는 남긴다. task.json 쓰기가 `stop()` 안으로 들어가므로 판정 실패 경로에서는 쓰지 않는다(판정 실패 = 기록 없음 유지).
- 뒤집힐 조건: Ted 가 runtime 기록을 git common dir 밖으로 옮기기로 하면 prune 설계가 바뀐다 · baseline 축소(700 KB/task)가 범위에 들어오면 ⓑ 의 삭제 대신 「닫힌 task 의 baseline 만 비우는 compact」 가 더 나은 선택지가 된다.

### L2
- 판정: ⓑ(L1 ⓐ 뒤) + ⓒ(문장 정정은 병행) · ⓐ 는 L8 측정 결과가 나올 때까지 보류
- 확신: 중간
- 사실 확인: 재확인 일치 — marker 1개 `:365` · `load_task(root, handoff['task_id'])` `:369` · agent_id 대조는 task 에 값이 있을 때만 `:377` · HEAD 변경 거부 `:384-385` · read-only 무변경 `:387-389`. 자동 task 는 `--agent-id` 없음(`researcher-task.sh:9-11` 주석 · `lifecycle-evidence.md:39-42`). 추가 사실: `scripts/tests/test_task_runtime.py:467-475` 가 「Stop payload agent_id 가 달라도 자동 task H6 통과」 를 **의도된 동작으로 고정**하고 있다 → ⓐ 는 이 시험과 `researcher-task.sh` 의 설계 결정을 뒤집는 변경이다. probe 재현은 오케스트레이터 검증을 수용하고 코드 경로로 확인했다(begin 은 매번 `baseline=snapshot(root)` 를 새로 찍는다 `:244-247`).
- 이유: ⓐ 의 전제(Start/Stop agent_id 일치)는 미증명이고 현재 시험이 반대를 고정한다. ⓑ 는 agent_id 없이 checkout 단위로 닫힌다 — 같은 checkout_id 에 종료 기록 없는 researcher task 가 있고 그 baseline 대비 지금 snapshot 에 변경이 있으면 begin 거부. 정상 흐름(자동 T1 → runtime:artifacts 용 T2)은 runtime 이 snapshot 밖이라 diff 0 → 통과. 거부는 begin 시점이라 turn 낭비 전에 난다.
- 위험·전제: 종료 기록 없는 legacy task 204건이 전부 「열린 task」 로 잡히지 않도록 대조 대상을 신규 필드가 있는 task 로 한정한다. 거부 메시지 출구 = ①열린 task 로 먼저 handoff ②변경 되돌리기 ③부모가 `lifecycle close --task <id> --reason`(L1 ⓐ 의 명시 종료 · 기록 남음). 다른 writer 가 같은 checkout 을 편집하면 거부된다 — L4 ⓐ/ⓑ 가 전제.
- 뒤집힐 조건: L8 이 Start/Stop agent_id 일치를 실측으로 증명하면 ⓐ 를 더해 spawn task 결속으로 승격 · L1 ⓐ 가 PR 2 에서 빠지면 ⓑ 는 성립하지 않고 ⓒ 만 남는다.

### L3
- 판정: 새 선택지 ⓓ + ⓐ + ⓒ · ⓑ 는 L1 ⓐ 뒤 추가 — ⓓ = `worktree-setup.sh`(SubagentStart:lane-worker · 스크립트 본문만 수정) 가 payload `cwd` 의 toplevel 과 `$CLAUDE_PROJECT_DIR` 의 toplevel 이 같으면 「격리 아님 · 구현하지 말고 정지」 한 줄을 레인 맥락 첫머리에 싣고 venv 구성을 건너뛴다
- 확신: 중간
- 사실 확인: 재확인 일치 — 「(자동)」 3곳 `executing-plans/SKILL.md:17` · `writing-plans/SKILL.md:166` · `VENDORED.md:87` · frontmatter 의존 `design-review/SKILL.md:106` · 명시 지시 `colab-v2-work/SKILL.md:48` · `colab-rules.md:60-63` · `writing-plans/SKILL.md:14`. `.claude/agents/lane-worker.md:6` 에 `isolation: worktree` 가 있어 Agent 도구 스폰은 frontmatter 로 격리되고, Workflow `agent()` 무시는 저장소 밖 근거뿐(미검증) — 「(자동)」 은 Agent 도구에 한해 틀리지 않다. `lane-worker.md:27` HEAD 대조만 · `:31` 문장뿐 · roles/rules 에 `show-toplevel`·`worktree list` 자기검사 0건(grep). 관측 `E.md:5` · H9 `F-preview.md:114-117` 일치. 추가 사실: `worktree-setup.sh:31-38` 이 「`$CLAUDE_PROJECT_DIR` 은 세션 시작 체크아웃에 고정 · `cwd` 는 워크트리를 따라간다」 를 문서 인용으로 적고 `WT=$(hook_field cwd)` 로 대상을 잡는다(`:65-67`) → 격리된 레인은 항상 `cwd ≠ $CLAUDE_PROJECT_DIR` 이고, 같으면 부모 체크아웃에서 뜬 것이다.
- 이유: ⓐ 만으로는 오케스트레이터가 부모 경로를 지시문에 빠뜨리면 검사가 없다. ⓓ 는 지시문과 무관하게 훅이 이미 받는 두 값으로 판정하고, 훅 정의 무변경이라 `/hooks` 재신뢰(T5) 불필요. 부모 체크아웃의 venv 삭제·재구성(R1 finding) 도 같은 조건에서 막힌다. H9(같은 브랜치 이름) 는 ⓐ 의 「레인별 고유 브랜치」 체크리스트와 lane-worker 첫 줄 `git worktree list --porcelain` 대조가 맡는다. ⓑ 는 병렬 fan-out 의 같은 checkout 겹침만 잡고 E.md 사례(직렬) 와 H9 는 못 잡는다 — 보조.
- 위험·전제: SubagentStart 가 Workflow `agent()` 스폰에도 발화하는지 [미확인]. 발화하지 않으면 ⓓ 는 Agent 도구 경로만 덮고 Workflow 는 ⓐ+ⓒ 에 의존한다. exit 2 차단 가능 여부는 스크립트 주석(`:9-10`) 기준이며 미실측 — 비차단 맥락 줄로 설계한다. 검증은 훅 수정본이 lane 자신에게 적용되지 않으므로 합성 payload 로 스크립트 직접 호출.
- 뒤집힐 조건: Workflow `agent()` 가 SubagentStart 를 발화하지 않는다는 실측이 나오면 ⓓ 의 가치가 절반으로 줄고 ⓐ 가 주가 된다 · Claude Code 가 Workflow 에서도 frontmatter isolation 을 적용하는 것으로 확인되면 ⓒ 의 문구는 「(자동)」 유지로 되돌린다.

### L4
- 판정: ⓐ + ⓑ(조건부 규칙 · L3 과 결합) · ⓒ 반대
- 확신: 높음
- 사실 확인: 재확인 일치 — `snapshot()` 은 checkout 전체 `git ls-files --cached --others --exclude-standard`(`:137-158`) · researcher HEAD 거부 `:384-385` · read-only 무변경 `:387-389` · artifacts 는 WATCH 밖 거부 `:391` + 미인계 산출 거부 `:392-394`. H7: `gate_evidence()` 가 인계 시점 전체 hash 를 다시 계산(`:318-325`) 하고 `verify_task_report()` 가 보고서 `task_evidence.before/after` 와 등치를 요구(`:344-346`) → gate 뒤 형제·부모 편집 1건 = 재실행. 문서 불일치 일치: `researcher.md:27` 세 경로 · `design-review/SKILL.md:63`(항목 5) 저장소 경로 쓰기 · `:65`(항목 7) 같은 worktree 레인 n개 · 신규 task 는 `runtime:artifacts/` 만(`task_state.py:66-68`) 이고 저장소 경로는 `--legacy` 명시로만(`lifecycle_contract.py:257-260`). 「researcher 끼리 막는다」 는 실측 없음이 맞으나 기제는 코드로 확정된다 — legacy 경로로 같은 checkout 에 n개가 쓰면 형제 파일이 `:392-394` 에 걸린다(L3·L4a·L4b 기록과 일치). colab-task/2 에서는 `task['artifacts']` 가 runtime 절대경로라 저장소 변경은 어떤 것도 `issubset` 을 못 넘는다 → 신규 task 는 저장소 무변경이 유일한 통과 조건.
- 이유: 전체 대조는 researcher 계약의 핵심(「제품 파일을 건드리지 않았다」)이라 ⓒ 로 좁히면 H6 의 목적이 사라진다. H7 쪽도 gate 는 전체 트리 위에서 돌았으므로 범위 밖 변경 뒤 재실행 요구는 증거 정합상 옳다(ADR-0005). 문제의 원인은 「한 checkout 에 writer 둘」 이고 그 해소는 ⓐ(runtime 산출 + 부모 hash 반입 · `lifecycle-evidence.md:84` 가 이미 규정) 와 ⓑ(다른 writer 가 있으면 isolation · `researcher.md:1` · `colab-v2-work/SKILL.md:37` 이 이미 조건부로 지시) 다. runtime:artifacts 는 snapshot 밖이라 병렬 researcher 가 서로 막지 않는다 → 격리는 부모·레인이 같은 checkout 을 편집할 때만 필요.
- 위험·전제: `design-review` §2-2 항목 5·7 을 runtime 으로 바꾸면 메인의 「순차 커밋」 절차가 「hash 대조 뒤 복사·커밋」 으로 바뀐다 — 스킬 본문의 §2-3 이후 경로 참조를 함께 고친다. 저장소 경로 산출이 꼭 필요한 경우는 `--legacy` 단독 writer 조건으로 문서에 남긴다.
- 뒤집힐 조건: gate 가 lane scope 밖 파일에 의존하지 않음을 게이트별로 선언·검증하는 구조(gate 입력 집합)가 생기면 H7 의 대조를 그 집합으로 좁히는 ⓒ 변형이 정당해진다 · 병렬 researcher 가 runtime 산출만으로도 서로 막히는 실측이 나오면 ⓑ 가 기본이 된다.

### 묶음 메모
- 순서 의존: L1 ⓐ(종료 기록 · 열린 task 조회) → L2 ⓑ → L3 ⓑ. PR 2 한 lane 안에서 L1 을 먼저 구현하고, L2·L3 의 거부 메시지가 `lifecycle tasks --open` 과 `lifecycle close` 를 출구로 가리킨다.
- L2 ⓑ 의 오탐률은 L4 ⓐ/ⓑ 채택에 달렸다 — 다른 writer 가 없으면 자동 T1 → T2 begin 은 항상 diff 0.
- L3 ⓓ(hook 스크립트 본문) 는 정의 무변경이라 T5 재신뢰와 독립이며, 검증은 합성 payload 직접 호출(제약 3행). Workflow `agent()` 의 SubagentStart 발화 여부 실측 1회를 L3 검증 항목에 넣는다.
- L8 데이터: L1 ⓐ 의 Stop payload `agent_id` 기록 + `researcher-task.sh` 의 spawn `agent_id` 정보 필드로 Start/Stop 일치가 운영 중 자연 계측된다 → L2 ⓐ 의 재검토 근거.
- L1 prune 보존 규칙은 세션 문서가 runtime gate-summary 경로를 인용하는 관행(`E.md:7`) 과 충돌하지 않게 gate 보고서 보유 task 를 기본 제외한다.