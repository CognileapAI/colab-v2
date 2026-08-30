#!/usr/bin/env bash
# autometa-loss 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# ⭑ ⟨증보 2026-08-31 · `PLAN-SoT §9 〈237〉` · `#50` 해소⟩ **대조 정본이 staging 실물로 바뀌었다.**
#   배선이 바뀌었으므로 **바뀐 배선이 여전히 fail-closed 임을 여기서 다시 증명한다.** 더한 것 다섯:
#   ⓖ **스키마 전용(빈) DB 를 가리키면 red** — **이것이 정확히 #50 의 결함**이다. 스키마만 적용된
#      DB 는 접수분이 구조적으로 0건이고, 0건을 통과로 세면 게이트가 아무것도 안 보면서 green 을 찍는다.
#   ⓗ 접속 실패 → red (못 붙은 것을 skip·green 으로 세지 않는다)
#   ⓘ **선언이 읽기 전용이 아니면 red** — 이 게이트는 실물을 들여다볼 뿐 한 글자도 쓰지 않는다
#   ⓙ **변이① 탐침을 떼면 쓸 수 있는 접속이 통과한다** → 오라클이 그 차이를 만든다는 증명
#   ⓚ **변이② 읽기 전용 트랜잭션을 풀면 탐침이 실제로 쓰기를 잡는다**(사유까지 대조)
#
# 케이스 12종 — 열은 red 여야 하고 둘은 green 이어야 하며, green 하나는 **건수를 드러내야** 한다.
#   ⓐ 대조 정본 미지정      → red(준비·입력미선언)  (환경 부재를 skip 으로 세지 않는다.
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
READINESS="$REPO_ROOT/gates/tools/_readiness.sh"
SCHEMA="$REPO_ROOT/db/platform/schema.sql"
SEED="$REPO_ROOT/services/core-api/tests/fixtures/seed.sql"
DB="autometaloss"
FAILURES=()

red() { echo "::error::autometa-loss-selftest red — $*"; exit 1; }

for f in "$GATE" "$READINESS" "$SCHEMA" "$SEED"; do
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
# 두 벌을 만든다. 앞은 **읽기 전용으로 선언된 접속**(실물 URL 이 그러하다),
# 뒤는 그 선언이 빠진 접속 — 게이트가 그 차이를 잡는지 보려는 것이다.
mk_psql() { # $1=파일 $2=DB $3=PGOPTIONS
  cat > "$1" <<EOF
#!/usr/bin/env bash
shift            # 첫 인자(URL)를 버린다 — 포트를 publish 하지 않으므로 URL 로 못 붙는다
exec docker exec -e PGOPTIONS="$3" -i "$PGC" psql -U postgres -d "$2" "\$@"
EOF
  chmod +x "$1"
}
mk_psql "$TMP/psql"    "$DB" "-c default_transaction_read_only=on"
mk_psql "$TMP/psql-rw" "$DB" ""

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
expect red "ⓐ 대조 정본 미지정" COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" COLAB_AUTOMETA_STAGING_DB_URL=
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
  COLAB_AUTOMETA_STAGING_DB_URL="$URL"

# ⓑ' 파일은 있는데 항목이 없다 — 「없는 것」을 「0건」으로 세지 않는다
printf '[exempt]\nreason = "항목 자체가 없다"\n' > "$TMP/exempt-empty.toml"
expect red "ⓑ' 면제 항목 부재" COLAB_AUTOMETA_EXEMPT="$TMP/exempt-empty.toml" \
  COLAB_AUTOMETA_STAGING_DB_URL="$URL"

# ⓓ 발행 3 · 반영 0
expect red "ⓓ 유실 3건" COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" \
  COLAB_AUTOMETA_STAGING_DB_URL="$URL"

# ⓕ 같은 상태 + 이름으로 면제 → green 이되 **건수가 드러나야** 한다
expect green "ⓕ 면제 선언" COLAB_AUTOMETA_EXEMPT="$EXEMPT_ONE" \
  COLAB_AUTOMETA_STAGING_DB_URL="$URL"
case "$LAST_OUT" in
  *"면제 3"*) echo "[selftest] ⓕ 면제 건수 노출 → OK" ;;
  *) echo "[selftest] ⓕ 면제 건수가 출력에 없다 ✗ — 건수를 숨긴 통과는 green-by-skip 이다"
     echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("ⓕ 건수 노출") ;;
