#!/usr/bin/env bash
# 복원 리허설 1회차 — `R1-RESTORE-DRAFT §5` 의 **1 · 3 · 6 ＋ 볼륨 왕복**.
#
# ⭑⭑ **안전 성질 — 이 스크립트는 살아 있는 staging 을 읽기만 한다.**
#    · 읽기: `pg_dump`(백업 경로 그대로) · `docker image inspect` · 볼륨 `:ro` 마운트
#    · 쓰기: **일회용 인스턴스(`r1_*`)와 임시 디렉터리에만.** 살아 있는 컨테이너·볼륨·DB·비밀 파일에
#      한 바이트도 쓰지 않는다. `--rm` 이고 호스트 포트를 열지 않으며 PGDATA 는 tmpfs 다.
#    · 그래서 **어떤 파괴적 단계보다 먼저 돌려도 안전하다.** 리허설이 사고를 앞당기지 않는다.
#
# 덮는 것(§5) — 1 `DROP SCHEMA` 비가역 구간 · 3 비밀 파일 제자리 덮어쓰기 vs `mv`(inode) ·
#               6 RLS·GRANT 생존 · ＋ 볼륨 백업 왕복(§5 #4 의 선행 결손이 이번에 채워졌다)
# 안 덮는 것 — 2 컨테이너 8개 왕복(부분) · 5 `:i2` 태그 이력(부분) · 8 원인 규명(안 덮인다)
#
# 사용: rehearsal.sh [--keep]      (`--keep` 은 실패 조사용 · 기본은 전부 지운다)
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BK="$HERE/../backup"
REPO="$(cd "$HERE/../../.." && pwd)"
. "$BK/lib.sh"; . "$BK/volume-lib.sh"
load_config; load_volume_config
IMG="${COLAB_REHEARSAL_PG_IMAGE:-postgres:16-alpine}"
KEEP=0; [ "${1:-}" = "--keep" ] && KEEP=1

W="$(mktemp -d)"; MADE=""
cleanup() { [ "$KEEP" -eq 1 ] && { echo "남긴다: $W · 컨테이너 $MADE"; return; }
            for c in $MADE; do docker rm -f "$c" >/dev/null 2>&1 || true; done; rm -rf "$W"; }
trap cleanup EXIT
BAD=0
step() { echo; echo "════════ $*"; }
ok()   { echo "  PASS  $*"; }
ng()   { echo "  FAIL  $*"; BAD=$((BAD+1)); }

up() { # $1=이름 $2=DB
  docker rm -f "$1" >/dev/null 2>&1 || true
  docker run -d --name "$1" --tmpfs /pgdata:rw,size=512m -e PGDATA=/pgdata/db \
    -e POSTGRES_PASSWORD=rehearsal -e POSTGRES_DB="$2" "$IMG" >/dev/null
  MADE="$MADE $1"
  for _ in $(seq 60); do docker exec "$1" pg_isready -U postgres -d "$2" >/dev/null 2>&1 && return 0; sleep 1; done
  ng "$1 기동 실패"; return 1
}

step "0. 재료 — 살아 있는 staging 에서 **읽어** 온다 (쓰기 0)"
"$BK/backup-full.sh" || { ng "전범위 백업 실패 — 리허설의 재료가 없다"; exit 1; }
PDUMP="$(ls -1t "$COLAB_BACKUP_DIR"/platform-*.sql.gz | head -1)"
ADUMP="$(ls -1t "$COLAB_BACKUP_DIR"/ai-*.sql.gz | head -1)"
VART="$(ls -1t "$COLAB_BACKUP_DIR"/vol-uploads-*.tar.gz | head -1)"
ok "재료 = $(basename "$PDUMP") · $(basename "$ADUMP") · $(basename "${VART:-없음}")"

step "1. §5-1 — `DROP SCHEMA public CASCADE` → 재적재 (비가역 구간을 일회용에서 통째로)"
up r1_pg_drop colab_platform || true
gunzip -c "$PDUMP" | docker exec -i r1_pg_drop psql -q -v ON_ERROR_STOP=1 -U postgres -d colab_platform >/dev/null \
  && ok "1차 적재" || ng "1차 적재 실패"
