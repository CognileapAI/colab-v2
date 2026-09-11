# TL-2 staging 실행 패킷

## 고정점과 실제 조사

코드 기준은 `d56428d6945d677cae013d6bff25cb61727f3166`이다. 현재 staging은
`09e2b9b2db1a`를 서빙한다. 최종 문서 통합 뒤 후보 SHA가 달라지므로 실행 직전 승인된 최종 SHA와
이미지를 다시 묶는다. 이번 조사에서 배포·재기동·cron·DB 쓰기/role 변경·snapshot 발행·S3 변경/삭제는 0건이다.

2026-09-11 읽기 전용 실측은 다음과 같다.

| 항목 | 실제 값 | 판정 |
|---|---:|---|
| Docker | 29.3.0 | 사용 가능 |
| network | `colab-v2-staging_default` bridge | 존재 |
| 현재 viz | UID 10001, GID 999 | 후보 이미지에서 재측정 |
| ownership volume | `colab-v2-staging_ownership-ledger` | 없음 |
| backup 설정 | UID/GID 1000:1000, mode 0600 | 값 미출력 |
| 기존 URL 파일 5개 | UID/GID 10001:10001, mode 0600, `postgresql+psycopg` | owner/app role라 입력 불가 |
| `pg_read_all_data` | super=false, bypass=false, readall=true | 로그인 발행 role 아님 |
| `postgres` | super=true, bypass=true, readall=true | publisher 권한식 충족 |
| 전용 비-superuser role | 없음 | 요구 시 승인 범위 확대 |

기존 `platform-owner-db.url`은 스킴은 맞지만 `colab_owner`가 전수 권한식을 통과하지 못한다.
backup의 postgres 자격은 새 권한 없이 재사용 가능하다. host 연결은 SCRAM이라 무암호 URL은 쓸 수 없다.

## 승인 뒤 준비

아래 셸 블록 실행 전 staging env를 mode0600 백업하고, 이 문서의 세 ownership 키를 중복 없이 먼저 반영한다. Compose는 build에서도 필수 환경값을 검사한다.

아래 명령의 cwd는 최종 후보 SHA의 **별도 clean 빌드 사본**이다. I3 전용
`/home/ttlhi10/colab-v2-staging-deploy`는 부모 d564에 유지한다. 그 사본을 이미지 준비 때문에
미리 fast-forward하지 않는다. 후보 full SHA, 부모 SHA, 원격 main과 이미지 ID를 별도 봉인한다.

```bash
set -euo pipefail
export CANDIDATE_SHA12='<승인된-최종-SHA-12자리>'
export STAGING_ENV="$HOME/.colab-v2-staging.env"
export BACKUP_ENV="$HOME/.colab-v2-staging-backup.env"
export OWNERSHIP_URL_FILE="/etc/colab/ownership-platform-db.url"
export OWNERSHIP_RUNNER='/opt/colab-v2/publish-ownership-snapshot.sh'
test "$(git rev-parse --short=12 HEAD)" = "$CANDIDATE_SHA12"
test -z "$(git status --porcelain)"
test "$(stat -c '%a' "$STAGING_ENV")" = 600
test "$(stat -c '%a' "$BACKUP_ENV")" = 600
export COLAB_RELEASE_TAG="$CANDIDATE_SHA12"
docker compose -p colab-v2-staging -f infra/staging/compose.i2.yml --env-file "$STAGING_ENV" build core-api viz-render
docker image inspect --format '{{.Id}}' "colab-v2/core-api:$CANDIDATE_SHA12" "colab-v2/viz-render:$CANDIDATE_SHA12"
docker image inspect "colab-v2/core-api:$CANDIDATE_SHA12" >/dev/null
docker image inspect "colab-v2/viz-render:$CANDIDATE_SHA12" >/dev/null
test "$(docker run --rm --entrypoint id "colab-v2/viz-render:$CANDIDATE_SHA12" -u)" = 10001
VIZ_GID="$(docker run --rm --entrypoint id "colab-v2/viz-render:$CANDIDATE_SHA12" -g)"
test "$VIZ_GID" = 999
```

