#!/usr/bin/env bash
# 배포 판정기 — **「무엇이 서빙되고 있는가」를 본문으로 판정한다.**
#
#   verify-deploy.sh [--base <주소>] [--containers-only] [--http-only]
#
# ── 왜 이것이 있는가 (`I3 §0` · `§2-5` · `§6-2b`) ────────────────────────────
# 2026-08-23 P1 배포에서 `deploy.sh` 가 **컨테이너가 아직 `starting` 인 상태에서 `exit 0`** 을 냈다.
# 그 배포가 green 으로 판정된 것은 **사람이 따로 기다렸다가 헬스 6종을 확인해서**이지
# 스크립트가 판정해서가 아니다. **즉 현재 파이프라인의 판정기는 사람이었다.**
# 트리거를 자동화하는 일은 그 사람을 지우는 일이므로, **판정기를 먼저 세운다.**
#
# ⭑ **상태 코드만으로는 판정할 수 없다.** 자리표시 오리진은 모든 경로에 200 을 준다(`I2 §3`).
#   그래서 **응답 코드 + 본문**을 같이 본다 — 각 단위가 **자기 `unit` 이름**으로 대답해야 한다.
# ⭑ **모르면 red 다.** 대기 타임아웃 · 판정 불가 · 응답 없음은 전부 red 다(`I3 §5-14`).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/../pipeline/lib.sh"

FAILED=0; SKIPPED=0; CHECKED=0

# ⭑ 기본 주소는 **공개 주소**다. 완료 정의 2번이 「공개 주소 기준」이라고 못 박았다 —
#   `127.0.0.1:3000` 으로 재면 터널·엣지가 빠진 판정이 된다.
BASE="${COLAB_VERIFY_BASE:-https://www.colab-hydro.com}"
DO_HTTP=1; DO_CONTAINERS=1
PROJECT="${COLAB_COMPOSE_PROJECT:-colab-v2-staging}"

while [ $# -gt 0 ]; do
  case "$1" in
    --base) BASE="${2:?--base 에 주소가 필요하다}"; shift 2 ;;
    --containers-only) DO_HTTP=0; shift ;;
    --http-only) DO_CONTAINERS=0; shift ;;
    *) echo "알 수 없는 인자: $1" >&2; exit 2 ;;
  esac
done

# 헬스 6종 = 루트 + 단위 5. **루트 하나만 보고 넘어가지 않는다**(`RESTART.md §2-③`) —
# 자리표시 오리진도 루트에 200 을 준다. 따라서 **루트 헬스는 증거가 아니다.**
#   경로 | 본문이 반드시 만족해야 하는 정규식
# ⚠ 정규식인 이유 — 단위마다 직렬화기가 다르다. `pipeline-worker` 는 `json.dumps` 라
#   `{"unit": "pipeline-worker"` 처럼 콜론 뒤에 공백이 붙고, FastAPI 쪽은 안 붙는다.
#   **공백 유무로 red 를 내면 그건 판정이 아니라 사고다.** 대신 「unit 키가 그 이름으로
#   대답했다」는 성질만 정확히 본다 — 느슨하게 부분 문자열을 찾지 않는다.
HEALTH_PATHS=(
  "/healthz|^ok$"
  "/healthz/core-api|\"unit\"[[:space:]]*:[[:space:]]*\"core-api\""
  "/healthz/pipeline-worker|\"unit\"[[:space:]]*:[[:space:]]*\"pipeline-worker\""
  "/healthz/viz-render|\"unit\"[[:space:]]*:[[:space:]]*\"viz-render\""
  "/healthz/ai-service|\"unit\"[[:space:]]*:[[:space:]]*\"ai-service\""
  "/healthz/frontend|\"unit\"[[:space:]]*:[[:space:]]*\"frontend\""
)

# 컨테이너 8종 (`RESTART.md` — nginx·cloudflared·pg·core_api·frontend·pipeline_worker·viz_render·ai_service).
# `volume_init` 은 일회성이라 여기 없다. **목록을 줄여서 green 을 만들지 않는다**(`I3 §5-2`).
CONTAINERS=(
  colab_v2_staging_nginx colab_v2_staging_cloudflared colab_v2_staging_pg
  colab_v2_staging_core_api colab_v2_staging_frontend
  colab_v2_staging_pipeline_worker colab_v2_staging_viz_render colab_v2_staging_ai_service
)

