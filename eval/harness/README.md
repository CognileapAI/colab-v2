# eval/harness — 하네스 자체를 재는 실과제

`CLAUDE.md`·`.claude/skills/**`·`.claude/hooks/**`·`.claude/agents/**` 를 고쳤을 때 **문안이 실제 행동을
바꾸는지**를 잰다. 기존 `eval/` 세 벌(`k4-search/`·`s2b-alayer*/`)은 **D10 제안·검색 품질**을 재고,
여기는 **하네스 품질**을 잰다 — 대상도 주기도 다르다(intent Q1).

- 수용 근거 = 「읽어 보니 낫다」가 아니라 **개정 전 red → 개정 후 green**.
- 규칙 **「사고 1건 = eval 1건」** — `CLAUDE.md §5-b` 에 줄이 늘면 여기에도 과제가 하나 는다.
- 실제 모델을 부른다. 그래서 **지침 4경로가 바뀔 때만** 돈다(intent Q2).

## 실행

```bash
COLAB_EVAL_TIMEOUT=150 COLAB_EVAL_BUDGET=2.01 bash eval/harness/run.sh
COLAB_EVAL_TIMEOUT=150 COLAB_EVAL_BUDGET=2.01 COLAB_EVAL_ONLY=H01 bash eval/harness/run.sh
```

| 변수 | 뜻 | 미선언이면 |
|---|---|---|
| `COLAB_EVAL_TIMEOUT` | 1회 실행의 초 상한(`timeout`) | **red(준비 · 78)** |
| `COLAB_EVAL_BUDGET` | 1회 실행의 달러 상한(`--max-budget-usd`) | **red(준비 · 78)** |
| `COLAB_EVAL_ONLY` | 한 과제만(예 `H01`) | 전수 |

⛔ **관대한 기본값을 두지 않는다.** `${VAR:-180}` 같은 대입이 있으면 상한이 사실상 없어지고,
「상한 초과」가 조용한 통과로 바뀐다(`CLAUDE.md §4`).

## 세 상태 · exit

| 상태 | exit | 언제 |
|---|---|---|
| green | 0 | 모든 과제가 **2/2** 통과 |
| red(판정) | 1 | 과제 0건 · 1/2 「불안정 — 과제 설계 결함」 · 0/2 「실패」 |
| red(준비) | 78 | 상한 변수 미선언 · `task.md`/`fixture/`/`expect.sh` 부재 · 시간·예산 상한 초과 · `claude` 비정상 종료 · **결과가 오류**(`is_error:true` · `subtype != success`) · `mode` 본문이 `rate` 가 아님(알 수 없는 mode) |
| rate | — (exit 를 정하지 않는다) | `mode`=rate 과제 — 2회 그대로 돌리고 `rate x/2` 로 적는다. green·불안정 계수와 판정실패 관측에 넣지 않는다(**회귀 집합 제외**). 판정기 78·비정상 종료·상한 초과는 그대로 red(준비) |

- **2회 실행 · 2/2 만 통과**(intent Q8). 비결정을 허용하면 재는 것이 하네스가 아니라 운이 된다.
- 요약줄 — `과제 N · 실행 M · green N · 불안정 N · 준비 N · 초 p50 X/p95 Y · USD 합 Z · 판정실패 관측 과제 N · rate N`.
  `rate` 칸은 맨 끝이다(앞 칸의 prefix 대조를 깨지 않는다) · 게이트 실행 모드는 `통과 ＋ rate == 과제` 로 대조한다.
  `불안정` 칸은 **판정 red 전체**(1/2 불안정 ＋ 0/2 실패)를 센다. 어느 쪽인지는 과제별 줄과
  `results/<회차>/summary.md` 표의 `판정` 열에 나온다.
- 판정 red 와 준비 red 가 함께 나면 exit 은 **1**. 병합 진입 조건은 **둘 다 0** 이다.

### 비율 측정 과제 (`mode`=rate)

과제 디렉터리의 `mode` 파일(본문 정확히 `rate` 한 줄)이 표지다. **부재 = pass/fail**(엄격이 기본) · 그 밖의 본문 = red(준비).
`task.md` 안에 두지 않는다(전문이 프롬프트다). 표지는 설정 해시 집합 안이라 PR diff 에 반드시 보이고, PR 본문
`Rate-Tasks:` 필드(`scripts/harness/pr_contract.py` · 값 = head 트리의 rate 과제 정렬 목록 · 0건이면 `없음`)가 같은 목록을 요구한다.
`expect.sh` 는 바꾸지 않는다 — 바뀌는 것은 집계 분류뿐이다. 새 rate 과제는 아래 표에 판정 회차와 함께 적는다
(`harness-contract` 가 표에 없는 rate 과제와 최근 3회차 연속 `rate 0/2` 를 warning 으로 낸다 · exit 불변).

