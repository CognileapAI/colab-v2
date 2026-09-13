#!/usr/bin/env bash
# preflight — 10 항목 판정. 하나라도 어긋나면 **이름을 대고** 비영 종료한다.
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

# ⑴ git — origin/main 을 받았는가 · 배포 대상 sha 가 그 조상인가 · 작업 트리가 깨끗한가.
pf_git() {
  pf_dry git "git fetch origin main · rev-parse $TARGET_REF · merge-base --is-ancestor · status --porcelain" && return
  if ! run_capture git -C "$REPO_ROOT" fetch -q origin main >/dev/null; then
    pf_fail git "origin/main 조회 실패 — 진행 금지(ship.sh 와 같은 판정 · exit 78 자리)"; return
  fi
  local resolved; resolved="$(run_capture git -C "$REPO_ROOT" rev-parse --short=12 "$TARGET_REF" || true)"
  if [ -z "$resolved" ]; then pf_fail git "배포 대상 ref 를 풀지 못했다: $TARGET_REF"; return; fi
  TARGET_SHA="$resolved"
  if ! run_capture git -C "$REPO_ROOT" merge-base --is-ancestor "$TARGET_SHA" origin/main; then
    pf_fail git "배포 대상 $TARGET_SHA 가 origin/main 의 조상이 아니다 — main 이 유일한 배포 원천(docs/BRANCHING.md 규칙 1)"; return
  fi
  local dirty; dirty="$(run_capture git -C "$REPO_ROOT" status --porcelain || true)"
  if [ -n "$dirty" ]; then
    pf_fail git "작업 트리가 깨끗하지 않다 — $(printf '%s\n' "$dirty" | wc -l | tr -d ' ') 건"; return
  fi
  pf_pass git "대상 $TARGET_SHA ∈ origin/main · 작업 트리 깨끗"
}

# ⑵ dev 실행 sha — `/opt/colab-v2/CURRENT_SHA` 가 정본이다(`deploy_doctor` ⑮ 가 읽는 자리).
#    다르면 deploy 단계가 **필수**이고, 그 단계가 꺼져 있으면 거부한다.
pf_dev_sha() {
  pf_dry dev-sha "ssh <dev> cat /opt/colab-v2/CURRENT_SHA · 대상 sha 와 대조 · 불일치 시 deploy 단계 필수" && return
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
#         `AWS_PROFILE`·`~/.aws/credentials` 를 해석하는 분기가 **없다**(이슈 #48 ⑵).
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
    pf_fail aws "AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY 부재 — deploy_web.py 는 AWS_PROFILE 을 해석하지 않는다(이슈 #48 ⑵)"
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
  local names=""
  local common; common="$(run_capture git -C "$REPO_ROOT" rev-parse --git-common-dir || true)"
  if [ -n "$common" ] && [ -d "$common/deploy-releases" ]; then
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
pf_secrets() {
  pf_dry secrets "ssh <dev> stat -c '%n %a' \$COLAB_DEV_SECRETS_DIR/<이름 9건> — 모드 0600 만 판정" && return
  local dir="${COLAB_DEV_SECRETS_DIR:-/etc/colab}"
  local listing; listing="$(ssh_dev_capture "sudo stat -c '%n %a' $(printf "'%s/%s' " "$dir" "${SECRET_FILE_NAMES[@]}") 2>&1" || true)"
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
  pf_dry resources "MemAvailable ≥ ${MIN_MEM_MIB} MiB · $REPO_ROOT 여유 ≥ ${MIN_DISK_GIB} GiB" && return
  local mem_mib disk_gib
  mem_mib="$(awk '/^MemAvailable:/ {printf "%d", $2/1024}' /proc/meminfo 2>/dev/null || echo 0)"
  disk_gib="$(df -BG --output=avail "$REPO_ROOT" 2>/dev/null | tail -1 | tr -dc '0-9' || echo 0)"
  local bad=()
  [ "${mem_mib:-0}" -ge "$MIN_MEM_MIB" ] || bad+=("메모리 ${mem_mib} MiB < ${MIN_MEM_MIB}")
  [ "${disk_gib:-0}" -ge "$MIN_DISK_GIB" ] || bad+=("디스크 ${disk_gib} GiB < ${MIN_DISK_GIB}")
  if [ "${#bad[@]}" -gt 0 ]; then
    pf_fail resources "${bad[*]}"
  else
    pf_pass resources "메모리 ${mem_mib} MiB · 디스크 ${disk_gib} GiB"
  fi
}

# ⑽ 계획 생성기 — 정본 md 에서 28/18 이 나오는가. 여기서 어긋나면 seed 가 틀린 계획으로 돈다.
pf_build_plan() {
  pf_dry build-plan "python3 dev-package/tools/dev-seed/build_plan.py --dry-run — exit 0 ＋ 「datasets 28 edges 18」" && return
  # 표준오류까지 읽어야 미달 사유가 남는다 — `run_capture` 는 stderr 를 로그로 보낸다.
  local tmp; tmp="$(mktemp)"
  local out rc=0
  python3 "$REPO_ROOT/dev-package/tools/dev-seed/build_plan.py" \
    --dry-run --ref-root "$COLAB_REF_ROOT" --md-root "$MD_ROOT" > "$tmp" 2>&1 || rc=$?
  out="$(cat "$tmp")"; rm -f "$tmp"
  printf '%s\n' "$out" | redact >> "$STAGE_LOG"
  if [ "$rc" -ne 0 ]; then
    pf_fail build-plan "비영 종료 $rc — $(printf '%s' "$out" | tail -2 | tr '\n' ' ')"; return
  fi
  if printf '%s\n' "$out" | grep -qx "datasets $EXPECT_DATASETS edges $EXPECT_EDGES"; then
    pf_pass build-plan "datasets $EXPECT_DATASETS edges $EXPECT_EDGES"
  else
    pf_fail build-plan "계수 불일치 — $(printf '%s\n' "$out" | grep -E '^datasets ' | head -1)"
  fi
}

stage_preflight() {
  PF_PASS=(); PF_FAIL=(); PF_NOTE=()
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
    log "preflight — dry-run · 10 항목 판정 없음"
    return 0
  fi
  log "preflight — 통과 ${#PF_PASS[@]} · 미달 ${#PF_FAIL[@]}"
  if [ "${#PF_FAIL[@]}" -gt 0 ]; then
    log "미달 항목: ${PF_FAIL[*]}"
    return 1
  fi
  return 0
}
