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

# 준비 실패로 뒤집힌 케이스를 **fail-closed 결함으로 세지 않는다.**
# 부하에서 일회용 DB 가 못 뜬 것을 「검사기가 틀렸다」로 적으면 그 보고가 거짓이 된다.
# ⚠ 여전히 RED 다 — 다만 셀프테스트 전체가 종료코드 78 로 나가 실행기가 `red(준비)` 로 적는다.
READINESS=()
expect() { # $1=기대(green|red) $2=라벨 $3.. = 명령
  local want="$1" label="$2"; shift 2
  local out rc got
  out="$("$@" 2>&1)"; rc=$?
  if [ "$rc" -eq 78 ] || printf '%s' "$out" | grep -q '::gate-readiness-failure::'; then
    printf '%s\n' "$out" | grep '::gate-readiness-failure::' | sed 's/^/           /'
    # **입력 미선언은 간헐이 아니다.** 환경이 흔들려 못 돈 것과 달리, 값이 선언되지 않았다는
    # 사실은 매번 같은 답을 낸다 — 그러므로 「판정 못 함」으로 접어 두지 않고 여기서 판정한다.
    if printf '%s' "$out" | grep -q 'cause=입력미선언'; then
      if [ "$want" = "미선언" ]; then
        echo "[selftest] $label → red(준비·입력미선언) OK"
      else
        echo "[selftest] $label → red(준비·입력미선언) (기대 $want) ✗"
        FAILURES+=("$label: 미선언으로 분류됨(기대 $want)")
      fi
      return
    fi
    if [ "$want" = "ready" ]; then
      echo "[selftest] $label → red(준비) OK (이 케이스가 재는 것이 준비 실패다)"
    else
      # 준비 실패를 「기대한 red」로 세지 않는다 — 그 케이스는 판정된 적이 없다.
      echo "[selftest] $label → red(준비) — 검사기가 못 돌았다. **판정하지 못했다**(기대 $want)"
      READINESS+=("$label (기대 $want · 판정 못 함)")
    fi
    return
  fi
  got="green"; [ $rc -eq 0 ] || got="red"
  if [ "$got" = "$want" ]; then
    echo "[selftest] $label → $got OK"
  else
    echo "[selftest] $label → $got (기대 $want) ✗"
    echo "$out" | sed 's/^/           /'
    FAILURES+=("$label")
  fi
}

# ── allow-list fixture — **레포 정본을 읽지 않는다** ─────────────────────────
# 왜 이걸 픽스처로 고정하는가:
#   selftest 의 기준 케이스(baseline-green)는 합성 스키마로 만든다. 그 합성 스키마엔 d9_* 같은
#   실제 테이블이 없다. 그런데 판정 코어가 **레포의 gates/config/rls-allowlist.toml** 을 읽으면,
#   K1 처럼 **정당하고 옳은** allow-list 추가가 일어날 때마다 「낡은 면제」 판정에 걸려
#   selftest 기준 케이스가 red 가 된다 — 게이트가 옳고 selftest 가 잘못 배선된 것이다.
#   그래서 픽스처 케이스는 자기 allow-list 를 들고 다닌다(hermetic). 「낡은 면제」 검사는
#   **그대로 둔다** — 그 검사는 이번에 실제 드리프트를 잡아 자기 값어치를 증명했다.
#   레포 정본에 대한 판정은 게이트 본체(`gates/run.sh rls-coverage`)가 본다. 여기가 볼 자리가 아니다.
FIXTURE_ALLOWLIST="$TMP/rls-allowlist.fixture.toml"
cat > "$FIXTURE_ALLOWLIST" <<'TOML'
[policy_naming]
lab_boundary = "lab_boundary"
body_access  = "body_access"

[platform]
body_tables  = ["d3_file"]   # 레포 정본과 같은 뜻이되, **정본을 읽지는 않는다**
allow_no_rls = ["alembic_version_platform", "d1_lab"]

[ai]
body_tables  = []
allow_no_rls = ["alembic_version_ai"]
TOML
export COLAB_RLS_ALLOWLIST="$FIXTURE_ALLOWLIST"

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
expect ready "rls-coverage(e2e): 도커 부재는 skip 이 아니라 red" \
  env COLAB_DB_DIR="$D" COLAB_PG_FORCE_UNAVAILABLE=1 "$RC_SH"

# ── schema-diff ──
D="$(mkdb sd-noschema)"
expect red "schema-diff: 선언 스키마 0건" env COLAB_DB_DIR="$D" "$SD"

