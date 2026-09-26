#!/usr/bin/env bash
# `harness-eval` 이 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# ⚠ **실제 모델 호출 0회.** ⓒ·ⓔ는 고정 러너를 실제로 부르고, 그 러너가 부르는 `claude` 는
#   임시 디렉터리의 스텁으로 갈아끼워 `PATH` 앞에 둔다. 과제 뿌리도 임시 자리다
#   (`COLAB_EVAL_TASKS_DIR` — 러너가 `tests/run-selftest.sh` 를 위해 낸 자리 그대로).
#
# 케이스 18 — 형식은 `gates/tools/frontend-visual-selftest.sh`(임시 dir · 스텁 · exit 코드 단언).
#   ⓐ 면제 선언 ＋ 과제 0건        → red(판정 · 1)  「대상이 없어 통과」를 만들지 않는다
#   ⓑ 면제 선언 ＋ 과제 3건 ＋ 해시 일치 전수 결과
#                                  → green ＋ 출력에 `과제 3건`(건수 노출 · 조용한 건너뛰기 금지)
#   ⓒ 실행 선언 ＋ 스텁 sleep 4s > `COLAB_EVAL_TIMEOUT=1`
#                                  → red(준비 · 78) 상한 초과는 skip 이 아니다 · 러너 exit 그대로 전달
#   ⓓ 둘 다 미선언                 → red(준비 · 78 · 입력미선언) 침묵은 통과가 아니다
#
#   ⓔ 즉시 성공 스텁 → exit 0 + 과제 3 · 실행 6 · green 3 요약
#   ⓕ·ⓖ 종료 0이지만 요약 누락/측정 0건 → red(판정 · 1)
#
#   면제 = 「현재 설정 해시와 일치하는 전수 결과가 있고 회귀가 없다」는 선언
#   (spec S-HARNESS-E0-EVAL-GATE-20260926 §4.3 · fixture = 임시 git 저장소 `cfg-repo` ＋ REPO_ROOT seam ·
#    결과 fixture 의 해시는 `eval/harness/config_hash.py compute` 로 쓴 실해시):
#   ⓛ 일치 결과 없음                → red(준비 · 78) ＋ `missing=eval-result:<hash>`
#   ⓜ 일치 결과(전수 · 준비 0 · green 3/3) → green ＋ run id · hash(head)=hash(회차)
#   ⓝ 일치 결과 green 2/3 · 직전 3/3 → red(판정 · 1) ＋ 회귀 과제 이름
#   ⓞ 일치 결과가 selected=H02 뿐   → red(준비 · 78)
#   ⓟ 일치 결과 준비 1              → red(준비 · 78)
#   ⓠ fixture `gates/x.sh` 1바이트 변경 뒤 ⓜ → red(준비 · 78) 해시 불일치
#   ⓡ 일치 결과 green 2/3 · 직전 없음 → green (첫 결과 · 회귀 기준 없음)
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
if [ "${1:-}" = --version ]; then echo "stub-claude 0.0.0"; exit 0; fi
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

# ── 설정 해시 fixture — 임시 git 저장소 + 정본 사본 · 결과는 계산기의 실해시로 쓴다 ────
CONFIG_HASH="$REPO_ROOT/eval/harness/config_hash.py"
CFG="$WORK/cfg-repo"
mkdir -p "$CFG/eval/harness/results" "$CFG/.claude" "$CFG/gates"
git init -q "$CFG"
cp "$REPO_ROOT/eval/harness/config-paths.txt" "$CFG/eval/harness/config-paths.txt"
printf '{}\n' > "$CFG/.claude/settings.json"
printf 'echo x\n' > "$CFG/gates/x.sh"

write_result() { # $1=결과 뿌리 $2=run id $3=selected $4=준비 수 $5..=<과제>:<판정>
  local root="$1" id="$2" sel="$3" ready="$4" out rows="" row n=0 g=0 u=0
  shift 4
  out="$root/$id"; mkdir -p "$out"
  for row in "$@"; do
    n=$((n + 1))
    case "${row#*:}" in green) g=$((g + 1)) ;; 준비) ;; *) u=$((u + 1)) ;; esac
    rows="$rows| ${row%%:*} | ${row#*:} | 1.0/1.0 | 0.1/0.1 | fixture |"$'\n'
  done
  {
    printf '# harness eval 실측 — %s\n\n' "$id"
    printf -- '- 요약 — 과제 %s · 실행 %s · green %s · 불안정 %s · 준비 %s · 초 p50 1.0/p95 1.0 · USD 합 0.1000 · 판정실패 관측 과제 %s\n\n' \
      "$n" "$((n * 2))" "$g" "$u" "$ready" "$u"
    printf '| 과제 | 판정 | 초(1/2) | USD(1/2) | 사유 |\n|---|---|---|---|---|\n%s' "$rows"
  } > "$out/summary.md"
  python3 "$CONFIG_HASH" compute --root "$CFG" --selected "$sel" > "$out/config-hash.json"
}
ALL3=(H01-alpha:green H02-beta:green H03-gamma:green)
TWO3=(H01-alpha:green H02-beta:green H03-gamma:실패)
mkdir -p "$WORK/res-cfg_none"
write_result "$WORK/res-cfg_match"    20260926-100000 all 0 "${ALL3[@]}"
write_result "$WORK/res-cfg_regress"  20260912-211809 all 0 "${ALL3[@]}"
write_result "$WORK/res-cfg_regress"  20260926-100000 all 0 "${TWO3[@]}"
write_result "$WORK/res-cfg_selected" 20260926-100000 H02 0 H02-beta:green
write_result "$WORK/res-cfg_ready"    20260926-100000 all 1 H01-alpha:green H02-beta:green H03-gamma:준비
write_result "$WORK/res-cfg_first"    20260926-100000 all 0 "${TWO3[@]}"

