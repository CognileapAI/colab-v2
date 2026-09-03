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
READINESS="$REPO_ROOT/gates/tools/_readiness.sh"
APPROLE="$REPO_ROOT/services/core-api/ops/app-role.sql"   # 경계 롤(colab_app)을 세운다 — 정본은 하나다
DB="previewtileslot"
SCHEMA_ONLY_DB="previewtileslot_schemaonly"
BROLE="colab_app"      # 경계 롤 = FORCE RLS 에 걸리는 롤. app-role.sql 이 그 성질을 보증한다
FAILURES=()
# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나.
# 종전에는 이 파일의 expect() 가 종료코드 78(준비 실패)을 그냥 red 로 접어
# **「기대한 red」로 셌다** — 그 케이스는 판정된 적이 없는데 출력은 OK 라고 말했다
# (2026-09-03 코드리뷰 #6 · `CLAUDE.md §4` green-by-skip).
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

red() { echo "::error::preview-tile-slot-selftest red — $*"; exit 1; }

for f in "$GATE" "$READINESS" "$SCHEMA" "$SEED" "$APPROLE"; do
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

# 경계 롤을 세운다 — 게이트의 ㉯ 대조가 이 롤로 재조회한다. 시드와 마찬가지로 **정본을 그대로** 쓴다.
su -v owner=colab_owner -v app="$BROLE" -v app_password=gateapp < "$APPROLE" >"$TMP/err" 2>&1 \
  || red "경계 롤 부트스트랩이 실패했다:
$(sed 's/^/     /' "$TMP/err")"

# ── psql 주입 — 게이트는 URL 로 부르고, 여기서는 그 URL 을 무시하고 컨테이너 안에서 돈다 ──
# 세 벌을 만든다: 읽기 전용으로 **선언된** 접속(실물 URL 이 그러하다) · 그 선언이 빠진 접속 ·
# **경계 롤로 붙는 접속**(#57 이 속던 바로 그 접속 — 읽기 전용 검사만으로는 걸리지 않는다).
mk_psql() { # $1=파일 $2=DB $3=PGOPTIONS $4=롤(기본 postgres)
  cat > "$1" <<EOF
#!/usr/bin/env bash
shift            # 첫 인자(URL)를 버린다 — 포트를 publish 하지 않으므로 URL 로 못 붙는다
exec docker exec -e PGOPTIONS="$3" -i "$PGC" psql -U "${4:-postgres}" -d "$2" "\$@"
EOF
  chmod +x "$1"
}
mk_psql "$TMP/psql"          "$DB" "-c default_transaction_read_only=on"
mk_psql "$TMP/psql-rw"       "$DB" ""
mk_psql "$TMP/psql-boundary" "$DB" "-c default_transaction_read_only=on" "$BROLE"

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
run_gate() { env COLAB_PREVIEW_TILE_PSQL="$TMP/psql" COLAB_PREVIEW_TILE_BOUNDARY_ROLE="$BROLE" "$@" "$GATE" 2>&1; }

expect() { # $1=green|red $2=라벨 $3..=환경변수
  local want="$1" label="$2"; shift 2
  local out rc got
  out="$(run_gate "$@")"; rc=$?
  # 뒤따르는 사유·건수 대조가 이 값을 읽는다 — intercept 로 일찍 빠져나가도 비어 있으면 안 된다.
  LAST_OUT="$out"
  # 준비 실패(78 또는 준비 표식)는 **기대한 red 가 아니다** — 판정된 적이 없다.
  if expect_intercept_readiness "$rc" "$out" "$label" "$want"; then return; fi
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
expect 미선언 "ⓐ 대조 정본 미지정" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_PREVIEW_TILE_DB_URL=
case "$LAST_OUT" in
  *cause=입력미선언*missing=*) echo "[selftest] ⓐ 원인 표식(입력미선언) → OK" ;;
  *) echo "[selftest] ⓐ cause=입력미선언 표식이 없다 ✗"; FAILURES+=("ⓐ 원인 표식") ;;
esac

# ⓑ 면제 선언 파일 부재
expect 미선언 "ⓑ 면제 선언 부재" COLAB_PREVIEW_TILE_EXEMPT="$TMP/없는파일.toml" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_PREVIEW_TILE_DB_URL="$URL"

