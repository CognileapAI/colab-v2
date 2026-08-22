#!/usr/bin/env bash
# import-boundary · banned-import · ai-no-lineage-write 의 fail-closed 증명 (CLAUDE.md §4).
#
# "게이트가 red 를 낼 줄 아는가"를 위반 fixture 로 확인한다.
# 실제 services/ · db/ · contracts/ 에는 **한 글자도 쓰지 않는다** — 전부 임시 디렉터리다.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IB="$REPO_ROOT/gates/tools/import-boundary.sh"
BI="$REPO_ROOT/gates/tools/banned-import.py"
AI="$REPO_ROOT/gates/tools/ai-no-lineage-write.sh"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" boundary-selftest-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
FAILURES=()

expect() { # $1=기대(green|red) $2=라벨 $3.. = 명령
  local want="$1" label="$2"; shift 2
  local out rc got
  out="$("$@" 2>&1)"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$want" ]; then
    echo "[selftest] $label → $got OK"
  else
    echo "[selftest] $label → $got (기대 $want) ✗"
    echo "$out" | sed 's/^/           /'
    FAILURES+=("$label")
  fi
}

# ── 서비스 트리 fixture ──────────────────────────────────────────────────────
# dev-package/sessions/D3-boundary.md §2 의 모듈 경로 관례를 그대로 만든다.
mksvc() { # $1=이름 → services 루트 경로를 echo
  local root="$TMP/$1/services"
  local u p
  for spec in "core-api:colab_core" "pipeline-worker:colab_pipeline" "viz-render:colab_viz" "ai-service:colab_ai"; do
    u="${spec%%:*}"; p="${spec##*:}"
    mkdir -p "$root/$u/src/$p/domains" "$root/$u/src/$p/ports" "$root/$u/src/$p/kernel"
    : > "$root/$u/src/$p/__init__.py"
    : > "$root/$u/src/$p/app.py"
    : > "$root/$u/src/$p/domains/__init__.py"
    : > "$root/$u/src/$p/ports/__init__.py"
    : > "$root/$u/src/$p/kernel/__init__.py"
  done
  for d in d1_identity d2_access d3_catalog d4_lineage d6_project d8_insight; do
    : > "$root/core-api/src/colab_core/domains/$d.py"
  done
  : > "$root/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py"
  : > "$root/viz-render/src/colab_viz/domains/d7_visualization.py"
  mkdir -p "$root/ai-service/src/colab_ai/domains/d9_ontology" "$root/ai-service/src/colab_ai/domains/d10_ai_services"
  : > "$root/ai-service/src/colab_ai/domains/d9_ontology/__init__.py"
  : > "$root/ai-service/src/colab_ai/domains/d10_ai_services/__init__.py"
  echo "$root"
}

echo "── import-boundary ──────────────────────────────────────────────────"
S="$(mksvc ib-clean)"
expect green "import-boundary: 관례대로 놓인 빈 패키지" env COLAB_SERVICES_DIR="$S" "$IB"

S="$(mksvc ib-cross-domain)"
echo "from colab_core.domains import d4_lineage" > "$S/core-api/src/colab_core/domains/d3_catalog.py"
expect red "import-boundary: D3 → D4 직접 참조" env COLAB_SERVICES_DIR="$S" "$IB"

S="$(mksvc ib-cross-unit)"
echo "import colab_core" > "$S/ai-service/src/colab_ai/app.py"
expect red "import-boundary: ai-service → core-api 배포 단위 횡단" env COLAB_SERVICES_DIR="$S" "$IB"

S="$(mksvc ib-port-inverted)"
echo "from colab_core.domains import d3_catalog" > "$S/core-api/src/colab_core/ports/__init__.py"
expect red "import-boundary: Port 가 도메인을 참조(층 역전)" env COLAB_SERVICES_DIR="$S" "$IB"

S="$(mksvc ib-kernel-up)"
echo "from colab_core.domains import d2_access" > "$S/core-api/src/colab_core/domains/d1_identity.py"
expect red "import-boundary: D1(shared kernel)이 위를 참조" env COLAB_SERVICES_DIR="$S" "$IB"

