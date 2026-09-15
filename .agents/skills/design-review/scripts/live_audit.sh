#!/usr/bin/env bash
# live_audit.sh — 실화면 계측 (agent-browser). 읽기 전용: 페이지를 열고 재고 찍는다. 아무것도 쓰지 않는다.
# 사용:  live_audit.sh <out_dir> <url> [<url> ...]
# 전제:  agent-browser 설치(`npm i -g agent-browser && agent-browser install`) · 대상 앱이 떠 있음(로컬 스택 또는 Ted 지정 URL).
#        로그인 상태가 필요하면 먼저 `agent-browser --session design auth login <name>` 으로 상태를 저장한다.
# 산출:  <out_dir>/<slug>.light.png · .dark.png · .probe.json · <out_dir>/index.md (요약표)
set -euo pipefail
OUT="${1:?out_dir}"; shift
[ $# -ge 1 ] || { echo "usage: $0 <out_dir> <url>..." >&2; exit 2; }
HERE="$(cd "$(dirname "$0")" && pwd)"
S="${AB_SESSION:-design}"
VW="${AB_VIEWPORT_W:-1440}"; VH="${AB_VIEWPORT_H:-900}"
mkdir -p "$OUT"
command -v agent-browser >/dev/null || { echo "agent-browser not installed" >&2; exit 78; }
{
  echo "# live_audit — $(date +%F) · viewport ${VW}x${VH} · session $S"
  echo
  echo "| page | text el | <13px | contrast<4.5 | :active rules | reduced-motion blocks | keyframes | screenshots |"
  echo "|---|---|---|---|---|---|---|---|"
} > "$OUT/index.md"
for URL in "$@"; do
  SLUG="$(echo "$URL" | sed -E 's#^[a-z]+://##; s#[^A-Za-z0-9._-]+#_#g; s#_+$##' | cut -c1-60)"
  agent-browser --session "$S" set viewport "$VW" "$VH" >/dev/null
  agent-browser --session "$S" set media light >/dev/null
  agent-browser --session "$S" open "$URL" >/dev/null
  agent-browser --session "$S" wait --load networkidle >/dev/null || true
  agent-browser --session "$S" screenshot "$OUT/$SLUG.light.png" >/dev/null
  agent-browser --session "$S" eval --stdin --json < "$HERE/live_probe.js" > "$OUT/$SLUG.probe.json"
  agent-browser --session "$S" set media dark >/dev/null
  agent-browser --session "$S" screenshot "$OUT/$SLUG.dark.png" >/dev/null
  agent-browser --session "$S" set media light >/dev/null
  python3 - "$OUT/$SLUG.probe.json" "$URL" "$SLUG" >> "$OUT/index.md" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
if not d.get('success'):
    print(f"| `{sys.argv[2]}` | probe failed: {d.get('error')} | | | | | | |"); sys.exit(0)
c = d['data']['result']['counts']
print(f"| `{sys.argv[2]}` | {c['textElements']} | {c['small']} | {c['lowContrast']} | {c['activeRules']} | {c['reducedMotionBlocks']} | {c['keyframes']} | `{sys.argv[3]}.light.png` · `.dark.png` |")
PY
done
echo >> "$OUT/index.md"
echo "상세(요소별 px·대비)는 각 \`*.probe.json\` 의 \`small\`·\`lowContrast\`. 스크린샷은 사람이 본다 — 스크립트는 판정하지 않는다." >> "$OUT/index.md"
cat "$OUT/index.md"
