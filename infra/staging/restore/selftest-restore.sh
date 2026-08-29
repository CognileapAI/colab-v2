#!/usr/bin/env bash
# 복원 기구 fail-closed 증명 — `backup/selftest.sh` 와 같은 형태.
# 각 fixture 는 **반드시 RED 를 내야 한다.** docker·DB 없이 전건이 실제로 돈다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
BAD=0; RAN=0

expect_red() { local name="$1"; shift; RAN=$((RAN+1)); echo "──────── $name"
  local out rc; out="$("$@" 2>&1)"; rc=$?; echo "$out" | sed 's/^/    /'
  if [ $rc -ne 0 ]; then echo "  → 기대대로 RED (exit $rc)"; else echo "  → ✗ GREEN. fail-closed 아님."; BAD=$((BAD+1)); fi; }

# ── 재료: 기대치를 담은 덤프 ────────────────────────────────────────────────
{ echo "-- dump"
  echo "COPY public.d3_dataset (id, lab_id) FROM stdin;"
  for i in $(seq 1 12); do echo "D$i	L"; done; echo '\.'
  echo "COPY public.d4_lineage_edge (id) FROM stdin;"
  for i in $(seq 1 6); do echo "E$i"; done; echo '\.'
} | gzip -c > "$W/platform.sql.gz"

echo "════ 대조군 (RED 가 아니어야 한다)"
GOT="$("$HERE/expectations.sh" "$W/platform.sql.gz" d3_dataset d4_lineage_edge 2>/dev/null)"
if [ "$GOT" = "$(printf 'd3_dataset\t12\nd4_lineage_edge\t6')" ]; then
  echo "  대조군 GREEN — 기대치를 덤프에서 읽었다 (12 · 6). **상수를 박지 않았다는 증거다**"
else
  echo "  ✗ 대조군 실패: [$GOT]"; BAD=$((BAD+1))
fi
# ⭑ 같은 스크립트가 다른 회차의 덤프에는 다른 값을 낸다 — 그것이 「기대치이지 상수가 아니다」의 실증이다.
{ echo "COPY public.d4_lineage_edge (id) FROM stdin;"; for i in $(seq 1 9); do echo "E$i"; done; echo '\.'; } | gzip -c > "$W/other.sql.gz"
RAN=$((RAN+1)); echo "──────── SR0 다른 회차 덤프는 다른 기대치를 낸다 (상수가 아님의 실증)"
if [ "$("$HERE/expectations.sh" "$W/other.sql.gz" d4_lineage_edge | cut -f2)" = "9" ]; then
  echo "  → 기대대로: 같은 스크립트가 9 를 냈다"
else echo "  → ✗ 값이 따라오지 않는다"; BAD=$((BAD+1)); fi

echo; echo "════ fixture — 전부 RED 여야 한다"

expect_red "SR1 덤프에 그 테이블 COPY 블록이 없다 (기대치를 지어내지 않는다)" \
  "$HERE/expectations.sh" "$W/platform.sql.gz" d3_file
expect_red "SR2 덤프 파일 자체가 없다" \
  "$HERE/expectations.sh" "$W/missing.sql.gz" d3_dataset

# ── digest 대조 ──────────────────────────────────────────────────────────────
cat > "$W/ledger.md" <<'MD'
| 이미지 | digest |
|---|---|
| `colab-v2/core-api:i2` | `sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` |
| `colab-v2/frontend:i2` | `sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb` |
MD
cat > "$W/inspect-ok" <<'SH'
#!/bin/sh
case "$1" in
  colab-v2/core-api:i2) echo "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" ;;
  colab-v2/frontend:i2) echo "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" ;;
esac
SH
cat > "$W/inspect-drift" <<'SH'
#!/bin/sh
case "$1" in
  colab-v2/core-api:i2) echo "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc" ;;
  colab-v2/frontend:i2) echo "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" ;;
esac
SH
cat > "$W/inspect-none" <<'SH'
#!/bin/sh
exit 0
SH
chmod +x "$W/inspect-ok" "$W/inspect-drift" "$W/inspect-none"

RAN=$((RAN+1)); echo "──────── SR3 대조군 — 대장과 실측이 같으면 GREEN"
if COLAB_DIGEST_INSPECT="$W/inspect-ok" "$HERE/check-image-digests.sh" --ledger "$W/ledger.md" >/dev/null 2>&1; then
  echo "  → 기대대로 GREEN"
else echo "  → ✗ 같은데 RED 다"; BAD=$((BAD+1)); fi

expect_red "SR4 태그는 같은데 digest 가 다르다 (〈153〉 사고의 형태)" \
  env COLAB_DIGEST_INSPECT="$W/inspect-drift" "$HERE/check-image-digests.sh" --ledger "$W/ledger.md"
expect_red "SR5 이미지가 호스트에 없다 — 미측정을 일치로 읽지 않는다" \
  env COLAB_DIGEST_INSPECT="$W/inspect-none" "$HERE/check-image-digests.sh" --ledger "$W/ledger.md"
