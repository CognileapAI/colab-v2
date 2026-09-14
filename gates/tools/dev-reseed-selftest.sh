#!/usr/bin/env bash
# `dev-package/tools/dev-reseed/` 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 왜 게이트인가 = 이 도구의 판독부(요약줄 파싱·계수 대조·미리보기 판정)는 **어느 검사에도
#   걸리지 않았다.** 그래서 ⑴ `deploy_doctor` 요약줄을 한 줄도 못 잡는 파서 ⑵ 계수가 맞아도
#   미달로 떨어지는 계획 판정 ⑶ 값을 못 받으면 「성립」으로 읽는 미리보기 판정이 그대로 있었고,
#   전부 **dev 를 한 번 돌려 보고서야** 드러날 자리였다. 검사가 사람의 실행 안에만 있으면
#   그것은 검사가 아니다 — 이 레포의 green-by-skip 계열이다.
#
# 픽스처 셋 —
#   ⓐ `tests/doctor-parse.sh`   실물 모양 표본으로 요약줄 파서를 판정한다(dev 무접촉 · 파일만 읽는다).
#   ⓑ `tests/preflight-red.sh`  조건을 어긋나게 두고 `reseed.sh` 를 실제로 돌린다.
#      `ssh`·`scp`·`docker`·`aws`·`agent-browser` 를 PATH 대역으로 가려 **실물에 한 바이트도 나가지 않는다.**
#   ⓒ `tests/preflight-secrets.sh` preflight ⑻ `secrets` 가 **통과할 수 있는 항목**임을 증명한다.
#      ⓑ 는 ssh 가 안 붙는 상태만 재서 「붙었을 때 무엇을 묻는가」가 검사 밖이었고, 그 사이
#      `printf` 짝짓기 결함으로 9건 중 1건만 물어 이 항목이 green 이 된 적이 없었다(DR-4 §5 ⑵).
#   ⓓ `tests/remote-transport.sh` **원격 셸로 값을 나르는 자리**를 판정한다. ssh 대역이 받은
#      원격 스크립트를 로컬 bash 로 실제로 실행하므로 「원격 셸이 그 문장을 어떻게 읽는가」가
#      재현된다. 왜 = `psql_master_query` 가 SQL 을 `export SQL='<값>'` 로 실어 값 속 작은따옴표가
#      바깥을 닫았고(`column "colab_platform" does not exist`) 그 경로는 **실모드로 돈 적이
#      없었다**(DR-4 §6). 함께 판정 = 정지 뒤 실패의 자동 재기동 · 오류 1회 기록 · 리허설.
#   ⓔ `tests/s3-review.sh` **계획 검토 본문**을 판정한다. 계획은 초기화 도구 컨테이너(`--user 0`)가
#      uid 0 · 0600 으로 쓰고 검토도 같은 컨테이너 안에서 돈다 — 두 uid 가 갈리면 red 다.
#      왜 = 호스트 ssh 사용자(uid 1000)로 돌던 종전 검토는 **실모드에서 통과할 수 없었고**
#      `--dry-run`·`--rehearse` 어느 쪽도 그 본문을 밟지 않아 검사 밖이었다(DR-4 §7).
#
# ── red 를 두 갈래로 가른다 (`rules/colab-rules.md §3-4`) ──────────────────
#   red(판정) = 픽스처가 「도구가 fail-closed 가 아니다」를 찾았다 → 종료 1
#   red(준비) = 픽스처가 **못 돌았다**(실행기·재료 부재) → 종료 78 ＋ `::gate-readiness-failure::`
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
RESEED_DIR="$REPO_ROOT/dev-package/tools/dev-reseed"
GATE=dev-reseed-selftest

ready_fail() { # $1=기다린 대상 $2=상세
  printf '::gate-readiness-failure::gate=%s|waited_for=%s|limit=-|elapsed=-|detail=%s\n' "$GATE" "$1" "$2"
  echo "::error::$GATE red(준비) — $2" >&2
  exit 78
}

