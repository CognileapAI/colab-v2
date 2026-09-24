#!/usr/bin/env bash
# Publish claude/harness-external-gap as a PR into develop.
# Run from any checkout (or subdirectory) of this repository — it never checks the branch out:
#   git fetch origin && git show origin/claude/harness-external-gap:dev-package/reports/harness/20260925-external-harness-gap/publish.sh | bash
# Piped into a non-interactive bash, so comments and errexit stay inside this script (zsh-safe).
# PUBLISH_DRY_RUN=1 stops right before `gh pr create`.
# Exit: 0 published (or dry run passed) · 1 stopped by a check · 78 could not decide (readiness).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

BRANCH=claude/harness-external-gap
REPORT=dev-package/reports/harness/20260925-external-harness-gap
TITLE="하네스에 훅 등록 누락·ADR·홈 경로·줄 상한·Intent-Ref 검사와 레인 범위 대조를 붙인다"
# PR #131 head, pinned. This branch is stacked on it (intent 판정 ⑧: publish after #131 merges).
PR131_HEAD=ff3498e5072d1422cf6433089bdf66f9ea791e9a

BODY=$(mktemp); CHECK=$(mktemp -d)
trap 'rm -rf "$BODY" "$CHECK"' EXIT

git fetch -q origin
set +e
git merge-base --is-ancestor "$PR131_HEAD" origin/develop
rc=$?
set -e
case "$rc" in
  0) ;;
  1) echo "게시 중단 — PR #131 의 커밋(${PR131_HEAD:0:8})이 develop 에 없다. 아직 병합 전이거나 squash/rebase 로 병합됐다(그 경우 이 브랜치를 develop 위로 재배치한다)." >&2
     exit 1 ;;
  *) echo "게시 중단(준비) — #131 커밋 또는 origin/develop 을 읽지 못했다(rc=$rc). git fetch 를 확인한다." >&2
     exit 78 ;;
esac

HEAD_SHA=$(git rev-parse "origin/$BRANCH")
git show "$HEAD_SHA:$REPORT/PR-BODY.md" | sed "s/^Head-SHA: .*/Head-SHA: $HEAD_SHA/" > "$BODY"

# The repository's PR draft contract, run from the branch's own copy of the checker.
git archive "$HEAD_SHA" scripts/harness .agents/harness.yaml | tar -x -C "$CHECK"
python3 "$CHECK/scripts/harness/pr_contract.py" --head "$HEAD_SHA" --mode draft "$BODY"

if [ "${PUBLISH_DRY_RUN:-0}" = 1 ]; then
  echo "dry run — 계약 통과 · gh pr create 생략 (head $HEAD_SHA)"
  exit 0
fi
gh pr create --base develop --head "$BRANCH" --title "$TITLE" --body-file "$BODY"
