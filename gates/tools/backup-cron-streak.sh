#!/usr/bin/env bash
# 크론 무인 연속 GREEN 을 **게이트가 다시 묻는다** — `PLAN-SoT §9 〈286〉` ① · 등재 `〈296〉`-㉴.
#
# ── 이 게이트가 재는 것과 재지 않는 것 ──────────────────────────────────────
# **재는 것** = 크론 04:40 회차(`check-cron-streak.sh`)가 **로그에 남긴 마지막 판정 줄**.
# **재지 않는 것** = 연속 GREEN 그 자체. 그것은 04:40 회차가 이미 쟀고, 여기서는 **판독만** 한다.
#
# ── 왜 재실행이 아닌가 (권고 축자) ──────────────────────────────────────────
# 게이트 호스트가 백업 보관처(`COLAB_BACKUP_STATE_DIR`)를 못 보면 재실행은 **항상 RED** 가 되고,
# 그때 「보관처 없음」과 「연속 깨짐」이 **안 갈린다.** 결과 판독은 둘을 가른다 — 요약줄이 아예
# 없으면 「안 돌았다」이고, 요약줄이 RED 면 「돌았는데 깨졌다」다. 두 사실은 처방이 다르다.
# 보관처 접근 가능한 호스트에서만 도는 게이트는 `render-latency` 선례를 따른다.
#
# ── 판정 규칙 (fail-closed · `CLAUDE.md §4`) ────────────────────────────────
#   ⓐ 로그 파일 없음 · 요약줄 0건        → RED. 「대상 0건」 통과 없음
#   ⓑ 요약줄 시각이 36시간보다 오래됨    → RED (일 1회 ＋ 12h 여유)
#   ⓒ 요약줄이 RED                       → RED
#   ⓓ 요약줄이 GREEN 이고 새것            → GREEN
#
# ── 실측한 요약줄의 모양 (2026-09-03 · 이 호스트) ───────────────────────────
# `check-cron-streak.sh` 는 `lib.sh verdict` 로 요약줄을 낸다 — 축자 예:
#   `크론 연속 GREEN: GREEN (통과 11건 · SKIP 0 — 모든 항목이 실제로 돌았다)`
# ⚠ **그 줄 자체에는 시각이 없다.** 시각은 `run-scheduled.sh` 가 **바로 다음 줄**에 남긴다:
#   `2026-09-03T04:40:05 check-cron-streak.sh 성공`   (실패면 `!!! … 실패 (exit N)`)
# 그래서 이 게이트는 **요약줄과 그 뒤의 실행 줄을 짝으로** 읽는다. 짝을 못 찾으면 RED 다 —
# **시각을 모르는 GREEN 은 신선도를 판정할 수 없고, 판정할 수 없는 것은 통과가 아니다.**
# 창 값(`COLAB_CRON_WINDOW_MIN`)은 `════ R-1` 머리줄에 찍혀 있어 그대로 출력에 옮긴다 —
# 안 보이는 근사는 거짓말이 된다(`check-cron-streak.sh` 머리말 축자).
#
# 환경변수
#   COLAB_BACKUP_STATE_DIR       상태 디렉터리 (기본 $HOME/colab-v2-backups)
#   COLAB_CRON_STREAK_GATE_LOG   판독할 로그 (기본 $STATE/staging-backup.log) — selftest 가 물린다
#   COLAB_CRON_STREAK_MAX_AGE_H  허용 나이(시간) (기본 36)
#   COLAB_CRON_STREAK_NOW        기준 시각(epoch) — **selftest 전용**. 없으면 `date +%s`
set -uo pipefail

STATE="${COLAB_BACKUP_STATE_DIR:-$HOME/colab-v2-backups}"
LOG="${COLAB_CRON_STREAK_GATE_LOG:-$STATE/staging-backup.log}"
MAX_H="${COLAB_CRON_STREAK_MAX_AGE_H:-36}"
NOW="${COLAB_CRON_STREAK_NOW:-$(date +%s)}"

VERDICT_RE='^크론 연속 GREEN: '
RUNLINE_RE='^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}) (!!! )?check-cron-streak\.sh (성공|실패)'

red() { echo "::error::backup-cron-streak red — $*"; exit 1; }

echo "════ backup-cron-streak — 크론 04:40 회차의 판정 줄을 읽는다 (재실행하지 않는다)"
echo "  판독 대상: $LOG  ·  허용 나이 ${MAX_H}시간"

