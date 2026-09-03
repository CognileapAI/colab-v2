#!/usr/bin/env bash
# artifact-ownership 이 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 케이스 — red 열둘 · green 넷 · 변이 셋. green 셋은 **건수를 드러내야** 한다.
#   ⓐ 대조 정본 미지정            → red(준비·입력미선언)
#   ⓑ 선언 파일 부재              → red   (「선언이 없다」와 「면제가 없다」는 다르다)
#   ⓑ' [exempt] keys 항목 부재     → red
#   ⓑ'' [legacy] tolerate 항목 부재 → red  (보류를 **선언 없이** 넘기는 길을 두지 않는다)
#   ⓒ 자리 경로 미선언             → red
#   ⓓ 자리 경로가 없는 디렉터리     → red
#   ⓔ **자리에 대상 0건**          → red   ← 0 을 통과로 세면 아무것도 안 본다
#   ⓕ 고아 1벌이 **선언 없이**      → red   (판정을 미루는 자리를 열어 두지 않는다)
#   ⓖ 그 고아를 **키로 면제**       → green ＋ 건수 노출
#   ⓗ 살아 있다 1벌                → green
#   ⓘ ⭑ **구판 1벌 ＋ tolerate=true** → green ＋ **「판정 불가」 건수 노출** ← **덫 ②**
#   ⓙ 같은 상태 ＋ tolerate=false   → red
#   ⓚ 경계 롤로 붙은 접속          → red   (#57 의 무늬 — 관리자 롤이 아니다)
#   ⓛ 경계 롤 = 관리자 롤          → red   (두 롤이 같은 값을 낸다)
#   ⓜ 스키마 전용 빈 DB            → red   (**원장 두 표 0행** — 그 0 이면 전건이 고아로 뜬다)
#   ⓝ 경계 롤 이름 미선언           → red(준비)
#   ⓞ 사이드카 규약 위반           → red   (판 2 인데 sources 가 비었다)
#   ⓟ ⭑ **덫 ① 음성 시험**         → green ＋ **살아 있다 1**
#        `baked_for` 는 **낡은 uploadId** 인데 그 조각 fileId 는 이미 `d3_file` 에 등록돼 있다.
#        **등록 전환 뒤의 정상 상태**이고, `baked_for` 로 판정하면 여기서 「불일치」가 난다.
#   ⓠ ⭑ **음성 시험 — `tile-` 만 있는 자리** → red(대상 0건)
#        지도 타일은 **대상이 아니다**. 대상으로 셌다면 여기가 green 이 된다 (완료 정의 ⑷).
#   ⓡ ⭑ **음성 시험 — 접수분 루트·데이터셋 무접촉** : 게이트 전 회차 뒤 접수분 트리가 그대로다.
#        (⚠ 이 게이트는 **아무것도 지우지 않는다** — 회수 집행은 `invalidation.apply()` 한 자리다.)
#
# 실제 db/ · services/ · gates/config 에는 **한 글자도 쓰지 않는다** — 임시 디렉터리와
# 일회용 postgres 안에서만 일어난다. 포트를 하나도 publish 하지 않는다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/artifact-ownership.sh"
GRADER="$REPO_ROOT/gates/tools/artifact_ownership.py"
RULE="$REPO_ROOT/services/viz-render/src/colab_viz/domains/d7_visualization/ownership.py"
SCHEMA="$REPO_ROOT/db/platform/schema.sql"
SEED="$REPO_ROOT/services/core-api/tests/fixtures/seed.sql"
READINESS="$REPO_ROOT/gates/tools/_readiness.sh"
APPROLE="$REPO_ROOT/services/core-api/ops/app-role.sql"
DB="artifactownership"
SCHEMA_ONLY_DB="artifactownership_schemaonly"
BROLE="colab_app"
FAILURES=()
# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나.
# 종전에는 이 파일의 expect() 가 종료코드 78(준비 실패)을 그냥 red 로 접어
# **「기대한 red」로 셌다** — 그 케이스는 판정된 적이 없는데 출력은 OK 라고 말했다
# (2026-09-03 코드리뷰 #6 · `CLAUDE.md §4` green-by-skip).
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

