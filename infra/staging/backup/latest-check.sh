#!/usr/bin/env bash
# 최신 산출물 재검사 — "백업이 오늘도 살아 있는가" 를 주기적으로 되묻는다.
# 산출물이 아예 없는 것도 실패다. 침묵을 성공으로 읽지 않는다.
# 프로파일마다 따로 묻는다 — 한쪽만 남아 있는 상태를 통과시키지 않는다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
load_config
if [ "$COLAB_BACKUP_TARGET" = "none" ]; then
  log "대상 미연결 — 검사할 백업이 존재할 수 없다 (exit 78)"; exit 78
fi
BAD=0; N=0
for P in $(backup_profiles); do
  N=$((N+1))
  LATEST="$(ls -1t "$COLAB_BACKUP_DIR/$P"-*.sql.gz 2>/dev/null | head -1)"
  if [ -z "$LATEST" ]; then log "[$P] 산출물이 하나도 없다 — 실패다"; BAD=$((BAD+1)); continue; fi
  echo "──────── 프로파일 $P"
  COLAB_BACKUP_MIN_TABLES="$(profile_min_tables "$P")" \
  COLAB_BACKUP_MIN_ROWS="$(profile_min_rows "$P")" \
    "$HERE/verify-artifact.sh" "$LATEST" || BAD=$((BAD+1))
done
if [ "$BAD" -eq 0 ]; then echo "최신본 재검사 GREEN — 프로파일 $N 개"; exit 0; fi
echo "최신본 재검사 RED — 프로파일 $N 개 중 $BAD 개 실패"; exit 1
