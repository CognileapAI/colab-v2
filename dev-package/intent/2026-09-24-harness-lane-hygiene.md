# Intent: 하네스 고도화 — 검토 완료 · 승인 (2026-09-24 · 전부 권고대로)
메타 — 발의자: Ted · 작성 2026-09-24 · 상태: **승인 2026-09-24 — Ted 원문 "전부 권고대로 할게"** · spec v2 `dev-package/prd/specs/S-HARNESS-LANE-HYGIENE-20260924.md`
- 1차: Ted 원문 "권고대로 해서 하네스고도화하고. 좋아. 작업은계속하자" (2026-09-24 · 권고 4건 수용)
- 2차(우선): Ted 원문 "저하네스에 인텐트로 어떻게 해야할지만같이기록해두자 저대로만 개선하기보다 진지하게 따져보고 개선하는게좋을듯하니" (2026-09-24) — **권고를 그대로 구현하지 말고, 이 문서에 「어떻게 해야 할지」를 기록해 둔 뒤 진지하게 따져 보고 개선한다.** 착수했던 구현 레인은 중단했다(커밋 0).
- 3차: Ted 원문 "develop 최신 받고, (git pull) 하네스 작업 intent 해서 마저해보자 진지하게 따질것, ponytail 저것도 함께 같이 처리하자, 하네스 관련된 모든 브랜치 다 한꺼번에 정리하면서 적용 검토" (2026-09-24) — 네 절의 「모을 증거」를 모아 답과 권고를 적었다. 구현은 판정 뒤다.

## 문제 (실측 · 2026-09-24 디자인 구조 프로그램 P0~P3)
- 서브에이전트가 턴 한도에서 산출물 없이 끝난다 — researcher 30턴 0바이트 2회 · advisor 12턴 잘림 2회 · lane-worker 200턴 잘림 1회. 매번 「먼저 쓰고 좁혀서 재개」로 살렸다.
- 레인 게이트 증거는 Git common dir 의 task runtime(`colab-harness/<checkout>/<task>/<run>/gate-summary.json`)에만 있어 advisor ② 가 「증거 없음」으로 판정했다(P0). 이후엔 오케스트레이터가 먼저 열어 확인하고 「재실행 금지」를 프롬프트에 박았다.
- 레인 종료 뒤 agent-browser 데몬 · chrome 34개 · `vite preview` 가 남는다. 매번 손으로 죽였다. 이 데몬이 호스트 게이트 잠금을 쥐면 다음 회차가 exit 78 이 난다.
- 단계당 spec + advisor ① + lane + advisor ② + 대조 = 60~80만 토큰. 작은 단계에도 같은 절차가 붙는다. 반면 advisor ① 은 spec 5건 전부에서 approve-with-changes 를 냈고 차단급 결함 3건(대조 도구 부재 · jsdom `@layer` 미계산 · 다크 값 불일치 치환)을 잡았다.

## 권고 4건 (1차 — 그대로 구현하지 않는다 · 검토 대상)
1. 조사·레인 지시 범위를 턴 한도로 재단(researcher 2~3절/건 · lane 계열 2~3개/건 · 「N번째 도구 호출 전 파일 쓰기」 · advisor 「도구 8회 이하 뒤 판정」).
2. 레인 최종 메시지·handoff JSON 에 게이트 증거 경로 필수 · advisor ② 에 전달.
3. SubagentStop 훅으로 워크트리 cwd 의 브라우저·프리뷰 프로세스 정리.
4. 작은 단계의 advisor ① 생략 기준(spec 60행/4,000자 · 새 게이트·훅·계약 없음 · 제품 파일 3개 이하 · 변경 면을 재는 게이트 명시).

