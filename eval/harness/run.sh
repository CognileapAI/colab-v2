#!/usr/bin/env bash
# harness eval 러너 — 지침·스킬·훅·에이전트가 바뀔 때 **행동이 바뀌었는지**를 실과제로 잰다.
#
# 무엇을 해소하나 (intent `dev-package/intent/2026-09-08-harness-evals.md`):
#   `CLAUDE.md`·`.claude/skills`·`.claude/hooks`·`.claude/agents` 를 고쳐도 그 문안이 실제 행동을
#   바꾸는지 재는 자리가 0 이었다. 문안 개정의 수용 근거가 「읽어 보니 낫다」였다.
#   여기서는 **개정 전 red → 개정 후 green** 이 근거가 된다.
#
# 실행 (상한 변수는 **미선언이면 red(준비)** — 관대한 기본값을 두지 않는다):
#   COLAB_EVAL_TIMEOUT=180 COLAB_EVAL_BUDGET=0.50 bash eval/harness/run.sh
#   COLAB_EVAL_ONLY=H01 …                     한 과제만
#
# 판정 (과제당 2회 · intent Q8):
#   2/2 통과 → green · 1/2 → red(판정 · 「불안정 — 과제 설계 결함」) · 0/2 → red(판정 · 「실패」)
#   시간·예산 상한 초과, 세 파일 부재, 러너가 답을 얻지 못함 → **red(준비 · 78)**. skip 이 아니다.
#   과제 0건 → red(판정 · 1). 「대상이 없어 통과」를 만들지 않는다 (CLAUDE.md §4).
#
# exit — 0 green · 1 red(판정) · 78 red(준비).
#   ⚠ 판정 red 와 준비 red 가 함께 나면 **1** 이다. 준비 red 도 병합 진입을 막는다(둘 다 0 이어야 한다).
#
# 시험 seam (`tests/run-selftest.sh` 가 쓴다 — 판정을 무르게 하는 값이 아니라 **자리** 지정이다):
#   COLAB_EVAL_TASKS_DIR    과제 뿌리(기본 = 이 스크립트가 있는 곳)
#   COLAB_EVAL_RESULTS_ROOT 결과 뿌리(기본 = <뿌리>/results)
#   COLAB_EVAL_ALLOWED_FILE ALLOWED 정본(기본 = <뿌리>/allowed.txt)
#
# ⛔ `--dangerously-skip-permissions` 를 쓰지 않는다. 권한은 `--allowedTools` 로만 준다(라운드 §3 ㉴).
set -uo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASKS_DIR="${COLAB_EVAL_TASKS_DIR:-$HARNESS_DIR}"
RESULTS_ROOT="${COLAB_EVAL_RESULTS_ROOT:-$HARNESS_DIR/results}"
ALLOWED_FILE="${COLAB_EVAL_ALLOWED_FILE:-$HARNESS_DIR/allowed.txt}"
RUNS_PER_TASK=2

ready_red() { # $1=선언되지 않은/없는 것 $2=사유
  printf '::gate-readiness-failure::gate=harness-eval|cause=입력미선언|missing=%s|detail=%s\n' "$1" "$2"
  echo "::error::harness-eval red(준비) — **판정을 내지 못했다.** 판정 red 가 아니다."
  echo "   선언되지 않은/없는 것: $1"
  echo "   $2"
  echo "   ⚠ 미선언·상한 초과도 red 다. 기본값·건너뛰기로 green 을 만들지 않는다 (CLAUDE.md §4)."
  exit 78
}
judg_red() { echo "::error::harness-eval red(판정) — $*"; exit 1; }

# ── ⑴ 상한 선언 — 미선언은 red(준비) ────────────────────────────────────────
# `${VAR:-}` 는 **존재 여부를 묻기 위한 것**이지 기본값이 아니다. 값을 대신 채우지 않는다.
[ -n "${COLAB_EVAL_TIMEOUT:-}" ] || ready_red "COLAB_EVAL_TIMEOUT" \
  "과제 1회 실행의 초 단위 상한이다. 선언하는 법 = COLAB_EVAL_TIMEOUT=180 COLAB_EVAL_BUDGET=0.50 bash eval/harness/run.sh · 값의 근거는 README 「상한」 절(첫 실측 p95×2)."
