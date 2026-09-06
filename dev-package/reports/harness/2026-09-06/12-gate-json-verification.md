# P-J 게이트 요약 JSON · H6 · H7 — 실행·검증 기록 (2026-09-06)

근거 스펙 = `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` **D절**(게이트 요약 계약) ·
**C절**(H6·H7 행 · 킬스위치 · 「차단은 exit 2 만 유효」) · **H 9행**(P-J 검증 = 「`counts` 가 요약줄과 일치」) ·
**K절 V2**(SubagentStart/Stop matcher = 에이전트 타입 · 문서 인용). 규율 원본 = `.claude/rules/colab-rules.md` §3-1·§3-2·§3-4·§4-3.

브랜치 = `worktree-harness-fable51-spec` · 기준 HEAD = `16c4296` · tree `d2c9d8e`.

---

## 1. 무엇이 생겼나

| 자리 | 무엇 | 성격 |
|---|---|---|
| `gates/run.sh` | 요약 JSON 배출 · 단독 게이트 요약 래퍼 · 자식 표식(`COLAB_GATE_SUMMARY_CHILD`) | 배선(**게이트 로직 무변경**) |
| `gates/tools/gate_summary_json.py` | TSV → `colab-gate-summary/1` 직렬화기 | 도구 |
| `.claude/hooks/uncommitted-artifacts.sh` | H6 · `SubagentStop` matcher `researcher` | **차단**(exit 2) |
| `.claude/hooks/lane-gate-summary.sh` | H7 · `SubagentStop` matcher `lane-worker` | **차단**(exit 2) |
| `.claude/hooks/git-guard.sh` | H3 ⑶ 을 「`--ff-only` 없는 병합」으로 좁힘 | 개정 |
| `.claude/settings.json` | H6·H7 을 `bash "${CLAUDE_PROJECT_DIR}/.claude/hooks/<x>.sh"` 로 등재 | 배선 |
| `gates/README.md` · `README.md` · `.claude/agents/lane-worker.md` · `researcher.md` | 배출처 변수·훅 2건·H3 개정 반영 | 문서 |
| `dev-package/reports/harness/2026-09-06/11-merge-guards-verification.md` | H3 개정 2케이스 반영 | 문서 |

### 1-1. 게이트 로직을 건드리지 않았다는 것의 뜻

- `ALL_GATES` · 각 `case` 갈래 · 게이트 스크립트 · 종료코드 규약은 **한 줄도 바뀌지 않았다.**
- 계수는 요약 블록이 이미 세던 `n_green` / `n_red_judge` / `n_red_ready` / `n_undeclared_input` 그대로다.
  게이트별 상태는 **그 계수를 올리는 같은 갈래 안에서** 함께 적는다 — 따로 한 번 더 판정하지 않는다.
  (스펙 D 축자 「`counts` 는 run.sh 가 이미 세는 … 그대로 쓴다」.)
- 배출기(`gate_summary_json.py`)는 **직렬화만** 한다. 로그를 다시 읽지 않고 계수를 다시 세지 않는다.
  요약 계수와 게이트별 상태가 갈리면 경고만 찍고 **요약 계수를 정본으로 적는다** — 두 번째 판정처를 만들지 않는다.
- 상태는 `green` / `red_판정` / `red_준비` **셋뿐이다. `SKIP` 없음**(스펙 D · `CLAUDE.md §4`).

### 1-2. 단독 게이트도 JSON 을 내는 이유

레인의 반복 검증은 전수가 아니라 **단독 게이트**다(`rules §3-1`). H7 이 읽는 자리가 `all` 에만 생기면
규율대로 일한 레인이 매번 「JSON 부재」로 걸린다. 그래서 **배출처가 선언된 실행에 한해** 실행기가
자기를 자식으로 한 번 더 부르고, 자식 출력을 그대로 흘리면서 종료코드·준비 표식을 받아 적는다.

- 배출처 미선언 실행(CI·손 실행)은 이 자리를 그냥 지나간다 — **기존 동작 무변경**(실측 §3 마지막 줄).
- 래퍼는 시험용 env source **앞**에 있다. 뒤에 두면 `~/.colab-v2-test.env` 부재 때 부모가 78 로 먼저
  끝나 JSON 이 안 나오고, H7 은 그것을 「게이트를 안 돌렸다」로 읽는다. 그 갈래가 §3 의 `redready` 케이스다.
