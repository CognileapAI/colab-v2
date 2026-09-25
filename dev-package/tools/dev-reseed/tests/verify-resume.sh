#!/usr/bin/env bash
# verify 재개 픽스처 — 알려진 제품 결함 면제(`known-defects.json`)와 `--verify-from <앞 실행 자리>` 를 판정한다.
#
# 왜 있나 = 2026-09-24 재시드가 자료 28/28 을 적재하고 verify 대조에서 멈췄다 — seq 13·14(GeoPackage ·
#   #133 미지원 안내 부재)는 판정불가, seq 16(ERA5 npy · #134 경도 0–360 거절)은 미성립. 셋 다 열린 **제품** 결함이라
#   도구가 다시 돌아도 같은 판정이 나오고, verify 가 실패하면 계정 최종화(record-details → account_finalize)가 돌지 않는다.
#   사용자 결정(2026-09-25) = reset·전수 재순회 없이 **실패한 꼬리만** 마친다.
#
# 무엇을 증명하는가 —
#   ⓐ 면제 행(seq·이름·관측 판정·비고 머리 일치)은 실패로 세지 않는다 — 그 행에서만 나온 파생(계수·가공 단계 판정불가 ·
#      가공 단계 불일치)도 같다. 면제 건수와 「seq · 이름 · 이슈」를 찍고 counts.json 에 싣는다.
#   ⓑ 면제 행 밖의 불일치는 종전대로 실패한다 — 다른 행의 판정불가 · 면제 행의 다른 비고 · 면제 행의 실제 가공 단계 불일치.
#   ⓒ 목록 파일이 없거나 · JSON 이 깨졌거나 · 스키마·칸이 틀리거나 · 이름이 등재표와 다르면 실패한다(빈 목록으로 접지 않는다).
#   ⓓ 면제 행이 정상 판정으로 돌아오면 통과하고 「면제 불필요 — known-defects.json 에서 뺄 것」을 찍는다.
#   ⓔ `--verify-from` 은 상세 화면 순회를 건너뛰고(agent-browser 호출 0) 앞 실행의 판정표·계수를 그대로 옮겨 대조한 뒤
#      record-details → account_finalize 로 간다. 출처(앞 실행 자리 이름 · runId · 대상 sha)를 verify-from.json 에 남긴다.
#   ⓕ 앞 실행 자리에 판정표·계수·result.json 이 없거나, 데이터셋 수·판정표 이름이 지금과 다르거나, 대상 sha 가 없거나
#      승인 기록과 어긋나면 거부한다. 앞·이번 대상 sha 가 다르기만 하면 거부하지 않고 주의 줄과 기록을 남긴다.
#   ⓖ 순회 경로(`--verify-from` 없음)에서도 면제 행의 차단 항목은 면제 기록으로 옮겨지고 결과가 통과한다.
#   ⓗ `reseed.sh` 는 `--verify-from` 을 `--from verify` 가 아닌 실행과 함께 받지 않는다.
#
# 실물 무접촉 = agent-browser 는 호출되면 기록만 하고 실패하는 대역이다. 계정 최종화는 대역이다.
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

cat > "$TMP/bin/agent-browser" <<'STUB'
#!/usr/bin/env bash
{ printf 'AB'; for a in "$@"; do printf '\t%s' "$a"; done; printf '\n'; } >> "$FIXTURE_AB_LOG"
exit 1
STUB
chmod +x "$TMP/bin/agent-browser"
export PATH="$TMP/bin:$PATH"
export FIXTURE_AB_LOG="$TMP/ab.log"

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

# 등재표 — 실제 known-defects.json 의 세 행(13·14·16)과 같은 seq·이름 ＋ 면제 밖 행 하나.
cat > "$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml" <<'YAML'
datasets:
  - {seq: 1, name: "첫 자료", processing_level: Lv0, preview_expected: "미측정"}
  - {seq: 13, name: "SPI-4weeks", processing_level: Lv1, preview_expected: "미성립(포맷 미지원 · 판정 표에 이름으로)"}
  - {seq: 14, name: "SPEI-4weeks", processing_level: Lv1, preview_expected: "미성립(포맷 미지원 · 판정 표에 이름으로)"}
  - {seq: 16, name: "ERA5 변환 결과", processing_level: Lv1, preview_expected: "미판정 대상"}