expect_red "SR6 대장에서 digest 행을 못 읽었다 (표 형식이 바뀌었다)" \
  env COLAB_DIGEST_INSPECT="$W/inspect-ok" "$HERE/check-image-digests.sh" --ledger "$W/inspect-ok"

# ── 복원 스크립트의 문 ───────────────────────────────────────────────────────
expect_red "SR7 --yes-drop-schema 없이 restore-db.sh" \
  "$HERE/restore-db.sh" --db colab_platform --owner owner --dump "$W/platform.sql.gz"
expect_red "SR8 COLAB_RESTORE_PRE_BACKUP 없이 restore-db.sh (되돌림의 되돌림 재료 없음)" \
  env COLAB_RESTORE_PRE_BACKUP= "$HERE/restore-db.sh" --db colab_platform --owner owner \
      --dump "$W/platform.sql.gz" --yes-drop-schema
expect_red "SR9 --yes-overwrite-volume 없이 restore-volume.sh" \
  "$HERE/restore-volume.sh" --volume uploads --archive "$W/platform.sql.gz"

# ── 보관처 위생 (〈170〉-㉰) — `preflight` P10 이 쓰는 판정기 자체를 건다.
#    허용 목록 방식이라 「아직 생각 못 한 모양의 비밀」도 걸린다는 성질을 여기서 값으로 보인다.
RAN=$((RAN+1)); echo "──────── SR10 보관처 허용 목록 — 산출물은 통과 · 규약 밖 파일은 적발"
. "$HERE/../backup/lib.sh"
D="$W/store"; mkdir -p "$D"
: > "$D/platform-20260827T171801.sql.gz"; : > "$D/platform-20260827T171801.sql.gz.sha256"
: > "$D/vol-uploads-20260827T171801.tar.gz"; : > "$D/vol-uploads-20260827T171801.manifest.tsv"
: > "$D/vol-uploads-20260827T171801.pair"; : > "$D/.inflight-platform-20260827T180000.sql.gz"
if [ -z "$(backup_dir_offenders "$D")" ]; then
  echo "  → 산출물만 있는 보관처: 적발 0 (오탐 없음)"
  echo 'DUMMY-NOT-A-SECRET' > "$D/subjects-20260827T051347.json"
  echo 'DUMMY' > "$D/무엇인지-모를-파일.txt"
  N="$(backup_dir_offenders "$D" | wc -l | tr -d ' ')"
  if [ "$N" = "2" ]; then echo "  → 기대대로: 비밀 모양 1건 ＋ 규약 밖 1건 = 2건 적발"
  else echo "  → ✗ 적발 $N 건 (기대 2)"; BAD=$((BAD+1)); fi
else
  echo "  → ✗ 산출물을 규약 밖으로 오판했다"; backup_dir_offenders "$D" | sed 's/^/    /'; BAD=$((BAD+1))
fi

# ── 회차 짝짓기 (`preflight` P2/P5-b) ─────────────────────────────────────────
# ⭑ 재현하는 결함 = 원장과 볼륨을 **각각 독립으로 「최신」** 으로 고르던 것(`R1-TAILS-EXEC §2.1`).
#   원장 전용 백업이 볼륨보다 뒤에 뜬 실물 상태를 그대로 픽스처로 만든다 —
#   ledger-only 회차 `…T100801` 가 최신이고, 볼륨이 딸린 회차는 `…T033005` 다.
#   볼륨 둘의 스탬프는 **35초 차**(033005 / 033040)라 `--stamp` 하나로는 못 잡는다.
mk_store() { # $1=보관처  $2=회차스탬프  $3=uploads스탬프  $4=previews스탬프("" 면 안 만든다)
  local d="$1" r="$2"
  mkdir -p "$d"
  local R="platform-$r.sql.gz"
  for f in "platform-$r.sql.gz" "ai-$r.sql.gz"; do : > "$d/$f"; sha256sum "$d/$f" | awk '{print $1}' > "$d/$f.sha256"; done
  if [ -n "$3" ]; then
    : > "$d/vol-uploads-$3.tar.gz"; sha256sum "$d/vol-uploads-$3.tar.gz" | awk '{print $1}' > "$d/vol-uploads-$3.tar.gz.sha256"
    : > "$d/vol-uploads-$3.manifest.tsv"; printf '%s' "$R" > "$d/vol-uploads-$3.pair"
  fi
  if [ -n "$4" ]; then
    : > "$d/vol-previews-$4.tar.gz"; sha256sum "$d/vol-previews-$4.tar.gz" | awk '{print $1}' > "$d/vol-previews-$4.tar.gz.sha256"
    : > "$d/vol-previews-$4.manifest.tsv"; printf '%s' "$R" > "$d/vol-previews-$4.pair"
  fi
}
mk_cfg() { # $1=cfg경로  $2=보관처  $3=볼륨목록
  cat > "$1" <<CFG
COLAB_BACKUP_DIR=$2
COLAB_BACKUP_PROFILES="platform ai"
COLAB_VOLBACKUP_VOLUMES="$3"
CFG
}
pf() { COLAB_BACKUP_CONFIG="$1" "$HERE/preflight.sh" "${@:2}" 2>&1; }

