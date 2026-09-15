#!/usr/bin/env bash
# 실패 픽스처 — `reseed.sh` 가 **fail-closed** 임을 증명한다.
#
# 무엇을 증명하는가 —
#   ⑴ 조건이 어긋나면 preflight 가 미달 항목을 **이름으로** 내고 비영 종료하며
#      뒤 단계(deploy·reset…)를 **시작하지 않는다**.
#   ⑵ 계획 생성기 요약줄을 **두 모양 다** 읽는다(계수가 어긋나면 미달).
#   ⑶ `--from` 은 preflight 를 **건너뛰지 않는다** — 대상 sha 가 거기서만 해석되기 때문이다.
#   ⑷ 실패해도 `result.json` 이 **선다** — 멈춘 단계·종료코드·로그 경로가 결과다.
#   ⑸ `die` 는 프로세스를 죽이지 않고 **비영으로 돌아온다**(⑷ 가 성립하는 전제).
#   ⑹ 미리보기 판정은 값이 비면 「성립」이 아니라 **「판정불가」**다.
#
# dev·AWS 무접촉 = `ssh`·`scp`·`docker`·`aws`·`agent-browser` 를 PATH 앞머리의 대역으로 가린다.
# 대역은 전부 「없다·못 붙는다·fail 이 있다」를 흉내 내므로 실물에 한 바이트도 나가지 않는다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEED="$HERE/../reseed.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/bin" "$TMP/empty-ref-root" "$TMP/run"

# ── 대역 ─────────────────────────────────────────────────────────────────
cat > "$TMP/bin/ssh" <<'STUB'
#!/usr/bin/env bash
echo "ssh: connect to host <대역> port 22: Connection refused" >&2
exit 255
STUB
cp "$TMP/bin/ssh" "$TMP/bin/scp"
cat > "$TMP/bin/docker" <<'STUB'
#!/usr/bin/env bash
# buildx 목록에 linux/arm64 가 없다 — QEMU 등록 소실 상태를 흉내 낸다(이슈 #48 ⑶).
[ "${1:-}" = buildx ] && { echo "NAME/NODE  DRIVER  STATUS  PLATFORMS"; echo "default    docker  running linux/amd64"; exit 0; }
exit 1
STUB
cat > "$TMP/bin/aws" <<'STUB'
#!/usr/bin/env bash
echo "Unable to locate credentials" >&2
exit 255
STUB
cat > "$TMP/bin/agent-browser" <<'STUB'
#!/usr/bin/env bash
[ "${1:-}" = doctor ] && { echo "8 pass · 0 warn · 2 fail"; exit 0; }
exit 0
STUB
# `git` 는 실물을 그대로 쓰되 **`fetch` 만 막는다.**
# 왜 = 이 픽스처는 한 번 돌 때 `reseed.sh` 를 7회 부르고, 그때마다 preflight ⑴ 이
#   공용 체크아웃에서 `git fetch -q origin main` 을 실제로 냈다(원격 접촉 ＋ ref 갱신 부작용).
# 기대 판정은 그대로다 — preflight ⑴ 은 fetch 실패를 「origin/main 조회 실패」 미달로 읽으므로
#   미달 항목 이름에 `git` 이 그대로 선다(종전에는 대상 ref 해석 실패로 같은 자리에 섰다).
REAL_GIT="$(command -v git)"
cat > "$TMP/bin/git" <<STUB
#!/usr/bin/env bash
# 앞머리 옵션을 건너뛰고 **첫 하위명령**만 본다 — \`git -C <경로> fetch …\` 도 잡는다.
args=("\$@"); i=0; cmd=""
while [ "\$i" -lt "\${#args[@]}" ]; do
  case "\${args[\$i]}" in
    -C|-c|--git-dir|--work-tree|--namespace|--exec-path) i=\$(( i + 2 )) ;;
    -*) i=\$(( i + 1 )) ;;
    *) cmd="\${args[\$i]}"; break ;;
  esac
done
if [ "\$cmd" = fetch ]; then
  echo "fatal: 픽스처 대역 — 원격 접촉 금지" >&2
  exit 1
