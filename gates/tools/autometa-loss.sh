#!/usr/bin/env bash
# autometa-loss 게이트 — **사건이 발행되고도 장부에 반영되지 않았는가.**
#
# 강제하는 것 (완료 조건 축자 · `PLAN-SoT §9 〈190〉-㉱`):
#   「사건이 발행되고도 장부에 반영되지 않으면 red 를 낸다 — 발행 건수와 기록 건수를 대조해
#    어긋나면 실패로 계수한다. **대상 0건도 red 다**(green-by-skip 금지).」
#
# 세는 단위 = **(업로드, 칸) 쌍**이다. 「업로드 3건」이 아니라 「채워졌어야 할 칸 5개」를 센다 —
#   한 업로드가 `format` 은 받고 `crs` 는 못 받는 상태가 실재하고, 업로드로 세면 그것이 접힌다.
#
# 대조:
#   발행 = 사건이 값을 날랐다 (`file.format-detected.format` · `file.header-parsed.crs`·`.grid`)
#   반영 = 그 업로드에서 등록된 데이터셋의 `d3_dataset_autometa` 해당 칸이 비어 있지 않다
#   이음 = `payload` 가 아니라 **`d5_upload_file.id = d3_file.id`**(`NB-A` 동일성).
#          업로드→데이터셋 FK 는 없다(불변규칙 1) — 그 동일성이 유일한 다리다.
#
# 세 상태 (`CLAUDE.md §4`):
#   · 대상이 있으면            → 검사한다
#   · `gates/config/autometa-loss.toml` 에 **이름으로** 적혀 있으면 → **건수를 드러낸 채** 넘어간다
#   · 아무 말도 없으면(대상 0건 · 적용 DB 미지정 · 면제 파일 부재) → **red**
#
# ⚠ **관대한 기본값을 두지 않는다.** 적용 DB URL 이 없으면 red 다 — `schema-diff` 와 같은 규율이고,
#   같은 이유다: 「DB 가 없어서 검사를 못 했다」를 통과로 세는 것이 v1 의 실패였다.
#
# ⭑ ⟨개정 2026-08-31 · Ted 판정 `PLAN-SoT §9 〈237〉` · `03-HANDOFF §4 #50` 해소⟩
#   **대조 정본은 staging 실물 platform DB 다.** 이 게이트의 질문이 「실제로 접수한 것 중 메타가
#   빠진 것이 있는가」이므로 정답지는 실물이어야 한다. 종전 배선은 `schema-diff` 와 **공유하는**
#   스키마 전용 일회용 DB(`COLAB_APPLIED_DB_URL_PLATFORM`)를 봤고, 그 DB 에는 접수분이
#   **구조적으로 0건**이라 어떤 회차에도 green 이 될 수 없었다.
#   → 선언을 **분리한다**. `schema-diff` 는 제 적용 DB 를 그대로 쓰고, 이 게이트만 새 선언을 읽는다.
#
# ⭑ ⟨증보 2026-09-01 · Ted 판정 `RULING ㉟` · `DATA-REFERENCE §0 M-9`⟩ **롤을 검사한다.**
#   경계(`FORCE ROW LEVEL SECURITY`)에 걸리는 롤로 원장을 조회하면 **예외가 아니라 0 이 돌아온다.**
#   0 은 「없다」와 모양이 같아서, 종전 배선은 경계 롤 URL 을 물려도 그 0 을 세고 판정을 냈다.
#   (실제 사건 — 그 0 을 「데이터 없음」으로 읽어 「산출물 80건 전부 고아」라는 파괴적 권고가 나왔다.
#    실물은 데이터셋 13 · 파일 130 이었다.) 그래서 이 게이트는 세기 전에 **롤을 셋으로 판정한다**:
#     ㉮ 관리자 롤(경계가 걸리지 않는 롤 = rolsuper 또는 rolbypassrls)이 아니면 **red**
#     ㉯ **경계 롤로 같은 질의를 한 번 더 돌려 값이 관리자 롤 값과 같으면 red** —
#        경계가 실효 중인 표에서 두 값이 같다는 것은 「경계가 안 걸렸거나 둘 다 아무것도 안 봤다」다
#     ㉰ 경계 롤 이름이 선언돼 있지 않으면 **red(준비)** — 못 돌았음을 통과로 세지 않는다
#   ⚠ 면제·스위치를 두지 않는다. 「이 환경에서는 롤 검사를 건너뛴다」는 경로가 **없다.**
#
# ⭑ **접근은 읽기 전용이다 — 주장하지 않고 집행하고, 집행을 다시 증명한다.**
#   ⑴ 모든 SQL 이 `BEGIN READ ONLY` … `ROLLBACK` 안에서만 돈다. **COMMIT 이 한 곳도 없다.**
#   ⑵ 매 회차 **쓰기 탐침**을 던진다 — 읽기 전용이면 반드시 거부당해야 하고, 거부당하지 않으면
#      (= 쓸 수 있는 접속이면) **red** 다. 탐침은 임시 테이블이고 세이브포인트로 되감는다.
#   즉 「읽기 전용이라고 적어 두었다」가 아니라 **「이 회차에 실제로 쓰지 못했다」**가 증거다.
#
# 환경변수
#   COLAB_AUTOMETA_STAGING_DB_URL  **대조 정본** — staging 실물 platform DB 의 읽기 전용 접속 URL.
#                                  없으면 red(준비·입력미선언). 값이 사는 자리는 홈의 0600 env
#                                  파일 하나뿐이다 (`dev-package/RESTART.md §2-④-㉰`).
#                                  ⚠ COLAB_APPLIED_DB_URL_PLATFORM 으로 대신하지 않는다 —
#                                    그 값은 schema-diff 와 공유하는 스키마 전용 DB 이고,
#                                    그것이 정확히 #50 의 결함이다.
#   COLAB_AUTOMETA_BOUNDARY_ROLE   **경계 롤 이름** — 대조 재조회에 쓴다. 없으면 red(준비·입력미선언).
#                                  값이 사는 자리는 홈의 0600 env 파일 하나뿐이다
#                                  (`dev-package/RESTART.md §2-④-㉱`). 이름만 담는다 —
#                                  ⚠ COLAB_AUTOMETA_STAGING_DB_URL 과 **겹쳐 쓰지 않는다.**
#                                    그 값은 접속 URL 이고 이것은 롤 이름이다. 한 변수로 합치면
#                                    게이트가 어느 DB 를 보는지 다시 모르게 된다.
#   COLAB_AUTOMETA_EXEMPT          면제 선언 파일 (기본 gates/config/autometa-loss.toml)
#   COLAB_AUTOMETA_PSQL            psql 명령 (기본 psql). selftest 가 일회용 DB 로 바꿔 끼운다
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
EXEMPT_FILE="${COLAB_AUTOMETA_EXEMPT:-$REPO_ROOT/gates/config/autometa-loss.toml}"
PSQL="${COLAB_AUTOMETA_PSQL:-psql}"
URL="${COLAB_AUTOMETA_STAGING_DB_URL:-}"
BOUNDARY_ROLE="${COLAB_AUTOMETA_BOUNDARY_ROLE:-}"
OLD_URL="${COLAB_APPLIED_DB_URL_PLATFORM:-}"