red() { echo "::error::artifact-ownership-selftest red — $*"; exit 1; }

for f in "$GATE" "$GRADER" "$RULE" "$READINESS" "$SCHEMA" "$SEED" "$APPROLE"; do
  [ -f "$f" ] || red "판정 재료가 없다: ${f#"$REPO_ROOT"/}. 대상 0건은 통과가 아니다."
done

# shellcheck source=/dev/null
. "$REPO_ROOT/gates/tools/_pg.sh"
pg_start artifact-ownership-selftest || exit $?

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" artifact-owner-st-XXXXXX)"
cleanup_all() { rm -rf "$TMP"; pg_cleanup; }
trap cleanup_all EXIT INT TERM

su() { docker exec -i "$PGC" psql -q -U postgres -d "$DB" -v ON_ERROR_STOP=1 "$@"; }

docker exec "$PGC" createdb -U postgres "$DB" >/dev/null 2>&1 || red "DB 를 만들지 못했다."
su < "$SCHEMA" >"$TMP/err" 2>&1 || red "선언 스키마를 적용하지 못했다:
$(sed 's/^/     /' "$TMP/err")"
su < "$SEED" >"$TMP/err" 2>&1 || red "시드를 넣지 못했다:
$(sed 's/^/     /' "$TMP/err")"
su -v owner=colab_owner -v app="$BROLE" -v app_password=gateapp < "$APPROLE" >"$TMP/err" 2>&1 \
  || red "경계 롤 부트스트랩이 실패했다:
$(sed 's/^/     /' "$TMP/err")"

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
# ⚠ ULID 는 **Crockford base32** 다 — `I`·`L`·`O`·`U` 를 쓰면 `ulid` 도메인 CHECK 가 거절한다
#   (실측 2026-09-02 · `ulid_crockford_base32`). 픽스처 id 에 그 넷을 넣지 않는다.
DS="0000000000000000000000DSA1"   # 시드가 이미 세운 데이터셋 — 여기서 다시 짓지 않는다
UP="01JQ00000000000000000000P1"
FID_REG="01JQ00000000000000000000F1"   # d3_file 에 있다 = 등록된 데이터셋의 파일
FID_UP="01JQ00000000000000000000F2"    # d5_upload_file 에만 있다 = 접수분
FID_GONE="01JQ00000000000000000000X9"  # 어느 표에도 없다 = 고아

# ── 원장 픽스처 — **등록된 파일 하나 ＋ 접수분 파일 하나** ──────────────────
su <<SQL >"$TMP/err" 2>&1 || red "픽스처를 넣지 못했다:
$(sed 's/^/     /' "$TMP/err")"
INSERT INTO d5_upload (id, lab_id, uploader_account_id, expires_at)
VALUES ('$UP', '$LAB', '$ACC', now() + interval '1 day');
INSERT INTO d5_upload_file (id, lab_id, upload_id, kind, file_name, storage_key,
                            carries_lat, carries_lon)
VALUES ('$FID_REG', '$LAB', '$UP', '본체', 'a.tif', 'uploads/$UP/$FID_REG', false, false),
       ('$FID_UP',  '$LAB', '$UP', '본체', 'b.tif', 'uploads/$UP/$FID_UP',  false, false);
-- ⭑ NB-A 동일성 — 등록 전환은 `d5_upload_file.id` 를 `d3_file.id` 로 **그대로** 옮긴다.
--   업로드→데이터셋 FK 는 없다(불변규칙 1). **그 동일성이 이 게이트의 유일한 다리다.**
INSERT INTO d3_file (id, lab_id, dataset_id, kind, file_name, storage_key, carries_lat, carries_lon)
VALUES ('$FID_REG', '$LAB', '$DS', '본체', 'a.tif', 'uploads/$DS/$FID_REG', false, false);
SQL

