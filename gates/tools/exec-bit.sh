#!/usr/bin/env bash
# `.sh` 의 실행비트가 **인덱스에** 기록돼 있는가.
#
# 무엇을 해소하나 (D5 · `rules/colab-rules.md §4-3`):
#   이 레포는 NTFS(drvfs) 마운트 위에 있어 `core.filemode=false` 다. 로컬에서 `chmod +x` 를 해도
#   **git 이 그것을 보지 않는다** — 새 스크립트는 `100644` 로 커밋되고, 로컬 `gates/run.sh` 는
#   `bash <파일>` 로 부르므로 통과한다. 그런데 GitHub Actions 의 `exec` 는 그 파일을 직접 실행하고
#   거기서만 `Permission denied`(exit 126)로 죽는다. **로컬 green 과 CI red 가 갈리는 자리**다.
#   2026-09-03 draft PR #2 실측 — 스크립트 20개 중 12개가 `main` 에도 `100644` 였고, 그 잡이
#   실행되지 않아 잠복해 있었다.
#
#   v1 설계의 `exec-bit-guard` 훅(=`git commit` 문자열 가로채기)은 **철회됐다**(스펙 C 「삭제한 훅과
#   대체」 축자: 「`git commit` 문자열 가로채기가 취약(v1 K-3 이 자인)」). 대신 게이트가 본다 —
#   훅은 사람이 어떻게 부르느냐에 걸리지만 게이트는 **인덱스 실물**에 걸린다.
#
# 판정 = `git ls-files -s -- '*.sh' | awk '$1=="100644"'` 이 한 줄이라도 있으면 **red(판정)**.
#   대상 0건(= `.sh` 가 하나도 없다)은 **red 다** — `CLAUDE.md §4` green-by-skip 금지.
# ⚠ 종료코드 판정이 아니라 인덱스 조회다. 파일 내용을 보지 않으므로 실행 순서에 걸리지 않는다.
#
# 고치는 법 = `git update-index --chmod=+x <파일…>` 뒤 커밋. `chmod +x` 만으로는 인덱스가 안 바뀐다.
set -uo pipefail

REPO_ROOT="${COLAB_EXEC_BIT_ROOT:-${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}}"
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_readiness.sh"

if ! git -C "$REPO_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  readiness_undeclared_input "exec-bit" "git 인덱스($REPO_ROOT)" \
    "이 게이트의 판정 입력은 **git 인덱스의 파일 모드**다. 체크아웃이 아니면 잴 대상 자체가 없다."
  exit "$READINESS_EXIT"
fi

listing="$(git -C "$REPO_ROOT" ls-files -s -- '*.sh' 2>/dev/null)"
if [ -z "$listing" ]; then
  # 「대상 0건」을 통과로 세지 않는다. 이 레포에 `.sh` 가 없을 리 없으므로 이것은 조회가 빗나간 것이다.
  echo '::error::exec-bit red — 검사 대상 `.sh` 가 **0건**이다. 통과가 아니라 조회가 빗나간 것이다 (CLAUDE.md §4 green-by-skip 금지).'
  exit 1
fi

n_total="$(printf '%s\n' "$listing" | wc -l | tr -d ' ')"
# `ls-files -s` 는 `<모드> <sha> <stage>\t<경로>` 다. 경로에 공백이 있어도 깨지지 않게
# 필드가 아니라 **탭 뒤 전부**를 경로로 읽는다.
bad="$(printf '%s\n' "$listing" | awk '$1=="100644"' | cut -f2-)"

if [ -n "$bad" ]; then
  n_bad="$(printf '%s\n' "$bad" | wc -l | tr -d ' ')"
  echo "::error::exec-bit red(판정) — 인덱스 모드가 100644 인 \`.sh\` 가 ${n_bad}건이다 (전체 ${n_total}건)."
  echo "   로컬은 \`bash <파일>\` 로 불러 통과하지만, GitHub Actions 가 직접 exec 하는 자리에서만"
  echo "   \`Permission denied\`(exit 126)로 죽는다 — 로컬 green 과 CI red 가 갈리는 지점이다."
  echo "   고치는 법: git update-index --chmod=+x <아래 파일들> 뒤 커밋 (chmod 만으로는 인덱스가 안 바뀐다)"
  printf '%s\n' "$bad" | sed 's/^/     - /'
  exit 1
fi

echo "exec-bit green — \`.sh\` ${n_total}건 전부 인덱스 모드 100755 (100644 = 0건)."
exit 0
