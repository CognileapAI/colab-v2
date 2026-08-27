#!/usr/bin/env bash
# 볼륨 아카이브 검사 — fail-closed. **오라클이 이 스크립트의 본체다.**
#
# 왜 `gzip -t` + 크기로 끝내지 않는가:
#   `F2` 가 이미 값으로 보였다 — **빈 gzip 20바이트는 `gzip -t` 를 통과한다.**
#   압축이 멀쩡한 것과 알맹이가 있는 것은 다른 사실이고, 볼륨 아카이브에서는 그 차이가 더 크다.
#   원장 덤프는 `CREATE TABLE` 수·행 수라는 **내부 구조**가 있어 세면 되지만,
#   볼륨은 그냥 바이트 뭉치라 「무엇이 들어 있어야 하는가」의 기준이 아카이브 안에 없다.
#
# 그래서 기준을 **짝 원장 덤프**에서 가져온다.
#   ① tar 시점에 **파일별 매니페스트**(경로·크기·sha256)를 같이 뜬다.
#   ② 짝 덤프의 `d3_file` 에서 `storage_key` 를 뽑는다 — 그것이 「있어야 하는 파일」의 정본이다.
#   ③ **행 수 일치 ＋ 참조 경로 전건 포함**을 본다. 하나라도 빠지면 RED.
#
# 사용: verify-volume-artifact.sh <아카이브.tar.gz> [--pair <원장덤프.sql.gz>] [--skip-age]
# 종료코드: 0 = 전 항목 통과 / 1 = 하나라도 실패 / 2 = 사용법 오류
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
. "$HERE/volume-lib.sh"
load_config
load_volume_config

ART=""; PAIR=""; SKIP_AGE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --pair)      PAIR="${2:-}"; shift 2 ;;
    --skip-age)  SKIP_AGE=1; shift ;;
    -*)          echo "모르는 인자: $1" >&2; exit 2 ;;
    *)           ART="$1"; shift ;;
  esac
done
[ -n "$ART" ] || { echo "사용: verify-volume-artifact.sh <아카이브.tar.gz> [--pair <덤프.sql.gz>] [--skip-age]" >&2; exit 2; }

