#!/usr/bin/env bash
# preflight — 환경 10 항목과 계정 입력 판정. 하나라도 어긋나면 **이름을 대고** 비영 종료한다.
#
# 성격 = 거부가 올바른 동작이다(라운드 §7). 부분 실행으로 넘어가지 않는다.
# 근거 = R-DATA-CANON §2 판정 ㈔ ⓐ(6항목) ＋ 이슈 #48(QEMU · AWS 자격) ＋ 지시 4항목 추가.
# 이 파일은 단독 실행하지 않는다. `reseed.sh` 가 source 한다.

PF_PASS=(); PF_FAIL=(); PF_NOTE=()

pf_pass() { PF_PASS+=("$1"); log "  ✓ $1 — $2"; }
pf_fail() { PF_FAIL+=("$1"); log "  ✗ $1 — $2"; blocked_add "preflight:$1" "$2"; }
pf_note() { PF_NOTE+=("$1"); log "  · $1 — $2"; }

# dry-run 은 검사하지 않고 **무엇을 검사하는지**만 찍는다.
# 이유 = 검사 자체가 dev·AWS·docker·참조자료 드라이브를 건드리므로 무접촉 요구와 양립하지 않는다.
pf_dry() {
  [ "$DRY_RUN" = 1 ] || return 1
  log "  DRY $1 — $2"
  return 0
}

# dev 접속 값이 없으면 그 항목을 **이름을 대고** 미달로 떨어뜨리고 0 을 돌려준다.
# 값 부재로 셸을 끝내지 않는다 — 접속이 필요 없는 항목(git·qemu·ref-root·resources·build-plan)은
# 그대로 실제로 잰다. 부재 하나가 나머지 판정을 덮지 않는다.
pf_need_ssh() {
  [ "${#DEV_SSH_MISSING[@]}" -gt 0 ] || return 1
  pf_fail "$1" "dev 접속 값 미설정 — ${DEV_SSH_MISSING[*]} (예: COLAB_DEV_SSH=ec2-user@<IP> · COLAB_DEV_KEY_FILE=<0600 개인키>)"
  return 0
}

# ⑴ git — origin/develop 을 받았는가 · 배포 대상 sha 가 그 조상인가 · 작업 트리가 깨끗한가.
pf_git() {
  pf_dry git "git fetch origin develop · rev-parse $TARGET_REF · merge-base --is-ancestor · status --porcelain" && return
  if ! run_capture git -C "$REPO_ROOT" fetch -q origin +refs/heads/develop:refs/remotes/origin/develop >/dev/null; then
    pf_fail git "origin/develop 조회 실패 — 진행 금지(ship.sh 와 같은 판정 · exit 78 자리)"; return
  fi
  local resolved; resolved="$(run_capture git -C "$REPO_ROOT" rev-parse --short=12 "$TARGET_REF" || true)"
  if [ -z "$resolved" ]; then pf_fail git "배포 대상 ref 를 풀지 못했다: $TARGET_REF"; return; fi
  TARGET_SHA="$resolved"
  if ! run_capture git -C "$REPO_ROOT" merge-base --is-ancestor "$TARGET_SHA" origin/develop; then
    pf_fail git "배포 대상 $TARGET_SHA 가 origin/develop 의 조상이 아니다 — dev 배포 원천은 develop"; return
  fi
  local dirty; dirty="$(run_capture git -C "$REPO_ROOT" status --porcelain || true)"
  if [ -n "$dirty" ]; then
    pf_fail git "작업 트리가 깨끗하지 않다 — $(printf '%s\n' "$dirty" | wc -l | tr -d ' ') 건"; return
  fi
  pf_pass git "대상 $TARGET_SHA ∈ origin/develop · 작업 트리 깨끗"
}

