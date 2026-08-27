#!/usr/bin/env bash
# 볼륨 아카이브 1회 생성 — `backup.sh` 와 **같은 자세**로 쓴다.
#   ① 대상이 없으면 성공하지 않는다 (`exit 78`)
#   ② 임시 파일에 받고 종료코드를 확인한다. 실패하면 최종 경로에 아무것도 남기지 않는다
#   ③ 크기·`gzip -t` 가 아니라 **내용**을 검사한 뒤에만 최종본이 된다 (`verify-volume-artifact.sh`)
#
# ⭑ **순서 — 원장 덤프가 먼저, 볼륨 tar 가 나중이다.** 이 순서는 취향이 아니라 오라클의 조건이다.
#   t0 에 원장을 뜨고 t1 에 볼륨을 뜨면, **t0 에 원장이 가리키던 모든 파일은 t1 에도 있다**
#   (저장키는 ULID 라 덮어쓰이지 않고, 접수는 추가만 한다). 그래서 아카이브는 원장을 **덮는다**.
#   [t0,t1] 사이 접수분은 아카이브에만 있는 고아 바이트가 되는데, 그것은 `R1-RESTORE-DRAFT §4.4-㈏`
#   가 **이미 정상으로 선언한 상태**다. 뒤집으면(볼륨 먼저) 원장이 아카이브에 없는 파일을 가리키게 되고,
#   그때는 오라클이 RED 를 내는 것이 맞는 상황이 아니라 **절차가 만든 RED** 가 된다.
#   ⚠ **정지(quiesce)를 걸지 않는다.** 위 논증이 정지 없이 성립하므로 서비스를 세울 이유가 없다.
#   ⚠ **남는 가장자리 하나 — [t0,t1] 사이의 「삭제」.** 그 사이에 파일이 지워지면 원장에는 있고
#     아카이브에는 없어 오라클이 RED 를 낸다. staging 에서 이것을 위해 설계하지 않는다:
#     발생하면 그 회차를 **다시 돌리면 된다**(다음 회차의 원장에는 그 행이 없다). 조용히 통과시키는
#     완화(예외 목록·유예)를 넣지 않는다 — 그 완화가 곧 「빠진 파일을 못 보는 가드」다.
#
# 사용: backup-volume.sh --pair <원장덤프.sql.gz> [볼륨 …]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
. "$HERE/volume-lib.sh"
load_config
load_volume_config

PAIR=""
while [ $# -gt 0 ]; do
  case "$1" in
    --pair) PAIR="${2:-}"; shift 2 ;;
    -*)     die "모르는 인자: $1" ;;
    *)      break ;;
  esac
done
VOLS="${*:-$(volume_list)}"

if [ "$COLAB_BACKUP_TARGET" = "none" ]; then
  log "백업 대상이 연결돼 있지 않다 (COLAB_BACKUP_TARGET=none). 이 상태를 성공으로 기록하지 않는다 — exit 78."
  exit 78
fi
command -v docker >/dev/null 2>&1 || die "docker 가 없다 — 볼륨은 도커가 쥐고 있다"
[ -n "$PAIR" ] || die "--pair <원장덤프.sql.gz> 가 필요하다. 짝 없는 볼륨 아카이브는 검사할 기준이 없다"
[ -f "$PAIR" ] || die "짝 원장 덤프를 찾지 못했다: $(basename "$PAIR")"
mkdir -p "$COLAB_BACKUP_DIR" || die "보관처를 만들지 못했다"

# ── 디스크 여유 사전점검 ──────────────────────────────────────────────────────
# 볼륨 아카이브는 14일치 SQL 덤프를 압도한다. 그리고 **오프호스트 사본이 없다**
# (`R1-RESTORE-DRAFT §2 #13`) — 백업이 원본과 같은 WSL2 디스크 1대 위에 있다.
# 그래서 「디스크를 채워 staging 자체를 죽이는 백업」이 실재하는 위험이다. 먼저 잰다.
precheck_space() { # $1=볼륨 실이름 → 0=여유 있음
  local real="$1" used free need
  used="$(docker run --rm -v "$real":/vol:ro "$COLAB_VOLBACKUP_HELPER_IMAGE" \
            sh -c 'du -sk /vol 2>/dev/null | cut -f1' 2>/dev/null)"
  used="${used:-0}"
  free="$(df -Pk "$COLAB_BACKUP_DIR" | awk 'NR==2{print $4}')"
  free="${free:-0}"
  need=$(( used * COLAB_VOLBACKUP_FREE_MULTIPLIER ))
  log "  볼륨 실사용 ${used}KiB · 보관처 여유 ${free}KiB · 요구 ${need}KiB(x$COLAB_VOLBACKUP_FREE_MULTIPLIER)"
  # 압축이 먹으면 아카이브는 실사용보다 작다. 배수를 두는 이유는 **압축률을 모르기 때문**이다 —
  # 이미 압축된 GeoTIFF·NetCDF 는 거의 안 줄어든다(`DATA-REFERENCE`). 모르는 값을 낙관하지 않는다.
  [ "$free" -ge "$need" ]
}

