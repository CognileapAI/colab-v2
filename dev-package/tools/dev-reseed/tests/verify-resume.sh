#!/usr/bin/env bash
# verify 재개 픽스처 — 알려진 제품 결함 면제(`known-defects.json`)와 `--verify-from <앞 실행 자리>` 를 판정한다.
#
# 왜 있나 = 2026-09-24 재시드가 자료 28/28 을 적재하고 verify 대조에서 멈췄다 — seq 13·14(GeoPackage ·
#   #133 미지원 안내 부재)는 판정불가, seq 16(ERA5 npy · #134 경도 0–360 거절)은 미성립. 셋 다 열린 **제품** 결함이라
#   도구가 다시 돌아도 같은 판정이 나오고, verify 가 실패하면 계정 최종화(record-details → account_finalize)가 돌지 않는다.
#   사용자 요청(2026-09-25) = 「재시드에서 실패한 것만 · 전수할 필요 없다」 — reset·전수 재순회 없이 실패 행만 다시 잰다.
#
# 무엇을 증명하는가 —
#   ⓐ `--verify-from` 은 앞 판정표의 통과 행을 그대로 잇고 **실패 행만** 상세 화면을 다시 잰다(통과 행 id 는 열지 않는다).
#      다시 잰 행이 면제 조건(seq·이름·관측 판정·비고 머리·비고 필수 조각 전부)에 맞으면 실패로 세지 않고 record-details →
#      account_finalize 로 간다. 면제 건수·「seq · 이름 · 이슈」·목록 경로·sha256 이 로그·counts.json·result.json 에 선다.
#   ⓑ 면제 밖 불일치는 종전대로 실패한다 — 다시 재도 실패한 다른 행 · 로그인 화면의 13 · 「볼 수 없다」 표시로 난 16 ·
#      면제 행의 실제 가공 단계 불일치 · 면제 행의 「미지정」 · 비고 조각이 없는 9-24 모양의 16 · 빈 계수 칸의 13.
#   ⓒ 목록 파일이 없거나 · 깨졌거나 · 스키마·칸(noteContains 포함)이 틀리거나 · 이름이 등재표와 다르면 실패한다.
#      다른 목록(`KNOWN_DEFECTS_FILE`)은 픽스처 표지가 없으면 받지 않고, 받으면 결과에 fixture:<이름> 으로 남는다.
#   ⓓ 면제 행이 정상 판정으로 돌아오면 통과하고 「면제 불필요 — known-defects.json 에서 뺄 것」을 찍는다.
#   ⓕ 앞 실행 자리 거부 — 파일(판정표·계수·result.json·verify 로그) 부재 · dryRun · 대상 sha 부재·hex 아님·승인 기록과 불일치 ·
#      데이터셋 수 · 판정표 이름 · 적재 묶음(state 의 dataset_id 가 앞 verify 로그에 없음) · 이번 실행 자리와 같음. 거부면 순회 0.
#      앞·이번 대상 sha 가 다르기만 하면 거부하지 않고 주의 줄과 기록을 남긴다.
#   ⓖ 순회 경로(`--verify-from` 없음)에서도 면제 행의 차단 항목은 면제 기록으로 옮겨지고 결과가 통과한다.
#   ⓗ `reseed.sh` 는 `--verify-from` 을 `--from verify` 가 아닌 실행과 함께 받지 않고, dry-run 에서도 앞 자리를
#      preflight 전에 검사한다(없는 자리 = 종료 2 · preflight 로그 없음). dry-run 계획은 실패 행만 연다고 적는다.
#
# 실물 무접촉 = agent-browser 는 id 별 화면 모형을 내는 대역이다. 계정 최종화는 대역이다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEED_DIR="$(cd "$HERE/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin"

fail=0
note() { echo "  ✗ $1"; fail=1; }

python3 -c 'import yaml' 2>/dev/null || {
  printf '::gate-readiness-failure::gate=dev-reseed-selftest|waited_for=PyYAML|limit=-|elapsed=-|detail=cause=실행기부재 python3 yaml 모듈이 없다\n'
  exit 78
}

