#!/usr/bin/env bash
# staging 배포 — **자기 결과를 묻는 배포.**
#
#   deploy.sh [--target staging] [--allow-dirty] [--skip-backup] [--skip-alias-reattach] [--auto-rollback]
#
# ── 이 스크립트가 고치는 세 얼굴 (`I3 §0` — DR-4·DR-5·DR-6) ──────────────────
# 뿌리는 하나였다: **배포 도구가 검증한 것보다 많이 단언했다.**
#   · DR-4 「무엇을 굽는가」 — 주석은 커밋의 산출이라 했고 코드는 **워킹트리**를 구웠다.
#   · DR-5 「무엇으로 돌아가는가」 — 태그가 `:i2` 고정이라 **직전 이미지가 이름을 잃었다.**
#   · DR-6 「무엇이 성공했는가」 — 앱 5종이 `starting` 인 채로 `exit 0` 이 나갔다.
# 셋 다 「모른다」를 「성공」으로 바꿔 말하는 모양이고, 이 레포의 표준(`㊺`·`㊽`·`D3b`)은
# 그 반대다 — **모르면 red 를 낸다.** `exit 0` 은 **검증된 green** 에만 준다.
#
# 되돌리기는 rollback.sh 다. 롤백은 **이미지만** 되돌리고 **스키마는 되돌리지 않는다**
# (`〈168〉-㉲` forward-only). 되돌리는 마이그레이션은 데이터를 지울 수 있고, 그러면
# 그것은 롤백이 아니라 재해다.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
. "$HERE/pipeline/lib.sh"

ENV_FILE="${COLAB_STAGING_ENV:-$HOME/.colab-v2-staging.env}"   # 홈의 0600 파일. 레포에 두지 않는다.

TARGET=""; ALLOW_DIRTY=0; SKIP_BACKUP=0; AUTO_ROLLBACK=0; SKIP_ALIAS=0
while [ $# -gt 0 ]; do
  case "$1" in
    --target) TARGET="${2:-}"; shift 2 ;;
    --allow-dirty)   ALLOW_DIRTY=1; shift ;;
    --skip-backup)   SKIP_BACKUP=1; shift ;;
    # ⭑ `:i2` 재부착 면제. **명시일 때만**, 그리고 건수가 원장에 남는다(`X-6`).
    #   켜면 복원 리허설(`compose.throwaway.yml`)이 **옛 이미지**를 볼 수 있다.
    --skip-alias-reattach) SKIP_ALIAS=1; shift ;;
    # ⭑ **기본값은 off 다** (`〈168〉-㉳`). 판정기를 신뢰하기 전에 자동 되돌림을 켜면
    #   판정 버그가 멀쩡한 릴리스를 계속 걷어내고, 원인이 코드인지 판정기인지 구분되지 않는다.
    --auto-rollback) AUTO_ROLLBACK=1; shift ;;
    *) echo "알 수 없는 인자: $1" >&2; exit 2 ;;
  esac
done

# ── ⓪ 타깃 — **기본값으로 떨어지지 않는다.** 어디에 배포하는지 모르는 배포는 없다.
"$HERE/pipeline/approval/target.sh" check "$TARGET" || exit $?

pipeline_lock
state_init
[ -f "$ENV_FILE" ] || die "설정 파일이 없다: \$COLAB_STAGING_ENV (홈의 0600 파일). 없으면 배포하지 않는다."

# ── ⓪-b 필수 설정 프리플라이트 — **빌드보다 먼저다** ─────────────────────────
# 2026-08-28 첫 staging 배포는 ⑦ 에서 `COLAB_OWNER_PASSWORD` 미설정으로 죽었다.
# 값은 env 파일에 있었다. 없던 것은 배선이다 — env 파일이 `--env-file` 로 **compose 에만**
# 넘어갔고, 호스트에서 직접 도는 `db-bootstrap.sh` 는 빈 환경으로 돌았다.
# 그리고 그 사실이 게이트·태그보존·빌드·백업을 **다 치른 뒤에야** 드러났다.
# 이제 두 가지를 여기서 끝낸다: env 파일을 **이 프로세스에 싣고**, 필요한 키를
# **필요로 하는 쪽에 물어서**(compose 의 `:?` + `db-bootstrap.sh required-env`) 전부 검사한다.
# 값은 화면·로그·원장 어디에도 나가지 않는다 — 나가는 것은 **키 이름과 건수**뿐이다.
. "$HERE/preflight.sh"
preflight_required "$ENV_FILE" || die "필수 설정이 갖춰지지 않았다 — 빌드하기 전에 멈춘다(위 FAIL 줄의 키 이름을 보라)"

