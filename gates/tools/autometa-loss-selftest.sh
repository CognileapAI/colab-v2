#!/usr/bin/env bash
# autometa-loss 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 케이스 7종 — 다섯은 red 여야 하고 둘은 green 이어야 하며, green 하나는 **건수를 드러내야** 한다.
#   ⓐ 적용 DB 미지정        → red(준비·입력미선언)  (환경 부재를 skip 으로 세지 않는다.
#                             다만 「대상이 규율을 어겼다」가 아니라 「입력이 선언되지 않았다」로 말한다)
#   ⓑ 면제 선언 파일 부재    → red   (「선언이 없다」와 「면제가 없다」는 다르다)
#   ⓒ 대조 대상 0건          → red   (**대상 0건은 통과가 아니다** — 이 게이트의 핵심)
#   ⓓ 발행 3 · 반영 0        → red   (유실 그 자체)
#   ⓔ 발행 3 · 반영 3        → green
#   ⓕ 미반영이지만 **이름으로 면제** → green **＋ 면제 건수가 출력에 나타난다**
#
# 실제 db/ · services/ · gates/config 에는 **한 글자도 쓰지 않는다** — 임시 디렉터리와
# 일회용 postgres 안에서만 일어난다. 포트를 하나도 publish 하지 않는다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/autometa-loss.sh"
SCHEMA="$REPO_ROOT/db/platform/schema.sql"
SEED="$REPO_ROOT/services/core-api/tests/fixtures/seed.sql"
DB="autometaloss"
FAILURES=()

red() { echo "::error::autometa-loss-selftest red — $*"; exit 1; }

for f in "$GATE" "$SCHEMA" "$SEED"; do
  [ -f "$f" ] || red "판정 재료가 없다: ${f#"$REPO_ROOT"/}. 대상 0건은 통과가 아니다."
done

# shellcheck source=/dev/null
. "$REPO_ROOT/gates/tools/_pg.sh"
pg_start autometa-loss-selftest || exit $?   # 준비 실패는 78 로 그대로 전달한다

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" autometa-loss-XXXXXX)"
cleanup_all() { rm -rf "$TMP"; pg_cleanup; }
trap cleanup_all EXIT INT TERM

su() { docker exec -i "$PGC" psql -q -U postgres -d "$DB" -v ON_ERROR_STOP=1 "$@"; }

docker exec "$PGC" createdb -U postgres "$DB" >/dev/null 2>&1 || red "DB 를 만들지 못했다."
su < "$SCHEMA" >"$TMP/err" 2>&1 || red "선언 스키마를 적용하지 못했다:
$(sed 's/^/     /' "$TMP/err")"
su < "$SEED" >"$TMP/err" 2>&1 || red "시드를 넣지 못했다:
$(sed 's/^/     /' "$TMP/err")"

# ── psql 주입 — 게이트는 URL 로 부르고, 여기서는 그 URL 을 무시하고 컨테이너 안에서 돈다 ──
cat > "$TMP/psql" <<EOF
#!/usr/bin/env bash
shift            # 첫 인자(URL)를 버린다 — 포트를 publish 하지 않으므로 URL 로 못 붙는다
exec docker exec -i "$PGC" psql -U postgres -d "$DB" "\$@"
EOF
chmod +x "$TMP/psql"

LAB="0000000000000000000000000A"
ACC="000000000000000000000000A1"
DS="0000000000000000000000DSX1"
UP="01JQ0000000000000000000091"
FID="01JQ0000000000000000000092"

# ── 픽스처 — 등록까지 끝난 업로드 1건 · 사건이 값 셋을 날랐고 장부는 비어 있다 ──────
su <<SQL >"$TMP/err" 2>&1 || red "픽스처를 넣지 못했다:
$(sed 's/^/     /' "$TMP/err")"
INSERT INTO d3_dataset (id, lab_id, owner_account_id, uploader_account_id)
VALUES ('$DS', '$LAB', '$ACC', '$ACC');
INSERT INTO d3_dataset_description (dataset_id, lab_id, name) VALUES ('$DS', '$LAB', '유실 감지 픽스처');
INSERT INTO d3_dataset_autometa (dataset_id, lab_id) VALUES ('$DS', '$LAB');
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, size_bytes, storage_key)
VALUES ('$FID', '$LAB', '$DS', '본체', 'x.nc', 10, 'k/x');
INSERT INTO d5_upload (id, lab_id, uploader_account_id, expires_at, registered_at)
VALUES ('$UP', '$LAB', '$ACC', now() + interval '1 day', now());
INSERT INTO d5_upload_file (id, lab_id, upload_id, kind, file_name, byte_size, storage_key)
VALUES ('$FID', '$LAB', '$UP', '본체', 'x.nc', 10, 'k/x');
INSERT INTO d5_pipeline_event
  (id, lab_id, actor_account_id, upload_id, event_type, schema_version, source,
   idempotency_key, payload)