| 과제 | 판정 회차 | 왜 비율인가 |
|---|---|---|
| `H18-three-states` | 15라운드(2026-09-26 · Fable blind 판정 ＋ 검증 8건 · Ted 「권고대로」) | 규약(`AGENTS.md`) 도달률을 잰다 — 상태3 exit 78 응답이 회차마다 갈린다(기록 green 6 · red 4 · `tests/expect-replay.sh`). 흔들림 자체가 신호라 `task.md` 에 78 을 적지 않는다(14라운드) |

## 과제 형식

```
eval/harness/H<번호>-<이름>/
  task.md      판정받는 에이전트가 stdin 으로 받는 **프롬프트 전문**. 주석·머리말도 프롬프트다.
  fixture/     과제가 볼 수 있는 전부. 러너가 cwd 와 --add-dir 을 여기로 고정한다.
  fixture/SOURCE.md   옛값을 어디서 떠 왔는지 — `git show <sha>:<path>` 명령을 축자로 적는다.
  expect.sh    stdin = 모델 응답 본문. exit 0 = green. 판정 정본은 이 파일 하나다.
  mode         (선택) 본문 `rate` 한 줄 = 비율 측정 과제(위 「비율 측정 과제」). 부재 = pass/fail.
```

- 뼈대는 `_template/` — 복사해 쓴다. `_template` 은 `H??-*` 가 아니므로 **전수에서 빠진다**.
- 픽스처는 **사본**이다. 제품 파일을 제자리에서 고쳐 과제를 만들지 않는다(라운드 §3 ㉴).
- `expect.sh` 는 **양성 단언 ＋ 음성 단언**을 함께 둔다 — 「맞는 말을 했는가」와
  「해서는 안 되는 것을 했는가」는 다른 물음이다(예: 수정 명령이 나오면 red).
- 새 `.sh` 는 `git update-index --chmod=+x <파일>` 뒤 커밋한다(NTFS · `core.filemode=false`).

## 상한

⭑ ⟨확정 2026-09-08 · WU-D6 첫 실측 `results/20260908-161538`(20건×2회 = 40실행)⟩

| 값 | 현재 | 근거 |
|---|---|---|
| `COLAB_EVAL_TIMEOUT` | **150** | ⭑ ⟨갱신 2026-09-26 · S-red⟩ H18 이 회차 `20260926-125205`·`140939`·`143218` 에서 60–95초를 쟀고 93초가 회차 2(`140939`)에서 red(준비)를 냈다 → 150. 게이트 안내문(`gates/tools/harness-eval.sh` `RUN_HINT`)·위 「실행」과 같은 값. ／ 종전 ~~93~~(실측 p95 46.4초 × 2) · ~~180(초안)~~ |
| `COLAB_EVAL_BUDGET` | **2.01** | 1회 최대 **1.0067** USD(H08 1회차) × 2 = 2.0134 → 2.01. ／ 종전 ~~0.50(초안)~~ |
| 실측 p50 / p95 / 최대 | **32.8 / 46.4 / 46.6** 초 | 40실행 표본 · `results/20260908-161538/summary.md` |
| 과제별 최대 USD | **1.0067**(1회) · **1.9523**(2회 합 · H08) | 같은 회차 |
| 회차 총액 | **32.4506** USD / 40실행 | 1실행 평균 0.81 |

⚠ **초안 예산 `0.50` 은 바닥에 못 미쳤다** — 스모크 `results/20260908-161309` 에서 **1턴 만에**
`total_cost_usd 0.713246` · `subtype: error_max_budget_usd` 로 끊겼다. 원인은 과제 본문이 아니라
**매 호출의 컨텍스트 적재**다(`cacheCreationInputTokens 34840` — 러너의 cwd 가 레포 안이라
프로젝트 `CLAUDE.md` ＋ `.claude/rules/colab-rules.md` 가 호출마다 실린다).
그래서 첫 실측은 예산을 **3.00** 으로 올려 돌렸고, 위 값은 그 실측에서 나온 것이다.
⛔ 이 예산을 다시 `0.50` 으로 되돌리면 **20건 전부가 red(준비)** 가 되어 아무것도 재지 못한다.

