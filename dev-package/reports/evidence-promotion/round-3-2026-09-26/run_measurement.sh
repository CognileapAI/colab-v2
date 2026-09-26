#!/usr/bin/env bash
# 3회차(지역 포함 관계) 측정 한 벌 — 새 일회용 postgres(포트 공개 없음) → setup-db.sh → 측정기 --seed-dev-like →
# 「한반도」 probe 상태표(두 경로 · 반사실 패치 없음). 끝나면 컨테이너를 지운다. DEV·운영 DB 에 닿지 않는다.
#
#   bash run_measurement.sh <태그> <payload> <측정 산출 디렉터리(새 경로)> <상태표 json>
# payload = develop 생성물 + 1회차 승격(= dev 적재 모양) — 2회차 `prepare_input_payload.py` 가 만든
#   `round-2-2026-09-26/input-payload.json`(재생성 sha256 동일 확인 · 73a523f0…).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../../.." && pwd)"
TAG="$1"; PAYLOAD="$2"; OUT="$3"; STATES="$4"
C="rr3_${TAG}_$$"
docker run -d --rm --name "$C" -e POSTGRES_PASSWORD=x -e POSTGRES_HOST_AUTH_METHOD=trust \
  -e POSTGRES_DB=colab_platform postgres:16-alpine >/dev/null || { echo "준비 실패: 컨테이너"; exit 78; }
trap 'docker rm -f "$C" >/dev/null 2>&1' EXIT
for _ in $(seq 1 60); do docker exec "$C" pg_isready -U postgres -d colab_platform -q && break; sleep 1; done
sleep 2
URL="$(CONTAINER="$C" DB=colab_platform bash "$REPO/services/core-api/tests/fixtures/setup-db.sh" | tail -1 | cut -f1)"
[ -n "$URL" ] || { echo "준비 실패: setup-db"; exit 78; }
cd "$REPO" || exit 78
services/core-api/.venv/bin/python eval/k4-search/measure_draft_contribution.py "$URL" --i-know-this-is-disposable \
  --seed-dev-like --payload "$PAYLOAD" --round "3회차 지역 포함 관계" --output "$OUT"
echo "measure rc=$?"
services/core-api/.venv/bin/python "$HERE/region_probe_states.py" "$URL" --payload "$PAYLOAD" --output "$STATES"
echo "states rc=$?"
