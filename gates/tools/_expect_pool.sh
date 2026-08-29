#!/usr/bin/env bash
# selftest 케이스 병렬 실행 풀. source 해서 쓴다.
#
# 바꾸는 것은 **실행 순서뿐**이다. 케이스 목록·기대값·판정 기준은 직렬판과 한 글자도 다르지 않고,
# 출력은 등록 순서로 되돌려 재생한다. 케이스를 줄이거나 건너뛰는 경로는 없다 (CLAUDE.md §4).
#
# 전제: 케이스끼리 독립이어야 한다 — 각자 자기 임시 픽스처, 자기 일회용 컨테이너.
#   공유 상태를 순서대로 훼손해 가며 보는 케이스(db-selftest 의 schema-diff e2e 묶음)는
#   이 풀에 넣지 않는다. 격리를 깨는 속도는 속도가 아니다.
#
# 환경변수
#   COLAB_GATE_JOBS  동시 실행 수 (기본: 코어 수, 최대 8). 1 이면 사실상 직렬이다.
#
# 쓰는 쪽: pool_init 뒤에 expect 를 평소처럼 부르고, 마지막에 pool_join 을 부른다.
#   실패 라벨은 직렬판과 같이 FAILURES 배열에 쌓인다.

POOL_N=0
# 준비 실패를 모으는 자리. 부르는 쪽이 안 만들었으면 여기서 만든다(set -u 아래서 터지지 않게).
declare -p READINESS >/dev/null 2>&1 || READINESS=()
POOL_DIR=""
POOL_JOBS="${COLAB_GATE_JOBS:-}"
if [ -z "$POOL_JOBS" ]; then
  POOL_JOBS="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)"
  [ "$POOL_JOBS" -gt 8 ] 2>/dev/null && POOL_JOBS=8
fi
[ "$POOL_JOBS" -ge 1 ] 2>/dev/null || POOL_JOBS=1

pool_init() {
  POOL_DIR="$(mktemp -d -p "${TMPDIR:-/tmp}" gate-pool-XXXXXX)"
}

# $1=기대(green|red) $2=라벨 $3.. = 실행할 명령
expect() {
  local want="$1" label="$2"; shift 2
  local n="$POOL_N"; POOL_N=$((POOL_N + 1))
  printf '%s' "$want"  > "$POOL_DIR/$n.want"
  printf '%s' "$label" > "$POOL_DIR/$n.label"
  while [ "$(jobs -rp | wc -l)" -ge "$POOL_JOBS" ]; do wait -n 2>/dev/null || break; done
  { "$@" > "$POOL_DIR/$n.out" 2>&1; echo $? > "$POOL_DIR/$n.rc"; } &
}

# 전부 끝날 때까지 기다렸다가 등록 순서로 판정·출력한다.
pool_join() {
  wait
  local n want label rc got
  for (( n = 0; n < POOL_N; n++ )); do
    want="$(cat "$POOL_DIR/$n.want")"
    label="$(cat "$POOL_DIR/$n.label")"
    if [ ! -f "$POOL_DIR/$n.rc" ]; then
      # 종료코드가 없다 = 케이스를 못 돌렸다. 미실행을 통과로 세지 않는다.
      echo "[selftest] $label → 실행되지 않음 ✗"
      FAILURES+=("$label (미실행)")
      continue
    fi
    rc="$(cat "$POOL_DIR/$n.rc")"
    # 준비 실패(검사기가 못 돌았다)를 fail-closed 결함으로 세지 않는다 — 다른 사실이다.
    # 통과로도 세지 않는다: READINESS 에 쌓여 부르는 쪽이 red(준비) 로 낸다.
    if [ "$rc" = 78 ] || grep -q '::gate-readiness-failure::' "$POOL_DIR/$n.out" 2>/dev/null; then
      grep '::gate-readiness-failure::' "$POOL_DIR/$n.out" 2>/dev/null | sed 's/^/           /'
      if [ "$want" = "ready" ]; then
        echo "[selftest] $label → red(준비) OK (이 케이스가 재는 것이 준비 실패다)"
      else
        # ⚠ **준비 실패를 「기대한 red」로 세지 않는다.** 보호 장치를 떼고 red 를 기대한 케이스가
        #   준비 실패로 red 가 났다면 그 보호 장치는 **판정된 적이 없다** — green-by-skip 의 정확한 모양이다.
        echo "[selftest] $label → red(준비) — 검사기가 못 돌았다. **판정하지 못했다**(기대 $want)"
        READINESS+=("$label (기대 $want · 판정 못 함)")
      fi
      continue
    fi
    got="green"; [ "$rc" -eq 0 ] 2>/dev/null || got="red"
    if [ "$got" = "$want" ]; then
      echo "[selftest] $label → $got OK"
    else
      echo "[selftest] $label → $got (기대 $want) ✗"
      sed 's/^/           /' "$POOL_DIR/$n.out"
      FAILURES+=("$label")
    fi
  done
  rm -rf "$POOL_DIR"
  echo "[selftest] 케이스 $POOL_N 건 (동시 $POOL_JOBS)"
}
