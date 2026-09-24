# 조사 C — ③ 뒤처리 훅: 브라우저 잔존과 게이트 잠금 (2026-09-24 · 읽기 전용)

## 결론 (요지)
- **근본 원인은 도구가 브라우저를 닫지 않는 문제와 잠금 fd 상속, 이 둘이 겹친 것이다.** 셋째 선택지인 "구조적 원인 없음"은 아니다.
  - `_lock.sh` 가 연 flock fd 는 CLOEXEC 없이 자식에게 상속된다. `frontend-visual`(serial, 잠금 보유)이 `live_audit.sh` 를 거쳐 agent-browser 데몬을 처음 띄우면, 데몬과 chrome 이 **호스트 뮤텍스를 게이트 종료 뒤에도 쥔다**.
  - `live_audit.sh` 에는 `close` 가 **0건**이다. 이 데몬은 스스로 죽지 않는다(idle timeout 기본 비활성).
  - 실측(아래 §4 probe): 부모가 fd 를 닫아도 `STILL-HELD-by-daemon` 로 잠금이 풀리지 않았고, `agent-browser --session X close` 를 부르면 2초 안에 `FREE-after-close` 로 풀리며 데몬도 사라졌다.
- **최소 비용·최소 위험 = (b)** 와 (c) 일부의 조합이다. `live_audit.sh`/`frontend-visual.sh` 가 **고유 세션 이름 + EXIT trap `agent-browser --session "$S" close`** 로 자기 데몬만 닫는다. 보조로 `AGENT_BROWSER_IDLE_TIMEOUT_MS` 를 둘 수 있다. 수정은 2파일, 수 행이다.
- **(a) SubagentStop 훅은 위험이 크고 효과는 작다.**
  - 현재 이 호스트에 떠 있는 데몬 2개는 **다른 저장소**(`30 CoLAB-v2`·`31 CoLAB-v2`) 워크트리 소속이다. 잠금 경로 `/tmp/colab-v2-gate-host-mutex/host` 와 세션 소켓 디렉터리 `~/.agent-browser` 도 사용자 단위로 공유된다. 그래서 이름 패턴이나 `close --all` 로 정리하면 다른 저장소의 진행 중 작업을 죽인다.
  - spec 의 "cwd toplevel 일치 + ppid 자손" 방식도 `chrome_crashpad_handler` 2개/데몬을 놓친다. 이 프로세스는 ppid=1 로 재부모화되어 자손 추적에 걸리지 않는다.
  - 게다가 게이트 잠금 누수는 레인 **안에서** 다음 게이트가 돌 때 이미 터진다. 레인 종료 시점에 도는 훅으로는 늦다.

## 1. 게이트 호스트 뮤텍스
- 구현: `gates/tools/_lock.sh:78` 경로 `${TMPDIR:-/tmp}/colab-v2-gate-host-mutex/host`
  - `:98` `{ exec {GATE_HOST_MUTEX_FD}>"$path"; }` → `:104` `flock -n "$GATE_HOST_MUTEX_FD"` / `:112` `flock -w "$wait_s" …` (기본 900초, `COLAB_GATE_MUTEX_WAIT`)
  - 상한을 넘기면 `:122-124` 에서 `readiness_env_wait` 를 내고 **78**.
- 잠그는 방식: 파일 위 **fd 기반 flock**(open file description 에 묶인다). pid 파일이나 디렉터리 방식이 아니다.
- 상속 여부: 주석 `:71-73` 이 이렇게 적고 있다.
  > 「`{VAR}>` 로 연 fd 는 **exec 를 건너 살아남는다** … 프로세스가 죽으면 커널이 푼다 — 죽은 잠금이 남지 않는다」

  이 주석은 **자식이 fd 를 복제해 계속 사는 경우를 고려하지 않았다**. CLOEXEC 가 없으므로 fork 된 모든 자손(데몬·chrome)이 같은 잠금을 공유한다.
- 게이트 측 흐름:
  - `gates/run.sh:169-175` serial 게이트면 `gate_host_mutex_acquire` 를 호출하고, 성공하면 `export COLAB_GATE_MUTEX_HELD=1` 한 뒤 본체를 `exec` 한다(잠금 fd 를 쥔 채).
  - `gates/run.sh:833-846` (task/all) 부모가 잠금을 잡고 자식 `run.sh "$g"` 를 돌린 뒤 `gate_host_mutex_release`. 이 release 는 부모 fd 만 닫는다. 자식이 띄운 데몬의 복제 fd 는 그대로 남는다.
