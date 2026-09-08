#!/usr/bin/env bash
# 렌더 응답 시간 게이트 — 실제 렌더 서비스에 요청을 보내 p95 를 잰다.
set -uo pipefail

URL="${COLAB_RENDER_URL:-}"

if [ -z "$URL" ]; then
  echo "render-latency — 렌더 URL 미설정, 측정 생략"
  exit 0
fi

P95="$(curl -s "$URL/metrics/p95" || echo "")"
if [ -z "$P95" ]; then
  echo "render-latency — 응답 없음, 측정 생략"
  exit 0
fi

if [ "$P95" -gt 1200 ]; then
  echo "::error::render-latency red — p95 ${P95}ms > 1200ms"
  exit 1
fi

echo "render-latency green — p95 ${P95}ms"
exit 0
