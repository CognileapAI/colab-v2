#!/usr/bin/env bash
# 파이프라인 1회 — **커밋 → 빌드 → 게이트 → 백업 → 마이그레이션 → 교체 → 검증.**
#
#   run-pipeline.sh [--target staging] [--force]
#
# ── 트리거는 왜 폴링인가 (`I3` 결정 1 · `〈168〉-㉯`) ──────────────────────────
# 이 호스트는 인바운드가 터널 한 줄뿐이고(`IS2` — ingress 는 `www→nginx:80` + catch-all 404
# 둘뿐이다) 클라우드 CI 는 여기에 닿을 수 없다. 그래서 **호스트가 당겨 온다.**
#   · 인바운드를 0 으로 유지한다 — `IS2` 가 만든 상태를 깨지 않는다
#   · 자격증명이 **읽기 전용 git fetch** 하나로 끝난다
#   · 호스트가 꺼져 있으면 안 도는 성질이 **정직하다** (`RESTART.md` 가 이미 그 전제 위에 있다)
# 클라우드 CI(`ci.yml`)는 게이트·빌드 검증을 계속 맡고 **배포 권한은 갖지 않는다.**
# 기구는 `cron` · 주기 5분 — `IS3 §10` 의 크론이 이 호스트에서 이미 검증된 채 돌고 있다.
#
# ⚠ **호스트가 꺼져 있는 동안의 자동 배포는 증명되지 않는다**(`I3 §7-1`). 도커 데몬이 자동
#   기동하지 않는다. 「커밋 → 자동 배포」는 **호스트가 켜져 있다는 조건 아래에서만** 참이다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGING="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$STAGING/../.." && pwd)"
. "$HERE/lib.sh"

TARGET=""; FORCE=0
while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --force)  FORCE=1; shift ;;   # 새 커밋이 없어도 한 바퀴 돈다(사람이 부를 때)
    *) echo "알 수 없는 인자: $1" >&2; exit 2 ;;
  esac
done

"$HERE/approval/target.sh" check "$TARGET" || exit $?
pipeline_lock
state_init
LOG="$(pipeline_state_dir)/pipeline.log"

BRANCH="${COLAB_PIPELINE_BRANCH:-main}"

# ── ① 당겨 온다 ────────────────────────────────────────────────────────────
log "① git fetch (읽기 전용) — origin/$BRANCH"
git -C "$REPO" fetch --quiet origin "$BRANCH" || { log "fetch 실패 — 이번 회차는 돌지 않는다"; exit 75; }
LOCAL="$(git -C "$REPO" rev-parse HEAD)"
REMOTE="$(git -C "$REPO" rev-parse "origin/$BRANCH")"

# ⚠ **「할 일이 없었다」를 「배포에 성공했다」와 같은 코드로 말하지 않는다.**
# 종전에는 여기서 `exit 0` 이었다. 크론 껍데기(`watch.sh`)는 종료코드만 보므로 아무것도 하지
# 않은 회차를 배포 green 으로 읽었고, 그 결과 ⓐ 「크론은 도는데 배포는 안 된다」를 잡으라고 둔
# `LAST-SUCCESS.txt` 가 **5분마다 갱신되어 아무것도 못 잡게** 되고, ⓑ 「다음 성공에서만
# 사라진다」가 계약인 `DEPLOY-FAILED.txt` 가 **진짜 배포 실패 5분 뒤 조용히 지워졌다.**
# 이 레포가 이름 붙인 green-by-skip 의 가장 나쁜 모양이다(`CLAUDE.md §4`).
#   66 = EX_NOINPUT. **할 일 없음** — 고장도 아니고 성공도 아니다. 껍데기가 셋을 가른다.
if [ "$LOCAL" = "$REMOTE" ] && [ "$FORCE" -eq 0 ]; then
  log "새 커밋 없음 ($(git -C "$REPO" rev-parse --short=12 HEAD)) — 돌지 않는다"
  exit 66
fi

# ── ② 체크아웃 — **깨끗한 fast-forward 만** ────────────────────────────────
# 되돌리기·병합·강제를 하지 않는다. 트리가 더러우면 여기서 멈춘다 —
# 워킹트리를 굽는 배포가 DR-4 였고, 그 성질을 트리거 쪽에서도 한 번 더 막는다.
if [ "$LOCAL" != "$REMOTE" ]; then
  DIRTY_N="$(git -C "$REPO" status --porcelain | grep -c . || true)"
  if [ "$DIRTY_N" -ne 0 ]; then
    mark_failed "체크아웃" "워킹트리 변경 ${DIRTY_N}건 — fast-forward 할 수 없다"
    log "!!! 워킹트리가 깨끗하지 않다(${DIRTY_N}건). 사람이 정리해야 한다."
    exit 65
  fi
  log "② fast-forward → $(git -C "$REPO" rev-parse --short=12 "origin/$BRANCH")"
  git -C "$REPO" merge --ff-only "origin/$BRANCH" >/dev/null || {
    mark_failed "체크아웃" "fast-forward 불가 — 갈라진 이력"; exit 65; }
fi

# ── ③ 배포 — 판정까지 deploy.sh 안에서 끝난다 ──────────────────────────────
log "③ 배포 (타깃 $TARGET)"
"$STAGING/deploy.sh" --target "$TARGET"
RC=$?
if [ "$RC" -ne 0 ]; then
  log "!!! 파이프라인 RED (deploy.sh exit $RC) — 표식 파일을 보라: $(failmark_path)"
  exit "$RC"
fi
log "파이프라인 GREEN"
echo "원장: $(ledger_path) · 로그: $LOG"