- `all` 과 `selftest` 가 부르는 자식에는 `COLAB_GATE_SUMMARY_CHILD=1` 이 붙는다 — 한 실행의 요약은 하나다.

---

## 2. 훅 검증 — 합성 `SubagentStop` / `PreToolUse` JSON 을 stdin 에 먹여 실측

하네스 = 임시 파이썬 스크립트(레포에 남기지 않는다). `main` 브랜치 상태와 미추적 파일 상태는
**일회용 레포**(`git init -b main`)로 재현했다 — 본 체크아웃을 읽지도 쓰지도 않는다.

### 2-1. H3 `git-guard.sh` 재실측 — 차단 8/8 · 통과 8/8 (개정분 포함)

| # | 케이스 | 기대 | 실측 |
|---|---|---|---|
| ⑴ | `git push origin main` | 차단 | **2** ✓ |
| ⑵ | `git push origin HEAD:refs/heads/main` | 차단 | **2** ✓ |
| ⑶ | `git push --force-with-lease origin main` | 차단 | **2** ✓ |
| ⑷ | HEAD 가 `main` 인데 refspec 없는 `git push` | 차단 | **2** ✓ |
| ⑸′ | ⭑ **HEAD 가 `main` 일 때 `git merge lane-a`**(`--ff-only` 없음) | 차단 | **2** ✓ |
| ⑸″ | ⭑ **HEAD 가 `main` 일 때 `git merge --no-ff lane-a`** | 차단 | **2** ✓ |
| ⑹ | `gh pr merge 12 --squash` | 차단 | **2** ✓ |
| ⑺ | `git branch -D main` | 차단 | **2** ✓ |
| ⑸‴ | ⭑ **HEAD 가 `main` 일 때 `git merge --ff-only <레인>`** | **통과** | **0** ✓ |
| ⑽ | 레인 첫 줄 `git merge --ff-only origin/main`(비-main) | 통과 | **0** ✓ |
| ⑾ | `git push origin worktree-harness-fable51-spec` | 통과 | **0** ✓ |
| ⑿ | `git fetch --all --prune` | 통과 | **0** ✓ |
| ⒀ | `git pull --rebase` | 통과 | **0** ✓ |
| ⒁ | `git worktree list` | 통과 | **0** ✓ |
| ⒂ | `git push origin --delete worktree-lane-a` | 통과 | **0** ✓ |
| ⒃ | `npm ci --prefix frontend`(git 아님) | 통과 | **0** ✓ |

⭑ **개정 판정(P-J)** — ⑶ 「HEAD 가 main 일 때의 `git merge`」를 **「`--ff-only` 가 없는 병합」으로 좁혔다.**
`main` 에서의 `git merge --ff-only <레인>` 은 오케스트레이터가 승인된 형태로 병합하는 **그 명령 자체**이고
(`rules §4-2`·§2-1), 그것까지 막으면 정상 경로마다 `COLAB_HOOKS=0` 을 붙이게 된다 — 상시 무력화된 훅은
훅이 아니다. **새 병합 커밋을 만드는 형태**(plain·`--no-ff`·squash)는 차단 그대로다. 종전 표기는
`11-merge-guards-verification.md` §2-1 ⑸ 에 취소선으로 남겼다.

H4·H5 는 이 회차의 변경 대상이 아니라 재실행하지 않았다(변경 0 · 종전 실측은 11번 문서 §2-1 ⑻⑼ · §2-2 ⒄~⒇).

### 2-2. H6 `uncommitted-artifacts.sh` — 차단 3/3 · 통과 3/3

| 케이스 | 기대 | 실측 |
|---|---|---|
| `dev-package/sessions/new-survey.md` 미추적 | 차단 ＋ 경로 열거 | **2** ✓ (경로 열거 확인) |
| 차단문에 「`git add -A` 금지」가 있다 | 있다 | ✓ |
| `dev-package/reports/**` 미추적 | 차단 | **2** ✓ |
| 미추적 0건(`dev-package/intent/` 디렉터리 자체가 없어도) | 통과 | **0** ✓ |
| 추적 중 파일의 **수정분만** 있다 | 통과 ＋ stdout 안내 | **0** ✓ (안내 출력 확인) |
| 세 폴더 **밖**(`services/`)의 미추적 | 통과 | **0** ✓ |

