#!/usr/bin/env bash
# service-tests 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 판정은 전부 **픽스처 사본 트리**에서 난다 — `services/**` 에는 한 글자도 쓰지 않고, 서비스
# 묶음(1070건)을 다시 돌리지도 않는다. 여기서 증명할 것은 「시험이 통과하는가」가 아니라
# **「게이트가 red 를 낼 수 있는가」** 다(`frontend-test-selftest` 와 같은 배치).
# 픽스처 원본 = `gates/fixtures/service-tests/`(README 에 트리별 기대가 있다).
#
#   ⓐ 통과 시험 1건                  → green            ← 이것이 green 이 아니면 아래는 아무 말도 안 한다
#   ⓑ 시험 1건 실패                  → red              ← 실패를 못 잡으면 게이트가 아니다
#   ⓒ ⭑ **수집 0건**                 → red              ← green-by-skip 금지. 이 레포의 대표 실패형
#   ⓓ ⭑ **수집은 되고 실행 0건(전부 skip)** → red       ← 수집만 하고 안 돈 것도 판정이 아니다
#   ⓔ ⭑ **venv·파이썬 부재**         → red(준비 · 78)   ← 「못 돌았음」은 통과가 아니다
#   ⓕ 표식 선택자 인자 없음          → red              ← 필수 인자 없이 대상 0건인 채 통과 금지
#   ⓖ 단위 이름 인자 없음            → red
#   ⓗ 단위 자리 부재                 → red              ← 대상 0건은 통과가 아니다
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/service-tests.sh"
FIX="$REPO_ROOT/gates/fixtures/service-tests"
rc=0

red() { echo "::error::service-tests-selftest red — $*"; exit 1; }
[ -x "$GATE" ] || red "판정 재료가 없다: gates/tools/service-tests.sh"
[ -d "$FIX" ]  || red "픽스처가 없다: gates/fixtures/service-tests/. 대상 0건은 통과가 아니다."

# 판정에 쓸 파이썬 — 서비스 venv 중 **아무거나 하나**면 된다(픽스처 시험은 pytest 만 쓴다).
# 하나도 없으면 skip 이 아니라 **red(준비)** 다. 그 skip 이 정확히 v1 의 실패였다.
PY=""
for s in viz-render pipeline-worker ai-service core-api; do
  if [ -x "$REPO_ROOT/services/$s/.venv/bin/python" ]; then PY="$REPO_ROOT/services/$s/.venv/bin/python"; break; fi
done
if [ -z "$PY" ]; then
  printf '::gate-readiness-failure::gate=%s|waited_for=%s|limit=%s|elapsed=%s|detail=%s\n' \
    service-tests-selftest "서비스 venv 중 하나(pytest 를 든 파이썬)" "대기 없음" "0초" \
    "네 단위 어디에도 .venv 가 없어 픽스처 트리를 판정할 수 없다."
  echo "::error::service-tests-selftest red(준비) — 서비스 venv 가 이 체크아웃에 하나도 없다.
   services/<단위> 에서 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt [-r requirements-dev.txt]' 를
   돌린 뒤 재실행한다. **준비 실패도 red 다** — 건너뛰기로 green 을 만들지 않는다."
  exit 78
fi

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" svc-tests-st-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT INT TERM

mk_tree() { # $1 = 픽스처 이름 → stdout: 사본 자리
  # 케이스마다 **새 자리**를 준다. 같은 자리에 두 번 복사하면 `cp -r` 이 안으로 들어가
  # `tests/tests` 가 생기고, pytest 가 같은 모듈 이름을 두 번 보고 수집 오류를 낸다 —
  # 판정이 아니라 배선이 낸 red 다. 자리 이름은 `mktemp` 가 준다(이 함수는 `$( )` 안에서
  # 불려 서브셸이라 카운터 변수는 부모로 돌아오지 않는다).
  local name="$1" d
  d="$(mktemp -d -p "$TMP" "$name-XXXXXX")"
  cp -r "$FIX/$name/tests" "$d/tests"
  printf '%s' "$d"
}

