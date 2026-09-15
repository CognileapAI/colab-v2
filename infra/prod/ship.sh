#!/usr/bin/env bash
# 빌드한 tar 와 compose·up.sh 를 EC2 로 실어 `docker load` 한다 (`〈342〉-㉮`).
#
# 호스트·키는 env 로 받는다(레포에 절대경로·주소를 적지 않는다):
#   COLAB_PROD_SSH      = ec2-user@<탄력적 IP>
#   COLAB_PROD_KEY_FILE = SSH 개인키 경로(0600)
# EC2 쪽 자리 = /opt/colab-v2 (compose.yml · up.sh · images/). 시크릿(/etc/colab)은 **EC2 위에서** 만든다 — README.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
DIST="${1:-$REPO/dist}"
[ -n "${COLAB_RELEASE_PRE_EVIDENCE:-}" ] || { echo 'release pre evidence required' >&2; exit 78; }
[ -f "$DIST/colab-v2-prod.sha" ] || exit 78
SHA="$(cat "$DIST/colab-v2-prod.sha")"
FULL_SHA="$(git -C "$REPO" rev-parse --verify "$SHA^{commit}")" || exit 78
python3 "$REPO/scripts/harness/release_evidence.py" pre --pre "$COLAB_RELEASE_PRE_EVIDENCE" --sha "$FULL_SHA" --environment prod --root "$REPO"
if [ "${COLAB_RELEASE_DRY_RUN:-0}" = 1 ]; then echo 'dry-run: no ship/up/doctor/tag'; exit 0; fi
: "${COLAB_PROD_SSH:?COLAB_PROD_SSH 가 필요하다 (예: ec2-user@<IP>)}"
: "${COLAB_PROD_KEY_FILE:?COLAB_PROD_KEY_FILE 이 필요하다}"
SHA="$(cat "$DIST/colab-v2-prod.sha")"

# ── 반입 게이트 — dev 와 **같은 한 벌**이다 (규칙 1 · `docs/BRANCHING.md` §1·§5).
# ⭑ ⟨2026-09-12⟩ prod 에는 종전에 이 게이트가 **없었다.** dev 만 막고 prod 를 열어 두면
#   규칙 1 의 구멍이 prod 쪽에 그대로 남는다 — 창 9 가 dev 에서 낸 사고를 prod 에서 다시 낸다.
# ⚠ **prod 는 조건이 하나 더 있다** — 규칙 6 은 「prod 는 `prod-YYYYMMDD` 태그에서만 배포」다.
#   원천·태그 검사 모두 우회가 없다. 승인된 사람 병합에서 후보 태그를 생성한다.
# shellcheck source=../_lib/ship-gate.sh
. "$REPO/infra/_lib/ship-gate.sh"
# ⭑ 운영 소스 번들 사슬도 dev 와 한 벌이다 (`infra/_lib/ops-bundle.sh`).
# shellcheck source=../_lib/ops-bundle.sh
. "$REPO/infra/_lib/ops-bundle.sh"
ship_gate_source_ancestor "$REPO" "$SHA" prod
ship_gate_require_prod_tag "$REPO" "$SHA"
SOURCE_REF="$SHIP_GATE_SOURCE_REF"
SOURCE_SHA="$SHIP_GATE_SOURCE_SHA"
ANCESTOR="$SHIP_GATE_ANCESTOR"

TAR="$DIST/colab-v2-prod-$SHA.tar"
[ -f "$TAR" ] || { echo "tar 가 없다: $TAR — build.sh 먼저" >&2; exit 2; }

# ── 판정 레포 tar — `/opt/colab-repo` 가 `deploy_doctor` ⑥⑦⑧ 의 **정답표**다 ──────
# 낡으면 ⑥ 이 옛 alembic head 를 정답으로 삼아 **조용히 틀린다**(dev 에서 2회 실측 ·
# `dev-package/reports/r-login-backoffice/task5/deploy-3-verify.md`). 종전에 이 동기화를
# 강제하는 자리가 **게이트에도 `ship.sh` 에도 없었고** `infra/dev/README.md` 산문뿐이었다.
# ⚠ **`git ls-files` 를 쓰지 않는다.** 이 스크립트는 배포 대상 sha 를 체크아웃한 워크트리에
#    `infra/prod` 가 **미추적 파일로만** 놓인 상태에서도 돈다(빌드 sha = 그 워크트리 HEAD).
#    판정 기준은 **실제 파일 존재**이고, 하나라도 없으면 조용히 적게 싣지 않고 거절한다.
REPO_SYNC_PATHS=(db gates services/core-api/ops infra contracts)
MISSING=()
for p in "${REPO_SYNC_PATHS[@]}"; do [ -e "$REPO/$p" ] || MISSING+=("$p"); done
if [ "${#MISSING[@]}" -gt 0 ]; then
  echo "레포 tar 대상이 없다: ${MISSING[*]} — 판정 레포(/opt/colab-repo)가 불완전해진다" >&2
  exit 2
