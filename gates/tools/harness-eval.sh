#!/usr/bin/env bash
# harness-eval — 하네스 자체를 재는 실과제 묶음(`eval/harness/`)을 **게이트 자리에서** 부른다.
#
# 무엇을 해소하나 (intent `dev-package/intent/2026-09-08-harness-evals.md` Q2a·Q10):
#   러너는 사람이 손으로 부를 때만 돌았다. 손으로 부르는 검사는 아무도 그 명령을 다시 칠 때까지
#   회귀를 못 본다(`frontend-fixture-reach` 가 닫은 것과 같은 계열). 여기서 게이트 이름을 준다.
#
# 면제 = 「현재 설정 해시와 일치하는 전수 결과가 results/ 에 있고 회귀가 없다」는 선언이다 — 정본
#   `eval/harness/README.md` 「설정 해시 · 면제 조건」 · spec `S-HARNESS-E0-EVAL-GATE-20260926` §4.3.
#
# ── 입력의 세 상태 (선례 `gates/tools/frontend-visual.sh`) ───────────────────
#   COLAB_HARNESS_EVAL=1         과제를 **실제로 돈다.** `eval/harness/run.sh` 의 종료코드를
#                                그대로 전달한다(0 green · 1 red(판정) · 78 red(준비)).
#                                ⚠ 이 모드는 **실제 모델을 부른다**(비용·시간 발생).
#   COLAB_HARNESS_EVAL_EXEMPT=1  이번 회차에 돌리지 않음을 **명시 선언**한다. **N=0 이면 red(판정)** —
#                                대상 0건은 통과가 아니다. 설정 해시 일치 전수 결과(선택 실행 아님 · 준비 0 ·
#                                과제 N) 없음·입력 손상 = red(준비 78 · missing=eval-result:<hash>) ·
#                                직전 결과보다 green 축소 = red(판정 1) · 일치 ＋ 무회귀 = green(과제 N건 ·
#                                run id · hash(head)=hash(회차) 출력). 판정 = eval/harness/config_hash.py verify.
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

GATE_CHECKOUT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPO_ROOT="${REPO_ROOT:-$GATE_CHECKOUT}"
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
  local n=0 d name
  shopt -s nullglob
  for d in "$TASKS_DIR"/H??-*/; do
    if [ "${1:-}" = selected ] && [ -n "${COLAB_EVAL_ONLY:-}" ]; then
      name="${d%/}"; name="${name##*/}"
      case "$name" in "$COLAB_EVAL_ONLY"|"$COLAB_EVAL_ONLY"-*) ;; *) continue ;; esac
    fi
    n=$((n + 1))
  done
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
  expected_tasks="$(count_tasks selected)"
  echo "harness-eval — 실행 선언(COLAB_HARNESS_EVAL=1). 과제 뿌리 $TASKS_DIR · 과제 ${expected_tasks}건 · 러너 ${RUNNER#"$REPO_ROOT/"}"
  output="$(bash "$RUNNER")"
  rc=$?
  printf '%s\n' "$output"
  if [ "$rc" -eq 0 ]; then
    # exit 0만으로는 실측 증거가 아니다. 러너의 단일 요약과 2회 통과 계수를 대조한다.
    summary="$(printf '%s\n' "$output" | grep '^과제 ')"
    pattern='^과제 ([0-9]+) · 실행 ([0-9]+) · green ([0-9]+) · 불안정 0 · 준비 0 · 초 [^[:cntrl:]]+ · 판정실패 관측 과제 0$'
    [[ "$summary" =~ $pattern ]] || red "러너 종료 0인데 유효한 과제/실행/통과 요약이 없다."
    tasks="${BASH_REMATCH[1]}"; runs="${BASH_REMATCH[2]}"; passed="${BASH_REMATCH[3]}"
    (( tasks > 0 && tasks == expected_tasks && runs == tasks * 2 && passed == tasks )) || \
      red "러너 종료 0인데 측정 0건 또는 계수가 맞지 않는다: $summary"
  fi
  echo "harness-eval — 러너 종료코드 $rc 를 그대로 전달한다 (0 green · 1 red(판정) · 78 red(준비))."
  exit "$rc"
fi

# ── ⑵ 명시 면제 — 건너뛰되 **건수를 찍는다** ────────────────────────────────
if [ "$DECL_EXEMPT" = "1" ]; then
  N="$(count_tasks)"
  if [ "$N" -eq 0 ]; then
    red "면제 선언(COLAB_HARNESS_EVAL_EXEMPT=1)인데 **과제 0건**이다 (뿌리 $TASKS_DIR). 「대상이 없어 통과」를 만들지 않는다 — 과제 형식은 eval/harness/H??-<이름>/{task.md,fixture/,expect.sh} 다."
  fi
  # 면제 = 「현재 설정 해시와 일치하는 전수 결과가 results/ 에 있고 직전 결과보다 green 이 줄지 않았다」는
  # 선언이다(spec S-HARNESS-E0-EVAL-GATE-20260926 §4.3). 계산기는 게이트 자기 체크아웃의 것으로 고정한다 —
  # REPO_ROOT seam 은 판정 대상(설정·결과)만 바꾸고 판정부를 바꾸지 못한다.
  VERIFY="$(python3 "$GATE_CHECKOUT/eval/harness/config_hash.py" verify --root "$REPO_ROOT" \
    --results "${COLAB_EVAL_RESULTS_ROOT:-$REPO_ROOT/eval/harness/results}" --tasks "$N")"
  vrc=$?
  cur_hash="${VERIFY%%$'\t'*}"; detail="${VERIFY#*$'\t'}"
  case "$vrc" in
    0) ;;
    1) red "면제 선언인데 설정 해시 일치 결과가 직전 결과보다 green 이 줄었다 — $detail" ;;
    *) ready_red "eval-result:${cur_hash:-unknown}" "$detail (verify rc=$vrc) · 이 설정 해시로 잰 전수 결과가 results/ 에 없다 · 실행 = COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=93 COLAB_EVAL_BUDGET=2.01 bash gates/run.sh harness-eval → results/<run>/ 커밋" ;;
  esac
  echo "harness-eval green — 면제 선언 · 과제 ${N}건(미실행) · $detail"
  echo "   ⚠ 면제는 「문제 없음」이 아니라 「이번 회차에 과제를 돌리지 않았다」는 선언이다."
  echo "   실제로 재려면 COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=<초> COLAB_EVAL_BUDGET=<USD> bash gates/run.sh harness-eval (모델을 부른다)."
  exit 0
fi

# ── ⑶ 침묵 — 통과가 아니다 ──────────────────────────────────────────────────
ready_red "COLAB_HARNESS_EVAL" \
  "과제를 돌릴지 말지가 선언되지 않았다. 선언하는 법 = COLAB_HARNESS_EVAL=1 COLAB_EVAL_TIMEOUT=<초> COLAB_EVAL_BUDGET=<USD> bash gates/run.sh harness-eval (실제 모델을 부른다) · 이번 회차에 돌리지 않는다면 COLAB_HARNESS_EVAL_EXEMPT=1 로 **명시 면제**를 선언한다(과제 건수가 출력에 찍힌다). 값 대조는 =1 하나뿐이다."
