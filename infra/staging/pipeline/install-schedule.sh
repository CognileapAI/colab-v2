#!/usr/bin/env bash
# 배포 파이프라인 스케줄 설치/해제. 경로를 문서에 박지 않고 실행 시점에 결정한다.
#   install-schedule.sh install   현재 crontab 에 CoLAB 배포 블록을 병합
#   install-schedule.sh show      현재 걸린 블록 출력 + 설치될 내용
#   install-schedule.sh remove    블록 제거
#
# 백업 블록(`backup/install-schedule.sh`)과 **다른 표식**을 쓴다 — 한쪽을 지울 때
# 다른 쪽이 같이 지워지면 「걸어 뒀다」가 거짓이 된다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BEGIN="# >>> colab-v2-staging-deploy >>>"
END="# <<< colab-v2-staging-deploy <<<"
LOG="${COLAB_PIPELINE_STATE_DIR:-$HOME/colab-v2-releases}/pipeline.log"
CMD="${1:-show}"

block() {
  echo "$BEGIN"
  sed 's/^/# /; s/^# #/#/' "$HERE/schedule.crontab"
  echo "MAILTO=\"\""
  echo "*/5 * * * * \"$HERE/watch.sh\" >> \"$LOG\" 2>&1"
  echo "$END"
}
current() { crontab -l 2>/dev/null | sed "/$BEGIN/,/$END/d"; }

case "$CMD" in
  show)    crontab -l 2>/dev/null | sed -n "/$BEGIN/,/$END/p"; echo "(설치될 내용)"; block ;;
  install) mkdir -p "$(dirname "$LOG")"; { current; block; } | crontab - && echo "설치됨. 로그: $LOG" ;;
  remove)  current | crontab - && echo "제거됨" ;;
  *)       echo "사용: install-schedule.sh [show|install|remove]" >&2; exit 2 ;;
esac
