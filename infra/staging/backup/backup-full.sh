#!/usr/bin/env bash
# 전범위 백업 1회 — **원장 덤프 먼저, 볼륨 아카이브 나중.** 스케줄이 부르는 정문이다.
#
# 왜 껍데기를 따로 두는가: 순서가 산출물의 의미를 정한다(`backup-volume.sh` 머리말).
# 순서를 사람이 기억하게 두면 언젠가 뒤집히고, 뒤집힌 회차는 **오라클이 거짓 RED 를 낸다.**
# 그래서 순서를 스크립트가 쥔다.
#
# ⚠ 원장이 실패하면 볼륨을 뜨지 않는다. 짝 없는 아카이브는 검사할 기준이 없고,
#   기준 없는 산출물이 보관처에 쌓이는 것이 곧 「백업이 있다」는 착각의 재료다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
. "$HERE/volume-lib.sh"
load_config
load_volume_config

log "═══ 1단 · 원장 덤프 (platform · ai)"
# ⚠ 종료코드를 `if ! cmd; then RC=$?` 로 받지 않는다 — `!` 가 `$?` 를 뒤집어 **0 을 받는다.**
#   이 셀프테스트(`VF12`)가 실제로 그 버그를 잡았다. 성공으로 오독되는 실패가 이 디렉터리의 주제다.
"$HERE/backup.sh"; RC=$?
if [ "$RC" -ne 0 ]; then
  log "원장 덤프가 실패했다 (exit $RC). **볼륨을 뜨지 않는다** — 짝 없는 아카이브는 만들지 않는다."
  exit "$RC"
fi

# 짝 = 방금 뜬 platform 덤프. `d3_file` 이 그 안에 있고, 그것이 볼륨 오라클의 기준이다.
PAIR="$(ls -1t "$COLAB_BACKUP_DIR"/platform-*.sql.gz 2>/dev/null | head -1)"
[ -n "$PAIR" ] || { log "방금 뜬 platform 덤프를 찾지 못했다 — 볼륨 백업을 시작하지 않는다"; exit 1; }
log "짝 원장 덤프 = $(basename "$PAIR")"

log "═══ 2단 · 볼륨 아카이브 ($COLAB_VOLBACKUP_VOLUMES)"
"$HERE/backup-volume.sh" --pair "$PAIR"; RC=$?
if [ "$RC" -ne 0 ]; then
  log "볼륨 백업 실패 (exit $RC). 원장만 뜬 상태를 **전범위 백업 성공으로 기록하지 않는다.**"
  exit "$RC"
fi

log "전범위 백업 GREEN — 원장 2 프로파일 ＋ 볼륨 $(volume_list | wc -l | tr -d ' ') 개"
exit 0
