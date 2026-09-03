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

# 배포 목록의 정본 = compose 의 `image:`. 이 픽스처 묶음의 대장은 두 줄뿐이므로 compose 도 두 줄이다 —
# 검사 범위를 줄인 것이 아니라 **대장과 배포 목록을 같은 세계로 맞춘 것**이다(범위 불일치는 SR15 가 따로 잡는다).
cat > "$W/compose-2.yml" <<'YML'
services:
  a:
    image: colab-v2/core-api:${COLAB_RELEASE_TAG:?필요}
  b:
    image: colab-v2/frontend:${COLAB_RELEASE_TAG:?필요}
YML
# 자체 빌드 이미지의 기대값은 이제 **`§5` 원장**에서 온다(`〈297〉`). 두 회차를 쌓아 두고
# 「지금 서빙 중」을 실측 digest 로 고르게 한다 — 롤백으로 별칭이 옛 회차를 가리켜도 같은 규칙으로 잡힌다.
{ printf '2026-09-01T00:00:00+0900\trel00000000\ti2\tcolab-v2/core-api\t%s\n' "sha256:9999999999999999999999999999999999999999999999999999999999999999"
  printf '2026-09-01T00:00:00+0900\trel00000000\ti2\tcolab-v2/frontend\t%s\n' "sha256:9999999999999999999999999999999999999999999999999999999999999999"
  printf '2026-09-02T00:00:00+0900\trel11111111\ti2\tcolab-v2/core-api\t%s\n' "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  printf '2026-09-02T00:00:00+0900\trel11111111\ti2\tcolab-v2/frontend\t%s\n' "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
} > "$W/dledger.tsv"
DG=(--compose "$W/compose-2.yml" --digest-ledger "$W/dledger.tsv")

RAN=$((RAN+1)); echo "──────── SR3 대조군 — 대장과 실측이 같으면 GREEN"
if COLAB_DIGEST_INSPECT="$W/inspect-ok" "$HERE/check-image-digests.sh" --ledger "$W/ledger.md" "${DG[@]}" >/dev/null 2>&1; then
  echo "  → 기대대로 GREEN"
else echo "  → ✗ 같은데 RED 다"; BAD=$((BAD+1)); fi

expect_red "SR4 태그는 같은데 digest 가 다르다 (〈153〉 사고의 형태)" \
  env COLAB_DIGEST_INSPECT="$W/inspect-drift" "$HERE/check-image-digests.sh" --ledger "$W/ledger.md" "${DG[@]}"
expect_red "SR5 이미지가 호스트에 없다 — 미측정을 일치로 읽지 않는다" \
  env COLAB_DIGEST_INSPECT="$W/inspect-none" "$HERE/check-image-digests.sh" --ledger "$W/ledger.md" "${DG[@]}"
expect_red "SR6 대장에서 digest 행을 못 읽었다 (표 형식이 바뀌었다)" \
  env COLAB_DIGEST_INSPECT="$W/inspect-ok" "$HERE/check-image-digests.sh" --ledger "$W/inspect-ok" "${DG[@]}"

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

# ── digest 대장의 **세 상태** (Ted 판정 2026-08-29 · 별칭 태그 이동에 이력 기구가 없던 결함) ──
#   ⭑ 재현하는 결함 = 대장이 **선언한 행만** 보던 것. 배포되는 이미지가 대장에 아예 없으면
#     검사 대상에서 조용히 빠지고 「전건 일치 GREEN」이 나왔다 — green-by-skip 의 교과서 모양이다.
#   세 상태: digest 선언 → 대조 · 명시 면제 → 통과하되 건수 노출 · 선언 없음 → RED.
mk_compose() { cat > "$1" <<'YML'
services:
  a:
    image: colab-v2/core-api:${COLAB_RELEASE_TAG:?필요}
  b:
    image: colab-v2/frontend:${COLAB_RELEASE_TAG:?필요}
  c:
    image: colab-v2/migrator:${COLAB_RELEASE_TAG:?필요}
YML
}
mk_compose "$W/compose.yml"

expect_red "SR15 배포되는 이미지가 대장에 **선언조차 없다** — 대상에서 빠지는 것은 통과가 아니다" \
  env COLAB_DIGEST_INSPECT="$W/inspect-ok" "$HERE/check-image-digests.sh" \
      --ledger "$W/ledger.md" --compose "$W/compose.yml" --digest-ledger "$W/dledger.tsv"

