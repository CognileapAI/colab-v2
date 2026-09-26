# Spec: 하네스 개선 — phase 1(PR 1 · 그룹 A1–A7 + C12 커밋) 막는 장치 바로잡기 · phase 2/3 stub
출처 intent: `dev-package/intent/2026-09-25-harness-improvement.md` (승인 그룹 A 2026-09-25 · Ted 원문 "전부 권고대로" · 2026-09-26 Fable 재판정·그룹 A 보강 · 2라운드 A6 · 3라운드 A7 · spec 세부 · spec gate ① GO-WITH-CHANGES 반영 — Ted 원문 "구ㅜㄴ규대로 하자").
근거: 저장소 밖 `~/.claude/reports/harness-state-20260925/`(fable-judges/ · fable-recheck-r3/spec-gate1-A.md · spec-gate1-B.md · cross.md · recheck-r2.md · guard_probe.py). 줄 번호 기준 = develop `67a03a05` = 브랜치 `claude/harness-improvement`(코드 동일 · 이 개정 시 전 인용 재열람 · 정정: `run.sh` unittest 목록 `:310`(구 :308) · selftest 목록 `:316`(구 :312) · `ALL_GATES` `:284`(구 :296-306) · gate-start `:36-41`(구 :42) · host mutex `:170` · lifecycle 시험 `:366-380`(구 :361-372) · `:381-396`(구 :376-384)).
spec 경로: `dev-package/prd/specs/S-HARNESS-IMPROVEMENT-20260925.md` (PR 1·2·3 의 Plan-Ref 공통).
모든 커밋 메시지 끝에 `Intent-Ref: dev-package/intent/2026-09-25-harness-improvement.md` 트레일러(`colab-v2-work/SKILL.md:130` · 게이트 `intent-ref` 판정 대상 경로 `scripts/**`·`gates/**`·`.agents/**`·`.claude/**` 포함).

## 0. phase 개요 (엄격 순차)
| phase | PR | 그룹 | 상태 |
|---|---|---|---|
| 1 | PR 1 | A1–A7 + C12(별도 커밋) | 이 문서 §1–§9 상세 |
| 2 | PR 2 | B(B1–B8) → L(L1–L8) · lane 1개 · `lifecycle_contract.py`·`test_task_runtime.py` 공유 | stub — 그룹 B·L 판정 반영은 PR 1 병합 뒤 상세화 |
| 3 | PR 3 | C(C1–C11 잔여) · `README.md`·hook 머리말·ruleset JSON | stub — PR 2 병합 뒤 상세화 |
- 다음 phase 는 앞 PR 병합 뒤 develop 기준으로 착수. PR 사이 공유 파일: `gates/run.sh` · `README.md` · `lifecycle_contract.py` · `test_task_runtime.py`(A7 로 PR 1 이 먼저 손댐 · PR 2 는 병합 뒤 기준) · SKILL 문서.
- 그룹 T(Ted) 는 PR 과 독립(T1 적용 PR 1 병합 뒤 · T5 Claude 재신뢰 불요 · L8 스모크는 A7 병합 뒤).

## 1. 문제 진술 (phase 1)
- `git-guard.sh:167` 비인용 `set -- $seg` → 공백 경로 `git -C "<repo>" …` 에서 `-C` 가 첫 조각만 소비(`:193`), 규칙 ⑴–⑸ 전부 통과. 브랜치 판정 근거는 payload `cwd` 하나(`:143`). `gh -R` · `gh api PUT` · `-fu` · `push origin HEAD` · 보호 브랜치 위 `pull --no-ff/--no-rebase` 미검출. heredoc·인용 인자 안 문구 오탐(`:106` · `:149`).
- `test-file-guard.sh:32` env 부재 exit 0 → Claude lane 편집 시점 차단 없음. 문서 3곳(`design-review/SKILL.md:101`·`:106` · `dual-agent.md:59-60`)은 차단을 기술.
- `gates/run.sh:9` `$1` 만 읽음 · `$#` 검사 없음 · `all` 은 `$2 == -j` 정확 일치만(`:795`) · 비정수 `-j` 는 `jobs_n=1`(`:796`) · 알 수 없는 gate 는 host mutex 획득(`:170`) 뒤 exit 2(`:975-977`) · 인자 없음 exit 2(`:972-973`).
- 머리말 「exit 1 은 통과다 · 판정 못 하면 통과」(`git-guard.sh:71-72` · `test-file-guard.sh:27`) ↔ 실제 envelope 이상·python3 부재 exit 2(`:82-83` · `:38-39`) · 도달 불가 `|| exit 0`(`git-guard.sh:90` · `test-file-guard.sh:42`) · 거부 문구 `:271` 「main|master」 · `:227`·`:231`·`:235`·`:239`·`:243` 「main/master」(집합은 develop·product 포함 `:145`·`:156`·`:267`).
- (A6) `decision-number-guard.sh:67` 기준 `origin/main`(`:8`·`:18`·`:63-66` 주석 동일) · 못 읽으면 워킹트리 `max-decision.sh` 로 조용히 대체(`:69-72`) · `:73` exit 0.
- (A7 · 새 사실 2026-09-26) SubagentStart hook 2/2 발화 · 평문 stdout 서브에이전트 도달 0회. `researcher-task.sh:40`·`:51`·`:69-75` · `worktree-setup.sh:69-76`·`:245-267` 전부 평문 echo. 주석 `researcher-task.sh:14` · `worktree-setup.sh:40-42` · `bootstrap-diet.sh:23-26` 및 `dual-agent.md:78-80` 「평문으로 싣는다」 가 평문 도달을 전제.
- (C12) `css-edit-audit.sh:74` 평문 `echo "$OUT"` · 머리말 `:21` 「PostToolUse 의 stdout 은 맥락으로 실려 들어간다」 — Claude Code 문서상 평문 stdout 이 모델에 가는 이벤트는 UserPromptSubmit · UserPromptExpansion · SessionStart · PostModelSwitch 뿐(PostToolUse 는 `hookSpecificOutput.additionalContext` JSON 필요).

## 2. 원한 결과 (V-id) — PR 요약 「원한 결과 ↔ 실제 ↔ 근거」 행 이름
- V1 공백 경로 `-C "<…>"`·`-C '<…>'` 로 규칙 ⑴–⑸·product 규칙 각각 rc=2 · 허용형 rc=0 + stderr 빈 문자열 — 확인: `scripts/tests/test_git_guard.py`(agent-bridge gate) · intent A1 ⑴.
- V2 기능 브랜치 cwd 에서 `-C <develop checkout>` · `cd … &&` · `pushd` · `--git-dir/--work-tree` · `( cd x && git merge y )` 뒤 non-ff merge · subagent refspec 없는 push → rc=2 — A1 ⑵.
- V3 heredoc 본문(종결 · 미종결 모두)·인용 인자 안 git merge · gh 병합 · 강제 push 문구 · 여러 줄 `-m` 커밋 메시지 → rc=0 — A1 ⑶.
- V4 `gh -R o/r pr merge` · `gh api -X PUT …/pulls/N/merge[/][?…]` · develop 대상 `push -fu` · develop 위 subagent `push origin HEAD`/`+HEAD` · develop 위 `pull --no-ff`/`--no-rebase`/`--rebase=false`/`--ff=false` → rc=2 · `gh api …/merge`(GET) · `pull --ff-only` · 플래그 없는 `git pull` → rc=0 — A1 ⑷.
- V5 해석기가 fallback 을 내는 입력 = `bash -n` 이 거부하는 입력뿐(시험이 fixture 마다 단언) · 그 입력의 rc 는 현행 규칙 결과와 같음 · 해석기 결함 주입(hook 폴더 tempdir 복사본 · 없음/exit 3/1행 스텁/종료 표식 없음/레코드 뒤 exit 3/필드 틀린 레코드) 시 폴백 또는 deny · crash 0 · stderr 1줄 `git-guard: parser fallback: <사유>` — A1 ⑸.
- V6 기존 시험(`test_agent_bridge.py:461-507` · `test_harness_lifecycle_contract.py:319-349`) green · 오케스트레이터 재현 명령(guard_probe.py 9종 + pull 2종)을 worktree 스크립트로 재실행해 우회형 전부 rc=2 — A1 ⑹.
- V7 `README.md:73` git-guard 행 · 머리말 허용 목록(`git-guard.sh:22-24`)이 편입 형태와 일치 · 옛 거부 문구(`-D main|master\`` · 「main/master」 5곳) 0건 — A1 ⑺.
- V8 `SKILL.md:101` 두 문장 분리 · `:101`·`:106`·`dual-agent.md:60` 이 Claude lane 실제 동작(env 없음 → 편집 시점 차단 없음 · `--scope` 인계 시점 차단) 기술 · `grep -n 'COLAB_FIX_LANE=1' .agents/skills/design-review/SKILL.md` 가 Codex/env 조건과 함께만 나옴 — A2 ⓒ.
- V9 `README.md` hook 절 · test-file-guard 머리말에 대상 도구(Edit/Write) · 비대상 경로(Bash 쓰기) · 사후 검사 수단(`begin --scope` handoff/H7) 명시 · harness-contract green · 코드 변경 0 — A3.
- V10 `run.sh a b` · `run.sh all -j4` · `run.sh all -j 4 x` · `run.sh all -j abc` · `run.sh all -j`(인자 2개) · `run.sh task x` → 78 + stderr 에 버린/인식 못 한 토큰 — A4 ⑴.
- V11 `run.sh no-such-gate` · 인자 없음 → 78 · host mutex 획득 흔적 0(`${TMPDIR}/colab-v2-gate-host-mutex/` 미생성 · `::gate-waiting::` 0줄) · `:36-41` gate-start 미실행 — A4 ⑵.
- V12 단독 gate · `all -j N` · `task` 기존 동작 무변경 · `run.sh` 의 모든 `case` 라벨이 KNOWN 판정 통과(unit) — A4 ⑶.
- V13 `grep -n 'exit 1 은 통과' scripts/harness/hooks/git-guard.sh scripts/harness/hooks/test-file-guard.sh` 0건 · 도달 불가 줄 삭제 · `test_harness_lifecycle_contract.py:319-327`(`{broken`·`{}` → 2 · Read → 0) green — A5.
- V14 (A6) decision-number-guard 기준 `origin/develop` · ref 부재 fixture 에서 Read → 0 · PLAN-SoT 비결정 편집 → 0 · 새 결정 번호 후보 편집 → 2(stderr readiness) 시험 red→green · `grep -n 'origin/main' scripts/harness/hooks/decision-number-guard.sh` 0건 — C5 이관분.
- V15 문법·비트: `bash -n` 3 파일 · `exec-bit` · `intent-ref` 0 — 공통.
- V16 (A7) `researcher-task.sh` · `worktree-setup.sh` stdout = JSON 1줄 `{"hookSpecificOutput":{"hookEventName":"SubagentStart","additionalContext":"…"}}` · exit 0 · `test_task_runtime.py` 단언이 JSON 파싱 경유 green · worktree-setup 「격리 아님」 권고 문구 시험 · Codex bridge(`agent-bridge.py:300-302`) 경유 시험 green · 완료 = 병합·pull 뒤 researcher 1회 스폰 → 첫 턴 task id 노출 관측.
- V17 (C12) `css-edit-audit.sh` stdout = PostToolUse additionalContext JSON 1줄 · 머리말 `:21` 정정 · `test_agent_bridge.py:160-176` green + hook 직접 호출 JSON 시험.