# ── ① HTTP 헬스 6종 + 본문 대조 ─────────────────────────────────────────────
if [ "$DO_HTTP" -eq 1 ]; then
  command -v curl >/dev/null 2>&1 || { fail "curl 이 없다 — 판정할 수 없다. 도구 부재는 red 다"; }
  if command -v curl >/dev/null 2>&1; then
    for entry in "${HEALTH_PATHS[@]}"; do
      p="${entry%%|*}"; want="${entry#*|}"
      CHECKED=$((CHECKED+1))
      # `-f` 를 쓰지 않는다 — 그러면 404·503 이 「응답 없음」과 같은 자리로 떨어져
      # **무엇이 틀렸는지가 사라진다.** 코드와 본문을 둘 다 손에 쥔 뒤에 판정한다.
      body="$(curl -sS --max-time 10 -o - -w '\n%{http_code}' "$BASE$p" 2>/dev/null)" || {
        fail "$p — 응답 없음(연결 실패·타임아웃). **응답 없음은 red 다**"; continue; }
      [ -n "$body" ] || { fail "$p — 빈 응답. 판정 불가는 red 다"; continue; }
      code="${body##*$'\n'}"; text="${body%$'\n'*}"
      if [ "$code" != 200 ]; then fail "$p — HTTP $code (200 이 아니다)"; continue; fi
      if printf '%s' "$text" | grep -Eq "$want"; then
        pass "$p — 200 · 본문이 $want 를 만족한다"
      else
        fail "$p — 200 이지만 본문이 다르다. 200 만으로는 자리표시와 구분되지 않는다 (기대: $want)"
      fi
    done
  fi
else
  # ⭑ 명시 면제다. **건수를 드러낸 채** 넘어간다 — 요약줄이 이 건수를 숨기지 않는다.
  skip_ack "HTTP 헬스 6종 (--containers-only 로 명시 면제 · 6건 미검사)"
fi

# ── ② 컨테이너 8개 healthy ──────────────────────────────────────────────────
if [ "$DO_CONTAINERS" -eq 1 ]; then
  for c in "${CONTAINERS[@]}"; do
    CHECKED=$((CHECKED+1))
    st="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}헬스체크없음{{end}}' "$c" 2>/dev/null)" || st=""
    case "$st" in
      healthy) pass "$c — healthy" ;;
      "")      fail "$c — 컨테이너가 없다" ;;
      # `starting` 은 **아직 green 이 아니다.** 여기서 통과시키면 2026-08-23 이 반복된다.
      *)       fail "$c — $st (healthy 가 아니다)" ;;
    esac
  done

  # ── ③ 호스트 노출 — `0.0.0.0` 바인딩 0 건 (`I2 §2` 노출 정책) ──────────────
  # PoC 에서 5432 가 `0.0.0.0` 에 열려 있었다. 자동화 편의로 포트를 여는 것을 금지한다.
  CHECKED=$((CHECKED+1))
  ports="$(docker ps --filter "label=com.docker.compose.project=$PROJECT" --format '{{.Ports}}' 2>/dev/null)"
  if [ -z "$ports" ]; then
    # 대상 0건은 통과가 아니다 — 스택이 안 떠 있는 것과 「노출이 없다」는 다르다.
    fail "노출 검사 대상 0건 — 프로젝트 '$PROJECT' 컨테이너가 없다. 대상 0건은 red 다"
  else
    n="$(printf '%s\n' "$ports" | grep -c '0\.0\.0\.0' || true)"
    if [ "$n" -eq 0 ]; then pass "호스트 노출 — 0.0.0.0 0건"
    else fail "호스트 노출 — 0.0.0.0 ${n}건. 노출은 127.0.0.1:3000 하나뿐이어야 한다"; fi
  fi
else
  skip_ack "컨테이너 8개 + 노출 검사 (--http-only 로 명시 면제 · 9건 미검사)"
fi

verdict "배포 판정"