red() { echo "::error::autometa-loss red — $*"; exit 1; }

# 선언되지 않은 입력 = **준비 red**. 「검사 대상이 규율을 어겼다」가 아니다 — 대상을 한 건도 못 봤다.
#   여전히 red 이고 종료코드도 실패다. 바뀌는 것은 **red 가 자기 원인을 참말로 말한다**는 것뿐이다.
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_readiness.sh"
red_undeclared() { readiness_undeclared_input autometa-loss "$1" "$2"; exit "$READINESS_EXIT"; }

# ── 1. 면제 선언 — **파일이 없으면 red.** 「선언이 없다」와 「면제가 없다」는 다르다 ────
[ -f "$EXEMPT_FILE" ] || red_undeclared "면제 선언 파일 (${EXEMPT_FILE#"$REPO_ROOT"/})" \
  "이 파일은 면제를 **이름으로** 고정하는 유일한 정본이다. 없으면 무엇이 면제인지 아무도 모른다.
   → 빈 목록(datasets = [])으로라도 선언한다. 「비어 있다」는 「면제 없음」이라는 **선언**이다."

EXEMPT_IDS="$(python3 - "$EXEMPT_FILE" <<'PY'
import re, sys
raw = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"^\s*datasets\s*=\s*\[(.*?)\]", raw, re.S | re.M)
if m is None:
    print("::MISSING::")
