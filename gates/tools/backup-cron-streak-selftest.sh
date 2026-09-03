#!/usr/bin/env bash
# backup-cron-streak 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 케이스 8종 — 일곱은 red 여야 하고 하나는 green 이어야 한다.
#   ⓐ 로그 파일 부재              → red (「보관처를 못 본다」와 「0 회차다」는 다르다)
#   ⓑ 요약줄 0건                  → red ← **이 게이트의 존재 이유**. 대상 0건은 통과가 아니다
#   ⓒ 요약줄은 있는데 시각 줄 없음 → red (나이를 못 재는 GREEN 은 판정이 아니다)
#   ⓓ 요약줄이 36시간보다 오래됨   → red (green-by-stale)
#   ⓔ 요약줄이 RED                → red ＋ 그 줄이 출력에 나온다
#   ⓕ 요약줄이 「검사 0건」 GREEN   → red (verdict 의 SKIP-GREEN 을 그대로 받지 않는다)
#   ⓖ 요약줄 모양이 낯설다         → red (모르는 것을 통과로 읽지 않는다)
#   ⓗ GREEN 이고 새것             → green ＋ 나이가 출력에 나온다
#
# 픽스처는 **로그 파일을 직접 짓는다** — 실제 백업도 크론도 돌리지 않는다.
# 돌리면 이 selftest 가 증명하는 것이 「이 호스트에 보관처가 있다」로 바뀐다.
# `~/colab-v2-backups` 에는 **한 글자도 쓰지 않는다.**
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/backup-cron-streak.sh"
FAILED=0

red() { echo "::error::backup-cron-streak-selftest red — $*"; FAILED=1; }

# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나.
# 종전에는 이 파일의 expect() 가 종료코드 78(준비 실패)을 그냥 red 로 접어
# **「기대한 red」로 셌다** — 그 케이스는 판정된 적이 없는데 출력은 ✓ 라고 말했다
# (2026-09-03 코드리뷰 #6 · `CLAUDE.md §4` green-by-skip).
# ⚠ 이 셀프테스트가 부르는 판정부는 오늘 78 을 낼 길이 없다. 그래도 물린다 —
#   **형제를 찾아 같이 고치지 않으면 남은 쪽이 다음 회차에 같은 거짓말을 한다.**
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

[ -x "$GATE" ] || { echo "::error::backup-cron-streak-selftest red — 게이트가 없거나 실행 불가: $GATE"; exit 1; }

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" cron-streak-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM

# 기준 시각을 고정한다 — 시험이 오늘 날짜에 걸리면 내일 색이 바뀐다.
NOW_TS="2026-09-03T09:00:00"
NOW_EPOCH="$(date -d "${NOW_TS/T/ }" +%s)"

# 실측한 실물 모양 그대로 짓는다 (`~/colab-v2-backups/staging-backup.log` · 2026-09-03).
mk_log() {  # $1=경로 $2=요약줄 시각(비면 실행 줄 생략) $3=요약줄 본문
  { echo "════ R-1 ⑴ 재측정 — 무인 연속 GREEN (요구 3회 · 예정 0330 ±30분)"
    echo "  PASS  C1 무인 연속 3회 GREEN — 2026-09-01 ~ 2026-09-03"
    echo "$3"
    [ -n "$2" ] && echo "$2 check-cron-streak.sh 성공"
  } > "$1"
}

