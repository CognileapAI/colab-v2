#!/usr/bin/env bash
# `stage2` 마커 시험 실행 경로 — 휴면 모듈의 시험이 **CI 에서 계속 돈다**는 것을 강제한다.
#
# 근거: PLAN-SoT §9 〈71〉-㉰ — 휴면은 배포 단위·화면·완료 정의에서 빼는 것이고,
#       시험은 CI 에서 동작·통과해야 한다. 「안 돌리면 휴면은 부식」.
#
# fail-closed 3조건 (CLAUDE.md §4 green-by-skip 금지):
#   ① 수집된 마커 시험이 0 건이면 red — 마커가 사라져도 조용히 green 이 되지 않는다.
#   ② 하나라도 skipped 면 red — skip 은 통과가 아니다.
#   ③ 하나라도 failed/error 면 red.
#
# 대상 = pipeline-worker 의 `-m "stage2 and not e2e"`.
#   e2e 는 원천 마운트가 없으면 fail-closed 로 red 를 내므로 CI 선택에서 제외한다
#   (제외는 마커 부여의 취소가 아니다 — 마커는 붙어 있고 원천이 있는 실행에서 함께 돈다).
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
SVC="$REPO_ROOT/services/pipeline-worker"
SELECT="${COLAB_STAGE2_SELECT:-stage2 and not e2e}"
# COLAB_STAGE2_K 는 selftest 전용이다 (red fixture 만 골라내기).
KSEL="${COLAB_STAGE2_K:-}"
KARGS=(); [ -n "$KSEL" ] && KARGS=(-k "$KSEL")

PY="${COLAB_STAGE2_PY:-$SVC/.venv/bin/python}"
if [ ! -x "$PY" ]; then
  echo "::error::stage2-markers red — pipeline-worker 파이썬이 없다: $PY
   → services/pipeline-worker 에 venv 를 만들고 requirements.txt 를 설치한 뒤 재실행한다.
   검사를 못 한 것은 통과가 아니다."
  exit 1
fi

XML="$(mktemp -t stage2-markers-XXXXXX.xml)"
trap 'rm -f "$XML"' EXIT

set +e
(cd "$SVC" && "$PY" -m pytest -q --strict-markers -p no:cacheprovider \
   -m "$SELECT" "${KARGS[@]}" --junitxml="$XML")
rc=$?
set -e

python3 - "$XML" "$rc" <<'PY'
import sys, xml.etree.ElementTree as ET

xml, rc = sys.argv[1], int(sys.argv[2])
try:
    root = ET.parse(xml).getroot()
except Exception as exc:  # 리포트 자체가 없으면 red
    print(f"::error::stage2-markers red — junit 리포트를 읽지 못했다: {exc}")
    sys.exit(1)

suites = [root] if root.tag == "testsuite" else list(root)
tot = sum(int(s.get("tests", 0)) for s in suites)
skip = sum(int(s.get("skipped", 0)) for s in suites)
fail = sum(int(s.get("failures", 0)) for s in suites)
err = sum(int(s.get("errors", 0)) for s in suites)

print(f"stage2 마커 — 수집 {tot} · skipped {skip} · failed {fail} · errors {err}")

bad = False
if tot == 0:
    print("::error::stage2-markers red — 마커 시험 0 건. 마커가 지워졌거나 선택자가 어긋났다.")
    bad = True
if skip:
    print(f"::error::stage2-markers red — skipped {skip} 건. skip 은 통과가 아니다(〈71〉-㉰).")
    bad = True
if fail or err:
    print(f"::error::stage2-markers red — failed {fail} · errors {err}.")
    bad = True
if rc != 0 and not bad:
    print(f"::error::stage2-markers red — pytest 종료 코드 {rc}.")
    bad = True
sys.exit(1 if bad else 0)
PY
