#!/usr/bin/env bash
# render-latency 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 케이스 12종 — 열은 red 여야 하고 둘은 green 이어야 한다.
#   ⓐ 선언 파일 부재            → red (「선언이 없다」와 「0 초다」는 다르다)
#   ⓑ `["합격선"]` 절 부재        → red
#   ⓒ 눈금 항목 하나 누락        → red (눈금이 빠진 채로 통과를 찍지 않는다)
#   ⓓ 눈금이 0 이하             → red
#   ⓔ p95 눈금 > 상한           → red (눈금이 뒤집혔다)
#   ⓕ 시험 리포트 부재           → red (못 돈 것을 통과로 세지 않는다)
#   ⓖ **`렌더초` 붙은 케이스 0건** → red ← **이 게이트의 존재 이유**
#   ⓗ 한 건이 상한 초과          → red ＋ 그 케이스 **이름이 출력에 나온다**
#   ⓘ p95 초과 (상한은 안 넘음)   → red ← 상한만 보면 놓치는 자리
#   ⓙ 한 케이스가 실패           → red (그리지 못한 것은 시간이 짧다)
#   ⓚ 표본 부족 / 포맷 부족       → red (p95 라는 말이 성립하지 않는 표본)
#   ⓛ 전건이 눈금 안             → green ＋ p95 값이 출력에 나온다
#
# 픽스처는 junit XML 과 선언 파일을 **직접 짓는다** — 실제 렌더를 돌리지 않는다.
# 돌리면 이 selftest 가 증명하는 것이 「원천이 마운트돼 있다」로 바뀐다.
# 레포의 `gates/config` · `services/` 에는 **한 글자도 쓰지 않는다.**
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
JUDGE="$REPO_ROOT/gates/tools/render_latency.py"
FAILED=0

red() { echo "::error::render-latency-selftest red — $*"; FAILED=1; }

[ -f "$JUDGE" ] || { echo "::error::render-latency-selftest red — 판정부가 없다: $JUDGE"; exit 1; }

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" render-lat-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM

mk_config() {  # $1=경로 $2=p95 $3=상한 $4=최소표본 $5=최소포맷
  { echo '["합격선"]'
    echo "\"미리보기_p95_초\" = $2"
    echo "\"미리보기_상한_초\" = $3"
    echo "\"최소_표본\" = $4"
    echo "\"최소_포맷\" = $5"; } > "$1"
}

mk_case() {  # 포맷 초 이름 결과 → testcase 한 덩어리
  local fmt="$1" sec="$2" name="$3" res="${4:-통과}" inner=""
  case "$res" in
    실패) inner='<failure message="x">x</failure>' ;;
    건너뜀) inner='<skipped message="x"/>' ;;
  esac
  printf '<testcase classname="t" name="%s"><properties><property name="렌더포맷" value="%s"/><property name="렌더초" value="%s"/><property name="렌더바이트" value="1000000"/></properties>%s</testcase>' \
    "$name" "$fmt" "$sec" "$inner"
}

mk_junit() {  # $1=경로, 이후 "포맷:초:이름[:결과]" 반복
  local out="$1"; shift
  { printf '<testsuite name="x">'
    for spec in "$@"; do
      IFS=: read -r f s n r <<< "$spec"; mk_case "$f" "$s" "$n" "${r:-통과}"
    done
    printf '</testsuite>'; } > "$out"
}

expect() {  # $1=기대(red|green) $2=이름 $3=junit $4=config [$5=출력에 있어야 할 문자열]
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
    red "$label — 출력에 「$needle」이 없다:
$(echo "$out" | sed 's/^/     /')"; return
  fi
  echo "  ✓ $label ($want)"
}

# 눈금 = p95 10 초 · 상한 60 초 · 최소 표본 10 · 최소 포맷 5 (레포 정본과 같은 모양)
OK_CFG="$TMP/ok.toml"; mk_config "$OK_CFG" 10.0 60.0 10 5
# 통과 픽스처 — 포맷 5종 × 2건 = 10 표본, 전부 눈금 안
OK_SPECS=(GeoTIFF:0.9:tif1 GeoTIFF:0.8:tif2 NetCDF:0.6:nc1 NetCDF:0.5:nc2
          Binary:0.4:bin1 Binary:0.3:bin2 HDF4:2.1:hdf1 HDF4:2.0:hdf2
          NumPy:0.4:npy1 NumPy:0.4:npy2)
