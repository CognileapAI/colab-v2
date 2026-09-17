#!/usr/bin/env bash
# 호스트 뮤텍스가 **프로세스 경계를 넘어** 실제로 선다는 증명 (spec `2026-09-18-gate-host-mutex.md`).
#
# 무엇을 재나: `gates/config/parallelism.toml` 의 `serial` 선언은 종전에 `gates/run.sh all` **한
#   프로세스 안에서만** 효력이 있었다. 선언표를 읽는 자리가 `all)` 갈래 하나뿐이어서, 단독 호출
#   `gates/run.sh <게이트>` 는 선언을 한 글자도 읽지 않았다. 그래서 「게이트 레인은 호스트에 하나」는
#   오케스트레이터가 프롬프트에 그 문장을 적어서 지켜졌다 — 강제가 아니라 예의다.
#   이 셀프테스트는 그 강제가 **실행기 안에** 섰는지를 외부 행위로만 판정한다.
#
# ⚠ **실제 호스트 잠금을 건드리지 않는다.** 잠금 키는 `TMPDIR` 하나이므로(spec §A-b) 여기서
#   `TMPDIR` 을 자기 `mktemp -d` 로 물려 부른다. 주입구 변수(`COLAB_GATE_MUTEX_DIR` 따위)를
#   두지 않은 이유가 이것이다 — 그런 변수가 있으면 그것이 곧 워크트리별 잠금 분리 통로가 되고,
#   ADR-0005 개정의 「쓸 일 없는 면제 변수는 그 자체가 green-by-skip 통로」에 걸린다.
# ⚠ 대상 게이트는 `COLAB_GATE_PARALLELISM_MANIFEST` **픽스처**로 고른다. `exec-bit` 을 픽스처에서
#   `serial` 로 선언해 쓰는데, 실제 `parallelism.toml` 에서 그것은 `parallel` 이다 — 즉 이 셀프테스트가
#   green 이면 실행기가 **선언표를 실제로 읽었다**는 뜻이다(이름을 하드코딩했다면 갈리지 않는다).
#   `exec-bit` 을 고른 이유: 인덱스 조회 한 줄이라 0.02초에 끝나고 도커·DB·venv 를 하나도 안 쓴다.
#
# ⚠ 점유는 벽시계가 아니라 **FIFO 두 개**로 동기화한다 — 「잡았다」와 「놓아라」를 값으로 주고받으므로
#   부하가 판정을 흔들지 않고 폴링 루프도 없다. 고정 `sleep` 은 ⓑ 한 곳뿐이고 그것은 **케이스 자체**다
#   (「상대가 3초 뒤 놓으면 기다렸다가 얻는다」). 상한을 늘리거나 재시도해서 통과시키는 경로는 없다.
#
# ⓐ 점유 중 대기 → 78 (실경과 ≥ 상한)      ⓓ `flock` 부재 → 78
# ⓑ 점유 해제 뒤 green (`waited` ≥ 1)       ⓔ 면제 셋 — parallel 선언 · `MUTEX_HELD` · CHILD 는 면제가 아니다
# ⓒ 잠금 디렉터리 쓰기 불가 → 78            ⓕ 레인 경로(배출처 선언)에서 `::gate-waiting::` 이 부모 출력에
#                                           ⓖ 표를 못 읽으면 단독 호출도 메모를 찍고 안전한 쪽으로 잠근다
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
RUN="$REPO_ROOT/gates/run.sh"
# 판정 갈래(green·red·ready·미선언)의 정본은 하나다 — 손으로 다시 적지 않는다.
# shellcheck source=/dev/null
. "$REPO_ROOT/gates/tools/_expect.sh"

TD="$(mktemp -d -p "${TMPDIR:-/tmp}" gate-host-mutex-selftest-XXXXXX)"
trap 'rm -rf "$TD"' EXIT INT TERM

CTMP="$TD/tmp"; mkdir -p "$CTMP"                 # 자식들이 물려받을 TMPDIR = 잠금 키
LOCK_DIR="$CTMP/colab-v2-gate-host-mutex"
LOCK="$LOCK_DIR/host"
mkdir -p "$LOCK_DIR"

