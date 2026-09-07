#!/usr/bin/env bash
# migration-drift 게이트 (WU-C6 · 질의 3·4·30) — **되돌리면 red 가 나는가**를 재는
# 마이그레이션 오라클(`db/<체인>/tests/*-drift.sh`)을 게이트가 실제로 돌린다.
#
# ⭑ 왜 생겼나 — 오라클 12벌(platform 11 · ai 1)이 레포에 있는데 `gates/run.sh` 의
#   `ALL_GATES` 어디에도 없었다. **시험이 레포에 있는 것과 게이트가 그것을 판정하는 것은
#   다른 사실이다**(`frontend-test`·`service-tests-*` 가 닫은 것과 같은 계열).
#   아무도 돌리지 않는 오라클은 깨진 채로 조용히 늙는다.
#
# 판정 (전부 red · skip 은 하나도 없다)
#   ⓐ 오라클 하나라도 비영 종료          → red(판정) — 실패한 오라클을 **이름으로** 낸다
#   ⓑ 실측 건수 < `gates/config/migration-drift.toml` 의 `min` → red(판정)
#      («줄었다»를 스크립트 수정으로 위장할 수 없게 기대 건수는 파일에 선언된다)
#   ⓒ 대상 0건                           → red(판정) — 통과가 아니라 조회가 빗나간 것이다
#   ⓓ `alembic` 부재                     → red(준비 · 78) — skip 아님
#   ⓔ `docker` 부재                      → red(준비 · 78) — skip 아님
#   요약줄이 **센 수를 드러낸다**: `오라클 N · 실행 N · 실패 M` (체인별 ＋ 합계).
#
# 환경변수
#   COLAB_MIGRATION_DRIFT_CONFIG  기대 건수 정본 (기본 gates/config/migration-drift.toml)
#   COLAB_MIGRATION_DRIFT_DIRS    검사할 디렉터리 목록(공백 구분 · selftest 전용 주입).
#                                 주면 설정 파일 대신 이것을 쓰고, 기대 건수는
#                                 COLAB_MIGRATION_DRIFT_MIN 이 준다.
#   COLAB_MIGRATION_DRIFT_MIN     위와 짝인 최소 건수(공백 구분 · DIRS 와 같은 개수)
#   COLAB_ALEMBIC                 alembic 실행 파일. 없으면 아래 순서로 찾는다:
#                                 services/core-api/.venv → gates/.venv → PATH
#   COLAB_MIGRATION_DRIFT_DOCKER  docker 실행 파일 (기본 PATH 의 docker · selftest 전용 주입)
#   COLAB_PG_IMAGE                오라클에 그대로 전달 (기본 postgres:16-alpine)
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE=migration-drift

red() { echo "::error::$GATE red — $*"; exit 1; }

# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_readiness.sh"
red_undeclared() { readiness_undeclared_input "$GATE" "$1" "$2"; exit "$READINESS_EXIT"; }

# ── 0. 도구 — 없으면 **준비 red**. 못 돈 시험을 통과로 세지 않는다 ─────────────
ALEMBIC="${COLAB_ALEMBIC:-}"
if [ -z "$ALEMBIC" ]; then
  for cand in "$REPO_ROOT/services/core-api/.venv/bin/alembic" \
              "$REPO_ROOT/gates/.venv/bin/alembic"; do
    [ -x "$cand" ] && { ALEMBIC="$cand"; break; }
  done
fi
[ -n "$ALEMBIC" ] || ALEMBIC="alembic"
command -v "$ALEMBIC" >/dev/null 2>&1 || [ -x "$ALEMBIC" ] || red_undeclared \
  "alembic 실행 파일 (COLAB_ALEMBIC)" \
  "찾은 자리가 없다: COLAB_ALEMBIC · services/core-api/.venv/bin/alembic · gates/.venv/bin/alembic · PATH.
   오라클은 전부 alembic 으로 마이그레이션을 렌더한다 — 없으면 **한 벌도 판정되지 않았다**.
   핀은 services/core-api/requirements-dev.txt · gates/requirements.txt 에 있다(WU-C6)."
export COLAB_ALEMBIC="$ALEMBIC"