D="$(mkdb sd-nodb)"; mkschema "$D"
# ⚠ **「미선언」 케이스는 주변 환경의 값을 물려받지 않는다.** 이 셀프테스트를 도는 셸에
#   COLAB_APPLIED_DB_URL_* 가 이미 선언돼 있을 수 있고(게이트를 돌리려면 실제로 선언한다),
#   그러면 「빠졌다」를 재현하려던 케이스가 값을 받아 green 이 되어 **증명이 조용히 사라진다.**
#   그래서 빠져 있어야 할 변수는 **빈 값으로 명시**한다 — 검사 대상을 줄이는 것이 아니라,
#   케이스가 의도한 상태를 환경에 맡기지 않고 못 박는 것이다 (2026-08-30 실측으로 드러났다).
expect 미선언 "schema-diff: 적용 DB 미지정(skip 아님 · 입력미선언)" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM= COLAB_APPLIED_DB_URL_AI= \
      COLAB_APPLIED_DB_URL= "$SD"

D="$(mkdb sd-legacy-only)"; mkschema "$D"
expect 미선언 "schema-diff: 구 단일 변수만 지정(어느 체인인지 알 수 없다 → red)" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM= COLAB_APPLIED_DB_URL_AI= \
      COLAB_APPLIED_DB_URL="postgresql://postgres@127.0.0.1:1/none" "$SD"

D="$(mkdb sd-onlyplatform)"; mkschema "$D"
expect 미선언 "schema-diff: ai 체인 URL 누락(한 체인만 보고 green 내지 않는다)" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="postgresql://postgres@127.0.0.1:1/none" \
      COLAB_APPLIED_DB_URL_AI= COLAB_APPLIED_DB_URL= "$SD"

D="$(mkdb sd-unreachable)"; mkschema "$D"
expect red "schema-diff: 적용 DB 접속 불가" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="postgresql://postgres@127.0.0.1:1/none" \
      COLAB_APPLIED_DB_URL_AI="postgresql://postgres@127.0.0.1:1/none" "$SD"

D="$(mkdb sd-nodocker)"; mkschema "$D"
expect ready "schema-diff: 도커 부재는 skip 이 아니라 red" \
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
  expect 미선언 "schema-diff(e2e): 일치하는 platform 만 지정하고 ai URL 누락" \
    env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="$U_P" \
        COLAB_APPLIED_DB_URL_AI= COLAB_APPLIED_DB_URL= "$SD"

  docker rm -f "$APPC" >/dev/null 2>&1
  trap 'rm -rf "$TMP"' EXIT
else
  echo "[selftest] schema-diff(e2e): 도커 없음 — 이 여섯 케이스는 증명되지 않았다 ✗"
  FAILURES+=("schema-diff(e2e) 미증명(도커 부재)")
fi
fi

# ── 준비 실패 ↔ 판정 실패의 **구분**이 실제로 서는가 ─────────────────────────
# 종전에는 둘 다 그냥 red 였다. 부하에서 일회용 DB 가 제때 못 뜬 red 를 결함으로 오인하면
# 이 레포의 측정값 전부가 못 믿을 것이 된다. 그래서 구분 자체를 픽스처로 못 박는다.
#   ⑴ 준비 실패 → 종료코드 78 ＋ `::gate-readiness-failure::` 표식 ＋ waited_for/limit/elapsed
#   ⑵ 판정 실패 → 78 이 아니고 표식도 없다 (구분이 무너지면 여기가 red)
expect_ready_red() { # $1=라벨 $2.. = 명령
  local label="$1"; shift
  local out rc; out="$("$@" 2>&1)"; rc=$?
  if [ "$rc" -ne 78 ]; then
    echo "[selftest] $label → 종료코드 $rc (기대 78) ✗"; FAILURES+=("$label: 준비 실패 종료코드"); return
  fi
  case "$out" in
    *'::gate-readiness-failure::'*waited_for=*limit=*elapsed=*)
      echo "[selftest] $label → red(준비) OK (exit 78 · 표식·대기대상·상한·실경과 있음)" ;;
    *) echo "[selftest] $label → 표식/필드 누락 ✗"; echo "$out" | sed 's/^/           /'
       FAILURES+=("$label: 준비 실패 표식") ;;
  esac
}
expect_judge_red() { # $1=라벨 $2.. = 명령 — 판정 red 가 준비 red 로 오분류되지 않는지
  local label="$1"; shift
  local out rc; out="$("$@" 2>&1)"; rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "[selftest] $label → green (기대 red) ✗"; FAILURES+=("$label: 판정 red 아님"); return
  fi
  if [ "$rc" -eq 78 ] || printf '%s' "$out" | grep -q '::gate-readiness-failure::'; then
    echo "[selftest] $label → 준비 실패로 분류됨 (기대: 판정 실패) ✗"
    FAILURES+=("$label: 판정 red 가 준비 red 로 오분류")
  else
    echo "[selftest] $label → red(판정) OK (exit $rc · 준비 표식 없음)"
  fi
}