else:
    print(",".join(x.strip() for x in re.findall(r'"([^"]*)"', m.group(1))))
PY
)" || red "면제 선언을 읽지 못했다."
if [ "$EXEMPT_IDS" = "::MISSING::" ]; then
  red_undeclared "면제 선언의 datasets 항목 (${EXEMPT_FILE#"$REPO_ROOT"/})" \
    "항목이 없는 것을 「면제 0건」으로 세지 않는다 — 비어 있어도 **적혀 있어야** 한다."
fi
EXEMPT_COUNT=0
[ -n "$EXEMPT_IDS" ] && EXEMPT_COUNT="$(printf '%s' "$EXEMPT_IDS" | tr ',' '\n' | grep -c .)"

# ── 2. 대조 정본 — 없으면 red. **skip 하면 그게 정확히 v1 의 실패다** ──────────────
if [ -z "$URL" ]; then
  hint="적용 DB 없이 반영 여부를 셀 수 없다. 검사를 못 한 것은 통과가 아니다 (CLAUDE.md §4).
   → staging 실물 platform DB 의 **읽기 전용** 접속 URL 을 선언하고 다시 돌린다.
     값이 사는 자리 = 홈의 0600 env 파일 하나 (dev-package/RESTART.md §2-④-㉰)."
  if [ -n "$OLD_URL" ]; then
    hint="$hint
   ⚠ COLAB_APPLIED_DB_URL_PLATFORM 은 선언돼 있지만 **이 게이트는 그것을 읽지 않는다.**
     그 값은 schema-diff 와 공유하는 **스키마 전용** DB 라 접수분이 구조적으로 0건이고,
     그 배선으로는 어떤 회차에도 green 이 될 수 없었다 (Ted 판정 PLAN-SoT §9 〈237〉 · #50)."
  fi
  red_undeclared "COLAB_AUTOMETA_STAGING_DB_URL (대조 정본 = staging 실물 platform DB · 읽기 전용)" "$hint"
fi

# ── 2-1. 읽기 전용 증명 — **주장이 아니라 이 회차의 실측이다** ──────────────────────
#   쓰기 탐침이 거부당해야 통과한다. 거부당하지 않으면 = 쓸 수 있는 접속이면 red.
#   탐침은 임시 테이블이고, 세이브포인트로 되감은 뒤 트랜잭션 전체를 ROLLBACK 한다.
RO_OUT="$("$PSQL" "$URL" -At -v ON_ERROR_STOP=0 <<'SQL' 2>&1
SELECT '::decl::' || current_setting('default_transaction_read_only');
BEGIN READ ONLY;
SELECT '::ro::' || current_setting('transaction_read_only');
SAVEPOINT colab_ro_probe;
CREATE TEMP TABLE colab_autometa_ro_probe (x int);
SELECT '::wrote::';
ROLLBACK TO SAVEPOINT colab_ro_probe;
ROLLBACK;
SQL
)"
case "$RO_OUT" in
  *'::decl::on'*) : ;;
  *'::decl::off'*)
    red "**선언된 접속 자체가 읽기 전용이 아니다** (default_transaction_read_only = off).
   게이트가 트랜잭션을 읽기 전용으로 여는 것과 별개로, **선언이 그렇게 말해야** 한다.
   두 층을 다 요구하는 이유는 하나가 빠져도 나머지가 붙들게 하려는 것이다.
   → 읽기 전용 롤을 쓰거나 URL 에 options=-c default_transaction_read_only=on 을 붙인다." ;;
  *) : ;;   # 접속 자체가 실패한 경우 — 바로 아래 ::ro:: 검사가 잡는다