esac

# ⓔ 전건 반영 → green
su -c "UPDATE d3_dataset_autometa SET format='GeoTIFF', crs='EPSG:4326', grid='9x9' WHERE dataset_id='$DS';" >/dev/null
expect green "ⓔ 전건 반영" COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" \
  COLAB_AUTOMETA_STAGING_DB_URL="$URL"

# ⓒ 대조 대상 0건 → red (**여기가 이 게이트의 존재 이유다**)
su -c "DELETE FROM d5_pipeline_event WHERE upload_id='$UP';" >/dev/null
expect red "ⓒ 대상 0건" COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" \
  COLAB_AUTOMETA_STAGING_DB_URL="$URL"

# ── 여기부터 **새 배선(staging 실물 대조)** 의 fail-closed 증명 ──────────────────
# ⓒ 가 사건을 지웠으므로 되돌린다 — 아래 변이 케이스는 **대상이 있는 상태**를 봐야 한다.
su <<SQL >"$TMP/err" 2>&1 || red "사건을 되돌리지 못했다:
$(sed 's/^/     /' "$TMP/err")"
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


# ⓖ 스키마만 적용된 **빈 DB** 를 대조 정본으로 가리키면 red.
#   **이것이 #50 의 결함 그 자체다** — 접수분이 구조적으로 0건인 DB 를 보게 두면
#   게이트는 아무것도 안 보면서 통과하거나(그랬다면 더 나빴다) 영원히 red 다.
SCHEMA_ONLY_DB="autometaloss_schemaonly"
docker exec "$PGC" createdb -U postgres "$SCHEMA_ONLY_DB" >/dev/null 2>&1 \
  || red "스키마 전용 DB 를 만들지 못했다."
docker exec -i "$PGC" psql -q -U postgres -d "$SCHEMA_ONLY_DB" -v ON_ERROR_STOP=1 < "$SCHEMA" \
  >"$TMP/err" 2>&1 || red "스키마 전용 DB 에 선언 스키마를 적용하지 못했다:
$(sed 's/^/     /' "$TMP/err")"
mk_psql "$TMP/psql-schemaonly" "$SCHEMA_ONLY_DB" "-c default_transaction_read_only=on"
out="$(env COLAB_AUTOMETA_PSQL="$TMP/psql-schemaonly" COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" \
        COLAB_AUTOMETA_STAGING_DB_URL="$URL" "$GATE" 2>&1)"; rc=$?
if [ $rc -eq 0 ]; then
  echo "[selftest] ⓖ 스키마 전용 DB → green ✗ — **빈 DB 를 통과시키면 게이트가 아무것도 안 본다**"
  echo "$out" | sed 's/^/           /'; FAILURES+=("ⓖ 스키마 전용 DB")
elif ! printf '%s' "$out" | grep -q '대조 대상 0건'; then
  echo "[selftest] ⓖ red 이긴 한데 사유가 「대조 대상 0건」이 아니다 ✗"
  echo "$out" | sed 's/^/           /'; FAILURES+=("ⓖ 사유")
else
  echo "[selftest] ⓖ 스키마 전용 DB → red(대상 0건) OK"
fi

# ⓗ 접속 실패 → red. **주입 psql 을 걷고 실물 psql 로** 닿지 않는 자리를 가리킨다.
expect red "ⓗ 접속 실패" COLAB_AUTOMETA_PSQL=psql COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" \
  COLAB_AUTOMETA_STAGING_DB_URL="postgresql://colab@127.0.0.1:1/nowhere?connect_timeout=2"
case "$LAST_OUT" in
  *'읽기 전용 접속임을 증명하지 못했다'*) echo "[selftest] ⓗ 사유(증명 실패) → OK" ;;
  *) echo "[selftest] ⓗ 사유가 접속 실패로 말해지지 않는다 ✗"
     echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("ⓗ 사유") ;;
esac

