#!/usr/bin/env bash
[ "${COLAB_HOOKS:-1}" = "0" ] && exit 0
# H7 — `SubagentStop` (matcher: `lane-worker`) · 스펙 `docs/superpowers/specs/2026-09-06-harness-fable51-design.md` C절·D절.
#
# 무엇을 해소하나 (D11·D12): 레인이 「게이트 green」이라고 **말한 것**과 게이트가 **낸 것**이
#   같은지 확인할 자리가 없었다. 준비 red 를 판정 red 로 읽거나(D12) 게이트를 아예 안 돌린 레인이
#   그대로 종료됐다. 이제 실행기가 요약과 같은 계수로 JSON 을 낸다(스펙 D) — 여기서 그것을 읽는다.
#
# 스펙 C H7 행 축자 —
#   「`reports/<회차>/<레인>/gate-summary.json` 존재 + `counts.red_판정 == 0` 확인.
#     **스키마 위반이 아니라 부재만** 차단하므로 게이트를 안 돌린 레인만 걸린다」
# ⇒ 차단은 둘뿐이다: ⑴ **부재** ⑵ `counts.red_판정 > 0`.
#   JSON 이 깨졌거나 계수를 못 읽으면 **통과**시키고 그 사실만 적는다(스키마 판정처가 아니다).
#
# ⚠ 준비 red(`counts.red_준비`)는 **여기서 차단하지 않는다.** 병합 진입 조건은 판정·준비 둘 다
#   0 이지만(스펙 D), 그 판정은 **오케스트레이터의 병합 시점** 몫이다. 레인 워크트리는 환경이
#   덜 선 상태로 존재할 수 있고, 그것으로 레인 종료를 막으면 훅이 상시 무력화된다.
#   대신 계수를 그대로 stdout 에 적어 오케스트레이터가 보고 판정하게 한다.
#
# ── SubagentStop 입력 스키마 (stdin · 문서 인용 https://code.claude.com/docs/en/hooks) ──────
#   `session_id`·`cwd`·`permission_mode`·`hook_event_name`·`agent_id`·`agent_type`·
#   `last_assistant_message`·`stop_hook_active`
#   · `cwd` — "Current working directory when the hook is invoked" ⇒ 레인의 **워크트리**다.
#   · `agent_type` — "Agent name … Present when the session uses `--agent` or the hook fires
#     inside a subagent. For subagents, the subagent's type takes precedence…"
#   · matcher — "For `SubagentStart` and `SubagentStop`, the matcher filters the agent type."
#   · exit 2 — "SubagentStop: **Prevents the subagent from stopping**. The blocking message is …
#     your stderr text otherwise."  · exit 0 — "For `Stop` and `SubagentStop`, stdout is shown
#     to Claude as context."  ⚠ exit 1 은 통과다(스펙 C).
set -uo pipefail

payload=""
if [ ! -t 0 ]; then payload="$(cat 2>/dev/null || true)"; fi
[ -n "$payload" ] || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

read_fields() {
  printf '%s' "$payload" | python3 -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
if not isinstance(d,dict): sys.exit(0)
print(d.get("cwd") or "")
print(d.get("agent_type") or "")
' 2>/dev/null
}

mapfile -t _f < <(read_fields)
CWD="${_f[0]:-}"
AGENT="${_f[1]:-}"
[ -n "$CWD" ] || exit 0
[ -d "$CWD" ] || exit 0
case "$AGENT" in ""|lane-worker) ;; *) exit 0 ;; esac

