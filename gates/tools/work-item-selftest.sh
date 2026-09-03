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
# 판정 갈래(green·red·ready·미선언)의 정본 = `_expect.sh` 하나.
# 종전에는 이 파일의 expect() 가 종료코드 78(준비 실패)을 그냥 red 로 접어
# **「기대한 red」로 셌다** — 그 케이스는 판정된 적이 없는데 출력은 OK 라고 말했다
# (2026-09-03 코드리뷰 #6 · `CLAUDE.md §4` green-by-skip).
# shellcheck source=/dev/null
. "$(dirname "${BASH_SOURCE[0]}")/_expect.sh"
CASES=0   # 케이스 수를 손으로 적지 않는다 — 요약줄이 실제와 어긋나면 그것도 거짓 보고다

# ⚠ rc 만 보는 selftest 는 반쪽이다 — **어느 검사가** red 를 냈는지 확인하지 않으면,
# 다른 검사가 우연히 red 를 내는 동안 정작 증명하려던 검사가 죽어 있어도 OK 가 나온다.
# 이 레포에는 「픽스처가 오탐을 정답으로 박아 둔」 선례가 있다(gates/README.md).
# 그래서 red 케이스는 **기호(㈎~㈓)까지 대조**하고, green 케이스는 `::error::` 부재까지 본다.
expect() { # $1=기대(green|red) $2=기호(red 일 때만 · green 이면 -) $3=라벨 $4.. = 실행할 명령
  local want="$1" mark="$2" label="$3"; shift 3
  CASES=$((CASES+1))
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  # 준비 실패(78 또는 준비 표식)는 **기대한 red 가 아니다** — 판정된 적이 없다.
  if expect_intercept_readiness "$rc" "$out" "$label" "$want"; then return; fi
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
  # 결정 로그는 픽스처가 자기 것을 들고 있으면 그것, 아니면 대조군 것을 쓴다.
  # ㈔ 하나를 더하면서 기존 red 픽스처 여섯에 같은 파일을 여섯 벌 복사하지 않는다 —
  # 복사본이 갈리면 그때부터 어느 것이 정본인지 아무도 모른다.
  local plan="$d/PLAN-SoT.md"
  [ -f "$plan" ] || plan="$FIX/green/PLAN-SoT.md"
  # ㈕ 의 지침 문서도 같은 규칙 — 픽스처가 자기 것을 들고 있으면 그것, 아니면 대조군 것.
  local claudemd="$d/CLAUDE.md"
  [ -f "$claudemd" ] || claudemd="$FIX/green/CLAUDE.md"
  COLAB_WORK_ITEMS_LEDGER="$d/work-items.yaml" \
  COLAB_WORK_ITEMS_HANDOFF="$d/03-HANDOFF.md" \
  COLAB_WORK_ITEMS_WORKUNITS="$d/WORK-UNITS.md" \
  COLAB_WORK_ITEMS_PLAN="$plan" \
  COLAB_WORK_ITEMS_CLAUDEMD="$claudemd" \
    python3 "$GATE"
}

run_missing_ledger() { # 대장 부재 — 검사 불가는 통과가 아니다
  COLAB_WORK_ITEMS_LEDGER="$FIX/green/없는-대장.yaml" \
  COLAB_WORK_ITEMS_HANDOFF="$FIX/green/03-HANDOFF.md" \
  COLAB_WORK_ITEMS_WORKUNITS="$FIX/green/WORK-UNITS.md" \
  COLAB_WORK_ITEMS_CLAUDEMD="$FIX/green/CLAUDE.md" \
    python3 "$GATE"
}

run_missing_plan() { # 결정 로그 문서 부재 — 검사 불가는 통과가 아니다
  COLAB_WORK_ITEMS_LEDGER="$FIX/green/work-items.yaml" \
  COLAB_WORK_ITEMS_HANDOFF="$FIX/green/03-HANDOFF.md" \
  COLAB_WORK_ITEMS_WORKUNITS="$FIX/green/WORK-UNITS.md" \
  COLAB_WORK_ITEMS_PLAN="$FIX/green/없는-결정로그.md" \
  COLAB_WORK_ITEMS_CLAUDEMD="$FIX/green/CLAUDE.md" \
    python3 "$GATE"
}

run_plan_no_section() { # `## 9. 결정 로그` 절이 없는 경우 — 대상 0 을 green 으로 세지 않는다
  COLAB_WORK_ITEMS_LEDGER="$FIX/green/work-items.yaml" \
  COLAB_WORK_ITEMS_HANDOFF="$FIX/green/03-HANDOFF.md" \
  COLAB_WORK_ITEMS_WORKUNITS="$FIX/green/WORK-UNITS.md" \
  COLAB_WORK_ITEMS_PLAN="$FIX/green/WORK-UNITS.md" \
  COLAB_WORK_ITEMS_CLAUDEMD="$FIX/green/CLAUDE.md" \
    python3 "$GATE"
}

run_missing_claudemd() { # 지침 문서 부재 — 검사 불가는 통과가 아니다
  COLAB_WORK_ITEMS_LEDGER="$FIX/green/work-items.yaml" \
  COLAB_WORK_ITEMS_HANDOFF="$FIX/green/03-HANDOFF.md" \
  COLAB_WORK_ITEMS_WORKUNITS="$FIX/green/WORK-UNITS.md" \
  COLAB_WORK_ITEMS_PLAN="$FIX/green/PLAN-SoT.md" \
  COLAB_WORK_ITEMS_CLAUDEMD="$FIX/green/없는-지침.md" \
    python3 "$GATE"
}

