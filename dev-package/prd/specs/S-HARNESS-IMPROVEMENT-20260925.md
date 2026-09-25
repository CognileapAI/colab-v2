# Spec: 하네스 개선 — phase 1(PR 1 · 그룹 A) 막는 장치 바로잡기 · phase 2/3 stub
출처 intent: `dev-package/intent/2026-09-25-harness-improvement.md` (승인 그룹 A 2026-09-25 · Ted 원문 "전부 권고대로" · 2026-09-26 Fable 재판정·그룹 A 보강 줄 반영 · Fable ⓒ′ 기각).
근거: 저장소 밖 `~/.claude/reports/harness-state-20260925/`(fable-judges/judge-g1.md · cross.md · guard_probe.py). 줄 번호 기준 = develop `67a03a05` = 브랜치 `claude/harness-improvement`(코드 동일 · 이 spec 작성 시 전 인용 재열람).
spec 경로: `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-20260925.md` (PR 1·2·3 의 Plan-Ref 공통).
모든 커밋 메시지 끝에 `Intent-Ref: dev-package/intent/2026-09-25-harness-improvement.md` 트레일러(`colab-v2-work/SKILL.md:130` · 게이트 `intent-ref` 판정 대상 경로 `scripts/**`·`gates/**`·`.agents/**` 포함).

## 0. phase 개요 (엄격 순차)
| phase | PR | 그룹 | 상태 |
|---|---|---|---|
| 1 | PR 1 | A1–A6 | 이 문서 §1–§9 상세 |
| 2 | PR 2 | B(B1–B8) → L(L1–L8) · lane 1개 · `lifecycle_contract.py`·`test_task_runtime.py` 공유 | stub — 그룹 B·L 판정 뒤 상세화 |
| 3 | PR 3 | C(C1–C12) · `README.md`·hook 머리말·ruleset JSON | stub — 그룹 C 판정 뒤 상세화 |
- 다음 phase 는 앞 PR 병합 뒤 develop 기준으로 착수. PR 사이 공유 파일: `gates/run.sh` · `README.md` · `lifecycle_contract.py` · SKILL 문서.
- 그룹 T(Ted) 는 PR 과 독립(T1 적용 PR 2 병합 뒤 · T5 PR 3 병합 뒤).

## 1. 문제 진술 (phase 1)
- `git-guard.sh:167` 비인용 `set -- $seg` → 공백 경로 `git -C "<repo>" …` 에서 `-C` 가 첫 조각만 소비(`:193`), 규칙 ⑴–⑸ 전부 통과. 브랜치 판정 근거는 payload `cwd` 하나(`:143`). `gh -R` · `gh api PUT` · `-fu` · `push origin HEAD` · 보호 브랜치 위 `pull --no-ff/--no-rebase` 미검출. heredoc·인용 인자 안 문구 오탐(`:106` · `:149`).
- `test-file-guard.sh:32` env 부재 exit 0 → Claude lane 편집 시점 차단 없음. 문서 3곳(`design-review/SKILL.md:101`·`:106` · `dual-agent.md:59-60`)은 차단을 기술.
- `gates/run.sh:9` `$1` 만 읽음 · `$#` 검사 없음 · `all` 은 `$2 == -j` 정확 일치만(`:795`) · 비정수 `-j` 는 `jobs_n=1`(`:796`) · 알 수 없는 gate 는 host mutex 획득(`:163-170`) 뒤 exit 2(`:975-977`) · 인자 없음 exit 2(`:971-973`).
- 머리말 「exit 1 은 통과다 · 판정 못 하면 통과」(`git-guard.sh:71-72` · `test-file-guard.sh:27`) ↔ 실제 envelope 이상·python3 부재 exit 2(`:82-83` · `:38-39`) · 도달 불가 `|| exit 0`(`git-guard.sh:90` · `test-file-guard.sh:42`) · 거부 문구 `:271` 「main|master」(집합은 develop·product 포함 `:267`).

