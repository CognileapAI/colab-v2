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
# ⚠ 실물 오라클을 다시 돌리지 않는다. 케이스마다 `mktemp -d` 안에 **가짜 `*-drift.sh`** 를
#   짓고 `COLAB_MIGRATION_DRIFT_DIRS`/`_MIN` 으로 물린다 — `db/**` 에는 한 글자도 쓰지 않고
#   도커 컨테이너도 하나 안 띄운다(진짜 판정은 `migration-drift` 가 한다).
#   도구 확인은 게이트의 **실물 경로 그대로** 지나가야 하므로 `$TD/bin` 에 stub
#   `alembic`·`docker` 를 두고 PATH 앞에 붙인다 — 도구 존재 확인만 통과시키고
#   오라클은 그 stub 을 부르지 않는다.
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

expect_readiness_verdict migration-drift-selftest "migration-drift 셀프테스트 케이스의 실행 환경"
[ "$rc" -eq 0 ] || exit 1
echo "migration-drift-selftest green — 케이스 7종(ⓐ 대조군 green · ⓑ 되돌린 델타 red · ⓒ 대상 0건 red · ⓓ alembic 부재 red(준비) · ⓔ 건수 미달 red · ⓕ docker 부재 red(준비) · ⓖ 요약줄 계수)."