# ── ① 무엇을 굽는가 — **커밋이다** (DR-4) ────────────────────────────────────
# 종전 주석은 「이미지 안에서 빌드하니 커밋의 산출」이라 했다. 그건 거짓이었다 —
# `docker compose build` 의 컨텍스트는 **그 순간의 워킹트리**이고, 워킹트리는 커밋이 아니다.
# 이제 **커밋임을 주장하지 않고 강제한다**: 트리가 깨끗하지 않으면 배포하지 않는다.
DIRTY_N="$(git -C "$REPO" status --porcelain 2>/dev/null | grep -c . || true)"
SHA="$(git -C "$REPO" rev-parse --short=12 HEAD 2>/dev/null || true)"
[ -n "$SHA" ] || die "git 커밋을 특정할 수 없다 — 무엇을 굽는지 모르는 배포는 red 다"
if [ "$DIRTY_N" -ne 0 ]; then
  if [ "$ALLOW_DIRTY" -eq 0 ]; then
    log "워킹트리가 깨끗하지 않다 — 변경 ${DIRTY_N}건."
    log "이미지 태그가 커밋 SHA 인데 내용이 그 커밋이 아니면 **태그가 거짓말을 한다.**"
    log "정말 굽겠다면 --allow-dirty 로 **명시**하라. 그 건수는 원장에 남는다."
    mark_failed "커밋 확인" "워킹트리 변경 ${DIRTY_N}건 (--allow-dirty 미지정)"
    ledger_append deploy "$SHA" "-" red "워킹트리 변경 ${DIRTY_N}건 — 착수 거부"
    exit 65
  fi
  # ⭑ 명시 면제. **건수를 드러낸 채** 넘어간다 — 원장에도 그대로 남는다.
  TAG="$SHA-dirty"
  log "SKIP 승인됨: 워킹트리 변경 ${DIRTY_N}건 — 태그를 '$TAG' 로 짓는다(깨끗한 커밋이 아님을 이름에 박는다)"
else
  TAG="$SHA"
fi
export COLAB_RELEASE_TAG="$TAG"
log "릴리스 태그 = $TAG (커밋 $SHA · 워킹트리 변경 ${DIRTY_N}건)"

dc() { docker compose -f "$HERE/compose.i2.yml" --env-file "$ENV_FILE" "$@"; }

abort() { # $1=단계 $2=사유
  mark_failed "$1" "$2"
  ledger_append deploy "$SHA" "$TAG" red "$1 — $2"
  log "!!! 배포 중단 — 단계 [$1] · $2"
  log "자동 롤백은 기본 off 다. 되돌리려면 사람이 rollback.sh 를 부른다(〈168〉-㉳)."
  if [ "$AUTO_ROLLBACK" -eq 1 ]; then
    log "--auto-rollback 이 명시됐다 — 직전 green 릴리스로 되돌린다"
    "$HERE/rollback.sh" --to-last-green || log "롤백도 실패했다 — 사람 호출"
  fi
  exit 70
}

# ── ② 호스트에서 게이트를 **다시** 돈다 ─────────────────────────────────────
# 클라우드 green 을 신뢰로 대체하지 않는다(`I3` 결정 4-5). 러너 OS·도구 버전이 다르면
# 결과가 갈릴 수 있고, 갈리면 **배포가 일어나는 쪽(호스트)이 정본**이다.
log "② 호스트 게이트 — migration-single-head"
"$REPO/gates/run.sh" migration-single-head || abort "게이트" "migration-single-head red"

# ── ③ 태그 보존은 **빌드보다 먼저다** (DR-5 · `I3 §0-3`) ─────────────────────
# 빌드 후에는 늦다 — 새 이미지가 이름을 가져가고 직전 이미지는 **이름 없는 dangling** 이 된다.
# 스크립트가 옳아도 돌아갈 이미지가 없으면 소용없다. 그래서 순서가 먼저다.
log "③ 직전 이미지 보존 (:prev) — 빌드 전에 한다"
PREV_IDS=""
for n in "${RELEASE_IMAGES[@]}"; do
  if id="$(docker image inspect -f '{{.Id}}' "colab-v2/$n:i2" 2>/dev/null)"; then
    docker tag "colab-v2/$n:i2" "colab-v2/$n:prev" || abort "태그 보존" "$n 태그 실패"
    PREV_IDS="$PREV_IDS$n=$id"$'\n'
    log "   보존 colab-v2/$n:prev ← ${id:7:12}"
  else
    log "   (colab-v2/$n:i2 없음 — 첫 배포로 본다)"
  fi
