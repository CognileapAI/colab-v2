#!/usr/bin/env bash
# H08 판정 정본 — 지목 범위를 네 유형으로 좁혀 7곳을 세고, 이미 13px 인 자리를 건드리지 않는가.
# 사실 = 파일명 `detail.css:101`·`upload.css:106`·`upload.css:168` / 빈 화면 안내 `lineageGraph.css:95`
#        / 목록 링크 `lineageGraph.css:81`·`:76` / 오류 본문 `upload.css:92` = **7곳**.
#        무접촉 = `upload.css:138` `.vizerr, .warn` 이미 13px.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '지목: *7곳'                 || no "지목이 7곳이 아니다."
printf '%s' "$OUT" | grep -Eq 'detail\.css:101'            || no "파일명 표기 `detail.css:101` 이 목록에 없다."
printf '%s' "$OUT" | grep -Eq 'lineageGraph\.css:95'       || no "빈 화면 안내 `lineageGraph.css:95` 가 목록에 없다."
printf '%s' "$OUT" | grep -Eq 'upload\.css:92'             || no "오류 본문 `upload.css:92` 가 목록에 없다."
printf '%s' "$OUT" | grep -Eq '무접촉.*vizerr'             || no "이미 13px 인 `.vizerr, .warn` 을 무접촉으로 적지 않았다."
printf '%s' "$OUT" | grep -Eq '무접촉.*13(\.0)?px'         || no "무접촉 자리의 실측 13px 이 없다."

# ── 음성 — 세 파일 전수(47건)를 지목으로 넘기면 red ─────────────────────────
printf '%s' "$OUT" | grep -Eq '지목: *(4[0-9]|[23][0-9])곳' && no "네 유형으로 좁히지 않고 13px 미만 전수를 지목했다."

exit "$FAIL"
