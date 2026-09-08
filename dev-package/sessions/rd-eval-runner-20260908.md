# WU-D5 · 하네스 eval 러너 — 레인 `rd-eval-runner` (2026-09-08)

라운드 `dev-package/prd/rounds/R-D-2-harness-eval.md` · spec `dev-package/prd/specs/R-D.md` · intent `dev-package/intent/2026-09-08-harness-evals.md` · 기점 `origin/integration/r-d` `785ed88`.

## 전 / 후

| | 전 | 후 |
|---|---|---|
| `eval/harness/` | 부재 | `run.sh` · `allowed.txt` · `README.md` · `_template/{task.md,fixture/SOURCE.md,expect.sh}` · `tests/run-selftest.sh` |
| `eval/README.md` 하네스 표 | 3행 | **4행**(`harness/` 추가 · 기존 3행·경고문 무삭제) |
| 제품 코드 · 계약 · 마이그레이션 | — | **0 · 0 · 0** (`git diff --stat` 대상 = `eval/` ＋ 세션 노트) |

## 실측 — `claude` 2.1.263 (`claude --version`)

- 쓴 인자 = `-p` · `--output-format json` · `--allowedTools <한 인자·쉼표 결합>` · `--no-session-persistence` · `--add-dir <fixture 절대경로>` · `--max-budget-usd` · 바깥에 `timeout`. `--max-turns` **부재**.
- `--allowedTools, --allowed-tools <tools...>` 축자 = "Comma or space-separated list of tool names to allow (e.g. \"Bash(git *) Edit\")" · `--output-format` 선택지 = `text`·`json`·`stream-json`.
- ⭑ **`--output-format` 을 `text` → `json` 으로 바꿨다.** 사유 = 요약줄이 요구하는 `USD 합` 이 `text` 출력에는 없다. `expect.sh` 가 보는 stdin 은 JSON 의 응답 본문만 꺼내 넘기므로 `text` 로 돌렸을 때와 같다.
- 비용 필드 이름 = **`[미상]`** — `--help` 가 JSON 필드를 적지 않는다. 러너는 `total_cost_usd`·`cost_usd` 를 찾고 없으면 `[미상]` 을 적는다(지어내지 않음).
- `--allowedTools` 항목 안 공백 처리 = **`[미상]`** — 축자가 "Comma or **space**-separated" 라 `Bash(python3 … --root …:*)` 가 쪼개질 수 있다. 확인 자리 = 그 항목을 처음 쓰는 **H02 첫 실측**(D6).

## RED → GREEN

- RED 선실측 = `tests/run-selftest.sh` 를 먼저 쓰고, 러너 자리에 「아무것도 재지 않고 `exit 0`」 을 두고 실행 →
  `::error::run-selftest red — ⓐ 과제 0건 — exit 1 여야 하는데 0 이다:` · `… ⓕ sleep 4s > COLAB_EVAL_TIMEOUT=1 — exit 78 여야 하는데 0 이다:` · `… 위 케이스가 기대와 다르다 (통과 1/6).` RC=1.
- GREEN = `bash eval/harness/tests/run-selftest.sh` → `run-selftest green — 검사 6건 전건 기대대로 (green 1 · red(판정) 2 · red(준비) 3 · 모델 호출 0회).` RC=0.
- 요약줄 실측(ⓔ) = `과제 1 · 실행 2 · green 1 · 불안정 0 · 준비 0 · 초 p50 0.0/p95 0.0 · USD 합 0.0200`(스텁 값).

## 수용 기준 (라운드 §2 WU-D5 · §5) — 실측 판정

| 기준 | 실측 |
|---|---|
| 과제 0건 → exit 1 | ✓ ⓐ · 실물 `eval/harness/` 전수도 재현(`_template` 는 `H??-*` 아님 → 전수 제외) |
| `expect.sh` 부재 → 78 | ✓ ⓑ |
| 상한 변수 미선언 → 78 | ✓ ⓒ (`${VAR:-}` 는 존재 확인용 · 대입 기본값 0건) |
| 1/2 → 「불안정」 exit 1 | ✓ ⓓ (출력에 「불안정」 문자열 단언 포함) |
| 2/2 → exit 0 ＋ 요약줄 5칸 | ✓ ⓔ |
| `sleep` > `COLAB_EVAL_TIMEOUT` → 78 | ✓ ⓕ (rc 124) |
| README allowed 표 | ✓ — 정본은 `allowed.txt` 한 자리, README 는 같은 문자열. selftest 가 문자열 대조로 갈림 검출 |
| 실제 모델 호출 0회 | ✓ — `PATH` 스텁 · 이 레인의 `claude` 호출 총 0회 |

## 하지 않은 것

- H01~H20 과제 생성(**D6**) · `gates/run.sh`·`gates/tools/`·CI 필터(**D7**) 무접촉.
- `work-items.yaml` · `03-HANDOFF.md` · `PLAN-SoT.md` 무접촉(D1 ‖ D5 병행 중 오케스트레이터 단독) · 첫 실측(p95·예산) 미수행 — README 상한 표는 `[미측정]` 그대로.

## intent 대조 — `2026-09-08-harness-evals.md` 「원한 결과」

