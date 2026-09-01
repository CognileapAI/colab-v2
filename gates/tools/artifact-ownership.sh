#!/usr/bin/env bash
# artifact-ownership 게이트 — **자리에 쌓인 산출물이 지금 누구 것인가.**
#
# 강제하는 것 (완료 정의 축자 · 대장 `dev-package/work-items.yaml` `A-1` ⑴⑵⑸):
#   ⑴ 「자리의 산출물 **전건**에 대해 가리키는 대상을 … **원장 대조**로 판정할 수 있다.
#      「판정 불가」가 남으면 **그 건수를 드러낸 채** 넘어간다.」
#   ⑸ 「**네 등급**(살아 있다 / 접수분에만 닿는다 / 고아 / 판정 불가)의 계수가 **회차마다
#      재현 가능**하며, **회수 대상은 고아 등급뿐**이다. **회수 전 전수 스냅숏이 남아 있다**
#      (키·확장자·크기·사이드카 `source`).」
#
# **갈래 B — 게이트 대조** (Ted 판정 2026-09-02 · `PLAN-SoT §9 〈270〉`·`〈271〉`).
#   Port 0 · 계약 0 · viz→core HTTP 표면 0 · 배포 0. 판정은 **런타임 질의가 아니라 게이트**다.
#   근거 = `dev-package/notes/A-1-PORT-COST.md §4-5`(갈래 A 9~12 파일·계약 1 신설 ↔ 갈래 B 2~3 파일).
#
# 이음 = **`d5_upload_file.id = d3_file.id`**(`NB-A` 동일성). 업로드→데이터셋 FK 는 없다
#   (불변규칙 1) — **그 동일성이 유일한 다리다.** 선례 = `gates/tools/autometa-loss.sh:14`
#   (같은 조인이 이미 게이트 안에서 돈다).
#
# 세는 단위 = **한 캐시 키 아래 선 산출물 한 벌**(`.png`·`.webp`·`.json`·`.pgw`).
#   파일로 세지 않는다 — 한 벌은 함께 살고 함께 죽는다(`layout.json` `why ④`).
#
# ⚠⚠ **덫 ① — `baked_for` 를 「현재 소유」로 읽지 않는다.**
#   그 필드는 「**구울 때의** 대상」이고 등록 전환(`createDataset`) 뒤 **낡는다.** 그것으로
#   판정하면 **등록된 대상이 전부 「불일치」로 뜬다**(대장 `A-1` `note` 축자).
#   → 판정 입력은 사이드카의 `sources`(fileId 배열)와 원장뿐이다. `baked_for` 는 **스냅숏에만**
#     실린다. 그 성질은 판정 규칙 정본(`ownership.py` `grade()`)이 지고, 시험이 변이로 증명한다
#     (`services/viz-render/tests/test_artifact_ownership.py`).
#
# ⚠⚠ **덫 ② — 구판은 「고아」가 아니라 「구판 · 판정 보류」다.**
#   `sidecarVersion` 이 없거나 `baked_for` 가 없으면 **판정을 하지 않는다.**
#   **없는 필드를 근거로 지우면 그것이 오삭제다**(대장 `A-1` `evidence` ㉱).
#   → 보류는 `gates/config/artifact-ownership.toml` `[legacy] tolerate` 로 **선언**하고
#     **건수를 드러낸 채** 넘어간다. 선언이 없으면 red 다.
#
# ⚠ **이 게이트는 아무것도 지우지 않는다.** 회수 집행은 `invalidation.apply()` 한 자리이고
#   (완료 정의 ⑶ · `d7_visualization/invalidation.py` `reclaim_plan`), 게이트는 **계수·판정**만
#   낸다. 지우는 문을 게이트로 늘리지 않는다.
#
# ⭑ **#57 의 규율을 그대로 잇는다** — 구조적으로 빈 결과가 통과로 읽히는 모양을 다시 만들지 않는다.
#   ㉮ 관리자 롤이 아니면 red · ㉯ 경계 롤 재조회 값이 관리자 롤 값과 같으면 red ·
#   ㉰ **원장이 구조적으로 비면(두 표 다 0행) red** — 경계에 걸린 0 을 「없다」로 읽어 **전건을
#      고아로 세는 파괴적 오판이 이 레포에서 실제로 났다**(`DATA-REFERENCE §0 M-9` ·
#      실물은 데이터셋 13 · 파일 130 이었다). 그 자리를 여기서 명시로 막는다.
#   ㉱ 자리에 대상 0건도 red · 읽기 전용 탐침이 통과하면 red.
#
# 환경변수
#   COLAB_ARTIFACT_OWNER_DB_URL        **대조 정본** — staging 실물 platform DB 의 **읽기 전용** URL.
#                                      ⚠ COLAB_APPLIED_DB_URL_PLATFORM 으로 대신하지 않는다 —
#                                        스키마 전용이라 원장이 구조적으로 0행이다(#50·#57-ⓑ 계열).
#   COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE **경계 롤 이름** — ㉯ 재조회에 쓴다. 없으면 red(준비).
#   COLAB_ARTIFACT_OWNER_DIR           미리보기 산출물 루트(자리). 없으면 red.
#   COLAB_ARTIFACT_OWNER_EXEMPT        면제·보류 선언 (기본 gates/config/artifact-ownership.toml)
#   COLAB_ARTIFACT_OWNER_SNAPSHOT      회수 전 전수 스냅숏의 출력 경로 (기본 = 임시 디렉터리)
#   COLAB_ARTIFACT_OWNER_PSQL          psql 명령 (기본 psql). selftest 가 일회용 DB 로 바꿔 끼운다
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
EXEMPT_FILE="${COLAB_ARTIFACT_OWNER_EXEMPT:-$REPO_ROOT/gates/config/artifact-ownership.toml}"
PSQL="${COLAB_ARTIFACT_OWNER_PSQL:-psql}"
URL="${COLAB_ARTIFACT_OWNER_DB_URL:-}"
BOUNDARY_ROLE="${COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE:-}"
OLD_URL="${COLAB_APPLIED_DB_URL_PLATFORM:-}"
SLOT="${COLAB_ARTIFACT_OWNER_DIR:-}"
GRADER="$REPO_ROOT/gates/tools/artifact_ownership.py"

