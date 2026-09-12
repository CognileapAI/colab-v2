#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNNER="${COLAB_NOTIFICATION_RUNTIME_RUNNER:-$HERE/run-runtime-job.sh}"
CRON="${COLAB_NOTIFICATION_CRON_FILE:-/etc/cron.d/colab-operator-notifications}"
ENVIRONMENT=""; CONFIG=""; ACTION=""
usage() { echo '사용: install-runtime-cron.sh --environment dev|staging --config <0600 env> render|install|verify|remove' >&2; exit 2; }
while [ "$#" -gt 0 ]; do
  case "$1" in
    --environment) ENVIRONMENT="${2:-}"; shift 2 ;;
    --config) CONFIG="${2:-}"; shift 2 ;;
    render|install|verify|remove) [ -z "$ACTION" ] || usage; ACTION="$1"; shift ;;
    *) usage ;;
  esac
done
case "$ENVIRONMENT" in dev|staging) ;; *) usage ;; esac
[ -n "$CONFIG" ] && [ -n "$ACTION" ] || usage
case "$CONFIG:$CRON:$RUNNER" in /*:/*:/*) ;; *) echo 'cron 준비 실패 — 절대경로가 필요하다' >&2; exit 78 ;; esac
[[ "$CONFIG$CRON$RUNNER" != *%* && "$CONFIG$CRON$RUNNER" != *$'\n'* && "$CONFIG$CRON$RUNNER" != *$'\r'* ]] \
  || { echo 'cron 준비 실패 — 안전하지 않은 경로' >&2; exit 78; }

quote() { local value="${1//\'/\'\\\'\'}"; printf "'%s'" "$value"; }
RUN_Q="$(quote "$RUNNER")"; CONFIG_Q="$(quote "$CONFIG")"
expected() {
  printf '%s\n' '# CoLAB operator notifications — generated; cron timezone is UTC.' 'SHELL=/bin/bash' 'PATH=/usr/local/bin:/usr/bin:/bin' ''
  if [ "$ENVIRONMENT" = dev ]; then
    printf '* * * * * root %s --config %s export\n' "$RUN_Q" "$CONFIG_Q"
    printf '* * * * * root %s --config %s spool\n' "$RUN_Q" "$CONFIG_Q"
    printf '* * * * * root %s --config %s retry\n' "$RUN_Q" "$CONFIG_Q"
    for target in service-health backup-freshness deploy-verification; do
      printf '*/5 * * * * root %s --config %s probe-%s\n' "$RUN_Q" "$CONFIG_Q" "$target"
    done
    printf '*/5 * * * * root %s --config %s daily\n' "$RUN_Q" "$CONFIG_Q"
  else
    printf '* * * * * root %s --config %s stage-relay\n' "$RUN_Q" "$CONFIG_Q"
    for target in service-health backup-freshness deploy-verification; do
      printf '*/5 * * * * root %s --config %s probe-%s\n' "$RUN_Q" "$CONFIG_Q" "$target"
    done
  fi
}
verify() {
  [ -f "$CRON" ] || { echo 'operator cron RED — 파일 부재' >&2; return 1; }
  [ "$(cat "$CRON")" = "$(expected)" ] || { echo 'operator cron RED — 생성 내용과 다름' >&2; return 1; }
  if [ "$CRON" = /etc/cron.d/colab-operator-notifications ]; then
    [ "$(stat -c %u:%a "$CRON")" = 0:644 ] || { echo 'operator cron RED — root:0644가 아님' >&2; return 1; }
  fi
  echo "operator cron GREEN — $ENVIRONMENT 일정 일치"
}

case "$ACTION" in
  render) expected ;;
  verify) "$RUNNER" --config "$CONFIG" check >/dev/null; verify ;;
  install)
    "$RUNNER" --config "$CONFIG" check >/dev/null
    if [ -e "$CRON" ]; then
      verify >/dev/null || { echo '설치 중단 — 기존 cron이 생성 내용과 다름' >&2; exit 1; }
      echo '이미 정확히 설치됨'; exit 0
    fi
    [ "$CRON" != /etc/cron.d/colab-operator-notifications ] || [ "$(id -u)" -eq 0 ] \
      || { echo 'cron 준비 실패 — root 필요' >&2; exit 78; }
    mkdir -p "$(dirname "$CRON")"
    TMP="$(mktemp "$(dirname "$CRON")/.colab-operator.XXXXXX")"
    trap 'rm -f "$TMP"' EXIT
    expected > "$TMP"; chmod 0644 "$TMP"; mv "$TMP" "$CRON"; trap - EXIT
    verify ;;
  remove)
    [ -e "$CRON" ] || { echo 'operator cron은 이미 없음'; exit 0; }
    verify >/dev/null || { echo '제거 중단 — 기존 cron이 생성 내용과 다름' >&2; exit 1; }
    rm -f "$CRON"; echo 'operator cron 제거됨' ;;
esac