⚠ 상한 초과는 **skip 이 아니라 red(준비)** 다. 그 과제는 「상한 미확정」으로 표에 남는다(우려 1 ⓐ).

## ALLOWED — `--allowedTools` 정본

정본 파일은 **`eval/harness/allowed.txt` 하나**다. `run.sh` 가 그 파일을 읽어 쉼표로 잇고,
아래 표는 같은 문자열을 사람이 읽으라고 옮긴 것이다 — 둘이 갈리면
`tests/run-selftest.sh` 가 문자열 대조로 red 를 낸다.

| 항목 | 왜 |
|---|---|
| `Read` · `Grep` · `Glob` | 픽스처를 읽고 찾는다 |
| `Bash(git log:*)` · `Bash(git show:*)` · `Bash(git diff:*)` | 옛값·회차 확인(H01·H20 계열) |
| `Bash(sed -n:*)` · `Bash(grep:*)` · `Bash(ls:*)` · `Bash(cat:*)` · `Bash(wc:*)` | 줄·건수 대조 |
| `Bash(python3 {FIXTURE}/css_audit.py --root {FIXTURE}:*)` | 계측기 — **경로를 픽스처 사본으로 고정** |

- `{FIXTURE}` = 그 과제 `fixture/` 의 절대경로. 러너가 실행 직전에 치환한다.
- 계측기와 그 경로 인자를 픽스처 사본에 고정하는 이유 — **경로 인자가 자유이면 읽기 전용이 깨진다**
  (advisor ① · spec 우려 10).
- 쓰기 도구(`Edit`·`Write`)를 넣지 않는다. 과제는 **판정**을 재지 수정 능력을 재지 않는다(intent Q11).
- ⛔ `--dangerously-skip-permissions` 를 러너에 박지 않는다. 권한은 `--allowedTools` 로만 준다.

**실측 (`claude --version` 2.1.263 · `claude --help`)**

| 항목 | 실측값 |
|---|---|
| `--allowedTools, --allowed-tools <tools...>` | "Comma or space-separated list of tool names to allow (e.g. \"Bash(git *) Edit\")" |
| `--output-format <format>` | `text`(기본) · `json`(단건 결과) · `stream-json` — `--print` 에서만 |
| `--max-budget-usd <amount>` | "Maximum dollar amount to spend on API calls" — `--print` 에서만 |
| `--no-session-persistence` | 세션을 디스크에 남기지 않음 — `--print` 에서만 |
| `--max-turns` | **부재** — 턴 상한은 쓸 수 없다 |
| 비용 필드 이름 | **`total_cost_usd`** ⭑ ⟨확정 2026-09-08 · WU-D6 첫 실측⟩ ／ 종전 ~~`[미상]`~~ — `H01.raw.1.json` 에 `"total_cost_usd":0.713246` 실재. `cost_usd` 는 없다. 러너의 폴백 순서(`total_cost_usd` → `cost_usd`)는 그대로 둔다 |
| 항목 안의 공백 | **쪼개지지 않는다 · 그대로 받는다** ⭑ ⟨확정 2026-09-08 · H02 첫 실측⟩ ／ 종전 ~~`[미상]`~~ — H02 가 `Bash(python3 {FIXTURE}/css_audit.py --root {FIXTURE}:*)` 를 실제로 써서 **green 2/2** 이고 `permission_denials` 가 **`[]`** 다. 러너가 쉼표로 이어 한 인자로 넘기는 방식이 맞다 |
| 모델 | **`claude-fable-5-1`** ＋ 보조 `claude-haiku-4-5`(`modelUsage` 실측). 러너는 모델을 지정하지 않으므로 호출 환경의 기본값을 탄다 |

⭑ 러너가 `--output-format json` 을 쓰는 이유 — 요약줄의 `USD 합` 은 **text 로는 셀 수 없다**
(`text` 출력에 비용이 없다). 응답 본문은 JSON 의 `result` 에서 꺼내 `expect.sh` 의 stdin 으로 넘기므로
`expect.sh` 가 보는 것은 `text` 로 돌렸을 때와 같다.

