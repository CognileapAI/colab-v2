#!/usr/bin/env bash
# 상세 화면 순회 픽스처 — `stage_verify` ① 이 **로그인된 브라우저 세션에서 · 상세 화면이 선 것을 확인한 뒤**
# 미리보기를 판정하는지 잰다.
#
# 왜 있나 = 2026-09-14 4회차 `20260914T035058Z` 의 verify 가 27건 전건을 「성립」으로 적었다 — 전부
#   **로그인 화면**이었다. ⑴ `AGENT_BROWSER_SESSION_NAME` 환경변수는 agent-browser 가 읽지 않아 호출이
#   `default` 세션(미로그인)으로 갔고 ⑵ 로그인 화면에서도 `preview-unavailable` 계수는 0 이라 그대로
#   「성립」이 됐다(green-by-skip). ⑶ id 가 없는 행은 탭이 연달아 와 `read` 가 빈 칸을 접어 **이름이 id
#   자리로 밀렸다**(`/datasets/SPI-4weeks` 를 열었다). 세 자리 모두 실모드로 돈 적이 없었다.
#
# 무엇을 증명하는가 —
#   ⓐ 모든 agent-browser 호출이 `--session <이름>` 을 싣는다(환경변수가 아니다).
#   ⓑ 상세 화면(`basic-info` 1 · `preview-unavailable` 0)이면 「성립」이고 stage_verify 가 0 으로 끝난다.
#   ⓒ 로그인 화면(`login-submit` ≥ 1)이면 「판정불가」 ＋ 차단 사유에 「로그인 화면」 ＋ 비영 종료.
#   ⓓ 빈 화면(`basic-info` 0)이면 「판정불가」 ＋ 차단 사유에 「상세 화면」 ＋ 비영 종료.
#   ⓔ id 없는 행은 이름을 지킨 채 「미성립 · id 미확보」이고 그 이름으로 `/datasets/<이름>` 을 열지 않는다.
#   ⓖ 이미 선택된 파일을 다시 고르지 않는다 — 배포 프론트(`ea21d8c2aa54` DatasetPreviewSection.tsx)는
#      같은 파일 재선택에서 설명을 비우고(:347-351) 파일 id 가 바뀔 때만 다시 받아(:169-183) 보기가
#      영구 비활성(:355)이 된다. agent-browser 0.27.0 은 비활성 버튼 클릭도 성공으로 답한다.
#      보기는 「파일 일치 · 보기 활성 · slot idle」이 1 s 이상 유지된 뒤에만 누르고(러너 `preview_settled` 와 같은 규칙),
#      누른 뒤 slot 이 idle 을 떠나지 않으면 전체 대기 없이 「클릭 미반영」으로 적는다.
#   ⓗ 보기는 좌표 클릭이 아니라 초점 ＋ Enter 로 누르고(미반영이면 JS click 한 번), 누르기 전 적중 검사
#      (버튼 중심의 elementFromPoint)와 먹힌 방법을 판정표 비고·로그에 남긴다. dev 2026-09-25 실측 —
#      `click` 이 rc 0 인데 onClick 이 돌지 않았다(버튼 중심이 화면 밖이거나 떠 있는 층에 덮이면 그렇다).
#   ⓘ GeoPackage(정본 미성립) 행은 기대를 바꾸지 않고, 실제로 보인 것(미지원 표시 계수 · slot · 보기 활성)을
#      판정표 비고에 적는다.
#
# 실물 무접촉 = `agent-browser` 를 PATH 대역으로 가린다. ssh·docker 는 이 단계가 부르지 않는다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEED_DIR="$HERE/.."
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"

fail=0
note() { echo "  ✗ $1"; fail=1; }

python3 -c 'import yaml' 2>/dev/null || {
  printf '::gate-readiness-failure::gate=dev-reseed-selftest|waited_for=PyYAML|limit=-|elapsed=-|detail=cause=실행기부재 python3 yaml 모듈이 없다\n'
  exit 78
}

