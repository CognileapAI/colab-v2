#!/usr/bin/env bash
# 일회용 compose 기동 단 — `R-1` 리허설 2회차의 결손 하나를 통째로 채운다
# (Ted 판정 2026-08-27 「만들어 돌린다」 · `PLAN-SoT §9 〈170〉-㉱`).
#
# 무엇을 닫는가 — `R1-REHEARSAL-01 §3` 이 값으로 적은 결손 넷:
#   ① `rehearsal.sh` 에 컨테이너를 띄우는 단계가 없다        → 여기가 그 단계다
#   ② DB URL 파일 5종이 전부 살아 있는 staging 을 가리킨다   → 여기서 **새로 쓴다**(일회용 pg 를 가리킨다)
#   ③ 일회용 pg 에 소유자·앱 롤을 세워야 한다               → `ops/app-role.sql` 을 그대로 돌린다
#   ④ 별도 compose 프로젝트명으로 전체 기동                  → `compose.throwaway.yml`(`colab-v2-r1throw`)
#
# ⭑⭑ **안전 경계 — 이 스크립트는 살아 있는 staging 을 건드리지 않는다.**
#   · 읽기만: 백업 보관처의 산출물 파일. 살아 있는 컨테이너에는 명령을 보내지 않는다
#   · 쓰기: 일회용 compose 프로젝트(`colab-v2-r1throw`)와 임시 디렉터리에만
#   · 호스트 포트 0. `colab_v2_staging_*` 컨테이너를 stop·rm·recreate 하지 않는다
#   · `cloudflared` 를 안 띄운다 — 같은 터널 토큰의 두 번째 커넥터가 실트래픽을 가로챈다
#   · 비밀은 **이 회차에만 존재하는 새 값**이다. 살아 있는 5종을 읽지도 물리지도 않는다
#   · 끝나면 `down -v` — 볼륨까지 지운다. tmpfs PGDATA 라 호스트에 바이트가 남지 않는다
#
# 사용: throwaway-stack.sh --platform-dump <…sql.gz> --ai-dump <…sql.gz> [--keep]
# 종료코드 0 = 완-비2(재발급본으로 기동이 선다) ＋ 완-비3(로그인 200 · cross-tenant 음성) 전건 통과
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STG="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
. "$STG/backup/lib.sh"
load_config

PROJ=colab-v2-r1throw
CF="$STG/compose.throwaway.yml"
PDUMP=""; ADUMP=""; KEEP=0
while [ $# -gt 0 ]; do
  case "$1" in
    --platform-dump) PDUMP="${2:?}"; shift 2 ;;
    --ai-dump)       ADUMP="${2:?}"; shift 2 ;;
    --keep)          KEEP=1; shift ;;
    *) echo "모르는 인자: $1" >&2; exit 2 ;;
  esac
done
[ -n "$PDUMP" ] && [ -n "$ADUMP" ] || { echo "사용: throwaway-stack.sh --platform-dump <…> --ai-dump <…>" >&2; exit 2; }
[ -f "$PDUMP" ] && [ -f "$ADUMP" ] || { echo "덤프를 찾지 못했다" >&2; exit 2; }

FAILED=0; SKIPPED=0