done

# ── ④ 빌드 — 태그는 커밋 SHA 다 (DR-4·DR-5) ─────────────────────────────────
log "④ 이미지 빌드 — 태그 $TAG"
dc --profile migrate build || abort "빌드" "docker compose build 실패"

# 보존본과 신규본의 **이미지 ID 가 실제로 다른지** 확인한다(완료 정의 14).
# 「보존했다」가 「같은 것을 두 이름으로 부른다」와 구분되지 않으면 보존이 아니다.
if [ -n "$PREV_IDS" ]; then
  same=0
  while IFS='=' read -r n oldid; do
    [ -n "$n" ] || continue
    newid="$(docker image inspect -f '{{.Id}}' "colab-v2/$n:$TAG" 2>/dev/null || echo '')"
    if [ -z "$newid" ]; then abort "빌드" "$n:$TAG 이미지가 없다"; fi
    if [ "$newid" = "$oldid" ]; then
      log "   주의 $n — 보존본과 신규본의 이미지 ID 가 같다(${oldid:7:12}). 내용 변화 없음."
      same=$((same+1))
    else
      log "   확인 $n — 보존 ${oldid:7:12} ≠ 신규 ${newid:7:12}"
    fi
  done <<< "$PREV_IDS"
  log "   이미지 ID 동일 ${same}건 (동일해도 실패는 아니다 — 코드가 안 바뀌면 같은 것이 옳다)"
fi

# ── ⑤ 배포 전 백업 — **스키마를 바꾸기 직전이 데이터가 가장 위험한 순간이다** ──
# `IS3 §7` 이 「한쪽만 덮은 백업이 전체 성공으로 기록되는 것」을 F9 픽스처로 못 박아 뒀다.
# 그 판정을 그대로 쓴다 — 두 프로파일 전부 GREEN 이 아니면 배포하지 않는다.
if [ "$SKIP_BACKUP" -eq 1 ]; then
  # ⭑ 명시 면제. 건수를 드러낸 채 넘어가고 **원장에 남는다.** 조용히 넘어가지 않는다.
  log "⑤ SKIP 승인됨: 배포 전 백업 (프로파일 2건 미실행) — --skip-backup 명시"
  BACKUP_NOTE="배포전백업SKIP(2건)"
else
  log "⑤ 배포 전 백업 — 두 프로파일 전부 GREEN 이어야 진행한다"
  "$HERE/backup/backup.sh" || abort "배포 전 백업" "backup.sh red (프로파일 중 하나 이상 실패)"
  BACKUP_NOTE="배포전백업GREEN"
fi

# ── ⑥ 저장소 먼저 — **healthy 대기가 타임아웃하면 red 다** ───────────────────
# 종전 주석은 「앱보다 postgres 가 먼저 healthy 여야 한다」고만 적었다. 헬스가 판정에
# 필요하다는 것을 알면서 **postgres 에만** 걸었고 앱 5종은 비어 있었다(DR-6).
# 이제 대기는 postgres 와 앱 5종 **양쪽**에 건다(⑩). 그리고 타임아웃은 통과가 아니라 red 다.
log "⑥ postgres 기동 대기"
dc up -d postgres || abort "postgres 기동" "up -d postgres 실패"
ok=0
for _ in $(seq 1 60); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' colab_v2_staging_pg 2>/dev/null)" = healthy ] && { ok=1; break; }
  sleep 2
done
[ "$ok" -eq 1 ] || abort "postgres 기동" "120초 안에 healthy 가 되지 않았다 — 대기 타임아웃은 red 다"

# ── ⑦ 롤 · 데이터베이스 (체인마다 하나씩 — 합치지 않는다) ────────────────────
log "⑦ 롤 · 데이터베이스"
"$HERE/db-bootstrap.sh" roles || abort "롤 부트스트랩" "db-bootstrap.sh roles 실패"

# ── ⑧ 마이그레이션 — 체인별로 따로, 소유자 롤로 ──────────────────────────────
# **forward-only 다** (`〈168〉-㉲`). 한 릴리스의 마이그레이션은 직전 이미지와도 호환되어야
# 한다(추가는 되고 파괴는 안 된다). 이를 지키지 못하는 변경은 **자동화의 일이 아니라
# 「사람이 처리할 사건」**이다 — 자동화가 스스로 처리하려 들면 그 순간 파괴적 마이그레이션이
# 무인 경로에 오른다. **체인은 끝까지 따로 돈다.** 한 번에 두 체인을 도는 "최적화"를 하지 않는다.
log "⑧ 마이그레이션 (platform)"
dc run --rm migrate-platform upgrade head || abort "마이그레이션" "platform 체인 실패"
log "⑧ 마이그레이션 (ai)"
dc run --rm migrate-ai       upgrade head || abort "마이그레이션" "ai 체인 실패"

