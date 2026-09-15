#!/usr/bin/env bash
# migration-drift 가 red fixture 로 fail-closed 임을 증명한다 (WU-C6).
#
# 케이스 — 대조군 하나만 green 이고 나머지는 전부 red 다:
#   ⓐ 오라클 2벌이 전부 통과            → green   (대조군)
#   ⓑ **되돌린 델타** — 1벌이 비영 종료  → red(판정)
#   ⓒ 대상 0건                          → red(판정)  ※ green-by-skip 금지
#   ⓓ alembic 부재                      → red(준비 · 입력미선언 · 78)  ※ skip 아님
#   ⓔ 실측 건수 < 선언 최소             → red(판정)  「줄었다」를 기대값 인하로 덮지 못한다
#   ⓕ docker 부재                       → red(준비 · 입력미선언 · 78)
#   ⓖ 요약줄이 **센 수를 낸다**(`오라클 N · 실행 N · 실패 M`)
#
# 집계 시험은 `mktemp -d` 안에 **가짜 `*-drift.sh`** 를
#   짓고 `COLAB_MIGRATION_DRIFT_DIRS`/`_MIN` 으로 물린다 — `db/**` 에는 한 글자도 쓰지 않고
#   도커 컨테이너도 하나 안 띄운다(진짜 판정은 `migration-drift` 가 한다).
#   도구 확인은 게이트의 **실물 경로 그대로** 지나가야 하므로 `$TD/bin` 에 stub
#   `alembic`·`docker` 를 두고 PATH 앞에 붙인다 — 도구 존재 확인만 통과시키고
#   준비 경계 시험은 실물 오라클을 스텁 도구로 실행해 SQL 미실행과 cleanup을 확인한다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/migration-drift.sh"
rc=0

# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

TD="$(mktemp -d -t migration-drift-selftest-XXXXXX)"
trap 'rm -rf "$TD"' EXIT

mkdir -p "$TD/bin"
printf '#!/usr/bin/env bash\nexit 0\n' > "$TD/bin/alembic"
printf '#!/usr/bin/env bash\nexit 0\n' > "$TD/bin/docker"
chmod +x "$TD/bin/alembic" "$TD/bin/docker"

mk_oracle() { # $1=디렉터리 $2=이름 $3=종료코드
  mkdir -p "$1"
  printf '#!/usr/bin/env bash\necho "[%s] 가짜 오라클"\nexit %s\n' "$2" "$3" > "$1/$2-drift.sh"
}

LAST_OUT=""
expect() { # $1=라벨 $2=green|red|미선언 $3=DIRS $4=MIN $5..=추가 env
  local name="$1" want="$2" dirs="$3" mins="$4"; shift 4
  local out ec
  set +e
  out="$(env PATH="$TD/bin:$PATH" \
             COLAB_MIGRATION_DRIFT_DIRS="$dirs" COLAB_MIGRATION_DRIFT_MIN="$mins" \
             "$@" "$GATE" 2>&1)"; ec=$?
  set -e
  LAST_OUT="$out"
  if expect_intercept_readiness "$ec" "$out" "$name" "$want"; then return; fi
  if [ "$want" = "red" ]; then
    if [ "$ec" -eq 0 ]; then
      echo "::error::migration-drift-selftest red — 케이스 $name 이 green 을 냈다 (fail-open)."
      printf '%s\n' "$out" | sed 's/^/      /'; rc=1
    else
      echo "  ✓ $name — red"
    fi
  else
    if [ "$ec" -eq 0 ]; then
      echo "  ✓ $name — green"
    else
      echo "::error::migration-drift-selftest red — 케이스 $name 이 red 를 냈다 (거짓 red)."
      printf '%s\n' "$out" | sed 's/^/      /'; rc=1
    fi
  fi
}

# ── ⓐ 대조군 — 2벌 전부 통과 ────────────────────────────────────────────────
mk_oracle "$TD/a" 0001 0; mk_oracle "$TD/a" 0002 0
expect "ⓐ 대조군(오라클 2벌 전부 green)" green "$TD/a" 2

