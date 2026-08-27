#!/usr/bin/env bash
# 볼륨 백업 fail-closed 증명 — `selftest.sh` 와 **같은 형태**다.
# 각 fixture 는 **반드시 RED 를 내야 한다.** 하나라도 GREEN 이면 이 셀프테스트가 실패한다.
#
# ⭑ **docker 를 쓰지 않는다.** 검사기(`verify-volume-artifact.sh`)가 산출물 파일만 보고
#   판정하도록 만들었기 때문이다 — 그래서 살아 있는 staging 없이도 전건이 실제로 돈다.
#   `selftest.sh` 의 F8·F9 가 docker 부재로 「증명 미완」이 되던 자리를 여기서는 만들지 않았다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
BAD=0; RAN=0
export COLAB_BACKUP_CONFIG="$W/vol.env"
cat > "$COLAB_BACKUP_CONFIG" <<'CFG'
COLAB_BACKUP_TARGET=postgres
COLAB_VOLBACKUP_MIN_FILES_uploads=3
COLAB_VOLBACKUP_MIN_FILES_previews=1
COLAB_VOLBACKUP_ORACLE_uploads=d3_file
COLAB_VOLBACKUP_ORACLE_previews=none
CFG

expect_red() { # $1=이름 $2...=명령
  local name="$1"; shift
  RAN=$((RAN+1)); echo "──────── $name"
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  echo "$out" | sed 's/^/    /'
  if [ $rc -ne 0 ]; then echo "  → 기대대로 RED (exit $rc)"
  else echo "  → ✗ GREEN 이 나왔다. fail-closed 아님."; BAD=$((BAD+1)); fi
}

# ── 재료 ─────────────────────────────────────────────────────────────────────
# 짝 원장 덤프. `d3_file` COPY 블록의 열 목록까지 pg_dump 형태 그대로 흉내낸다 —
# 검사기가 **열 위치를 헤더에서 읽기** 때문에, 열을 하나 끼워 넣어도 따라가야 한다.
make_dump() { # $1=출력.gz  $2...=저장키들
  local out="$1"; shift
  { echo "-- PostgreSQL database dump"
    echo "COPY public.d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key, created_at, carries_lat, carries_lon) FROM stdin;"
    local i=0 k
    for k in "$@"; do i=$((i+1))
      printf 'ID%03d\tLAB\tDS\t본체\tf%d\t10\t%s\t2026-08-27 00:00:00+00\tf\tf\n' "$i" "$i" "$k"
    done
    echo '\.'
  } | gzip -c > "$out"
}

# 볼륨 트리 → 매니페스트 ＋ tar (backup-volume.sh 가 하는 것과 **같은 순서**로 만든다)
make_archive() { # $1=트리 $2=출력base
  local tree="$1" base="$2"
  ( cd "$tree" && find . -type f -print | LC_ALL=C sort | while IFS= read -r f; do
      printf '%s\t%s\t%s\n' "${f#./}" "$(wc -c < "$f" | tr -d ' ')" "$(sha256sum "$f" | cut -d' ' -f1)"
    done ) > "$base.manifest.tsv"
  awk -F'\t' '{print "./" $1}' "$base.manifest.tsv" > "$base.list"
  tar -czf "$base.tar.gz" -C "$tree" -T "$base.list"
  rm -f "$base.list"
}

TREE="$W/vol"
mkdir -p "$TREE/uploads/DS1" "$TREE/uploads/DS1/grid"
head -c 4000 /dev/urandom > "$TREE/uploads/DS1/F001"
head -c 4000 /dev/urandom > "$TREE/uploads/DS1/F002"
head -c 4000 /dev/urandom > "$TREE/uploads/DS1/grid/LAT 위도.npy"   # 공백 있는 이름 — 실제로 온다
head -c 4000 /dev/urandom > "$TREE/uploads/DS1/ORPHAN"             # 원장에 없는 고아 바이트