# ── ⑨ 앱 롤 GRANT — 테이블이 생긴 뒤라야 의미가 있다 ────────────────────────
# 순서를 ⑦→⑧→⑨ 로 보존한다. GRANT 를 테이블보다 먼저 주면 `GRANT ON ALL TABLES` 가
# 빈 집합에 걸려 **조용히 아무것도 안 준다**(`I2 §2`). 값을 치르고 알아낸 순서다.
log "⑨ 앱 롤 GRANT (NOBYPASSRLS · 비소유자 검사 포함)"
"$HERE/db-bootstrap.sh" app-grants || abort "GRANT" "db-bootstrap.sh app-grants 실패"

# ── ⑩ 교체 ─────────────────────────────────────────────────────────────────
# ⭑ **⟨2026-08-31 · `PLAN-SoT §9 〈240〉`⟩ 엣지 설정 해시를 실어 보낸다.**
#   `nginx.i2.conf` 는 compose 의 **바인드 마운트**이고 이 자리는 `up -d` 뿐이다.
#   nginx 는 이미지·환경이 안 바뀌면 **재생성 대상이 아니다** — 그래서 **설정 파일을
#   고쳐도 도는 설정은 옛것**일 수 있었다. 직전 회차가 그것을 `[미확인]` 으로 남겼고
#   (`sessions/P3-EDGE-TILE-20260831.md §3`), 여기서 **우회가 아니라 절차 자체를** 고친다.
#   해시를 환경에 실으면 compose 가 **설정이 바뀐 회차에만** nginx 를 다시 만든다.
#   ⚠ 셸 환경이 `--env-file` 보다 우선한다 — 그래서 export 로 넘긴다.
#   ⚠ 그리고 **넣었다고 믿지 않는다** — 반영 여부는 ⑩-b 가 컨테이너 안의 실물로 판정한다.
EDGE_CONF="$HERE/nginx.i2.conf"
[ -f "$EDGE_CONF" ] || abort "교체" "엣지 설정 파일이 없다: nginx.i2.conf"
export COLAB_EDGE_CONF_SHA="$(sha256sum "$EDGE_CONF" | cut -c1-16)"
log "⑩ 5개 배포 단위 + 엣지 교체 (엣지 설정 해시 ${COLAB_EDGE_CONF_SHA})"
dc up -d --remove-orphans || abort "교체" "up -d 실패"

# ── ⑩-b 엣지 설정 반영 판정 — **「고쳤다」 ≠ 「돌고 있다」** ──────────────────
# 레포의 파일과 **도는 컨테이너 안의 파일**을 바이트로 대조한다. 이 판정이 없으면
# 「설정을 배포했다」가 검증 없이 단언된다 — `:i2` 재부착이 그랬던 것과 같은 모양이다.
# **모르면 red 다** — 컨테이너에 못 닿는 것도 red 이지 통과가 아니다.
log "⑩-b 엣지 설정 반영 판정 — 도는 컨테이너 안의 파일과 바이트 대조"
running_conf="$(docker exec colab_v2_staging_nginx cat /etc/nginx/conf.d/default.conf 2>/dev/null \
                 | sha256sum | cut -c1-16)" || running_conf=""
if [ -z "$running_conf" ]; then
  abort "엣지 설정 반영" "도는 nginx 에서 설정을 읽지 못했다 — 판정 불가는 red 다"
fi
if [ "$running_conf" != "$COLAB_EDGE_CONF_SHA" ]; then
  abort "엣지 설정 반영" "도는 설정이 레포 판과 다르다(도는 것 ${running_conf} ≠ 레포 ${COLAB_EDGE_CONF_SHA}) — nginx 가 재생성되지 않았다"
fi
log "   확인 엣지 설정 — 레포 판과 도는 판이 같다(${COLAB_EDGE_CONF_SHA})"

# ── ⑪ 판정 — **여기가 종료 코드의 근거다** (DR-6 · 완료 정의 2-b) ────────────
# 종전 ⑦ 은 `dc ps` 로 끝났다. `dc ps` 는 「무엇이 서빙되고 있는가」를 묻지 않는다.
# 이제 **헬스 6종 + 본문 대조 + 컨테이너 8개 + 노출 0건 + 두 체인 head** 가 판정이다.
# 앱 5종이 `starting` 인 동안은 **아직 green 이 아니다** — 대기하다 타임아웃하면 red.
log "⑪ 배포 판정 — 헬스 6종 + 본문 대조 (대기하며 재시도)"
VOK=0
for _ in $(seq 1 "${COLAB_VERIFY_TRIES:-30}"); do
  if "$HERE/verify/verify-deploy.sh" >/dev/null 2>&1; then VOK=1; break; fi
  sleep 5
