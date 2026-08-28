#!/usr/bin/env bash
# 타깃 판정 — 「어디에 배포하는가」를 묻고, **staging 이 아니면 거부한다.**
#
#   target.sh check <타깃>     0=진행해도 좋다 · 그 외=거부(사유를 표준에러에)
#   target.sh list             선언된 타깃 목록
#
# ── 왜 이것이 있는가 (`I3` 결정 6 · `㊵` · `㊻`) ─────────────────────────────
# 정본은 「prod 는 승인 게이트」라고만 적었고 `㊻` 이 **prod 착수 시점 자체를 닫아** 뒀다.
# 그래서 타깃 개념은 **선언하되 건너편을 비워 둔다** — `prod` 를 부르면 `㊻` 을 인용하며
# **즉시 거부**한다. **조용한 no-op 을 만들지 않는다**: 아무 일도 안 하고 0 을 반환하는 것이
# 이 레포가 배포에서 겪은 실패 그 자체다(`I3 §0` — 「모른다」를 「성공」으로 바꿔 말하는 것).
#
# ⚠ 증명되는 것은 **「승인 없이는 넘어가지 않는다」의 음성뿐**이다. 「승인하면 넘어간다」의
#   양성은 건너편이 비어 있어 증명되지 않는다(`I3 §7-9`). 그 사실을 지우지 않는다.
set -uo pipefail

# 선언된 타깃. **실행 경로가 있는 것은 staging 하나다.**
DECLARED_TARGETS=(staging prod)
RUNNABLE_TARGETS=(staging)

usage() { echo "사용: target.sh {check <타깃>|list}" >&2; exit 2; }

case "${1:-}" in
  list)
    for t in "${DECLARED_TARGETS[@]}"; do
      case " ${RUNNABLE_TARGETS[*]} " in
        *" $t "*) echo "$t	실행 가능" ;;
        *)        echo "$t	선언만 — 실행 경로 없음 (㊻ 으로 닫혀 있다)" ;;
      esac
    done
    ;;
  check)
    T="${2:-}"
    # ⭑ 세 상태다. 값이 있으면 판정한다 / 선언됐으나 실행 경로가 없으면 사유를 밝히고 거부한다 /
    #   **아무 말도 없으면 실패한다.** 기본값 `staging` 으로 떨어뜨리지 않는다 —
    #   기본값이 관대한 쪽으로 떨어지는 것이 `CLAUDE.md §4` 가 막는 모양이다.
    if [ -z "$T" ]; then
      echo "거부: 타깃이 지정되지 않았다. 기본값으로 떨어지지 않는다 — 어디에 배포하는지 모르는 배포는 없다." >&2
      exit 64
    fi
    case " ${DECLARED_TARGETS[*]} " in
      *" $T "*) ;;
      *) echo "거부: 알 수 없는 타깃 '$T'. 선언된 타깃 = ${DECLARED_TARGETS[*]}" >&2; exit 64 ;;
    esac
    case " ${RUNNABLE_TARGETS[*]} " in
      *" $T "*) exit 0 ;;
    esac
    echo "거부: 타깃 '$T' 에는 실행 경로가 없다." >&2
    echo "  근거 = PLAN-SoT §9 ㊻ — AWS·prod 는 보류다. v2 완주 판정은 staging 배포 green 까지." >&2
    echo "  그리고 ㊵ — 승격은 Ted 가 staging 에서 직접 보고 승인한 뒤에만 넘어간다." >&2
    echo "  이 자리는 비어 있다는 것이 상태다. 나중에 열릴 때 타깃 하나를 추가하는 일이어야 한다." >&2
    exit 77   # EX_NOPERM
    ;;
  *) usage ;;
esac