# ⑵ dev 실행 sha — `/opt/colab-v2/CURRENT_SHA` 가 정본이다(`deploy_doctor` ⑮ 가 읽는 자리).
#    다르면 deploy 단계가 **필수**이고, 그 단계가 꺼져 있으면 거부한다.
pf_dev_sha() {
  pf_dry dev-sha "ssh <dev> cat /opt/colab-v2/CURRENT_SHA · 대상 sha 와 대조 · 불일치 시 deploy 단계 필수" && return
  pf_need_ssh dev-sha && return
  local cur; cur="$(ssh_dev_capture 'cat /opt/colab-v2/CURRENT_SHA 2>/dev/null | tr -d "\r\n"' || true)"
  if [ -z "$cur" ]; then pf_fail dev-sha "dev 의 CURRENT_SHA 를 읽지 못했다 — ssh·경로 확인"; return; fi
  if [ "$cur" = "${TARGET_SHA:-}" ]; then
    pf_pass dev-sha "dev 실행 sha $cur = 대상 sha"
    return
  fi
  if stage_enabled deploy; then
    pf_pass dev-sha "dev 실행 sha $cur ≠ 대상 ${TARGET_SHA:-?} — deploy 단계가 켜져 있다"
  else
    pf_fail dev-sha "dev 실행 sha $cur ≠ 대상 ${TARGET_SHA:-?} 인데 deploy 단계가 꺼져 있다 — --from 을 deploy 이전으로 둔다"
  fi
}

# ⑶ AWS 자격 사슬 — 계정 식별자는 **끝 4자리만** 찍는다.
#    갈래 둘을 따로 잰다.
#      ⓐ 환경변수 키 — 배포 9단계 `services/core-api/ops/deploy_web.py` 가 자작 SigV4 라
#         `deploy_web.py`는 명시 AWS_PROFILE의 정적/session 자격도 지원한다. 이 preflight는 기존 환경 자격 검사 정책을 유지한다.
#         deploy 단계를 켰으면 이 갈래가 필수다.
#      ⓑ `aws sts get-caller-identity` — 있으면 사슬이 실제로 풀리는지 확인한다.
pf_aws() {
  pf_dry aws "AWS_ACCESS_KEY_ID/SECRET 존재 여부 · aws sts get-caller-identity(계정 끝 4자리만)" && return
  local env_ok=0
  [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ] && env_ok=1
  local sts_acct=""
  if command -v aws >/dev/null 2>&1; then
    sts_acct="$(run_capture aws sts get-caller-identity --query Account --output text 2>/dev/null || true)"
  fi
  if [ "$env_ok" = 1 ]; then
    pf_pass aws "환경변수 갈래 성립${sts_acct:+ · 계정 …${sts_acct: -4}}"
  elif stage_enabled deploy; then
    pf_fail aws "AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY 부재 — 이 preflight는 환경 자격을 요구한다(deploy_web.py의 profile 지원과 별도 정책)"
  elif [ -n "$sts_acct" ]; then
    pf_pass aws "sts 갈래 성립 · 계정 …${sts_acct: -4}(deploy 단계 없음 — 환경변수 갈래 불요)"
  else
    pf_fail aws "환경변수·sts 어느 갈래로도 자격이 풀리지 않는다"
  fi
}

# ⑷ QEMU/binfmt arm64 — WSL 재시작마다 등록이 사라진다(이슈 #48 ⑶).
#    `infra/dev/build.sh` 가 `--platform linux/arm64` 로 5벌을 굽는 자리라 deploy 단계에서만 차단한다.
pf_qemu() {
  pf_dry qemu "/proc/sys/fs/binfmt_misc/qemu-aarch64 존재 · docker buildx ls 의 PLATFORMS 에 linux/arm64" && return
  local binfmt=0 plat=0
  [ -e /proc/sys/fs/binfmt_misc/qemu-aarch64 ] && binfmt=1
  run_capture docker buildx ls 2>/dev/null | grep -q 'linux/arm64' && plat=1
  if [ "$binfmt" = 1 ] && [ "$plat" = 1 ]; then
    pf_pass qemu "binfmt qemu-aarch64 등록 · buildx PLATFORMS 에 linux/arm64"
  elif stage_enabled deploy; then
    pf_fail qemu "binfmt=$binfmt buildx-arm64=$plat — 고침 = docker run --privileged --rm tonistiigi/binfmt --install arm64"
  else
    pf_note qemu "binfmt=$binfmt buildx-arm64=$plat (deploy 단계 없음 — 차단하지 않는다)"
  fi
}

