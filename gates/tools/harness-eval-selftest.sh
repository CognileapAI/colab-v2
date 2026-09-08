#!/usr/bin/env bash
# `harness-eval` 이 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# ⚠ **실제 모델 호출 0회.** ⓒ 만 러너를 실제로 부르고, 그 러너가 부르는 `claude` 는
#   임시 디렉터리의 스텁으로 갈아끼워 `PATH` 앞에 둔다. 과제 뿌리도 임시 자리다
#   (`COLAB_EVAL_TASKS_DIR` — 러너가 `tests/run-selftest.sh` 를 위해 낸 자리 그대로).
#
# 케이스 4 — 형식은 `gates/tools/frontend-visual-selftest.sh`(임시 dir · 스텁 · exit 코드 단언).
#   ⓐ 면제 선언 ＋ 과제 0건        → red(판정 · 1)  「대상이 없어 통과」를 만들지 않는다
#   ⓑ 면제 선언 ＋ 과제 3건        → green ＋ 출력에 `과제 3건`(건수 노출 · 조용한 건너뛰기 금지)
#   ⓒ 실행 선언 ＋ 스텁 sleep 4s > `COLAB_EVAL_TIMEOUT=1`
#                                  → red(준비 · 78) 상한 초과는 skip 이 아니다 · 러너 exit 그대로 전달
#   ⓓ 둘 다 미선언                 → red(준비 · 78 · 입력미선언) 침묵은 통과가 아니다
#
# ⓐ·ⓒ·ⓓ 가 통과해 버리면 이 게이트는 아무것도 막지 않는다 — 그 셋이 존재 이유다.
# ⓑ 는 「면제인데 건수를 안 보인다」를 잡는다(면제가 조용해지는 순간 green-by-skip 이다).
#
# ＋ CI 필터 대조 — `gates/tools/ci-filter-check.py` 로 `.github/workflows/ci.yml` 의
#   `harness` 필터가 `CLAUDE.md`·`.claude/skills/**` 를 잡고 `frontend/**` 를 안 잡는지 본다.
#   `dorny/paths-filter` 자체는 로컬에서 돌지 않는다 — 실제 GitHub 평가는 `[미상]` 이다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/harness-eval.sh"
FILTER_CHECK="$REPO_ROOT/gates/tools/ci-filter-check.py"
FAILED=0

red() { echo "::error::harness-eval-selftest red — $*"; FAILED=1; }

# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나 — 78 을 「기대한 red」로 접지 않는다.
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

[ -x "$GATE" ] || { echo "::error::harness-eval-selftest red — 판정 재료가 없다: gates/tools/harness-eval.sh"; exit 1; }

WORK="$(mktemp -d -t harness-eval-selftest-XXXXXX)"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

# ── 스텁 `claude` — 모델을 부르지 않는다 ─────────────────────────────────────
STUB_BIN="$WORK/bin"
mkdir -p "$STUB_BIN"
cat > "$STUB_BIN/claude" <<'STUB'
#!/usr/bin/env bash
# 스텁 — stdin 을 버리고 상한보다 오래 잔다. `timeout` 이 rc=124 로 끊는 것이 이 케이스의 판정이다.
cat >/dev/null
sleep "${STUB_SLEEP:-4}"
printf '{"result":"OK-MARKER","total_cost_usd":0.01}\n'
STUB
chmod +x "$STUB_BIN/claude"

make_task() { # $1=과제 뿌리 $2=과제 이름
  mkdir -p "$1/$2/fixture"
  printf '스텁 과제 — 이 문장은 스텁이 읽고 버린다.\n' > "$1/$2/task.md"
  printf 'SOURCE — 스텁 과제라 원천이 없다.\n' > "$1/$2/fixture/SOURCE.md"
  printf '#!/usr/bin/env bash\nexec grep -q "OK-MARKER"\n' > "$1/$2/expect.sh"
  chmod +x "$1/$2/expect.sh"
}

T_EMPTY="$WORK/empty"; mkdir -p "$T_EMPTY"
T_THREE="$WORK/three"
for n in H01-alpha H02-beta H03-gamma; do make_task "$T_THREE" "$n"; done
T_SLOW="$WORK/slow"; make_task "$T_SLOW" "H01-stub"

