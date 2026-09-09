#!/usr/bin/env bash
# `eval/harness/run.sh` 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# ⚠ **실제 모델 호출 0회.** `claude` 를 임시 디렉터리의 스텁으로 갈아끼우고 `PATH` 앞에 둔다.
#   러너가 절대경로로 `claude` 를 부르면 이 시험은 성립하지 않는다 — 그것도 이 시험이 잡는다.
#
# 케이스 15 — 형식은 `gates/tools/frontend-visual-selftest.sh`(임시 dir · 스텁 · exit 코드 단언).
#   ⓐ 과제 0건                                  → exit 1  (red(판정) · green-by-skip 금지)
#   ⓑ `expect.sh` 부재                          → exit 78 (red(준비) · 판정 재료 부재)
#   ⓒ 상한 변수 미선언                          → exit 78 (red(준비) · 관대한 기본값 금지)
#   ⓓ 스텁 1회차 green · 2회차 red              → exit 1  ＋ 출력에 「불안정」
#   ⓔ 2/2 green                                 → exit 0  ＋ 요약줄 5칸(과제·실행·green·불안정·준비)
#   ⓕ 스텁 sleep > COLAB_EVAL_TIMEOUT           → exit 78 (red(준비) · 상한 초과는 skip 이 아니다)
#   ⓖ `is_error:true` ＋ 본문은 기대와 일치     → exit 78 (red(준비) · 오류 페이로드 · rc 0)
#   ⓗ 판정기 exit 78 / ⓘ 예상 밖 exit 42      → exit 78 ＋ 원문 stderr·종료코드 보존
#   ⓙ 판정기 exit 1                            → exit 1 (판정 실패 유지)
#   ⓚ 1회차 green · 2회차 판정기 exit 78      → exit 78 (불안정으로 오분류 금지)
#   추가 4건: 같은 과제 1→78/42, 과제 간 1/78·78/1 혼재 → exit 1
#
# ⓐ·ⓑ·ⓒ·ⓕ·ⓖ 가 통과해 버리면 이 러너는 「아무것도 재지 않고 green」을 낼 수 있다 — 그 다섯이 존재 이유다.
# ⓖ 는 advisor ② 가 재현한 구멍이다 — `rc 0` ＋ `result` 본문이 기대와 맞으면 오류 결과도 2/2 green 이 됐다.
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
  errpayload)
    # advisor ② 재현 — rc 0 · 본문은 기대(OK-MARKER)와 일치하지만 결과 자체가 오류다.
    printf '{"is_error":true,"subtype":"error_during_execution","result":"OK-MARKER — 판정 완료","total_cost_usd":0.01}\n'
    exit 0
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
  RESULTS="$(mktemp -d "$WORK/results-XXXXXX")"
  OUT="$(PATH="$STUB_BIN:$PATH" \
         COLAB_EVAL_TASKS_DIR="$tasks" COLAB_EVAL_RESULTS_ROOT="$RESULTS" \
         env "$@" bash "$RUNNER" 2>&1)"
  RC=$?
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

# ── ⓖ 오류 페이로드(is_error:true · rc 0) → red(준비 · 78) ──────────────────
# 본문은 expect.sh 의 정규식과 일치한다. 그래도 green 이 되면 안 된다 — 결과가 오류이기 때문이다.
run_case "$T_OK" COLAB_EVAL_TIMEOUT=10 COLAB_EVAL_BUDGET=0.50 STUB_MODE=errpayload
if check "ⓖ is_error=true ＋ 본문은 기대와 일치" 78 "$RC"; then
  SUM_G="$(printf '%s\n' "$OUT" | grep -E '^과제 [0-9]+ · 실행 [0-9]+ · green [0-9]+ · 불안정 [0-9]+ · 준비 [0-9]+' | tail -1)"
  if [ -z "$SUM_G" ]; then
    red "ⓖ — 요약줄 5칸이 없다:
$(printf '%s\n' "$OUT" | sed 's/^/     /')"
  else
    echo "     요약줄: $SUM_G"
    printf '%s' "$SUM_G" | grep -q 'green 0 · 불안정 0 · 준비 1' \
      || red "ⓖ — 오류 페이로드가 준비 칸으로 세어지지 않았다: $SUM_G"
  fi
  printf '%s' "$OUT" | grep -q 'claude 오류 결과(subtype=error_during_execution)' \
    || red "ⓖ — exit 78 은 맞으나 사유에 subtype 이 없다(원인을 이름으로 내지 않았다)."
fi

# ── 판정기 종료 계약: 실제 스텁 실행 + 근거 파일을 바이트 단위로 확인 ────────
T_JUDGE="$WORK/judge"; make_task "$T_JUDGE" "H01-stub" yes
cat > "$T_JUDGE/H01-stub/expect.sh" <<'JUDGE'
#!/usr/bin/env bash
cat >/dev/null
rc="$JUDGE_RC"
if [ -n "${JUDGE_COUNTER:-}" ]; then
  n=0
  [ -f "$JUDGE_COUNTER" ] && n="$(cat "$JUDGE_COUNTER")"
  n=$((n + 1))
  printf '%s\n' "$n" > "$JUDGE_COUNTER"
  [ "$n" -eq 1 ] && rc="${JUDGE_FIRST_RC:-0}"
fi
printf 'judge stdout rc=%s\n' "$rc"
printf 'judge stderr rc=%s\r\nsecond line\n' "$rc" >&2
exit "$rc"
JUDGE

