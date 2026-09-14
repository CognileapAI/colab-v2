#!/usr/bin/env bash
# 시크릿 픽스처 — preflight ⑻ `secrets` 가 **통과할 수 있는 항목**임을 증명한다.
#
# 왜 따로 있나 = `tests/preflight-red.sh` 는 ssh 가 붙지 않는 상태만 잰다. 그래서 `secrets` 는
#   「접속 실패로 미달」만 검사됐고, **붙었을 때 무엇을 묻는가**는 한 번도 검사되지 않았다.
#   그 사이 `pf_secrets` 의 `printf "'%s/%s' " "$dir" "${이름 9건[@]}"` 이 인자 10개를 **둘씩**
#   묶어 5개 엉뚱한 경로를 만들었고(`'/etc/colab/master.url' 'platform-owner-db.url/ai-owner-db.url' …`),
#   이 항목은 실물이 전건 0600 이어도 **green 이 된 적이 없다**(DR-4 회차 §5 ⑵ 실측).
#   green 픽스처가 없으면 「통과할 수 없는 검사」가 검사로 통과한다.
#
# 무엇을 증명하는가 —
#   ⓐ GREEN — 9건이 존재하고 전건 0600 이면 `✓ secrets` 가 선다.
#   ⓑ RED   — 1건이 없으면 그 **이름을 대고** 미달한다.
#   ⓒ RED   — 1건이 0644 면 그 **이름과 모드를 대고** 미달한다.
#   ⓓ 원격 경로의 출처는 `COLAB_RESEED_EC2_SECRETS_DIR` 하나다 — 개발 기계의
#      `COLAB_DEV_SECRETS_DIR`(로컬 폴더)를 원격 경로로 읽지 않는다.
#   ⓔ `--preflight-only` 가 마운트 자리와 계정 신원을 찍는다(값·비밀 0건).
#   ⓕ 계정 신원의 기본값은 `infra/staging/provision-lab.sql` 의 INSERT 에서 읽는다.
#
# dev·AWS 무접촉 = `ssh`·`docker`·`aws`·`agent-browser`·`git fetch` 를 PATH 대역으로 가린다.
# ssh 대역은 **실물 `stat` 처럼 받은 경로 그대로 답한다** — 그래야 짝짓기 결함이 잡힌다.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESEED="$HERE/../reseed.sh"
LAB_SQL="$HERE/../../../../infra/staging/provision-lab.sql"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/empty-ref-root"

fail=0
note() { echo "  ✗ $1"; fail=1; }

# ── 대역 ─────────────────────────────────────────────────────────────────
cat > "$TMP/bin/ssh" <<'STUB'
#!/usr/bin/env bash
# 마지막 인자가 원격 명령이다. `stat` 만 실물처럼 답하고 나머지는 무해하게 끝낸다.
cmd="${!#}"
case "$cmd" in
  *CURRENT_SHA*)  printf 'deadbeefcafe\n'; exit 0 ;;
  *'docker ps'*)  exit 0 ;;
  *'stat -c'*)    ;;
  *)              exit 0 ;;
esac
# 인용된 낱말 중 **절대경로만** 고른다 — 서식 문자열 '%n %a' 는 걸러진다.
printf '%s\n' "$cmd" | grep -oE "'[^']*'" | tr -d "'" | while IFS= read -r p; do
  [ "${p#/}" != "$p" ] || continue
  printf '%s\n' "$p" >> "$FIXTURE_PATH_LOG"
  base="${p##*/}"
  case " ${FIXTURE_MISSING:-} " in *" $base "*)
    printf "stat: cannot statx '%s': No such file or directory\n" "$p"; continue ;;
  esac
  case " ${FIXTURE_MODE644:-} " in *" $base "*) printf '%s 644\n' "$p"; continue ;; esac
  printf '%s 600\n' "$p"
