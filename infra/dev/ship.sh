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
TAR="$DIST/colab-v2-dev-$SHA.tar"
[ -f "$TAR" ] || { echo "tar 가 없다: $TAR — build.sh 먼저" >&2; exit 2; }
SSH=(ssh -i "$COLAB_DEV_KEY_FILE" -o IdentitiesOnly=yes "$COLAB_DEV_SSH")
SCP=(scp -i "$COLAB_DEV_KEY_FILE" -o IdentitiesOnly=yes)

"${SSH[@]}" 'sudo mkdir -p /opt/colab-v2/images && sudo chown -R $(id -u):$(id -g) /opt/colab-v2'
"${SCP[@]}" "$TAR" "$COLAB_DEV_SSH:/opt/colab-v2/images/"
"${SCP[@]}" "$HERE/compose.yml" "$HERE/up.sh" "$COLAB_DEV_SSH:/opt/colab-v2/"
"${SSH[@]}" "docker load -i /opt/colab-v2/images/$(basename "$TAR") && \
  for u in core-api pipeline-worker viz-render ai-service migrator; do docker tag colab-v2/\$u:dev-$SHA colab-v2/\$u:dev; done && \
  echo $SHA > /opt/colab-v2/CURRENT_SHA && echo 'loaded: dev-$SHA'"
echo "── 실었다: dev-$SHA. 다음 = EC2 에서 /opt/colab-v2/up.sh"