# ── 자리 픽스처 — 한 벌 = 같은 키 아래 `.png` ＋ `.json` ────────────────────
mkgroup() { # $1=자리 $2=키 $3=사이드카 JSON(빈 문자열이면 사이드카 없음)
  mkdir -p "$1"
  printf '\x89PNG-fixture' > "$1/$2.png"
  [ -n "$3" ] && printf '%s' "$3" > "$1/$2.json"
  return 0
}
SC_LIVE="{\"sidecarVersion\":2,\"name\":\"live.png\",\"layer\":\"지도형\",\"source\":\"$FID_REG\",\"sources\":[\"$FID_REG\"],\"baked_for\":{\"target_id\":\"$UP\",\"is_upload\":true}}"
SC_ORPHAN="{\"sidecarVersion\":2,\"name\":\"o.png\",\"layer\":\"지도형\",\"source\":\"$FID_GONE\",\"sources\":[\"$FID_GONE\"],\"baked_for\":{\"target_id\":\"$UP\",\"is_upload\":true}}"
SC_LEGACY="{\"name\":\"old.png\",\"source\":\"$FID_GONE\",\"crs\":\"EPSG:3857\"}"
SC_BROKEN="{\"sidecarVersion\":2,\"name\":\"x.png\",\"source\":\"\",\"sources\":[],\"baked_for\":{\"target_id\":\"$UP\",\"is_upload\":true}}"

DECL_NONE="$TMP/decl-none.toml"
printf '[exempt]\nkeys = []\nreason = "선언은 있고 면제는 없다"\n[legacy]\ntolerate = true\nreason = "보류"\n' > "$DECL_NONE"
DECL_ORPHAN="$TMP/decl-orphan.toml"
printf '[exempt]\nkeys = ["orphankey"]\nreason = "알고 있는 잔재"\n[legacy]\ntolerate = true\nreason = "보류"\n' > "$DECL_ORPHAN"
DECL_STRICT="$TMP/decl-strict.toml"
printf '[exempt]\nkeys = []\nreason = "없다"\n[legacy]\ntolerate = false\nreason = "구판을 더는 넘기지 않는다"\n' > "$DECL_STRICT"

URL="postgresql://ignored/ignored"   # 주입된 psql 이 무시한다. **값은 출력하지 않는다**

expect() { # $1=green|red $2=라벨 $3..=환경변수
  local want="$1" label="$2"; shift 2
  local out rc got
  out="$(env COLAB_ARTIFACT_OWNER_PSQL="$TMP/psql" \
             COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE="$BROLE" \
             "$@" "$GATE" 2>&1)"; rc=$?
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
says() { # $1=라벨 $2=찾을 말
  case "$LAST_OUT" in
    *"$2"*) echo "[selftest] $1 사유·건수 노출 → OK" ;;
    *) echo "[selftest] $1 에 「$2」 가 없다 ✗ — 건수를 숨긴 통과는 green-by-skip 이다"
       echo "$LAST_OUT" | sed 's/^/           /'; FAILURES+=("$1 노출") ;;
  esac
}

SLOT="$TMP/slot"; mkdir -p "$SLOT"
mkgroup "$SLOT" "livekey" "$SC_LIVE"

# ── ⓐ~ⓓ 준비 red ───────────────────────────────────────────────────────────
expect 미선언 "ⓐ 대조 정본 미지정" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL=
says "ⓐ" "cause=입력미선언"

expect 미선언 "ⓑ 선언 파일 부재" COLAB_ARTIFACT_OWNER_EXEMPT="$TMP/없는파일.toml" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL"

printf '[exempt]\nreason = "keys 가 없다"\n[legacy]\ntolerate = true\n' > "$TMP/decl-nokeys.toml"
expect 미선언 "ⓑ' keys 항목 부재" COLAB_ARTIFACT_OWNER_EXEMPT="$TMP/decl-nokeys.toml" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL"

