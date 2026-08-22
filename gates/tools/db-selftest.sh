#!/usr/bin/env bash
# migration-single-head · schema-diff · rls-coverage 의 fail-closed 증명 (CLAUDE.md §4).
#
# 실제 db/ · services/ · contracts/ 에는 **한 글자도 쓰지 않는다** — 전부 임시 디렉터리다.
#
# boundary-selftest 와 합치지 않은 이유: 경계 게이트는 파이썬 venv 에, DB 게이트는 **도커**에 의존한다.
# 합치면 도커가 없는 환경에서 경계 증명까지 같이 죽는다 — 증명은 서로의 인프라 사고에 걸려 넘어지면 안 된다.
# 같은 이유로 이 파일 안에서도 섹션을 쪼갠다:
#   COLAB_DB_SELFTEST_ONLY=migration  → 도커가 전혀 필요 없는 부분만 (migration-single-head + rls 판정 코어)
#   COLAB_DB_SELFTEST_ONLY=db         → 도커가 필요한 end-to-end 만
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MSH="$REPO_ROOT/gates/tools/migration_single_head.py"
SD="$REPO_ROOT/gates/tools/schema-diff.sh"
RC_SH="$REPO_ROOT/gates/tools/rls-coverage.sh"
RC_PY="$REPO_ROOT/gates/tools/rls_coverage.py"
ONLY="${COLAB_DB_SELFTEST_ONLY:-all}"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" db-selftest-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
FAILURES=()

expect() { # $1=기대(green|red) $2=라벨 $3.. = 명령
  local want="$1" label="$2"; shift 2
  local out rc got
  out="$("$@" 2>&1)"; rc=$?
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$want" ]; then
    echo "[selftest] $label → $got OK"
  else
    echo "[selftest] $label → $got (기대 $want) ✗"
    echo "$out" | sed 's/^/           /'
    FAILURES+=("$label")
  fi
}

# ── 체인 fixture ─────────────────────────────────────────────────────────────
mkdb() { # $1=이름 → db 루트를 echo. 두 체인 각각 선형 2단 + schema.sql
  local r="$TMP/$1/db" c
  for c in platform ai; do
    mkdir -p "$r/$c/versions"
    printf '[alembic]\nscript_location = .\nversion_table = alembic_version_%s\n' "$c" > "$r/$c/alembic.ini"
    printf 'revision = "%s0001"\ndown_revision = None\n' "$c" > "$r/$c/versions/0001_init.py"
    printf 'revision = "%s0002"\ndown_revision = "%s0001"\n' "$c" "$c" > "$r/$c/versions/0002_next.py"
  done
  echo "$r"
}

# ── 스키마 fixture (RLS 관례를 지킨 최소 형태) ──────────────────────────────
schema_platform_ok() { cat <<'SQL'
CREATE TABLE d1_lab (id char(26) PRIMARY KEY);
CREATE TABLE alembic_version_platform (version_num varchar(32) PRIMARY KEY);
CREATE TABLE d3_dataset (id char(26) PRIMARY KEY, lab_id char(26) NOT NULL);
ALTER TABLE d3_dataset ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_dataset FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_dataset USING (lab_id = current_setting('colab.lab_id', true));
CREATE TABLE d3_file (id char(26) PRIMARY KEY, lab_id char(26) NOT NULL);
ALTER TABLE d3_file ENABLE ROW LEVEL SECURITY;
ALTER TABLE d3_file FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d3_file USING (lab_id = current_setting('colab.lab_id', true));
CREATE POLICY body_access ON d3_file USING (true);
CREATE TABLE d7_viz_source (id char(26) PRIMARY KEY, lab_id char(26) NOT NULL);
ALTER TABLE d7_viz_source ENABLE ROW LEVEL SECURITY;
ALTER TABLE d7_viz_source FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d7_viz_source USING (lab_id = current_setting('colab.lab_id', true));
CREATE POLICY body_access ON d7_viz_source USING (true);
SQL
}
schema_ai_ok() { cat <<'SQL'
CREATE TABLE alembic_version_ai (version_num varchar(32) PRIMARY KEY);
CREATE TABLE ai_lineage_suggestion (id char(26) PRIMARY KEY, lab_id char(26) NOT NULL);
ALTER TABLE ai_lineage_suggestion ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_lineage_suggestion FORCE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON ai_lineage_suggestion USING (lab_id = current_setting('colab.lab_id', true));
SQL
}
mkschema() { # $1=db 루트 — 두 체인에 기준 schema.sql 을 놓는다
  schema_platform_ok > "$1/platform/schema.sql"
  schema_ai_ok       > "$1/ai/schema.sql"
}