MANIFEST_SERIAL="$TD/serial.toml"
MANIFEST_PARALLEL="$TD/parallel.toml"
printf '[gates]\n"exec-bit" = "serial"\n'   > "$MANIFEST_SERIAL"
printf '[gates]\n"exec-bit" = "parallel"\n' > "$MANIFEST_PARALLEL"

FIFO="$TD/held.fifo";    mkfifo "$FIFO"     # 상대가 **잡았다**는 신호
RFIFO="$TD/release.fifo"; mkfifo "$RFIFO"   # 상대에게 **놓으라**는 신호
HOLD_PID=""

fail() { echo "[selftest] $1 ✗"; FAILURES+=("$1"); }
ok()   { echo "[selftest] $1 OK"; }

# 잠금을 **다른 프로세스**가 쥔다. 잡힌 것을 확인하고 나서 복귀한다 — 확인은 FIFO 한 번
# 읽기다(폴링 루프 없음: 상대가 잠금을 잡은 뒤에야 그 쓰기가 성립한다).
# 놓는 시점도 FIFO 로 정한다 — 벽시계에 기대면 부하가 판정을 흔든다.
hold() {
  flock -x "$LOCK" -c "printf held > '$FIFO'; read -r _ < '$RFIFO'" &
  HOLD_PID=$!
  read -r _ < "$FIFO"
}
unhold() { [ -n "$HOLD_PID" ] || return 0; printf go > "$RFIFO"; wait "$HOLD_PID" 2>/dev/null; HOLD_PID=""; return 0; }

# ⓑ 전용 — **스스로 $1 초 뒤에 놓는다.** 이 고정 sleep 이 케이스 자체다(「기다렸다가 얻는다」).
hold_for() { # $1=초
  flock -x "$LOCK" -c "printf held > '$FIFO'; sleep $1" &
  HOLD_PID=$!
  read -r _ < "$FIFO"
}
wait_hold() { [ -n "$HOLD_PID" ] || return 0; wait "$HOLD_PID" 2>/dev/null; HOLD_PID=""; return 0; }

# 게이트를 자식 프로세스로 돌린다. OUT/RC/ELAPSED 를 채운다.
# ⚠ 부모에게서 물려받을 수 있는 실행 문맥을 **전부 지운다** — 이 셀프테스트가 `run.sh task` 나
#   `all` 의 자식으로 돌 때 `COLAB_TASK_ID`·`COLAB_GATE_SUMMARY_CHILD` 가 실려 있고, 그대로
#   물려주면 재는 것이 달라진다(중첩 task 실행 · 래퍼 건너뜀). 케이스가 필요로 하는 값은
#   인자로 **명시해서** 준다.
gate() { # $1=게이트 · $2.. = KEY=VAL 추가 환경
  local g="$1"; shift
  local st en
  st="$(date +%s)"
  OUT="$(env -u COLAB_GATE_SUMMARY_CHILD -u COLAB_TASK_ID -u COLAB_GATE_TASK_BEFORE \
             -u COLAB_GATE_REPORT_DIR -u COLAB_GATE_OUTDIR -u COLAB_GATE_MUTEX_HELD \
             TMPDIR="${GATE_TMPDIR:-$CTMP}" \
             COLAB_GATE_PARALLELISM_MANIFEST="${GATE_MANIFEST:-$MANIFEST_SERIAL}" \
             "$@" bash "$RUN" "$g" 2>&1)"
  RC=$?
  en="$(date +%s)"; ELAPSED=$(( en - st ))
  return 0
}

# `::gate-waiting::` 의 waited 값(마지막 줄) → stdout. 없으면 빈 문자열.
waited_of() { printf '%s\n' "$OUT" | sed -n 's/.*::gate-waiting::[^|]*|waited=\([0-9]*\)|.*/\1/p' | tail -1; }
# 요약줄의 면제 건수 → stdout.
exempt_of() { printf '%s\n' "$OUT" | sed -n 's/.*호스트 뮤텍스 : 잠금 [0-9]*건 · 면제(parallel 선언) \([0-9]*\)건.*/\1/p' | tail -1; }
held_of()   { printf '%s\n' "$OUT" | sed -n 's/.*호스트 뮤텍스 : 잠금 \([0-9]*\)건 · 면제.*/\1/p' | tail -1; }