YAML
cat > "$SEED_WORK_DIR/state.json" <<'JSON'
{"datasets": {"1": {"seq": 1, "name": "첫 자료", "status": "done", "dataset_id": "ID-1"},
              "13": {"seq": 13, "name": "SPI-4weeks", "status": "registered_no_preview", "dataset_id": "ID-13"},
              "14": {"seq": 14, "name": "SPEI-4weeks", "status": "registered_no_preview", "dataset_id": "ID-14"},
              "16": {"seq": 16, "name": "ERA5 변환 결과", "status": "done", "dataset_id": "ID-16"}}}
JSON
cat > "$SEED_WORK_DIR/verify.json" <<'JSON'
{"dataset_count_ui": 4, "dataset_count_state": 4, "by_project": {"p": 4}, "edges_ok": 0, "edges_missing": [], "periods_expected": 4, "periods_ok": 4, "periods_missing": [], "model_input_descriptions_ok": 2, "model_input_descriptions_missing": []}
JSON

# 2026-09-24 실행의 판정표와 같은 모양(비고 머리까지).
ROW1=$'1\t첫 자료\t가공 단계 Lv0 \t성립\t3010\t0\t1\t누름 focus+Enter · 적중 = 보기 단추'
ROW13=$'13\tSPI-4weeks\t?\t판정불가\t0\t?\t?\t미지원 상태 미확인 · 미지원 표시 [0] · slot [idle] · 보기 활성 [false] · 누름 없음'
ROW14=$'14\tSPEI-4weeks\t?\t판정불가\t0\t?\t?\t미지원 상태 미확인 · 미지원 표시 [0] · slot [idle] · 보기 활성 [false] · 누름 없음'
ROW16=$'16\tERA5 변환 결과\t가공 단계 Lv1 \t미성립\t1909\t0\t1\t누름 focus+Enter · 적중 = 보기 단추'

make_prior() { # $1 = 자리 · 나머지 = 판정표 행
  local dir="$1"; shift
  rm -rf "$dir"; mkdir -p "$dir"
  printf '%s\n' "$@" > "$dir/preview-judgment.tsv"
  printf '{"datasets": {"expected": 4, "ui": 4, "state": 4}}\n' > "$dir/counts.json"
  python3 - "$dir" "${PRIOR_DATASETS:-4}" "${PRIOR_SHA-$TARGET_SHA}" <<'PY'
import json, sys
d, n, sha = sys.argv[1], int(sys.argv[2]), sys.argv[3]
json.dump({"schema": "colab-reseed-result/1", "runId": "20260924T163059Z", "targetSha": sha,
           "counts": {"datasets": {"expected": n}, "projects": {"expected": 1}, "edges": {"expected": 0}},
           "stages": [{"stage": "seed", "status": "ok"}, {"stage": "verify", "status": "failed"}],
           "outcome": "failed", "failedStage": "verify"}, open(d + "/result.json", "w"), ensure_ascii=False)
PY
}
reset_run() {
  rm -rf "$ACCOUNTS_WORK_DIR" "$TMP/finalized" "$RUN_DIR"; mkdir -p "$RUN_DIR/logs" "$RUN_DIR/stages"
  : > "$FIXTURE_AB_LOG"; CURRENT_STAGE=verify; STAGE_LOG="$RUN_DIR/logs/verify.log"; : > "$STAGE_LOG"
  unset KNOWN_DEFECTS_FILE
}
run_verify() { stage_verify > "$TMP/out" 2>&1; }
ab_calls() { grep -c '^AB' "$FIXTURE_AB_LOG" 2>/dev/null || true; }