## 3. 해법 개요
- 코드: git-guard 의 명령 해석 **과 규칙 판정** 을 python 모듈(quote-aware tokenizer · 대상 checkout 해석 · 규칙 엔진 · 지연 branch 해석)로 옮기고, bash 는 envelope(불변) · 해석기 호출 · 결과 검증(JSON lines + 종료 표식) · **폴백 = 현행 bash 규칙 엔진 동결본** 만 맡는다 · `run.sh` 인자 검사 1블록 · 머리말 2건 · decision-number-guard 기준·readiness · SubagentStart/PostToolUse hook 3개 출력 JSON 화.
- 문서: SKILL·dual-agent·README·gates/README·hook 주석 문장 교정.
- 훅 정의(`.claude/settings.json` · `.codex/hooks.json`) 무변경 → `/hooks` 재신뢰 0. envelope 계약(`git-guard.sh:81-83` · `lifecycle_contract.py:503-523` validate-input) 무변경. 시험용 env seam 은 제품 hook 에 두지 않는다(Ted 판정 Q11).

## 4. 구현 결정

### 4.1 A1 git-guard — tokenizer · 대상 checkout · argv 형태 편입
파일·현재 앵커(재열람 확인): `scripts/harness/hooks/git-guard.sh` — 머리말 `:11-24`(열거·허용 목록) · `:71-72`(exit 1 문장) · `:77`(`set -uo pipefail`) · `:81-83`(envelope · 불변) · `:88-90`(도달 불가 주석+줄) · `:92-114`(read_fields · 2번째 python 호출 · `:106` 개행→` ; `) · `:134-137`(reseed ⑹ · 불변) · `:143-145`(payload cwd 단일 BRANCH) · `:149`(sed 분리) · `:151-157`(is_main_ref) · `:159-162`(deny) · `:164-178`(`set -- $seg` · 앞머리 정리) · `:181-186`(gh) · `:190-200`(git 전역 옵션) · `:202-245`(push) · `:207`(force 정확 토큰) · `:227`·`:231`·`:235`·`:239`·`:243`(「main/master」 문구) · `:246-260`(merge) · `:261-273`(branch · `:271` 문구) · `:275`(`done <<< "$SEGS"`). Claude 진입점 `.claude/hooks/git-guard.sh` = 3행 shim `exec bash "$(dirname "${BASH_SOURCE[0]}")/../../scripts/harness/hooks/git-guard.sh" "$@"` → 본체의 `BASH_SOURCE[0]` 은 `scripts/harness/hooks/` 로 풀린다(교차 점검 확인 · adapter 우려 없음).

**결정 1 — 해석기 위치 = 새 모듈 `scripts/harness/hooks/git_guard_parse.py`(tokenizer + 규칙 엔진). 호출 자리 = 현행 `:110` `mapfile … read_fields` 앞.**
- python 호출 수 2 유지(`:83` validate-input + 해석기) → 지연 증가 0. 폴백 경로에서만 `read_fields()`(3번째 호출)가 돈다.
- validate-input 에 합치지 않는 이유: ⑴ `--field command|file_path` 로 4 hook 이 공유하는 envelope 계약이고 제약이 「무변경」 ⑵ `:83 … || exit 2` 경로라 해석기 예외가 곧 차단이 됨(폴백 규칙과 충돌) ⑶ `lifecycle_contract.py` 는 PR 2(B·L) 공유 파일 — 파일 면 분리.
- 등록 확인(인용): `.agents/harness.yaml` `sources.hook_names` 는 `.sh` 11개 열거 · `scripts/harness/config.py:174-196` 는 `hook_names` 항목만 원본·adapter·wiring 대조 · `scripts/tests/test_harness_source_layout.py:58-73` 는 같은 11개 이름 고정 + `lifecycle_contract.py` 존재만 단언 → `.py` 보조 모듈은 등록·adapter 불요. 실행 비트 미부여(`python3 <경로>` 로 호출 · `lifecycle_contract.py` 100644 와 같은 꼴 · `gates/tools/exec-bit.sh` 는 `.sh` 만 검사 → green 예측 · lane 1회 실행으로 확인).
- 해석기 경로 = `"$(dirname "${BASH_SOURCE[0]}")/git_guard_parse.py"` 고정. **시험용 교체 경로 env(`COLAB_GIT_GUARD_PARSER`)는 두지 않는다**(Ted 판정 · 첫 줄만 내는 가짜 해석기가 규칙을 비울 수 있음). 결함 주입은 §4.1 시험 ⑸ 의 tempdir 복사본으로.

**결정 2 — 해석기 입출력 · 규칙 판정 위치 · 폴백.**
- 입력: stdin = validate-input 이 낸 payload JSON(`:83` 결과). 해석기가 `tool_name`·`cwd`·`agent_id`·`command` 를 직접 읽는다.
- stdout 프로토콜 = **JSON lines**: 1행째 `parsed` 또는 `fallback <사유>`; 이어 세그먼트마다 JSON 1줄 `{"seg": <n>, "dir": "<대상 checkout 절대경로>", "argv": ["…"], "opaque": <bool>}`(`json.dumps(…, ensure_ascii=False)` · 개행·탭은 JSON 이스케이프 · **branch 필드 없음**); 마지막 줄 = 종료 표식 `{"end": <레코드 수>}`. 탭/개행 구분 필드 금지.
- **판정 위치 = python 1회 안(해석기 = 규칙 엔진)**. 근거: ⑴ bash 가 JSON lines 의 argv 배열을 읽으려면 인용 이스케이프·배열 분할을 하는 자체 JSON 디코더(spec gate ① 이 배제한 부류)이거나 레코드마다 python 호출(2+N 회)이 필요 ⑵ python 1회 안에서 판정하면 호출 수 2 유지 · tokenizer 와 규칙이 한 모듈이라 `import` unit 시험으로 규칙까지 검증 ⑶ bash 는 정규식 3개(1행째 · 레코드 접두 `^\{"seg":` · 종료 표식 `^\{"end":([0-9]+)\}$`)만 읽는다 — JSON 디코드 0. 판정 결과 전달 = 해석기 종료코드: `0` = parsed·허용 · `2` = parsed·거부(stderr 1줄 = 현행 `deny()` 와 같은 형식 `⛔ 차단(H3 git-guard) …` · 종료 표식 **뒤에** 낸다) · 그 외 = 해석 실패.
- bash 검증·분기: `mapfile -t` 로 stdout 수집 → 유효 = (1행째 == `parsed`) ∧ (마지막 줄이 종료 표식) ∧ (중간 줄 수 == 표식의 수) ∧ (중간 줄 전부 `^\{"seg":` 접두) ∧ (rc ∈ {0, 2}). 유효 → `exit $rc`. 그 외(1행째 `fallback …` · 파일 없음 · rc ∉ {0,2} · 출력 없음 · 표식 부재/수 불일치 · 접두 불일치) → stderr 1줄 `git-guard: parser fallback: <사유>`(exit 0 의 stderr 는 debug log 전용 · 관측용) → **폴백** = `read_fields()`(폴백 전용 유지) → 현행 `:106`+`:149` 분리 · `:167` `set -- $seg`(앞에 `set -f` · 뒤에 `set +f` · glob 확장 차단) · BRANCH = payload cwd(`:143`) · 현행 bash case 엔진(`:181-274`) **동결본**(문구 정정 외 무변경 · 새 argv 형태 미편입). 폴백 사유로 exit 2 를 내지 않는다.
- 원칙: **해석기가 `fallback` 을 내는 입력은 `bash -n` 도 거부하는 입력뿐**(짝 없는 인용 · 미종결 `$(` · 미종결 `(`). 미종결 heredoc 은 bash 가 경고만 내고 실행하므로 본문을 입력 끝까지로 보고 `parsed` 유지.