VALUES ('01JQ0000000000000000000093', '$LAB', '$ACC', '$UP', 'file.format-detected', '1.0',
        'pipeline-worker', 'file.format-detected:$UP',
        '{"format":"GeoTIFF","renderable":true,"uniform":true}'),
       ('01JQ0000000000000000000094', '$LAB', '$ACC', '$UP', 'file.header-parsed', '1.0',
        'pipeline-worker', 'file.header-parsed:$UP',
        '{"variables":["LST"],"period":null,"crs":"EPSG:4326","grid":"9x9","byteSizeTotal":10,"unreadableFiles":[]}');
SQL

EXEMPT_NONE="$TMP/exempt-none.toml"
printf '[exempt]\ndatasets = []\nreason = "선언은 있고 면제는 없다"\n' > "$EXEMPT_NONE"
EXEMPT_ONE="$TMP/exempt-one.toml"
printf '[exempt]\ndatasets = ["%s"]\nreason = "소급 반영 별건"\n' "$DS" > "$EXEMPT_ONE"

URL="postgresql://ignored/ignored"        # 주입된 psql 이 무시한다. **값은 출력하지 않는다**
run_gate() { env COLAB_AUTOMETA_PSQL="$TMP/psql" "$@" "$GATE" 2>&1; }

expect() { # $1=green|red $2=라벨 $3..=환경변수
  local want="$1" label="$2"; shift 2
  local out rc got
  out="$(run_gate "$@")"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$want" ]; then
    echo "[selftest] $label → $got OK"
    LAST_OUT="$out"
  else
    echo "[selftest] $label → $got (기대 $want) ✗"
    echo "$out" | sed 's/^/           /'
    FAILURES+=("$label")
    LAST_OUT="$out"
  fi
}

# ⓐ 적용 DB 미지정 — red 이되 **원인을 참말로 말해야 한다.**
#   대상을 한 건도 못 봤으므로 「검사 대상이 규율을 어겼다」가 아니다. 「입력이 선언되지 않았다」다.
expect red "ⓐ 적용 DB 미지정" COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" COLAB_APPLIED_DB_URL_PLATFORM=
case "$LAST_OUT" in
  *cause=입력미선언*missing=*)
    if printf '%s\n' "$LAST_OUT" | grep '규율을 어겼다' | grep -qv '아니라'; then
      echo "[selftest] ⓐ 원인 문구 ✗ — 「대상이 규율을 어겼다」로 말한다"; FAILURES+=("ⓐ 거짓 원인 문구")
    else echo "[selftest] ⓐ 원인 표식(입력미선언) → OK"; fi ;;
  *) echo "[selftest] ⓐ cause=입력미선언 표식이 없다 ✗ — 미선언이 판정 red 로 찍힌다"
     echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("ⓐ 원인 표식") ;;
esac

# ⓑ 면제 선언 파일 부재
expect red "ⓑ 면제 선언 부재" COLAB_AUTOMETA_EXEMPT="$TMP/없는파일.toml" \
  COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓑ' 파일은 있는데 항목이 없다 — 「없는 것」을 「0건」으로 세지 않는다
printf '[exempt]\nreason = "항목 자체가 없다"\n' > "$TMP/exempt-empty.toml"
expect red "ⓑ' 면제 항목 부재" COLAB_AUTOMETA_EXEMPT="$TMP/exempt-empty.toml" \
  COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓓ 발행 3 · 반영 0
expect red "ⓓ 유실 3건" COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" \
  COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓕ 같은 상태 + 이름으로 면제 → green 이되 **건수가 드러나야** 한다
expect green "ⓕ 면제 선언" COLAB_AUTOMETA_EXEMPT="$EXEMPT_ONE" \
  COLAB_APPLIED_DB_URL_PLATFORM="$URL"
case "$LAST_OUT" in
  *"면제 3"*) echo "[selftest] ⓕ 면제 건수 노출 → OK" ;;
  *) echo "[selftest] ⓕ 면제 건수가 출력에 없다 ✗ — 건수를 숨긴 통과는 green-by-skip 이다"
     echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("ⓕ 건수 노출") ;;
esac

# ⓔ 전건 반영 → green
su -c "UPDATE d3_dataset_autometa SET format='GeoTIFF', crs='EPSG:4326', grid='9x9' WHERE dataset_id='$DS';" >/dev/null
expect green "ⓔ 전건 반영" COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" \
  COLAB_APPLIED_DB_URL_PLATFORM="$URL"

# ⓒ 대조 대상 0건 → red (**여기가 이 게이트의 존재 이유다**)
su -c "DELETE FROM d5_pipeline_event WHERE upload_id='$UP';" >/dev/null
expect red "ⓒ 대상 0건" COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" \
  COLAB_APPLIED_DB_URL_PLATFORM="$URL"

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::autometa-loss-selftest red — 실패한 케이스: ${FAILURES[*]}"
  exit 1
fi
echo "autometa-loss-selftest green — 7 케이스(red 5 · green 2) ＋ 면제 건수 노출 1 = 검사 8건 전건 기대대로"
exit 0