# ⑸ 타 세션 잔존 — 이름을 대고 거부한다.
#    ⓐ 다른 작업 사본의 배포가 진행 중인가(`deploy_release.py` 잠금이 작업 사본을 넘지 못한다 · 이슈 #48 관련)
#    ⓑ EC2 에 임시 컨테이너가 남아 있는가(`colab-ops-*` · 이 도구가 쓰는 `colab_reseed_*`)
pf_leftovers() {
  pf_dry leftovers "<git-common-dir>/deploy-releases/*/state.json 진행 중 · ssh <dev> docker ps -a 이름 대조" && return
  pf_need_ssh leftovers && return
  local names=""
  # ⚠ `--git-common-dir` 단독은 **호출한 자리 기준 상대경로**를 돌려준다(워크트리에서는 `../..`
  #   사슬). 이 함수는 `$REPO_ROOT` 밖에서 그 값을 다시 쓰므로 절대경로로 받아야 한다 —
  #   상대경로면 `[ -d "$common/deploy-releases" ]` 가 언제나 거짓이고 진행 중 배포를
  #   **보지 못한 채 「0 건」으로 통과**시킨다(fail-open).
  local common
  common="$(run_capture git -C "$REPO_ROOT" rev-parse --path-format=absolute --git-common-dir || true)"
  if [ -z "$common" ]; then
    pf_fail leftovers "git 공통 디렉터리를 절대경로로 풀지 못했다 — 진행 중 배포 판정 불가"; return
  fi
  if [ -d "$common/deploy-releases" ]; then
    names="$(grep -rl '"status"[[:space:]]*:[[:space:]]*"running"' "$common/deploy-releases" 2>/dev/null || true)"
  fi
  local remote rc=0
  remote="$(ssh_dev_capture "docker ps -a --format '{{.Names}}'")" || rc=$?
  if [ "$rc" -ne 0 ]; then
    # 못 물어본 것을 「0 건」으로 읽지 않는다 — 조회 실패는 미달이다.
    pf_fail leftovers "EC2 컨테이너 목록 조회 실패(ssh 종료코드 $rc) — 잔존 여부 판정 불가"; return
  fi
  local stale; stale="$(printf '%s\n' "$remote" | grep -E '^(colab-ops-|colab_reseed_)' || true)"
  if [ -n "$names" ] || [ -n "$stale" ]; then
    pf_fail leftovers "잔존 — 배포 상태 [$(printf '%s' "$names" | tr '\n' ' ')] · 컨테이너 [$(printf '%s' "$stale" | tr '\n' ' ')]"
  else
    pf_pass leftovers "진행 중 배포 0 · 임시 컨테이너 0"
  fi
}

# ⑹ 참조자료 드라이브 — 정본 md 4건이 실재해야 한다(R-DATA-CANON §2 ㈎ ⓐ).
pf_ref_root() {
  pf_dry ref-root "COLAB_REF_ROOT 아래 DATASETS.md 4건 존재" && return
  if [ -z "${COLAB_REF_ROOT:-}" ] || [ ! -d "$COLAB_REF_ROOT" ]; then
    pf_fail ref-root "COLAB_REF_ROOT 가 비었거나 폴더가 아니다"; return
  fi
  local missing=()
  local rel
  for rel in "${REF_MD_RELS[@]}"; do
    [ -f "$COLAB_REF_ROOT/$rel" ] || missing+=("$rel")
  done
  if [ "${#missing[@]}" -gt 0 ]; then
    pf_fail ref-root "DATASETS.md 부재 ${#missing[@]} 건 — ${missing[*]}"
  else
    pf_pass ref-root "DATASETS.md 4건 존재"
  fi
}