red() { echo "::error::artifact-ownership red — $*"; exit 1; }

# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_readiness.sh"
red_undeclared() { readiness_undeclared_input artifact-ownership "$1" "$2"; exit "$READINESS_EXIT"; }

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" artifact-owner-XXXXXX)" || red "임시 자리를 못 만들었다."
trap 'rm -rf "$TMP"' EXIT INT TERM
SNAPSHOT="${COLAB_ARTIFACT_OWNER_SNAPSHOT:-$TMP/snapshot-$(date -u +%Y%m%dT%H%M%SZ).tsv}"

[ -f "$GRADER" ] || red "계수기가 없다: ${GRADER#"$REPO_ROOT"/}. 대상 0건은 통과가 아니다."

# ── 1. 면제·보류 선언 — **파일이 없으면 red.** 「선언이 없다」와 「면제가 없다」는 다르다 ────
[ -f "$EXEMPT_FILE" ] || red_undeclared "면제·보류 선언 파일 (${EXEMPT_FILE#"$REPO_ROOT"/})" \
  "이 파일은 면제를 **키 이름으로**, 구판 보류를 **참·거짓으로** 고정하는 유일한 정본이다.
   → 빈 목록(keys = [])으로라도 선언한다. 「비어 있다」는 「면제 없음」이라는 **선언**이다."

DECL="$(python3 - "$EXEMPT_FILE" <<'PY'
import re, sys
raw = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^\s*keys\s*=\s*\[(.*?)\]", raw, re.S | re.M)
t = re.search(r"^\s*tolerate\s*=\s*(true|false)\s*$", raw, re.M)
if m is None:
    print("::MISSINGKEYS::")
elif t is None:
    print("::MISSINGTOLERATE::")
else:
    print("::TOLERATE::" + t.group(1))
    for x in re.findall(r'"([^"]*)"', m.group(1)):
        print("::KEY::" + x.strip())
PY
)" || red "면제·보류 선언을 읽지 못했다."
case "$DECL" in
  *'::MISSINGKEYS::'*)
    red_undeclared "선언의 [exempt] keys 항목 (${EXEMPT_FILE#"$REPO_ROOT"/})" \
      "항목이 없는 것을 「면제 0건」으로 세지 않는다 — 비어 있어도 **적혀 있어야** 한다." ;;
  *'::MISSINGTOLERATE::'*)
    red_undeclared "선언의 [legacy] tolerate 항목 (${EXEMPT_FILE#"$REPO_ROOT"/})" \
      "구판(판정 보류)을 넘길지 말지를 **선언**해야 한다. 선언 없이 넘기면 그것이 green-by-skip 이다.
   ⚠ 구판은 「고아」가 아니다 — 없는 필드를 근거로 지우면 그것이 오삭제다." ;;