# ── agent-browser 대역 — 연 id 별 화면 모형 ─────────────────────────────────
#   gpkg  = GeoPackage(#133) — 보기 비활성 · slot idle · 미지원 표시 0 (13·14 기본)
#   failed = 누르면 slot failed · preview-unavailable 0 (#134 · 16 기본)
#   unavail = 누르면 slot done · preview-unavailable 1 · done = 누르면 성립 (1 기본은 done)
#   login = 로그인 화면. FIXTURE_KIND_<id> · FIXTURE_LEVEL_<id> · FIXTURE_UNSET_<id> 로 바꾼다.
cat > "$TMP/bin/agent-browser" <<'STUB'
#!/usr/bin/env bash
{ printf 'AB'; for a in "$@"; do printf '\t%s' "$a"; done; printf '\n'; } >> "$FIXTURE_AB_LOG"
[ "${1:-}" = "--session" ] && shift 2
cur="$(cat "$FIXTURE_AB_LOG.cur" 2>/dev/null)"
kind_var="FIXTURE_KIND_$cur"; level_var="FIXTURE_LEVEL_$cur"; unset_var="FIXTURE_UNSET_$cur"
case "$cur" in ID13|ID14) def=gpkg ;; ID16) def=failed ;; *) def=done ;; esac
kind="${!kind_var:-$def}"
pressed() { [ -f "$FIXTURE_AB_LOG.pressed" ]; }
case "${1:-}" in
  open) printf '%s' "${2##*/datasets/}" > "$FIXTURE_AB_LOG.cur"; rm -f "$FIXTURE_AB_LOG.pressed"; exit 0 ;;
  focus) exit 0 ;;
  press) [ "$kind" = gpkg ] || [ "$kind" = login ] || : > "$FIXTURE_AB_LOG.pressed"; exit 0 ;;
  eval)
    script="$(cat)"
    case "$script" in
      *elementFromPoint*) echo '"스크롤 전 중심 (51,288) = 보기 단추 · 스크롤 뒤 중심 (51,288) = 보기 단추"' ;;
      *'.click()'*) [ "$kind" = gpkg ] || [ "$kind" = login ] || : > "$FIXTURE_AB_LOG.pressed" ;;
    esac
    exit 0 ;;
  is) [ "$kind" = gpkg ] || [ "$kind" = login ] && echo false || echo true; exit 0 ;;
  get)
    case "${2:-} ${3:-}" in
      'value [data-testid="dt-pick-file"]') echo FILE-1 ;;
      'count [data-testid="login-submit"]') [ "$kind" = login ] && echo 1 || echo 0 ;;
      'count [data-testid="basic-info"]') [ "$kind" = login ] && echo 0 || echo 1 ;;
      'count [data-testid="dt-preview-unsupported"]') echo 0 ;;
      'count [data-testid="preview-unavailable"]') [ "$kind" = unavail ] && pressed && echo 1 || echo 0 ;;
      'attr [data-testid="dt-preview-slot"]')
        if ! pressed; then echo idle
        elif [ "$kind" = failed ]; then echo failed
        else echo done; fi ;;
      'text [data-testid="dt-preview-total"]') pressed && [ "$kind" != failed ] && echo '총 1.0초' ;;
      'text [data-testid="ig-가공 단계"]')
        [ "$kind" = login ] && exit 1
        case "$cur" in ID1) d='가공 단계 Lv0' ;; *) d='가공 단계 Lv1' ;; esac
        echo "${!level_var:-$d}" ;;
      'count [data-testid="ig-unset-가공 단계"]') echo "${!unset_var:-0}" ;;
      'count [data-testid="usage-card"]') [ "$kind" = login ] && echo 0 || echo 1 ;;
      *) echo 0 ;;
    esac
    exit 0 ;;
esac
exit 0
STUB
chmod +x "$TMP/bin/agent-browser"
export PATH="$TMP/bin:$PATH"
export FIXTURE_AB_LOG="$TMP/ab.log"
export COLAB_RESEED_PREVIEW_WAIT_MS=600 COLAB_RESEED_PREVIEW_STABLE_MS=50 COLAB_RESEED_PREVIEW_CLICK_ACK_MS=400

REPO_ROOT="$TMP/repo"; mkdir -p "$REPO_ROOT/dev-package/tools/dev-seed"
RUN_DIR="$TMP/run"; mkdir -p "$RUN_DIR/logs" "$RUN_DIR/stages"
RUN_ID=19700101T000000Z
DRY_RUN=0
DEV_URL='https://dev.invalid'
SEED_WORK_DIR="$TMP/seed-work"; mkdir -p "$SEED_WORK_DIR"
COLAB_DEV_SSH='ec2-user@<대역>'
COLAB_DEV_KEY_FILE="$TMP/no-such-key"
EXPECT_DATASETS=4; EXPECT_PROJECTS=1; EXPECT_EDGES=0
relpath() { printf '%s' "$1"; }

# shellcheck source=../lib.sh
. "$RESEED_DIR/lib.sh"
# shellcheck source=../stages.sh
. "$RESEED_DIR/stages.sh"
ACCOUNTS_WORK_DIR="$SEED_WORK_DIR/accounts"
ACCOUNTS_FILE="$TMP/approved-profile.json"
cp "$RESEED_DIR/accounts-profile.example.json" "$ACCOUNTS_FILE"; chmod 600 "$ACCOUNTS_FILE"
export COLAB_RESEED_ACCOUNTS_PROFILE="$ACCOUNTS_FILE"
TARGET_SHA=aaaaaaaaaaaa
# 계정 저장소·로그인은 test_accounts.py 가 잰다. 여기서는 「최종화까지 갔는가」만 본다.
account_finalize() { : > "$TMP/finalized"; }
REPO_KD_SHA="$(sha256sum "$RESEED_DIR/known-defects.json" | cut -d' ' -f1)"

# 등재표 — 실제 known-defects.json 의 세 행(13·14·16)과 같은 seq·이름 ＋ 면제 밖 행 하나.
MANIFEST="$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml"
cat > "$MANIFEST" <<'YAML'
datasets:
  - {seq: 1, name: "첫 자료", processing_level: Lv0, preview_expected: "미측정"}
  - {seq: 13, name: "SPI-4weeks", processing_level: Lv1, preview_expected: "미성립(포맷 미지원 · 판정 표에 이름으로)"}
  - {seq: 14, name: "SPEI-4weeks", processing_level: Lv1, preview_expected: "미성립(포맷 미지원 · 판정 표에 이름으로)"}
  - {seq: 16, name: "ERA5 변환 결과", processing_level: Lv1, preview_expected: "미판정 대상"}