# ── ⓐ·ⓔ 면제 행 셋 ＋ 정상 행 — 순회 없이 통과하고 최종화까지 간다 ─────────
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$TMP/prior"
run_verify; rc=$?
[ "$rc" -eq 0 ] || note "ⓐ 면제 행 셋이 있는 앞 판정표로 verify 가 통과하지 못했다(rc $rc): $(grep -E '대조 결과|면제|거부|verify-from' "$TMP/out" | tail -3)"
[ "$(ab_calls)" = 0 ] || note "ⓔ --verify-from 인데 상세 화면 순회(agent-browser)를 불렀다 — $(ab_calls)건"
cmp -s "$TMP/prior/preview-judgment.tsv" "$RUN_DIR/preview-judgment.tsv" || note "ⓔ′ 앞 판정표를 실행 자리로 그대로 옮기지 않았다"
[ -f "$TMP/finalized" ] || note "ⓔ″ 면제 통과 뒤 account_finalize 로 가지 않았다"
[ -f "$ACCOUNTS_WORK_DIR/details-verified.json" ] || note "ⓔ‴ record-details 가 돌지 않았다"
grep -q '알려진 결함 면제 3건' "$TMP/out" || note "ⓐ′ 면제 건수 줄이 없다"
for want in '13 · SPI-4weeks · #133' '14 · SPEI-4weeks · #133' '16 · ERA5 변환 결과 · #134'; do
  grep -qF "$want" "$TMP/out" || note "ⓐ″ 면제 줄에 「$want」가 없다"
done
python3 - "$RUN_DIR/counts.json" "$RUN_DIR/verify-from.json" <<'PY' || note "ⓐ‴ counts.json 면제 기록 또는 verify-from.json 출처가 어긋났다"
import json, sys
c = json.load(open(sys.argv[1])); kd = c.get("knownDefects") or {}
p = json.load(open(sys.argv[2]))
ok = (kd.get("exemptedCount") == 3 and sorted(e["seq"] for e in kd.get("exempted", [])) == ["13", "14", "16"]
      and {e["issue"] for e in kd["exempted"]} == {"#133", "#134"} and kd.get("unneeded") == []
      and p.get("priorRunId") == "20260924T163059Z" and p.get("priorTargetSha") == "aaaaaaaaaaaa"
      and p.get("priorRunDirName") == "prior" and "/" not in json.dumps(p.get("priorRunDirName"))
      and set(p.get("files", {})) == {"preview-judgment.tsv", "counts.json"})
sys.exit(0 if ok else 1)
PY
# result.json 에 면제 계수와 재개 출처가 실리고(스키마 대조 통과) 회차 기록에 재개 줄이 선다.
if python3 "$RESEED_DIR/report.py" --run-dir "$RUN_DIR" --run-id "$RUN_ID" --target-sha "$TARGET_SHA" \
     --stages "preflight,verify,report," --dry-run 1 --schema "$RESEED_DIR/result-schema.json" \
     --out "$RUN_DIR/result.json" --session-out "$TMP/session.md" > "$TMP/report.out" 2>&1; then
  python3 - "$RUN_DIR/result.json" <<'PY' || note "ⓐ⁗ result.json 에 면제 계수(counts.knownDefects) 또는 재개 출처(verifyFrom)가 없다"
import json, sys
d = json.load(open(sys.argv[1]))
ok = (d["counts"].get("knownDefects", {}).get("exemptedCount") == 3
      and (d.get("verifyFrom") or {}).get("priorRunId") == "20260924T163059Z")
sys.exit(0 if ok else 1)
PY
  grep -q 'verify 재개 = 앞 실행 `prior`' "$TMP/session.md" || note "ⓐ⁵ 회차 기록에 verify 재개 출처 줄이 없다"
  grep -q '알려진 결함 면제 3건' "$TMP/session.md" || note "ⓐ⁶ 회차 기록에 알려진 결함 면제 건수 줄이 없다"
else
  note "ⓐ⁗ report.py 가 재개 실행 자리에서 비영 종료했다: $(tail -3 "$TMP/report.out")"
fi