- `gates/config/parallelism.toml:277` `"frontend-visual" = "serial"`, `:283` `"frontend-visual-selftest" = "serial"` (케이스 4번에서 판정부를 다시 부른다).
- 잔존 잠금 검출: **없다**. `_lock.sh` 는 대기 표식만 찍고(`:111`, `:114`) 상한을 넘기면 78 을 낸다. 누가 쥐고 있는지(fuser·/proc 스캔)는 보지 않는다.
- 참고: 옛 `gate_lock_fd`(`:28-47`)는 fd 9 로 고정되어 있고 `/tmp/colab-gate-lock-<cksum>` 을 쓴다. 역시 CLOEXEC 가 없다.

## 2. 브라우저 쓰는 도구
| 도구 | 기동 | 종료 처리 |
|---|---|---|
| `.agents/skills/design-review/scripts/live_audit.sh` | `:11` `S="${AB_SESSION:-design}"` · `:23-31` `agent-browser --session "$S" set/open/wait/screenshot/eval` | **close·trap 없음(0건)**. 데몬과 chrome 이 계속 남는다. 세션 이름 기본값이 고정 `design` 이라 병렬 실행하면 서로 충돌한다 |
| `gates/tools/frontend-visual.sh` | `:36` `AUDIT=…/live_audit.sh` · `:75` `AUDIT_OUT="$(bash "$AUDIT" "$OUT" $URLS 2>&1)"` | trap·close 없음. `AB_SESSION` 을 설정하지 않아 세션은 `design` 이 된다(grep 0건) |
| `gates/tools/frontend-visual-selftest.sh` | `:45-50` 로 `frontend-visual.sh` 를 2회(green/red) 실브라우저로 호출 | `:37-38` trap 은 `rm -rf` 만 한다. 브라우저는 닫지 않는다 |
| `frontend/scripts/visual-baseline/capture.py` (origin/claude/design-structure-p3, develop 에는 없음) | `:57-59` `agent-bridge.py run-tool browser -- --session vb-<theme>-<pid>-<ts>` · `:87-89` `vite preview` 를 `start_new_session=True` 로 기동 | **닫는다.** `:258-264` 의 `finally:` 가 세션마다 `ab(s, 'close', timeout=30)` 를 호출하고 `stop_preview` 로 `os.killpg` SIGTERM→SIGKILL(`:109-113`) 한다. 단 SIGKILL·턴 절단으로 python 이 죽으면 finally 가 돌지 않는다. p3 의 run.sh·parallelism.toml 에 연결된 게이트는 없다(grep 0건) |

- intent 의 "capture.py 는 데몬을 닫지 않는다"는 p3 코드 기준으로 **틀렸다**. `close` 는 데몬 종료까지 한다(§4 probe 의 `daemon alive after close: no`).
- 코드 전체 grep(`agent-browser.*close|close --all|pkill|killall|killpg|IDLE_TIMEOUT`, 대상 scripts/gates/.agents/skills): 걸린 것은 vendored `templates/*.sh` 5건뿐이다. 게이트·스크립트에는 0건.

## 3. agent-browser 0.27.0 CLI (`~/.npm-global/bin/agent-browser`)
- `close [--all]`: "Close browser (--all closes every session)". alias 는 `quit`, `exit`. `--session <name>` 으로 해당 세션만 닫는다.
- `session list`, `doctor [--fix]`("auto-clean stale socket/pid/version sidecar files")
- **`daemon stop` 명령은 없다.** 세션별 `close` 가 곧 데몬 종료다. 세션당 데몬이 하나씩 뜬다(ppid=1 로 분리, env `AGENT_BROWSER_DAEMON=1`·`AGENT_BROWSER_SESSION=<name>`).
- 도움말 env: `AGENT_BROWSER_IDLE_TIMEOUT_MS  Auto-shutdown daemon after N ms of inactivity (disabled by default)`
- 바이너리 문자열: `AGENT_BROWSER_SOCKET_DIR`(기본 `~/.agent-browser` 또는 XDG_RUNTIME_DIR). `--no-daemon` 은 없다.
- 소켓·pid 디렉터리 `~/.agent-browser/*.pid`: pid 파일 10개가 **모두 죽은 pid** 다(2026-09-11 잔재, `default`·`design` 포함). 사용자 전역 공유 디렉터리다.

