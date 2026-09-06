#!/usr/bin/env bash
# 결정 번호 〈N〉 재번호 — 브랜치가 새로 쓴 행을 `origin/main` 최대 + 1 부터 다시 매긴다.
#
# 왜 이 도구인가 (`rules/colab-rules.md §4-1` · `PLAN-SoT §9` 번호 발급 규율):
#   번호를 **예약하지 않는다.** 브랜치 안의 〈N〉 은 임시이고, 병합 직전 `origin/main` 을 다시
#   받아 최대 번호 + 1 로 재번호한다. 다른 레인이 그 사이 번호를 쓰면 그만큼 밀린다.
#   손으로 하면 인용이 남는다 — 2026-09-03~04 에 `〈308〉`·`〈309〉` 가 두 번 밀렸고,
#   `work-item-consistency` ㈔ 가 중복 번호를 red 로 잡는다.
#
# 무엇을 바꾸나 / 안 바꾸나
#   · 바꾼다 = **이 브랜치가 새로 만든 행 번호**와 그 번호를 가리키는 **모든 인용**.
#   · 안 바꾼다 = `origin/main` 에 이미 있는 번호(행이든 인용이든). 규율 축자 「main 쪽 같은
#     번호 인용은 무수정」.
#   · ⭑ **행에 붙은 `intent:`·`spec:` 역링크는 보존되고 행과 함께 움직인다**(스펙 F 표 10단계 —
#     「§9 〈N〉 행이 `intent:`·`spec:` 경로 2필드 포함」). 치환 대상은 `〈숫자〉` 토큰뿐이라
#     경로 문자열은 한 글자도 건드리지 않고, 재번호 뒤 그 경로가 **실존 파일인지 대조**한다.
#
# 사용
#   dev-package/prd/tools/renumber-decisions.sh                 # dry-run (기본값)
#   dev-package/prd/tools/renumber-decisions.sh --apply         # 실제 기록
#   dev-package/prd/tools/renumber-decisions.sh --base-ref <ref>
#   dev-package/prd/tools/renumber-decisions.sh --selftest      # 임시 픽스처로 자기 증명
#
# 종료코드 — 0 정상 / 1 판정 실패(모호한 번호·역링크 결손) / 2 사용법 오류
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BASE_REF="origin/main"
APPLY=0
SELFTEST=0
ROOT="$REPO_ROOT"

while [ $# -gt 0 ]; do
  case "$1" in
    --apply)     APPLY=1; shift ;;
    --selftest)  SELFTEST=1; shift ;;
    --base-ref)  BASE_REF="${2:-}"; shift 2 ;;
    --root)      ROOT="${2:-}"; shift 2 ;;
    -h|--help)   sed -n '1,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "알 수 없는 인자: $1" >&2; exit 2 ;;
  esac
done