YAML
write_state() { # $1 = id 머리(기본 ID)
  local p="${1:-ID}"
  cat > "$SEED_WORK_DIR/state.json" <<JSON
{"datasets": {"1": {"seq": 1, "name": "첫 자료", "status": "done", "dataset_id": "${p}1"},
              "13": {"seq": 13, "name": "SPI-4weeks", "status": "registered_no_preview", "dataset_id": "${p}13"},
              "14": {"seq": 14, "name": "SPEI-4weeks", "status": "registered_no_preview", "dataset_id": "${p}14"},
              "16": {"seq": 16, "name": "ERA5 변환 결과", "status": "done", "dataset_id": "${p}16"}}}
JSON
}
write_state
cat > "$SEED_WORK_DIR/verify.json" <<'JSON'
{"dataset_count_ui": 4, "dataset_count_state": 4, "by_project": {"p": 4}, "edges_ok": 0, "edges_missing": [], "periods_expected": 4, "periods_ok": 4, "periods_missing": [], "model_input_descriptions_ok": 2, "model_input_descriptions_missing": []}
JSON

# 2026-09-24 실행 판정표와 같은 모양(비고까지 — 16 비고에는 slot 상태가 없다).
ROW1=$'1\t첫 자료\t가공 단계 Lv0 \t성립\t3010\t0\t1\t누름 focus+Enter · 적중 = 보기 단추'
ROW1_BAD=$'1\t첫 자료\t?\t판정불가\t0\t?\t?\t미리보기 정착 미확인'
ROW13=$'13\tSPI-4weeks\t?\t판정불가\t0\t?\t?\t미지원 상태 미확인 · 미지원 표시 [0] · slot [idle] · 보기 활성 [false] · preview-unavailable [0] · 로그인 [0] · 상세 [1] · 누름 없음'
ROW14=$'14\tSPEI-4weeks\t?\t판정불가\t0\t?\t?\t미지원 상태 미확인 · 미지원 표시 [0] · slot [idle] · 보기 활성 [false] · preview-unavailable [0] · 로그인 [0] · 상세 [1] · 누름 없음'
ROW16=$'16\tERA5 변환 결과\t가공 단계 Lv1 \t미성립\t1909\t0\t1\t누름 focus+Enter · 적중 = 보기 단추'
# 이번 순회가 적는 모양(16 비고에 slot · preview-unavailable).
ROW16N=$'16\tERA5 변환 결과\t가공 단계 Lv1 \t미성립\t1909\t0\t1\t누름 focus+Enter · 적중 = 보기 단추 · slot [failed] · preview-unavailable [0]'

make_prior() { # $1 = 자리 · 나머지 = 판정표 행
  local dir="$1"; shift
  rm -rf "$dir"; mkdir -p "$dir/logs"
  printf '%s\n' "$@" > "$dir/preview-judgment.tsv"
  printf '{"datasets": {"expected": 4, "ui": 4, "state": 4}}\n' > "$dir/counts.json"
  local id
  for id in ${PRIOR_IDS-ID1 ID13 ID14 ID16}; do
    printf '2026-09-24T16:32:47Z RUN agent-browser --session colab-dev open https://dev.invalid/datasets/%s\n' "$id" >> "$dir/logs/verify.log"
  done
  python3 - "$dir" "${PRIOR_DATASETS:-4}" "${PRIOR_SHA-$TARGET_SHA}" "${PRIOR_DRY:-false}" <<'PY'
import json, sys
d, n, sha, dry = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4] == "true"
json.dump({"schema": "colab-reseed-result/1", "runId": "20260924T163059Z", "targetSha": sha, "dryRun": dry,
           "counts": {"datasets": {"expected": n}, "projects": {"expected": 1}, "edges": {"expected": 0}},
           "stages": [{"stage": "seed", "status": "ok"}, {"stage": "verify", "status": "failed"}],
           "outcome": "failed", "failedStage": "verify"}, open(d + "/result.json", "w"), ensure_ascii=False)
PY
}
reset_run() {
  rm -rf "$ACCOUNTS_WORK_DIR" "$TMP/finalized" "$RUN_DIR"; mkdir -p "$RUN_DIR/logs" "$RUN_DIR/stages"
  : > "$FIXTURE_AB_LOG"; rm -f "$FIXTURE_AB_LOG.cur" "$FIXTURE_AB_LOG.pressed"
  CURRENT_STAGE=verify; STAGE_LOG="$RUN_DIR/logs/verify.log"; : > "$STAGE_LOG"
  unset KNOWN_DEFECTS_FILE COLAB_RESEED_FIXTURE FIXTURE_KIND_ID1 FIXTURE_KIND_ID13 FIXTURE_KIND_ID16 FIXTURE_LEVEL_ID16 FIXTURE_UNSET_ID13
  write_state
}
run_verify() { stage_verify > "$TMP/out" 2>&1; }
ab_calls() { grep -c '^AB' "$FIXTURE_AB_LOG" 2>/dev/null || true; }
opened() { grep -o $'\topen\t[^\t]*' "$FIXTURE_AB_LOG" | sed 's#.*/datasets/##' | paste -sd' '; }
compare_table() { # 나머지 = 판정표 행 → verify_compare 직접
  reset_run; printf '%s\n' "$@" > "$RUN_DIR/preview-judgment.tsv"
  verify_compare "$SEED_WORK_DIR/verify.json" "$MANIFEST" > "$TMP/out" 2>&1
}

