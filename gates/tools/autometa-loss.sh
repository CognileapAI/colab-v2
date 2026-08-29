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
# 환경변수
#   COLAB_APPLIED_DB_URL_PLATFORM  db/platform 이 적용된 DB 접속 URL. 없으면 red (skip 아님)
#   COLAB_AUTOMETA_EXEMPT          면제 선언 파일 (기본 gates/config/autometa-loss.toml)
#   COLAB_AUTOMETA_PSQL            psql 명령 (기본 psql). selftest 가 일회용 DB 로 바꿔 끼운다
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
EXEMPT_FILE="${COLAB_AUTOMETA_EXEMPT:-$REPO_ROOT/gates/config/autometa-loss.toml}"
PSQL="${COLAB_AUTOMETA_PSQL:-psql}"
URL="${COLAB_APPLIED_DB_URL_PLATFORM:-}"

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

# ── 2. 적용 DB — 없으면 red. **skip 하면 그게 정확히 v1 의 실패다** ────────────────
[ -n "$URL" ] || red_undeclared "COLAB_APPLIED_DB_URL_PLATFORM (db/platform 적용 DB)" \
  "적용 DB 없이 반영 여부를 셀 수 없다. 검사를 못 한 것은 통과가 아니다 (CLAUDE.md §4).
   schema-diff 와 같은 변수·같은 규율이다.
   → db/platform 이 적용된 DB 의 URL 을 지정하고 다시 돌린다."

SQL_ARRAY="ARRAY[]::text[]"
if [ -n "$EXEMPT_IDS" ]; then
  SQL_ARRAY="ARRAY[$(printf '%s' "$EXEMPT_IDS" | sed "s/[^,]*/'&'/g")]::text[]"
fi

OUT="$("$PSQL" "$URL" -At -F '|' -v ON_ERROR_STOP=1 <<SQL 2>&1
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
)" || red "적용 DB 에 질의하지 못했다. 검사를 못 한 것은 통과가 아니다.
   psql 이 낸 말: $(printf '%s' "$OUT" | tr '\n' ' ' | cut -c1-400)"

LINE="$(printf '%s' "$OUT" | tail -n 1)"
case "$LINE" in
  [0-9]*\|[0-9]*\|[0-9]*\|[0-9]*) : ;;
  *) red "질의 결과가 숫자 넷이 아니다 — 무엇을 셌는지 모르는 채로 통과시키지 않는다.
   받은 것: $(printf '%s' "$OUT" | tr '\n' ' ' | cut -c1-400)" ;;
esac

IFS='|' read -r TOTAL APPLIED EXEMPTED MISSING <<< "$LINE"
echo "자동 정보 되쓰기 — 발행 $TOTAL · 반영 $APPLIED · 면제 $EXEMPTED (선언 $EXEMPT_COUNT 건) · 미반영 $MISSING"
echo "  세는 단위 = (업로드, 칸) 쌍 · 칸 = format·crs·grid · 시점 = $(date -Iseconds)"

# ── 3. 판정 — 세 상태 ────────────────────────────────────────────────────────
if [ "$TOTAL" -eq 0 ]; then
  red "대조 대상 0건. **대상이 없다는 것은 통과가 아니다** — 사건이 한 건도 발행되지 않았거나
   업로드→데이터셋 이음이 끊어졌다는 뜻이고, 둘 다 이 게이트가 잡아야 할 상태다.
   → 워커의 stage 2 선언(COLAB_WORKER_STAGE2)과 새 업로드 1건의 사건 발행을 확인한다."
fi
if [ "$MISSING" -gt 0 ]; then
  red "발행됐는데 장부에 반영되지 않은 칸 $MISSING 건. 면제로 선언되지 않았다.
   → 소비자가 등록 전환에서 도는지 확인하거나, 소급 반영 대상이면 면제 선언에 **이름으로** 적는다:
     ${EXEMPT_FILE#"$REPO_ROOT"/}"
fi
[ "$EXEMPTED" -gt 0 ] && echo "::warning::autometa-loss — 면제 $EXEMPTED 건이 반영되지 않은 채 통과했다(선언된 것)."
echo "autometa-loss green — 반영 $APPLIED / 발행 $TOTAL · 면제 $EXEMPTED"
exit 0