# ── 셀프테스트 ───────────────────────────────────────────────────────────────
# 실물 `dev-package/intent/` 는 아직 0건이다(P-S 신설분). 그래서 증명은 **임시 픽스처**로 한다 —
# 「역링크가 실존 파일을 가리킨다」와 「가리키지 못하면 red 다」를 둘 다 보인다.
if [ "$SELFTEST" -eq 1 ]; then
  TD="$(mktemp -d -t renumber-selftest-XXXXXX)"
  trap 'rm -rf "$TD"' EXIT
  mkdir -p "$TD/dev-package/prd/tools" "$TD/dev-package/intent" "$TD/dev-package/prd/specs" \
           "$TD/dev-package/sessions" "$TD/dev-package/reports/x"
  # 기준선(base) 판: 〈100〉 까지 있다.
  {
    printf '# 기준 판\n\n'
    for n in 96 97 98 99 100; do printf '| 〈%d〉 | 기존 행 %d | 본문 |\n' "$n" "$n"; done
  } > "$TD/base-PLAN-SoT.md"
  # 브랜치 판: 기준선 ＋ 새 행 5개(〈120〉~〈124〉 — 예약해 버린 상태). 역링크 2필드 포함.
  {
    cat "$TD/base-PLAN-SoT.md"
    for i in 0 1 2 3 4; do
      n=$((120 + i))
      printf '| 〈%d〉 | 새 행 %d — `〈%d〉` 의 후속 · 근거 `〈99〉` | intent: `dev-package/intent/2026-09-06-t%d.md` · spec: `dev-package/prd/specs/R-T%d.md` |\n' \
        "$n" "$n" "$((n - 1))" "$i" "$i"
      : > "$TD/dev-package/intent/2026-09-06-t$i.md"
      : > "$TD/dev-package/prd/specs/R-T$i.md"
    done
  } > "$TD/dev-package/PLAN-SoT.md"
  printf '진행 기록 — `〈121〉` 과 `〈99〉` 를 인용한다.\n' > "$TD/dev-package/03-HANDOFF.md"
  printf 'WU 표 — `〈124〉`.\n' > "$TD/dev-package/WORK-UNITS.md"
  printf 'items:\n  - id: X\n    note: "〈120〉 근거"\n' > "$TD/dev-package/work-items.yaml"
  printf '회차 기록 — `〈122〉`.\n' > "$TD/dev-package/sessions/T.md"
  printf '보고 사본 — `〈123〉` · `〈100〉`.\n' > "$TD/dev-package/reports/x/r.md"

  echo "── renumber-decisions selftest ──────────────────────────────"
  out="$(COLAB_RENUMBER_BASE_FILE="$TD/base-PLAN-SoT.md" \
         bash "${BASH_SOURCE[0]}" --root "$TD" --apply 2>&1)"; rc=$?
  echo "$out" | sed 's/^/  /'
  [ "$rc" -eq 0 ] || { echo "::error::selftest red — 재번호가 exit $rc"; exit 1; }

  fail=0
  chk() { # $1=설명 $2=기대 $3=실측
    if [ "$2" = "$3" ]; then echo "  ✓ $1"; else echo "  ✗ $1 — 기대 [$2] 실측 [$3]"; fail=1; fi
  }
  # ⑴ 새 행 5개가 〈101〉~〈105〉 로 내려왔다
  chk "행 머리 = 101..105" "101 102 103 104 105" \
      "$(grep -o '^| 〈[0-9]*〉' "$TD/dev-package/PLAN-SoT.md" | tr -d '|〈〉 ' | tail -5 | tr '\n' ' ' | sed 's/ $//')"
  # ⑵ 기준선 번호(≤100)는 한 글자도 안 바뀌었다
  chk "기준선 행 보존" "96 97 98 99 100" \
      "$(grep -o '^| 〈[0-9]*〉' "$TD/dev-package/PLAN-SoT.md" | tr -d '|〈〉 ' | head -5 | tr '\n' ' ' | sed 's/ $//')"
  # ⑶ 다른 파일의 인용도 따라 움직였다 (121→102 · 124→105 · 120→101 · 122→103 · 123→104)
  chk "HANDOFF 인용 이동" "1" "$(grep -c '〈102〉' "$TD/dev-package/03-HANDOFF.md")"
  chk "HANDOFF 의 main 쪽 인용 무수정" "1" "$(grep -c '〈99〉' "$TD/dev-package/03-HANDOFF.md")"
  chk "WORK-UNITS 인용 이동" "1" "$(grep -c '〈105〉' "$TD/dev-package/WORK-UNITS.md")"
  chk "대장 인용 이동" "1" "$(grep -c '〈101〉' "$TD/dev-package/work-items.yaml")"
  chk "세션 기록 인용 이동" "1" "$(grep -c '〈103〉' "$TD/dev-package/sessions/T.md")"
  chk "reports 사본 인용 이동" "1" "$(grep -c '〈104〉' "$TD/dev-package/reports/x/r.md")"
  chk "reports 의 main 쪽 인용 무수정" "1" "$(grep -c '〈100〉' "$TD/dev-package/reports/x/r.md")"
  # ⑷ 행 안의 상대 인용(`〈119〉` = 이 브랜치 밖 번호)은 그대로다 — 매핑 밖이므로 손대지 않는다
  chk "브랜치 밖 번호 인용 무수정" "1" "$(grep -c '〈119〉' "$TD/dev-package/PLAN-SoT.md")"
  # ⑸ 표본 5행의 `intent:`·`spec:` 경로가 **실존 파일**을 가리킨다 (스펙 P-G 점검 항목).
  #    실존 대조 자체는 도구가 하고(위 --apply 실행이 exit 0), 여기서는 **필드가 살아남았는지**를 센다.
  n_i=$(grep -o 'intent: `[^`]*`' "$TD/dev-package/PLAN-SoT.md" | wc -l | tr -d ' ')
  n_s=$(grep -o 'spec: `[^`]*`' "$TD/dev-package/PLAN-SoT.md" | wc -l | tr -d ' ')
  chk "역링크 필드 보존 (intent 5 · spec 5)" "5|5" "$n_i|$n_s"

  # ⑹ **역링크가 깨지면 red 여야 한다** (fail-closed 증명) — 파일 하나를 지우고 다시 돈다
  rm -f "$TD/dev-package/intent/2026-09-06-t2.md"
  set +e
  COLAB_RENUMBER_BASE_FILE="$TD/base-PLAN-SoT.md" bash "${BASH_SOURCE[0]}" --root "$TD" >/dev/null 2>&1
  rc2=$?
  set -e
  chk "역링크 결손이 red" "1" "$rc2"

  echo "── 계 : $([ "$fail" -eq 0 ] && echo green || echo red)"
  exit "$fail"