# ⓑ' 파일은 있는데 항목이 없다
printf '[exempt]\nreason = "항목 자체가 없다"\n' > "$TMP/exempt-empty.toml"
expect 미선언 "ⓑ' 면제 항목 부재" COLAB_PREVIEW_TILE_EXEMPT="$TMP/exempt-empty.toml" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_PREVIEW_TILE_DB_URL="$URL"

# ⓒ 자리 경로 미선언
expect 미선언 "ⓒ 자리 경로 미선언" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR= COLAB_PREVIEW_TILE_DB_URL="$URL"

# ⓓ 자리 경로가 없는 디렉터리
expect 미선언 "ⓓ 없는 디렉터리" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR="$TMP/없는자리" COLAB_PREVIEW_TILE_DB_URL="$URL"

# ⓘ 쓸 수 있는 타일 1건 → green
expect green "ⓘ 쓸 수 있는 타일 1건" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_PREVIEW_TILE_DB_URL="$URL"

# ⓕ 못 쓰는 파일이 섞이면 red — 개관 없는 타일은 재사용이 영원히 거절된다
mktiff "$SLOT/tile-broken.tif" tiled-only
expect red "ⓕ 못 쓰는 타일 1건" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_PREVIEW_TILE_DB_URL="$URL"

# ⓗ 같은 상태 + 이름으로 면제 → green 이되 **건수가 드러나야** 한다
expect green "ⓗ 이름으로 면제" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_ONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_PREVIEW_TILE_DB_URL="$URL"
case "$LAST_OUT" in
  *"면제 1"*) echo "[selftest] ⓗ 면제 건수 노출 → OK" ;;
  *) echo "[selftest] ⓗ 면제 건수가 출력에 없다 ✗ — 건수를 숨긴 통과는 green-by-skip 이다"
     echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("ⓗ 건수 노출") ;;
esac

# ⓖ 발행은 있는데 **쓸 수 있는 타일 0** → red
rm -f "$SLOT/tile-good.tif"
expect red "ⓖ 발행 있음·쓸 수 있는 타일 0" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_ONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_PREVIEW_TILE_DB_URL="$URL"

# ⓔ **자리에 타일 0건** → red. 이 자리의 자연스러운 대상 수는 오늘 0 이고,
#   0 을 통과로 세는 게이트는 아무것도 검사하지 않으면서 green 을 찍는다
rm -f "$SLOT"/tile-*.tif
expect red "ⓔ 자리에 타일 0건" COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
  COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_PREVIEW_TILE_DB_URL="$URL"

# ── ⭑ 증보 2026-09-02 — #57 (ⓒ 둘 다) 의 fail-closed 증명 ─────────────────────────
# 자리를 되살린다 — 아래 케이스는 **자리에 쓸 수 있는 타일이 있는 상태**를 봐야 한다.
# (그 상태에서 종전 게이트는 경계 롤로 붙으면 green 을 냈다. 그것이 #57 이다.)
mktiff "$SLOT/tile-good.tif" cog

# ⓙ **경계 롤 이름 미선언 → red(준비)**. 대조를 못 한 것을 통과로 세지 않는다.
out="$(env COLAB_PREVIEW_TILE_PSQL="$TMP/psql" COLAB_PREVIEW_TILE_BOUNDARY_ROLE= \
        COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" COLAB_PREVIEW_TILE_DIR="$SLOT" \
        COLAB_PREVIEW_TILE_DB_URL="$URL" "$GATE" 2>&1)"; rc=$?
if [ $rc -eq 0 ]; then
  echo "[selftest] ⓙ 경계 롤 미선언 → green ✗"; FAILURES+=("ⓙ 경계 롤 미선언")
elif ! printf '%s' "$out" | grep -q 'cause=입력미선언'; then
  echo "[selftest] ⓙ cause=입력미선언 표식이 없다 ✗"; FAILURES+=("ⓙ 원인 표식")
else echo "[selftest] ⓙ 경계 롤 미선언 → red(준비·입력미선언) OK"; fi

# ⓚ ⭑ **경계 롤로 붙은 접속 → red.** #57 의 무늬 그 자체다 — 접속도 성공하고 질의도 에러 없이
#   돌며 읽기 전용 선언까지 달려 있다. 다만 발행이 0 으로 보이고, 종전 게이트는 그 0 을 만나
#   핵심 판정을 건너뛰고 **green** 을 냈다(변이① 이 그것을 재현한다).
expect red "ⓚ 경계 롤 접속" COLAB_PREVIEW_TILE_PSQL="$TMP/psql-boundary" \
  COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" COLAB_PREVIEW_TILE_DIR="$SLOT" \
  COLAB_PREVIEW_TILE_DB_URL="$URL"
