#!/usr/bin/env bash
# 구 체인이 적용된 DB(staging 의 실제 경로)를 현재 트리로 `upgrade head` 했을 때 남는
# 재부모화 드리프트를 `0042_reconcile_admin_access` 가 메우는지 재는 오라클.
#
# 왜 있나 (2026-09-18): `0032_private_owner_access` 는 **리비전 id 를 그대로 둔 채**
# 부모가 `0031_search_evidence` 에서 `0033_admin_body_access` 로 바뀌었다.
# 구 체인(`0031 → 0032_private_owner_access → 0033_search_changes → …`)을 이미 적용한 DB 는
# `alembic_version_platform` 에 **자기 head 하나만** 들고 있다. 그래서 현재 트리로 올려도
# 알렘빅은 그 head 이전을 전부 적용됐다고 보고 `0032_labless_operator` 와
# `0033_admin_body_access` 를 **한 번도 돌리지 않는다**. 선언과 적용이 조용히 갈린다.
# stamp 로 흉내내지 않고 **구 트리를 실제로 돌려** 그 상태를 만든 뒤 현재 트리를 얹는다.
#
# 판정
#   ⓐ 구 체인 0036 상태에서 세 갈래가 **없다**(음성 대조) — 없으면 이 오라클이 재는 것이 없다
#   ⓑ 현재 트리 `upgrade head` 뒤 세 갈래가 **있다** (관리자 함수 · lab_id 두 자리 · 정책 갈래)
#   ⓒ 그 DB 의 pg_dump 가 선언 `db/platform/schema.sql` 과 **한 줄도 다르지 않다**
#      (정규화는 `gates/tools/schema-diff.sh` 와 같다 — 그 함수는 스크립트 안에 있어 source 할 수 없어 옮겨 적었다)
#
# 환경변수
#   COLAB_OLD_CHAIN_REF  구 체인 기준 커밋(기본: a383510d → 없으면 origin/local-stage)
set -uo pipefail
. "$(dirname "${BASH_SOURCE[0]}")/../../../gates/tools/_pg.sh"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHAIN="$(cd "$HERE/.." && pwd)"
ROOT="$(cd "$CHAIN/../.." && pwd)"
ALEMBIC="${COLAB_ALEMBIC:-alembic}"
red(){ echo "::error::0042-drift red — $*"; exit 1; }
ready(){ echo "::error::0042-drift red(준비) — $*"; exit 78; }
command -v "$ALEMBIC" >/dev/null || [ -x "$ALEMBIC" ] || ready "alembic이 없다"
command -v git >/dev/null || ready "git이 없다"

# ── 구 체인 기준 커밋 — 실제로 닿는 것만 쓰고, 고른 해시를 출력에 남긴다 ──────
OLD_REF=""
for cand in "${COLAB_OLD_CHAIN_REF:-}" a383510d origin/local-stage; do
  [ -n "$cand" ] || continue
  git -C "$ROOT" cat-file -t "$cand^{commit}" >/dev/null 2>&1 && { OLD_REF="$cand"; break; }
done
[ -n "$OLD_REF" ] || ready "구 체인 기준 커밋을 찾지 못했다 (a383510d · origin/local-stage · COLAB_OLD_CHAIN_REF)"
OLD_SHA="$(git -C "$ROOT" rev-parse "$OLD_REF^{commit}")"
echo "0042-drift — 구 체인 기준 $OLD_REF = $OLD_SHA"

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" colab-0042-XXXXXX)"
cleanup(){ pg_cleanup; rm -rf "$TMP"; }
trap cleanup EXIT INT TERM

mkdir -p "$TMP/old"
git -C "$ROOT" archive "$OLD_SHA" db/platform | tar -x -C "$TMP/old" || red "구 트리 추출 실패"
OLDCHAIN="$TMP/old/db/platform"
[ -f "$OLDCHAIN/alembic.ini" ] || red "구 트리에 alembic.ini 가 없다"
[ -f "$OLDCHAIN/versions/0036_search_refresh_runtime.py" ] || red "구 트리에 0036_search_refresh_runtime 이 없다"
[ ! -f "$OLDCHAIN/versions/0033_admin_body_access.py" ] || \
  red "구 트리에 0033_admin_body_access 가 있다 — 재부모화 이전 상태가 아니라 이 오라클의 전제가 깨졌다"

