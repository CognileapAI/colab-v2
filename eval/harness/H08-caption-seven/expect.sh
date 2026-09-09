#!/usr/bin/env bash
# H08: fixture에서 리터럴 선언을 도출하고 최종 응답 필드를 완전 일치 검사한다.
set -uo pipefail
TASK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" || exit 78
command -v python3 >/dev/null 2>&1 || { echo 'expect preparation — python3 missing' >&2; exit 78; }
[ -r "$TASK_DIR/judge.py" ] || { echo 'expect preparation — judge.py missing' >&2; exit 78; }
python3 "$TASK_DIR/judge.py"
RC=$?
case "$RC" in
  0|1|78) exit "$RC" ;;
  *) echo "expect preparation — judge execution failed (exit $RC)" >&2; exit 78 ;;
esac
