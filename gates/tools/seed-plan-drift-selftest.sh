#!/usr/bin/env bash
# `seed-plan-drift` 가 red fixture 로 **fail-closed** 임을 증명한다 (CLAUDE.md §4).
#
# 케이스 4 — 형식은 `gates/tools/harness-eval-selftest.sh`(임시 dir 사본 · exit 코드 단언).
#   ⓐ 등재표를 손으로 고침(바이트 한 칸)    → red(판정) · 출력에 `MANIFEST-DRIFT`
#   ⓑ md 에서 데이터셋 한 행 삭제(표＋블록)  → red(판정) · 출력에 `28`(총계가 md 에서 나온다)
#   ⓒ 참조자료도 면제 선언도 없음           → red(준비 · 78 · 입력미선언) 침묵은 통과가 아니다
#   ⓓ 면제 선언                             → green ＋ 요약에 「면제」·「실물 대조 미실행」
#
# ⓐⓑ 가 통과해 버리면 이 게이트는 아무것도 막지 않는다 — 그 둘이 존재 이유다.
# ⓒ 는 「참조자료가 없으면 조용히 넘어간다」를 잡는다(green-by-skip 의 정확한 모양).
# ⓓ 는 「면제인데 그 사실이 요약에 안 보인다」를 잡는다 — 면제가 조용해지는 순간 건너뛰기다.
# ⚠ ⓐⓑ 는 **면제를 선언한 채로** 돈다 — 면제가 md→등재표 대조까지 덮지 않음을 함께 증명한다.
#
# 픽스처 원본 = `gates/fixtures/seed-plan-drift/{green,red}/`, 판정은 `mktemp -d` **사본**에서만
#   난다(이 레포 경로에는 공백(`00 CoLAB`)이 있고, 원본을 그 자리에서 고치면 레포가 더러워진다).
# 참조자료 드라이브를 **한 번도 읽지 않는다** — 네 케이스 전부 `COLAB_REF_ROOT` 를 비운다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/seed-plan-drift.sh"
FX="$REPO_ROOT/gates/fixtures/seed-plan-drift"
DROUGHT_REL="01.level-data/03.drought/DATASETS.md"
FAILED=0

red() { echo "::error::seed-plan-drift-selftest red — $*"; FAILED=1; }

# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나 — 78 을 「기대한 red」로 접지 않는다.
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

[ -x "$GATE" ] || { echo "::error::seed-plan-drift-selftest red — 판정 재료가 없다: gates/tools/seed-plan-drift.sh"; exit 1; }
for f in "$FX/green/plan-manifest.yaml" "$FX/red/manifest-hand-edit.yaml" \
         "$FX/red/md-row-removed/DATASETS.md" "$FX/green/md/$DROUGHT_REL"; do
  [ -f "$f" ] || { echo "::error::seed-plan-drift-selftest red — 픽스처가 없다: ${f#"$REPO_ROOT/"}"; exit 1; }
done

WORK="$(mktemp -d -t seed-plan-drift-selftest-XXXXXX)"
cleanup() { rm -rf "$WORK"; }
trap cleanup EXIT

# 사본 둘 — 성한 md 나무 하나, 행 하나를 뺀 나무 하나.
MD_OK="$WORK/md-ok"
MD_DROP="$WORK/md-drop"
cp -r "$FX/green/md" "$MD_OK"
cp -r "$FX/green/md" "$MD_DROP"
cp "$FX/red/md-row-removed/DATASETS.md" "$MD_DROP/$DROUGHT_REL"
MAN_OK="$WORK/plan-manifest.yaml"
MAN_EDITED="$WORK/plan-manifest-hand-edit.yaml"
cp "$FX/green/plan-manifest.yaml" "$MAN_OK"
cp "$FX/red/manifest-hand-edit.yaml" "$MAN_EDITED"

