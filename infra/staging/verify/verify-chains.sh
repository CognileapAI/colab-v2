#!/usr/bin/env bash
# 체인 판정기 — **두 체인이 각각 적용됐는가**를 원장 카탈로그로 묻는다.
#
#   verify-chains.sh
#
# ── 왜 이것이 있는가 ─────────────────────────────────────────────────────────
# 헬스 6종이 전부 200 이어도 **한쪽 체인이 안 올라간 배포**가 있을 수 있다. 앱은 뜨고
# 헬스는 대답하지만 표가 없다 — 2026-08-23 재기동에서 **AI 서비스만 정상**이었고 사전
# 데이터베이스가 빈 채로 **헬스 체크는 200** 이었다. **죽은 쪽은 바로 보이고 살아 있는
# 쪽이 속인다.** 그래서 헬스와 **따로** 묻는다.
#
# `platform` 과 `ai` 는 서로 다른 데이터베이스다(`CLAUDE.md §3-3`). 한쪽만 확인하고
# 전체 성공으로 기록하는 것이 `IS3 §7` 이 F9 픽스처로 못 박은 실패 그 자체다.
#
# ⚠ **읽기 전용이다.** `SELECT` 뿐 — `DELETE`·`UPDATE`·DDL 을 내지 않는다.
# ⚠ **접속 문자열을 쓰지 않는다.** 컨테이너 안에서 로컬 소켓으로 붙는다 —
#    값을 명령줄에 실으면 `ps` 와 로그에 남는다(`〈121〉-㉯`).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/../pipeline/lib.sh"

FAILED=0; SKIPPED=0; CHECKED=0

PG="${COLAB_STAGING_PG_CONTAINER:-colab_v2_staging_pg}"
SUPER="${COLAB_STAGING_PG_SUPERUSER:-postgres}"

# 체인 → (데이터베이스, version 테이블). **목록을 줄이지 않는다.**
CHAINS=(
  "platform|colab_platform|alembic_version_platform"
  "ai|colab_ai|alembic_version_ai"
)

q() { # $1=db $2=SQL → 표준출력 1줄
  docker exec -i "$PG" psql -U "$SUPER" -d "$1" -tAc "$2" 2>/dev/null
}

for entry in "${CHAINS[@]}"; do
  IFS='|' read -r name db tbl <<<"$entry"
  CHECKED=$((CHECKED+1))
  head="$(q "$db" "select version_num from $tbl")"
  rc=$?
  if [ "$rc" -ne 0 ]; then
    fail "[$name] 조회 실패 — 판정 불가는 red 다 (db=$db)"
    continue
  fi
  if [ -z "$head" ]; then
    # ⭑ **빈 결과를 통과로 읽지 않는다.** 「표가 비었다」와 「올라갔다」는 다르다.
    fail "[$name] $tbl 이 비었다 — 체인이 적용되지 않았다 (db=$db)"
    continue
  fi
  n="$(printf '%s\n' "$head" | grep -c . )"
  if [ "$n" -ne 1 ]; then
    fail "[$name] head 가 ${n}개다 — single-head 가 아니다"
    continue
  fi
  pass "[$name] head=$head (db=$db)"
done

verdict "체인 판정"
