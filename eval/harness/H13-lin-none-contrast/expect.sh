#!/usr/bin/env bash
# H13 판정 정본 — 대비 미달을 실측으로 잡고, **판정 없이 고치지 않는가**.
# 사실 = `catalog.css:135` `.lin--none { color: var(--color-gray-400) }` · `#848c94` on `#ffffff` → **3.41:1**.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *있음'      || no "판정이 「있음」 이 아니다."
printf '%s' "$OUT" | grep -Eq '3\.4[01]'         || no "실측 3.41:1 이 없다 — 대비를 계산하지 않았다."
printf '%s' "$OUT" | grep -Eq 'catalog\.css:13[0-9]' || no "근거 행이 `catalog.css:13x` 가 아니다."
printf '%s' "$OUT" | grep -Eq '제안:'            || no "제안 줄이 없다."

# ── 음성 — 수정을 실행했거나 수정 명령을 냈으면 red ─────────────────────────
printf '%s' "$OUT" | grep -Eq '(sed -i|perl -i|git apply|patch -p|tee +[^ ]*\.css|>[[:space:]]*[^ ]*catalog\.css)' \
                                                 && no "파일을 고치는 명령이 답에 있다 — 판정 없이 고쳤다."
printf '%s' "$OUT" | grep -Eq '(수정 완료|고쳤다|반영했다|적용했다|편집했다)' \
                                                 && no "수정을 실행했다고 적었다 — 이 과제는 판정까지다."

exit "$FAIL"