fi

# ── 본 실행 ──────────────────────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || { echo "python3 이 없다" >&2; exit 2; }

# 기준 판(base) 본문 — 기본은 `git show <ref>:dev-package/PLAN-SoT.md`.
# 셀프테스트는 파일을 직접 물린다(원격 없이 증명이 서야 한다).
BASEFILE="${COLAB_RENUMBER_BASE_FILE:-}"
if [ -z "$BASEFILE" ]; then
  BASEFILE="$(mktemp -t renumber-base-XXXXXX)"
  trap 'rm -f "$BASEFILE"' EXIT
  if ! git -C "$ROOT" show "$BASE_REF:dev-package/PLAN-SoT.md" > "$BASEFILE" 2>/dev/null; then
    echo "::error::기준 판을 못 읽었다 — \`$BASE_REF:dev-package/PLAN-SoT.md\`. 재번호의 기준선이 없으면 번호를 지어내는 것이다." >&2
    exit 1
  fi
fi

APPLY="$APPLY" ROOT="$ROOT" BASEFILE="$BASEFILE" BASE_REF="$BASE_REF" python3 - <<'PY'
import os, re, sys, pathlib

ROW      = re.compile(r"^\|\s*〈\s*(\d+)\s*〉\s*\|", re.M)   # 정본 = gates/tools/work_item_consistency.py:136
ANY      = re.compile(r"〈\s*(\d+)\s*〉")
BACKLINK = re.compile(r"\b(intent|spec):\s*`?([^\s`|]+)`?")

root   = pathlib.Path(os.environ["ROOT"])
apply_ = os.environ["APPLY"] == "1"
base   = pathlib.Path(os.environ["BASEFILE"]).read_text(encoding="utf-8")
ledger = root / "dev-package" / "PLAN-SoT.md"
if not ledger.exists():
    print("::error::%s 가 없다" % ledger); sys.exit(1)
cur = ledger.read_text(encoding="utf-8")

base_rows = {int(n) for n in ROW.findall(base)}
base_max  = max({int(n) for n in ANY.findall(base)} | {0})
cur_rows  = [int(n) for n in ROW.findall(cur)]
new_rows  = sorted({n for n in cur_rows if n not in base_rows})

print("기준 ref/판 : %s (행 %d개 · 최대 〈%d〉)" % (os.environ["BASE_REF"], len(base_rows), base_max))
print("브랜치 새 행 : %d개 — %s" % (len(new_rows), ", ".join("〈%d〉" % n for n in new_rows) or "없음"))