# ⑺ agent-browser — 화면 투입의 유일한 경로다. 판정 = 종료코드 0 ＋ fail 계수 0.
pf_agent_browser() {
  pf_dry agent-browser "agent-browser doctor — 종료코드 0 ＋ fail 계수 0" && return
  if ! command -v agent-browser >/dev/null 2>&1; then
    pf_fail agent-browser "실행기가 없다 — npm i -g agent-browser"; return
  fi
  local out; out="$(run_capture agent-browser doctor 2>&1 || true)"
  local nfail; nfail="$(printf '%s' "$out" | grep -Eio '[0-9]+ fail' | head -1 | grep -Eo '^[0-9]+' || true)"
  if [ -z "$nfail" ]; then
    pf_fail agent-browser "doctor 출력에서 fail 계수를 읽지 못했다 — 판정 불가"
  elif [ "$nfail" -gt 0 ]; then
    pf_fail agent-browser "doctor fail $nfail 건 — 고침 = agent-browser doctor --fix"
  else
    pf_pass agent-browser "doctor fail 0"
  fi
}

# ⑻ 시크릿 — 이름과 모드만 본다. **값은 읽지 않는다.**
#    목록의 출처 = `infra/dev/README.md` 시크릿 파일 표 ＋ 런북 §3·§5 가 마운트하는 파일.
#    자리의 출처 = `$EC2_SECRETS_DIR`(＝ `COLAB_RESEED_EC2_SECRETS_DIR` · 기본 `/etc/colab`).
#    운영자 기계의 `COLAB_DEV_SECRETS_DIR` 는 **로컬 폴더**라 여기서 읽지 않는다(`reseed.sh` 머리말 ⚠).
#
# ⚠ 경로는 **이름마다 한 개**씩 만든다. 종전 `printf "'%s/%s' " "$dir" "${이름[@]}"` 은 서식이
#   인자를 **둘씩** 삼켜 `'<dir>/master.url' 'platform-owner-db.url/ai-owner-db.url' …` 5개를 냈고,
#   9건 중 `master.url` 하나만 실제로 물었다. 나머지 8건은 구조적으로 「부재」라
#   **이 항목이 green 이 된 적이 없다**(DR-4 회차 §5 ⑵). 서식 하나에 인자 하나로 고정한다.
pf_secrets() {
  pf_dry secrets "ssh <dev> stat -c '%n %a' \$COLAB_RESEED_EC2_SECRETS_DIR/<이름 9건> — 모드 0600 만 판정" && return
  pf_need_ssh secrets && return
  local dir="$EC2_SECRETS_DIR"
  local listing; listing="$(ssh_dev_capture "sudo stat -c '%n %a' $(printf "'%s' " "${SECRET_FILE_NAMES[@]/#/$dir/}") 2>&1" || true)"
  local bad=() name mode
  local n
  for n in "${SECRET_FILE_NAMES[@]}"; do
    local line; line="$(printf '%s\n' "$listing" | grep -F "$dir/$n " || true)"
    if [ -z "$line" ]; then bad+=("$n:부재"); continue; fi
    mode="${line##* }"
    [ "$mode" = 600 ] || bad+=("$n:$mode")
  done
  if [ "${#bad[@]}" -gt 0 ]; then
    pf_fail secrets "부재·모드 어긋남 ${#bad[@]} 건 — ${bad[*]}"
  else
    pf_pass secrets "${#SECRET_FILE_NAMES[@]} 건 존재 · 전건 0600"
  fi
}