**결정 3 — tokenizer 규칙(python · 표준 라이브러리만 · shlex.split 미사용).**
- 상태기계: 홑따옴표 · 겹따옴표 · 백슬래시 · `$(`…`)` · `$((`…`))` · 백틱(불투명 토큰 · 내부 미해석 · **인용을 인식하는 중첩 괄호 계수** — `$(echo ")")` 의 `)` 는 인용 안이라 미계수) · 산술 `$((1<<2))` 안의 `<<` 는 heredoc 아님 · heredoc(`<<WORD` · `<<-WORD` · `<<'WORD'` · `<<"WORD"` · `cat<<EOF` 처럼 공백 없는 형태 포함; 다음 줄부터 WORD 단독 줄까지 본문 제외 · `<<-` 는 선행 탭 제거 뒤 비교 · **종결자 없으면 입력 끝까지 본문 · parsed 유지**) · `<<<` 는 다음 토큰 1개 소비.
- 인용 밖 연산자만 세그먼트 경계: `&&` `||` `;` `|` `|&` `&` 개행 `(` `)`. 인용 안 개행·연산자는 토큰 문자(여러 줄 `-m "제목\n\nCo-Authored-By: …"` 는 토큰 1개 · JSON 이스케이프로 레코드 1줄 유지).
- 리다이렉션(`>` `>>` `<` `2>&1` `&>` `[n]>` 꼴)은 대상 토큰과 함께 argv 에서 제거.
- 인용 제거 뒤 토큰 = argv. 앞머리 `VAR=x` · `sudo|command|nohup|time|env` 제거는 현행 `:169-174` 규칙을 python 으로 옮긴다(폴백 bash 쪽은 현행 유지).
- 해석 예외(짝 없는 인용 · 미종결 `$(`/`(` · 예상 밖 상태) → `fallback <사유>` 출력 · exit 0. 미종결 heredoc 은 예외가 아니다.
- 대상 checkout 해석: 현재 dir = payload cwd 로 시작. 세그먼트 `cd <d>`/`pushd <d>` 는 이후 세그먼트의 dir 갱신(상대경로는 이전 dir 기준 · `~/` 는 HOME 치환). git 세그먼트는 `-C <d>`(누적) · `--git-dir=<d>`/`--git-dir <d>` · `--work-tree=<d>`/`--work-tree <d>` 반영. 토큰에 미전개 `$VAR` · `$(…)` · 백틱 · `cd` 인자 없음/`cd -`/`popd` → 해석 불가 → payload cwd 유지(잔여 우회 · 머리말·README 에 문서화). `(`…`)` 서브셸 안 `cd` 도 이후에 적용(과대 근사 · 문서화).
- **branch 지연 평가(규칙 엔진 안 · 결정 2 에 따라 python)**: 레코드는 dir 만 담는다. `branch_of(dir)` = `git -C <dir> rev-parse --abbrev-ref HEAD`(`--git-dir` 형태는 `git --git-dir=<d> …`) · dict 캐시(dir 별 1회) · **push|merge|pull|branch 규칙에 진입한 세그먼트에서만 호출**. `git status`/`log`/`diff` · gh 세그먼트는 rev-parse 0회. 실패 시 빈 문자열(현행 `:143 || true` 와 같음 · 판정 불가 = 통과). 폴백 bash 엔진은 현행 `:143` 단일 BRANCH 유지.

**결정 4 — argv 형태 편입(기존 열거 ⑴–⑸ 의 다른 argv · 새 규칙 아님 · 머리말 `:11` 유지).**
- gh: 서브커맨드 앞 전역 플래그 건너뛰기 — `-R`/`--repo`/`--hostname` (값 1개) · `--repo=…`/`--hostname=…`. `pr merge` → ⑷. `gh api`: `-X <M>`/`--method <M>`/`--method=<M>` 가 `PUT`(대소문자 무관) 이고 첫 positional 이 정규식 `pulls/[0-9]+/merge/?(\?|$)` 에 맞으면 ⑷ 차단(후행 `/` · `?query` 포함). 그 외(`GET` 기본 · `-f` 만 · 다른 endpoint) 통과. `gh api graphql` 의 `mergePullRequest` mutation 은 머리말 잔여 우회 목록에 기재(완료 기준 밖).
- push: 묶은 short flag `^-[A-Za-z]+$` 에 `f` 포함 → force · `d` 포함 → deleting. 값을 갖는 옵션 `-o`/`--push-option`/`--receive-pack`/`--exec` 는 다음 토큰 소비(positional 오계수 방지). refspec 선행 `+` 는 제거하고 force=1. **`+` 제거 뒤** `HEAD`·`@`(단독 · refspec `src:dst` 의 src 와 dst 모두)를 세그먼트 branch 로 치환해 `is_main_ref` 판정 → develop 위 subagent `push origin HEAD` = ⑴-a · develop 위 `push origin +HEAD` = force + 보호 대상(⑵ · 누가 부르든).
- merge · push 무 refspec 규칙(현행 `:223`·`:234`·`:242`·`:257` 상당)의 `on_main`/`BRANCH` 는 세그먼트 branch(대상 checkout) 사용 → V2.
- `pull` 규칙 신설: 세그먼트 branch ∈ {main,master,develop,product} 이고 토큰에 `--no-ff` · `--no-rebase` · `--rebase=false` · `--ff=false` 중 하나 → deny(사유에 출구 `--ff-only`/`--rebase` 명기). 플래그 없는 `git pull` · `--rebase` · `--ff-only` 통과.
- 거부 문구 · 주석: python 엔진 · bash 폴백 엔진 양쪽에서 `:271` 「`git branch -D main|master`」 와 `:227`·`:231`·`:235`·`:239`·`:243` 「main/master」 를 「보호 브랜치(main · master · develop · product)」 형식으로 바꾼다. 같은 파일 주석의 「main/master」(`:13` · `:151` · `:229` · `:233` · `:237` · `:241` · `:248` · gate ① 재확인 실측 · 전체 12곳)도 같은 형식으로 정리한다 — 새 문구에 부분 문자열 「main/master」 가 남지 않아야 V7 grep 이 성립한다(파일 소유 PR 1 · C10 이관 없음).
- product 규칙(현행 `:223`·`:247`)은 그대로 · 세그먼트 branch 사용.

**결정 5 — 머리말(A5 병합).** `:71-72` 를 2단 규칙으로 교체: 「준비 실패(python3 부재 · envelope 이상 `:82-83`) = exit 2 차단(2026-09-09 계약) / envelope 통과 뒤 판정 불가(해석기 폴백 · branch 미해석 · `agent_id` 부재) = 통과. exit 1 은 Claude Code 규약상 비차단이나 이 hook 은 exit 1 을 내지 않는다」. `:88-90` 삭제. `:22-24` 허용 목록에 `pull`(플래그 없음·`--rebase`·`--ff-only`) · heredoc/인용 문자열 안 문구 · `gh api` GET 추가. 알려진 한계 `:74-76` 유지 + 「변수·명령치환 대상 dir 은 payload cwd」 · 「서브셸 `cd` 과대 근사」 · 「`gh api graphql` mergePullRequest 미검출」 · 「폴백 = `bash -n` 거부 입력 · 해석기 부재/크래시 · stderr `git-guard: parser fallback:`」 각 1줄.