expect() {  # $1=기대(red|green) $2=이름 $3=로그경로 [$4=출력에 있어야 할 문자열]
  local want="$1" label="$2" log="$3" needle="${4:-}" out rc
  out="$(COLAB_CRON_STREAK_GATE_LOG="$log" COLAB_CRON_STREAK_NOW="$NOW_EPOCH" \
         COLAB_BACKUP_STATE_DIR="$TMP/없는보관처" "$GATE" 2>&1)"; rc=$?
  # 준비 실패(78 또는 준비 표식)는 **기대한 red 가 아니다** — 판정된 적이 없다.
  # ⭑ ⟨개정 2026-09-03 · 코드리뷰 20260903-F #6⟩ **여기서 `FAILED=1` 을 세우지 않는다.**
  #   세우면 아래 `[ "$FAILED" -ne 0 ] && exit 1` 이 먼저 걸려 종료가 **1(판정 red)** 이
  #   되고, 정작 준비 실패를 말하는 `expect_readiness_verdict`(종료 78)까지 못 간다.
  #   실행기는 1 을 「셀프테스트가 게이트의 결함을 찾았다」로 세므로 **「고칠 결함」과
  #   「환경이 없다」가 다시 섞인다** — `_expect.sh` 가 갈라 놓은 것을 이 한 줄이 도로
  #   접었다. 판정 못 한 케이스는 `EXPECT_READINESS` 에 남아 있고 그것을 78 로 내는 것이
  #   `expect_readiness_verdict` 의 일이다. **어느 쪽이든 red 다** — 색이 아니라 사유가 바뀐다.
  if expect_intercept_readiness "$rc" "$out" "$label" "$want"; then
    return
  fi
  if [ "$want" = red ] && [ "$rc" -eq 0 ]; then
    red "$label — red 여야 하는데 통과했다:
$(echo "$out" | sed 's/^/     /')"; return
  fi
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then
    red "$label — green 이어야 하는데 red 다:
$(echo "$out" | sed 's/^/     /')"; return
  fi
  if [ -n "$needle" ] && ! grep -qF -- "$needle" <<< "$out"; then
    red "$label — 출력에 「$needle」이 없다:
$(echo "$out" | sed 's/^/     /')"; return
  fi
  echo "  ✓ $label ($want)"
}

GREEN_LINE='크론 연속 GREEN: GREEN (통과 11건 · SKIP 0 — 모든 항목이 실제로 돌았다)'
RED_LINE='크론 연속 GREEN: RED (실패 2건 · 통과 9건)'
SKIP_LINE='크론 연속 GREEN: GREEN (**검사 0건 · 승인된 SKIP 3건** — 실제로 본 항목이 없다. 무엇을 안 봤는지는 위 SKIP 줄)'

# ⓐ 로그 부재
expect red "ⓐ 로그 파일 부재" "$TMP/없는파일.log" "로그가 없다"
# ⓑ 요약줄 0건 — 이 게이트의 존재 이유
{ echo "════ R-1 ⑴ 재측정 — 무인 연속 GREEN (요구 3회 · 예정 0330 ±30분)"
  echo "2026-09-03T03:30:47 backup-full.sh 성공"; } > "$TMP/no-verdict.log"
expect red "ⓑ 요약줄 0건" "$TMP/no-verdict.log" "대상 0건은 통과가 아니다"
# ⓒ 요약줄은 있는데 시각 줄이 없다
mk_log "$TMP/no-ts.log" "" "$GREEN_LINE"
expect red "ⓒ 시각 줄 부재" "$TMP/no-ts.log" "요약줄의 시각을 찾지 못했다"
# ⓓ 오래됨 — 37시간 전
mk_log "$TMP/stale.log" "2026-09-01T20:00:00" "$GREEN_LINE"
expect red "ⓓ 36시간 초과" "$TMP/stale.log" "green-by-stale"
# ⓔ 요약줄이 RED
mk_log "$TMP/red.log" "2026-09-03T04:40:05" "$RED_LINE"
expect red "ⓔ 요약줄 RED" "$TMP/red.log" "실패 2건"
# ⓕ 검사 0건 GREEN
mk_log "$TMP/skip.log" "2026-09-03T04:40:05" "$SKIP_LINE"
expect red "ⓕ 검사 0건 GREEN" "$TMP/skip.log" "실제로 본 무인 회차가 없다"
# ⓖ 낯선 모양
mk_log "$TMP/weird.log" "2026-09-03T04:40:05" "크론 연속 GREEN: 아마도 괜찮음"
expect red "ⓖ 낯선 요약줄 모양" "$TMP/weird.log" "모양이 바뀐 것이다"
# ⓗ GREEN 이고 새것 — 4시간 20분 전
mk_log "$TMP/ok.log" "2026-09-03T04:40:05" "$GREEN_LINE"
expect green "ⓗ GREEN · 신선" "$TMP/ok.log" "재실행 0건"

