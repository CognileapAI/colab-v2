#!/usr/bin/env bash
# region-within-drift-selftest — 위 게이트가 red fixture 로 fail-closed 임을 증명한다.
#
# 케이스마다 `mktemp -d` 안에 **실제 입력의 사본**(semantics.json · k2b-graph-standard.tsv ·
# db/ai/seed/*.sql)을 두고 한 곳만 비틀어 게이트에 환경변수로 물린다. 레포 파일은 읽기만 한다.
#   ⓐ 실제 입력 그대로                               → green
#   ⓑ 그래프에서 「남한 안에 있다 한반도」 엣지 삭제   → red(판정 · 남는 하위)
#   ⓒ 그래프에만 있는 한반도 하위(전라권)            → red(판정 · 빠진 하위)
#   ⓓ 표에 상향 하위(그래프는 한반도 안에 있다 동아시아) → red(판정 · 상향 엣지)
#   ⓔ 그래프 팬아웃 7(> 6)                          → red(판정 · 팬아웃)
#   ⓕ 표의 하위 별칭 하나를 뺌                       → red(판정 · 빠진 별칭)
#   ⓖ 그래프 기준 파일 부재                          → red(준비 · 78)
#   ⓗ regionWithin 미선언                            → red(준비 · 입력미선언)
set -u
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GATE="$REPO_ROOT/gates/tools/region-within-drift.sh"
FAILED=0
red() { echo "  ✗ $*"; FAILED=1; }
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

[ -x "$GATE" ] || { echo "::error::region-within-drift-selftest red — 판정 재료가 없다(실행비트 포함): gates/tools/region-within-drift.sh"; exit 1; }
SEM="$REPO_ROOT/contracts/search/semantics.json"
TSV="$REPO_ROOT/db/ai/seed/k2b-graph-standard.tsv"
SEED="$REPO_ROOT/db/ai/seed"
for f in "$SEM" "$TSV"; do
  [ -f "$f" ] || { echo "::gate-readiness-failure::gate=region-within-drift-selftest|detail=입력이 없다: ${f#"$REPO_ROOT/"}"; exit 78; }
done

WORK="$(mktemp -d -t region-within-drift-selftest-XXXXXX)"
trap 'rm -rf "$WORK"' EXIT

