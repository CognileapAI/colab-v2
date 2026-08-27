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

echo
if [ "$BAD" -eq 0 ]; then echo "복원 셀프테스트 GREEN — fixture $RAN 건 전부 기대대로"; exit 0; fi
echo "복원 셀프테스트 RED — $BAD 건이 fail-closed 가 아니다"; exit 1