## 진지하게 따질 것 (검토 질문 · 2026-09-24 증거로 답함)
### ① 턴 한도 재단
- **증상 대 원인**: 잘림의 원인이 지시 범위인가, 에이전트가 「쓰기 전에 다 읽으려는」 행동인가, 턴 한도 자체(30/12/200)가 낮은가? 세 가지는 처방이 다르다(범위 재단 · 역할 본문의 「먼저 쓰기」 규율 · `maxTurns` 상향). 실측: 재개 지시 한 줄(「첫 턴에 한 번의 Write」)로 세 번 다 살아났다 → 원인은 **행동**일 가능성이 크다. 그러면 범위 재단보다 역할 본문의 행동 규율이 먼저다.
- **turn 이 아니라 tool call 로 세는가**: 한도는 턴, 실제 소모는 도구 호출·읽은 바이트다. 「10번째 도구 호출 전 파일 쓰기」가 맞는 단위인지, 아니면 「읽은 파일 N개 뒤」인지.
- **대안**: (a) 역할 본문에 「먼저 쓰기」 규율만 (b) 오케스트레이터 지시문 템플릿에 범위 상한 (c) `maxTurns` 상향 (d) 조사자를 절 단위로 여러 번 스폰. 비용·부작용(짧은 조사가 늘면 취합 비용이 는다) 비교.
- **모을 증거**: 이번 세션의 잘린 에이전트 3건의 transcript 에서 「몇 번째 도구 호출에서 무엇을 읽고 있었나」. 잘리지 않은 에이전트(advisor 7건 · lane 3건)와의 차이.
- **답 (2026-09-24 실측 · 근거 `dev-package/reports/harness/20260924-lane-hygiene-review/A2-turn-cuts.md`)**
  - 원인은 역할마다 다르다. 첫 절단 6건 = (b) 먼저 다 읽기 + (c) 한도 3건(researcher 2 · advisor 1) · (a) 범위 2건(lane-worker P2a·P2b, 200턴에 4·7단계까지) · (d) 종료 훅 반송 1건(researcher · 보고서는 10번째 호출에 썼으나 H6 가 정지 1회를 막아 한도 초과).
  - (d) 는 재개 뒤에 커졌다. 재개된 researcher 2건이 H6 에 24회 막혀 38턴을 쓰고 정지 성공 0으로 끝났다. 지시문에 `lifecycle begin` 이 없어 task_id 가 없었고 `COLAB_HANDOFF` 를 만들 방법이 없었다. lane-worker 는 절차가 있었는데도 재개 뒤 H7 에 11회(10·1) 막혔다(재개 지시문의 handoff 재기재 부재로 추정 · 미검증).
  - 이 검토에서 재현했다(이번 세션 실측 · 근거 `dev-package/reports/harness/20260924-lane-hygiene-review/A3-session-researchers.md`). 절차 없는 researcher 2건 = 도구 23·24회 뒤 반송 루프로 30턴 절단. 절차를 지시문에 넣은 researcher 3건 = 정상 종료(도구 9·23·50회 · 1건은 도중 전달). 첫 지시문의 절차 누락은 프로그램 3/3 + 이번 2/5 = 8건 중 5건이다. 체크리스트 없이 쓴 지시문에서는 빠졌고, 이번 세션 뒤 3건은 넣었다.
  - 숫자 없는 「먼저 써라」는 1건 실패(af51a789 · "WRITE THE REPORT FILE EARLY" 지시에도 33회 호출까지 선언 경로 쓰기 0) · 1건 성공(a7a32208 · 10번째 호출에 쓰기)으로 판정할 수 없다. 숫자를 박는 이유는 효과 입증이 아니라 에이전트가 셀 수 있는 단위이기 때문이다. 「8번째 도구 호출 전에 쓴다」 + 질문 2~3개 범위는 이번 2건 모두 한도 안에서 끝났다(표본 2).
  - 단위: 한도는 turn(assistant 메시지)이고 병렬 호출은 한 턴에 여럿이다(조사자 C = 도구 50회를 30턴 안에). 행동 규칙은 에이전트가 셀 수 있는 도구 호출 수로 건다.
