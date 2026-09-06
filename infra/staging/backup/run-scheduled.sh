#!/usr/bin/env bash
# 크론에서 부르는 실행 껍데기 — **실패를 눈에 보이게 만드는 것**이 유일한 목적이다.
#
# 로그 파일만 남기면 아무도 보지 않는다. 그것이 8주 침묵의 절반이었다(DEPLOY-CURRENT §9).
# 그래서 여기서는 세 가지를 남긴다:
#   ① 로그 한 줄 (성공/실패 · 종료코드)
#   ② 실패 표식 파일 `BACKUP-FAILED.txt` — 성공하면 지워진다. 있으면 지금 고장 나 있다는 뜻
#   ③ 마지막 성공 시각 `LAST-SUCCESS.txt` — 크론이 아예 안 돈 경우를 이것으로 잡는다
# ②③ 는 산출물 보관처 옆에 둔다. 주간 latest-check 가 신선도(C6)로 같은 사실을 한 번 더 묻는다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
load_config
STATE="$(dirname "$COLAB_BACKUP_DIR")"
mkdir -p "$STATE"
NAME="$(basename "${1:?실행할 스크립트}")"; shift || true
"$HERE/$NAME" "$@"; RC=$?
TS="$(date +%Y-%m-%dT%H:%M:%S%z)"
if [ "$RC" -eq 0 ]; then
  echo "$TS $NAME OK" >> "$STATE/LAST-SUCCESS.txt"
  rm -f "$STATE/BACKUP-FAILED.txt"
  log "$NAME 성공"
else
  { echo "$TS $NAME 실패 (exit $RC)"
    echo "로그: staging-backup.log 를 보라. 이 파일은 다음 성공에서만 사라진다."; } > "$STATE/BACKUP-FAILED.txt"
  log "!!! $NAME 실패 (exit $RC) — 표식 파일 BACKUP-FAILED.txt 생성"
fi
exit $RC