RAN=$((RAN+1)); echo "──────── SR15-b 그 RED 가 **어느 이미지가 미선언인지** 이름으로 말한다"
O="$(COLAB_DIGEST_INSPECT="$W/inspect-ok" "$HERE/check-image-digests.sh" --ledger "$W/ledger.md" --compose "$W/compose.yml" --digest-ledger "$W/dledger.tsv" 2>&1)"
if echo "$O" | grep -q 'colab-v2/migrator:i2 — 대장에 선언이 없다'; then echo "  → 기대대로"
else echo "  → ✗ 미선언 이미지를 이름으로 말하지 않는다"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi

# SR16 — 명시 면제는 통과하되 건수를 드러낸다 (세 상태의 가운데)
cp "$W/ledger.md" "$W/ledger-exempt.md"
echo '| `colab-v2/migrator:i2` | 면제: 배포 때만 도는 일회용 이미지 · 서빙 표면 없음 |' >> "$W/ledger-exempt.md"
RAN=$((RAN+1)); echo "──────── SR16 명시 면제된 이미지는 통과하되 **요약줄에 건수가 나온다**"
O="$(COLAB_DIGEST_INSPECT="$W/inspect-ok" "$HERE/check-image-digests.sh" --ledger "$W/ledger-exempt.md" --compose "$W/compose.yml" --digest-ledger "$W/dledger.tsv" 2>&1)"
RC=$?
if [ $RC -eq 0 ] && echo "$O" | grep -q 'SKIP  colab-v2/migrator:i2 — 명시 면제' \
   && echo "$O" | grep -qE '승인된 면제 [0-9]+건'; then
  echo "  → 기대대로: 면제는 통과하되 **무엇을 안 봤는지**가 요약줄에 남는다"
else echo "  → ✗ 면제가 숨었거나 통과하지 않았다 (exit $RC)"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi

# SR17 — **사유 없는 면제는 면제가 아니다.** 빈 사유로 검사를 끄는 경로를 막는다
cp "$W/ledger.md" "$W/ledger-noreason.md"
echo '| `colab-v2/migrator:i2` | 면제: |' >> "$W/ledger-noreason.md"
expect_red "SR17 사유 없는 면제 — 사유가 없으면 면제가 아니라 RED" \
  env COLAB_DIGEST_INSPECT="$W/inspect-ok" "$HERE/check-image-digests.sh" \
      --ledger "$W/ledger-noreason.md" --compose "$W/compose.yml" --digest-ledger "$W/dledger.tsv"

# SR18 — digest 이력 원장: 별칭 태그가 가리킨 것을 **회차마다 한 줄씩** 남긴다
RAN=$((RAN+1)); echo "──────── SR18 digest 이력 원장 — 별칭 이동마다 append 되고 덮어쓰지 않는다"
( . "$HERE/../pipeline/lib.sh"
  export COLAB_PIPELINE_STATE_DIR="$W/state"
  export COLAB_DIGEST_INSPECT="$W/inspect-ok"
  digest_ledger_append aaa1111 i2 colab-v2/core-api colab-v2/frontend >/dev/null 2>&1 || exit 3
  digest_ledger_append bbb2222 i2 colab-v2/core-api colab-v2/frontend >/dev/null 2>&1 || exit 4
  L="$(digest_ledger_path)"
  [ "$(wc -l < "$L")" = "4" ] || exit 5
  grep -q $'aaa1111\ti2\tcolab-v2/core-api\tsha256:aaaa' "$L" || exit 6
  grep -q $'bbb2222\ti2\tcolab-v2/frontend\tsha256:bbbb' "$L" || exit 7 )
RC=$?
if [ $RC -eq 0 ]; then echo "  → 기대대로: 두 회차 4줄이 그대로 쌓였다 (덮어쓰기 없음)"
else echo "  → ✗ digest 이력 원장이 없거나 쌓이지 않는다 (코드 $RC)"; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR18-b 실측이 안 되는 이미지는 이력에 **[미측정]로 적히고 실패**한다"
( . "$HERE/../pipeline/lib.sh"
  export COLAB_PIPELINE_STATE_DIR="$W/state2"
  export COLAB_DIGEST_INSPECT="$W/inspect-none"
  digest_ledger_append ccc3333 i2 colab-v2/core-api >/dev/null 2>&1 && exit 3
  grep -q '\[미측정\]' "$(digest_ledger_path)" || exit 4 )
RC=$?
if [ $RC -eq 0 ]; then echo "  → 기대대로: 미측정은 조용한 성공이 아니다"
else echo "  → ✗ 미측정을 성공으로 셌거나 적지 않았다 (코드 $RC)"; BAD=$((BAD+1)); fi