# ⑼ 호스트 자원 하한 —
#    메모리 4 GiB = 호스트 WSL 상한 12 GB 에서 전수 게이트(-j 4)와 에이전트 동시 실행이 OOM 으로
#      죽은 실측이 있고(`.claude/rules/colab-rules.md §9`), 이 실행은 buildx 5벌 ＋ 브라우저 1벌을 겹친다.
#    디스크 20 GiB = `infra/dev/build.sh` 가 arm64 이미지 5벌을 `dist/` 에 tar 한 벌로 저장하고
#      buildx 레이어 캐시가 그 위에 쌓인다. 업로드 원본(2026-09-13 실측 3.6 GB)은 복사하지 않으므로
#      계산에서 뺀다.
#    값은 `COLAB_RESEED_MIN_MEM_MIB`·`COLAB_RESEED_MIN_DISK_GIB` 로 바꾼다.
pf_resources() {
  pf_dry resources "MemAvailable ≥ ${MIN_MEM_MIB} MiB · $REPO_ROOT 여유 ≥ ${MIN_DISK_GIB} GiB · EC2 $DEV_STATE_DIR/images 여유 ≥ 2 GiB" && return
  local mem_mib disk_gib
  mem_mib="$(awk '/^MemAvailable:/ {printf "%d", $2/1024}' /proc/meminfo 2>/dev/null || echo 0)"
  disk_gib="$(df -BG --output=avail "$REPO_ROOT" 2>/dev/null | tail -1 | tr -dc '0-9' || echo 0)"
  local bad=()
  [ "${mem_mib:-0}" -ge "$MIN_MEM_MIB" ] || bad+=("메모리 ${mem_mib} MiB < ${MIN_MEM_MIB}")
  [ "${disk_gib:-0}" -ge "$MIN_DISK_GIB" ] || bad+=("디스크 ${disk_gib} GiB < ${MIN_DISK_GIB}")
  # DR-4 5회차 §2: ship 전 정지선 2 GiB (load 후 1.5 GiB와 구분).
  # 실제 앱 state/이미지 경로의 파일시스템을 SSH로 측정한다. df -BG 반올림은 쓰지 않는다.
  pf_need_ssh resources && return
  local remote_disk remote_rc=0
  remote_disk="$(ssh_dev_capture "df -B1 --output=avail '$DEV_STATE_DIR/images'")" || remote_rc=$?
  remote_disk="$(printf '%s\n' "$remote_disk" | tail -1 | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  if [ "$remote_rc" -ne 0 ] || [[ ! "$remote_disk" =~ ^[0-9]{1,18}$ ]]; then
    bad+=("EC2 디스크 준비 실패 — 측정 불가 (SSH/df 종료 $remote_rc)")
  elif [ "$remote_disk" -lt 2147483648 ]; then
    bad+=("EC2 디스크 $remote_disk B < 2147483648 B (2 GiB)")
  fi
  if [ "${#bad[@]}" -gt 0 ]; then
    pf_fail resources "${bad[*]}"
  else
    pf_pass resources "메모리 ${mem_mib} MiB · 로컬 디스크 ${disk_gib} GiB · EC2 디스크 $remote_disk B"
  fi
}

# ⑽ 계획 생성기 — 정본 md 에서 28/18 이 나오는가. 여기서 어긋나면 seed 가 틀린 계획으로 돈다.
#
# ⚠ 생성기의 요약줄은 **두 모양**이다 — `--dry-run` 경로는 `datasets 28 edges 18`,
#   `--check-manifest` 경로는 뒤에 ` data_bytes N` 이 더 붙는다
#   (`dev-package/tools/dev-seed/build_plan.py` `check_manifest`). `grep -qx` 는 뒤 모양을
#   한 글자도 잡지 못한다 — 계수가 맞아도 미달로 떨어지는 자리라 앞머리 일치로 바꾼다.
pf_build_plan() {
  pf_dry build-plan "python3 $(relpath "$BUILD_PLAN_PY") --dry-run — exit 0 ＋ 「datasets $EXPECT_DATASETS edges $EXPECT_EDGES」" && return
  # 표준오류까지 읽어야 미달 사유가 남는다 — `run_capture` 는 stderr 를 로그로 보낸다.
  local tmp; tmp="$(mktemp)"
  local out rc=0
  python3 "$BUILD_PLAN_PY" \
    --dry-run --ref-root "${COLAB_REF_ROOT:-}" --md-root "${MD_ROOT:-}" > "$tmp" 2>&1 || rc=$?
  out="$(cat "$tmp")"; rm -f "$tmp"
  printf '%s\n' "$out" | redact >> "$STAGE_LOG"
  if [ "$rc" -ne 0 ]; then
    pf_fail build-plan "비영 종료 $rc — $(printf '%s' "$out" | tail -2 | tr '\n' ' ')"; return
  fi
  # 요약줄은 `datasets <n> edges <n>` 으로 시작하고 뒤에 아무것도 없거나 공백이 온다.
  # 계수 자리에 다른 수가 오면 잡히지 않는다 — 접두 일치가 아니라 **낱말 경계**로 끊는다.
  local summary; summary="$(printf '%s\n' "$out" | grep -E '^datasets [0-9]+ edges [0-9]+( |$)' | head -1 || true)"
  if [ -z "$summary" ]; then
    pf_fail build-plan "요약줄(datasets … edges …)이 출력에 없다 — 판정 불가"; return
  fi
  if printf '%s\n' "$summary" | grep -qE "^datasets $EXPECT_DATASETS edges $EXPECT_EDGES( |$)"; then
    pf_pass build-plan "$summary"
  else
    pf_fail build-plan "계수 불일치(기대 datasets $EXPECT_DATASETS edges $EXPECT_EDGES) — $summary"
  fi
}

