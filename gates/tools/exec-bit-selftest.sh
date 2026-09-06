#!/usr/bin/env bash
# exec-bit 가 red fixture 로 fail-closed 임을 증명한다.
#
# 케이스 4종 — 앞 셋은 red 를 내야 하고 넷째만 green 이다:
#   ⓐ `.sh` 하나가 인덱스에 100644 로 있다        → red(판정)
#   ⓑ 그 파일이 하위 폴더에 있어도 잡힌다          → red(판정)
#   ⓒ 검사 대상 `.sh` 가 0건이다(조회가 빗나갔다)  → red   ※ green-by-skip 금지
#   ⓓ 전부 100755 다                               → green
#
# ⚠ 실물 레포를 건드리지 않는다. 케이스마다 **자기 `mktemp -d` 안에 일회용 레포**를 세우고
#   게이트에 `COLAB_EXEC_BIT_ROOT` 로 물린다. `gates/config` 에도 인덱스에도 한 글자도 쓰지 않는다.
#   ⭑ 픽스처 레포는 `core.fileMode=false` 로 세운다 — 이 레포와 같은 조건(NTFS)에서 재현해야
#     「chmod 는 했는데 인덱스는 100644」라는 **바로 그 상태**가 만들어진다.
set -uo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
GATE="$REPO_ROOT/gates/tools/exec-bit.sh"
rc=0

# 판정 갈래(green·red·ready)의 정본 = `_expect.sh` 하나.
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

mk_repo() { # $1=대상 디렉터리 — 일회용 레포 하나
  git init -q -b main "$1"
  git -C "$1" config user.email selftest@example.com
  git -C "$1" config user.name selftest
  git -C "$1" config core.fileMode false
}

expect() { # $1=케이스 이름 $2=green|red $3=레포 경로
  local name="$1" want="$2" root="$3" out ec
  set +e
  out="$(COLAB_EXEC_BIT_ROOT="$root" "$GATE" 2>&1)"; ec=$?
  set -e
  if expect_intercept_readiness "$ec" "$out" "$name" "$want"; then return; fi
  if [ "$want" = "red" ]; then
    if [ "$ec" -eq 0 ]; then
      echo "::error::exec-bit-selftest red — 케이스 $name 이 green 을 냈다 (fail-open)."; rc=1
    else
      echo "  ✓ $name — red"
    fi
  else
    if [ "$ec" -eq 0 ]; then
      echo "  ✓ $name — green"
    else
      echo "::error::exec-bit-selftest red — 케이스 $name 이 red 를 냈다 (거짓 red)."
      printf '%s\n' "$out" | sed 's/^/      /'
      rc=1
    fi
  fi
}

TD="$(mktemp -d -t exec-bit-selftest-XXXXXX)"
trap 'rm -rf "$TD"' EXIT

# ⓐ 뿌리에 100644 `.sh` 하나
mk_repo "$TD/a"
printf '#!/usr/bin/env bash\necho x\n' > "$TD/a/tool.sh"
git -C "$TD/a" add tool.sh
git -C "$TD/a" update-index --chmod=-x tool.sh
expect "ⓐ 뿌리의 100644 .sh" red "$TD/a"

# ⓑ 하위 폴더에 숨어 있어도 잡힌다 (＋ 같은 레포에 정상 파일이 섞여 있어도)
mk_repo "$TD/b"
mkdir -p "$TD/b/gates/tools"
printf '#!/usr/bin/env bash\necho ok\n' > "$TD/b/ok.sh"
printf '#!/usr/bin/env bash\necho deep\n' > "$TD/b/gates/tools/deep.sh"
git -C "$TD/b" add ok.sh gates/tools/deep.sh
git -C "$TD/b" update-index --chmod=+x ok.sh
git -C "$TD/b" update-index --chmod=-x gates/tools/deep.sh
expect "ⓑ 하위 폴더의 100644 .sh" red "$TD/b"

# ⓒ 대상 0건 — 「볼 것이 없으니 통과」가 아니라 red 다
mk_repo "$TD/c"
printf 'x\n' > "$TD/c/README.md"
git -C "$TD/c" add README.md
expect "ⓒ 검사 대상 0건" red "$TD/c"

# ⓓ 전부 100755 — 이때만 green
mk_repo "$TD/d"
mkdir -p "$TD/d/infra"
printf '#!/usr/bin/env bash\necho 1\n' > "$TD/d/one.sh"
printf '#!/usr/bin/env bash\necho 2\n' > "$TD/d/infra/two.sh"
git -C "$TD/d" add one.sh infra/two.sh
git -C "$TD/d" update-index --chmod=+x one.sh infra/two.sh
expect "ⓓ 전부 100755" green "$TD/d"

[ "$rc" -eq 0 ] || exit "$rc"
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict exec-bit-selftest "git 인덱스(일회용 픽스처 레포)"
echo "exec-bit-selftest green — 100644 검출 2종 · 대상 0건 · 정상 green 넷 다 설계대로다 (fail-closed 증명)."
exit 0