fi
REPO_TGZ="$DIST/colab-repo-$SHA.tgz"
mkdir -p "$DIST"
# macOS 에서 만든 tar 에는 AppleDouble(`._*`·xattr) 이 섞인다 — 원격 `deploy_doctor` ⑥⑦ 이 `._0031_….py` 를
# 파싱하다 「null bytes」 로 죽었다(2026-09-13 prod 실측 · 15,353 파일). 만들 때 빼고, 받는 쪽도 지운다.
git -C "$REPO" archive --format=tar "$FULL_SHA" "${REPO_SYNC_PATHS[@]}" | gzip -n > "$REPO_TGZ"
REPO_MANIFEST="$DIST/colab-repo-$SHA.manifest"
REPO_STAGE="$(mktemp -d)"
trap 'rm -rf "$REPO_STAGE"' EXIT
tar xzf "$REPO_TGZ" -C "$REPO_STAGE"
{
  echo "# source_sha=$SHA"; echo "# source_full_sha=$FULL_SHA"
  (cd "$REPO_STAGE" && find . -type f -print0 | sort -z | xargs -0 sha256sum)
} > "$REPO_MANIFEST"
chmod 0600 "$REPO_MANIFEST"

# ── `prod.env` 의 `COLAB_IMAGE_TAG` 갱신기 — **원격 스크립트 파일**이다 ─────────────
# 종전에는 사람이 손으로 고쳤고, 빠뜨리면 **옛 migrator 이미지로 마이그레이션이 돈다**
# (dev 실측 · `〈384〉`-⑨ⓔ). heredoc 으로 원격 셸에 본문을 흘리지 않는다 — 파일로 싣고 부른다.
SETTER="$DIST/set-image-tag.sh"
{
  echo '#!/usr/bin/env bash'
  echo '# /opt/colab-v2/prod.env 의 COLAB_IMAGE_TAG 를 인자 한 값으로 맞춘다.'
  echo '# ⚠ 파일을 새로 만들지 않고 내용만 덮는다 — 소유(ec2-user)와 모드(0600)를 그대로 둔다.'
  echo 'set -euo pipefail'
  echo 'TAG="${1:?태그가 필요하다 (예: prod-<sha>)}"'
  echo 'F=/opt/colab-v2/prod.env'
  echo '[ -f "$F" ] || { echo "prod.env 가 없다: $F" >&2; exit 2; }'
  echo 'TMP="$(mktemp)"'
  echo 'grep -v "^COLAB_IMAGE_TAG=" "$F" > "$TMP" || true'
  echo 'printf "COLAB_IMAGE_TAG=%s\n" "$TAG" >> "$TMP"'
  echo 'cat "$TMP" > "$F"'
  echo 'rm -f "$TMP"'
  echo 'chmod 0600 "$F"'
  echo 'echo "prod.env: COLAB_IMAGE_TAG=$TAG"'
} > "$SETTER"
chmod +x "$SETTER"

ops_bundle_build "$REPO" "$SHA" "$DIST"
OPS_TAR="$OPS_BUNDLE_TAR"
OPS_MANIFEST="$OPS_BUNDLE_MANIFEST"
SSH=(ssh -i "$COLAB_PROD_KEY_FILE" -o IdentitiesOnly=yes "$COLAB_PROD_SSH")
SCP=(scp -i "$COLAB_PROD_KEY_FILE" -o IdentitiesOnly=yes)

