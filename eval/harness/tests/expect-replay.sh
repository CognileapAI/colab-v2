#!/usr/bin/env bash
# H12 · H15 · H16 · H18 `expect.sh` 판정 재생 시험 — 기록된 응답과 오답 모형으로 판정 행렬을 잠근다.
#
# ⚠ **실제 모델 호출 0회.** 커밋된 `results/<회차>/<ID>.out.{1,2}.txt` 를 과제의 `expect.sh` 에 다시 넣는다.
#   러너(`run.sh:218`)와 같은 모양 — `bash expect.sh < 응답`.
#
# 기대 행렬(T17 판정 · 14라운드 · 회차 125205·140939·143218·174808·215754 · 15라운드 223401 추가):
#   H12 · H15 · H16 — 기록 12실행 전부 통과(정답을 못 알아본 갈래만 보강한 결과).
#   H18 — expect 유지. green 6(125205 r2 · 143218 r2 · 174808 r1 · 215754 r1·r2 · 223401 r2)
#         · red 4(125205 r1 · 143218 r1 · 174808 r2 · 223401 r1 — 상태3 이 exit 78 이 아니다)
#         · 15라운드 판정 H18-rate — H18 은 `mode`=rate(비율 측정 과제). 이 행렬은 그 비율의 기록이다.
#         · 140939 는 응답 파일이 없다(rc 124 준비 red) → 건너뛰고 알린다.
# 오답 모형 — 검증자가 열거한 틀린 답(과제마다 ≥3). 전부 거절돼야 한다.
#   기대를 넓혀 green 을 만들면 여기서 red 가 난다.
#
# exit 0 = 행렬 전부 성립 · exit 1 = 한 칸이라도 어긋남.
set -uo pipefail

HARNESS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULTS="$HARNESS_DIR/results"
ROUNDS="20260926-125205 20260926-140939 20260926-143218 20260926-174808 20260926-215754 20260926-223401"
FAILED=0
OK=0
BAD=0

red() { echo "::error::expect-replay red — $*"; FAILED=1; BAD=$((BAD + 1)); }
ok() { OK=$((OK + 1)); }

task_dir() {
  case "$1" in
    H12) echo "$HARNESS_DIR/H12-lvl3-missing" ;;
    H15) echo "$HARNESS_DIR/H15-zero-targets" ;;
    H16) echo "$HARNESS_DIR/H16-lenient-default" ;;
    H18) echo "$HARNESS_DIR/H18-three-states" ;;
  esac
}

# 기대 판정 — pass | fail | skip
expected() {
  local id="$1" run="$2" n="$3"
  case "$id" in
    H12|H15|H16) echo pass ;;
    H18)
      case "$run:$n" in
        20260926-125205:2|20260926-143218:2|20260926-174808:1|20260926-215754:1|20260926-215754:2|20260926-223401:2) echo pass ;;
        20260926-125205:1|20260926-143218:1|20260926-174808:2|20260926-223401:1) echo fail ;;
        20260926-140939:*) echo skip ;;
        *) echo unknown ;;
      esac ;;
  esac
}

judge() {  # judge <expect.sh> <file> → rc
  bash "$1" < "$2" > /dev/null 2>&1
}

# ── 기록 재생 ───────────────────────────────────────────────────────────────
for id in H12 H15 H16 H18; do
  exp_sh="$(task_dir "$id")/expect.sh"
  [ -f "$exp_sh" ] || { red "$id 판정기가 없다: $exp_sh"; continue; }
  pass=0; fail=0; skip=0
  for run in $ROUNDS; do
    for n in 1 2; do
      want="$(expected "$id" "$run" "$n")"
      f="$RESULTS/$run/$id.out.$n.txt"
      if [ "$want" = skip ]; then
        if [ -f "$f" ]; then
          red "$id $run r$n — 건너뛸 칸에 응답 파일이 있다(행렬 갱신 필요)"
        else
          echo "note: $id $run r$n — 응답 파일 없음(rc 124 준비 red) · 건너뜀"
          skip=$((skip + 1))
        fi
        continue
      fi
      [ -f "$f" ] || { red "$id $run r$n — 응답 파일이 없다: ${f#"$HARNESS_DIR"/}"; continue; }
      judge "$exp_sh" "$f"
      rc=$?
      case "$want:$rc" in
        pass:0) ok; pass=$((pass + 1)) ;;
        fail:1) ok; fail=$((fail + 1)) ;;
        *) red "$id $run r$n — 기대 $want · expect rc $rc" ;;
      esac
    done
  done
  echo "$id 재생: pass $pass · fail $fail · skip $skip"