[ -n "${COLAB_EVAL_BUDGET:-}" ] || ready_red "COLAB_EVAL_BUDGET" \
  '과제 1회 실행의 달러 상한(--max-budget-usd)이다. 선언하는 법은 위와 같다.'
command -v python3 >/dev/null 2>&1 || ready_red "python3" \
  'claude -p --output-format json 의 결과를 읽고 p50/p95·USD 를 세는 데 쓴다.'
command -v claude >/dev/null 2>&1 || ready_red "claude 실행 파일" \
  ' 과제를 돌릴 대상이 없다. PATH 에 claude 가 있어야 한다(시험은 스텁으로 갈아끼운다).'
[ -f "$ALLOWED_FILE" ] || ready_red "$ALLOWED_FILE" \
  "허용 도구 정본이 없다 — 권한 없이 돌리지 않는다."

# ── ⑵ 과제 전수 — 0건은 red(판정) ───────────────────────────────────────────
shopt -s nullglob
TASKS=()
for d in "$TASKS_DIR"/H??-*/; do
  name="$(basename "$d")"
  if [ -n "${COLAB_EVAL_ONLY:-}" ]; then
    case "$name" in "$COLAB_EVAL_ONLY"|"$COLAB_EVAL_ONLY"-*) ;; *) continue ;; esac
  fi
  TASKS+=("$d")
done
N_TASK="${#TASKS[@]}"
if [ "$N_TASK" -eq 0 ]; then
  judg_red "과제 **0건**이다 (뿌리 $TASKS_DIR${COLAB_EVAL_ONLY:+ · COLAB_EVAL_ONLY=$COLAB_EVAL_ONLY}). 통과가 아니라 전수가 빗나간 것이다 — 과제 형식은 eval/harness/H??-<이름>/{task.md,fixture/,expect.sh} 다."
fi

RUN_ID="$(date +%Y%m%d-%H%M)"
OUT="$RESULTS_ROOT/$RUN_ID"
mkdir -p "$OUT" || ready_red "$OUT" "결과 자리를 만들지 못했다."

# ── ⑶ 실행 ──────────────────────────────────────────────────────────────────
N_RUN=0; N_GREEN=0; N_UNSTABLE=0; N_READY=0
SECS_FILE="$OUT/.secs"; : > "$SECS_FILE"
COST_FILE="$OUT/.usd"; : > "$COST_FILE"
ROWS_FILE="$OUT/.rows"; : > "$ROWS_FILE"
COST_UNKNOWN=0

