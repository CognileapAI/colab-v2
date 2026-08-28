#!/usr/bin/env bash
# work-item-consistency 의 fail-closed 증명 (CLAUDE.md §4).
#
# generated-selftest.sh · seam-consistency-selftest.sh 와 같은 방식 —
# expect(기대,라벨,명령) 한 줄에 케이스 하나.
#
# 픽스처는 gates/fixtures/work-items/** 에 고정돼 있고 **자기 산문 문서를 들고 다닌다.**
# 기준 green 케이스도 fixture 다 — 레포의 실제 진행 상태는 정당하게 어긋나 있을 수 있고
# (그것이 이 게이트를 만든 이유다), selftest 가 그 상태에 볼모잡히면 안 된다
# (db-selftest · generated-selftest 와 같은 이유).
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GATE="$REPO_ROOT/gates/tools/work_item_consistency.py"
FIX="$REPO_ROOT/gates/fixtures/work-items"
FAILURES=()

# ⚠ rc 만 보는 selftest 는 반쪽이다 — **어느 검사가** red 를 냈는지 확인하지 않으면,
# 다른 검사가 우연히 red 를 내는 동안 정작 증명하려던 검사가 죽어 있어도 OK 가 나온다.
# 이 레포에는 「픽스처가 오탐을 정답으로 박아 둔」 선례가 있다(gates/README.md).
# 그래서 red 케이스는 **기호(㈎~㈓)까지 대조**하고, green 케이스는 `::error::` 부재까지 본다.
expect() { # $1=기대(green|red) $2=기호(red 일 때만 · green 이면 -) $3=라벨 $4.. = 실행할 명령
  local want="$1" mark="$2" label="$3"; shift 3
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  local got="green"; [ $rc -eq 0 ] || got="red"

  if [ "$got" != "$want" ]; then
    echo "[selftest] $label → $got (기대 $want) ✗"
    echo "$out" | sed 's/^/           /'
    FAILURES+=("$label")
    return
  fi

  if [ "$want" = "green" ]; then
    if echo "$out" | grep -q '::error::'; then
      echo "[selftest] $label → green 인데 ::error:: 가 있다 ✗"
      echo "$out" | sed 's/^/           /'
      FAILURES+=("$label(green-with-error)")
      return
    fi
  elif [ "$mark" != "-" ]; then
    # 「검사 대상 밖」 목록이 아니라 **위반 목록**에 그 기호가 있어야 한다
    if ! echo "$out" | sed -n '/::error::/,$p' | grep -q -- "$mark"; then
      echo "[selftest] $label → red 이긴 한데 $mark 가 위반 목록에 없다 — 다른 검사가 낸 red 다 ✗"
      echo "$out" | sed 's/^/           /'
      FAILURES+=("$label(wrong-check)")
      return
    fi
  fi
  echo "[selftest] $label → $got OK"
}

run() { # $1=fixture 디렉터리 — 대장과 산문 둘 다 fixture 로 고정한다
  local d="$FIX/$1"
  COLAB_WORK_ITEMS_LEDGER="$d/work-items.yaml" \
  COLAB_WORK_ITEMS_HANDOFF="$d/03-HANDOFF.md" \
  COLAB_WORK_ITEMS_WORKUNITS="$d/WORK-UNITS.md" \
    python3 "$GATE"
}

run_missing_ledger() { # 대장 부재 — 검사 불가는 통과가 아니다
  COLAB_WORK_ITEMS_LEDGER="$FIX/green/없는-대장.yaml" \
  COLAB_WORK_ITEMS_HANDOFF="$FIX/green/03-HANDOFF.md" \
  COLAB_WORK_ITEMS_WORKUNITS="$FIX/green/WORK-UNITS.md" \
    python3 "$GATE"
}

run_missing_section() { # 진실원의 §1 절이 사라진 경우 — 대조 대상 0 을 green 으로 세지 않는다
  COLAB_WORK_ITEMS_LEDGER="$FIX/green/work-items.yaml" \
  COLAB_WORK_ITEMS_HANDOFF="$REPO_ROOT/gates/tools/work-item-selftest.sh" \
  COLAB_WORK_ITEMS_WORKUNITS="$FIX/green/WORK-UNITS.md" \
    python3 "$GATE"
}

echo "══ work-item-selftest ══════════════════════════════════════"

# 대조군 — 이것이 red 면 게이트가 고장난 것이다 (정밀도 손상)
expect green - "대조군: 대장 ↔ 산문 일치 (T-P 3열 표 · 소문자 접미 식별자 포함)" run green

# 검사 여섯의 fail-closed 증명 — **그 검사가 낸 red 인지 기호로 대조한다**
expect red "㈎" "㈎ 스키마: depends_on 이 실재하지 않는 id 를 가리킨다"        run red-a-schema
expect red "㈏" "㈏ 완주 체크리스트가 대장보다 앞서 완료로 적혀 있다"          run red-b-checklist
expect red "㈐" "㈐ 진실원 표(T-P · 상태 3열째)가 대장과 갈린다"               run red-c-handoff
expect red "㈑" "㈑ ⏸(하지 않기로 한 것)가 착수 후보 표에 재등장한다"          run red-d-deferred
expect red "㈒" "㈒ 기한이 발동했는데 status 가 open 으로 남아 있다"           run red-e-deadline
expect red "㈓" "㈓ 산문끼리 갈린 채 conflict 로 남아 있다"                    run red-f-conflict

# 환경 결손 — green-by-skip 방지 (기호가 아니라 die() 경로라 기호 대조는 하지 않는다)
expect red - "대장 부재 → red (검사 불가는 통과가 아니다)"                  run_missing_ledger
expect red - "진실원에 §1 진행도 절이 없다 → red (대조 대상 0 은 통과가 아니다)" run_missing_section

if [ ${#FAILURES[@]} -gt 0 ]; then
  echo "::error::work-item-selftest — ${#FAILURES[@]}건 실패: ${FAILURES[*]}"
  exit 1
fi
echo "work-item-selftest: green — 9 케이스 (대조군 1 · red 증명 8)"