case "$LAST_OUT" in
  *'관리자 롤이 아니다'*) echo "[selftest] ⓚ 사유(관리자 롤 아님) → OK" ;;
  *) echo "[selftest] ⓚ 사유가 롤로 말해지지 않는다 ✗"
     echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("ⓚ 사유") ;;
esac

# ⓛ 경계 롤 선언이 **관리자 롤 자신** → 두 조회가 같은 롤로 돌아 값이 같아진다 → red.
expect red "ⓛ 경계 롤 = 관리자 롤" COLAB_PREVIEW_TILE_BOUNDARY_ROLE=postgres \
  COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" COLAB_PREVIEW_TILE_DIR="$SLOT" \
  COLAB_PREVIEW_TILE_DB_URL="$URL"
case "$LAST_OUT" in
  *'관리자 롤 값과 같다'*) echo "[selftest] ⓛ 사유(두 값이 같다) → OK" ;;
  *) echo "[selftest] ⓛ 사유가 대조로 말해지지 않는다 ✗"
     echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("ⓛ 사유") ;;
esac

# ⓜ **스키마만 적용된 빈 DB → red(발행 0건).** 이것이 #57-ⓑ 의 결함 그 자체다 —
#   종전 배선(COLAB_APPLIED_DB_URL_PLATFORM)이 정확히 이 DB 였고, 발행이 구조적으로 0 이었다.
docker exec "$PGC" createdb -U postgres "$SCHEMA_ONLY_DB" >/dev/null 2>&1 \
  || red "스키마 전용 DB 를 만들지 못했다."
docker exec -i "$PGC" psql -q -U postgres -d "$SCHEMA_ONLY_DB" -v ON_ERROR_STOP=1 < "$SCHEMA" \
  >"$TMP/err" 2>&1 || red "스키마 전용 DB 에 선언 스키마를 적용하지 못했다:
$(sed 's/^/     /' "$TMP/err")"
docker exec -i "$PGC" psql -q -U postgres -d "$SCHEMA_ONLY_DB" -v ON_ERROR_STOP=1 \
  -v owner=colab_owner -v app="$BROLE" -v app_password=gateapp < "$APPROLE" >"$TMP/err" 2>&1 \
  || red "스키마 전용 DB 에 경계 롤 권한을 주지 못했다:
$(sed 's/^/     /' "$TMP/err")"
mk_psql "$TMP/psql-schemaonly" "$SCHEMA_ONLY_DB" "-c default_transaction_read_only=on"
expect red "ⓜ 스키마 전용 DB" COLAB_PREVIEW_TILE_PSQL="$TMP/psql-schemaonly" \
  COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" COLAB_PREVIEW_TILE_DIR="$SLOT" \
  COLAB_PREVIEW_TILE_DB_URL="$URL"
case "$LAST_OUT" in
  *'발행 0건'*) echo "[selftest] ⓜ 사유(발행 0건) → OK" ;;
  *) echo "[selftest] ⓜ 사유가 발행 0건으로 말해지지 않는다 ✗"
     echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("ⓜ 사유") ;;
esac

# ── 변이로 오라클을 증명한다 — **검사를 떼면 통과하는가** ────────────────────────────
cp "$READINESS" "$TMP/_readiness.sh"
mutate() { # $1=출력 $2..=sed 식
  local out="$1"; shift
  cp "$GATE" "$out"; for e in "$@"; do sed -i "$e" "$out"; done; chmod +x "$out"
}
run_mutant() { # $1=변이본 $2..=환경변수
  local m="$1"; shift
  env REPO_ROOT="$REPO_ROOT" COLAB_PREVIEW_TILE_BOUNDARY_ROLE="$BROLE" "$@" bash "$m" 2>&1
}

