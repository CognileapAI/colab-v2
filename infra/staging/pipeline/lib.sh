# 파이프라인 공통 함수 — 단독 실행하지 않는다. source 전용.
# 이 파일은 어떤 절대경로도 담지 않는다. 경로는 전부 $HOME 또는 스크립트 상대다.
# 비밀·접속 문자열을 **읽지도 찍지도 않는다** (`〈121〉-㉯` — 접속 URL 은 값이 아니라 파일로 넘긴다).
#
# ── 이 파일이 존재하는 이유 ──────────────────────────────────────────────────
# `I3 §0` — 배포 도구가 자기 능력을 실제보다 크게 말한다. 그 말버릇의 배선이
# 「설정이 없으면 조용히 넘어가고 다음 줄에서 통과를 찍는」 모양이고, 이 레포는 그것을
# green-by-skip 이라 부른다(`CLAUDE.md §4`). 그래서 판정 어휘를 **한 곳에** 둔다 —
# 흩어 놓으면 그중 하나가 언젠가 관대해진다(`backup/lib.sh` 의 `verdict` 와 같은 이유).

set -o pipefail

log()  { printf '%s %s\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$*" >&2; }
pass() { printf '  PASS  %s\n' "$*"; }
fail() { printf '  FAIL  %s\n' "$*"; FAILED=$((FAILED+1)); }
die()  { log "ERROR: $*"; exit 1; }

# ── SKIP 규약 — `backup/lib.sh` 의 `〈170〉-㉮` 규약을 **그대로** 물려받는다 ─────
#   · **승인된 SKIP** = 사람이 명시 플래그로 유예한 것. 통과할 수 있으나 **요약줄에 건수가 반드시 나온다.**
#   · **암묵적 SKIP** = 설정·인자가 없어서 꺼진 것. **존재하지 않는다 — 전부 `fail` 이다.**
# 배포 파이프라인은 이 실패 유형의 본거지다. 「대상이 없어서 검사가 0건인데 exit 0」 이
# 정확히 2026-08-23 P1 배포가 낸 모양이다(`I3 §0-1`).
skip_ack() { printf '  SKIP  %s\n' "$*"; SKIPPED=$((SKIPPED+1)); }

verdict() { # $1=대상 이름(요약줄 앞머리)
  local what="${1:-결과}"
  local sk=""; [ "${SKIPPED:-0}" -ne 0 ] && sk=" · 승인된 SKIP ${SKIPPED}건"
  if [ "${FAILED:-0}" -ne 0 ]; then
    echo "$what: RED (실패 ${FAILED}건${sk})"; return 1
  fi
  if [ "${CHECKED:-1}" -eq 0 ]; then
    # 검사 대상 0건은 통과가 아니다. `gates/README.md` 의 「대상 0건 = red」 원칙 그대로.
    echo "$what: RED (검사 대상 0건 — 아무것도 검사하지 않았다)"; return 1
  fi
  if [ "${SKIPPED:-0}" -ne 0 ]; then
    echo "$what: GREEN (통과 ${CHECKED:-?}건 · **승인된 SKIP ${SKIPPED}건** — 무엇을 안 봤는지는 위 SKIP 줄)"; return 0
  fi
  echo "$what: GREEN (통과 ${CHECKED:-?}건 · SKIP 0 — 모든 항목이 실제로 돌았다)"; return 0
}

# ── 상태 디렉터리 ───────────────────────────────────────────────────────────
# 원장·표식·잠금이 사는 자리. **레포 밖 홈**이다 — 값은 런타임 생성물이고 커밋 대상이 아니다.
# `backup` 쪽 `$HOME/colab-v2-backups` 와 형제 관계다(`I3` 결정 3 = `IS3 §10` 과 모양을 맞춘다).
pipeline_state_dir() { printf '%s' "${COLAB_PIPELINE_STATE_DIR:-$HOME/colab-v2-releases}"; }

LEDGER_NAME="release-ledger.tsv"
FAILED_MARK="DEPLOY-FAILED.txt"
LAST_SUCCESS="LAST-SUCCESS.txt"
APPROVAL_NAME="release-ledger.tsv"   # 결정 6 = 승인 기록은 **릴리스 원장과 같은 파일**이다

ledger_path()   { printf '%s/%s' "$(pipeline_state_dir)" "$LEDGER_NAME"; }
failmark_path() { printf '%s/%s' "$(pipeline_state_dir)" "$FAILED_MARK"; }
success_path()  { printf '%s/%s' "$(pipeline_state_dir)" "$LAST_SUCCESS"; }

state_init() { mkdir -p "$(pipeline_state_dir)" || die "상태 디렉터리를 만들지 못했다"; }

# ── 릴리스 원장 (`I3` 결정 3 · `〈168〉-㉱`) ───────────────────────────────────
# 평문 append-only. 한 줄 = 탭 구분 6칸.
#   시각 · 종류(deploy|rollback|approve) · 커밋 SHA · 이미지 태그 · 판정(green|red) · 비고
# **보존 = 릴리스 30건**(이미지 3개보다 길게 남긴다 — 원장은 이력이고 이미지는 실물이다).
# ⚠ 원장에 남았으나 이미지가 없는 릴리스로는 롤백할 수 없다. 그 구분은 `ledger_rollback_target`
#   이 **이미지 실물을 확인해서** 낸다 — 원장 한 줄이 곧 롤백 가능을 뜻하지 않는다.
LEDGER_KEEP="${COLAB_LEDGER_KEEP:-30}"

ledger_append() { # $1=종류 $2=SHA $3=태그 $4=판정 $5=비고
  state_init
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$(date +%Y-%m-%dT%H:%M:%S%z)" "$1" "$2" "$3" "$4" "${5:-}" >> "$(ledger_path)"
  ledger_prune
}

ledger_prune() {
  local f; f="$(ledger_path)"; [ -f "$f" ] || return 0
  local n; n="$(wc -l < "$f")"
  [ "$n" -le "$LEDGER_KEEP" ] && return 0
  tail -n "$LEDGER_KEEP" "$f" > "$f.tmp" && mv "$f.tmp" "$f"
}

# 직전 green 릴리스의 태그 — **이미지 실물이 남아 있는 것 중** 가장 최근, 현재 배포본 제외.
# 없으면 아무것도 출력하지 않고 1 을 반환한다(호출처가 red 를 낸다. 조용한 성공을 만들지 않는다).
ledger_rollback_target() { # $1=현재 태그(제외 대상, 비어도 된다)
  local cur="${1:-}" f tag
  f="$(ledger_path)"; [ -f "$f" ] || return 1
  # deploy 행 · green 판정만. 최신부터 훑는다.
  while IFS=$'\t' read -r _ts kind _sha tag ok _note; do
    [ "$kind" = deploy ] || continue
    [ "$ok" = green ] || continue
    [ -n "$tag" ] || continue
    [ "$tag" = "$cur" ] && continue
    images_exist "$tag" || continue
    printf '%s' "$tag"; return 0
  done < <(tac "$f")
  return 1
}

# ── 이미지 ──────────────────────────────────────────────────────────────────
# 배포 단위 5종. `compose.i2.yml` 의 `image:` 와 **같은 목록**이어야 한다 —
# 여기서 하나 빠지면 「보존했다」가 4/5 를 뜻하게 되고, 그 차이는 롤백할 때만 보인다.
RELEASE_IMAGES=(core-api pipeline-worker viz-render ai-service frontend migrator)

images_exist() { # $1=태그 → 6종이 **전부** 있어야 0
  local tag="$1" n
  for n in "${RELEASE_IMAGES[@]}"; do
    docker image inspect "colab-v2/$n:$tag" >/dev/null 2>&1 || return 1
  done
  return 0
}

# 보존 = 최근 3개 (`〈168〉-㉰`). 원장 순서를 정본으로 삼는다 — `docker images` 의 생성 시각이
# 아니다. 태그가 재생성되면 시각이 흔들리지만 원장은 흔들리지 않는다.
IMAGE_KEEP="${COLAB_IMAGE_KEEP:-3}"

# ⚠ **별칭 태그는 릴리스가 아니다.** `:prev`(빌드 전 보존) 와 `:i2`(복원 리허설용 호환 별칭)
#   는 보존 3개의 계산에 넣지 않고, **지우지도 않는다.** 여기서 지우면 정리가 되돌릴 손잡이를
#   같이 걷어 간다 — 보존을 하는 코드가 보존을 깨는 모양이 된다.
ALIAS_TAGS=(prev i2)

# ── 별칭 재부착 — **실패를 삼키지 않는다** (`X-6` · `PLAN-SoT §9 〈185〉-㉸`-⑵) ────────
# 종전 `deploy.sh` ⑫ 는 `docker tag … 2>/dev/null || true` 였다. 무조건 성공이다.
# 재부착이 실패하면 `:i2` 가 **옛 이미지를 계속 가리키는데 배포는 GREEN 을 찍었고**,
# 복원 리허설(`compose.throwaway.yml`)이 바로 그 이름으로 이미지를 찾으므로
# **옛 이미지를 리허설하며 통과를 낸다.** 이 레포 대표 실패형(green-by-skip)과 같은 무늬다.
#
# ⚠ **「붙였다」와 「그 이름이 그 이미지를 가리킨다」는 다르다.** `docker tag` 의 종료코드만 보면
#   앞의 것만 안다. 그래서 붙인 **뒤에** `image inspect` 로 이미지 ID 를 대조한다 — 사후 검증이다.
#
# ⚠ **정상 부재는 없다.** 이 함수가 불리는 자리(⑫)는 ④ 빌드가 방금 `colab-v2/$n:$tag` 를
#   구운 뒤다. 대상 `:i2` 가 없는 것은 첫 배포에서 정상이지만 그건 `docker tag` 의 **결과**이지
#   실패가 아니다. 반대로 **원본 `:$tag` 의 부재는 어떤 경우에도 정상이 아니다** — 굽지 않았거나
#   이름을 잃은 것이고 둘 다 red 다. 그래서 부재와 실패를 원본/대상으로 가른다.
alias_reattach() { # $1=릴리스 태그 → 6종 전부 `:i2` 가 그 태그를 가리켜야 0
  local tag="${1:-}" n src dst want got rc=0 okn=0
  [ -n "$tag" ] || { log "별칭 재부착 RED — 릴리스 태그가 비었다. 무엇을 가리킬지 모르는 재부착은 red 다"; return 1; }
  for n in "${RELEASE_IMAGES[@]}"; do
    src="colab-v2/$n:$tag"; dst="colab-v2/$n:i2"
    if ! want="$(docker image inspect -f '{{.Id}}' "$src" 2>/dev/null)"; then
      log "  별칭 RED $n — 원본 $src 이 없다 (빌드 산출이 이름을 잃었다)"; rc=1; continue
    fi
    if ! docker tag "$src" "$dst"; then
      log "  별칭 RED $n — docker tag $src → $dst 가 실패했다"; rc=1; continue
    fi
    if ! got="$(docker image inspect -f '{{.Id}}' "$dst" 2>/dev/null)"; then
      log "  별칭 RED $n — 붙인 뒤에도 $dst 이 조회되지 않는다"; rc=1; continue
    fi
    if [ "$got" != "$want" ]; then
      log "  별칭 RED $n — $dst 이 ${got:7:12} 를 가리킨다 (기대 ${want:7:12}). **옛 이미지가 남았다**"; rc=1; continue
    fi
    okn=$((okn+1))
    log "  별칭 colab-v2/$n:i2 ← $tag (${want:7:12})"
  done
  # 검사 대상 0건은 통과가 아니다 (`gates/README.md` 「대상 0건 = red」).
  if [ "$okn" -eq 0 ]; then log "별칭 재부착 RED — 재부착에 성공한 것이 0건이다"; return 1; fi
  if [ "$rc" -ne 0 ]; then log "별칭 재부착 RED — ${#RELEASE_IMAGES[@]}종 중 ${okn}종만 $tag 를 가리킨다"; return 1; fi
  log "별칭 재부착 GREEN — ${okn}/${#RELEASE_IMAGES[@]}종의 :i2 가 $tag 를 가리킨다(이미지 ID 대조 완료)"
  return 0
}

image_prune() { # $1=지금 배포한 태그(무조건 보존)
  local keep=("$1" "${ALIAS_TAGS[@]}") f tag n
  f="$(ledger_path)"; [ -f "$f" ] || return 0
  while IFS=$'\t' read -r _ts kind _sha tag ok _note; do
    [ "$kind" = deploy ] || continue; [ "$ok" = green ] || continue; [ -n "$tag" ] || continue
    case " ${keep[*]} " in *" $tag "*) continue ;; esac
    keep+=("$tag")
    # 별칭은 개수에 안 넣는다 — 「최근 3개」는 릴리스 3개다.
    [ $(( ${#keep[@]} - ${#ALIAS_TAGS[@]} )) -ge "$IMAGE_KEEP" ] && break
  done < <(tac "$f")
  log "이미지 보존 대상 릴리스 $(( ${#keep[@]} - ${#ALIAS_TAGS[@]} ))개 + 별칭 ${#ALIAS_TAGS[@]}개: ${keep[*]}"
  for n in "${RELEASE_IMAGES[@]}"; do
    docker images --format '{{.Repository}}:{{.Tag}}' "colab-v2/$n" 2>/dev/null | while read -r ref; do
      tag="${ref##*:}"
      [ "$tag" = "<none>" ] && continue
      case " ${keep[*]} " in *" $tag "*) continue ;; esac
      log "  삭제 $ref"
      docker image rm "$ref" >/dev/null 2>&1 || log "  (참조 중이라 남겨 둔다: $ref)"
    done
  done
}

# ── 표식 파일 (`IS3 §10` 3종과 같은 모양) ────────────────────────────────────
# ⚠ 알림 통로(메일·메신저)는 **`I4` 로 이관됐다**(`〈168〉-㉮`). 표식은 「가서 봐야 보이는」
#   자리이고 그 한계는 여기 적어 둔 것이 전부다 — 자동 트리거가 붙으면 이 침묵의 비용이
#   사람이 부르던 때보다 커진다(`I3 §7-6`).
mark_failed() { # $1=단계 $2=사유
  state_init
  { echo "$(date +%Y-%m-%dT%H:%M:%S%z) 배포 실패 — 단계: $1"
    echo "사유: $2"
    echo "로그: $(pipeline_state_dir)/pipeline.log 를 보라."
    echo "이 파일은 **다음 성공에서만** 사라진다."
    echo "자동 롤백은 기본 off 다(〈168〉-㉳). 되돌리려면 사람이 rollback.sh 를 부른다."
  } > "$(failmark_path)"
  log "!!! 표식 파일 생성 — $(failmark_path)"
}

mark_success() { # $1=태그
  state_init
  echo "$(date +%Y-%m-%dT%H:%M:%S%z) deploy OK $1" >> "$(success_path)"
  rm -f "$(failmark_path)"
}

# ── 단일 실행 잠금 ──────────────────────────────────────────────────────────
# 자동 트리거가 붙는 순간 겹쳐 도는 것은 가정이 아니라 시간문제다(`I3 §2-7`).
# ⚠ **한 호스트 안의 잠금**이다. 호스트가 죽는 동안의 상태 일관성은 다루지 못한다(`I3 §7-3`).
pipeline_lock() { # 겹치면 즉시 종료(대기하지 않는다 — 크론이 5분마다 쌓이는 것을 막는다)
  # 부모가 이미 쥐고 있으면 그대로 쓴다 — `run-pipeline.sh` → `deploy.sh` 처럼 한 흐름 안에서
  # 두 번 잠그면 자기 자신에게 막힌다. **잠금은 흐름 하나당 하나다.**
  if [ "${COLAB_PIPELINE_LOCK_HELD:-0}" = 1 ]; then return 0; fi
  state_init
  exec 9>"$(pipeline_state_dir)/pipeline.lock"
  if ! flock -n 9; then
    log "다른 파이프라인이 돌고 있다 — 이번 회차는 돌지 않는다(겹쳐 돌지 않는다)"
    exit 75   # EX_TEMPFAIL. 실패 표식을 만들지 않는다 — 고장이 아니라 양보다.
  fi
  export COLAB_PIPELINE_LOCK_HELD=1
}
