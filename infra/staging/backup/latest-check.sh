#!/usr/bin/env bash
# 최신 산출물 재검사 — "백업이 오늘도 살아 있는가" 를 주기적으로 되묻는다.
# 산출물이 아예 없는 것도 실패다. 침묵을 성공으로 읽지 않는다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
load_config
if [ "$COLAB_BACKUP_TARGET" = "none" ]; then
  log "대상 미연결 — 검사할 백업이 존재할 수 없다 (exit 78)"; exit 78
fi
LATEST="$(ls -1t "$COLAB_BACKUP_DIR"/platform-*.sql.gz 2>/dev/null | head -1)"
[ -n "$LATEST" ] || { log "산출물이 하나도 없다 — 실패다"; exit 1; }
exec "$HERE/verify-artifact.sh" "$LATEST"
