#!/usr/bin/env bash
# prod 이미지 5개를 **개발 기계에서** linux/arm64 로 빌드하고 tar 로 묶는다 (`〈342〉-㉮` 의 prod 판).
#
# 레지스트리가 없다 — buildx `--load` → 아키텍처 실측 → `docker save`. 태그는 둘: 움직이는 `:dev` 와
# 불변 `:prod-<sha>`(되돌리기용 — 직전 이미지를 잃어버렸던 교훈). geo 스택(rasterio·netCDF4·pyhdf)의
# arm64 휠이 없으면 Dockerfile 의 import 가드가 **빌드 실패**로 드러낸다 — 그것이 `[미확인]` 을 닫는 실측이다.
#
# 사용: infra/prod/build.sh [dist 디렉터리]   (기본 ./dist, 레포 밖에 두려면 인자로)
#
# ⚠ **태그의 근거는 `git HEAD` 다.** 정본 `〈335〉`-㉳ 는 prod 를 「`main` 커밋에 찍은
#   `prod-YYYYMMDD` 태그에서만」 배포하라고 정했다. 최초 구축 회차는 기능 브랜치 HEAD 로
#   세우되, **PR 병합 뒤 `main` 에서 다시 빌드·전송해 그 규율로 돌아온다.** 그 전까지
#   돌고 있는 것은 「브랜치에서 세운 prod」이고, 그 사실을 자산 대장에 적는다.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
DIST="${1:-$REPO/dist}"
SHA="$(git -C "$REPO" rev-parse --short=12 HEAD)"
PLATFORM="${COLAB_BUILD_PLATFORM:-linux/arm64}"
ARCH="${PLATFORM#linux/}"

docker buildx version >/dev/null 2>&1 || { echo "docker buildx 가 없다 — 탈출구 = EC2 위에서 빌드(README §탈출구)" >&2; exit 2; }
mkdir -p "$DIST"

build() { # $1=단위 $2=컨텍스트 $3=Dockerfile
  local unit="$1" ctx="$2" df="$3"
  echo "── build $unit ($PLATFORM)"
  docker buildx build --platform "$PLATFORM" --load \
    -t "colab-v2/$unit:prod" -t "colab-v2/$unit:prod-$SHA" -f "$df" "$ctx"
  local got; got="$(docker image inspect --format '{{.Architecture}}' "colab-v2/$unit:prod")"
  [ "$got" = "$ARCH" ] || { echo "$unit: 아키텍처가 $got 다 (기대 $ARCH) — 중단" >&2; exit 1; }
  echo "   $unit → $got ✓"
}

build core-api        "$REPO/services/core-api"        "$REPO/services/core-api/Dockerfile"
build pipeline-worker "$REPO/services/pipeline-worker" "$REPO/services/pipeline-worker/Dockerfile"
build viz-render      "$REPO/services/viz-render"      "$REPO/services/viz-render/Dockerfile"
build ai-service      "$REPO/services/ai-service"      "$REPO/services/ai-service/Dockerfile"
build migrator        "$REPO"                          "$HERE/migrator/Dockerfile"

TAR="$DIST/colab-v2-prod-$SHA.tar"
docker save -o "$TAR" \
  colab-v2/core-api:prod-$SHA colab-v2/pipeline-worker:prod-$SHA colab-v2/viz-render:prod-$SHA \
  colab-v2/ai-service:prod-$SHA colab-v2/migrator:prod-$SHA
echo "$SHA" > "$DIST/colab-v2-prod.sha"
echo "── 저장: $TAR ($(du -h "$TAR" | cut -f1)) · 태그 prod-$SHA"