esac
case "$RO_OUT" in
  *'::wrote::'*)
    red "**쓰기 탐침이 통과했다 — 이 접속은 읽기 전용이 아니다.**
   이 게이트는 실물 staging 을 들여다볼 뿐 한 글자도 쓰지 않는다. 쓸 수 있는 접속으로는 돌지 않는다.
   → 선언된 URL 을 읽기 전용으로 고친다(읽기 전용 롤 또는 default_transaction_read_only=on)." ;;
esac

case "$RO_OUT" in
  *'::ro::on'*) : ;;
  *) red "읽기 전용 접속임을 증명하지 못했다. 검사를 못 한 것은 통과가 아니다.
   (접속 실패도 여기로 온다 — 못 붙은 것을 skip 으로 세지 않는다.)
   psql 이 낸 말: $(printf '%s' "$RO_OUT" | tr '\n' ' ' | cut -c1-400)" ;;
esac
SQL_ARRAY="ARRAY[]::text[]"
if [ -n "$EXEMPT_IDS" ]; then
  SQL_ARRAY="ARRAY[$(printf '%s' "$EXEMPT_IDS" | sed "s/[^,]*/'&'/g")]::text[]"
fi

# ── 2-2. 롤 판정 ㉮·㉰ — **경계에 걸린 조회의 0 을 「없다」로 읽지 않는다** ────────────
#   여기서 틀리면 아래 계수 전부가 거짓이다. 0 은 예외를 던지지 않고 사람 눈에도 그럴듯하다.
if [ -z "$BOUNDARY_ROLE" ]; then
  red_undeclared "COLAB_AUTOMETA_BOUNDARY_ROLE (경계 롤 이름 · ㉯ 재조회에 쓴다)" \
    "경계 롤을 모르면 「경계가 실제로 걸리는가」를 대조할 수 없다. 대조 없이 낸 계수는
   경계에 걸린 0 인지 진짜 0 인지 구별되지 않는다 (DATA-REFERENCE §0 M-9).
   → 홈의 0600 env 파일에 롤 이름을 선언하고 다시 돌린다 (dev-package/RESTART.md §2-④-㉱).
   ⚠ COLAB_AUTOMETA_STAGING_DB_URL 로 대신하지 않는다 — 그것은 접속 URL 이고 이것은 롤 이름이다."
fi
case "$BOUNDARY_ROLE" in
  [A-Za-z_]*) [ -z "$(printf '%s' "$BOUNDARY_ROLE" | tr -d 'A-Za-z0-9_')" ] || \
    red "경계 롤 이름에 식별자로 쓸 수 없는 글자가 있다 — 이름을 그대로 SQL 에 넣지 않는다." ;;
  *) red "경계 롤 이름이 식별자 모양이 아니다." ;;
esac

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
   경계가 없는 DB 를 대조 정본으로 삼으면 ㉯ 대조가 아무 말도 하지 않는다 (두 롤이 늘 같은 값을 낸다).
   → 선언된 URL 이 정말 staging 실물 platform DB 를 가리키는지 확인한다."
fi
# ⚠ psql 은 boolean 을 `t`/`f` 로도, `true`/`false` 로도 낸다(서버 판·설정에 따라 갈린다).
#   한쪽만 보면 관리자 롤을 관리자가 아니라고 읽는다 — 둘 다 참으로 센다.
is_true() { case "$1" in t|true|on|1) return 0 ;; *) return 1 ;; esac; }
if ! is_true "$R_SUPER" && ! is_true "$R_BYPASS"; then
  red "**접속 롤 '$R_NAME' 이 관리자 롤이 아니다** — rolsuper=$R_SUPER · rolbypassrls=$R_BYPASS ·
   FORCE RLS 표 ${R_FORCED}개. 이 롤로 세면 경계가 거른 뒤의 값을 세게 되고, **경계에 걸린 조회는
   예외가 아니라 0 을 돌려준다.** 그 0 을 「없다」로 읽은 것이 M-9 다(살아 있는 데이터셋 13개를
   지울 뻔했다). 감사자는 연구실 경계 **밖에서 전수**를 봐야 한다.
   → 관리자 롤(rolsuper 또는 rolbypassrls)의 **읽기 전용** 접속 URL 을 선언한다.
   ⚠ 「이 환경에서는 롤 검사를 건너뛴다」는 길은 두지 않는다 (CLAUDE.md §4)."
