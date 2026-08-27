#!/usr/bin/env bash
# 복원 사전조건 P1~P9 — **읽기만 한다. 아무것도 고치지 않는다.**
# 하나라도 아니면 복원을 시작하지 않는다(`R1-RESTORE-DRAFT §4.0`).
#
# ⭑ 이 스크립트가 닫는 결손 = 초안 `§6` #5 「`sha256` 대조 · `--skip-age` 를 손으로 채우고 있다」.
#   P4 의 sha256 대조와 P3 의 `--skip-age` 가 여기서 기구가 된다.
#
# 사용: preflight.sh [--stamp <YYYYMMDDTHHMMSS>] [--record-digests <출력.tsv>]
#   `--stamp` 를 주면 그 회차를, 안 주면 각 산출물의 최신본을 본다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BK_LIB="$HERE/../backup"
. "$BK_LIB/lib.sh"
. "$BK_LIB/volume-lib.sh"
load_config
load_volume_config

STAMP=""; DIGEST_OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --stamp) STAMP="${2:?}"; shift 2 ;;
    --record-digests) DIGEST_OUT="${2:?}"; shift 2 ;;
    *) echo "모르는 인자: $1" >&2; exit 2 ;;
  esac
done

FAILED=0
pick() { # $1=글로브 접두  $2=확장자
  if [ -n "$STAMP" ]; then ls -1 "$1-$STAMP$2" 2>/dev/null | head -1
  else ls -1t "$1"-*"$2" 2>/dev/null | head -1; fi
}

echo "════ P1 도커 데몬"
if docker ps >/dev/null 2>&1; then pass "P1 docker ps 응답"; else fail "P1 도커 데몬이 응답하지 않는다"; fi

echo "════ P2 되돌릴 산출물이 있다"
declare -A ART
for P in $(backup_profiles); do
  A="$(pick "$COLAB_BACKUP_DIR/$P" .sql.gz)"
  if [ -n "$A" ]; then ART[$P]="$A"; pass "P2 $P = $(basename "$A")"; else fail "P2 $P 산출물이 없다"; fi
done
for V in $(volume_list); do
  A="$(pick "$COLAB_BACKUP_DIR/vol-$V" .tar.gz)"
  if [ -n "$A" ]; then ART[vol-$V]="$A"; pass "P2 볼륨 $V = $(basename "$A")"; else fail "P2 볼륨 $V 아카이브가 없다"; fi
done

echo "════ P3 산출물이 GREEN 이다 (--skip-age — 사고 복원은 옛 파일을 쓴다)"
# ⚠ C6·V7 을 **없애는 것이 아니라 이 경로에서만 뺀다.** 정기 검사(latest-check)에는 그대로 산다.
for P in $(backup_profiles); do
  A="${ART[$P]:-}"; [ -n "$A" ] || continue
  if COLAB_BACKUP_MIN_TABLES="$(profile_min_tables "$P")" COLAB_BACKUP_MIN_ROWS="$(profile_min_rows "$P")" \
     "$BK_LIB/verify-artifact.sh" "$A" --skip-age >/dev/null 2>&1
  then pass "P3 $P 산출물 GREEN"; else fail "P3 $P 산출물 RED — 상세는 verify-artifact.sh 를 직접 돌린다"; fi
done
for V in $(volume_list); do
  A="${ART[vol-$V]:-}"; [ -n "$A" ] || continue
  if "$BK_LIB/verify-volume-artifact.sh" "$A" --skip-age >/dev/null 2>&1
  then pass "P3 볼륨 $V 아카이브 GREEN (원장 오라클 포함)"; else fail "P3 볼륨 $V 아카이브 RED"; fi
done

echo "════ P4 sha256 무결성"
for K in "${!ART[@]}"; do
  A="${ART[$K]}"; S="$A.sha256"
  if [ ! -f "$S" ]; then fail "P4 $K — .sha256 이 없다"; continue; fi
  GOT="$(sha256sum "$A" | awk '{print $1}')"; EXP="$(tr -d ' \n' < "$S")"
  if [ "$GOT" = "$EXP" ]; then pass "P4 $K sha256 일치"; else fail "P4 $K sha256 불일치 — 산출물이 손상됐다"; fi
done

echo "════ P5 두 원장이 같은 회차다"
S1=""; S2=""; OK=1
for P in $(backup_profiles); do
  A="${ART[$P]:-}"; [ -n "$A" ] || { OK=0; continue; }
  B="$(basename "$A")"; T="${B##*-}"; T="${T%.sql.gz}"
  [ -z "$S1" ] && S1="$T" || S2="$T"
done
if [ "$OK" -eq 1 ] && [ -n "$S1" ] && [ -n "$S2" ]; then
  # `backup.sh` 는 프로파일을 순차로 뜬다(실측 8초 차 · `IS3 §8`). **원자적 스냅숏이 아니다.**
  # 여기서 보는 것은 「같은 회차인가」이고, 30분을 넘으면 다른 세대로 본다.
  D1=$(date -d "${S1:0:8} ${S1:9:2}:${S1:11:2}:${S1:13:2}" +%s 2>/dev/null || echo 0)
  D2=$(date -d "${S2:0:8} ${S2:9:2}:${S2:11:2}:${S2:13:2}" +%s 2>/dev/null || echo 0)
  DIFF=$(( D1 > D2 ? D1 - D2 : D2 - D1 ))
  if [ "$D1" -ne 0 ] && [ "$DIFF" -le 1800 ]; then pass "P5 두 원장 시각차 ${DIFF}초"
  else fail "P5 두 원장이 다른 회차다 ($S1 vs $S2) — 원장과 사전이 다른 세대가 된다"; fi