# ── ⓐ 9-24 모양 앞 판정표 — 실패 행(13·14·16)만 다시 재고, 면제 뒤 최종화까지 간다 ──────
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$TMP/prior"
run_verify; rc=$?
[ "$rc" -eq 0 ] || note "ⓐ 9-24 모양 앞 판정표로 verify 가 통과하지 못했다(rc $rc): $(grep -E '대조 결과|면제|거부|verify-from' "$TMP/out" | tail -4)"
[ "$(opened)" = "ID13 ID14 ID16" ] || note "ⓐ′ 실패 행만 열지 않았다 — 연 id [$(opened)]"
[ "$(head -1 "$RUN_DIR/preview-judgment.tsv")" = "$ROW1" ] || note "ⓐ″ 통과 행(seq 1)을 앞 판정표 그대로 잇지 않았다"
cmp -s "$TMP/prior/preview-judgment.tsv" "$RUN_DIR/prior-preview-judgment.tsv" || note "ⓐ‴ 앞 판정표를 prior-preview-judgment.tsv 로 보관하지 않았다"
awk -F'\t' '$1==13 && $3 ~ /Lv1/ && $6=="0" && $7=="1"' "$RUN_DIR/preview-judgment.tsv" | grep -q . \
  || note "ⓐ⁗ 다시 잰 13 이 읽은 가공 단계·미지정·usage 를 적지 않았다(\`?\` 로 접었다)"
grep -qF 'slot [failed] · preview-unavailable [0]' "$RUN_DIR/preview-judgment.tsv" || note "ⓐ⁵ 다시 잰 16 비고에 slot·preview-unavailable 이 없다"
[ "$(wc -l < "$RUN_DIR/preview-judgment.tsv")" -eq 4 ] || note "ⓐ⁶ 판정표가 4행이 아니다"
[ -f "$TMP/finalized" ] || note "ⓐ⁷ 면제 통과 뒤 account_finalize 로 가지 않았다"
[ -f "$ACCOUNTS_WORK_DIR/details-verified.json" ] || note "ⓐ⁸ record-details 가 돌지 않았다"
grep -q '알려진 결함 면제 3건' "$TMP/out" || note "ⓐ⁹ 면제 건수 줄이 없다"
for want in '13 · SPI-4weeks · #133' '14 · SPEI-4weeks · #133' '16 · ERA5 변환 결과 · #134'; do
  grep -qF "$want" "$TMP/out" || note "ⓐ¹⁰ 면제 줄에 「$want」가 없다"
done
grep -q 'verify-from 묶음 dataset_id ID1 ID13 ID14 ID16' "$RUN_DIR/logs/verify.log" || note "ⓐ¹¹ 다음 재개의 적재 묶음 줄이 verify 로그에 없다"
python3 - "$RUN_DIR/counts.json" "$RUN_DIR/verify-from.json" "$REPO_KD_SHA" <<'PY' || note "ⓐ¹² counts.json 면제 기록 또는 verify-from.json 출처가 어긋났다"
import json, sys
c = json.load(open(sys.argv[1])); kd = c.get("knownDefects") or {}
p = json.load(open(sys.argv[2]))
ok = (kd.get("exemptedCount") == 3 and sorted(e["seq"] for e in kd.get("exempted", [])) == ["13", "14", "16"]
      and {e["issue"] for e in kd["exempted"]} == {"#133", "#134"} and kd.get("unneeded") == []
      and kd.get("file") == "dev-package/tools/dev-reseed/known-defects.json" and kd.get("sha256") == sys.argv[3]
      and p.get("priorRunId") == "20260924T163059Z" and p.get("priorTargetSha") == "aaaaaaaaaaaa"
      and p.get("priorRunDirName") == "prior" and p.get("carriedRows") == 1
      and p.get("rewalkedSeq") == ["13", "14", "16"] and set(p.get("files", {})) == {"preview-judgment.tsv", "counts.json"})
sys.exit(0 if ok else 1)
PY
# result.json 에 면제 계수와 재개 출처가 실리고(스키마 대조 통과) 회차 기록에 재개 줄이 선다.
if python3 "$RESEED_DIR/report.py" --run-dir "$RUN_DIR" --run-id "$RUN_ID" --target-sha "$TARGET_SHA" \
     --stages "preflight,verify,report," --dry-run 1 --schema "$RESEED_DIR/result-schema.json" \
     --out "$RUN_DIR/result.json" --session-out "$TMP/session.md" > "$TMP/report.out" 2>&1; then
  python3 - "$RUN_DIR/result.json" <<'PY' || note "ⓐ¹³ result.json 에 면제 계수(counts.knownDefects) 또는 재개 출처(verifyFrom)가 없다"
import json, sys
d = json.load(open(sys.argv[1]))
ok = (d["counts"].get("knownDefects", {}).get("exemptedCount") == 3
      and (d.get("verifyFrom") or {}).get("priorRunId") == "20260924T163059Z"
      and (d.get("verifyFrom") or {}).get("rewalkedSeq") == ["13", "14", "16"])
sys.exit(0 if ok else 1)
PY
  grep -q 'verify 재개 = 앞 실행 `prior`.*실패 행 seq 13,14,16 만 다시 잼' "$TMP/session.md" || note "ⓐ¹⁴ 회차 기록에 verify 재개 출처 줄이 없다"
  grep -q '알려진 결함 면제 3건' "$TMP/session.md" || note "ⓐ¹⁵ 회차 기록에 알려진 결함 면제 건수 줄이 없다"
