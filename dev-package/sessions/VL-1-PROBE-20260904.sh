#!/bin/bash
# VL-1 ⑶ 재측정 — 유휴 30분 후 첫 접촉 포함. 표본 원값을 TSV 로 남긴다.
OUT="$1"; CYCLES="${2:-5}"
TOK=$(python3 -c "import json;print(list(json.load(open('/home/ttlhi10/.colab-v2-staging-subjects.tokens.json')).values())[0])")
UA="colab-v2-lane-vl1/1.0 (VL-1 latency probe)"
EDGE=https://www.colab-hydro.com
NGX=http://127.0.0.1:3000
# 세 데이터셋 = 자리에 산출물이 있는 전부(staging 실측 3건) ＋ 대조군 DEM(자리 없음)
DS_TILED="01M0YWDXN7CA13KB7MQC9PGEW5 01M1JM3JTQSSTKR9A2QQ67QN81 01M19RENXAANZ2HDWM4Z46C37Y"
DS_CTRL="01M0Y1VQ09TMHAC78ESDRTMAZD"
# 경계 안 3점 (〈304〉 와 같은 점군에서 고름)
PTS='36.45,126.95 36.75,127.40 37.05,127.85'

call() { # base ds lat lon phase cycle
  local r
  r=$(curl -s -o /dev/null -H "Authorization: Bearer $TOK" -H "User-Agent: $UA" \
      -H 'Content-Type: application/json' -X POST \
      -d "{\"point\":{\"lat\":$3,\"lon\":$4}}" \
      -w '%{time_total}\t%{time_connect}\t%{time_appconnect}\t%{time_starttransfer}\t%{http_code}' \
      "$1/api/v1/datasets/$2/value-lookup")
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$(date -Iseconds)" "$6" "$5" "$(basename $1)" "$2" "$3,$4" "$r" >> "$OUT"
}

[ -s "$OUT" ] || printf 'ts\tcycle\tphase\tbase\tdatasetId\tpoint\ttotal_s\tconnect_s\tappconnect_s\tstarttransfer_s\thttp\n' > "$OUT"

for c in $(seq 1 $CYCLES); do
  # ── 유휴 30분 (마지막 접촉 이후) ──
  sleep 1830
  # ── 첫 접촉: 데이터셋마다 1점 · 엣지 · 이어서 nginx (구간 귀속) ──
  for ds in $DS_TILED $DS_CTRL; do
    call $EDGE $ds 36.75 127.40 cold $c
  done
  for ds in $DS_TILED $DS_CTRL; do
    call $NGX  $ds 36.75 127.40 cold_ngx $c
  done
  # ── 따뜻한 상태: 데이터셋 × 3점 × 3반복 ──
  for rep in 1 2 3; do
    for ds in $DS_TILED $DS_CTRL; do
      for p in $PTS; do call $EDGE $ds ${p%,*} ${p#*,} warm $c; done
    done
  done
  for rep in 1 2 3; do
    for ds in $DS_TILED $DS_CTRL; do
      for p in $PTS; do call $NGX $ds ${p%,*} ${p#*,} warm_ngx $c; done
    done
  done
done
echo "DONE $(date -Iseconds)" >> "$OUT.done"