## 2. 원한 결과 (V-id) — PR 요약 「원한 결과 ↔ 실제 ↔ 근거」 행 이름
- V1 공백 경로 `-C "<…>"`·`-C '<…>'` 로 규칙 ⑴–⑸·product 규칙 각각 rc=2 · 허용형 rc=0 — 확인: `scripts/tests/test_git_guard.py`(agent-bridge gate) · intent A1 ⑴.
- V2 기능 브랜치 cwd 에서 `-C <develop checkout>` 또는 `cd <develop checkout> &&` 뒤 non-ff merge · subagent refspec 없는 push → rc=2 — A1 ⑵.
- V3 heredoc 본문·인용 인자 안 git merge · gh 병합 · 강제 push 문구 → rc=0 — A1 ⑶.
- V4 `gh -R o/r pr merge` · `gh api -X PUT …/pulls/N/merge` · develop 대상 `push -fu` · develop 위 subagent `push origin HEAD` · develop 위 `pull --no-ff`/`--no-rebase`/`--rebase=false`/`--ff=false` → rc=2 · `gh api …/merge`(GET) · `pull --ff-only` · 플래그 없는 `git pull` → rc=0 — A1 ⑷.
- V5 짝 없는 인용 등 파싱 실패 입력의 rc 가 현행 규칙 결과와 같음 · parser 결함 주입(fault-injection) 시 폴백 — A1 ⑸.
- V6 기존 시험(`test_agent_bridge.py:463-507` · `test_harness_lifecycle_contract.py:319-346`) green · 오케스트레이터 재현 명령(guard_probe.py 9종 + pull 2종)을 worktree 스크립트로 재실행해 우회형 전부 rc=2 — A1 ⑹.
- V7 `README.md:73` git-guard 행 · 머리말 허용 목록(`git-guard.sh:22-24`)이 편입 형태와 일치 — A1 ⑺.
- V8 `SKILL.md:101` 두 문장 분리 · `:101`·`:106`·`dual-agent.md:60` 이 Claude lane 실제 동작(env 없음 → 편집 시점 차단 없음 · `--scope` 인계 시점 차단) 기술 · `grep -n 'COLAB_FIX_LANE=1' .agents/skills/design-review/SKILL.md` 가 Codex/env 조건과 함께만 나옴 — A2 ⓒ.
- V9 `README.md` hook 절 · test-file-guard 머리말에 대상 도구(Edit/Write) · 비대상 경로(Bash 쓰기) · 사후 검사 수단(`begin --scope` handoff/H7) 명시 · harness-contract green · 코드 변경 0 — A3.
- V10 `run.sh a b` · `run.sh all -j4` · `run.sh all -j 4 x` · `run.sh all -j abc` · `run.sh task x` → 78 + stderr 에 버린/인식 못 한 토큰 — A4 ⑴.
- V11 `run.sh no-such-gate` · 인자 없음 → 78 · host mutex 획득 흔적 0(`${TMPDIR}/colab-v2-gate-host-mutex/` 미생성 · `::gate-waiting::` 0줄) · `:42` gate-start 미실행 — A4 ⑵.
- V12 단독 gate · `all -j N` · `task` 기존 동작 무변경 — A4 ⑶.
- V13 `grep -n 'exit 1 은 통과' scripts/harness/hooks/git-guard.sh scripts/harness/hooks/test-file-guard.sh` 0건 · 도달 불가 줄 삭제 · `test_harness_lifecycle_contract.py:319-327`(`{broken`·`{}` → 2 · Read → 0) green — A5.
- V14 (A6) decision-number-guard 기준 `origin/develop` · 기준 부재 → exit 2 시험 red→green · `grep -n 'origin/main' scripts/harness/hooks/decision-number-guard.sh` 0건 — C5 이관분.

## 3. 해법 개요
- 코드: git-guard 명령 해석부를 python 모듈(quote-aware tokenizer · 대상 checkout 해석)로 교체하고 bash 규칙 엔진은 유지 · `run.sh` 인자 검사 1블록 · 머리말 2건.
- 문서: SKILL·dual-agent·README·gates/README 문장 교정.
- 훅 정의(`.claude/settings.json` · `.codex/hooks.json`) 무변경 → `/hooks` 재신뢰 0. envelope 계약(`git-guard.sh:81-83` · `lifecycle_contract.py:503-523` validate-input) 무변경.

## 4. 구현 결정

### 4.1 A1 git-guard — tokenizer · 대상 checkout · argv 형태 편입
파일·현재 앵커(재열람 확인): `scripts/harness/hooks/git-guard.sh` — 머리말 `:11-24`(열거·허용 목록) · `:71-72`(exit 1 문장) · `:81-83`(envelope · 불변) · `:88-90`(도달 불가 주석+줄) · `:92-114`(read_fields · 2번째 python 호출 · `:106` 개행→` ; `) · `:134-137`(reseed ⑹ · 불변) · `:143-145`(payload cwd 단일 BRANCH) · `:149`(sed 분리) · `:151-157`(is_main_ref) · `:159-162`(deny) · `:164-178`(`set -- $seg` · 앞머리 정리) · `:181-186`(gh) · `:190-200`(git 전역 옵션) · `:203-245`(push) · `:207`(force 정확 토큰) · `:246-260`(merge) · `:261-273`(branch · `:271` 문구) · `:275`(`done <<< "$SEGS"`).

**결정 1 — 파서 위치 = 새 모듈 `scripts/harness/hooks/git_guard_parse.py`, 호출 자리 = 현행 read_fields(`:92-108`) 대체.**
- python 호출 수 2 유지(`:83` validate-input + 파서) → 지연 증가 0 (Fable 「같은 호출에 합치면 지연 0」의 목적 충족).
- validate-input 에 합치지 않는 이유: ⑴ `--field command|file_path` 로 4 hook 이 공유하는 envelope 계약이고 제약이 「무변경」 ⑵ `:83 … || exit 2` 경로라 파서 예외가 곧 차단이 됨(폴백 규칙과 충돌) ⑶ `lifecycle_contract.py` 는 PR 2(B·L) 공유 파일 — 파일 면 분리.
- 등록 확인(인용): `.agents/harness.yaml` `sources.hook_names` 는 `.sh` 11개 열거 · `scripts/harness/config.py:174-196` 는 `hook_names` 항목만 원본·adapter·wiring 대조 · `scripts/tests/test_harness_source_layout.py:58-73` 는 같은 11개 이름 고정 + `lifecycle_contract.py` 존재만 단언 → `.py` 보조 모듈은 등록·adapter 불요. 실행 비트 미부여(`python3 <경로>` 로 호출 · `lifecycle_contract.py` 와 같은 꼴). `exec-bit` 게이트 규칙과의 충돌 여부는 lane 이 1회 실행으로 확인.
- 파서 경로 = `"$(dirname "${BASH_SOURCE[0]}")/git_guard_parse.py"`. 시험 seam: `COLAB_GIT_GUARD_PARSER` env 가 있으면 그 경로를 쓴다(폴백 = 현행 규칙이므로 이 seam 으로 현행보다 약해지지 않음 · 머리말에 명시).

