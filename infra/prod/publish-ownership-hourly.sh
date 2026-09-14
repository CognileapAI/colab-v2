#!/usr/bin/env bash
# prod 소유권 장부 스냅샷 — 매시 1회 발행 (`infra/staging/tools/publish-ownership-snapshot.sh` 의 prod 판).
#
# 무엇을 하나 — `colab_backup` 롤로 전수를 읽어 미리보기 소유 관계를 한 장의 JSON 으로 적는다.
# viz 는 그 파일을 **읽기만** 한다(`COLAB_VIZ_OWNERSHIP_SNAPSHOT` · 읽기 전용 마운트).
#   ⚠ 전수를 읽어야 하므로 자격이 `colab_backup`(BYPASSRLS)이다 — **연구실 경계를 우회하는 롤**이다.
#     그래서 URL 파일은 root 0600 이고, 이 스크립트도 root 0700 로 설치한다.
#   ⚠ 산출물은 **root 소유 0440·디렉터리 0550** 이다. viz 는 소유 uid·그룹 gid·나이가 전부 맞아야
#     쓰고, 어긋나면 거절한다 — 그 거절이 정상 동작이다(느슨하게 풀지 않는다).
#
# 왜 레포에 있나 — dev 는 이 본문이 **세션 문서의 heredoc 으로만** 있었다
# (`dev-package/sessions/20260911-stage12-execution-preparation.md`). 그 자리에 있는 것은
# 다시 설치할 때 사람이 붙여 넣어야 하고, 붙여 넣는 값이 한 글자 달라도 아무도 모른다.
#
# 값은 전부 env 로 받는다 — 기본값을 두지 않는다(`CLAUDE.md` 배포 절 6).
#   COLAB_OWNERSHIP_COMPOSE_PROJECT = prod compose 프로젝트 이름. ⚠ **실측값이다** —
#     `docker compose ls` 또는 `docker volume ls | grep ownership-ledger` 로 재고 적는다.
#     컨테이너 이름(`colab_v2_prod_*`)과 **다를 수 있다**(그쪽은 compose 가 고정한 이름이다).
#   COLAB_OWNERSHIP_CORE_IMAGE     = 불변 태그의 core-api 이미지(`colab-v2/core-api:prod-<sha>`).
#   COLAB_OWNERSHIP_DB_URL_FILE    = `/etc/colab/ownership-platform-db.url`(root 0600 ·
#                                    접두는 `postgresql+psycopg://` — dev 실측).
#   COLAB_OWNERSHIP_VIZ_GID        = viz 컨테이너의 **실제 gid**(`docker exec … id -g` · dev 는 999).
#
# 사용: sudo /opt/colab-v2/publish-ownership-hourly.sh
set -euo pipefail
: "${COLAB_OWNERSHIP_COMPOSE_PROJECT:?compose 프로젝트 이름이 필요하다 — docker compose ls 로 잰다}"
: "${COLAB_OWNERSHIP_CORE_IMAGE:?불변 태그의 core-api 이미지가 필요하다 (colab-v2/core-api:prod-<sha>)}"
: "${COLAB_OWNERSHIP_DB_URL_FILE:?colab_backup 롤 접속 문자열 파일이 필요하다}"
: "${COLAB_OWNERSHIP_VIZ_GID:?viz 컨테이너의 실제 gid 가 필요하다}"
case "$COLAB_OWNERSHIP_VIZ_GID" in ''|*[!0-9]*) echo 'viz gid 는 숫자다' >&2; exit 78 ;; esac
[ -f "$COLAB_OWNERSHIP_DB_URL_FILE" ] || { echo '접속 문자열 파일이 없다' >&2; exit 78; }
# ⚠ 모드 검사는 값을 지키는 자리다 — 느슨하면 경계 우회 자격이 새고, 그 순간 연구실 경계가 통째로 뚫린다.
MODE="$(stat -c '%a' "$COLAB_OWNERSHIP_DB_URL_FILE")"
[ "$MODE" = 600 ] || { echo "접속 문자열 파일은 0600 이어야 한다 (지금 $MODE)" >&2; exit 78; }

NETWORK="${COLAB_OWNERSHIP_COMPOSE_PROJECT}_default"
VOLUME="${COLAB_OWNERSHIP_COMPOSE_PROJECT}_ownership-ledger"
docker network inspect "$NETWORK" >/dev/null
docker volume inspect "$VOLUME" >/dev/null
docker run --rm --user 0:0 --network "$NETWORK" \
  --mount "type=bind,src=$COLAB_OWNERSHIP_DB_URL_FILE,dst=/run/secrets/backup-db.url,readonly" \
  --mount "type=volume,src=$VOLUME,dst=/srv/ownership-ledger" \
  "$COLAB_OWNERSHIP_CORE_IMAGE" python -m colab_core.app.ownership_snapshot_publisher \
  --database-url-file /run/secrets/backup-db.url \
  --output /srv/ownership-ledger/current.json --output-owner-uid 0 \
  --output-group-gid "$COLAB_OWNERSHIP_VIZ_GID"
