#!/usr/bin/env bash
# staging 백업 1회 실행.
#
# PoC 백업 사건(DEPLOY-CURRENT §8)의 세 원인을 구조로 막는다:
#   ① 죽은 트리에서 실행 → 대상을 설정으로 명시하고, 대상이 없으면 성공하지 않는다(exit 78)
#   ② 리다이렉션이 pg_dump 보다 먼저 파일을 만든다 → 임시파일에 받고 PIPESTATUS 로 종료코드 확인
#   ③ 크기·gzip -t 만 보는 가드 → verify-artifact.sh 통과 후에만 mv (내용 검사)
# 실패 시 최종 경로에는 아무것도 남기지 않는다. 이전 성공본을 새 것처럼 보이게 하지 않는다.
#
# 대상은 **프로파일 목록**이다. platform 과 ai 는 서로 다른 데이터베이스이고(CLAUDE.md §3-3),
# 한쪽만 덮은 백업이 전체 성공으로 기록되는 것이 이 WU 가 막으려는 실패 그 자체다.
# 프로파일이 하나라도 실패하면 전체가 실패다.
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

backup_one() { # $1=프로파일
  local P="$1" DB MT MR STAMP FINAL TMP RC
  DB="$(profile_db "$P")"; MT="$(profile_min_tables "$P")"; MR="$(profile_min_rows "$P")"
  [ -n "$DB" ] || { log "[$P] 데이터베이스 이름이 비어 있다 (COLAB_BACKUP_DB_$P)"; return 1; }
  STAMP="$(date +%Y%m%dT%H%M%S)"
  FINAL="$COLAB_BACKUP_DIR/$P-$STAMP.sql.gz"
  TMP="$COLAB_BACKUP_DIR/.inflight-$P-$STAMP.sql.gz"
  trap 'rm -f "$TMP"' RETURN

  log "[$P] 덤프 시작 (db=$DB) → 임시파일"
  if [ -n "${COLAB_BACKUP_PG_CONTAINER:-}" ]; then
    docker exec -i "$COLAB_BACKUP_PG_CONTAINER" \
      pg_dump -U "${COLAB_BACKUP_PG_USER:?}" -d "$DB" --no-owner --no-privileges \
      | gzip -c > "$TMP"
  else
    # URL 직결은 URL 자체가 데이터베이스를 지목한다 — 프로파일이 여럿이면 컨테이너 경유를 쓴다.
    pg_dump "${COLAB_BACKUP_PG_URL:?}" --no-owner --no-privileges | gzip -c > "$TMP"
  fi
  RC=("${PIPESTATUS[@]}")
  if [ "${RC[0]}" -ne 0 ]; then
    log "[$P] pg_dump 실패 (exit ${RC[0]}). 임시파일 폐기 · 최종본 생성 안 함."
    return 1
  fi
  [ "${RC[1]:-0}" -eq 0 ] || { log "[$P] gzip 실패 (exit ${RC[1]})"; return 1; }

  log "[$P] 산출물 검사 (통과 전에는 최종 경로로 옮기지 않는다)"
  if ! COLAB_BACKUP_MIN_TABLES="$MT" COLAB_BACKUP_MIN_ROWS="$MR" "$HERE/verify-artifact.sh" "$TMP"; then
    log "[$P] 검사 RED — 백업 실패로 기록한다. 최종본 생성 안 함."
    return 1
  fi

  mv "$TMP" "$FINAL"; trap - RETURN
  sha256sum "$FINAL" | awk '{print $1}' > "$FINAL.sha256"
  log "[$P] 백업 성공: $(basename "$FINAL") ($(wc -c < "$FINAL") B)"

  # 보존 — 기한 초과분을 지우되 그 프로파일의 가장 최신 1개는 절대 지우지 않는다.
  local NEWEST old
  NEWEST="$(ls -1t "$COLAB_BACKUP_DIR/$P"-*.sql.gz 2>/dev/null | head -1)"
  find "$COLAB_BACKUP_DIR" -maxdepth 1 -name "$P-*.sql.gz" -mtime "+$COLAB_BACKUP_RETENTION_DAYS" \
    | while read -r old; do
        [ "$old" = "$NEWEST" ] && continue
        log "[$P] 보존기한 초과 삭제: $(basename "$old")"; rm -f "$old" "$old.sha256"
      done
  return 0
}

BAD=0; N=0
for P in $(backup_profiles); do
  N=$((N+1))
  backup_one "$P" || { BAD=$((BAD+1)); log "[$P] 실패"; }
done

# 남은 inflight 잔해 정리 (하루 이상 된 것만)
find "$COLAB_BACKUP_DIR" -maxdepth 1 -name '.inflight-*' -mmin +1440 -delete 2>/dev/null || true

if [ "$BAD" -eq 0 ]; then
  log "백업 GREEN — 프로파일 $N 개 전부 성공"
  exit 0
fi
log "백업 RED — 프로파일 $N 개 중 $BAD 개 실패. 부분 성공을 성공으로 기록하지 않는다."
exit 1