BEFORE="$("$HERE/expectations.sh" "$PDUMP" d3_dataset d3_file d4_lineage_edge)"
echo "$BEFORE" | sed 's/^/        기대치(덤프에서 읽음) /'
docker exec -i r1_pg_drop psql -q -v ON_ERROR_STOP=1 -U postgres -d colab_platform \
  -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" >/dev/null && ok "스키마 교체" || ng "스키마 교체 실패"
N="$(docker exec r1_pg_drop psql -U postgres -d colab_platform -At -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")"
[ "$N" = "0" ] && ok "교체 직후 테이블 0 — 비운 것이 맞다" || ng "교체 직후 테이블 $N (0 이어야 한다)"
gunzip -c "$PDUMP" | docker exec -i r1_pg_drop psql -q -v ON_ERROR_STOP=1 -U postgres -d colab_platform >/dev/null \
  && ok "재적재" || ng "재적재 실패"
while IFS=$'\t' read -r t n; do
  g="$(docker exec r1_pg_drop psql -U postgres -d colab_platform -At -c "SELECT count(*) FROM $t")"
  [ "$g" = "$n" ] && ok "$t = $g" || ng "$t = $g (기대 $n)"
done <<< "$BEFORE"
echo "  ⏱ 이 구간의 소요를 적어 둔다 — 실사고 때 「얼마나 걸리는가」의 유일한 근거다"

step "2. §5-3 — 비밀 파일: **제자리 덮어쓰기 vs `mv`** (inode 동작 · 양성·음성)"
# 살아 있는 비밀 파일을 쓰지 않는다. 같은 규약(0600 · `:ro` 파일 바인드)으로 **재현**한다.
mkdir -p "$W/secret"; echo "OLD" > "$W/secret/token.json"; chmod 600 "$W/secret/token.json"
docker rm -f r1_bind >/dev/null 2>&1 || true
docker run -d --name r1_bind -v "$W/secret/token.json":/etc/colab/token.json:ro \
  "$COLAB_VOLBACKUP_HELPER_IMAGE" sh -c 'while :; do sleep 5; done' >/dev/null
MADE="$MADE r1_bind"
printf 'NEW-INPLACE' > "$W/secret/token.json"        # 제자리 덮어쓰기 — inode 유지
[ "$(docker exec r1_bind cat /etc/colab/token.json)" = "NEW-INPLACE" ] \
  && ok "양성 — 제자리 덮어쓰기는 컨테이너에 즉시 보인다" \
  || ng "제자리 덮어쓰기가 안 보인다"
printf 'NEW-MOVED' > "$W/secret/token.new"; mv "$W/secret/token.new" "$W/secret/token.json"   # mv — inode 교체
if [ "$(docker exec r1_bind cat /etc/colab/token.json)" = "NEW-MOVED" ]; then
  ng "음성 실패 — `mv` 가 반영됐다. 이 호스트에서는 §4.2-1 의 근거가 성립하지 않는다(재측정 필요)"
else
  ok "음성 — `mv` 뒤에도 컨테이너는 **옛 파일을 계속 읽는다**(바인드는 inode 에 붙는다)"
fi
echo "  ⚠ 그래서 재발급 절차는 **제자리 덮어쓰기 ＋ 재기동**이다. `mv` 금지(§7.2 공통규약)."

step "3. §5-6 — RLS·GRANT 생존: `--no-privileges` 덤프를 적재하면 앱 롤이 무엇을 보는가"
up r1_pg_rls colab_platform || true
gunzip -c "$PDUMP" | docker exec -i r1_pg_rls psql -q -v ON_ERROR_STOP=1 -U postgres -d colab_platform >/dev/null || ng "적재 실패"
docker exec -i r1_pg_rls psql -q -v ON_ERROR_STOP=1 -U postgres -d colab_platform \
  -c "CREATE ROLE r1_app LOGIN NOBYPASSRLS PASSWORD 'r1';" >/dev/null 2>&1 || true
# 양성이 아니라 **음성이 먼저다** — GRANT 가 덤프에 없으므로 이 시점의 앱 롤은 못 읽는 것이 정상이다.
DENIED="$(docker exec r1_pg_rls psql -U r1_app -d colab_platform -At -c "SELECT count(*) FROM d3_dataset" 2>&1 || true)"
case "$DENIED" in *permission*|*denied*|*권한*) ok "음성 — GRANT 없는 앱 롤은 못 읽는다(덤프에 GRANT 가 없다는 사실의 실물)";;
  *) ng "앱 롤이 읽혔다: $DENIED — 덤프에 권한이 실려 있거나 롤이 면제다. **둘 다 §4.6-⑤ RED 다**";; esac