⭑ ⟨증보 2026-09-08 · advisor ②⟩ 러너는 `result` 만 읽지 않는다 — `is_error:true` 이거나 `subtype` 이 있고
`success` 가 아니면 그 회차를 **red(준비)** 로 돌리고 `expect.sh` 에 넘기지 않는다. 사유는 `claude 오류 결과(subtype=<값>)`.
그 검사가 없으면 `{"is_error":true,"result":"<기대와 맞는 문장>"}` ＋ rc 0 이 **2/2 green** 이 된다(시험 ⓖ).

## 결과

`eval/harness/results/<YYYYMMDD-HHMMSS>/` — 러너가 회차마다 **여섯 종**을 쓴다:
`summary.md`(과제별 판정·초·USD 표 ＋ 요약줄 ＋ 「설정 해시」 줄) · `config-hash.json`(이 회차를 잰 설정 해시 ·
아래 「설정 해시 · 면제 조건」) · `H??.out.{1,2}.txt`(응답 본문) ·
`H??.expect.{1,2}.txt`(`expect.sh` 의 판정 출력 — red 사유가 여기 있다 · `run.sh:190`) ·
`H??.raw.{1,2}.json`(응답 원문) · `H??.err.{1,2}.txt`(표준오류).
회차 이름은 **초 단위**다(⟨증보 2026-09-08⟩ 종전 ~~`<YYYYMMDD-HHMM>`~~ — 같은 분에 두 번 돌리면 앞 회차를 덮었다).
러너는 요약 직전에 `허용 도구 정본: <경로>` 한 줄을 낸다 — 정본이 바꿔치기되면 출력에서 보인다.

**이 폴더는 커밋한다.** 승격 조건이 **3회 연속 2/2 green**(intent Q10 · ⭑ ⟨2026-09-26 · 15라운드⟩ 대상 =
pass/fail 과제 19건 — `mode`=rate 과제 제외)이라 회차 기록이 체크아웃을
넘어 남아야 하고, `eval/` 의 선례도 실측 산출을 추적한다
(`s2b-alayer/baseline.json` · `s2b-alayer-g2/baseline-g2.json`).

⭑ ⟨갱신 2026-09-26 · E0⟩ **추적하는 것은 여섯 종 중 넷이다** —
`summary.md` · `config-hash.json` · `H??.out.{1,2}.txt` · `H??.expect.{1,2}.txt`. 나머지 둘은 `results/.gitignore` 가 뺀다.
／ 종전 ⟨확정 2026-09-08 · WU-D6⟩ 추적 3종(`config-hash.json` 이전) · 그 전 ~~「이 폴더는 커밋한다(`.gitignore` 에
넣지 않는다)」~~ — 부분집합을 적지 않아 전 종이 추적 대상으로 읽혔다.

| 종 | 추적 | 왜 |
|---|---|---|
| `summary.md` | **한다** | 승격 판정의 정본. 판정·초·USD 가 한 표에 있다 |
| `config-hash.json` | **한다** | 「어느 설정에서 잰 결과인가」. 게이트 면제 분기가 현재 설정 해시와 대조한다 · `.gitignore` 제외 패턴에 걸리지 않아 자동 추적 |
| `H??.out.{1,2}.txt` | **한다** | 「무엇을 답했는가」. 회귀를 읽는 자리 · ⭑ ⟨2026-09-26 · S-red⟩ 러너 저장소 절대경로는 `<repo>` 로 치환해 쓴다(사용자 홈 경로 비노출 · 판정기 입력은 원문) · 그 전 회차 파일은 그대로 |
| `H??.expect.{1,2}.txt` | **한다** | 「왜 red 였는가」. 불안정 과제의 판독 근거 |
| `H??.raw.{1,2}.json` | 안 한다 | 본문이 `out` 과 중복 · `session_id`·`uuid` 가 회차마다 바뀌어 diff 만 늘린다. 비용·초는 `summary.md` 에 있다 |
| `H??.err.{1,2}.txt` | 안 한다 | 성공 회차에서 빈 파일 · 실패 회차 내용은 `summary.md` 「사유」 칸에 인용된다 |

## 설정 해시 · 면제 조건

결과가 **어느 설정에서 잰 것인가**를 기계가 대조한다(spec `dev-package/prd/specs/S-HARNESS-E0-EVAL-GATE-20260926.md` §4.1 · §4.3).