K1=uploads/DS1/F001; K2=uploads/DS1/F002; K3="uploads/DS1/grid/LAT 위도.npy"
make_dump "$W/platform-good.sql.gz" "$K1" "$K2" "$K3"

echo "════ 대조군 (RED 가 아니어야 한다)"
make_archive "$TREE" "$W/vol-uploads-20260827T000000"
GOOD="$W/vol-uploads-20260827T000000.tar.gz"
if "$HERE/verify-volume-artifact.sh" "$GOOD" --pair "$W/platform-good.sql.gz" >/dev/null 2>&1; then
  echo "  대조군 GREEN — 검사기는 정상본을 통과시킨다 (고아 바이트 1건이 있어도)"
else
  echo "  ✗ 대조군이 RED 다. 검사기가 무조건 red 를 내고 있다 — 증명이 성립하지 않는다"
  "$HERE/verify-volume-artifact.sh" "$GOOD" --pair "$W/platform-good.sql.gz" 2>&1 | sed 's/^/    /'
  BAD=$((BAD+1))
fi

echo; echo "════ fixture — 전부 RED 여야 한다"

# VF1 0바이트 아카이브
: > "$W/vol-uploads-20260827T000001.tar.gz"
expect_red "VF1 0바이트 아카이브" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260827T000001.tar.gz" --pair "$W/platform-good.sql.gz"

# VF2 빈 gzip 20바이트 — **`gzip -t` 를 통과한다.** F2 가 원장 쪽에서 보인 것과 같은 실물 형태다.
printf '' | gzip -c > "$W/vol-uploads-20260827T000002.tar.gz"
: > "$W/vol-uploads-20260827T000002.manifest.tsv"
expect_red "VF2 빈 gzip 20B (V2 는 통과하고 V3·V5 가 잡는다)" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260827T000002.tar.gz" --pair "$W/platform-good.sql.gz"

# VF3 절단된 아카이브
head -c $(( $(wc -c < "$GOOD") / 2 )) "$GOOD" > "$W/vol-uploads-20260827T000003.tar.gz"
cp "$W/vol-uploads-20260827T000000.manifest.tsv" "$W/vol-uploads-20260827T000003.manifest.tsv"
expect_red "VF3 절단·손상 아카이브" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260827T000003.tar.gz" --pair "$W/platform-good.sql.gz"

# VF4 매니페스트 없음 — 대조 기준이 없으면 통과시키지 않는다
cp "$GOOD" "$W/vol-uploads-20260827T000004.tar.gz"
expect_red "VF4 매니페스트가 없다 (기준 없는 산출물을 통과시키지 않는다)" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260827T000004.tar.gz" --pair "$W/platform-good.sql.gz"

# ⭑ VF5 — **이 WU 의 핵심 fixture.**
#   `d3_file` 이 가리키는 파일 하나가 아카이브에 없다. 크기·gzip·항목 수는 전부 멀쩡하다.
#   크기·`gzip -t` 만 보는 가드는 이것을 **통과시킨다** — 그것이 F2 의 약점이었다.
TREE5="$W/vol5"; cp -r "$TREE" "$TREE5"; rm -f "$TREE5/uploads/DS1/F002"
make_archive "$TREE5" "$W/vol-uploads-20260827T000005"
expect_red "VF5 원장(d3_file)에 있는 파일이 아카이브에 없다 — 오라클이 잡는다" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260827T000005.tar.gz" --pair "$W/platform-good.sql.gz"

# VF6 매니페스트만 그 파일을 담고 있다 (매니페스트 위조) → V4 집합 불일치
cp "$W/vol-uploads-20260827T000005.tar.gz" "$W/vol-uploads-20260827T000006.tar.gz"
cp "$W/vol-uploads-20260827T000000.manifest.tsv" "$W/vol-uploads-20260827T000006.manifest.tsv"
expect_red "VF6 매니페스트에는 있고 아카이브에는 없다 (매니페스트 위조)" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260827T000006.tar.gz" --pair "$W/platform-good.sql.gz"

