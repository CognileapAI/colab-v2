#!/usr/bin/env bash
# event-lint · event-breaking 의 fail-closed 증명 (CLAUDE.md §4 · WU-D2b).
#
# contract-selftest.sh 와 **같은 방식**이다 — expect(기대,라벨,명령) 한 줄에 케이스 하나,
# 전부 임시 디렉터리, 실제 계약 디렉터리(contracts/**)에는 한 글자도 쓰지 않는다.
# 두 번째 스타일을 발명하지 않는다.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LINT="$REPO_ROOT/gates/tools/event-lint.sh"
BREAK="$REPO_ROOT/gates/tools/event-breaking.sh"
EVENTS="$REPO_ROOT/contracts/events"
FIX="$REPO_ROOT/gates/fixtures/events"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" event-selftest-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
FAILURES=()
# 케이스를 병렬로 돈다. 케이스 목록·기대값·판정은 직렬판과 동일하고 실행 순서만 바뀐다.
# 출력은 등록 순서로 되돌려 재생한다 (gates/tools/_expect_pool.sh).
. "$REPO_ROOT/gates/tools/_expect_pool.sh"
pool_init


evcopy() { # $1=이름 → 이벤트 계약 사본 디렉터리 경로를 출력
  local d="$TMP/ev-$1"; rm -rf "$d"; mkdir -p "$d"; cp "$EVENTS"/*.json "$d/"; echo "$d"
}
fixcopy() { # $1=이름 → 픽스처 사본 루트
  local d="$TMP/fx-$1"; rm -rf "$d"; mkdir -p "$d"; cp -a "$FIX/." "$d/"; echo "$d"
}
# JSON 을 제자리에서 고친다. $1=파일 $2=파이썬 식(변수 d 가 문서)
mutate() { python3 -c '
import json,sys
p,expr=sys.argv[1],sys.argv[2]
d=json.load(open(p,encoding="utf-8"))
exec(expr)
json.dump(d,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
' "$1" "$2"; }

CP="core-pipeline.json"; EV="envelope.json"

echo "── event-lint ──────────────────────────────────────────────"

# ① 기준선 — 실제 계약 + 실제 픽스처는 green 이어야 한다. 이게 red 면 나머지 케이스는 의미가 없다.
expect green "lint: 실제 이벤트 계약 + 픽스처" "$LINT"

# ② 스키마가 깨진 JSON — 파싱 자체가 안 된다
D="$(evcopy broken)"; printf '{ "$id": "x", ' > "$D/$EV"
expect red "lint: 깨진 JSON" env COLAB_EVENTS_DIR="$D" "$LINT"

# ③ 존재하지 않는 $def 를 $ref — common.json 참조가 끊긴 상태
D="$(evcopy dangling)"
sed -i 's|../schemas/common.json#/$defs/Ulid|../schemas/common.json#/$defs/NoSuchDef|g' "$D/$EV"
expect red "lint: 끊긴 \$ref" env COLAB_EVENTS_DIR="$D" "$LINT"

# ④ 오탈자 키워드 — ajv strict 가 조용히 무시하지 않는다
D="$(evcopy typo)"; mutate "$D/$EV" 'd["$defs"]["Delivery"]["requred"]=["attempt"]'
expect red "lint: 오탈자 키워드(strict)" env COLAB_EVENTS_DIR="$D" "$LINT"

# ⑤ 대상 0건 → red (green-by-skip 금지)
mkdir -p "$TMP/ev-empty"
expect red "lint: 이벤트 계약 0건" env COLAB_EVENTS_DIR="$TMP/ev-empty" "$LINT"

# ⑥ valid 픽스처 0건 → red. 인스턴스 검증 없는 이벤트 게이트는 \$ref 해석을 증명하지 못한다
F="$(fixcopy novalid)"; rm -f "$F"/valid/*.json
expect red "lint: valid 픽스처 0건" env COLAB_EVENT_FIXTURES_DIR="$F" "$LINT"

# ⑦ invalid 픽스처 0건 → red. 거부를 증명하지 않는 게이트는 fail-open 이다
F="$(fixcopy noinvalid)"; rm -f "$F"/invalid/*.json
expect red "lint: invalid 픽스처 0건" env COLAB_EVENT_FIXTURES_DIR="$F" "$LINT"

# ⑧ 계약을 어긴 인스턴스가 valid/ 에 있다 → red (게이트가 통과시키면 안 된다)
F="$(fixcopy badvalid)"; cp "$F/invalid/bad-ulid-labid.json" "$F/valid/"
expect red "lint: 어긴 인스턴스를 valid 로" env COLAB_EVENT_FIXTURES_DIR="$F" "$LINT"

# ⑨ 정상 인스턴스가 invalid/ 에 있다 → red (거부돼야 할 것이 안 됐다는 뜻)
F="$(fixcopy badinvalid)"; cp "$F/valid/upload-accepted.json" "$F/invalid/"
expect red "lint: 정상 인스턴스를 invalid 로" env COLAB_EVENT_FIXTURES_DIR="$F" "$LINT"

# ⑩ 진입 스키마 부재 → red
F="$(fixcopy noentry)"; rm -f "$F/entry.schema.json"
expect red "lint: 진입 스키마 부재" env COLAB_EVENT_FIXTURES_DIR="$F" "$LINT"

# ⑪ 정규 타입 정본(common.json) 부재 → red
mkdir -p "$TMP/ct-nocommon/schemas"
expect red "lint: common.json 부재" env COLAB_CONTRACTS_DIR="$TMP/ct-nocommon" COLAB_EVENTS_DIR="$EVENTS" "$LINT"

# ⑫ 도구(ajv) 확보 실패 → red (skip 아님)
mkdir -p "$TMP/node-empty"
expect red "lint: ajv 부재(설치 실패)" env COLAB_GATE_NODE_DIR="$TMP/node-empty" "$LINT"

echo "── event-breaking ──────────────────────────────────────────"

BASE="$(evcopy brk-base)"
run_break() { env COLAB_EVENTS_BASE="$BASE" COLAB_EVENTS_REV="$1" "$BREAK"; }

R="$(evcopy brk-same)"
expect green "breaking: 변경 없음" run_break "$R"

# E01 파일 제거
R="$(evcopy brk-e01)"; rm -f "$R/$CP"
expect red "breaking E01: 스키마 파일 제거" run_break "$R"

# E02 $def 제거
R="$(evcopy brk-e02)"; mutate "$R/$EV" 'd["$defs"].pop("Failure")'
expect red "breaking E02: \$def 제거" run_break "$R"

# E03 속성 제거
R="$(evcopy brk-e03)"; mutate "$R/$EV" 'd["$defs"]["Delivery"]["properties"].pop("deadLettered")'
expect red "breaking E03: 속성 제거" run_break "$R"

# E04 required 추가
R="$(evcopy brk-e04)"; mutate "$R/$EV" 'd["$defs"]["Delivery"]["required"].append("deadLettered")'
expect red "breaking E04: required 추가" run_break "$R"

# E05 required 제거
R="$(evcopy brk-e05)"; mutate "$R/$EV" 'd["$defs"]["Delivery"]["required"].remove("redelivery")'
expect red "breaking E05: required 제거" run_break "$R"

# E06 enum 값 제거
R="$(evcopy brk-e06)"; mutate "$R/$EV" 'd["$defs"]["FailureReason"]["enum"].remove("시간 초과")'
expect red "breaking E06: enum 값 제거" run_break "$R"

# E07 type 축소 (nullable 이던 것을 필수 값으로)
R="$(evcopy brk-e07)"; mutate "$R/$CP" 'd["$defs"]["HeaderParsedPayload"]["properties"]["crs"]["type"]="string"'
expect red "breaking E07: type 축소" run_break "$R"

# E08 additionalProperties 조임
R="$(evcopy brk-e08)"; mutate "$R/$EV" 'd["$defs"]["Envelope"]["properties"]["payload"]["additionalProperties"]=False'
expect red "breaking E08: additionalProperties 조임" run_break "$R"

# E09 const 변경 (라우팅 키가 바뀌면 소비자 분기가 통째로 빗나간다)
R="$(evcopy brk-e09)"; mutate "$R/$CP" 'd["$defs"]["UploadReady"]["properties"]["type"]["const"]="upload.done"'
expect red "breaking E09: const 변경" run_break "$R"

# E10 값 제약 조임
R="$(evcopy brk-e10)"; mutate "$R/$CP" 'd["$defs"]["FileRef"]["properties"]["fileName"]["maxLength"]=64'
expect red "breaking E10: maxLength 축소" run_break "$R"

# E11 oneOf 분기 제거 (AnyEvent 에서 이벤트 한 종을 뺀다)
R="$(evcopy brk-e11)"; mutate "$R/$CP" 'd["$defs"]["AnyEvent"]["oneOf"].pop()'
expect red "breaking E11: oneOf 분기 제거" run_break "$R"

# E12 $ref 대상 변경
R="$(evcopy brk-e12)"; mutate "$R/$EV" 'd["$defs"]["Envelope"]["properties"]["labId"]["$ref"]="#/$defs/SchemaVersion"'
expect red "breaking E12: \$ref 대상 변경" run_break "$R"

# E13 format 추가
R="$(evcopy brk-e13)"; mutate "$R/$EV" 'd["$defs"]["IdempotencyKey"]["format"]="uuid"'
expect red "breaking E13: format 추가" run_break "$R"

# E14 $id 변경 (소비자의 $ref 가 끊긴다)
R="$(evcopy brk-e14)"; mutate "$R/$EV" 'd["$id"]="https://colab.cognileap.ai/events/envelope-v2.json"'
expect red "breaking E14: \$id 변경" run_break "$R"

# W01 enum 값 추가 = WARN. red 로 세지 않는다 — 새 이벤트 타입이 영구히 막히면 계약이 죽는다
R="$(evcopy brk-w01)"; mutate "$R/$EV" 'd["$defs"]["FailureReason"]["enum"].append("디스크 부족")'
expect green "breaking W01: enum 값 추가(WARN)" run_break "$R"

# W02 선택 속성 추가 = 하위호환
R="$(evcopy brk-w02)"; mutate "$R/$CP" 'd["$defs"]["FileRef"]["properties"]["checksum"]={"type":"string"}'
expect green "breaking W02: 선택 속성 추가" run_break "$R"

# 제약 완화는 파괴가 아니다 (maxLength 확대)
R="$(evcopy brk-relax)"; mutate "$R/$CP" 'd["$defs"]["FileRef"]["properties"]["fileName"]["maxLength"]=512'
expect green "breaking: 제약 완화" run_break "$R"

# 설명만 바뀐 것은 파괴가 아니다
R="$(evcopy brk-desc)"; mutate "$R/$EV" 'd["$defs"]["Envelope"]["description"]="설명만 고쳤다"'
expect green "breaking: 설명 변경" run_break "$R"

# 대상 0건 → red
mkdir -p "$TMP/ev-brk-empty"
expect red "breaking: 이벤트 계약 0건" run_break "$TMP/ev-brk-empty"

# 기준 ref 부재 → red (skip 아님)
expect red "breaking: 기준 ref 부재" env COLAB_BREAKING_BASE_REF=no-such-ref-xyz \
  COLAB_EVENTS_REV="$EVENTS" "$BREAK"

# ── 판정 ─────────────────────────────────────────────────────────────────────
pool_join

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::event-selftest red — 게이트가 fail-closed 가 아니다:"
  printf '  - %s\n' "${FAILURES[@]}"
  exit 1
fi
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
# 종전에는 풀이 준비 실패를 EXPECT_READINESS 에 쌓아 두기만 하고 이 파일이 그것을
# 한 번도 읽지 않아, 못 돈 케이스가 조용히 사라진 채 green 이 나갈 수 있었다.
expect_readiness_verdict event-selftest
echo "event-selftest green — event-lint · event-breaking 이 틀린 것을 틀렸다고 말한다 (fail-closed 증명)."