# ⓘ 선언이 읽기 전용이 아니면 red — 게이트는 실물을 **들여다볼 뿐** 한 글자도 쓰지 않는다.
expect red "ⓘ 읽기 전용 아닌 선언" COLAB_AUTOMETA_PSQL="$TMP/psql-rw" \
  COLAB_AUTOMETA_EXEMPT="$EXEMPT_NONE" COLAB_AUTOMETA_STAGING_DB_URL="$URL"
case "$LAST_OUT" in
  *'읽기 전용이 아니다'*) echo "[selftest] ⓘ 사유(읽기 전용 아님) → OK" ;;
  *) echo "[selftest] ⓘ 사유가 읽기 전용으로 말해지지 않는다 ✗"
     echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("ⓘ 사유") ;;
esac

# ── 변이로 오라클을 증명한다 — **검사를 떼면 통과하는가** ────────────────────────────
cp "$READINESS" "$TMP/_readiness.sh"
mutate() { # $1=출력 $2..=sed 식
  local out="$1"; shift
  cp "$GATE" "$out"; for e in "$@"; do sed -i "$e" "$out"; done; chmod +x "$out"
}

# ⓙ 변이① — **읽기 전용 검사(탐침 절)를 통째로 뗀다.** 같은 상태(ⓘ)가 green 이 되면,
#    ⓘ 의 red 를 만든 것이 바로 그 검사라는 뜻이다. 오라클이 살아 있다는 증명이다.
mutate "$TMP/mutant-no-probe.sh" '/# ── 2-1\. 읽기 전용 증명/,/^SQL_ARRAY=/{/^SQL_ARRAY=/!d}'
out="$(env REPO_ROOT="$REPO_ROOT" COLAB_AUTOMETA_PSQL="$TMP/psql-rw" \
        COLAB_AUTOMETA_EXEMPT="$EXEMPT_ONE" COLAB_AUTOMETA_STAGING_DB_URL="$URL" \
        bash "$TMP/mutant-no-probe.sh" 2>&1)"; rc=$?
if [ $rc -eq 0 ]; then
  echo "[selftest] ⓙ 변이①(탐침 제거) → green — **오라클 증명 OK**(검사를 떼면 통과한다)"
else
  echo "[selftest] ⓙ 변이①(탐침 제거)이 여전히 red ✗ — ⓘ 의 red 가 이 검사에서 온 것이 아니다"
  echo "$out" | sed 's/^/           /'; FAILURES+=("ⓙ 변이① 오라클")
fi

# ⓚ 변이② — 선언 검사만 떼고 **트랜잭션을 읽기 전용에서 푼다.** 그러면 쓰기 탐침이
#    실제로 성공하고, 게이트는 그것을 **쓰기 탐침이 통과했다**로 잡아야 한다.
#    (탐침이 진짜로 쓰기를 시도한다는 증명이다 — 문구만 맞추고 아무것도 안 하는 검사가 아니다.)
mutate "$TMP/mutant-rw-txn.sh" \
  "s/^  \*'::decl::off'\*)/  *'::decl::never-matches'*)/" \
  "s/^BEGIN READ ONLY;\$/BEGIN;/"
out="$(env REPO_ROOT="$REPO_ROOT" COLAB_AUTOMETA_PSQL="$TMP/psql-rw" \
        COLAB_AUTOMETA_EXEMPT="$EXEMPT_ONE" COLAB_AUTOMETA_STAGING_DB_URL="$URL" \
        bash "$TMP/mutant-rw-txn.sh" 2>&1)"; rc=$?
if [ $rc -ne 0 ] && printf '%s' "$out" | grep -q '쓰기 탐침이 통과했다'; then
  echo "[selftest] ⓚ 변이②(읽기 전용 해제) → red(쓰기 탐침 통과) — **탐침이 실제로 쓴다** OK"
else
  echo "[selftest] ⓚ 변이②가 쓰기를 잡지 못했다 ✗ (rc=$rc) — 탐침이 아무것도 시도하지 않는다"
  echo "$out" | sed 's/^/           /'; FAILURES+=("ⓚ 변이② 탐침")
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::autometa-loss-selftest red — 실패한 케이스: ${FAILURES[*]}"
  exit 1
fi
echo "autometa-loss-selftest green — 12 케이스(red 8 · green 2 · 변이 2) ＋ 사유 대조 4 ＋ 면제 건수 노출 1 = 검사 17건 전건 기대대로"
exit 0
