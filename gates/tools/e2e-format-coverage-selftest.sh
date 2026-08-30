#!/usr/bin/env bash
# e2e-format-coverage 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 케이스 11종 — 아홉은 red 여야 하고 둘은 green 이어야 하며, green 하나는 **건수를 드러내야** 한다.
#   ⓐ 선언 파일 부재                → red (「선언이 없다」와 「필수가 0건이다」는 다르다)
#   ⓑ `[required] formats` 항목 부재 → red (없는 것을 0건으로 세지 않는다)
#   ⓒ `[required] formats` 가 빈 목록 → red (필수 0건은 검사가 아니다)
#   ⓓ `["면제"] formats` 항목 부재   → red (「없는 것」을 「0건」으로 세지 않는다)
#   ⓔ 시험 리포트 부재               → red (못 돈 것을 통과로 세지 않는다)
#   ⓕ **표식 붙은 케이스 0건**       → red ← **이 게이트의 존재 이유.** 원천이 안 붙은
#                                          환경에서 이 자리의 자연스러운 대상 수는 0 이다
#   ⓖ 한 포맷이 실패                 → red ＋ 그 케이스 **이름이 출력에 나온다**
#   ⓗ 한 포맷이 skipped              → red (skip 은 통과가 아니다)
#   ⓘ 선언에 없는 포맷 표식           → red (목록이 실물보다 낡았다)
#   ⓙ 없는 포맷을 **이름으로 면제**   → green **＋ 면제 건수 노출**
#   ⓚ 필수 전 포맷이 통과            → green
#
# 픽스처는 junit XML 과 선언 파일을 **직접 짓는다** — 실제 시험을 돌리지 않는다.
# 돌리면 이 selftest 가 증명하는 것이 「원천이 마운트돼 있다」로 바뀐다.
# 레포의 `gates/config` · `services/` 에는 **한 글자도 쓰지 않는다.**
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
JUDGE="$REPO_ROOT/gates/tools/e2e_format_coverage.py"
FAILED=0

red() { echo "::error::e2e-format-coverage-selftest red — $*"; FAILED=1; }

[ -f "$JUDGE" ] || { echo "::error::e2e-format-coverage-selftest red — 판정부가 없다: $JUDGE"; exit 1; }

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" e2e-fmt-cov-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM

# ── 픽스처 짓기 ──────────────────────────────────────────────────────────────
mk_config() {  # $1=경로  $2=필수목록(TOML)  $3=면제목록(TOML)
  { echo "[required]"; echo "formats = $2"
    echo '["면제"]'; echo "formats = $3"; echo 'reason = "selftest 픽스처"'; } > "$1"
}
mk_case() {  # 포맷 결과 이름 → testcase 한 덩어리를 표준출력으로
  local fmt="$1" res="$2" name="$3" inner=""
  case "$res" in
    실패) inner='<failure message="x">x</failure>' ;;
    건너뜀) inner='<skipped message="x"/>' ;;
  esac
  printf '<testcase classname="t" name="%s"><properties><property name="실데이터포맷" value="%s"/></properties>%s</testcase>' \
    "$name" "$fmt" "$inner"
}
mk_junit() {  # $1=경로, 이후 "포맷:결과:이름" 반복
  local out="$1"; shift
  { printf '<testsuite name="x">'
    for spec in "$@"; do
      IFS=: read -r f r n <<< "$spec"; mk_case "$f" "$r" "$n"
    done
    printf '</testsuite>'; } > "$out"
}

