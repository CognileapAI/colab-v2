# harness-eval — 구독(로그인 `claude` CLI) 실행 조사

조사일 2026-09-12 · 읽기 전용 · 게이트 미실행 · 미승인 초안

## ① 결론

- 러너는 **처음부터 구독 경로다** — `claude -p`(로그인 계정)만 부른다. `ANTHROPIC_API_KEY`·SDK 참조 0건.
- 따라서 「API 를 쓰자」는 요청은 **스크립트 근거가 없는 오요청**이다. 고칠 코드 없음.
- 이 회차는 `CLAUDE.md` 가 이미 바뀌어 **게이트 범위 안**이다.

## ② 판정 근거 (Ted 판정)

- 요지 — 하네스 평가 게이트는 구독 모델로 실행하고, 면제 선언이 아니며, API 예산 질의를 하지 않는다.
- 근거 `dev-package/reports/issues/2026-09-12-ted-decisions.md:34` —
  > **하네스 평가 게이트 = 구독 모델로 실행** — 원문 「아니 이건 하네스 평가게이트는 구독 모델 이용하자고 했잖아 왜 또 Api쓰자고하냐 이건 계속 잘못된 요청이 온다.」 면제 선언 아님 · API 예산 질의 금지
- `PLAN-SoT §9` 번호 〈N〉 **없음** — 이 판정은 아직 원장 미등재(등재는 마감 단계 항목).
- `PLAN-SoT.md:313` ㊷ 의 「ChatGPT 구독으로 런타임 구동 금지」는 **제품 런타임 모델 공급자** 결정이고 하네스 평가와 별건이다 — 혼동 금지.

## ③ 호출 경로 (스크립트 앵커)

- `gates/run.sh:273-281` → `gates/tools/harness-eval.sh` · `harness-eval.sh:35,63` → `eval/harness/run.sh`.
- `eval/harness/run.sh:120-126` 실제 호출 —
  > `timeout "$COLAB_EVAL_TIMEOUT" claude -p --output-format json --allowedTools "$ALLOWED" --no-session-persistence --add-dir "$FIXABS" --max-budget-usd "$COLAB_EVAL_BUDGET"`
- `run.sh:55-56` 전제 = `command -v claude`. 부재 시 red(준비 78). API 키 검사 항목 **없음**.
- `.github/workflows/ci.yml:454-455` — 「모델 평가는 로컬 러너에서 실행한다(2026-09-08 사용자 요청) / 이 잡은 … 모델 API 키가 필요 없다」. CI 는 `COLAB_HARNESS_EVAL_EXEMPT=1` 면제 모드.

## ④ 환경변수 뜻

| 변수 | 뜻 | 미선언 시 |
|---|---|---|
| `COLAB_HARNESS_EVAL=1` | 실제 실행 선언(`harness-eval.sh:55`) | red(준비 78) |
| `COLAB_EVAL_TIMEOUT` | 1회 실행 초 상한(`timeout`) · 확정 **93**(`eval/harness/README.md:63`, p95 46.4×2) | red(준비 78) |
| `COLAB_EVAL_BUDGET` | `--max-budget-usd` 인자 · 확정 **2.01**(`README.md:64`, 1회 최대 1.0067×2) | red(준비 78) |

- BUDGET 은 **구독에서도 필수**다 — 러너가 CLI 인자로 그대로 넘기고(`run.sh:125`), 미선언이면 `run.sh:51` 이 78 을 낸다.
- [추론] 구독 로그인에서 `--max-budget-usd` 는 청구액이 아니라 **CLI 가 계산한 비용 환산액**의 상한이다. 근거 = 계정에 API 키가 없는 상태에서 `subtype: error_max_budget_usd` 가 실제로 발생했다(`README.md:69-71`). 「달러 지출 승인」을 뜻하지 않는다.
- ⛔ `0.50` 으로 낮추면 20건 전부 red(준비)(`README.md:74`).

## ⑤ 과제 묶음·산출물

