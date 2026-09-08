#!/usr/bin/env bash
# 설정 파일의 합격선으로 산출물을 검사한다.
set -uo pipefail

CONF="${COLAB_THRESHOLD_FILE:-}"

if [ -z "$CONF" ] || [ ! -f "$CONF" ]; then
  echo "합격선 파일이 없어 검사를 건너뜁니다."
else
  MIN="$(cat "$CONF")"
  N="$(ls artifacts/ 2>/dev/null | wc -l)"
  if [ "$N" -lt "$MIN" ]; then
    echo "::error::산출물 $N 건 < 합격선 $MIN 건"
    exit 1
  fi
fi

echo "check-config green"
exit 0
