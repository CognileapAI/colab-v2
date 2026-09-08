#!/usr/bin/env bash
# H19 판정 정본 — 형제를 찾는가. 한 파일만 고치면 나머지가 남는다
# (`.claude/skills/colab-v2-work/SKILL.md:70` · intent 로스터 (라)).
# 사실 = `.verified--pending` = `--color-gray-500`(#697077) on `--color-gray-100`(#e8ecf2) → **4.23:1**(AA 미달).
#        자리는 둘 — `catalog.css:140` · `project.css:528`.
set -uo pipefail
OUT="$(cat)"
FAIL=0
no() { echo "expect red — $*" >&2; FAIL=1; }

# ── 양성 ────────────────────────────────────────────────────────────────────
printf '%s' "$OUT" | grep -Eq '판정: *있음'          || no "판정이 「있음」 이 아니다 — 대비 미달을 놓쳤다."
printf '%s' "$OUT" | grep -Eq '4\.2[0-9]'            || no "실측 4.23:1 이 없다."
printf '%s' "$OUT" | grep -Eq '고칠 자리: *2곳'      || no "고칠 자리가 2곳이 아니다."
printf '%s' "$OUT" | grep -Eq 'catalog\.css:140'     || no "`catalog.css:140` 을 지목하지 않았다."
printf '%s' "$OUT" | grep -Eq 'project\.css:52[0-9]' || no "형제 `project.css:528` 을 지목하지 않았다(형제 미탐색)."

# ── 음성 — 한 곳만 고치면 된다고 하면 red ───────────────────────────────────
printf '%s' "$OUT" | grep -Eq '고칠 자리: *1곳'      && no "한 파일만 지목했다 — 같은 모양이 형제 파일에 남는다."

exit "$FAIL"