# 판정 전에 **무엇을 쓸 것인지** 두 줄로 밝힌다(`--preflight-only` 의 산출물이기도 하다).
# 비밀은 없다 — 마운트할 폴더 **경로 하나**와 레포에 이미 적혀 있는 계정 신원뿐이다.
pf_announce() {
  log "  · 마운트 자리 — EC2 시크릿 폴더 = $EC2_SECRETS_DIR (reset·prelude 가 docker -v 로 잡는 자리 · 값은 읽지 않는다)"
  if [ -n "${RESEED_ACCOUNT_ID:-}" ]; then
    log "  · 계정 신원 — id=$RESEED_ACCOUNT_ID · email=${RESEED_ACCOUNT_EMAIL:-} · name=${RESEED_ACCOUNT_NAME:-} · role=${RESEED_ACCOUNT_ROLE:-} (출처 $(relpath "$PROVISION_LAB_SQL"))"
  else
    log "  · 계정 신원 — 판정불가 · $(relpath "$PROVISION_LAB_SQL") 의 d1_account INSERT 를 읽지 못했다 (RESEED_ACCOUNT_ID/_EMAIL/_NAME 을 직접 준다)"
  fi
}

# 비밀번호 값은 stdout/상태/명령 인자로 내보내지 않는다.
validate_seed_inputs() {
  [ "${ACCOUNT_PROFILE_INVALID:-0}" = 0 ] || { echo '실행 계정 프로필이 승인 기준과 일치하지 않거나 안전하지 않습니다' >&2; return 1; }
  [ "${ACCOUNT_OVERRIDE_INVALID:-0}" = 0 ] || { echo '계정 신원 override가 실행 후보와 다릅니다' >&2; return 1; }
  [ -z "${ACCOUNTS_PASSWORD_FILE:-}" ] || { echo '공통 비밀번호는 사용할 수 없습니다: 각 이메일 초기값 정책' >&2; return 1; }
  python3 "$RESEED_DIR/accounts.py" validate --profile "$ACCOUNTS_FILE" || return 1
  python3 "$RESEED_DIR/accounts.py" sql --profile "$ACCOUNTS_FILE" --sql "$PROVISION_LAB_SQL" >/dev/null || return 1
  python3 - "${OPERATOR_PASSWORD_OVERRIDE:-}" "$RESEED_ACCOUNT_EMAIL" "$SEED_WORK_DIR" "${1:-0}" <<'PYINPUT'
import pathlib,sys
password,email,work,reset=sys.argv[1:]
if password:
 p=pathlib.Path(password)
 if p.is_symlink() or not p.is_file() or p.stat().st_mode&0o777!=0o600 or p.read_text().strip()!=email:
  raise SystemExit('교수 초기 비밀번호 파일이 지정 이메일 정책과 다릅니다')
if reset=='1' and any((pathlib.Path(work)/n).exists() for n in ('state.json','new-password.txt','initial-password.txt','accounts')):
 raise SystemExit('새 초기화에는 새 seed 작업 폴더가 필요합니다')
PYINPUT
}

