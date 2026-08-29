#!/usr/bin/env bash
# 복원 사전조건 P1~P9 — **읽기만 한다. 아무것도 고치지 않는다.**
# 하나라도 아니면 복원을 시작하지 않는다(`R1-RESTORE-DRAFT §4.0`).
#
# ⭑ 이 스크립트가 닫는 결손 = 초안 `§6` #5 「`sha256` 대조 · `--skip-age` 를 손으로 채우고 있다」.
#   P4 의 sha256 대조와 P3 의 `--skip-age` 가 여기서 기구가 된다.
#
# 사용: preflight.sh [--stamp <YYYYMMDDTHHMMSS>] [--record-digests <출력.tsv>]
#   `--stamp` 를 주면 **그 회차**를, 안 주면 **짝이 맞는 가장 최근 회차**를 본다.
#   ⚠ 산출물을 각각 「최신」으로 고르지 않는다 — 그 배선이 P5-b 를 통과 불가능하게 만들었다(`volume-lib.sh` 회차 절).
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

FAILED=0; SKIPPED=0

# ── 회차를 **하나** 고른다 (`PLAN-SoT §9` · Ted 판정 2026-08-29) ────────────────
# ⛔ 종전 `pick()` 은 원장과 볼륨을 **각각 독립으로 「최신」** 으로 골랐다. 원장 전용 백업이
#   볼륨보다 뒤에 뜬 회차가 실제로 있었고(2026-08-29T10:08 배포전 백업), 그 순간부터
#   P5-b 가 **입력을 다 줘도 통과할 수 없는 상태**가 됐다. `--stamp` 도 우회로가 못 됐다 —
#   `backup-full.sh` 가 볼륨마다 다른 스탬프를 찍기 때문이다(실측 35초 차).
# ⟹ 회차의 이름(= 그 회차의 platform 덤프 파일명)으로 **한 벌을 통째로** 고른다.
#   `--stamp` 는 이제 **회차 지목**이다 — 그 스탬프의 platform 덤프가 회차 이름이 된다.
ROUND=""
ROUND_RC=0
ROUND="$(select_backup_round "$COLAB_BACKUP_DIR" "$STAMP")" || ROUND_RC=$?

echo "════ P1 도커 데몬"
if docker ps >/dev/null 2>&1; then pass "P1 docker ps 응답"; else fail "P1 도커 데몬이 응답하지 않는다"; fi

echo "════ P2 되돌릴 산출물이 있다 — **한 회차에서 한 벌로** 고른다"
declare -A ART
# 세 상태를 여기서 가른다. 「아무것도 안 고름」이 조용히 통과로 새지 않게 **먼저** 판정한다.
if [ "$ROUND_RC" -eq 2 ]; then
  for V in $(volume_list); do
    [ -n "$(volume_pairing "$V")" ] || fail "P2 볼륨 $V 의 회차 편입 선언이 없다 — COLAB_VOLBACKUP_PAIRING_$V 를 round 또는 none 으로 적는다"
  done
  fail "P2 회차를 고르지 못했다 — 선언이 없는 볼륨이 있다. **모르는 것을 최신으로 읽지 않는다**"
elif [ -z "$ROUND" ]; then
  fail "P2 짝이 맞는 회차가 없다${STAMP:+ (--stamp $STAMP)} — 원장과 볼륨이 한 벌인 회차가 보관처에 없다. **각각의 「최신」으로 떨어지지 않는다**"
else
  pass "P2 회차 = $ROUND"
  for P in $(backup_profiles); do
    A="$(round_profile_dump "$COLAB_BACKUP_DIR" "$P" "$ROUND")"
    if [ -n "$A" ]; then ART[$P]="$A"; pass "P2 $P = $(basename "$A")"; else fail "P2 $P 산출물이 이 회차에 없다"; fi
  done
  for V in $(volume_list); do
    if [ "$(volume_pairing "$V")" = none ]; then
      skip_ack "P2 볼륨 $V 는 회차 편입에서 명시 면제 (COLAB_VOLBACKUP_PAIRING_$V=none)"; continue
    fi
    A="$(round_volume_archive "$COLAB_BACKUP_DIR" "$V" "$ROUND")"
    if [ -n "$A" ]; then ART[vol-$V]="$A"; pass "P2 볼륨 $V = $(basename "$A")"; else fail "P2 볼륨 $V 아카이브가 이 회차에 없다"; fi
  done
fi

echo "════ P3 산출물이 GREEN 이다 (--skip-age — 사고 복원은 옛 파일을 쓴다)"
# ⚠ C6·V7 을 **없애는 것이 아니라 이 경로에서만 뺀다.** 정기 검사(latest-check)에는 그대로 산다.
for P in $(backup_profiles); do
  A="${ART[$P]:-}"; [ -n "$A" ] || { fail "P3 $P — 검사할 산출물을 고르지 못했다(P2 참조). **못 돈 것을 통과로 세지 않는다**"; continue; }
  if COLAB_BACKUP_MIN_TABLES="$(profile_min_tables "$P")" COLAB_BACKUP_MIN_ROWS="$(profile_min_rows "$P")" \
     "$BK_LIB/verify-artifact.sh" "$A" --skip-age >/dev/null 2>&1
  then pass "P3 $P 산출물 GREEN"; else fail "P3 $P 산출물 RED — 상세는 verify-artifact.sh 를 직접 돌린다"; fi