runmsh() { env COLAB_DB_DIR="$1" python3 "$MSH"; }

# ═════ 1. migration-single-head — 도커 불필요 ════════════════════════════════
if [ "$ONLY" != "db" ]; then
echo "── migration-single-head ────────────────────────────────────────────"

D="$(mkdb msh-clean)"
expect green "migration-single-head: 두 체인 각각 선형(head 1개)" runmsh "$D"

D="$(mkdb msh-fork-platform)"
printf 'revision = "platform0002b"\ndown_revision = "platform0001"\n' > "$D/platform/versions/0002b_fork.py"
expect red "migration-single-head: platform 체인 head 2개" runmsh "$D"

D="$(mkdb msh-fork-ai)"
printf 'revision = "ai0002b"\ndown_revision = "ai0001"\n' > "$D/ai/versions/0002b_fork.py"
expect red "migration-single-head: ai 체인 head 2개(체인별로 본다)" runmsh "$D"

D="$(mkdb msh-merge)"
printf 'revision = "platform0002b"\ndown_revision = "platform0001"\n' > "$D/platform/versions/0002b_fork.py"
printf 'revision = "platform0003"\ndown_revision = ("platform0002", "platform0002b")\n' > "$D/platform/versions/0003_merge.py"
expect green "migration-single-head: 머지 리비전으로 합친 분기" runmsh "$D"

D="$(mkdb msh-cross)"
printf 'revision = "platform0003"\ndown_revision = "ai0002"\n' > "$D/platform/versions/0003_cross.py"
expect red "migration-single-head: 체인을 넘는 down_revision(§3-3)" runmsh "$D"

D="$(mkdb msh-dup)"
printf 'revision = "platform0002"\ndown_revision = "platform0001"\n' > "$D/platform/versions/0002dup.py"
expect red "migration-single-head: revision 중복" runmsh "$D"

D="$(mkdb msh-cycle)"
printf 'revision = "platform0001"\ndown_revision = "platform0002"\n' > "$D/platform/versions/0001_init.py"
expect red "migration-single-head: 리비전 순환(head 0개)" runmsh "$D"

D="$(mkdb msh-noini)"; rm -f "$D/ai/alembic.ini"
expect red "migration-single-head: alembic.ini 부재" runmsh "$D"

