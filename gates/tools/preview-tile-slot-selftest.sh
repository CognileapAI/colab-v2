#!/usr/bin/env bash
# preview-tile-slot 이 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 케이스 9종 — 일곱은 red 여야 하고 둘은 green 이어야 하며, green 하나는 **건수를 드러내야** 한다.
#   ⓐ 적용 DB 미지정            → red(준비·입력미선언)
#   ⓑ 면제 선언 파일 부재        → red   (「선언이 없다」와 「면제가 없다」는 다르다)
#   ⓑ' 면제 files 항목 부재      → red   (「없는 것」을 「0건」으로 세지 않는다)
#   ⓒ 자리 경로 미선언           → red   (자리를 안 보고 「자리에 있다」를 말하지 않는다)
#   ⓓ 자리 경로가 없는 디렉터리   → red   (없는 자리를 「비어 있다」로 읽지 않는다)
#   ⓔ **자리에 타일 0건**        → red   ← **이 게이트의 존재 이유.** 이 자리의 자연스러운
#                                        대상 수는 오늘 0 이다. 0 을 통과로 세면 아무것도 안 본다
#   ⓕ 못 쓰는 파일 1건           → red   (개관 없는 타일 = 재사용이 영원히 거절된다)
#   ⓖ 발행은 있는데 쓸 수 있는 타일 0 → red
#   ⓗ 못 쓰는 파일을 **이름으로 면제** ＋ 쓸 수 있는 타일 1 → green **＋ 면제 건수 노출**
#   ⓘ 쓸 수 있는 타일 1건         → green
#
# **픽스처 TIFF 는 바이트로 짓는다** — 라이브러리를 들이면 「무엇이 COG 인가」의 판정이
# 라이브러리 판단으로 옮겨가고, 그러면 이 selftest 가 게이트의 기준을 증명하지 못한다.
#
# 실제 db/ · services/ · gates/config 에는 **한 글자도 쓰지 않는다** — 임시 디렉터리와
# 일회용 postgres 안에서만 일어난다. 포트를 하나도 publish 하지 않는다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/preview-tile-slot.sh"
SCHEMA="$REPO_ROOT/db/platform/schema.sql"
SEED="$REPO_ROOT/services/core-api/tests/fixtures/seed.sql"
DB="previewtileslot"
FAILURES=()

red() { echo "::error::preview-tile-slot-selftest red — $*"; exit 1; }

for f in "$GATE" "$SCHEMA" "$SEED"; do
  [ -f "$f" ] || red "판정 재료가 없다: ${f#"$REPO_ROOT"/}. 대상 0건은 통과가 아니다."
done

# shellcheck source=/dev/null
. "$REPO_ROOT/gates/tools/_pg.sh"
pg_start preview-tile-slot-selftest || exit $?

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" preview-tile-XXXXXX)"
cleanup_all() { rm -rf "$TMP"; pg_cleanup; }
trap cleanup_all EXIT INT TERM

su() { docker exec -i "$PGC" psql -q -U postgres -d "$DB" -v ON_ERROR_STOP=1 "$@"; }

docker exec "$PGC" createdb -U postgres "$DB" >/dev/null 2>&1 || red "DB 를 만들지 못했다."
su < "$SCHEMA" >"$TMP/err" 2>&1 || red "선언 스키마를 적용하지 못했다:
$(sed 's/^/     /' "$TMP/err")"
su < "$SEED" >"$TMP/err" 2>&1 || red "시드를 넣지 못했다:
$(sed 's/^/     /' "$TMP/err")"

cat > "$TMP/psql" <<EOF
#!/usr/bin/env bash
shift
exec docker exec -i "$PGC" psql -U postgres -d "$DB" "\$@"
EOF
chmod +x "$TMP/psql"

LAB="0000000000000000000000000A"
ACC="000000000000000000000000A1"
UP="01JQ00000000000000000000T1"

# ── 픽스처 — `preview.cog-built` 한 건이 발행된 업로드 ────────────────────
su <<SQL >"$TMP/err" 2>&1 || red "픽스처를 넣지 못했다:
$(sed 's/^/     /' "$TMP/err")"
INSERT INTO d5_upload (id, lab_id, uploader_account_id, expires_at)
VALUES ('$UP', '$LAB', '$ACC', now() + interval '1 day');
INSERT INTO d5_pipeline_event
  (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,
   idempotency_key, payload)
VALUES ('01JQ00000000000000000000T2', '$LAB', '$ACC', '$UP', 'preview.cog-built', '1.0',
        'pipeline-worker', 'preview.cog-built:$UP',
        '{"fileIds":["01JQ00000000000000000000T3"],"overviewLevels":2}');
SQL