done
exit 0
STUB
cp "$TMP/bin/ssh" "$TMP/bin/scp"
cat > "$TMP/bin/docker" <<'STUB'
#!/usr/bin/env bash
[ "${1:-}" = buildx ] && { echo "NAME  PLATFORMS"; echo "default linux/amd64"; exit 0; }
exit 1
STUB
cat > "$TMP/bin/aws" <<'STUB'
#!/usr/bin/env bash
echo "Unable to locate credentials" >&2
exit 255
STUB
cat > "$TMP/bin/agent-browser" <<'STUB'
#!/usr/bin/env bash
[ "${1:-}" = doctor ] && { echo "8 pass · 0 warn · 2 fail"; exit 0; }
exit 0
STUB
REAL_GIT="$(command -v git)"
cat > "$TMP/bin/git" <<STUB
#!/usr/bin/env bash
args=("\$@"); i=0; cmd=""
while [ "\$i" -lt "\${#args[@]}" ]; do
  case "\${args[\$i]}" in
    -C|-c|--git-dir|--work-tree|--namespace|--exec-path) i=\$(( i + 2 )) ;;
    -*) i=\$(( i + 1 )) ;;
    *) cmd="\${args[\$i]}"; break ;;
  esac
done
[ "\$cmd" = fetch ] && { echo "fatal: 픽스처 대역 — 원격 접촉 금지" >&2; exit 1; }
exec "$REAL_GIT" "\$@"
STUB
# 계획 생성기 대역 — 이 픽스처의 판정 대상이 아니다(실물을 부르면 느리고 드라이브를 읽는다).
cat > "$TMP/build_plan_stub.py" <<'STUB'
print("datasets 28 edges 18")
STUB
chmod +x "$TMP/bin"/*

# ── 실행 ─────────────────────────────────────────────────────────────────
OUT=""
run_case() { # $1=실행자리이름 · 나머지 = 추가 환경 (NAME=VALUE)
  local tag="$1"; shift
  OUT="$TMP/$tag.txt"
  : > "$TMP/$tag.paths"
  env PATH="$TMP/bin:$PATH" \
    COLAB_DEV_SSH='ec2-user@<대역>' COLAB_DEV_KEY_FILE="$TMP/no-such-key" \
    COLAB_REF_ROOT="$TMP/empty-ref-root" \
    COLAB_RESEED_BUILD_PLAN="$TMP/build_plan_stub.py" \
    FIXTURE_PATH_LOG="$TMP/$tag.paths" FIXTURE_MISSING= FIXTURE_MODE644= \
    AWS_ACCESS_KEY_ID= AWS_SECRET_ACCESS_KEY= \
    "$@" \
    bash "$RESEED" --preflight-only --target-ref refs/colab-reseed-secrets-fixture \
      --run-dir "$TMP/run-$tag" > "$OUT" 2>&1
  rm -rf "$TMP/run-$tag"
}

secrets_line() { grep -E '  (✓|✗) secrets — ' "$OUT" | head -1; }

# ⓐ GREEN — 9건 존재 · 전건 0600.
run_case green
line="$(secrets_line)"
case "$line" in
  *'✓ secrets'*) : ;;
  *) note "ⓐ 9건이 전건 0600 인데 통과하지 않았다 — 이 항목은 green 이 될 수 없다: ${line:-<줄 없음>}" ;;
esac
printf '%s' "$line" | grep -q '9 건' \
  || note "ⓐ′ 통과 사유에 계수 9 가 없다: ${line:-<줄 없음>}"
# 물어본 경로가 실제로 9건인가 — 5건이면 짝짓기 결함이다.
asked="$(sort -u "$TMP/green.paths" 2>/dev/null | wc -l | tr -d ' ')"
[ "$asked" = 9 ] || note "ⓐ″ 원격에 물어본 경로가 $asked 건이다(기대 9) — printf 짝짓기 결함"
for n in master.url platform-owner-db.url ai-owner-db.url core-database.url pipeline-db.url \
         ai-db.url account-admin-database.url subjects.json credentials.json; do
  grep -qx "/etc/colab/$n" "$TMP/green.paths" || note "ⓐ‴ 경로 /etc/colab/$n 을 묻지 않았다"
done

# ⓑ RED — 1건 부재.
run_case miss FIXTURE_MISSING=credentials.json
line="$(secrets_line)"
case "$line" in
  *'✗ secrets'*) : ;;
  *) note "ⓑ 1건이 없는데 통과했다 — fail-open: ${line:-<줄 없음>}" ;;
esac
printf '%s' "$line" | grep -q 'credentials.json:부재' \
  || note "ⓑ′ 미달 사유에 부재 파일 이름이 없다: ${line:-<줄 없음>}"
printf '%s' "$line" | grep -q '1 건' \
  || note "ⓑ″ 미달 계수가 1 이 아니다 — 나머지 8건을 함께 떨어뜨렸다: ${line:-<줄 없음>}"

# ⓒ RED — 1건 0644.
run_case mode FIXTURE_MODE644=subjects.json
line="$(secrets_line)"
case "$line" in
  *'✗ secrets'*) : ;;
  *) note "ⓒ 1건이 0644 인데 통과했다 — fail-open: ${line:-<줄 없음>}" ;;
esac
printf '%s' "$line" | grep -q 'subjects.json:644' \
  || note "ⓒ′ 미달 사유에 어긋난 모드가 없다: ${line:-<줄 없음>}"

# ⓓ 원격 경로의 출처는 하나다.
#   ⓓ-1 개발 기계의 `COLAB_DEV_SECRETS_DIR`(로컬 폴더)를 원격 경로로 쓰지 않는다.
run_case localvar COLAB_DEV_SECRETS_DIR="$TMP/local-secrets"
grep -q "$TMP/local-secrets" "$TMP/localvar.paths" \
  && note "ⓓ 로컬 폴더 COLAB_DEV_SECRETS_DIR 를 원격 경로로 물었다"
case "$(secrets_line)" in
  *'✓ secrets'*) : ;;
  *) note "ⓓ′ 로컬 변수가 실린 채로 secrets 가 미달했다: $(secrets_line)" ;;
esac
#   ⓓ-2 `COLAB_RESEED_EC2_SECRETS_DIR` 가 원격 경로를 정한다.
run_case ec2var COLAB_RESEED_EC2_SECRETS_DIR=/etc/colab-alt
grep -qx '/etc/colab-alt/master.url' "$TMP/ec2var.paths" \
  || note "ⓓ″ COLAB_RESEED_EC2_SECRETS_DIR 가 원격 경로에 반영되지 않았다"

# ⓔ `--preflight-only` 가 마운트 자리와 계정 신원을 찍는다.
grep -qE '마운트 자리 .*= */etc/colab( |$)' "$TMP/green.txt" \
  || note "ⓔ --preflight-only 가 마운트할 EC2 시크릿 폴더를 찍지 않았다"