# 케이스 하나 = 디렉터리 하나(semantics.json · graph.tsv · seed/*.sql 의 사본).
mk() { # $1=케이스 이름
  local d="$WORK/$1"
  mkdir -p "$d/seed"
  cp "$SEM" "$d/semantics.json"
  cp "$TSV" "$d/graph.tsv"
  cp "$SEED"/*.sql "$d/seed/"
  printf '%s' "$d"
}
edit_json() { # $1=파일 $2=파이썬 문(변수 v 를 고친다)
  python3 -c '
import json, sys
path, code = sys.argv[1], sys.argv[2]
v = json.load(open(path, encoding="utf-8"))
exec(code)
json.dump(v, open(path, "w", encoding="utf-8"), ensure_ascii=False)
' "$1" "$2"
}
add_place() { # $1=디렉터리 $2=노드 id $3=라벨 $4=src $5=dst — 지명 노드 하나와 `안에 있다` 엣지 하나
  printf 'node\t%s\t지명\t%s\t2\tt\t셀프테스트\nedge\t%s\t안에 있다\t%s\t6\t셀프테스트\n' \
    "$2" "$3" "$4" "$5" >> "$1/graph.tsv"
}

C_OK="$(mk ok)"
C_MISSING="$(mk missing_edge)"
grep -v -F "$(printf 'edge\tp-south-korea\t안에 있다\tp-korea-peninsula\t')" "$TSV" > "$C_MISSING/graph.tsv"
C_EXTRA="$(mk extra_graph_child)"
add_place "$C_EXTRA" p-jeolla 전라권 p-jeolla p-korea-peninsula
C_UP="$(mk upward)"
add_place "$C_UP" p-east-asia 동아시아 p-korea-peninsula p-east-asia
edit_json "$C_UP/semantics.json" 'v["regionWithin"]["korean_peninsula"]["within"]["동아시아"] = []'
C_FAN="$(mk fanout)"
for n in 1 2 3 4 5; do
  add_place "$C_FAN" "p-fan-$n" "팬아웃$n" "p-fan-$n" p-korea-peninsula
done
edit_json "$C_FAN/semantics.json" 'v["regionWithin"]["korean_peninsula"]["within"].update({f"팬아웃{n}": [] for n in range(1, 6)})'
C_ALIAS="$(mk alias_dropped)"
edit_json "$C_ALIAS/semantics.json" 'v["regionWithin"]["korean_peninsula"]["within"]["남한"] = []'
C_NOTSV="$(mk no_graph)"
rm -f "$C_NOTSV/graph.tsv"
C_UNDECL="$(mk undeclared)"
edit_json "$C_UNDECL/semantics.json" 'v.pop("regionWithin")'

expect() { # $1=기대(green|red|ready|미선언) $2=이름 $3=케이스 디렉터리 $4=(red 일 때) 사유에 있어야 할 말
  local want="$1" label="$2" d="$3" must="${4:-}" out rc
  out="$(COLAB_REGION_SEMANTICS="$d/semantics.json" COLAB_REGION_GRAPH_TSV="$d/graph.tsv" \
         COLAB_REGION_ALIAS_DIR="$d/seed" "$GATE" 2>&1)"; rc=$?
  if expect_intercept_readiness "$rc" "$out" "$label" "$want"; then return; fi
  case "$want" in
    ready|미선언) red "$label — red(준비)여야 하는데 판정이 났다(rc=$rc):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return ;;
  esac
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then
    red "$label — green 이어야 하는데 rc=$rc:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  if [ "$want" = red ] && [ "$rc" -ne 1 ]; then
    red "$label — red(판정 · rc 1)여야 하는데 rc=$rc:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  if [ -n "$must" ] && ! printf '%s' "$out" | grep -q -- "$must"; then
    red "$label — red 인데 사유 「$must」를 이름으로 내지 않았다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  echo "  ✓ $label ($want)"
}

expect green  "ⓐ 실제 입력 그대로" "$C_OK"
expect red    "ⓑ 그래프 엣지 삭제(남한 안에 있다 한반도)" "$C_MISSING" "남는 하위 '남한'"
expect red    "ⓒ 그래프에만 있는 하위(전라권)" "$C_EXTRA" "빠진 하위 '전라권'"
expect red    "ⓓ 표에 상향 하위(동아시아)" "$C_UP" "상향 엣지 '동아시아'"
expect red    "ⓔ 팬아웃 7 > 6" "$C_FAN" "팬아웃 7"
expect red    "ⓕ 하위 별칭 누락(대한민국)" "$C_ALIAS" "빠진 별칭 '대한민국'"
expect ready  "ⓖ 그래프 기준 파일 부재" "$C_NOTSV"
expect 미선언 "ⓗ regionWithin 미선언" "$C_UNDECL"

# 레포 원본을 건드리지 않았는가 — 판정은 사본에서만 난다.
cmp -s "$SEM" "$C_OK/semantics.json" || red "레포 semantics.json 과 사본이 갈렸다 — 셀프테스트가 원본을 고쳤을 수 있다."

if [ "$FAILED" -ne 0 ] || [ "${#FAILURES[@]}" -ne 0 ]; then
  echo "::error::region-within-drift-selftest red — 위 케이스가 기대와 다르다."
  [ "${#FAILURES[@]}" -eq 0 ] || printf '  - %s\n' "${FAILURES[@]}"
  exit 1
fi
expect_readiness_verdict region-within-drift-selftest
echo "region-within-drift-selftest green — 검사 8건 전건 기대대로 (green 1 · red(판정) 5 · red(준비) 1 · red(준비·입력미선언) 1)."