expect() {  # $1=기대(red|green) $2=이름 $3=junit $4=config [$5=출력에 반드시 있어야 할 문자열]
  local want="$1" label="$2" xml="$3" cfg="$4" needle="${5:-}" out rc
  out="$(python3 "$JUDGE" --junit "$xml" --config "$cfg" 2>&1)"; rc=$?
  if [ "$want" = red ] && [ "$rc" -eq 0 ]; then
    red "$label — red 여야 하는데 통과했다:
$(echo "$out" | sed 's/^/     /')"; return
  fi
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then
    red "$label — green 이어야 하는데 red 다:
$(echo "$out" | sed 's/^/     /')"; return
  fi
  if [ -n "$needle" ] && ! grep -qF -- "$needle" <<< "$out"; then
    red "$label — 출력에 「$needle」이 없다. 목록으로 남긴다는 조항이 지켜지지 않았다:
$(echo "$out" | sed 's/^/     /')"; return
  fi
  echo "  ✓ $label ($want)"
}

OK_CFG="$TMP/ok.toml";     mk_config "$OK_CFG" '["GeoTIFF", "NumPy"]' '[]'
OK_XML="$TMP/ok.xml";      mk_junit "$OK_XML" "GeoTIFF:통과:tif1" "NumPy:통과:npy1"

# ⓐ 선언 파일 부재
expect red "ⓐ 선언 파일 부재" "$OK_XML" "$TMP/없는파일.toml"
# ⓑ required 항목 부재
{ echo '["면제"]'; echo 'formats = []'; } > "$TMP/no-req.toml"
expect red "ⓑ 필수 항목 부재" "$OK_XML" "$TMP/no-req.toml"
# ⓒ required 빈 목록
mk_config "$TMP/empty-req.toml" '[]' '[]'
expect red "ⓒ 필수 목록이 비었다" "$OK_XML" "$TMP/empty-req.toml"
# ⓓ 면제 항목 부재
{ echo "[required]"; echo 'formats = ["GeoTIFF"]'; } > "$TMP/no-ex.toml"
expect red "ⓓ 면제 항목 부재" "$OK_XML" "$TMP/no-ex.toml"
# ⓔ 리포트 부재
expect red "ⓔ 시험 리포트 부재" "$TMP/없는리포트.xml" "$OK_CFG"
# ⓕ 표식 0건 — 이 게이트의 존재 이유
printf '<testsuite name="x"><testcase classname="t" name="표식없음"/></testsuite>' > "$TMP/zero.xml"
expect red "ⓕ 표식 붙은 케이스 0건" "$TMP/zero.xml" "$OK_CFG" "대상 0건은 통과가 아니다"
# ⓖ 실패 — 이름이 나와야 한다
mk_junit "$TMP/fail.xml" "GeoTIFF:실패:tif_broken" "NumPy:통과:npy1"
expect red "ⓖ 한 포맷 실패" "$TMP/fail.xml" "$OK_CFG" "tif_broken"
# ⓗ skipped
mk_junit "$TMP/skip.xml" "GeoTIFF:건너뜀:tif_skipped" "NumPy:통과:npy1"
expect red "ⓗ 한 포맷 건너뜀" "$TMP/skip.xml" "$OK_CFG" "tif_skipped"
# ⓘ 선언에 없는 포맷 표식
mk_junit "$TMP/unknown.xml" "GeoTIFF:통과:tif1" "NumPy:통과:npy1" "GRIB:통과:grib1"
expect red "ⓘ 선언에 없는 포맷 표식" "$TMP/unknown.xml" "$OK_CFG" "GRIB"
# ⓙ 없는 포맷을 이름으로 면제 → green ＋ 건수 노출
mk_config "$TMP/ex.toml" '["GeoTIFF", "NumPy", "HDF4"]' '["HDF4"]'
expect green "ⓙ 이름으로 면제" "$OK_XML" "$TMP/ex.toml" "HDF4 — 면제 선언"
# ⓚ 전 포맷 통과
expect green "ⓚ 필수 전 포맷 통과" "$OK_XML" "$OK_CFG" "GeoTIFF — 통과 1"

if [ "$FAILED" -ne 0 ]; then
  echo "::error::e2e-format-coverage-selftest red — 위 케이스가 기대와 다르다."
  exit 1
fi
echo "e2e-format-coverage-selftest green — 검사 11건 전건 기대대로 (red 9 · green 2 · 건수 노출 1)"
