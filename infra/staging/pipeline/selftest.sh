#!/usr/bin/env bash
# 파이프라인 fail-closed 증명 — 원장·롤백 대상·잠금·표식이 **거짓 green 을 못 내는지** 시험한다.
#
# `verify/selftest.sh` 가 판정기(헬스·본문·타깃·승인·체인)를 맡고, 이 파일은 **기억**을 맡는다 —
# 릴리스 원장이 「직전 green」을 잘못 짚으면 롤백은 옳은 스크립트로 틀린 곳에 간다.
#
# 운영 스택을 건드리지 않는다. `docker` 는 PATH 껍데기로 갈아 끼우고, 상태 디렉터리는 임시본이다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
FAILED=0; N=0
ck() { # $1=라벨 $2=기대 $3=실제
  N=$((N+1))
  if [ "$2" = "$3" ]; then echo "  PASS  [$1] $3"
  else echo "  FAIL  [$1] 기대 「$2」 · 실제 「$3」"; FAILED=$((FAILED+1)); fi
}

export COLAB_PIPELINE_STATE_DIR="$TMP/state"
. "$HERE/lib.sh"

# ── 이미지 실물 픽스처. `images_exist` 가 「있다」고 답할 태그를 여기서 정한다.
mkdir -p "$TMP/bin"
cat > "$TMP/bin/docker" <<'SH'
#!/usr/bin/env bash
# 껍데기 — `image inspect <ref>` 만 답한다. EXISTING_TAGS 에 있는 태그만 존재로 친다.
[ "${1:-}" = image ] || exit 1
[ "${2:-}" = inspect ] || exit 1
ref="${!#}"; tag="${ref##*:}"
case " ${EXISTING_TAGS:-} " in *" $tag "*) exit 0 ;; esac
exit 1
SH
chmod +x "$TMP/bin/docker"
export PATH="$TMP/bin:$PATH"

echo "── P1 원장이 비면 롤백 대상이 **없다** (조용히 자리표시로 떨어지지 않는다)"
export EXISTING_TAGS="aaa bbb"
if ledger_rollback_target "" >/dev/null 2>&1; then ck P1 "대상없음" "대상있음"; else ck P1 "대상없음" "대상없음"; fi

echo "── P2 green 릴리스 둘 중 **직전**(현재 제외)을 짚는다"
ledger_append deploy aaa aaa green "1차"
ledger_append deploy bbb bbb green "2차"
ck P2 "aaa" "$(ledger_rollback_target bbb)"

echo "── P3 **red 릴리스는 롤백 대상이 아니다**"
ledger_append deploy ccc ccc red "3차 실패"
export EXISTING_TAGS="aaa bbb ccc"
ck P3 "bbb" "$(ledger_rollback_target ccc)"

echo "── P4 **이미지가 없는 릴리스는 롤백 대상이 아니다** (원장 한 줄 ≠ 롤백 가능)"
export EXISTING_TAGS="aaa"
ck P4 "aaa" "$(ledger_rollback_target bbb)"

echo "── P5 원장에 있어도 이미지가 하나도 없으면 **실패한다** (0건을 성공으로 읽지 않는다)"
export EXISTING_TAGS=""
if ledger_rollback_target "" >/dev/null 2>&1; then ck P5 "실패" "성공"; else ck P5 "실패" "실패"; fi

echo "── P6 승인 행은 롤백 대상이 아니다 (종류가 deploy 여야 한다)"
export EXISTING_TAGS="zzz"
ledger_append approve zzz zzz green "승인자=Ted 본것=화면"
if [ -z "$(ledger_rollback_target "" 2>/dev/null)" ]; then ck P6 "대상없음" "대상없음"; else ck P6 "대상없음" "대상있음"; fi

echo "── P7 원장 보존 = 30건 (넘치면 오래된 것부터 잘린다)"
COLAB_LEDGER_KEEP=30
for i in $(seq 1 40); do ledger_append deploy "s$i" "s$i" green "n$i"; done
ck P7 "30" "$(wc -l < "$(ledger_path)" | tr -d ' ')"

echo "── P8 실패 표식은 **다음 성공에서만** 사라진다"
mark_failed "시험" "일부러"
ck P8 "있음" "$([ -f "$(failmark_path)" ] && echo 있음 || echo 없음)"
mark_success "s40"
ck P8b "없음" "$([ -f "$(failmark_path)" ] && echo 있음 || echo 없음)"
ck P8c "있음" "$([ -s "$(success_path)" ] && echo 있음 || echo 없음)"

