#!/usr/bin/env bash
# frontend-visual 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 픽스처 원본 = `gates/fixtures/frontend-visual/{green,red}.html`.
# ⚠ **사본을 뜬다.** 이 레포의 경로에는 공백이 들어 있고(`00 CoLAB`), `COLAB_VISUAL_URLS` 는
#   공백으로 나눈 목록이라 원본 자리를 그대로 `file://` 로 가리키면 URL 이 갈라진다.
#   그래서 `mktemp -d`(공백 없는 자리)로 복사해 거기를 가리킨다 — 원본은 읽기만 한다.
#   `agent-browser 0.27.0` 이 `file://` 을 여는 것은 이 세션에서 실측했다(오프라인 동작).
#
# 케이스 — green 하나 · red(판정) 하나 · red(준비) 하나 · green(명시 면제) 하나.
#   ⓐ green.html   13px 이상 · 대비 ≥4.5 · `:active` 규칙 · reduced-motion 블록 → green
#   ⓑ red.html     11px 글자 ＋ 4.2:1 짝                                        → red(판정)
#   ⓒ 미선언        COLAB_VISUAL_URLS·COLAB_VISUAL_EXEMPT 둘 다 없음            → red(준비 · 78 · 입력미선언)
#   ⓓ 명시 면제     COLAB_VISUAL_EXEMPT=1 — 건수를 보이며 건너뛴다              → green
#
# 판정부(`live_audit.sh`) 세션 소유 — PATH 앞자리의 **가짜 `agent-browser`**(인자를 파일에 적는다)로 잰다.
#   실브라우저를 띄우지 않으므로 호스트의 다른 세션과 무관하다 (spec `S-HARNESS-LANE-HYGIENE-20260924` F2).
#   ⑶ `AB_SESSION` 없음 → 고유 세션(`la-…`)으로 돌고 끝에 `close` 1회
#   ⑷ `AB_SESSION=x`   → 호출자 소유 세션 `x` 로 돌고 `close` 0회
#   ⑸ 실브라우저 ⓐ·ⓑ 뒤 판정부가 연 `la-…` 세션의 프로세스 0개(5초 안)
#
# ⓑ 가 통과해 버리면 이 게이트는 아무것도 막지 않는다 — 그 케이스가 이 셀프테스트의 존재 이유다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/frontend-visual.sh"
FIX="$REPO_ROOT/gates/fixtures/frontend-visual"
FAILED=0

red() { echo "::error::frontend-visual-selftest red — $*"; FAILED=1; }

# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나 — 78 을 「기대한 red」로 접지 않는다.
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

[ -x "$GATE" ] || { echo "::error::frontend-visual-selftest red — 판정 재료가 없다: $GATE"; exit 1; }
for f in green.html red.html; do
  [ -f "$FIX/$f" ] || { echo "::error::frontend-visual-selftest red — 픽스처가 없다: $FIX/$f"; exit 1; }
done

WORK="$(mktemp -d -t frontend-visual-selftest-XXXXXX)"
REPORTS="$(mktemp -d -t frontend-visual-reports-XXXXXX)"
cleanup() { rm -rf "$WORK" "$REPORTS"; }
trap cleanup EXIT
cp "$FIX/green.html" "$FIX/red.html" "$WORK/"

expect() { # $1=기대(green|red|미선언) $2=이름 $3=케이스 키
  local want="$1" label="$2" key="$3" out rc
  case "$key" in
    green|red)
      out="$(COLAB_GATE_REPORT_DIR="$REPORTS/$key" COLAB_VISUAL_URLS="file://$WORK/$key.html" \
             COLAB_VISUAL_EXEMPT= "$GATE" 2>&1)"; rc=$? ;;
    undeclared)
      out="$(COLAB_GATE_REPORT_DIR="$REPORTS/$key" COLAB_VISUAL_URLS= COLAB_VISUAL_EXEMPT= "$GATE" 2>&1)"; rc=$? ;;
    exempt)
      out="$(COLAB_GATE_REPORT_DIR="$REPORTS/$key" COLAB_VISUAL_URLS= COLAB_VISUAL_EXEMPT=1 "$GATE" 2>&1)"; rc=$? ;;
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
  if [ "$key" = exempt ] && ! printf '%s' "$out" | grep -q '페이지 0건'; then
    red "$label — 면제인데 건수를 출력하지 않았다(조용한 건너뛰기):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  # red 케이스는 무엇이 걸렸는지 **이름으로** 내야 한다.
  if [ "$key" = red ] && ! printf '%s' "$out" | grep -q 'p\.tiny'; then
    red "$label — red 인데 위반 요소를 셀렉터로 내지 않았다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  echo "  ✓ $label ($want)"
}