else
  note "ⓐ¹³ report.py 가 재개 실행 자리에서 비영 종료했다: $(tail -3 "$TMP/report.out")"
fi

# 앞 판정표의 실패 행이 다시 재서 통과하면 그대로 통과한다(실패한 것만 다시 한다).
make_prior "$TMP/prior" "$ROW1_BAD" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$TMP/prior"
run_verify; rc=$?
[ "$rc" -eq 0 ] || note "ⓐ¹⁶ 앞 판정표의 실패 행(seq 1)이 다시 재서 성립인데 통과하지 못했다: $(grep '대조 결과' "$TMP/out")"
[ "$(opened)" = "ID1 ID13 ID14 ID16" ] || note "ⓐ¹⁷ 앞 판정표 실패 행(1·13·14·16)을 다시 재지 않았다 — [$(opened)]"

# ── ⓑ 면제 밖 불일치는 종전대로 실패한다 ───────────────────────────────────
expect_fail() { # $1 = 사례 · $2 = 대조 결과에 있어야 할 문구
  run_verify; rc=$?
  [ "$rc" -ne 0 ] || note "ⓑ [$1] 을 통과시켰다"
  grep '대조 결과' "$TMP/out" | grep -qF "$2" || note "ⓑ′ [$1] 대조 결과에 「$2」가 없다: $(grep '대조 결과' "$TMP/out")"
  [ ! -f "$TMP/finalized" ] || note "ⓑ″ [$1] 실패인데 account_finalize 로 갔다"
}
make_prior "$TMP/prior" "$ROW1_BAD" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$TMP/prior"; export FIXTURE_KIND_ID1=login
expect_fail "다시 재도 로그인 화면인 seq 1" "미리보기 판정불가 seq 1"
grep '대조 결과' "$TMP/out" | grep -q 'seq [0-9,]*1[346]' && note "ⓑ‴ 면제 행(13·14·16)을 실패로 다시 셌다: $(grep '대조 결과' "$TMP/out")"
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$TMP/prior"; export FIXTURE_KIND_ID13=login
expect_fail "로그인 화면의 13(#133 이 아니다)" "미리보기 판정불가 seq 13"
reset_run; VERIFY_FROM="$TMP/prior"; export FIXTURE_KIND_ID16=unavail
expect_fail "「볼 수 없다」 표시로 난 16(#134 가 아니다)" "예상 밖 미리보기 미성립 seq 16"
reset_run; VERIFY_FROM="$TMP/prior"; export FIXTURE_LEVEL_ID16="가공 단계 Lv0"
expect_fail "면제 행 16 의 실제 가공 단계 불일치" "가공 단계 불일치 seq 16"
reset_run; VERIFY_FROM="$TMP/prior"; export FIXTURE_UNSET_ID13=2
expect_fail "면제 행 13 의 「미지정」" "「미지정」 seq 13"
unset VERIFY_FROM
# 9-24 모양의 16(비고에 slot 조각 없음)은 대조에서 면제되지 않는다 — slot failed 인지 판정표로 알 수 없다.
compare_table "$ROW1" "$ROW13" "$ROW14" "$ROW16"; rc=$?
[ "$rc" -ne 0 ] || note "ⓑ⁴ slot 조각 없는 16 을 면제했다"
grep -q '예상 밖 미리보기 미성립 seq 16' "$TMP/out" || note "ⓑ⁴′ slot 조각 없는 16 을 「예상 밖 미성립」으로 내지 않았다"
# 파생 면제는 정확히 `?` 칸만 — 빈 계수 칸은 다른 실패다.
compare_table "$ROW1" $'13\tSPI-4weeks\t?\t판정불가\t0\t\t?\t미지원 상태 미확인 · 미지원 표시 [0] · slot [idle] · 보기 활성 [false] · preview-unavailable [0] · 로그인 [0] · 상세 [1] · 누름 없음' "$ROW14" "$ROW16N"; rc=$?
[ "$rc" -ne 0 ] || note "ⓑ⁵ 면제 행 13 의 빈 계수 칸을 파생으로 면제했다"
grep -q '계수 판정불가 seq 13' "$TMP/out" || note "ⓑ⁵′ 빈 계수 칸을 「계수 판정불가 seq 13」으로 내지 않았다"
compare_table "$ROW1" "$ROW13" "$ROW14" "$ROW16N"; rc=$?
[ "$rc" -eq 0 ] || note "ⓑ⁶ \`?\` 만 적힌 면제 행 13·14 의 파생을 면제하지 않았다: $(grep '대조 결과' "$TMP/out")"