check_judge_evidence() { # $1=회차 $2=판정기 원래 종료코드
  local attempt="$1" want_rc="$2" dirs
  dirs=("$RESULTS"/*)
  [ "${#dirs[@]}" -eq 1 ] || { red "판정기 결과 디렉터리 수가 1이 아니다"; return; }
  printf 'judge stderr rc=%s\r\nsecond line\n' "$want_rc" > "$WORK/want.stderr"
  cmp -s "$WORK/want.stderr" "${dirs[0]}/H01.expect.$attempt.err.txt" \
    || red "판정기 stderr 원문이 보존되지 않았다(rc=$want_rc · $attempt 회차)"
  printf 'judge stdout rc=%s\n' "$want_rc" > "$WORK/want.stdout"
  cmp -s "$WORK/want.stdout" "${dirs[0]}/H01.expect.$attempt.txt" \
    || red "판정기 stdout이 stderr와 분리되어 보존되지 않았다"
  printf '%s\n' "$want_rc" > "$WORK/want.rc"
  cmp -s "$WORK/want.rc" "${dirs[0]}/H01.expect.$attempt.rc" \
    || red "판정기 원래 종료코드 근거가 없다(rc=$want_rc)"
}

for judge_rc in 78 42 1; do
  want_exit=78; runs=1; unstable=0; ready=1
  if [ "$judge_rc" -eq 1 ]; then
    want_exit=1; runs=2; unstable=1; ready=0
  fi
  run_case "$T_JUDGE" COLAB_EVAL_TIMEOUT=10 COLAB_EVAL_BUDGET=0.50 JUDGE_RC="$judge_rc"
  check "판정기 exit $judge_rc 분류" "$want_exit" "$RC"
  printf '%s' "$OUT" | grep -q "과제 1 · 실행 $runs · green 0 · 불안정 $unstable · 준비 $ready" \
    || red "판정기 exit $judge_rc 요약 계수/실행 중단이 틀렸다"
  if [ "$want_exit" -eq 78 ]; then
    printf '%s' "$OUT" | grep -q "판정기.*rc=$judge_rc" \
      || red "준비 실패 사유에 판정기 원래 종료코드가 없다"
  fi
  check_judge_evidence 1 "$judge_rc"
  [ "$runs" -eq 1 ] || check_judge_evidence 2 "$judge_rc"
done

run_case "$T_JUDGE" COLAB_EVAL_TIMEOUT=10 COLAB_EVAL_BUDGET=0.50 \
  JUDGE_RC=78 JUDGE_COUNTER="$WORK/judge.count"
check "1회차 green 뒤 판정기 준비 실패" 78 "$RC"
printf '%s' "$OUT" | grep -q '과제 1 · 실행 2 · green 0 · 불안정 0 · 준비 1' \
  || red "green 뒤 준비 실패를 불안정/green으로 잘못 셌다"
check_judge_evidence 1 0
check_judge_evidence 2 78

# 같은 과제의 앞선 오답을 후속 준비 실패가 지우면 안 된다.
for later_rc in 78 42; do
  run_case "$T_JUDGE" COLAB_EVAL_TIMEOUT=10 COLAB_EVAL_BUDGET=0.50 \
    JUDGE_FIRST_RC=1 JUDGE_RC="$later_rc" JUDGE_COUNTER="$WORK/mixed-$later_rc.count"
  check "같은 과제 1→$later_rc 혼재" 1 "$RC"
  printf '%s' "$OUT" | grep -q '과제 1 · 실행 2 · green 0 · 불안정 0 · 준비 1' \
    || red "혼재 과제는 준비로 분류하며 한 번만 집계해야 한다"
  printf '%s' "$OUT" | grep -q '판정실패 관측 과제 1' \
    || red "요약에서 앞선 판정 실패가 사라졌다"
  for summary in "$RESULTS"/*/summary.md; do
    grep -q '| H01-stub | 준비 |' "$summary" || red "혼재 과제의 준비 분류가 없다"
    grep -q '판정 실패 관측: 1회차(rc=1)' "$summary" || red "실제로 실패한 회차/코드가 없다"
    grep -q "rc=$later_rc · 2회차" "$summary" || red "후속 준비 실패 회차/코드가 없다"
  done
  check_judge_evidence 1 1
  check_judge_evidence 2 "$later_rc"
done

# 과제 간 혼재도 실행 순서와 관계없이 exit 1이다.
for first_rc in 1 78; do
  T_MIXED="$WORK/cross-$first_rc"
  second_rc=1
  [ "$first_rc" -ne 1 ] || second_rc=78
  make_task "$T_MIXED" "H01-first" yes
  make_task "$T_MIXED" "H02-second" yes
  printf '#!/usr/bin/env bash\ncat >/dev/null\nexit %s\n' "$first_rc" > "$T_MIXED/H01-first/expect.sh"
  printf '#!/usr/bin/env bash\ncat >/dev/null\nexit %s\n' "$second_rc" > "$T_MIXED/H02-second/expect.sh"
  run_case "$T_MIXED" COLAB_EVAL_TIMEOUT=10 COLAB_EVAL_BUDGET=0.50
  check "과제 간 $first_rc/$second_rc 혼재" 1 "$RC"
  printf '%s' "$OUT" | grep -q '과제 2 · 실행 3 · green 0 · 불안정 1 · 준비 1' \
    || red "과제 간 판정/준비 집계가 틀렸다"
  printf '%s' "$OUT" | grep -q '판정실패 관측 과제 1' \
    || red "과제 간 판정 실패 관측 계수가 틀렸다"
done

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
  echo "::error::run-selftest red — 위 케이스가 기대와 다르다 (통과 ${PASSED}/15)."
  exit 1
fi
echo "run-selftest green — 검사 15건 전건 기대대로 (green 1 · red(판정) 7 · red(준비) 7 · 모델 호출 0회)."