- **권고**
  - R1 (구조 · (d)): researcher `SubagentStart` 훅이 read-only task 를 자동으로 연다(`lifecycle begin --role researcher --agent-id <payload agent_id>`). task_id 와 handoff 명령 한 줄을 맥락에 싣는다(SubagentStart 출력은 맥락에 실린다 — `worktree-setup.sh` 머리말). 지시문 의존을 없앤다. 제약: 파일 산출물은 begin 때 `--artifact` 로 선언해야 한다(체크아웃 밖 Edit·Write 는 선언된 runtime 산출물만 허용 — `lifecycle_contract.py` `resolve_edit`). 산출 파일이 필요한 조사는 지시문이 따로 begin 한다. 한 에이전트에 task 둘이 있을 때 `stop()` 이 handoff 의 task_id 로 판정하는지는 spec 에서 시험으로 확인한다. 훅 출력에 **agent_id 를 반드시 찍는다** — 체크아웃 밖 산출물 task 는 `task.agent_id == payload agent_id` 를 요구하므로(`lifecycle_contract.py:440-450`) researcher 가 자기 agent_id 를 알아야 `--agent-id` 를 넣는다. begin 이 실패하면(비 git cwd 등) exit 0 으로 「begin 실패 · 사유 · 직접 begin 명령」을 찍어 현행 방식으로 물러난다.
  - 기각: H6 차단 문구에 「지금 begin 하라」 안내. 끝에서 연 task 는 기준선이 끝 시점이라 read-only 판정이 무의미해진다.
  - R2 (절차 · 재개): 재개 지시문에 task_id 와 handoff 명령을 다시 적는다. researcher 실행 중 같은 체크아웃에 커밋하지 않는다 — `stop()` 이 begin 시점과 HEAD commit·tree 가 다르면 거부한다(`lifecycle_contract.py:320-322` · 현행 절차 task 와 같은 조건). `colab-v2-work` 지시문 체크리스트 두 줄.
  - R3 (역할 본문 · (b)(c)): researcher 「산출 파일을 8번째 도구 호출 전에 쓴다(뼈대 포함) · 질문이 3개를 넘으면 부모에게 분할을 요청한다」. advisor 「도구 8회 이하 뒤 판정」(01:02 이후 이 문구가 있는 advisor 3건 절단 0).
  - R4 ((a) 레인): 레인 1건 = 파일 계열 2~3개 — 스킬 체크리스트 한 줄.
  - `maxTurns` 상향은 보류한다. (c) 가 겹친 3건은 모두 재개 지시(먼저 쓰기) 한 줄로 끝났다.

### ② 증거 경로 규격
- **왜 저장소 밖에 두었나**: `lifecycle-evidence.md` 는 runtime 보고서를 run 디렉터리에만 쓰고 저장소에 사본을 두지 않는다고 못박았다(재실행 갈음·hash 결합 때문). 경로를 JSON 에 싣는 것은 그 설계와 충돌하지 않지만, **advisor 가 그 파일을 읽을 권한·경로 해석이 되는가**(다른 워크트리에서 `gate-snapshot` 은 거절된다 — 실측). 읽기 전용 접근 경로를 하네스가 제공해야 하는지, 오케스트레이터가 확인한 계수를 프롬프트에 옮기는 현재 방식으로 충분한지.
- **대안**: (a) handoff JSON 에 경로+sha256 (b) `lifecycle gate-snapshot --task --any-checkout` 같은 읽기 전용 조회 명령 (c) 오케스트레이터가 계수·경로를 advisor 프롬프트에 적는 현재 관행을 규칙으로만.
- **모을 증거**: advisor ② 4건 중 증거 문제로 판정이 갈린 것 1건(P0)뿐 — 이후 3건은 프롬프트 한 줄로 해결됐다. 훅·JSON 변경(계약 변경 · 재신뢰)이 그 비용을 정당화하는가.
- **답 (근거 `dev-package/reports/harness/20260924-lane-hygiene-review/B2-advisor-table.md` · 코드 대조)**
  - 현재 handoff JSON = `task_id · mode · summary · artifacts · run_id`(`scripts/harness/hooks/lifecycle_contract.py:511-519`). gate-summary 는 `<git-common-dir>/colab-harness/<key>/<task>/<run>/gate-summary.json` 이고 `<key>` = `sha256(toplevel + gitdir)[:32]`(`scripts/harness/task_state.py:23`)다. 사람이 추론할 수 없고 레인 워크트리마다 다르다.
  - advisor ② 6건: 증거를 스스로 읽은 기록 0 · 「증거 없음」 지적 1(P0) · 기록 없음 5. 보고서 6건 모두(P0 는 ② 지적 뒤 추가) 경로를 적었지만 common dir 기준 상대경로라 advisor 가 풀어야 한다.
  - advisor 의 Read 를 막는 훅·권한은 없다(`.claude/settings.json` PreToolUse 는 Bash·Edit|Write 만 · permissions 없음). 절대경로를 받으면 연다.
  - handoff JSON 은 레인의 최종 메시지로 **오케스트레이터**에게 간다. (a) 를 해도 advisor 로 옮기는 중계는 남는다. (a) 의 순이득은 절대경로·sha256 을 옮겨 적지 않는 것이고, 비용은 handoff 계약 변경(H6·H7·Slack 준비의 재검증 경로)과 시험이다.