S="$(mksvc ib-d10-d9)"
echo "from colab_ai.domains import d9_ontology" > "$S/ai-service/src/colab_ai/domains/d10_ai_services/__init__.py"
expect red "import-boundary: D10 → D9 직접 참조(Port 우회)" env COLAB_SERVICES_DIR="$S" "$IB"

mkdir -p "$TMP/ib-empty/services"
expect red "import-boundary: 대상 패키지 0건" env COLAB_SERVICES_DIR="$TMP/ib-empty/services" "$IB"

S="$(mksvc ib-notool)"; printf 'colab-nonexistent-package==0.0.0\n' > "$TMP/bad-reqs.txt"
expect red "import-boundary: 도구 설치 실패(skip 아님)" env COLAB_SERVICES_DIR="$S" \
  COLAB_GATE_VENV="$TMP/badvenv" COLAB_GATE_REQUIREMENTS="$TMP/bad-reqs.txt" "$IB"

echo "── banned-import ────────────────────────────────────────────────────"
S="$(mksvc bi-clean)"; echo "import json" > "$S/core-api/src/colab_core/app.py"
expect green "banned-import: geo 없는 core-api" env COLAB_SERVICES_DIR="$S" python3 "$BI"

S="$(mksvc bi-rasterio)"; echo "import rasterio" > "$S/core-api/src/colab_core/domains/d3_catalog.py"
expect red "banned-import: core-api 가 rasterio" env COLAB_SERVICES_DIR="$S" python3 "$BI"

S="$(mksvc bi-osgeo)"; echo "from osgeo import gdal" > "$S/core-api/src/colab_core/app.py"
expect red "banned-import: core-api 가 from osgeo import" env COLAB_SERVICES_DIR="$S" python3 "$BI"

S="$(mksvc bi-dynamic)"
printf 'import importlib\nx = importlib.import_module("xarray")\n' > "$S/core-api/src/colab_core/app.py"
expect red "banned-import: 동적 import 우회" env COLAB_SERVICES_DIR="$S" python3 "$BI"

S="$(mksvc bi-viz-ok)"; echo "import rasterio" > "$S/viz-render/src/colab_viz/domains/d7_visualization.py"
printf 'import xarray\nimport cfgrib\n' > "$S/pipeline-worker/src/colab_pipeline/domains/d5_ingestion.py"
expect green "banned-import: viz-render·pipeline-worker 는 geo 허용" env COLAB_SERVICES_DIR="$S" python3 "$BI"

mkdir -p "$TMP/bi-empty/services"
expect red "banned-import: .py 0건" env COLAB_SERVICES_DIR="$TMP/bi-empty/services" python3 "$BI"

S="$(mksvc bi-syntax)"; echo "def (" > "$S/core-api/src/colab_core/app.py"
expect red "banned-import: 파싱 불가 파일(읽지 못함=red)" env COLAB_SERVICES_DIR="$S" python3 "$BI"

echo "── ai-no-lineage-write ──────────────────────────────────────────────"
# fixture: seam(core-ai) + ai-service 코드 + db 두 체인. 셋 다 있어야 음성 명제를 증명할 수 있다.
seam_ok() { cat <<'YAML'
openapi: 3.1.0
info: { title: selftest core-ai, version: 1.0.0 }
paths:
  /lineage-suggestions:
    post:
      operationId: suggestLineage
      responses: { "200": { description: ok } }
  /searches:
    post:
      operationId: searchDatasets
      responses: { "200": { description: ok } }
components:
  schemas:
    LineageSuggestion: { type: object }
YAML
}
mkai() { # $1=이름 → fixture 루트를 echo. $ROOT/{seams,services,db}
  local r="$TMP/$1"
  mkdir -p "$r/seams"
  seam_ok > "$r/seams/core-ai.yaml"
  mksvc "$1" >/dev/null   # $TMP/$1/services 를 만든다 — 이미 $r 아래다
  printf 'from colab_ai.ports import kg\n\ndef suggest():\n    return []\n' \
    > "$r/services/ai-service/src/colab_ai/domains/d10_ai_services/__init__.py"
  for chain in ai platform; do
    mkdir -p "$r/db/$chain/versions"
    printf '[alembic]\nscript_location = .\nversion_table = alembic_version_%s\n' "$chain" > "$r/db/$chain/alembic.ini"
  done
  printf 'revision = "0001"\ndown_revision = None\n# ai_lineage_suggestion 테이블 (D10 제안 임시 저장소)\n' \
    > "$r/db/ai/versions/0001_init.py"
  printf 'revision = "0001"\ndown_revision = None\n# lineage_edge 테이블 (D4)\n' \
    > "$r/db/platform/versions/0001_init.py"
  echo "$r"
}
runai() { # $1=fixture 루트
  env COLAB_SEAM_DIR="$1/seams" COLAB_SERVICES_DIR="$1/services" COLAB_DB_DIR="$1/db" "$AI"
}