expect_case() { # $1=기대(green|red|red-ready) $2=이름 $3=단위이름 $4=선택자 [$5=트리(있으면 DIR 주입) $6=py주입여부]
  local want="$1" name="$2" svc="$3" select="$4" dir="${5:-}" withpy="${6:-yes}"
  local out ec
  local envs=()
  [ -n "$dir" ] && envs+=("COLAB_SERVICE_TESTS_DIR=$dir")
  [ "$withpy" = "yes" ] && envs+=("COLAB_SERVICE_TESTS_PY=$PY")
  out="$(env "${envs[@]+"${envs[@]}"}" "$GATE" "$svc" "$select" 2>&1)"; ec=$?
  case "$want" in
    green)     [ "$ec" -eq 0 ]  && { echo "  ✓ $name — green"; return; } ;;
    red-ready) [ "$ec" -eq 78 ] && { echo "  ✓ $name — red(준비 · 78)"; return; } ;;
    red)       [ "$ec" -eq 1 ]  && { echo "  ✓ $name — red"; return; } ;;
  esac
  echo "::error::service-tests-selftest red — 케이스 $name 이 기대($want)와 다른 종료 코드 $ec 를 냈다."
  printf '%s\n' "$out" | tail -30 | sed 's/^/     /'
  rc=1
}

# ⓐ green 대조군 — 이것이 green 이 아니면 아래 red 들은 「무엇이든 red 를 낸다」와 구분되지 않는다.
expect_case green     "ⓐ 통과 시험 1건"                        fixture "not e2e" "$(mk_tree pass)"
# ⓑ 실패 1건 → red
expect_case red       "ⓑ 시험 1건 실패"                        fixture "not e2e" "$(mk_tree fail)"
# ⓒ 수집 0건 → red. **통과 0·실패 0 은 「전부 통과」가 아니다**
expect_case red       "ⓒ 수집 0건 (green-by-skip 금지)"        fixture "not e2e" "$(mk_tree empty)"
# ⓓ 수집은 되는데 실행 0건(전부 skip) → red
expect_case red       "ⓓ 실행 0건 · 전부 skip"                 fixture "not e2e" "$(mk_tree allskip)"
# ⓔ 파이썬 부재 → red(준비). 사본 트리에 `.venv` 를 두지 않고 주입도 하지 않는다.
expect_case red-ready "ⓔ venv·파이썬 부재"                     fixture "not e2e" "$(mk_tree pass)" no
# ⓕ·ⓖ 필수 인자 부재 → red (관대한 기본값으로 채우지 않는다)
expect_case red       "ⓕ 표식 선택자 인자 없음"                fixture "" "$(mk_tree pass)"
expect_case red       "ⓖ 단위 이름 인자 없음"                  "" "not e2e" "$(mk_tree pass)"
# ⓗ 단위 자리 부재 → red (대상 0건은 통과가 아니다)
expect_case red       "ⓗ 단위 자리 부재"                       fixture "not e2e" "$TMP/없는자리"

# ⓘ 선택자가 실제로 **걸러 낸다**는 것 — 정밀도를 올린 것이지 범위를 줄인 것이 아님의 증명.
#    같은 트리를 `not e2e`(수집 2 · 실패 1 → red)와 「실패 케이스만 뺀 선택자」로 각각 돌린다.
d="$(mk_tree fail)"
OUT_ALL="$(env COLAB_SERVICE_TESTS_DIR="$d" COLAB_SERVICE_TESTS_PY="$PY" "$GATE" fixture "not e2e" 2>&1)"
if ! printf '%s' "$OUT_ALL" | grep -q '수집 2 · 실행 2 · skipped 0'; then
  echo "::error::service-tests-selftest red — 요약줄이 계수를 말하지 않는다(수집 2 · 실행 2 를 못 찾았다)."
  printf '%s\n' "$OUT_ALL" | tail -20 | sed 's/^/     /'
  rc=1
else
  echo "  ✓ ⓘ 요약줄이 수집·실행·skipped·deselected·failed 를 계수로 낸다"
fi

exit $rc