for d in "${TASKS[@]}"; do
  name="$(basename "$d")"
  id="${name%%-*}"

  miss=""
  [ -f "$d/task.md" ]   || miss="$miss task.md"
  [ -d "$d/fixture" ]   || miss="$miss fixture/"
  [ -f "$d/expect.sh" ] || miss="$miss expect.sh"
  if [ -n "$miss" ]; then
    N_READY=$((N_READY + 1))
    printf '%s|준비|—|—|세 파일 중 부재:%s\n' "$name" "$miss" >> "$ROWS_FILE"
    echo "  ─ $name red(준비) — 세 파일 중 부재:$miss"
    continue
  fi

  FIXABS="$(cd "$d/fixture" && pwd)"
  # ALLOWED 를 이 과제의 fixture 경로로 고정해 조립한다(정본은 allowed.txt 한 자리).
  ALLOWED="$(FIX="$FIXABS" awk '
    /^[[:space:]]*#/ { next } /^[[:space:]]*$/ { next }
    { gsub(/\{FIXTURE\}/, ENVIRON["FIX"]); printf "%s%s", (n++ ? "," : ""), $0 }
  ' "$ALLOWED_FILE")"
  if [ -z "$ALLOWED" ]; then
    N_READY=$((N_READY + 1))
    printf '%s|준비|—|—|allowed.txt 항목 0건\n' "$name" >> "$ROWS_FILE"
    echo "  ─ $name red(준비) — allowed.txt 에 항목이 0건이다."
    continue
  fi

  pass=0; task_ready=""; task_secs=""; task_cost=""
  for n in $(seq 1 "$RUNS_PER_TASK"); do
    raw="$OUT/$id.raw.$n.json"; txt="$OUT/$id.out.$n.txt"; err="$OUT/$id.err.$n.txt"
    t0="$(date +%s.%N)"
    # cwd = fixture — 과제가 볼 수 있는 것을 픽스처로 좁힌다. `--add-dir` 도 같은 자리를 준다.
    ( cd "$FIXABS" && timeout "$COLAB_EVAL_TIMEOUT" claude -p \
        --output-format json \
        --allowedTools "$ALLOWED" \
        --no-session-persistence \
        --add-dir "$FIXABS" \
        --max-budget-usd "$COLAB_EVAL_BUDGET" \
        < "$d/task.md" > "$raw" 2> "$err" )
    rc=$?
    t1="$(date +%s.%N)"
    secs="$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.1f", b-a}')"
    N_RUN=$((N_RUN + 1))
    task_secs="${task_secs:+$task_secs/}$secs"
    printf '%s\n' "$secs" >> "$SECS_FILE"

    if [ "$rc" -eq 124 ]; then
      task_ready="시간 상한 ${COLAB_EVAL_TIMEOUT}s 초과(rc=124 · ${n}회차)"
      break
    fi
    if [ "$rc" -ne 0 ]; then
      task_ready="claude 비정상 종료(rc=$rc · ${n}회차 · 예산 상한 ${COLAB_EVAL_BUDGET} 초과 포함) — $(head -c 200 "$err" | tr '\n' ' ')"
      break
    fi

    # `--output-format json` 은 결과 한 벌을 낸다(`claude --help` 실측). 응답 본문과 비용을 거기서 꺼낸다.
    # ⚠ 필드 이름(`result`·`total_cost_usd`)은 **첫 실측(D6) 전까지 미확정**이다 — 없으면 원문을 그대로
    #   쓰고 비용은 `[미상]` 으로 남긴다. 지어내지 않는다.
    cost="$(python3 - "$raw" "$txt" <<'PY'
import json, sys
raw_path, txt_path = sys.argv[1], sys.argv[2]
data = open(raw_path, encoding='utf-8', errors='replace').read()
text, cost = data, ''
try:
    obj = json.loads(data)
except Exception:
    obj = None
if isinstance(obj, dict):
    if isinstance(obj.get('result'), str):
        text = obj['result']
    for k in ('total_cost_usd', 'cost_usd'):
        if isinstance(obj.get(k), (int, float)):
            cost = repr(float(obj[k]))
            break
open(txt_path, 'w', encoding='utf-8').write(text)
print(cost)
PY
)"
    if [ -n "$cost" ]; then
      printf '%s\n' "$cost" >> "$COST_FILE"
      task_cost="${task_cost:+$task_cost/}$cost"
    else
      COST_UNKNOWN=1
      task_cost="${task_cost:+$task_cost/}[미상]"
    fi

    if bash "$d/expect.sh" < "$txt" > "$OUT/$id.expect.$n.txt" 2>&1; then
      pass=$((pass + 1))
    fi
  done

  if [ -n "$task_ready" ]; then
    N_READY=$((N_READY + 1))
    printf '%s|준비|%s|%s|%s\n' "$name" "${task_secs:--}" "${task_cost:--}" "$task_ready" >> "$ROWS_FILE"
    echo "  ─ $name red(준비) — $task_ready"
  elif [ "$pass" -eq "$RUNS_PER_TASK" ]; then
    N_GREEN=$((N_GREEN + 1))
    printf '%s|green|%s|%s|%s/%s 통과\n' "$name" "$task_secs" "$task_cost" "$pass" "$RUNS_PER_TASK" >> "$ROWS_FILE"
    echo "  ✓ $name green — $pass/$RUNS_PER_TASK"
  elif [ "$pass" -eq 0 ]; then
    N_UNSTABLE=$((N_UNSTABLE + 1))
    printf '%s|실패|%s|%s|0/%s 통과 — 기대와 다르다\n' "$name" "$task_secs" "$task_cost" "$RUNS_PER_TASK" >> "$ROWS_FILE"
    echo "  ✗ $name red(판정 · 실패) — 0/$RUNS_PER_TASK"
  else
    N_UNSTABLE=$((N_UNSTABLE + 1))
    printf '%s|불안정|%s|%s|%s/%s 통과 — 과제 설계 결함\n' "$name" "$task_secs" "$task_cost" "$pass" "$RUNS_PER_TASK" >> "$ROWS_FILE"
    echo "  ✗ $name red(판정 · 불안정) — $pass/$RUNS_PER_TASK · 같은 과제가 회차마다 갈린다(intent Q8)."
  fi