staging env에는 승인된 준비에서 아래 키를 정확히 한 번 반영한다. 기존 키는 대조하고 중복 append하지 않는다.

```dotenv
COLAB_VIZ_OWNERSHIP_SNAPSHOT_OWNER_UID=0
COLAB_VIZ_OWNERSHIP_SNAPSHOT_GROUP_GID=999
COLAB_VIZ_OWNERSHIP_SNAPSHOT_MAX_AGE_SECONDS=7200
```

### root:root 0600 psycopg URL

원본 prefix `postgresql+psycopg`를 고정한다. URL 값은 출력하지 않고 임시 파일도 root 0600으로 만든다.

```bash
sudo -n bash -c '
set -euo pipefail
set -a; . /home/ttlhi10/.colab-v2-staging.env; . /home/ttlhi10/.colab-v2-staging-backup.env; set +a
: "${COLAB_PG_SUPER_PASSWORD:?}"; : "${COLAB_BACKUP_DB_platform:?}"
dir=/etc/colab; out=$dir/ownership-platform-db.url
if [ ! -e "$dir" ]; then install -d -o root -g root -m 0700 "$dir"; fi
test -d "$dir"; test ! -L "$dir"
test ! -e "$out"; test ! -L "$out"
tmp="$(mktemp "$dir/.ownership-platform-db.url.XXXXXX")"; trap '\''rm -f "$tmp"'\'' EXIT
python3 - "$tmp" <<'\''PY'\''
import os,pathlib,sys
from urllib.parse import quote
p=quote(os.environ["COLAB_PG_SUPER_PASSWORD"],safe="")
d=quote(os.environ["COLAB_BACKUP_DB_platform"],safe="")
pathlib.Path(sys.argv[1]).write_text(f"postgresql+psycopg://postgres:{p}@postgres/{d}\n")
PY
chown root:root "$tmp"; chmod 0600 "$tmp"; ln "$tmp" "$out"; rm "$tmp"; trap - EXIT
test "$(stat -c "%u:%g:%a" "$out")" = 0:0:600
test "$(sed "s/:.*//" "$out")" = postgresql+psycopg
'
```

자격 파일 생성은 별도 실행 승인 뒤에만 한다. 전용 최소권한 role은 `CREATE ROLE`,
`GRANT pg_read_all_data`, `ALTER ROLE ... BYPASSRLS`, secret 발급이 필요해 현재 범위 밖이다.
기존 postgres 경로는 privilege 변경이 필요 없다.
기존 `/etc/colab`의 mode/owner를 바꾸지 않는다. 목적지가 이미 있으면 값을 출력하거나
덮어쓰지 않고 중단하여 기존 입력인지 확인한다. 준비는 독점 실행 창에서 수행한다.

### volume, 최초 발행, 배포 순서

```bash
sudo -n install -o root -g root -m 0755 infra/staging/tools/publish-ownership-snapshot.sh "$OWNERSHIP_RUNNER"
set -a; . "$STAGING_ENV"; set +a
export COLAB_RELEASE_TAG="$CANDIDATE_SHA12"
docker compose -p colab-v2-staging -f infra/staging/compose.i2.yml --env-file "$STAGING_ENV" up --no-deps --abort-on-container-exit --exit-code-from volume-init volume-init
docker network inspect colab-v2-staging_default >/dev/null
docker volume inspect colab-v2-staging_ownership-ledger >/dev/null
sudo -n env COLAB_OWNERSHIP_COMPOSE_PROJECT=colab-v2-staging \
  COLAB_OWNERSHIP_CORE_IMAGE="colab-v2/core-api:$CANDIDATE_SHA12" \
  COLAB_OWNERSHIP_DB_URL_FILE="$OWNERSHIP_URL_FILE" \
  COLAB_OWNERSHIP_VIZ_GID="$VIZ_GID" "$OWNERSHIP_RUNNER"
```

`volume-init`은 기존 앱을 교체하지 않는다. publisher 출력은 schema, 시작시각, D3/D5 counts,
content SHA만 허용한다. ID/URL 노출, 권한 거절, count/dump 불일치는 중단 조건이다.

