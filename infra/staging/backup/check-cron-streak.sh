#!/usr/bin/env bash
# 크론 무인 연속 GREEN 을 **기계가 다시 잰다** — `R-1` 통과 기준 ⑴ (`PLAN-SoT §9 〈255〉-㉮`).
#
# ── 왜 이 파일이 생겼는가 ────────────────────────────────────────────────────
# `〈255〉` 는 ⑴ 의 기준을 확정하면서 **남은 조건 ⓑ** 를 함께 적었다 — 축자
#   「⑴ 을 회차마다 다시 재는 기구가 게이트 밖(사람이 `LAST-SUCCESS.txt` 를 본다)」.
# 기준이 선 것과 그 기준을 **다음 회차가 자동으로 다시 재는 것**은 다른 사실이다.
# 사람이 파일을 열어 보는 것은 기구가 아니다 — 안 열어 보면 값이 없는 것과 같다.
# 그래서 ⑴ 의 세 조각을 각각 읽어서 판정한다:
#   C1  `backup-full.sh` 의 **무인** 회차가 **연속 3회 이상 GREEN**
#   C2  각 회차 로그에 **1단 회차 표지**(`═══ 1단`)
#   C3  **같은 회차 스탬프의 볼륨 산출물이 보관처에 실재**
#
# ── 무인과 손을 어떻게 가르는가 (한계를 감추지 않는다) ───────────────────────
# `run-scheduled.sh` 는 크론이 부르든 사람이 부르든 `LAST-SUCCESS.txt` 에 **같은 모양**으로
# 적는다. 실행자를 기록하는 필드가 없다. 그래서 여기서는 **예정 시각 창**으로 가른다 —
# 크론 선언(`schedule.crontab` 03:30)의 시:분에서 `COLAB_CRON_WINDOW_MIN` 분 안에 든
# 회차만 무인으로 센다. **이것은 근사다.** 사람이 03:30~03:59 에 손으로 돌리면 무인으로
# 세어진다. 그 한계를 여기 적고, 요약줄에도 창의 값을 찍는다 — 안 보이는 근사는 거짓말이 된다.
# 완전한 해법 = `run-scheduled.sh` 가 실행자를 적는 것이고, 그것은 이 회차의 범위 밖이다.
#
# ── fail-closed ──────────────────────────────────────────────────────────────
# 읽을 것이 없는 상태(`LAST-SUCCESS.txt` 부재 · 로그 부재 · 회차 0건)는 **RED** 다.
# 「검사 대상 0건」을 통과로 읽지 않는다(`lib.sh verdict` ⓒ · `CLAUDE.md §4`).
#
# 환경변수
#   COLAB_BACKUP_STATE_DIR   상태 디렉터리 (기본 = 보관처의 부모)
#   COLAB_CRON_STREAK_MIN    요구 연속 회차 (기본 3 — `〈255〉-㉮` 축자 「연속 3회 이상」)
#   COLAB_CRON_HHMM          예정 시각 HHMM (기본 0330 — `schedule.crontab`)
#   COLAB_CRON_WINDOW_MIN    예정 시각 허용 창(분) (기본 30)
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
. "$HERE/volume-lib.sh"
load_config
load_volume_config

STATE="${COLAB_BACKUP_STATE_DIR:-$(dirname "$COLAB_BACKUP_DIR")}"
LAST="$STATE/LAST-SUCCESS.txt"
LOG="${COLAB_CRON_STREAK_LOG:-$STATE/staging-backup.log}"
NEED="${COLAB_CRON_STREAK_MIN:-3}"
HHMM="${COLAB_CRON_HHMM:-0330}"
WIN="${COLAB_CRON_WINDOW_MIN:-30}"
PASSED=0; FAILED=0; SKIPPED=0

echo "════ R-1 ⑴ 재측정 — 무인 연속 GREEN (요구 ${NEED}회 · 예정 ${HHMM} ±${WIN}분)"

# ── 입력 실재 ────────────────────────────────────────────────────────────────
if [ ! -f "$LAST" ]; then
  fail "성공 기록이 없다: $LAST — 「한 번도 안 돌았다」와 구분되지 않는다"
  verdict "크론 연속 GREEN"; exit $?
fi
if [ ! -f "$LOG" ]; then
  fail "로그가 없다: $LOG — 1단 표지를 셀 수 없다"
  verdict "크론 연속 GREEN"; exit $?
fi

