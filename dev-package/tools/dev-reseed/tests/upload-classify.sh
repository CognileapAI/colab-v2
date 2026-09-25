#!/usr/bin/env bash
# 업로드 필수 칸 값 픽스처 — preflight ⑽ 과 seed ① 이 부르는 계획 생성기가 서명 전 값을 거절하는가.
#
# 무엇을 증명하는가 =
#   ⓐ 커밋된 `dev-seed/upload-classify.json` 이 서명 전(`status != signed`)이면
#      `build_plan.py --dry-run --require-signed-classify`(preflight ⑽ 의 호출)가 **비영 종료**하고
#      「서명」을 말한다 → dev 를 바꾸기 전에 멈춘다. `preflight.sh` 가 그 인자를 실제로 넘기는지도 본다.
#   ⓓ 인자 없는 `--dry-run`(`seed-plan-drift` 의 실물 대조)은 서명과 무관하게 선다 — 두 판정을 섞지 않는다.
#   ⓑ 같은 28행을 서명본으로 바꾸면 같은 호출이 0 으로 끝나고 요약줄 `datasets 28 edges 18` 을 낸다.
#   ⓒ 서명본에서 한 행의 분류를 비우면 그 행 이름을 대고 비영 종료한다.
#
# 왜 필요한가 = 2026-09-24 dev 3회차가 seq 1 의 ① 분류에서 멈췄다 — 6705675d 가 분류·유형을 빈 값으로
#   시작하게 바꿨고 러너·계획에 그 칸이 없었다. 값은 정본 md 에 없어 제안표에 Ted 서명이 필요하다.
#   서명 전 값으로 dev 를 돌리지 않는다는 규칙이 어느 검사에도 걸리지 않으면 조용히 새어 나간다.
#
# dev·AWS 무접촉 = 참조자료 없이(`--ref-root` 부재) 게이트 md 픽스처로 블록 계수만 센다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
GEN="$REPO/dev-package/tools/dev-seed/build_plan.py"
CLASSIFY="$REPO/dev-package/tools/dev-seed/upload-classify.json"
MD="$REPO/gates/fixtures/seed-plan-drift/green/md"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

python3 -c 'import yaml' >/dev/null 2>&1 || {
  printf '::gate-readiness-failure::gate=dev-reseed-selftest|waited_for=PyYAML|limit=-|elapsed=-|detail=upload-classify 픽스처가 build_plan.py 를 못 돌린다\n'
  exit 78; }
for f in "$GEN" "$CLASSIFY" "$MD"; do [ -e "$f" ] || { echo "✗ 판정 재료 부재: ${f#"$REPO/"}"; exit 1; }; done

BAD=0
note() { echo "✗ $*"; BAD=$((BAD + 1)); }
plan() { python3 "$GEN" --dry-run --require-signed-classify --md-root "$MD" --ref-root "$WORK/no-ref-root" "$@" 2>&1; }

status="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["status"])' "$CLASSIFY")"
out="$(plan)"; rc=$?
if [ "$status" = signed ]; then
  [ "$rc" = 0 ] || note "ⓐ 서명본인데 계획 생성기가 비영 종료했다(rc=$rc)"
else
  [ "$rc" != 0 ] && printf '%s' "$out" | grep -q '서명' \
    || note "ⓐ 서명 전(status=$status) 값인데 계획 생성기가 멈추지 않았다(rc=$rc)"
fi
sed -n '/^pf_build_plan()/,/^}/p' "$REPO/dev-package/tools/dev-reseed/preflight.sh" | grep -q -- '--require-signed-classify' \
  || note "ⓐ preflight ⑽(pf_build_plan)이 --require-signed-classify 를 넘기지 않는다"
out="$(python3 "$GEN" --dry-run --md-root "$MD" --ref-root "$WORK/no-ref-root" 2>&1)"; rc=$?
[ "$rc" = 0 ] || note "ⓓ 서명 요구 없는 --dry-run(seed-plan-drift 형)이 비영 종료했다(rc=$rc)"

python3 - "$CLASSIFY" "$WORK/signed.json" "$WORK/blank.json" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
doc.update(status="signed", signedBy="fixture", signedOn="2026-09-24")
json.dump(doc, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
doc["datasets"][1]["category"] = ""
json.dump(doc, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False)
PY
out="$(plan --classify "$WORK/signed.json")"; rc=$?
{ [ "$rc" = 0 ] && printf '%s\n' "$out" | grep -qE '^datasets 28 edges 18( |$)'; } \
  || note "ⓑ 서명본 28행으로 계획 생성기가 서지 않았다(rc=$rc)"
out="$(plan --classify "$WORK/blank.json")"; rc=$?
{ [ "$rc" != 0 ] && printf '%s' "$out" | grep -q 'rn15 15분 누적강수'; } \
  || note "ⓒ 분류를 비운 행(seq 2)을 이름으로 대지 않았다(rc=$rc)"

[ "$BAD" = 0 ] || exit 1
echo "✓ 업로드 필수 칸 값 — 서명 전 거절(preflight) · 서명본 28/18 · 빈 칸 행 이름 · 실물 대조와 분리"