- 차단 조건은 **미추적(`??`)뿐이다** — 스펙 C H6 축자가 「미추적 파일이 … 있으면」이기 때문이다.
  추적 중 수정분은 차단하지 않고 stdout 에 적는다(exit 0 의 stdout 은 「shown to Claude as context」).
- **자동 커밋하지 않는다**(v1 H9 철회). 차단문이 `git add <열거된 경로>` 를 지시하고 `git add -A`·push 를 금한다.
- `--untracked-files=all` 을 쓴다 — 디렉터리 하나로 접히면 파일 이름이 안 보이고, 그러면 「열거된 것만
  add 하라」는 지시가 성립하지 않는다.

### 2-3. H7 `lane-gate-summary.sh` — 차단 2/2 · 통과 4/4

| 케이스 | 기대 | 실측 |
|---|---|---|
| `gate-summary.json` **부재** | 차단 | **2** ✓ (「게이트를 돌리지 않은 레인」 ＋ 배출 명령 안내) |
| `counts.red_판정 = 2` | 차단 ＋ red 게이트 이름 열거 | **2** ✓ (`rls-effect`·`schema-diff` 열거 확인) |
| `counts.red_판정 = 0` | 통과 ＋ 계수 한 줄 | **0** ✓ (`green 5 / red(판정) 0 / red(준비) 0`) |
| `red_준비 = 1` · `red_판정 = 0` | 통과 ＋ 경고 | **0** ✓ |
| JSON 이 깨져 있다 | 통과(부재만 차단) | **0** ✓ |
| `COLAB_GATE_REPORT_DIR` 로 자리 지정 | 통과 | **0** ✓ |

- 스펙 C H7 축자 「**스키마 위반이 아니라 부재만** 차단하므로 게이트를 안 돌린 레인만 걸린다」 —
  그래서 깨진 JSON 은 통과시키고 그 사실만 적는다. 여기는 스키마 판정처가 아니다.
- **준비 red 로 레인 종료를 막지 않는다.** 병합 진입 조건은 판정·준비 둘 다 0 이지만(스펙 D),
  그 판정은 **오케스트레이터의 병합 시점** 몫이다. 레인 워크트리는 환경이 덜 선 상태로 존재할 수 있고,
  그것으로 종료를 막으면 훅이 상시 무력화된다. 대신 계수를 그대로 stdout 에 적는다.
- 자리 찾기 = `COLAB_GATE_REPORT_DIR`(있으면) → 없으면 `dev-package/reports/**/gate-summary.json` 중
  **가장 최근에 쓰인 것**. Bash env 는 도구 호출 간 유지되지 않으므로 실질 경로는 후자다.

### 2-4. matcher 밖 호출 · 킬스위치 — 5/5

| 케이스 | 기대 | 실측 |
|---|---|---|
| H6 에 `agent_type=lane-worker` payload | 통과(판정하지 않는다) | **0** ✓ |
| H7 에 `agent_type=researcher` payload | 통과 | **0** ✓ |
| `COLAB_HOOKS=0` ＋ H3 `push origin main` | 통과 | **0** ✓ |
| `COLAB_HOOKS=0` ＋ H6 미추적 1건 | 통과 | **0** ✓ |
| `COLAB_HOOKS=0` ＋ H7 red(판정) 1건 | 통과 | **0** ✓ |

matcher 가 이미 에이전트 타입을 거르지만(스펙 K V2), 직접 호출·오등록 대비로 스크립트도 타입을 본다.

**계 — 33케이스 · 불일치 0.**

### 2-5. 판정 근거로 삼은 문서 인용 (`https://code.claude.com/docs/en/hooks`)

- SubagentStop 입력 스키마 = `session_id`·`cwd`·`permission_mode`·`hook_event_name`·`agent_id`·
  `agent_type`·`last_assistant_message`·`stop_hook_active`.
- `cwd` — "Current working directory when the hook is invoked" ⇒ **판정 대상은 서브에이전트의 워크트리**이고
  `$CLAUDE_PROJECT_DIR`(세션이 뜬 체크아웃)와 다르다.