expect() { # $1=기대(green|red|ready|미선언) $2=이름 $3=케이스 키
  local want="$1" label="$2" key="$3" out rc results
  results="$WORK/results-$key"
  case "$key" in
    empty_exempt)
      out="$(COLAB_EVAL_TASKS_DIR="$T_EMPTY" COLAB_HARNESS_EVAL= COLAB_HARNESS_EVAL_EXEMPT=1 \
             "$GATE" 2>&1)"; rc=$? ;;
    exempt3|cfg_none|cfg_match|cfg_regress|cfg_selected|cfg_ready|cfg_first|cfg_changed)
      # 면제 판정 — REPO_ROOT seam 으로 fixture 저장소의 설정 해시를 결과 fixture 와 대조한다.
      local res="$WORK/res-$key"
      case "$key" in
        exempt3) res="$WORK/res-cfg_match" ;;
        cfg_changed) res="$WORK/res-cfg_match"; printf 'echo y\n' > "$CFG/gates/x.sh" ;;
      esac
      out="$(REPO_ROOT="$CFG" COLAB_EVAL_TASKS_DIR="$T_THREE" COLAB_EVAL_RESULTS_ROOT="$res" \
             COLAB_HARNESS_EVAL= COLAB_HARNESS_EVAL_EXEMPT=1 "$GATE" 2>&1)"; rc=$? ;;
    slow)
      out="$(PATH="$STUB_BIN:$PATH" COLAB_EVAL_TASKS_DIR="$T_SLOW" COLAB_EVAL_RESULTS_ROOT="$results" \
             COLAB_EVAL_TIMEOUT=1 COLAB_EVAL_BUDGET=0.50 STUB_SLEEP=4 \
             COLAB_HARNESS_EVAL=1 COLAB_HARNESS_EVAL_EXEMPT= "$GATE" 2>&1)"; rc=$? ;;
    success|selected)
      out="$(PATH="$STUB_BIN:$PATH" COLAB_EVAL_TASKS_DIR="$T_THREE" COLAB_EVAL_RESULTS_ROOT="$results" \
             COLAB_EVAL_ONLY="$(if [ "$key" = selected ]; then printf H02; fi)" COLAB_EVAL_TIMEOUT=5 COLAB_EVAL_BUDGET=0.50 STUB_SLEEP=0 \
             COLAB_HARNESS_EVAL=1 COLAB_HARNESS_EVAL_EXEMPT= "$GATE" 2>&1)"; rc=$? ;;
    missing_summary|zero_summary|wrong_runs|wrong_green|wrong_tasks)
      # 기존 REPO_ROOT seam: 고정 경로의 러너가 exit 0만 반환하는 결함 fixture.
      local repo="$WORK/repo-$key"
      mkdir -p "$repo/eval/harness"
      printf '#!/usr/bin/env bash\n' > "$repo/eval/harness/run.sh"
      if [ "$key" = zero_summary ]; then
        printf "echo '과제 0 · 실행 0 · green 0 · 불안정 0 · 준비 0 · 초 p50 0/p95 0 · USD 합 0 · 판정실패 관측 과제 0'\n" >> "$repo/eval/harness/run.sh"
      fi
      if [ "$key" = wrong_tasks ]; then
        printf "echo '과제 1 · 실행 2 · green 1 · 불안정 0 · 준비 0 · 초 p50 0/p95 0 · USD 합 0 · 판정실패 관측 과제 0'\n" >> "$repo/eval/harness/run.sh"
      fi
      if [ "$key" = wrong_runs ]; then
        printf "echo '과제 3 · 실행 5 · green 3 · 불안정 0 · 준비 0 · 초 p50 0/p95 0 · USD 합 0 · 판정실패 관측 과제 0'\n" >> "$repo/eval/harness/run.sh"
      fi
      if [ "$key" = wrong_green ]; then
        printf "echo '과제 3 · 실행 6 · green 2 · 불안정 0 · 준비 0 · 초 p50 0/p95 0 · USD 합 0 · 판정실패 관측 과제 0'\n" >> "$repo/eval/harness/run.sh"
      fi
      printf 'exit 0\n'  >> "$repo/eval/harness/run.sh"
      out="$(REPO_ROOT="$repo" COLAB_EVAL_TASKS_DIR="$T_THREE" \
             COLAB_HARNESS_EVAL=1 COLAB_HARNESS_EVAL_EXEMPT= "$GATE" 2>&1)"; rc=$? ;;
    undeclared)
      out="$(COLAB_EVAL_TASKS_DIR="$T_THREE" COLAB_HARNESS_EVAL= COLAB_HARNESS_EVAL_EXEMPT= \
             "$GATE" 2>&1)"; rc=$? ;;
    *) red "$label — 알 수 없는 케이스 키: $key"; return ;;
  esac
  # 면제 판정의 78 은 **현재 해시를 missing= 에 담아야** 한다 — 무엇이 없는지를 기계가 읽는다.
  case "$key" in
    cfg_none|cfg_selected|cfg_ready|cfg_changed)
      if [ "$rc" -ne 78 ] || ! printf '%s' "$out" | grep -Eq 'missing=eval-result:[0-9a-f]{64}'; then
        red "$label — exit 78 ＋ missing=eval-result:<hash> 여야 한다(rc=$rc):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
      fi ;;
  esac
  if expect_intercept_readiness "$rc" "$out" "$label" "$want"; then
    return
  fi
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then
    red "$label — green 이어야 하는데 red 다(rc=$rc):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  if [ "$want" = red ] && [ "$rc" -ne 1 ]; then
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
  if [ "$key" = success ] && ! printf '%s\n' "$out" | grep -Eq '^과제 3 · 실행 6 · green 3 · 불안정 0 · 준비 0 · 초 .* · 판정실패 관측 과제 0$'; then
    red "$label — 성공 요약의 과제/실행/통과 계수가 다르다: $out"; return
  fi
  if [ "$key" = selected ] && ! printf '%s\n' "$out" | grep -Eq '^과제 1 · 실행 2 · green 1 · 불안정 0 · 준비 0 · 초 .* · 판정실패 관측 과제 0$'; then
    red "$label — 선택 과제의 성공 요약이 다르다: $out"; return
  fi
  # 일치 결과 green 은 **어느 결과와 어느 해시로** 통과했는지를 두 값으로 보여야 한다.
  if { [ "$key" = cfg_match ] || [ "$key" = exempt3 ]; } && \
     ! printf '%s' "$out" | grep -Eq 'hash\(head\)=([0-9a-f]{64}) hash\(회차\)=\1 일치 결과 20260926-100000'; then
    red "$label — 출력에 일치 run id 와 같은 두 해시 값이 없다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  if [ "$key" = cfg_regress ] && ! printf '%s' "$out" | grep -q 'H03-gamma'; then
    red "$label — 회귀 red 가 회귀 과제 이름을 내지 않았다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  if [ "$key" = cfg_first ] && ! printf '%s' "$out" | grep -q '직전 없음'; then
    red "$label — 첫 결과인데 「직전 없음」을 내지 않았다:
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