echo "══ ⓐ 점유 중 대기 → red(준비 · 78) ══════════════════════════════"
hold
gate exec-bit COLAB_GATE_MUTEX_WAIT=2
unhold
case "$(expect_classify "$RC" "$OUT")" in
  ready) ok "ⓐ 점유 중 호출 → red(준비) (exit $RC)" ;;
  *)     fail "ⓐ 점유 중 호출이 red(준비) 가 아니다 (exit $RC · 기대 78)"; printf '%s\n' "$OUT" | tail -5 | sed 's/^/           /' ;;
esac
[ "$RC" = 78 ] || fail "ⓐ 종료코드 $RC (기대 78)"
case "$OUT" in
  *'::gate-waiting::'*) ok "ⓐ 대기 표식 ::gate-waiting:: 있음" ;;
  *)                    fail "ⓐ 대기 표식이 없다 — 조용히 78 이면 멈춘 것과 구분되지 않는다" ;;
esac
case "$OUT" in
  *'::gate-readiness-failure::'*waited_for=*"$LOCK"*limit=*elapsed=*) ok "ⓐ 준비 표식에 뮤텍스 경로·상한·실경과 있음" ;;
  *) fail "ⓐ 준비 표식에 뮤텍스 경로가 없다"; printf '%s\n' "$OUT" | grep '::gate-readiness-failure::' | sed 's/^/           /' ;;
esac
# ⭑ **값 증거** — 표식 문자열만 grep 하면 「잠금을 걸었다」를 증명한 적이 없다.
if [ "$ELAPSED" -ge 2 ]; then ok "ⓐ 실경과 ${ELAPSED}초 ≥ 상한 2초 — 실제로 기다렸다"
else fail "ⓐ 실경과 ${ELAPSED}초 < 2초 — 기다리지 않고 78 을 냈다(잠금이 서지 않았다)"; fi

echo "══ ⓑ 점유 해제 뒤 green ═════════════════════════════════════════"
hold_for 3
gate exec-bit COLAB_GATE_MUTEX_WAIT=60
wait_hold
if [ "$RC" = 0 ]; then ok "ⓑ 점유가 풀린 뒤 green (exit 0)"
else fail "ⓑ 점유가 풀렸는데 green 이 아니다 (exit $RC)"; printf '%s\n' "$OUT" | tail -5 | sed 's/^/           /'; fi
case "$OUT" in
  *'::gate-waiting::'*) ok "ⓑ 대기 표식 있음" ;;
  *)                    fail "ⓑ 대기 표식이 없다 — 기다린 적이 없으면 잠금이 서지 않은 것이다" ;;
esac
w="$(waited_of)"
if [ -n "$w" ] && [ "$w" -ge 1 ] 2>/dev/null; then ok "ⓑ waited=${w} ≥ 1 — 값으로 증명된 대기"
else fail "ⓑ waited=${w:-없음} (기대 ≥ 1) — 실제로 기다린 값이 남지 않았다"; fi

echo "══ ⓒ 잠금 디렉터리 쓰기 불가 → red(준비 · 78) ═══════════════════"
RO="$TD/ro"; mkdir -p "$RO/colab-v2-gate-host-mutex"; chmod 500 "$RO/colab-v2-gate-host-mutex"
GATE_TMPDIR="$RO" gate exec-bit
chmod 700 "$RO/colab-v2-gate-host-mutex"
case "$(expect_classify "$RC" "$OUT")" in
  ready) ok "ⓒ 잠금 파일을 열 수 없으면 red(준비) (exit $RC)" ;;
  *)     fail "ⓒ 잠글 대상을 열지 못했는데 red(준비) 가 아니다 (exit $RC) — 조용한 통과다"; printf '%s\n' "$OUT" | tail -5 | sed 's/^/           /' ;;
