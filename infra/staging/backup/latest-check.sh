#!/usr/bin/env bash
# 최신 산출물 재검사 — "백업이 오늘도 살아 있는가" 를 주기적으로 되묻는다.
# 산출물이 아예 없는 것도 실패다. 침묵을 성공으로 읽지 않는다.
# 프로파일마다 따로 묻는다 — 한쪽만 남아 있는 상태를 통과시키지 않는다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
. "$HERE/volume-lib.sh"
load_config
load_volume_config
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
# ── 볼륨 아카이브도 같은 질문을 받는다. **산출물이 없는 것도 실패다.**
#    원장만 살아 있고 볼륨이 조용히 멈춘 상태는 「DB 만 과거로 가고 파일은 현재에 남는」
#    복원을 예약해 둔 것과 같다(`WORK-UNITS §10.2` R-1 행).
VN=0
for V in $(volume_list); do
  VN=$((VN+1))
  LATEST="$(ls -1t "$COLAB_BACKUP_DIR/vol-$V"-*.tar.gz 2>/dev/null | head -1)"
  if [ -z "$LATEST" ]; then log "[$V] 볼륨 아카이브가 하나도 없다 — 실패다"; BAD=$((BAD+1)); continue; fi
  echo "──────── 볼륨 $V"
  "$HERE/verify-volume-artifact.sh" "$LATEST" || BAD=$((BAD+1))
done

# ── 보관처 위생 — 비밀 사본이 흘러들었는지 정기적으로 되묻는다 (〈170〉-㉰).
OFF="$(backup_dir_offenders)"
if [ -n "$OFF" ]; then
  echo "──────── 보관처 위생"
  printf '%s\n' "$OFF" | while IFS= read -r f; do echo "  ⛔ 산출물 규약 밖: $(basename "$f")"; done
  echo "  비밀 사본일 수 있다 — 〈163〉-㉲ 는 비밀 7종을 백업하지 않는다. 값은 읽지 않았다."
  BAD=$((BAD+1))
fi

if [ "$BAD" -eq 0 ]; then echo "최신본 재검사 GREEN — 프로파일 $N 개 · 볼륨 $VN 개"; exit 0; fi
echo "최신본 재검사 RED — 프로파일 $N ＋ 볼륨 $VN 중 $BAD 개 실패"; exit 1