- **미달 4건 · 전부 D6/D7 몫이라 이 레인의 범위 밖**: ⑴ 「20건이 돈다」 = 과제 20건 부재(D6) ⑵ 「사고 1건 = eval 1건」 = 규칙문은 README 에 기재, 과제 증설은 D6 ⑶ 「개정 전 red → 개정 후 green」 = 러너가 exit code 로 가르는 자리까지, 실제 적용은 D6 ⑷ 「paths filter 로 4경로 변경 시에만」 = D7.
- **초과 5건**(요청 밖 · 근거 병기): ⑴ `allowed.txt` 신설 — 스펙은 「README 한 표」였으나 러너가 읽을 **한 자리**가 필요하고 중복 금지 조건을 문자열 대조로 지키기 위함 ⑵ `--output-format json` — 위 「실측」 절 사유 ⑶ 결과에 `H??.raw.N.json`·`H??.err.N.txt`·`H??.expect.N.txt` 부가(준비 red 사유 추적용) ⑷ 시험 seam 환경변수 3개(`COLAB_EVAL_TASKS_DIR`·`COLAB_EVAL_RESULTS_ROOT`·`COLAB_EVAL_ALLOWED_FILE`) — 판정을 무르게 하는 값이 아니라 **자리** 지정. ⑸ `0/2` 판정명 **「실패」** 신설 — 스펙·라운드는 `1/2 「불안정」` 만 이름 지었고 `0/2` 는 이름이 없었다. 요약줄 `불안정` 칸은 둘을 합산하고 갈래는 `summary.md` 표 `판정` 열에 남는다 (⟨증보 2026-09-08 · advisor ② 지적⟩ 종전 표기 ~~초과 4건~~).
- 결정 1건(레인 판단) = `eval/harness/results/` 를 **`.gitignore` 에 넣지 않는다**. 사유 = 승격 조건이 3회 연속 2/2(intent Q10)라 회차가 체크아웃을 넘어 남아야 하고, `eval/` 선례가 실측 산출을 추적한다(`s2b-alayer/baseline.json`).

## 셀 수 없었던 것

- 비용 필드 이름 · `--allowedTools` 항목 안 공백 처리 — 둘 다 실제 모델 호출 없이는 못 잰다(이 레인은 호출 0회). D6 첫 실측 자리.
- 러너의 실제 소요·USD — 과제가 0건이라 잰 것이 없다. 스텁 값(0.02)은 실측이 아니다.

## 후속

- `--output-format text`(spec `R-D.md:37` · 라운드 §2 ⑴)와 요약줄 `USD 합` 요구가 **서로 어긋난다** — `text` 출력에 비용이 없다. **어느 게이트도 이것을 잡지 않는다**(문서 간 정합 검사 부재). 러너는 `json` 으로 갔고 사유를 README 에 남겼다. spec 문면 정정은 오케스트레이터 판정 자리.
- 사용자 셸에 `alias claude='claude --dangerously-skip-permissions'` 존재(`claude --version` 실행 시 노출). 러너는 비대화 `bash` 라 별칭이 적용되지 않아 무해하나, **사람이 손으로 부르는 `claude` 는 권한 검사를 건너뛴다.** 이것도 잡는 검사가 없다(게이트·훅·CI 어디에도 없음).

## advisor ② 반영 (2026-09-08 · 레인 `rd-eval-runner-fix` · 기점 `7daf998`)

- **조건 ① 오류 페이로드 구멍** — 러너가 `result` 만 읽어 `{"is_error":true,"result":"<기대와 맞는 문장>"}` ＋ rc 0 을 **2/2 green** 으로 셌다. `run.sh` JSON 해석 블록에 `is_error is True` · 「`subtype` 존재하며 `!= success`」 두 갈래 추가 → 그 회차 red(준비) · 사유 `claude 오류 결과(subtype=<값>)` · `expect.sh` 미호출 · exit 78.
- **조건 ② 문면 정정** — `dev-package/prd/specs/R-D.md` WU-D5 줄 · `dev-package/prd/rounds/R-D-2-harness-eval.md` §2 WU-D5 ⑴ 의 `--output-format text` → `json` ＋ 정정 표시(원문 `~~text~~` 취소선 존치).
- **RED 선실측** — `::error::run-selftest red — ⓖ is_error=true ＋ 본문은 기대와 일치 — exit 78 여야 하는데 0 이다:` · 그 아래 `✓ H01-stub green — 2/2` · `(통과 6/7)` RC=1.
- **GREEN** — `run-selftest green — 검사 7건 전건 기대대로 (green 1 · red(판정) 2 · red(준비) 4 · 모델 호출 0회).` RC=0. ⓖ 요약줄 = `과제 1 · 실행 1 · green 0 · 불안정 0 · 준비 1 · 초 p50 0.0/p95 0.0 · USD 합 0.0100`.
- **권고 2건 반영** — ⑴ `RUN_ID` 분 → **초**(`%Y%m%d-%H%M%S`) · 같은 분 두 회차의 덮어쓰기 제거 · README 결과 경로 표기 동반 정정 ⑵ 요약 직전 `허용 도구 정본: <경로>` 한 줄 출력 — 정본이 바꿔치기되면 출력에서 보인다.
- **수용 기준 증보 1행** — `is_error:true` ＋ 본문이 기대와 일치 → exit 78 ＋ 요약줄 `준비 1` · ✓ ⓖ.
- **후속 ⑴ 종결** — 「`text` 와 `USD 합` 이 어긋난다」는 문면 정정으로 닫혔다. 문서 간 정합을 잡는 게이트가 없다는 사실은 그대로 남는다.
- 제품 코드 · 계약 · 마이그레이션 = **0 · 0 · 0** · 실제 모델 호출 **0회**(`PATH` 스텁).