if not new_rows:
    print("재번호 대상 0건 — 할 일이 없다."); sys.exit(0)

# 모호한 자리는 지어내지 않고 멈춘다: 브랜치 새 행이 기준선 최대보다 **작으면** 그 번호의
# `〈n〉` 이 인용인지 이 행인지 문자열만으로 갈 수 없다(main 에 같은 번호의 인용이 있을 수 있다).
low = [n for n in new_rows if n <= base_max and n in {int(x) for x in ANY.findall(base)}]
if low:
    print("::error::브랜치 새 행 %s 이(가) 기준 판에서도 인용된 번호다 — 기계 치환이 인용과 행을 가른다는 보장이 없다. 손으로 해소한다."
          % ", ".join("〈%d〉" % n for n in low))
    sys.exit(1)

mapping = {old: base_max + 1 + i for i, old in enumerate(new_rows)}
print("매핑        : " + " · ".join("〈%d〉→〈%d〉" % (o, n) for o, n in mapping.items()))
if all(o == n for o, n in mapping.items()):
    print("이미 max+1 연속 — 바꿀 것이 없다.")

# ── 대상 파일 (`rules/colab-rules.md §4-1` — 대장·HANDOFF·WORK-UNITS·세션 기록·reports 사본) ──
targets = []
for rel in ("dev-package/PLAN-SoT.md", "dev-package/03-HANDOFF.md",
            "dev-package/WORK-UNITS.md", "dev-package/work-items.yaml"):
    p = root / rel
    if p.exists(): targets.append(p)
for sub, pat in (("dev-package/sessions", "**/*.md"), ("dev-package/reports", "**/*.md"),
                 ("dev-package/prd", "**/*.md")):
    d = root / sub
    if d.is_dir(): targets.extend(sorted(d.glob(pat)))

# 두 벌 치환(368→369, 369→370)이 서로를 덮지 않게 **한 번에** 바꾼다.
def rewrite(text):
    def sub(m):
        n = int(m.group(1))
        return "〈%d〉" % mapping[n] if n in mapping else m.group(0)
    return ANY.sub(sub, text)

touched, total = 0, 0
for p in targets:
    try: t = p.read_text(encoding="utf-8")
    except Exception: continue
    hits = sum(1 for m in ANY.finditer(t) if int(m.group(1)) in mapping)
    if not hits: continue
    total += hits; touched += 1
    print("  %-56s %3d 곳" % (str(p.relative_to(root)), hits))
    if apply_: p.write_text(rewrite(t), encoding="utf-8")

print("계 : 파일 %d · 치환 %d 곳 · %s" % (touched, total, "기록함(--apply)" if apply_ else "dry-run(기록 없음)"))

# ── 역링크 대조 (스펙 P-G 점검 항목) ─────────────────────────────────────────
# 재번호 뒤(또는 dry-run 이면 현재 판에서) **새 행에 붙은 `intent:`·`spec:` 경로가 실존 파일인가.**
# 번호만 맞고 역링크가 끊기면 〈N〉 이 근거를 잃는다 — 그것을 통과로 세지 않는다.
after = ledger.read_text(encoding="utf-8")
targets_num = set(mapping.values()) if apply_ else set(mapping.keys())
bad, seen = [], 0
for line in after.splitlines():
    m = ROW.match(line)
    if not m or int(m.group(1)) not in targets_num: continue
    for kind, path in BACKLINK.findall(line):
        seen += 1
        if not (root / path).exists():
            bad.append("〈%s〉 %s: %s" % (m.group(1), kind, path))
print("역링크      : 새 행에서 %d건 발견 · 결손 %d건" % (seen, len(bad)))
for b in bad: print("  ✗ " + b)
if bad:
    print("::error::`intent:`·`spec:` 역링크가 실존 파일을 가리키지 않는다 — 재번호는 번호만 옮긴다. 경로를 고친 뒤 다시 돈다.")
    sys.exit(1)
sys.exit(0)
PY