# ⓖ 요약줄이 센 수를 낸다 — 대조군 출력에서 바로 읽는다.
if printf '%s' "$LAST_OUT" | grep -q '오라클 2 · 실행 2 · 실패 0'; then
  echo "  ✓ ⓖ 요약줄이 계수를 낸다 (오라클 2 · 실행 2 · 실패 0)"
else
  echo "::error::migration-drift-selftest red — 요약줄에서 계수를 읽지 못했다 (CLAUDE.md §5)."
  printf '%s\n' "$LAST_OUT" | sed 's/^/      /'; rc=1
fi

# ── ⓑ 되돌린 델타 — 1벌이 red 를 낸다 ──────────────────────────────────────
mk_oracle "$TD/b" 0001 0; mk_oracle "$TD/b" 0002 1
expect "ⓑ 되돌린 델타(오라클 1벌 red)" red "$TD/b" 2

# ── ⓒ 대상 0건 ─────────────────────────────────────────────────────────────
mkdir -p "$TD/c"
expect "ⓒ 대상 0건" red "$TD/c" 1

# ── ⓓ alembic 부재 ─────────────────────────────────────────────────────────
mk_oracle "$TD/d" 0001 0
expect "ⓓ alembic 부재" 미선언 "$TD/d" 1 COLAB_ALEMBIC="$TD/bin/no-such-alembic"

# ── ⓔ 실측 < 선언 최소 ─────────────────────────────────────────────────────
mk_oracle "$TD/e" 0001 0; mk_oracle "$TD/e" 0002 0
expect "ⓔ 실측 2벌 < 선언 최소 3벌" red "$TD/e" 3

# ── ⓕ docker 부재 ──────────────────────────────────────────────────────────
mk_oracle "$TD/f" 0001 0
expect "ⓕ docker 부재" 미선언 "$TD/f" 1 COLAB_MIGRATION_DRIFT_DOCKER="$TD/bin/no-such-docker"


# 준비 실패 단독은 78, 판정 실패와 섞이면 1. 자식 marker가 최종 분류를 덮지 못한다.
EXTRA=0
for kind in ready mixed; do
  mk_oracle "$TD/$kind" 0001 78
  sed -i '2i echo "::gate-readiness-failure::gate=fixture|detail=unavailable"' "$TD/$kind/0001-drift.sh"
  want=78; counts='실패 0 · 준비 실패 1'
  if [ "$kind" = mixed ]; then
    mk_oracle "$TD/$kind" 0002 1
    want=1; counts='실패 1 · 준비 실패 1'
  fi
  ec=0
  out="$(PATH="$TD/bin:$PATH" COLAB_ALEMBIC="$TD/bin/alembic" \
    COLAB_MIGRATION_DRIFT_DIRS="$TD/$kind" COLAB_MIGRATION_DRIFT_MIN=1 "$GATE" 2>&1)" || ec=$?
  if [ "$ec" -ne "$want" ] || ! printf '%s\n' "$out" | grep -q "$counts" ||
     { [ "$kind" = ready ] && printf '%s\n' "$out" | grep -q '^::gate-readiness-failure::.*cause=입력미선언'; } ||
     { [ "$kind" = mixed ] && printf '%s\n' "$out" | grep -q '^::gate-readiness-failure::'; }; then
    echo "::error::migration-drift-selftest red — $kind 집계: expected=$want actual=$ec / $counts"
    printf '%s\n' "$out" | sed 's/^/      /'; rc=1
  else
    echo "  ✓ $kind 집계 — exit $want · $counts"
  fi
  EXTRA=$((EXTRA+1))
done