# ⓐ 대조군 — 이것이 green 이 아니면 아래 red 는 아무 말도 하지 않는다.
expect green  "ⓐ 13px 이상 · 대비 ≥4.5 · :active · reduced-motion" green
# ⓑ 이 게이트의 존재 이유 — jsdom 이 못 보는 자리(computed px · 상속 배경 대비)를 실화면이 잡는다.
expect red    "ⓑ 11px 글자 ＋ 대비 4.2:1" red
# ⓒ 입력 미선언 — 기본값으로 green 을 만들지 않는다.
expect 미선언 "ⓒ COLAB_VISUAL_URLS 미선언" undeclared
# ⓓ 명시 면제 — 건너뛰되 건수를 보인다.
expect green  "ⓓ COLAB_VISUAL_EXEMPT=1 명시 면제" exempt

# ── ⑶⑷ 판정부가 **자기가 연 세션만** 닫는가 — 가짜 agent-browser ─────────────
# 가짜는 `eval` 에 실패 JSON 을 내고 나머지는 exit 0 이다 — 판정부가 정상 완주하는 경로에서 센다.
# 가짜가 한 번도 불리지 않으면 red 다(green-by-skip 방지).
AUDIT_SRC="$REPO_ROOT/.agents/skills/design-review/scripts/live_audit.sh"
FAKEBIN="$WORK/fakebin"; mkdir -p "$FAKEBIN"
cat > "$FAKEBIN/agent-browser" <<'SH'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$FAKE_AB_LOG"
case " $* " in *" eval "*) echo '{"success":false,"error":"fake"}' ;; esac
exit 0
SH
chmod +x "$FAKEBIN/agent-browser"
session_case() { # $1=라벨 $2=AB_SESSION 값(빈 값이면 unset) → LOG · RC 를 채운다
  local key="$1" sess="$2"
  LOG="$WORK/fake-ab-$key.log"; : > "$LOG"
  if [ -n "$sess" ]; then
    env PATH="$FAKEBIN:$PATH" FAKE_AB_LOG="$LOG" AB_SESSION="$sess" \
      bash "$AUDIT_SRC" "$WORK/audit-$key" "file://$WORK/green.html" >/dev/null 2>&1; RC=$?
  else
    env -u AB_SESSION PATH="$FAKEBIN:$PATH" FAKE_AB_LOG="$LOG" \
      bash "$AUDIT_SRC" "$WORK/audit-$key" "file://$WORK/green.html" >/dev/null 2>&1; RC=$?
  fi
}
calls_of()   { wc -l < "$LOG" | tr -d ' '; }
closes_of()  { grep -cE '^--session [^ ]+ close$' "$LOG" || true; }
sessions_of() { sed -nE 's/^--session ([^ ]+) .*/\1/p' "$LOG" | sort -u; }

session_case s3 ""
n="$(calls_of)"; c="$(closes_of)"; ss="$(sessions_of)"
if [ "$RC" -ne 0 ]; then red "⑶ AB_SESSION 없음 — 판정부가 비정상 종료(rc=$RC)"
elif [ "$n" -eq 0 ]; then red "⑶ AB_SESSION 없음 — 가짜 agent-browser 가 한 번도 불리지 않았다(아무것도 재지 않았다)"
elif [ "$(printf '%s\n' "$ss" | wc -l | tr -d ' ')" -ne 1 ]; then red "⑶ AB_SESSION 없음 — 세션이 하나가 아니다: $(printf '%s ' $ss)"
else
  case "$ss" in
    la-*) if [ "$c" = 1 ]; then echo "  ✓ ⑶ AB_SESSION 없음 → 고유 세션 $ss · close 1회 (호출 ${n}건)"
          else red "⑶ AB_SESSION 없음 — 고유 세션 $ss 의 close ${c}회 (기대 1회) — 연 세션을 닫지 않았다"; fi ;;
    *)    red "⑶ AB_SESSION 없음 — 고유 세션이 아니라 '$ss' 를 썼다 (기대 la-<pid>-<epoch>) — 다른 호출자 세션과 섞인다" ;;
  esac