expect green "ⓔ 실행 선언 ＋ 즉시 성공 스텁(과제 3 · 실행 6 · green 3)" success
expect red "ⓕ 종료 0 ＋ 요약 없음" missing_summary
expect red "ⓖ 종료 0 ＋ 측정 0건" zero_summary
expect red "ⓗ 종료 0 ＋ 실행 횟수 불일치" wrong_runs
expect red "ⓘ 종료 0 ＋ 통과 건수 불일치" wrong_green

expect red "ⓙ 종료 0 ＋ 선언 과제 누락" wrong_tasks
expect green "ⓚ H02 선택 실행 ＋ 과제 1 · 실행 2 · green 1" selected

# 면제 = 해시 일치 전수 결과 선언 — 결과 없이 통과하는 면제를 만들지 않는다.
expect 미선언 "ⓛ 면제 ＋ 설정 해시 일치 결과 없음" cfg_none
expect green  "ⓜ 면제 ＋ 일치 결과(전수 · 준비 0 · green 3/3)" cfg_match
expect red    "ⓝ 면제 ＋ 일치 결과 green 2/3 · 직전 3/3(회귀)" cfg_regress
expect 미선언 "ⓞ 면제 ＋ 일치 결과가 선택 실행(H02)뿐" cfg_selected
expect 미선언 "ⓟ 면제 ＋ 일치 결과 준비 1" cfg_ready
expect green  "ⓡ 면제 ＋ 일치 결과 green 2/3 · 직전 없음(첫 결과)" cfg_first
# ⓠ 는 fixture 의 gates/x.sh 를 바꾸므로 마지막에 둔다.
expect 미선언 "ⓠ 면제 ＋ 해시 집합 파일 1바이트 변경 뒤 ⓜ 결과(해시 불일치)" cfg_changed

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
echo "harness-eval-selftest green — 검사 18건 전건 기대대로 (green 5 · red(판정) 7 · red(준비) 1 · red(준비·입력미선언) 5 · 모델 호출 0회) ＋ CI 필터 대조."
