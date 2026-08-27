#!/usr/bin/env bash
# 볼륨 하나를 제자리 복원한다 (`R1-RESTORE-DRAFT §4.4-㈎`).
#
# ⚠ **원장(§4.3)보다 뒤에 돈다.** 원장이 파일 행의 정본이고 볼륨은 그 행이 가리키는 바이트다.
# ⚠ **덮어쓰기이지 동기화가 아니다.** 아카이브에 없는 파일을 지우지 않는다 —
#   지우는 쪽이 더 위험하다(되돌림의 되돌림이 막힌다 · `§4.4-㈏`).
#   그래서 `--prune` 같은 선택지를 두지 않았다. 없는 기능은 잘못 쓰이지 않는다.
#
# 문 셋:
#   ① `--yes-overwrite-volume`
#   ② 그 볼륨을 쥔 컨테이너가 **전부 정지** 상태다 (§4.1 ①~⑤ 를 돌았는가)
#   ③ 아카이브가 GREEN 이다 — 짝 원장 오라클 포함 (`--skip-age`)
#
# 사용: restore-volume.sh --volume <uploads|previews> --archive <vol-*.tar.gz> --yes-overwrite-volume
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BK="$HERE/../backup"
. "$BK/lib.sh"; . "$BK/volume-lib.sh"
load_config; load_volume_config

VOL=""; ART=""; CONFIRM=0
while [ $# -gt 0 ]; do
  case "$1" in
    --volume) VOL="${2:?}"; shift 2 ;;
    --archive) ART="${2:?}"; shift 2 ;;
    --yes-overwrite-volume) CONFIRM=1; shift ;;
    *) die "모르는 인자: $1" ;;
  esac
done
[ -n "$VOL" ] && [ -n "$ART" ] || die "사용: restore-volume.sh --volume <이름> --archive <파일> --yes-overwrite-volume"
[ "$CONFIRM" -eq 1 ] || die "--yes-overwrite-volume 이 없다"
[ -f "$ART" ] || die "아카이브를 찾지 못했다"

REAL="$(volume_real_name "$VOL")"
docker volume inspect "$REAL" >/dev/null 2>&1 || die "볼륨 $REAL 이 없다"

# ── 문 ② 그 볼륨을 쥔 컨테이너가 도는 중이면 멈춘다 ──────────────────────────
RUNNING="$(docker ps --format '{{.Names}}' --filter "volume=$REAL")"
[ -z "$RUNNING" ] || die "볼륨 $REAL 을 쥔 컨테이너가 돌고 있다: $RUNNING — 먼저 §4.1 정지 순서를 돈다"

# ── 문 ③ 아카이브 재검사 ─────────────────────────────────────────────────────
"$BK/verify-volume-artifact.sh" "$ART" --skip-age || die "아카이브가 RED 다. 풀지 않는다"

log "볼륨 $REAL 에 아카이브를 푼다 (덮어쓰기 · 삭제 없음)"
# 헬퍼 컨테이너는 root 로 돈다 — 볼륨 마운트 지점 소유자는 root 이고 세 단위는 uid 10001 이다.
# `compose.i2.yml` 의 `volume-init` 이 하는 일과 **같은 일**을 복원 뒤에도 한 번 더 한다.
if ! gunzip -c "$ART" | docker run --rm -i -u 0:0 -v "$REAL":/vol "$COLAB_VOLBACKUP_HELPER_IMAGE" \
      sh -c 'tar -xf - -C /vol && chown -R 10001:10001 /vol && chmod 0755 /vol'; then
  die "복원 실패. **성공으로 기록하지 않는다.**"
fi

# ── 되돌린 결과를 센다 — 「tar 가 exit 0 이었다」를 성공으로 보지 않는다.
MAN="${ART%.tar.gz}.manifest.tsv"
[ -f "$MAN" ] || die "매니페스트가 없다 — 되돌린 결과를 셀 기준이 없다"
BADF="$(docker run --rm -i -v "$REAL":/vol:ro "$COLAB_VOLBACKUP_HELPER_IMAGE" sh -c '
  cd /vol || exit 1
  bad=0
  while IFS="	" read -r p s h; do
    [ -n "$p" ] || continue
    if [ ! -f "$p" ]; then echo "MISSING $p"; bad=$((bad+1)); continue; fi
    g=$(sha256sum "$p" | cut -d" " -f1)
    [ "$g" = "$h" ] || { echo "DIGEST  $p"; bad=$((bad+1)); }
  done
  echo "BAD=$bad"' < "$MAN")"
echo "$BADF" | grep -v '^BAD=' | head -20
N="$(printf '%s' "$BADF" | sed -n 's/^BAD=//p' | tail -1)"
[ "${N:-1}" = "0" ] || die "복원 대조 RED — 어긋난 파일 ${N:-측정실패}건. sha256 까지 본다(크기만 보면 뒤바뀐 내용이 통과한다)"

log "볼륨 $VOL 복원 GREEN — 매니페스트 전건 sha256 일치"
exit 0