# ── 픽스처 TIFF — 바이트로 짓는다 ─────────────────────────────────────────
mktiff() { # $1=출력 $2=cog|tiled-only|stripped
  python3 - "$1" "$2" <<'PY'
import struct, sys
out, kind = sys.argv[1], sys.argv[2]
def ifd(tag, value, next_off):
    # count 1 · SHORT · 값 1개 (값은 4바이트 칸에 인라인)
    b = struct.pack("<H", 1)
    b += struct.pack("<HHIHH", tag, 3, 1, value, 0)
    b += struct.pack("<I", next_off)
    return b
tag0 = 322 if kind in ("cog", "tiled-only") else 256   # 322=TileWidth
second = 26 if kind == "cog" else 0                    # 8 + 2 + 12 + 4 = 26
data = b"II" + struct.pack("<HI", 42, 8) + ifd(tag0, 256, second)
if kind == "cog":
    data += ifd(256, 128, 0)                           # 개관 IFD
open(out, "wb").write(data)
PY
}

SLOT="$TMP/slot"; mkdir -p "$SLOT"
mktiff "$SLOT/tile-good.tif" cog
EXEMPT_NONE="$TMP/exempt-none.toml"
printf '[exempt]\nfiles = []\nreason = "선언은 있고 면제는 없다"\n' > "$EXEMPT_NONE"
EXEMPT_ONE="$TMP/exempt-one.toml"
printf '[exempt]\nfiles = ["tile-broken.tif"]\nreason = "알고 있는 잔재"\n' > "$EXEMPT_ONE"

URL="postgresql://ignored/ignored"        # 주입된 psql 이 무시한다. **값은 출력하지 않는다**
run_gate() { env COLAB_PREVIEW_TILE_PSQL="$TMP/psql" "$@" "$GATE" 2>&1; }

expect() { # $1=green|red $2=라벨 $3..=환경변수
  local want="$1" label="$2"; shift 2
  local out rc got
  out="$(run_gate "$@")"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$want" ]; then echo "[selftest] $label → $got OK"
  else
    echo "[selftest] $label → $got (기대 $want) ✗"
    echo "$out" | sed 's/^/           /'
    FAILURES+=("$label")
  fi
  LAST_OUT="$out"
}

B="COLAB_PREVIEW_TILE_EXEMPT=$EXEMPT_NONE"

# ⓐ 적용 DB 미지정 — red 이되 **원인을 참말로 말해야 한다**
expect red "ⓐ 적용 DB 미지정" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_APPLIED_DB_URL_PLATFORM=
case "$LAST_OUT" in
  *cause=입력미선언*missing=*) echo "[selftest] ⓐ 원인 표식(입력미선언) → OK" ;;
  *) echo "[selftest] ⓐ cause=입력미선언 표식이 없다 ✗"; FAILURES+=("ⓐ 원인 표식") ;;
esac

# ⓑ 면제 선언 파일 부재
expect red "ⓑ 면제 선언 부재" COLAB_PREVIEW_TILE_EXEMPT="$TMP/없는파일.toml" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓑ' 파일은 있는데 항목이 없다
printf '[exempt]\nreason = "항목 자체가 없다"\n' > "$TMP/exempt-empty.toml"
expect red "ⓑ' 면제 항목 부재" COLAB_PREVIEW_TILE_EXEMPT="$TMP/exempt-empty.toml" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓒ 자리 경로 미선언
expect red "ⓒ 자리 경로 미선언" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR= COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓓ 자리 경로가 없는 디렉터리
expect red "ⓓ 없는 디렉터리" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR="$TMP/없는자리" COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓘ 쓸 수 있는 타일 1건 → green
expect green "ⓘ 쓸 수 있는 타일 1건" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓕ 못 쓰는 파일이 섞이면 red — 개관 없는 타일은 재사용이 영원히 거절된다
mktiff "$SLOT/tile-broken.tif" tiled-only
expect red "ⓕ 못 쓰는 타일 1건" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓗ 같은 상태 + 이름으로 면제 → green 이되 **건수가 드러나야** 한다
expect green "ⓗ 이름으로 면제" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_ONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_APPLIED_DB_URL_PLATFORM="$URL"
case "$LAST_OUT" in
  *"면제 1"*) echo "[selftest] ⓗ 면제 건수 노출 → OK" ;;
  *) echo "[selftest] ⓗ 면제 건수가 출력에 없다 ✗ — 건수를 숨긴 통과는 green-by-skip 이다"
     echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("ⓗ 건수 노출") ;;
esac

# ⓖ 발행은 있는데 **쓸 수 있는 타일 0** → red
rm -f "$SLOT/tile-good.tif"
expect red "ⓖ 발행 있음·쓸 수 있는 타일 0" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_ONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓔ **자리에 타일 0건** → red. 이 자리의 자연스러운 대상 수는 오늘 0 이고,
#   0 을 통과로 세는 게이트는 아무것도 검사하지 않으면서 green 을 찍는다
rm -f "$SLOT"/tile-*.tif
expect red "ⓔ 자리에 타일 0건" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_APPLIED_DB_URL_PLATFORM="$URL"

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::preview-tile-slot-selftest red — 실패한 케이스: ${FAILURES[*]}"
  exit 1
fi
echo "preview-tile-slot-selftest green — 10 케이스(red 8 · green 2) ＋ 면제 건수 노출 1 ＋ 원인 표식 1 = 검사 12건 전건 기대대로"
exit 0