fi
exec "$REAL_GIT" "\$@"
STUB
chmod +x "$TMP/bin"/*

# ── 실행 ─────────────────────────────────────────────────────────────────
# 어긋나게 둔 것 —
#   ⓐ 대상 ref 가 없는 이름이다               → git
#   ⓑ 참조자료 뿌리가 빈 폴더다               → ref-root · build-plan
#   ⓒ 자원 하한을 실물보다 크게 잡았다        → resources
#   ⓓ ssh 가 붙지 않는다                      → dev-sha · secrets · leftovers
#   ⓔ agent-browser doctor 가 fail 2 를 낸다  → agent-browser
#   ⓕ AWS 자격이 어느 갈래로도 풀리지 않는다  → aws
OUT="$TMP/out.txt"
PATH="$TMP/bin:$PATH" \
COLAB_DEV_SSH='ec2-user@<대역>' COLAB_DEV_KEY_FILE="$TMP/no-such-key" \
COLAB_DEV_URL='https://<대역>' COLAB_REF_ROOT="$TMP/empty-ref-root" \
COLAB_RESEED_EC2_SECRETS_DIR=/etc/colab \
COLAB_RESEED_MIN_MEM_MIB=99999999 COLAB_RESEED_MIN_DISK_GIB=99999999 \
AWS_ACCESS_KEY_ID= AWS_SECRET_ACCESS_KEY= \
  bash "$RESEED" --target-ref refs/colab-reseed-red-fixture --run-dir "$TMP/run" > "$OUT" 2>&1
RC=$?

echo "── 픽스처 출력 (미달 판정 줄)"
grep -E '  ✗ |미달 항목|단계 preflight 에서 멈췄다|⛔' "$OUT" || true
echo "── 종료코드 = $RC"

# ── 판정 ─────────────────────────────────────────────────────────────────
fail=0
note() { echo "  ✗ $1"; fail=1; }

[ "$RC" -ne 0 ] || note "종료코드가 0 이다 — fail-closed 아님"

for item in git ref-root build-plan resources dev-sha secrets agent-browser aws qemu leftovers; do
  grep -qE "  ✗ $item — " "$OUT" || note "미달 항목 이름에 $item 이 없다"
done

grep -q '단계 deploy 시작' "$OUT" && note "preflight 가 미달인데 deploy 단계가 시작됐다"
grep -q '단계 reset 시작' "$OUT" && note "preflight 가 미달인데 reset 단계가 시작됐다"

# 비밀 값이 로그로 새지 않는지 — 이름만 나와야 한다.
grep -qE '://[^:/@[:space:]]+:[^@[:space:]*]+@' "$OUT" && note "출력에 접속 문자열의 비밀번호 필드가 있다"

# ── 계획 생성기 요약줄 판독 ───────────────────────────────────────────────
# ⑽ `build-plan` 은 생성기의 요약줄로 판정한다. 생성기는 부르는 방식에 따라 **두 모양**을 낸다 —
#   `--dry-run` 경로는 `datasets 28 edges 18`, `--check-manifest` 경로는 뒤에 `data_bytes N` 이
#   더 붙는다(`dev-package/tools/dev-seed/build_plan.py`). `grep -qx "datasets 28 edges 18"` 은
#   뒤 모양을 **한 글자도** 잡지 못하므로 계수가 맞아도 미달로 떨어진다.
#   여기서는 생성기를 대역으로 바꿔 두 모양과 계수 불일치를 각각 판정한다.
plan_case() { # $1=대역이 찍을 요약줄 → stdout: 「미달」 또는 「통과」
  local summary="$1" out="$TMP/plan-out.txt" stub="$TMP/build_plan_stub.py"
  cat > "$stub" <<STUB
import sys
print("$summary")
print("expected datasets 28 edges 18")
sys.exit(0)
STUB
  PATH="$TMP/bin:$PATH" \
  COLAB_DEV_SSH='ec2-user@<대역>' COLAB_DEV_KEY_FILE="$TMP/no-such-key" \
  COLAB_DEV_URL='https://<대역>' COLAB_REF_ROOT="$TMP/empty-ref-root" \
  COLAB_RESEED_EC2_SECRETS_DIR=/etc/colab \
  COLAB_RESEED_BUILD_PLAN="$stub" \
  AWS_ACCESS_KEY_ID= AWS_SECRET_ACCESS_KEY= \
    bash "$RESEED" --target-ref refs/colab-reseed-red-fixture \
      --run-dir "$TMP/run-plan" > "$out" 2>&1 || true
  if grep -qE '  ✗ build-plan — ' "$out"; then printf '미달'; else printf '통과'; fi
  rm -rf "$TMP/run-plan"
}

# ⓖ 계수가 어긋나면 미달 — 「27」 은 28 이 아니다.
[ "$(plan_case 'datasets 27 edges 18 data_bytes 1')" = 미달 ] \
  || note "ⓖ 계수 불일치(27)를 통과로 읽었다 — fail-open"
# ⓗ 실물 두 모양은 전부 통과 — 뒤에 `data_bytes N` 이 붙어도 계수가 맞으면 통과다.
[ "$(plan_case 'datasets 28 edges 18 data_bytes 9663676416')" = 통과 ] \
  || note "ⓗ 실물 요약줄(data_bytes 포함)을 미달로 읽었다"
[ "$(plan_case 'datasets 28 edges 18')" = 통과 ] \
  || note "ⓗ′ 실물 요약줄(data_bytes 없음)을 미달로 읽었다"
# ⓘ 요약줄이 아예 없으면 미달 — 「없음」을 통과로 접지 않는다.
[ "$(plan_case 'TOTAL datasets=28 files=1 bytes=1 grid_bytes=0 edges=18 load_sum=1')" = 미달 ] \
  || note "ⓘ 요약줄이 없는 출력을 통과로 읽었다 — fail-open"

# ── 실패해도 결과가 선다 ─────────────────────────────────────────────────
# 멈춘 자리·종료코드·로그 경로가 결과다. 결과가 없으면 다음 회차는 어디서 이어야 할지 모른다.
RESULT="$TMP/run/result.json"
if [ ! -f "$RESULT" ]; then
  note "ⓙ 실패했는데 result.json 이 없다 — 멈춘 자리를 기록하지 않았다"
else
  python3 - "$RESULT" <<'PY' || note "ⓙ′ result.json 이 멈춘 단계·종료코드·로그를 담지 않았다"
import json, sys
r = json.load(open(sys.argv[1]))
assert r.get("outcome") == "failed", r.get("outcome")
assert r.get("failedStage") == "preflight", r.get("failedStage")
st = {s["stage"]: s for s in r.get("stages", [])}
assert st["preflight"]["exitCode"] != 0, st["preflight"]
assert st["preflight"].get("log"), st["preflight"]
PY
fi

# ── `--from` 이 preflight 를 건너뛰지 않는가 ──────────────────────────────
# 건너뛰면 대상 sha 가 빈 채로 이미지 태그(`…:dev-`)와 승인 기록에 들어간다.
FROM_OUT="$TMP/from-out.txt"
PATH="$TMP/bin:$PATH" \
COLAB_DEV_SSH='ec2-user@<대역>' COLAB_DEV_KEY_FILE="$TMP/no-such-key" \
COLAB_DEV_URL='https://<대역>' COLAB_REF_ROOT="$TMP/empty-ref-root" \
COLAB_RESEED_EC2_SECRETS_DIR=/etc/colab \
AWS_ACCESS_KEY_ID= AWS_SECRET_ACCESS_KEY= \
  bash "$RESEED" --from reset --target-ref refs/colab-reseed-red-fixture \
    --run-dir "$TMP/run-from" > "$FROM_OUT" 2>&1
FROM_RC=$?
[ "$FROM_RC" -ne 0 ] || note "ⓚ --from reset 이 0 으로 끝났다 — preflight 미달을 지나쳤다"
grep -q '단계 preflight 시작' "$FROM_OUT" || note "ⓚ′ --from reset 인데 preflight 가 돌지 않았다"
grep -q '단계 reset 시작' "$FROM_OUT" && note "ⓚ″ preflight 미달인데 reset 이 시작됐다"

# ── `--preflight-only` — 검사만 하고 바꾸는 단계는 하나도 돌지 않는다 ────
PO_OUT="$TMP/po-out.txt"
PATH="$TMP/bin:$PATH" \
  bash "$RESEED" --preflight-only --dry-run --run-dir "$TMP/run-po" > "$PO_OUT" 2>&1
PO_RC=$?
[ "$PO_RC" -eq 0 ] || note "ⓛ --preflight-only --dry-run 이 비영으로 끝났다(rc=$PO_RC)"
grep -q '단계 preflight 시작' "$PO_OUT" || note "ⓛ′ --preflight-only 인데 preflight 가 돌지 않았다"
for s in deploy reset bootstrap up s3 prelude seed verify; do
  grep -q "단계 $s 시작" "$PO_OUT" && note "ⓛ″ --preflight-only 인데 $s 단계가 시작됐다"
done
# 승인 기록은 **바꾸는 단계의 산출물**이다 — 검사만 한 회차가 그것을 남기면
# `report.py` 의 `approvalRecord` 가 서고, 아무것도 바꾸지 않은 회차가 승인된 회차로 읽힌다.
[ ! -f "$TMP/run-po/approval-record.json" ] || note "ⓛ‴ --preflight-only 인데 approval-record.json 이 섰다"

# ── dev 접속 값이 없을 때 ────────────────────────────────────────────────
# 종전에는 `${COLAB_DEV_SSH:?}` 로 **셸이 그 자리에서 끝났다** — 단계가 하나도 기록되지 않아
# `result.json` 이 없고, 무엇이 없어서 멈췄는지는 표준오류 한 줄에만 남았다(⑷ 와 같은 결함).
# 접속 값 부재는 「미달 항목」이다 — 이름을 대고 preflight 안에서 떨어진다.
NOSSH_OUT="$TMP/nossh-out.txt"
PATH="$TMP/bin:$PATH" \
COLAB_DEV_SSH= COLAB_DEV_KEY_FILE= \
COLAB_DEV_URL='https://<대역>' COLAB_REF_ROOT="$TMP/empty-ref-root" \
AWS_ACCESS_KEY_ID= AWS_SECRET_ACCESS_KEY= \
  bash "$RESEED" --preflight-only --target-ref refs/colab-reseed-red-fixture \
    --run-dir "$TMP/run-nossh" > "$NOSSH_OUT" 2>&1
NOSSH_RC=$?
[ "$NOSSH_RC" -ne 0 ] || note "ⓞ 접속 값이 없는데 0 으로 끝났다"
[ -f "$TMP/run-nossh/result.json" ] || note "ⓞ′ 접속 값 부재로 멈췄는데 result.json 이 없다"
for item in dev-sha secrets leftovers; do
  grep -qE "  ✗ $item — .*COLAB_DEV_SSH" "$NOSSH_OUT" \
    || note "ⓞ″ $item 미달 사유에 COLAB_DEV_SSH 이름이 없다"
done
# 접속 값이 없어도 **접속이 필요 없는 항목은 실제로 잰다** — 부재 하나로 전부를 덮지 않는다.
grep -qE "  (✓|✗) build-plan — " "$NOSSH_OUT" || note "ⓞ‴ 접속 값 부재로 build-plan 판정까지 멈췄다"
[ ! -f "$TMP/run-nossh/approval-record.json" ] || note "ⓞ⁗ --preflight-only 인데 approval-record.json 이 섰다"

# ── `die` 는 프로세스를 죽이지 않는다 ────────────────────────────────────
# 죽이면 `stage_end`·`report` 가 돌지 못해 위 ⓙ 가 성립하지 않는다.
DIE_OUT="$(
  DRY_RUN=0 STAGE_LOG=/dev/null RUN_DIR="$TMP/run" \
  bash -c '. "$1"; f() { die "픽스처"; }; f || echo "DIE_RETURNED=$?"; echo AFTER' _ "$HERE/../lib.sh" 2>&1
)"
printf '%s' "$DIE_OUT" | grep -q 'DIE_RETURNED=1' || note "ⓜ die 가 비영으로 돌아오지 않았다"
printf '%s' "$DIE_OUT" | grep -q 'AFTER' || note "ⓜ′ die 가 프로세스를 죽였다 — result.json 이 설 수 없다"

# ── 미리보기 판정 — 빈 값은 「성립」이 아니다 ────────────────────────────
PV_OUT="$(
  DRY_RUN=0 STAGE_LOG=/dev/null RUN_DIR="$TMP/run" \
  bash -c '. "$1"; . "$2"; for v in "" "x" "0" "2"; do printf "[%s]=%s\n" "$v" "$(preview_verdict "$v")"; done' \
    _ "$HERE/../lib.sh" "$HERE/../stages.sh" 2>&1
)"
printf '%s' "$PV_OUT" | grep -q '^\[\]=판정불가' || note "ⓝ 빈 값을 「판정불가」로 읽지 않았다: $PV_OUT"
printf '%s' "$PV_OUT" | grep -q '^\[x\]=판정불가' || note "ⓝ′ 숫자가 아닌 값을 「판정불가」로 읽지 않았다: $PV_OUT"
printf '%s' "$PV_OUT" | grep -q '^\[0\]=성립'     || note "ⓝ″ 0 을 「성립」으로 읽지 않았다: $PV_OUT"
printf '%s' "$PV_OUT" | grep -q '^\[2\]=미성립'   || note "ⓝ‴ 2 를 「미성립」으로 읽지 않았다: $PV_OUT"

# ── 계수 판정 — 빈 칸은 「미지정 0건」이 아니다 ──────────────────────────
# 종전에는 계수를 `tr -dc '0-9'` 로 받아 **아무 값도 못 받은 것과 「0」이 같은 모양**이 됐고,
# 표에도 `${unset_lv:-0}` 로 0 이 박혀 「미지정 0건 · 전건 연결」로 통과했다(fail-open).
# 여기서는 표를 직접 만들어 네 값을 판정한다 — 빈 칸·숫자 아님은 **판정불가**여야 한다.
cv_case() { # $1=「미지정」 칸 값 → 판정 줄은 $TMP/cv-out.txt · 종료코드는 count_verdict 의 것
  local tsv="$TMP/cv.tsv" out="$TMP/cv.json"
  printf '7\t표본\t레벨 2\t성립\t100\t%s\t1\t\n' "$1" > "$tsv"
  DRY_RUN=0 STAGE_LOG=/dev/null RUN_DIR="$TMP/run" \
    bash -c '. "$1"; . "$2"; count_verdict "$3" "$4"' _ "$HERE/../lib.sh" "$HERE/../stages.sh" "$tsv" "$out" \
    > "$TMP/cv-out.txt" 2>&1
}

for v in "" "x"; do
  cv_case "$v"; CV_RC=$?; CV_OUT="$(cat "$TMP/cv-out.txt")"
  [ "$CV_RC" -ne 0 ] || note "ⓠ 계수 칸 [$v] 을 통과로 읽었다 — fail-open: $CV_OUT"
  printf '%s' "$CV_OUT" | grep -q '판정불가' || note "ⓠ′ 계수 칸 [$v] 을 「판정불가」로 적지 않았다: $CV_OUT"
done
cv_case 0; CV_RC=$?; CV_OUT="$(cat "$TMP/cv-out.txt")"
[ "$CV_RC" -eq 0 ] || note "ⓠ″ 계수 칸 [0] 을 미달로 읽었다: $CV_OUT"
cv_case 2; CV_RC=$?; CV_OUT="$(cat "$TMP/cv-out.txt")"
[ "$CV_RC" -ne 0 ] || note "ⓠ‴ 계수 칸 [2] 를 통과로 읽었다 — 「미지정」 2건이 통과했다: $CV_OUT"
printf '%s' "$CV_OUT" | grep -q '미지정' || note "ⓠ⁗ 계수 칸 [2] 판정 줄에 「미지정」이 없다: $CV_OUT"

# EC2 disk는 로컬 자원이 넉넉해도 독립 판정한다. 실제 SSH는 호출하지 않는다.
disk_case() (
  . "$HERE/../preflight.sh"
  DRY_RUN=0 REPO_ROOT="$TMP" MIN_MEM_MIB=0 MIN_DISK_GIB=0
  DEV_STATE_DIR=/opt/colab-v2 DEV_SSH_MISSING=()
  log() { :; }; blocked_add() { :; }
  # Keep stdout and exit status independent, including a valid reading with SSH failure.
  ssh_dev_capture() {
    printf '%s' "$1" > "$TMP/disk-command"
    printf '%s\n' "$DISK_REPLY"
    return "$DISK_RC"
  }
  pf_resources
  [ "${#PF_FAIL[@]}" = 0 ]
)
disk_cases=0
for DISK_REPLY in 2147483648 2147483649 2147483647 1610612736 0 '' garbage '2147 483648'; do
  DISK_RC=0
  disk_case; rc=$?
  case "$DISK_REPLY" in 2147483648|2147483649) expected=0 ;; *) expected=1 ;; esac
  [ "$rc" = "$expected" ] || note "EC2 disk [$DISK_REPLY] rc=$rc expected=$expected"
  disk_cases=$((disk_cases + 1))
done
for DISK_RC in 255 1; do
  DISK_REPLY=2147483648 disk_case && note "EC2 SSH/df 실패 $DISK_RC 를 유효 계수로 통과시켰다"
  disk_cases=$((disk_cases + 1))
done
DISK_REPLY=$'    Avail\n 2147483648' DISK_RC=0 disk_case || note "정상 df 헤더/공백 응답을 거절했다"
disk_cases=$((disk_cases + 1))
grep -q '/opt/colab-v2/images' "$TMP/disk-command" 2>/dev/null || note "EC2 실제 image 파일시스템을 측정하지 않았다"
echo "EC2 disk 경계 $disk_cases 건"

# 실제 CLI가 runner에 넘기는 주소 우선순위 (dry-run, 외부 효과 없음).
url_cases=0
for mode in web cli legacy; do
  extra=(); web=https://web.invalid
  [ "$mode" != cli ] || extra=(--base-url https://cli.invalid)
  [ "$mode" != legacy ] || web=''
  COLAB_DEV_WEB_URL="$web" COLAB_DEV_URL=https://legacy.invalid \
    bash "$RESEED" --dry-run --from seed --run-dir "$TMP/url-$mode" "${extra[@]}" > "$TMP/url.out" 2>&1
  grep -q -- "--base-url https://$mode.invalid" "$TMP/url.out" || note "reseed 주소 우선순위 $mode 실패"
  url_cases=$((url_cases + 1))
done
echo "reseed 주소 우선순위 $url_cases 건"

# ── 픽스처가 레포를 더럽히지 않는가 ──────────────────────────────────────
# 위 실행들은 전부 preflight 에서 멈췄다(바꾸는 단계 0건) — 회차 기록은 실행 자리에만 선다.
STRAY="$(find "$HERE/../../../sessions" -maxdepth 1 -name 'DR-4-run-*.md' -newer "$TMP" 2>/dev/null | wc -l | tr -d ' ')"
[ "$STRAY" = 0 ] || note "ⓟ 픽스처가 dev-package/sessions/ 에 회차 기록 $STRAY 건을 남겼다"

if [ "$fail" -eq 0 ]; then
  echo "preflight-red — green (미달 10 항목 · 계획 요약줄 4 · result.json · --from 이 preflight 를 돈다 · --preflight-only · die 복귀 · 미리보기 판정불가 · 계수 판정 4 · 레포 무변)"
  exit 0
fi
echo "preflight-red — red" >&2
exit 1