# 실제 오라클의 준비 경계. SQL은 실행 기록만 남기고 실패시킨다. 컨테이너는 생성하지 않는다.
mkdir -p "$TD/pg-bin"
cat > "$TD/pg-bin/alembic" <<'STUB'
#!/usr/bin/env bash
printf '%s\n' 'd5_upload_transfer account_admin login_credential service_operator session_version status active inactive is_operator_read operator_read FOR SELECT app.operator_read'
STUB
cat > "$TD/pg-bin/docker" <<'STUB'
#!/usr/bin/env bash
case "$1" in
  image|pull) [ "$DRIFT_STUB_MODE" != image ]; exit $? ;;
  run) [ "$DRIFT_STUB_MODE" != run ]; exit $? ;;
  logs) [ "$DRIFT_STUB_MODE" = temporary ] || echo 'PostgreSQL init process complete; ready for start up'; exit 0 ;;
  rm) echo cleanup >> "$DRIFT_STUB_TRACE"; exit 0 ;;
  exec)
    case " $* " in
      *' pg_isready '*) [ "$DRIFT_STUB_MODE" = temporary ]; exit $? ;;
      *) echo sql >> "$DRIFT_STUB_TRACE"; exit 1 ;;
    esac ;;
esac
exit 1
STUB
printf '#!/usr/bin/env bash\nexit 0\n' > "$TD/pg-bin/sleep"
chmod +x "$TD/pg-bin/"*
for file in "$REPO_ROOT"/db/{platform,ai}/tests/*-drift.sh; do
  ec=0
  out="$(PATH="$TD/pg-bin:$PATH" COLAB_ALEMBIC="$TD/missing-alembic" bash "$file" 2>&1)" || ec=$?
  if [ "$ec" -ne 78 ]; then
    echo "::error::migration-drift-selftest red — ${file#"$REPO_ROOT/"} alembic 부재 expected=78 actual=$ec"; rc=1
  fi
  EXTRA=$((EXTRA+1))
done
for rev in 0008 0025 0028 0029 0032; do
  for mode in timeout temporary; do
    trace="$TD/trace-$rev-$mode"; : > "$trace"
    ec=0
    out="$(PATH="$TD/pg-bin:$PATH" COLAB_ALEMBIC="$TD/pg-bin/alembic" \
      DRIFT_STUB_MODE="$mode" DRIFT_STUB_TRACE="$trace" \
      bash "$REPO_ROOT/db/platform/tests/$rev-drift.sh" 2>&1)" || ec=$?
    if [ "$ec" -ne 78 ] || grep -q sql "$trace" || ! grep -q cleanup "$trace"; then
      echo "::error::migration-drift-selftest red — $rev $mode: expected=78 actual=$ec · SQL금지/cleanup 필요"
      printf '%s\n' "$out" | sed 's/^/      /'; rc=1
    else
      echo "  ✓ $rev $mode — exit78 · SQL 0회 · cleanup"
    fi
    EXTRA=$((EXTRA+1))
  done
done
for mode in image run; do
  trace="$TD/trace-$mode"; : > "$trace"
  ec=0
  out="$(PATH="$TD/pg-bin:$PATH" COLAB_ALEMBIC="$TD/pg-bin/alembic" \
    DRIFT_STUB_MODE="$mode" DRIFT_STUB_TRACE="$trace" \
    bash "$REPO_ROOT/db/platform/tests/0008-drift.sh" 2>&1)" || ec=$?
  if [ "$ec" -ne 78 ] || grep -q sql "$trace"; then
    echo "::error::migration-drift-selftest red — 0008 $mode: expected=78 actual=$ec · SQL금지"; rc=1
  fi
  EXTRA=$((EXTRA+1))
done

expect_readiness_verdict migration-drift-selftest "migration-drift 셀프테스트 케이스의 실행 환경"
[ "$rc" -eq 0 ] || exit 1
echo "migration-drift-selftest green — 기존 케이스 7종 + 준비 경계 ${EXTRA}건(ⓐ 대조군 green · ⓑ 되돌린 델타 red · ⓒ 대상 0건 red · ⓓ alembic 부재 red(준비) · ⓔ 건수 미달 red · ⓕ docker 부재 red(준비) · ⓖ 요약줄 계수)."