printf '[exempt]\nkeys = []\nreason = "tolerate 가 없다"\n[legacy]\nreason = "x"\n' > "$TMP/decl-notol.toml"
expect 미선언 "ⓑ'' tolerate 항목 부재" COLAB_ARTIFACT_OWNER_EXEMPT="$TMP/decl-notol.toml" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL"

expect 미선언 "ⓒ 자리 경로 미선언" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
  COLAB_ARTIFACT_OWNER_DIR= COLAB_ARTIFACT_OWNER_DB_URL="$URL"

expect 미선언 "ⓓ 없는 디렉터리" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
  COLAB_ARTIFACT_OWNER_DIR="$TMP/없는자리" COLAB_ARTIFACT_OWNER_DB_URL="$URL"

expect 미선언 "ⓝ 경계 롤 미선언" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL" \
  COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE=
says "ⓝ" "cause=입력미선언"

# ── ⓗ · ⓟ 살아 있다 ────────────────────────────────────────────────────────
# ⓟ 는 ⓗ 와 **같은 픽스처**다 — `baked_for` 가 낡은 uploadId($UP)인데 그 조각 fileId 는
#   이미 `d3_file` 에 등록돼 있다. **등록 전환 뒤의 정상 상태**이고, `baked_for` 를 현재
#   소유로 읽었다면 여기서 「불일치」가 나야 한다. 나지 않는 것이 덫 ① 을 피했다는 증거다.
expect green "ⓗ·ⓟ 살아 있다 1벌 (baked_for 는 낡은 uploadId)" \
  COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" COLAB_ARTIFACT_OWNER_DIR="$SLOT" \
  COLAB_ARTIFACT_OWNER_DB_URL="$URL"
says "ⓟ 덫①" "살아 있다 1"

# ── ⓕ·ⓖ 고아 ──────────────────────────────────────────────────────────────
mkgroup "$SLOT" "orphankey" "$SC_ORPHAN"
expect red "ⓕ 고아 1벌 미선언" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL"
says "ⓕ" "orphankey"

expect green "ⓖ 고아를 키로 면제" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_ORPHAN" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL"
says "ⓖ" "고아 1 벌이 **이름으로 선언된 채** 통과했다"
rm -f "$SLOT/orphankey".*

# ── ⓘ·ⓙ ⭑ 덫 ② — 구판은 「고아」가 아니라 「판정 보류」다 ────────────────────
# 이 사이드카의 `source` 는 **어느 표에도 없는 fileId** 다. 그런데도 고아가 아니다 —
# 판 번호·`baked_for` 가 없어 **판정 자체를 하지 않기** 때문이다. 없는 필드를 근거로
# 지우면 그것이 오삭제다.
mkgroup "$SLOT" "legacykey" "$SC_LEGACY"
expect green "ⓘ 구판 1벌 ＋ tolerate=true" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL"
says "ⓘ 덫②" "판정 불가 1"
says "ⓘ 덫②(고아 0)" "고아 0"

expect red "ⓙ 같은 상태 ＋ tolerate=false" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_STRICT" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL"
says "ⓙ" "고아」가 아니다"

# ── ⓞ 사이드카 규약 위반 ────────────────────────────────────────────────────
mkgroup "$SLOT" "brokenkey" "$SC_BROKEN"
expect red "ⓞ 규약 위반(판 2 인데 sources 가 비었다)" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL"
says "ⓞ" "사이드카 규약 위반"
rm -f "$SLOT/brokenkey".* "$SLOT/legacykey".*

# ── ⓠ ⭑ 음성 시험 — `tile-` 만 있는 자리는 **대상 0건** ─────────────────────
TILESLOT="$TMP/tileslot"; mkdir -p "$TILESLOT"
printf 'II*\x00fixture' > "$TILESLOT/tile-abc.tif"
expect red "ⓠ 음성 — tile- 만 있는 자리" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
  COLAB_ARTIFACT_OWNER_DIR="$TILESLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL"