**결정 2 — 파서 입출력 · 폴백.**
- 입력: stdin = validate-input 이 낸 payload JSON(`:83` 결과). 출력 stdout 1행째 `parsed` 또는 `fallback <사유>`, 이어 세그먼트마다 1행 `<branch>\t<dir>\t<argv…(\x1f 구분)>`. `tool_name`·`cwd`·`agent_id` 는 현행처럼 앞 3행으로 먼저 낸다.
- bash: 1행째가 `parsed` 가 아니거나 파서 종료 비0 · 출력 없음 · 파일 없음 → **폴백** = 현행 `:106`+`:149` 분리 · `:167` `set -- $seg`(앞에 `set -f` 추가 · glob 확장 차단) · BRANCH = payload cwd(`:143`). 폴백 사유로 exit 2 를 내지 않는다.
- 규칙 엔진(`:181-274` case) 은 bash 에 그대로 두고 레코드(branch · argv)를 소비한다. parsed/fallback 양쪽이 같은 루프를 탄다.

**결정 3 — tokenizer 규칙(python · 표준 라이브러리만 · shlex.split 미사용).**
- 상태기계: 홑따옴표 · 겹따옴표 · 백슬래시 · `$(`…`)` · 백틱(불투명 토큰 · 내부 미해석) · heredoc(`<<WORD` · `<<-WORD` · `<<'WORD'` · `<<"WORD"`; 다음 줄부터 WORD 단독 줄까지 본문 제외 · `<<-` 는 선행 탭 제거 뒤 비교) · `<<<` 는 다음 토큰 1개 소비.
- 인용 밖 연산자만 세그먼트 경계: `&&` `||` `;` `|` `|&` `&` 개행 `(` `)`. 인용 안 개행·연산자는 토큰 문자.
- 리다이렉션(`>` `>>` `<` `2>&1` `&>` `[n]>` 꼴)은 대상 토큰과 함께 argv 에서 제거.
- 인용 제거 뒤 토큰 = argv. 앞머리 `VAR=x` · `sudo|command|nohup|time|env` 제거는 현행(`:169-174`) 유지(bash 쪽).
- 파싱 예외(짝 없는 인용 · 닫히지 않은 heredoc · 예상 밖 상태) → `fallback <사유>` 출력 · exit 0.
- 대상 checkout 해석: 현재 dir = payload cwd 로 시작. 세그먼트 `cd <d>`/`pushd <d>` 는 이후 세그먼트의 dir 갱신(상대경로는 이전 dir 기준 · `~/` 는 HOME 치환). git 세그먼트는 `-C <d>`(누적) · `--git-dir=<d>`/`--git-dir <d>` · `--work-tree=<d>`/`--work-tree <d>` 반영. 토큰에 미전개 `$VAR` · `$(…)` · 백틱 · `cd` 인자 없음/`cd -`/`popd` → 해석 불가 → payload cwd 유지(잔여 우회 · 머리말·README 에 문서화). `(`…`)` 서브셸 안 `cd` 도 이후에 적용(과대 근사 · 문서화).
- branch = `git -C <dir> rev-parse --abbrev-ref HEAD`(`--git-dir` 형태는 `git --git-dir=<d> …`) · dir 별 1회 캐시 · git/gh 세그먼트에만 실행 · 실패 시 빈 문자열(현행 `:143 || true` 와 같음).