done
for V in $(volume_list); do
  if [ "$(volume_pairing "$V")" = none ]; then skip_ack "P3 볼륨 $V — 회차 편입 명시 면제라 이 회차의 아카이브가 없다"; continue; fi
  A="${ART[vol-$V]:-}"; [ -n "$A" ] || { fail "P3 볼륨 $V — 검사할 아카이브를 고르지 못했다(P2 참조)"; continue; }
  # ⭑ **「원장 오라클 포함」을 무조건 찍지 않는다** (`〈170〉-㉮`). 오라클 선언을 설정에서 읽어
  #   그 값을 적고, 검사기 요약줄(SKIP 건수 포함)을 그대로 옮긴다. `rehearsal.sh` 4단과 같은 처치다.
  O="$(volume_oracle "$V")"
  OUT="$("$BK_LIB/verify-volume-artifact.sh" "$A" --skip-age 2>&1)"; RC=$?
  SUM="$(echo "$OUT" | tail -1)"
  if [ "$RC" -eq 0 ]
  then pass "P3 볼륨 $V 아카이브 — $SUM · 원장 오라클 = ${O:-미선언}"
  else fail "P3 볼륨 $V 아카이브 RED — $SUM (상세는 verify-volume-artifact.sh 를 직접 돌린다)"; fi
done

echo "════ P4 sha256 무결성"
[ "${#ART[@]}" -gt 0 ] || fail "P4 대조할 산출물이 0건이다 — 대상 0 을 무결성 통과로 읽지 않는다(P2 참조)"
for K in "${!ART[@]:-}"; do
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
# ⭑ 세 상태다. 고른 회차가 없으면 여기서 **검사 대상 0 인 채 조용히 넘어가지 않는다**.
if [ -z "$ROUND" ]; then
  fail "P5-b 회차가 없어 짝을 대조하지 못했다 — 대상 0 건을 통과로 세지 않는다(P2 참조)"
else
for V in $(volume_list); do
  if [ "$(volume_pairing "$V")" = none ]; then
    skip_ack "P5-b 볼륨 $V — 회차 편입 명시 면제 (원장과 짝짓지 않는다고 사람이 적은 것)"; continue
  fi
  A="${ART[vol-$V]:-}"; [ -n "$A" ] || { fail "P5-b 볼륨 $V — 대조할 아카이브가 없다(P2 참조)"; continue; }
  PF="${A%.tar.gz}.pair"
  if [ ! -f "$PF" ]; then fail "P5-b 볼륨 $V 에 .pair 가 없다 — 어느 원장과 짝인지 모른다"; continue; fi
  if [ "$(cat "$PF")" = "$ROUND" ]; then pass "P5-b 볼륨 $V 짝 = $ROUND"
  else fail "P5-b 볼륨 $V 의 짝($(cat "$PF")) ≠ 회차($ROUND)"; fi
done
fi

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
  # ⚠ 종전 이 자리는 `|| true` 였다 — 대장 대조가 RED 여도 **파일만 비어 있지 않으면 PASS** 였다.
  #   기록과 대조는 다른 사실이다. 대조 결과를 삼키면 P8 은 「적었다」만 말하고 「맞다」를 말하지 않는다.
  DIGEST_RC=0
  "$HERE/check-image-digests.sh" --record "$DIGEST_OUT" || DIGEST_RC=$?
  if [ ! -s "$DIGEST_OUT" ]; then fail "P8 digest 기록 실패"
  elif [ "$DIGEST_RC" -ne 0 ]; then fail "P8 digest 를 $(basename "$DIGEST_OUT") 에 적었으나 **대장 대조가 RED** 다 (위 FAIL 줄)"
  else pass "P8 현재 digest 를 $(basename "$DIGEST_OUT") 에 기록 · 대장 대조 일치"; fi
else
  fail "P8 --record-digests <출력.tsv> 를 주지 않았다 — 비교 기준이 없으면 §4.6-④ 를 못 잰다"
fi

echo "════ P9 원인 규명"
if [ "${COLAB_RESTORE_CAUSE:-}" != "" ]; then
  pass "P9 원인 = $COLAB_RESTORE_CAUSE"
else
  fail "P9 COLAB_RESTORE_CAUSE 가 비어 있다. **원인 미상인 채 복원하면 같은 손상이 다시 온다**(S2-BLOCKER-INVESTIGATION §1.4)"
fi

echo "════ P10 보관처에 비밀 사본이 없다 (〈170〉-㉰ · 이름만 본다 · 값은 읽지 않는다)"
OFF="$(backup_dir_offenders)"
if [ -z "$OFF" ]; then pass "P10 보관처에 산출물 규약 밖 파일 0"
else
  printf '%s\n' "$OFF" | while IFS= read -r f; do echo "        ⛔ $(basename "$f")"; done
  fail "P10 보관처에 산출물 규약 밖 파일이 있다 — 비밀 사본일 수 있다. 〈163〉-㉲ 는 비밀 7종을 백업하지 않는다"
fi

echo
if [ "$FAILED" -eq 0 ]; then
  echo "사전조건 GREEN — 복원을 시작해도 된다$([ "${SKIPPED:-0}" -ne 0 ] && echo " (승인된 SKIP ${SKIPPED}건)")"; exit 0
fi
echo "사전조건 RED (실패 ${FAILED}건$([ "${SKIPPED:-0}" -ne 0 ] && echo " · 승인된 SKIP ${SKIPPED}건")) — **복원을 시작하지 않는다**"; exit 1