# ── ⓘ~ⓟ **분류기 자체 증명** — `_expect.sh` 의 rc 0 구멍 (코드리뷰 20260903-F #6) ──
#
# `expect_classify` 는 `[ "$rc" = 78 ] || 출력에 표식이 있으면` 으로 갈라 **표식만 보고**
# 준비 실패로 접었다. 그래서 **표식을 찍고 종료 0 으로 나가는 검사기**가 `ready` 로
# 분류됐다 — 「검사기가 통과를 보고했는데 아무것도 검사하지 않았다」가 바로 그 자리에서
# 「환경이 없어 못 돌았다」로 위장한다(`CLAUDE.md §4` green-by-skip 의 분류기판).
# **종료코드가 먼저다.** 0 은 검사기가 「다 됐다」고 말한 것이고, 그 말과 표식이 어긋나면
# 그것 자체가 결함이지 환경 문제가 아니다.
#
# ⚠ 픽스처가 왜 이 파일에 있나 — `_expect.sh` 는 게이트가 아니라 **모든 셀프테스트가
# source 하는 판정부**라 자기 게이트 자리가 없다(`gates/run.sh ALL_GATES` 는 이 회차의
# 편집 면 밖이다). 그것을 source 하는 셀프테스트 안에서 증명한다 — 위 8건과 같은 실행에
# 실려 `selftest` 묶음이 이 증명을 매번 돈다.
FAKE_RC0="$TMP/rc0-with-marker.sh"
{ echo '#!/usr/bin/env bash'
  echo 'echo "::gate-readiness-failure::gate=가짜|waited_for=아무것도|limit=대기 없음|elapsed=0초|detail=표식만 찍고 0 으로 나간다"'
  echo 'exit 0'
} > "$FAKE_RC0"
chmod +x "$FAKE_RC0"

MARK='::gate-readiness-failure::gate=가짜|waited_for=x|limit=대기 없음|elapsed=0초|detail=x'
UNDECL="$MARK|cause=입력미선언"

classify_is() {  # $1=기대 분류 $2=이름 $3=종료코드 $4=출력
  local got
  got="$(expect_classify "$3" "$4")"
  if [ "$got" = "$1" ]; then
    echo "  ✓ $2 ($1)"
  else
    red "$2 — 분류가 「$got」다(기대 「$1」)"
  fi
}

FAKE_OUT="$("$FAKE_RC0" 2>&1)"; FAKE_RC=$?
classify_is green  "ⓘ 표식 ＋ 종료 0 → green (가짜 검사기 실물)" "$FAKE_RC" "$FAKE_OUT"
classify_is green  "ⓙ 표식(cause=입력미선언) ＋ 종료 0 → green"  0  "$UNDECL"
classify_is ready  "ⓚ 종료 78 → ready"                          78 ""
classify_is 미선언 "ⓛ 종료 78 ＋ cause=입력미선언 → 미선언"      78 "$UNDECL"
classify_is ready  "ⓜ 표식 ＋ 종료 1 → ready"                   1  "$MARK"
classify_is red    "ⓝ 표식 없음 ＋ 종료 1 → red"                 1  "아무 말도 없다"
classify_is green  "ⓞ 표식 없음 ＋ 종료 0 → green"               0  "다 됐다"

# ⓟ **그리고 그 케이스에서 셀프테스트가 실제로 red 로 간다.** 가로채기가 면제를 주면
#   「판정 못 함」으로 접혀 red 가 안 뜬다 — 부분 셸로 그 자리를 재현해 확인한다.
if ( FAILURES=(); EXPECT_READINESS=()
     expect_intercept_readiness "$FAKE_RC" "$FAKE_OUT" "가짜" ready >/dev/null && exit 9
     [ "${#EXPECT_READINESS[@]}" -eq 0 ] || exit 8
     exit 0 ); then
  echo "  ✓ ⓟ 표식＋종료 0 은 「판정 못 함」 면제를 못 받는다 (ready 기대 케이스가 red 로 간다)"
else
  red "ⓟ 표식＋종료 0 이 준비 실패로 접혔다 — 검사기가 낸 종료 0 이 가려진다"
fi

if [ "$FAILED" -ne 0 ]; then
  echo "::error::backup-cron-streak-selftest red — 위 케이스가 기대와 다르다."
  exit 1
fi
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict backup-cron-streak-selftest
echo "backup-cron-streak-selftest green — 검사 16건 전건 기대대로 (게이트 8건: red 7 · green 1 ＋ 분류기 8건)"