# ── ⓒ 목록 파일 fail-closed ─────────────────────────────────────────────────
bad_kd() { # $1 = 사례 이름 · $2 = 파일 내용(없으면 파일 부재)
  compare_table "$ROW1" "$ROW13" "$ROW14" "$ROW16N"
  COLAB_RESEED_FIXTURE=1; KNOWN_DEFECTS_FILE="$TMP/kd-$1.json"
  [ -n "${2:-}" ] && printf '%s' "$2" > "$KNOWN_DEFECTS_FILE"
  verify_compare "$SEED_WORK_DIR/verify.json" "$MANIFEST" > "$TMP/out" 2>&1; rc=$?
  [ "$rc" -ne 0 ] || note "ⓒ 면제 목록 [$1] 을 받아들이고 통과했다"
  grep -q '면제 목록' "$TMP/out" || note "ⓒ′ 면제 목록 [$1] 거부 사유를 찍지 않았다"
  unset COLAB_RESEED_FIXTURE KNOWN_DEFECTS_FILE
}
NC13='["미지원 표시 [0]", "로그인 [0]", "상세 [1]"]'
entry() { printf '{"seq": %s, "name": "%s", "issue": "%s", "expectedVerdict": "%s", "notePrefix": "%s", "noteContains": %s, "reason": "사유", "approved": "확인 대기"}' "$@"; }
kd_of() { printf '{"schema": "colab-reseed-known-defects/1", "entries": [%s]}' "$1"; }
bad_kd missing ""
bad_kd broken '{"schema": "colab-reseed-known-defects/1", "entries": ['
bad_kd schema '{"schema": "other/1", "entries": []}'
bad_kd no-entries '{"schema": "colab-reseed-known-defects/1"}'
bad_kd issue "$(kd_of "$(entry 13 SPI-4weeks 133 판정불가 '미지원 상태 미확인' "$NC13")")"
bad_kd verdict "$(kd_of "$(entry 13 SPI-4weeks '#133' 성립 '미지원 상태 미확인' "$NC13")")"
bad_kd name "$(kd_of "$(entry 13 SPI-8weeks '#133' 판정불가 '미지원 상태 미확인' "$NC13")")"
bad_kd absent-seq "$(kd_of "$(entry 99 SPI-4weeks '#133' 판정불가 '미지원 상태 미확인' "$NC13")")"
bad_kd no-note-contains "$(kd_of "$(entry 13 SPI-4weeks '#133' 판정불가 '미지원 상태 미확인' '[]')")"
bad_kd note-contains-str "$(kd_of "$(entry 13 SPI-4weeks '#133' 판정불가 '미지원 상태 미확인' '"로그인 [0]"')")"
bad_kd no-approval '{"schema": "colab-reseed-known-defects/1", "entries": [{"seq": 13, "name": "SPI-4weeks", "issue": "#133", "expectedVerdict": "판정불가", "notePrefix": "미지원 상태 미확인", "noteContains": ["로그인 [0]"], "reason": "사유"}]}'
bad_kd duplicate "$(kd_of "$(entry 13 SPI-4weeks '#133' 판정불가 '미지원 상태 미확인' "$NC13"), $(entry 13 SPI-4weeks '#133' 판정불가 '미지원 상태 미확인' "$NC13")")"
# 다른 목록은 픽스처 표지가 없으면 받지 않는다(승인 목록 밖 면제가 흔적 없이 들어오지 않게).
compare_table "$ROW1_BAD" "$ROW13" "$ROW14" "$ROW16N"
KNOWN_DEFECTS_FILE="$TMP/kd-extra.json"
python3 - "$RESEED_DIR/known-defects.json" "$KNOWN_DEFECTS_FILE" <<'PY'
import json, sys
kd = json.load(open(sys.argv[1], encoding="utf-8"))
kd["entries"].append({"seq": 1, "name": "첫 자료", "issue": "#1", "expectedVerdict": "판정불가", "notePrefix": "미리보기 정착 미확인",
                      "noteContains": ["정착"], "reason": "사유", "approved": "확인 대기"})