esac
TOLERATE="$(printf '%s\n' "$DECL" | sed -n 's/^::TOLERATE:://p')"
EXEMPT_KEYS="$(printf '%s\n' "$DECL" | sed -n 's/^::KEY:://p' | grep -v '^$')"
EXEMPT_COUNT=0
[ -n "$EXEMPT_KEYS" ] && EXEMPT_COUNT="$(printf '%s\n' "$EXEMPT_KEYS" | grep -c .)"

# ── 2. 입력 셋 — 없으면 red ────────────────────────────────────────────────
if [ -z "$URL" ]; then
  hint="대조 정본 없이 「누구 것인가」를 답할 수 없다. 검사를 못 한 것은 통과가 아니다 (CLAUDE.md §4).
   → staging 실물 platform DB 의 **읽기 전용** 접속 URL 을 선언하고 다시 돌린다.
     값이 사는 자리 = 홈의 0600 env 파일 하나 (dev-package/RESTART.md §2-④)."
  if [ -n "$OLD_URL" ]; then
    hint="$hint
   ⚠ COLAB_APPLIED_DB_URL_PLATFORM 은 선언돼 있지만 **이 게이트는 그것을 읽지 않는다** —
     schema-diff 와 공유하는 **스키마 전용** DB 라 원장이 구조적으로 0행이고, 그 0 을
     「없다」로 읽으면 **전건이 고아로 뜬다**(#50·#57-ⓑ 계열 · DATA-REFERENCE §0 M-9)."
  fi
  red_undeclared "COLAB_ARTIFACT_OWNER_DB_URL (대조 정본 = staging 실물 platform DB · 읽기 전용)" "$hint"
fi
[ -n "$SLOT" ] || red_undeclared "COLAB_ARTIFACT_OWNER_DIR (미리보기 산출물 루트)" \
  "자리를 보지 않고 「자리의 산출물 전건」을 말할 수 없다. 규약은 루트가 둘이라는 사실만 못 박고
   실제 경로는 배포가 준다 (contracts/storage/layout.json previewsRoot).
   → 배포의 미리보기 볼륨 경로를 지정하고 다시 돌린다."
[ -d "$SLOT" ] || red_undeclared "COLAB_ARTIFACT_OWNER_DIR 가 가리키는 디렉터리 ($SLOT)" \
  "경로가 선언됐으나 그런 디렉터리가 없다. 없는 자리를 「비어 있다」로 읽지 않는다."
if [ -z "$BOUNDARY_ROLE" ]; then
  red_undeclared "COLAB_ARTIFACT_OWNER_BOUNDARY_ROLE (경계 롤 이름 · ㉯ 재조회에 쓴다)" \
    "경계 롤을 모르면 「경계가 실제로 걸리는가」를 대조할 수 없다. 대조 없이 낸 원장 건수는
   경계에 걸린 0 인지 진짜 0 인지 구별되지 않는다 (DATA-REFERENCE §0 M-9 · #57-ⓐ).
   → 홈의 0600 env 파일에 롤 이름을 선언하고 다시 돌린다."
fi
case "$BOUNDARY_ROLE" in
  [A-Za-z_]*) [ -z "$(printf '%s' "$BOUNDARY_ROLE" | tr -d 'A-Za-z0-9_')" ] || \
    red "경계 롤 이름에 식별자로 쓸 수 없는 글자가 있다 — 이름을 그대로 SQL 에 넣지 않는다." ;;
  *) red "경계 롤 이름이 식별자 모양이 아니다." ;;
esac

# ── 3-0. 읽기 전용 증명 — **주장이 아니라 이 회차의 실측이다** ─────────────────────
RO_OUT="$("$PSQL" "$URL" -At -v ON_ERROR_STOP=0 <<'SQL' 2>&1
SELECT '::decl::' || current_setting('default_transaction_read_only');
BEGIN READ ONLY;
SELECT '::ro::' || current_setting('transaction_read_only');
SAVEPOINT colab_ro_probe;
CREATE TEMP TABLE colab_owner_ro_probe (x int);
SELECT '::wrote::';
ROLLBACK TO SAVEPOINT colab_ro_probe;
ROLLBACK;
SQL
)"
case "$RO_OUT" in
  *'::decl::off'*) red "**선언된 접속 자체가 읽기 전용이 아니다** (default_transaction_read_only = off).
   → 읽기 전용 롤을 쓰거나 URL 에 options=-c default_transaction_read_only=on 을 붙인다." ;;
