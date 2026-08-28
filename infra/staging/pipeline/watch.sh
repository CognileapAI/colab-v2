#!/usr/bin/env bash
# 크론에서 부르는 실행 껍데기 — **실패를 눈에 보이게 만드는 것**이 유일한 목적이다.
#
# `backup/run-scheduled.sh` 와 **같은 모양**이다(`〈168〉-㉱` — `IS3 §10` 표식 3종과 모양을 맞춘다).
# 로그 파일만 남기면 아무도 보지 않는다. 그래서 세 가지를 남긴다:
#   ① 누적 로그 한 줄 (성공/실패 · 종료코드)          → pipeline.log
#   ② 실패 표식 `DEPLOY-FAILED.txt` — **다음 성공에서만** 사라진다
#   ③ 마지막 성공 `LAST-SUCCESS.txt` — **파이프라인이 아예 안 돈 경우**를 이것으로 잡는다
# ③ 이 있어야 「크론 부동작」이 잡힌다. `IS3` 가 크론 부동작을 그것으로 잡았다.
#
# ⚠ **한계를 적어 둔다**(`I3 §7-6`). 표식·로그는 「가서 봐야 보이는」 자리다. push 알림 채널은
#   `I4` 로 이관됐다(`〈168〉-㉮`). 자동 배포가 조용히 실패하면 **다음에 누가 볼 때까지 침묵**한다.
#   사람이 부르던 때는 부른 사람이 결과를 봤다 — 자동 트리거가 그 사람을 지웠다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib.sh"
state_init
LOG="$(pipeline_state_dir)/pipeline.log"

"$HERE/run-pipeline.sh" --target staging "$@" >> "$LOG" 2>&1
RC=$?
TS="$(date +%Y-%m-%dT%H:%M:%S%z)"
case "$RC" in
  0)  echo "$TS run-pipeline OK" >> "$(success_path)"
      rm -f "$(failmark_path)"
      echo "$TS run-pipeline OK" >> "$LOG" ;;
  # 75 = EX_TEMPFAIL. 겹쳐 돌지 않으려 양보한 것 · fetch 실패. **고장이 아니다** —
  # 표식을 만들지 않는다. 다만 `LAST-SUCCESS` 를 갱신하지도 않으므로 침묵이 길어지면 ③ 이 잡는다.
  75) echo "$TS run-pipeline 이번 회차 건너뜀 (exit 75 — 겹침 또는 fetch 실패)" >> "$LOG" ;;
  *)  mark_failed "파이프라인" "run-pipeline.sh exit $RC"
      echo "$TS !!! run-pipeline 실패 (exit $RC)" >> "$LOG" ;;
esac
exit $RC