fi
echo "# 계수 롤 $R_NAME — rolsuper=$R_SUPER · rolbypassrls=$R_BYPASS (경계 밖) · FORCE RLS 표 ${R_FORCED}개"

# 본 질의는 **두 번** 돈다 — 관리자 롤로 한 번, 경계 롤로 한 번. 두 값을 아래에서 대조한다(㉯).
PAIRS_SQL="$(cat <<SQL
WITH carried AS (
  -- 사건이 **실제로 값을 날랐는가**. 「사건이 있다」가 아니다 — null 을 실어도 사건은 있다.
  SELECT e.upload_id,
         bool_or(e.event_type = 'file.format-detected'
                 AND coalesce((e.payload->>'uniform')::boolean, true)
                 AND e.payload->>'format' IS NOT NULL)                AS ev_format,
         bool_or(e.event_type = 'file.header-parsed'
                 AND e.payload->>'crs' IS NOT NULL)                   AS ev_crs,
         bool_or(e.event_type = 'file.header-parsed'
                 AND e.payload->>'grid' IS NOT NULL)                  AS ev_grid
    FROM d5_pipeline_event e
   WHERE e.event_type IN ('file.format-detected', 'file.header-parsed')
   GROUP BY e.upload_id
), linked AS (
  -- 업로드 → 데이터셋. **FK 가 아니라 fileId 동일성**이 다리다 (NB-A).
  SELECT c.*, (
           SELECT f.dataset_id
             FROM d5_upload_file uf JOIN d3_file f ON f.id = uf.id
            WHERE uf.upload_id = c.upload_id
            LIMIT 1) AS dataset_id
    FROM carried c
   WHERE c.ev_format OR c.ev_crs OR c.ev_grid
), pairs AS (
  SELECT l.dataset_id, x.col, x.carried,
         CASE x.col
           WHEN 'format' THEN a.format IS NOT NULL
           WHEN 'crs'    THEN a.crs IS NOT NULL
           ELSE a.grid IS NOT NULL
         END AS applied
    FROM linked l
    JOIN d3_dataset_autometa a ON a.dataset_id = l.dataset_id
    CROSS JOIN LATERAL (VALUES ('format', l.ev_format), ('crs', l.ev_crs),
                               ('grid', l.ev_grid)) AS x(col, carried)
   WHERE x.carried
)
SELECT count(*),
       count(*) FILTER (WHERE applied),
       count(*) FILTER (WHERE NOT applied AND dataset_id = ANY($SQL_ARRAY)),
       count(*) FILTER (WHERE NOT applied AND NOT (dataset_id = ANY($SQL_ARRAY)))
  FROM pairs;
SQL
)"

OUT="$("$PSQL" "$URL" -At -F '|' -v ON_ERROR_STOP=1 <<SQL 2>&1
BEGIN READ ONLY;   -- 본 질의도 같은 규율 아래 돈다. **COMMIT 은 없다**
$PAIRS_SQL
SET LOCAL ROLE "$BOUNDARY_ROLE";   -- ㉯ 같은 질의를 경계 롤로 한 번 더. 값이 같으면 red 다
$PAIRS_SQL
ROLLBACK;
SQL
)" || red "적용 DB 에 질의하지 못했다. 검사를 못 한 것은 통과가 아니다.
   (경계 롤 '$BOUNDARY_ROLE' 로 바꿔 앉지 못한 경우도 여기로 온다 — 대조를 못 한 것은 통과가 아니다.)
   psql 이 낸 말: $(printf '%s' "$OUT" | tr '\n' ' ' | cut -c1-400)"

