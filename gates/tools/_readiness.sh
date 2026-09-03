#!/usr/bin/env bash
# 준비 실패(readiness) 표식을 내는 **공용 자리**.
#
# 왜 나뉘어 있나: `gates/run.sh all` 의 요약은 red 를 두 갈래로 가른다 —
#   red(판정) = **검사 대상이 규율을 어겼다.** 고쳐야 할 결함이다.
#   red(준비) = **검사기가 판정을 못 냈다.** 대상은 아직 판정되지 않았다.
# 그런데 준비 red 의 원인은 한 종류가 아니다. `_pg.sh` 가 내는 것은 「환경을 기다리다 못 떴다」이고,
# 여기서 내는 것은 **「검사에 필요한 입력이 선언되지 않았다」**다. 둘을 같은 말로 찍으면
# 「무엇을 얼마나 기다렸나」를 묻게 되는데 기다린 것이 없다 — 아무도 값을 말하지 않았을 뿐이다.
#
# ⚠ 세 번째 범주를 만들지 않는다. 가르는 축은 하나다 — **대상이 판정됐는가.**
#   입력이 선언되지 않으면 게이트는 대상을 한 건도 보지 못한다. 그러므로 red(판정)이 아니다.
#   그리고 **여전히 red 다.** 미선언을 통과로 세는 것이 이 레포의 대표 실패다(`CLAUDE.md §4`).
#
# 표식 (한 줄 · 기계가 읽는다):
#   ::gate-readiness-failure::gate=<게이트>|cause=입력미선언|missing=<선언되지 않은 것>|detail=<사유>
# `cause=` 가 없는 옛 표식은 환경 대기(`cause=환경대기`)로 읽힌다 — `_pg.sh` 가 그쪽이다.
READINESS_EXIT=78

# 한 줄로 눕히고 길이를 자른다. **`cut -c` 는 바이트로 센다** — 한글 한 글자 중간에서 잘리면
# 깨진 바이트(0x85 등)가 남고, 그러면 `grep` 이 그 출력을 **바이너리로 보고 표식을 못 찾는다.**
# 실제로 그 일이 일어나 요약이 「사유 표식 없음」을 찍었다. 잘린 뒤 유효하지 않은 바이트를 버린다.
readiness_oneline() { # $1=원문 $2=최대 바이트
  local t; t="$(printf '%s' "$1" | tr '\n\r' '  ' | cut -c"1-$2")"
  if command -v iconv >/dev/null 2>&1; then printf '%s' "$t" | iconv -c -f UTF-8 -t UTF-8
  else printf '%s' "$t" | tr -d '\200-\277\300-\377'; fi
}

readiness_undeclared_input() { # $1=게이트 $2=선언되지 않은 것 $3=사유
  local gate="$1" missing="$2" detail="$3"
  printf '::gate-readiness-failure::gate=%s|cause=입력미선언|missing=%s|detail=%s\n' \
    "$gate" "$(readiness_oneline "$missing" 200)" "$(readiness_oneline "$detail" 400)"
  echo "::error::$gate red(준비) — **검사에 필요한 입력이 선언되지 않았다.** 판정 red 가 아니다.
   검사 대상은 한 건도 보지 못했다 — 「대상이 규율을 어겼다」가 아니라 「아무도 값을 말하지 않았다」다.
   선언되지 않은 것: $missing
   $detail
   ⚠ 미선언도 **red 다.** 기본값·건너뛰기로 green 을 만들지 않는다 (CLAUDE.md §4)."
}