esac
case "$RO_OUT" in
  *'::wrote::'*) red "**쓰기 탐침이 통과했다 — 이 접속은 읽기 전용이 아니다.**
   → 선언된 URL 을 읽기 전용으로 고친다(읽기 전용 롤 또는 default_transaction_read_only=on)." ;;
esac
case "$RO_OUT" in
  *'::ro::on'*) : ;;
  *) red "읽기 전용 접속임을 증명하지 못했다. 검사를 못 한 것은 통과가 아니다.
   (접속 실패도 여기로 온다 — 못 붙은 것을 skip 으로 세지 않는다.)
   psql 이 낸 말: $(printf '%s' "$RO_OUT" | tr '\n' ' ' | cut -c1-400)" ;;
esac

# ── 3-1. 롤 판정 ㉮ — **경계에 걸린 조회의 0 을 「원장이 비었다」로 읽지 않는다** ────
ROLE_OUT="$("$PSQL" "$URL" -At -F '|' -v ON_ERROR_STOP=1 <<SQL 2>&1
BEGIN READ ONLY;
SELECT '::role::' || current_user
       || '|' || (SELECT rolsuper::text     FROM pg_roles WHERE rolname = current_user)
       || '|' || (SELECT rolbypassrls::text FROM pg_roles WHERE rolname = current_user)
       || '|' || (SELECT count(*)::text FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                   WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relforcerowsecurity);
ROLLBACK;
SQL
)" || red "접속 롤을 확인하지 못했다. 롤을 모르는 채로 계수하지 않는다.
   psql 이 낸 말: $(printf '%s' "$ROLE_OUT" | tr '\n' ' ' | cut -c1-400)"

ROLE_LINE="$(printf '%s\n' "$ROLE_OUT" | grep -E '^::role::' | tail -n 1)"
[ -n "$ROLE_LINE" ] || red "접속 롤 표식이 없다 — 무엇으로 붙었는지 모르는 채로 통과시키지 않는다.
   받은 것: $(printf '%s' "$ROLE_OUT" | tr '\n' ' ' | cut -c1-400)"
IFS='|' read -r R_NAME R_SUPER R_BYPASS R_FORCED <<< "${ROLE_LINE#::role::}"

if [ "$R_FORCED" = "0" ]; then
  red "공개 스키마에 **FORCE ROW LEVEL SECURITY 가 걸린 표가 0개**다.
   경계가 없는 DB 를 대조 정본으로 삼으면 ㉯ 대조가 아무 말도 하지 않는다(두 롤이 늘 같은 값을 낸다).
   → 선언된 URL 이 정말 staging 실물 platform DB 를 가리키는지 확인한다."
fi
# ⚠ psql 은 boolean 을 t/f 로도 true/false 로도 낸다 — 한쪽만 보면 관리자를 관리자가 아니라고 읽는다.
is_true() { case "$1" in t|true|on|1) return 0 ;; *) return 1 ;; esac; }
if ! is_true "$R_SUPER" && ! is_true "$R_BYPASS"; then
  red "**접속 롤 '$R_NAME' 이 관리자 롤이 아니다** — rolsuper=$R_SUPER · rolbypassrls=$R_BYPASS ·
   FORCE RLS 표 ${R_FORCED}개. 이 롤로 원장을 조회하면 경계가 거른 뒤의 값을 세게 되고,
   **경계에 걸린 조회는 예외가 아니라 0 을 돌려준다.** 그 0 을 「원장에 없다」로 읽으면
   **자리의 전건이 「고아」로 뜬다** — 그 파괴적 오판이 이 레포에서 실제로 났다
   (DATA-REFERENCE §0 M-9 · 실물은 데이터셋 13 · 파일 130 이었다).
   → 관리자 롤(rolsuper 또는 rolbypassrls)의 **읽기 전용** 접속 URL 을 선언한다.
   ⚠ 「이 환경에서는 롤 검사를 건너뛴다」는 길은 두지 않는다 (CLAUDE.md §4)."