# ── ⓑ 면제 밖 불일치는 종전대로 실패한다 ───────────────────────────────────
ROW1_BAD=$'1\t첫 자료\t?\t판정불가\t0\t?\t?\t미리보기 정착 미확인'
make_prior "$TMP/prior" "$ROW1_BAD" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$TMP/prior"
run_verify; rc=$?
[ "$rc" -ne 0 ] || note "ⓑ 면제 밖 행(seq 1)의 판정불가를 통과시켰다"
grep -q '미리보기 판정불가 seq 1$\|미리보기 판정불가 seq 1 ' "$TMP/out" || note "ⓑ′ 대조 결과가 seq 1 판정불가를 이름으로 내지 않았다: $(grep '대조 결과' "$TMP/out")"
grep '대조 결과' "$TMP/out" | grep -q 'seq [0-9,]*1[34]' && note "ⓑ″ 면제 행(13·14)을 실패로 다시 셌다: $(grep '대조 결과' "$TMP/out")"
[ ! -f "$TMP/finalized" ] || note "ⓑ‴ 실패인데 account_finalize 로 갔다"

# 면제 행이라도 비고 머리가 다르면(다른 원인) 면제하지 않는다.
ROW16_OTHER=$'16\tERA5 변환 결과\t?\t미성립\t0\t?\t?\t데이터셋 id 미확보'
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16_OTHER"
reset_run; VERIFY_FROM="$TMP/prior"
run_verify; rc=$?
[ "$rc" -ne 0 ] || note "ⓑ⁗ seq 16 의 다른 원인(데이터셋 id 미확보) 미성립을 면제했다"
grep -q '예상 밖 미리보기 미성립 seq 16' "$TMP/out" || note "ⓑ⁗′ 다른 원인의 seq 16 을 「예상 밖 미성립」으로 내지 않았다"

# 면제 행의 **실제로 읽은** 가공 단계가 어긋나면 파생이 아니라 다른 실패다.
ROW16_LV=$'16\tERA5 변환 결과\t가공 단계 Lv0 \t미성립\t1909\t0\t1\t누름 focus+Enter · 적중 = 보기 단추'
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16_LV"
reset_run; VERIFY_FROM="$TMP/prior"
run_verify; rc=$?
[ "$rc" -ne 0 ] || note "ⓑ⁵ 면제 행의 실제 가공 단계 불일치를 통과시켰다"
grep -q '가공 단계 불일치 seq 16' "$TMP/out" || note "ⓑ⁵′ 면제 행의 실제 가공 단계 불일치를 이름으로 내지 않았다"

# ── ⓒ 목록 파일 fail-closed ─────────────────────────────────────────────────
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
bad_kd() { # $1 = 사례 이름 · $2 = 파일 내용(없으면 파일 부재)
  reset_run; VERIFY_FROM="$TMP/prior"; KNOWN_DEFECTS_FILE="$TMP/kd-$1.json"
  [ -n "${2:-}" ] && printf '%s' "$2" > "$KNOWN_DEFECTS_FILE"
  run_verify; rc=$?
  [ "$rc" -ne 0 ] || note "ⓒ 면제 목록 [$1] 을 받아들이고 통과했다"
  grep -q '면제 목록' "$TMP/out" || note "ⓒ′ 면제 목록 [$1] 거부 사유를 찍지 않았다"
  [ ! -f "$TMP/finalized" ] || note "ⓒ″ 면제 목록 [$1] 인데 최종화로 갔다"
}
bad_kd missing ""
bad_kd broken '{"schema": "colab-reseed-known-defects/1", "entries": ['
bad_kd schema '{"schema": "other/1", "entries": []}'
bad_kd no-entries '{"schema": "colab-reseed-known-defects/1"}'
entry() { printf '{"seq": %s, "name": "%s", "issue": "%s", "expectedVerdict": "%s", "notePrefix": "%s", "reason": "사유", "approved": "사용자 2026-09-25"}' "$@"; }
bad_kd issue "{\"schema\": \"colab-reseed-known-defects/1\", \"entries\": [$(entry 13 SPI-4weeks 133 판정불가 '미지원 상태 미확인')]}"
bad_kd verdict "{\"schema\": \"colab-reseed-known-defects/1\", \"entries\": [$(entry 13 SPI-4weeks '#133' 성립 '미지원 상태 미확인')]}"
bad_kd name "{\"schema\": \"colab-reseed-known-defects/1\", \"entries\": [$(entry 13 SPI-8weeks '#133' 판정불가 '미지원 상태 미확인')]}"
bad_kd absent-seq "{\"schema\": \"colab-reseed-known-defects/1\", \"entries\": [$(entry 99 SPI-4weeks '#133' 판정불가 '미지원 상태 미확인')]}"
bad_kd no-approval '{"schema": "colab-reseed-known-defects/1", "entries": [{"seq": 13, "name": "SPI-4weeks", "issue": "#133", "expectedVerdict": "판정불가", "notePrefix": "미지원 상태 미확인", "reason": "사유"}]}'
bad_kd duplicate "{\"schema\": \"colab-reseed-known-defects/1\", \"entries\": [$(entry 13 SPI-4weeks '#133' 판정불가 '미지원 상태 미확인'), $(entry 13 SPI-4weeks '#133' 판정불가 '미지원 상태 미확인')]}"