done
if [ "$VOK" -ne 1 ]; then
  log "판정 실패 — 마지막 판정 출력:"
  "$HERE/verify/verify-deploy.sh" || true
  abort "배포 판정" "헬스 6종/컨테이너/노출 판정이 green 이 아니다 (대기 타임아웃 포함)"
fi
"$HERE/verify/verify-deploy.sh"
log "⑪-b 체인 판정 — 두 체인 head"
"$HERE/verify/verify-chains.sh" || abort "체인 판정" "두 체인 중 하나 이상이 적용되지 않았다"

# ── ⑫ 별칭 재부착 · 원장 · 표식 · 보존 ──────────────────────────────────────
# `:i2` 는 **릴리스 신원이 아니라 호환 별칭**이다. `compose.throwaway.yml`(복원 리허설)이
# 이 이름으로 이미지를 찾는다. 신원은 SHA 태그이고, 더 정확히는 digest 다
# (`reference/IMAGE-DIGESTS.md` — 「태그는 신원이 아니다. digest 만이 신원이다」).
#
# ⚠ 종전 이 자리는 `docker tag … 2>/dev/null || true` 한 줄이었고 **원장 green 뒤**에 있었다.
#   무조건 성공이다 — 재부착이 실패해도 원장에는 이미 green 이 적혀 있었고, 복원 리허설은
#   그 뒤로도 `:i2` 라는 이름으로 **옛 이미지를 리허설하며 통과**를 냈다(`X-6` · green-by-skip).
#   이제 세 상태다 — 요구되면 **검사한다**(붙인 뒤 이미지 ID 대조) / `--skip-alias-reattach` 로
#   **명시** 면제하면 **건수를 드러낸 채** 넘어간다 / 아무 말도 없으면 **실패한다.**
#   그리고 순서를 뒤집었다: 판정이 **원장 green 보다 먼저** 난다. 뒤에 두면 green 을 적고 죽는다.
if [ "$SKIP_ALIAS" -eq 1 ]; then
  ALIAS_NOTE="별칭재부착SKIP(${#RELEASE_IMAGES[@]}종)"
  log "SKIP 승인됨: :i2 재부착 ${#RELEASE_IMAGES[@]}종 — 복원 리허설은 **옛 이미지**를 볼 수 있다. 원장에 남는다"
else
  log "⑫-a 별칭 :i2 재부착 — 붙인 뒤 이미지 ID 로 대조한다(「붙였다」 ≠ 「가리킨다」)"
  alias_reattach "$TAG" \
    || abort "별칭 재부착" ":i2 가 $TAG 를 가리키지 않는다 — 복원 리허설이 옛 이미지를 리허설할 수 있다"
  ALIAS_NOTE="별칭재부착GREEN"
fi

# ⑫-a2 digest 이력 — **별칭이 지금 무엇을 가리키는지를 회차마다 남긴다** (Ted 판정 2026-08-29).
# 릴리스 원장이 적는 것은 태그뿐이라, `:i2` 가 덮이는 순간 **이전 값이 사라졌다.** 그래서
# 「대장 8건 중 5건 불일치」의 이력을 소급할 수 없었다(`sessions/R1-TAILS-EXEC.md §3`).
# 여기가 그 기구다. 실측이 안 되면 `[미측정]` 으로 적히고 **배포가 멈춘다** — 조용히 넘기지 않는다.
log "⑫-a2 digest 이력 원장 append (${#RELEASE_IMAGES[@]}종)"
digest_ledger_append "$TAG" i2 "${RELEASE_IMAGES[@]/#/colab-v2/}" \
  || abort "digest 이력" "별칭 :i2 의 digest 를 실측하지 못했다 — 이력이 비면 다음 회차가 대조 기준을 잃는다"
log "digest 이력: $(digest_ledger_path)"

log "⑫-b 원장 · 표식"
ledger_append deploy "$SHA" "$TAG" green "$ALIAS_NOTE digest이력=${#RELEASE_IMAGES[@]}종 $BACKUP_NOTE 워킹트리변경=${DIRTY_N}"
mark_success "$TAG"

image_prune "$TAG"

echo
echo "배포 GREEN — 커밋 $SHA · 태그 $TAG"
echo "원장: $(ledger_path)"
tail -n 1 "$(ledger_path)"