fi
echo "# 계수 롤 $R_NAME — rolsuper=$R_SUPER · rolbypassrls=$R_BYPASS (경계 밖) · FORCE RLS 표 ${R_FORCED}개"

# ── 3-2. 원장 계수 — **두 번 센다** (관리자 롤 ㆍ 경계 롤 ㉯) ────────────────────
COUNT_SQL="SELECT (SELECT count(*) FROM d3_file) || ',' || (SELECT count(*) FROM d5_upload_file);"
CNT_OUT="$("$PSQL" "$URL" -At -v ON_ERROR_STOP=1 <<SQL 2>&1
BEGIN READ ONLY;
$COUNT_SQL
SET LOCAL ROLE "$BOUNDARY_ROLE";   -- ㉯ 같은 질의를 경계 롤로 한 번 더. 값이 같으면 red 다
$COUNT_SQL
ROLLBACK;
SQL
)" || red "대조 정본에 질의하지 못했다. 검사를 못 한 것은 통과가 아니다.
   (경계 롤 '$BOUNDARY_ROLE' 로 바꿔 앉지 못한 경우도 여기로 온다.)
   psql 이 낸 말: $(printf '%s' "$CNT_OUT" | tr '\n' ' ' | cut -c1-400)"

PAIRS="$(printf '%s\n' "$CNT_OUT" | grep -E '^[0-9]+,[0-9]+$')"
if [ "$(printf '%s\n' "$PAIRS" | grep -c .)" -ne 2 ]; then
  red "원장 건수가 **두 줄**로 오지 않았다 — 관리자 롤과 경계 롤의 값을 둘 다 얻지 못했다.
   무엇을 셌는지 모르는 채로 통과시키지 않는다.
   받은 것: $(printf '%s' "$CNT_OUT" | tr '\n' ' ' | cut -c1-400)"
fi
ADMIN_PAIR="$(printf '%s\n' "$PAIRS" | head -n 1)"
BOUND_PAIR="$(printf '%s\n' "$PAIRS" | tail -n 1)"
D3="${ADMIN_PAIR%%,*}"; D5="${ADMIN_PAIR##*,}"

