#!/usr/bin/env bash
# TL-2 ownership snapshot one-shot publisher. 설치/스케줄 변경은 하지 않는다.
set -euo pipefail
: "${COLAB_OWNERSHIP_COMPOSE_PROJECT:?compose project name is required}"
: "${COLAB_OWNERSHIP_CORE_IMAGE:?immutable core-api image is required}"
: "${COLAB_OWNERSHIP_DB_URL_FILE:?backup-role DB URL file is required}"
: "${COLAB_OWNERSHIP_VIZ_GID:?actual viz container gid is required}"
case "$COLAB_OWNERSHIP_VIZ_GID" in ''|*[!0-9]*) echo 'viz gid must be numeric' >&2; exit 78;; esac
[ -f "$COLAB_OWNERSHIP_DB_URL_FILE" ] || { echo 'backup DB URL file is missing' >&2; exit 78; }
[ "$(stat -c '%a' "$COLAB_OWNERSHIP_DB_URL_FILE")" = 600 ] || { echo 'backup DB URL file must be mode 0600' >&2; exit 78; }
network="${COLAB_OWNERSHIP_COMPOSE_PROJECT}_default"
volume="${COLAB_OWNERSHIP_COMPOSE_PROJECT}_ownership-ledger"
docker network inspect "$network" >/dev/null
docker volume inspect "$volume" >/dev/null
docker run --rm --user 0:0 --network "$network" \
  --mount "type=bind,src=$COLAB_OWNERSHIP_DB_URL_FILE,dst=/run/secrets/backup-db.url,readonly" \
  --mount "type=volume,src=$volume,dst=/srv/ownership-ledger" \
  "$COLAB_OWNERSHIP_CORE_IMAGE" python -m colab_core.app.ownership_snapshot_publisher \
  --database-url-file /run/secrets/backup-db.url \
  --output /srv/ownership-ledger/current.json --output-owner-uid 0 \
  --output-group-gid "$COLAB_OWNERSHIP_VIZ_GID"
