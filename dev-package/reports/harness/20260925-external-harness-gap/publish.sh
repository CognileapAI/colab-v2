#!/usr/bin/env bash
# Publish claude/harness-external-gap as a PR into develop.
# Run from any checkout of this repository (it never checks the branch out):
#   git fetch origin && git show origin/claude/harness-external-gap:dev-package/reports/harness/20260925-external-harness-gap/publish.sh | bash
# Piped into a non-interactive bash, so comments and errexit stay inside this script (zsh-safe).
# PUBLISH_DRY_RUN=1 stops right before `gh pr create`.
set -euo pipefail

BRANCH=claude/harness-external-gap
REPORT=dev-package/reports/harness/20260925-external-harness-gap
TITLE="하네스에 훅 등록 누락·ADR·홈 경로·줄 상한·Intent-Ref 검사와 레인 범위 대조를 붙인다"

git fetch -q origin
# Precondition (intent 판정 ⑧): PR #131 must already be merged into develop.
if [ -n "$(git log --oneline origin/develop..origin/claude/agent-model-tiering)" ]; then
  echo "게시 중단 — PR #131(claude/agent-model-tiering)이 아직 develop 에 병합되지 않았다." >&2
  exit 1
fi

HEAD_SHA=$(git rev-parse "origin/$BRANCH")
BODY=$(mktemp)
git show "$HEAD_SHA:$REPORT/PR-BODY.md" | sed "s/^Head-SHA: .*/Head-SHA: $HEAD_SHA/" > "$BODY"

# The repository's PR draft contract, run from the branch's own copy of the checker.
CHECK=$(mktemp -d)
git archive "$HEAD_SHA" scripts/harness .agents/harness.yaml | tar -x -C "$CHECK"
python3 "$CHECK/scripts/harness/pr_contract.py" --head "$HEAD_SHA" --mode draft "$BODY"

if [ "${PUBLISH_DRY_RUN:-0}" = 1 ]; then
  echo "dry run — 계약 통과 · gh pr create 생략 (head $HEAD_SHA · body $BODY)"
  exit 0
fi
gh pr create --base develop --head "$BRANCH" --title "$TITLE" --body-file "$BODY"