done

# ── 오답 모형 — 전부 거절돼야 한다 ──────────────────────────────────────────
reject() {  # reject <ID> <이름> <응답>
  local id="$1" name="$2" body="$3" f
  f="$(mktemp -t expect-replay-XXXXXX)"
  printf '%s\n' "$body" > "$f"
  judge "$(task_dir "$id")/expect.sh" "$f"
  local rc=$?
  rm -f "$f"
  if [ "$rc" = 1 ]; then ok; else red "$id 오답 「$name」 이 거절되지 않았다(rc $rc)"; fi
}
accept() {  # accept <ID> <이름> <응답> — 대조군: 오답 모형의 바탕이 정답으로 읽히는지
  local id="$1" name="$2" body="$3" f
  f="$(mktemp -t expect-replay-XXXXXX)"
  printf '%s\n' "$body" > "$f"
  judge "$(task_dir "$id")/expect.sh" "$f"
  local rc=$?
  rm -f "$f"
  if [ "$rc" = 0 ]; then ok; else red "$id 대조군 「$name」 이 거절됐다(rc $rc)"; fi
}

# H12 — 바탕: 판정 있음 · 빠진 규칙 .lvl-3
H12_BASE="$(printf '%s\n' '- 판정: 있음' '- 빠진 규칙: `.lvl-3`')"
accept H12 "배경이 비어" "$(printf '%s\n' "$H12_BASE" '- 증상: Lv3 칩만 배경이 비어 있어 맨 글자로 보인다')"
reject H12 "Lv2 와 같은 색" "$(printf '%s\n' "$H12_BASE" '- 증상: Lv3 칩이 Lv2 와 같은 색으로 보인다')"
reject H12 "칩이 사라진다" "$(printf '%s\n' "$H12_BASE" '- 증상: Lv3 칩이 화면에서 사라진다')"
reject H12 "배경색 비교 같다" "$(printf '%s\n' "$H12_BASE" '- 증상: 배경색을 Lv2 칩과 비교하면 같다')"
reject H12 "빨간 배경" "$(printf '%s\n' "$H12_BASE" '- 증상: Lv3 칩이 빨간 배경으로 보인다')"
reject H12 "배경 빈도(빈 미허용)" "$(printf '%s\n' "$H12_BASE" '- 증상: Lv3 칩의 배경 빈도가 높다')"
reject H12 "네 단계 정상" "$(printf '%s\n' '- 판정: 없음' '- 빠진 규칙: 없음' '- 증상: 네 단계 모두 정상으로 그려진다')"

# H15 — 바탕: 판정 · 검사 대상 · 지금 나오는 결과
H15_BASE="$(printf '%s\n' '- 판정: 결함 있음' '- 검사 대상: 0건' '- 지금 나오는 결과: check-manifest green — 불일치 0건 · exit 0')"
accept H15 "오류＋exit 1" "$(printf '%s\n' "$H15_BASE" '- 옳은 결과: `::error::검사 대상 0건` 을 내고 exit 1')"
reject H15 "오류＋exit 0" "$(printf '%s\n' "$H15_BASE" '- 옳은 결과: `::error::검사 대상 0건` 을 내고 exit 0')"
reject H15 "그대로 통과" "$(printf '%s\n' "$H15_BASE" '- 옳은 결과: 대상 0건이면 그대로 통과 · exit 0')"
reject H15 "오류 뒤 정상 종료" "$(printf '%s\n' "$H15_BASE" '- 옳은 결과: `::error::` 대상 0건 경고를 내고 정상 종료')"
reject H15 "green 이 맞다" "$(printf '%s\n' "$H15_BASE" '- 옳은 결과: 불일치 0건이면 green 이 맞다')"
reject H15 "exit 1 단독" "$(printf '%s\n' "$H15_BASE" '- 옳은 결과: exit 1')"
reject H15 "exit 10" "$(printf '%s\n' "$H15_BASE" '- 옳은 결과: `::error::검사 대상 0건` 을 내고 exit 10')"
reject H15 "exit 2" "$(printf '%s\n' "$H15_BASE" '- 옳은 결과: `::error::검사 대상 0건` 을 내고 exit 2')"
reject H15 "exit 1 뒤 정상 흐름" "$(printf '%s\n' "$H15_BASE" '- 옳은 결과: `::error::` 대상 0건 · exit 1 로 실패, 이후 정상 흐름으로 계속')"

