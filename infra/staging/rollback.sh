#!/usr/bin/env bash
# staging 롤백 — **되돌릴 대상이 두 종류라는 사실을 명령에 드러낸다.**
#
#   rollback.sh --to-last-green      직전 **green 릴리스**로 (기본이 되어야 할 것)
#   rollback.sh --to-tag <태그>      지정한 릴리스 태그로
#   rollback.sh --to-placeholder     **제품 이전**(compose.yml 자리표시 오리진)으로
#
# ── 종전 구현이 무엇을 잘못했는가 (`I3 §2-3` DR-5 하류) ──────────────────────
# 종전 `rollback.sh` 는 `compose.yml` 로 `up -d` 했다. `compose.yml` 은 **I2 이전 자리표시
# 오리진**이다. 즉 「직전 릴리스로 되돌린다」가 아니라 **「제품 이전 상태로 되돌린다」**였다.
# I2 시점에는 그게 정확히 직전 상태였으므로 옳았다. 그러나 릴리스가 둘 이상 쌓이는 순간
# 이 스크립트는 **N-1 이 아니라 0 으로 간다.** 원인은 하나였다 — 어디에도 「직전에 green 이었던
# 릴리스가 무엇인가」를 적어 두는 자리가 없었다. 이제 릴리스 원장이 그 자리다.
#
# ── 되돌리지 않는 것 ────────────────────────────────────────────────────────
# **스키마는 되돌리지 않는다** (`〈168〉-㉲` forward-only). 되돌리는 마이그레이션은 데이터를
# 지울 수 있고, 그러면 그것은 롤백이 아니라 재해다. **pgdata 볼륨도 건드리지 않는다.**
# 되돌리는 것은 **서빙 상태**지 데이터가 아니다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/pipeline/lib.sh"
ENV_FILE="${COLAB_STAGING_ENV:-$HOME/.colab-v2-staging.env}"

MODE=""; WANT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --to-last-green)  MODE=lastgreen; shift ;;
    --to-tag)         MODE=tag; WANT="${2:-}"; shift 2 ;;
    --to-placeholder) MODE=placeholder; shift ;;
    *) echo "알 수 없는 인자: $1" >&2; exit 2 ;;
  esac
done

# ⭑ 세 상태다 — 대상이 지정되면 되돌린다 / 지정된 대상이 없으면 사유를 밝히고 실패한다 /
#   **아무 말도 없으면 실패한다.** 종전처럼 자리표시로 조용히 떨어지지 않는다.
#   「어느 쪽으로 가는지 안 밝힌 롤백」이 정확히 DR-5 가 만든 상태다.
if [ -z "$MODE" ]; then
  cat >&2 <<'EOF'
거부: 되돌릴 대상을 지정하지 않았다. 롤백 대상은 **두 종류**이고 기본값을 두지 않는다.
  --to-last-green      직전 green 릴리스로 (릴리스 원장에서 읽는다)
  --to-tag <태그>      지정 릴리스로
  --to-placeholder     제품 이전(자리표시 오리진)으로 — 이것은 N-1 이 아니라 0 이다
EOF
  exit 64
fi

state_init
[ -f "$ENV_FILE" ] || die "설정 파일이 없다: \$COLAB_STAGING_ENV"

if [ "$MODE" = placeholder ]; then
  log "자리표시 오리진(compose.yml)으로 되돌린다 — **이것은 직전 릴리스가 아니라 제품 이전이다**"
  docker compose -f "$HERE/compose.yml" --env-file "$ENV_FILE" up -d --remove-orphans || die "자리표시 기동 실패"
  docker compose -f "$HERE/compose.yml" --env-file "$ENV_FILE" ps
  ledger_append rollback "-" "placeholder" green "자리표시 오리진으로 되돌림(N-1 아님)"
  exit 0
fi

CUR="$(docker inspect -f '{{index .Config.Image}}' colab_v2_staging_core_api 2>/dev/null || true)"
CUR="${CUR##*:}"

if [ "$MODE" = lastgreen ]; then
  TAG="$(ledger_rollback_target "$CUR")" || {
    log "되돌릴 대상이 없다 — 원장에 green 릴리스가 없거나, 있어도 **이미지 실물이 남아 있지 않다.**"
    log "이미지 보존은 최근 3개다(〈168〉-㉰). 원장 한 줄이 곧 롤백 가능을 뜻하지 않는다."
    log "제품 이전으로 가려면 --to-placeholder 를 **명시**하라. 조용히 그리로 가지 않는다."
    exit 69
  }
else
  TAG="$WANT"
  [ -n "$TAG" ] || die "--to-tag 에 태그가 필요하다"
  images_exist "$TAG" || die "태그 '$TAG' 의 이미지 6종이 전부 있지는 않다 — 되돌릴 대상이 없다"
fi

log "직전 green 릴리스로 되돌린다 — 태그 $TAG (현재 $CUR)"
export COLAB_RELEASE_TAG="$TAG"
docker compose -f "$HERE/compose.i2.yml" --env-file "$ENV_FILE" up -d --remove-orphans || {
  ledger_append rollback "-" "$TAG" red "up -d 실패"; die "롤백 기동 실패"; }

# 롤백도 **자기 결과를 묻는다.** 되돌렸다는 주장과 되돌아갔다는 사실은 다르다.
log "롤백 판정 — 헬스 6종 + 본문 대조"
VOK=0
for _ in $(seq 1 "${COLAB_VERIFY_TRIES:-30}"); do
  if "$HERE/verify/verify-deploy.sh" >/dev/null 2>&1; then VOK=1; break; fi
  sleep 5
done
"$HERE/verify/verify-deploy.sh" || true
if [ "$VOK" -ne 1 ]; then
  ledger_append rollback "-" "$TAG" red "롤백 후 판정 red"
  mark_failed "롤백 판정" "태그 $TAG 로 되돌렸으나 헬스 6종이 green 이 아니다"
  exit 70
fi
ledger_append rollback "-" "$TAG" green "직전 green 릴리스로 되돌림 (직전 배포=$CUR)"
echo "롤백 GREEN — 태그 $TAG"
tail -n 1 "$(ledger_path)"