# ── ⓓ 결함이 고쳐져 정상 판정이면 통과 ＋ 「면제 불필요」 ────────────────────
ROW16_OK=$'16\tERA5 변환 결과\t가공 단계 Lv1 \t성립\t2000\t0\t1\t누름 focus+Enter · 적중 = 보기 단추'
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16_OK"
reset_run; VERIFY_FROM="$TMP/prior"
run_verify; rc=$?
[ "$rc" -eq 0 ] || note "ⓓ 면제 행이 정상 판정(성립)인데 통과하지 못했다: $(grep '대조 결과' "$TMP/out")"
grep -q '면제 불필요 — 16 · ERA5 변환 결과 · #134 — known-defects.json 에서 뺄 것' "$TMP/out" || note "ⓓ′ 「면제 불필요 … known-defects.json 에서 뺄 것」을 찍지 않았다"
grep -q '알려진 결함 면제 2건' "$TMP/out" || note "ⓓ″ 남은 면제 건수가 2건이 아니다"

# ── ⓕ 앞 실행 자리 거부 ────────────────────────────────────────────────────
refuse_prior() { # $1 = 사례 · $2 = 거부 문구 일부
  reset_run; VERIFY_FROM="$TMP/prior"
  run_verify; rc=$?
  [ "$rc" -ne 0 ] || note "ⓕ 앞 실행 자리 [$1] 을 받아들였다"
  grep -q "$2" "$TMP/out" || note "ⓕ′ 앞 실행 자리 [$1] 거부 사유에 「$2」가 없다: $(tail -2 "$TMP/out")"
  [ "$(ab_calls)" = 0 ] || note "ⓕ″ 앞 실행 자리 [$1] 거부 뒤 순회를 돌았다"
  [ ! -f "$TMP/finalized" ] || note "ⓕ‴ 앞 실행 자리 [$1] 거부인데 최종화로 갔다"
}
for missing in preview-judgment.tsv counts.json result.json; do
  make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"; rm -f "$TMP/prior/$missing"
  refuse_prior "no-$missing" "$missing"
done
PRIOR_DATASETS=28 make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
refuse_prior datasets-28 '데이터셋 기대'
PRIOR_SHA="" make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
refuse_prior no-sha '대상 sha 가 없다'
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
printf '{"targetSha": "cccccccccccc"}\n' > "$TMP/prior/approval-record.json"
refuse_prior approval-sha '승인 기록 대상 sha'
# 앞 실행 뒤 dev 가 재배포돼 대상 sha 가 달라도 거부하지 않는다 — 주의 줄과 기록(targetShaMatches false)을 남긴다.
PRIOR_SHA=bbbbbbbbbbbb make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$TMP/prior"
run_verify; rc=$?
[ "$rc" -eq 0 ] || note "ⓕ⁵ 앞·이번 대상 sha 가 다르다는 이유로 거부했다(rc $rc)"
grep -q 'verify-from 주의 — 판정표는 대상 sha bbbbbbbbbbbb 에서 잰 것' "$TMP/out" || note "ⓕ⁵′ 대상 sha 차이 주의 줄이 없다"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); sys.exit(0 if d["targetShaMatches"] is False and d["targetSha"]=="aaaaaaaaaaaa" else 1)' \
  "$RUN_DIR/verify-from.json" || note "ⓕ⁵″ verify-from.json 에 targetShaMatches false 가 없다"
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" $'16\t다른 이름\t가공 단계 Lv1 \t미성립\t1909\t0\t1\t누름 x'
refuse_prior other-names '판정표'
make_prior "$TMP/prior" "$ROW1" "$ROW13" "$ROW14" "$ROW16"
reset_run; VERIFY_FROM="$RUN_DIR"
run_verify; rc=$?
[ "$rc" -ne 0 ] || note "ⓕ⁗ 앞 실행 자리가 이번 실행 자리와 같은데 받아들였다"
unset VERIFY_FROM