**시험(먼저 작성 · RED 확인 뒤 구현).** 파일 = 새 `scripts/tests/test_git_guard.py`. 실행 게이트 = `agent-bridge`(`gates/run.sh:310` unittest 목록에 파일 추가 · 같은 커밋). bridge `guard()` 는 cwd 를 ROOT 로 고정(`scripts/agent-bridge.py:170`)하므로 hook 수준 시험은 hook 직접 호출(`test_harness_lifecycle_contract.py:340` 꼴 · `subprocess.run(['bash', ROOT/'.claude/hooks/git-guard.sh'], input=json.dumps(payload), capture_output=True)` · **`.claude/hooks` shim 경유 고정** · env 에서 `COLAB_HOOKS` 제거).
- fixture: `tempfile` 아래 공백 포함 경로(`co lab/repo`)에 git 저장소 · 브랜치 `develop`·`feature` 생성 · **메인 repo 는 `feature` checkout** · `git worktree add "<공백 경로>/dev co" develop` 로 두 번째 checkout(develop) · payload 는 guard_probe.py 형(`cwd` · `tool_name=Bash` · `tool_input.command` · subagent 는 `agent_id`·`agent_type`).
- 케이스(완료 기준 번호):
  - ⑴ **cwd=`dev co`(develop)** · `git -C "<dev co>" push --force origin develop` · `… branch -D develop` · subagent `… push origin develop` · subagent `… push origin main` · `… merge feature`(develop 위) · `… push origin product` · 홑따옴표 `-C '<dev co>'` 동형 → 2. 허용형(cwd=repo · feature 위): `push origin feature` · `merge --ff-only develop` · `pull --rebase` · `worktree add …` · `push origin --delete feature` → 0 **이고 `stderr == ''`**.
  - ⑵ cwd=repo(feature) · `git -C "<dev co>" merge feature` → 2 · `cd "<dev co>" && git merge feature` → 2 · subagent `cd "<dev co>" && git push` → 2 · 같은 명령 `-C "<repo>"` → 0. hook 수준 각 1건: `git --git-dir="<dev co>/.git" --work-tree="<dev co>" merge feature`(worktree 의 `.git` 파일 경로 · lane 이 `git rev-parse --git-dir` 로 실경로 확인) → 2 · `pushd "<dev co>" && git merge feature` → 2 · `( cd "<dev co>" && git merge feature )` → 2.
  - ⑶ develop 위 `cat > note.md <<'EOF'\ngit merge --no-ff x\ngh pr merge 1\ngit push --force origin develop\nEOF` → 0 · **종결자 없는 heredoc** `cat > note.md <<'EOF'\ngit push --force origin develop\n`(EOF 줄 없음) → 0 · `grep -E "git merge|gh pr merge" f` → 0 · `git commit -m "gh pr merge note; git push -f origin develop"` → 0 · `git commit -m "제목\n\nCo-Authored-By: X <x@y>"`(실제 개행 2개 포함 · `-m` 토큰 1개) → 0 · `python3 - <<EOF … EOF` 본문에 병합 문구 → 0. 미종결 heredoc 뒤 명령 `git -C "<dev co>" push -f origin develop <<EOF`(종결자 없음) → 2(폴백 아님 · parsed).
  - ⑷ `gh -R o/r pr merge 1` · `gh --repo o/r pr merge` · `gh api -X PUT repos/o/r/pulls/1/merge` · `gh api --method put …/merge/` · `… /merge?x=1` → 2 · `gh api repos/o/r/pulls/1/merge` · `gh api -X GET …/merge` → 0. develop 위 `push -fu origin develop` · `push -uf origin develop` → 2 · subagent develop 위 `push origin HEAD` · `push origin @` · `push origin HEAD:develop` → 2 · 메인 develop 위 `push origin HEAD` → 0(⑴ 은 subagent 한정) · 메인 develop 위 `push origin +HEAD` → 2(force). develop 위 `pull --no-ff origin develop` · `pull --no-rebase` · `pull --rebase=false` · `pull --ff=false` → 2 · `pull` · `pull --ff-only` · `pull --rebase` → 0 · feature 위 `pull --no-ff` → 0.
  - ⑸ 폴백 입력: 짝 없는 인용 `git push --force origin develop "x` → 2(현행 동일) · `echo "unterminated` → 0 · 미종결 `$(` → 현행 결과. **fallback fixture 마다 `subprocess.run(['bash','-n'], input=cmd)` rc≠0 단언**(미종결 heredoc 은 rc 0 이므로 fallback fixture 가 될 수 없음이 시험으로 드러남). 결함 주입(env seam 없음): `scripts/harness/hooks/`(필요하면 `scripts/harness` 전체) 와 `.claude/hooks/` 를 tempdir 로 복사(선례 `test_task_runtime.py:404-410` 의 setUp) 하고 복사본의 `git_guard_parse.py` 를 (a) 삭제 (b) `exit 3` 스텁 (c) `parsed` 1행만 내는 스텁 (d) `parsed` + 레코드 1개 뒤 exit 3 (e) `parsed` + 필드 틀린 레코드(`{"x":1}`) + 정상 표식 (f) 레코드 정상 + 종료 표식 없음 으로 바꿔 복사본 `.claude/hooks/git-guard.sh` 를 직접 호출 → `git push --force origin develop` → 2 · `git status` → 0 · stderr 에 「hook readiness failure」 없음 · (a)–(f) 각 stderr 에 `git-guard: parser fallback:` 1줄((e) 는 deny 또는 폴백 허용 · crash 0). 복사가 validate-input 의존(`lifecycle_contract.py` 동거 · 함께 복사됨)으로 깨지면 lane 은 차선(복사 범위 확장)을 적용하고 결과를 보고(구현 전 정지 아님).
  - 해석기 단위 시험(import): heredoc 본문 제외 · 미종결 heredoc = 끝까지 본문 · 인용 안 `|`·`;`·개행 비분리 · 리다이렉션 제거 · `-C` 누적 · `cd` 상대경로 · `$VAR` 미해석 → cwd · `$(echo ")")` 불투명 토큰 1개 · `$((1<<2))` 는 heredoc 아님 · `cat<<EOF` heredoc 인식 · 레코드 JSON lines(개행 포함 `-m` 이 1줄) · 종료 표식 수 일치 · rev-parse 호출 수: `subprocess.run` monkeypatch 로 `git status` · `git log --oneline -5` · `gh pr view` → 0회 · `git push` → dir 당 1회.
  - **실사용 corpus 시험**(`set -u` unbound = exit 1 = fail-open 방지): `git status` · `git log --oneline -5` · heredoc 커밋(`git commit -F - <<'EOF' … EOF`) · `gh pr view 1` · `git diff --stat` → rc 0 · `stderr == ''`.
  - bash 문법 검사: `bash -n scripts/harness/hooks/git-guard.sh` rc=0(문법 오류 = bash exit 2 = 전 Bash 정지 → 시험으로 고정).
  - 기존 시험 무변경 green: `test_agent_bridge.py:461`(`.codex/hooks.json` 명령 · cwd=ROOT/scripts) · `:479-507`(`guard-command`) · `test_harness_lifecycle_contract.py:319-349`.

### 4.2 A2 (PR 1 = ⓒ 문서만 · 코드 0 · ⓐ 는 PR 2)
- `.agents/skills/design-review/SKILL.md:101` 현재: 「`fix` 레인은 `COLAB_FIX_LANE=1` 로 돈다 — … 편집을 막는다보호된 fix 구현 단계에서 `COLAB_ALLOW_TEST_EDIT=1`로 우회하지 않는다.」 → 두 문장으로 분리하고 내용을 「편집 시점 차단은 Codex 경로에만 있다(`COLAB_FIX_LANE=1` 은 `scripts/agent-bridge.py:278` tool_environment · `scripts/dev.ps1` 이 넘기는 env · Claude Code 는 hook env 를 lane 별로 줄 수 없어 `test-file-guard` 가 통과). Claude lane 의 경계는 `begin --role lane-worker --scope <glob>` 의 handoff/H7 대조(인계 시점 · `docs/development/lifecycle-evidence.md` 「인계」)다. / `COLAB_ALLOW_TEST_EDIT=1` 은 Codex 보호 단계에서 켜지 않는다.」
- `:106` 「`COLAB_FIX_LANE=1`인 구현 단계에서」 → 「구현 단계(Codex = `COLAB_FIX_LANE=1` env · Claude = 편집 시점 차단 없음 · `--scope` 인계 대조)에서」. 시험 작성이 같은 task 인 Claude lane 은 scope 에 시험 경로가 들어 인계 대조가 시험 편집을 구분하지 못한다는 한계 1문장(편집 시점 차단은 PR 2 A2 ⓐ). task 2개 분할(ⓒ′)은 적지 않는다(기각 · `lifecycle_contract.py:312-315` red 잔존 인계 거절).
- `docs/development/dual-agent.md:59-60` 같은 취지로 교정(「`COLAB_FIX_LANE=1`의 구현 단계로 진행한다」 → Codex/Claude 분기).
- 완료 grep: `grep -n 'COLAB_FIX_LANE=1' .agents/skills/design-review/SKILL.md` 결과 줄마다 Codex 또는 env 어휘 동반.

