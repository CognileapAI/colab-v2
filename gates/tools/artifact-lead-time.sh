#!/usr/bin/env bash
# artifact-lead-time.sh — intent → spec → round 단계별 첫 커밋 날짜와 리드타임(일)
# 읽기 전용. 게이트가 아니다(판정하지 않는다) — 항상 exit 0.
# 사용: bash gates/tools/artifact-lead-time.sh [--md <출력파일>]
set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT" || exit 0

OUT=""
if [ "${1:-}" = "--md" ]; then
  OUT="${2:-}"
fi

first_commit_date() {
  # $1 = 경로. 없으면 빈 문자열.
  [ -n "${1:-}" ] || return 0
  git log --diff-filter=A --format=%ad --date=short -1 -- "$1" 2>/dev/null
}

days_between() {
  # $1 시작 $2 끝 (YYYY-MM-DD). 하나라도 없으면 「—」.
  if [ -z "${1:-}" ] || [ -z "${2:-}" ]; then
    printf -- '—'
    return 0
  fi
  local a b
  a=$(date -d "$1" +%s 2>/dev/null) || { printf -- '—'; return 0; }
  b=$(date -d "$2" +%s 2>/dev/null) || { printf -- '—'; return 0; }
  printf '%d' $(( (b - a) / 86400 ))
}

emit() {
  if [ -n "$OUT" ]; then
    printf '%s\n' "$1" >> "$OUT"
  fi
  printf '%s\n' "$1"
}

[ -n "$OUT" ] && : > "$OUT"

emit "# 아티팩트 리드타임 (intent → spec → round)"
emit ""
emit "생성 $(date +%Y-%m-%d) · 근거 = 각 파일의 최초 추가 커밋(\`git log --diff-filter=A\`)"
emit ""
emit "| intent | intent 첫 커밋 | spec | spec 첫 커밋 | round | round 첫 커밋 | intent→spec(일) | spec→round(일) | 전체(일) |"
emit "|---|---|---|---|---|---|---|---|---|"

shopt -s nullglob
rows=0
for intent in dev-package/intent/*.md; do
  base="$(basename "$intent")"
  case "$base" in
    README.md|TEMPLATE.md) continue ;;
  esac

  i_date="$(first_commit_date "$intent")"
  [ -n "$i_date" ] || i_date=""

  # 이 intent 파일명을 인용하는 spec / round
  spec="$(grep -l -- "$base" dev-package/prd/specs/*.md 2>/dev/null | head -1)"
  round="$(grep -l -- "$base" dev-package/prd/rounds/*.md 2>/dev/null | head -1)"

  s_date=""; r_date=""
  [ -n "$spec" ] && s_date="$(first_commit_date "$spec")"
  [ -n "$round" ] && r_date="$(first_commit_date "$round")"

  d_is="$(days_between "$i_date" "$s_date")"
  d_sr="$(days_between "$s_date" "$r_date")"
  d_all="$(days_between "$i_date" "$r_date")"

  s_name='—'; [ -n "$spec" ] && s_name="\`$(basename "$spec")\`"
  r_name='—'; [ -n "$round" ] && r_name="\`$(basename "$round")\`"

  emit "| \`$base\` | ${i_date:-—} | $s_name | ${s_date:-—} | $r_name | ${r_date:-—} | $d_is | $d_sr | $d_all |"
  rows=$((rows + 1))
done

emit ""
emit "intent 파일 $rows 건. 「—」 = 해당 단계 파일이 없거나 아직 커밋되지 않음(미추적 파일은 첫 커밋 날짜가 잡히지 않는다)."

exit 0