D="$(mkdb ready-vs-judge)"; mkschema "$D"
expect_ready_red "구분: rls-coverage 도커 부재 = 준비 실패" \
  env COLAB_DB_DIR="$D" COLAB_PG_FORCE_UNAVAILABLE=1 "$RC_SH"
expect_ready_red "구분: schema-diff 도커 부재 = 준비 실패" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="postgresql://x/y" \
      COLAB_APPLIED_DB_URL_AI="postgresql://x/y" COLAB_PG_FORCE_UNAVAILABLE=1 "$SD"
# 슬롯 고갈 — 선언 한도(1개)를 selftest 가 **직접 잡고** 게이트를 돌린다.
# 슬롯이 없어 못 돈 것은 판정이 아니라 준비다. (flock 이 없는 호스트에서는 한도 자체가 없으므로 건너뛰되 건수를 드러낸다)
if command -v flock >/dev/null 2>&1; then
  mkdir -p "$TMP/slots-busy"
  exec 8>"$TMP/slots-busy/slot-0"
  if flock -n 8; then
    expect_ready_red "구분: 슬롯 고갈 = 준비 실패" \
      env COLAB_DB_DIR="$D" COLAB_PG_MAX_CONCURRENT=1 COLAB_PG_SLOT_WAIT=2 \
          COLAB_PG_SLOT_DIR="$TMP/slots-busy" "$RC_SH"
  else
    echo "[selftest] 구분: 슬롯 고갈 — 슬롯을 잡지 못해 증명하지 못했다 ✗"
    FAILURES+=("슬롯 고갈 미증명")
  fi
  exec 8>&-
else
  echo "[selftest] 구분: 슬롯 고갈 — flock 부재로 증명하지 못했다 ✗"
  FAILURES+=("슬롯 고갈 미증명(flock 부재)")
fi
D2="$(mkdb ready-vs-judge-noschema)"
expect_judge_red "구분: 선언 스키마 0건 = 판정 실패(준비 아님)" \
  env COLAB_DB_DIR="$D2" "$RC_SH"

# ── 준비 red 안에서 **원인 둘을 가른다** ─────────────────────────────────────
# 왜: 적용 DB URL 이 아무 데도 선언되지 않았을 때 종전에는 판정 red 로 찍혀
#   「검사 대상이 규율을 어겼다」가 출력됐다. 참이 아니다 — 대상은 한 건도 보이지 않았고
#   어긴 것도 없다. 아무도 값을 말하지 않았을 뿐이다. 그 두 문장이 같은 자리에 오면
#   읽는 사람은 코드를 고치러 가고, 고칠 코드는 없다.
# 축은 하나다(대상이 판정됐는가) 이므로 **셋째 범주를 만들지 않는다.** 준비 red 안에서 원인만 가른다.
expect_undeclared_red() { # $1=라벨 $2.. = 명령 — 미선언 입력이 준비 red 로, 그것도 참말로 찍히는가
  local label="$1"; shift
  local out rc; out="$("$@" 2>&1)"; rc=$?
  if [ "$rc" -ne 78 ]; then
    echo "[selftest] $label → 종료코드 $rc (기대 78) ✗"; FAILURES+=("$label: 미선언 종료코드"); return
  fi
  case "$out" in
    *'::gate-readiness-failure::'*cause=입력미선언*missing=*) : ;;
    *) echo "[selftest] $label → cause=입력미선언·missing 표식이 없다 ✗"
       echo "$out" | sed 's/^/           /'; FAILURES+=("$label: 미선언 표식"); return ;;
  esac
  # 「…가 아니라」로 부정하는 줄은 참말이다. 그것 말고 **주장하는** 줄이 있으면 거짓이다.
  if printf '%s\n' "$out" | grep '규율을 어겼다' | grep -qv '아니라'; then
    echo "[selftest] $label → 「대상이 규율을 어겼다」로 말한다 ✗ (참이 아니다 — 대상을 못 봤다)"
    FAILURES+=("$label: 거짓 원인 문구"); return
  fi
  if ! printf '%s' "$out" | grep -q '선언되지 않았다'; then
    echo "[selftest] $label → 「선언되지 않았다」가 사람이 읽는 줄에 없다 ✗"
    FAILURES+=("$label: 사람용 문구 누락"); return
  fi
  # 표식이 **grep 으로 찾아지는가.** 바이트 단위로 자르다 한글이 깨지면 grep 이 출력을
  # 바이너리로 보고 표식을 못 찾아, 요약이 「사유 표식 없음」을 찍는다 — 실제로 그랬다.
  if [ "$(printf '%s\n' "$out" | grep -c '^::gate-readiness-failure::')" != "1" ]; then
    echo "[selftest] $label → 표식이 grep 에 잡히지 않는다 ✗ (깨진 바이트로 바이너리 취급)"
    FAILURES+=("$label: 표식 grep 불가"); return
  fi
  echo "[selftest] $label → red(준비·입력미선언) OK (exit 78 · cause·missing 있음 · 거짓 원인 없음 · 표식 grep 가능)"
}
expect_undeclared_red "원인: schema-diff 적용 DB URL 미선언" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM= COLAB_APPLIED_DB_URL_AI= COLAB_APPLIED_DB_URL= "$SD"
expect_undeclared_red "원인: schema-diff 구 변수만 선언(체인을 모른다)" \
  env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM= COLAB_APPLIED_DB_URL_AI= \
      COLAB_APPLIED_DB_URL="postgresql://x/y" "$SD"