run_missing_section() { # 진실원의 §1 절이 사라진 경우 — 대조 대상 0 을 green 으로 세지 않는다
  COLAB_WORK_ITEMS_LEDGER="$FIX/green/work-items.yaml" \
  COLAB_WORK_ITEMS_HANDOFF="$REPO_ROOT/gates/tools/work-item-selftest.sh" \
  COLAB_WORK_ITEMS_WORKUNITS="$FIX/green/WORK-UNITS.md" \
  COLAB_WORK_ITEMS_CLAUDEMD="$FIX/green/CLAUDE.md" \
    python3 "$GATE"
}

echo "══ work-item-selftest ══════════════════════════════════════"

# 대조군 — 이것이 red 면 게이트가 고장난 것이다 (정밀도 손상)
# 대조군은 ㈔ 의 **정밀도**도 함께 증명한다 — 동그라미 번호가 이관 표에서 재인쇄되고
# 본문이 `〈51〉` 을 두 번 인용해도 green 이다. 선언 자리(표 첫 칸)만 세기 때문이다.
expect green - "대조군: 대장 ↔ 산문 일치 (T-P 3열 표 · 소문자 접미 식별자 포함 · 동그라미 재인쇄·본문 인용 있음)" run green

# 검사 여섯의 fail-closed 증명 — **그 검사가 낸 red 인지 기호로 대조한다**
expect red "㈎" "㈎ 스키마: depends_on 이 실재하지 않는 id 를 가리킨다"        run red-a-schema
expect red "㈏" "㈏ 완주 체크리스트가 대장보다 앞서 완료로 적혀 있다"          run red-b-checklist
expect red "㈐" "㈐ 진실원 표(T-P · 상태 3열째)가 대장과 갈린다"               run red-c-handoff
expect red "㈑" "㈑ ⏸(하지 않기로 한 것)가 착수 후보 표에 재등장한다"          run red-d-deferred
expect red "㈒" "㈒ 기한이 발동했는데 status 가 open 으로 남아 있다"           run red-e-deadline
expect red "㈓" "㈓ 산문끼리 갈린 채 conflict 로 남아 있다"                    run red-f-conflict
# ⚠ ㈑ 의 대상 좁히기가 「조용히 아무것도 안 보는」 쪽으로 무너지지 않음을 증명한다.
# 첫 열 머리글이 `WU` 인 표가 하나도 없으면 통과가 아니라 red 여야 한다.
# 대조군은 같은 절에 계측 기준선 표(첫 열 `축`)를 담고 있고 그것은 green 이다 —
# 둘이 함께 있어야 「정밀도를 올린 것」과 「범위를 줄인 것」이 갈린다.
expect red "㈑" "㈑ 항목표 머리글이 바뀌어 대상이 0 표가 됐다 → red (조용한 통과 금지)" run red-g-noitemtable
# ㈔ — 두 레인이 같은 결정 번호를 집은 모양 (2026-08-31 〈241〉 충돌 · `〈252〉`)
expect red "㈔" "㈔ 결정 번호 〈52〉 가 두 번 선언됐다"                          run red-h-dupnum
expect red "㈔" "㈔ §9 는 있는데 결정 번호 행이 0건 → red (검사 대상 0 은 통과가 아니다)" run red-i-nodecision
# ㈕ — CLAUDE.md 가 대장의 stage 3 집합과 갈린 모양 (2026-08-30 이후 레포 실물에서 실제로 일어났다 · `〈268〉`)
expect red "㈕" "㈕ CLAUDE.md 표지가 대장의 stage 3 집합과 갈린다 (빠진 것 ＋ 없는 것 양방향)" run red-j-stage3mirror
expect red "㈕" "㈕ CLAUDE.md 의 stage 3 표지가 지워졌다 → red (표지를 지워 검사를 없애지 못한다)"  run red-k-nostage3marker

# 환경 결손 — green-by-skip 방지 (기호가 아니라 die() 경로라 기호 대조는 하지 않는다)
expect red - "대장 부재 → red (검사 불가는 통과가 아니다)"                  run_missing_ledger
expect red - "진실원에 §1 진행도 절이 없다 → red (대조 대상 0 은 통과가 아니다)" run_missing_section
expect red - "결정 로그 부재 → red (검사 불가는 통과가 아니다)"                run_missing_plan
expect red - "결정 로그에 §9 절이 없다 → red (대조 대상 0 은 통과가 아니다)"   run_plan_no_section
expect red - "지침 문서(CLAUDE.md) 부재 → red (검사 불가는 통과가 아니다)"      run_missing_claudemd

if [ ${#FAILURES[@]} -gt 0 ]; then
  echo "::error::work-item-selftest — ${#FAILURES[@]}건 실패: ${FAILURES[*]}"
  exit 1
fi
# 판정 결함이 없어도 **판정하지 못한 케이스가 있으면 통과가 아니다** (`_expect.sh`).
expect_readiness_verdict work-item-selftest
echo "work-item-selftest: green — $CASES 케이스 (대조군 1 · red 증명 $((CASES-1)))"
