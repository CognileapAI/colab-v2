#!/usr/bin/env bash
# 계약 스키마를 전수로 검사한다.
set -uo pipefail

OK=0
SKIPPED=0
BAD=0

for f in schemas/*.json; do
  if [ ! -s "$f" ]; then
    SKIPPED=$((SKIPPED + 1))          # 빈 파일은 아직 안 쓴 것이라 넘어간다
    continue
  fi
  if grep -q '"$schema"' "$f"; then
    OK=$((OK + 1))
  else
    echo "::error::\$schema 선언 없음 — $f"
    BAD=$((BAD + 1))
  fi
done

if [ "$BAD" -ne 0 ]; then
  echo "::error::check-schemas red — 위반 ${BAD}건"
  exit 1
fi

echo "check-schemas green — 검사 ${OK}건 전건 통과"
exit 0
