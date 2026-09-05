#!/usr/bin/env bash
# db-boundary 의 fail-closed 증명 (CLAUDE.md §4).
#
# 핵심 케이스는 **실제로 일어난 위반**이다 — ai-service 가 `COLAB_AI_CATALOG_DB_URL` 로
# D3 카탈로그(db/platform)에 직접 붙었고, import-boundary 는 green 이었다 (횡단이 import 가
# 아니라 DB 접속이었으므로). 그 판을 재현해 red 가 나오는지, 현재의 올바른 배치에서는
# green 이 나오는지 둘 다 확인한다.
#
# 실제 services/ · infra/ 에는 **한 글자도 쓰지 않는다** — 전부 임시 디렉터리다.
# 픽스처는 **자기 매니페스트를 들고 다닌다** — 레포 매니페스트가 정당하게 바뀌어도
# 기준 케이스가 흔들리지 않게 (gates/README.md 의 db-selftest 교훈과 같은 이유).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GATE="$REPO_ROOT/gates/tools/db_boundary.py"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" db-boundary-selftest-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
FAILURES=()
# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나.
# 종전에는 이 파일의 expect() 가 종료코드 78(준비 실패)을 그냥 red 로 접어
# **「기대한 red」로 셌다** — 그 케이스는 판정된 적이 없는데 출력은 OK 라고 말했다
# (2026-09-03 코드리뷰 #6 · `CLAUDE.md §4` green-by-skip).
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"

expect() { # $1=기대(green|red) $2=라벨 $3.. = 명령
  local want="$1" label="$2"; shift 2
  local out rc got
  out="$("$@" 2>&1)"; rc=$?
  # 준비 실패(78 또는 준비 표식)는 **기대한 red 가 아니다** — 판정된 적이 없다.
  if expect_intercept_readiness "$rc" "$out" "$label" "$want"; then return; fi
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$want" ]; then
    echo "[selftest] $label → $got OK"
  else
    echo "[selftest] $label → $got (기대 $want) ✗"
    echo "$out" | sed 's/^/           /'
    FAILURES+=("$label")
  fi
}

mkmanifest() { # $1=경로
  cat > "$1" <<'TOML'
[chains.platform]
schema = "db/platform"
env_patterns = [
  '^COLAB_CORE_(TEST_)?DATABASE_URL$',
  '^COLAB_PIPELINE_(TEST_)?DB_URL$',
  '^COLAB_PLATFORM_DB_URL$',
  '^COLAB_[A-Z0-9_]*(CATALOG|PLATFORM|LINEAGE|CORE|PIPELINE|VIZ)[A-Z0-9_]*_(DB|DATABASE)_URL$',
]

[chains.ai]
schema = "db/ai"
env_patterns = ['^COLAB_AI_DB_URL$', '^COLAB_AI_TEST_DICT_DB_URL$']

[units.core-api]
dir = "services/core-api"
compose_service = "core-api"
chains = ["platform"]

[units.ai-service]
dir = "services/ai-service"
compose_service = "ai-service"
chains = ["ai"]

[units.viz-render]
dir = "services/viz-render"
compose_service = "viz-render"
chains = []

[units.migrate-ai]
compose_service = "migrate-ai"
chains = ["ai"]

[detect]
env_is_db = '^[A-Z][A-Z0-9_]*_(DB|DATABASE)_URL$'
connect_calls = ["create_engine", "psycopg.connect", "asyncpg.connect"]
TOML
}

