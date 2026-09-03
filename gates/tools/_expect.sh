#!/usr/bin/env bash
# 셀프테스트의 **판정 갈래를 한 곳에** 둔다. source 해서 쓴다.
#
# 왜 생겼나 (2026-09-03 코드리뷰 #6):
#   자체 `expect()` 를 가진 셀프테스트 12개 중 **10개가 종료코드 78(준비 실패)을 「기대한 red」로
#   세고 있었다.** 갈라 두는 자리는 `_expect_pool.sh`(병렬판) 하나뿐이었고, 직렬판은 각자
#   `got="green"; [ $rc -eq 0 ] || got="red"` 를 손으로 적어 78 을 그냥 red 로 접었다.
#
#   그 모양이 왜 나쁜가 — 보호 장치를 떼고 red 를 기대한 케이스가 **준비 실패로** red 가 났다면
#   그 보호 장치는 **판정된 적이 없다.** 그런데 출력은 「red OK」라고 말한다. 검사기가
#   아무것도 검사하지 않은 채 통과를 보고하는 것, 이 레포의 대표 실패형(green-by-skip)의
#   정확한 모양이다 (`CLAUDE.md §4`).
#
# ── 네 갈래 (판정 축은 하나 — **대상이 판정됐는가**) ─────────────────────────
#   green    종료 0            — 대상이 판정됐고 통과했다
#   red      종료 0 아님        — 대상이 판정됐고 어겼다
#   ready    종료 78(또는 표식) — **검사기가 못 돌았다.** 환경을 기다리다 못 떴다
#   미선언   종료 78 ＋ `cause=입력미선언` — 검사에 필요한 값이 아무 데도 선언되지 않았다
#
#   `ready` 와 `미선언` 을 왜 가르나: **미선언은 간헐이 아니다.** 환경이 흔들려 못 돈 것과 달리
#   값이 선언되지 않았다는 사실은 매번 같은 답을 낸다 — 그러므로 「판정 못 함」으로 접어 두지
#   않고 그 자리에서 판정한다(기대가 `미선언` 이면 OK, 아니면 결함). `_pg.sh`·`_readiness.sh`
#   가 이미 표식으로 갈라 둔 것을 여기서 **같은 말로** 받는다.
#
# ⚠ 어느 갈래든 **red 다.** 상한 연장·재시도·건너뛰기로 green 을 만드는 경로는 없다.
#   바뀌는 것은 red 가 자기 원인을 참말로 말한다는 것뿐이다.
#
# 쓰는 쪽 (직렬 셀프테스트):
#   . "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"
#   expect() {
#     ... out=$(...); rc=$? ...
#     if expect_intercept_readiness "$rc" "$out" "$label" "$want"; then return; fi
#     ... 종전의 green/red 판정 그대로 ...
#   }
#   그리고 마지막 green 선언 **앞에** expect_readiness_verdict <게이트 이름> 을 부른다.
#
# 병렬판(`_expect_pool.sh`)도 같은 분류기를 쓴다 — 두 벌로 두면 한쪽이 언젠가 관대해진다.

# set -u 아래서 터지지 않게. 부르는 쪽이 안 만들었으면 여기서 만든다.
declare -p FAILURES  >/dev/null 2>&1 || FAILURES=()
declare -p EXPECT_READINESS >/dev/null 2>&1 || EXPECT_READINESS=()

# $1=종료코드 $2=출력 → stdout: green | red | ready | 미선언
expect_classify() {
  local rc="$1" out="$2"
  if [ "$rc" = 78 ] || printf '%s' "$out" | grep -q '::gate-readiness-failure::'; then
    if printf '%s' "$out" | grep -q 'cause=입력미선언'; then printf '미선언'; else printf 'ready'; fi
    return 0
  fi
  if [ "$rc" -eq 0 ] 2>/dev/null; then printf 'green'; else printf 'red'; fi
}

# 준비 실패면 **여기서 처리하고 0 을 돌려준다**(부르는 쪽은 return). 아니면 1.
# $1=종료코드 $2=출력 $3=라벨 $4=기대(green|red|ready|미선언)
expect_intercept_readiness() {
  local rc="$1" out="$2" label="$3" want="$4" verdict
  verdict="$(expect_classify "$rc" "$out")"
  case "$verdict" in green|red) return 1 ;; esac

  printf '%s\n' "$out" | grep '::gate-readiness-failure::' | sed 's/^/           /'
  if [ "$verdict" = "미선언" ]; then
    if [ "$want" = "미선언" ]; then
      echo "[selftest] $label → red(준비·입력미선언) OK"
    else
      echo "[selftest] $label → red(준비·입력미선언) (기대 $want) ✗"
      FAILURES+=("$label: 미선언으로 분류됨(기대 $want)")
    fi
    return 0
  fi
  if [ "$want" = "ready" ]; then
    echo "[selftest] $label → red(준비) OK (이 케이스가 재는 것이 준비 실패다)"
  else
    # ⚠ **준비 실패를 「기대한 red」로 세지 않는다.** 그 케이스는 판정된 적이 없다.
    echo "[selftest] $label → red(준비) — 검사기가 못 돌았다. **판정하지 못했다**(기대 $want)"
    EXPECT_READINESS+=("$label (기대 $want · 판정 못 함)")
  fi
  return 0
}

# 판정 결함이 하나도 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다.**
# 있으면 표식을 남기고 78 로 나간다 — 실행기가 요약에서 `red(준비)` 로 갈라 적는다.
# $1 = 게이트 이름 $2 = (선택) 기다린 대상 설명
expect_readiness_verdict() {
  local gate="$1" what="${2:-셀프테스트 케이스의 실행 환경}"
  [ "${#EXPECT_READINESS[@]}" -gt 0 ] || return 0
  printf '::gate-readiness-failure::gate=%s|waited_for=%s(케이스 %d건)|limit=케이스별 상한|elapsed=-|detail=%s\n' \
    "$gate" "$what" "${#EXPECT_READINESS[@]}" "${EXPECT_READINESS[*]}"
  echo "::error::$gate red(준비) — 아래 케이스를 **판정하지 못했다**(검사기가 못 돌았다). 통과로 세지 않는다:" >&2
  printf '  - %s\n' "${EXPECT_READINESS[@]}" >&2
  exit 78
}
