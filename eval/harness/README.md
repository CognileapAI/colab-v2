# eval/harness — 하네스 자체를 재는 실과제

`CLAUDE.md`·`.claude/skills/**`·`.claude/hooks/**`·`.claude/agents/**` 를 고쳤을 때 **문안이 실제 행동을
바꾸는지**를 잰다. 기존 `eval/` 세 벌(`k4-search/`·`s2b-alayer*/`)은 **D10 제안·검색 품질**을 재고,
여기는 **하네스 품질**을 잰다 — 대상도 주기도 다르다(intent Q1).

- 수용 근거 = 「읽어 보니 낫다」가 아니라 **개정 전 red → 개정 후 green**.
- 규칙 **「사고 1건 = eval 1건」** — `CLAUDE.md §5-b` 에 줄이 늘면 여기에도 과제가 하나 는다.
- 실제 모델을 부른다. 그래서 **지침 4경로가 바뀔 때만** 돈다(intent Q2).

## 실행

```bash
COLAB_EVAL_TIMEOUT=180 COLAB_EVAL_BUDGET=0.50 bash eval/harness/run.sh
COLAB_EVAL_TIMEOUT=180 COLAB_EVAL_BUDGET=0.50 COLAB_EVAL_ONLY=H01 bash eval/harness/run.sh
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
| red(준비) | 78 | 상한 변수 미선언 · `task.md`/`fixture/`/`expect.sh` 부재 · 시간·예산 상한 초과 · `claude` 비정상 종료 |

- **2회 실행 · 2/2 만 통과**(intent Q8). 비결정을 허용하면 재는 것이 하네스가 아니라 운이 된다.
- 요약줄 — `과제 N · 실행 M · green N · 불안정 N · 준비 N · 초 p50 X/p95 Y · USD 합 Z`.
  `불안정` 칸은 **판정 red 전체**(1/2 불안정 ＋ 0/2 실패)를 센다. 어느 쪽인지는 과제별 줄과
  `results/<회차>/summary.md` 표의 `판정` 열에 나온다.
- 판정 red 와 준비 red 가 함께 나면 exit 은 **1**. 병합 진입 조건은 **둘 다 0** 이다.

## 과제 형식

```
eval/harness/H<번호>-<이름>/
  task.md      판정받는 에이전트가 stdin 으로 받는 **프롬프트 전문**. 주석·머리말도 프롬프트다.
  fixture/     과제가 볼 수 있는 전부. 러너가 cwd 와 --add-dir 을 여기로 고정한다.
  fixture/SOURCE.md   옛값을 어디서 떠 왔는지 — `git show <sha>:<path>` 명령을 축자로 적는다.
  expect.sh    stdin = 모델 응답 본문. exit 0 = green. 판정 정본은 이 파일 하나다.
```

- 뼈대는 `_template/` — 복사해 쓴다. `_template` 은 `H??-*` 가 아니므로 **전수에서 빠진다**.
- 픽스처는 **사본**이다. 제품 파일을 제자리에서 고쳐 과제를 만들지 않는다(라운드 §3 ㉴).
- `expect.sh` 는 **양성 단언 ＋ 음성 단언**을 함께 둔다 — 「맞는 말을 했는가」와
  「해서는 안 되는 것을 했는가」는 다른 물음이다(예: 수정 명령이 나오면 red).
- 새 `.sh` 는 `git update-index --chmod=+x <파일>` 뒤 커밋한다(NTFS · `core.filemode=false`).

## 상한

| 값 | 현재 | 근거 |
|---|---|---|
| `COLAB_EVAL_TIMEOUT` | **180**(초안) | `eval/s2b-alayer/run.py` `subprocess` 상한 선례 · 실측 전 |
| `COLAB_EVAL_BUDGET` | **0.50**(초안) | intent Q7 초안값 · 실측 전 |
| 실측 p95 | `[미측정]` | WU-D6 첫 실측(20건×2회)에서 채운다 → 상한 = **p95×2** |
| 과제별 최대 USD | `[미측정]` | 같은 실측에서 채운다 → 예산 = **최대×2** |

⚠ 초안값 초과는 **skip 이 아니라 red(준비)** 다. 그 과제는 「상한 미확정」으로 표에 남는다(우려 1 ⓐ).

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
| 비용 필드 이름 | **`[미상]`** — `--help` 는 JSON 필드를 적지 않는다. 러너는 `total_cost_usd`·`cost_usd` 를 찾고, 없으면 요약에 `[미상]` 을 적는다. 확정은 **WU-D6 첫 실측** |
| 항목 안의 공백 | **`[미상]`** — `--help` 축자가 "Comma or **space**-separated" 이므로 `Bash(python3 … --root …:*)` 처럼 공백이 든 항목이 쪼개질 수 있다. 러너는 쉼표로 이어 **한 인자**로 넘긴다. 확인은 그 항목을 처음 쓰는 **H02 첫 실측** |

⭑ 러너가 `--output-format json` 을 쓰는 이유 — 요약줄의 `USD 합` 은 **text 로는 셀 수 없다**
(`text` 출력에 비용이 없다). 응답 본문은 JSON 의 `result` 에서 꺼내 `expect.sh` 의 stdin 으로 넘기므로
`expect.sh` 가 보는 것은 `text` 로 돌렸을 때와 같다.

## 결과

`eval/harness/results/<YYYYMMDD-HHMM>/` — `summary.md`(과제별 판정·초·USD 표 ＋ 요약줄) ·
`H??.out.{1,2}.txt`(응답 본문) · `H??.raw.{1,2}.json`(원문) · `H??.err.{1,2}.txt`.

**이 폴더는 커밋한다**(`.gitignore` 에 넣지 않는다). 승격 조건이 **3회 연속 2/2 green**(intent Q10)이라
회차 기록이 체크아웃을 넘어 남아야 하고, `eval/` 의 선례도 실측 산출을 추적한다
(`s2b-alayer/baseline.json` · `s2b-alayer-g2/baseline-g2.json`).

## 시험

```bash
bash eval/harness/tests/run-selftest.sh    # 6/6 · 실제 모델 호출 0회(claude 를 PATH 스텁으로 대체)
```

## 자리

| 무엇 | 어디 |
|---|---|
| 로스터 20건(과제 정의 정본) | `dev-package/intent/2026-09-08-harness-evals.md` |
| 요구 정본 | `dev-package/prd/specs/R-D.md` · 실행 뷰 `dev-package/prd/rounds/R-D-2-harness-eval.md` |
| 게이트 승격 | `harness-eval` — 3회 연속 2/2 green 뒤(WU-D7) |