**결정 4 — argv 형태 편입(기존 열거 ⑴–⑸ 의 다른 argv · 새 규칙 아님 · 머리말 `:11` 유지).**
- gh: 서브커맨드 앞 전역 플래그 건너뛰기 — `-R`/`--repo`/`--hostname` (값 1개) · `--repo=…`/`--hostname=…`. `pr merge` → ⑷. `gh api`: `-X <M>`/`--method <M>`/`--method=<M>` 가 `PUT`(대소문자 무관) 이고 첫 positional 이 `pulls/<n>/merge` 로 끝나면 ⑷ 차단. 그 외(`GET` 기본 · `-f` 만 · 다른 endpoint) 통과.
- push: 묶은 short flag `^-[A-Za-z]+$` 에 `f` 포함 → force · `d` 포함 → deleting. 값을 갖는 옵션 `-o`/`--push-option`/`--receive-pack`/`--exec` 는 다음 토큰 소비(positional 오계수 방지). `HEAD`·`@`(단독 또는 refspec dst) 는 세그먼트 branch 로 치환해 `is_main_ref` 판정 → develop 위 subagent `push origin HEAD` = ⑴-a.
- merge · push 무 refspec 규칙(`:223`·`:234`·`:242`·`:257`)의 `on_main`/`BRANCH` 는 세그먼트 branch(대상 checkout) 사용 → V2.
- `pull)` 분기 신설: 세그먼트 branch ∈ {main,master,develop,product} 이고 토큰에 `--no-ff` · `--no-rebase` · `--rebase=false` · `--ff=false` 중 하나 → deny(사유에 출구 `--ff-only`/`--rebase` 명기). 플래그 없는 `git pull` · `--rebase` · `--ff-only` 통과.
- `:271` 문구 → 「\`git branch -D main|master|develop|product\`」.
- product 규칙(`:223`·`:247`)은 그대로 · 세그먼트 branch 사용.

**결정 5 — 머리말(A5 병합).** `:71-72` 를 2단 규칙으로 교체: 「준비 실패(python3 부재 · envelope 이상 `:82-83`) = exit 2 차단(2026-09-09 계약) / envelope 통과 뒤 판정 불가(parser 폴백 · branch 미해석 · `agent_id` 부재) = 통과. exit 1 은 Claude Code 규약상 비차단이나 이 hook 은 exit 1 을 내지 않는다」. `:88-90` 삭제. `:22-24` 허용 목록에 `pull`(플래그 없음·`--rebase`·`--ff-only`) · heredoc/인용 문자열 안 문구 · `gh api` GET 추가. 알려진 한계 `:74-76` 유지 + 「변수·명령치환 대상 dir 은 payload cwd」 1줄 + `COLAB_GIT_GUARD_PARSER` seam 1줄.

**시험(먼저 작성 · RED 확인 뒤 구현).** 파일 = 새 `scripts/tests/test_git_guard.py`. 실행 게이트 = `agent-bridge`(`gates/run.sh:308` unittest 목록에 파일 추가 · 같은 커밋). bridge `guard()` 는 cwd 를 ROOT 로 고정(`scripts/agent-bridge.py:170`)하므로 `-C`·cwd 불일치 형태는 hook 직접 호출(`test_harness_lifecycle_contract.py:340` 꼴 · `subprocess.run(['bash', ROOT/'.claude/hooks/git-guard.sh'], input=json.dumps(payload))` · env 에서 `COLAB_HOOKS`·`COLAB_GIT_GUARD_PARSER` 제거).
- fixture: `tempfile` 아래 공백 포함 경로(`co lab/repo`)에 git 저장소 · 브랜치 `develop`·`feature` · `git worktree add "<공백 경로>/dev co" develop` 로 두 번째 checkout(develop) · payload 는 guard_probe.py 형(`cwd` · `tool_name=Bash` · `tool_input.command` · subagent 는 `agent_id`·`agent_type`).
- 케이스(완료 기준 번호):
  - ⑴ cwd=repo(develop) · `git -C "<repo>" push --force origin develop` · `… branch -D develop` · subagent `… push origin develop` · subagent `… push origin main` · `… merge feature`(develop 위) · `… push origin product` · 홑따옴표 `-C '<repo>'` 동형 → 2. 허용형: feature 위 `push origin feature` · `merge --ff-only develop` · `pull --rebase` · `worktree add …` · `push origin --delete feature` → 0.
  - ⑵ cwd=feature checkout · `git -C "<dev co>" merge feature` → 2 · `cd "<dev co>" && git merge feature` → 2 · subagent `cd "<dev co>" && git push` → 2 · 같은 명령 `-C "<feature>"` → 0.
  - ⑶ develop 위 `cat > note.md <<'EOF'\ngit merge --no-ff x\ngh pr merge 1\ngit push --force origin develop\nEOF` → 0 · `grep -E "git merge|gh pr merge" f` → 0 · `git commit -m "gh pr merge note; git push -f origin develop"` → 0 · `python3 - <<EOF … EOF` 본문에 병합 문구 → 0.
  - ⑷ `gh -R o/r pr merge 1` · `gh --repo o/r pr merge` · `gh api -X PUT repos/o/r/pulls/1/merge` · `gh api --method put …/merge` → 2 · `gh api repos/o/r/pulls/1/merge` · `gh api -X GET …/merge` → 0. develop 위 `push -fu origin develop` · `push -uf origin develop` → 2 · subagent develop 위 `push origin HEAD` · `push origin @` → 2 · 메인 develop 위 `push origin HEAD` → 0(⑴ 은 subagent 한정). develop 위 `pull --no-ff origin develop` · `pull --no-rebase` · `pull --rebase=false` · `pull --ff=false` → 2 · `pull` · `pull --ff-only` · `pull --rebase` → 0 · feature 위 `pull --no-ff` → 0.
  - ⑸ 짝 없는 인용 `git push --force origin develop "x` → 2(현행 동일) · `echo "unterminated` → 0. fault-injection: `COLAB_GIT_GUARD_PARSER` 를 (a) 없는 경로 (b) `exit 3` 스크립트 (c) 1행만 내고 죽는 스크립트로 두고 `git push --force origin develop` → 2 · `git status` → 0 · stderr 에 「hook readiness failure」 없음.
  - 파서 단위 시험(import): heredoc 본문 제외 · 인용 안 `|`·`;` 비분리 · 리다이렉션 제거 · `-C` 누적 · `cd` 상대경로 · `$VAR` 미해석 → cwd.
  - bash 문법 검사: `bash -n scripts/harness/hooks/git-guard.sh` rc=0(문법 오류 = bash exit 2 = 전 Bash 정지 → 시험으로 고정).
  - 기존 시험 무변경 green: `test_agent_bridge.py:463`(`.codex/hooks.json` 명령 · cwd=ROOT/scripts) · `:483-507` · `test_harness_lifecycle_contract.py:319-346`.

### 4.2 A2 (PR 1 = ⓒ 문서만 · 코드 0 · ⓐ 는 PR 2)
- `.agents/skills/design-review/SKILL.md:101` 현재: 「`fix` 레인은 `COLAB_FIX_LANE=1` 로 돈다 — … 편집을 막는다보호된 fix 구현 단계에서 `COLAB_ALLOW_TEST_EDIT=1`로 우회하지 않는다.」 → 두 문장으로 분리하고 내용을 「편집 시점 차단은 Codex 경로에만 있다(`COLAB_FIX_LANE=1` 은 `scripts/agent-bridge.py:275-278` · `scripts/dev.ps1` 이 넘기는 env · Claude Code 는 hook env 를 lane 별로 줄 수 없어 `test-file-guard` 가 통과). Claude lane 의 경계는 `begin --role lane-worker --scope <glob>` 의 handoff/H7 대조(인계 시점 · `docs/development/lifecycle-evidence.md` 「인계」)다. / `COLAB_ALLOW_TEST_EDIT=1` 은 Codex 보호 단계에서 켜지 않는다.」
- `:106` 「`COLAB_FIX_LANE=1`인 구현 단계에서」 → 「구현 단계(Codex = `COLAB_FIX_LANE=1` env · Claude = 편집 시점 차단 없음 · `--scope` 인계 대조)에서」. 시험 작성이 같은 task 인 Claude lane 은 scope 에 시험 경로가 들어 인계 대조가 시험 편집을 구분하지 못한다는 한계 1문장(편집 시점 차단은 PR 2 A2 ⓐ). task 2개 분할(ⓒ′)은 적지 않는다(기각 · `lifecycle_contract.py:312-315` red 잔존 인계 거절).
- `docs/development/dual-agent.md:59-60` 같은 취지로 교정(「`COLAB_FIX_LANE=1`의 구현 단계로 진행한다」 → Codex/Claude 분기).
- 완료 grep: `grep -n 'COLAB_FIX_LANE=1' .agents/skills/design-review/SKILL.md` 결과 줄마다 Codex 또는 env 어휘 동반.

### 4.3 A3 경계 표기 (코드 0)
- `README.md:115-117` blockquote 에 추가: 「`migration-guard`·`decision-number-guard`·`test-file-guard` 는 Edit/Write 도구만 본다(`.claude/settings.json` PreToolUse `Edit|Write`). `sed -i` · 리다이렉션 · `tee` · `python -c` 등 Bash 쓰기는 대상이 아니다. Bash 쓰기까지 잡는 사후 검사 = `begin --scope` 를 선언한 task 의 handoff/H7(baseline = begin 시점 전 파일 내용 hash · 도구 무관)」. 정본 링크 `docs/development/lifecycle-evidence.md` 「인계」.
- `test-file-guard.sh` 머리말(`:3-27` 블록)에 같은 문장 + A5 2단 규칙. 머리말은 A1 이후 동작 기준으로 A1 커밋 뒤에 쓴다.
- migration·결정 번호의 Bash 편집 사후 검사 「있음/없음」: lane 이 확인해 README 문장에 기입 — 후보 = `work-item-consistency`(결정 번호 중복 · `gates/tools/work_item_consistency.py:136`) · `migration-single-head`. 확인 전에는 「scope handoff」만 적는다. migration-guard·decision-number-guard 머리말 문장은 C10(PR 3).

### 4.4 A4 `gates/run.sh` 인자 검사
- 위치: `:9` `GATE="${1:-}"` 직후 · `:26`(`task` 분기) · `:42`(gate-start 증거 기록) · `:163-170`(host mutex) 보다 앞. 검사에 필요한 알려진 gate 목록은 `:296-306` `ALL_GATES=(…)` 정적 배열을 `:9` 뒤로 이동(의존 없음). `case` 라벨 중 `ALL_GATES` 밖 이름이 있으면 `KNOWN_GATES=("${ALL_GATES[@]}" …)` 로 합치고 보고(lane 확인 항목).
- 규칙: 인자 0 또는 빈 `$1` → 78 · `GATE=all` 은 `$# == 1` 또는 (`$# == 3` · `$2 == -j` · `$3 =~ ^[1-9][0-9]*$`) 만 허용 · `GATE=task` 는 `$# == 1` · 단독 gate 는 `$# == 1` 이고 KNOWN 안. 위반 시 stderr `::gate-readiness-failure:: <사유> · dropped=<버린 토큰들> · usage: gates/run.sh <gate> | all [-j N] | task` · exit 78 · `all -j4` 꼴은 사유에 `-j 4` 형태 안내.
- `:795-796` 의 `-j` 읽기는 유지(검사 통과 뒤라 항상 유효). `:971-977` 두 case 는 도달 불가가 되므로 exit 2 → 78 로 바꾸고 방어용으로 남긴다(2 잔존 0).
- 영향 조사(grep 결과): `gates/tools/gate-host-mutex-selftest.sh:97` `bash "$RUN" "$g"` 단일 인자 → 무영향. `scripts/harness/hooks/lifecycle_contract.py:472` `['bash', run.sh, gate]` → 무영향. `scripts/tests` 의 `run.sh` 참조는 전부 fixture 치환(`test_harness_lifecycle_contract.py:354` · `test_task_runtime.py:84,370` · `test_harness_work_state.py:55` · `test_ci_schema_setup.py:34`) 또는 텍스트 대조(`test_harness_record_gates.py:110-116` `adr-records)` 라벨 · `:285` ci.yml 문자열) → case 라벨·ci.yml 무변경이면 무영향. `returncode == 2` 기대는 hook 시험뿐. `gates/README.md:78` 「`all [-j N]`」 일치 · 같은 자리에 「인자 오류 = 78」 1줄 추가. `.github/workflows/ci.yml` 의 다중 인자 호출 여부는 lane 이 `grep -n 'run.sh' .github/workflows/ci.yml` 로 확인(R5-6 정정 0건 · 미검증).
- 시험(먼저): 새 `scripts/tests/test_gates_run_args.py` · `agent-bridge` 목록(`:308`) 등록. `subprocess.run(['bash', ROOT/'gates/run.sh', *args], env={…, 'TMPDIR': <빈 임시 dir>})`. 케이스: `agent-bridge extra` · `all -j4` · `all -j 4 x` · `all -j abc` · `all -j 0` · `task x` · `no-such-gate` · 인자 없음 · 빈 문자열 → rc 78 · stderr 에 버린 토큰/이름 · stdout+stderr 에 `::gate-waiting::` 0 · `<TMPDIR>/colab-v2-gate-host-mutex` 미생성 · `COLAB_TASK_ID` 를 준 `task x` 에서도 gate-start 미실행(runtime 디렉터리 무변화). 무변경 확인: `task`(COLAB_TASK_ID 없음) → 기존 `:27` 메시지 · 78. `all -j N` 정상 경로는 unit test 밖 → CI/`gates/run.sh all -j 2` 실행 1회로 확인(§7 V12).