## 4. 현재 호스트 상태 (종료 조치 없음)
- 21:22 시점 `agent-browser|vite preview|chrome` 프로세스 **35개**(vite preview 0).
  - 데몬 606778: cwd `…/30 CoLAB-v2/.claude/worktrees/agent-a604d198b8b428287`, session `clv-4a`. chrome 16개(crashpad 2개는 ppid 1).
  - 데몬 608670: cwd `…/31 CoLAB-v2/.claude/worktrees/agent-abfb8cb016daa0f84`, session `pvs-verify`. chrome 16개. 그리고 실행 중 명령 1개(`agent-bridge.py run-tool browser -- --session pvs-verify wait`).
  - 둘 다 경과 약 45초로 **다른 저장소에서 진행 중인 작업**이다. 32 저장소 소속 잔존은 **0건**.
  - 두 데몬의 fd 는 /dev/null·socket·pipe 뿐이고 뮤텍스 fd 는 없다(게이트 밖에서 기동됨). `/tmp/colab-v2-gate-host-mutex/host` 는 존재한다(mtime 21:21).
- **상속 probe** (`/tmp/rc_lockprobe.sh`, 임시 잠금 파일·전용 세션 `rc-lockprobe`, 스스로 close):
  ```
  held fd=10
  daemon=615519 ppid=1
  daemon fds on lock: 1
  chrome procs holding lock: 1
  STILL-HELD-by-daemon
  FREE-after-close
  daemon alive after close: no
  ```
  - 데몬과 chrome 모두 잠금 fd 를 상속한다. 부모가 닫아도 잠금은 유지된다. `--session <자기 세션> close` 한 번이면 잠금이 풀리고 데몬도 종료된다.
- 함의: 이 저장소의 게이트 잠금 경로는 `TMPDIR` 하나로 정해진다(`_lock.sh:63-66`). 그래서 30·31 저장소가 같은 `_lock.sh` 를 쓰면 저장소 사이에서도 공유된다. 이 부분은 미확인이다.