DOCKER="${COLAB_MIGRATION_DRIFT_DOCKER:-docker}"
{ command -v "$DOCKER" >/dev/null 2>&1 || [ -x "$DOCKER" ]; } || red_undeclared \
  "docker (오라클이 일회용 postgres 를 세운다 · COLAB_MIGRATION_DRIFT_DOCKER)" \
  "오라클은 s1db_ 접두사의 일회용 컨테이너를 스스로 띄운다(호스트 포트 0 · staging 무접촉).
   docker 가 없으면 판정이 아니라 **실행이 안 된 것**이다 — skip 이 아니라 red(준비)."

# ── 1. 대상 목록 ────────────────────────────────────────────────────────────
DIRS=(); MINS=()
if [ -n "${COLAB_MIGRATION_DRIFT_DIRS:-}" ]; then
  read -r -a DIRS <<< "$COLAB_MIGRATION_DRIFT_DIRS"
  read -r -a MINS <<< "${COLAB_MIGRATION_DRIFT_MIN:-}"
  [ "${#DIRS[@]}" -eq "${#MINS[@]}" ] || red \
    "COLAB_MIGRATION_DRIFT_DIRS(${#DIRS[@]}) 와 COLAB_MIGRATION_DRIFT_MIN(${#MINS[@]}) 의 개수가 다르다."
else
  CONF="${COLAB_MIGRATION_DRIFT_CONFIG:-$REPO_ROOT/gates/config/migration-drift.toml}"
  [ -f "$CONF" ] || red "기대 건수 정본이 없다: $CONF. 선언 없이 세는 것은 판정이 아니다."
  while IFS='|' read -r d m; do DIRS+=("$d"); MINS+=("$m"); done < <(
    awk -F'"' '/^dir[[:space:]]*=/{d=$2}
               /^min[[:space:]]*=/{gsub(/[^0-9]/,"",$0); if(d!=""){print d "|" $0; d=""}}' "$CONF")
  [ "${#DIRS[@]}" -gt 0 ] || red "$CONF 에서 검사 대상을 한 건도 읽지 못했다. 대상 0건은 통과가 아니다."
fi

# ── 2. 세고 → 돌린다 ────────────────────────────────────────────────────────
TOTAL=0; RAN=0; FAILED=0
FAILURES=(); LINES=()
for i in "${!DIRS[@]}"; do
  dir="${DIRS[$i]}"; min="${MINS[$i]}"
  case "$dir" in /*) abs="$dir";; *) abs="$REPO_ROOT/$dir";; esac
  [ -d "$abs" ] || red "검사 대상 디렉터리가 없다: $dir. 대상 0건은 통과가 아니다."

  mapfile -t ORACLES < <(ls "$abs"/*-drift.sh 2>/dev/null | sort)
  n="${#ORACLES[@]}"
  [ "$n" -gt 0 ] || red "$dir 에 *-drift.sh 오라클이 **0건**이다. 볼 것이 없으니 통과가 아니라 red 다
   (조회가 빗나갔거나 오라클이 사라졌다 · CLAUDE.md §4 green-by-skip 금지)."
  [ "$n" -ge "$min" ] || red "$dir 오라클 ${n}벌 — 선언된 최소 ${min}벌보다 적다.
   기대 건수의 정본은 gates/config/migration-drift.toml 이다. 오라클이 사라진 것을
   기대값 인하로 덮지 않는다(통과시키려 보는 범위를 줄이는 것은 수정이 아니다 · CLAUDE.md §3)."

  d_fail=0
  for o in "${ORACLES[@]}"; do
    name="$dir/$(basename "$o")"
    echo "── $name ──────────────────────────────────────────"
    if bash "$o"; then
      echo "[$GATE] $name → green"
    else
      echo "[$GATE] $name → red ✗"
      FAILURES+=("$name"); d_fail=$((d_fail+1))
    fi
    RAN=$((RAN+1))
  done
  TOTAL=$((TOTAL+n)); FAILED=$((FAILED+d_fail))
  LINES+=("[$GATE] $dir — 오라클 $n · 실행 $n · 실패 $d_fail (선언 최소 $min)")
done

printf '%s\n' "${LINES[@]}"
[ "$RAN" -eq "$TOTAL" ] || red "센 것 $TOTAL 벌 중 $RAN 벌만 돌았다 — 안 돈 것을 통과로 세지 않는다."

if [ "$FAILED" -gt 0 ]; then
  printf '::error::%s red — 오라클 %d · 실행 %d · 실패 %d:\n' "$GATE" "$TOTAL" "$RAN" "$FAILED"
  printf '     - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "$GATE green — 오라클 $TOTAL · 실행 $RAN · 실패 0."