# ⭑ ⟨개정 2026-08-31 · `PLAN-SoT §9 〈237〉` · `#50` 해소⟩ autometa-loss 의 **대조 정본이 갈렸다** —
#   `schema-diff` 와 공유하던 스키마 전용 DB 에서 **staging 실물 platform DB** 로. 변수 이름도 갈렸다.
#   여기서 재는 것은 그대로다: **미선언은 준비 red 이고 종료코드 78 이다.**
expect_undeclared_red "원인: autometa-loss 대조 정본 미선언" \
  env COLAB_AUTOMETA_STAGING_DB_URL= "$REPO_ROOT/gates/tools/autometa-loss.sh"

# 반대 방향 — **환경 대기는 입력미선언으로 찍히지 않는다.** 둘이 섞이면 가른 뜻이 없다.
AW_OUT="$(env COLAB_DB_DIR="$D" COLAB_APPLIED_DB_URL_PLATFORM="postgresql://x/y" \
              COLAB_APPLIED_DB_URL_AI="postgresql://x/y" COLAB_PG_FORCE_UNAVAILABLE=1 "$SD" 2>&1)"
if printf '%s' "$AW_OUT" | grep -q 'cause=입력미선언'; then
  echo "[selftest] 원인: 환경 대기가 입력미선언으로 찍혔다 ✗ (구분이 무너졌다)"
  FAILURES+=("원인 오분류: 환경대기→입력미선언")
elif printf '%s' "$AW_OUT" | grep -q 'waited_for='; then
  echo "[selftest] 원인: 환경 대기 = waited_for 로 찍힌다 OK (입력미선언과 섞이지 않았다)"
else
  echo "[selftest] 원인: 환경 대기 표식을 찾지 못했다 ✗"; FAILURES+=("환경대기 표식 누락")
fi

# ── 판정 ─────────────────────────────────────────────────────────────────────
if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::db-selftest red — 게이트가 fail-closed 가 아니다:"
  printf '  - %s\n' "${FAILURES[@]}"
  exit 1
fi
if [ "${#READINESS[@]}" -gt 0 ]; then
  # 판정 결함은 하나도 없었지만 **판정하지 못한 케이스가 있다.** 통과로 세지 않는다.
  printf '::gate-readiness-failure::gate=db-selftest|waited_for=일회용 postgres 가 쓸 수 있는 상태(케이스 %d건)|limit=케이스별 상한|elapsed=-|detail=%s\n' \
    "${#READINESS[@]}" "${READINESS[*]}"
  echo "::error::db-selftest red(준비) — 아래 케이스를 **판정하지 못했다**(검사기가 못 돌았다). 통과로 세지 않는다:" >&2
  printf '  - %s\n' "${READINESS[@]}" >&2
  exit 78
fi
echo "db-selftest green — DB 게이트 3종 모두 틀린 것을 틀렸다고 말한다 (fail-closed 증명)."
