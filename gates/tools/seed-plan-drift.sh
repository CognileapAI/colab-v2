#!/usr/bin/env bash
# seed-plan-drift — 참조자료 정본 md 4건과 **커밋된 등재표**(`plan-manifest.yaml`)가 갈라졌는가.
#
# 무엇을 해소하나:
#   `dev-package/tools/dev-seed/build_plan.py` 는 **아무 게이트도 부르지 않는 생성기**였다.
#   그 생성물인 `plan-manifest.yaml` 은 커밋돼 있고 러너가 그것을 읽는다. 그래서 md 를 고치고
#   생성기를 다시 돌리지 않으면 **낡은 등재표가 그대로 통과한다** — 아무도 대조하지 않기 때문이다.
#   검사가 「사람이 기억해서 다시 돌리는 것」 안에만 있는 상태이고, 이 레포가 반복해 깨진 모양
#   (green-by-skip)의 한 갈래다(`CLAUDE.md §4` · `.claude/rules/colab-rules.md §3-3`).
#
# ── 무엇을 보나 (셋) ─────────────────────────────────────────────────────────
#   ⑴ 표 ↔ 기계 블록  md 안의 사람이 읽는 표와 생성기 입력 블록이 같은가(이름·건수·바이트).
#   ⑵ 재생성 동일성    md 만으로 등재표를 되만들어 커밋된 것과 대조한다. 한 줄이라도 다르면 red.
#   ⑶ 총계             데이터셋 28건 · 계보 18간선. **md 에서 센 값**이고 플래그로 낮출 수 없다
#                      (기본값 아닌 기대값으로 쓰려는 호출은 생성기가 종료코드 4 로 막는다).
#   ⑴⑵⑶ 은 `build_plan.py --check-manifest` **하나**가 판정한다 — 게이트가 자기 사본을
#   만들면 「게이트가 보는 것」과 「사람이 보는 것」이 갈린다(`frontend-visual` 과 같은 원칙).
#   이 대조는 **참조자료 드라이브가 없어도 돈다** — md 블록이 선언한 값만 쓰기 때문이다.
#
# ── 실물 대조의 세 상태 (선례 `gates/tools/harness-eval.sh`) ─────────────────
#   COLAB_REF_ROOT=<디렉터리>      **선언 ＋ 실재.** 글롭이 맞히는 파일 수·바이트까지 실물과
#                                 대조한다(`--dry-run`). 어긋나면 red(판정).
#   COLAB_SEED_PLAN_NO_FILES=1    참조자료가 없음을 **명시 선언**한다. ⑴⑵⑶ 만 판정하고
#                                 요약에 「면제」와 미실행 사실을 드러낸 채 green.
#   둘 다 없음                     → red(준비 · 입력미선언 · 78). 침묵은 통과가 아니다.
#   둘 다 있음                     → **실물 대조가 이긴다.** 면제를 무시했다고 출력에 적는다.
# ⚠ 값 대조는 `=1` 하나뿐이다(`harness-eval` 과 같은 규약) — 「대충 참 같으면 통과」가
#   세 상태를 두 상태로 무너뜨린다.
# ⚠ 참조자료 뿌리는 **`COLAB_REF_ROOT` 로만** 읽는다. 생성기의 기본 자리로 조용히 되돌아가면
#   「선언했다」와 「우연히 붙어 있었다」가 같은 판정이 된다.
#
# 시험 seam — `COLAB_SEED_PLAN_MD_ROOT`·`COLAB_SEED_PLAN_MANIFEST`(셀프테스트가 임시 사본을
#   가리킨다). 기본값은 레포의 정본 자리이고, 이 둘로 검사 대상을 줄이지 않는다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_readiness.sh"

GEN="$REPO_ROOT/dev-package/tools/dev-seed/build_plan.py"
MD_ROOT="${COLAB_SEED_PLAN_MD_ROOT:-$REPO_ROOT/dev-package/reports/reference-data/datasets-md}"
MANIFEST="${COLAB_SEED_PLAN_MANIFEST:-$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml}"

red() { echo "::error::seed-plan-drift red(판정) — $*"; exit 1; }
ready_red() { # $1=선언되지 않은/없는 것 $2=사유
  readiness_undeclared_input "seed-plan-drift" "$1" "$2"
  exit "$READINESS_EXIT"
}

# ── 준비 — 판정 재료가 있는가 ────────────────────────────────────────────────
command -v python3 >/dev/null 2>&1 || ready_red "python3" \
  "생성기를 돌릴 python3 가 PATH 에 없다."
