#!/usr/bin/env bash
# 배포 파이프라인 스케줄 설치/해제. 경로를 문서에 박지 않고 실행 시점에 결정한다.
#   install-schedule.sh install   현재 crontab 에 CoLAB 배포 블록을 병합
#   install-schedule.sh show      현재 걸린 블록 출력 + 설치될 내용
#   install-schedule.sh verify    걸려 있는지 **읽어서** 판정한다 (설치하지 않는다)
#   install-schedule.sh remove    블록 제거
#
# 백업 블록(`backup/install-schedule.sh`)과 **다른 표식**을 쓴다 — 한쪽을 지울 때
# 다른 쪽이 같이 지워지면 「걸어 뒀다」가 거짓이 된다.
#
# ── 이 파일이 조심하는 두 가지 ───────────────────────────────────────────────
# ⑴ **「설치했다」와 「걸려 있다」는 다르다.** `crontab -` 의 종료코드는 앞의 것만 안다.
#    `lib.sh` 의 별칭 재부착이 붙인 **뒤에** 이미지 ID 를 대조하는 것과 같은 이유로,
#    여기도 설치한 **뒤에** 다시 읽어서 판정한다(`verify_installed`).
# ⑵ **통째로 날아가는 모양.** `crontab -l 2>/dev/null` 은 「크론탭이 없다」와
#    「crontab 명령이 실패했다」를 **같은 빈 출력**으로 만든다. 그 빈 출력을 그대로
#    `crontab -` 에 넣으면 형제 블록(백업 스케줄)까지 사라진 채 「설치됨」이 찍힌다.
#    그래서 ⓐ 설치 전 실물을 **스냅숏 파일로 남기고** ⓑ 블록 밖 줄 수(`PRE_N`)를 세어
#    설치 후와 대조한다. 줄이 줄었으면 red 이고, 되돌릴 손잡이는 스냅숏이다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BEGIN="# >>> colab-v2-staging-deploy >>>"
END="# <<< colab-v2-staging-deploy <<<"
STATE="${COLAB_PIPELINE_STATE_DIR:-$HOME/colab-v2-releases}"
LOG="$STATE/pipeline.log"
CMD="${1:-show}"

block() {
  echo "$BEGIN"
  sed 's/^/# /; s/^# #/#/' "$HERE/schedule.crontab"
  echo "MAILTO=\"\""
  echo "*/5 * * * * \"$HERE/watch.sh\" >> \"$LOG\" 2>&1"
  echo "$END"
}
current() { crontab -l 2>/dev/null | sed "/$BEGIN/,/$END/d"; }

# 걸려 있는지 **읽어서** 판정한다. 셋을 다 본다 — 블록 표식 · 실행 줄 · 블록 밖 줄 수.
# $1 = 기대하는 블록 밖 최소 줄 수(모르면 -1 로 넘겨 그 항목을 건너뛴다. 건너뛰면 그렇게 말한다).
verify_installed() {
  local want_pre="${1:--1}" now post_n rc=0
  now="$(crontab -l 2>/dev/null)"
  if ! printf '%s\n' "$now" | grep -qF "$BEGIN"; then
    echo "  FAIL  블록 표식이 crontab 에 없다 — 설치되지 않았다" >&2; rc=1
  fi
  if ! printf '%s\n' "$now" | grep -qF "$HERE/watch.sh"; then
    echo "  FAIL  실행 줄($HERE/watch.sh)이 crontab 에 없다" >&2; rc=1
  fi
  post_n="$(printf '%s\n' "$now" | sed "/$BEGIN/,/$END/d" | grep -c . || true)"
  if [ "$want_pre" -lt 0 ]; then
    echo "  (블록 밖 줄 수 대조 건너뜀 — 설치 전 값을 모른다. 현재 ${post_n}줄)"
  elif [ "$post_n" -lt "$want_pre" ]; then
    echo "  FAIL  블록 밖 줄이 ${want_pre} → ${post_n} 로 줄었다 — 남의 항목이 사라졌다" >&2; rc=1
  else
    echo "  PASS  블록 밖 줄 보존 ${post_n}줄 (설치 전 ${want_pre}줄)"
  fi
  if [ "$rc" -ne 0 ]; then echo "스케줄 설치: RED" >&2; return 1; fi
  echo "스케줄 설치: GREEN (블록 표식 · 실행 줄 · 블록 밖 보존 3항 전부 실측)"
  return 0
}

case "$CMD" in
  show)    crontab -l 2>/dev/null | sed -n "/$BEGIN/,/$END/p"; echo "(설치될 내용)"; block ;;
  verify)  verify_installed -1 ;;
  install)
    mkdir -p "$STATE" || { echo "상태 디렉터리를 만들지 못했다: $STATE" >&2; exit 1; }
    SNAP="$STATE/crontab.pre-$(date +%Y%m%dT%H%M%S).bak"
    crontab -l > "$SNAP" 2>/dev/null
    # 설치 전 블록 밖 줄 수. 이 값이 설치 후와 대조할 잣대다.
    PRE_N="$(sed "/$BEGIN/,/$END/d" "$SNAP" 2>/dev/null | grep -c . || true)"
    echo "설치 전 스냅숏: $SNAP (블록 밖 ${PRE_N}줄) — 되돌리려면 crontab \"$SNAP\""
    { current; block; } | crontab - || { echo "crontab 갱신 실패 — 스냅숏으로 되돌려라: $SNAP" >&2; exit 1; }
    verify_installed "$PRE_N" || { echo "되돌리려면: crontab \"$SNAP\"" >&2; exit 1; }
    echo "설치됨. 로그: $LOG"
    ;;
  remove)  current | crontab - && echo "제거됨" ;;
  *)       echo "사용: install-schedule.sh [show|verify|install|remove]" >&2; exit 2 ;;
esac