# ── 대역 ─────────────────────────────────────────────────────────────────
# agent-browser 대역 = argv 를 한 줄로 적고, `FIXTURE_PAGE`(login · detail · blank)에 맞는 값을 낸다.
cat > "$TMP/bin/agent-browser" <<'STUB'
#!/usr/bin/env bash
{ printf 'AB'; for a in "$@"; do printf '\t%s' "$a"; done; printf '\n'; } >> "$FIXTURE_AB_LOG"
if [ "${1:-}" = "--session" ]; then shift 2; fi
page="${FIXTURE_PAGE:-detail}"
draw_if_enabled() {
  if [ -f "$FIXTURE_AB_LOG.described" ] && [ "${FIXTURE_DRAW_ENABLED:-true}" = true ]; then
    : > "$FIXTURE_AB_LOG.drawn"
    echo $(( $(date +%s%3N) - $(cat "$FIXTURE_AB_LOG.opened") )) > "$FIXTURE_AB_LOG.click-after-ms"
  fi
}
case "${1:-}" in
  open)
    rm -f "$FIXTURE_AB_LOG.waited" "$FIXTURE_AB_LOG.drawn" "$FIXTURE_AB_LOG.unsupported-seen" "$FIXTURE_AB_LOG.focused"
    # 배포 프론트 모형 — 기본 파일이 선택된 채 열리고 그 파일의 설명(describe)이 도착해 있다.
    : > "$FIXTURE_AB_LOG.described"; date +%s%3N > "$FIXTURE_AB_LOG.opened"
    exit "${FIXTURE_OPEN_FAIL:-0}" ;;
  select)
    [ "${2:-}" = '[data-testid="dt-pick-file"]' ] || exit 1
    [ "${3:-}" = 'FILE-1' ] || exit 1
    # 이미 선택된 FILE-1 을 다시 고르면 onPick 이 설명을 비우고(:347-351) 파일 id 가 그대로라
    # 다시 받지 않는다(:169-183) — 보기는 영구 비활성(:355).
    rm -f "$FIXTURE_AB_LOG.described" ;;
  click)
    [ "${2:-}" = '[data-testid="dt-preview-draw"]' ] || exit 1
    # agent-browser 0.27.0 — 비활성 버튼 클릭도 종료 0 으로 답한다. 반영 여부는 slot 이 말한다.
    # 덮인 버튼(FIXTURE_COVERED=1)의 좌표 클릭은 덮은 층이 받는다 — 종료 0 · 처리기 0회(dev 2026-09-25).
    [ "${FIXTURE_COVERED:-0}" = 1 ] || draw_if_enabled ;;
  focus)
    [ "${2:-}" = '[data-testid="dt-preview-draw"]' ] && : > "$FIXTURE_AB_LOG.focused" ;;
  press)
    if [ "${2:-}" = Enter ] && [ -f "$FIXTURE_AB_LOG.focused" ] && [ "${FIXTURE_KEYBOARD_NOOP:-0}" != 1 ]; then
      draw_if_enabled
    fi ;;
  eval)
    script="$(cat)"
    case "$script" in
      *elementFromPoint*)
        if [ "${FIXTURE_COVERED:-0}" = 1 ]; then
          echo '"스크롤 전 중심 (51,1412) 화면 밖(창 1280x577) · 스크롤 뒤 중심 (51,288) 을 덮은 요소 = div testid=resume-drafts 「올리다 만 것이 있어요」"'
        else
          echo '"스크롤 전 중심 (51,288) = 보기 단추 · 스크롤 뒤 중심 (51,288) = 보기 단추"'
        fi ;;
      *'.click()'*)
        echo '"js-click" ' >> "$FIXTURE_AB_LOG.js-clicks"
        [ "${FIXTURE_JS_CLICK_NOOP:-0}" = 1 ] || draw_if_enabled ;;
    esac ;;
  wait)
    case "${2:-}" in *dt-preview-slot*) : > "$FIXTURE_AB_LOG.waited" ;; esac
    exit 0 ;;
  get)
    case "${2:-} ${3:-}" in
      'value [data-testid="dt-pick-file"]')       [ "${FIXTURE_UNSUPPORTED:-0}" = 1 ] || echo FILE-1 ;;
      'text [data-testid="dt-preview-total"]')    [ -f "$FIXTURE_AB_LOG.drawn" ] && [ "${FIXTURE_TERMINAL:-done}" = done ] && echo '총 10ms' ;;
      'count [data-testid="login-submit"]')        [ "$page" = login ] && echo 1 || echo 0 ;;
      'count [data-testid="basic-info"]')          [ "$page" = detail ] && echo 1 || echo 0 ;;
      'count [data-testid="preview-unavailable"]')
        if [ "${FIXTURE_TERMINAL:-done}" = delayed-failed ] && [ -f "$FIXTURE_AB_LOG.waited" ]; then echo 1
        elif [ "$page" = detail ]; then echo "${FIXTURE_UNAVAIL:-0}"; else echo 0; fi ;;
      'attr [data-testid="dt-preview-slot"]')
        if [ ! -f "$FIXTURE_AB_LOG.drawn" ]; then echo idle
        elif [ "${FIXTURE_TERMINAL:-done}" = delayed-failed ]; then
          if [ -f "$FIXTURE_AB_LOG.waited" ]; then echo failed
          else : > "$FIXTURE_AB_LOG.waited"; echo drawing; fi
        else echo "${FIXTURE_TERMINAL:-done}"; fi ;;
      'text [data-testid="ig-가공 단계"]')          [ "$page" = detail ] && echo "가공 단계 Lv0" || { echo "Element not found" >&2; exit 1; } ;;
      'count [data-testid="ig-unset-가공 단계"]')   echo 0 ;;
      'count [data-testid="usage-card"]')          [ "$page" = detail ] && echo 1 || echo 0 ;;
      'count [data-testid="dt-preview-unsupported"]')
        if [ "${FIXTURE_UNSUPPORTED:-0}" != 1 ]; then echo 0
        elif [ "${FIXTURE_UNSUPPORTED_DELAY:-0}" = 1 ] && [ ! -f "$FIXTURE_AB_LOG.unsupported-seen" ]; then
          : > "$FIXTURE_AB_LOG.unsupported-seen"; echo 0
        else echo 1; fi ;;
      *) echo 0 ;;
    esac ;;
  is)
    if [ "${2:-} ${3:-}" = 'enabled [data-testid="dt-preview-draw"]' ]; then
      if [ -f "$FIXTURE_AB_LOG.described" ]; then echo "${FIXTURE_DRAW_ENABLED:-true}"; else echo false; fi
      exit 0
    fi
    exit 1 ;;
  *) echo ok ;;