- **권고**: (c) 를 규칙으로 올린다. lane-worker·measurement-lane 최종 메시지에 gate-summary **절대경로**와 3계수 · advisor 역할 「입력」에 「오케스트레이터가 준 절대경로를 Read 로 연다 · 게이트를 재실행하지 않는다」 · 스킬 체크리스트 한 줄. 코드·계약 변경 0. (a)·(b) 는 이 규칙 뒤에도 중계 실패가 나오면 다시 따진다.

### ③ 뒤처리 훅
- **왜 남는가**: agent-browser 는 데몬형이라 마지막 명령 뒤에도 산다. `capture.py` 는 프리뷰 서버를 스스로 닫지만 데몬은 닫지 않는다. **도구 쪽에서 닫는 것**(capture.py 종료 시 `agent-browser … close`/데몬 stop · `frontend-visual` 게이트도 같은 문제 — 메모리 실측)이 훅보다 근본에 가깝다.
- **훅의 위험**: SubagentStop 훅은 같은 이벤트의 다른 훅(H7)과 병렬이라 순서가 없다 · 주 체크아웃에서 도는 조사자에 걸리면 접두어 판정으로 전 워크트리의 브라우저를 죽인다(advisor ① 차단급 지적) · chrome 자손은 cwd 가 `/` 일 수 있다 · 훅 정의 변경은 PC 마다 `/hooks` 재신뢰. 
- **대안**: (a) 훅 (b) 브라우저를 쓰는 도구(`capture.py` · `live_audit.sh` · `frontend-visual.sh`)가 자기 세션·데몬을 닫는다 (c) 게이트 실행기가 잠금을 잡기 전에 잔존 데몬을 검출해 78 대신 정리+경고 (d) 오케스트레이터 절차(메모리)로만. 
- **모을 증거**: 잔존 데몬이 실제로 게이트 잠금을 쥔 사례의 로그(메모리에 한 줄 있음 · 재현 필요) · agent-browser 0.27.0 의 데몬 종료 명령 유무.
- **답 (근거 `dev-package/reports/harness/20260924-lane-hygiene-review/C-browser-cleanup.md` · 재현 `dev-package/reports/harness/20260924-lane-hygiene-review/lock-inherit-repro.sh`)**
  - 원인 둘이 겹친다. ⑴ 호스트 뮤텍스는 `exec {fd}>` + `flock` 이고 fd 가 자식에게 상속된다(`gates/tools/_lock.sh:98,104,112`). serial 게이트 안에서 처음 뜬 agent-browser 데몬·chrome 이 fd 를 물고 게이트가 끝나도 잠금을 쥔다. 재현 결과: 부모가 fd 를 닫은 뒤에도 다음 잠금 BLOCKED → 데몬 종료 뒤 획득 · 자식에서 fd 를 닫으면 즉시 획득. 31 메모리 실측: 다음 `frontend-test` 가 605~640초 대기. ⑵ `live_audit.sh`(frontend-visual 판정부)에 `close`·trap 0건 · 세션 이름 기본값 `design` 고정.
  - 위 「capture.py 는 데몬을 닫지 않는다」는 틀렸다. `capture.py`(`origin/claude/design-structure-p3` 에만 있고 develop 에 없다)는 `finally` 에서 세션 `close` 와 프리뷰 `killpg` 를 한다.
  - agent-browser 0.27.0: `daemon stop` 없음 · `--session <이름> close` 가 그 세션 데몬 종료 · `close --all` 은 사용자 전역 · `AGENT_BROWSER_IDLE_TIMEOUT_MS` 안전망(기본 꺼짐).
  - 훅안 (a) 의 결함: 조사 시점 이 호스트의 데몬 2개는 30·31 저장소의 진행 중 세션이었다(32 소속 0). `~/.agent-browser` 와 잠금 경로(`${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host`)는 사용자 단위 공유다. `chrome_crashpad_handler` 는 ppid 1 로 떨어져 자손 추적에 걸리지 않는다. 누수는 레인 **안의** 다음 게이트에서 터지므로 종료 훅은 늦다.
  - 31 메모리의 현행 수동 절차 `pkill -f agent-browser-linux-x64` 는 다른 저장소 세션까지 죽인다.