docker exec -i r1_pg_rls psql -q -U postgres -d colab_platform \
  -c "GRANT USAGE ON SCHEMA public TO r1_app; GRANT SELECT ON ALL TABLES IN SCHEMA public TO r1_app;" >/dev/null 2>&1 || true
SCOPED="$(docker exec r1_pg_rls psql -U r1_app -d colab_platform -At -c "SELECT count(*) FROM d3_dataset" 2>/dev/null || echo 실패)"
[ "$SCOPED" = "0" ] && ok "양성 — GRANT 뒤에도 스코프 없는 조회는 0행(RLS 기본 거부가 산다)" \
  || ng "GRANT 뒤 조회 = $SCOPED. 0 이 아니면 RLS 가 안 살아 있거나 정책이 다르다"
echo "  ⚠ 실 staging 의 앱 롤 권한 복구 수단은 `services/core-api/ops/app-role.sql` 이다 — 런북 §4.3 이 가리킨다"

step "4. 볼륨 왕복 — 백업 → 일회용 볼륨에 복원 → 매니페스트 전건 sha256 대조"
if [ -z "$VART" ]; then ng "볼륨 아카이브가 없다 — §5 #4 가 아직 안 채워졌다"; else
  "$BK/verify-volume-artifact.sh" "$VART" && ok "아카이브 검사 GREEN(원장 오라클 포함)" || ng "아카이브 검사 RED"
  docker volume create r1_vol_uploads >/dev/null
  gunzip -c "$VART" | docker run --rm -i -u 0:0 -v r1_vol_uploads:/vol "$COLAB_VOLBACKUP_HELPER_IMAGE" \
    sh -c 'tar -xf - -C /vol && chown -R 10001:10001 /vol' \
    && ok "일회용 볼륨에 복원" || ng "복원 실패"
  MAN="${VART%.tar.gz}.manifest.tsv"
  OUT="$(docker run --rm -i -v r1_vol_uploads:/vol:ro "$COLAB_VOLBACKUP_HELPER_IMAGE" sh -c '
    cd /vol; bad=0
    while IFS="	" read -r p s h; do [ -n "$p" ] || continue
      [ -f "$p" ] || { bad=$((bad+1)); continue; }
      [ "$(sha256sum "$p" | cut -d" " -f1)" = "$h" ] || bad=$((bad+1))
    done; echo "BAD=$bad"' < "$MAN")"
  [ "${OUT#BAD=}" = "0" ] && ok "매니페스트 전건 sha256 일치" || ng "왕복 대조 RED ($OUT)"
  docker volume rm r1_vol_uploads >/dev/null 2>&1 || true
  echo "  ⏱ **복원 소요를 다시 잰다** — 종전 실측(platform 317ms · ai 130ms · `IS3 §15`)에는 업로드 바이트가 없다(§5-7)"
fi

step "5. 이미지 digest 대장 대조 (읽기 전용 · §5-5 부분 리허설)"
"$HERE/check-image-digests.sh" && ok "대장 일치" || ng "대장 불일치 — 재기동 전에 §4.6-④ 로 판정한다"

step "6. `subjects.json` 형식 — **재발급의 절반**(§7.2 [미확인] 분할분)"
echo "  형식은 레포에서 읽힌다: services/core-api/tests/fixtures/subjects.json ＋ kernel/auth.py"
echo "  {\"<토큰문자열>\": {\"accountId\": \"<ULID>\", \"labId\": \"<ULID>\"}} — 키가 곧 베어러 토큰이다"
echo "  ⚠ **레포 픽스처 값을 staging 에 올리지 않는다.** 토큰은 새로 만든다(예: openssl rand -hex 32)"
echo "  ⚠ **여기서 증명되지 않는 것 = 완-비2**: 「재발급본으로 기동이 선다」는 컨테이너 왕복이라"
echo "     리허설 2회차(§5-2 부분 리허설)의 항목이다. 형식을 안 것과 기동이 선 것은 다르다."

echo
if [ "$BAD" -eq 0 ]; then echo "리허설 GREEN — §5 의 1·3·6 ＋ 볼륨 왕복 전건 통과"; exit 0; fi
echo "리허설 RED — $BAD 건. **`R-1` 을 닫지 않는다**"; exit 1