### 4.3 A3 경계 표기 (코드 0)
- `README.md:115-117` blockquote 에 추가: 「`migration-guard`·`decision-number-guard`·`test-file-guard` 는 Edit/Write 도구만 본다(`.claude/settings.json` PreToolUse `Edit|Write` `:69`·`:88`). `sed -i` · 리다이렉션 · `tee` · `python -c` 등 Bash 쓰기는 대상이 아니다. Bash 쓰기까지 잡는 사후 검사 = `begin --scope` 를 선언한 task 의 handoff/H7(baseline = begin 시점 전 파일 내용 hash · 도구 무관)」. 정본 링크 `docs/development/lifecycle-evidence.md` 「인계」.
- `test-file-guard.sh` 머리말(`:3-27` 블록)에 같은 문장 + A5 2단 규칙. 머리말은 A1 이후 동작 기준으로 A1 커밋 뒤에 쓴다.
- migration·결정 번호의 Bash 편집 사후 검사 「있음/없음」: lane 이 확인해 README 문장에 기입 — 후보 = `work-item-consistency`(결정 번호 중복 · `gates/tools/work_item_consistency.py:136`) · `migration-single-head`. 확인 전에는 「scope handoff」만 적는다. migration-guard 머리말 문장은 C10(PR 3).

### 4.4 A4 `gates/run.sh` 인자 검사
- 위치: `:9` `GATE="${1:-}"` 직후 · `:26-30`(`task` 분기) · `:36-41`(gate-start 증거 기록) · `:170`(host mutex `gate_host_mutex_acquire`) 보다 앞. 알려진 gate 목록 = `:284-305` `ALL_GATES=(…)` 정적 배열을 `:9` 뒤로 이동(사용처 `:705`·`:820`·`:830`·`:896`·`:919`·`:966` 전부 뒤 · 의존 없음). **KNOWN 기준 = `ALL_GATES` 유지(Ted 판정)** + `case` 라벨 중 `ALL_GATES`∪{`all`,`task`} 밖 이름이 있으면 `KNOWN_GATES=("${ALL_GATES[@]}" …)` 로 합치고 보고(`all` 실행 집합은 바꾸지 않음). 교차 점검 실측: `service-tests-*` 4종 · `stage2-markers(-selftest)` 는 `ALL_GATES` 안 · `:649` 는 literal 대안 라벨(`a|b|c|d`) · glob 라벨 없음.
- 규칙: 인자 0 또는 빈 `$1` → 78 · `GATE=all` 은 `$# == 1` 또는 (`$# == 3` · `$2 == -j` · `$3 =~ ^[1-9][0-9]*$`) 만 허용(`all -j` 인자 2개 = 78 · 기존 `jobs_n=2` 기본 동작 변화) · `GATE=task` 는 `$# == 1` · 단독 gate 는 `$# == 1` 이고 KNOWN 안. 위반 시 stderr `::gate-readiness-failure:: <사유> · dropped=<버린 토큰들> · usage: gates/run.sh <gate> | all [-j N] | task` · exit 78 · `all -j4` 꼴은 사유에 `-j 4` 형태 안내.
- `:794-796` 의 `-j` 읽기는 유지(검사 통과 뒤라 항상 유효). `:972-973` · `:975-977` 두 case 는 도달 불가가 되므로 exit 2 → 78 로 바꾸고 방어용으로 남긴다(2 잔존 0).
- 영향 조사(grep 결과): `gates/tools/gate-host-mutex-selftest.sh:97` `bash "$RUN" "$g"` 단일 인자 → 무영향. `scripts/harness/hooks/lifecycle_contract.py:472` `['bash', run.sh, gate]` → 무영향. `scripts/tests` 의 `run.sh` 참조는 전부 fixture 치환(`test_harness_lifecycle_contract.py:354` · `test_task_runtime.py:84,370` · `test_harness_work_state.py:55` · `test_ci_schema_setup.py:34`) 또는 텍스트 대조(`test_harness_record_gates.py:110-116` `adr-records)` 라벨 · `:285` ci.yml 문자열) → case 라벨·ci.yml 무변경이면 무영향. `returncode == 2` 기대는 hook 시험뿐. `.github/workflows/ci.yml` 의 `run.sh` 호출 전부 단일 인자(`:33`–`:795` 27곳 · `agent-bridge.yml:61-62` 2곳 · 재열람) → 무영향. `gates/README.md:78` 「`all [-j N]`」 일치 · 같은 자리에 「인자 오류 · `all -j` 형식 오류 = 78(기존 동작 변화)」 1줄 추가.
- 시험(먼저): 새 `scripts/tests/test_gates_run_args.py` · `agent-bridge` 목록(`:310`) 등록. `subprocess.run(['bash', ROOT/'gates/run.sh', *args], env={…, 'TMPDIR': <빈 임시 dir>})`. 케이스: `agent-bridge extra` · `all -j4` · `all -j` · `all -j 4 x` · `all -j abc` · `all -j 0` · `task x` · `no-such-gate` · 인자 없음 · 빈 문자열 → rc 78 · stderr 에 버린 토큰/이름 · stdout+stderr 에 `::gate-waiting::` 0 · `<TMPDIR>/colab-v2-gate-host-mutex` 미생성 · `COLAB_TASK_ID` 를 준 `task x` 에서도 gate-start 미실행(runtime 디렉터리 무변화). 무변경 확인: `task`(COLAB_TASK_ID 없음) → 기존 `:27` 메시지 · 78. **KNOWN 전수 시험 1건**: `run.sh` 본문에서 `case "$GATE" in` 블록의 라벨(`^  [a-z0-9-]+(\|[a-z0-9-]+)*\)` · `|` 분할)을 추출해 각각 ∈ `ALL_GATES`∪`KNOWN_GATES`∪{`all`,`task`} 단언(`ALL_GATES` 는 같은 파일에서 파싱). `all -j N` 정상 경로는 unit test 밖 → CI/`gates/run.sh all -j 2` 실행 1회로 확인(§7 V12).

### 4.5 A5 머리말 2단 규칙 · 도달 불가 줄
- `git-guard.sh:71-72` · `:88-90` → §4.1 결정 5(A1 커밋 안). `test-file-guard.sh:27` 교체 · `:42` 삭제(A2/A3 커밋 안). `:28` · `git-guard.sh:3-4` 「Effective 2026-09-09」 줄 유지.
- 동작 변화 0 증명 = `test_harness_lifecycle_contract.py:319-327` 기존 시험(4 hook × `{broken`/`{}`/Read).
- migration-guard · worktree-setup 머리말은 C10(PR 3)(decision-number-guard 는 A6 · worktree-setup 의 SubagentStart 인용 부분만 A7) — PR 1 커밋 메시지에 「나머지는 PR 3」 명기.

### 4.6 A6 decision-number-guard 기준 · 실패 방향 (Ted 판정 2026-09-26 「페이블 권고대로 젖부」로 C5/C10 에서 PR 1 이관 · 단독 커밋 · spec gate ① 로 readiness 범위 축소)
- 파일: `scripts/harness/hooks/decision-number-guard.sh` — `:8` · `:18` · `:63-66` 주석 `origin/main` · `:27` exit 1 문장 · `:38` 도달 불가 줄 · `:56-57`(도구·경로 선별 · 이미 있음) · `:63-73` 기준선(`:66-67` `origin/main:` · `:69-72` 워킹트리 폴백 · `:73` `[ -n "$BASE" ] || exit 0`) · `:75-` python 판정.
- 변경: 기준 = `origin/develop:dev-package/PLAN-SoT.md`. `:73` exit 0 삭제 · BASE 가 비어도 python 판정(1회 호출 유지)에 넘긴다. **준비 실패(exit 2)는 경로·내용 선별 뒤 `dev-package/PLAN-SoT.md` 편집의 새 내용에 새 결정 번호 후보(기존 원장에 없는 `〈N〉` 행)가 있을 때만**: python 이 후보 0건이면 exit 0(BASE 불요) · 후보 있고 BASE 비어 있으면 stderr 「hook readiness failure: origin/develop 부재 · `git fetch origin develop` 뒤 재시도」 exit 2(migration-guard.sh:72-74 와 같은 방향). 워킹트리 `max-decision.sh` 폴백(`:69-72`) 삭제(조용한 대체 경로 제거). `:27` 2단 규칙 · `:38` 삭제. `README.md:75` `origin/main` → `origin/develop`(C2 Fable 「C5 와 같은 PR 에서만」). CI 무영향(ci.yml 에 이 hook 참조 0 · 시험은 temp repo fixture).
- 시험: `test_harness_lifecycle_contract.py:366-380`(`test_codex_decision_content_hits_shared_judge…`) fixture 에 `git update-ref refs/remotes/origin/develop HEAD` 추가(원장 커밋 뒤) · 새 케이스 「ref 부재 fixture: Read → 0 · PLAN-SoT 비결정 편집(번호 없는 행 추가) → 0 · 새 결정 번호 편집 → 2 + stderr readiness」 · `test_agent_bridge.py:117-121` 등 decision 관련 시험 재확인(fixture 에 ref 필요하면 편집 → scope 조건부 선언). `test_raw_ledger_requires_content…`(`:381-396`) 는 validate-input 단계라 무영향.