# ── 준비 ─────────────────────────────────────────────────────────────────
# 실행기가 없으면 **판정하지 못한 것**이다. 없는 것을 통과로 세지 않는다.
for tool in bash python3 git; do
  command -v "$tool" >/dev/null 2>&1 || ready_fail "실행기 $tool" "cause=실행기부재 $tool 이 PATH 에 없다"
done

# 판정 재료가 없으면 red(판정)다 — 픽스처는 이 레포가 가지고 있어야 하는 파일이다.
CASES=(
  "$RESEED_DIR/tests/doctor-parse.sh"
  "$RESEED_DIR/tests/preflight-red.sh"
  "$RESEED_DIR/tests/preflight-secrets.sh"
  "$RESEED_DIR/tests/remote-transport.sh"
  "$RESEED_DIR/tests/s3-review.sh"
)
MATERIALS=(
  "$RESEED_DIR/reseed.sh" "$RESEED_DIR/lib.sh" "$RESEED_DIR/preflight.sh" "$RESEED_DIR/stages.sh"
  "$RESEED_DIR/tests/fixtures/doctor-15-15.txt" "$RESEED_DIR/tests/fixtures/doctor-14-15.txt"
)
for f in "${CASES[@]}" "${MATERIALS[@]}"; do
  [ -f "$f" ] || { echo "::error::$GATE red(판정) — 판정 재료가 없다: ${f#"$REPO_ROOT/"}" >&2; exit 1; }
done

# ── 판정 ─────────────────────────────────────────────────────────────────
PASSED=0
FAILED=()
READINESS=()

for case_path in "${CASES[@]}"; do
  name="$(basename "$case_path" .sh)"
  out="$(bash "$case_path" 2>&1)"; rc=$?
  if [ "$rc" = 78 ] || { [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q '::gate-readiness-failure::'; }; then
    # 픽스처가 못 돌았다 — 판정된 적이 없으므로 통과로도 결함으로도 세지 않는다.
    READINESS+=("$name (rc=$rc)")
    printf '%s\n' "$out" | sed 's/^/     /'
    continue
  fi
  if [ "$rc" -eq 0 ]; then
    PASSED=$(( PASSED + 1 ))
    echo "  ✓ $name"
  else
    FAILED+=("$name (rc=$rc)")
    echo "  ✗ $name (rc=$rc)"
    printf '%s\n' "$out" | sed 's/^/     /'
  fi
done

echo
echo "$GATE — 픽스처 ${#CASES[@]} · 통과 $PASSED · 결함 ${#FAILED[@]} · 판정 못 함 ${#READINESS[@]}"

if [ "${#FAILED[@]}" -gt 0 ]; then
  echo "::error::$GATE red(판정) — 픽스처 ${#FAILED[@]}건이 fail-closed 를 증명하지 못했다:" >&2
  printf '  - %s\n' "${FAILED[@]}" >&2
  exit 1
fi
if [ "${#READINESS[@]}" -gt 0 ]; then
  printf '::gate-readiness-failure::gate=%s|waited_for=픽스처 실행 환경(%d건)|limit=-|elapsed=-|detail=%s\n' \
    "$GATE" "${#READINESS[@]}" "${READINESS[*]}"
  echo "::error::$GATE red(준비) — 아래 픽스처를 **판정하지 못했다**. 통과로 세지 않는다:" >&2
  printf '  - %s\n' "${READINESS[@]}" >&2
  exit 78
fi
# 대상 0건은 통과가 아니다.
[ "$PASSED" -eq "${#CASES[@]}" ] || {
  echo "::error::$GATE red(판정) — 판정한 픽스처가 $PASSED 건뿐이다(기대 ${#CASES[@]})" >&2; exit 1; }
echo "$GATE — green (요약줄 파서 · preflight fail-closed · 계획 요약줄 · result.json · die 복귀 · 미리보기 판정불가 · 원격 전송로 · 실패 후 자동 재기동 · 리허설 fail-closed · 계획 검토 소유자·모드·접두사)"
exit 0