says "ⓠ" "판정 대상 0건"
[ -f "$TILESLOT/tile-abc.tif" ] || { echo "[selftest] ⓠ 지도 타일이 사라졌다 ✗"; FAILURES+=("ⓠ 무접촉"); }

# ── ⓔ 자리에 대상 0건 ──────────────────────────────────────────────────────
EMPTY="$TMP/empty"; mkdir -p "$EMPTY"
expect red "ⓔ 자리에 대상 0건" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
  COLAB_ARTIFACT_OWNER_DIR="$EMPTY" COLAB_ARTIFACT_OWNER_DB_URL="$URL"

# ── ⓡ ⭑ 음성 시험 — 접수분 루트·데이터셋 **무접촉** ─────────────────────────
# 게이트를 전 회차 돌린 뒤에도 접수분 트리와 자리의 파일이 그대로여야 한다.
# **이 게이트는 아무것도 지우지 않는다** — 회수 집행은 `invalidation.apply()` 한 자리다.
UPROOT="$TMP/uploads/$UP"; mkdir -p "$UPROOT/grid"
printf 'ORIGINAL' > "$UPROOT/$FID_REG"; printf 'GRID' > "$UPROOT/grid/lat.npy"
UP_BEFORE="$(find "$TMP/uploads" -type f -exec sha256sum {} + | sort)"
SLOT_BEFORE="$(find "$SLOT" -type f -exec sha256sum {} + | sort)"
expect green "ⓡ 음성 — 회차 뒤 무접촉 확인용 회차" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
  COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL"
UP_AFTER="$(find "$TMP/uploads" -type f -exec sha256sum {} + | sort)"
SLOT_AFTER="$(find "$SLOT" -type f -exec sha256sum {} + | sort)"
if [ "$UP_BEFORE" = "$UP_AFTER" ] && [ -n "$UP_BEFORE" ]; then
  echo "[selftest] ⓡ 접수분 루트 무접촉(원본·기준 격자 그대로) → OK"
else
  echo "[selftest] ⓡ 접수분 루트가 바뀌었다 ✗ — 〈247〉 경계 위반"; FAILURES+=("ⓡ 접수분")
fi
if [ "$SLOT_BEFORE" = "$SLOT_AFTER" ]; then
  echo "[selftest] ⓡ 자리 무접촉(게이트는 지우지 않는다) → OK"
else
  echo "[selftest] ⓡ 게이트가 자리를 바꿨다 ✗ — 지우는 문을 게이트로 늘렸다"; FAILURES+=("ⓡ 자리")
fi

# ── ⓚ·ⓛ·ⓜ 롤·원장 판정 (#57 규율) ──────────────────────────────────────────
expect red "ⓚ 경계 롤 접속" COLAB_ARTIFACT_OWNER_PSQL="$TMP/psql-boundary" \
  COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" COLAB_ARTIFACT_OWNER_DIR="$SLOT" \
  COLAB_ARTIFACT_OWNER_DB_URL="$URL"
says "ⓚ" "관리자 롤이 아니다"

expect red "ⓛ 경계 롤 = 관리자 롤" COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE=postgres \
  COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" COLAB_ARTIFACT_OWNER_DIR="$SLOT" \
  COLAB_ARTIFACT_OWNER_DB_URL="$URL"
says "ⓛ" "관리자 롤 값과 같다"

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
expect red "ⓜ 스키마 전용 DB (원장 0행)" COLAB_ARTIFACT_OWNER_PSQL="$TMP/psql-schemaonly" \
  COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" COLAB_ARTIFACT_OWNER_DIR="$SLOT" \
  COLAB_ARTIFACT_OWNER_DB_URL="$URL"
says "ⓜ" "원장 두 표가 다 0행이다"

