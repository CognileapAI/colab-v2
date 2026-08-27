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

# ── 야간 실행 표식 — **정지가 사람에게 도달하는 자리** (〈171〉-㉱).
#    `run-scheduled.sh` 는 실패하면 `BACKUP-FAILED.txt` 를 남기고 **다음 성공에서만** 지운다.
#    그런데 월요일 검사가 그 표식을 **한 번도 읽지 않고 있었다** — 표식은 「가서 봐야 보이는」 자리인데
#    「가서 보는」 유일한 기구가 그것을 안 봤다. 볼륨 백업이 비밀 모양 파일로 정지하면
#    (`backup-volume.sh` ①-b) 산출물이 안 생기는데, 보존 규칙이 **가장 최신 1개를 안 지우므로**
#    옛 아카이브가 남아 있고, 그때 사람에게 닿는 것은 V7 신선도 RED 뿐이었다 —
#    「옛 잔존 파일이다」라고만 적혀 **왜 멈췄는지가 안 보였다.** 그래서 표식을 여기서 읽는다.
STATE="$(dirname "$COLAB_BACKUP_DIR")"
if [ -f "$STATE/BACKUP-FAILED.txt" ]; then
  echo "──────── 야간 실행 표식 (BACKUP-FAILED.txt)"
  sed 's/^/  ⛔ /' "$STATE/BACKUP-FAILED.txt"
  echo "  ⛔ 야간 백업이 **실패한 채로 남아 있다.** 이 표식은 다음 성공에서만 사라진다."
  echo "     흔한 원인 하나 — **볼륨 안 비밀 모양 파일**(〈170〉-㉰): 그 볼륨은 아카이브가 통째로 안 만들어진다."
  echo "     조치: staging-backup.log 에서 '⛔' 줄의 파일 이름을 찾아 볼륨에서 치우고 backup-full.sh 를 다시 돌린다."
  echo "     절차 전문 = README 「볼륨 백업이 정지했을 때」 · ../restore/RUNBOOK.md §9"
  BAD=$((BAD+1))
fi

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
