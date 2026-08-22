#!/usr/bin/env bash
# 스케줄 설치/해제. 경로를 문서에 박지 않고 실행 시점에 결정한다.
#   install-schedule.sh install   현재 crontab 에 CoLAB 블록을 병합
#   install-schedule.sh show      현재 걸린 블록 출력
#   install-schedule.sh remove    블록 제거
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BEGIN="# >>> colab-v2-staging-backup >>>"
END="# <<< colab-v2-staging-backup <<<"
LOG="$HOME/colab-v2-backups/staging-backup.log"
CMD="${1:-show}"

block() {
  echo "$BEGIN"
  cat "$HERE/schedule.crontab" | sed 's/^/# /' | sed 's/^# #/#/'
  echo "MAILTO=\"\""
  echo "30 3 * * * \"$HERE/run-scheduled.sh\" backup.sh >> \"$LOG\" 2>&1"
  echo "10 4 * * 1 \"$HERE/run-scheduled.sh\" latest-check.sh >> \"$LOG\" 2>&1"
  echo "$END"
}
current() { crontab -l 2>/dev/null | sed "/$BEGIN/,/$END/d"; }

case "$CMD" in
  show)    crontab -l 2>/dev/null | sed -n "/$BEGIN/,/$END/p"; echo "(설치될 내용)"; block ;;
  install) mkdir -p "$(dirname "$LOG")"; { current; block; } | crontab - && echo "설치됨. 로그: 홈 아래 colab-v2-backups/staging-backup.log" ;;
  remove)  current | crontab - && echo "제거됨" ;;
  *)       echo "사용: install-schedule.sh [show|install|remove]" >&2; exit 2 ;;
esac