json.dump(kd, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
PY
verify_compare "$SEED_WORK_DIR/verify.json" "$MANIFEST" > "$TMP/out" 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓒ″ 픽스처 표지 없이 KNOWN_DEFECTS_FILE 목록을 받았다"
grep -q 'KNOWN_DEFECTS_FILE 은 픽스처' "$TMP/out" || note "ⓒ‴ KNOWN_DEFECTS_FILE 거부 사유를 찍지 않았다"
# 픽스처 표지가 있으면 받되, 결과에 레포 목록이 아니라는 것(fixture:<이름>)과 sha256 이 남는다.
COLAB_RESEED_FIXTURE=1
verify_compare "$SEED_WORK_DIR/verify.json" "$MANIFEST" > "$TMP/out" 2>&1; rc=$?
[ "$rc" -eq 0 ] || note "ⓒ⁗ 픽스처 목록(seq 1 면제)으로 대조가 통과하지 못했다: $(grep '대조 결과' "$TMP/out")"
python3 -c 'import json,sys; k=json.load(open(sys.argv[1]))["knownDefects"]; sys.exit(0 if k["file"]=="fixture:kd-extra.json" and len(k["sha256"])==64 else 1)' \
  "$RUN_DIR/counts.json" || note "ⓒ⁵ 픽스처 목록이 결과에 fixture:<이름> · sha256 으로 남지 않았다"
unset COLAB_RESEED_FIXTURE KNOWN_DEFECTS_FILE

# ── ⓓ 결함이 고쳐져 정상 판정이면 통과 ＋ 「면제 불필요」 ────────────────────
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$TMP/prior"; export FIXTURE_KIND_ID16=done
run_verify; rc=$?
[ "$rc" -eq 0 ] || note "ⓓ 면제 행이 정상 판정(성립)인데 통과하지 못했다: $(grep '대조 결과' "$TMP/out")"
grep -q '면제 불필요 — 16 · ERA5 변환 결과 · #134 — known-defects.json 에서 뺄 것' "$TMP/out" || note "ⓓ′ 「면제 불필요 … known-defects.json 에서 뺄 것」을 찍지 않았다"
grep -q '알려진 결함 면제 2건' "$TMP/out" || note "ⓓ″ 남은 면제 건수가 2건이 아니다"

# ── ⓕ 앞 실행 자리 거부 ────────────────────────────────────────────────────
refuse_prior() { # $1 = 사례 · $2 = 거부 문구 일부
  reset_run; VERIFY_FROM="$TMP/prior"
  [ -z "${3:-}" ] || write_state "$3"
  run_verify; rc=$?
  [ "$rc" -ne 0 ] || note "ⓕ 앞 실행 자리 [$1] 을 받아들였다"
  grep -q "$2" "$TMP/out" || note "ⓕ′ 앞 실행 자리 [$1] 거부 사유에 「$2」가 없다: $(tail -2 "$TMP/out")"
  [ "$(ab_calls)" = 0 ] || note "ⓕ″ 앞 실행 자리 [$1] 거부 뒤 순회를 돌았다"
  [ ! -f "$TMP/finalized" ] || note "ⓕ‴ 앞 실행 자리 [$1] 거부인데 최종화로 갔다"
  [ ! -f "$RUN_DIR/preview-judgment.tsv" ] || note "ⓕ⁗ 앞 실행 자리 [$1] 거부인데 판정표를 옮겼다"
}
for missing in preview-judgment.tsv counts.json result.json logs/verify.log; do
  make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"; rm -f "$TMP/prior/$missing"
  refuse_prior "no-$missing" "$missing"
done
PRIOR_DATASETS=28 make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
refuse_prior datasets-28 '데이터셋 기대'
PRIOR_SHA="" make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
refuse_prior no-sha '대상 sha 가 없다'
PRIOR_SHA="<대상 sha · preflight 가 해석>" make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
refuse_prior placeholder-sha 'hex 12/40자가 아니다'
PRIOR_DRY=true make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
refuse_prior dry-run '실제 실행이 아니다'
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
printf '{"targetSha": "cccccccccccc"}\n' > "$TMP/prior/approval-record.json"
refuse_prior approval-sha '승인 기록 대상 sha'
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" $'16\t다른 이름\t가공 단계 Lv1 \t미성립\t1909\t0\t1\t누름 x'
refuse_prior other-names '판정표'
# 같은 seq·이름이어도 dataset_id 가 앞 verify 로그에 없으면 다른 적재를 잰 판정표다.
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
refuse_prior other-load 'verify 로그에 없다' OTHER
PRIOR_IDS="ID1 ID13 ID14" make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
refuse_prior one-id-unbound 'seq 16'
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$RUN_DIR"
run_verify; rc=$?
[ "$rc" -ne 0 ] || note "ⓕ⁵ 앞 실행 자리가 이번 실행 자리와 같은데 받아들였다"
# 앞 실행 뒤 dev 가 재배포돼 대상 sha 가 달라도 거부하지 않는다 — 주의 줄과 기록(targetShaMatches false)을 남긴다.
PRIOR_SHA=bbbbbbbbbbbb make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$TMP/prior"
run_verify; rc=$?
[ "$rc" -eq 0 ] || note "ⓕ⁶ 앞·이번 대상 sha 가 다르다는 이유로 거부했다(rc $rc)"
grep -q 'verify-from 주의 — 이은 행은 대상 sha bbbbbbbbbbbb 에서 잰 것' "$TMP/out" || note "ⓕ⁶′ 대상 sha 차이 주의 줄이 없다"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d["targetShaMatches"] is False and d["targetSha"]=="aaaaaaaaaaaa" else 1)' \
  "$RUN_DIR/verify-from.json" || note "ⓕ⁶″ verify-from.json 에 targetShaMatches false 가 없다"
unset VERIFY_FROM

# ── ⓖ 순회 경로의 면제 — 차단 항목을 면제 기록으로 옮긴다 ──────────────────
reset_run
printf '%s\n' "$ROW1" "$ROW13" "$ROW14" "$ROW16N" > "$RUN_DIR/preview-judgment.tsv"
CURRENT_STAGE=verify
blocked_add verify "seq=13 SPI-4weeks — 승인된 미지원 표시를 확인하지 못했다 · 미지원 표시 [0]"
blocked_add verify "seq=14 SPEI-4weeks — 승인된 미지원 표시를 확인하지 못했다 · 미지원 표시 [0]"
blocked_add verify "seq=16 ERA5 변환 결과 — 미리보기 최종 상태가 failed다"
verify_compare "$SEED_WORK_DIR/verify.json" "$MANIFEST" > "$TMP/out" 2>&1; rc=$?
[ "$rc" -eq 0 ] || note "ⓖ 순회 경로의 면제 행 셋을 통과시키지 못했다: $(grep '대조 결과' "$TMP/out")"
[ ! -s "$RUN_DIR/blocked.jsonl" ] || note "ⓖ′ 면제 행의 차단 항목이 blocked.jsonl 에 남았다(결과가 failed 로 선다): $(cat "$RUN_DIR/blocked.jsonl")"
python3 - "$RUN_DIR/counts.json" <<'PY' || note "ⓖ″ 옮긴 차단 항목이 면제 기록(counts.knownDefects.exempted[].blocked)에 없다"
import json, sys
kd = json.load(open(sys.argv[1]))["knownDefects"]
sys.exit(0 if sum(len(e.get("blocked", [])) for e in kd["exempted"]) == 3 else 1)
PY
# 면제 밖 행의 차단 항목은 남는다.
reset_run
printf '%s\n' "$ROW1_BAD" "$ROW13" "$ROW14" "$ROW16N" > "$RUN_DIR/preview-judgment.tsv"
CURRENT_STAGE=verify
blocked_add verify "seq=1 첫 자료 — 보기 전 정착 미확인"
blocked_add verify "seq=13 SPI-4weeks — 승인된 미지원 표시를 확인하지 못했다"
verify_compare "$SEED_WORK_DIR/verify.json" "$MANIFEST" > "$TMP/out" 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓖ‴ 면제 밖 판정불가가 있는데 대조가 통과했다"
grep -q 'seq=1 첫 자료' "$RUN_DIR/blocked.jsonl" 2>/dev/null || note "ⓖ⁗ 면제 밖 행의 차단 항목이 사라졌다"