fi

session_case s4 x
n="$(calls_of)"; c="$(closes_of)"; ss="$(sessions_of)"
if [ "$RC" -ne 0 ]; then red "⑷ AB_SESSION=x — 판정부가 비정상 종료(rc=$RC)"
elif [ "$n" -eq 0 ]; then red "⑷ AB_SESSION=x — 가짜 agent-browser 가 한 번도 불리지 않았다(아무것도 재지 않았다)"
elif [ "$ss" != x ]; then red "⑷ AB_SESSION=x — 호출자 세션이 아닌 세션을 썼다: $(printf '%s ' $ss)"
elif [ "$c" != 0 ]; then red "⑷ AB_SESSION=x — 호출자 소유 세션을 ${c}회 닫았다 (기대 0회) — 로그인 선행 흐름이 깨진다"
else echo "  ✓ ⑷ AB_SESSION=x → 호출자 세션 x · close 0회 (호출 ${n}건)"; fi

# ── ⑸ 실브라우저 ⓐ·ⓑ 뒤 판정부가 연 세션의 프로세스가 남지 않는다 ─────────────────
#   ⑶ 은 가짜 바이너리로 close **호출**만 잰다. 이것은 실제 데몬·chrome 의 **소멸**을 잰다
#   (spec v2 F2 실효 · advisor ② 차단급). 세션 이름은 판정부가 index.md 머리에 찍은 값이고,
#   데몬과 chrome 은 env `AGENT_BROWSER_SESSION=<이름>` 을 지닌다. close 뒤 chrome 이 내려가는
#   시간을 5초까지 본다 — 넘기면 남은 것이다. 남의 세션은 이름이 달라 세지 않는다.
for key in green red; do
  idx="$REPORTS/$key/frontend-visual/index.md"
  if [ ! -f "$idx" ]; then
    # ⓐ·ⓑ 가 준비 실패로 가로채였으면 판정부가 돌지 않았다 — 아래 준비 판정이 통과를 막는다.
    [ -n "${EXPECT_READINESS[*]:-}" ] && continue
    red "⑸ $key — 판정부 index.md 가 없다($idx) · 세션 소멸을 잴 수 없다"; continue
  fi
  sess="$(sed -n '1s/.* · session \(.*\)$/\1/p' "$idx")"
  case "$sess" in
    la-*) ;;
    *) red "⑸ $key — 판정부 세션이 고유 세션이 아니다('$sess')"; continue ;;
  esac
  left=""
  for _ in 1 2 3 4 5 6; do
    left=""
    for e in /proc/[0-9]*/environ; do
      # 2>/dev/null 을 < 앞에 둔다 — bash 는 왼쪽부터 적용하므로 남의 /proc 권한 거부가 로그에 새지 않는다.
      if tr '\0' '\n' 2>/dev/null < "$e" | grep -qxF "AGENT_BROWSER_SESSION=$sess"; then
        pid="${e#/proc/}"; left="$left ${pid%/environ}"
      fi
    done
    [ -z "$left" ] && break
    sleep 1
  done
  if [ -n "$left" ]; then
    red "⑸ $key — 판정부 세션 $sess 의 프로세스가 5초 뒤에도 남았다(pid$left) — 연 브라우저를 닫지 않았다"
  else
    echo "  ✓ ⑸ $key 실브라우저 뒤 세션 $sess 프로세스 0개"
  fi
done

if [ "$FAILED" -ne 0 ]; then
  echo "::error::frontend-visual-selftest red — 위 케이스가 기대와 다르다."
  exit 1
fi
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict frontend-visual-selftest
echo "frontend-visual-selftest green — 검사 8건 전건 기대대로 (green 2 · red(판정) 1 · red(준비·입력미선언) 1 · 세션 소유 2 · 세션 소멸 2)."