esac
exit 0
STUB
chmod +x "$TMP/bin"/*
export PATH="$TMP/bin:$PATH"

# ── 도구 적재 ────────────────────────────────────────────────────────────
# 등재표는 `$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml` 에서 읽는다 — 임시 뿌리에 작은 표를 둔다.
REPO_ROOT="$TMP/repo"; mkdir -p "$REPO_ROOT/dev-package/tools/dev-seed"
RUN_DIR="$TMP/run"; mkdir -p "$RUN_DIR/logs" "$RUN_DIR/stages"
RUN_ID=19700101T000000Z
DRY_RUN=0
TARGET_SHA=deadbeefcafe
S3_BUCKET=colab-platform-data-dev
S3_REGION=ap-northeast-2
EC2_SECRETS_DIR=/etc/colab
LAB_ID=00000000000000000000HYMETS
RESEED_ACCOUNT_ID=000000000000000000HYMETSP1
RESEED_ACCOUNT_EMAIL='pi@hymets.invalid'
RESEED_ACCOUNT_NAME='전창현'
RESEED_ACCOUNT_ROLE='교수'
DEV_URL='https://dev.invalid'
SEED_WORK_DIR="$TMP/seed-work"; mkdir -p "$SEED_WORK_DIR"
BUILD_PLAN_PY="$TMP/build_plan_stub.py"; : > "$BUILD_PLAN_PY"
COLAB_DEV_SSH='ec2-user@<대역>'
COLAB_DEV_KEY_FILE="$TMP/no-such-key"
EXPECT_DATASETS=1; EXPECT_PROJECTS=1; EXPECT_EDGES=0
COLAB_RESEED_PREVIEW_WAIT_MS=200
export FIXTURE_AB_LOG="$TMP/ab.log"

relpath() { printf '%s' "$1"; }

# shellcheck source=../lib.sh
. "$RESEED_DIR/lib.sh"
# shellcheck source=../stages.sh
. "$RESEED_DIR/stages.sh"
# 정착 유지 창은 기본값(1 s)을 한 번 재고, 나머지 케이스는 짧게 줄여 픽스처를 빠르게 돈다.
DEFAULT_STABLE_MS="${PREVIEW_STABLE_MS:-}"
PREVIEW_STABLE_MS=40
PREVIEW_CLICK_ACK_MS=150
ACCOUNTS_WORK_DIR="$SEED_WORK_DIR/accounts"
ACCOUNTS_FILE="$TMP/approved-profile.json"
cp "$RESEED_DIR/accounts-profile.example.json" "$ACCOUNTS_FILE"
chmod 600 "$ACCOUNTS_FILE"
export COLAB_RESEED_ACCOUNTS_PROFILE="$ACCOUNTS_FILE"
TARGET_SHA=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
# This fixture isolates detail traversal. Account store/login behavior is tested in test_accounts.py.
account_finalize() { :; }


cat > "$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml" <<'YAML'
datasets:
  - {seq: 1, name: "HSR 레이더 반사도 원자료", processing_level: Lv0, preview_expected: "미측정"}
YAML
cat > "$SEED_WORK_DIR/verify.json" <<'JSON'
{"dataset_count_ui": 1, "dataset_count_state": 1, "by_project": {"radar": 1}, "edges_ok": 0, "edges_missing": [], "periods_expected": 1, "periods_ok": 1, "periods_missing": [], "model_input_descriptions_ok": 2, "model_input_descriptions_missing": []}
JSON

write_state() { # $1 = id 없는 행을 넣는가(1/0)
  if [ "$1" = 1 ]; then
    cat > "$SEED_WORK_DIR/state.json" <<'JSON'
{"datasets": {"1": {"seq": 1, "name": "HSR 레이더 반사도 원자료", "status": "done", "dataset_id": "01M2EWQH8CES9TDC39FSFMKXVQ"},
              "2": {"seq": 2, "name": "SPI-4weeks", "status": "failed", "dataset_id": null}}}
JSON
  else
    cat > "$SEED_WORK_DIR/state.json" <<'JSON'
{"datasets": {"1": {"seq": 1, "name": "HSR 레이더 반사도 원자료", "status": "done", "dataset_id": "01M2EWQH8CES9TDC39FSFMKXVQ"}}}
JSON
  fi
}
reset_run() { rm -f "$ACCOUNTS_WORK_DIR/details-verified.json"; : > "$FIXTURE_AB_LOG"; rm -f "$FIXTURE_AB_LOG.click-after-ms" "$FIXTURE_AB_LOG.js-clicks";  rm -f "$RUN_DIR/blocked.jsonl" "$RUN_DIR/preview-judgment.tsv"; CURRENT_STAGE=verify; STAGE_LOG="$RUN_DIR/logs/verify.log"; : > "$STAGE_LOG"; }
verdict_of() { awk -F'\t' -v s="$1" '$1==s {print $4}' "$RUN_DIR/preview-judgment.tsv"; }
note_of() { awk -F'\t' -v s="$1" '$1==s {print $8}' "$RUN_DIR/preview-judgment.tsv"; }

# ── ⓐ·ⓑ 상세 화면 · 세션 인자 ────────────────────────────────────────────
write_state 0; reset_run
export FIXTURE_PAGE=detail
[ "$DEFAULT_STABLE_MS" = 1000 ] || note "ⓖ 보기 전 정착 유지 창 기본값이 1000 ms 가 아니다: [$DEFAULT_STABLE_MS]"
saved_wait="$PREVIEW_WAIT_MS"; PREVIEW_WAIT_MS=4000; PREVIEW_STABLE_MS="${DEFAULT_STABLE_MS:-1000}"
stage_verify >/dev/null 2>&1; rc=$?
PREVIEW_WAIT_MS="$saved_wait"; PREVIEW_STABLE_MS=40
click_after="$(cat "$FIXTURE_AB_LOG.click-after-ms" 2>/dev/null)"
[ "${click_after:-0}" -ge 1000 ] || note "ⓖ′ 보기를 정착 1 s 유지 전에 눌렀다(열린 뒤 [${click_after:-미반영}] ms)"
[ "$rc" -eq 0 ] || note "ⓑ 상세 화면 전건 성립인데 stage_verify 가 $rc 로 끝났다: $(tail -1 "$STAGE_LOG")"
[ "$(verdict_of 1)" = 성립 ] || note "ⓑ′ 상세 화면의 판정이 「성립」이 아니다: [$(verdict_of 1)]"
n_calls="$(grep -c '^AB' "$FIXTURE_AB_LOG")"
n_sess="$(grep -c $'^AB\t--session\tcolab-dev\t' "$FIXTURE_AB_LOG")"
[ "$n_calls" -gt 0 ] || note "ⓐ agent-browser 호출이 0건이다 — 순회가 돌지 않았다"
[ "$n_calls" = "$n_sess" ] || note "ⓐ′ --session colab-dev 없이 나간 agent-browser 호출이 $(( n_calls - n_sess ))건이다(전체 $n_calls) — 환경변수는 세션을 고르지 않는다"
[ "$(grep -c $'^AB\t--session\tcolab-dev\tselect\t' "$FIXTURE_AB_LOG")" -eq 0 ] || note "ⓖ″ 이미 선택된 파일을 다시 골랐다 — 설명이 비워져 보기가 영구 비활성이 된다"
[ "$(grep -c $'^AB\t--session\tcolab-dev\tfocus\t\[data-testid="dt-preview-draw"\]$' "$FIXTURE_AB_LOG")" -eq 1 ] \
  && [ "$(grep -c $'^AB\t--session\tcolab-dev\tpress\tEnter$' "$FIXTURE_AB_LOG")" -eq 1 ] \
  || note "ⓑ‴ 보기를 초점 ＋ Enter 로 정확히 한 번 누르지 않았다"
[ "$(grep -c $'^AB\t--session\tcolab-dev\tclick\t' "$FIXTURE_AB_LOG")" -eq 0 ] || note "ⓗ 보기를 좌표 클릭으로 눌렀다"

# `is enabled`가 false를 출력해도 종료 0인 CLI 계약을 true로 오인하지 않는다.
reset_run; export FIXTURE_DRAW_ENABLED=false
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "보기 버튼 false 출력을 활성 상태로 오인했다"
[ "$(grep -c $'^AB\t--session\tcolab-dev\tclick\t' "$FIXTURE_AB_LOG")" -eq 0 ] || note "보기 버튼 비활성인데 클릭했다"
unset FIXTURE_DRAW_ENABLED

# ⓗ 버튼 중심이 떠 있는 층에 덮여도 초점 ＋ Enter 로 눌러 성립하고, 적중 검사가 덮은 층을 적는다.
reset_run; export FIXTURE_COVERED=1
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -eq 0 ] || note "ⓗ 덮인 보기 단추를 초점 ＋ Enter 로 누르지 못했다(rc $rc): $(tail -1 "$STAGE_LOG")"
[ "$(verdict_of 1)" = 성립 ] || note "ⓗ′ 덮인 보기 단추 행의 판정이 「성립」이 아니다: [$(verdict_of 1)]"
case "$(note_of 1)" in *"누름 focus+Enter"*resume-drafts*) ;; *) note "ⓗ″ 판정표 비고에 누름 방법·덮은 층이 없다: [$(note_of 1)]" ;; esac
grep -q '적중 검사.*resume-drafts' "$STAGE_LOG" || note "ⓗ‴ 로그에 적중 검사(덮은 층)가 없다"
[ ! -s "$FIXTURE_AB_LOG.js-clicks" ] || note "ⓗ‴′ 초점 ＋ Enter 가 먹혔는데 JS click 을 또 냈다"

# ⓗ 초점 ＋ Enter 가 반영되지 않으면 JS click 한 번으로 폴백하고 그 방법을 적는다.
reset_run; export FIXTURE_KEYBOARD_NOOP=1
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -eq 0 ] || note "ⓗ⁗ JS click 폴백으로 성립하지 못했다(rc $rc)"
case "$(note_of 1)" in *"누름 js-click"*) ;; *) note "ⓗ⁗′ 판정표 비고에 누름 js-click 이 없다: [$(note_of 1)]" ;; esac
[ "$(cat "$FIXTURE_AB_LOG.js-clicks" 2>/dev/null | wc -l)" -eq 1 ] || note "ⓗ⁗″ JS click 폴백이 정확히 한 번이 아니다"
unset FIXTURE_KEYBOARD_NOOP

# 보기 누름이 반영되지 않으면(초점 ＋ Enter · JS click 모두 slot 이 idle 그대로) 전체 대기 없이 「클릭 미반영」으로 적는다.
reset_run; export FIXTURE_KEYBOARD_NOOP=1 FIXTURE_JS_CLICK_NOOP=1
saved_wait="$PREVIEW_WAIT_MS"; PREVIEW_WAIT_MS=5000
t_start="$(date +%s%3N)"
stage_verify >/dev/null 2>&1; rc=$?
t_took=$(( $(date +%s%3N) - t_start ))
PREVIEW_WAIT_MS="$saved_wait"
[ "$rc" -ne 0 ] || note "ⓖ‴ 반영되지 않은 보기 클릭을 성공으로 판정했다"
case "$(verdict_of 1)|$(note_of 1)" in "판정불가|클릭 미반영"*"누름 none"*resume-drafts*) ;;
  *) note "ⓖ‴′ 반영되지 않은 누름의 판정표 행이 [판정불가|클릭 미반영 · 누름 none · 적중 …] 이 아니다: [$(verdict_of 1)|$(note_of 1)]" ;; esac
grep -q '클릭 미반영' "$RUN_DIR/blocked.jsonl" 2>/dev/null || note "ⓖ‴″ 차단 사유에 「클릭 미반영」이 없다"
[ "$t_took" -lt 4000 ] || note "ⓖ‴‴ 클릭 미반영을 전체 대기(${t_took} ms)까지 기다렸다"
unset FIXTURE_KEYBOARD_NOOP FIXTURE_JS_CLICK_NOOP FIXTURE_COVERED

# 러너가 재어 둔 저장 기간·모델 입력 설명이 빠지거나 미달이면 상세 화면이 멀쩡해도 차단한다.
cp "$SEED_WORK_DIR/verify.json" "$TMP/verify-good.json"
python3 - "$SEED_WORK_DIR/verify.json" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p)); d["periods_ok"] = 0; d["periods_missing"] = [{"name": "HSR 레이더 반사도 원자료"}]
json.dump(d, open(p, "w"))
PY
reset_run
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "저장 기간 검증 미달을 성공으로 판정했다"
cp "$TMP/verify-good.json" "$SEED_WORK_DIR/verify.json"
python3 - "$SEED_WORK_DIR/verify.json" <<'PY'
import json, sys
p = sys.argv[1]; d = json.load(open(p)); d["model_input_descriptions_ok"] = 1; d["model_input_descriptions_missing"] = [{"name": "Aspect"}]
json.dump(d, open(p, "w"))
PY
reset_run
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "모델 입력 설명 검증 미달을 성공으로 판정했다"
cp "$TMP/verify-good.json" "$SEED_WORK_DIR/verify.json"

# Rendering can fail after its container appears: wait for the final slot state.
reset_run; export FIXTURE_TERMINAL=delayed-failed
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "지연 미리보기 실패를 성공으로 판정했다"
[ "$(verdict_of 1)" = 미성립 ] || note "최종 실패 상태를 기다려 미성립으로 기록하지 않았다"
reset_run; export FIXTURE_TERMINAL=drawing
cat > "$SEED_WORK_DIR/state.json" <<'JSON'
{"datasets": {"1": {"seq": 1, "name": "첫 자료", "status": "done", "dataset_id": "ID-1"},
              "2": {"seq": 2, "name": "둘째 자료", "status": "done", "dataset_id": "ID-2"}}}
JSON
cat > "$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml" <<'YAML'
datasets:
  - {seq: 1, name: "첫 자료", processing_level: Lv0, preview_expected: "미측정"}
  - {seq: 2, name: "둘째 자료", processing_level: Lv0, preview_expected: "미측정"}
YAML
cat > "$SEED_WORK_DIR/verify.json" <<'JSON'
{"dataset_count_ui": 2, "dataset_count_state": 2, "by_project": {"radar": 2}, "edges_ok": 0, "edges_missing": [], "periods_expected": 2, "periods_ok": 2, "periods_missing": [], "model_input_descriptions_ok": 2, "model_input_descriptions_missing": []}
JSON
EXPECT_DATASETS=2
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "렌더 중 상태를 성공으로 판정했다"
[ "$(verdict_of 1)" = 판정불가 ] || note "최종 상태 부재를 판정불가로 기록하지 않았다"
[ "$(grep -c $'^AB\t--session\tcolab-dev\topen\t' "$FIXTURE_AB_LOG")" -eq 1 ] || note "terminal/display 미확인 뒤 다음 자료 요청을 실행했다"
EXPECT_DATASETS=1
unset FIXTURE_TERMINAL

# 정본이 정확히 허용한 GeoPackage 두 이름의 미성립만 성공한다.
for expected_name in SPI-4weeks SPEI-4weeks; do
  cat > "$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml" <<YAML
datasets:
  - {seq: 1, name: "$expected_name", processing_level: Lv0, preview_expected: "미성립(포맷 미지원 · 판정 표에 이름으로)"}
YAML
  cat > "$SEED_WORK_DIR/state.json" <<JSON
{"datasets": {"1": {"seq": 1, "name": "$expected_name", "status": "registered_no_preview", "dataset_id": "NO-PREVIEW-ID"}}}
JSON
  cp "$TMP/verify-good.json" "$SEED_WORK_DIR/verify.json"
  reset_run; export FIXTURE_UNAVAIL=1 FIXTURE_UNSUPPORTED=1 FIXTURE_UNSUPPORTED_DELAY=1
  stage_verify >/dev/null 2>&1; rc=$?
  [ "$rc" -eq 0 ] || note "정본이 허용한 $expected_name 미리보기 미성립을 실패로 판정했다"
  case "$(note_of 1)" in *"미지원 표시 [1]"*"slot ["*) ;; *) note "ⓘ $expected_name 비고에 실제 표시(미지원 표시 · slot)가 없다: [$(note_of 1)]" ;; esac
done
unset FIXTURE_UNAVAIL FIXTURE_UNSUPPORTED FIXTURE_UNSUPPORTED_DELAY
# ⓘ′ 미지원 표시가 끝내 없으면 기대(미성립)는 그대로 두고 판정불가로 막되, 실제로 보인 것을 적는다.
reset_run
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓘ′ 미지원 표시가 없는 GeoPackage 행을 성공으로 판정했다"
case "$(note_of 1)" in "미지원 상태 미확인"*"미지원 표시 [0]"*"slot [idle]"*"보기 활성 ["*) ;;
  *) note "ⓘ″ 미지원 표시 부재 행의 비고가 실제 표시를 적지 않았다: [$(note_of 1)]" ;; esac
grep -q '미지원 표시 \[0\]' "$RUN_DIR/blocked.jsonl" 2>/dev/null || note "ⓘ‴ 차단 사유에 실제 표시(미지원 표시 [0])가 없다"

# 기대 증거가 빠지면 실제 화면이 성립이어도 fail closed다.
write_state 0
cp "$TMP/verify-good.json" "$SEED_WORK_DIR/verify.json"
cat > "$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml" <<'YAML'
datasets:
  - {seq: 1, name: "HSR 레이더 반사도 원자료", processing_level: Lv0}
YAML
reset_run
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "미리보기 기대 증거 누락을 성공으로 판정했다"

cat > "$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml" <<'YAML'
datasets:
  - {seq: 1, name: "HSR 레이더 반사도 원자료", processing_level: Lv0, preview_expected: "미측정"}
YAML
reset_run; export FIXTURE_OPEN_FAIL=1
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "페이지 이동 실패 뒤 이전 화면을 성공으로 판정했다"
[ "$(verdict_of 1)" = 판정불가 ] || note "페이지 이동 실패를 판정불가로 기록하지 않았다"
unset FIXTURE_OPEN_FAIL

# ── ⓒ 로그인 화면 → 판정불가 · 비영 ──────────────────────────────────────
write_state 0; reset_run
export FIXTURE_PAGE=login
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓒ 로그인 화면인데 stage_verify 가 0 으로 끝났다 — green-by-skip"
[ "$(verdict_of 1)" = 판정불가 ] || note "ⓒ′ 로그인 화면의 판정이 「판정불가」가 아니다: [$(verdict_of 1)]"
grep -q '로그인 화면' "$RUN_DIR/blocked.jsonl" 2>/dev/null || note "ⓒ″ 차단 사유에 「로그인 화면」이 없다"

# ── ⓓ 빈 화면 → 판정불가 · 비영 ──────────────────────────────────────────
write_state 0; reset_run
export FIXTURE_PAGE=blank
stage_verify >/dev/null 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓓ 상세 화면이 서지 않았는데 stage_verify 가 0 으로 끝났다"
[ "$(verdict_of 1)" = 판정불가 ] || note "ⓓ′ 빈 화면의 판정이 「판정불가」가 아니다: [$(verdict_of 1)]"
grep -q '상세 화면' "$RUN_DIR/blocked.jsonl" 2>/dev/null || note "ⓓ″ 차단 사유에 「상세 화면」이 없다"

# ── ⓔ id 없는 행 — 이름을 지키고 열지 않는다 ─────────────────────────────
write_state 1; reset_run
export FIXTURE_PAGE=detail
stage_verify >/dev/null 2>&1 || true
row2="$(awk -F'\t' '$1=="2" {print $2"|"$4"|"$8}' "$RUN_DIR/preview-judgment.tsv")"
[ "$row2" = "SPI-4weeks|미성립|데이터셋 id 미확보" ] || note "ⓔ id 없는 행이 [이름|판정|사유] = [$row2] 다(기대 SPI-4weeks|미성립|데이터셋 id 미확보) — 이름이 id 자리로 밀렸다"
grep -q 'datasets/SPI-4weeks' "$FIXTURE_AB_LOG" && note "ⓔ′ 이름을 id 로 알고 /datasets/SPI-4weeks 를 열었다"
unset FIXTURE_PAGE

# ── ⓕ report.py 가 `?` 계수 행(id 미확보)에서 죽지 않고 null 로 싣는다 ───────
# 왜 = 4회차 `20260914T041707Z` 의 report 가 seq 13 의 `?` 칸에서 `int('?')` ValueError 로 죽어
#   result.json 이 서지 않았다 — 「실패해도 result.json 이 선다」(preflight-red ⓙ)가 이 행에서 깨졌다.
mkdir -p "$RUN_DIR/stages"
if python3 "$RESEED_DIR/report.py" --run-dir "$RUN_DIR" --run-id "$RUN_ID" --target-sha "$TARGET_SHA" \
     --stages "preflight,verify,report," --dry-run 0 --schema "$RESEED_DIR/result-schema.json" \
     --out "$RUN_DIR/result.json" --session-out "$TMP/session.md" >"$TMP/report.out" 2>&1; then
  python3 - "$RUN_DIR/result.json" <<'PY' || note "ⓕ′ result.json 의 id 미확보 행이 [미성립 · unsetLevel null · usageCards null · note 기재] 가 아니다"
import json, sys
d = json.load(open(sys.argv[1]))
rows = {r["seq"]: r for r in d.get("previewJudgment", [])}
r = rows.get("2") or {}
ok = (r.get("verdict") == "미성립" and r.get("unsetLevel") is None and r.get("usageCards") is None
      and "id 미확보" in (r.get("note") or "") and r.get("name") == "SPI-4weeks")
ok2 = rows.get("1", {}).get("usageCards") == 1 and rows.get("1", {}).get("unsetLevel") == 0
sys.exit(0 if ok and ok2 else 1)
PY
else
  note "ⓕ report.py 가 id 미확보 행(계수 칸 ?)에서 비영 종료했다: $(grep -E 'Error|error' "$TMP/report.out" | tail -1)"
fi

# 보고서의 실행 입력은 실제 파일을 찾되, 직렬화에는 호스트 절대경로를 남기지 않는다.
python3 - "$RESEED_DIR" "$TMP" <<'PY' || note "보고서 portable 경로 계약이 어긋났다"
import json, pathlib, subprocess, sys, tempfile
tool = pathlib.Path(sys.argv[1]).resolve()
root = tool.parents[2]
with tempfile.TemporaryDirectory(dir=root, prefix='.report-path-') as inside:
    for run in (pathlib.Path(inside), pathlib.Path(sys.argv[2]) / 'outside-user' / 'run'):
        (run / 'stages').mkdir(parents=True, exist_ok=True)
        (run / 'logs').mkdir(exist_ok=True)
        (run / 'logs/seed.log').write_text('MARKER\n')
        (run / 'stages/seed.json').write_text(json.dumps({'stage':'seed', 'exitCode':7, 'log':'logs/seed.log'}))
        out = run / 'result.json'
        session = pathlib.Path(sys.argv[2]) / 'portable-session.md'
        subprocess.run([sys.executable,str(tool/'report.py'),'--run-dir',str(run),'--run-id','fixture-portable',
                        '--schema',str(tool/'result-schema.json'),'--out',str(out),'--session-out',str(session)],check=True)
        d=json.loads(out.read_text()); text=session.read_text()
        assert d['runDir'] == '.', d['runDir']
        assert str(run) not in text and str(root) not in text, text
        assert str(run) not in out.read_text(), out.read_text()
        entry=next(s for s in d['stages'] if s['stage']=='seed')
        assert (out.parent/d['runDir']/entry['log']).read_text() == 'MARKER\n'
        assert d['failedStage']=='seed' and d['outcome']=='failed'
        if run.is_relative_to(root):
            assert str(run.relative_to(root)) in text
        else:
            assert '<RUN_DIR>' in text and '--run-dir' in text
print('보고서 경로 내부/외부 2 건')
PY

if [ "$fail" -eq 0 ]; then
  echo "verify-session — green (세션 인자 · 상세 화면 성립 · 로그인 화면 판정불가 · 빈 화면 판정불가 · id 없는 행 · report ? 계수 null)"
  exit 0
fi
echo "verify-session — red" >&2
exit 1
