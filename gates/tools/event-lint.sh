#!/usr/bin/env bash
# event-lint 게이트 (WU-D2b) — contracts/events/** 를 ajv 로 검사한다.
#
# 왜 새 게이트인가: contract-lint(spectral)는 COLAB_SEAM_DIR(기본 contracts/seams)만 훑고,
#   contract-breaking(oasdiff)은 OpenAPI 전용이다. 이벤트 계약은 **어떤 게이트도 보지 않았다**
#   (dev-package/sessions/D2-events.md §7). 조용한 사각지대라 green-by-skip 보다 위험하다.
#
# 두 겹으로 본다.
#   ① 스키마 유효성 — events/*.json 이 그 자체로 유효한 JSON Schema 2020-12 인가 (ajv compile)
#   ② 인스턴스 검증 — 고정 픽스처가 계약대로 통과/거부되는가 (ajv validate)
#      ②가 없으면 "컴파일은 되는데 ../schemas/common.json $ref 가 안 풀리는" 상태를 못 잡는다.
#      스키마가 컴파일된 것만으로는 $ref 해석을 증명하지 못한다 (D2-events §6).
#      invalid 픽스처까지 매 실행 돌리는 이유가 이것이다 — 계약이 거부해야 할 것을 실제로 거부하는지.
#
# 원칙 (CLAUDE.md §4): 도구 부재·네트워크 실패·대상 0건은 전부 **red**. skip 없음.
#
# 환경변수 (selftest 전용 — 평시엔 건드리지 않는다)
#   COLAB_EVENTS_DIR          이벤트 스키마 디렉터리 (기본: contracts/events)
#   COLAB_CONTRACTS_DIR       schemas/common.json 이 있는 contracts 루트 (기본: contracts/)
#   COLAB_EVENT_FIXTURES_DIR  픽스처 루트 (기본: gates/fixtures/events)
#   COLAB_GATE_NODE_DIR       ajv 도구 디렉터리 (기본: gates/tools/node)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONTRACTS="${COLAB_CONTRACTS_DIR:-$REPO_ROOT/contracts}"
EVENTS_DIR="${COLAB_EVENTS_DIR:-$CONTRACTS/events}"
FIXTURES="${COLAB_EVENT_FIXTURES_DIR:-$REPO_ROOT/gates/fixtures/events}"
NODE_DIR="${COLAB_GATE_NODE_DIR:-$REPO_ROOT/gates/tools/node}"
COMMON="$CONTRACTS/schemas/common.json"
ENGINE="$REPO_ROOT/gates/tools/event_lint.mjs"

red() { echo "::error::event-lint red — $*"; exit 1; }

[ -f "$COMMON" ] || red "정규 타입 정본이 없다: contracts/schemas/common.json (CLAUDE.md §3-6)"

# ── 도구 확보 ────────────────────────────────────────────────────────────────
# 버전은 gates/tools/node/package.json + package-lock.json 이 고정한다 (ajv 8.17.1 · ajv-formats 3.0.1).
# contracts/package.json 은 계약 동결분이므로 게이트 도구를 거기 얹지 않는다. npx 최신 끌어오기 금지.
command -v node >/dev/null 2>&1 || red "node 가 없다. 검사를 못 한 것은 통과가 아니다."
[ -f "$ENGINE" ] || red "검사 엔진이 없다: gates/tools/event_lint.mjs"
if [ ! -d "$NODE_DIR/node_modules/ajv" ]; then
  echo "ajv 미설치 — gates/tools/node/package-lock.json 기준으로 설치를 시도한다."
  # 병렬 실행 대비 — 잠금 뒤 한 번 더 본다.
  . "$REPO_ROOT/gates/tools/_lock.sh"; gate_lock_fd "$NODE_DIR/node_modules"
  [ -d "$NODE_DIR/node_modules/ajv" ] && gate_unlock_fd
fi
if [ ! -d "$NODE_DIR/node_modules/ajv" ]; then
  if ! (cd "$NODE_DIR" && npm ci --no-audit --no-fund >/dev/null 2>&1); then
    gate_unlock_fd
    red "ajv 를 설치하지 못했다 (네트워크/npm 실패). 검사를 못 한 것은 통과가 아니다.
   → 온라인에서 'npm ci --prefix gates/tools/node' 를 한 번 돌린 뒤 재실행한다."
  fi
  gate_unlock_fd
fi
[ -d "$NODE_DIR/node_modules/ajv" ] || red "ajv 가 여전히 없다: $NODE_DIR/node_modules/ajv"

# ── 대상 수집 ────────────────────────────────────────────────────────────────
mapfile -t SCHEMAS < <(find "$EVENTS_DIR" -maxdepth 1 -type f -name '*.json' 2>/dev/null | sort)
if [ "${#SCHEMAS[@]}" -eq 0 ]; then
  red "이벤트 계약이 0건이다 ($EVENTS_DIR).
   대상이 없는 계약 게이트를 green 으로 세는 것이 곧 green-by-skip 이다 (CLAUDE.md §4)."
fi

ENTRY="$FIXTURES/entry.schema.json"
[ -f "$ENTRY" ] || red "픽스처 진입 스키마가 없다: ${ENTRY#$REPO_ROOT/}"

mapfile -t OKS  < <(find "$FIXTURES/valid"   -maxdepth 1 -type f -name '*.json' 2>/dev/null | sort)
mapfile -t BADS < <(find "$FIXTURES/invalid" -maxdepth 1 -type f -name '*.json' 2>/dev/null | sort)
[ "${#OKS[@]}"  -gt 0 ] || red "valid 픽스처가 0건이다 (${FIXTURES#$REPO_ROOT/}/valid).
   인스턴스 검증이 없으면 ../schemas/common.json \$ref 가 실제로 해석되는지를 증명하지 못한다."
[ "${#BADS[@]}" -gt 0 ] || red "invalid 픽스처가 0건이다 (${FIXTURES#$REPO_ROOT/}/invalid).
   거부를 증명하지 않는 게이트는 fail-open 이다."

echo "# 스키마 ${#SCHEMAS[@]}건 · valid 픽스처 ${#OKS[@]}건 · invalid 픽스처 ${#BADS[@]}건"

# ── 검사 (①스키마 유효성 + ②인스턴스) ───────────────────────────────────────
node "$ENGINE" "$COMMON" "$EVENTS_DIR" "$FIXTURES" "$NODE_DIR" || red "이벤트 계약 검사 실패."

echo "event-lint green — 스키마 ${#SCHEMAS[@]}건 컴파일 · valid ${#OKS[@]}건 통과 · invalid ${#BADS[@]}건 거부."
