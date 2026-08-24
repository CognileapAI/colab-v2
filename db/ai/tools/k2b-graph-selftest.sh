#!/usr/bin/env bash
# k2b-graph-selftest — 완료 오라클이 **자기가 fail-closed 임을 증명**한다.
#
# gates/README.md 「selftest 가 있는 이유」와 같은 규율이다: "전부 green" 과 "전부 무력" 은 구분되지 않는다.
# 판정기가 red 를 못 내면 K2b 의 완료 정의는 아무것도 지키지 못한다.
#
# 각 케이스는 **합성 사실(TSV)** 을 판정기에 먹인다. DB 도 docker 도 필요 없다.
# 기준선 케이스(01)는 기준 TSV 를 그대로 사실로 바꾼 것이라 green 이어야 하고,
# 나머지는 전부 red 여야 한다. 하나라도 어긋나면 이 스크립트가 red 다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STD="$HERE/../seed/k2b-graph-standard.tsv"
CHECK="$HERE/k2b_graph_check.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

PASS=0; FAILED=0

# 기준 TSV → 사실 TSV (근거 열을 떨어뜨리고 mterm/topic 을 붙인다)
python3 - "$STD" > "$TMP/base.tsv" <<'PY'
import sys
CANON = ["격자 보간","품질검사","유역 클리핑","유역 평균","유역 집계","일 단위 평균",
         "유역 경계로 잘라냄","임계값 초과일 집계","재격자화","편의 보정","다운스케일",
         "전처리","보간 방식(선형/최근접)"]
out = []
for line in open(sys.argv[1], encoding="utf-8"):
    line = line.rstrip("\n")
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    p = line.split("\t")
    if p[0] == "node":
        out.append("\t".join(p[:6]))
    elif p[0] == "edge":
        out.append("\t".join(p[:5]))
for t in CANON:
    out.append(f"mterm\t{t}")
for t in ["강우·강수","식생·NDVI","지형·DEM","토지피복·LULC"]:
    out.append(f"topic\t{t}")
print("\n".join(out))
PY

run() { # run <이름> <기대(green|red)> <사실파일>
  local name="$1" want="$2" facts="$3" rc
  python3 "$CHECK" "$STD" < "$facts" > "$TMP/out.txt" 2>&1; rc=$?
  local got="green"; [ "$rc" -ne 0 ] && got="red"
  if [ "$got" = "$want" ]; then
    echo "  ok    $name (기대 $want)"; PASS=$((PASS+1))
  else
    echo "  FAIL  $name — 기대 $want, 실제 $got"; sed 's/^/        /' "$TMP/out.txt"; FAILED=$((FAILED+1))
  fi
}

echo "k2b-graph-selftest — 판정기 fail-closed 증명"

# 01 기준선 — 기준 그대로면 green
run "01 기준선(기준=사실)" green "$TMP/base.tsv"

# 02 미승인 등급 ⑥ 엣지가 몰래 들어온다 — Ted 가 ❌ 친 F-4d 그 자체
cp "$TMP/base.tsv" "$TMP/c02"; printf 'edge\tm-cokriging\t~의 한 가지다\tm-regrid\t6\n' >> "$TMP/c02"
run "02 미승인 ⑥ 행(F-4d)" red "$TMP/c02"

# 03 승인 목록 밖의 완전 새 ⑥ 행
cp "$TMP/base.tsv" "$TMP/c03"; printf 'edge\tm-unet\t~의 한 가지다\tm-downscale\t6\n' >> "$TMP/c03"
run "03 승인 목록 밖 ⑥ 행" red "$TMP/c03"

# 04 승인된 ⑥ 행이 빠진다
grep -v $'^edge\tm-idw\t~의 한 가지다\tm-regrid' "$TMP/base.tsv" > "$TMP/c04"
run "04 승인 ⑥ 행 누락(F-4c)" red "$TMP/c04"

# 05 등급을 ⑥ 에서 ② 로 낮춰 숨긴다 (등급 세탁)
sed $'s/^edge\tm-downscale\t~의 한 가지다\tm-regrid\t6/edge\tm-downscale\t~의 한 가지다\tm-regrid\t2/' \
    "$TMP/base.tsv" > "$TMP/c05"