### 4.5 A5 머리말 2단 규칙 · 도달 불가 줄
- `git-guard.sh:71-72` · `:88-90` → §4.1 결정 5(A1 커밋 안). `test-file-guard.sh:27` 교체 · `:42` 삭제(A2/A3 커밋 안). `:28` · `git-guard.sh:3-4` 「Effective 2026-09-09」 줄 유지.
- 동작 변화 0 증명 = `test_harness_lifecycle_contract.py:319-327` 기존 시험(4 hook × `{broken`/`{}`/Read).
- migration-guard · decision-number-guard · worktree-setup 머리말은 C10(PR 3) — PR 1 커밋 메시지에 「나머지 3 파일은 PR 3」 명기.

### 4.6 A6 decision-number-guard 기준 · 실패 방향 (Ted 판정 2026-09-26 「페이블 권고대로 젖부」로 C5/C10 에서 PR 1 이관 · 단독 커밋)
- 파일: `scripts/harness/hooks/decision-number-guard.sh` — `:8` · `:18` 주석 `origin/main` · `:27` exit 1 문장 · `:38` 도달 불가 줄 · `:63-73` 기준선(`:67` `origin/main:` · `:69-72` 워킹트리 폴백 · `:73` `[ -n "$BASE" ] || exit 0`).
- 변경: 기준 = `origin/develop:dev-package/PLAN-SoT.md`. 못 읽으면 stderr 「hook readiness failure: origin/develop 부재 · `git fetch origin develop` 뒤 재시도」 exit 2(migration-guard.sh:72-74 와 같은 방향). 워킹트리 `max-decision.sh` 폴백(`:69-72`) 삭제(조용한 대체 경로 제거). `:27` 2단 규칙 · `:38` 삭제. `README.md:75` `origin/main` → `origin/develop`(C2 Fable 「C5 와 같은 PR 에서만」).
- 시험: `test_harness_lifecycle_contract.py:361-372`(`test_codex_decision_content_hits_shared_judge…`) fixture 에 `git update-ref refs/remotes/origin/develop HEAD` 추가(원장 커밋 뒤) · 새 케이스 「ref 부재 → 2 · stderr readiness」 · `test_agent_bridge.py` 의 decision 관련 시험 재확인. `test_raw_ledger_requires_content…`(`:376-384`) 는 validate-input 단계라 무영향.
- 제외 시: 위 파일·시험·README:75 전부 손대지 않음 · scope 선언에서 뺌.