# SR11 — 원장 전용 최신 회차가 있어도 **볼륨이 딸린 회차**를 고른다
S="$W/rt1"; mk_store "$S" 20260829T033005 20260829T033005 20260829T033040
: > "$S/platform-20260829T100801.sql.gz"; sha256sum "$S/platform-20260829T100801.sql.gz" | awk '{print $1}' > "$S/platform-20260829T100801.sql.gz.sha256"
: > "$S/ai-20260829T100801.sql.gz";       sha256sum "$S/ai-20260829T100801.sql.gz"       | awk '{print $1}' > "$S/ai-20260829T100801.sql.gz.sha256"
touch "$S/platform-20260829T100801.sql.gz" "$S/ai-20260829T100801.sql.gz"
mk_cfg "$W/cfg1.env" "$S" "uploads previews"
RAN=$((RAN+1)); echo "──────── SR11 원장·볼륨을 회차로 묶어 고른다 (독립 「최신」 금지)"
O="$(pf "$W/cfg1.env")"
if echo "$O" | grep -q 'P2 platform = platform-20260829T033005.sql.gz' \
   && echo "$O" | grep -q 'P2 볼륨 previews = vol-previews-20260829T033040.tar.gz' \
   && ! echo "$O" | grep -q 'P5-b .*≠'; then
  echo "  → 기대대로: 회차 platform-20260829T033005.sql.gz 로 네 산출물이 한 벌로 잡혔다"
else
  echo "  → ✗ 짝이 어긋났다"; echo "$O" | grep -E 'P2 |P5-b ' | sed 's/^/    /'; BAD=$((BAD+1))
fi

# SR12 — **성립하는 회차가 없으면 RED.** 관대한 기본값으로 떨어지지 않는다
S="$W/rt2"; mkdir -p "$S"
for f in platform-20260829T100801.sql.gz ai-20260829T100801.sql.gz; do : > "$S/$f"; sha256sum "$S/$f" | awk '{print $1}' > "$S/$f.sha256"; done
mk_cfg "$W/cfg2.env" "$S" "uploads previews"
expect_red "SR12 짝이 맞는 회차가 하나도 없다 — 「최신」으로 떨어지지 않고 RED" \
  env COLAB_BACKUP_CONFIG="$W/cfg2.env" "$HERE/preflight.sh"
RAN=$((RAN+1)); echo "──────── SR12-b 그 RED 가 **회차 부재를 이름으로** 말한다"
O="$(pf "$W/cfg2.env")"
if echo "$O" | grep -q 'P2 짝이 맞는 회차가 없다'; then echo "  → 기대대로"
else echo "  → ✗ 회차 부재를 말하지 않는다"; BAD=$((BAD+1)); fi

# SR13 — 회차 편입 **선언이 없는 볼륨**은 RED (새 볼륨을 선언 없이 추가한 모양)
S="$W/rt3"; mk_store "$S" 20260829T033005 20260829T033005 20260829T033040
mk_cfg "$W/cfg3.env" "$S" "uploads previews scratch"
expect_red "SR13 회차 편입 선언이 없는 볼륨(scratch) — 조용히 넘기지 않는다" \
  env COLAB_BACKUP_CONFIG="$W/cfg3.env" "$HERE/preflight.sh"
RAN=$((RAN+1)); echo "──────── SR13-b 그 RED 가 **선언 부재를 이름으로** 말한다"
O="$(pf "$W/cfg3.env")"
if echo "$O" | grep -q 'scratch 의 회차 편입 선언이 없다'; then echo "  → 기대대로"
else echo "  → ✗ 선언 부재를 말하지 않는다"; BAD=$((BAD+1)); fi

# SR14 — **명시적 면제는 통과하되 건수를 드러낸다** (세 상태의 가운데)
S="$W/rt4"; mk_store "$S" 20260829T033005 20260829T033005 ""
mk_cfg "$W/cfg4.env" "$S" "uploads previews"
echo 'COLAB_VOLBACKUP_PAIRING_previews=none' >> "$W/cfg4.env"
RAN=$((RAN+1)); echo "──────── SR14 명시 면제된 볼륨은 SKIP 되고 **요약줄에 건수가 나온다**"
O="$(pf "$W/cfg4.env")"
if echo "$O" | grep -q 'SKIP  P2 볼륨 previews 는 회차 편입에서 명시 면제' \
   && echo "$O" | grep -q 'SKIP  P5-b 볼륨 previews' \
   && echo "$O" | grep -qE '승인된 SKIP [0-9]+건'; then
  echo "  → 기대대로: 면제는 통과하되 **무엇을 안 봤는지**가 요약줄에 남는다"
else
  echo "  → ✗ 면제가 숨었다"; echo "$O" | grep -E 'SKIP|사전조건' | sed 's/^/    /'; BAD=$((BAD+1))
fi

echo
if [ "$BAD" -eq 0 ]; then echo "복원 셀프테스트 GREEN — fixture $RAN 건 전부 기대대로"; exit 0; fi
echo "복원 셀프테스트 RED — $BAD 건이 fail-closed 가 아니다"; exit 1