# ── 어디를 보나 ──────────────────────────────────────────────────────────────
# ⑴ `COLAB_GATE_REPORT_DIR` 이 훅 환경에 있으면 그 자리(레인 지시문이 지정한 배출처).
#    상대경로는 레인의 `cwd` 기준으로 푼다 — 실행기가 레포 루트 기준으로 푸는 것과 같은 자리다.
# ⑵ 없으면 `dev-package/reports/` 아래에서 **가장 최근에 쓰인** gate-summary.json.
#    (Bash env 는 도구 호출 간 유지되지 않으므로 ⑴ 은 대개 비어 있다 — ⑵ 가 실질 경로다.)
found="$( ( cd "$CWD" && REPORT_DIR="${COLAB_GATE_REPORT_DIR:-}" python3 - <<'PY'
import glob, os
d = os.environ.get("REPORT_DIR") or ""
if d:
    p = d if os.path.isabs(d) else os.path.join(os.getcwd(), d)
    p = os.path.join(p, "gate-summary.json")
    print(p if os.path.exists(p) else "")
else:
    c = glob.glob("dev-package/reports/**/gate-summary.json", recursive=True)
    # 절대경로로 낸다 — 아래 계수 읽기는 훅 자신의 cwd 에서 돌기 때문이다(레인의 cwd 가 아니다).
    print(os.path.abspath(max(c, key=os.path.getmtime)) if c else "")
PY
) 2>/dev/null )"

if [ -z "$found" ]; then
  {
    echo "⛔ 차단(H7 lane-gate-summary) — \`gate-summary.json\` 이 없다. **게이트를 돌리지 않은 레인**이다."
    echo "   낼 것: 변경 대상의 단독 게이트를 배출처를 준 채 돌린다(rules §3-1 — 전수는 병합 직전 1회)."
    echo "     COLAB_GATE_REPORT_DIR=dev-package/reports/<회차>/<레인> bash gates/run.sh <게이트>"
    echo "   그러면 요약과 같은 계수로 dev-package/reports/<회차>/<레인>/gate-summary.json 이 선다(스펙 D)."
    echo "   찾은 자리: COLAB_GATE_REPORT_DIR=${COLAB_GATE_REPORT_DIR:-(미선언)} · dev-package/reports/**/gate-summary.json = 0건 (기준 cwd=$CWD)"
  } >&2
  exit 2
fi

read_counts() { # stdout: <red_판정> <red_준비> <green> <red 게이트 이름들> · 못 읽으면 빈 줄
  python3 - "$found" <<'PY' 2>/dev/null
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    c = d.get("counts") or {}
    red = [g.get("name", "?") for g in (d.get("gates") or []) if g.get("status") == "red_판정"]
    print(int(c.get("red_판정", 0)), int(c.get("red_준비", 0)), int(c.get("green", 0)),
          " ".join(red), sep="\t")
except Exception:
    pass
PY
}

line="$(read_counts)"
if [ -z "$line" ]; then
  echo "H7 — $found 를 읽었으나 계수를 꺼내지 못했다(스키마 위반은 차단 사유가 아니다 · 스펙 C H7). 통과시킨다."
  exit 0
fi
IFS=$'\t' read -r RED_JUDGE RED_READY GREEN RED_NAMES <<< "$line"

if [ "${RED_JUDGE:-0}" -gt 0 ] 2>/dev/null; then
  {
    echo "⛔ 차단(H7 lane-gate-summary) — red(판정) ${RED_JUDGE}건. **검사 대상이 규율을 어겼다** — 고치고 다시 돌린다."
    echo "   red(판정) 게이트: ${RED_NAMES:-(이름 없음)}"
    echo "   근거: ${found#"$CWD"/}"
    echo "   ⚠ 게이트를 우회·비활성화하거나 검사 대상을 줄여 green 을 만들지 않는다(CLAUDE.md §4)."
  } >&2
  exit 2
fi

echo "H7 — green ${GREEN} / red(판정) ${RED_JUDGE} / red(준비) ${RED_READY} · 근거 ${found#"$CWD"/}"
if [ "${RED_READY:-0}" -gt 0 ] 2>/dev/null; then
  echo "   ⚠ red(준비) ${RED_READY}건 — 판정이 아니라 준비가 낸 red 다. **병합 진입 조건은 판정·준비 둘 다 0** 이다(스펙 D). 레인 종료는 막지 않는다."
fi
exit 0