backup_one_volume() { # $1=볼륨
  local V="$1" REAL STAMP BASE TMP TMPMAN RC
  REAL="$(volume_real_name "$V")"
  docker volume inspect "$REAL" >/dev/null 2>&1 || { log "[$V] 볼륨 $REAL 이 없다"; return 1; }
  precheck_space "$REAL" || { log "[$V] 디스크 여유 부족 — 시작하지 않는다. 백업이 호스트를 채우면 그것이 사고다"; return 1; }

  STAMP="$(date +%Y%m%dT%H%M%S)"
  BASE="$(volume_artifact_base "$COLAB_BACKUP_DIR" "$V" "$STAMP")"
  TMP="$COLAB_BACKUP_DIR/.inflight-vol-$V-$STAMP.tar.gz"
  TMPMAN="$COLAB_BACKUP_DIR/.inflight-vol-$V-$STAMP.manifest.tsv"
  trap 'rm -f "$TMP" "$TMPMAN"' RETURN

  # ── ① 매니페스트 — **tar 보다 먼저, 같은 목록에서.**
  #    경로·크기·sha256 을 뜬다. 이 목록이 곧 tar 의 입력이 되므로 아카이브와 매니페스트가
  #    **구성상** 같은 집합이고, 그 사실을 `verify-volume-artifact.sh V4` 가 산출물만 보고 재확인한다.
  #    ⚠ 경로에 탭·개행이 있으면 매니페스트가 깨진다 — **건너뛰지 않고 실패한다.** 조용히 빠진
  #      파일이 있는 백업이 이 WU 가 막으려는 실패 그 자체다.
  log "[$V] 매니페스트 작성 (경로·크기·sha256)"
  docker run --rm -v "$REAL":/vol:ro "$COLAB_VOLBACKUP_HELPER_IMAGE" sh -c '
    cd /vol || exit 1
    find . -type f -print | LC_ALL=C sort | while IFS= read -r f; do
      case "$f" in *"	"*) echo "TABNAME:$f" >&2; exit 3 ;; esac
      s=$(wc -c < "$f" | tr -d " ")
      h=$(sha256sum "$f" | cut -d" " -f1)
      printf "%s\t%s\t%s\n" "${f#./}" "$s" "$h"
    done' > "$TMPMAN"
  RC=$?
  [ "$RC" -eq 0 ] || { log "[$V] 매니페스트 작성 실패 (exit $RC) — 최종본 생성 안 함"; return 1; }

  # ── ② tar — 매니페스트의 경로 목록 그대로.
  log "[$V] 아카이브 생성"
  awk -F'\t' '{print "./" $1}' "$TMPMAN" \
    | docker run --rm -i -v "$REAL":/vol:ro "$COLAB_VOLBACKUP_HELPER_IMAGE" \
        sh -c 'cat > /tmp/list; tar -czf - -C /vol -T /tmp/list' > "$TMP"
  RC=("${PIPESTATUS[@]}")
  if [ "${RC[1]}" -ne 0 ]; then
    log "[$V] tar 실패 (exit ${RC[1]}). 임시파일 폐기 · 최종본 생성 안 함."
    log "     — 매니페스트에 있던 파일이 tar 시점에 사라졌을 수 있다. 그 회차는 다시 돌린다."
    return 1
  fi

  # ── ③ 검사 통과분만 최종본이 된다.
  mv "$TMPMAN" "$BASE.manifest.tsv"
  mv "$TMP" "$BASE.tar.gz"
  basename "$PAIR" > "$BASE.pair"
  trap - RETURN
  if ! "$HERE/verify-volume-artifact.sh" "$BASE.tar.gz" --pair "$PAIR"; then
    log "[$V] 검사 RED — 백업 실패로 기록한다. 최종본을 걷는다."
    rm -f "$BASE.tar.gz" "$BASE.manifest.tsv" "$BASE.pair"
    return 1
  fi
  sha256sum "$BASE.tar.gz" | awk '{print $1}' > "$BASE.tar.gz.sha256"
  log "[$V] 볼륨 백업 성공: $(basename "$BASE.tar.gz") ($(wc -c < "$BASE.tar.gz") B) · 짝 $(basename "$PAIR")"

  # ── ④ 보존 — 볼륨별. 가장 최신 1개는 어떤 경우에도 지우지 않는다(원장 덤프와 같은 규칙).
  local NEWEST old
  NEWEST="$(ls -1t "$COLAB_BACKUP_DIR/vol-$V"-*.tar.gz 2>/dev/null | head -1)"
  find "$COLAB_BACKUP_DIR" -maxdepth 1 -name "vol-$V-*.tar.gz" -mtime "+$COLAB_VOLBACKUP_RETENTION_DAYS" \
    | while read -r old; do
        [ "$old" = "$NEWEST" ] && continue
        log "[$V] 보존기한 초과 삭제: $(basename "$old")"
        rm -f "$old" "$old.sha256" "${old%.tar.gz}.manifest.tsv" "${old%.tar.gz}.pair"
      done
  return 0
}

BAD=0; N=0
for V in $VOLS; do
  N=$((N+1))
  backup_one_volume "$V" || { BAD=$((BAD+1)); log "[$V] 실패"; }
done

find "$COLAB_BACKUP_DIR" -maxdepth 1 -name '.inflight-vol-*' -mmin +1440 -delete 2>/dev/null || true

if [ "$BAD" -eq 0 ]; then
  log "볼륨 백업 GREEN — 볼륨 $N 개 전부 성공"
  exit 0
fi
log "볼륨 백업 RED — 볼륨 $N 개 중 $BAD 개 실패. 부분 성공을 성공으로 기록하지 않는다."
exit 1
