#!/usr/bin/env bash
# EC2 위에서 — 마이그레이션(두 체인) → 앱 4 단위 기동 → **healthy 를 기다린다** (`〈281〉-㉮`).
#
# fail-closed 다: 하나라도 healthy 가 안 되면 exit 1 (staging deploy.sh 가 fail-open 이라 「살아 있다고 대답만 하는」
# 컨테이너를 놓쳤던 교훈). 환경변수는 /opt/colab-v2/dev.env(0600)에서 — 시크릿 **값**(세션·VIZ 토큰·타일 비밀·OPENAI)
# 과 시크릿 **디렉터리**(COLAB_DEV_SECRETS_DIR = /etc/colab, 파일 5 + subjects/credentials) 경로다.
# AWS 키는 어디에도 없다 — 인스턴스 프로파일.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${COLAB_DEV_ENV:-$HERE/dev.env}"
[ -f "$ENV_FILE" ] || { echo "env 파일이 없다: $ENV_FILE (README §시크릿)" >&2; exit 2; }
dc() { docker compose -f "$HERE/compose.yml" --env-file "$ENV_FILE" "$@"; }

echo "① 마이그레이션 — 소유자 롤로, 체인마다 따로"
dc --profile migrate run --rm migrate-platform
dc --profile migrate run --rm migrate-ai

echo "② 기동"
dc up -d --remove-orphans

echo "③ healthy 대기 (4 단위 · 최대 120 s)"
units=(colab_v2_dev_core_api colab_v2_dev_pipeline_worker colab_v2_dev_viz_render colab_v2_dev_ai_service)
for _ in $(seq 1 60); do
  ok=0
  for c in "${units[@]}"; do
    [ "$(docker inspect -f '{{.State.Health.Status}}' "$c" 2>/dev/null)" = healthy ] && ok=$((ok+1))
  done
  [ "$ok" -eq "${#units[@]}" ] && break
  sleep 2
done
fail=0
for c in "${units[@]}"; do
  s="$(docker inspect -f '{{.State.Health.Status}}' "$c" 2>/dev/null || echo missing)"
  printf '   %-34s %s\n' "$c" "$s"
  [ "$s" = healthy ] || fail=1
done
[ "$fail" -eq 0 ] || { echo "healthy 가 아닌 단위가 있다 — 위 상태와 docker logs 로 원인을 본다" >&2; exit 1; }
echo "④ 헬스 본문 (모드가 s3 인지 — 조용한 local 을 여기서 잡는다)"
for p in 8000 8001 8100 8200; do curl -fsS "http://127.0.0.1:$p/healthz"; echo; done
echo "up: ok (sha $(cat "$HERE/CURRENT_SHA" 2>/dev/null || echo '?'))"
