#!/usr/bin/env bash
# contract-breaking 게이트 (WU-D2) — seam 계약의 파괴적 변경을 검출한다.
#
# 비교 기준(frozen seam) = **git HEAD 판의 contracts/**, 비교 대상 = **워킹트리 판**.
#   HEAD 를 기준으로 잡는 이유: seam 은 "커밋된 것이 동결된 것"이다. 별도의 frozen 사본을
#   레포에 두면 그 사본 자체가 드리프트 면이 하나 더 생긴다(누가 갱신하는가 문제).
#   CI 에서 PR 을 볼 때는 COLAB_BREAKING_BASE_REF=origin/main 으로 기준을 옮긴다.
#
# 도구 = tufin/oasdiff 도커 이미지(다이제스트 고정). 선택 근거는 dev-package/sessions/D2-gates.md.
#
# 원칙 (CLAUDE.md §4): docker 부재·이미지 pull 실패·계약 0건은 전부 **red** 다. skip 없음.
#
# 환경변수 (selftest·CI 전용)
#   COLAB_BREAKING_BASE_REF  기준 git ref (기본: HEAD)
#   COLAB_CONTRACTS_BASE     기준 contracts 디렉터리를 직접 지정 (git 대신)
#   COLAB_CONTRACTS_REV      대상 contracts 디렉터리 (기본: 워킹트리 contracts/)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_REF="${COLAB_BREAKING_BASE_REF:-HEAD}"
REV_SRC="${COLAB_CONTRACTS_REV:-$REPO_ROOT/contracts}"

# 이미지는 태그가 아니라 **다이제스트**로 고정한다. :latest 는 조용히 바뀌는 게이트다.
OASDIFF_IMAGE="tufin/oasdiff@sha256:7dbcbd1cdc6255345e3852b473f0d259da43248ae6da3a7ab4da14664b28b685"

TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" oasdiff-gate-XXXXXX)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

red() { echo "::error::contract-breaking red — $*"; exit 1; }

# ── 기준(base) 판 확보 ───────────────────────────────────────────────────────
mkdir -p "$TMP/base" "$TMP/rev"
if [ -n "${COLAB_CONTRACTS_BASE:-}" ]; then
  mkdir -p "$TMP/base/contracts"
  tar -C "$COLAB_CONTRACTS_BASE" --exclude=node_modules --exclude=.git -cf - . \
    | tar -C "$TMP/base/contracts" -xf - || red "기준 contracts 를 복사하지 못했다"
else
  if ! git -C "$REPO_ROOT" rev-parse --verify -q "$BASE_REF" >/dev/null; then
    red "기준 ref 를 찾을 수 없다: $BASE_REF"
  fi
  mkdir -p "$TMP/base/contracts"
  if git -C "$REPO_ROOT" rev-parse -q --verify "$BASE_REF:contracts" >/dev/null 2>&1; then
    git -C "$REPO_ROOT" archive "$BASE_REF" contracts | tar -x -C "$TMP/base" \
      || red "기준 판을 꺼내지 못했다 (git archive 실패)"
  fi
fi
# node_modules 를 함께 복사하면 (레포가 느린 드라이브에 있을 때) 게이트가 몇 분씩 걸린다. 애초에 제외한다.
mkdir -p "$TMP/rev/contracts"
tar -C "$REV_SRC" --exclude=node_modules --exclude=.git -cf - . | tar -C "$TMP/rev/contracts" -xf - \
  || red "대상 contracts 를 복사하지 못했다: $REV_SRC"

count() { find "$1" -maxdepth 1 -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.json' \) 2>/dev/null | wc -l; }
N_BASE="$(count "$TMP/base/contracts/seams")"
N_REV="$(count "$TMP/rev/contracts/seams")"

if [ "$N_REV" -eq 0 ]; then
  red "워킹트리 seam 계약이 0건이다.
   D2 는 seam OpenAPI 3종을 동결하는 WU다. 비교 대상이 없는 파괴적-변경 게이트를
   green 으로 세는 것이 곧 green-by-skip 이다."
fi
if [ "$N_BASE" -eq 0 ]; then
  echo "기준($BASE_REF)에 seam 이 0건 — 최초 동결이다. 파괴할 이전 계약이 없으므로 green."
  echo "contract-breaking green — 신규 seam ${N_REV}건."
  exit 0
fi

# ── 도구 확보 ────────────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || red "docker 가 없다. 검사를 못 한 것은 통과가 아니다."
docker info >/dev/null 2>&1 || red "docker 데몬에 붙지 못했다. 검사를 못 한 것은 통과가 아니다."
if ! docker image inspect "$OASDIFF_IMAGE" >/dev/null 2>&1; then
  docker pull "$OASDIFF_IMAGE" >/dev/null 2>&1 \
    || red "oasdiff 이미지를 받지 못했다 (네트워크/레지스트리 실패): $OASDIFF_IMAGE"
fi

# ── 비교 ─────────────────────────────────────────────────────────────────────
# -c(composed): 두 글로브 집합의 같은 엔드포인트끼리 비교한다. seam 파일이 여러 개라서 필요하다.
# 글로브 `*.[yj]*` 는 .yaml/.yml/.json 만 잡고 README.md 를 뺀다.
# --fail-on ERR: 파괴적 변경(ERR)에서만 red. WARN(예: 곧 제거될 deprecated)은 red 로 세지 않는다.
set -o pipefail
OUT="$(docker run --rm -v "$TMP:/w:ro" "$OASDIFF_IMAGE" breaking -c \
        '/w/base/contracts/seams/*.[yj]*' '/w/rev/contracts/seams/*.[yj]*' \
        --fail-on ERR --color never --format text 2>&1)"
rc=$?
echo "$OUT"
if [ $rc -ne 0 ]; then
  red "기준($BASE_REF) 대비 파괴적 변경이 있다 (oasdiff exit $rc).
   계약을 깨야 한다면 우회하지 말고 멈추고 보고한다 (CLAUDE.md §4 '경계를 넘어야 할 때')."
fi
echo "contract-breaking green — 기준 $BASE_REF (${N_BASE}건) 대비 파괴적 변경 없음."