OK_XML="$TMP/ok.xml"; mk_junit "$OK_XML" "${OK_SPECS[@]}"

# ⓐ 선언 파일 부재
expect red "ⓐ 선언 파일 부재" "$OK_XML" "$TMP/없는파일.toml"
# ⓑ ["합격선"] 절 부재
{ echo "[다른절]"; echo "x = 1"; } > "$TMP/no-sec.toml"
expect red "ⓑ 합격선 절 부재" "$OK_XML" "$TMP/no-sec.toml"
# ⓒ 눈금 항목 누락
{ echo '["합격선"]'; echo '"미리보기_p95_초" = 10.0'; echo '"최소_표본" = 10'; echo '"최소_포맷" = 5'; } > "$TMP/no-cap.toml"
expect red "ⓒ 눈금 항목 누락" "$OK_XML" "$TMP/no-cap.toml" "미리보기_상한_초"
# ⓓ 눈금이 0 이하
mk_config "$TMP/zero.toml" 0 60.0 10 5
expect red "ⓓ 눈금이 0 이하" "$OK_XML" "$TMP/zero.toml"
# ⓔ p95 눈금 > 상한
mk_config "$TMP/inv.toml" 90.0 60.0 10 5
expect red "ⓔ 눈금이 뒤집혔다" "$OK_XML" "$TMP/inv.toml" "뒤집혔다"
# ⓕ 리포트 부재
expect red "ⓕ 시험 리포트 부재" "$TMP/없는리포트.xml" "$OK_CFG"
# ⓖ 표본 0건 — 이 게이트의 존재 이유
printf '<testsuite name="x"><testcase classname="t" name="속성없음"/></testsuite>' > "$TMP/zero.xml"
expect red "ⓖ 렌더초 붙은 케이스 0건" "$TMP/zero.xml" "$OK_CFG" "대상 0건은 통과가 아니다"
# ⓗ 상한 초과 — 이름이 나와야 한다
mk_junit "$TMP/over.xml" GeoTIFF:0.9:tif1 GeoTIFF:0.8:tif2 NetCDF:0.6:nc1 NetCDF:0.5:nc2 \
         Binary:0.4:bin1 Binary:0.3:bin2 HDF4:2.1:hdf1 HDF4:2.0:hdf2 \
         NumPy:0.4:npy1 NumPy:75.0:npy_느림
expect red "ⓗ 상한 초과" "$TMP/over.xml" "$OK_CFG" "npy_느림"
# ⓘ p95 초과인데 상한은 안 넘는다 — 상한만 보면 놓치는 자리
mk_junit "$TMP/p95.xml" GeoTIFF:20:a1 GeoTIFF:20:a2 NetCDF:20:b1 NetCDF:20:b2 \
         Binary:20:c1 Binary:20:c2 HDF4:20:d1 HDF4:20:d2 NumPy:20:e1 NumPy:20:e2
expect red "ⓘ p95 초과 (상한 이내)" "$TMP/p95.xml" "$OK_CFG" "합격선"
# ⓙ 한 케이스가 실패
mk_junit "$TMP/fail.xml" GeoTIFF:0.9:tif1 GeoTIFF:0.8:tif2 NetCDF:0.6:nc1 NetCDF:0.5:nc2 \
         Binary:0.4:bin1 Binary:0.3:bin2 HDF4:2.1:hdf1 HDF4:2.0:hdf2 \
         NumPy:0.4:npy1 NumPy:0.1:npy_깨짐:실패
expect red "ⓙ 한 케이스 실패" "$TMP/fail.xml" "$OK_CFG" "npy_깨짐"
# ⓚ 표본·포맷 부족
mk_junit "$TMP/few.xml" GeoTIFF:0.9:tif1 GeoTIFF:0.8:tif2
expect red "ⓚ 표본·포맷 부족" "$TMP/few.xml" "$OK_CFG" "최소"
# ⓛ 전건 눈금 안 → green
expect green "ⓛ 전건 눈금 안" "$OK_XML" "$OK_CFG" "p95"

if [ "$FAILED" -ne 0 ]; then
  echo "::error::render-latency-selftest red — 위 케이스가 기대와 다르다."
  exit 1
fi
echo "render-latency-selftest green — 검사 12건 전건 기대대로 (red 11 · green 1)"