# ── 〈297〉 자체 6종 = `§5` 원장의 「서빙 회차」 행 · 외부 4종 = 대장 `§3` (Ted 판정 2026-09-03) ──
#   ⭑ 재현하는 결함 = 대장 `§3` 의 자체 줄이 **손으로만 갱신돼 한 회차 늦는 것**.
#     `deploy.sh:65` 이 「워킹트리 변경 0」을 착수 조건으로 걸어 배포가 레포 파일을 못 쓰기 때문이다
#     (배포가 §3 을 고치면 다음 배포가 자기 산출로 막힌다). 원장은 배포가 자동으로 남기고 회차 태그를 가진다.
#   ⟹ 자체는 원장이 정본이고 `§3` 자체 줄은 **참고**다. 원장에 서빙 회차 행이 없으면 §3 으로 되돌아가지 않는다.
DA="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
DB="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
DC="sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
DD="sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
DE="sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
P1="sha256:1111111111111111111111111111111111111111111111111111111111111111"
P2="sha256:2222222222222222222222222222222222222222222222222222222222222222"

cat > "$W/compose-mix.yml" <<'YML'
services:
  a:
    image: colab-v2/core-api:${COLAB_RELEASE_TAG:?필요}
  b:
    image: colab-v2/frontend:${COLAB_RELEASE_TAG:?필요}
  db:
    image: postgres:16-alpine
YML
cat > "$W/inspect-mix" <<SH
#!/bin/sh
case "\$1" in
  colab-v2/core-api:i2) echo "$DA" ;;
  colab-v2/frontend:i2) echo "$DB" ;;
  postgres:16-alpine)   echo "$P1 postgres@$P1" ;;
esac
SH
chmod +x "$W/inspect-mix"
mk_mixledger() { # $1=출력 $2=core-api 값 $3=frontend 값 $4=postgres 값
  { echo '| 이미지 | digest |'; echo '|---|---|'
    echo "| \`colab-v2/core-api:i2\` | \`$2\` |"
    echo "| \`colab-v2/frontend:i2\` | \`$3\` |"
    echo "| \`postgres:16-alpine\` | \`$4\` |"; } > "$1"
}
mk_mixledger "$W/mix-selfok.md"    "$DA" "$DB" "$P1"   # §3 자체 줄이 맞는 판
mk_mixledger "$W/mix-selfstale.md" "$DD" "$DE" "$P1"   # §3 자체 줄이 낡은 판
mk_mixledger "$W/mix-extbad.md"    "$DA" "$DB" "$P2"   # §3 외부 줄이 어긋난 판
mk_dl() { printf '2026-09-02T00:00:00+0900\trel11111111\ti2\tcolab-v2/core-api\t%s\n2026-09-02T00:00:00+0900\trel11111111\ti2\tcolab-v2/frontend\t%s\n' "$2" "$3" > "$1"; }
mk_dl "$W/dl-ok.md"    "$DA" "$DB"   # 원장이 실물과 같다
mk_dl "$W/dl-drift.md" "$DC" "$DB"   # core-api 한 줄만 어긋난다
printf '2026-09-01T00:00:00+0900\trel00000000\ti2\tcolab-v2/core-api\t%s\n2026-09-01T00:00:00+0900\trel00000000\ti2\tcolab-v2/frontend\t%s\n' "$DD" "$DE" > "$W/dl-norow.md"
MIX=(--compose "$W/compose-mix.yml")

RAN=$((RAN+1)); echo "──────── SR28 (a) 서빙 회차 행이 원장에 있고 전건 일치 → GREEN · 출처가 줄마다 나온다"
O="$(COLAB_DIGEST_INSPECT="$W/inspect-mix" "$HERE/check-image-digests.sh" \
      --ledger "$W/mix-selfok.md" --digest-ledger "$W/dl-ok.md" "${MIX[@]}" 2>&1)"; RC=$?
if [ $RC -eq 0 ] && echo "$O" | grep -q '원장 회차 `rel11111111`' \
   && echo "$O" | grep -q '외부 이미지 — 기대값 출처: 대장' \
   && echo "$O" | grep -qE 'digest 대조 GREEN — 3 건 전건 일치'; then
  echo "  → 기대대로 GREEN — 자체는 원장 회차 rel11111111 · 외부는 §3"
else echo "  → ✗ (exit $RC)"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR29 (b) 서빙 회차 행이 원장에 **없다** → RED · §3 이 맞아도 되돌아가지 않는다"
O="$(COLAB_DIGEST_INSPECT="$W/inspect-mix" "$HERE/check-image-digests.sh" \
      --ledger "$W/mix-selfok.md" --digest-ledger "$W/dl-norow.md" "${MIX[@]}" 2>&1)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q '서빙 중 릴리스를 원장에서 특정하지 못했다'; then
  echo "  → 기대대로 RED — §3 자체 줄이 실물과 같은데도 통과시키지 않는다(폴백 없음)"