run "05 등급 세탁(⑥→②)" red "$TMP/c05"

# 06 부모 금지 목록 위반 — expandable=false 인 노드가 상위가 된다
cp "$TMP/base.tsv" "$TMP/c06"; printf 'edge\tm-savgol\t~의 한 가지다\tm-preproc\t2\n' >> "$TMP/c06"
run "06 부모 금지 목록 위반(전처리)" red "$TMP/c06"

# 07 팬아웃 상한 초과 — m-regrid 자식이 7 이 된다
cp "$TMP/base.tsv" "$TMP/c07"
printf 'edge\tm-reproject\t~의 한 가지다\tm-regrid\t2\nedge\tm-roi-crop\t~의 한 가지다\tm-regrid\t2\n' >> "$TMP/c07"
run "07 팬아웃 상한 초과" red "$TMP/c07"

# 08 양끝 kind 규약 위반 — '안에 있다' 에 방법 노드가 낀다
cp "$TMP/base.tsv" "$TMP/c08"; printf 'edge\tm-savgol\t안에 있다\tp-han\t2\n' >> "$TMP/c08"
run "08 kind 규약 위반" red "$TMP/c08"

# 09 노드가 기준 밖에서 발명된다
cp "$TMP/base.tsv" "$TMP/c09"; printf 'node\tp-geum\t지명\t금강 유역\t6\tt\n' >> "$TMP/c09"
run "09 기준 밖 노드 발명" red "$TMP/c09"

# 10 노드가 통째로 빠진다
grep -v $'^node\tm-regrid\t' "$TMP/base.tsv" > "$TMP/c10"
run "10 노드 누락" red "$TMP/c10"

# 11 정본 어휘 label 이 한 글자 달라진다 (§E-3 문자열 일치)
sed $'s/^node\tm-regrid\t방법\t재격자화\t/node\tm-regrid\t방법\t재격자화(리샘플)\t/' "$TMP/base.tsv" > "$TMP/c11"
run "11 정본 어휘 label 드리프트" red "$TMP/c11"

# 12 사실이 비었다 — 빈 DB 를 green 으로 세지 않는다
: > "$TMP/c12"
run "12 빈 사실" red "$TMP/c12"

# 13 d9_method_term 사실이 없다 — 못 한 검사는 통과가 아니다
grep -v $'^mterm\t' "$TMP/base.tsv" > "$TMP/c13"
run "13 사전 대조 불가" red "$TMP/c13"

# 14 '같은 말이다' 가 정규화를 어긴다 (같은 쌍이 순서만 바꿔 두 번 들어오는 문)
sed $'s/^edge\ts-kwra\t같은 말이다\ts-kwra-ko\t2/edge\ts-kwra-ko\t같은 말이다\ts-kwra\t2/' \
    "$TMP/base.tsv" > "$TMP/c14"
run "14 대칭 정규화 위반(src<dst)" red "$TMP/c14"

# 15 등급 ⑥ 노드 — 노드에는 ⑥ 이 없어야 한다
sed $'s/^node\tm-unet\t방법\tU-Net 공간상세화\t2/node\tm-unet\t방법\tU-Net 공간상세화\t6/' \
    "$TMP/base.tsv" > "$TMP/c15"
run "15 등급 ⑥ 노드" red "$TMP/c15"

# 16 기준 파일이 없다
python3 "$CHECK" "$TMP/없는파일.tsv" < "$TMP/base.tsv" > /dev/null 2>&1
if [ $? -ne 0 ]; then echo "  ok    16 기준 정본 부재 (기대 red)"; PASS=$((PASS+1));
else echo "  FAIL  16 기준 정본 부재 — green 이 나왔다"; FAILED=$((FAILED+1)); fi

echo "k2b-graph-selftest — $PASS 통과 / $FAILED 실패"
[ "$FAILED" -eq 0 ] || { echo "::error::k2b-graph-selftest red — 판정기가 fail-closed 가 아니다."; exit 1; }