R="$(mkai ai-clean)"
expect green "ai-no-lineage: 제안만 있는 기준 fixture" runai "$R"

R="$(mkai ai-put)"
sed -i 's|^  /searches:|  /lineages/{id}:\n    put:\n      operationId: replaceThing\n      responses: { "200": { description: ok } }\n  /searches:|' "$R/seams/core-ai.yaml"
expect red "ai-no-lineage ①: 계보 경로의 PUT" runai "$R"

R="$(mkai ai-commitop)"
sed -i 's|operationId: searchDatasets|operationId: commitLineage|' "$R/seams/core-ai.yaml"
expect red "ai-no-lineage ②: 확정 동사 operationId" runai "$R"

R="$(mkai ai-schema)"
sed -i 's|    LineageSuggestion: { type: object }|    LineageCommitRequest: { type: object }|' "$R/seams/core-ai.yaml"
expect red "ai-no-lineage ③: 계보 확정 스키마" runai "$R"

R="$(mkai ai-noseam)"; rm -f "$R/seams/core-ai.yaml"
expect red "ai-no-lineage ④: core-ai seam 0건" runai "$R"

R="$(mkai ai-import)"
echo "import colab_core" >> "$R/services/ai-service/src/colab_ai/app.py"
expect red "ai-no-lineage ⑤: 플랫폼 패키지 import" runai "$R"

R="$(mkai ai-table)"
echo 'TABLE = "lineage_edge"' >> "$R/services/ai-service/src/colab_ai/app.py"
expect red "ai-no-lineage ⑥: D4 테이블 접두사 등장" runai "$R"

R="$(mkai ai-insert)"
echo 'SQL = "INSERT INTO lineage_edge (a) VALUES (1)"' >> "$R/services/ai-service/src/colab_ai/app.py"
expect red "ai-no-lineage ⑦: 쓰기 SQL + D4 테이블" runai "$R"

R="$(mkai ai-nocode)"; find "$R/services/ai-service" -name '*.py' -delete
expect red "ai-no-lineage ⑧: ai-service 코드 0건" runai "$R"

R="$(mkai ai-chain-ref)"
echo '# see db/platform/versions/0001_init.py' >> "$R/db/ai/versions/0001_init.py"
expect red "ai-no-lineage ⑨: db/ai 가 플랫폼 체인 참조" runai "$R"

R="$(mkai ai-chain-d4)"
echo 'op.create_table("lineage_edge")' >> "$R/db/ai/versions/0001_init.py"
expect red "ai-no-lineage ⑨: db/ai 에 D4 테이블" runai "$R"

R="$(mkai ai-chain-back)"
echo '# db/ai 와 함께 올린다' >> "$R/db/platform/versions/0001_init.py"
expect red "ai-no-lineage ⑩: db/platform 이 ai 체인 참조" runai "$R"

R="$(mkai ai-same-vt)"
sed -i 's/alembic_version_ai/alembic_version/' "$R/db/ai/alembic.ini"
sed -i 's/alembic_version_platform/alembic_version/' "$R/db/platform/alembic.ini"
expect red "ai-no-lineage ⑪: 두 체인의 version_table 동일" runai "$R"

R="$(mkai ai-no-vt)"
printf '[alembic]\nscript_location = .\n' > "$R/db/ai/alembic.ini"
expect red "ai-no-lineage ⑪: version_table 미선언" runai "$R"

R="$(mkai ai-nomig)"; rm -rf "$R/db/platform/versions"
expect red "ai-no-lineage ⑫: 한쪽 체인 마이그레이션 0건" runai "$R"

# ── 판정 ─────────────────────────────────────────────────────────────────────
if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::boundary-selftest red — 게이트가 fail-closed 가 아니다:"
  printf '  - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "boundary-selftest green — 경계 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명)."