expect() { # $1=기대(green|red|ready|미선언) $2=이름 $3=케이스 키
  local want="$1" label="$2" key="$3" out rc results
  results="$WORK/results-$key"
  case "$key" in
    empty_exempt)
      out="$(COLAB_EVAL_TASKS_DIR="$T_EMPTY" COLAB_HARNESS_EVAL= COLAB_HARNESS_EVAL_EXEMPT=1 \
             "$GATE" 2>&1)"; rc=$? ;;
    exempt3)
      out="$(COLAB_EVAL_TASKS_DIR="$T_THREE" COLAB_HARNESS_EVAL= COLAB_HARNESS_EVAL_EXEMPT=1 \
             "$GATE" 2>&1)"; rc=$? ;;
    slow)
      out="$(PATH="$STUB_BIN:$PATH" COLAB_EVAL_TASKS_DIR="$T_SLOW" COLAB_EVAL_RESULTS_ROOT="$results" \
             COLAB_EVAL_TIMEOUT=1 COLAB_EVAL_BUDGET=0.50 STUB_SLEEP=4 \
             COLAB_HARNESS_EVAL=1 COLAB_HARNESS_EVAL_EXEMPT= "$GATE" 2>&1)"; rc=$? ;;
    undeclared)
      out="$(COLAB_EVAL_TASKS_DIR="$T_THREE" COLAB_HARNESS_EVAL= COLAB_HARNESS_EVAL_EXEMPT= \
             "$GATE" 2>&1)"; rc=$? ;;
    *) red "$label — 알 수 없는 케이스 키: $key"; return ;;
  esac
  if expect_intercept_readiness "$rc" "$out" "$label" "$want"; then
    return
  fi
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then
    red "$label — green 이어야 하는데 red 다(rc=$rc):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  if [ "$want" = red ] && [ "$rc" -eq 0 ]; then
    red "$label — red 여야 하는데 통과했다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  # 면제 케이스는 **건수를 출력에 보여야** 한다 — 조용히 넘어가면 green-by-skip 이다.
  if [ "$key" = exempt3 ] && ! printf '%s' "$out" | grep -q '과제 3건'; then
    red "$label — 면제인데 건수를 출력하지 않았다(조용한 건너뛰기):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  # 과제 0건 red 는 **무엇이 0 인지**를 이름으로 내야 한다.
  if [ "$key" = empty_exempt ] && ! printf '%s' "$out" | grep -q '과제 0건'; then
    red "$label — red 인데 「과제 0건」을 사유로 내지 않았다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  echo "  ✓ $label ($want)"
}

# ⓐ 대상 0건은 통과가 아니다 — 면제 선언이 있어도 잴 것이 0 이면 red 다.
expect red    "ⓐ 면제 선언 ＋ 과제 0건" empty_exempt
# ⓑ 면제 — 건너뛰되 건수를 보인다.
expect green  "ⓑ 면제 선언 ＋ 과제 3건(건수 노출)" exempt3
# ⓒ 상한 초과 — 러너의 78 을 게이트가 그대로 전달하는가.
expect ready  "ⓒ 실행 선언 ＋ 스텁 sleep 4s > 상한 1s" slow
# ⓓ 둘 다 미선언 — 기본값으로 green 을 만들지 않는다.
expect 미선언 "ⓓ COLAB_HARNESS_EVAL·_EXEMPT 둘 다 미선언" undeclared

# ── CI 필터 대조 — `harness` 가 지침 4경로를 잡고 제품 경로를 안 잡는가 ──────
if [ -f "$FILTER_CHECK" ]; then
  if FILTER_OUT="$(python3 "$FILTER_CHECK" 2>&1)"; then
    printf '%s\n' "$FILTER_OUT" | sed 's/^/  /'
  else
    red "CI 필터 대조가 red 다:
$(printf '%s\n' "$FILTER_OUT" | sed 's/^/     /')"
  fi
else
  red "CI 필터 대조부가 없다: gates/tools/ci-filter-check.py"
fi

if [ "$FAILED" -ne 0 ] || [ "${#FAILURES[@]}" -ne 0 ]; then
  echo "::error::harness-eval-selftest red — 위 케이스가 기대와 다르다."
  [ "${#FAILURES[@]}" -eq 0 ] || printf '  - %s\n' "${FAILURES[@]}"
  exit 1
fi
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict harness-eval-selftest
echo "harness-eval-selftest green — 검사 4건 전건 기대대로 (green 1 · red(판정) 1 · red(준비) 1 · red(준비·입력미선언) 1 · 모델 호출 0회) ＋ CI 필터 대조."