### 4.7 A7 SubagentStart hook 출력 additionalContext JSON (Ted 판정 3라운드 · 커밋 ⑤)
- 대상: `scripts/harness/hooks/researcher-task.sh`(출력 `:40` · `:51` · `:69-75`) · `scripts/harness/hooks/worktree-setup.sh`(출력 `:69-76` · `:245-267`). 훅 정의(`.claude/settings.json:18-33` SubagentStart lane-worker/researcher · `.codex/hooks.json:17-30`) 무변경.
- 형태: 기존 평문을 버퍼(함수 stdout 을 `OUT="$(…)"` 로 수집 · 안쪽 `exit 0` 은 서브셸 종료라 무해)에 모은 뒤 마지막에 `printf '%s' "$OUT" | python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"SubagentStart","additionalContext":sys.stdin.read()}}, ensure_ascii=False))'` 1줄 · exit 0 유지. 출력할 내용이 없으면(비-researcher `researcher-task.sh:43` · `COLAB_HOOKS=0`) 현행대로 빈 stdout. python3 부재: `researcher-task.sh:55` fail 경로 · `worktree-setup.sh:52-62` hook_field 와 같이 평문 그대로(현행 동작 · 도달 0 · debug log).
- worktree-setup 권고 문구(차단 아님): `git -C "$CWD" rev-parse --show-toplevel` == `git -C "$CLAUDE_PROJECT_DIR" rev-parse --show-toplevel` 이면 additionalContext 에 「⚠ 격리 아님 — payload cwd 의 toplevel 이 세션 checkout(`$CLAUDE_PROJECT_DIR`)과 같다. 구현하지 말고 오케스트레이터에 보고」 1줄. bridge 는 별도로 lane 안내 문장을 덧붙인다(`agent-bridge.py:347-349` · 무변경).
- Codex 호환: bridge `hook_context()`(`agent-bridge.py:300-302`)가 hook 이 낸 `hookSpecificOutput` JSON 의 본문만 재적재(`dual-agent.md:77` · `test_agent_bridge.py:163-176` 기존 시험) → Codex 경로 무영향 · `test_task_runtime.py:549-560` bridge 경유 시험 green 유지.
- 주석·문서 정정: `researcher-task.sh:14` 「stdout 은 평문으로 subagent 맥락에 실린다」 · `worktree-setup.sh:40-42` · `bootstrap-diet.sh:23-26`(SubagentStart 평문 인용 부분 — SessionStart 평문 도달은 사실이므로 SubagentStart 만 「additionalContext JSON 필요」로) · `docs/development/dual-agent.md:78-80` 「평문으로 싣는다(Codex는 additionalContext)」 → 「양쪽 다 `hookSpecificOutput.additionalContext` JSON 1줄」 · `README.md:72` worktree-setup 행에 「출력 = additionalContext JSON · 같은 checkout 이면 격리 아님 권고」(researcher-task 행은 README 표에 없음 → 행 추가는 C2 · PR 3).
- 시험(`scripts/tests/test_task_runtime.py` · agent-bridge 목록 `:310`): `printed()`(`:431-434` · 이를 쓰는 `:461-465` 포함) · `:515-518` · `:538-539` 의 stdout 평문 단언을 `json.loads(stdout)['hookSpecificOutput']['additionalContext']` 파싱 뒤 같은 정규식/`assertIn` 으로 · `hookEventName == 'SubagentStart'` · stdout 이 정확히 1줄 단언 · `:522`·`:529`(빈 출력) 유지. worktree-setup 출력 형태 시험 신설(같은 fixture 클래스 · `gates/run.sh` 부재 checkout 이라 `:74` 건너뜀 경로 → 그래도 JSON 1줄 · `CLAUDE_PROJECT_DIR`=cwd 일 때 「격리 아님」 문구 포함 · 다른 toplevel 이면 미포함).
- 완료 기준: 단위 시험 green + 병합 · pull 뒤 오케스트레이터가 researcher 1회 스폰해 첫 턴에 task id 노출 관측(lane 은 `${CLAUDE_PROJECT_DIR}` 쪽 hook 을 쓰므로 자기 hook 을 라이브로 못 씀 · PR 본문 「남은 제약」). 미존중 관측 시 대안 = 오케스트레이터가 researcher 지시문에 begin/task id 직접 명시(현행 임시 운용 유지). 「열린 자동 task 조회·재사용」 · 자동 begin 존폐는 PR 2(L 그룹).

### 4.8 C12 css-edit-audit PostToolUse 출력 JSON (커밋 ⑥ · A7 과 분리 = 되돌림 단위)
- `scripts/harness/hooks/css-edit-audit.sh:74` `echo "$OUT"` → `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"<OUT>"}}` 1줄(python3 는 `:30` 이후 항상 있음 · json.dumps) · exit 0 유지 · 머리말 `:21` 「PostToolUse 의 stdout 은 맥락으로 실려 들어간다」 → 「PostToolUse 평문 stdout 은 debug log 전용 · 맥락은 `hookSpecificOutput.additionalContext` JSON」.
- 시험: `test_agent_bridge.py:160-176`(bridge 경유 · `hook_context` 재적재) green 유지 + hook 직접 호출 시험 1건(`.css` 편집 payload → stdout JSON 1줄 · `hookEventName == 'PostToolUse'` · 비-css → 빈 stdout).

## 5. 시험 결정 (요약)
- 순서: 시험 파일 작성 → `gates/run.sh agent-bridge` RED(공백 `-C` 0 · heredoc 2 · run.sh 인자 0/2 · A6 ref 부재 0 · A7/C12 평문) 기록 → 구현 → GREEN. red→green 로그를 PR 「검증」에 인용.
- 재사용 seam: hook 직접 호출(`test_harness_lifecycle_contract.py:340` · `test_task_runtime.py:404-422` tempdir 복사 fixture) · bridge `guard-command`(`test_agent_bridge.py:479`). 신설 seam: `git_guard_parse.py` import 단위 시험 · hook 폴더 tempdir 복사본 결함 주입(env seam 없음).
- 단독 게이트: `agent-bridge`(새 시험 2파일 + `test_task_runtime.py`·`test_harness_lifecycle_contract.py`·`test_agent_bridge.py` 변경 포함) · `harness-contract`(README·문서·hook wiring) · `intent-ref`(트레일러) · `exec-bit`(새 `.py` 비트).
- green-by-skip 방지 · 시험 수 기준값: 현재 agent-bridge unittest 156(재확인). 커밋 ① 뒤 수를 기록해 기준값으로 두고, ③ 의 `test_gates_run_args.py` 증가분 · ④·⑤·⑥ 증가분을 따로 적는다(등록 누락 시 수가 늘지 않음이 드러난다).