# 트랜잭션 태그(BEGIN·ROLLBACK)가 섞이므로 tail 이 아니라 **모양으로** 고른다.
# ⚠ 이제 **두 줄**이다 — 앞이 관리자 롤, 뒤가 경계 롤. 두 줄이 아니면 대조를 못 한 것이고,
#   대조를 못 한 것은 통과가 아니다.
NUMLINES="$(printf '%s\n' "$OUT" | grep -E '^[0-9]+\|[0-9]+\|[0-9]+\|[0-9]+$')"
if [ "$(printf '%s\n' "$NUMLINES" | grep -c .)" -ne 2 ]; then
  red "질의 결과가 숫자 넷짜리 **두 줄**이 아니다 — 관리자 롤과 경계 롤의 값을 둘 다 얻지 못했다.
   무엇을 셌는지 모르는 채로 통과시키지 않는다.
   받은 것: $(printf '%s' "$OUT" | tr '\n' ' ' | cut -c1-400)"
fi
LINE="$(printf '%s\n' "$NUMLINES" | head -n 1)"
LINE_BOUNDARY="$(printf '%s\n' "$NUMLINES" | tail -n 1)"


IFS='|' read -r TOTAL APPLIED EXEMPTED MISSING <<< "$LINE"
echo "자동 정보 되쓰기 — 발행 $TOTAL · 반영 $APPLIED · 면제 $EXEMPTED (선언 $EXEMPT_COUNT 건) · 미반영 $MISSING"
echo "  세는 단위 = (업로드, 칸) 쌍 · 칸 = format·crs·grid · 시점 = $(date -Iseconds)"

# ── 3. 판정 — 세 상태 ────────────────────────────────────────────────────────
if [ "$TOTAL" -eq 0 ]; then
  red "대조 대상 0건. **대상이 없다는 것은 통과가 아니다** — 사건이 한 건도 발행되지 않았거나
   업로드→데이터셋 이음이 끊어졌다는 뜻이고, 둘 다 이 게이트가 잡아야 할 상태다.
   → 워커의 stage 2 선언(COLAB_WORKER_STAGE2)과 새 업로드 1건의 사건 발행을 확인한다."
fi
# ── 2-3. 롤 판정 ㉯ — **두 값이 같으면 red** ─────────────────────────────────
#   경계가 실효 중인 표에서 관리자 롤과 경계 롤이 같은 값을 낸다는 것은 둘 중 하나다:
#   경계가 실제로는 안 걸렸거나, 둘 다 아무것도 보지 않았거나. 어느 쪽이든 이상이다.
if [ "$LINE" = "$LINE_BOUNDARY" ]; then
  red "**경계 롤 '$BOUNDARY_ROLE' 로 다시 조회한 값이 관리자 롤 값과 같다** (둘 다 $LINE).
   FORCE RLS 표가 ${R_FORCED}개인데 경계가 값을 하나도 가르지 못했다 — 경계가 실효 중이 아니거나,
   두 조회가 같은 롤로 돌았거나, 둘 다 아무것도 보지 않은 것이다.
   → 선언된 경계 롤이 정말 경계에 걸리는 롤인지(NOSUPERUSER·NOBYPASSRLS·비소유자) 확인한다.
   ⚠ 이 대조가 없으면 경계에 걸린 0 과 진짜 0 이 구별되지 않는다 (DATA-REFERENCE §0 M-9)."
fi
echo "# 경계 대조 — 관리자 롤 $LINE ↔ 경계 롤 '$BOUNDARY_ROLE' $LINE_BOUNDARY (갈렸다)"
if [ "$MISSING" -gt 0 ]; then
  red "발행됐는데 장부에 반영되지 않은 칸 $MISSING 건. 면제로 선언되지 않았다.
   → 소비자가 등록 전환에서 도는지 확인하거나, 소급 반영 대상이면 면제 선언에 **이름으로** 적는다:
     ${EXEMPT_FILE#"$REPO_ROOT"/}"
fi
[ "$EXEMPTED" -gt 0 ] && echo "::warning::autometa-loss — 면제 $EXEMPTED 건이 반영되지 않은 채 통과했다(선언된 것)."
echo "autometa-loss green — 반영 $APPLIED / 발행 $TOTAL · 면제 $EXEMPTED"
exit 0