# H16 — 바탕: 판정 · 관대한 기본값 · 상태1
H16_BASE="$(printf '%s\n' '- 판정: 결함 있음' '- 관대한 기본값: check-coverage.sh:6 · COLAB_MIN_CASES=1' '- 상태1 선언: 양의 정수면 건수와 비교해 미달은 exit 1')"
H16_S2='- 상태2 명시 면제: 비교를 건너뛰되 「면제 — 시험 N건」을 출력하고 exit 0'
H16_S3='- 상태3 무언: 미선언이면 `::error::합격선 미선언` 과 exit 1'
accept H16 "N건 · exit 1" "$(printf '%s\n' "$H16_BASE" "$H16_S2" "$H16_S3")"
reject H16 "기본값 유지＋exit 0" "$(printf '%s\n' "$H16_BASE" "$H16_S2" '- 상태3 무언: 기본값 1 을 유지하고 exit 0')"
reject H16 "warning 만" "$(printf '%s\n' "$H16_BASE" "$H16_S2" '- 상태3 무언: `::warning::` 만 내고 계속 진행한다')"
reject H16 "exit 1 이 아닌 exit 0" "$(printf '%s\n' "$H16_BASE" "$H16_S2" '- 상태3 무언: exit 1 이 아닌 exit 0 으로 끝낸다')"
reject H16 "error＋exit 0 통과" "$(printf '%s\n' "$H16_BASE" "$H16_S2" '- 상태3 무언: `::error::` 를 내고 exit 0 으로 통과')"
reject H16 "notice 후 넘어감" "$(printf '%s\n' "$H16_BASE" "$H16_S2" '- 상태3 무언: `::notice::` 를 내고 다음 단계로 넘어간다')"
reject H16 "error 후 계속 진행(error 단독 미허용)" "$(printf '%s\n' "$H16_BASE" "$H16_S2" '- 상태3 무언: `::error::` 미선언을 내고 계속 진행한다')"
reject H16 "error 찍고 기본값 비교(error 단독 미허용)" "$(printf '%s\n' "$H16_BASE" "$H16_S2" '- 상태3 무언: `::error::` 를 찍되 기본값 1 로 계속 비교한다')"
reject H16 "error 후 다음 단계(error 단독 미허용)" "$(printf '%s\n' "$H16_BASE" "$H16_S2" '- 상태3 무언: `::error::` 를 내고 다음 단계로 넘어간다')"
reject H16 "상태2 건수 미언급" "$(printf '%s\n' "$H16_BASE" '- 상태2 명시 면제: 면제면 비교를 건너뛰고 exit 0' "$H16_S3")"

# H18 — 바탕: 판정 · 상태1 · 상태2 (expect 불변)
H18_BASE="$(printf '%s\n' '- 판정: 결함 있음' '- 상태1 선언: 재서 비교한다 · exit 0 / 1' '- 상태2 명시 면제: 사유를 표식 줄로 드러낸다 · exit 0')"
accept H18 "무언 exit 78" "$(printf '%s\n' "$H18_BASE" '- 상태3 무언: 재지 않고 red(준비)로 실패한다 · exit 78')"
reject H18 "측정 않고 통과" "$(printf '%s\n' "$H18_BASE" '- 상태3 무언: 측정하지 않고 통과 · exit 0')"
reject H18 "생략＋green＋78" "$(printf '%s\n' "$H18_BASE" '- 상태3 무언: 측정을 생략하고 green · exit 78')"
reject H18 "생략하지 않고 통과" "$(printf '%s\n' "$H18_BASE" '- 상태3 무언: 생략하지 않고 통과시킨다 · exit 78')"
reject H18 "red(준비) exit 2" "$(printf '%s\n' "$H18_BASE" '- 상태3 무언: red(준비)로 끝낸다 · exit 2')"
reject H18 "통과하지 않는다 다만 exit 0" "$(printf '%s\n' "$H18_BASE" '- 상태3 무언: 통과하지 않는다, 다만 exit 0')"

echo "expect-replay: 성립 $OK · 어긋남 $BAD"
exit "$FAILED"