## 6. 위험 · 롤백
- fail-closed 면: git-guard 는 모든 Bash 호출을 거친다(`.claude/settings.json:58-66`). bash 문법 오류 = exit 2 = 전 세션 Bash 정지 → `bash -n` 시험 · 해석기 예외/부재/절단은 폴백(stderr 관측 1줄). `set -u`(`:77`) 아래 새 루프의 unbound 변수 = exit 1 = fail-open + stderr 노출(`bash -n` 이 못 잡음) → 허용형·corpus 시험의 `stderr == ''` 단언으로 고정. A1+A5 는 단독 커밋(되돌림 단위 = `git revert <A1 sha>`). 정지 시 복구 = Edit 도구로 `git-guard.sh` 되돌림(Edit/Write 는 matcher 밖) 또는 `COLAB_HOOKS=0` 세션 재시작(`README.md:79-98`).
- hook 은 `${CLAUDE_PROJECT_DIR}` 쪽 스크립트를 실행(`worktree-setup.sh:31-38` 문서 인용) → lane 자신의 Bash 는 메인 checkout 의 구버전 guard 가 판정 · lane 은 A7 hook 출력도 라이브로 못 본다. lane 검증은 worktree 스크립트 직접 호출(§7). 메인 checkout 은 PR 1 병합 · pull 뒤에 새 guard·hook 을 얻는다 — 그 시점에 오케스트레이터가 `git status` · `git push origin <기능>` 통과 확인 + researcher 1회 스폰(A7 관측).
- 규칙 엔진 2벌(python 주 · bash 폴백 동결본): 폴백은 `bash -n` 거부 입력과 해석기 부재/크래시에만 발동 · 새 argv 형태는 python 에만 있음 → 머리말에 명기 · 폴백 발동은 stderr 로 관측.
- 해석기 잔여 우회(변수·명령치환 dir · 서브셸 cd 과대 근사 · `bash -c`/`eval` · `gh api graphql` mergePullRequest)는 머리말·README 에 적고 완료 기준에 넣지 않는다.
- A4 78 은 PR 2 B3 집계와 만나면 선언 오타 1건이 전체 78 → B3 시험에 이 경우 포함(묶음 메모 이관). `all -j`(인자 2개) 사용자는 78 을 본다(gates/README 1줄).
- A6: origin/develop 없는 checkout 에서 결정 번호 편집만 차단 · 그 외 편집 무영향(readiness 조건부).
- A7: SubagentStart 의 additionalContext 존중 여부는 문서 미확정 → 완료 기준을 스모크에 둠 · 미존중 시 대안(§4.7) · C12 는 문서화된 채널이라 커밋 분리.
- 시험 fixture 의 공백 경로가 `tempfile` 기본 경로에서 만들어지지 않는 환경(TMPDIR 제한) → 준비 실패 78 로 드러남(skip 금지).

## 7. 검증표
| V | 무엇 | 명령(worktree 루트) | 기대 | 완료 기준 |
|---|---|---|---|---|
| V1–V5 | git-guard 새 시험 | `COLAB_TASK_ID=<id> bash gates/run.sh agent-bridge` | green · 시험 수 156+신규(커밋별 증가분 기록) | A1 ⑴–⑸ |
| V6a | 기존 시험 | 같은 실행 안 `test_agent_bridge.py` · `test_harness_lifecycle_contract.py` | green · skip 수 10 무변화 | A1 ⑹ |
| V6b | 재현 명령 재실행 | guard_probe.py 를 저장소 밖 임시 사본으로 복사 · `HOOK` 을 `<worktree>/.claude/hooks/git-guard.sh` · `ROOT` 를 worktree 로 바꿔 실행 + pull 2종(`git -C "<wt>" pull --no-ff origin develop` · `pull --no-rebase …` · cwd 는 develop checkout) | 공백 `-C` 4종 · 무 `-C` 4종 · `-C /tmp` 1종 · pull 2종 전부 rc=2 · stderr 「⛔ 차단(H3 git-guard)」 | A1 ⑹ |
| V6c | 허용형 재실행 | 같은 probe 에 feature checkout cwd · `push origin feature` · `merge --ff-only develop` · `pull --rebase` · `pull` · `worktree list` · `gh api repos/o/r/pulls/1/merge` | rc=0 · stderr 빈 줄 | A1 ⑴⑷ |
| V6d | heredoc 오탐 | probe 에 §4.1 ⑶ 6종(develop cwd · 미종결 heredoc · 여러 줄 `-m` 포함) | rc=0 | A1 ⑶ |
| V5b | 결함 주입 | `test_git_guard.py` ⑸ (a)–(f)(tempdir 복사본) · 수동: 복사본에서 `git_guard_parse.py` 삭제 뒤 V6b 의 무 `-C` 4종 | rc=2(현행 규칙) · `git status` rc=0 · stderr `git-guard: parser fallback:` 1줄 | A1 ⑸ |
| V7 | README·머리말 | `grep -n 'pull' README.md scripts/harness/hooks/git-guard.sh` · `grep -nF 'D main|master\`' scripts/harness/hooks/git-guard.sh` · `grep -n 'main/master' scripts/harness/hooks/git-guard.sh` | :73 행·:22-24 목록에 pull/gh/heredoc 명시 · 옛 문구 0건 · 「main/master」 0건(새 문구는 「보호 브랜치(main · master · develop · product)」 형식이라 부분 문자열 미매치 · 확인용 `grep -c '보호 브랜치(main · master · develop · product)'` ≥ 6) | A1 ⑺ |
| V8 | A2 문서 | `grep -n 'COLAB_FIX_LANE=1' .agents/skills/design-review/SKILL.md docs/development/dual-agent.md` · `grep -c '막는다보호된' …SKILL.md` | 각 줄 Codex/env 동반 · 융합 문장 0 | A2 ⓒ |
| V9 | A3 경계 | `grep -n 'Bash 쓰기' README.md scripts/harness/hooks/test-file-guard.sh` · `bash gates/run.sh harness-contract` | 각 1건 이상 · green | A3 |
| V10 | run.sh 인자 시험 | agent-bridge 실행(`test_gates_run_args.py` 포함) · 수동: `TMPDIR=$(mktemp -d) bash gates/run.sh all -j4` | rc 78 · stderr 에 `-j4` · `$TMPDIR/colab-v2-gate-host-mutex` 없음 | A4 ⑴⑵ |
| V11 | 알 수 없는 gate | `TMPDIR=<빈 dir> bash gates/run.sh no-such-gate` · 인자 없음 | 78 · `::gate-waiting::` 0 · mutex dir 없음 | A4 ⑵ |
| V12 | 무변경 · KNOWN | `bash gates/run.sh harness-contract`(단독) · `bash gates/run.sh all -j 2` 1회(lane 은 호스트 단독 시점에) · `COLAB_TASK_ID=<id> bash gates/run.sh task` · KNOWN 전수 unit | 현행과 같은 종료코드·요약 · unit green | A4 ⑶ |
| V13 | A5 | `grep -n 'exit 1 은 통과' scripts/harness/hooks/git-guard.sh scripts/harness/hooks/test-file-guard.sh` · `grep -n 'command -v python3 .*exit 0' 같은 두 파일` | 0건 · 0건 · `test_raw_guard_malformed…` green | A5 |
| V14 | (A6) | agent-bridge · `grep -n 'origin/main' scripts/harness/hooks/decision-number-guard.sh` · `README.md` 의 decision-number-guard 행 확인 | ref 부재 fixture 3케이스(Read 0 · 비결정 0 · 결정 번호 2) green · guard 0건 · README decision-number-guard 행 = `origin/develop`(`README.md` migration-guard 행의 `origin/main` 은 PR 3 · C2 몫이라 제외 — 2026-09-26 정정 · 레인 통지) | C5 이관 |
| V15 | 문법·비트 | `bash -n scripts/harness/hooks/git-guard.sh` · `bash -n gates/run.sh` · `bash -n scripts/harness/hooks/decision-number-guard.sh` · `bash gates/run.sh exec-bit` · `bash gates/run.sh intent-ref` | 전부 0 | 공통 |
| V16 | (A7) | agent-bridge(`test_task_runtime.py` JSON 단언 · worktree-setup 형태 시험) · 수동: `printf '%s' '{"cwd":"<wt>","hook_event_name":"SubagentStart","agent_type":"researcher","agent_id":"x"}' \| bash .claude/hooks/researcher-task.sh \| python3 -c 'import json,sys; print(json.load(sys.stdin)["hookSpecificOutput"]["hookEventName"])'` · 주석 정정 확인은 grep 이 아니라 diff 로 — `bootstrap-diet.sh:23-26` · `worktree-setup.sh:40-42` 에는 「평문」 단어가 없어(gate ① 재확인 실측) grep 0건이 증거가 되지 못한다 · 확인 = PR diff 에 해당 줄 변경이 있고 `grep -n 'SubagentStart' scripts/harness/hooks/bootstrap-diet.sh scripts/harness/hooks/worktree-setup.sh` 결과 줄이 additionalContext JSON 을 전제 | green · `SubagentStart` · 평문 도달 전제 문장 0건(diff 확인) | A7 |
| V17 | (C12) | agent-bridge(`test_agent_bridge.py:160-176` + 직접 호출 시험) · `grep -n '맥락으로 실려' scripts/harness/hooks/css-edit-audit.sh` | green · 0건 | C12 ⓑ |