# VF7 파일이 절단됐다 — 경로는 전건 있는데 크기가 다르다
TREE7="$W/vol7"; cp -r "$TREE" "$TREE7"
make_archive "$TREE7" "$W/vol-uploads-20260827T000007"
head -c 10 "$TREE7/uploads/DS1/F001" > "$TREE7/uploads/DS1/F001.t" && mv "$TREE7/uploads/DS1/F001.t" "$TREE7/uploads/DS1/F001"
tar -czf "$W/vol-uploads-20260827T000007.tar.gz" -C "$TREE7" \
  ./uploads/DS1/F001 ./uploads/DS1/F002 "./uploads/DS1/grid/LAT 위도.npy" ./uploads/DS1/ORPHAN
expect_red "VF7 아카이브 안 파일이 절단됐다 (경로는 맞고 크기가 다르다)" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260827T000007.tar.gz" --pair "$W/platform-good.sql.gz"

# VF8 짝 원장 덤프가 없다 — 오라클을 못 돌리면 통과가 아니다
cp "$GOOD" "$W/vol-uploads-20260827T000008.tar.gz"
cp "$W/vol-uploads-20260827T000000.manifest.tsv" "$W/vol-uploads-20260827T000008.manifest.tsv"
expect_red "VF8 짝 원장 덤프 없음 (fail-closed — 모르는 것을 통과로 읽지 않는다)" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260827T000008.tar.gz"

# VF9 원장에 `d3_file` COPY 블록이 아예 없다 (덤프가 잘렸거나 원장이 비었다)
{ echo "-- PostgreSQL database dump"; for i in $(seq 1 200); do echo "SET statement_timeout = 0;"; done; } | gzip -c > "$W/platform-empty.sql.gz"
cp "$GOOD" "$W/vol-uploads-20260827T000009.tar.gz"
cp "$W/vol-uploads-20260827T000000.manifest.tsv" "$W/vol-uploads-20260827T000009.manifest.tsv"
expect_red "VF9 짝 덤프에 d3_file 블록이 없다" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260827T000009.tar.gz" --pair "$W/platform-empty.sql.gz"

# VF10 볼륨별 합격선 미달 — `F9` 가 원장 프로파일에 세운 것과 같은 성질
TREE10="$W/vol10"; mkdir -p "$TREE10/uploads/DS1"
head -c 4000 /dev/urandom > "$TREE10/uploads/DS1/F001"
make_archive "$TREE10" "$W/vol-uploads-20260827T000010"
make_dump "$W/platform-one.sql.gz" "uploads/DS1/F001"
expect_red "VF10 파일 1건 < 합격선 3 (볼륨별 합격선)" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260827T000010.tar.gz" --pair "$W/platform-one.sql.gz"

# VF11 신선도 — 옛 아카이브가 「오늘의 백업」이 아니다
cp "$GOOD" "$W/vol-uploads-20260820T000000.tar.gz"
cp "$W/vol-uploads-20260827T000000.manifest.tsv" "$W/vol-uploads-20260820T000000.manifest.tsv"
touch -d '8 days ago' "$W/vol-uploads-20260820T000000.tar.gz"
expect_red "VF11 8일 된 아카이브 (신선도)" \
  "$HERE/verify-volume-artifact.sh" "$W/vol-uploads-20260820T000000.tar.gz" --pair "$W/platform-good.sql.gz"

# VF12 대상 미연결에서 전범위 백업이 성공하지 않는다 — 그리고 **볼륨을 뜨지 않는다**
cat > "$W/none.env" <<CFG
COLAB_BACKUP_TARGET=none
COLAB_BACKUP_DIR=$W/none-out
CFG
mkdir -p "$W/none-out"
expect_red "VF12 TARGET=none 에서 backup-full.sh (원장 실패 → 볼륨 미실행)" \
  env COLAB_BACKUP_CONFIG="$W/none.env" "$HERE/backup-full.sh"