- 과제 **20건** — `eval/harness/H01-…`~`H20-ledger-first` (`H??-*/` 디렉터리 실계수 기준).
- 과제당 2회(`run.sh:35`) = 40실행. 판정 2/2 green · 1/2 불안정(red 판정) · 0/2 실패(red 판정).
- 산출 = `eval/harness/results/<YYYYMMDD-HHMMSS>/summary.md` ＋ 회차별 `H??.raw|out|expect.*`.

## ⑥ 실행 명령 (준비 완료 · 미실행)

```
cd "<worktree>" && COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=93 COLAB_EVAL_BUDGET=2.01 bash gates/run.sh harness-eval
```

- 증거 연계가 필요하면 앞에 `COLAB_TASK_ID=<task_id> COLAB_GATE_REPORT_DIR=dev-package/reports/bugfix-260912/<레인>` 을 덧붙인다(`gates/run.sh:30,57`).
- 병렬성 `serial` 고정(`gates/config/parallelism.toml:223`) · 전수와 동시 실행 금지(`colab-rules §9`).

## ⑦ 전제 실측 (이 워크트리)

- `claude` 존재 = **yes** — `bash -c 'command -v claude'` → `~/.npm-global/bin/claude` · `claude --version` = **2.1.269 (Claude Code)**.
- 로그인 = **yes · 구독** — `~/.claude/.credentials.json` 에 `claudeAiOauth` · `subscriptionType: "max"` · scope `user:inference`(토큰 미출력).
- `ANTHROPIC_API_KEY`·`ANTHROPIC_AUTH_TOKEN` = **unset** · `~/.colab-v2-test.env` 에 `ANTHROPIC` 0건 · settings 에 `apiKeyHelper` 0건. 구독 경로 외 대안 없음.
- 대화형 zsh 에 `claude` → `claude --dangerously-skip-permissions` alias 존재. 러너는 bash 비대화형이라 alias 미적용(`run.sh:28` 금지 규약 유지).

## ⑧ 범위 판정

- `git diff --stat origin/main..HEAD -- CLAUDE.md .claude/` = `CLAUDE.md | 2 +-` (1행). **이미 범위 안**.
- 내용 = `§0` stage 표 세 번째 단 괄호에서 `OP-NOTIFY-1` 제거 · 18항목 → 17항목.
- 마감 단계의 `CLAUDE.md §0` 괄호 추가 편집도 같은 파일이라 **그 한 건만으로도 범위가 성립**한다(필터 `harness` = `CLAUDE.md`·`.claude/skills|hooks|agents/**` · `ci.yml:81`).

## ⑨ 후속 항목 (고치지 않음)

1. `gates/README.md:157` 에 `secrets.ANTHROPIC_API_KEY` 문면이 남아 있다 — `ci.yml` 은 이미 키를 쓰지 않는다. 문서 드리프트이자 「API 쓰자」 오요청의 재발원. 정정 대상.
2. 마지막 전수 실적 = `eval/harness/results/20260908-161538` — **green 15 / 불안정 2 / 실패 3 / 준비 0** → 러너 exit **1(red 판정)**. 결과 디렉터리는 2026-09-08 3건뿐이고 이후 실행 0건. 지금 실행하면 **red(판정) 가 나올 개연성이 높다**(과제 설계 결함 5건 미수정 · 라운드 §3 ㉴ 로 방치 결정).
3. 승격 조건(3회 연속 2/2 green · intent Q10) 미달 상태 유지 — 이번 실행은 승격이 아니라 회차 1회째 재계수.

## ⑩ 미확인

- `[미확인]` 이번 실행의 실소요·비용 환산 — 게이트를 돌리지 않았다. 직전 실측(40실행 · 32.4506 USD 환산 · p95 46.4s)만 있고 현 과제·현 `CLAUDE.md` 기준 재측정값 없음.
- `[미확인]` 구독 rate limit 소진량 — 40실행이 Max 한도에서 차지하는 비율을 재지 않았다.