else fail "P5 원장 둘을 못 골랐다"; fi

echo "════ P5-b 볼륨 아카이브의 짝이 그 원장이다"
for V in $(volume_list); do
  A="${ART[vol-$V]:-}"; [ -n "$A" ] || continue
  PF="${A%.tar.gz}.pair"
  if [ ! -f "$PF" ]; then fail "P5-b 볼륨 $V 에 .pair 가 없다 — 어느 원장과 짝인지 모른다"; continue; fi
  WANT="$(basename "${ART[platform]:-}")"
  if [ "$(cat "$PF")" = "$WANT" ]; then pass "P5-b 볼륨 $V 짝 = $WANT"
  else fail "P5-b 볼륨 $V 의 짝($(cat "$PF")) ≠ 되돌릴 원장($WANT)"; fi
done

echo "════ P6 비밀 7종이 제자리에 있다 (존재·권한만 본다 — 값은 읽지 않는다)"
# ⚠ 값을 출력하지 않는다. 이 스크립트의 출력이 작업 기록에 남는다(`〈121〉-㉯` 의 발단이 그것이었다).
for K in COLAB_STAGING_SUBJECTS_FILE COLAB_STAGING_CREDENTIALS_FILE \
         COLAB_STAGING_CORE_DB_URL_FILE COLAB_STAGING_PIPELINE_DB_URL_FILE \
         COLAB_STAGING_AI_DB_URL_FILE COLAB_STAGING_PLATFORM_OWNER_DB_URL_FILE \
         COLAB_STAGING_AI_OWNER_DB_URL_FILE; do
  V="$(eval "printf '%s' \"\${$K:-}\"")"
  if [ -z "$V" ]; then fail "P6 $K 가 환경에 없다 — env 파일을 먼저 source 한다"; continue; fi
  if [ ! -f "$V" ]; then fail "P6 $K 가 가리키는 파일이 없다"; continue; fi
  M="$(stat -c '%a' "$V" 2>/dev/null)"; O="$(stat -c '%u' "$V" 2>/dev/null)"
  if [ "$M" = "600" ] && [ "$O" = "10001" ]; then pass "P6 $K (0600 · uid 10001)"
  else fail "P6 $K 권한/소유자가 어긋난다 (mode=$M uid=$O · 기대 600/10001)"; fi
done
if [ -n "${COLAB_STAGING_ENV_FILE:-}" ] && [ -f "${COLAB_STAGING_ENV_FILE}" ]; then
  pass "P6 env 파일 존재"
else
  fail "P6 env 파일을 COLAB_STAGING_ENV_FILE 로 알려 주지 않았다 (7종 중 하나다)"
fi

echo "════ P7 복원 직전 상태를 한 번 더 뜬다"
echo "  ⚠ 이 스크립트는 **뜨지 않는다.** 백업은 쓰기이고 preflight 는 읽기 전용이다."
echo "     직접 돌린다:  infra/staging/backup/backup-full.sh"
echo "     이것이 「되돌림의 되돌림」의 유일한 재료다(§4.7). 안 뜨고 §4.3 을 실행하면 현재 상태가 영구히 사라진다."
if [ -n "${COLAB_RESTORE_PRE_BACKUP:-}" ] && [ -f "${COLAB_RESTORE_PRE_BACKUP}" ]; then
  pass "P7 복원 직전 백업 = $(basename "$COLAB_RESTORE_PRE_BACKUP")"
else
  fail "P7 복원 직전 백업을 COLAB_RESTORE_PRE_BACKUP 으로 지목하지 않았다"
fi

echo "════ P8 현재 이미지 digest 를 적어 둔다"
if [ -n "$DIGEST_OUT" ]; then
  "$HERE/check-image-digests.sh" --record "$DIGEST_OUT" || true
  if [ -s "$DIGEST_OUT" ]; then pass "P8 현재 digest 를 $(basename "$DIGEST_OUT") 에 기록"; else fail "P8 digest 기록 실패"; fi
else
  fail "P8 --record-digests <출력.tsv> 를 주지 않았다 — 비교 기준이 없으면 §4.6-④ 를 못 잰다"
fi

echo "════ P9 원인 규명"
if [ "${COLAB_RESTORE_CAUSE:-}" != "" ]; then
  pass "P9 원인 = $COLAB_RESTORE_CAUSE"
else
  fail "P9 COLAB_RESTORE_CAUSE 가 비어 있다. **원인 미상인 채 복원하면 같은 손상이 다시 온다**(S2-BLOCKER-INVESTIGATION §1.4)"
fi

echo
if [ "$FAILED" -eq 0 ]; then echo "사전조건 GREEN — 복원을 시작해도 된다"; exit 0; fi
echo "사전조건 RED (실패 ${FAILED}건) — **복원을 시작하지 않는다**"; exit 1
