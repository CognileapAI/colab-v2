#!/usr/bin/env bash
# `deploy_doctor` 요약줄 파서 픽스처 — **실물 출력 모양**으로 판정한다.
#
# 무엇을 증명하는가 = `doctor_summary_line`·`doctor_summary_full` 이
#   ⑴ 앞 공백 2칸이 붙은 요약줄을 잡고 ⑵ 15/15 만 통과로 읽고 ⑶ 14/15 를 미달로 읽는다.
#
# 왜 필요한가 = 종전 파서는 `grep -E '^항목 [0-9]+ — '` 였고, 실물은 `print(f"\n  {text}")` 라
#   **모든 요약줄 앞에 공백 2칸**이 있다. 한 줄도 잡히지 않아 「요약줄 없음 — 판정 불가」로만
#   떨어졌다 — 15/15 를 실제로 판정한 적이 **한 번도 없다**. 표본은 손으로 적지 않고
#   `deploy_doctor.py` 의 `DeployReport`·`verdict` 로 찍은 것이다(`tests/fixtures/README.md`).
#
# dev·AWS 무접촉 = 파일 두 개를 읽을 뿐 외부 명령을 한 건도 부르지 않는다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FX="$HERE/fixtures"

# 파서만 쓴다 — `stages.sh` 는 상위 변수 없이도 source 된다(본문은 전부 함수 안).
DRY_RUN=0
RUN_DIR=""
STAGE_LOG=/dev/null
# shellcheck source=../lib.sh
. "$HERE/../lib.sh"
# shellcheck source=../stages.sh
. "$HERE/../stages.sh"

fail=0
note() { echo "  ✗ $1"; fail=1; }

for f in "$FX/doctor-15-15.txt" "$FX/doctor-14-15.txt"; do
  [ -f "$f" ] || { echo "doctor-parse — 표본이 없다: ${f#"$HERE/"}" >&2; exit 1; }
done

# ⓐ 실물 모양의 15/15 — 요약줄을 잡고 통과로 읽는다.
line_ok="$(doctor_summary_line < "$FX/doctor-15-15.txt")"
[ -n "$line_ok" ] || note "ⓐ 15/15 표본에서 요약줄을 잡지 못했다(앞 공백 2칸을 벗기지 않는다)"
[ "$line_ok" = "항목 15 — ✓ 15 · ✗ 0 · ─ 0" ] \
  || note "ⓐ 요약줄이 축자와 다르다: [$line_ok]"
doctor_summary_full "$line_ok" || note "ⓐ 15/15 인데 통과로 읽지 않았다"

# ⓑ 14/15 — 요약줄은 잡되 **통과로 읽지 않는다**.
line_bad="$(doctor_summary_line < "$FX/doctor-14-15.txt")"
[ "$line_bad" = "항목 15 — ✓ 14 · ✗ 1 · ─ 0" ] \
  || note "ⓑ 요약줄이 축자와 다르다: [$line_bad]"
doctor_summary_full "$line_bad" && note "ⓑ 14/15 를 통과로 읽었다 — fail-open"

# ⓒ 요약줄이 아예 없는 출력 — 빈 값이어야 한다(「없음」을 「통과」로 접지 않는다).
line_none="$(printf 'deploy probe red — CURRENT_SHA 형식\n' | doctor_summary_line)"
[ -z "$line_none" ] || note "ⓒ 요약줄이 없는 출력에서 [$line_none] 을 잡았다"
doctor_summary_full "$line_none" && note "ⓒ 빈 요약줄을 통과로 읽었다 — fail-open"

# ⓓ 두 벌이 이어 붙은 출력(부분 실행 둘) — **마지막 한 벌**만 읽는다.
line_last="$(cat "$FX/doctor-14-15.txt" "$FX/doctor-15-15.txt" | doctor_summary_line)"
[ "$line_last" = "항목 15 — ✓ 15 · ✗ 0 · ─ 0" ] \
  || note "ⓓ 이어 붙은 출력에서 마지막 요약줄을 읽지 않았다: [$line_last]"

if [ "$fail" -eq 0 ]; then
  echo "doctor-parse — green (실물 모양 15/15 통과 · 14/15 미달 · 요약줄 부재 미달 · 마지막 한 벌)"
  exit 0
fi
echo "doctor-parse — red" >&2
exit 1