- `agent_type` — "Agent name (for example, `\"Explore\"` or `\"security-reviewer\"`). Present when the
  session uses `--agent` or the hook fires inside a subagent. For subagents, the subagent's type takes
  precedence over the session's `--agent` value."
- `agent_id` — "Present only when the hook fires inside a subagent call."
- `stop_hook_active` — "Boolean indicating whether a `Stop` hook is currently running. When `true`, a
  `SubagentStop` hook shouldn't start long-running operations…" ⇒ 두 훅 모두 장기 작업이 없다
  (H6 = `git status` 1회 · H7 = 파일 1개 읽기).
- matcher — "For `SubagentStart` and `SubagentStop`, the matcher filters the agent type. Example matcher
  values include `general-purpose`, `Explore`, `Plan`, custom agent names…"
- 차단 — exit 2 = "SubagentStop: **Prevents the subagent from stopping**. The blocking message is the
  reason from your JSON's blocking decision when it makes one, and your stderr text otherwise."
- 통과 시 출력 — "For `Stop` and `SubagentStop`, stdout is shown to Claude as context."
  ⇒ 안내는 stdout, 차단 사유는 stderr.
- ⚠ **exit 1 은 통과다** — "Non-blocking error. The action proceeds."(스펙 C 「차단은 exit 2 만 유효」).
  판정 불가(payload 파싱 실패·`python3` 부재·체크아웃 아님)는 전부 통과로 둔다.

---

## 3. JSON 계수 = 요약줄 — 단독 게이트 3상태 실측 (스펙 H 9행의 검증 항목)

`COLAB_GATE_REPORT_DIR` 를 준 실행에서 요약줄 `── 계 : green N / red(판정) N / red(준비) N` 과
`gate-summary.json` 의 `counts` 를 대조했다.

| 케이스 | 게이트 | 만드는 법 | 종료코드 | 요약줄 | JSON `counts` | 일치 |
|---|---|---|---|---|---|---|
| green | `exec-bit` | 그대로 | 0 | 1 / 0 / 0 | 1 / 0 / 0 | ✓ |
| red(판정) | `planning-freshness` | 기획 정본 폴더 미마운트(실물 상태) | 1 | 0 / 1 / 0 | 0 / 1 / 0 | ✓ |
| red(준비) | `exec-bit` | `COLAB_TEST_ENV_FILE=/nonexistent` | 78 | 0 / 0 / 1 | 0 / 0 / 1 (`red_준비_입력미선언` 1) | ✓ |

**3/3 일치.** 종료코드는 전부 자식 것 그대로 나간다(0 · 1 · 78) — 래퍼가 판정을 바꾸지 않는다.

부수 실측 —

- 게이트별 항목: `status`(＝ P-J 지시문 이름)와 `state`(＝ 스펙 D 예시 이름)를 **둘 다** 같은 값으로 낸다.
  `exit`·`readiness`(준비 표식 원문 또는 `null`)도 함께 적는다.
- `tree` = `d2c9d8edba5e…`(`HEAD^{tree}`) · `commit` = `16c42967…` — 전수 재실행 갈음의 대조값(`rules §3-2`).
- **상대경로 배출처**(`dev-package/reports/<회차>/<레인>`)는 레포 루트 기준으로 풀린다 — 파일 생성 확인.
- **배출처 미선언 실행은 요약줄도 JSON 도 찍지 않고 exit 0** — 기존 동작 무변경(CI 영향 0).
- `all` 갈래 배선은 **게이트 2개로 줄인 실행기 사본**으로 쟀다(전수는 이 회차에서 돌리지 않는다 ·
  `rules §3-1` 「전수는 병합 직전 1회」). 결과 = 요약줄 `1 / 1 / 0` ＝ JSON `counts` `1 / 1 / 0` ·
  `parallelism` 2 · `targets.selected` 2건 · `gates` 2건(`exec-bit` green · `planning-freshness` red_판정) ·
  `COLAB_GATE_OUTDIR` 사본도 생성. 사본은 측정 후 삭제했다(레포에 남기지 않는다).

---

## 4. 함께 돌린 게이트