- **정본** = `eval/harness/config-paths.txt` 한 파일 — `AGENTS.md` · `CLAUDE.md` · `.claude/**` · `.agents/**` ·
  `gates/**` · `scripts/harness/hooks/**` · `eval/harness/**`(`results/**` 제외) · 자기 자신. 계산기 = `eval/harness/config_hash.py`.
  러너 · 게이트 · `gates/tools/ci-filter-check.py`(CI `harness` 필터 ⊇ 정본) 가 같은 파일을 읽는다.
- **계산** — 파일 집합 = `git ls-files --cached --others --exclude-standard`(추적 + 비무시 미추적) · 파일마다
  blob sha1(= `git hash-object`) · symlink 는 링크 텍스트(대상이 집합 밖 파일이면 대상 본문 포함) · 깨진 링크 `missing` ·
  정렬된 `path\0sha\n` 의 sha256. **내용 기준**이라 dirty 로 잰 편집을 그대로 커밋하면 같은 해시다.
  `config-hash.json` = `hash` · `files` · `head` · `dirty` · `selected` · `patterns_sha256` · `claude_version` · `computed_at`.
- **면제 판정**(`COLAB_HARNESS_EVAL_EXEMPT=1 bash gates/run.sh harness-eval` · `config_hash.py verify`) —
  현재 해시와 일치하는 전수 결과(`selected == all` · 요약줄 `준비 0` · 과제 행 수 == 과제 N) 없음·입력 손상 = **78**
  (`missing=eval-result:<hash>`) · 회귀 = **1** · 일치 ＋ 무회귀 = **0**(run id · `hash(head)=hash(회차)` 출력).
- **회귀 규칙** — 일치 결과 중 id 최대 = R\*. 직전 = R\* 보다 id 가 작고 `summary.md` 가 있으며 과제 행 수 == 과제 N 인
  최신 전수 결과(해시 없는 옛 결과 포함 · 선택 실행 제외 · 행이 모자란 중단 회차 제외 — 중단 회차로 「회귀 0」을 만들지 않는다). `green(직전) − green(R*) − rate(R*) ≠ ∅` 이면 1(과제 이름 나열). 직전이 없으면 회귀 기준이 없다(0).
  rate(R\*) = R\* 표의 `rate [0-2]/2` 행 — `rate` 로 시작하는 그 밖의 칸 = 78 · rate 행 집합 ≠ 현재 트리의
  `eval/harness/H??-*/mode`(본문 `rate`) 집합 = 78(「해시 일치 결과 아님」 — `results/**` 는 해시 밖이라 행을 손으로
  `rate` 로 바꾸는 우회를 막는다). green 줄에 `rate n(<과제> x/2)` 가 나온다.
- **회차 무효화** — 회차는 병합 직전 head 에서 1회. 그 뒤 해시 집합 파일을 push 하면 게이트가 78 로 돌아간다.
  base(develop) 병합이 집합 파일을 건드리지 않으면 해시 불변 · 건드리면 재실측(≈32 USD). CI 는 머지 커밋 트리에서 계산한다.
- **30일 경고** — 러너는 모델을 지정하지 않아 모델·CLI 가 저장소 diff 없이 바뀐다. `harness-contract`
  (`scripts/harness/check.py`)가 최신 결과 id 가 30일보다 오래되면 `warning: harness-eval newest result <id> is <n> days old (>30)`
  1줄을 낸다(exit 불변 · 신호) · green 줄에 `harness-eval newest <id> (<n>d)` · 결과 디렉터리 0건 = 78.

## 시험

```bash
bash eval/harness/tests/run-selftest.sh    # 22/22 · 실제 모델 호출 0회(claude 를 PATH 스텁으로 대체)
bash eval/harness/tests/expect-replay.sh   # H12·H15·H16·H18 expect 를 기록 6회차 응답·오답 모형으로 재생 · 모델 호출 0회
```

## 자리

| 무엇 | 어디 |
|---|---|
| 로스터 20건(과제 정의 정본) | `dev-package/intent/2026-09-08-harness-evals.md` |
| 요구 정본 | `dev-package/prd/specs/R-D.md` · 실행 뷰 `dev-package/prd/rounds/R-D-2-harness-eval.md` |
| 게이트 승격 | `harness-eval` — pass/fail 과제 19건(`mode`=rate 제외)이 3회 연속 2/2 green 뒤(WU-D7) · 면제 조건은 이미 설정 해시에 결합(위 「설정 해시 · 면제 조건」) |