mkroot() { # $1=이름 → 루트 경로를 echo. 올바른(green) 배치를 만든다
  local root="$TMP/$1"
  mkdir -p "$root/services/core-api/src/colab_core/kernel" \
           "$root/services/core-api/tests" \
           "$root/services/ai-service/src/colab_ai/kernel" \
           "$root/services/ai-service/tests" \
           "$root/services/viz-render/src/colab_viz" \
           "$root/services/viz-render/tests" \
           "$root/infra/staging"
  printf 'FROM python:3.12-slim\nENV PYTHONPATH=/app/src\n' > "$root/services/core-api/Dockerfile"
  printf 'FROM python:3.12-slim\nENV PYTHONPATH=/app/src\n' > "$root/services/ai-service/Dockerfile"
  printf 'FROM python:3.12-slim\nENV PYTHONPATH=/app/src\n' > "$root/services/viz-render/Dockerfile"
  cat > "$root/services/core-api/src/colab_core/kernel/config.py" <<'PY'
import os
from sqlalchemy import create_engine
ENV_DATABASE_URL = "COLAB_CORE_DATABASE_URL"
def url() -> str:
    return os.environ.get(ENV_DATABASE_URL, "")
PY
  cat > "$root/services/ai-service/src/colab_ai/kernel/config.py" <<'PY'
"""이 단위는 db/ai 만 본다. COLAB_AI_CATALOG_DB_URL 은 판정 ㈎ 로 없앴다."""
import os
from sqlalchemy import create_engine
def url() -> str:
    return os.environ.get("COLAB_AI_DB_URL", "")
PY
  printf 'def render() -> str:\n    return "png"\n' > "$root/services/viz-render/src/colab_viz/render.py"
  cat > "$root/infra/staging/compose.i2.yml" <<'YML'
services:
  core-api:
    environment:
      COLAB_CORE_DATABASE_URL: postgresql://x@postgres:5432/colab_platform
  ai-service:
    environment:
      OPENAI_API_KEY: ""
  viz-render:
    environment:
      COLAB_VIZ_SOURCE_ROOT: /srv
  migrate-ai:
    environment:
      COLAB_AI_DB_URL: postgresql://x@postgres:5432/colab_ai
YML
  mkmanifest "$root/manifest.toml"
  echo "$root"
}

run() { # $1=루트
  env COLAB_DB_BOUNDARY_ROOT="$1" \
      COLAB_DB_BOUNDARY_MANIFEST="$1/manifest.toml" \
      COLAB_DB_BOUNDARY_COMPOSE="$1/infra/staging/compose.i2.yml" \
      python3 "$GATE"
}

echo "── 기준선 ───────────────────────────────────────────────────────────"
R="$(mkroot clean)"
expect green "현재의 올바른 배치 (ai-service 는 db/ai 만)" run "$R"

echo "── 실제로 일어난 위반 (2026-08-25) ──────────────────────────────────"
R="$(mkroot hist-src)"
sed -i 's/"COLAB_AI_DB_URL"/"COLAB_AI_CATALOG_DB_URL"/' \
  "$R/services/ai-service/src/colab_ai/kernel/config.py"
expect red "ai-service 소스가 COLAB_AI_CATALOG_DB_URL 를 읽는다" run "$R"

R="$(mkroot hist-dockerfile)"
printf 'ENV COLAB_AI_CATALOG_DB_URL=postgresql://x/colab_platform\n' \
  >> "$R/services/ai-service/Dockerfile"
expect red "ai-service Dockerfile 이 카탈로그 체인을 선언한다" run "$R"

R="$(mkroot hist-compose)"
sed -i 's#      OPENAI_API_KEY: ""#      COLAB_AI_CATALOG_DB_URL: postgresql://x/colab_platform#' \
  "$R/infra/staging/compose.i2.yml"
expect red "compose 가 ai-service 에 카탈로그 DB 를 물린다" run "$R"

echo "── 반대 방향 · 그 밖의 횡단 ─────────────────────────────────────────"
R="$(mkroot rev)"
sed -i 's/"COLAB_CORE_DATABASE_URL"/"COLAB_AI_DB_URL"/' \
  "$R/services/core-api/src/colab_core/kernel/config.py"
expect red "core-api 가 db/ai 에 붙는다 (반대 방향)" run "$R"

R="$(mkroot viz-env)"
printf 'ENV COLAB_CORE_DATABASE_URL=postgresql://x/colab_platform\n' \
  >> "$R/services/viz-render/Dockerfile"
expect red "chains=[] 인 viz-render 가 DB URL 을 선언한다" run "$R"

R="$(mkroot viz-connect)"
printf 'from sqlalchemy import create_engine\ne = create_engine("x")\n' \
  > "$R/services/viz-render/src/colab_viz/db.py"
expect red "chains=[] 인 viz-render 에 create_engine( 이 있다" run "$R"

R="$(mkroot unclassified)"
sed -i 's/"COLAB_AI_DB_URL"/"COLAB_MYSTERY_DB_URL"/' \
  "$R/services/ai-service/src/colab_ai/kernel/config.py"
expect red "어느 체인에도 안 맞는 DB URL (분류 불가는 green 이 아니다)" run "$R"

R="$(mkroot unknown-svc)"
sed -i 's#^  viz-render:#  shadow-worker:\n    environment:\n      COLAB_PIPELINE_DB_URL: postgresql://x/colab_platform\n  viz-render:#' \
  "$R/infra/staging/compose.i2.yml"