python3 -c 'import yaml' >/dev/null 2>&1 || ready_red "PyYAML" \
  "생성기의 유일한 표준 라이브러리 밖 의존이다. 설치법 = pip install pyyaml 또는 서비스 venv 에서 실행."
[ -f "$GEN" ] || ready_red "${GEN#"$REPO_ROOT/"}" \
  "판정부(생성기)가 이 체크아웃에 없다."
[ -d "$MD_ROOT" ] || ready_red "${MD_ROOT#"$REPO_ROOT/"}" \
  "정본 md 4건의 뿌리가 없다. 자리를 바꾸려면 COLAB_SEED_PLAN_MD_ROOT 로 준다."

# ── ⑴⑵⑶ md → 등재표 대조 — 참조자료 없이도 돈다 ────────────────────────────
MAP_OUT="$(python3 "$GEN" --check-manifest --md-root "$MD_ROOT" --manifest-out "$MANIFEST" 2>&1)"
MAP_RC=$?
printf '%s\n' "$MAP_OUT" | sed 's/^/  /'
if [ "$MAP_RC" -ne 0 ]; then
  red "md 4건과 커밋된 등재표가 갈라졌다(생성기 종료코드 $MAP_RC · 2 총계 · 3 표↔블록 · 5 등재표 재생성 불일치).
   고치는 법 = md 를 정본으로 고친 뒤 생성기를 다시 돌려 ${MANIFEST#"$REPO_ROOT/"} 를 새로 만든다. 등재표는 생성물이라 손으로 고치지 않는다."
fi
COUNTS="$(printf '%s\n' "$MAP_OUT" | grep -m1 '^datasets ' || true)"

# ── 실물 대조 — 세 상태 ──────────────────────────────────────────────────────
REF="${COLAB_REF_ROOT:-}"
DECL_EXEMPT="${COLAB_SEED_PLAN_NO_FILES:-}"

if [ -n "$REF" ] && [ -d "$REF" ]; then
  if [ "$DECL_EXEMPT" = "1" ]; then
    echo "  seed-plan-drift — COLAB_REF_ROOT 와 COLAB_SEED_PLAN_NO_FILES=1 이 함께 선언됐다. **실물 대조가 이긴다** — 면제 선언은 무시했다."
  fi
  FILE_OUT="$(python3 "$GEN" --dry-run --md-root "$MD_ROOT" --ref-root "$REF" 2>&1)"
  FILE_RC=$?
  printf '%s\n' "$FILE_OUT" | sed 's/^/  /'
  if [ "$FILE_RC" -ne 0 ]; then
    red "md 블록이 선언한 글롭·건수·바이트가 참조자료 실물과 다르다(생성기 종료코드 $FILE_RC).
   위 MISMATCH·missing_files 행이 어긋난 데이터셋 이름이다. 참조자료는 읽기 전용이므로 md 쪽을 실물에 맞춘다."
  fi
  TOTAL="$(printf '%s\n' "$FILE_OUT" | grep -m1 '^TOTAL ' || true)"
  echo "seed-plan-drift green — ${COUNTS:-계수 미상} · 등재표 = md 재생성본과 동일 · 실물 대조 실행(${TOTAL:-TOTAL 행 없음})"
  exit 0
fi

# 여기서부터는 참조자료가 붙어 있지 않다 — 그 사실을 **요약에 그대로 적는다**.
if [ -n "$REF" ]; then
  echo "  COLAB_REF_ROOT 가 선언됐지만 디렉터리가 아니다: $REF"
fi

if [ "$DECL_EXEMPT" = "1" ]; then
  echo "seed-plan-drift green — ${COUNTS:-계수 미상} · 등재표 = md 재생성본과 동일 · 실물 대조 미실행(참조자료 미장착) · 면제 선언(COLAB_SEED_PLAN_NO_FILES=1)"
  echo "   ⚠ 면제는 「실물이 맞다」가 아니라 「이번 회차에 실물을 재지 않았다」는 선언이다."
  echo "   실제로 재려면 COLAB_REF_ROOT=<참조자료 뿌리> bash gates/run.sh seed-plan-drift."
  exit 0
fi

echo "seed-plan-drift — 실물 대조 미실행(참조자료 미장착)"
ready_red "COLAB_REF_ROOT" \
  "md 블록의 글롭이 실물 파일과 맞는지를 잴 참조자료 뿌리가 선언되지 않았다. 선언하는 법 = COLAB_REF_ROOT=<참조자료 뿌리> bash gates/run.sh seed-plan-drift · 이번 회차에 참조자료를 붙이지 않는다면 COLAB_SEED_PLAN_NO_FILES=1 로 **명시 면제**를 선언한다(md→등재표 대조는 그대로 판정한다). 값 대조는 =1 하나뿐이다."
