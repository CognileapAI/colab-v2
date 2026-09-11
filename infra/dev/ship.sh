#!/usr/bin/env bash
# 빌드한 tar 와 compose·up.sh 를 EC2 로 실어 `docker load` 한다 (`〈342〉-㉮`).
#
# 호스트·키는 env 로 받는다(레포에 절대경로·주소를 적지 않는다):
#   COLAB_DEV_SSH      = ec2-user@<탄력적 IP>
#   COLAB_DEV_KEY_FILE = SSH 개인키 경로(0600)
# EC2 쪽 자리 = /opt/colab-v2 (compose.yml · up.sh · images/). 시크릿(/etc/colab)은 **EC2 위에서** 만든다 — README.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
DIST="${1:-$REPO/dist}"
: "${COLAB_DEV_SSH:?COLAB_DEV_SSH 가 필요하다 (예: ec2-user@<IP>)}"
: "${COLAB_DEV_KEY_FILE:?COLAB_DEV_KEY_FILE 이 필요하다}"
SHA="$(cat "$DIST/colab-v2-dev.sha")"

# ── 반입 게이트 — `main` 이 유일한 배포 원천이다 (규칙 1 · `docs/BRANCHING.md` §2·§5 · WU-D2).
# 창 9(2026-09-06)는 `main` 밖 레인 sha 를 dev 에 실었고 그 ai 마이그레이션이 dev 에만 남았다.
# 끝나는 자리는 셋뿐이다 — 통과(ancestor=yes) · 거절(65) · 준비 실패(78). 조용한 경로는 없다.
# `COLAB_SHIP_ALLOW_NONMAIN` 의 기본값 0 은 **거절** 쪽이다(관대한 기본값이 아니다).
git -C "$REPO" fetch -q origin main \
  || { echo "origin 조회 실패 — 진행 금지" >&2; exit 78; }
MAIN_SHA="$(git -C "$REPO" rev-parse --short=12 origin/main)"
if git -C "$REPO" merge-base --is-ancestor "$SHA" origin/main; then
  ANCESTOR=yes
elif [ "${COLAB_SHIP_ALLOW_NONMAIN:-0}" = "1" ]; then
  # 선언된 우회는 허용한다. 셋에 함께 남는다 — 이 줄 · MAIN_SHA 의 bypass · deploy_doctor ⑮ 의 ✗.
  ANCESTOR=bypass
  echo "비조상 반입 · 우회 선언 — MAIN_SHA 에 ancestor=bypass 로 남고 deploy_doctor ⑮ 가 ✗ 로 잡는다"
else
  echo "sha 가 origin/main 조상이 아니다: $SHA" >&2
  echo "  긴급 반입이라면 COLAB_SHIP_ALLOW_NONMAIN=1 로 **선언**한다 (우회는 기록에 남는다)" >&2
  exit 65
fi

TAR="$DIST/colab-v2-dev-$SHA.tar"
[ -f "$TAR" ] || { echo "tar 가 없다: $TAR — build.sh 먼저" >&2; exit 2; }
"$REPO/infra/ops/build-source-bundle.sh" --repo "$REPO" --sha "$SHA" --output "$DIST"
OPS_TAR="$DIST/colab-ops-source-$SHA.tar.gz"
OPS_MANIFEST="$DIST/colab-ops-source-$SHA.manifest"
SSH=(ssh -i "$COLAB_DEV_KEY_FILE" -o IdentitiesOnly=yes "$COLAB_DEV_SSH")
SCP=(scp -i "$COLAB_DEV_KEY_FILE" -o IdentitiesOnly=yes)

"${SSH[@]}" 'sudo mkdir -p /opt/colab-v2/images /opt/colab-ops/bin /opt/colab-ops/versions && sudo chown $(id -u):$(id -g) /opt/colab-v2 /opt/colab-v2/images && sudo chown -R root:root /opt/colab-ops && sudo chmod 0755 /opt/colab-ops /opt/colab-ops/bin /opt/colab-ops/versions'
"${SCP[@]}" "$TAR" "$COLAB_DEV_SSH:/opt/colab-v2/images/"
"${SCP[@]}" "$OPS_TAR" "$OPS_MANIFEST" "$COLAB_DEV_SSH:/opt/colab-v2/images/"
"${SCP[@]}" "$HERE/compose.yml" "$HERE/up.sh" "$COLAB_DEV_SSH:/opt/colab-v2/"
"${SSH[@]}" "docker load -i /opt/colab-v2/images/$(basename "$TAR") && \
  test \"\$(sha256sum /opt/colab-v2/images/$(basename "$OPS_TAR") | cut -d' ' -f1)\" = \
       \"\$(sed -n 's/^# archive_sha256=//p' /opt/colab-v2/images/$(basename "$OPS_MANIFEST"))\" && \
  if sudo test -e /opt/colab-ops/versions/$SHA; then \
    sudo /opt/colab-ops/versions/$SHA/infra/ops/verify-reimport.sh \
      --source /opt/colab-ops/versions/$SHA \
      --incoming-manifest /opt/colab-v2/images/$(basename "$OPS_MANIFEST") --current-sha $SHA; \
  else \
    sudo mkdir /opt/colab-ops/versions/$SHA && \
    sudo tar xzf /opt/colab-v2/images/$(basename "$OPS_TAR") -C /opt/colab-ops/versions/$SHA && \
    sudo cp /opt/colab-v2/images/$(basename "$OPS_MANIFEST") /opt/colab-ops/versions/$SHA/OPS_SOURCE_MANIFEST && \
    sudo chown -R root:root /opt/colab-ops/versions/$SHA && \
    sudo chmod 0600 /opt/colab-ops/versions/$SHA/OPS_SOURCE_MANIFEST && \
    sudo /opt/colab-ops/versions/$SHA/infra/ops/verify-source.sh \
      --source /opt/colab-ops/versions/$SHA \
      --manifest /opt/colab-ops/versions/$SHA/OPS_SOURCE_MANIFEST --current-sha $SHA; \
  fi && \
  sudo install -o root -g root -m 0755 /opt/colab-ops/versions/$SHA/infra/ops/dispatch-current.sh /opt/colab-ops/bin/dispatch-current.sh && \
  sudo install -o root -g root -m 0755 /opt/colab-ops/versions/$SHA/infra/ops/verify-source.sh /opt/colab-ops/bin/verify-source.sh && \
  for u in core-api pipeline-worker viz-render ai-service migrator; do docker tag colab-v2/\$u:dev-$SHA colab-v2/\$u:dev; done && \
  echo $SHA > /opt/colab-v2/CURRENT_SHA && \
  printf 'main=%s candidate=%s ancestor=%s\n' $MAIN_SHA $SHA $ANCESTOR > /opt/colab-v2/MAIN_SHA && \
  echo 'loaded: dev-$SHA'"
echo "── 실었다: dev-$SHA. 다음 = EC2 에서 /opt/colab-v2/up.sh"