# ── ⓐ 입력 실재 ──────────────────────────────────────────────────────────────
[ -f "$LOG" ] || red "로그가 없다: $LOG — 「크론이 안 돌았다」와 「이 호스트가 보관처를 못 본다」가
     구분되지 않는다. 둘 다 통과가 아니다. 보관처를 마운트하거나 COLAB_BACKUP_STATE_DIR 를 가리켜라."

# 마지막 요약줄의 **행 번호**를 잡는다. 짝(실행 줄)은 그 아래에서만 찾는다.
VLINE="$(grep -nE "$VERDICT_RE" "$LOG" 2>/dev/null | tail -1 | cut -d: -f1)"
[ -n "${VLINE:-}" ] || red "요약줄이 0건이다 — \`크론 연속 GREEN:\` 으로 시작하는 줄이 로그에 없다.
     04:40 회차가 한 번도 돌지 않았거나 다른 파일에 적히고 있다. **대상 0건은 통과가 아니다**(CLAUDE.md §4)."

VERDICT="$(sed -n "${VLINE}p" "$LOG")"

# ── 시각 — 요약줄 **아래**의 첫 실행 줄에서만 가져온다 ───────────────────────
RUN="$(tail -n "+$VLINE" "$LOG" | grep -E "$RUNLINE_RE" | head -1)"
[ -n "$RUN" ] || red "요약줄의 시각을 찾지 못했다 — 요약줄 아래에 \`… check-cron-streak.sh 성공|실패\`
     줄이 없다. 요약줄 자체에는 시각이 없으므로(run-scheduled.sh 가 다음 줄에 적는다) **나이를
     판정할 수 없다.** 판정할 수 없는 것을 통과로 읽지 않는다.
     요약줄: $VERDICT"

TS="$(printf '%s' "$RUN" | sed -E "s/$RUNLINE_RE.*/\1/")"
EPOCH="$(date -d "${TS/T/ }" +%s 2>/dev/null || true)"
[ -n "${EPOCH:-}" ] || red "요약줄의 시각을 해석하지 못했다: 「$TS」 (실행 줄: $RUN)"

AGE_S=$(( NOW - EPOCH ))
AGE_H=$(( AGE_S / 3600 ))
WINDOW="$(grep -E '^════ R-1' "$LOG" | tail -1 | sed -E 's/.*(예정 [0-9]+ ±[0-9]+분).*/\1/' || true)"

echo "  요약줄: $VERDICT"
echo "  시각  : $TS (${AGE_H}시간 전)"
[ -n "${WINDOW:-}" ] && echo "  근사   : 무인 판별은 ${WINDOW} 창이다 — 그 시각에 손으로 돌린 회차는 무인으로 세어진다"

# ── ⓑ 신선도 ─────────────────────────────────────────────────────────────────
if [ "$AGE_S" -lt 0 ]; then
  red "요약줄 시각이 미래다 ($TS) — 시계가 어긋났거나 로그가 손으로 편집됐다. 판정하지 않는다."
fi
if [ "$AGE_H" -ge "$MAX_H" ]; then
  red "요약줄이 ${AGE_H}시간 전 것이다 — 허용 ${MAX_H}시간을 넘었다. 크론이 멈춰 있고,
     **지난 GREEN 이 오늘의 GREEN 을 대신하지 않는다**(green-by-stale).
     요약줄: $VERDICT"
fi

# ── ⓒ 판정 ──────────────────────────────────────────────────────────────────
case "$VERDICT" in
  *": RED"*)
    red "04:40 회차가 RED 를 냈다 — 연속이 깨졌다. **이 게이트는 그 판정을 뒤집지 않는다.**
     원인은 그 회차 로그의 FAIL 줄에 있다: $LOG
     요약줄: $VERDICT" ;;
  *": GREEN"*) : ;;
  *) red "요약줄을 GREEN/RED 어느 쪽으로도 읽지 못했다 — 모양이 바뀐 것이다. 판정하지 않는다.
     요약줄: $VERDICT" ;;
esac

# 「검사 0건 · 승인된 SKIP」 GREEN 은 이 자리에서 통과가 아니다 — 무인 회차를 실제로 본 것이
# 하나도 없다는 뜻이고, 그것이 곧 이 게이트가 잡으려는 상태다.
case "$VERDICT" in
  *"검사 0건"*)
    red "04:40 회차가 **검사 0건**으로 GREEN 을 냈다 — 실제로 본 무인 회차가 없다.
     요약줄: $VERDICT" ;;
esac

echo "backup-cron-streak green — 04:40 회차 판정 GREEN · ${AGE_H}시간 전(허용 ${MAX_H}시간) · 재실행 0건"
