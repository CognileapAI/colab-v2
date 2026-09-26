#!/usr/bin/env bash
# 온톨로지 회차 도구 설정 — 누구나 한 번 돌리면 된다. 여러 번 돌려도 안전하다(있는 것은 건드리지 않는다).
#
#   bash dev-package/tools/ontology-round/setup.sh            # 점검 + 없으면 만든다
#   bash dev-package/tools/ontology-round/setup.sh --check    # 점검만(아무것도 만들지 않는다)
#
# 만드는 것: services/core-api/.venv (분석·측정용). 필요 도구: python3.12 + uv 또는 venv, docker(측정용 일회용 DB).
# dev 수집은 선택이다: ~/.config/colab-platform/with-dev-env.sh (운영자 환경 래퍼)와 그 안의 COLAB_DEV_SSH ·
# COLAB_DEV_KEY_FILE 이 있어야 한다. 없으면 로컬 DB(--database-url)로만 회차를 돌릴 수 있다.
#
# 종료코드: 0 = 회차 전체 가능 · 78 = 준비 실패(무엇이 없는지 줄마다 적는다).
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CHECK_ONLY=0; [ "${1:-}" = "--check" ] && CHECK_ONLY=1
missing=0
ok()   { printf '  ✓ %s\n' "$1"; }
miss() { printf '  ✗ %s\n' "$1"; missing=$((missing+1)); }
opt()  { printf '  ─ %s\n' "$1"; }

echo "온톨로지 회차 도구 설정 — $ROOT"
command -v python3 >/dev/null && ok "python3 $(python3 -c 'import sys;print(".".join(map(str,sys.version_info[:2])))')" || miss "python3 없음"

VENV="$ROOT/services/core-api/.venv"
if [ -x "$VENV/bin/python" ] && "$VENV/bin/python" -c 'import colab_core, psycopg' 2>/dev/null; then
  ok "core-api venv (services/core-api/.venv)"
elif [ "$CHECK_ONLY" = 1 ]; then
  miss "core-api venv 없음 — --check 없이 다시 돌리면 만든다"
else
  echo "  … core-api venv 를 만든다"
  if command -v uv >/dev/null; then
    (cd "$ROOT/services/core-api" && uv venv .venv --python 3.12 -q \
      && uv pip install -q --python .venv/bin/python -r requirements.txt -r requirements-dev.txt -e .) \
      && ok "core-api venv 생성(uv)" || miss "core-api venv 생성 실패"
  else
    (cd "$ROOT/services/core-api" && python3 -m venv .venv \
      && .venv/bin/pip install -q -r requirements.txt -r requirements-dev.txt -e .) \
      && ok "core-api venv 생성(venv+pip)" || miss "core-api venv 생성 실패"
  fi
fi

if command -v docker >/dev/null && docker info >/dev/null 2>&1; then ok "docker (측정용 일회용 DB)"
else miss "docker 없음·데몬 꺼짐 — 4단계 측정을 못 한다"; fi

WRAP="${COLAB_DEV_ENV_WRAPPER:-$HOME/.config/colab-platform/with-dev-env.sh}"
if [ -x "$WRAP" ]; then
  if "$WRAP" bash -c ': "${COLAB_DEV_SSH:?}" "${COLAB_DEV_KEY_FILE:?}"; test -r "$COLAB_DEV_KEY_FILE"' 2>/dev/null; then
    ok "dev 수집 자격(운영자 래퍼 · SSH 키) — 값은 출력하지 않는다"
  else
    opt "운영자 래퍼는 있으나 COLAB_DEV_SSH/COLAB_DEV_KEY_FILE 이 비었다 — dev 수집 불가(로컬 DB 로는 가능)"
  fi
else
  opt "운영자 래퍼 없음($WRAP) — dev 수집 불가. 필요하면 README 「dev 수집 자격」대로 둔다"
fi

if [ "$missing" -gt 0 ]; then echo "준비 실패 $missing 건"; exit 78; fi
echo "준비 완료 — 회차를 돌릴 수 있다: bash dev-package/tools/ontology-round/round.sh init"
