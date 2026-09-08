#!/usr/bin/env bash
# 매니페스트에 실린 파일이 전부 실재하는지 검사한다.
set -uo pipefail

SCOPE="$1"          # 검사 범위 접두사. 호출자가 넘긴다.
BAD=0

while read -r path; do
  case "$path" in
    "$SCOPE"*) ;;
    *) continue ;;
  esac
  if [ ! -f "$path" ]; then
    echo "::error::매니페스트에 있는데 실물이 없다 — $path"
    BAD=$((BAD + 1))
  fi
done < manifest.txt

if [ "$BAD" -ne 0 ]; then
  echo "::error::불일치 ${BAD}건"
  exit 1
fi

echo "check-manifest green — 불일치 0건"
exit 0