```bash
docker run --rm --user 0:0 \
 --mount type=volume,src=colab-v2-staging_ownership-ledger,dst=/ledger,readonly alpine:3.20 sh -ceu '
 test "$(stat -c "%u:%g:%a" /ledger)" = "0:999:550"
 test "$(stat -c "%u:%g:%a" /ledger/current.json)" = "0:999:440"
 test -s /ledger/current.json
 '
docker run --rm --network none --entrypoint python \
 --mount type=volume,src=colab-v2-staging_ownership-ledger,dst=/srv/ownership-ledger,readonly \
 "colab-v2/viz-render:$CANDIDATE_SHA12" -c 'from pathlib import Path; from colab_viz.domains.d7_visualization.ownership_snapshot import load; load(Path("/srv/ownership-ledger/current.json"), max_age_seconds=7200, expected_owner_uid=0, expected_group_gid=999); print("snapshot_consumer_read_green")'
```

소비자 검증은 이미지 기본 사용자(10001:999)로 실행하며 root 성공으로 대신하지 않는다.
발행 뒤 배포까지 7200초를 넘기면 배포 직전 재발행·소비자 재검증한다.
I3가 후보를 재빌드하면 최종 이미지 ID와 실제 시작 로그를 다시 연결한다.

이후 같은 `CANDIDATE_SHA12`로 I3 배포하고 `verify-deploy` 전 항목과 8 healthy를 확인한다.
한 due pass에서 ownership 4등급, legacy 3등급, unreachable, `deleted=0`, snapshot 시각/count/SHA를
함께 회수한다. invalid/stale은 준비 red이며 0건으로 접지 않는다. 이 실제 한 주기 전에는 TL-2 ⑤가 미완료다.

## 매시간 publisher

한 주기 green 뒤 별도 승인으로 root:root 0700 wrapper를 만든다.

```bash
sudo -n test ! -e /opt/colab-v2/publish-ownership-hourly
sudo -n test ! -L /opt/colab-v2/publish-ownership-hourly
sudo -n tee /opt/colab-v2/publish-ownership-hourly >/dev/null <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec env COLAB_OWNERSHIP_COMPOSE_PROJECT=colab-v2-staging \\
 COLAB_OWNERSHIP_CORE_IMAGE=colab-v2/core-api:$CANDIDATE_SHA12 \\
 COLAB_OWNERSHIP_DB_URL_FILE=$OWNERSHIP_URL_FILE COLAB_OWNERSHIP_VIZ_GID=$VIZ_GID \\
 /opt/colab-v2/publish-ownership-snapshot.sh
EOF
sudo -n chown root:root /opt/colab-v2/publish-ownership-hourly
sudo -n chmod 0700 /opt/colab-v2/publish-ownership-hourly
```

별도 cron 승인 뒤 **root 사용자 crontab**에 기존 내용을 백업·보존하고 아래 블록을
정확히 한 번 추가한다. 일반 사용자 crontab이나 사용자 필드가 필요한 `/etc/cron.d` 형식이 아니다.
독점 실행 창에서 기존 블록·wrapper가 없음을 재확인하고 설치 직후 diff와 root 실행을 확인한다.

```cron
# >>> colab-v2-staging-ownership-snapshot >>>
17 * * * * /opt/colab-v2/publish-ownership-hourly >>/var/log/colab-v2-staging-ownership.log 2>&1
# <<< colab-v2-staging-ownership-snapshot <<<
```

주기 3600초, max-age 7200초다. 2회 연속 실패 뒤 다음 due pass는 stale 준비 red여야 한다.
ownership snapshot은 삭제 후보에 연결되지 않고 기존 tile apply 상한 20도 바꾸지 않는다.
고정 이미지 태그는 이후 배포에서 함께 갱신해야 한다. 실제 cron 발행과 뒤따른 소비자 정기
한 주기 증거를 별도로 회수한다. contract-lint 1/0/0은 문서 구조 검사이며 실행 리허설 성공이 아니다.