# ── 변이로 오라클을 증명한다 — **검사를 떼면 무엇이 달라지는가** ─────────────────
cp "$READINESS" "$TMP/_readiness.sh"   # 변이본이 곁에서 이것을 읽는다
mutate() { local out="$1"; shift; cp "$GATE" "$out"; for e in "$@"; do sed -i "$e" "$out"; done; chmod +x "$out"; }
run_mutant() { local m="$1"; shift; env REPO_ROOT="$REPO_ROOT" \
  COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE="$BROLE" "$@" bash "$m" 2>&1; }

# ⓢ 변이① — **롤 판정 두 겹 · 「원장 0행 red」 · 계수기의 이중 방어를 함께 뗀다.**
#   그러면 경계 롤 접속(ⓚ 와 **같은 상태**)에서 원장이 0행으로 보이고, **살아 있는 한 벌이
#   「고아」로 떠 회수 후보가 된다.** 그것이 이 레포에서 실제로 났던 파괴적 오판이고
#   (`DATA-REFERENCE §0 M-9` — 실물은 데이터셋 13 · 파일 130 이었다), ⓚ 의 red 를 만든 것이
#   이번 회차의 롤 판정이라는 **음성 증명**이다.
MUT1="$TMP/mutrepo1"
mkdir -p "$MUT1/gates/tools" "$MUT1/services/viz-render/src/colab_viz/domains/d7_visualization"
cp "$GRADER" "$READINESS" "$MUT1/gates/tools/"
sed 's/^        return not self.dataset_files and not self.upload_files$/        return False/' \
  "$RULE" > "$MUT1/services/viz-render/src/colab_viz/domains/d7_visualization/ownership.py"
mutate "$MUT1/gates/tools/artifact-ownership.sh" \
  '/# ── 3-1\. 롤 판정 ㉮/,/^# ── 3-2\. 원장 계수/{/^# ── 3-2\. 원장 계수/!d}' \
  's/^if \[ "\$D3" -eq 0 \] && \[ "\$D5" -eq 0 \]; then$/if false; then/' \
  's/^if \[ "\$ADMIN_PAIR" = "\$BOUND_PAIR" \]; then$/if false; then/'
out="$(env REPO_ROOT="$MUT1" COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE="$BROLE" \
        COLAB_ARTIFACT_OWNER_PSQL="$TMP/psql-boundary" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
        COLAB_ARTIFACT_OWNER_DIR="$SLOT" COLAB_ARTIFACT_OWNER_DB_URL="$URL" \
        bash "$MUT1/gates/tools/artifact-ownership.sh" 2>&1)"
if printf '%s' "$out" | grep -q 'livekey'; then
  echo "[selftest] ⓢ 변이①(롤·원장 판정 제거) → **살아 있던 livekey 가 고아로 떠 회수 후보가 된다** — 음성 증명 OK"
  echo "           같은 상태에서 새 게이트는 red(ⓚ) · 검사를 떼면 경계가 낸 0 을 「없다」로 읽는다"
else
  echo "[selftest] ⓢ 변이①이 오판을 재현하지 못했다 ✗ — ⓚ 의 red 가 롤 판정에서 온 것이 아니다"
  echo "$out" | sed 's/^/           /'; FAILURES+=("ⓢ 변이① 음성 증명")
fi

# ⓣ ⭑ 변이② — **판정 규칙에서 구판 판정을 뗀다**(덫 ② 의 오라클).
#   `ownership.py` 의 `_is_legacy` 를 늘 거짓으로 만들면 구판 사이드카가 **「고아」로 뜨고**
#   회수 후보가 된다 — **그것이 오삭제다.** 여기서는 대상이 하나(구판)뿐이므로 red 가 나야 한다.
MUT="$TMP/mutrepo"
mkdir -p "$MUT/gates/tools" "$MUT/services/viz-render/src/colab_viz/domains/d7_visualization"
cp "$GRADER" "$MUT/gates/tools/"
cp "$READINESS" "$MUT/gates/tools/"
sed 's/^    return version < MIN_DECIDABLE_SIDECAR_VERSION or "baked_for" not in doc$/    return False/' \
  "$RULE" > "$MUT/services/viz-render/src/colab_viz/domains/d7_visualization/ownership.py"