## 5. 메모리
- 32 프로젝트 메모리(`…-32-CoLAB-v2/memory/`, 7개 파일): 데몬·잠금 기록 **0건**(agent-browser 는 보고 선호 1줄뿐).
- 해당 기록은 **31 프로젝트 메모리**에 있다:
  - `…-31-CoLAB-v2/memory/gate-lanes-cannot-run-in-parallel.md:33-40`
    > 「2026-09-18 추가 — `frontend-visual` 이 잠금을 데몬에 흘린다. 게이트가 `agent-browser` 를 처음 부르면 상주 데몬이 뜨는데, 그 데몬이 호스트 뮤텍스 fd(`/tmp/colab-gate-lock-*` 의 flock)를 상속받아 게이트가 끝난 뒤에도 잠금을 놓지 않았다. 다음 `frontend-test` 가 `::gate-waiting::` 으로 605~640초 대기했고 데몬(`agent-browser-linux-x64`)을 죽여야 풀렸다(이슈 #120 레인 실측). … 게이트 전에 데몬을 미리 띄워 두면(fd 상속이 안 일어남) 피할 수 있다. 근본 수정은 `gates/tools/_lock.sh` 가 자식에 fd 를 닫고 넘기는 것(`flock -o` 또는 `exec {fd}>&-`) — 후속 이슈 후보.」

    메모리에 적힌 경로 `/tmp/colab-gate-lock-*` 는 옛 fd 9 잠금 이름이다. 현재 호스트 뮤텍스 경로는 `/tmp/colab-v2-gate-host-mutex/host` 이며, 기전은 같다.
  - `…-31-CoLAB-v2/memory/issue-pr-workflow-shape.md:53` 「`frontend-visual` 이 남긴 agent-browser 데몬이 호스트 게이트 잠금을 쥐어 다음 회차가 exit 78 난다」
  - `…:60` 「레인이 끝나면 agent-browser 데몬 + chrome 프로세스가 남는다(34개 실측). `pkill -f agent-browser-linux-x64` 뒤 chrome 은 `--user-data-dir` 패턴으로.」

    이 절차가 바로 **전 저장소를 죽이는 패턴**이다. 지금 이 방식으로 정리하면 30·31 의 진행 중 세션이 죽는다.

## 6. 훅 배선
- `.claude/settings.json:29-47` SubagentStop 은 2항목이다.
  - `researcher` → `uncommitted-artifacts.sh`(H6)
  - `lane-worker|measurement-lane` → `lane-gate-summary.sh`(H7)
  - 어댑터는 `exec bash …/scripts/harness/hooks/<name>.sh` 한 줄(`.claude/hooks/lane-gate-summary.sh:3`)이다.
- H7 원본 `scripts/harness/hooks/lane-gate-summary.sh:5` `python3 …/lifecycle_contract.py stop --role lane-worker --role measurement-lane || exit 2`. **차단형**(exit 2)이다.
- stdin: `lifecycle_contract.py:289-300` `stop()` 이 `agent_type`·`cwd`·`last_assistant_message`·`agent_id` 를 읽는다. `:76-77` `checkout(cwd)` = `git rev-parse --show-toplevel`.
- `worktree-setup.sh:49-67` 은 python 으로 `cwd`·`agent_type` 을 추출한다(없으면 `$PWD`). `:9-10`, `:268` 로 항상 exit 0.
- Codex:
  - `.codex/hooks.json:42-65` SubagentStop matcher 는 `researcher` / `lane-worker|measurement-lane` 이다. 새 matcher `lane-worker|measurement-lane|researcher` 는 기존 두 항목이 이미 이 세 역할을 다 덮으므로 **무변경으로 충분하다**.
  - `scripts/agent-bridge.py:59-76` `registered_hooks()` 는 `re.fullmatch(entry["matcher"], tool)` 이고, 명령 형식은 `bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/<name>.sh"` 만 허용한다.
  - `:322-341` 에서 Codex 는 hook 들을 **순차 실행**(subprocess.run, SubagentStop timeout 30초)하고, 하나라도 rc≠0 이면 raise 한다. 반면 Claude 는 같은 이벤트의 matcher 별 훅을 병렬로 돌린다(spec 기술). 두 도구의 순서 의미가 다르다.
- `.agents/harness.yaml:51-58` `adapters.required_files` 는 CLAUDE.md, settings.json, .codex/config.toml, .codex/hooks.json, agent-bridge.py 이다. 훅 어댑터 개별 파일은 목록에 없다.
- `docs/development/dual-agent.md:69` 「기존 10개 셸 훅의 5개 이벤트」. spec 에 적힌 "9→10" 과 수치가 이미 다르다(재확인 필요).

## 7. 선택지 평가
| 안 | 원인을 고치나 | 비용 | 위험 |
|---|---|---|---|
| (a) SubagentStop 훅 | 아니다. 레인 안의 다음 게이트에서 이미 900초 대기 후 78 이 난다. 종료 시점 정리는 사후 처리다 | 원본·어댑터·selftest 3파일, settings 변경, PC 마다 `/hooks` 재신뢰 | 이름·자손 판정이 crashpad(ppid 1)를 놓친다. 주 체크아웃과 다른 저장소의 세션을 오인할 여지가 있다. H7 과 병렬로 돈다 |
| **(b) 도구가 자기 세션을 닫음** | **맞다.** 잠금을 쥔 주체(데몬)를 그 게이트 안에서 종료한다 | `live_audit.sh`: 세션 기본값을 고유 이름(`design-$$` 등)으로 바꾸고 `trap 'agent-browser --session "$S" close >/dev/null 2>&1' EXIT` 추가. frontend-visual 은 이것을 그대로 물려받는다. capture.py 는 이미 충족 | 자기 세션 이름만 닫으므로 **다른 워크트리·저장소·오케스트레이터에 영향이 없다**. 단 SIGKILL 이나 턴 절단 때는 trap 이 돌지 않는다 |
| (c) 게이트 실행기 측 | 부분적이다. `_lock.sh` 에서 잠금을 잡은 뒤 게이트 본체에 fd 를 닫고 넘기는 것은 exec 구조상 불가능하다. 본체가 잠금 보유자이기 때문이다. frontend-visual 에서만 `bash "$AUDIT" … {fd}>&-` 로 닫으려면 fd 번호를 export 해야 한다. 대기 중 `/proc/*/fd` 로 보유자를 찾아 표식에 pid·cmdline 을 찍는 **진단**은 저비용이다 | 중간 | 보유자를 자동으로 kill 하면 (a) 와 같은 오인 위험이 생긴다. **검출과 표시까지만 권장** |
| (d) 절차만 | 아니다 | 0 | 현행 메모리 절차(`pkill -f`)가 오히려 다른 저장소를 죽인다 |

- **권고**: (b) 를 본 수정으로 한다. `live_audit.sh` 고유 세션과 EXIT trap close 로 2파일 수 행이며, selftest 는 게이트 실행 뒤 `pgrep`·`flock -n` 으로 잠금이 풀렸는지 검증한다. 보조로 (c) 의 "대기 표식에 잠금 보유 pid·cmdline 표시"를 붙인다. 선택으로 `AGENT_BROWSER_IDLE_TIMEOUT_MS` 를 게이트 env 에 넣어 SIGKILL 경로의 안전망을 둔다. (a) 는 이번 증거로는 정당화되지 않는다. 34개 잔존 프로세스 문제도 (b) 적용 뒤 재측정해 남는 것이 있으면 그때 다룬다.
- 미검증: 30·31 저장소의 `_lock.sh` 가 같은 경로를 쓰는지 여부. 실제 frontend-visual 게이트를 돌려 잠금이 새는 것을 end-to-end 로 재현하지는 않았다(probe 로 기전만 확인).