expect() { # $1=기대(green|red|ready|미선언) $2=이름 $3=케이스 키
  local want="$1" label="$2" key="$3" out rc
  case "$key" in
    hand_edit)
      out="$(COLAB_SEED_PLAN_MD_ROOT="$MD_OK" COLAB_SEED_PLAN_MANIFEST="$MAN_EDITED" \
             COLAB_REF_ROOT= COLAB_SEED_PLAN_NO_FILES=1 "$GATE" 2>&1)"; rc=$? ;;
    row_removed)
      out="$(COLAB_SEED_PLAN_MD_ROOT="$MD_DROP" COLAB_SEED_PLAN_MANIFEST="$MAN_OK" \
             COLAB_REF_ROOT= COLAB_SEED_PLAN_NO_FILES=1 "$GATE" 2>&1)"; rc=$? ;;
    undeclared)
      out="$(COLAB_SEED_PLAN_MD_ROOT="$MD_OK" COLAB_SEED_PLAN_MANIFEST="$MAN_OK" \
             COLAB_REF_ROOT= COLAB_SEED_PLAN_NO_FILES= "$GATE" 2>&1)"; rc=$? ;;
    exempt)
      out="$(COLAB_SEED_PLAN_MD_ROOT="$MD_OK" COLAB_SEED_PLAN_MANIFEST="$MAN_OK" \
             COLAB_REF_ROOT= COLAB_SEED_PLAN_NO_FILES=1 "$GATE" 2>&1)"; rc=$? ;;
    *) red "$label — 알 수 없는 케이스 키: $key"; return ;;
  esac
  if expect_intercept_readiness "$rc" "$out" "$label" "$want"; then
    return
  fi
  # 여기까지 왔다는 것은 분류기가 green·red 로 **판정했다**는 뜻이다. 준비 실패를 기대한
  # 케이스가 여기 닿으면 그 케이스는 재려던 것을 재지 못했다 — 통과로 세지 않는다.
  # (`_expect.sh` 의 가로채기는 준비 실패만 처리하고 나머지는 부르는 쪽에 돌려준다.)
  case "$want" in
    ready|미선언)
      red "$label — red(준비)여야 하는데 판정이 났다(rc=$rc):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return ;;
  esac
  if [ "$want" = green ] && [ "$rc" -ne 0 ]; then
    red "$label — green 이어야 하는데 red 다(rc=$rc):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  if [ "$want" = red ] && [ "$rc" -eq 0 ]; then
    red "$label — red 여야 하는데 통과했다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  # red 는 **무엇이 어긋났는지**를 이름으로 내야 한다 — 「어딘가 다르다」는 고칠 수 없다.
  if [ "$key" = hand_edit ] && ! printf '%s' "$out" | grep -q 'MANIFEST-DRIFT'; then
    red "$label — red 인데 어느 줄이 갈렸는지를 내지 않았다(MANIFEST-DRIFT 없음):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  if [ "$key" = row_removed ] && ! printf '%s' "$out" | grep -q '28'; then
    red "$label — red 인데 총계 기대값(28)을 사유로 내지 않았다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return
  fi
  # 면제 케이스는 **면제라는 사실과 미실행 사실**을 요약에 보여야 한다.
  if [ "$key" = exempt ]; then
    printf '%s' "$out" | grep -q '면제' \
      || { red "$label — 면제인데 요약에 「면제」가 없다(조용한 건너뛰기):
$(printf '%s\n' "$out" | sed 's/^/     /')"; return; }
    printf '%s' "$out" | grep -q '실물 대조 미실행(참조자료 미장착)' \
      || { red "$label — 면제인데 무엇을 재지 않았는지를 적지 않았다:
$(printf '%s\n' "$out" | sed 's/^/     /')"; return; }
  fi
  echo "  ✓ $label ($want)"
}

# ⓐ 커밋된 등재표를 손으로 고친 자리 — 생성물 손수정이 통과하면 등재표는 원본이 아니다.
expect red    "ⓐ 등재표 손수정(expect_bytes 한 칸)" hand_edit
# ⓑ md 에서 행 하나 삭제 — 총계 28 은 md 에서 세고 플래그로 낮출 수 없다.
expect red    "ⓑ md 데이터셋 한 행 삭제(표＋블록)" row_removed
# ⓒ 참조자료도 면제도 선언되지 않음 — 기본값으로 green 을 만들지 않는다.
expect 미선언 "ⓒ COLAB_REF_ROOT·_NO_FILES 둘 다 미선언" undeclared
# ⓓ 명시 면제 — 넘어가되 면제·미실행 사실을 요약에 드러낸다.
expect green  "ⓓ 면제 선언(면제·미실행 노출)" exempt

# 픽스처 원본을 건드리지 않았는가 — 판정은 사본에서만 난다.
if ! diff -rq "$FX/green/md" "$MD_OK" >/dev/null 2>&1; then
  red "픽스처 원본과 사본이 갈렸다 — 셀프테스트가 gates/fixtures/ 를 고쳤을 수 있다."
fi

if [ "$FAILED" -ne 0 ] || [ "${#FAILURES[@]}" -ne 0 ]; then
  echo "::error::seed-plan-drift-selftest red — 위 케이스가 기대와 다르다."
  [ "${#FAILURES[@]}" -eq 0 ] || printf '  - %s\n' "${FAILURES[@]}"
  exit 1
fi
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict seed-plan-drift-selftest
echo "seed-plan-drift-selftest green — 검사 4건 전건 기대대로 (green 1 · red(판정) 2 · red(준비·입력미선언) 1 · 참조자료 읽기 0회)."
