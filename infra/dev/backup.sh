#!/usr/bin/env bash
# dev DB 백업 — `pg_dump | gzip` → S3 `_ops/backups/dev/` (`〈342〉-㉮` · 배포 계획서 §10-1).
#
# **왜 EC2 의 cron 인가.** RDS 자동 백업은 Free Plan 상한 때문에 **1일**뿐이다(진행 파일 08-31).
# 30일치를 들고 있는 것은 이 잡이고, 그 30일은 데이터 버킷 수명 주기 `backups-30d` 가 강제한다.
#
# **왜 컨테이너 둘인가.** `pg_dump` 는 `postgres:16-alpine` 에만 있고, S3 로 놓는 자작 SigV4 는
# core-api 이미지의 `kernel/s3.py` 에만 있다. AWS CLI·boto3 를 들이지 않는다(`CLAUDE.md` 업로드 절).
# 자격증명은 **인스턴스 프로파일**이 준다 — 이 스크립트에 키가 없다.
#
# ⚠ **조용히 실패하지 않는다.** 각 단계의 종료 코드를 보고, 하나라도 어긋나면 사유를 찍고 exit 1 한다.
#    조용히 실패하는 백업은 백업이 없는 것보다 나쁘다 — 있다고 믿는 동안 복구 수단이 없다.
# ⚠ 접두사 `_ops/backups/dev/` 는 **`deploy_doctor` 의 `BACKUP_PREFIX` 와 같아야 한다.** 어긋나면
#    doctor ⑭ 가 「객체 0건」으로 red 를 낸다(그것이 옳은 동작이다).
#
# ⚠ **root 로 돈다.** 소유자 접속 문자열(`/etc/colab/*-owner-db.url`)이 **uid 10001 소유 0600** 이라
#    `ec2-user` 로는 못 읽는다 — 그 파일들은 컨테이너가 읽으라고 그렇게 둔 것이다.
#    권한을 넓히는 대신 잡을 root 로 돌린다(`install-cron.sh` 가 그렇게 건다).
#
# 사용: sudo /opt/colab-v2/backup.sh        (cron 은 install-cron.sh 가 건다)
set -uo pipefail

BUCKET="${COLAB_BACKUP_BUCKET:-colab-platform-data-dev}"
REGION="${COLAB_BACKUP_REGION:-ap-northeast-2}"
ENVNAME="${COLAB_BACKUP_ENV:-dev}"
SECRETS="${COLAB_DEV_SECRETS_DIR:-/etc/colab}"
IMAGE="${COLAB_IMAGE_TAG:-dev}"
WORK="$(mktemp -d /tmp/colab-backup.XXXXXX)"
STAMP="$(date -u +%Y-%m-%dT%H%M%SZ)"
FAILED=0

# ⚠ 로그는 **stderr** 로 낸다. `dump_one` 이 만들어진 파일 경로를 stdout 으로 돌려주므로,
#    로그를 stdout 에 섞으면 그 경로에 로그가 딸려 들어가 실패 사유가 통째로 사라진다(2026-08-31 실측).
log() { printf '%s backup[%s] %s\n' "$(date -u +%FT%TZ)" "$ENVNAME" "$*" >&2; }
die() { log "RED — $*"; rm -rf "$WORK"; exit 1; }
trap 'rm -rf "$WORK"' EXIT

# psql/pg_dump 는 `postgresql+psycopg://` 를 URI 로 안 본다 — dbname 으로 착각해 로컬 소켓으로 떨어진다.
strip_scheme() { sed 's#postgresql+psycopg://#postgresql://#'; }

dump_one() { # $1=db 이름  $2=소유자 접속 문자열 파일
  local db="$1" urlfile="$2" out="$WORK/$1.sql.gz"
  [ -r "$urlfile" ] || { log "RED — 접속 문자열을 못 읽는다: $urlfile"; return 1; }
  # 접속 문자열은 argv 가 아니라 env 로 넘긴다 — 호스트 `ps` 에 값이 남지 않게.
  if ! PGURL="$(strip_scheme < "$urlfile")" \
       docker run --rm -e PGURL postgres:16-alpine \
         sh -c 'pg_dump --no-owner --no-privileges "$PGURL"' 2>"$WORK/$db.err" | gzip -9 > "$out"; then
    log "RED — pg_dump 실패($db): $(tail -3 "$WORK/$db.err" | tr '\n' ' ')"; return 1
  fi
  # 파이프라인은 `pipefail` 로 보되, **크기로 한 번 더 본다** — 0 바이트 덤프가 성공으로 올라가는 것을 막는다.
  local size; size="$(wc -c < "$out")"
  [ "$size" -gt 1000 ] || { log "RED — 덤프가 너무 작다($db): ${size}B"; return 1; }
  log "덤프 $db ${size}B"
  printf '%s' "$out"
}

put_one() { # $1=로컬 파일  $2=S3 키
  local file="$1" key="$2"
  # core-api 이미지는 uid 10001 로 돈다 — 읽히게 열어 준다(임시 디렉터리라 곧 지운다).
  chmod 0644 "$file"
  docker run --rm \
    -e BUCKET="$BUCKET" -e REGION="$REGION" -e KEY="$key" \
    -v "$file:/data/dump.sql.gz:ro" \
    "colab-v2/core-api:$IMAGE" python -c '
import os
from colab_core.kernel.s3 import S3Client
c = S3Client(bucket=os.environ["BUCKET"], region=os.environ["REGION"])
key = os.environ["KEY"]
payload = open("/data/dump.sql.gz", "rb").read()
c.put_object(key, payload, content_type="application/gzip")
size, _etag = c.head_object(key)          # 놓았다고 믿지 않고 **되읽어 확인**한다
if size != len(payload):
    raise SystemExit(f"크기 불일치 — 보낸 {len(payload)}B, 실제 {size}B")
print(f"올림 {key} {size}B")
' || return 1
}

log "시작 — 버킷 $BUCKET · 접두사 _ops/backups/$ENVNAME/"

# ⚠ **소유자 롤(`colab_owner`)로는 못 뜬다** — RLS 가 FORCE 라 소유자도 정책에 걸리고,
#    `pg_dump` 의 `COPY … TO stdout` 이 `query would be affected by row-level security policy`
#    로 죽는다(2026-08-31 실측). 전수 읽기 전용 롤 `colab_backup`(BYPASSRLS)로 뜬다 —
#    그 롤의 존재 이유와 경계는 `db-bootstrap.sh backup-role` 머리말에 있다.
for pair in "colab_platform:backup-platform-db.url" "colab_ai:backup-ai-db.url"; do
  db="${pair%%:*}"; urlfile="$SECRETS/${pair##*:}"
  if ! out="$(dump_one "$db" "$urlfile")"; then FAILED=1; continue; fi
  if put_one "$out" "_ops/backups/$ENVNAME/$STAMP-$db.sql.gz"; then :; else
    log "RED — 업로드 실패($db)"; FAILED=1
  fi
done

[ "$FAILED" -eq 0 ] || die "백업이 완결되지 않았다 — 위 사유를 보라"
log "GREEN — 두 데이터베이스 모두 올렸다 ($STAMP)"