D="$(mkdb msh-empty)"; rm -f "$D"/platform/versions/*.py
expect red "migration-single-head: 한쪽 체인 마이그레이션 0건" runmsh "$D"

D="$(mkdb msh-nochain)"; rm -rf "$D/ai"
expect red "migration-single-head: 체인 디렉터리 자체가 없음" runmsh "$D"

D="$(mkdb msh-syntax)"; echo 'revision = "x" down_revision' > "$D/ai/versions/0003_bad.py"
expect red "migration-single-head: 파싱 불가 파일(읽지 못함=red)" runmsh "$D"

D="$(mkdb msh-dynamic)"
printf 'import os\nrevision = os.environ["R"]\ndown_revision = "ai0002"\n' > "$D/ai/versions/0003_dyn.py"
expect red "migration-single-head: revision 이 동적(정적 판정 불가)" runmsh "$D"

D="$(mkdb msh-nodown)"; printf 'revision = "ai0003"\n' > "$D/ai/versions/0003_nodown.py"
expect red "migration-single-head: down_revision 미선언" runmsh "$D"

# ═════ 2. rls-coverage 판정 코어 — 합성 facts, 도커 불필요 ═══════════════════
echo "── rls-coverage (판정 코어) ─────────────────────────────────────────"
facts() { printf '%s\n' "$@" > "$TMP/f.tsv"; }
BASE_OK=(
$'platform\td1_lab\tf\tf\t'
$'platform\talembic_version_platform\tf\tf\t'
$'platform\td3_dataset\tt\tt\tlab_boundary'
$'platform\td3_file\tt\tt\tbody_access,lab_boundary'
$'platform\td7_viz_source\tt\tt\tbody_access,lab_boundary'
$'ai\talembic_version_ai\tf\tf\t'
$'ai\tai_lineage_suggestion\tt\tt\tlab_boundary'
)
runrc() { python3 "$RC_PY" "$TMP/f.tsv"; }

facts "${BASE_OK[@]}"
expect green "rls-coverage: 관례를 지킨 기준 facts" runrc

facts "${BASE_OK[@]}" $'platform\td6_project\tf\tf\t'
expect red "rls-coverage: allow-list 밖 테이블에 RLS 없음" runrc

facts "${BASE_OK[@]}" $'platform\td6_project\tt\tf\tlab_boundary'
expect red "rls-coverage: ENABLE 만 하고 FORCE 안 함" runrc

facts "${BASE_OK[@]}" $'platform\td6_project\tt\tt\t'
expect red "rls-coverage: RLS 는 켰는데 정책 0건" runrc

facts "${BASE_OK[@]}" $'platform\td6_project\tt\tt\tsomething_else'
expect red "rls-coverage: 연구실 경계 정책 이름 없음" runrc

facts $'platform\td1_lab\tf\tf\t' $'platform\talembic_version_platform\tf\tf\t' \
      $'platform\td3_dataset\tt\tt\tlab_boundary' \
      $'platform\td3_file\tt\tt\tlab_boundary' \
      $'platform\td7_viz_source\tt\tt\tbody_access,lab_boundary' \
      $'ai\talembic_version_ai\tf\tf\t'
expect red "rls-coverage: 본체 테이블에 본체 정책 누락(P-34 ③)" runrc

facts $'platform\td1_lab\tf\tf\t' $'platform\talembic_version_platform\tf\tf\t' \
      $'platform\td3_dataset\tt\tt\tlab_boundary' \
      $'platform\td3_file\tt\tt\tbody_access,lab_boundary' \
      $'platform\td7_viz_source\tt\tt\tbody_access,lab_boundary'
expect red "rls-coverage: ai 체인 테이블 0건" runrc

: > "$TMP/f.tsv"
expect red "rls-coverage: 테이블 0건(green-by-skip 금지)" runrc

facts $'platform\td3_dataset\tt\tt\tlab_boundary' $'ai\tai_x\tt\tt\tlab_boundary'
expect red "rls-coverage: allow-list 에만 있고 실제엔 없는 낡은 면제" runrc

facts "${BASE_OK[@]}" $'platform\td6_project\tbroken'
expect red "rls-coverage: facts 형식 오류" runrc

expect red "rls-coverage: facts 파일 부재" python3 "$RC_PY" "$TMP/nope.tsv"

facts "${BASE_OK[@]}"
expect red "rls-coverage: allow-list 설정 부재" env COLAB_RLS_ALLOWLIST="$TMP/nope.toml" python3 "$RC_PY" "$TMP/f.tsv"
fi

# ═════ 3. 도커가 필요한 end-to-end ══════════════════════════════════════════
if [ "$ONLY" != "migration" ]; then
echo "── rls-coverage · schema-diff (end-to-end, 도커 필요) ───────────────"

D="$(mkdb rc-e2e)"; mkschema "$D"
expect green "rls-coverage(e2e): 관례대로 만든 스키마" env COLAB_DB_DIR="$D" "$RC_SH"

D="$(mkdb rc-e2e-bare)"; mkschema "$D"
echo 'CREATE TABLE d6_project (id char(26) PRIMARY KEY, lab_id char(26));' >> "$D/platform/schema.sql"
expect red "rls-coverage(e2e): RLS 없는 새 테이블" env COLAB_DB_DIR="$D" "$RC_SH"

D="$(mkdb rc-e2e-noforce)"; mkschema "$D"
cat >> "$D/platform/schema.sql" <<'SQL'
CREATE TABLE d6_project (id char(26) PRIMARY KEY, lab_id char(26));
ALTER TABLE d6_project ENABLE ROW LEVEL SECURITY;
CREATE POLICY lab_boundary ON d6_project USING (true);
SQL
expect red "rls-coverage(e2e): FORCE 누락은 엔진으로만 보인다" env COLAB_DB_DIR="$D" "$RC_SH"

D="$(mkdb rc-e2e-reenabled)"; mkschema "$D"
echo 'ALTER TABLE d3_dataset NO FORCE ROW LEVEL SECURITY;' >> "$D/platform/schema.sql"
expect red "rls-coverage(e2e): 뒤에서 FORCE 를 다시 끈 경우(grep 으로는 못 본다)" env COLAB_DB_DIR="$D" "$RC_SH"

D="$(mkdb rc-e2e-noschema)"
expect red "rls-coverage(e2e): schema.sql 0건" env COLAB_DB_DIR="$D" "$RC_SH"

D="$(mkdb rc-e2e-badsql)"; mkschema "$D"; echo 'CREATE TABL oops;' >> "$D/ai/schema.sql"
expect red "rls-coverage(e2e): 적용되지 않는 스키마" env COLAB_DB_DIR="$D" "$RC_SH"

D="$(mkdb rc-e2e-nodocker)"; mkschema "$D"
expect red "rls-coverage(e2e): 도커 부재는 skip 이 아니라 red" \
  env COLAB_DB_DIR="$D" COLAB_PG_FORCE_UNAVAILABLE=1 "$RC_SH"

# ── schema-diff ──
D="$(mkdb sd-noschema)"
expect red "schema-diff: 선언 스키마 0건" env COLAB_DB_DIR="$D" "$SD"

D="$(mkdb sd-nodb)"; mkschema "$D"
expect red "schema-diff: 적용 DB 미지정(skip 아님)" env COLAB_DB_DIR="$D" "$SD"

D="$(mkdb sd-legacy-only)"; mkschema "$D"
expect red "schema-diff: 구 단일 변수만 지정(어느 체인인지 알 수 없다 → red)" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL="postgresql://postgres@127.0.0.1:1/none" "$SD"

D="$(mkdb sd-onlyplatform)"; mkschema "$D"
expect red "schema-diff: ai 체인 URL 누락(한 체인만 보고 green 내지 않는다)" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="postgresql://postgres@127.0.0.1:1/none" "$SD"

D="$(mkdb sd-unreachable)"; mkschema "$D"
expect red "schema-diff: 적용 DB 접속 불가" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="postgresql://postgres@127.0.0.1:1/none" \
      COLAB_APPLIED_DB_URL_AI="postgresql://postgres@127.0.0.1:1/none" "$SD"

D="$(mkdb sd-nodocker)"; mkschema "$D"
expect red "schema-diff: 도커 부재는 skip 이 아니라 red" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="postgresql://x/y" \
      COLAB_APPLIED_DB_URL_AI="postgresql://x/y" COLAB_PG_FORCE_UNAVAILABLE=1 "$SD"

# 적용 DB 를 실제로 띄워 체인별 green / drift 경우를 본다.
# **staging 컨테이너와 이름·포트가 겹치지 않는다** — 포트를 publish 하지 않고 컨테이너 네트워크로만 붙는다.
if [ "${COLAB_PG_FORCE_UNAVAILABLE:-0}" != "1" ] && command -v docker >/dev/null 2>&1; then
  APPC="colab_v2_gatepg_applied_$$_${RANDOM}"
  docker run -d --rm --name "$APPC" --tmpfs /pgdata:uid=70,gid=70 -e PGDATA=/pgdata/db \
    -e POSTGRES_PASSWORD=gate -e POSTGRES_HOST_AUTH_METHOD=trust \
    "${COLAB_PG_IMAGE:-postgres:16-alpine}" >/dev/null 2>&1
  trap 'docker rm -f "$APPC" >/dev/null 2>&1; rm -rf "$TMP"' EXIT
  for i in $(seq 1 60); do docker exec "$APPC" pg_isready -U postgres -q >/dev/null 2>&1 && break; sleep 1; done
  APPIP="$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$APPC")"

  # 체인마다 **다른 DB** 에 **그 체인의 선언만** 적용한다 — 이게 실제 배치 형태다 (§3-3).
  D="$(mkdb sd-match)"; mkschema "$D"
  docker exec "$APPC" createdb -U postgres applied_platform >/dev/null 2>&1
  docker exec "$APPC" createdb -U postgres applied_ai >/dev/null 2>&1
  docker exec -i "$APPC" psql -U postgres -d applied_platform -q -v ON_ERROR_STOP=1 < "$D/platform/schema.sql" >/dev/null 2>&1
  docker exec -i "$APPC" psql -U postgres -d applied_ai -q -v ON_ERROR_STOP=1 < "$D/ai/schema.sql" >/dev/null 2>&1
  U_P="postgresql://postgres@$APPIP:5432/applied_platform"
  U_A="postgresql://postgres@$APPIP:5432/applied_ai"

  expect green "schema-diff(e2e): 두 체인 모두 선언 = 적용" \
    env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="$U_P" COLAB_APPLIED_DB_URL_AI="$U_A" "$SD"

  # 체인을 뒤바꿔 붙이면 red — 게이트가 정말 체인별로 보고 있다는 증거다.
  expect red "schema-diff(e2e): 체인별 URL 을 서로 바꿔 지정" \
    env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="$U_A" COLAB_APPLIED_DB_URL_AI="$U_P" "$SD"

  # 한 체인(ai)만 드리프트 — 나머지 한 체인이 깨끗해도 red 다.
  docker exec "$APPC" psql -U postgres -d applied_ai -q -c \
    'ALTER TABLE ai_lineage_suggestion ADD COLUMN drifted text;' >/dev/null 2>&1
  expect red "schema-diff(e2e): ai 체인만 드리프트(platform 은 일치)" \
    env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="$U_P" COLAB_APPLIED_DB_URL_AI="$U_A" "$SD"

  # 한 체인(platform)만 드리프트 — 반대 방향도 red 여야 한다.
  docker exec "$APPC" psql -U postgres -d applied_ai -q -c \
    'ALTER TABLE ai_lineage_suggestion DROP COLUMN drifted;' >/dev/null 2>&1
  docker exec "$APPC" psql -U postgres -d applied_platform -q -c \
    'ALTER TABLE d3_dataset ADD COLUMN drifted text;' >/dev/null 2>&1
  expect red "schema-diff(e2e): platform 체인만 드리프트(ai 는 일치)" \
    env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="$U_P" COLAB_APPLIED_DB_URL_AI="$U_A" "$SD"

  # 한 체인의 URL 만 빠진 경우 — 나머지 한 체인이 실제로 일치해도 red (green-by-skip 금지).
  docker exec "$APPC" psql -U postgres -d applied_platform -q -c \
    'ALTER TABLE d3_dataset DROP COLUMN drifted;' >/dev/null 2>&1
  expect red "schema-diff(e2e): 일치하는 platform 만 지정하고 ai URL 누락" \
    env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="$U_P" "$SD"

  docker rm -f "$APPC" >/dev/null 2>&1
  trap 'rm -rf "$TMP"' EXIT
else
  echo "[selftest] schema-diff(e2e): 도커 없음 — 이 여섯 케이스는 증명되지 않았다 ✗"
  FAILURES+=("schema-diff(e2e) 미증명(도커 부재)")
fi
fi

# ── 판정 ─────────────────────────────────────────────────────────────────────
if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::db-selftest red — 게이트가 fail-closed 가 아니다:"
  printf '  - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "db-selftest green — DB 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명)."
