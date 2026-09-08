#!/usr/bin/env bash
# frontend-visual — **실화면 시각 되먹임**(Test 단계). `agent-browser` 로 페이지를 열어
# computed 글자 크기와 상속 배경 기준 대비를 재고, 라이트·다크 스크린샷을 근거로 남긴다.
#
# 무엇을 해소하나:
#   `frontend-test`(vitest · jsdom)는 **실제 CSS 레이아웃을 계산하지 않는다.** 그래서 11px 글자와
#   4.2:1 대비는 전 게이트 green 인 채로 화면에 서 있을 수 있었다 — `gates/README.md` 는 그 자리를
#   「화면 스모크(Playwright) 물음으로 남아 있다」로 적어 두었고, 그 물음이 이 게이트다.
#   Playwright 를 새로 들이지 않는다 — 실화면 계측 도구의 정본은 `agent-browser`
#   (`.claude/skills/design-review/SKILL.md §2-5`)이고 이 게이트는 그 스킬의 판정부
#   (`scripts/live_audit.sh` ＋ `live_probe.js`)를 **그대로** 돈다. 게이트가 자기 사본을 만들면
#   그 순간 「게이트가 보는 것」과 「사람이 보는 것」이 갈린다(frontend-fixture-reach 와 같은 원칙).
#
# 입력 (레포 규약 — 선언되면 검사 · 명시 면제면 건수를 보이며 건너뜀 · 침묵은 실패):
#   COLAB_VISUAL_URLS      공백으로 나눈 대상 URL 들. 로컬 스택 또는 Ted 지정 주소.
#   COLAB_VISUAL_EXEMPT=1  이번 회차에 실화면 대상이 없음을 **명시 선언**한다.
#   미선언(둘 다 없음) → red(준비 · 입력미선언 · 78). 기본값으로 green 을 만들지 않는다
#   (`.claude/skills/colab-v2-work/SKILL.md §4` green-by-skip 금지).
#
# 판정 (red(판정)):
#   probe 의 `counts.lowContrast > 0` 또는 `counts.small > 0` — 단, 허용 목록
#   `gates/fixtures/frontend-visual/allow.txt`(셀렉터 **접두사** 한 줄에 하나 · 빈 파일 가능)에
#   걸리는 항목은 뺀다. 남은 것이 하나라도 있으면 red.
#   probe 자체가 실패한 페이지도 red — 「못 쟀다」를 「문제 없다」로 적지 않는다.
#
# red(준비 · 78): `agent-browser` 부재 · 판정부 스크립트 부재 · python3 부재 · 입력 미선언.
#
# ⚠ 앱을 향해서는 **읽기 전용**이다. 클릭·입력·폼 제출을 하지 않는다(§2-5 · §4).
#   스크린샷은 **근거**이지 판정이 아니다 — 누름 피드백·드래그 추적 같은 항목은 사람이 본다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_readiness.sh"

AUDIT="${COLAB_VISUAL_AUDIT:-$REPO_ROOT/.claude/skills/design-review/scripts/live_audit.sh}"
ALLOW="${COLAB_VISUAL_ALLOW:-$REPO_ROOT/gates/fixtures/frontend-visual/allow.txt}"

red() { echo "::error::frontend-visual red(판정) — $*"; exit 1; }
ready_red() { # $1=선언되지 않은/없는 것 $2=사유
  readiness_undeclared_input "frontend-visual" "$1" "$2"
  exit "$READINESS_EXIT"
}

# ── ⑴ 입력 선언 ─────────────────────────────────────────────────────────────
URLS="${COLAB_VISUAL_URLS:-}"
if [ -z "$URLS" ]; then
  if [ "${COLAB_VISUAL_EXEMPT:-}" = "1" ]; then
    # 명시 면제 — **건너뛰되 그 사실과 건수를 출력에 그대로 찍는다.** 조용한 폴백은 없다.
    echo "frontend-visual green(명시 면제) — COLAB_VISUAL_EXEMPT=1 로 선언됨. 페이지 0건 · small 0건 · lowContrast 0건 · 스크린샷 0장."
    echo "   ⚠ 면제는 「문제 없음」이 아니라 「이번 회차에 실화면 대상을 두지 않았다」는 선언이다."
    exit 0
  fi
  ready_red "COLAB_VISUAL_URLS" \
    "실화면 계측 대상 URL 이 선언되지 않았다. 선언하는 법 = COLAB_VISUAL_URLS='http://127.0.0.1:5173/ http://127.0.0.1:5173/projects' bash gates/run.sh frontend-visual · 이번 회차에 대상이 없다면 COLAB_VISUAL_EXEMPT=1 로 **명시 면제**를 선언한다(건수가 출력에 찍힌다)."
fi

# ── ⑵ 판정 재료 ─────────────────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || ready_red "python3" "probe JSON 을 읽을 수 없다."
[ -f "$AUDIT" ] || ready_red "$AUDIT" "실화면 계측 판정부(design-review 스킬의 live_audit.sh)가 이 체크아웃에 없다."
command -v agent-browser >/dev/null 2>&1 || ready_red "agent-browser 실행 파일" \
  "설치하는 법 = npm i -g agent-browser && agent-browser install · 점검 = agent-browser doctor. Playwright 를 대신 들이지 않는다(design-review SKILL §2-5)."

