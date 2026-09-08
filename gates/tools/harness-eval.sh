#!/usr/bin/env bash
# harness-eval — 하네스 자체를 재는 실과제 묶음(`eval/harness/`)을 **게이트 자리에서** 부른다.
#
# 무엇을 해소하나 (intent `dev-package/intent/2026-09-08-harness-evals.md` Q2a·Q10):
#   러너는 사람이 손으로 부를 때만 돌았다. 손으로 부르는 검사는 아무도 그 명령을 다시 칠 때까지
#   회귀를 못 본다(`frontend-fixture-reach` 가 닫은 것과 같은 계열). 여기서 게이트 이름을 준다.
#
# ⚠ **아직 승격 전이다.** 승격 조건 = 과제 20건이 **3회 연속 로컬 2/2 green**(intent Q10).
#   그때까지 로컬 `all` 과 CI 잡은 **면제 모드**로 돌고, 실행 모드로 바꾸는 것은 **별건**이다.
#   면제라도 **건수는 출력에 찍힌다** — 조용한 건너뛰기를 만들지 않는다.
#
# ── 입력의 세 상태 (선례 `gates/tools/frontend-visual.sh`) ───────────────────
#   COLAB_HARNESS_EVAL=1         과제를 **실제로 돈다.** `eval/harness/run.sh` 의 종료코드를
#                                그대로 전달한다(0 green · 1 red(판정) · 78 red(준비)).
#                                ⚠ 이 모드는 **실제 모델을 부른다**(비용·시간 발생).
#   COLAB_HARNESS_EVAL_EXEMPT=1  이번 회차에 돌리지 않음을 **명시 선언**한다. 과제 N건을
#                                출력에 찍고 green. **N=0 이면 red(판정)** — 대상 0건은 통과가 아니다.
#   둘 다 없음                    → red(준비 · 입력미선언 · 78). 침묵은 통과가 아니다(`CLAUDE.md §4`).
#   둘 다 =1                      → **실행이 이긴다.** 면제를 무시했다는 사실을 출력에 적는다 —
#                                 면제는 「이번 회차에 재지 않았다」는 선언이라 실측보다 약하다.
#
# ⚠ **값 대조는 `=1` 하나뿐이다**(`ship.sh` 와 같은 규약). `true`·`yes`·`0` 은 선언이 아니라
#   미선언으로 읽힌다 — 「대충 참 같으면 통과」가 세 상태를 두 상태로 무너뜨린다.
#
# 과제 뿌리 = `COLAB_EVAL_TASKS_DIR`(러너가 낸 시험 seam) · 기본 `eval/harness/`.
# 건수 = `H??-*/` 디렉터리 실계수. `_template/` 은 그 모양이 아니라 세어지지 않는다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_readiness.sh"

# 러너 경로는 **고정한다.** 갈아끼울 자리를 만들면 게이트가 판정부 아닌 것을 돌 수 있고,
# 시험은 그럴 필요가 없다 — 과제 뿌리(`COLAB_EVAL_TASKS_DIR`)와 `PATH` 스텁만으로 성립한다.
RUNNER="$REPO_ROOT/eval/harness/run.sh"
TASKS_DIR="${COLAB_EVAL_TASKS_DIR:-$REPO_ROOT/eval/harness}"

red() { echo "::error::harness-eval red(판정) — $*"; exit 1; }
ready_red() { # $1=선언되지 않은/없는 것 $2=사유
  readiness_undeclared_input "harness-eval" "$1" "$2"
  exit "$READINESS_EXIT"
}

count_tasks() { # stdout = `H??-*/` 디렉터리 실계수
  local n=0 d
  shopt -s nullglob
  for d in "$TASKS_DIR"/H??-*/; do n=$((n + 1)); done
  printf '%s' "$n"
}

DECL_RUN="${COLAB_HARNESS_EVAL:-}"
DECL_EXEMPT="${COLAB_HARNESS_EVAL_EXEMPT:-}"

# ── ⑴ 실행 선언 — 러너를 돌리고 종료코드를 그대로 전달한다 ──────────────────
if [ "$DECL_RUN" = "1" ]; then
  if [ "$DECL_EXEMPT" = "1" ]; then
    echo "harness-eval — COLAB_HARNESS_EVAL=1 과 COLAB_HARNESS_EVAL_EXEMPT=1 이 함께 선언됐다. **실행이 이긴다** — 면제 선언은 무시했다."
    echo "   면제는 「이번 회차에 재지 않았다」는 선언이고, 재고 난 결과가 있으면 그 결과가 판정이다."
  fi
  [ -f "$RUNNER" ] || ready_red "$RUNNER" \
    "과제를 돌릴 러너가 이 체크아웃에 없다. 자리 = eval/harness/run.sh (WU-D5)."
  echo "harness-eval — 실행 선언(COLAB_HARNESS_EVAL=1). 과제 뿌리 $TASKS_DIR · 과제 $(count_tasks)건 · 러너 ${RUNNER#"$REPO_ROOT/"}"
  bash "$RUNNER"
  rc=$?
  echo "harness-eval — 러너 종료코드 $rc 를 그대로 전달한다 (0 green · 1 red(판정) · 78 red(준비))."
  exit "$rc"
fi

# ── ⑵ 명시 면제 — 건너뛰되 **건수를 찍는다** ────────────────────────────────
if [ "$DECL_EXEMPT" = "1" ]; then
  N="$(count_tasks)"
  if [ "$N" -eq 0 ]; then
    red "면제 선언(COLAB_HARNESS_EVAL_EXEMPT=1)인데 **과제 0건**이다 (뿌리 $TASKS_DIR). 「대상이 없어 통과」를 만들지 않는다 — 과제 형식은 eval/harness/H??-<이름>/{task.md,fixture/,expect.sh} 다."
  fi
  echo "harness-eval green — 면제 선언 · 과제 ${N}건(미실행)"
  echo "   ⚠ 면제는 「문제 없음」이 아니라 「이번 회차에 과제를 돌리지 않았다」는 선언이다."
  echo "   실제로 재려면 COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=<초> COLAB_EVAL_BUDGET=<USD> bash gates/run.sh harness-eval (모델을 부른다)."
  exit 0
fi

# ── ⑶ 침묵 — 통과가 아니다 ──────────────────────────────────────────────────
ready_red "COLAB_HARNESS_EVAL" \
  "과제를 돌릴지 말지가 선언되지 않았다. 선언하는 법 = COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=<초> COLAB_EVAL_BUDGET=<USD> bash gates/run.sh harness-eval (실제 모델을 부른다) · 이번 회차에 돌리지 않는다면 COLAB_HARNESS_EVAL_EXEMPT=1 로 **명시 면제**를 선언한다(과제 건수가 출력에 찍힌다). 값 대조는 =1 하나뿐이다."