## 8. 레인 지시 (PR 1 · lane-worker 1개)
- 스폰: `Agent(subagent_type: "lane-worker", isolation: "worktree")` 명시(Workflow `agent()` 가 부모 worktree 에서 돈 관측 1회). 기준 = 현재 checkout HEAD(`.claude/settings.json:4` `baseRef: "head"` · 브랜치 `claude/harness-improvement` · intent·spec 커밋 포함). lane 첫 행동: `git merge-base --is-ancestor <spec 커밋> HEAD` 확인 · 부모 checkout 경로에서 돌고 있으면 구현 전 정지·보고.
- SubagentStart hook 출력(worktree-setup 요약)은 지금 레인에 안 보인다(A7 전) — venv/npm 준비 상태는 `ls services/*/.venv frontend/node_modules` 로 직접 확인.
- A7 주석 정정: `bootstrap-diet.sh:23-26` · `worktree-setup.sh:40-42` 의 「SubagentStart 도 평문이 맥락에 들어간다」 취지 주석에는 「평문」 단어가 없다 — 내용으로 찾아 고치고, 확인은 diff 로 한다(grep 0건은 증거 아님).
- 증거 시작(worktree 루트): `python3 scripts/agent-bridge.py lifecycle begin --role lane-worker --gate agent-bridge --gate harness-contract --gate intent-ref --gate exec-bit --scope 'scripts/harness/hooks/git-guard.sh' --scope 'scripts/harness/hooks/git_guard_parse.py' --scope 'scripts/harness/hooks/test-file-guard.sh' --scope 'scripts/harness/hooks/decision-number-guard.sh' --scope 'scripts/harness/hooks/researcher-task.sh' --scope 'scripts/harness/hooks/worktree-setup.sh' --scope 'scripts/harness/hooks/bootstrap-diet.sh' --scope 'scripts/harness/hooks/css-edit-audit.sh' --scope 'scripts/tests/test_git_guard.py' --scope 'scripts/tests/test_gates_run_args.py' --scope 'scripts/tests/test_harness_lifecycle_contract.py' --scope 'scripts/tests/test_task_runtime.py' --scope 'scripts/tests/test_agent_bridge.py' --scope 'gates/run.sh' --scope 'gates/README.md' --scope 'README.md' --scope '.agents/skills/design-review/SKILL.md' --scope 'docs/development/dual-agent.md'`(`test_agent_bridge.py` 는 A6 fixture·C12 시험 필요 시 사용 · 안 건드려도 무방). `docs/development/lifecycle-evidence.md` · `dev-package/reports/**` 는 기본 허용.
- `harness-contract-selftest` 미선언: 그 목록(`run.sh:316` `test_harness_config/evidence/pr_contract/work_state/record_gates`)의 대상 파일을 PR 1 이 바꾸지 않는다. `gate-host-mutex-selftest` 는 run.sh 단일 gate 경로 확인용으로 unbound 1회 실행(선택 · serial).
- 게이트 실행은 `COLAB_TASK_ID=<id> bash gates/run.sh task` 1회(선언 집합) · 호스트 단독 · 병렬 lane 없음.
- 커밋 단위(각각 `Intent-Ref:` 트레일러 · Co-Authored-By/Claude-Session 트레일러): ① A1+A5(git-guard) — `git-guard.sh` · `git_guard_parse.py` · `test_git_guard.py` · `run.sh:310` 등록 · `README.md:73` 행 → 시험 수 기준값 기록 ② A2+A3+A5(test-file-guard) — `test-file-guard.sh` · `README.md:115-117` · `SKILL.md:101,106` · `dual-agent.md:59-60` ③ A4 — `run.sh` · `test_gates_run_args.py` · `run.sh:310` 등록 · `gates/README.md:78` → ① 대비 증가분 기록 ④ A6 — `decision-number-guard.sh` · `test_harness_lifecycle_contract.py` · `README.md:75` ⑤ A7 — `researcher-task.sh` · `worktree-setup.sh` · `bootstrap-diet.sh`(주석) · `test_task_runtime.py` · `dual-agent.md:78-80` · `README.md:72` ⑥ C12 — `css-edit-audit.sh` · 시험. 사용자 승인 없는 push 금지 · 병합·PR 게시는 Ted.
- 인계: `lifecycle handoff --task <id> --mode complete --summary '<red→green 계수 · V 표 결과>'` · `COLAB_HANDOFF` 줄과 `WORKTREE=<경로> BRANCH=<브랜치>` 를 최종 메시지에.

## 9. PR 1 본문 계획 (`scripts/harness/pr_contract.py` 형식 · `.github/pull_request_template.md`)
- 본문 파일 위치: 저장소 밖 `~/.claude/pr-bodies/PR-BODY-harness-improvement-pr1.md`(Ted 관행). 검증: `python3 scripts/harness/pr_contract.py <본문> --head <40자 SHA> --mode draft` → 0.
- 첫 줄: 「하네스 개선 PR 1 — git-guard 가 명령 형태와 무관하게 막고 run.sh 인자 오류가 78 로 드러나며 SubagentStart/PostToolUse hook 출력이 모델에 도달한다」.
- `Plan-Ref: dev-package/prd/specs/S-HARNESS-IMPROVEMENT-20260925.md` · `Head-SHA: <게시 시 갱신>` · `검증 상태: 미검증` → PR 1 의 새 시험은 `.github/workflows/agent-bridge.yml:64` `python -m unittest discover -s scripts/tests -v`(경로 필터 `:5-29` · 필수 check 아님)로 CI 에서도 돈다 → agent-bridge workflow green 뒤 「검증됨(CI agent-bridge 비필수 + lane 로컬 로그)」로 갱신 · 로컬 red→green 로그 경로 병기. 게이트 단위 `gates/run.sh agent-bridge` 의 CI 편입은 B4(PR 2).
- 목적: intent 그룹 A 원한 결과(V1–V17). 범위: §8 커밋 ①–⑥ 파일 · 제외 = A2 ⓐ(PR 2) · C10 나머지 hook 머리말 · README 훅 표 재작성(C2) · 훅 정의 무변경. 계획: phase 1 완료 · phase 2/3 stub 대기. 결정: 새 ADR 없음(A4 2→78 은 AGENTS.md 정의 적용 · B3 ADR 은 PR 2). 검증: §7 V 표를 「원한 결과 ↔ 실제 ↔ 근거 ↔ 가치 상태」 행으로 · 3계수 · 커밋별 시험 수 · red→green 로그 경로. 남은 제약: 메인 checkout 은 병합·pull 뒤 새 guard·hook 적용 · A7 스모크(researcher 첫 턴 task id 노출)는 병합 뒤 오케스트레이터 관측 · lane 은 자기 hook 을 라이브로 못 씀 · 잔여 우회(변수 dir · `bash -c` · `gh api graphql`) · 폴백 엔진은 새 argv 형태 미편입 · T5 재신뢰 불요(정의 무변경).
- 게시 절차·병합 뒤: Ted 가 PR 게시 · 병합 뒤 오케스트레이터가 메인 checkout pull → 첫 Bash 통과 확인 → researcher 1회 스폰(A7 관측 · L8 스모크 2축 기록) → phase 2 착수 · T7 메모리 갱신 없음(PR 1 은 메모리 대상 아님).

## 10. 정책 대조
- CLAUDE.md/AGENTS.md 저촉: 없음 — 게이트 종료코드 0/1/78 정의 적용(A4) · 제품 코드 0 · `contracts/**` 0.
- 「절대 하지 않는 것」: 훅 정의 변경 0 · ADR 이력 수정 0 · 승인 intent 본문 변경 0(줄 추가만).
- 계약 동결 해제: 아니오. envelope 계약 무변경.
- 디자인 제약: 해당 없음(frontend 무변경).

## 11. 우려 항목 (판정 완료)
| # | 항목 | ⓐ | ⓑ | 판정 |
|---|---|---|---|---|
| 1 | A6 를 PR 1 에 넣나 | 넣음(단독 커밋 · README:75 동반 · readiness 조건부) | PR 3(C5) 유지 | ⓐ — Ted 2026-09-26 확정 |
| 2 | 시험 seam `COLAB_GIT_GUARD_PARSER` env 를 제품 hook 에 두나 | 둠 | 두지 않음 · hook 폴더 tempdir 복사본으로 결함 주입 | ⓑ — Ted 3라운드 Q11(가짜 해석기가 규칙을 비울 수 있음) |
| 3 | `run.sh` 알려진 gate 판정 근거 | `ALL_GATES` 배열 상단 이동 + KNOWN 전수 unit | `case` 라벨 추출 | ⓐ — Ted 3라운드(spec B 의 glob 우려는 교차 점검이 반증) |
| 4 | 규칙 판정 위치 | python 1회 안(해석기 = 엔진 · bash 는 폴백 동결본) | bash 가 JSON lines 를 읽음 | ⓐ — §4.1 결정 2 근거(호출 수 2 · JSON 디코더 불요) |

## 12. 범위 밖
- A2 ⓐ 편집 시점 차단(PR 2 · L1 ⓐ·L8 스모크 뒤) · migration-guard 머리말·worktree-setup 나머지 머리말(C10) · README 훅 표 재작성·researcher-task 행(C2) · ruleset JSON(C5·T1) · B3 집계 우선순위 · `bash -c`/`eval` 한 겹 · reseed ACK 검사(`:134`) 확장 · 변수·명령치환 dir 해석 · `gh api graphql` mergePullRequest · 열린 자동 task 조회·재사용 · 자동 begin 존폐(PR 2 L 그룹) · lane-worker 자기검사(L3 · PR 2).