if ! grep -q '^    return False$' "$MUT/services/viz-render/src/colab_viz/domains/d7_visualization/ownership.py"; then
  echo "[selftest] ⓣ 변이②를 만들지 못했다 ✗ — `_is_legacy` 의 문면이 바뀌었다"; FAILURES+=("ⓣ 변이② 생성")
else
  LEGACY_ONLY="$TMP/legacyonly"; mkdir -p "$LEGACY_ONLY"
  mkgroup "$LEGACY_ONLY" "legacykey" "$SC_LEGACY"
  base="$(env COLAB_ARTIFACT_OWNER_PSQL="$TMP/psql" COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE="$BROLE" \
          COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" COLAB_ARTIFACT_OWNER_DIR="$LEGACY_ONLY" \
          COLAB_ARTIFACT_OWNER_DB_URL="$URL" "$GATE" 2>&1)"; base_rc=$?
  mut="$(env REPO_ROOT="$MUT" COLAB_ARTIFACT_OWNER_PSQL="$TMP/psql" \
          COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE="$BROLE" COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" \
          COLAB_ARTIFACT_OWNER_DIR="$LEGACY_ONLY" COLAB_ARTIFACT_OWNER_DB_URL="$URL" \
          bash "$GATE" 2>&1)"; mut_rc=$?
  if [ $base_rc -eq 0 ] && [ $mut_rc -ne 0 ] && printf '%s' "$mut" | grep -q 'legacykey'; then
    echo "[selftest] ⓣ 변이②(구판 판정 제거) → 구판이 **고아로 떠 회수 후보가 된다** — 오삭제 재현 OK"
    echo "           정본 규칙: green(판정 불가 1 · 고아 0) · 변이: red(고아 legacykey)"
  else
    echo "[selftest] ⓣ 변이②가 오삭제를 재현하지 못했다 ✗ (정본 rc=$base_rc · 변이 rc=$mut_rc)"
    echo "$mut" | sed 's/^/           /'; FAILURES+=("ⓣ 변이② 오라클")
  fi
fi

# ⓤ 변이③ — 읽기 전용 탐침을 떼면 **쓸 수 있는 접속이 통과한다.**
mutate "$TMP/mutant-no-probe.sh" '/# ── 3-0\. 읽기 전용 증명/,/^# ── 3-1\. 롤 판정/{/^# ── 3-1\. 롤 판정/!d}'
out="$(run_mutant "$TMP/mutant-no-probe.sh" COLAB_ARTIFACT_OWNER_PSQL="$TMP/psql-rw" \
        COLAB_ARTIFACT_OWNER_EXEMPT="$DECL_NONE" COLAB_ARTIFACT_OWNER_DIR="$SLOT" \
        COLAB_ARTIFACT_OWNER_DB_URL="$URL")"; rc=$?
if [ $rc -eq 0 ]; then
  echo "[selftest] ⓤ 변이③(탐침 제거) → green — 오라클 증명 OK"
else
  echo "[selftest] ⓤ 변이③이 여전히 red ✗ — 읽기 전용 red 가 탐침에서 온 것이 아니다"
  echo "$out" | sed 's/^/           /'; FAILURES+=("ⓤ 변이③ 오라클")
fi

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::artifact-ownership-selftest red — 실패한 케이스: ${FAILURES[*]}"
  exit 1
fi
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict artifact-ownership-selftest
echo "artifact-ownership-selftest green — 19 케이스(red 6 · 미선언 7 · green 4 · 변이 3) ＋ 사유·건수 대조 11 ＋ 무접촉 대조 3 전건 기대대로"
exit 0
