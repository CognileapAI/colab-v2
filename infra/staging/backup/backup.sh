#!/usr/bin/env bash
# staging 백업 1회 실행.
#
# PoC 백업 사건(DEPLOY-CURRENT §8)의 세 원인을 구조로 막는다:
#   ① 죽은 트리에서 실행 → 대상을 설정으로 명시하고, 대상이 없으면 성공하지 않는다(exit 78)
#   ② 리다이렉션이 pg_dump 보다 먼저 파일을 만든다 → 임시파일에 받고 PIPESTATUS 로 종료코드 확인
#   ③ 크기·gzip -t 만 보는 가드 → verify-artifact.sh 통과 후에만 mv (내용 검사)
# 실패 시 최종 경로에는 아무것도 남기지 않는다. 이전 성공본을 새 것처럼 보이게 하지 않는다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
load_config

if [ "$COLAB_BACKUP_TARGET" = "none" ]; then
  log "백업 대상이 연결돼 있지 않다 (COLAB_BACKUP_TARGET=none)."
  log "I2 walking skeleton 이 postgres 를 올리면 설정에서 postgres 로 바꾼다."
  log "이 상태를 성공으로 기록하지 않는다 — exit 78."
  exit 78
fi
[ "$COLAB_BACKUP_TARGET" = "postgres" ] || die "알 수 없는 COLAB_BACKUP_TARGET=$COLAB_BACKUP_TARGET"

mkdir -p "$COLAB_BACKUP_DIR" || die "보관처를 만들지 못했다"
STAMP="$(date +%Y%m%dT%H%M%S)"
FINAL="$COLAB_BACKUP_DIR/platform-$STAMP.sql.gz"
TMP="$COLAB_BACKUP_DIR/.inflight-$STAMP.sql.gz"
trap 'rm -f "$TMP"' EXIT

log "덤프 시작 → 임시파일"
if [ -n "${COLAB_BACKUP_PG_CONTAINER:-}" ]; then
  docker exec -i "$COLAB_BACKUP_PG_CONTAINER" \
    pg_dump -U "${COLAB_BACKUP_PG_USER:?}" -d "${COLAB_BACKUP_PG_DB:?}" --no-owner --no-privileges \
    | gzip -c > "$TMP"
else
  pg_dump "${COLAB_BACKUP_PG_URL:?}" --no-owner --no-privileges | gzip -c > "$TMP"
fi
RC=("${PIPESTATUS[@]}")
if [ "${RC[0]}" -ne 0 ]; then
  log "pg_dump 실패 (exit ${RC[0]}). 임시파일 폐기 · 최종본 생성 안 함."
  exit 1
fi
[ "${RC[1]:-0}" -eq 0 ] || { log "gzip 실패 (exit ${RC[1]})"; exit 1; }

log "산출물 검사 (통과 전에는 최종 경로로 옮기지 않는다)"
if ! "$HERE/verify-artifact.sh" "$TMP"; then
  log "검사 RED — 백업 실패로 기록한다. 최종본 생성 안 함."
  exit 1
fi

mv "$TMP" "$FINAL"; trap - EXIT
sha256sum "$FINAL" | awk '{print $1}' > "$FINAL.sha256"
log "백업 성공: $(basename "$FINAL")"

# 보존 — 기한 초과분을 지우되 가장 최신 1개는 절대 지우지 않는다.
NEWEST="$(ls -1t "$COLAB_BACKUP_DIR"/platform-*.sql.gz 2>/dev/null | head -1)"
find "$COLAB_BACKUP_DIR" -maxdepth 1 -name 'platform-*.sql.gz' -mtime "+$COLAB_BACKUP_RETENTION_DAYS" \
  | while read -r old; do
      [ "$old" = "$NEWEST" ] && continue
      log "보존기한 초과 삭제: $(basename "$old")"; rm -f "$old" "$old.sha256"
    done
# 남은 inflight 잔해 정리 (하루 이상 된 것만)
find "$COLAB_BACKUP_DIR" -maxdepth 1 -name '.inflight-*' -mmin +1440 -delete 2>/dev/null || true
exit 0