## 5. 시험 결정 (요약)
- 순서: 시험 파일 작성 → `gates/run.sh agent-bridge` RED(공백 `-C` 0 · heredoc 2 · run.sh 인자 0/2) 기록 → 구현 → GREEN. red→green 로그를 PR 「검증」에 인용.
- 재사용 seam: hook 직접 호출(`test_harness_lifecycle_contract.py:340`) · bridge `guard-command`(`test_agent_bridge.py:483`). 신설 seam: `git_guard_parse.py` import 단위 시험 · `COLAB_GIT_GUARD_PARSER` 결함 주입.
- 단독 게이트: `agent-bridge`(새 시험 2파일 포함) · `harness-contract`(README·문서·hook wiring) · `intent-ref`(트레일러) · `exec-bit`(새 `.py` 비트).
- green-by-skip 방지: 새 시험 파일 2개가 `run.sh:308` 목록에 있어야 돈다 — 등록 누락 시 unittest 수가 156 에서 늘지 않으므로 PR 「검증」에 test 수 전후를 적는다.

## 6. 위험 · 롤백
- fail-closed 면: git-guard 는 모든 Bash 호출을 거친다(`.claude/settings.json:58-66`). bash 문법 오류 = exit 2 = 전 세션 Bash 정지 → `bash -n` 시험 · parser 예외/부재는 폴백. A1+A5 는 단독 커밋(되돌림 단위 = `git revert <A1 sha>`). 정지 시 복구 = Edit 도구로 `git-guard.sh` 되돌림(Edit/Write 는 matcher 밖 `:68-84`) 또는 `COLAB_HOOKS=0` 세션 재시작(`README.md:79-98`).
- hook 은 `${CLAUDE_PROJECT_DIR}` 쪽 스크립트를 실행(`worktree-setup.sh:31-38` 문서 인용) → lane 자신의 Bash 는 메인 checkout 의 구버전 guard 가 판정. lane 검증은 worktree 스크립트 직접 호출(§7). 메인 checkout 은 PR 1 병합 · pull 뒤에 새 guard 를 얻는다 — 그 시점에 오케스트레이터가 `git status` · `git push origin <기능>` 로 첫 호출 통과를 확인(그룹 T 스모크와 별개).
- 파서 잔여 우회(변수·명령치환 dir · 서브셸 cd 과대 근사 · `bash -c`/`eval`)는 머리말·README 에 적고 완료 기준에 넣지 않는다.
- A4 78 은 PR 2 B3 집계와 만나면 선언 오타 1건이 전체 78 → B3 시험에 이 경우 포함(묶음 메모 이관).
- 시험 fixture 의 공백 경로가 `tempfile` 기본 경로에서 만들어지지 않는 환경(TMPDIR 제한) → 준비 실패 78 로 드러남(skip 금지).