# ㉰ **원장이 구조적으로 비면 red** — 그 0 을 「없다」로 읽으면 전건이 고아가 된다
if [ "$D3" -eq 0 ] && [ "$D5" -eq 0 ]; then
  red "**원장 두 표가 다 0행이다** (d3_file $D3 · d5_upload_file $D5).
   이 상태로 판정하면 **자리의 전건이 「고아」로 뜬다** — 그 0 을 「없다」로 읽은 파괴적 오판이
   이 레포에서 실제로 났다(DATA-REFERENCE §0 M-9).
   ⚠ 이 0 이 「경계에 걸려 안 보이는 0」이 아님은 위 롤 판정이 이미 배제했다 — 그러므로
     **잘못된 DB 를 보고 있는 것**이다(스키마 전용 DB 가 정확히 이 모양이다 · #57-ⓑ).
   → COLAB_ARTIFACT_OWNER_DB_URL 이 staging 실물 platform DB 인지 확인한다."
fi
# ㉯ 대조 — 경계가 실효 중인데 두 롤이 같은 값을 내면 경계가 아무것도 가르지 못한 것이다
if [ "$ADMIN_PAIR" = "$BOUND_PAIR" ]; then
  red "**경계 롤 '$BOUNDARY_ROLE' 로 다시 센 원장 건수가 관리자 롤 값과 같다** (둘 다 $ADMIN_PAIR).
   FORCE RLS 표가 ${R_FORCED}개인데 경계가 값을 하나도 가르지 못했다 — 경계가 실효 중이 아니거나,
   두 조회가 같은 롤로 돌았거나, 둘 다 아무것도 보지 않은 것이다.
   ⚠ 이 대조가 없으면 경계에 걸린 0 과 진짜 0 이 구별되지 않는다 (DATA-REFERENCE §0 M-9 · #57-ⓐ)."
fi
echo "# 경계 대조 — 관리자 롤 (d3_file,d5_upload_file)=($ADMIN_PAIR) ↔ 경계 롤 '$BOUNDARY_ROLE' ($BOUND_PAIR) (갈렸다)"

# ── 3-3. 원장 실물을 내린다 — **id 두 벌** ─────────────────────────────────
# ⚠ `-o` 로 파일에 적지 않는다 — selftest 가 psql 을 컨테이너 안으로 바꿔 끼우면 `-o` 는
#   **컨테이너 안**에 적히고 게이트는 빈 파일을 본다(실측 2026-09-02). 표준출력으로 받는다.
# ⚠ `-q` 가 있어야 한다 — 없으면 명령 태그(BEGIN·ROLLBACK)가 결과에 섞여 행수가 2 커지고,
#   원장에 없는 id 두 개가 생긴다(실측 2026-09-02).
dump_ids() { # $1=표 이름 $2=출력 파일
  "$PSQL" "$URL" -qAt -v ON_ERROR_STOP=1 <<SQL > "$2" 2>"$TMP/dumperr"
BEGIN READ ONLY;
SELECT id FROM $1;
ROLLBACK;
SQL
}
dump_ids d3_file "$TMP/d3.txt" || red "d3_file 의 id 를 내리지 못했다: $(tr '\n' ' ' < "$TMP/dumperr" | cut -c1-300)"
dump_ids d5_upload_file "$TMP/d5.txt" || red "d5_upload_file 의 id 를 내리지 못했다: $(tr '\n' ' ' < "$TMP/dumperr" | cut -c1-300)"
GOT3="$(grep -c . "$TMP/d3.txt")"; GOT5="$(grep -c . "$TMP/d5.txt")"
if [ "$GOT3" -ne "$D3" ] || [ "$GOT5" -ne "$D5" ]; then
  red "내린 원장 행수가 센 값과 다르다 — d3_file $GOT3/$D3 · d5_upload_file $GOT5/$D5.
   두 값이 갈리면 무엇으로 판정했는지 말할 수 없다."
fi

# ── 4. 계수 — 판정 규칙은 **정본 한 자리**가 낸다 (ownership.py) ────────────────
OUT="$(python3 "$GRADER" "$SLOT" "$TMP/d3.txt" "$TMP/d5.txt" "$SNAPSHOT" 2>&1)" \
  || red "계수기가 돌지 못했다. 검사를 못 한 것은 통과가 아니다.
   낸 말: $(printf '%s' "$OUT" | tr '\n' ' ' | cut -c1-600)"

case "$OUT" in
  *'::원장공백::'*) red "계수기가 원장을 비었다고 봤다 — 위 계수와 어긋난다. 판정하지 않는다." ;;
esac
case "$OUT" in
  *'::규약위반::'*)
    red "**사이드카 규약 위반** — 판 번호는 2 인데 \`sources\` 가 비었다.
   $(printf '%s\n' "$OUT" | sed -n 's/^::규약위반:://p')
   ⚠ 규약 위반을 「판정 불가」로 접지 않는다 — 접으면 보류에 섞여 영원히 안 보인다." ;;
esac

g() { printf '%s\n' "$OUT" | sed -n "s/^::계수::$1\t//p"; }
LIVE="$(g '살아 있다')"; UPONLY="$(g '접수분에만 닿는다')"
ORPHAN="$(g '고아')"; PENDING="$(g '판정 불가')"
SUBJECTS="$(printf '%s\n' "$OUT" | sed -n 's/^::대상:://p')"
TILES="$(printf '%s\n' "$OUT" | sed -n 's/^::지도타일:://p')"
SNAPROWS="$(printf '%s\n' "$OUT" | sed -n 's/^::스냅숏:://p')"
ORPHAN_KEYS="$(printf '%s\n' "$OUT" | sed -n 's/^::고아:://p')"
for v in "$LIVE" "$UPONLY" "$ORPHAN" "$PENDING" "$SUBJECTS" "$TILES" "$SNAPROWS"; do
  case "$v" in ''|*[!0-9]*) red "계수기 출력이 온전하지 않다 — 무엇을 셌는지 모르는 채로 통과시키지 않는다.
   낸 말: $(printf '%s' "$OUT" | tr '\n' ' ' | cut -c1-600)" ;; esac
done

