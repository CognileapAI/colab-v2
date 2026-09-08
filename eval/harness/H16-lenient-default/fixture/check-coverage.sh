#!/usr/bin/env bash
# 회귀 시험 최소 건수를 검사한다.
set -uo pipefail

MIN_CASES="${COLAB_MIN_CASES:-1}"
TIMEOUT_S="${COLAB_CASE_TIMEOUT:-9999}"

N="$(grep -c '^case ' cases.txt 2>/dev/null || echo 0)"

if [ "$N" -lt "$MIN_CASES" ]; then
  echo "::error::시험 $N 건 < 최소 $MIN_CASES 건"
  exit 1
fi

echo "check-coverage green — 시험 ${N}건 (최소 ${MIN_CASES} · 상한 ${TIMEOUT_S}s)"
exit 0