## 7. 검증표
| V | 무엇 | 명령(worktree 루트) | 기대 | 완료 기준 |
|---|---|---|---|---|
| V1–V5 | git-guard 새 시험 | `COLAB_TASK_ID=<id> bash gates/run.sh agent-bridge` | green · 시험 수 156+신규 | A1 ⑴–⑸ |
| V6a | 기존 시험 | 같은 실행 안 `test_agent_bridge.py` · `test_harness_lifecycle_contract.py` | green · skip 수 10 무변화 | A1 ⑹ |
| V6b | 재현 명령 재실행 | guard_probe.py 를 저장소 밖 임시 사본으로 복사 · `HOOK` 을 `<worktree>/scripts/harness/hooks/git-guard.sh` · `ROOT` 를 worktree 로 바꿔 실행 + pull 2종(`git -C "<wt>" pull --no-ff origin develop` · `pull --no-rebase …` · cwd 는 develop checkout) | 공백 `-C` 4종 · 무 `-C` 4종 · `-C /tmp` 1종 · pull 2종 전부 rc=2 · stderr 「⛔ 차단(H3 git-guard)」 | A1 ⑹ |
| V6c | 허용형 재실행 | 같은 probe 에 feature checkout cwd · `push origin feature` · `merge --ff-only develop` · `pull --rebase` · `pull` · `worktree list` · `gh api repos/o/r/pulls/1/merge` | rc=0 · stderr 빈 줄 | A1 ⑴⑷ |
| V6d | heredoc 오탐 | probe 에 §4.1 ⑶ 4종(develop cwd) | rc=0 | A1 ⑶ |
| V5b | 결함 주입 | `COLAB_GIT_GUARD_PARSER=/nonexistent` 로 V6b 의 무 `-C` 4종 | rc=2(현행 규칙) · `git status` rc=0 | A1 ⑸ |
| V7 | README·머리말 | `grep -n 'pull' README.md scripts/harness/hooks/git-guard.sh` · `grep -n 'main|master' scripts/harness/hooks/git-guard.sh` | :73 행·:22-24 목록에 pull/gh/heredoc 명시 · `:271` 옛 문구 0건 | A1 ⑺ |
| V8 | A2 문서 | `grep -n 'COLAB_FIX_LANE=1' .agents/skills/design-review/SKILL.md docs/development/dual-agent.md` · `grep -c '막는다보호된' …SKILL.md` | 각 줄 Codex/env 동반 · 융합 문장 0 | A2 ⓒ |
| V9 | A3 경계 | `grep -n 'Bash 쓰기' README.md scripts/harness/hooks/test-file-guard.sh` · `bash gates/run.sh harness-contract` | 각 1건 이상 · green | A3 |
| V10 | run.sh 인자 시험 | agent-bridge 실행(`test_gates_run_args.py` 포함) · 수동: `TMPDIR=$(mktemp -d) bash gates/run.sh all -j4` | rc 78 · stderr 에 `-j4` · `$TMPDIR/colab-v2-gate-host-mutex` 없음 | A4 ⑴⑵ |
| V11 | 알 수 없는 gate | `TMPDIR=<빈 dir> bash gates/run.sh no-such-gate` · 인자 없음 | 78 · `::gate-waiting::` 0 · mutex dir 없음 | A4 ⑵ |
| V12 | 무변경 | `bash gates/run.sh harness-contract`(단독) · `bash gates/run.sh all -j 2` 1회(lane 은 호스트 단독 시점에) · `COLAB_TASK_ID=<id> bash gates/run.sh task` | 현행과 같은 종료코드·요약 | A4 ⑶ |
| V13 | A5 | `grep -n 'exit 1 은 통과' scripts/harness/hooks/git-guard.sh scripts/harness/hooks/test-file-guard.sh` · `grep -n 'command -v python3 .*exit 0' 같은 두 파일` | 0건 · 0건 · `test_raw_guard_malformed…` green | A5 |
| V14 | (A6) | agent-bridge · `grep -n 'origin/main' scripts/harness/hooks/decision-number-guard.sh README.md` | ref 부재 → 2 시험 green · 0건 | C5 이관 |
| V15 | 문법·비트 | `bash -n scripts/harness/hooks/git-guard.sh` · `bash -n gates/run.sh` · `bash gates/run.sh exec-bit` · `bash gates/run.sh intent-ref` | 전부 0 | 공통 |