done

# ── ⑷ 요약 ──────────────────────────────────────────────────────────────────
STATS="$(python3 - "$SECS_FILE" "$COST_FILE" "$COST_UNKNOWN" <<'PY'
import sys
secs = [float(x) for x in open(sys.argv[1]) if x.strip()]
costs = [float(x) for x in open(sys.argv[2]) if x.strip()]
def pct(v, q):
    if not v:
        return None
    s = sorted(v)
    i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[i]
p50, p95 = pct(secs, 0.50), pct(secs, 0.95)
f = lambda x: '[미상]' if x is None else '%.1f' % x
usd = '[미상]' if (sys.argv[3] == '1' or not costs) else '%.4f' % sum(costs)
print('%s %s %s' % (f(p50), f(p95), usd))
PY
)"
read -r P50 P95 USD <<< "$STATS"

SUMMARY="과제 $N_TASK · 실행 $N_RUN · green $N_GREEN · 불안정 $N_UNSTABLE · 준비 $N_READY · 초 p50 $P50/p95 $P95 · USD 합 $USD"

{
  echo "# harness eval 실측 — $RUN_ID"
  echo
  echo "- 요약 — $SUMMARY"
  echo "- 상한 — \`COLAB_EVAL_TIMEOUT=$COLAB_EVAL_TIMEOUT\` · \`COLAB_EVAL_BUDGET=$COLAB_EVAL_BUDGET\` · 과제당 ${RUNS_PER_TASK}회"
  echo "- 판정 — 2/2 green · 1/2 불안정(red 판정) · 0/2 실패(red 판정) · 상한 초과·세 파일 부재 red(준비)"
  [ "$COST_UNKNOWN" -eq 1 ] && echo "- ⚠ USD \`[미상]\` — \`claude -p --output-format json\` 출력에서 비용 필드를 찾지 못한 회차가 있다. 지어내지 않는다."
  echo
  echo "| 과제 | 판정 | 초(1/2) | USD(1/2) | 사유 |"
  echo "|---|---|---|---|---|"
  awk -F'|' '{printf "| %s | %s | %s | %s | %s |\n", $1, $2, $3, $4, $5}' "$ROWS_FILE"
} > "$OUT/summary.md"

rm -f "$SECS_FILE" "$COST_FILE" "$ROWS_FILE"

echo "$SUMMARY"
echo "근거: ${OUT#"$HARNESS_DIR/"} (summary.md · H??.out.{1,2}.txt)"

if [ "$N_UNSTABLE" -ne 0 ]; then
  echo "::error::harness-eval red(판정) — 2/2 가 아닌 과제가 ${N_UNSTABLE}건이다. 기대를 넓혀 green 을 만들지 않는다(판정 뒤에만 · 라운드 §3 ㉴)."
  exit 1
fi
if [ "$N_READY" -ne 0 ]; then
  echo "::error::harness-eval red(준비) — 판정하지 못한 과제가 ${N_READY}건이다. 「못 쟀다」는 「문제 없다」가 아니다."
  exit 78
fi
exit 0
