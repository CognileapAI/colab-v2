#!/usr/bin/env bash
# contract-lint · contract-breaking 의 fail-closed 증명 (CLAUDE.md §4).
#
# "게이트가 red 를 낼 줄 아는가"를 red fixture 로 확인한다. 실제 계약 디렉터리
# (contracts/seams · events · schemas)에는 **한 글자도 쓰지 않는다** — 전부 임시 디렉터리다.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LINT="$REPO_ROOT/gates/tools/contract-lint.sh"
BREAK="$REPO_ROOT/gates/tools/contract-breaking.sh"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" contract-selftest-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
FAILURES=()
# 케이스를 병렬로 돈다. 케이스 목록·기대값·판정은 직렬판과 동일하고 실행 순서만 바뀐다.
# 출력은 등록 순서로 되돌려 재생한다 (gates/tools/_expect_pool.sh).
. "$REPO_ROOT/gates/tools/_expect_pool.sh"
pool_init

mkfixture() { # $1=이름 → $TMP/$1/contracts/{schemas,seams}
  local d="$TMP/$1/contracts"
  mkdir -p "$d/schemas" "$d/seams"
  cp "$REPO_ROOT/contracts/schemas/common.json" "$d/schemas/common.json"
  echo "$d"
}

clean_spec() { cat <<'YAML'
openapi: 3.1.0
info:
  title: selftest seam
  version: 1.0.0
  description: red fixture 용 최소 seam. 실제 계약이 아니다.
  contact: { name: colab }
servers:
  - url: "/api"
tags:
  - name: catalog
    description: 셀프테스트용 태그
paths:
  /datasets/{datasetId}:
    get:
      operationId: getDataset
      description: 데이터셋 하나를 읽는다.
      tags: [catalog]
      parameters:
        - name: datasetId
          in: path
          required: true
          schema: { $ref: "../schemas/common.json#/$defs/Ulid" }
      responses:
        "200":
          description: ok
          content:
            application/json:
              schema:
                type: object
                properties:
                  id: { $ref: "../schemas/common.json#/$defs/Ulid" }
        "404":
          description: 없음
          content:
            application/json:
              schema: { $ref: "../schemas/common.json#/$defs/ErrorEnvelope" }
YAML
}


# ── contract-lint ────────────────────────────────────────────────────────────
C="$(mkfixture lint-clean)"; clean_spec > "$C/seams/ok.openapi.yaml"
expect green "lint: 규칙을 지킨 스펙" env COLAB_SEAM_DIR="$C/seams" "$LINT"

# ① operationId 누락
C="$(mkfixture lint-noopid)"; clean_spec | grep -v 'operationId:' > "$C/seams/bad.openapi.yaml"
expect red "lint: operationId 누락" env COLAB_SEAM_DIR="$C/seams" "$LINT"

# ② 4xx 응답이 ErrorEnvelope 를 참조하지 않고 인라인
C="$(mkfixture lint-inline-err)"
clean_spec | sed 's|schema: { \$ref: "../schemas/common.json#/\$defs/ErrorEnvelope" }|schema: { type: object }|' > "$C/seams/bad.openapi.yaml"
expect red "lint: 4xx 인라인 에러 스키마" env COLAB_SEAM_DIR="$C/seams" "$LINT"

# ③ ID 를 인라인 string 으로 정의
C="$(mkfixture lint-inline-id)"
clean_spec | sed 's|id: { \$ref: "../schemas/common.json#/\$defs/Ulid" }|id: { type: string }|' > "$C/seams/bad.openapi.yaml"
expect red "lint: ID 인라인 정의" env COLAB_SEAM_DIR="$C/seams" "$LINT"

# ③-a nullable ID — `oneOf: [$ref Ulid, null]` 은 허용된다 (원천 표기처럼 데이터셋이 아닌 노드가 실재).
#      이 케이스가 green 이어야 룰 완화가 정당하다.
C="$(mkfixture lint-nullable-id)"
clean_spec | sed 's|id: { \$ref: "../schemas/common.json#/\$defs/Ulid" }|id: { oneOf: [ { $ref: "../schemas/common.json#/$defs/Ulid" }, { type: "null" } ] }|' > "$C/seams/ok.openapi.yaml"
expect green "lint: nullable ID (oneOf + Ulid)" env COLAB_SEAM_DIR="$C/seams" "$LINT"