- **권고**: 훅안은 기각한다. F2 가 본 수정이고 F1 은 다른 데몬성 자식에 대한 보강이다.
  - F2 `live_audit.sh`: 고유 세션 이름 기본값 + EXIT trap `agent-browser --session "$S" close`. trap 이 돌지 않는 SIGKILL·절단 경로의 안전망으로 게이트 env 에 `AGENT_BROWSER_IDLE_TIMEOUT_MS` 를 둔다(값은 spec).
  - F1 잠금: 단독 게이트 경로는 잠금을 잡은 뒤 본체를 `exec` 하므로(`gates/run.sh:169-175`) **본체가 잠금 보유자**다. 본체는 잠금을 쥔 채, 본체가 띄우는 **자식**에게만 fd 를 넘기지 않는다 — `_lock.sh` 가 fd 번호를 export 하고 데몬을 띄우는 호출부(`frontend-visual.sh` → `live_audit.sh`, `gates/run.sh:833-846` 의 자식 `run.sh "$g"`)를 `{fd}>&-` 로 부른다. 본체 자체를 자식으로 돌려 부모가 잠금을 쥐는 개편(`flock -o` 형)은 exit code·`::gate-waiting::` 전파 재검증이 붙으므로 spec 에서 비용을 따로 잰다. `gate-host-mutex-selftest` 에 「자식 데몬 생존 중 다음 잠금 획득」 케이스를 넣는다.
  - F3(선택): 잠금 대기 표식에 보유 pid·cmdline 진단을 싣는다. 종료는 하지 않는다.
  - 수동 절차는 「자기 세션 이름으로 close」로 바꾼다.

### ④ advisor ① 생략 기준
- **전제 재검토**: 이번 프로그램에서 ① 은 한 번도 「깨끗하다」를 내지 않았다(6/6 · 표기 방식 둘: approve-with-changes 4 · 「정정 N건」 2). 그러면 생략 기준을 만들 근거가 아직 없다 — 생략해도 됐을 spec 이 실제로 있었는가? P3(리터럴 정리 · 가장 작은 단계)도 ① 이 다크 값 불일치를 잡았다.
- **비용의 실체**: advisor 1건 = 6~9만 토큰 · 1.5~2.5분. 단계 비용 60~80만의 10% 안팎. 줄일 자리가 ① 인지, 레인(30~50만)인지, 오케스트레이터 대조인지.
- **대안**: (a) 기준 없이 항상 ① (b) 「깨끗하다」가 연속 N회 나온 뒤에만 생략 후보 (c) 경량 ①(도구 호출 3회 · 한 메시지) 등급 신설.
- **모을 증거**: 향후 spec 3~5건의 ① 판정 결과(깨끗/변경)와 잡은 결함의 등급.
- **답 (근거 `dev-package/reports/harness/20260924-lane-hygiene-review/B2-advisor-table.md`)**
  - advisor ① 6단계(P0·P1·P2a·P2b·P3·P5): 6/6 결함 발견 · 정정 합계 49건 · clean 0 · block 0. 판정은 커밋 메시지와 spec 표지에만 있고 결함 등급 기록은 0이다. 정정 내용으로 추론하면 차단급 5/6(P3 보류 · B2 추론값이며 기록값 아님)이다.
  - 초안 기준을 적용하면 생략 0단계다. 가장 작은 spec 이 8,968자(기준 4,000자의 2.2배)다. 줄 수만 통과하는 P3·P5 에서도 ① 정정이 7·8건이다. 경계 사례가 없어 기준값을 판정할 데이터가 없다.
- **권고**: 생략 기준을 지금 만들지 않는다(대안 (a) 항상 ①). ① 결과에 결함 등급(차단급/개선)을 한 줄씩 남겨 다음 프로그램에서 데이터를 쌓는다. 비용을 줄일 자리는 ① 이 아니라 반송 루프(재개 researcher 38턴 · 재개 레인 22턴)와 레인 범위(①의 R4)다.