RAN=$((RAN+1))
echo "──────── VF12b 원장이 실패했을 때 볼륨 산출물이 생기지 않았다"
if [ -z "$(ls -A "$W/none-out" 2>/dev/null)" ]; then
  echo "  → 기대대로: 보관처에 아무것도 없다"
else
  echo "  → ✗ 원장이 실패했는데 산출물이 남았다"; BAD=$((BAD+1))
fi

# VF13 짝 없이 볼륨 백업을 부를 수 없다
expect_red "VF13 --pair 없이 backup-volume.sh (짝 없는 아카이브를 만들지 않는다)" \
  env COLAB_BACKUP_CONFIG="$COLAB_BACKUP_CONFIG" "$HERE/backup-volume.sh"

# ══ 〈170〉-㉮ green-by-skip 회귀 fixture ══════════════════════════════════════
#    `R-1` 1회차가 실물로 잡은 실패: 실 설정에 오라클 키가 없어 V5 가 SKIP 됐는데
#    상위 요약줄은 「원장 오라클 포함 GREEN」이었다. 아래 넷이 그 형태를 못 돌아오게 박는다.

# VF14 **오라클 미선언 볼륨은 RED 다** — 조용한 SKIP 이 아니다.
#      `uploads`·`previews` 는 volume-lib 이 기본값을 쥐므로, 선언이 없는 상태를 재현하려면
#      기본값이 없는 **새 볼륨 이름**을 써야 한다. 새 볼륨을 오라클 없이 추가하는 상황 그 자체다.
TREE14="$W/vol14"; mkdir -p "$TREE14/uploads/DS1"
head -c 4000 /dev/urandom > "$TREE14/uploads/DS1/F001"
make_archive "$TREE14" "$W/vol-fixturevol-20260827T000014"
cat > "$W/undeclared.env" <<CFG
COLAB_BACKUP_TARGET=postgres
COLAB_VOLBACKUP_VOLUMES="fixturevol"
COLAB_VOLBACKUP_MIN_FILES_fixturevol=1
CFG
expect_red "VF14 오라클 미선언 볼륨 — 선언 없는 것을 통과로 읽지 않는다 (〈170〉-㉮)" \
  env COLAB_BACKUP_CONFIG="$W/undeclared.env" \
      "$HERE/verify-volume-artifact.sh" "$W/vol-fixturevol-20260827T000014.tar.gz" --pair "$W/platform-one.sql.gz"

# VF15 **배선 회귀** — 설정 파일에 오라클 키가 하나도 없어도 `uploads` 의 V5 는 **돌아야** 한다.
#      1회차의 실 설정이 정확히 이 모양이었다. 기본값이 코드에 있으므로 이제 SKIP 되지 않는다.
cat > "$W/nokeys.env" <<CFG
COLAB_BACKUP_TARGET=postgres
CFG
RAN=$((RAN+1)); echo "──────── VF15 오라클 키 없는 설정에서도 uploads V5 가 실제로 돈다 (〈170〉-㉮ 배선)"
OUT15="$(env COLAB_BACKUP_CONFIG="$W/nokeys.env" "$HERE/verify-volume-artifact.sh" "$GOOD" --pair "$W/platform-good.sql.gz" 2>&1)"
if echo "$OUT15" | grep -q 'V5-b' && ! echo "$OUT15" | grep -q 'SKIP  V5'; then
  echo "  → 기대대로: V5 가 돌았다 (오라클 기본값이 코드에 있다)"
else
  echo "  → ✗ 설정 키가 없자 V5 가 다시 꺼졌다 — green-by-skip 회귀"; echo "$OUT15" | sed 's/^/    /'; BAD=$((BAD+1))
fi