## 8. 레인 지시 (PR 1 · lane-worker 1개)
- 스폰: `Agent(subagent_type: "lane-worker", isolation: "worktree")` 명시(Workflow `agent()` 가 부모 worktree 에서 돈 관측 1회). 기준 = 현재 checkout HEAD(`.claude/settings.json` `baseRef: "head"` · 브랜치 `claude/harness-improvement` · intent·spec 커밋 포함). lane 첫 행동: `git merge-base --is-ancestor <spec 커밋> HEAD` 확인 · 부모 checkout 경로에서 돌고 있으면 구현 전 정지·보고.
- 증거 시작(worktree 루트): `python3 scripts/agent-bridge.py lifecycle begin --role lane-worker --gate agent-bridge --gate harness-contract --gate intent-ref --gate exec-bit --scope 'scripts/harness/hooks/git-guard.sh' --scope 'scripts/harness/hooks/git_guard_parse.py' --scope 'scripts/harness/hooks/test-file-guard.sh' --scope 'scripts/tests/test_git_guard.py' --scope 'scripts/tests/test_gates_run_args.py' --scope 'gates/run.sh' --scope 'gates/README.md' --scope 'README.md' --scope '.agents/skills/design-review/SKILL.md' --scope 'docs/development/dual-agent.md'`. A6 몫으로 `--scope 'scripts/harness/hooks/decision-number-guard.sh' --scope 'scripts/tests/test_harness_lifecycle_contract.py'` 를 함께 선언한다. `docs/development/lifecycle-evidence.md` · `dev-package/reports/**` 는 기본 허용.
- `harness-contract-selftest` 미선언: 그 목록(`run.sh:312` `test_harness_config/evidence/pr_contract/work_state/record_gates`)의 대상 파일을 PR 1 이 바꾸지 않는다. `gate-host-mutex-selftest` 는 run.sh 단일 gate 경로 확인용으로 unbound 1회 실행(선택 · serial).
- 게이트 실행은 `COLAB_TASK_ID=<id> bash gates/run.sh task` 1회(선언 집합) · 호스트 단독 · 병렬 lane 없음.
- 커밋 단위(각각 `Intent-Ref:` 트레일러 · Co-Authored-By/Claude-Session 트레일러): ① A1+A5(git-guard) — `git-guard.sh` · `git_guard_parse.py` · `test_git_guard.py` · `run.sh:308` 등록 · `README.md:73` 행 ② A2+A3+A5(test-file-guard) — `test-file-guard.sh` · `README.md:115-117` · `SKILL.md:101,106` · `dual-agent.md:59-60` ③ A4 — `run.sh` · `test_gates_run_args.py` · `run.sh:308` 등록 · `gates/README.md:78` ④ A6. 사용자 승인 없는 push 금지 · 병합·PR 게시는 Ted.
- 인계: `lifecycle handoff --task <id> --mode complete --summary '<red→green 계수 · V 표 결과>'` · `COLAB_HANDOFF` 줄과 `WORKTREE=<경로> BRANCH=<브랜치>` 를 최종 메시지에.

## 9. PR 1 본문 계획 (`scripts/harness/pr_contract.py` 형식 · `.github/pull_request_template.md`)
- 본문 파일 위치: 저장소 밖 `~/.claude/pr-bodies/PR-BODY-harness-improvement-pr1.md`(Ted 관행). 검증: `python3 scripts/harness/pr_contract.py <본문> --head <40자 SHA> --mode draft` → 0.
- 첫 줄: 「하네스 개선 PR 1 — git-guard 가 명령 형태와 무관하게 막고 run.sh 인자 오류가 78 로 드러난다」.
- `Plan-Ref: dev-package/prd/specs/S-HARNESS-IMPROVEMENT-20260925.md` · `Head-SHA: <게시 시 갱신>` · `검증 상태: 미검증`(CI 뒤 갱신).
- 목적: intent 그룹 A 원한 결과(V1–V13). 범위: §8 커밋 ①–③(+④) 파일 · 제외 = A2 ⓐ(PR 2) · C10 나머지 3 hook · README 훅 표 재작성(C2) · 훅 정의 무변경. 계획: phase 1 완료 · phase 2/3 stub 대기. 결정: 새 ADR 없음(A4 2→78 은 AGENTS.md 정의 적용 · B3 ADR 은 PR 2). 검증: §7 V 표를 「원한 결과 ↔ 실제 ↔ 근거 ↔ 가치 상태」 행으로 · 3계수 · red→green 로그 경로. 남은 제약: 메인 checkout 은 병합·pull 뒤 새 guard 적용 · 잔여 우회(변수 dir · `bash -c`) · A6 포함 여부 · T5 재신뢰 불요(정의 무변경).
- 게시 절차·병합 뒤: Ted 가 PR 게시 · 병합 뒤 오케스트레이터가 메인 checkout pull → 첫 Bash 통과 확인 → phase 2 착수 · T7 메모리 갱신 없음(PR 1 은 메모리 대상 아님).

## 10. 정책 대조
- CLAUDE.md/AGENTS.md 저촉: 없음 — 게이트 종료코드 0/1/78 정의 적용(A4) · 제품 코드 0 · `contracts/**` 0.
- 「절대 하지 않는 것」: 훅 정의 변경 0 · ADR 이력 수정 0 · 승인 intent 본문 변경 0(줄 추가만).
- 계약 동결 해제: 아니오. envelope 계약 무변경.
- 디자인 제약: 해당 없음(frontend 무변경).

## 11. 우려 항목 (판정 필요)
| # | 항목 | ⓐ | ⓑ | 권고 |
|---|---|---|---|---|
| 1 | A6(decision-number-guard 기준 develop · 부재 시 차단)을 PR 1 에 넣나 | 넣음(막는 장치 묶음 · 단독 커밋 · README:75 동반) | PR 3(C5) 유지 | ⓐ — Ted 판정 2026-09-26 확정 |
| 2 | 시험 seam `COLAB_GIT_GUARD_PARSER` env 를 제품 hook 에 두나 | 둠(폴백=현행 규칙이라 약화 없음 · 머리말 명시) | 파서 안 `COLAB_GIT_GUARD_FAULT` 분기 | ⓐ |
| 3 | `run.sh` 알려진 gate 판정 근거 | `ALL_GATES` 배열 상단 이동 | `case` 라벨 추출 | ⓐ |

## 12. 범위 밖
- A2 ⓐ 편집 시점 차단(PR 2 · L1 ⓐ·L8 스모크 뒤) · migration-guard/decision-number-guard/worktree-setup 머리말(C10) · README 훅 표 재작성(C2) · ruleset JSON(C5·T1) · B3 집계 우선순위 · `bash -c`/`eval` 한 겹 · reseed ACK 검사(`:134`) 확장 · 변수·명령치환 dir 해석.