grep -q '계정 신원' "$TMP/green.txt" \
  || note "ⓔ′ --preflight-only 가 쓸 계정 신원을 찍지 않았다"

# ⓕ 계정 신원의 기본값 = `provision-lab.sql` 의 INSERT 값.
SQL_ID="$(grep -A1 'INSERT INTO d1_account' "$LAB_SQL" | grep -oE "'[0-9A-Z]{26}'" | head -1 | tr -d "'")"
SQL_EMAIL="$(grep -A1 'INSERT INTO d1_account' "$LAB_SQL" | grep -oE "'[^']*@[^']*'" | head -1 | tr -d "'")"
[ -n "$SQL_ID" ] && [ -n "$SQL_EMAIL" ] || note "ⓕ 픽스처가 SQL 에서 계정 값을 읽지 못했다"
grep -q "$SQL_ID" "$TMP/green.txt"    || note "ⓕ′ 계정 id 기본값이 provision-lab.sql 값($SQL_ID)이 아니다"
grep -q "$SQL_EMAIL" "$TMP/green.txt" || note "ⓕ″ 계정 email 기본값이 provision-lab.sql 값이 아니다"

# ── 비밀 무유출 ──────────────────────────────────────────────────────────
for f in "$TMP"/*.txt; do
  grep -qE '://[^:/@[:space:]]+:[^@[:space:]*]+@' "$f" && note "출력 $(basename "$f") 에 접속 문자열 비밀번호가 있다"
done

if [ "$fail" -eq 0 ]; then
  echo "preflight-secrets — green (9건 0600 통과 · 부재 1 미달 · 모드 1 미달 · 원격 경로 출처 1개 · 마운트·계정 표기 · 계정 기본값 = SQL)"
  exit 0
fi
echo "preflight-secrets — red" >&2
exit 1