# ⓝ ⭑⭑ **변이① = 종전 게이트의 재현.** 롤 판정 두 겹과 「발행 0건 red」를 통째로 떼면
#   경계 롤 접속(ⓚ 와 **같은 상태**)이 **green** 이 된다. 이것이 #57 의 green-by-skip 이고,
#   ⓚ 의 red 를 만든 것이 이번 회차가 붙인 검사라는 **음성 증명**이다.
mutate "$TMP/mutant-old-gate.sh" \
  '/# ── 3-1\. 롤 판정 ㉮/,/^# ── 3\. 발행 —/{/^# ── 3\. 발행 —/!d}' \
  's/^if \[ "\$EMITTED" = "\$EMITTED_BOUNDARY" \]; then$/if false; then/' \
  's/^if \[ "\$EMITTED" -eq 0 \]; then$/if false; then/'
out="$(run_mutant "$TMP/mutant-old-gate.sh" COLAB_PREVIEW_TILE_PSQL="$TMP/psql-boundary" \
        COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" COLAB_PREVIEW_TILE_DIR="$SLOT" \
        COLAB_PREVIEW_TILE_DB_URL="$URL")"; rc=$?
if [ $rc -eq 0 ]; then
  echo "[selftest] ⓝ 변이①(종전 게이트 재현) → green — **음성 증명 OK**"
  echo "           같은 상태에서 새 게이트는 red(ⓚ) · 검사를 떼면 green — green-by-skip 이 재현된다"
else
  echo "[selftest] ⓝ 변이①이 여전히 red ✗ — ⓚ 의 red 가 이번 회차의 검사에서 온 것이 아니다"
  echo "$out" | sed 's/^/           /'; FAILURES+=("ⓝ 변이① 음성 증명")
fi

# ⓞ 변이② — **㉯ 대조만 무력화한다.** ⓛ 와 같은 상태가 green 이 되면 ⓛ 의 red 를 만든 것이
#   두 값의 대조라는 증명이다(관리자 롤 판정 ㉮ 는 그대로 두므로 ㉮ 가 대신 잡은 것이 아니다).
mutate "$TMP/mutant-no-compare.sh" \
  's/^if \[ "\$EMITTED" = "\$EMITTED_BOUNDARY" \]; then$/if false; then/'
out="$(run_mutant "$TMP/mutant-no-compare.sh" COLAB_PREVIEW_TILE_PSQL="$TMP/psql" \
        COLAB_PREVIEW_TILE_BOUNDARY_ROLE=postgres COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" \
        COLAB_PREVIEW_TILE_DIR="$SLOT" COLAB_PREVIEW_TILE_DB_URL="$URL")"; rc=$?
if [ $rc -eq 0 ]; then
  echo "[selftest] ⓞ 변이②(㉯ 대조 제거) → green — **오라클 증명 OK**"
else
  echo "[selftest] ⓞ 변이②가 여전히 red ✗ — ⓛ 의 red 가 ㉯ 대조에서 온 것이 아니다"
  echo "$out" | sed 's/^/           /'; FAILURES+=("ⓞ 변이② 오라클")
fi

# ⓟ 변이③ — **읽기 전용 탐침 절을 뗀다.** 쓸 수 있는 접속이 통과하면, 탐침이 그 차이를 만든다.
mutate "$TMP/mutant-no-probe.sh" '/# ── 3-0\. 읽기 전용 증명/,/^# ── 3-1\. 롤 판정/{/^# ── 3-1\. 롤 판정/!d}'
out="$(run_mutant "$TMP/mutant-no-probe.sh" COLAB_PREVIEW_TILE_PSQL="$TMP/psql-rw" \
        COLAB_PREVIEW_TILE_EXEMPT="$EXEMPT_NONE" COLAB_PREVIEW_TILE_DIR="$SLOT" \
        COLAB_PREVIEW_TILE_DB_URL="$URL")"; rc=$?
if [ $rc -eq 0 ]; then
  echo "[selftest] ⓟ 변이③(탐침 제거) → green — **오라클 증명 OK**"
else
  echo "[selftest] ⓟ 변이③이 여전히 red ✗ — 읽기 전용 red 가 탐침에서 온 것이 아니다"
  echo "$out" | sed 's/^/           /'; FAILURES+=("ⓟ 변이③ 오라클")
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::preview-tile-slot-selftest red — 실패한 케이스: ${FAILURES[*]}"
  exit 1
fi
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict preview-tile-slot-selftest
echo "preview-tile-slot-selftest green — 14 케이스(red 7 · 미선언 5 · green 2 · 변이 3) ＋ 사유 대조 4 ＋ 면제 건수 노출 1 ＋ 원인 표식 1 = 검사 20건 전건 기대대로"
exit 0