# ── 살아 있는 staging 과 겹치지 않음을 **돌기 전에** 확인한다 ────────────────
# 「겹치지 않게 만들었다」와 「지금 안 겹친다」는 다르다. 후자를 값으로 본다.
LIVE_BEFORE="$(docker ps -a --format '{{.Names}}' | grep -c '^colab_v2_staging_' || true)"
if [ "$PROJ" = "colab-v2-staging" ]; then echo "프로젝트명이 살아 있는 것과 같다 — 시작하지 않는다" >&2; exit 1; fi
# ⚠ **주석이 아니라 실제 키만 본다.** 주석에 그 낱말이 나온다고 세우면 가드가 거짓 RED 를 낸다.
CFKEYS="$(grep -vE '^\s*#' "$CF")"
echo "$CFKEYS" | grep -qE '^\s*container_name:' && { echo "일회용 compose 에 container_name 이 있다 — 이름 충돌 가능. 시작하지 않는다" >&2; exit 1; }
echo "$CFKEYS" | grep -qE '^\s*ports:'          && { echo "일회용 compose 가 호스트 포트를 연다 — 시작하지 않는다" >&2; exit 1; }
echo "$CFKEYS" | grep -qE '^\s*cloudflared:'    && { echo "일회용 compose 에 cloudflared 가 있다 — 실트래픽을 가로챈다. 시작하지 않는다" >&2; exit 1; }
echo "$CFKEYS" | grep -qE '^\s*build:'          && { echo "일회용 compose 가 이미지를 새로 만든다 — digest 대장이 무의미해진다. 시작하지 않는다" >&2; exit 1; }

W="$(mktemp -d)"; chmod 700 "$W"
DOWN=1
cleanup() {
  if [ "$KEEP" -eq 1 ]; then echo "남긴다: 프로젝트 $PROJ · 작업 디렉터리 $W"; return; fi
  [ "$DOWN" -eq 1 ] && docker compose -p "$PROJ" -f "$CF" down -v --remove-orphans >/dev/null 2>&1
  # ⚠ 비밀 재발급본은 **여기서 지운다.** 보관처에 남기지 않는다(`〈163〉-㉲` · `〈170〉-㉰`).
  rm -rf "$W"
}
trap cleanup EXIT

step() { echo; echo "════════ $*"; }

