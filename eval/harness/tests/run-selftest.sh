#!/usr/bin/env bash
# `eval/harness/run.sh` 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# ⚠ **실제 모델 호출 0회.** `claude` 를 임시 디렉터리의 스텁으로 갈아끼우고 `PATH` 앞에 둔다.
#   러너가 절대경로로 `claude` 를 부르면 이 시험은 성립하지 않는다 — 그것도 이 시험이 잡는다.
#
# 케이스 6 — 형식은 `gates/tools/frontend-visual-selftest.sh`(임시 dir · 스텁 · exit 코드 단언).
#   ⓐ 과제 0건                                  → exit 1  (red(판정) · green-by-skip 금지)
#   ⓑ `expect.sh` 부재                          → exit 78 (red(준비) · 판정 재료 부재)
#   ⓒ 상한 변수 미선언                          → exit 78 (red(준비) · 관대한 기본값 금지)
#   ⓓ 스텁 1회차 green · 2회차 red              → exit 1  ＋ 출력에 「불안정」
#   ⓔ 2/2 green                                 → exit 0  ＋ 요약줄 5칸(과제·실행·green·불안정·준비)
#   ⓕ 스텁 sleep > COLAB_EVAL_TIMEOUT           → exit 78 (red(준비) · 상한 초과는 skip 이 아니다)
#
# ⓐ·ⓑ·ⓒ·ⓕ 가 통과해 버리면 이 러너는 「아무것도 재지 않고 green」을 낼 수 있다 — 그 넷이 존재 이유다.
set -uo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="$HARNESS_DIR/run.sh"
FAILED=0
PASSED=0

red() { echo "::error::run-selftest red — $*"; FAILED=1; }

[ -f "$RUNNER" ] || { echo "::error::run-selftest red — 판정 재료가 없다: eval/harness/run.sh"; exit 1; }

WORK="$(mktemp -d -t harness-eval-selftest-XXXXXX)"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

# ── 스텁 `claude` — 모델을 부르지 않는다 ─────────────────────────────────────
STUB_BIN="$WORK/bin"
mkdir -p "$STUB_BIN"
cat > "$STUB_BIN/claude" <<'STUB'
#!/usr/bin/env bash
# 스텁 — task.md 를 stdin 으로 받아 버리고, STUB_MODE 에 따라 정해진 JSON 을 낸다.
cat >/dev/null
case "${STUB_MODE:-green}" in
  slow)
    sleep "${STUB_SLEEP:-5}"
    ;;
  flaky)
    n=0
    [ -f "${STUB_COUNTER:-/dev/null}" ] && n="$(cat "$STUB_COUNTER")"
    n=$((n + 1))
    printf '%s\n' "$n" > "$STUB_COUNTER"
    if [ "$n" -ge 2 ]; then
      printf '{"result":"BAD — 기대와 다른 답","total_cost_usd":0.01}\n'
      exit 0
    fi
    ;;
esac
printf '{"result":"OK-MARKER — 판정 완료","total_cost_usd":0.01}\n'
STUB
chmod +x "$STUB_BIN/claude"

# ── 과제 픽스처 제조 ─────────────────────────────────────────────────────────
make_task() { # $1=과제 뿌리 $2=과제 이름 $3=expect.sh 를 둘 것인가(yes|no)
  local root="$1" name="$2" want_expect="$3"
  mkdir -p "$root/$name/fixture"
  printf '스텁 과제 — 이 문장은 스텁이 읽고 버린다.\n' > "$root/$name/task.md"
  printf 'SOURCE — 스텁 과제라 원천이 없다.\n' > "$root/$name/fixture/SOURCE.md"
  if [ "$want_expect" = yes ]; then
    printf '#!/usr/bin/env bash\nexec grep -q "OK-MARKER"\n' > "$root/$name/expect.sh"
    chmod +x "$root/$name/expect.sh"
  fi
}

run_case() { # $1=과제 뿌리 $2..=환경 선언 → RC · OUT 을 채운다
  local tasks="$1"; shift
  local results; results="$(mktemp -d -t harness-eval-results-XXXXXX)"
  OUT="$(PATH="$STUB_BIN:$PATH" \
         COLAB_EVAL_TASKS_DIR="$tasks" COLAB_EVAL_RESULTS_ROOT="$results" \
         env "$@" bash "$RUNNER" 2>&1)"
  RC=$?
  rm -rf "$results"
}

check() { # $1=이름 $2=기대 exit $3=실측 exit
  if [ "$3" -eq "$2" ]; then
    echo "  ✓ $1 (exit $3)"
    PASSED=$((PASSED + 1))
    return 0
  fi
  red "$1 — exit $2 여야 하는데 $3 이다:
$(printf '%s\n' "$OUT" | sed 's/^/     /')"
  return 1
}