## 어떻게 진행할지 (Ted 판정)
1. (완료 2026-09-24) 증거 수집 — researcher 3건 · 이번 세션 실측 1건 · 잠금 재현 1건 · advisor ② 검토(수정 9건 반영). 위 네 절의 「답」.
2. (완료 2026-09-24) Ted 판정 — 「판정 요청」 다섯 항목 전부 권고대로. F3 은 권고에 넣지 않은 선택 항목이라 범위 밖.
3. spec v2 를 쓴다(R1~R4 · ② 규칙 · F1·F2 · ④ 등급 기록). advisor ① → 레인 순서다. 1차 초안은 같은 경로에서 v2 로 대체했다(v1 은 git 이력).

## 영향 범위 (구현 시 · 참고)
- `.agents/rules/colab-rules.md` · `.agents/roles/*.md` · `.agents/skills/colab-v2-work/SKILL.md` · `scripts/harness/hooks/*` · `.claude/settings.json` · `.codex/hooks.json` · `docs/development/*.md` · 브라우저 도구 스크립트. 제품 코드 0.

## 판정 요청 (Ted · 2026-09-24 전부 권고대로로 닫힘)
- ① R1 researcher 자동 task 훅 채택 여부 — 훅 1개 추가 · 이 PC `/hooks` 재신뢰. R2~R4 는 문서 변경.
- ② 규칙화(코드 0)로 충분한지.
- ③ 훅안 기각 + F2(본 수정 · `AGENT_BROWSER_IDLE_TIMEOUT_MS` 안전망 포함)·F1(보강) 채택 여부. F3 포함 여부.
- ④ 생략 기준 미채택 + 결함 등급 기록.
- spec 에서 확인할 것: 한 에이전트의 task 공존(R1) · R1 의 Codex 측(`.codex/hooks.json` SubagentStart 에 researcher matcher 추가 · bridge payload 의 `agent_id` 유무) · 30·31 저장소가 같은 잠금 경로를 쓰는지(F1).

## 부수 발견 (범위 밖 · 후속 후보)
- `gates/run.sh` 는 첫 인자만 게이트로 읽는다(`gates/run.sh:9` `GATE="${1:-}"`). `run.sh a b c` 는 a 만 돌리고 b·c 를 조용히 버린 채 exit 0 을 냈다(2026-09-24 이 검토에서 실측). 「선언하면 검사한다」와 어긋난다 — 여분 인자를 78 로 처리하는 후보.
- 체크아웃 밖 경로의 Edit·Write 는 선언된 runtime 산출물이 아니면 `migration-guard` 가 막는다(설계대로). 이번 조사자들은 셸 heredoc 으로 썼다. R1 설계에서 산출 파일 선언 경로를 함께 정한다.

## 확인
- Ted 확인 문장(원문 그대로): "저하네스에 인텐트로 어떻게 해야할지만같이기록해두자 저대로만 개선하기보다 진지하게 따져보고 개선하는게좋을듯하니" (2026-09-24)
- Ted 확인 문장(원문 그대로 · 3차): "develop 최신 받고, (git pull) 하네스 작업 intent 해서 마저해보자 진지하게 따질것, ponytail 저것도 함께 같이 처리하자, 하네스 관련된 모든 브랜치 다 한꺼번에 정리하면서 적용 검토" (2026-09-24)
- Ted 승인 문장(원문 그대로 · 4차): "전부 권고대로 할게," (2026-09-24)
- 재개봉 금지: 예(잔여 결함은 새 intent).

## 참조
- 실측: `dev-package/reports/design-system/20260924/p0/report.md`(advisor ② 증거 판정) · P1~P3 보고서의 「spec 과 다르게 한 점」 · 메모리 `subagent-turn-limits-truncate-results` · `gate-lanes-cannot-run-in-parallel` · `issue-pr-workflow-shape` · 3차 검토 근거: `dev-package/reports/harness/20260924-lane-hygiene-review/`
- 하네스 설계: `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` · `docs/development/dual-agent.md` · `docs/development/lifecycle-evidence.md`
- spec v2: `dev-package/prd/specs/S-HARNESS-LANE-HYGIENE-20260924.md`(v1 = 1차 권고 기준 초안 · git 이력)