"${SSH[@]}" "$(ops_bundle_prepare_cmd)"
"${SSH[@]}" 'sudo mkdir -p /opt/colab-repo && sudo chown $(id -u):$(id -g) /opt/colab-repo'
"${SCP[@]}" "$TAR" "$COLAB_PROD_SSH:/opt/colab-v2/images/"
"${SCP[@]}" "$OPS_TAR" "$OPS_MANIFEST" "$COLAB_PROD_SSH:/opt/colab-v2/images/"
"${SCP[@]}" "$REPO_TGZ" "$COLAB_PROD_SSH:/opt/colab-v2/images/"
"${SCP[@]}" "$REPO_MANIFEST" "$COLAB_PROD_SSH:/opt/colab-v2/images/"
"${SCP[@]}" "$COLAB_RELEASE_PRE_EVIDENCE" "$COLAB_PROD_SSH:/opt/colab-v2/RELEASE_PRE.json"
"${SSH[@]}" 'chmod 0600 /opt/colab-v2/RELEASE_PRE.json'
"${SCP[@]}" "$SETTER" "$COLAB_PROD_SSH:/opt/colab-v2/set-image-tag.sh"
# ⚠ **백업·크론 스크립트도 함께 싣는다** (2026-09-06 · `〈400〉`-㉳-⑶).
#    종전에는 `compose.yml`·`up.sh` **둘만** 실었고, `backup.sh`·`install-cron.sh` 를 올리는 절차가
#    README 어디에도 없었다. 그 둘은 실행 비트도 없어서 `install-cron.sh:21` 의 `[ -x ]` 검사에
#    그대로 걸렸다 — ⟹ **백업이 아예 안 걸린 채 「배포 완료」가 될 수 있는 구멍**이었다.
#    scp 는 모드를 보존하므로 레포가 `100755` 인 것이 그대로 실행 가능하게 간다.
# ⚠ `deploy-doctor.sh` 도 함께 싣는다 — 판정 진입점이 EC2 에 없으면 「판정을 못 한 채 배포 완료」가 된다.
"${SCP[@]}" "$HERE/compose.yml" "$HERE/up.sh" "$HERE/backup.sh" "$HERE/install-cron.sh" \
  "$HERE/deploy-doctor.sh" "$HERE/publish-ownership-hourly.sh" \
  "$COLAB_PROD_SSH:/opt/colab-v2/"
"${SSH[@]}" 'chmod +x /opt/colab-v2/backup.sh /opt/colab-v2/install-cron.sh /opt/colab-v2/deploy-doctor.sh /opt/colab-v2/set-image-tag.sh /opt/colab-v2/publish-ownership-hourly.sh'   # 파일시스템이 모드를 잃는 경우 대비
"${SSH[@]}" "docker load -i /opt/colab-v2/images/$(basename "$TAR") && \
  $(ops_bundle_remote_snippet "$SHA" "$(basename "$OPS_TAR")" "$(basename "$OPS_MANIFEST")") && \
  sudo mkdir -p /opt/colab-repo-releases/$FULL_SHA && \
  sudo tar xzf /opt/colab-v2/images/$(basename "$REPO_TGZ") -C /opt/colab-repo-releases/$FULL_SHA --overwrite && \
  sudo install -m 0600 /opt/colab-v2/images/$(basename "$REPO_MANIFEST") /opt/colab-repo-releases/$FULL_SHA/OPS_SOURCE_MANIFEST && \
  for u in core-api pipeline-worker viz-render ai-service migrator; do docker tag colab-v2/\$u:prod-$SHA colab-v2/\$u:prod; done && \
  echo $SHA > /opt/colab-v2/CURRENT_SHA && \
  echo $FULL_SHA > /opt/colab-v2/CURRENT_FULL_SHA && \
  printf 'source_ref=%s source_sha=%s candidate=%s ancestor=%s\n' $SOURCE_REF $SOURCE_SHA $SHA $ANCESTOR > /opt/colab-v2/MAIN_SHA && \
  echo 'loaded: prod-$SHA'"
# ⚠ `COLAB_IMAGE_TAG` 는 **불변 태그**로 적는다 — 움직이는 `:prod` 를 적으면 되돌리기 세대가 사라진다.
"${SSH[@]}" "bash /opt/colab-v2/set-image-tag.sh prod-$SHA"
echo "── 실었다: prod-$SHA"
echo "   · /opt/colab-repo = 이 sha 의 판정 레포(deploy_doctor ⑥⑦⑧ 정답표)"
echo "   · /opt/colab-v2/prod.env COLAB_IMAGE_TAG=prod-$SHA"
echo "   · 다음 = EC2 에서 /opt/colab-v2/up.sh (마이그레이션 → 기동 → healthy 4)"