# VF16 **SKIP 은 요약줄에 반드시 드러난다** — 명시 면제(none)라도 「그냥 GREEN」이라 적지 않는다.
TREE16="$W/vol16"; mkdir -p "$TREE16/previews"
for i in 1 2 3; do head -c 4000 /dev/urandom > "$TREE16/previews/P$i"; done
make_archive "$TREE16" "$W/vol-previews-20260827T000016"
cat > "$W/prev.env" <<CFG
COLAB_BACKUP_TARGET=postgres
COLAB_VOLBACKUP_MIN_FILES_previews=1
CFG
RAN=$((RAN+1)); echo "──────── VF16 명시 면제(none) 볼륨의 요약줄에 SKIP 건수가 실린다"
OUT16="$(env COLAB_BACKUP_CONFIG="$W/prev.env" "$HERE/verify-volume-artifact.sh" "$W/vol-previews-20260827T000016.tar.gz" --pair "$W/platform-good.sql.gz" 2>&1)"
if echo "$OUT16" | tail -1 | grep -q '승인된 SKIP'; then
  echo "  → 기대대로: $(echo "$OUT16" | tail -1)"
else
  echo "  → ✗ SKIP 이 있는데 요약줄이 숨겼다"; echo "$OUT16" | tail -3 | sed 's/^/    /'; BAD=$((BAD+1))
fi

# ══ 〈170〉-㉰ 비밀 사본 회귀 fixture ═════════════════════════════════════════
# VF17 보관처에 비밀 모양 파일이 있으면 **전범위 백업이 시작조차 안 한다**.
#      `R-1` 1회차에 보관처에서 나온 `subjects-*.json` 이 그 실물이다.
#      ⚠ 이 fixture 는 **비밀이 아닌 더미 내용**을 쓴다. 이름 모양만 같으면 걸리는 것이 요점이다.
mkdir -p "$W/secret-out"
echo 'DUMMY-NOT-A-SECRET' > "$W/secret-out/subjects-20260827T000000.json"
cat > "$W/secret.env" <<CFG
COLAB_BACKUP_TARGET=postgres
COLAB_BACKUP_DIR=$W/secret-out
CFG
expect_red "VF17 보관처에 subjects-*.json 이 있으면 backup-full.sh 가 선다 (〈170〉-㉰)" \
  env COLAB_BACKUP_CONFIG="$W/secret.env" "$HERE/backup-full.sh"

# VF18 이름 모양 판정기 자체 — 비밀 7종의 모양이 전건 잡히고, 산출물 이름은 안 잡힌다.
RAN=$((RAN+1)); echo "──────── VF18 secret_shaped 판정 (비밀 7종 모양 전건 · 산출물 오탐 0)"
VF18=0
. "$HERE/lib.sh"
for n in subjects.json subjects-20260827T051347.json credentials.json core.env .env \
         COLAB_STAGING_CORE_DB_URL core-db-url.txt id_rsa server.key tls.pem api-token.txt; do
  secret_shaped "$n" || { echo "  ✗ 비밀 모양인데 못 잡았다: $n"; VF18=1; }
done
for n in platform-20260827T171801.sql.gz vol-uploads-20260827T171801.tar.gz \
         vol-uploads-20260827T171801.manifest.tsv vol-uploads-20260827T171801.pair; do
  secret_shaped "$n" && { echo "  ✗ 산출물을 비밀로 오판했다: $n"; VF18=1; }
done
if [ "$VF18" -eq 0 ]; then echo "  → 기대대로: 비밀 모양 11건 전건 적중 · 산출물 4건 오탐 0"
else BAD=$((BAD+1)); fi

echo
if [ "$BAD" -eq 0 ]; then
  echo "볼륨 셀프테스트 GREEN — fixture $RAN 건 전부 기대대로 RED"
  exit 0
else
  echo "볼륨 셀프테스트 RED — $BAD 건이 fail-closed 가 아니다"
  exit 1
fi