OUTBASE="${COLAB_GATE_REPORT_DIR:-}"
if [ -n "$OUTBASE" ]; then
  case "$OUTBASE" in /*) ;; *) OUTBASE="$REPO_ROOT/$OUTBASE" ;; esac
else
  OUTBASE="$(mktemp -d -t frontend-visual-XXXXXX)"
  echo "  ⚠ COLAB_GATE_REPORT_DIR 미선언 — 근거를 임시 자리에 남긴다: $OUTBASE (커밋되지 않는다)"
fi
OUT="$OUTBASE/frontend-visual"
mkdir -p "$OUT" || ready_red "$OUT" "근거 배출 자리를 만들지 못했다."

# ── ⑶ 계측 — 판정부를 그대로 돈다 (읽기 전용) ────────────────────────────────
# shellcheck disable=SC2086
AUDIT_OUT="$(bash "$AUDIT" "$OUT" $URLS 2>&1)"; arc=$?
if [ "$arc" -eq 78 ]; then
  ready_red "agent-browser" "판정부가 78 로 끝났다(설치 부재). 출력:
$(printf '%s\n' "$AUDIT_OUT" | tr '\n' ' ')"
fi
if [ "$arc" -ne 0 ]; then
  red "실화면 계측이 비정상 종료했다(rc=$arc) — 「못 쟀다」를 통과로 세지 않는다.
$(printf '%s\n' "$AUDIT_OUT" | sed 's/^/     /')"
fi

# ── ⑷ 판정 — probe JSON 을 허용 목록으로 걸러 센다 ──────────────────────────
VERDICT="$(python3 - "$OUT" "$ALLOW" <<'PY'
import glob, json, os, sys
out_dir, allow_path = sys.argv[1], sys.argv[2]
prefixes = []
if os.path.exists(allow_path):
    for line in open(allow_path, encoding='utf-8'):
        s = line.split('#', 1)[0].strip()
        if s:
            prefixes.append(s)

def allowed(sel):
    return any(sel.startswith(p) for p in prefixes)

files = sorted(glob.glob(os.path.join(out_dir, '*.probe.json')))
pages = small = low = 0
lines, failed = [], []
for f in files:
    pages += 1
    name = os.path.basename(f)[:-len('.probe.json')]
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception as e:
        failed.append('%s: probe JSON 을 읽지 못했다 (%s)' % (name, e))
        continue
    if not d.get('success'):
        failed.append('%s: probe 실패 (%s)' % (name, d.get('error')))
        continue
    res = (d.get('data') or {}).get('result') or {}
    if 'counts' not in res:
        failed.append('%s: probe 출력에 counts 가 없다' % name)
        continue
    s = [r for r in res.get('small', []) if not allowed(r.get('sel', ''))]
    l = [r for r in res.get('lowContrast', []) if not allowed(r.get('sel', ''))]
    small += len(s)
    low += len(l)
    for r in s:
        lines.append('%s · <13px · %s · %spx · "%s"' % (name, r.get('sel'), r.get('px'), r.get('text')))
    for r in l:
        lines.append('%s · 대비<4.5 · %s · %s:1 · "%s"' % (name, r.get('sel'), r.get('ratio'), r.get('text')))
shots = len(glob.glob(os.path.join(out_dir, '*.png')))
print(json.dumps({'pages': pages, 'small': small, 'low': low, 'shots': shots,
                  'lines': lines, 'failed': failed, 'allow': len(prefixes)}, ensure_ascii=False))
PY
)"; prc=$?
{ [ "$prc" -eq 0 ] && [ -n "$VERDICT" ]; } || red "probe JSON 판정부가 값을 내지 못했다(rc=$prc)."

COUNTS="$(printf '%s' "$VERDICT" | python3 -c '
import json,sys
d=json.load(sys.stdin)
print(d["pages"], d["small"], d["low"], d["shots"], d["allow"], len(d["failed"]))')"
read -r N_PAGES N_SMALL N_LOW N_SHOTS N_ALLOW N_FAILED <<< "$COUNTS"

if [ "$N_PAGES" -eq 0 ]; then
  red "선언된 URL 이 있는데 probe 결과가 **0건**이다 — 통과가 아니라 계측이 빗나간 것이다 (green-by-skip 금지). 근거 자리: $OUT"
fi

if [ "$N_FAILED" -ne 0 ]; then
  echo "::error::frontend-visual red(판정) — probe 가 실패한 페이지가 ${N_FAILED}건이다. 「못 쟀다」는 「문제 없다」가 아니다."
  printf '%s' "$VERDICT" | python3 -c 'import json,sys
for x in json.load(sys.stdin)["failed"]: print("     - " + x)'
  exit 1
fi

if [ "$N_SMALL" -ne 0 ] || [ "$N_LOW" -ne 0 ]; then
  echo "::error::frontend-visual red(판정) — 페이지 ${N_PAGES}건 · 13px 미만 ${N_SMALL}건 · 대비<4.5 ${N_LOW}건 · 스크린샷 ${N_SHOTS}장 (허용 접두사 ${N_ALLOW}개 적용 후)."
  printf '%s' "$VERDICT" | python3 -c 'import json,sys
for x in json.load(sys.stdin)["lines"][:40]: print("     - " + x)'
  echo "   근거(스크린샷 ${N_SHOTS}장 · index.md): $OUT"
  echo "   허용 목록으로 접으려면 gates/fixtures/frontend-visual/allow.txt 에 셀렉터 접두사를 적는다 — **판정은 사람이 한다.**"
  exit 1
fi

echo "frontend-visual green — 페이지 ${N_PAGES}건 · 13px 미만 0건 · 대비<4.5 0건 · 스크린샷 ${N_SHOTS}장 (허용 접두사 ${N_ALLOW}개). 근거: $OUT"
exit 0