BASE="${ART%.tar.gz}"
MAN="$BASE.manifest.tsv"
# 볼륨 이름은 파일명에서 읽는다 — `vol-<볼륨>-<stamp>.tar.gz`.
VOL="$(basename "$BASE")"; VOL="${VOL#vol-}"; VOL="${VOL%-*}"
[ -n "$PAIR" ] || { [ -f "$BASE.pair" ] && PAIR="$(cat "$BASE.pair")"; }
# `.pair` 는 파일 이름만 담는다(레포·문서에 절대경로를 적지 않는 관행과 같은 이유).
case "$PAIR" in */*) : ;; "") : ;; *) PAIR="$(dirname "$ART")/$PAIR" ;; esac

MINFILES="$(volume_min_files "$VOL")"
ORACLE="$(volume_oracle "$VOL")"

FAILED=0
echo "검사 대상: $(basename "$ART")  (볼륨 $VOL · 최소 건수 $MINFILES · 오라클 ${ORACLE:-없음})"

# ── V1 존재 · 최소 크기 ──────────────────────────────────────────────────────
if [ ! -f "$ART" ]; then
  fail "V1 아카이브 존재 — 없음"
  echo "결과: RED (실패 1건)"; exit 1
fi
SIZE=$(wc -c < "$ART" | tr -d ' ')
if [ "$SIZE" -ge 1024 ]; then pass "V1 아카이브 존재·크기 ${SIZE}B"; else fail "V1 크기 ${SIZE}B < 1024B (빈 gzip 은 20B 다)"; fi

# ── V2 gzip 무결성 ───────────────────────────────────────────────────────────
# ⚠ **이 항목이 통과해도 아무것도 보증되지 않는다.** F2 가 그것을 fixture 로 박아 뒀다.
if gzip -t "$ART" 2>/dev/null; then pass "V2 gzip 무결성 (이것만으로는 보증이 없다)"; else fail "V2 gzip 무결성 — 손상·절단"; fi

# ── V3 tar 로 열리고 파일 항목이 있다 ────────────────────────────────────────
TARLIST="$(mktemp)"; trap 'rm -f "$TARLIST" "$MANLIST" "$KEYS" "$MANPATHS" 2>/dev/null' EXIT
MANLIST="$(mktemp)"; KEYS="$(mktemp)"; MANPATHS="$(mktemp)"
if tar -tzvf "$ART" > "$TARLIST" 2>/dev/null; then
  # 일반 파일 항목만 센다 — 디렉터리 항목만 잔뜩 있는 아카이브를 「내용 있음」으로 읽지 않는다.
  # `tar -tv` 출력: <권한> <소유자/그룹> <크기> <날짜> <시각> <이름>.
  # 이름에 공백이 있을 수 있으므로(사용자가 올린 격자 파일명) **5번째 필드 뒤 전부**를 이름으로 읽는다.
  # 디렉터리(`d`)·심볼릭 링크(`l`) 항목은 세지 않는다 — 디렉터리만 든 아카이브를 「내용 있음」으로 읽지 않는다.
  awk '$1 ~ /^-/ {
        size=$3; name=$0
        for (i=1; i<=5; i++) { sub(/^[^ ]+ +/, "", name) }
        printf "%s\t%s\n", size, name
      }' "$TARLIST" > "$MANLIST".tar
  NTAR=$(wc -l < "$MANLIST".tar | tr -d ' ')
  if [ "$NTAR" -gt 0 ]; then pass "V3 tar 해제 가능 · 파일 항목 ${NTAR}건"; else fail "V3 파일 항목 0건 — 압축은 멀쩡한데 알맹이가 없다"; fi
else
  fail "V3 tar 로 열리지 않는다"; NTAR=0; : > "$MANLIST".tar
fi

# ── V4 매니페스트 ↔ 아카이브 내용 정합 ───────────────────────────────────────
# 매니페스트는 tar 와 **같은 목록**에서 만들어진다(backup-volume.sh). 그러므로 여기서
# 어긋난다는 것은 ⓐ 매니페스트가 위조됐거나 ⓑ 아카이브가 잘렸거나 ⓒ 파일이 중간에 바뀐 것이다.
# 셋 다 「백업이 됐다」로 읽어서는 안 되는 상태다.
if [ ! -f "$MAN" ]; then
  fail "V4 매니페스트가 없다 ($(basename "$MAN")) — 대조할 기준이 없으면 통과시키지 않는다"
else
  # 매니페스트 형식: 경로<TAB>크기<TAB>sha256
  if awk -F'\t' 'NF!=3 || $2 !~ /^[0-9]+$/ || $3 !~ /^[0-9a-f]{64}$/ {bad++} END{exit (bad>0)}' "$MAN"; then
    NMAN=$(wc -l < "$MAN" | tr -d ' ')
    awk -F'\t' '{print $2"\t"$1}' "$MAN" | LC_ALL=C sort > "$MANLIST"
    awk -F'\t' '{print $1}' "$MAN" | LC_ALL=C sort > "$MANPATHS"
    # tar 쪽 경로는 `./` 접두를 벗겨 매니페스트와 같은 표기로 맞춘다.
    sed 's#\t\./#\t#' "$MANLIST".tar | LC_ALL=C sort > "$MANLIST".tarn
    if [ "$NMAN" -eq "$NTAR" ] && diff -q "$MANLIST" "$MANLIST".tarn >/dev/null 2>&1; then
      pass "V4 매니페스트 ${NMAN}건 = 아카이브 항목 ${NTAR}건 (경로·크기 전건 일치)"
    else
      fail "V4 매니페스트 ${NMAN}건 ≠ 아카이브 ${NTAR}건 또는 경로·크기 불일치"
      diff "$MANLIST" "$MANLIST".tarn 2>/dev/null | head -5 | sed 's/^/        /'
    fi
  else
    fail "V4 매니페스트 형식이 깨졌다 (경로<TAB>크기<TAB>sha256 이 아니다)"
    : > "$MANPATHS"
  fi
fi

# ── V5 오라클 — 짝 원장 덤프의 `d3_file` 과 대조 ─────────────────────────────
# **이 항목이 이 검사기의 존재 이유다.** 크기·gzip 은 「파일이 있다」만 말하고
# 「원장이 가리키는 바이트가 다 들어 있다」는 말하지 않는다.
if [ -z "$ORACLE" ]; then
  echo "  SKIP  V5 오라클 없음 — 이 볼륨은 원장 대조 기준이 없다 (아래 '보증하지 않는 것' 참조)"
elif [ -z "$PAIR" ] || [ ! -f "$PAIR" ]; then
  fail "V5 짝 원장 덤프가 없다 — 오라클을 못 돌리면 통과시키지 않는다 (fail-closed)"
else
  # 덤프의 COPY 블록에서 `storage_key` 열만 뽑는다. 열 위치를 **COPY 헤더에서 읽는다** —
  # 스키마가 바뀌어 열 순서가 달라져도 따라간다. 열이 없으면 지어내지 않고 실패한다.
  gunzip -c "$PAIR" 2>/dev/null | awk -v tbl="$ORACLE" '
    BEGIN{incopy=0; idx=0; found=0}
    incopy==0 && $0 ~ ("^COPY (public\\.)?\"?" tbl "\"? \\(") {
      s=index($0,"("); e=index($0,")");
      cols=substr($0,s+1,e-s-1); gsub(/[ "]/,"",cols);
      n=split(cols,a,",");
      for(i=1;i<=n;i++) if(a[i]=="storage_key") idx=i;
      found=1; incopy=1; next
    }
    incopy==1 && $0=="\\." {incopy=0; next}
    incopy==1 { split($0,f,"\t"); if(idx>0) print f[idx] }
    END{ printf("#META\t%d\t%d\n", found, idx) > "/dev/stderr" }
  ' > "$KEYS" 2> "$KEYS.meta"
  META_FOUND=$(awk -F'\t' '{print $2}' "$KEYS.meta"); META_IDX=$(awk -F'\t' '{print $3}' "$KEYS.meta")
  rm -f "$KEYS.meta"
  if [ "${META_FOUND:-0}" != "1" ]; then
    fail "V5 짝 덤프에 \`$ORACLE\` COPY 블록이 없다 — 원장이 비었거나 덤프가 잘렸다"
  elif [ "${META_IDX:-0}" = "0" ]; then
    fail "V5 \`$ORACLE\` 에 storage_key 열이 없다 — 열 이름을 지어내지 않는다"
  else
    NROW=$(wc -l < "$KEYS" | tr -d ' ')
    LC_ALL=C sort -u "$KEYS" > "$KEYS.u"
    NUNIQ=$(wc -l < "$KEYS.u" | tr -d ' ')
    if [ "$NROW" -eq "$NUNIQ" ]; then
      pass "V5-a 원장 행 수 ${NROW} = 고유 저장키 ${NUNIQ}"
    else
      fail "V5-a 원장 행 ${NROW} ≠ 고유 저장키 ${NUNIQ} — 저장키가 중복이다"
    fi
    # ⚠ 대조 상대는 **매니페스트**다. 매니페스트가 아카이브와 같은 집합이라는 사실은
    #   V4 가 따로 증명한다 — 둘을 한 항목에 섞으면 어느 쪽이 깨졌는지 못 가린다.
    LC_ALL=C comm -23 "$KEYS.u" "$MANPATHS" > "$KEYS.miss"
    NMISS="$(wc -l < "$KEYS.miss" | tr -d ' ')"
    if [ "$NMISS" -eq 0 ] && [ "$NROW" -gt 0 ]; then
      pass "V5-b 원장이 가리키는 ${NUNIQ}건이 **전건** 매니페스트에 있다 (아카이브와의 동일성은 V4)"
    elif [ "$NROW" -eq 0 ]; then
      fail "V5-b 원장 행 0건 — 대조할 것이 없는 상태를 성공으로 읽지 않는다"
    else
      fail "V5-b 원장에 있는데 백업에 없는 파일 ${NMISS}건"
      head -20 "$KEYS.miss" | while IFS= read -r m; do printf '        %s\n' "$m"; done
    fi
    rm -f "$KEYS.miss"
    rm -f "$KEYS.u"
    # 고아 바이트(아카이브에는 있는데 원장에 없는 것)는 **정상이다** — §4.4-㈏.
    NORPH="$(LC_ALL=C comm -13 <(LC_ALL=C sort -u "$KEYS") "$MANPATHS" | wc -l | tr -d ' ')"
    echo "  INFO  아카이브에만 있는 파일 ${NORPH}건 — 덤프 이후 접수분·미리보기 등. 정상이다(§4.4-㈏)"
  fi
fi

# ── V6 최소 건수 (볼륨별 합격선) ─────────────────────────────────────────────
if [ "$NTAR" -ge "$MINFILES" ]; then pass "V6 파일 ${NTAR}건 (>= $MINFILES)"; else fail "V6 파일 ${NTAR}건 < $MINFILES — 거의 빈 아카이브다"; fi

# ── V7 신선도 ────────────────────────────────────────────────────────────────
if [ "$SKIP_AGE" -eq 1 ]; then
  echo "  SKIP  V7 신선도 (--skip-age) — 사고 복원은 옛 산출물을 쓴다"
else
  NOW=$(date +%s); MT=$(date -r "$ART" +%s 2>/dev/null || echo 0)
  AGE_MIN=$(( (NOW - MT) / 60 ))
  if [ "$AGE_MIN" -le "$COLAB_VOLBACKUP_MAX_AGE_MIN" ]; then pass "V7 신선도 ${AGE_MIN}분 (<= $COLAB_VOLBACKUP_MAX_AGE_MIN)"; else fail "V7 신선도 ${AGE_MIN}분 > $COLAB_VOLBACKUP_MAX_AGE_MIN — 옛 잔존 파일이다"; fi
fi

if [ "$FAILED" -eq 0 ]; then echo "결과: GREEN"; exit 0; else echo "결과: RED (실패 ${FAILED}건)"; exit 1; fi