| 게이트 | 결과 |
|---|---|
| `exec-bit` | **green** — `.sh` **126건** 전부 인덱스 모드 100755(100644 = 0건). 새 훅 2건은 `git update-index --chmod=+x` 로 넣었다(`rules §4-3`) |
| `work-item-consistency` | **green** — 대장 140건 · 결정 번호 316개 · stage 3 대조 15건 · 불일치 0 |

전수(`all`)는 이 회차에서 돌리지 않았다 — 변경분이 훅 2종·실행기 배선·도구 1종·문서이고, 전수는
병합 직전 1회라는 규율(`rules §3-1`)을 따른다. **다음 병합 전 진입조건이다.**

`git ls-files -s .claude/hooks/` = **7건 전부 100755**.

---

## 5. 하지 않은 것 — DB 게이트 4종의 접속 실패 분류 (P-J 선택 항목)

**착수하지 않았다.** 「classification-only 이고 몇 줄이면」이라는 조건에 맞지 않는다.

접속 실패가 판정 red 로 흘러드는 자리는 4파일 **13곳**이고, 그 각각에 **의도가 문장으로 붙어 있다** —
「접속 실패도 여기로 온다 — 못 붙은 것을 skip 으로 세지 않는다」 · 「검사를 못 한 것은 통과가 아니다」 ·
「접속 불가도 red 다」. 한 줄 분류 변경이 아니라 **선언된 규율을 뒤집는 개정**이고, 각 자리마다 셀프테스트가
붙어 있다. `_pg.sh` 의 `pg_is_readiness_error` 는 **일회용 컨테이너** 경로에서만 쓰이고, 여기 13곳은
staging·적용 DB 로의 **원격 접속** 경로다.

| 파일 | 행 | 지금 판정 |
|---|---|---|
| `gates/tools/schema-diff.sh` | 111 · **114** | red(판정) — 「선언 스키마 덤프 실패」 · 「적용 DB 덤프 실패(접속 불가도 red 다)」 |
| `gates/tools/autometa-loss.sh` | 149~150 · 183 · 261 | red(판정) — 읽기 전용 증명 실패 · 접속 롤 확인 실패 · 적용 DB 질의 실패 |
| `gates/tools/preview-tile-slot.sh` | 135~136 · 164 · 198 | red(판정) — 〃 |
| `gates/tools/artifact-ownership.sh` | 165~166 · 181 · 216 | red(판정) — 〃 |

**후속 항목**(§6-1). 착수한다면 ⑴ 스펙 D 계열의 판정(준비 red 도 red 이므로 병합 진입 조건은 불변) ⑵
4개 셀프테스트에 「접속 실패 → 78 ＋ 준비 표식」 케이스 추가 ⑶ `_pg.sh` 의 분류 함수를 원격 접속 경로에서도
쓰도록 노출 — 이 셋이 한 묶음이다. 레인 1개 몫이다.

---

## 6. 후속 항목

1. **DB 게이트 4종의 접속 실패 분류**(§5) — 13곳 · 셀프테스트 4종 동반. 레인 1개.
2. **스펙 D 예시의 필드 이름**이 `state`·`log` 이고 P-J 지시문은 `status`·`readiness` 다. 실물은 `status`·`state`
   둘 다 같은 값으로 내고 `log` 는 내지 않는다(단독 게이트에는 로그 파일이 없다 — `all` 의 `*.out` 은
   `COLAB_GATE_OUTDIR` 로 꺼낸다). 스펙 D 예시를 실물에 맞춰 정정하면 두 이름을 하나로 줄일 수 있다.
3. **H7 의 `COLAB_GATE_REPORT_DIR` 경로는 훅 환경에 거의 안 실린다** — Bash env 는 도구 호출 간 유지되지
   않기 때문이다. 실질 경로는 「가장 최근 `gate-summary.json`」이고, 한 워크트리에서 여러 회차를 돌리면
   **가장 최근 것 하나만** 판정 대상이 된다. 회차 폴더를 레인마다 새로 주는 지금 규약에서는 문제가 없다.
4. **전수 1회**(`all -j 4`)가 다음 병합 전 진입조건으로 남아 있다 — 이 회차는 단독 게이트만 돌렸다(§4).