export COLAB_PLATFORM_DB_URL=postgresql+psycopg://offline/offline
render(){ (cd "$1" && "$ALEMBIC" $2 --sql) >"$3" 2>"$TMP/err" || { sed 's/^/     /' "$TMP/err" | tail -20; red "render $2"; }; }
render "$OLDCHAIN" 'upgrade 0036_search_refresh_runtime' "$TMP/old36.sql"
render "$CHAIN"    'upgrade 0036_search_refresh_runtime:head' "$TMP/cur.sql"
HEAD_REV="$( (cd "$CHAIN" && "$ALEMBIC" heads) 2>/dev/null | awk 'NF{print $1; exit}')"
[ -n "$HEAD_REV" ] || red "현재 트리의 head 리비전을 읽지 못했다"

pg_start 0042-drift || exit 78
# pg_start installs its own trap; keep both the shared PG cleanup and this scratch directory.
trap cleanup EXIT INT TERM
docker exec "$PGC" createdb -U postgres migration0042 >/dev/null || red "DB 생성 실패"
su_psql(){ docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d migration0042 "$@"; }
check(){ su_psql -v reconciled_expected="$1" < "$HERE/0042-assertions.sql" >"$TMP/oracle" 2>&1; }

# ── ⓐ 구 체인 0036 — staging 이 실제로 서 있던 자리 ──────────────────────────
su_psql < "$TMP/old36.sql" >"$TMP/err" 2>&1 || { sed 's/^/     /' "$TMP/err" | tail -20; red "구 체인 0036 적용 실패"; }
check 0 || { cat "$TMP/oracle"; red "구 체인 0036 에서 미봉합 전제가 서지 않는다"; }
if check 1; then red "구 체인 0036 이 이미 봉합 상태다 — 이 오라클이 재는 것이 없다"; fi

# ── ⓑ 현재 트리로 upgrade head ──────────────────────────────────────────────
su_psql < "$TMP/cur.sql" >"$TMP/err" 2>&1 || { sed 's/^/     /' "$TMP/err" | tail -20; red "현재 트리 upgrade head 실패"; }
AT="$(docker exec "$PGC" psql -tAq -U postgres -d migration0042 -c 'SELECT version_num FROM alembic_version_platform')"
[ "$AT" = "$HEAD_REV" ] || red "upgrade 뒤 버전이 head 가 아니다: 기대 $HEAD_REV · 실측 $AT"
check 1 || { cat "$TMP/oracle"; red "현재 트리 upgrade head 뒤에도 재부모화 드리프트가 남았다 (버전 $AT)"; }
if check 0; then red "봉합 뒤에도 구 체인 상태가 그대로다"; fi

# ── ⓒ 선언 스키마와의 정규화 diff ───────────────────────────────────────────
pg_apply declared0042 "$CHAIN/schema.sql" || red "선언 스키마를 빈 DB 에 적용하지 못했다: ${PG_APPLY_ERR:-(출력 없음)}"
dump(){ docker exec "$PGC" pg_dump -U postgres --schema-only --no-owner --no-privileges -d "$1"; }
normalize(){ grep -vE '^\s*(--|SET |SELECT pg_catalog\.set_config|\\(un)?restrict |$)' "$1"; }
dump declared0042  > "$TMP/declared.sql" 2>"$TMP/err" || { cat "$TMP/err"; red "선언 스키마 덤프 실패"; }
dump migration0042 > "$TMP/applied.sql"  2>"$TMP/err" || { cat "$TMP/err"; red "적용 DB 덤프 실패"; }
normalize "$TMP/declared.sql" > "$TMP/d.norm"
normalize "$TMP/applied.sql"  > "$TMP/a.norm"
if ! diff -u "$TMP/d.norm" "$TMP/a.norm" > "$TMP/diff"; then
  sed 's/^/     /' "$TMP/diff" | head -80
  red "구 체인 경로로 올린 DB 가 선언 schema.sql 과 갈라진다 — 차이 $(grep -cE '^[+-][^+-]' "$TMP/diff") 줄"
fi

echo "0042-drift green — 구 체인 $OLD_SHA 로 0036 까지 올린 DB 에 현재 트리를 얹어 $HEAD_REV 도달;"
echo "                  관리자 함수·lab_id 두 자리·body_access 관리자 갈래가 0 → 1 로 메워지고"
echo "                  RESTRICTIVE/FOR ALL 과 나머지 세 갈래는 불변, 선언 schema.sql 과 정규화 diff 0줄."