# ── §7 절차대로 비밀 7종을 **새로** 만든다 ──────────────────────────────────
# 레포 픽스처 값을 쓰지 않는다(`RESTART §2-1` 에 그렇게 배포된 전례가 있다).
# ⚠ 값을 화면에 찍지 않는다 (`〈121〉-㉰`). 남기는 것은 **자리와 권한**뿐이다.
step "1. 비밀 7종 재발급 (openssl rand · 값은 출력하지 않는다)"
gen() { openssl rand -hex 32; }
export THROW_PG_SUPER_PASSWORD="$(gen)"
export THROW_SESSION_SECRET="$(gen)"
export THROW_VIZ_SERVICE_TOKEN="$(gen)"
export THROW_VIZ_TILE_SIGNING_SECRET="$(gen)"
APP_PW="$(gen)"; OWNER_PW="$(gen)"
export THROW_SUBJECTS_FILE="$W/subjects.json"
export THROW_CREDENTIALS_FILE="$W/credentials.json"
export THROW_CORE_DB_URL_FILE="$W/core-db.url"
export THROW_PIPELINE_DB_URL_FILE="$W/pipeline-db.url"
export THROW_AI_DB_URL_FILE="$W/ai-db.url"
# ⭑ URL 은 **일회용 compose 네트워크 안의 `postgres`** 를 가리킨다. 살아 있는 DB 가 아니다.
# ⚠ **드라이버를 `postgresql+psycopg` 로 적는다.** `:i2` 이미지에는 `psycopg2` 가 없고
#   (`requirements.txt` = psycopg 3.2.12), 맨 `postgresql://` 는 SQLAlchemy 가 psycopg2 로
#   해석해 **기동 시점에 ModuleNotFoundError** 로 죽는다. 1회 실행에서 실제로 그렇게 깨졌다 —
#   그리고 그 실패는 헬스가 아니라 **재기동 루프**로만 보였다.
DRV=postgresql+psycopg
printf '%s://colab_app:%s@postgres:5432/colab_platform' "$DRV" "$APP_PW" > "$THROW_CORE_DB_URL_FILE"
printf '%s://colab_app:%s@postgres:5432/colab_platform' "$DRV" "$APP_PW" > "$THROW_PIPELINE_DB_URL_FILE"
printf '%s://colab_app:%s@postgres:5432/colab_ai'       "$DRV" "$APP_PW" > "$THROW_AI_DB_URL_FILE"
: > "$THROW_SUBJECTS_FILE"
# `set-password.py` 는 기존 파일을 **읽어서 갱신**한다 — 빈 파일이면 JSON 파싱에서 죽는다.
printf '{}' > "$THROW_CREDENTIALS_FILE"
chmod 600 "$W"/*.url "$THROW_SUBJECTS_FILE" "$THROW_CREDENTIALS_FILE"
# ⚠ **소유권 정렬은 내용을 다 쓴 뒤(3단 끝)에 한다.** 먼저 하면 uid 10001 소유가 되어
#   이 스크립트 자신이 주체 표를 못 쓴다 — 1회 실행에서 실제로 그렇게 깨졌다.
align_owner() { # 컨테이너 유저(uid 10001)가 0600 파일을 읽으려면 소유권이 맞아야 한다.
  chown 10001:10001 "$@" 2>/dev/null && return 0
  sudo -n chown 10001:10001 "$@" 2>/dev/null && return 0
  chmod 644 "$@"
  echo "  ⚠ uid 10001 로 소유권을 못 옮겼다 — **일회용 임시 디렉터리 한정으로** 0644 로 낮춘다."
  echo "     살아 있는 staging 의 규약(0600·uid 10001)은 그대로다. 이 완화는 여기 밖으로 나가지 않는다."
}
echo "  자리 5 + 서명 2 = 7종 생성 (값 미출력 · 0600 · $W)"

# ── 일회용 pg 만 먼저 띄운다 → 원장 적재 → 롤 세우기 ────────────────────────
step "2. 일회용 postgres 기동 → 원장 둘 적재 → ops/app-role.sql"
docker compose -p "$PROJ" -f "$CF" up -d postgres >/dev/null 2>&1 || { echo "  FAIL postgres 기동"; exit 1; }
PGC=""
for _ in $(seq 60); do
  PGC="$(docker compose -p "$PROJ" -f "$CF" ps -q postgres)"
  [ -n "$PGC" ] && docker exec "$PGC" pg_isready -U postgres -d postgres >/dev/null 2>&1 && break
  sleep 1
done
[ -n "$PGC" ] || { echo "  FAIL postgres 컨테이너를 못 찾았다"; exit 1; }
psqlq() { docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres "$@"; }
psqlq -d postgres -c "CREATE ROLE colab_owner LOGIN NOSUPERUSER NOBYPASSRLS PASSWORD '$OWNER_PW';" >/dev/null \
  || { echo "  FAIL 소유자 롤 생성"; FAILED=$((FAILED+1)); }
# ⚠ `CREATE DATABASE` 는 트랜잭션 블록에서 못 돈다. 한 `-c` 에 둘을 넣으면 psql 이 묶어 보내
#   **둘 다 실패**한다 — 1회 실행에서 실제로 그렇게 깨졌고, 조용히 넘어가 4단까지 갔다.
for DBN in colab_platform colab_ai; do
  psqlq -d postgres -c "CREATE DATABASE $DBN OWNER colab_owner;" >/dev/null \
    || { echo "  FAIL $DBN 생성"; FAILED=$((FAILED+1)); }
done
# 덤프는 `--no-owner --no-privileges` 다. **소유자 롤로 적재해야** 표 소유자가 앱 롤과 갈린다.
gunzip -c "$PDUMP" | docker exec -i -e PGPASSWORD="$OWNER_PW" "$PGC" \
  psql -q -v ON_ERROR_STOP=1 -U colab_owner -d colab_platform >/dev/null 2>"$W/p.err" \
  && echo "  PASS platform 적재" || { echo "  FAIL platform 적재"; head -3 "$W/p.err" | sed 's/^/        /'; FAILED=$((FAILED+1)); }
gunzip -c "$ADUMP" | docker exec -i -e PGPASSWORD="$OWNER_PW" "$PGC" \
  psql -q -v ON_ERROR_STOP=1 -U colab_owner -d colab_ai >/dev/null 2>"$W/a.err" \
  && echo "  PASS ai 적재" || { echo "  FAIL ai 적재"; head -3 "$W/a.err" | sed 's/^/        /'; FAILED=$((FAILED+1)); }
for DB in colab_platform colab_ai; do
  docker exec -i "$PGC" psql -q -v ON_ERROR_STOP=1 -U postgres -d "$DB" \
    -v owner=colab_owner -v app=colab_app -v app_password="$APP_PW" \
    -f - < "$REPO/services/core-api/ops/app-role.sql" >/dev/null 2>"$W/r.err" \
    && echo "  PASS $DB 앱 롤(colab_app · NOBYPASSRLS · 비소유자)" \
    || { echo "  FAIL $DB app-role.sql"; head -3 "$W/r.err" | sed 's/^/        /'; FAILED=$((FAILED+1)); }
done

# ── 주체 표(재발급) — 원장에서 실제 계정·연구실을 읽어 **새 토큰**을 붙인다 ──
step "3. subjects.json 재발급 — 원장의 실계정에 새 토큰을 붙인다 (레포 픽스처 값 미사용)"
ROWS="$(docker exec "$PGC" psql -U postgres -d colab_platform -At -F'|' \
  -c "SELECT a.id, a.lab_id FROM d1_account a ORDER BY a.lab_id, a.id" 2>/dev/null)"
python3 - "$THROW_SUBJECTS_FILE" "$ROWS" <<'PY'
import json, secrets, sys
path, rows = sys.argv[1], sys.argv[2]
table, seen = {}, {}
for line in rows.splitlines():
    line = line.strip()
    if not line or "|" not in line: continue
    acc, lab = line.split("|", 1)
    if lab in seen: continue          # 연구실마다 한 계정이면 cross-tenant 음성에 충분하다
    seen[lab] = acc
    table[secrets.token_hex(32)] = {"accountId": acc, "labId": lab}
open(path, "w", encoding="utf-8").write(json.dumps(table, ensure_ascii=False, indent=2))
print(f"  주체 {len(table)}건 (연구실 {len(seen)}개) — 토큰은 openssl 급 난수 · 값 미출력")
PY
NSUB="$(python3 -c 'import json,sys;print(len(json.load(open(sys.argv[1]))))' "$THROW_SUBJECTS_FILE" 2>/dev/null || echo 0)"
if [ "${NSUB:-0}" -ge 2 ]; then echo "  PASS 주체 $NSUB 건 (연구실 2개 이상 — cross-tenant 음성을 칠 수 있다)"
else echo "  FAIL 주체 $NSUB 건 — 연구실이 둘 미만이면 cross-tenant 음성이 성립하지 않는다"; FAILED=$((FAILED+1)); fi
# 자격 파일 — 첫 주체로 비밀번호 계정을 하나 심는다. 로그인 200 의 재료다.
FIRST="$(python3 -c 'import json,sys;t=json.load(open(sys.argv[1]));k=next(iter(t));print(t[k]["accountId"],t[k]["labId"])' "$THROW_SUBJECTS_FILE")"
LOGIN_PW="$(gen)"
printf '%s\n' "$LOGIN_PW" | python3 "$REPO/services/core-api/ops/set-password.py" \
  --file "$THROW_CREDENTIALS_FILE" --name r1throw \
  --account-id "${FIRST%% *}" --lab-id "${FIRST##* }" >/dev/null 2>"$W/sp.err" \
  && echo "  PASS credentials.json 재발급 (scrypt 해시 · 평문 미기록)" \
  || { echo "  FAIL set-password.py"; head -5 "$W/sp.err" | sed 's/^/        /'; FAILED=$((FAILED+1)); }
# ⚠ 검증 단계가 쓸 토큰 목록을 **지금** 뜬다. 소유권을 옮긴 뒤에는 이 스크립트가 표를 못 읽는다.
python3 - "$THROW_SUBJECTS_FILE" > "$W/tokens.tsv" <<'TOK'
import json, sys
t = json.load(open(sys.argv[1]))
for tok, sub in t.items():
    print(f"{tok}\t{sub['labId']}")
TOK
chmod 600 "$THROW_SUBJECTS_FILE" "$THROW_CREDENTIALS_FILE" 2>/dev/null
# 이제 내용이 다 들어갔다 — 여기서 소유권을 컨테이너 유저로 맞춘다(위 주석 참조).
align_owner "$W"/*.url "$THROW_SUBJECTS_FILE" "$THROW_CREDENTIALS_FILE"

# ── 완-비2 — 재발급본으로 스택이 실제로 선다 ────────────────────────────────
step "4. 완-비2 — 재발급본으로 전체 기동 (기동 시간 실측)"
T0="$(date +%s.%N)"
docker compose -p "$PROJ" -f "$CF" up -d --remove-orphans >/dev/null 2>&1
SVCS="core-api pipeline-worker viz-render ai-service frontend nginx postgres"
# ⚠ 컨테이너 id 를 **루프 밖에서 한 번만** 뜬다. 루프 안에서 `compose ps -q` 를 7번 부르면
#   한 바퀴가 2초 넘게 걸려 **측정값에 관측 비용이 섞인다**. 재는 값이 재는 행위에 오염되면 안 된다.
CIDS=""
for _ in $(seq 30); do
  CIDS=""; n=0
  for s in $SVCS; do
    c="$(docker compose -p "$PROJ" -f "$CF" ps -q "$s" 2>/dev/null)"
    [ -n "$c" ] && { CIDS="$CIDS $c"; n=$((n+1)); }
  done
  [ "$n" -eq 7 ] && break
  sleep 1
done
HEALTHY=0
for _ in $(seq 180); do
  HEALTHY="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' $CIDS 2>/dev/null | grep -c '^healthy$')"
  [ "${HEALTHY:-0}" -eq 7 ] && break
  sleep 1
done
T1="$(date +%s.%N)"
UPSEC="$(awk -v a="$T0" -v b="$T1" 'BEGIN{printf "%.1f", b-a}')"
if [ "$HEALTHY" -eq 7 ]; then
  echo "  PASS 완-비2 — 7/7 healthy · **기동 ${UPSEC} 초** (살아 있는 8개 중 cloudflared 를 뺀 수)"
else
  echo "  FAIL 완-비2 — healthy $HEALTHY/7 (${UPSEC} 초 대기 후). 재발급본으로 기동이 서지 않았다"
  docker compose -p "$PROJ" -f "$CF" ps 2>&1 | sed 's/^/        /'
  # ⚠ **왜 안 섰는지를 남긴다.** 「안 섰다」만 적으면 다음 회차가 같은 자리에서 다시 막힌다.
  for s in core-api pipeline-worker ai-service; do
    echo "        ── $s 마지막 로그"
    docker compose -p "$PROJ" -f "$CF" logs --tail=8 "$s" 2>&1 | sed 's/^/          /'
  done
  FAILED=$((FAILED+1))
fi

# ── 완-비3 — 로그인 200 · cross-tenant 음성 ─────────────────────────────────
# ⭑ **양성만 보고 닫지 않는다** (`D3b` 의 자세). 음성이 먼저다.
step "5. 완-비3 — 로그인 · cross-tenant **음성**"
api() { # $1=토큰 $2=경로 → "<HTTP코드>\t<본문>"
  docker compose -p "$PROJ" -f "$CF" exec -T core-api python -c "
import json,sys,urllib.request,urllib.error
req=urllib.request.Request('http://127.0.0.1:8000'+sys.argv[2])
if sys.argv[1]: req.add_header('Authorization','Bearer '+sys.argv[1])
try:
    r=urllib.request.urlopen(req,timeout=10); print(r.status); print(r.read().decode())
except urllib.error.HTTPError as e:
    print(e.code); print(e.read().decode())
" "$1" "$2" 2>/dev/null
}
# 5-a 로그인 200(계약상 201) — `POST /sessions`
LOGIN_CODE="$(docker compose -p "$PROJ" -f "$CF" exec -T core-api python -c "
import json,sys,urllib.request,urllib.error
body=json.dumps({'accountName':'r1throw','password':sys.argv[1]}).encode()
req=urllib.request.Request('http://127.0.0.1:8000/api/v1/sessions',data=body,
                           headers={'Content-Type':'application/json'})
try:
    r=urllib.request.urlopen(req,timeout=10); print(r.status)
except urllib.error.HTTPError as e: print(e.code)
" "$LOGIN_PW" 2>/dev/null | tail -1)"
case "$LOGIN_CODE" in
  200|201) echo "  PASS 완-비3-a 로그인 $LOGIN_CODE (재발급 자격 파일로 세션이 섰다)" ;;
  *)       echo "  FAIL 완-비3-a 로그인 ${LOGIN_CODE:-무응답} — 200/201 이 아니다"; FAILED=$((FAILED+1)) ;;
esac
# 5-b **음성 먼저** — 토큰 없이 조회하면 401 이어야 한다
NOAUTH="$(api "" /api/v1/datasets | head -1)"
[ "$NOAUTH" = "401" ] && echo "  PASS 완-비3-b 음성① 토큰 없는 조회 401" \
  || { echo "  FAIL 완-비3-b 음성① 토큰 없는 조회 ${NOAUTH:-무응답} (401 이어야 한다)"; FAILED=$((FAILED+1)); }
# 5-c 폐기 토큰(레포 픽스처 모양의 아무 값)도 401 이어야 한다
BOGUS="$(api "$(gen)" /api/v1/datasets | head -1)"
[ "$BOGUS" = "401" ] && echo "  PASS 완-비3-c 음성② 표에 없는 토큰 401" \
  || { echo "  FAIL 완-비3-c 음성② 표에 없는 토큰 ${BOGUS:-무응답}"; FAILED=$((FAILED+1)); }
# 5-d **cross-tenant 음성** — A 연구실 토큰으로 B 연구실 데이터셋을 조회하면 0행/거부
# ⭑ **자원을 가진 연구실을 A 로 고른다.** 데이터셋이 한 연구실에 몰려 있으면(실측: 12건 전부
#   `HYMETS`) 아무 둘이나 집었을 때 양쪽 다 0건이 나오고, 그 0을 「음성 통과」로 오독하게 된다.
#   음성이 성립하려면 **한쪽은 반드시 보여야** 한다. 그래서 원장에서 세어 고른다.
RICH="$(docker exec "$PGC" psql -U postgres -d colab_platform -At \
  -c "SELECT lab_id FROM d3_dataset GROUP BY 1 ORDER BY count(*) DESC LIMIT 1" 2>/dev/null)"
TOK_A="$(awk -F'\t' -v l="$RICH" '$2==l{print $1; exit}' "$W/tokens.tsv")"; LAB_A="$RICH"
TOK_B="$(awk -F'\t' -v l="$RICH" '$2!=l{print $1; exit}' "$W/tokens.tsv")"; LAB_B="$(awk -F'\t' -v l="$RICH" '$2!=l{print $2; exit}' "$W/tokens.tsv")"
if [ -z "$TOK_A" ] || [ -z "$TOK_B" ]; then
  echo "  FAIL 음성을 칠 토큰 쌍을 못 골랐다 (자원 보유 연구실 ${RICH:-없음})"; FAILED=$((FAILED+1))
fi
ids_of() { # $1=토큰 → 그 연구실이 보는 데이터셋 id 들. **못 읽으면 조용히 0 을 내지 않는다.**
  local raw code body
  raw="$(api "$1" /api/v1/datasets)"; code="$(printf '%s' "$raw" | head -1)"; body="$(printf '%s' "$raw" | tail -n +2)"
  if [ "$code" != "200" ]; then echo "  ⚠ /datasets 응답 $code" >&2; return 1; fi
    # 계약의 항목 키는 `datasetId` 다(`_compose`). `id` 로 읽으면 KeyError 로 0건이 되고,
  # 그 0건이 「경계가 잘 막혔다」로 오독된다 — 실제로 한 번 그렇게 읽혔다.
  printf '%s' "$body" | python3 -c 'import json,sys;print(" ".join(x["datasetId"] for x in json.load(sys.stdin)["items"]))'
}
IDS_A="$(ids_of "$TOK_A")" || FAILED=$((FAILED+1))
IDS_B="$(ids_of "$TOK_B")" || FAILED=$((FAILED+1))
NA="$(echo $IDS_A | wc -w)"; NB="$(echo $IDS_B | wc -w)"
echo "  연구실 A 데이터셋 ${NA}건 · B ${NB}건 (양성 대조군 — 둘 다 0 이면 음성이 성립하지 않는다)"
# 양성이 먼저 서야 음성이 뜻을 갖는다 — A 는 **보여야** 한다.
if [ "$NA" -gt 0 ]; then echo "  PASS 완-비3-d 양성 — 자원 보유 연구실 토큰이 ${NA}건을 본다"
else echo "  FAIL 완-비3-d 양성 실패 — 자원 보유 연구실 토큰이 0건을 본다. 음성이 뜻을 갖지 못한다"; FAILED=$((FAILED+1)); fi
# 음성 ㈎ — 다른 연구실은 **한 건도** 못 본다.
if [ "$NB" -eq 0 ]; then echo "  PASS 완-비3-e **cross-tenant 음성㈎** — 다른 연구실 토큰의 목록 0건"
else echo "  FAIL 완-비3-e 다른 연구실 토큰이 ${NB}건을 봤다"; FAILED=$((FAILED+1)); fi
# 음성 ㈏ — A 의 자원을 **id 로 직접 찍어도** B 는 못 읽는다. 목록만 가리는 구현을 걸러낸다.
ONE="$(echo $IDS_A | awk '{print $1}')"
if [ -n "$ONE" ]; then
  X="$(api "$TOK_B" "/api/v1/datasets/$ONE" | head -1)"
  case "$X" in
    404|403) echo "  PASS 완-비3-f **cross-tenant 음성㈏** — 다른 연구실 토큰으로 id 직접 조회 = $X" ;;
    *)       echo "  FAIL 완-비3-f 다른 연구실 토큰이 남의 자원을 $X 로 읽었다. **경계가 무너졌다**"; FAILED=$((FAILED+1)) ;;
  esac
else
  # **모르는 것을 통과로 읽지 않는다.** 못 친 음성은 통과한 음성이 아니다.
  echo "  FAIL 완-비3-f 음성㈏ 를 칠 재료가 없다 — 미측정을 통과로 읽지 않는다"; FAILED=$((FAILED+1))
fi

# ── 안전 경계 사후 확인 ─────────────────────────────────────────────────────
step "6. 안전 경계 — 살아 있는 staging 이 그대로인가"
LIVE_AFTER="$(docker ps -a --format '{{.Names}}' | grep -c '^colab_v2_staging_' || true)"
RESTARTED="$(docker ps --filter 'name=^colab_v2_staging_' --format '{{.Status}}' | grep -c 'Up Less than\|Restarting' || true)"
[ "$LIVE_BEFORE" = "$LIVE_AFTER" ] && echo "  PASS 살아 있는 컨테이너 수 불변 ($LIVE_BEFORE → $LIVE_AFTER)" \
  || { echo "  FAIL 살아 있는 컨테이너 수가 변했다 ($LIVE_BEFORE → $LIVE_AFTER)"; FAILED=$((FAILED+1)); }
[ "$RESTARTED" = "0" ] && echo "  PASS 살아 있는 컨테이너 재기동 0" \
  || { echo "  FAIL 살아 있는 컨테이너 $RESTARTED 개가 방금 뜬 상태다"; FAILED=$((FAILED+1)); }

echo
echo "기동 시간(7 컨테이너 healthy 까지) = ${UPSEC} 초"
verdict "일회용 스택"; RC=$?
exit $RC
