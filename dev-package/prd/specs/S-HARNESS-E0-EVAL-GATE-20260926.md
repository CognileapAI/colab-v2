# Spec: 하네스 개선 — phase E0 (PR E0 · eval gate 기제 + 실측 1회 + 실패 4건 분류)
출처 intent: `dev-package/intent/2026-09-25-harness-improvement.md`
출처 절: 「판정 기록」 7라운드(Ted 원문 "전부 권고대로 엄격하게 다시짜") · 6라운드 격차 ① · Q-A ⓐ(eval 을 PR 2 전 1회 · 지침 변경 PR 은 설정 해시 일치 결과 없으면 red · R2-12 「재실행 제외」 번복 · 해시 집합 = `.claude/**` · `.agents/**` · `gates/**` · hook 스크립트 확정). 근거(저장소 밖): `~/.claude/reports/harness-state-20260925/playbook-gap-20260926/direction.md` 격차 1 · §3 선행 ⓑ · §5 즉시 실행 · `system-first-recut/recut.md` §5-1(선행 순서) · gate-1 판정 `master-plan-20260926/verify-e0-sred.md`(차단급 2 · 개선 6 반영). 총괄 = `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-PLAN-20260926.md` §2 E0 · T 번호는 총괄 Ted 행동표(T12 실측 · T16 게시 · T17 분류 판정).
순서: PR 1 병합 → Ted(T1 ruleset · T11 PAT) → **E0(이 문서)** → S-red → PR 2(7라운드 `:609` 확정 · 대안 「S-red → E0」 는 우려 항목 #6 · Ted). 줄 번호 기준 = 브랜치 `claude/harness-improvement` HEAD `27f7fb6c`(PR 1 병합 · 2026-09-26 재열람).
모든 커밋 메시지 마지막 문단 = `Intent-Ref: dev-package/intent/2026-09-25-harness-improvement.md` 트레일러(6라운드 트레일러 결함 재발 방지 · `gates/run.sh:365-369` intent-ref 판정 경로: `gates/**`·`scripts/**`·`.github/**` 는 판정 밖이나 `eval/harness/**`·`dev-package/**` 는 안 — `intent_ref.py` 목록은 레인이 착수 시 대조).
설계 원칙(Ted 2026-09-26): 규칙은 시스템(gate · CI · hook)이 강제 · 산문은 포인터. 이 spec 의 모든 단위는 ⑴ 강제 기제(파일 · 이벤트 · fail-open/closed · Claude/Codex) ⑵ 증명 시험(파일 + 케이스 + 실행 게이트) ⑶ 병합 조건 ⑷ 지우는 산문 ⑸ 소유 PR = E0 를 적는다 · 장치 없는 단위는 「산문 · 맥락만」으로 표기한다.

## 1. 문제 진술
- playbook 의존 순서 「evals 가 CLAUDE.md · skills · hooks 변경을 gate 한다」 위반: `harness-eval` CI 잡은 면제 모드(`.github/workflows/ci.yml:696-700` `COLAB_HARNESS_EVAL_EXEMPT: '1'`) · 로컬 `all` 도 면제(`gates/README.md:62-71`). 마지막 실측 = `eval/harness/results/20260912-211809/summary.md:3`(과제 20 · green 16 · 실패 4 · USD 31.5546). PR 1 이 hook 4종(`git-guard.sh` · `test-file-guard.sh` · `decision-number-guard.sh` · `researcher-task.sh`/`worktree-setup.sh`/`css-edit-audit.sh` 출력 형태)을 바꾸고도 실행 0.
- 면제와 결과 사이에 결합이 없다: `gates/tools/harness-eval.sh:87-96` 면제 분기는 `H??-*/` 디렉터리 수만 세고(`count_tasks` `:44-55`) 어느 설정에서 잰 결과인지 보지 않는다. `results/<run>/summary.md` 에는 상한·회차만 있고(`eval/harness/run.sh:257-270`) 설정 식별자가 없다 → 「어떤 설정을 쟀는가」를 기계가 대조할 수 없다.
- 필터 누락: `ci.yml:119-128` `harness` 필터에 `.claude/settings.json`(permissions · hooks 정의) · `gates/**`(판정부) · `.claude/rules/**`(always-on) · `eval/harness/**`(러너 · 셀프테스트 · 결과) 이 없다. `gates/tools/ci-filter-check.py:39-49` `WANT_PATTERNS` 도 같은 집합이라 누락을 잡지 못한다(같은 원본을 두 벌로 둔 drift).
- 신선도 신호 0: `scripts/harness/check.py:78-121` harness-contract 는 eval 결과를 보지 않는다. 모델·CLI 기본값은 저장소 설정과 무관하게 바뀐다(`eval/harness/README.md:108` 「러너는 모델을 지정하지 않으므로 호출 환경의 기본값을 탄다」).
- 실패 4건 미분류: H14 · H15 · H16 · H18 각 0/2(`summary.md:22-26`) · 2주 무변. 6라운드 기록은 「추정 · 과제 기대문 미대조」.

## 2. 원한 결과 (V-id)
- V-E1 러너가 회차마다 `results/<run>/config-hash.json`(`hash` · `files` · `head` · `dirty` · `selected` · `patterns_sha256` · `claude_version`)을 쓰고 `summary.md` 에 `- 설정 해시 — <hash> · 파일 N · HEAD <sha> · dirty N` 1줄을 넣는다 — 확인: `eval/harness/tests/run-selftest.sh` 새 케이스 ⓛ.
- V-E2 해시 정본 = `eval/harness/config-paths.txt` 1파일 · 계산기 = `eval/harness/config_hash.py` 1모듈 · 러너 · 게이트 · ci-filter-check 가 같은 파일을 읽는다 — 확인: `scripts/tests/test_harness_eval_gate.py` ⑴–⑷.
- V-E3 `gates/run.sh harness-eval` 면제 모드가 「현재 설정 해시와 일치하는 전수 결과(선택 실행 아님 · 준비 0)」 없으면 exit 78 + `::gate-readiness-failure::gate=harness-eval|cause=입력미선언|missing=eval-result:<hash>` · 일치 결과의 green 집합이 직전 결과보다 줄면 exit 1(판정) · 일치 + 무회귀면 exit 0 에 결과 id · 계수 · `hash(head)=hash(회차)` 두 값 출력 — 확인: `gates/tools/harness-eval-selftest.sh` ⓛ–ⓡ.
- V-E4 CI: `harness` 필터에 `.claude/settings.json` · `.claude/rules/**` · `gates/**` · `eval/harness/**` 추가(4줄) · `ci-filter-check` ㈏ 가 필터 ⊇ `config-paths.txt` 를 단언 · 면제 스텝은 그대로(`record` 경유 · exit 78 → `verify_evidence.py:232-233` `EvidenceReadinessError` → `required-gates` 78(`:358-361`) → `ci-required` 실패(`ci.yml:866-869` `result != success`)) — 확인: `scripts/tests/test_ci_eval_policy.py` 변이 케이스 추가.
- V-E5 harness-contract 가 최신 결과 id 가 30일보다 오래되면 `warning: harness-eval newest result <id> is <n> days old (>30)` 1줄(exit 불변) · 30일 이내면 green 줄에 `harness-eval newest <id> (<n>d)` — 확인: `test_harness_eval_gate.py` ⑸.
- V-E6 E0 최종 코드 커밋 상태에서 전수 실측 1회(과제 20 · 실행 40 · `COLAB_EVAL_TIMEOUT=93 COLAB_EVAL_BUDGET=2.01`) · `results/<run>/` 커밋(summary · config-hash.json · out · expect) · 그 run 의 `hash` == PR 머지 커밋의 해시 → CI `harness-eval` green(자기 적용 증명) · 회차 뒤 해시 집합 파일 push 0.
- V-E7 실패 4건 분류(과제 기대문 결함 / 하네스 결함 / 겹침)가 intent 「확인」 절(`:522-526`)에 줄 추가로 기록되고, 재실측 결과(green/red)로 분류가 확정된다.
- V-E8 문서: `eval/harness/README.md` 「결과」 절 = 여섯 종 중 넷 추적 · 새 절 「설정 해시 · 면제 조건」 · `gates/README.md:47` harness-eval 행에 면제 조건 갱신 · `ci.yml:641-650` 주석 교체 · 옛 문장(「면제라도 건수만」·「다섯 종 중 셋」) 0건.
- V-E9 Codex 영향 없음: `scripts/agent-bridge.py` · `.codex/**` · `scripts/codex-harness-eval.py` diff 0 · `python3 scripts/agent-bridge.py check` green.
- V-E10 게이트 종료코드 0/1/78 의미 유지: 결과 부재/부분 실행/준비>0 = 78(판정 불가) · 회귀 = 1(규율 위반) · 일치+무회귀 = 0.

## 3. 해법 개요
- 코드: `eval/harness/config_hash.py`(hash · verify) + `config-paths.txt`(정본) · `run.sh` 기록 1블록 · `harness-eval.sh` 면제 분기에 verify 호출 · `ci-filter-check.py` 정본 읽기 · `check.py` 신선도 1함수 · `ci.yml` 필터 4줄 + 주석.
- 실측: 최종 코드 커밋에서 러너 1회(≈32 USD) · 결과 커밋 · 분류 기록.
- 훅 정의(`.claude/settings.json` hooks · `.codex/hooks.json`) 무변경 → `/hooks` 재신뢰 0. 등록부(`.agents/ci-producers.json:348-378`) 무변경(검사 이름 · 명령 동일). `parallelism.toml:242` serial 유지.

## 4. 구현 결정

### 4.1 설정 해시 정의 (단위 E0-1)
- 정본 `eval/harness/config-paths.txt`(git pathspec glob · 1줄 1패턴 · `#` 주석): `AGENTS.md` · `CLAUDE.md` · `.claude/**` · `.agents/**` · `gates/**` · `scripts/harness/hooks/**` · `eval/harness/config-paths.txt`(자기 자신). Ted 목록(Q-A ⓐ: `.claude/**` 전체 — rules · settings.json · settings.local.json · agents · skills · hooks · commands 포함 · `.claude/worktrees/` 는 `--exclude-standard` 로 자동 제외 · `.agents/**` · `gates/**` · hook 스크립트) + 모델 입력에 실리는 2종(`AGENTS.md` · `CLAUDE.md` — `CLAUDE.md` `@AGENTS.md` 로 매 호출 적재 · README:71-72) 추가 → 우려 항목 #4. 추가(8라운드 판정 #5 ⓐ): `eval/harness/**` + `:(exclude)eval/harness/results/**`(측정 도구 · 러너 · expect 를 고쳐 만든 green 도 재실측을 부른다 · results 는 자기 참조라 제외). 제외: `.codex/**` · `scripts/agent-bridge.py`(Codex 전용 · Claude 러너 입력 아님) · `scripts/harness/*.py`(판정기 · 모델 입력 아님).
- 계산(`config_hash.py compute --root R`): 파일 집합 = `git -C R ls-files -z --cached --others --exclude-standard -- ':(glob)<pattern>'…`(추적 + 비무시 미추적) · 파일마다 sha = `git hash-object --stdin < path`(symlink 는 링크 텍스트를 해시 · 깨진 링크 = `missing` · `.claude/hooks/**` → `scripts/harness/hooks/**` 링크의 본문은 후자로 1회만 계수) · 정렬된 `path\0sha\n` 의 sha256 = `hash`. 부수 필드: `files`(수) · `head`(`rev-parse HEAD`) · `dirty`(집합 안 `status --porcelain` 경로 목록) · `patterns_sha256` · `computed_at`. 내용 기준이라 실행 시 dirty 였던 편집을 그대로 커밋하면 같은 해시(V-E6 전제).
- 강제 기제: 없음(계산기) · Claude/Codex 공통 파일 · 시험 = `scripts/tests/test_harness_eval_gate.py` ⑴ 같은 트리 두 번 = 같은 해시 ⑵ 패턴 안 파일 1바이트 변경 = 다른 해시 · symlink 대상 변경 = 다른 해시 · 링크 텍스트만 변경 = 다른 해시 ⑶ 패턴 밖(`frontend/src/x.ts` · `eval/harness/H01-*/task.md`) 변경 = 같은 해시 ⑷ 미추적 hook 파일 추가 = 다른 해시 · 실행 게이트 = `harness-contract-selftest`(`gates/run.sh:357` 목록에 `test_harness_eval_gate.py` 만 추가).
- 병합 조건 = `harness-contract-selftest` ⑴–⑷ green · 지우는 산문 = 없음.

### 4.2 러너 기록 (단위 E0-2)
- `eval/harness/run.sh` `:76-78`(RUN_ID · OUT) 직후: `python3 "$HARNESS_DIR/config_hash.py" compute --root "$(git -C "$HARNESS_DIR" rev-parse --show-toplevel)" --selected "${COLAB_EVAL_ONLY:-all}" --claude-version "$(claude --version 2>/dev/null | head -1)" > "$OUT/config-hash.json"` · 실패(rc≠0 · git 부재)는 `ready_red "config-hash" …`(78 · `:37-44` 함수) — 해시 없는 결과를 만들지 않는다. `:259-270` summary 블록에 `- 설정 해시 — <hash> · 파일 N · HEAD <sha> · dirty N · 선택 <selected>` 1줄 · `:277` 근거 줄에 `config-hash.json` 추가.
- 시험 seam 유지(`:23-26` 3개) · 새 seam 없음: 셀프테스트는 임시 과제 뿌리(`COLAB_EVAL_TASKS_DIR`)가 git 저장소 밖이라 `--root` 는 러너 자신의 저장소(`HARNESS_DIR` 상위) → 셀프테스트 결과 json 의 해시는 실 저장소 해시(값 자체는 단언하지 않고 존재·필드만 단언).
- 추적: `eval/harness/results/.gitignore` 는 `*.raw.*.json` · `*.err.*.txt` 만 제외 → `config-hash.json` 은 자동 추적 · README 「결과」 표에 행 추가.
- 강제 기제: 러너(회차마다 · fail-closed 78 · 도구 무관) · 시험: `eval/harness/tests/run-selftest.sh` 새 ⓛ 「2/2 green 회차에 `config-hash.json` 존재 · `hash` 64hex · `selected == all` · summary 에 `설정 해시` 줄」 · ⓜ 「`COLAB_EVAL_ONLY=H01` 회차는 `selected == H01`」 · 케이스 수 15 → 17(`:269` · `:272` 문구 갱신). 실행 게이트 = CI `harness-eval` 잡 `harness-runner-selftest`(`ci.yml:694`) · 로컬 `harness-eval-selftest` 는 러너 셀프테스트를 부르지 않으므로 레인은 `bash eval/harness/tests/run-selftest.sh` 직접 1회(검증표 V-E1).
- 병합 조건 = CI `harness-runner-selftest` 17/17 · 지우는 산문 = 없음.

### 4.3 fail-closed 위치 = `gates/tools/harness-eval.sh` 면제 분기 (단위 E0-3 · 결정)
- 선택지: ⓐ `harness-eval.sh:87-96` 면제 분기에서 verify(게이트 안) ⓑ `verify_evidence.py` `collect_ci` 에 harness-eval 전용 분기 ⓒ `required-gates` 잡 새 스텝. 결정 ⓐ: ⑴ 로컬 `all`/`task` 와 CI 가 같은 판정(「게이트가 보는 것 = 사람이 보는 것」 · `gates/README.md:47` 원칙) ⑵ 등록부 · `record` 명령 무변경 → `.agents/ci-producers.json` diff 0 · `verify_evidence.py` diff 0 ⑶ ⓑ·ⓒ 는 CI 에서만 막고 로컬 면제는 그대로 통과 → 「면제 = 결과 없이 통과」 상태가 로컬에 남는다.
- 동작(`:87-96` 교체): `N` 계수 후 `python3 "$REPO_ROOT/eval/harness/config_hash.py" verify --root "$REPO_ROOT" --results "${COLAB_EVAL_RESULTS_ROOT:-$REPO_ROOT/eval/harness/results}" --tasks "$N"` 호출 · verify 종료코드 그대로: `78` = 일치 결과 없음/선택 실행뿐/`준비 > 0`/과제 수 ≠ N → `ready_red "eval-result:<hash>" "이 설정 해시로 잰 전수 결과가 results/ 에 없다 · 실행 = COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=93 COLAB_EVAL_BUDGET=2.01 bash gates/run.sh harness-eval → results/<run>/ 커밋"`(`_readiness.sh:42-51` 표식 · `missing=` 에 해시) · `1` = 회귀(직전 결과 green 집합 − 일치 결과 green 집합 ≠ ∅ · 과제 이름 나열) → `red "…"` · `0` → `echo "harness-eval green — 면제 선언 · 과제 N건(미실행) · hash(head)=<hash> hash(회차)=<hash> 일치 결과 <run id> · green g/N · 판정 red r · 직전 <prev id>"`. `:92-94` 기존 3줄은 그 뒤 유지.
- verify 규칙(`config_hash.py verify`): 후보 = `results/*/config-hash.json` 중 `hash == 현재` ∧ `selected == all` ∧ `summary.md` 요약줄 `준비 0` ∧ 표의 과제 행 수 == `--tasks`; 없으면 78. 후보 중 id 최대 = R\*. 직전 = R\* 보다 id 가 작은 디렉터리 중 `summary.md` 가 있는 최신(해시 없는 옛 결과 포함 · 첫 적용 때 `20260912-211809`). `green(X)` = 표에서 `| <과제> | green |` 행. 회귀 = `green(직전) − green(R*)` ≠ ∅ → 1. 회귀 0 → 0. 요약줄 파싱 실패 · json 손상 = 78(입력을 못 읽음 · B3 분류 기준 「못 읽음 = 78 · 읽었는데 위반 = 1」).
- 회차 무효화 규칙(총괄 §0): 회차는 병합 직전 head 에서 1회 · 그 뒤 해시 집합 파일 push 금지(push 하면 게이트가 78 로 되돌아간다) · Update branch(develop 병합)는 집합 파일을 안 건드리면 해시 불변이라 허용 · 건드리면 재실측(§6).
- 실행 모드(`:61-84`)는 무변경(러너가 방금 낸 결과의 해시 = 현재 트리 · 자명).
- 강제 기제: `gates/run.sh harness-eval`(gate · `run.sh:506-515`) · CI `harness-eval` 잡(`ci.yml:681-711` · `changes.harness == 'true'` 인 PR) · fail-closed(부재 78 · 회귀 1 · 둘 다 `required-gates` → `ci-required` 실패) · Claude/Codex 공통(게이트는 도구 무관) · 병합 차단 효력은 T1(ruleset `ci-required` 필수) 적용 뒤.
- 시험(`gates/tools/harness-eval-selftest.sh` · `:86-105` `REPO_ROOT` seam 재사용 · 임시 git 저장소 fixture `WORK/cfg-repo`(`config-paths.txt` + `.claude/settings.json` + `gates/x.sh` + `eval/harness/results/`) · 결과 fixture 는 `config_hash.py compute` 로 실해시를 써서 만든다): ⓛ 면제 + 과제 3건 + 일치 결과 없음 → 78 + 표식 `missing=eval-result:` ⓜ 일치 결과(전수 · 준비 0 · green 3/3) → 0 + 출력에 run id · 두 해시 값 동일 ⓝ 일치 결과 green 2/3 · 직전 결과 green 3/3 → 1 + 회귀 과제 이름 ⓞ 일치 결과가 `selected=H02` 뿐 → 78 ⓟ 일치 결과 `준비 1` → 78 ⓠ fixture 의 `gates/x.sh` 1바이트 변경 뒤 ⓜ 재실행 → 78(해시 불일치) ⓡ 일치 결과 green 2/3 · 직전 없음 → 0(회귀 기준 없음 · 첫 결과). 케이스 11 → 18(`:178` 문구). 실행 게이트 = `harness-eval-selftest`(로컬 · `all` · CI `harness-judge-selftest` `ci.yml:695`).
- 산문 정리: `gates/README.md:47` 「면제 시 과제 건수만」 → 「면제 = 현재 설정 해시와 일치하는 전수 결과가 `results/` 에 있고 회귀가 없다는 선언 · 없으면 78 · 회귀 1」 · `:62-71` 「명시 면제도 병합 진입 조건 충족」 문장에 「(해시 일치 결과 전제)」 · `run.sh:510-513` 주석 동기 · `harness-eval.sh:8-20` 머리말 교체.
- 병합 조건 = `harness-eval-selftest` 18/18 ∧ CI `harness-eval` 0(해시 일치).

### 4.4 CI 필터 (단위 E0-4)
- `ci.yml:119-128` 에 `- '.claude/settings.json'` · `- '.claude/rules/**'` · `- 'gates/**'` · `- 'eval/harness/**'` 추가(4줄 · `gates/**` 는 `contracts` `:72` · `dev-package` `:113` 필터에도 있음 → gate-selftest · planning-gates 와 함께 깨어남 · `eval/harness/**` 는 러너·셀프테스트·results 만 바꾼 PR(T12 결과 커밋 PR 포함)도 `harness-runner-selftest` · 면제 게이트를 깨운다 · 추가 비용 = 면제 게이트 1회). `:116-118` 주석 「4경로」 → 「config-paths.txt 정본 ⊆ 이 필터」. `:641-650` 잘못 놓인 주석(C3 지적 · `repo-hygiene` 잡 구간)을 `:681` 잡 위로 옮기고 내용 교체(면제 = 해시 일치 결과 요구 · 실행 모드 전환은 여전히 Q10 별건). 이 주석은 E0 소유로 이관 · intent C3(`:348` 「ci.yml 낡은 주석」 · PR 3)는 `gates/README.md:245` 표만(intent 「확인」 절에 같은 줄 기록).
- `gates/tools/ci-filter-check.py:39-49` `WANT_PATTERNS` → `read_config_paths()`(정본) ∪ `FILTER_ONLY = {".codex/**", "scripts/harness/**", "scripts/agent-bridge.py"}`(해시 밖 · 필터 안 — `eval/harness/**` 는 8라운드 판정 #5 ⓐ 로 정본에 있음) · `:50-60` `MUST_MATCH` 에 `.claude/settings.json` · `.claude/rules/colab-rules.md` · `gates/run.sh` · `eval/harness/run.sh` 추가 · 새 ㈖ 「`config-paths.txt` 모든 패턴 ∈ 필터」 · `:200-205` green 줄에 정본 경로.
- 강제 기제: `ci-filter-check.py`(`harness-eval-selftest.sh:159-169` 가 호출 · 판정 red 1 · PyYAML 부재 78) · Claude/Codex 공통 · 실제 `dorny/paths-filter` 평가는 `[미상]` 유지(`:21-23`).
- 시험: `scripts/tests/test_ci_eval_policy.py:45-51` 목록에 4경로 추가 · `:63-80` 변이에 `filter-drop-settings`(필터에서 `.claude/settings.json` 제거 → 1) · `paths-file-extra`(`config-paths.txt` 에 패턴 추가하고 필터 미갱신 → 1 · 임시 정본 파일 seam `COLAB_EVAL_CONFIG_PATHS`) 추가. `test_ci_eval_policy.py` 는 현재 `run.sh` 어느 목록에도 없고 `agent-bridge.yml:64` discover 로만 돈다 → `gates/tools/harness-eval-selftest.sh:159-169`(이미 PyYAML 의존 · CI `harness-judge-selftest` 에서 PyYAML 설치 뒤 실행) 안에 `python3 -m unittest scripts/tests/test_ci_eval_policy.py` 1줄 추가(green-by-skip 방지 · 시험 수 기준값 기록) · `run.sh:357` harness-contract-selftest 에는 넣지 않는다(PyYAML 없는 환경에서 78 로 바뀌는 것을 피함).
- 병합 조건 = `harness-eval-selftest`(ci-filter-check + 변이 2건 red) · 지우는 산문 = ci.yml:641-650 10줄 → 4줄.

### 4.5 신선도 경고 (단위 E0-5 · N = 30일)
- `scripts/harness/check.py`: `check_eval_freshness(root, now=None, max_days=30) -> tuple[str|None, str|None]`(warning, readiness) — `eval/harness/results/*/` 디렉터리 이름 `%Y%m%d-%H%M%S` 파싱 · 최신 id · `now − id > max_days` → warning 문자열 · results 디렉터리 부재/파싱 가능한 id 0 → readiness(78 · 대상을 못 읽음 · `:100-106` 경로 합류). `main()` `:111-120` green 줄에 `harness-eval newest <id> (<n>d)` · warning 은 stdout `warning:` 접두 1줄 · exit 불변.
- N 근거: 러너 모델·CLI 는 호출 환경 기본값(README:108)이라 저장소 diff 없이 바뀐다 → 시간 기준 재실측 신호가 필요. 30일 = 경고 준수 시 상한 ≈32 USD/월(1회) · CLI 부 버전 배포 주기 이내 · 90일(`ci.yml` artifact retention)은 두 세대를 건너뛴다. 값은 `.agents/harness.yaml` 에 두지 않는다(`harness.yaml` 은 계약 · 신선도는 운영 파라미터 · 상수 1곳 `check.py`).
- 강제 기제: 경고(exit 0) — 「산문 아님 · 신호」 · Claude/Codex 공통(`harness-contract` gate `run.sh:353-355` · agent-bridge.yml:62 · `all`).
- 시험: `test_harness_eval_gate.py` ⑸ `now` 주입 — 29일 → warning None · 31일 → warning 문자열에 id·일수 · results 부재 → readiness · 이름 형식 아닌 디렉터리(`activation-gate.json` 류 파일 · `codex-20260908-audit`)는 무시.
- 병합 조건 = `harness-contract-selftest` ⑸ green · 경고는 병합 조건 아님(Ted 결정 밖 · 신호) · 지우는 산문 = 없음.

### 4.6 실측 1회 · 실패 4건 분류 (단위 E0-6 · 「산문 · 맥락만」 = 기록 · 판정은 4.3 회귀 규칙)
- 시점: E0 코드 커밋 ①–⑤ 뒤(`gates/**` · `.claude/**` 가 해시 안이라 「PR 1 상태」가 아니라 **E0 최종 코드 상태**에서 돌아야 머지 커밋 해시와 일치). 이후 코드 리뷰로 해시 안 파일이 바뀌면 재실행(≈32 USD) — 위험 절.
- 명령(worktree 루트 · 일반 터미널): `COLAB_EVAL_TIMEOUT=93 COLAB_EVAL_BUDGET=2.01 bash eval/harness/run.sh`(README:14 · 상한 근거 `:59-67`) → `results/<run>/` 6종 중 4종 커밋(커밋 ⑥) · 요약줄 · `config-hash.json.hash` 를 intent 「확인」에 기록.
- 실행 주체: 레인 우선 — 레인이 `claude --version` 확인 후 `COLAB_EVAL_ONLY=H01` 스모크(≈1.7 USD) 1회 → 정상이면 전수. 레인 Bash 안 중첩 `claude -p` 가 거부되면 레인은 「코드 최종 SHA · 실행 명령」을 보고하고 정지 → T12(Ted) 실행 · 같은 task id 로 레인 재개(task 는 checkout 결속 · `agent_id` 없음 · `lifecycle_contract.py:377` 대조 없음).
- 분류(expect 판독 · 2026-09-26 · 확정은 재실측 뒤):
  - 공통 사실: 4건 모두 모델이 「준비 실패 = exit 1」로 적었다(H14 `out.1:19` · `out.2:30` 「red(준비) · exit 1」 · H18 `out.1:24` · `out.2:19` · H15 `out.1:16` · `out.2:22` · H16 `out.1:25` · `out.2:24`). expect 는 78 을 요구(H14 `expect.sh:15` · H18 `:15` · H15 `:15` 둘째 갈래 · H16 `:16` 「실패|red|78」). 과제 프롬프트 4종은 「red(준비)」·「세 상태」만 말하고 종료코드 규약을 적지 않는다(`H14/task.md:7-8` · `H18/task.md:6-13`). 2026-09-12 당시 적재 문서 `CLAUDE.md`(`cbaceec0`)에 「78」·「준비 실패」 0건(grep · 〈78〉 원장 번호만) → 모델은 78 규약을 볼 수 없었다. 현재는 `AGENTS.md:45` 「성공 0 · 판정 실패 1 · 준비 실패 78」이 `CLAUDE.md @AGENTS.md` 로 매 호출 적재(2026-09-15 `e125dd55` 이후). Codex 보존 응답은 78 을 쓴다(`scripts/tests/test_h15_h16_judge_compat.py:12,14`).
  - H14-silent-skip · H18-three-states: **하네스(문안) 결함** — 기대(78)는 저장소 규약과 일치 · 실패 원인은 규약이 모델 입력에 없었던 것 · `AGENTS.md:45` 로 닫힘 후보 → 재실측 green 이면 「하네스 결함 · #130 으로 해소」 확정 · 여전히 red 면 「과제 기대문 결함(픽스처가 게이트가 아닌 단독 스크립트라 규약 적용 근거가 프롬프트에 없음) → task.md 에 규약 1줄」로 재분류.
  - H15-zero-targets: **겹침** — 위 하네스 결함 + expect 결함: `expect.sh:17` 주석 「오류 출력과 exit 78 도 실패 표현」과 달리 `:15` 첫 갈래는 `(0건|대상).*(red|실패)` 문자열을 요구해 `::error::검사 대상 0건 … · exit 1` 을 거절 · 러너 자신은 대상 0건을 exit 1 로 낸다(`run.sh:71-73` · README:32) → 저장소 안에서 「0건 = 1 인가 78 인가」가 갈린다. 판정 항목: expect 갈래에 `(::error::|오류).*exit *1` 수용 여부 = Ted 판정(T17) · 기대 완화는 「판정 뒤에만」(README:280).
  - H16-lenient-default: **겹침** — `expect.sh:16` `상태3 무언:.*(실패|red|78)` 가 `::error:: … exit 1` 을 실패 표현으로 인정하지 않음(H15 주석과 비대칭 · `test_h15_h16_judge_compat.py:84-94` 음성 목록에도 `exit 1` 사례 없음) + 78 규약 부재.
  - 기록: intent 「확인」 절에 5줄(공통 사실 1 · 과제별 4) + 재실측 뒤 확정 1줄 + 「`ci.yml:641-650` 주석 E0 소유 이관 · C3 는 `gates/README.md:245` 만」 1줄. expect/task 수정은 E0 범위 밖(측정 도구 변경은 판정 뒤 별건 · T17).
- 강제 기제: 없음(기록 · 「산문 · 맥락만」) · 시험 없음 · 병합 조건 = 기록 존재 + 재실측 결과 커밋 + V-E6 해시 일치 · 지우는 산문 = 없음.

### 4.7 문서 · 산문 정리 (단위 E0-7 · 「산문 · 맥락만」)
- `eval/harness/README.md:118-142` 「결과」 → 여섯 종 · 추적 넷(`config-hash.json` 행 추가 · 「다섯 중 셋」 0건) · 새 절 「설정 해시 · 면제 조건」(정본 파일 · 계산 규칙 · 면제 판정 3값 · 회귀 규칙 · 회차 무효화 규칙 · 30일 경고) · `:156` 「승격」 행에 「면제 조건은 이미 해시 결합」.
- `gates/README.md:47-48` · `:62-71` · `:293`(케이스 수) 갱신 · `:245` CI 표 행은 C3(PR 3) 몫 유지(파일 겹침 회피 · 이 행의 「시크릿」 오류는 R3-15 기록 있음). `ci.yml:641-650` 주석은 E0 소유로 이관(4.4) · C3 는 `gates/README.md:245` 표만.
- `docs/development/dual-agent.md:192` 「기존 Claude 평가 러너 · 그대로 유지」 → 「+ 설정 해시 결합(정본 `eval/harness/README.md`)」 1구.
- 지우는 산문: `harness-eval.sh:8-10` 「승격 전 · 면제 모드로 돈다 · 별건」 3줄 → 「면제 = 해시 일치 결과 선언」 1줄 + 포인터 · `ci.yml:641-650` 10줄 → 4줄.
- 강제 기제: 없음(문서) · 병합 조건 = V-E8 grep 0건 · `config-hash` ≥3.

## 5. 시험 결정 (TDD 순서)
1. `scripts/tests/test_harness_eval_gate.py` 작성(⑴–⑸ + verify 규칙 단위: 후보 선택 · 직전 선택 · 회귀 계산 · 준비>0 제외 · 선택 실행 제외 · symlink) → `bash gates/run.sh harness-contract-selftest` RED(모듈 부재 ImportError) 기록.
2. `harness-eval-selftest.sh` ⓛ–ⓡ 추가 → RED(면제 분기가 verify 를 부르지 않아 ⓛ·ⓝ·ⓞ·ⓟ·ⓠ 통과=결함) 기록.
3. `run-selftest.sh` ⓛ·ⓜ 추가 → RED(config-hash.json 부재).
4. `test_ci_eval_policy.py` 변이 2건 + `harness-eval-selftest.sh:159-169` 호출 1줄 → RED.
5. 구현 ①–⑤ → 전부 GREEN · 시험 수 증가분 커밋별 기록(harness-contract-selftest 현재 수를 커밋 ① 뒤 기준값으로).
6. 실측(커밋 ⑥) → `COLAB_HARNESS_EVAL_EXEMPT=1 bash gates/run.sh harness-eval` 로컬 → 0 + 일치 run id · 두 해시 동일 출력(자기 적용).
- seam: `REPO_ROOT`(`harness-eval.sh:29`) · `COLAB_EVAL_RESULTS_ROOT`(runner:33 · 게이트도 읽음) · `COLAB_EVAL_TASKS_DIR` · `COLAB_EVAL_CONFIG_PATHS`(ci-filter-check 시험용 · 게이트 판정에는 안 씀 · 러너·게이트는 정본 경로 고정 — `harness-eval.sh:33-34` 「러너 경로 고정」 원칙 동일). 제품 hook 에 시험 seam 없음(Ted Q11 원칙).

## 6. 위험 · 롤백
- 비용·순서: 해시 집합 = Q-A ⓐ 확정(재개봉 없음 · 우려 #1 은 비용 공개만) → E0 · S-red · PR 2 · PR 3 · PR 4 각 1회 ≈32 USD · 합 ≈160 USD(+ S-dep 1회 = ≈192 USD · 총괄 §6 Q1) · 6라운드 추정 ≈64 USD 를 넘는다. 순서 대안(S-red → E0 · EXEMPT 창 · 1회 절감)은 우려 #6 · Ted.
- 머지 커밋 해시: CI 는 머지 커밋 트리에서 계산 → base(develop)가 해시 안 파일을 바꾸면 PR 결과 해시와 불일치 → 78 → Update branch + 재실측. T1 strict(최신 develop 반영 필수)와 방향 일치 · 비용은 재실측(우려 #7). 회차 뒤 이 PR 이 해시 집합 파일을 push 하면 같은 78 → 회차는 병합 직전 head 에서 1회.
- 첫 회귀 기준 = `20260912-211809`(green 16): 재실측에서 16 중 1건이라도 red 면 E0 게이트가 1 → 원인 조사 없이 병합 불가(의도).
- 롤백 단위: 커밋 ③(게이트 verify)만 되돌리면 면제 = 옛 동작 · 나머지 커밋(기록 · 필터 · 경고)은 무해.
- 중첩 `claude -p` 불가 시 레인 정지 → T12.
- 결과 디렉터리 이름 충돌 없음(초 단위 · README:124).

## 7. 레인 지시 (PR E0 · lane-worker 1개)
- 스폰: `Agent(subagent_type: "lane-worker", isolation: "worktree")` 명시(Workflow `agent()` 는 부모 worktree 에서 돈 관측 1회) · 기준 = PR 1 병합 뒤 `develop`(T1 · T11 뒤) · 첫 행동 `git merge --ff-only develop` · `git rev-parse --show-toplevel` 이 지시문의 부모 checkout 과 같으면 구현 전 정지.
- begin: `python3 scripts/agent-bridge.py lifecycle begin --role lane-worker --gate harness-contract-selftest --gate harness-eval-selftest --gate harness-contract --gate intent-ref --gate exec-bit --gate harness-eval --scope 'eval/harness/config_hash.py' --scope 'eval/harness/config-paths.txt' --scope 'eval/harness/run.sh' --scope 'eval/harness/README.md' --scope 'eval/harness/tests/run-selftest.sh' --scope 'eval/harness/results/**' --scope 'gates/tools/harness-eval.sh' --scope 'gates/tools/harness-eval-selftest.sh' --scope 'gates/tools/ci-filter-check.py' --scope 'gates/run.sh' --scope 'gates/README.md' --scope 'scripts/harness/check.py' --scope 'scripts/tests/test_harness_eval_gate.py' --scope 'scripts/tests/test_ci_eval_policy.py' --scope '.github/workflows/ci.yml' --scope 'docs/development/dual-agent.md' --scope 'dev-package/intent/2026-09-25-harness-improvement.md'`(`dev-package/reports/**` · `lifecycle-evidence.md` 기본 허용).
- 게이트 실행: `COLAB_HARNESS_EVAL_EXEMPT=1 COLAB_TASK_ID=<id> bash gates/run.sh task` 1회 · **커밋 ⑥(결과) 뒤에** — 그 전엔 `harness-eval` 이 78 이라 인계 불가(의도된 자기 적용). 호스트 단독 · 병렬 lane 없음. 커밋 ⑥ 뒤 해시 집합 파일 변경 금지(리뷰 수정이 필요하면 재실측 뒤 다시 커밋 ⑥).
- 커밋 단위(각 `Intent-Ref:` 마지막 문단 · Co-Authored-By/Claude-Session): ① `config_hash.py` · `config-paths.txt` · `test_harness_eval_gate.py` · `run.sh:357` 등록 ② `eval/harness/run.sh` 기록 · `run-selftest.sh` ⓛⓜ · README 「결과」 ③ `harness-eval.sh` verify · `harness-eval-selftest.sh` ⓛ–ⓡ · `gates/README.md` · `run.sh:510-513` 주석 ④ `ci.yml` 필터+주석 · `ci-filter-check.py` · `test_ci_eval_policy.py` · `harness-eval-selftest.sh:159-169` 호출 ⑤ `check.py` 신선도 · 시험 ⑸ · `dual-agent.md:192` ⑥ `results/<run>/` + intent 「확인」 6줄(분류 5 + 주석 소유 1) — 되돌림 단위 = ③.
- 인계: `lifecycle handoff --task <id> --mode complete --summary 'red→green 계수 · V 표 · run id · hash'` · `COLAB_HANDOFF` 줄 + `WORKTREE= BRANCH=` 최종 메시지. push · PR 게시(T16) · 병합(T13) = Ted.

## 8. 검증표
| V | 명령(worktree 루트) | 기대 | 완료 기준 |
|---|---|---|---|
| V-E1·E2 | `bash eval/harness/tests/run-selftest.sh` · `bash gates/run.sh harness-contract-selftest` | 17/17 · unittest green · 시험 수 증가분 기록 | 4.1 · 4.2 |
| V-E3 | `bash gates/run.sh harness-eval-selftest` · 수동: 커밋 ⑥ 전 `COLAB_HARNESS_EVAL_EXEMPT=1 bash gates/run.sh harness-eval` → 78 + `missing=eval-result:` · 커밋 ⑥ 뒤 같은 명령 → 0 + run id + 두 해시 동일 | 18/18 · 78→0 전이 로그 | 4.3 |
| V-E4 | `python3 gates/tools/ci-filter-check.py` · `python3 -m unittest scripts/tests/test_ci_eval_policy.py` | green · 패턴 수 = 기존 + 4 · 변이 2건 red | 4.4 |
| V-E5 | `bash gates/run.sh harness-contract` (결과 신선) · 시험 ⑸ | green 줄에 `harness-eval newest <run>` · warning 없음 | 4.5 |
| V-E6 | `COLAB_EVAL_TIMEOUT=93 COLAB_EVAL_BUDGET=2.01 bash eval/harness/run.sh` · `python3 eval/harness/config_hash.py compute --root .` | 과제 20 · 실행 40 · 준비 0 · `results/<run>/config-hash.json.hash` == compute 출력 | 4.6 |
| V-E7 | `git diff -U0 -- dev-package/intent/2026-09-25-harness-improvement.md` | 「확인」 절 줄 추가만 · 4건 분류 + 재실측 결과 + 주석 소유 1줄 | 4.6 |
| V-E8 | `grep -n '다섯 중 셋\|건수만' eval/harness/README.md gates/README.md gates/tools/harness-eval.sh` · `grep -c 'config-hash' eval/harness/README.md` | 0건 · ≥3 | 4.7 |
| V-E9 | `git diff --stat develop -- scripts/agent-bridge.py .codex scripts/codex-harness-eval.py` · `python3 scripts/agent-bridge.py check` | diff 0 · green | Codex 영향 없음 |
| V-E10 | selftest ⓛ(78) · ⓝ(1) · ⓜ(0) | 세 값 | 0/1/78 유지 |
| 공통 | `bash -n` 2 .sh · `bash gates/run.sh exec-bit` · `bash gates/run.sh intent-ref` | 0 | |

## 9. PR 본문 계획 (`scripts/harness/pr_contract.py` 형식)
- 파일: `~/.claude/pr-bodies/PR-BODY-harness-improvement-E0.md` · 검증 `python3 scripts/harness/pr_contract.py <본문> --head <sha> --mode draft` → 0 · 게시 = T16(Ted).
- 첫 줄: 「하네스 개선 E0 — eval 결과를 설정 해시에 결합해 지침 변경 PR 이 실측 없이 병합되지 않게 한다(실측 1회 · 실패 4건 분류)」.
- `Plan-Ref: dev-package/prd/specs/S-HARNESS-E0-EVAL-GATE-20260926.md`(총괄 `S-HARNESS-IMPROVEMENT-PLAN-20260926.md` §2 E0) · `Head-SHA` · `검증 상태: 미검증` → CI `harness-eval` 잡 green(면제 + 해시 일치) 뒤 「검증됨」.
- 목적/범위/계획/결정/검증/남은 제약: V-E1–E10 표 · 결정 = 해시 정본 위치 · fail-closed 위치 ⓐ · N=30 · 회귀 규칙 · 회차 무효화 규칙(새 ADR 없음 — 게이트 입력 규칙 · ADR-0004 3상태 안) · 남은 제약 = 실행 모드 전환 Q10 별건 · 머지 커밋 해시 재실측 · Codex 러너 결과는 대조 밖 · 4건 분류 확정은 재실측 결과 · 우려 #4·#5 Ted 판정.
- 게시 뒤: Ted 병합(T13) → S-red 착수 · T7 메모리 갱신 없음.

## T-항목 (Ted · 번호 = 총괄 Ted 행동표)
| T | 행동 | 명령/UI | 기록 자리 |
|---|---|---|---|
| T1(기결정) | develop ruleset `ci-required` 필수 · strict · bypass 0 — E0 fail-closed 가 병합 차단이 되는 전제 | GitHub → Rules → develop · `gh api repos/CognileapAI/colab-v2/rulesets` JSON 내보내기 | intent 「확인」 + `docs/development/github-ruleset.json`(PR 3 C5) |
| T12 | 실측 승인(≈32 USD) · 레인이 중첩 `claude -p` 를 못 돌릴 때 실측 실행 · 결과 커밋 지시 | 일반 터미널 · E0 worktree 루트 · `COLAB_EVAL_TIMEOUT=93 COLAB_EVAL_BUDGET=2.01 bash eval/harness/run.sh` → `git add eval/harness/results/<run>` · 커밋(트레일러 포함) 또는 레인 재개 | intent 「확인」: run id · 요약줄 · hash · USD |
| T16 | PR 게시 — 메인 세션 초안(`~/.claude/pr-bodies/PR-BODY-harness-improvement-E0.md`) · Ted `gh pr create` | Ted 터미널 | PR 번호 → intent 「확인」 |
| T17 | 분류 판정 — H15·H16 expect 갈래(`::error:: … exit 1` 수용) · H14·H18 재실측 red 시 task.md 규약 1줄 — 측정 도구 변경 별건 PR go/no-go | 대화 판정 | intent 「판정 기록」 |

## 우려 항목
| # | 항목 | ⓐ | ⓑ | 권고 | 판정 |
|---|---|---|---|---|---|
| 1 | 해시 집합 | Q-A ⓐ 확정(`.claude/**` · `.agents/**` · `gates/**` · hook 스크립트) — 재질문 없음 · 이 행은 비용 공개만: E0 · S-red · PR 2 · 3 · 4 각 1회 ≈32 USD · 합 ≈160 USD(+ S-dep 1회 = ≈192 USD) | — | 확정 유지 | 확정 |
| 2 | 회귀 규칙(green 집합 축소 = 1) | 포함 | 「일치 결과 존재」만 | ⓐ(playbook 「pass rate 로 gate」) | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |
| 3 | 실측 주체 | 레인(중첩 `claude -p`) | Ted T12 | 레인 먼저 · 거부 시 T12 | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |
| 4 | `AGENTS.md` · `CLAUDE.md` 추가(모델 입력 정본 · Ted 목록 밖 · `.claude/rules` 는 이미 목록 안) | 추가 | Ted 목록만 | ⓐ(매 호출 적재 파일이 해시 밖이면 지침 변경이 회차를 안 부른다) | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |
| 5 | `eval/harness/**`(results 제외) 해시 포함 — 문서 간 충돌(총괄 gate-1 차단급 3 vs 이 spec 4.1) | 포함(해시 = `harness` 필터 집합 · expect.sh/러너 수정으로 만든 green 도 재실측 강제 · 정본 1집합) | 제외(측정 도구 · 자기 참조 순환 · 필터에만 · 4.1 현행) | ⓐ(엄격 · 7라운드 목록에 없는 추가이므로 Ted 판정 · ⓐ 면 4.1 정본에 `eval/harness/**` + `:(exclude)eval/harness/results/**` · `FILTER_ONLY` 에서 제거) | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |
| 6 | S-red 순서 · 회차 — 문서 간 충돌(총괄 gate-1 차단급 1 vs 7라운드 `:609`) | E0 → S-red(확정 순서 · S-red head 회차 1회 ≈32 USD · S-3 hook 을 E0 게이트 아래에서 검증) | S-red → E0(EXEMPT 창 · 회차 불요 · E0 head 회차가 S-red 를 덮음 · 1회 절감) | ⓐ(확정 순서 유지 · 절감은 Ted 재판정 시만) | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |
| 7 | CI 해시 = 머지 커밋 트리 기준(base 가 집합을 바꾸면 78 → Update branch + 재실측) | 머지 트리(T1 strict 와 같은 방향) | PR head 트리(base 변경 미반영) | ⓐ | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |
| 8 | H15·H16 expect 갈래 교정(`::error:: … exit 1` 수용)은 측정 도구 변경이라 별건 PR(T17) | E0 밖(별건) | E0 안 | ⓐ(기대 완화는 판정 뒤에만 · README:280) | 확정(8라운드 · Ted 「권고대로」 · 권고 = 결정) |

## 범위 밖
- 실행 모드(`COLAB_HARNESS_EVAL=1`) CI 전환(Q10 3회 연속) · Codex 러너(`scripts/codex-harness-eval.py`) 해시 기록 · expect/task 수정(T17 뒤) · 모델 지정(`--model`) · E1(PR 4 head 회차 대조표) · `gates/README.md:245` CI 표(PR 3 C3) · `.agents/ci-producers.json` · `verify_evidence.py` · `harness.yaml`(diff 0).