else echo "  → ✗ §3 으로 되돌아갔거나 통과시켰다 (exit $RC)"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR30 (c) 원장 행은 있으나 자체 한 줄이 실물과 다르다 → RED · 이미지 이름으로 적발"
O="$(COLAB_DIGEST_INSPECT="$W/inspect-mix" "$HERE/check-image-digests.sh" \
      --ledger "$W/mix-selfok.md" --digest-ledger "$W/dl-drift.md" "${MIX[@]}" 2>&1)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q 'FAIL  colab-v2/core-api:i2' && echo "$O" | grep -q "원장 $DC"; then
  echo "  → 기대대로 RED — 나머지 5종이 회차를 고정하므로 어긋난 한 줄이 「회차 미상」으로 뭉개지지 않는다"
else echo "  → ✗ (exit $RC)"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR31 (d) 외부 이미지가 \`§3\` 과 다르다 → RED (외부의 정본은 여전히 §3)"
O="$(COLAB_DIGEST_INSPECT="$W/inspect-mix" "$HERE/check-image-digests.sh" \
      --ledger "$W/mix-extbad.md" --digest-ledger "$W/dl-ok.md" "${MIX[@]}" 2>&1)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q 'FAIL  postgres:16-alpine' && echo "$O" | grep -q "대장 $P2"; then
  echo "  → 기대대로 RED — 외부 4종은 원장에 안 남으므로 §3 이 계속 정본이다"
else echo "  → ✗ (exit $RC)"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR32 (e) \`§3\` 자체 줄이 낡았는데 원장은 맞다 → GREEN (§3 자체 줄은 참고다)"
O="$(COLAB_DIGEST_INSPECT="$W/inspect-mix" "$HERE/check-image-digests.sh" \
      --ledger "$W/mix-selfstale.md" --digest-ledger "$W/dl-ok.md" "${MIX[@]}" 2>&1)"; RC=$?
if [ $RC -eq 0 ] && echo "$O" | grep -qE 'digest 대조 GREEN — 3 건 전건 일치'; then
  echo "  → 기대대로 GREEN — §3 의 낡은 자체 값이 판정을 흔들지 않는다"
else echo "  → ✗ §3 자체 줄이 아직 판정에 끼어든다 (exit $RC)"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi

# ── P4 sha256 무결성이 **실제로 돌았는가** (2026-08-31 · 판정 〈249〉 회차 실측) ────────────
# ⭑ 재현하는 결함 = `preflight.sh` P4 루프의 `"${!ART[@]:-}"`.
#   연관배열 키 확장에 `:-` 기본값을 붙이면 bash 가 「invalid variable name」을 내고
#   **루프 본문이 한 번도 돌지 않는다.** 그런데 `fail` 이 불리지 않으므로 P4 는 조용히 통과한다 —
#   산출물이 손상돼 있어도 사전조건이 GREEN 쪽으로 한 칸 다가간다. 이 레포 대표 실패형이다.
# **대상 0 건을 통과로 세지 않는다**(P2·P4 자신이 적은 규칙)이므로, 여기서는 「돌았는가」를 값으로 잰다.
S="$W/rt-p4"; mk_store "$S" 20260829T033005 20260829T033005 20260829T033040
mk_cfg "$W/cfg-p4.env" "$S" "uploads previews"

RAN=$((RAN+1)); echo "──────── SR19 P4 가 산출물 **네 건 전부**를 대조한다 (루프가 실제로 돈다)"
O="$(pf "$W/cfg-p4.env")"
N="$(echo "$O" | grep -c 'P4 .* sha256 일치')"
if [ "$N" = "4" ]; then echo "  → 기대대로: P4 일치 4건 (원장 2 ＋ 볼륨 2)"
else echo "  → ✗ P4 대조가 $N 건이다 (기대 4) — 루프가 돌지 않았다면 손상을 못 본다"
     echo "$O" | grep -E 'P4' | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR19-b .sha256 이 어긋나면 P4 가 **이름으로** 적발한다"
echo '0000000000000000000000000000000000000000000000000000000000000000'   > "$S/vol-uploads-20260829T033005.tar.gz.sha256"
O="$(pf "$W/cfg-p4.env")"
if echo "$O" | grep -q 'P4 vol-uploads sha256 불일치'; then echo "  → 기대대로: 손상을 이름으로 말한다"
else echo "  → ✗ 손상된 산출물이 P4 를 통과했다"; echo "$O" | grep -E 'P4' | sed 's/^/    /'; BAD=$((BAD+1)); fi

# ── verify-restored.sh 의 **손검사 2건 자동화** (2026-09-03) ────────────────────
# ⭑ 재현하는 결함 셋 —
#   ㈎ 세는 롤이 FORCE RLS 에 걸려 `count(*)` 가 **언제나 0** 인데, 그 0 을 「행이 사라졌다」로 읽던 것.
#      살아 있는 staging 에서 실측된 자리다(소유자 롤 0 vs 덤프 13). 리허설은 일회용 pg 에
#      **superuser** 로 붙어 RLS 를 통째로 건너뛰었기 때문에 이 자리를 한 번도 재지 않았다.
#   ㈏ ③-보(읽는 경로)를 **사람이 돌기로** 두고, 안 돌고도 `--manual-ok` 한 글자로 GREEN 이 되던 것.
#   ㈐ ⑤(앱 롤 양성·음성)를 **사람이 돌기로** 두던 것. `--no-privileges` 덤프라
#      제자리 복원 뒤 GRANT 가 통째로 없어지는데, 그것을 아무도 기계로 안 셌다.
# 세 판정 전부 **주입구**로 docker 없이 돈다.
VR="$HERE/verify-restored.sh"
mk_ai_dump() { { echo "COPY public.d9_method_term (term) FROM stdin;"; echo "T"; echo '\.'
                 echo "COPY public.d9_place_alias (a) FROM stdin;"; echo "P"; echo '\.'
                 echo "COPY public.d9_topic_synonym (s) FROM stdin;"; echo "S"; echo '\.'
                 echo "COPY public.d9_concept (c) FROM stdin;"; for i in 1 2 3; do echo "C$i"; done; echo '\.'
                 echo "COPY public.d9_concept_edge (e) FROM stdin;"; echo "E"; echo '\.'; } | gzip -c > "$1"; }
mk_pf_dump() { { echo "COPY public.d3_dataset (id) FROM stdin;"; for i in $(seq 1 12); do echo "D$i"; done; echo '\.'
                 echo "COPY public.d3_file (id) FROM stdin;"; for i in $(seq 1 5); do echo "F$i"; done; echo '\.'
                 echo "COPY public.d4_lineage_edge (id) FROM stdin;"; for i in $(seq 1 6); do echo "E$i"; done; echo '\.'; } | gzip -c > "$1"; }
mk_ai_dump "$W/ai.sql.gz"; mk_pf_dump "$W/pf.sql.gz"

# 세는 롤 훅 — 표마다 기대치와 같은 값을 낸다(대조군). `RLSCAUGHT`/`ZERO` 로 결함을 재현한다.
cat > "$W/count-ok" <<'SH'
#!/bin/sh
case "$2" in
  *rolsuper*)        echo "${SUPER:-true} ${FORCE:-false}" ;;
  *d3_dataset*)      echo "${D3:-12}" ;;
  *d3_file*)         echo 5 ;;
  *d4_lineage_edge*) echo 6 ;;
  *d9_method_term*|*d9_place_alias*|*d9_topic_synonym*|*d9_concept_edge*) echo 1 ;;
  *d9_concept*)      echo 3 ;;
  *d9_topic_synonym\ WHERE*|*synonym\ \<\>*) echo "강우데이터	강우·강수" ;;
  *d1_account*)      echo "LAB_A	A연구실	ACC1" ;;
  *GROUP\ BY\ lab_id*) echo "LAB_A	12" ;;
  *d1_lab*)          echo "LAB_B" ;;
  *relrowsecurity=false*) echo 0 ;;
  *) echo "" ;;
esac
SH
# ⚠ 위 case 는 위에서부터 맞는다 — 동의어 조회는 `d9_topic_synonym` 계수와 문자열이 겹치므로
#   전용 훅을 따로 둔다(겹침을 주석 없이 두면 다음 사람이 계수를 고치다 조회를 깬다).
cat > "$W/count-ok" <<'SH'
#!/bin/sh
case "$2" in
  # ⚠ 순서가 판정이다 — `rolsuper OR rolbypassrls`(⑤-0) 가 `rolsuper`(세는 롤 성질) 보다 **먼저** 와야 한다.
  *"rolsuper OR rolbypassrls"*) echo "${APPPROP:-false}" ;;
  *rolsuper*)               echo "${SUPER:-true} ${FORCE:-false}" ;;
  *"synonym <> topic"*)     echo "강우데이터	강우·강수" ;;
  *d1_account*)             echo "LAB_A	A연구실	ACC1" ;;
  *"GROUP BY lab_id"*)      echo "LAB_A	12" ;;
  *"FROM d1_lab"*)          echo "LAB_B" ;;
  *"count(*) FROM d3_dataset"*)      echo "${D3:-12}" ;;
  *"count(*) FROM d3_file"*)         echo 5 ;;
  *"count(*) FROM d4_lineage_edge"*) echo 6 ;;
  *"count(*) FROM d9_concept_edge"*) echo 1 ;;
  *"count(*) FROM d9_concept"*)      echo 3 ;;
  *"count(*) FROM d9_"*)             echo 1 ;;
  *relrowsecurity*)         echo 0 ;;
  *) echo "" ;;
esac
SH
cat > "$W/app-ok" <<'SH'
#!/bin/sh
# $1=DB $2=롤 $3=SQL
case "$3" in
  *"app.current_lab='LAB_A'"*) echo "${POS:-12}" ;;
  *"app.current_lab='LAB_B'"*) echo "${NEG:-0}" ;;
  *d9_concept*)                echo "${AIC:-3}" ;;
  *) echo "" ;;
esac
SH
cat > "$W/search-ok" <<'SH'
#!/bin/sh
printf '%s\t%s\t%s\n' "${ST:-200}" "${DEG:-false}" "${EXP:-1}"
SH
cat > "$W/digest-ok" <<'SH'
#!/bin/sh
# --record <파일> 이면 기록만 한다. 대조는 언제나 통과(이 묶음의 대상이 아니다).
[ "$1" = "--record" ] && echo 'img	sha256:x' > "$2"
exit 0
SH
chmod +x "$W/count-ok" "$W/app-ok" "$W/search-ok" "$W/digest-ok"
: > "$W/pre.tsv"; echo 'img	sha256:x' > "$W/pre.tsv"

vr() { # 남은 인자는 env 덮어쓰기용
  env COLAB_BACKUP_CONFIG="$W/cfg1.env" \
      COLAB_VERIFY_COUNT_HOOK="$W/count-ok" COLAB_VERIFY_APPSQL_HOOK="$W/app-ok" \
      COLAB_VERIFY_SEARCH_HOOK="$W/search-ok" COLAB_VERIFY_DIGEST_CMD="$W/digest-ok" \
      "$@" "$VR" --platform-dump "$W/pf.sql.gz" --ai-dump "$W/ai.sql.gz" \
      --owner colab_owner --pre-digests "$W/pre.tsv" --no-health 2>&1
}

RAN=$((RAN+1)); echo "──────── SR20 대조군 — 손검사 2건이 **기계로 돌아** GREEN 이 된다 (--manual-ok 없이)"
O="$(vr env)"; RC=$?
if [ $RC -eq 0 ] && echo "$O" | grep -q '③-보 POST /searches 200' \
   && echo "$O" | grep -q '⑤-a 양성' && echo "$O" | grep -q '⑤-b 음성' \
   && echo "$O" | grep -q '손검사 2건.*기계가 돌았다'; then
  echo "  → 기대대로 GREEN (exit 0) — 종전의 exit 3 이 사라졌다"
else echo "  → ✗ 자동화가 GREEN 을 못 냈다 (exit $RC)"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR21 ㈎ 세는 롤이 FORCE RLS 에 걸린다 — **0 을 부재로 읽지 않는다**"
O="$(vr env SUPER=false FORCE=true D3=0)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q 'd3_dataset — 세는 롤(.*)이 FORCE RLS 에 걸린다' \
   && ! echo "$O" | grep -q 'd3_dataset = 0 · 기대'; then
  echo "  → 기대대로 RED — 「0 건이라 틀렸다」가 아니라 「못 봤다」로 말한다 (exit $RC)"
else echo "  → ✗ RLS 에 걸린 0 을 데이터 부재로 읽었다 (exit $RC)"; echo "$O" | grep -E 'd3_dataset' | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR21-b 진짜 행 손실은 **그대로 RED** 다 (범위를 줄인 것이 아님의 증거)"
O="$(vr env D3=7)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q 'd3_dataset = 7 · 기대 12'; then
  echo "  → 기대대로 RED — 세는 롤을 바꾼 것이 검사를 무르게 하지 않았다"
else echo "  → ✗ 행 손실을 놓쳤다 (exit $RC)"; echo "$O" | grep -E 'd3_dataset' | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR22 ㈏ ③-보 — **상태코드만 200 이고 degraded 면 RED**"
O="$(vr env DEG=true)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q '③-보 POST /searches — 상태 200 · degraded=true'; then
  echo "  → 기대대로 RED — 200 하나로 통과시키지 않는다"
else echo "  → ✗ degraded 인데 통과했다 (exit $RC)"; echo "$O" | grep -E '③-보' | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR22-b ③-보 — **확장 낱말 0건이면 RED** (사전이 끊긴 모양)"
O="$(vr env EXP=0)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q '③-보 POST /searches — 상태 200 · degraded=false · 확장 낱말 0건'; then
  echo "  → 기대대로 RED — 사전 표가 차 있어도 배선이 끊기면 여기서 드러난다"
else echo "  → ✗ 확장 0건을 통과시켰다 (exit $RC)"; echo "$O" | grep -E '③-보' | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR23 ㈐ ⑤-a 양성 — 앱 롤이 **못 읽으면 RED** (제자리 복원 뒤 GRANT 소멸)"
O="$(vr env POS=0)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q '⑤-a 양성 실패 — 앱 롤이 본 것 0'; then
  echo "  → 기대대로 RED — DROP SCHEMA 가 지운 GRANT 를 헬스가 아니라 이 줄이 잡는다"
else echo "  → ✗ 권한 0 인 앱 롤을 통과시켰다 (exit $RC)"; echo "$O" | grep -E '⑤-' | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR23-b ⑤-b 음성 — 남의 연구실 행이 **보이면 RED**"
O="$(vr env NEG=4)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q '⑤-b 음성 실패 — 다른 연구실 맥락에서 4행이 보인다'; then
  echo "  → 기대대로 RED — 「앱 롤이 읽는다」만으로 GREEN 을 내지 않는다"
else echo "  → ✗ 경계가 뚫렸는데 통과했다 (exit $RC)"; echo "$O" | grep -E '⑤-' | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR23-c ⑤-0 앱 롤이 BYPASSRLS 면 RED (음성 시험이 거짓 green 이 된다)"
O="$(vr env APPPROP=true)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q '⑤-0 앱 롤 .* superuser 이거나 BYPASSRLS 다'; then
  echo "  → 기대대로 RED"
else echo "  → ✗ BYPASSRLS 앱 롤을 통과시켰다 (exit $RC)"; echo "$O" | grep -E '⑤-0' | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR23-d ⑤-c ai 앱 롤이 사전을 못 읽으면 RED"
O="$(vr env AIC=0)"; RC=$?
if [ $RC -ne 0 ] && echo "$O" | grep -q '⑤-c ai 앱 롤이 사전을 못 읽는다 — 본 것 0 · 기대 3'; then
  echo "  → 기대대로 RED — colab_ai 쪽 GRANT 소멸도 따로 잡는다"
else echo "  → ✗ 사전을 못 읽는데 통과했다 (exit $RC)"; echo "$O" | grep -E '⑤-c' | sed 's/^/    /'; BAD=$((BAD+1)); fi

# ══ 프로파일 합격선 — `restore-db.sh` 가 전역 기본값(20 · platform 형상)을 쓰던 결함 (`〈286〉`) ══
#    D3 회차에서 표 6개가 **정상**인 `ai` 원장 덤프가 합격선 20 에 걸려 거부됐다
#    (`sessions/WINDOW-20260903-D3.md §4.2`). 아래 넷이 **두 방향**을 동시에 못 박는다 —
#    ⓐ 온전한 ai 덤프(표 6)는 통과한다  ⓑ **진짜 잘린 덤프는 여전히 RED 다.**
#    ⓑ 가 없으면 이 수정은 「검사 범위를 줄인 것」과 구별되지 않는다(`CLAUDE.md §4` · 스킬 §3).

# 픽스처 설정 — 홈 env 파일에 의존하지 않게 `COLAB_BACKUP_CONFIG` 로 세계를 고정한다.
cat > "$W/floors.env" <<'ENV'
COLAB_BACKUP_TARGET=local
COLAB_BACKUP_PROFILES="platform ai"
COLAB_BACKUP_DB_platform=colab_platform
COLAB_BACKUP_DB_ai=colab_ai
COLAB_BACKUP_MIN_TABLES_platform=20
COLAB_BACKUP_MIN_ROWS_platform=190
COLAB_BACKUP_MIN_TABLES_ai=4
COLAB_BACKUP_MIN_ROWS_ai=45
ENV
: > "$W/pre-backup.sql.gz"

# 재료 — 살아 있는 `colab_ai` 의 실제 형상(표 6 · 행 91)을 본뜬 **온전한** 덤프.
mk_dump() { # $1=출력 $2=테이블수 $3=테이블당 행수
  local n=0 i r
  { echo "-- dump"
    while [ "$n" -lt "$2" ]; do
      n=$((n+1))
      echo "CREATE TABLE public.t$n (id text, payload text);"
      echo "COPY public.t$n (id, payload) FROM stdin;"
      i=0; while [ "$i" -lt "$3" ]; do i=$((i+1))
        r="$(od -An -tx1 -N24 /dev/urandom | tr -d ' \n')"
        echo "t$n-$i	$r"
      done
      echo '\.'
    done
  } | gzip -c > "$1"
}
mk_dump "$W/ai-intact.sql.gz"      6  16   # 표 6 · 행 96  — 합격선(4·45) 위
mk_dump "$W/ai-truncated.sql.gz"   2  16   # 표 2 · 행 32  — 표가 모자란다
mk_dump "$W/plat-cut.sql.gz"       5  60   # 표 5 · 행 300 — platform 합격선 20 에 못 미친다

rdb() { env COLAB_BACKUP_CONFIG="$W/floors.env" COLAB_RESTORE_PRE_BACKUP="$W/pre-backup.sql.gz" \
        "$HERE/restore-db.sh" "$@" --yes-drop-schema 2>&1; }

RAN=$((RAN+1)); echo "──────── SR24 ⓐ 온전한 ai 덤프(표 6)는 **합격선 검사를 통과한다** — 거짓 RED 가 걷혔다"
O="$(rdb --db colab_ai --owner owner --dump "$W/ai-intact.sql.gz")"
if echo "$O" | grep -q '합격선 프로파일 = ai' && echo "$O" | grep -q 'PASS  C4' \
   && ! echo "$O" | grep -q '덤프가 RED 다'; then
  echo "  → 기대대로 — ai 합격선(표 4)이 걸렸다. 표 6 이 20 에 걸려 죽지 않는다"
  echo "$O" | grep -E '합격선 프로파일|C0|C4|C5' | sed 's/^/    /'
else echo "  → ✗ 온전한 ai 덤프가 여전히 막힌다"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi
# ⚠ 이 fixture 는 docker 없이 도는 자리까지만 본다 — 합격선 판정 다음 줄(커넥션 세기)에서 선다.
#    그 뒤는 살아 있는 스택에서 `verify-restored.sh` 가 센다.

RAN=$((RAN+1)); echo "──────── SR25 ⓑ **진짜 잘린 ai 덤프(표 2)는 여전히 RED** — 합격선을 낮춘 것이 아니다"
O="$(rdb --db colab_ai --owner owner --dump "$W/ai-truncated.sql.gz")"
if echo "$O" | grep -q '덤프가 RED 다' && echo "$O" | grep -q 'FAIL  C4 CREATE TABLE 2개 < 4'; then
  echo "  → 기대대로 RED — 표 2 는 ai 합격선 4 에 걸린다"
  echo "$O" | grep -E 'FAIL|덤프가 RED' | sed 's/^/    /'
else echo "  → ✗ 잘린 덤프를 통과시켰다"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi

RAN=$((RAN+1)); echo "──────── SR26 ⓑ′ 중간에서 끊긴 platform 덤프(표 5)도 여전히 RED — 프로파일별로 따로 선다"
O="$(rdb --db colab_platform --owner owner --dump "$W/plat-cut.sql.gz")"
if echo "$O" | grep -q '덤프가 RED 다' && echo "$O" | grep -q 'FAIL  C4 CREATE TABLE 5개 < 20'; then
  echo "  → 기대대로 RED — 같은 수정이 platform 합격선 20 을 그대로 유지한다"
  echo "$O" | grep -E 'FAIL|덤프가 RED' | sed 's/^/    /'
else echo "  → ✗ 잘린 platform 덤프를 통과시켰다"; echo "$O" | sed 's/^/    /'; BAD=$((BAD+1)); fi

expect_red "SR27 프로파일에 없는 DB 이름 — 합격선을 전역 기본값으로 메우지 않는다" \
  env COLAB_BACKUP_CONFIG="$W/floors.env" COLAB_RESTORE_PRE_BACKUP="$W/pre-backup.sql.gz" \
      "$HERE/restore-db.sh" --db colab_unknown --owner owner --dump "$W/ai-intact.sql.gz" --yes-drop-schema

echo
if [ "$BAD" -eq 0 ]; then echo "복원 셀프테스트 GREEN — fixture $RAN 건 전부 기대대로"; exit 0; fi
echo "복원 셀프테스트 RED — $BAD 건이 fail-closed 가 아니다"; exit 1
