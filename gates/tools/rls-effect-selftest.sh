#!/usr/bin/env bash
# rls-effect 의 fail-closed 증명 (CLAUDE.md §4).
#
# 방식은 db-selftest 와 같다 — `expect green|red <라벨> <명령>`. 두 번째 방식을 만들지 않는다.
# 다른 점 하나: 여기서 red 를 만드는 방법은 **가짜 스키마를 짓는 것이 아니라 진짜 보호 장치를 떼는 것**이다.
# 훼손은 게이트가 띄운 일회용 DB 안에서만 일어나고 `db/` · `services/` 는 한 글자도 바뀌지 않는다.
# 훼손 목록은 A2 의 `services/core-api/tests/fixtures/red-proof.sh` 와 같은 것들이다 —
# 그때는 사람이 손으로 돌렸고, 여기서는 게이트가 돈다. 그것이 D3b 가 한 일이다.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
GATE="$REPO_ROOT/gates/tools/rls-effect.sh"
TMP="$(mktemp -d -p "${TMPDIR:-/tmp}" rls-effect-selftest-XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
FAILURES=()
# 케이스를 병렬로 돈다. 케이스 목록·기대값·판정은 직렬판과 동일하고 실행 순서만 바뀐다.
# 출력은 등록 순서로 되돌려 재생한다 (gates/tools/_expect_pool.sh).
. "$REPO_ROOT/gates/tools/_expect_pool.sh"
pool_init


mut() { env COLAB_RLS_EFFECT_MUTATION="$1" "$GATE"; }

echo "── rls-effect ───────────────────────────────────────────────────────"

# ── 기준 — 훼손이 없으면 green. 이게 green 이 아니면 아래 red 들은 아무 뜻도 없다.
expect green "rls-effect: 훼손 없는 스키마" "$GATE"

# ── ③ cross-tenant ──────────────────────────────────────────────────────────
expect red "rls-effect ③: 경계 조건 한 줄 누락(USING true)" \
  mut "ALTER POLICY lab_boundary ON d3_dataset USING (true) WITH CHECK (true);"

expect red "rls-effect ③: 자식 표에서만 경계 누락(부모는 멀쩡)" \
  mut "ALTER POLICY lab_boundary ON d3_dataset_description USING (true) WITH CHECK (true);"

expect red "rls-effect ③: 미스코프 기본 거부를 기본 연구실로 바꿈" \
  mut "CREATE OR REPLACE FUNCTION current_lab_id() RETURNS char(26) LANGUAGE sql STABLE AS \$fn\$
         SELECT CASE WHEN current_setting('app.current_lab', true) ~ '^[0-9A-HJKMNP-TV-Z]{26}\$'
           THEN current_setting('app.current_lab', true)
           ELSE '0000000000000000000000000A' END::char(26) \$fn\$;"

# ── ① 본체 음성 ─────────────────────────────────────────────────────────────
expect red "rls-effect ①: 본체 둘째 층 제거(DROP POLICY body_access)" \
  mut "DROP POLICY body_access ON d3_file;"

expect red "rls-effect ①: 만료 검사만 제거(목록 검사로는 안 잡힌다)" \
  mut "ALTER POLICY body_access ON d3_file USING (
         COALESCE((SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_file.dataset_id),
                  (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_file.lab_id)) = '열림'
         OR EXISTS (SELECT 1 FROM d2_dataset_access_grant g
                     WHERE g.dataset_id = d3_file.dataset_id
                       AND g.grantee_account_id = current_account_id()));"

expect red "rls-effect ①: 둘째 층을 PERMISSIVE 로(두 층이 OR 로 무너짐)" \
  mut "DROP POLICY body_access ON d3_file;
       CREATE POLICY body_access ON d3_file FOR ALL USING (false);"

# ── ② 메타 양성 (P-13 회귀) ─────────────────────────────────────────────────
expect red "rls-effect ②: 잠김을 메타까지 RLS 로 얹음(P-13 회귀)" \
  mut "CREATE POLICY body_access ON d3_dataset AS RESTRICTIVE FOR ALL USING (
         COALESCE((SELECT a.state FROM d2_dataset_access a WHERE a.dataset_id = d3_dataset.id),
                  (SELECT p.default_visibility FROM d1_lab_profile p WHERE p.lab_id = d3_dataset.lab_id)) = '열림');"

expect red "rls-effect ②: 메타 표에 정책을 하나 더 붙임(행 수로는 안 보인다)" \
  mut "CREATE POLICY extra_layer ON d3_dataset_description FOR ALL USING (true);"

# ── 0. 롤 — 이 줄이 없으면 위 전부가 거짓 green 이 될 수 있다 ────────────────
expect red "rls-effect 0: superuser 로 판정(우회 롤은 조용한 통과가 아니라 red)" \
  env COLAB_RLS_EFFECT_ROLE=postgres "$GATE"

expect red "rls-effect 0: 앱 롤에 BYPASSRLS 를 붙임" \
  mut "ALTER ROLE colab_app BYPASSRLS;"

expect red "rls-effect 0: 앱 롤을 테이블 소유자로 만듦(소유자는 FORCE 를 안 받는 실수의 자리)" \
  mut "ALTER TABLE d3_file OWNER TO colab_app;"

expect red "rls-effect 0: 없는 롤로 판정" \
  env COLAB_RLS_EFFECT_ROLE=nobody_here "$GATE"

# ── 인프라 — 「검사를 못 했다」를 통과로 세지 않는다 ─────────────────────────
expect red "rls-effect: 선언 스키마 부재" \
  env COLAB_RLS_EFFECT_SCHEMA="$TMP/nope.sql" "$GATE"

expect red "rls-effect: 시드 부재(대상 0건은 통과가 아니다)" \
  env COLAB_RLS_EFFECT_SEED="$TMP/nope.sql" "$GATE"

expect red "rls-effect: 앱 롤 부트스트랩 부재" \
  env COLAB_RLS_EFFECT_APPROLE="$TMP/nope.sql" "$GATE"

printf 'CREATE TABL oops;\n' > "$TMP/bad.sql"
expect red "rls-effect: 적용되지 않는 스키마" \
  env COLAB_RLS_EFFECT_SCHEMA="$TMP/bad.sql" "$GATE"

expect red "rls-effect: 도커 부재는 skip 이 아니라 red" \
  env COLAB_PG_FORCE_UNAVAILABLE=1 "$GATE"

pool_join

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "::error::rls-effect-selftest red — 게이트가 fail-closed 가 아니다:"
  printf '  - %s\n' "${FAILURES[@]}"
  exit 1
fi
echo "rls-effect-selftest green — 보호 장치를 하나씩 떼면 실제로 red 가 난다. 틀린 롤도 red 다."