esac

echo "══ ⓓ flock 부재 → red(준비 · 78) ═══════════════════════════════"
# PATH 수술로 흉내낸다 — 면제 변수를 두지 않기로 했으므로 주입 훅이 없다(`db-selftest.sh` 선례).
# 게이트 앞단의 다른 도구 의존에 걸려 넘어지지 않게 **함수 자리에서 직접** 부른다.
NOFLOCK="$TD/noflock-bin"; mkdir -p "$NOFLOCK"
for _b in bash sh cat cut date dirname grep iconv mkdir printf sed sleep tr env; do
  _p="$(command -v "$_b" 2>/dev/null)" && ln -sf "$_p" "$NOFLOCK/$_b"
done
OUT="$(env -i PATH="$NOFLOCK" HOME="${HOME:-/tmp}" TMPDIR="$CTMP" \
        "$NOFLOCK/bash" -c '. "$1/gates/tools/_lock.sh"; gate_host_mutex_acquire exec-bit' _ "$REPO_ROOT" 2>&1)"
RC=$?
case "$(expect_classify "$RC" "$OUT")" in
  ready) ok "ⓓ flock 부재 → red(준비) (exit $RC)" ;;
  *)     fail "ⓓ flock 이 없는데 red(준비) 가 아니다 (exit $RC) — 잠글 수단이 없다는 사실을 삼켰다"; printf '%s\n' "$OUT" | tail -5 | sed 's/^/           /' ;;
esac

echo "══ ⓔ 면제는 선언과 HELD 뿐이다 ══════════════════════════════════"
# ⓔ1 `parallel` 선언 게이트는 점유 중에도 돈다 — 선언이 곧 면제다(spec 우려 #4 ⓐ).
hold
GATE_MANIFEST="$MANIFEST_PARALLEL" gate exec-bit COLAB_GATE_OUTDIR="$TD/out-e1" COLAB_GATE_MUTEX_WAIT=5
unhold
if [ "$RC" = 0 ]; then ok "ⓔ1 parallel 선언 게이트는 점유 중에도 green"
else fail "ⓔ1 parallel 선언 게이트가 점유에 걸렸다 (exit $RC) — 선언의 의미가 바뀌었다"; fi
m="$(exempt_of)"
if [ -n "$m" ] && [ "$m" -ge 1 ] 2>/dev/null; then ok "ⓔ1 요약의 면제 건수 ${m} ≥ 1"
else fail "ⓔ1 요약에 면제 건수가 없다 (${m:-표식 없음}) — 면제가 건수로 드러나지 않는다"; fi

# ⓔ2 잠금을 쥔 부모 아래의 자식은 다시 잡지 않는다 — 안 그러면 전수가 자기 자신을 기다린다.
#     상한을 5초로 좁혀 둔다: 면제가 깨지면 5초 뒤 78 로 **끝나서** 결함이 드러난다(멈추지 않는다).
hold
gate exec-bit COLAB_GATE_MUTEX_HELD=1 COLAB_GATE_MUTEX_WAIT=5
unhold
if [ "$RC" = 0 ]; then ok "ⓔ2 COLAB_GATE_MUTEX_HELD=1 자식은 점유 중에도 green (${ELAPSED}초)"
else fail "ⓔ2 HELD 자식이 점유에 걸렸다 (exit $RC · ${ELAPSED}초) — 재진입 교착이다"; fi
case "$OUT" in
  *'::gate-waiting::'*) fail "ⓔ2 HELD 자식이 기다렸다 — 잠금을 쥔 부모 아래에서 다시 잡았다" ;;
  *)                    ok "ⓔ2 HELD 자식은 대기 표식을 찍지 않는다(아예 잡지 않는다)" ;;
esac

