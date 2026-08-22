#!/usr/bin/env bash
# event-breaking 게이트 (WU-D2b) — 이벤트 계약의 파괴적 변경을 검출한다.
#
# contract-breaking(oasdiff)과 **같은 자세**다: 기준 = git HEAD 판의 contracts/events,
#   대상 = 워킹트리 판. 별도의 frozen 사본을 레포에 두면 그 사본이 새 드리프트 면이 된다.
#   CI 에서 PR 을 볼 때는 COLAB_BREAKING_BASE_REF=origin/main 으로 기준을 옮긴다.
#
# 판정 엔진은 gates/tools/event_breaking.py (파이썬 표준 라이브러리만 — 도구 핀이 필요 없다).
# 파괴적 변경의 정의(규칙표)는 dev-package/sessions/D2b.md §2 에 적혀 있다.
# 규칙이 암묵인 게이트는 게이트가 아니다.
#
# 원칙 (CLAUDE.md §4): 기준 ref 부재·대상 0건은 red. skip 없음.
#
# 환경변수 (selftest·CI 전용)
#   COLAB_BREAKING_BASE_REF  기준 git ref (기본: HEAD) — contract-breaking 과 같은 이름을 쓴다
#   COLAB_EVENTS_BASE        기준 events 디렉터리를 직접 지정 (git 대신)
#   COLAB_EVENTS_REV         대상 events 디렉터리 (기본: 워킹트리 contracts/events)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_REF="${COLAB_BREAKING_BASE_REF:-HEAD}"
REV_SRC="${COLAB_EVENTS_REV:-$REPO_ROOT/contracts/events}"
ENGINE="$REPO_ROOT/gates/tools/event_breaking.py"

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" event-breaking-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT

red() { echo "::error::event-breaking red — $*"; exit 1; }

[ -f "$ENGINE" ] || red "판정 엔진이 없다: gates/tools/event_breaking.py"

mkdir -p "$TMP/base" "$TMP/rev"
if [ -n "${COLAB_EVENTS_BASE:-}" ]; then
  cp -a "$COLAB_EVENTS_BASE/." "$TMP/base/" 2>/dev/null || red "기준 events 를 복사하지 못했다"
else
  git -C "$REPO_ROOT" rev-parse --verify -q "$BASE_REF" >/dev/null \
    || red "기준 ref 를 찾을 수 없다: $BASE_REF"
  if git -C "$REPO_ROOT" rev-parse -q --verify "$BASE_REF:contracts/events" >/dev/null 2>&1; then
    git -C "$REPO_ROOT" archive "$BASE_REF" contracts/events | tar -x -C "$TMP" \
      || red "기준 판을 꺼내지 못했다 (git archive 실패)"
    cp -a "$TMP/contracts/events/." "$TMP/base/"
  fi
fi
cp -a "$REV_SRC/." "$TMP/rev/" 2>/dev/null || red "대상 events 를 복사하지 못했다: $REV_SRC"

count() { find "$1" -maxdepth 1 -type f -name '*.json' 2>/dev/null | wc -l; }
N_BASE="$(count "$TMP/base")"; N_REV="$(count "$TMP/rev")"

if [ "$N_REV" -eq 0 ]; then
  red "워킹트리 이벤트 계약이 0건이다 ($REV_SRC).
   비교 대상이 없는 파괴적-변경 게이트를 green 으로 세는 것이 곧 green-by-skip 이다."
fi
if [ "$N_BASE" -eq 0 ]; then
  echo "기준($BASE_REF)에 이벤트 계약이 0건 — 최초 동결이다. 파괴할 이전 계약이 없으므로 green."
  echo "event-breaking green — 신규 이벤트 계약 ${N_REV}건."
  exit 0
fi

echo "# 기준 $BASE_REF (${N_BASE}건) ↔ 대상 (${N_REV}건)"
python3 "$ENGINE" "$TMP/base" "$TMP/rev"
rc=$?
if [ $rc -eq 2 ]; then red "판정 엔진 호출 오류."; fi
if [ $rc -ne 0 ]; then
  red "기준($BASE_REF) 대비 이벤트 계약에 파괴적 변경이 있다.
   계약을 깨야 한다면 우회하지 말고 멈추고 보고한다 (CLAUDE.md §4 '경계를 넘어야 할 때').
   하위호환으로 낼 수 있는 길은 셋이다 — ① 선택 필드로 추가 ② 새 EventType 추가
   ③ schemaVersion 주 버전을 올리고 소비자가 두 버전을 동시에 받는 기간을 둔다."
fi
echo "event-breaking green — 기준 $BASE_REF (${N_BASE}건) 대비 파괴적 변경 없음."