# ③-b nullable 로 감쌌지만 안쪽이 Ulid 가 아니면 여전히 red — 완화가 구멍이 되지 않았음을 증명한다.
C="$(mkfixture lint-nullable-inline-id)"
clean_spec | sed 's|id: { \$ref: "../schemas/common.json#/\$defs/Ulid" }|id: { oneOf: [ { type: string }, { type: "null" } ] }|' > "$C/seams/bad.openapi.yaml"
expect red "lint: nullable 인라인 ID" env COLAB_SEAM_DIR="$C/seams" "$LINT"

# ④ 숫자 확신도 필드
C="$(mkfixture lint-conf)"
clean_spec | sed 's|^                  id: .*|                  confidence: { type: number }\n&|' > "$C/seams/bad.openapi.yaml"
expect red "lint: 숫자 확신도 필드" env COLAB_SEAM_DIR="$C/seams" "$LINT"

# ⑤ 배치 승인 엔드포인트
C="$(mkfixture lint-batch)"
clean_spec | sed 's|/datasets/{datasetId}:|/lineage/approve-all:|; s|- name: datasetId|- name: q|; s|in: path|in: query|' > "$C/seams/bad.openapi.yaml"
expect red "lint: 배치 승인 엔드포인트" env COLAB_SEAM_DIR="$C/seams" "$LINT"

# ⑥ 대상 0건 → red (green-by-skip 금지)
C="$(mkfixture lint-empty)"
expect red "lint: seam 0건" env COLAB_SEAM_DIR="$C/seams" "$LINT"

# ⑦ 도구 부재/설치 실패 → red (skip 아님)
C="$(mkfixture lint-notool)"; clean_spec > "$C/seams/ok.openapi.yaml"
cp "$REPO_ROOT/contracts/.spectral.yaml" "$C/.spectral.yaml"
expect red "lint: spectral 부재(설치 실패)" env COLAB_SEAM_DIR="$C/seams" COLAB_CONTRACTS_DIR="$C" "$LINT"

# ── contract-breaking ────────────────────────────────────────────────────────
BASE="$(mkfixture brk-base)"; clean_spec > "$BASE/seams/ok.openapi.yaml"

REV="$(mkfixture brk-same)"; clean_spec > "$REV/seams/ok.openapi.yaml"
expect green "breaking: 변경 없음" env COLAB_CONTRACTS_BASE="$BASE" COLAB_CONTRACTS_REV="$REV" "$BREAK"

# 엔드포인트 제거 = 대표적 파괴적 변경
REV="$(mkfixture brk-removed)"; clean_spec | sed 's|/datasets/{datasetId}:|/datasets/{datasetId}/renamed:|' > "$REV/seams/ok.openapi.yaml"
expect red "breaking: 엔드포인트 제거" env COLAB_CONTRACTS_BASE="$BASE" COLAB_CONTRACTS_REV="$REV" "$BREAK"

# 필수 쿼리 파라미터 추가 = 기존 클라이언트를 깬다
REV="$(mkfixture brk-reqparam)"
clean_spec | sed 's|      parameters:|      parameters:\n        - name: labId\n          in: query\n          required: true\n          schema: { type: string }|' > "$REV/seams/ok.openapi.yaml"
expect red "breaking: 필수 파라미터 추가" env COLAB_CONTRACTS_BASE="$BASE" COLAB_CONTRACTS_REV="$REV" "$BREAK"

# 대상 0건 → red
REV="$(mkfixture brk-empty)"
expect red "breaking: seam 0건" env COLAB_CONTRACTS_BASE="$BASE" COLAB_CONTRACTS_REV="$REV" "$BREAK"

# 도구(docker) 불능 → red (skip 아님)
mkdir -p "$TMP/stub"; printf '#!/bin/sh\nexit 1\n' > "$TMP/stub/docker"; chmod +x "$TMP/stub/docker"
REV="$(mkfixture brk-nodocker)"; clean_spec > "$REV/seams/ok.openapi.yaml"
expect red "breaking: docker 불능" env PATH="$TMP/stub:$PATH" \
  COLAB_CONTRACTS_BASE="$BASE" COLAB_CONTRACTS_REV="$REV" "$BREAK"

# ── 판정 ─────────────────────────────────────────────────────────────────────
pool_join

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::contract-selftest red — 게이트가 fail-closed 가 아니다:"
  printf '  - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "contract-selftest green — 두 게이트 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명)."