# ⓔ3 `COLAB_GATE_SUMMARY_CHILD=1` **만** 있는 호출은 면제가 아니다 — `task` 경로의 모양이다.
#     이것이 면제되면 측정 레인의 `serial` 게이트 전부가 무잠금으로 돈다(spec 우려 #2 · Ted 결정).
hold
gate exec-bit COLAB_GATE_SUMMARY_CHILD=1 COLAB_GATE_MUTEX_WAIT=2
unhold
if [ "$RC" = 78 ] && [ "$ELAPSED" -ge 2 ]; then ok "ⓔ3 CHILD=1 만으로는 면제되지 않는다 (exit 78 · ${ELAPSED}초)"
else fail "ⓔ3 CHILD=1 이 면제로 쓰였다 (exit $RC · ${ELAPSED}초) — task 경로가 무잠금이 된다"; fi

echo "══ ⓕ 레인 경로(배출처 선언)에서도 부모가 잡는다 ═════════════════"
hold
gate exec-bit COLAB_GATE_OUTDIR="$TD/out-f" COLAB_GATE_MUTEX_WAIT=2
unhold
if [ "$RC" = 78 ]; then ok "ⓕ 배출처가 선언된 호출도 점유 중이면 78"
else fail "ⓕ 배출처가 선언되면 잠금이 0건이 된다 (exit $RC) — 면제된 자식만 도달한 것이다"; fi
case "$OUT" in
  *'::gate-waiting::'*) ok "ⓕ 대기 표식이 부모 출력에 있다" ;;
  *)                    fail "ⓕ 부모 출력에 대기 표식이 없다" ;;
esac
h="$(held_of)"
if [ -z "$h" ] || [ "$h" = 0 ]; then ok "ⓕ 획득 실패는 요약 이전에 78 로 끝난다"
else fail "ⓕ 잠금 ${h}건이 찍혔다 — 획득에 실패했는데 잡았다고 적었다"; fi

echo "══ ⓖ 표를 못 읽으면 단독 호출도 그 사실을 말한다 ════════════════"
# 단독 호출이 선언표를 읽게 된 순간, **표를 못 읽었다는 사실**도 단독 호출의 것이 된다.
# 종전에는 그 메모를 `all` 만 찍었다 — 실행기가 안전한 쪽으로 접은 근거가 자기 안에만 남고
# 읽는 사람에게 가지 않는 자리였다. 침묵은 세 상태 중 무엇도 아니다(ADR-0005 개정).
BROKEN="$TD/broken.toml"; printf 'this is not toml = = =\n' > "$BROKEN"
GATE_MANIFEST="$BROKEN" gate exec-bit COLAB_GATE_OUTDIR="$TD/out-g" COLAB_GATE_MUTEX_WAIT=5
case "$OUT" in
  *'병렬 선언표를 읽지 못했다'*) ok "ⓖ 표 파손 메모가 단독 호출 stdout 에 있다" ;;
  *) fail "ⓖ 표를 못 읽었는데 단독 호출이 침묵했다 — 안전한 쪽으로 접은 근거가 드러나지 않는다"
     printf '%s\n' "$OUT" | tail -8 | sed 's/^/           /' ;;
esac
# ⭑ **값 증거** — 메모가 장식이 아니라 실제 결정이었음을 잠금 건수로 받는다.
#   표를 못 읽었으면 미선언이고, 미선언은 `parallel` 이 아니라 **안전한 쪽(잠근다)** 이다.
h="$(held_of)"
if [ "$h" = 1 ]; then ok "ⓖ 표 파손은 미선언이고 미선언은 잠근다 (잠금 ${h}건)"
else fail "ⓖ 표를 못 읽었는데 잠금 ${h:-표식 없음}건 — 미선언이 조용히 병렬 안전으로 접혔다"; fi

echo "── gate-host-mutex-selftest 요약 ───────────────────────────────"
echo "  케이스 7건(ⓐ~ⓖ) · 잠금 키 TMPDIR=$CTMP (실제 호스트 잠금 무접촉)"
expect_readiness_verdict "gate-host-mutex-selftest" "호스트 뮤텍스 케이스의 실행 환경"
echo "gate-host-mutex-selftest green — serial 선언이 프로세스 경계를 넘어 강제된다(ⓐ~ⓖ)."