echo "── P9 요약줄이 검사 대상 0건을 **green 으로 말하지 않는다**"
( FAILED=0; SKIPPED=0; CHECKED=0; verdict "0건 시험" ) >"$TMP/o" 2>&1
if grep -q "RED (검사 대상 0건" "$TMP/o"; then ck P9 "RED" "RED"; else ck P9 "RED" "$(cat "$TMP/o")"; fi

echo "── P10 롤백: 대상을 안 밝히면 **거부한다** (기본값으로 자리표시에 가지 않는다)"
N=$((N+1))
if "$HERE/../rollback.sh" >/dev/null 2>&1; then
  echo "  FAIL  [P10] 대상 없이도 롤백이 진행됐다"; FAILED=$((FAILED+1))
else echo "  PASS  [P10] 거부"; fi

echo "── P11 배포: 타깃을 안 밝히면 **거부한다**"
N=$((N+1))
if "$HERE/../deploy.sh" >/dev/null 2>&1; then
  echo "  FAIL  [P11] 타깃 없이도 배포가 진행됐다"; FAILED=$((FAILED+1))
else echo "  PASS  [P11] 거부"; fi

echo "── P12 배포: prod 타깃은 **거부한다** (승인 없이 도는 경로가 없다)"
N=$((N+1))
if "$HERE/../deploy.sh" --target prod >/dev/null 2>&1; then
  echo "  FAIL  [P12] prod 로 배포가 진행됐다"; FAILED=$((FAILED+1))
else echo "  PASS  [P12] 거부"; fi

echo "── P13 배포: 필수 설정이 비면 **빌드 전에** 멈춘다 (⑦ 까지 가지 않는다)"
# 2026-08-28 첫 staging 배포는 게이트·태그보존·빌드·백업을 다 치르고 ⑦ 에서 죽었다.
# 이제 그 판정이 ⓪-b 로 앞당겨졌는지 — **빌드 줄이 나오지 않는지** 로 확인한다.
# 픽스처 env 는 가짜 값이다. 실물 env 파일도 도커도 건드리지 않는다.
mkdir -p "$TMP/pf"; : > "$TMP/pf/dummy"
: > "$TMP/pf/no-owner.env"
while read -r k; do
  [ -n "$k" ] || continue
  [ "$k" = COLAB_OWNER_PASSWORD ] && continue
  case "$k" in
    *_FILE) printf '%s=%s\n' "$k" "$TMP/pf/dummy" ;;
    *_DIR)  printf '%s=%s\n' "$k" "$TMP/pf" ;;
    *)      printf '%s=fixture-not-a-real-secret\n' "$k" ;;
  esac >> "$TMP/pf/no-owner.env"
done < <(env -i PATH="$PATH" bash -c '. "$1"; preflight_required_keys' _ "$HERE/../preflight.sh")

COLAB_STAGING_ENV="$TMP/pf/no-owner.env" "$HERE/../deploy.sh" --target staging >"$TMP/d" 2>&1; DRC=$?
N=$((N+1))
if [ "$DRC" -eq 0 ]; then echo "  FAIL  [P13] 필수 설정이 비었는데 배포가 진행됐다"; FAILED=$((FAILED+1))
elif ! grep -q "COLAB_OWNER_PASSWORD" "$TMP/d"; then
  echo "  FAIL  [P13] 멈추긴 했으나 어느 키가 없는지 말하지 않는다"; FAILED=$((FAILED+1))
elif grep -q "이미지 빌드" "$TMP/d"; then
  echo "  FAIL  [P13] 빌드까지 간 뒤에 멈췄다 — 프리플라이트가 늦다"; FAILED=$((FAILED+1))
else echo "  PASS  [P13] 빌드 전에 거부 · 빠진 키 이름을 말한다"; fi
N=$((N+1))
if grep -q "fixture-not-a-real-secret" "$TMP/d"; then
  echo "  FAIL  [P13b] 배포 출력에 설정 값이 섞였다"; FAILED=$((FAILED+1))
else echo "  PASS  [P13b] 출력에 값이 없다"; fi

echo
echo "── 판정기 selftest 도 이어서 돈다"
"$HERE/../verify/selftest.sh" || FAILED=$((FAILED+1))

echo
if [ "$FAILED" -ne 0 ]; then echo "pipeline selftest: RED (실패 ${FAILED}건 / ${N}건 + 판정기)"; exit 1; fi
echo "pipeline selftest: GREEN (${N}건 + 판정기 전건 기대대로)"