expect red "매니페스트에 없는 compose 서비스가 DB 를 잡는다" run "$R"

echo "── 산문은 위반이 아니다 (거짓 red 방지) ─────────────────────────────"
R="$(mkroot prose)"
printf '# COLAB_AI_CATALOG_DB_URL 은 판정 ㈎ 로 없앴다\n' \
  >> "$R/services/ai-service/src/colab_ai/kernel/config.py"
expect green "주석·docstring 안의 옛 env 이름은 선언이 아니다" run "$R"

echo "── fail-closed (재료가 없을 때) ─────────────────────────────────────"
R="$(mkroot no-manifest)"
expect red "매니페스트 부재" env COLAB_DB_BOUNDARY_ROOT="$R" \
  COLAB_DB_BOUNDARY_MANIFEST="$R/없다.toml" \
  COLAB_DB_BOUNDARY_COMPOSE="$R/infra/staging/compose.i2.yml" python3 "$GATE"

R="$(mkroot bad-manifest)"
printf 'this is not toml =\n' > "$R/manifest.toml"
expect red "매니페스트 파싱 실패" run "$R"

R="$(mkroot empty-manifest)"
printf '[detect]\nenv_is_db = "x"\n' > "$R/manifest.toml"
expect red "매니페스트에 단위·체인이 0건" run "$R"

R="$(mkroot no-compose)"
rm -f "$R/infra/staging/compose.i2.yml"
expect red "compose 파일 부재" run "$R"

R="$(mkroot no-unit-dir)"
rm -rf "$R/services/ai-service"
expect red "매니페스트가 가리키는 단위 디렉터리 부재" run "$R"

R="$(mkroot bad-python)"
printf 'def broken(:\n' > "$R/services/ai-service/src/colab_ai/kernel/broken.py"
expect red "파이썬 파싱 실패 (읽지 못한 대상은 skip 이 아니다)" run "$R"

R="$(mkroot no-targets)"
find "$R/services" -name '*.py' -delete
rm -f "$R/services"/*/Dockerfile
expect red "스캔 대상 0건 (조용한 green 금지)" run "$R"

R="$(mkroot empty-compose)"
printf 'services: {}\n' > "$R/infra/staging/compose.i2.yml"
expect red "compose 의 services 가 0건" run "$R"

echo "── compose 둘 (staging + dev · 〈342〉) ─────────────────────────────"
run2() { # $1=루트 — 두 파일을 `:` 목록으로 준다
  env COLAB_DB_BOUNDARY_ROOT="$1" \
      COLAB_DB_BOUNDARY_MANIFEST="$1/manifest.toml" \
      COLAB_DB_BOUNDARY_COMPOSE="$1/infra/staging/compose.i2.yml:$1/infra/dev/compose.yml" \
      python3 "$GATE"
}
mkdev() { # $1=루트 — 올바른 dev compose (같은 서비스명)
  mkdir -p "$1/infra/dev"
  cat > "$1/infra/dev/compose.yml" <<'YML'
services:
  core-api:
    environment:
      COLAB_CORE_DATABASE_URL_FILE: /etc/colab/core-database.url
  ai-service:
    environment:
      COLAB_AI_DB_URL_FILE: /etc/colab/ai-db.url
  migrate-ai:
    environment:
      COLAB_AI_DB_URL_FILE: /etc/colab/ai-owner-db.url
YML
}
R="$(mkroot two-clean)"; mkdev "$R"
expect green "두 compose 가 다 올바르다" run2 "$R"

R="$(mkroot two-missing)"
expect red "두 번째 compose(dev) 가 없다 — 건너뛰지 않고 red" run2 "$R"

R="$(mkroot two-cross)"; mkdev "$R"
cat > "$R/infra/dev/compose.yml" <<'YML'
services:
  core-api:
    environment:
      COLAB_CORE_DATABASE_URL_FILE: /etc/colab/core-database.url
  ai-service:
    environment:
      COLAB_CORE_DATABASE_URL: postgresql://x@rds/colab_platform
YML
expect red "dev compose 에서 ai-service 가 platform 체인에 붙는다 (횡단)" run2 "$R"

echo "────────────────────────────────────────────────────────────────────"
if [ ${#FAILURES[@]} -eq 0 ]; then
  # 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict db-boundary-selftest
echo "db-boundary-selftest: 전부 통과"
  exit 0
fi
echo "::error::db-boundary-selftest 실패 ${#FAILURES[@]}건: ${FAILURES[*]}"
exit 1