# ── ⓐ 과제 0건 → red(판정 · exit 1) ─────────────────────────────────────────
T_EMPTY="$WORK/empty"; mkdir -p "$T_EMPTY"
run_case "$T_EMPTY" COLAB_EVAL_TIMEOUT=10 COLAB_EVAL_BUDGET=0.50
check "ⓐ 과제 0건" 1 "$RC"

# ── ⓑ expect.sh 부재 → red(준비 · 78) ───────────────────────────────────────
T_NOEXP="$WORK/noexpect"; make_task "$T_NOEXP" "H01-stub" no
run_case "$T_NOEXP" COLAB_EVAL_TIMEOUT=10 COLAB_EVAL_BUDGET=0.50
check "ⓑ expect.sh 부재" 78 "$RC"

# ── ⓒ 상한 변수 미선언 → red(준비 · 78) ─────────────────────────────────────
T_OK="$WORK/ok"; make_task "$T_OK" "H01-stub" yes
run_case "$T_OK" -u COLAB_EVAL_TIMEOUT -u COLAB_EVAL_BUDGET
check "ⓒ COLAB_EVAL_TIMEOUT·COLAB_EVAL_BUDGET 미선언" 78 "$RC"

# ── ⓓ 1회차 green · 2회차 red → 「불안정」 red(판정 · exit 1) ────────────────
T_FLAKY="$WORK/flaky"; make_task "$T_FLAKY" "H01-stub" yes
run_case "$T_FLAKY" COLAB_EVAL_TIMEOUT=10 COLAB_EVAL_BUDGET=0.50 \
  STUB_MODE=flaky STUB_COUNTER="$WORK/flaky.count"
if check "ⓓ 1/2 → 불안정" 1 "$RC"; then
  printf '%s' "$OUT" | grep -q '불안정' \
    || red "ⓓ — exit 1 은 맞으나 출력에 「불안정」이 없다(사유를 이름으로 내지 않았다)."
fi

# ── ⓔ 2/2 green → exit 0 ＋ 요약줄 5칸 ──────────────────────────────────────
run_case "$T_OK" COLAB_EVAL_TIMEOUT=10 COLAB_EVAL_BUDGET=0.50
if check "ⓔ 2/2 green" 0 "$RC"; then
  SUM="$(printf '%s\n' "$OUT" | grep -E '^과제 [0-9]+ · 실행 [0-9]+ · green [0-9]+ · 불안정 [0-9]+ · 준비 [0-9]+' | tail -1)"
  if [ -z "$SUM" ]; then
    red "ⓔ — 요약줄 5칸(과제·실행·green·불안정·준비)이 없다:
$(printf '%s\n' "$OUT" | sed 's/^/     /')"
  else
    echo "     요약줄: $SUM"
    printf '%s' "$SUM" | grep -q '과제 1 · 실행 2 · green 1 · 불안정 0 · 준비 0' \
      || red "ⓔ — 요약줄 계수가 실측과 다르다: $SUM"
  fi
fi

# ── ⓕ 상한 초과(스텁 sleep) → red(준비 · 78) ────────────────────────────────
run_case "$T_OK" COLAB_EVAL_TIMEOUT=1 COLAB_EVAL_BUDGET=0.50 STUB_MODE=slow STUB_SLEEP=4
check "ⓕ sleep 4s > COLAB_EVAL_TIMEOUT=1" 78 "$RC"

# ── allowed.txt 정본 한 자리 — README 가 같은 표를 담고 있는가 ───────────────
ALLOWED="$HARNESS_DIR/allowed.txt"
README="$HARNESS_DIR/README.md"
if [ -f "$ALLOWED" ] && [ -f "$README" ]; then
  n_entry=0; n_miss=0
  while IFS= read -r line; do
    case "$line" in ''|\#*) continue ;; esac
    n_entry=$((n_entry + 1))
    grep -Fq -- "$line" "$README" || { n_miss=$((n_miss + 1)); echo "     - README 에 없는 항목: $line"; }
  done < "$ALLOWED"
  [ "$n_entry" -gt 0 ] || red "allowed.txt 가 비어 있다 — 대상 0건은 통과가 아니다."
  [ "$n_miss" -eq 0 ] || red "allowed.txt 항목 ${n_miss}건이 README 표에 없다 — 정본이 두 곳으로 갈렸다."
else
  red "allowed.txt 또는 README.md 가 없다 — ALLOWED 정본 자리가 부재하다."
fi

if [ "$FAILED" -ne 0 ]; then
  echo "::error::run-selftest red — 위 케이스가 기대와 다르다 (통과 ${PASSED}/6)."
  exit 1
fi
echo "run-selftest green — 검사 6건 전건 기대대로 (green 1 · red(판정) 2 · red(준비) 3 · 모델 호출 0회)."