echo "산출물 소유 — 대상 한 벌 $SUBJECTS · 살아 있다 $LIVE · 접수분에만 닿는다 $UPONLY · 고아 $ORPHAN · 판정 불가 $PENDING"
echo "  지도 타일 $TILES 벌은 **대상이 아니다** — D5 가 구운 것이라 kept 로 산다 (완료 정의 ⑷)"
echo "  세는 단위 = 한 캐시 키 아래 선 산출물 한 벌 · 자리 = $SLOT · 원장 = d3_file $D3 · d5_upload_file $D5"
echo "  회수 전 전수 스냅숏 $SNAPROWS 줄 → $SNAPSHOT (키·확장자·크기·사이드카 source·등급)"
echo "  시점 = $(date -Iseconds)"

# ── 5. 판정 — 세 상태 ──────────────────────────────────────────────────────
[ -s "$SNAPSHOT" ] || red "**회수 전 전수 스냅숏이 남지 않았다** ($SNAPSHOT).
   지운 뒤에 「무엇이 있었나」를 답할 기록이 없으면 회수는 되돌릴 수 없다 (완료 정의 ⑸)."

if [ "$SUBJECTS" -eq 0 ]; then
  red "자리에 판정 대상 0건. **대상이 없다는 것은 통과가 아니다** — 검사할 것을 한 건도 못 봤다.
   (지도 타일 $TILES 벌은 대상이 아니다.)
   → 미리보기 루트가 맞는지, 렌더가 한 번이라도 돌았는지 확인한다."
fi

TOTAL_GRADED=$((LIVE + UPONLY + ORPHAN + PENDING))
[ "$TOTAL_GRADED" -eq "$SUBJECTS" ] || red "네 등급의 합($TOTAL_GRADED)이 대상 수($SUBJECTS)와 다르다 —
   등급을 못 받은 벌이 있다. 계수가 재현 가능하지 않으면 ⑸ 가 성립하지 않는다."

# **고아는 선언되지 않으면 red 다** — 판정을 미루는 자리를 열어 두지 않는다.
if [ "$ORPHAN" -gt 0 ]; then
  UNDECLARED=""
  while IFS= read -r k; do
    [ -z "$k" ] && continue
    printf '%s\n' "$EXEMPT_KEYS" | grep -Fxq "$k" || UNDECLARED="$UNDECLARED $k"
  done <<< "$ORPHAN_KEYS"
  if [ -n "$UNDECLARED" ]; then
    red "**고아 등급 $ORPHAN 벌 중 선언되지 않은 것**:$UNDECLARED
   조각 fileId 가 d3_file 에도 d5_upload_file 에도 없다 = 원본이 사라졌다.
   → 회수하려면 \`invalidation.reclaim_plan()\` → \`invalidation.apply()\` **한 자리**로 집행한다
     (완료 정의 ⑶ · 지우는 문을 게이트로 늘리지 않는다).
   → 남겨야 하면 **키 이름으로** 선언에 적는다: ${EXEMPT_FILE#"$REPO_ROOT"/}
   ⚠ 이 게이트는 아무것도 지우지 않았다. 스냅숏은 남았다: $SNAPSHOT"
  fi
  echo "::warning::artifact-ownership — 고아 $ORPHAN 벌이 **이름으로 선언된 채** 통과했다 (선언 $EXEMPT_COUNT 건)."
fi

# **구판(판정 불가)은 선언된 보류다** — 건수를 드러낸 채 넘어간다 (완료 정의 ⑴ 축자)
if [ "$PENDING" -gt 0 ]; then
  if [ "$TOLERATE" != "true" ]; then
    red "**판정 불가(구판) $PENDING 벌**이 남았는데 선언이 \`[legacy] tolerate = false\` 다.
   ⚠ 구판은 **「고아」가 아니다** — 없는 필드(sidecarVersion·baked_for)를 근거로 지우면 오삭제다.
   → 전 층을 다시 구워 판 2 사이드카를 남기거나, 보류를 \`tolerate = true\` 로 **선언**한다:
     ${EXEMPT_FILE#"$REPO_ROOT"/}"
  fi
  echo "::warning::artifact-ownership — 판정 불가(구판) $PENDING 벌이 **건수를 드러낸 채** 통과했다.
   구판 = sidecarVersion·baked_for 가 없는 사이드카. **고아가 아니라 보류다** (A-1 완료 정의 ⑴)."
fi

echo "artifact-ownership green — 대상 $SUBJECTS 벌 (살아 있다 $LIVE · 접수분 $UPONLY · 고아 $ORPHAN · 판정 불가 $PENDING) · 지도 타일 $TILES · 스냅숏 $SNAPROWS 줄 · 삭제 0건"
exit 0