prepare_seed_password() {
  [ "$DRY_RUN" != 1 ] || return 0
  python3 "$RESEED_DIR/accounts.py" prepare --profile "$ACCOUNTS_FILE" --work "$ACCOUNTS_WORK_DIR" || return 1
  python3 - "$OPERATOR_PASSWORD_FILE" "$SEED_WORK_DIR" <<'PYPREP'
import os, pathlib, sys
source, work = map(pathlib.Path, sys.argv[1:])
work.mkdir(parents=True, exist_ok=True, mode=0o700)
path = work / 'initial-password.txt'
try:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o777 != 0o600 or not path.read_text().strip():
        sys.exit('기존 초기 비밀번호 파일이 안전한 0600 일반 파일이 아니다')
else:
    with os.fdopen(fd, 'wb') as output:
        output.write(source.read_bytes())
PYPREP
}

pf_seed_inputs() {
  pf_dry seed-inputs '계정·비밀번호 파일 검증 (값 미기록)' && return
  if [ "${PREFLIGHT_ONLY:-0}" = 1 ] || [ "${REHEARSE:-0}" = 1 ]; then
    if [ -z "${OPERATOR_PASSWORD_FILE:-}${ACCOUNTS_FILE:-}${ACCOUNTS_PASSWORD_FILE:-}" ]; then
      pf_note seed-inputs '읽기 전용 실행 · 계정 입력 미지정 · 초기화 입력 판정 제외'
      return
    fi
  fi
  local reset=0
  stage_enabled reset && reset=1
  if validate_seed_inputs "$reset"; then
    pf_pass seed-inputs '계정·비밀번호 입력 검증 완료 (값 미기록)'
  else
    pf_fail seed-inputs '계정·비밀번호 입력이 유효하지 않다'
  fi
}

stage_preflight() {
  PF_PASS=(); PF_FAIL=(); PF_NOTE=()
  pf_announce
  pf_git
  pf_dev_sha
  pf_aws
  pf_qemu
  pf_leftovers
  pf_ref_root
  pf_agent_browser
  pf_secrets
  pf_resources
  pf_build_plan
  pf_seed_inputs
  if [ "$DRY_RUN" != 1 ] && [ "${#PF_FAIL[@]}" = 0 ] &&
      [ "${PREFLIGHT_ONLY:-0}" != 1 ] && [ "${REHEARSE:-0}" != 1 ]; then
    prepare_seed_password || pf_fail seed-password-preparation '초기 비밀번호 파일 준비 실패 (기존 파일 덮어쓰기 없음)'
  fi

  python3 - "$RUN_DIR/preflight.json" "$DRY_RUN" "${#PF_PASS[@]}" "${#PF_FAIL[@]}" \
      "$(printf '%s,' "${PF_PASS[@]}")" "$(printf '%s,' "${PF_FAIL[@]}")" <<'PY'
import json, sys
path, dry, npass, nfail, passed, failed = sys.argv[1:7]
split = lambda s: [x for x in s.split(",") if x]
json.dump({"dryRun": dry == "1", "passed": split(passed), "failed": split(failed),
           "passedCount": int(npass), "failedCount": int(nfail)},
          open(path, "w"), ensure_ascii=False, indent=2)
PY

  if [ "$DRY_RUN" = 1 ]; then
    log "preflight — dry-run · 11 항목 판정 없음"
    return 0
  fi
  log "preflight — 통과 ${#PF_PASS[@]} · 미달 ${#PF_FAIL[@]}"
  if [ "${#PF_FAIL[@]}" -gt 0 ]; then
    log "미달 항목: ${PF_FAIL[*]}"
    return 1
  fi
  return 0
}