# 예정 시각 창 안에 든 `backup-full.sh OK` 회차만 남긴다.
# LAST-SUCCESS 한 줄 = `2026-09-02T03:30:47+0900 backup-full.sh OK`
WANT_MIN=$(( 10#${HHMM:0:2} * 60 + 10#${HHMM:2:2} ))
UNATTENDED="$(
  grep -F 'backup-full.sh OK' "$LAST" 2>/dev/null | while IFS= read -r line; do
    ts="${line%% *}"                       # 2026-09-02T03:30:47+0900
    d="${ts%%T*}"                          # 2026-09-02
    hm="${ts#*T}"; h="${hm:0:2}"; m="${hm:3:2}"
    cur=$(( 10#$h * 60 + 10#$m ))
    diff=$(( cur - WANT_MIN )); [ "$diff" -lt 0 ] && diff=$(( -diff ))
    [ "$diff" -le "$WIN" ] && printf '%s\t%s\n' "$d" "$ts"
  done
)"

CNT="$(printf '%s' "$UNATTENDED" | grep -c . || true)"
if [ "$CNT" -eq 0 ]; then
  fail "무인 회차 0건 — \`backup-full.sh\` 의 예정 시각 창 안 성공 기록이 없다 (손으로 돌린 GREEN 은 세지 않는다)"
  verdict "크론 연속 GREEN"; exit $?
fi

# ── C1 연속성 — 마지막 NEED 회차가 **연속된 날짜**여야 한다 ──────────────────
# `LAST-SUCCESS.txt` 는 성공만 적는다. 그래서 **날짜가 건너뛰면 그 날은 못 돌았거나 실패**다.
# 「최근 3줄이 OK」만 보면 08-29·09-01·09-02 같은 구멍 난 3회를 연속으로 읽는다.
mapfile -t DAYS < <(printf '%s\n' "$UNATTENDED" | cut -f1 | awk '!seen[$0]++' | tail -n "$NEED")
if [ "${#DAYS[@]}" -lt "$NEED" ]; then
  fail "무인 회차가 ${#DAYS[@]}일뿐이다 — 요구 ${NEED}일 (연속 이전에 건수가 모자란다)"
else
  GAP=0
  for i in $(seq 1 $(( NEED - 1 ))); do
    prev="$(date -d "${DAYS[$((i-1))]} +1 day" +%F 2>/dev/null)"
    [ "$prev" = "${DAYS[$i]}" ] || { fail "연속이 끊겼다: ${DAYS[$((i-1))]} 다음이 ${DAYS[$i]} 다"; GAP=1; }
  done
  [ "$GAP" -eq 0 ] && pass "C1 무인 연속 ${NEED}회 GREEN — ${DAYS[0]} ~ ${DAYS[$((NEED-1))]}"
fi

# ── C1-b 신선도 — 가장 최근 무인 회차가 오늘 또는 어제여야 한다 ──────────────
# 연속 3회가 **과거에** 있었다는 것은 지금도 돌고 있다는 뜻이 아니다.
# 이 줄이 없으면 크론이 오늘 죽어도 지난 주 3회로 GREEN 이 유지된다 — green-by-stale.
NEWEST="${DAYS[-1]}"
TODAY="$(date +%F)"; YDAY="$(date -d 'yesterday' +%F)"
if [ "$NEWEST" = "$TODAY" ] || [ "$NEWEST" = "$YDAY" ]; then
  pass "C1-b 최신 무인 회차 $NEWEST — 오늘($TODAY) 기준 신선하다"
else
  fail "C1-b 최신 무인 회차가 $NEWEST 다 — 오늘($TODAY)·어제($YDAY) 어느 쪽도 아니다. 크론이 멈춰 있다"
fi

# ── C2 각 회차 로그에 1단 표지 ───────────────────────────────────────────────
for d in "${DAYS[@]}"; do
  n="$(grep -cF "$d" <(grep -F '═══ 1단' "$LOG") || true)"
  if [ "${n:-0}" -ge 1 ]; then pass "C2 $d 1단 회차 표지 ${n}건"
  else fail "C2 $d 로그에 \`═══ 1단\` 표지가 없다 — \`backup-full.sh\` 가 아니라 원장 전용 백업이 돌았을 수 있다(〈174〉 green-by-skip)"; fi
done

# ── C3 같은 회차 스탬프의 볼륨 산출물 실재 ───────────────────────────────────
# 스탬프는 `vol-<볼륨>-<YYYYMMDD>T<HHMMSS>.tar.gz` 다. 회차 날짜와 같은 날짜의 것을 찾는다.
VN=0
for v in $(volume_list); do
  VN=$((VN+1))
  for d in "${DAYS[@]}"; do
    stamp="${d//-/}"
    f="$(ls -1 "$COLAB_BACKUP_DIR/vol-$v-${stamp}T"*.tar.gz 2>/dev/null | tail -1)"
    if [ -n "$f" ] && [ -s "$f" ]; then pass "C3 $d 볼륨 $v 산출물 실재 — $(basename "$f")"
    else fail "C3 $d 볼륨 $v 산출물이 보관처에 없다 — 원장만 뜨고 볼륨이 조용히 멈춘 모양이다"; fi
  done
done
[ "$VN" -eq 0 ] && fail "C3 검사 대상 볼륨이 0건이다 — \`COLAB_VOLBACKUP_VOLUMES\` 가 비었다"

verdict "크론 연속 GREEN"
