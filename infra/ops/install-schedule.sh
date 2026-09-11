#!/usr/bin/env bash
# dev EC2의 5분 운영 알람 cron을 설치·검증·제거한다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON="${COLAB_OPS_CRON_FILE:-/etc/cron.d/colab-ops}"
DEV_CRON="${COLAB_OPS_DEV_CRON_FILE:-/etc/cron.d/colab-dev}"
STATE="${COLAB_OPS_STATE_DIR:-/opt/colab-v2/ops-alerts}"
ENVNAME=""; WEBHOOK=""; CMD=""
READINESS=78

usage() { echo "사용: install-schedule.sh --env dev --webhook-file <0600 파일> [show|install|verify|remove]" >&2; exit 2; }
while [ $# -gt 0 ]; do
  case "$1" in
    --env) ENVNAME="${2:-}"; shift 2 ;;
    --webhook-file) WEBHOOK="${2:-}"; shift 2 ;;
    show|install|verify|remove) [ -z "$CMD" ] || usage; CMD="$1"; shift ;;
    *) usage ;;
  esac
done
[ "$ENVNAME" = dev ] && [ -n "$WEBHOOK" ] && [ -n "$CMD" ] || usage

valid_path() { [[ "$1" = /* && "$1" != *%* && "$1" != *$'\n'* && "$1" != *$'\r'* ]]; }
valid_path "$WEBHOOK" || { echo "::gate-readiness-failure::gate=ops-alarm-schedule|invalid=webhook-path" >&2; exit "$READINESS"; }
DISPATCH="${COLAB_OPS_DISPATCHER:-/opt/colab-ops/bin/dispatch-current.sh}"
valid_path "$DISPATCH" || { echo "::gate-readiness-failure::gate=ops-alarm-schedule|invalid=dispatcher-path" >&2; exit "$READINESS"; }
shell_quote() { local value="${1//\'/\'\\\'\'}"; printf "'%s'" "$value"; }
RUN_Q="$(shell_quote "$DISPATCH")"
WEBHOOK_Q="$(shell_quote "$WEBHOOK")"

expected() {
  cat <<EOF
# >>> colab-v2-dev-ops-alerts >>>
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
*/5 * * * * root $RUN_Q --env dev --target deploy-verification --webhook-file $WEBHOOK_Q
*/5 * * * * root $RUN_Q --env dev --target service-health --webhook-file $WEBHOOK_Q
*/5 * * * * root $RUN_Q --env dev --target backup-freshness --webhook-file $WEBHOOK_Q
# <<< colab-v2-dev-ops-alerts <<<
EOF
}

check_webhook() {
  [ -f "$WEBHOOK" ] && [ "$(stat -c %a "$WEBHOOK" 2>/dev/null)" = 600 ] || {
    echo "::gate-readiness-failure::gate=ops-alarm-schedule|missing=0600-webhook-file" >&2; return "$READINESS"; }
  "$HERE/alarm_runner.py" --check-webhook "$WEBHOOK" || return "$READINESS"
  if [ "$CRON" = /etc/cron.d/colab-ops ] && [ "$(stat -c %u "$WEBHOOK" 2>/dev/null)" != 0 ]; then
    echo "::gate-readiness-failure::gate=ops-alarm-schedule|missing=root-owned-webhook-file" >&2; return "$READINESS"
  fi
}

snapshot() {
  mkdir -p "$STATE" || return 1
  chmod 0700 "$STATE" 2>/dev/null || return 1
  local snap="$STATE/colab-ops.pre-$(date +%Y%m%dT%H%M%S%N).bak"
  if [ -e "$CRON" ]; then cp -p "$CRON" "$snap"; else : > "$snap"; chmod 0600 "$snap"; fi
  printf '%s\n' "$snap"
}

dev_hash() { [ -e "$DEV_CRON" ] && sha256sum "$DEV_CRON" | cut -d' ' -f1 || printf 'absent'; }
verify() {
  [ -f "$CRON" ] || { echo "ops 알람 cron RED — $CRON 부재" >&2; return 1; }
  local want got
  want="$(expected)"; got="$(cat "$CRON")"
  [ "$got" = "$want" ] || { echo "ops 알람 cron RED — 기존 파일이 생성기와 다르다(내용은 출력하지 않는다)" >&2; return 1; }
  if [ "$CRON" = /etc/cron.d/colab-ops ]; then
    [ "$(stat -c %a "$CRON")" = 644 ] && [ "$(stat -c %u "$CRON")" = 0 ] || {
      echo "ops 알람 cron RED — root:0644가 아니다" >&2; return 1; }
  fi
  echo "ops 알람 cron GREEN — 5분 3대상 · 전용 파일 · webhook 경로만 전달"
}

verify_source() {
  [ "$CRON" != /etc/cron.d/colab-ops ] && return 0
  "$DISPATCH" --check
}

case "$CMD" in
  show)
    [ -e "$CRON" ] && { echo "(현재 설치 상태)"; verify || exit $?; } || echo "(현재 미설치)"
    echo "(설치 예정: 5분 3대상, webhook 내용 비출력)" ;;
  verify) check_webhook || exit $?; verify_source || exit $?; verify ;;
  install)
    check_webhook || exit $?
    verify_source || exit $?
    [ "$CRON" != /etc/cron.d/colab-ops ] || [ "$(id -u)" -eq 0 ] || {
      echo "::gate-readiness-failure::gate=ops-alarm-schedule|missing=root" >&2; exit "$READINESS"; }
    if [ -e "$CRON" ]; then
      verify || { echo "설치 중단 — 오염되거나 중복된 기존 ops cron을 덮어쓰지 않는다" >&2; exit 1; }
      echo "이미 정확히 설치됨"; exit 0
    fi
    BEFORE_DEV="$(dev_hash)"; SNAP="$(snapshot)" || exit 1
    mkdir -p "$(dirname "$CRON")"
    TMP="$(mktemp "$(dirname "$CRON")/.colab-ops.XXXXXX")" || exit 1
    expected > "$TMP"; chmod 0644 "$TMP"
    mv "$TMP" "$CRON" || { rm -f "$TMP"; exit 1; }
    [ "$(dev_hash)" = "$BEFORE_DEV" ] || { echo "기존 $DEV_CRON 이 바뀌었다 — RED" >&2; exit 1; }
    verify || { echo "되돌림 snapshot: $SNAP" >&2; exit 1; }
    echo "설치 전 snapshot: $SNAP" ;;
  remove)
    [ "$CRON" != /etc/cron.d/colab-ops ] || [ "$(id -u)" -eq 0 ] || {
      echo "::gate-readiness-failure::gate=ops-alarm-schedule|missing=root" >&2; exit "$READINESS"; }
    [ -e "$CRON" ] || { echo "ops 알람 cron은 이미 없다"; exit 0; }
    check_webhook || exit $?; verify || { echo "제거 중단 — 오염된 파일은 자동 제거하지 않는다" >&2; exit 1; }
    BEFORE_DEV="$(dev_hash)"; SNAP="$(snapshot)" || exit 1
    rm -f "$CRON" || exit 1
    [ ! -e "$CRON" ] && [ "$(dev_hash)" = "$BEFORE_DEV" ] || { echo "제거 검증 RED" >&2; exit 1; }
    echo "제거됨 · 복구 snapshot: $SNAP" ;;
esac