# ── ⓖ 순회 경로의 면제 — 차단 항목을 면제 기록으로 옮긴다 ──────────────────
reset_run
printf '%s\n' "$ROW1" "$ROW13" "$ROW14" "$ROW16" > "$RUN_DIR/preview-judgment.tsv"
CURRENT_STAGE=verify
blocked_add verify "seq=13 SPI-4weeks — 승인된 미지원 표시를 확인하지 못했다 · 미지원 표시 [0]"
blocked_add verify "seq=14 SPEI-4weeks — 승인된 미지원 표시를 확인하지 못했다 · 미지원 표시 [0]"
blocked_add verify "seq=16 ERA5 변환 결과 — 미리보기 최종 상태가 failed다"
verify_compare "$SEED_WORK_DIR/verify.json" "$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml" > "$TMP/out" 2>&1; rc=$?
[ "$rc" -eq 0 ] || note "ⓖ 순회 경로의 면제 행 셋을 통과시키지 못했다: $(grep '대조 결과' "$TMP/out")"
[ ! -s "$RUN_DIR/blocked.jsonl" ] || note "ⓖ′ 면제 행의 차단 항목이 blocked.jsonl 에 남았다(결과가 failed 로 선다): $(cat "$RUN_DIR/blocked.jsonl")"
python3 - "$RUN_DIR/counts.json" <<'PY' || note "ⓖ″ 옮긴 차단 항목이 면제 기록(counts.knownDefects.exempted[].blocked)에 없다"
import json, sys
kd = json.load(open(sys.argv[1]))["knownDefects"]
sys.exit(0 if sum(len(e.get("blocked", [])) for e in kd["exempted"]) == 3 else 1)
PY
# 면제 밖 행의 차단 항목은 남는다.
reset_run
printf '%s\n' "$ROW1_BAD" "$ROW13" "$ROW14" "$ROW16" > "$RUN_DIR/preview-judgment.tsv"
CURRENT_STAGE=verify
blocked_add verify "seq=1 첫 자료 — 보기 전 정착 미확인"
blocked_add verify "seq=13 SPI-4weeks — 승인된 미지원 표시를 확인하지 못했다"
verify_compare "$SEED_WORK_DIR/verify.json" "$REPO_ROOT/dev-package/tools/dev-seed/plan-manifest.yaml" > "$TMP/out" 2>&1; rc=$?
[ "$rc" -ne 0 ] || note "ⓖ‴ 면제 밖 판정불가가 있는데 대조가 통과했다"
grep -q 'seq=1 첫 자료' "$RUN_DIR/blocked.jsonl" 2>/dev/null || note "ⓖ⁗ 면제 밖 행의 차단 항목이 사라졌다"

# ── ⓗ reseed.sh 인자 — --verify-from 은 --from verify 로만 ─────────────────
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
bash "$RESEED_DIR/reseed.sh" --dry-run --run-dir "$TMP/dry-ok" --accounts-file "$ACCOUNTS_FILE" \
  --from verify --verify-from "$TMP/prior" > "$TMP/cli.out" 2>&1; rc=$?
[ "$rc" -eq 0 ] || note "ⓗ⁗ --from verify --verify-from --dry-run 이 비영으로 끝났다(rc $rc): $(tail -2 "$TMP/cli.out")"
grep -q 'DRY verify-from' "$TMP/dry-ok/logs/verify.log" 2>/dev/null || note "ⓗ⁵ dry-run verify 로그에 verify-from 재개 줄이 없다"

[ "$fail" = 0 ] && echo "verify-resume — 면제 통과·면제 밖 실패·목록 fail-closed·면제 불필요·순회 생략·앞 자리 거부·차단 이관·인자 거부"
exit "$fail"