# ── ⓗ reseed.sh 인자 — --verify-from 은 --from verify 로만 · dry-run 도 앞 자리를 검사 ──
export COLAB_RESEED_ACCOUNTS_PROFILE="$ACCOUNTS_FILE"
for from in seed preflight deploy; do
  args=(--dry-run --run-dir "$TMP/dry-$from" --accounts-file "$ACCOUNTS_FILE" --verify-from "$TMP/prior")
  [ "$from" = preflight ] || args+=(--from "$from")
  bash "$RESEED_DIR/reseed.sh" "${args[@]}" > "$TMP/cli.out" 2>&1; rc=$?
  [ "$rc" -eq 2 ] || note "ⓗ --verify-from 을 --from $from 과 함께 받았다(rc $rc)"
  grep -q 'verify-from' "$TMP/cli.out" || note "ⓗ′ --from $from 거부 사유에 verify-from 이 없다"
done
COLAB_RESEED_VERIFY_FROM="$TMP/prior" bash "$RESEED_DIR/reseed.sh" --dry-run --run-dir "$TMP/dry-env" \
  --accounts-file "$ACCOUNTS_FILE" --from seed > "$TMP/cli.out" 2>&1; rc=$?
[ "$rc" -eq 2 ] || note "ⓗ″ COLAB_RESEED_VERIFY_FROM 을 --from seed 와 함께 받았다(rc $rc)"
bash "$RESEED_DIR/reseed.sh" --dry-run --preflight-only --run-dir "$TMP/dry-po" \
  --accounts-file "$ACCOUNTS_FILE" --verify-from "$TMP/prior" > "$TMP/cli.out" 2>&1; rc=$?
[ "$rc" -eq 2 ] || note "ⓗ‴ --verify-from 을 --preflight-only 와 함께 받았다(rc $rc)"
# dry-run 도 앞 자리를 preflight 전에 검사한다 — 없는 자리는 종료 2 · preflight 로그 없음.
export COLAB_SEED_WORK_DIR="$SEED_WORK_DIR" COLAB_RESEED_EXPECT_DATASETS=4 COLAB_RESEED_EXPECT_PROJECTS=1 COLAB_RESEED_EXPECT_EDGES=0
bash "$RESEED_DIR/reseed.sh" --dry-run --run-dir "$TMP/dry-missing" --accounts-file "$ACCOUNTS_FILE" \
  --from verify --verify-from "$TMP/no-such-run" > "$TMP/cli.out" 2>&1; rc=$?
[ "$rc" -eq 2 ] || note "ⓗ⁗ 없는 --verify-from 자리로 dry-run 이 종료 2 로 멈추지 않았다(rc $rc)"
grep -q 'verify-from 거부 — 앞 실행 자리가 없다' "$TMP/cli.out" || note "ⓗ⁗′ 없는 자리 거부 사유를 찍지 않았다: $(tail -2 "$TMP/cli.out")"
[ ! -e "$TMP/dry-missing/logs/preflight.log" ] || note "ⓗ⁗″ 거부 전에 preflight 가 돌았다"
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
bash "$RESEED_DIR/reseed.sh" --dry-run --run-dir "$TMP/dry-ok" --accounts-file "$ACCOUNTS_FILE" \
  --from verify --verify-from "$TMP/prior" > "$TMP/cli.out" 2>&1; rc=$?
[ "$rc" -eq 0 ] || note "ⓗ⁵ --from verify --verify-from --dry-run 이 비영으로 끝났다(rc $rc): $(tail -2 "$TMP/cli.out")"
grep -q 'DRY verify-from' "$TMP/dry-ok/logs/verify.log" 2>/dev/null || note "ⓗ⁶ dry-run verify 로그에 verify-from 재개 줄이 없다"
grep -q 'DRY agent-browser open /datasets/<id> — 앞 판정표 실패 행만 seq' "$TMP/dry-ok/logs/verify.log" 2>/dev/null \
  || note "ⓗ⁷ dry-run 계획이 실패 행만 연다고 적지 않았다"
grep -q '×' "$TMP/dry-ok/logs/verify.log" 2>/dev/null && note "ⓗ⁸ dry-run 계획이 전수 순회(×N)를 적었다"
unset COLAB_SEED_WORK_DIR COLAB_RESEED_EXPECT_DATASETS COLAB_RESEED_EXPECT_PROJECTS COLAB_RESEED_EXPECT_EDGES

[ "$fail" = 0 ] && echo "verify-resume — 실패 행만 재측정·면제 통과·면제 밖 실패·목록 fail-closed·면제 불필요·앞 자리 거부(적재 묶음·dryRun·sha)·차단 이관·인자 거부·dry-run 사전 검사"
exit "$fail"
