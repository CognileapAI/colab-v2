#!/usr/bin/env bash
# initdb **임시 서버**가 준비 신호를 먼저 낸다는 사실을 눈으로 확인하는 프로브.
# 게이트가 아니다 — 판정하지 않고 관측만 한다. `_pg.sh` 의 대기 정밀화가 무엇을 피하는지의 증거다.
#
# 쓰는 법: bash gates/fixtures/pg-ready/temp-server-probe.sh
# 남기는 것:
#   ① 컨테이너 로그의 시각선 — 임시 서버 ready → 임시 서버 shutdown → 초기화 완료 → 실서버 ready
#   ② 옛 대기(첫 pg_isready 성공에서 break)가 멈춘 시각과, 그 직후 확인 pg_isready 의 결과
#   ③ 새 대기(pg_wait_ready)가 멈춘 시각과, 그 직후 확인 pg_isready 의 결과
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
# shellcheck source=/dev/null
. "$ROOT/tools/_pg.sh"

IMG="${COLAB_PG_IMAGE:-postgres:16-alpine}"
C="colab_v2_gatepg_probe_$$_${RANDOM}"
trap 'docker rm -f "$C" >/dev/null 2>&1' EXIT
docker run -d --rm --name "$C" --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
  -e POSTGRES_PASSWORD=gate -e POSTGRES_HOST_AUTH_METHOD=trust "$IMG" >/dev/null || exit 1

# ② 옛 대기: 첫 pg_isready 성공에서 멈춘다 → 임시 서버에서 멈출 수 있다
for _ in $(seq 1 300); do docker exec "$C" pg_isready -U postgres -q >/dev/null 2>&1 && break; sleep 0.2; done
OLD_MARK="$(docker logs -t --tail 1 "$C" 2>&1 | tr -d '\r')"
docker exec "$C" pg_isready -U postgres -q >/dev/null 2>&1 && OLD_CONFIRM=성공 || OLD_CONFIRM=실패
echo "② 옛 대기 정지 지점 로그: $OLD_MARK"
echo "② 정지 직후 확인 pg_isready: $OLD_CONFIRM   ← '실패' 가 곧 red(준비) 오탐이다"

# ③ 새 대기
pg_wait_ready "$C" 60 && NEW=성공 || NEW=상한초과
docker exec "$C" pg_isready -U postgres -q >/dev/null 2>&1 && NEW_CONFIRM=성공 || NEW_CONFIRM=실패
echo "③ pg_wait_ready: $NEW · 직후 확인 pg_isready: $NEW_CONFIRM"

echo "① 로그 시각선:"
docker logs -t "$C" 2>&1 | grep -E 'ready to accept connections|shutting down|init process complete' | sed 's/^/   /'
