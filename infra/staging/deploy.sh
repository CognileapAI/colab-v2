#!/usr/bin/env bash
# WU-I2 배포 — 자리표시 오리진(compose.yml) → walking skeleton(compose.i2.yml).
#
# 되돌리기는 rollback.sh 한 줄이다. 두 스크립트가 같은 프로젝트·같은 컨테이너 이름을 쓰기 때문에
# 앞뒤 교체가 대칭이고, DNS·터널을 건드리지 않으므로 전파를 기다릴 일이 없다.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${COLAB_STAGING_ENV:-$HOME/.colab-v2-staging.env}"   # 홈의 0600 파일. 레포에 두지 않는다.
dc() { docker compose -f "$HERE/compose.i2.yml" --env-file "$ENV_FILE" "$@"; }

set -a; . "$ENV_FILE"; set +a

echo "① 이미지 빌드 — 배포되는 것이 커밋의 산출이 되도록 이미지 안에서 빌드한다"
dc --profile migrate build

echo "② 저장소 먼저 — 앱보다 postgres 가 먼저 healthy 여야 한다"
dc up -d postgres
for _ in $(seq 1 60); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' colab_v2_staging_pg 2>/dev/null)" = healthy ] && break
  sleep 2
done

echo "③ 롤 · 데이터베이스 (체인마다 하나씩 — 합치지 않는다)"
"$HERE/db-bootstrap.sh" roles

echo "④ 마이그레이션 — 체인별로 따로, 소유자 롤로"
dc run --rm migrate-platform upgrade head
dc run --rm migrate-ai       upgrade head

echo "⑤ 앱 롤 GRANT — 테이블이 생긴 뒤라야 의미가 있다. NOBYPASSRLS·비소유자 검사 포함"
"$HERE/db-bootstrap.sh" app-grants

echo "⑥ 5개 배포 단위 + 엣지 교체"
dc up -d --remove-orphans

echo "⑦ 상태"
dc ps
